TimeService 是在算子中提供定时器的管理行为，包含定时器的注册和删除。TimerService 在 DataStream、State 中都有应用。在 DataStream 和 State 模块中，一般会在 Keyed 算子中使用。

那么在执行层面上，时间服务 TimerService 具体是怎么发挥其作用的呢?
简单来讲，在算子中使用时间服务来创建定时器（Timer），并且在 Timer 触发的时候进行回调，从而进行业务逻辑处理。前边章节中延迟Join的示例中使用过Timer。

## 1. TimerService 接口

定时器服务在 Flink 中叫作 TimerService，窗口算子（WindowOperator）中使用了 InternalTimerService 来管理定时器（Timer），其初始化是在 WindowOperator#open（）中实现的。
对于 InternalTimerService 而言，有几个元素比较重要：名称、命名空间类型N（及其序列化器）、键类型K（及其序列化器）和Triggerable对象（支持延时计算的算子，继承了Triggerable接口来实现回调）。

一个算子中可以有多个 InternalTimeService，通过名称进行区分，如在WindowOperator中，InternalTimeService的名称是“window-timers”，在KeyedProcessOperator中名称是“user-timers”，在CepOperator中名称是“watermark-callbacks”。
InternalTimerService接口的实现类是InternalTimerServiceImpl，Timer的实现类是InternalTimer。InternalTimerServiceImpl使用了两个TimerHeapInternalTimer的优先队列（HeapPriorityQueueSet，该优先队列是Flink自己实现的），分别用于维护事件时间和处理时间的Timer。
InternalTimeServiceManager是Task级别提供的InternalTimeService集中管理器，其使用Map保存了当前所有的InternalTimeService，Map的Key是InternalTimerService的名字。


我们先来看下 TimerService 的设计与实现，在 DataStream API 中提供了 TimerService 接口，用于获取和操作时间相关的信息，包括获取处理时间和事件时间以及注册、删除处理时间定时器和事件时间定时器，如下所示：
```java
public interface TimerService {
    // 当前处理时间
    long currentProcessingTime();
    // 当前 Watermark
    long currentWatermark();
    // 注册处理时间定时器
    void registerProcessingTimeTimer(long time);
    // 注册事件时间定时器
    void registerEventTimeTimer(long time);
    // 删除指定时间的处理时间定时器
    void deleteProcessingTimeTimer(long time);
    // 删除指定时间的事件时间定时器
    void deleteEventTimeTimer(long time);
}
```

TimerService 接口的默认实现有 SimpleTimerService，在 Flink Table API 模块的 AbstractProcessStreamOperator.ContextImpl 内部类中也实现了 TimerService 接口。

![](1)

SimpleTimerService 会将 InternalTimerService 接口作为内部成员变量，因此在 SimpleTimerService 中提供的方法基本上都是借助 InternalTimerService 实现的，实际上将 InternalTimerService 进行了封装：
```java
@Internal
public class SimpleTimerService implements TimerService {
    // InternalTimerService 接口作为内部成员变量
    private final InternalTimerService<VoidNamespace> internalTimerService;

    public SimpleTimerService(InternalTimerService<VoidNamespace> internalTimerService) {
        this.internalTimerService = internalTimerService;
    }
    // 以下方法都需要借助 InternalTimerService 实现
    @Override
    public long currentProcessingTime() {
        // 当前处理时间
        return internalTimerService.currentProcessingTime();
    }
    @Override
    public long currentWatermark() {
        // 当前 Watermark
        return internalTimerService.currentWatermark();
    }
    @Override
    public void registerProcessingTimeTimer(long time) {
        // 注册处理时间定时器
        internalTimerService.registerProcessingTimeTimer(VoidNamespace.INSTANCE, time);
    }
    @Override
    public void registerEventTimeTimer(long time) {
        // 注册事件时间定时器
        internalTimerService.registerEventTimeTimer(VoidNamespace.INSTANCE, time);
    }
    @Override
    public void deleteProcessingTimeTimer(long time) {
        // 删除指定时间的处理时间定时器
        internalTimerService.deleteProcessingTimeTimer(VoidNamespace.INSTANCE, time);
    }
    @Override
    public void deleteEventTimeTimer(long time) {
        // 删除指定时间的事件时间定时器
        internalTimerService.deleteEventTimeTimer(VoidNamespace.INSTANCE, time);
    }
}
```
InternalTimerService 实际上是 TimerService 接口的内部版本，而 TimerService 接口是专门供用户使用的外部接口：
```java
public interface InternalTimerService<N> {
    // 当前处理时间
    long currentProcessingTime();
    long currentWatermark();
    void registerProcessingTimeTimer(N namespace, long time);
    void deleteProcessingTimeTimer(N namespace, long time);
    void registerEventTimeTimer(N namespace, long time);
    void deleteEventTimeTimer(N namespace, long time);
    void forEachEventTimeTimer(BiConsumerWithException<N, Long, Exception> consumer) throws Exception;
    void forEachProcessingTimeTimer(BiConsumerWithException<N, Long, Exception> consumer) throws Exception;
}
```
> org.apache.flink.streaming.api.operators#InternalTimerService

