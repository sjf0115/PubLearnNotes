
> Flink 1.15.2

Window 操作的主要处理逻辑在 WindowOperator 中。由于 window 的使用方式比较比较灵活，下面我们将先介绍最通用的窗口处理逻辑的实现，接着介绍窗口聚合函数的实现，最后介绍对可以合并的窗口的处理逻辑。

## 1. WindowOperator 框架

```java
// org.apache.flink.streaming.runtime.operators.windowing#WindowOperator
public class WindowOperator<K, IN, ACC, OUT, W extends Window>
        extends AbstractUdfStreamOperator<OUT, InternalWindowFunction<ACC, OUT, K, W>>
        implements OneInputStreamOperator<IN, OUT>, Triggerable<K, W> {
    // 1. 继承 AbstractUdfStreamOperator
    public WindowOperator(InternalWindowFunction<ACC, OUT, K, W> userFunction) {
        super(userFunction);
    }
    @Override
    public void open() throws Exception {
        super.open();
    }
    @Override
    public void close() throws Exception {
        super.close();
    }
    @Override
    public void dispose() throws Exception {
        super.dispose();
    }

    // 2. 实现 OneInputStreamOperator 接口
    @Override
    public void processElement(StreamRecord<IN> element) throws Exception {
        ...
    }

    // 3. 实现 Triggerable 接口
    @Override
    public void onEventTime(InternalTimer<K, W> timer) throws Exception {
        ...
    }
    @Override
    public void onProcessingTime(InternalTimer<K, W> timer) throws Exception {
        ...
    }
}
```

变量：


## 2. 生命周期管理

### 2.1 构造器

根据给定的策略和用户函数创建一个新的 WindowOperator：
```java
public WindowOperator(
        WindowAssigner<? super IN, W> windowAssigner,
        TypeSerializer<W> windowSerializer,
        KeySelector<IN, K> keySelector,
        TypeSerializer<K> keySerializer,
        StateDescriptor<? extends AppendingState<IN, ACC>, ?> windowStateDescriptor,
        InternalWindowFunction<ACC, OUT, K, W> windowFunction,
        Trigger<? super IN, ? super W> trigger,
        long allowedLateness,
        OutputTag<IN> lateDataOutputTag) {
    super(windowFunction);
    this.windowAssigner = checkNotNull(windowAssigner);
    this.windowSerializer = checkNotNull(windowSerializer);
    this.keySelector = checkNotNull(keySelector);
    this.keySerializer = checkNotNull(keySerializer);
    this.windowStateDescriptor = windowStateDescriptor;
    this.trigger = checkNotNull(trigger);
    this.allowedLateness = allowedLateness;
    this.lateDataOutputTag = lateDataOutputTag;
    setChainingStrategy(ChainingStrategy.ALWAYS);
}
```
可以看出，构造 WindowOperator 时需要提供的比较重要的对象包括窗口分配器 `WindowAssigner`、窗口触发器 `Trigger`、窗口状态描述符 `StateDescriptor` 以及窗口函数 `InternalWindowFunction`。从窗口状态描述符 StateDescriptor 中知道窗口状态必须是 AppendingState 的子类。

### 2.2 初始化

通过 WindowOperator#open 方法来进行窗口操作之前的初始化工作：
```java
public void open() throws Exception {
    super.open();
    ...
}
首先第一件核心的事情就是通过 InternalTimeServiceManager 获取时间服务 InternalTimerService：
```java
internalTimerService = getInternalTimerService("window-timers", windowSerializer, this);
// WindowOperator#getInternalTimerService
public <K, N> InternalTimerService<N> getInternalTimerService(String name, TypeSerializer<N> namespaceSerializer, Triggerable<K, N> triggerable) {
    if (timeServiceManager == null) {
        throw new RuntimeException("The timer service has not been initialized.");
    }
    InternalTimeServiceManager<K> keyedTimeServiceHandler = (InternalTimeServiceManager<K>) timeServiceManager;
    KeyedStateBackend<K> keyedStateBackend = getKeyedStateBackend();
    checkState(keyedStateBackend != null, "Timers can only be used on keyed operators.");
    return keyedTimeServiceHandler.getInternalTimerService(
            name, keyedStateBackend.getKeySerializer(), namespaceSerializer, triggerable);
}
```
第二件核心的事情是创建上下文对象，包含触发器上下文、窗口上下文以及窗口分配器上下文：
```java
triggerContext = new Context(null, null);
processContext = new WindowContext(null);
windowAssignerContext =
        new WindowAssigner.WindowAssignerContext() {
            @Override
            public long getCurrentProcessingTime() {
                return internalTimerService.currentProcessingTime();
            }
        };
