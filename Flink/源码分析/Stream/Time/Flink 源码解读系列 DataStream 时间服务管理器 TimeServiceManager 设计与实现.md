> Flink 1.15.2

## 1. InternalTimeServiceManager 设计

Flink 1.12.0 版本将 InternalTimeServiceManager 重构为一个接口，目标是可以自定义实现不同的 InternalTimerService 实现，具体查阅[FLINK-19288](https://issues.apache.org/jira/browse/FLINK-19288)。当前版本下，InternalTimeServiceManager 提供了2个核心方法，一个是创建 InternalTimerService 实例的 getInternalTimerService，另一个就是通知所有 InternalTimerService 实例 Watermark 更新的 advanceWatermark：
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

## 2. InternalTimeServiceManager 实现

InternalTimeServiceManagerImpl 是 InternalTimeServiceManager 的一个实现类。维护所有与时间相关服务，到目前为止只维护了一个 InternalTimerServiceImpl 定时器服务。通过 HashMap 来存储管理的所有定时器服务：
```java
Map<String, InternalTimerServiceImpl<K, ?>> timerServices;
```
timerServices 的 key 为定时器服务的名称，value 是名称对应的定时器服务实现。

首先我们如何创建 InternalTimeServiceManager 实例呢？InternalTimeServiceManagerImpl 为我们提供了静态方法 create 可以来创建 InternalTimeServiceManager 实例：
```java
public static <K> InternalTimeServiceManagerImpl<K> create(
        CheckpointableKeyedStateBackend<K> keyedStateBackend,
        ClassLoader userClassloader,
        KeyContext keyContext,
        ProcessingTimeService processingTimeService,
        Iterable<KeyGroupStatePartitionStreamProvider> rawKeyedStates)
        throws Exception {
    final KeyGroupRange keyGroupRange = keyedStateBackend.getKeyGroupRange();
    // 实例化 InternalTimeServiceManagerImpl
    final InternalTimeServiceManagerImpl<K> timeServiceManager =
            new InternalTimeServiceManagerImpl<>(keyGroupRange, keyContext, keyedStateBackend, processingTimeService);
    // 初始化定时器服务
    for (KeyGroupStatePartitionStreamProvider streamProvider : rawKeyedStates) {
        int keyGroupIdx = streamProvider.getKeyGroupId();
        timeServiceManager.restoreStateForKeyGroup(
                streamProvider.getStream(), keyGroupIdx, userClassloader
        );
    }
    return timeServiceManager;
}
```

### 2.1 创建 InternalTimerService 实例

有了 InternalTimeServiceManager 实例之后，我们就可以从 InternalTimeServiceManager 实例中获取一个 InternalTimerService。可以通过 InternalTimeServiceManager 的 getInternalTimerService 方法可以直接获取：
```java
public <N> InternalTimerService<N> getInternalTimerService(
        String name,
        TypeSerializer<K> keySerializer,
        TypeSerializer<N> namespaceSerializer,
        Triggerable<K, N> triggerable) {
    checkNotNull(keySerializer, "Timers can only be used on keyed operators.");
    // 定时器序列化器
    TimerSerializer<K, N> timerSerializer = new TimerSerializer<>(keySerializer, namespaceSerializer);
    // 获取一个时间服务
    InternalTimerServiceImpl<K, N> timerService = registerOrGetTimerService(name, timerSerializer);
    // 启动时间服务
    timerService.startTimerService(timerSerializer.getKeySerializer(),
            timerSerializer.getNamespaceSerializer(),triggerable
    );
    return timerService;
}
```
在一个算子中可以同时创建多个 InternalTimerService 实例，为了区分还必须指定相应的 KeySerializer 和 NamespaceSerializer 序列化类，如果不需要区分 Namespace 类型，也可以使用 VoidNamespaceSerializer。除了 name 和 timerSerializer 参数外，getInternalTimerService 方法还需要传递 triggerable 回调函数作为参数。当触发定时器时会调用 Triggerable 接口的 onEventTime 或 onProcessingTime 方法，以触发定时调度需要执行的逻辑。

我们可以看到在 getInternalTimerService 方法中实际上会调用 registerOrGetTimerService 方法来注册和获取 InternalTimerService 实例。通过 registerOrGetTimerService 可以看出，会事先根据名称从 timerServices 的 HashMap 中获取已经注册的 InternalTimerService，如果没有获取到，则实例化 InternalTimerServiceImpl 类创建一个新的 InternalTimerService：
```java
<N> InternalTimerServiceImpl<K, N> registerOrGetTimerService(String name, TimerSerializer<K, N> timerSerializer) {
    InternalTimerServiceImpl<K, N> timerService = (InternalTimerServiceImpl<K, N>) timerServices.get(name);
    // 如果没有名称对应的定时器服务则创建一个新的
    if (timerService == null) {
        timerService = new InternalTimerServiceImpl<>(
              localKeyGroupRange, keyContext, processingTimeService,
              createTimerPriorityQueue(PROCESSING_TIMER_PREFIX + name, timerSerializer),
              createTimerPriorityQueue(EVENT_TIMER_PREFIX + name, timerSerializer)
        );
        timerServices.put(name, timerService);
    }
    return timerService;
}
```

### 2.2 通知 Watermark 更新

除了通过 getInternalTimerService 获取 InternalTimerService 实例，另一个比较重要的事情就是通过 advanceWatermark 通知所有 InternalTimerService 实例 Watermark 更新：
```java
public void advanceWatermark(Watermark watermark) throws Exception {
    for (InternalTimerServiceImpl<?, ?> service : timerServices.values()) {
        service.advanceWatermark(watermark.getTimestamp());
    }
}
```
可以看到从 timerServices 的 HashMap 中获取全部的 InternalTimerService，然后调用 advanceWatermark 来周知定时器服务 Watermark 更新。

## 3. InternalTimeServiceManager 使用

当 Watermark 流入算子时，调用 AbstractStreamOperator#processWatermark 方法来处理 Watermark：
```java
public void processWatermark(Watermark mark) throws Exception {
    if (timeServiceManager != null) {
        timeServiceManager.advanceWatermark(mark);
    }
    output.emitWatermark(mark);
}
```
在 AbstractStreamOperator#processWatermark 方法中，实际上会调用 InternalTimeServiceManager#advanceWatermark 方法来周知其下管理的 InternalTimerService 定时器服务 Watermark 更新。

接下来我们看看在具体算子中是如何通过 InternalTimeServiceManager 创建和获取 InternalTimerService 实例。在这我们以 WindowOperator 为例展开说明，在 WindowOperator#open 方法中通过调用 AbstractStreamOperator#getInternalTimerService 方法来获取 InternalTimerService 实例：
```java
public class WindowOperator<K, IN, ACC, OUT, W extends Window>
        extends AbstractUdfStreamOperator<OUT, InternalWindowFunction<ACC, OUT, K, W>>
        implements OneInputStreamOperator<IN, OUT>, Triggerable<K, W> {
    ...
    @Override
    public void open() throws Exception {
        ...
        internalTimerService = getInternalTimerService("window-timers", windowSerializer, this);
        ...
    }
    ...
}
```

在 AbstractStreamOperator#getInternalTimerService 方法中，实际上会调用 InternalTimeServiceManager#getInternalTimerService 方法获取 InternalTimerService 实例：
```java
public <K, N> InternalTimerService<N> getInternalTimerService(String name, TypeSerializer<N> namespaceSerializer, Triggerable<K, N> triggerable) {
    if (timeServiceManager == null) {
        throw new RuntimeException("The timer service has not been initialized.");
    }
    InternalTimeServiceManager<K> keyedTimeServiceHandler = (InternalTimeServiceManager<K>) timeServiceManager;
    KeyedStateBackend<K> keyedStateBackend = getKeyedStateBackend();
    checkState(keyedStateBackend != null, "Timers can only be used on keyed operators.");
    return keyedTimeServiceHandler.getInternalTimerService(
                name, keyedStateBackend.getKeySerializer(), namespaceSerializer, triggerable
          );
}
```

> 从上面可以知道，只要继承 AbstractStreamOperator 的算子都可以通过 getInternalTimerService 方法来获取 InternalTimerService 实例以及通过 processWatermark 方法来处理 Watermark。


> 源代码：[InternalTimeServiceManager](https://github.com/apache/flink/blob/release-1.15.2/flink-streaming-java/src/main/java/org/apache/flink/streaming/api/operators/InternalTimeServiceManager.java)