InternalTimerService 需要按照 Key 和命名空间进行划分，并提供操作时间和定时器的内部方法，因此不仅是 SimpleTimerService 通过 InternalTimerService 操作和获取时间信息以及定时器，其他还有如 WindowOperator、IntervalJoinOperator 等内置算子也都会通过 InternalTimerService 提供的方法执行时间相关的操作。

## 2. InternalTimerServiceImpl

InternalTimerService 接口具有 InternalTimerServiceImpl 的默认实现类，在 InternalTimerServiceImpl 中，实际上包含了两个比较重要的成员变量，分别为 `processingTimeService` 和 `KeyGroupedInternalPriorityQueue<TimerHeapInternalTimer<K, N>>` 队列。其中 processingTimeService 是基于系统处理时间提供的 TimerService，即基于 ProcessingTimeService 的实现类可以注册基于处理时间的定时器。TimerHeapInternalTimer 队列主要分为 processingTimeTimersQueue 和 eventTimeTimersQueue 两种类型，用于存储相应类型的定时器队列。TimerHeapInternalTimer 基于 Heap 堆内存存储定时器，并通过 HeapPriorityQueueSet 结构存储注册好的定时器。

在 InternalTimerServiceImpl 中，会记录 currentWatermark 信息，用于表示当前算子的最新 Watermark，实际上 InternalTimerServiceImpl 实现了基于 Watermark 的时钟，此时算子会递增更新 InternalTimerServiceImpl 中 Watermark 对应的时间戳。此时 InternalTimerService 会判断 eventTimeTimersQueue 队列中是否有定时器、是否满足触发条件，如果满足则将相应的 TimerHeapInternalTimer 取出，并执行对应算子中的 onEventTime() 回调方法，此时就和 ProcessFunction 中的 onTimer() 方法联系在一起了。

```java
// 当前处理时间
@Override
public long currentProcessingTime() {
    return processingTimeService.getCurrentProcessingTime();
}
// 当前 Watermark
@Override
public long currentWatermark() {
    return currentWatermark;
}
// 注册处理时间定时器
public void registerProcessingTimeTimer(N namespace, long time) {
    InternalTimer<K, N> oldHead = processingTimeTimersQueue.peek();
    TimerHeapInternalTimer timer = new TimerHeapInternalTimer<>(time, (K) keyContext.getCurrentKey(), namespace);
    if (processingTimeTimersQueue.add(timer)) {
        long nextTriggerTime = oldHead != null ? oldHead.getTimestamp() : Long.MAX_VALUE;
        // check if we need to re-schedule our timer to earlier
        if (time < nextTriggerTime) {
            if (nextTimer != null) {
                nextTimer.cancel(false);
            }
            nextTimer = processingTimeService.registerTimer(time, this::onProcessingTime);
        }
    }
}
// 注册事件时间定时器
public void registerEventTimeTimer(N namespace, long time) {
    eventTimeTimersQueue.add(
          new TimerHeapInternalTimer<>(time, (K) keyContext.getCurrentKey(), namespace)
    );
}
// 删除处理时间定时器
@Override
public void deleteProcessingTimeTimer(N namespace, long time) {
    processingTimeTimersQueue.remove(
          new TimerHeapInternalTimer<>(time, (K) keyContext.getCurrentKey(), namespace)
    );
}
// 删除事件时间定时器
@Override
public void deleteEventTimeTimer(N namespace, long time) {
    eventTimeTimersQueue.remove(
          new TimerHeapInternalTimer<>(time, (K) keyContext.getCurrentKey(), namespace)
    );
}
```

## 3. 如何获取时间服务

接下来我们看看在算子中如何通过调用 AbstractStreamOperator.getInternalTimerService() 方法创建和获取 InternalTimerService 实例。