```
第三件核心的事情是根据窗口状态描述符创建窗口状态：
```java
if (windowStateDescriptor != null) {
    windowState = (InternalAppendingState<K, W, IN, ACC, ACC>)
            getOrCreateKeyedState(windowSerializer, windowStateDescriptor);
}
```
最后比较关注的核心事情只是针对于可以合并的窗口，例如会话窗口。可以合并的窗口相比于不可以合并的窗口，除了上面提及到的时间服务、上下文以及窗口状态初始化之外，还会初始化一个新的 windowMergingState 用来存储窗口合并的状态以及一个 mergingSetsState 用于保存 MergingWindowSet 元数据的状态：
```java
if (windowAssigner instanceof MergingWindowAssigner) {
    // 窗口状态必须是可以合并的 用来存储窗口合并的状态
    if (windowState instanceof InternalMergingState) {
        windowMergingState = (InternalMergingState<K, W, IN, ACC, ACC>) windowState;
    }
    // 存储 MergingWindowSet 状态
    final Class<Tuple2<W, W>> typedTuple = (Class<Tuple2<W, W>>) (Class<?>) Tuple2.class;
    final TupleSerializer<Tuple2<W, W>> tupleSerializer =
            new TupleSerializer<>(typedTuple, new TypeSerializer[] {windowSerializer, windowSerializer});
    final ListStateDescriptor<Tuple2<W, W>> mergingSetsStateDescriptor =
            new ListStateDescriptor<>("merging-window-set", tupleSerializer);
    mergingSetsState =
            (InternalListState<K, VoidNamespace, Tuple2<W, W>>)
                    getOrCreateKeyedState(
                            VoidNamespaceSerializer.INSTANCE, mergingSetsStateDescriptor);
    mergingSetsState.setCurrentNamespace(VoidNamespace.INSTANCE);
}
```
相比于不可合并的窗口，可以合并的窗口实现上的一个难点就在于窗口合并时状态的处理，这需要依赖于 mergingSetsState 和 MergingWindowSet。后面会详细地看具体的实现。

注意，需要区分一下几种关于窗口的状态：
- `InternalAppendingState<K, W, IN, ACC, ACC> windowState`：存储窗口中的内容
- `InternalMergingState<K, W, IN, ACC, ACC> windowMergingState`：存储窗口合并的状态
- `InternalListState<K, VoidNamespace, Tuple2<W, W>> mergingSetsState`：存储合并窗口元数据的状态，即 MergingWindowSet

### 2.2 关闭

通过 WindowOperator#close 方法来关闭各种上下文对象：
```java
public void close() throws Exception {
    super.close();
    timestampedCollector = null;
    triggerContext = null;
    processContext = null;
    windowAssignerContext = null;
}
```

## 3. 数据处理

WindowOperator 通过 processElement 方法处理数据流中的每一条数据记录：
```java
public void processElement(StreamRecord<IN> element) throws Exception {
    final Collection<W> elementWindows = windowAssigner.assignWindows(
        element.getValue(), element.getTimestamp(), windowAssignerContext
    );
    ...
}
```
第一步就是要知道要处理的每一个数据记录分配到哪个窗口上。

```java
for (W window : elementWindows) {
    // 1. 丢弃迟到窗口
    if (isWindowLate(window)) {
        continue;
    }
    isSkippedElement = false;
    // 2. 将数据记录存储在窗口状态中
    windowState.setCurrentNamespace(window);
    windowState.add(element.getValue());
    // 3. 通过触发器上下文判断触发结果
    triggerContext.key = key;
    triggerContext.window = window;
    TriggerResult triggerResult = triggerContext.onElement(element);
    // 触发器触发计算
    if (triggerResult.isFire()) {
        ACC contents = windowState.get();
        if (contents == null) {
            continue;
        }
        emitWindowContents(window, contents);
    }
    // 触发器触发清除
    if (triggerResult.isPurge()) {
        windowState.clear();
    }
    registerCleanupTimer(window);
}
```

如果一条数据记录元素到达后，触发器触发了计算操作，则会通过 emitWindowContents 方法调用窗口函数来处理存储在窗口状态中的数据记录：
```java
private void emitWindowContents(W window, ACC contents) throws Exception {
    timestampedCollector.setAbsoluteTimestamp(window.maxTimestamp());
    processContext.window = window;
    userFunction.process(triggerContext.key, window, processContext, contents, timestampedCollector);
}
```
如果触发器触发了清除操作，则会直接清除窗口状态 windowState 中的状态。从侧面可以知道，如果触发器触发的是 CONTINUE，即什么都不做，数据记录只是缓存在窗口状态中等到下一次的触发计算。


最后一步是兜底处理，如果元素没有被窗口处理并且本身也是迟到数据：
```java
if (isSkippedElement && isElementLate(element)) {
    if (lateDataOutputTag != null) {
        sideOutput(element);
    } else {
        this.numLateRecordsDropped.inc();
    }
}
```




```java
protected boolean isElementLate(StreamRecord<IN> element) {
   return (windowAssigner.isEventTime())
           && (element.getTimestamp() + allowedLateness
                   <= internalTimerService.currentWatermark());
}
```


只有基于事件时间的窗口才有迟到窗口的概念，当窗口的清除时间小于等于当前 Watermark 即认为是迟到窗口：
```java
protected boolean isWindowLate(W window) {
    return (windowAssigner.isEventTime()
            && (cleanupTime(window) <= internalTimerService.currentWatermark()));
}
```
如果是基于事件时间的窗口，窗口的清除时间为窗口的最大时间戳加上最大可允许的时间 allowedLateness；如果是基于处理时间的窗口，窗口的清除时间为窗口为窗口的最大时间戳：
```java
private long cleanupTime(W window) {
    if (windowAssigner.isEventTime()) {
        long cleanupTime = window.maxTimestamp() + allowedLateness;
        return cleanupTime >= window.maxTimestamp() ? cleanupTime : Long.MAX_VALUE;
    } else {
        return window.maxTimestamp();
    }
}
```

```java
protected void registerCleanupTimer(W window) {
    // 根据窗口计算窗口清除时间
    long cleanupTime = cleanupTime(window);
    if (cleanupTime == Long.MAX_VALUE) {
        return;
    }
    if (windowAssigner.isEventTime()) {
        // 注册事件时间触发器
        triggerContext.registerEventTimeTimer(cleanupTime);
    } else {
        // 注册处理时间触发器
        triggerContext.registerProcessingTimeTimer(cleanupTime);
    }
}
```


## 4. 定时器触发

### 4.1 基于事件时间触发

```java
public void onEventTime(InternalTimer<K, W> timer) throws Exception {
    triggerContext.key = timer.getKey();
    triggerContext.window = timer.getNamespace();

    MergingWindowSet<W> mergingWindows;
    // 窗口是否可以合并
    if (windowAssigner instanceof MergingWindowAssigner) {
        // 可合并窗口
        mergingWindows = getMergingWindowSet();
        W stateWindow = mergingWindows.getStateWindow(triggerContext.window);
        if (stateWindow == null) {
            return;
        } else {
            windowState.setCurrentNamespace(stateWindow);
        }
    } else {
        // 不可合并窗口
        windowState.setCurrentNamespace(triggerContext.window);
        mergingWindows = null;
    }

    // 触发器触发
    TriggerResult triggerResult = triggerContext.onEventTime(timer.getTimestamp());
    if (triggerResult.isFire()) {
        // 触发窗口计算
        ACC contents = windowState.get();
        if (contents != null) {
            emitWindowContents(triggerContext.window, contents);
        }
    }
    if (triggerResult.isPurge()) {
        // 触发窗口清除
        windowState.clear();
    }
    // 判断是否到达了窗口的清除时间
    if (windowAssigner.isEventTime() && isCleanupTime(triggerContext.window, timer.getTimestamp())) {
        // 清除所有的状态
        clearAllState(triggerContext.window, windowState, mergingWindows);
    }
    if (mergingWindows != null) {
        mergingWindows.persist();
    }
}
```
是否到达了窗口的清除时间：
```java
protected final boolean isCleanupTime(W window, long time) {
    return time == cleanupTime(window);
}
```
清除所有的窗口状态、上下文信息：
```java
private void clearAllState(W window, AppendingState<IN, ACC> windowState, MergingWindowSet<W> mergingWindows) throws Exception {
    windowState.clear();
    triggerContext.clear();
    processContext.window = window;
    processContext.clear();
    if (mergingWindows != null) {
        mergingWindows.retireWindow(window);
        mergingWindows.persist();
    }
}
```


### 4.2 基于处理时间触发

```java
public void onProcessingTime(InternalTimer<K, W> timer) throws Exception {
    triggerContext.key = timer.getKey();
    triggerContext.window = timer.getNamespace();

    MergingWindowSet<W> mergingWindows;

    if (windowAssigner instanceof MergingWindowAssigner) {
        mergingWindows = getMergingWindowSet();
        W stateWindow = mergingWindows.getStateWindow(triggerContext.window);
        if (stateWindow == null) {
            return;
        } else {
            windowState.setCurrentNamespace(stateWindow);
        }
    } else {
        windowState.setCurrentNamespace(triggerContext.window);
        mergingWindows = null;
    }

    TriggerResult triggerResult = triggerContext.onProcessingTime(timer.getTimestamp());
    if (triggerResult.isFire()) {
        ACC contents = windowState.get();
        if (contents != null) {
            emitWindowContents(triggerContext.window, contents);
        }
    }

    if (triggerResult.isPurge()) {
        windowState.clear();
    }

    if (!windowAssigner.isEventTime()
            && isCleanupTime(triggerContext.window, timer.getTimestamp())) {
        clearAllState(triggerContext.window, windowState, mergingWindows);
    }

    if (mergingWindows != null) {
        // need to make sure to update the merging state in state
        mergingWindows.persist();
    }
}
```