在 AbstractStreamOperator.getInternalTimerService() 方法中，实际上会调用 InternalTimeServiceManager.getInternalTimerService() 方法获取 InternalTimerService 实例。在一个 Operator 中可以同时创建多个 TimerService 实例，且必须具有相应的 KeySerializer和 NamespaceSerializer 序列化类，如果不需要区分 Namespace 类型，也可以使用 VoidNamespaceSerializer。

除了 name 和 timerSerializer 参数外，getInternalTimerService() 方法还需要传递 triggerable 回调函数作为参数。当触发定时器时会调用 Triggerable 接口的 onEventTime() 或 onProcessingTime() 方法，以触发定时调度需要执行的逻辑，这里的 Triggerable 接口实现类实际上就是 StreamOperator 接口的实现类。

代码清单2-33 InternalTimeServiceManager.getInternalTimerService()方法
//获取InternalTimerService
public <N> InternalTimerService<N> getInternalTimerService(
   String name,
   TimerSerializer<K, N> timerSerializer,
   Triggerable<K, N> triggerable) {
   InternalTimerServiceImpl<K, N> timerService = registerOrGetTimerService
      (name, timerSerializer);
   timerService.startTimerService(
      timerSerializer.getKeySerializer(),
      timerSerializer.getNamespaceSerializer(),
      triggerable);
   return timerService;
}

如代码清单2-34所示，在getInternalTimerService()方法中实际上会调用registerOrGetTimerService()方法注册和获取InternalTimerService实例。在InternalTimeServiceManager.registerOrGetTimerService中可以看出，会事先根据名称从timerServices的HashMap获取已经注册的InternalTimerService，如果没有获取到，则实例化InternalTimerServiceImpl类，创建新的TimerService。
代码清单2-34 InternalTimeServiceManager.registerOrGetTimerService()方法定义
// 注册及获取TimerService
<N> InternalTimerServiceImpl<K, N> registerOrGetTimerService(String name,
   TimerSerializer<K, N> timerSerializer) {
      InternalTimerServiceImpl<K, N> timerService =
         (InternalTimerServiceImpl<K, N>)
//先从timerServices中获取创建好的TimerService
   timerServices.get(name);
      // 如果没有获取到就创建新的timerService
      if (timerService == null) {
         timerService = new InternalTimerServiceImpl<>(
            localKeyGroupRange,
            keyContext,
            processingTimeService,
            createTimerPriorityQueue(PROCESSING_TIMER_PREFIX + name,
               timerSerializer),
            createTimerPriorityQueue(EVENT_TIMER_PREFIX + name,
               timerSerializer));
         timerServices.put(name, timerService);
      }
      return timerService;
   }
```java
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

Flink 1.12.0 版本将 InternalTimeServiceManager 重构为一个接口，目标是可以自定义实现不同的 InternalTimerService 实现。当前版本下，InternalTimeServiceManager 核心提供了三个方法，一个是创建内部时间服务 InternalTimerService 实例的 getInternalTimerService，另一个就是通知所有内部时间服务 InternalTimerService 实例 Watermark 更新的 advanceWatermark：
```java
@Internal
public interface InternalTimeServiceManager<K> {
    // 创建一个 InternalTimerService
    <N> InternalTimerService<N> getInternalTimerService(
            String name,
            TypeSerializer<K> keySerializer,
            TypeSerializer<N> namespaceSerializer,
            Triggerable<K, N> triggerable);
    // 通知 Watermark 的更新
    void advanceWatermark(Watermark watermark) throws Exception;
    // 快照定时器
    void snapshotToRawKeyedState(
            KeyedStateCheckpointOutputStream stateCheckpointOutputStream, String operatorName)
            throws Exception;
    // 用于创建 InternalTimeServiceManager
    @FunctionalInterface
    interface Provider extends Serializable {
        <K> InternalTimeServiceManager<K> create(
                CheckpointableKeyedStateBackend<K> keyedStatedBackend,
                ClassLoader userClassloader,
                KeyContext keyContext,
                ProcessingTimeService processingTimeService,
                Iterable<KeyGroupStatePartitionStreamProvider> rawKeyedStates)
                throws Exception;
    }
}
```
> org.apache.flink.streaming.api.operators#InternalTimeServiceManager

InternalTimeServiceManagerImpl 是一个维护所有与时间相关服务的实现类。但是，到目前为止只维护一个 InternalTimerServiceImpl 定时器服务。





...
