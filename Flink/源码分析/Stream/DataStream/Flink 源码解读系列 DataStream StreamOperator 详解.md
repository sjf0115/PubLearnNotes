算子在 Flink 中叫作 StreamOperator。StreamOperator 是流计算的算子。Flink 作业运行时由 Task 组成一个 Dataflow，每个 Task 中包含一个或者多个算子，1个算子就是1个计算步骤，具体的计算由算子中包装的 Function 来执行。除了业务逻辑的执行算子外，还提供了生命周期的管理。

所有的算子都包含了生命周期管理、状态与容错管理、数据处理3个方面的关键行为。
1.生命周期管理
所有的算子都有共同的生命周期管理，其核心生命周期阶段如下。
1）setup：初始化环境、时间服务、注册监控等。
2）open：该行为由各个具体的算子负责实现，包含了算子的初始化逻辑，如状态初始化等。算子执行该方法之后，才会执行Function进行数据的处理。
3）close：所有的数据处理完毕之后关闭算子，此时需要确保将所有的缓存数据向下游发送。
4）dispose：该方法在算子生命周期的最后阶段执行，此时算子已经关闭，停止处理数据，进行资源的释放。
StreamTask作为算子的容器，负责管理算子的生命周期。
2.状态与容错管理
算子负责状态管理，提供状态存储，触发检查点的时候，保存状态快照，并且将快照异步保存到外部的分布式存储。当作业失败的时候算子负责从保存的快照中恢复状态。
3.数据处理
算子对数据的处理，不仅会进行数据记录


StreamOperator 作为接口，在被 OneInputStreamOperator 接口和 TwoInputStreamOperator 接口继承的同时，又分别被 AbstractStreamOperator 和 AbstractUdfStreamOperator 两个抽象类继承和实现。其中 OneInputStreamOperato 和 TwoInputStreamOperator 定义了不同输入数量的 StreamOperator 方法，例如：单输入类型算子通常会实现 OneInputStreamOperator 接口，常见的实现有 StreamSource 和 StreamSink 等算子；TwoInputStreamOperator 则定义了双输入类型算子，常见的实现有 CoProcessOperator、CoStreamMap 等算子。从这里我们可以看出，StreamOperator 和 Transformation 基本上是一一对应的，最多支持双输入类型算子，而不支持多输入类型，用户可以通过多次关联 TwoInputTransformation 实现多输入类型的算子。


通过图2-3可以看出，不管是 OneInputStreamOperator 还是 TwoInputStreamOperator 类型的算子，最终都会继承 AbstractStreamOperator 基本实现类。在调度和执行 Task 实例时，会通过 AbstractStreamOperator 提供的入口方法触发和执行 Operator。同时在 AbstractStreamOperator 中也定义了所有算子中公共的组成部分，如 StreamingRuntimeContext、OperatorStateBackend 等。对于 AbstractStreamOperator 如何被 SubTask 触发和执行，我们会在第4章讲解任务提交与运行时做详细介绍。另外，AbstractUdfStreamOperator 基本实现类则主要包含了 UserFunction 成员变量，允许当前算子通过自定义 UserFunction 实现具体的计算逻辑。

## 1. StreamOperator

接下来我们深入了解 StreamOperator 接口的定义：
```java
public interface StreamOperator<OUT> extends CheckpointListener, KeyContext, Disposable, Serializable {
    // 生命周期
    void open() throws Exception;
    void close() throws Exception;
    @Override
    void dispose() throws Exception;
    // 状态快照
    void prepareSnapshotPreBarrier(long checkpointId) throws Exception;
    OperatorSnapshotFutures snapshotState(
            long checkpointId, long timestamp,
            CheckpointOptions checkpointOptions,
            CheckpointStreamFactory storageLocation) throws Exception;
    void initializeState(StreamTaskStateInitializer streamTaskStateManager) throws Exception;
    void setKeyContextElement1(StreamRecord<?> record) throws Exception;
    void setKeyContextElement2(StreamRecord<?> record) throws Exception;
    MetricGroup getMetricGroup();
    OperatorID getOperatorID();
}
```
StreamOperator 接口主要包括如下核心方法：
- open：定义当前 Operator 的初始化方法，在数据元素正式接入 Operator 运算之前，Task 会调用 open 方法对该算子进行初始化，具体 open 方法的定义由子类实现，常见的用法如调用 RichFunction 中的 open 方法创建相应的状态变量。
- close：当所有的数据元素都添加到当前 Operator 时，就会调用该方法刷新所有剩余的缓冲数据，保证算子中所有数据被正确处理。
- dispose：算子生命周期结束时会调用此方法，包括算子操作执行成功、失败或者取消时。
- prepareSnapshotPreBarrier：在 StreamOperator 正式执行 checkpoint 操作之前会调用该方法，目前仅在 MapBundleOperator 算子中使用该方法。
- snapshotState：当 SubTask 执行 checkpoint 操作时会调用该方法，用于触发该 Operator 中状态数据的快照操作。
- initializeState：当算子启动或重启时，调用该方法初始化状态数据，当恢复作业任务时，算子会从检查点（checkpoint）持久化的数据中恢复状态数据。

> StreamOperator 接口实现的方法主要供 Task 调用和执行。

## 2. AbstractStreamOperator

AbstractStreamOperator 作为 StreamOperator 的基本实现类，所有的 Operator 都会继承和实现该抽象实现类。在 AbstractStreamOperator 中定义了 Operator 用到的基础方法和成员信息：
```java

```


我们重点梳理 AbstractStreamOperator 的主要成员变量和方法。AbstractStreamOperator包含的主要成员变量如下
- ChainingStrategy chainingStrategy：用于指定 Operator 的上下游算子链接策略，其中 ChainStrategy 可以是 ALWAYS、NEVER 或 HEAD 类型，该参数实际上就是转换过程中配置的链接策略。
- StreamTask<?, ?> container：表示当前 Operator 所属的 StreamTask，最终会通过 StreamTask 中的 invoke() 方法执行当前 StreamTask 中的所有 Operator。
- StreamConfig config：存储了该StreamOperator的配置信息，实际上是对Configuration参数进行了封装。
- Output<StreamRecord<OUT>> output：定义了当前StreamOperator的输出操作，执行完该算子的所有转换操作后，会通过Output组件将数据推送到下游算子继续执行。
- StreamingRuntimeContext runtimeContext：主要定义了UDF执行过程中的上下文信息，例如获取累加器、状态数据。
- KeySelector<?, ?> stateKeySelector1：只有 DataStream 经过 keyBy() 转换操作生成 KeyedStream 后，才会设定该算子的 stateKeySelector1 变量信息。
- KeySelector<?, ?> stateKeySelector2：只在执行两个 KeyedStream 关联操作时使用，例如 Join 操作，在 AbstractStreamOperator 中会保存 stateKeySelector2 的信息。
- AbstractKeyedStateBackend<?> keyedStateBackend：用于存储 KeyedState 的状态管理后端，默认为 HeapKeyedStateBackend。如果配置 RocksDB 作为状态存储后端，则此处为 RocksDBKeyedStateBackend。
- DefaultKeyedStateStore
keyedStateStore：主要提供KeyedState的状态存储服务，实际上是对KeyedStateBackend进行封装并提供了不同类型的KeyedState获取方法，例如通过getReducingState(ReducingStateDescriptor stateProperties)方法获取ReducingState。
·OperatorStateBackend operatorStateBackend：和keyedStateBackend相似，主要提供OperatorState对应的状态后端存储，默认OperatorStateBackend只有DefaultOperatorStateBackend实现。
·OperatorMetricGroup metrics：用于记录当前算子层面的监控指标，包括numRecordsIn、numRecordsOut、numRecordsInRate、numRecordsOutRate等。
·LatencyStats latencyStats：用于采集和汇报当前Operator的延时状况。
·ProcessingTimeService processingTimeService：基于ProcessingTime的时间服务，实现ProcessingTime时间域操作，例如获取当前ProcessingTime，然后创建定时器回调等。
·InternalTimeServiceManager<?>timeServiceManager：Flink内部时间服务，和processingTimeService相似，但支持基于事件时间的时间域处理数据，还可以同时注册基于事件时间和处理时间的定时器，例如在窗口、CEP等高级类型的算子中，会在ProcessFunction中通过timeServiceManager注册Timer定时器，当事件时间或处理时间到达指定时间后执行Timer定时器，以实现复杂的函数计算。
·long combinedWatermark：在双输入类型的算子中，如果基于事件时间处理乱序事件，会在AbstractStreamOperator中合并输入的Watermark，选择最小的Watermark作为合并后的指标，并存储在combinedWatermark变量中。
·long input1Watermark：二元输入算子中input1对应的Watermark大小。
·long input2Watermark：二元输入算子中input2对应的Watermark大小。


AbstractStreamOperator除了定义主要的成员变量之外，还定义了子类实现的基本抽象方法。
·processLatencyMarker()：用于处理在SourceOperator中产生的LatencyMarker信息。在当前Operator中会计算事件和LatencyMarker之间的差值，用于评估当前算子的延时程度。
·processWatermark()：用于处理接入的Watermark时间戳信息，并用最新的Watermark更新当前算子内部的时钟。
·getInternalTimerService()：提供子类获取InternalTimerService的方法，以实现不同类型的Timer注册操作。



```java

```

## 3. AbstractUdfStreamOperator

当 StreamOperator 涉及自定义用户函数数据转换处理时，对应的 Operator 会继承 AbstractUdfStreamOperator 抽象实现类，常见的有 StreamMap、CoProcessOperator 等算子。当然，并不是所有的 Operator 都继承自 AbstractUdfStreamOperator。在 Flink Table API 模块实现的算子中，都会直接继承和实现 AbstractStreamOperator 抽象实现类。另外，有状态查询的 AbstractQueryableStateOperator 也不需要使用用户自定义函数处理数据。

AbstractUdfStreamOperator 继承自 AbstractStreamOperator 抽象类，作为具有用户自定义函数算子的基类。对于 AbstractUdfStreamOperator 抽象类来讲，最重要的拓展就是增加了成员变量 userFunction：
```java
public abstract class AbstractUdfStreamOperator<OUT, F extends Function>
        extends AbstractStreamOperator<OUT> implements OutputTypeConfigurable<OUT> {
    private static final long serialVersionUID = 1L;
    // 用户自定义函数
    protected final F userFunction;
    // 避免在 close() 和 dispose() 中重复调用 function.close() 的标记
    private transient boolean functionsClosed = false;
    // 指定自定义函数创建 AbstractUdfStreamOperator
    public AbstractUdfStreamOperator(F userFunction) {
        this.userFunction = requireNonNull(userFunction);
        // 用户自定义函数不允许同时实现 CheckpointedFunction 和 ListCheckpointed
        checkUdfCheckpointingPreconditions();
    }
    public F getUserFunction() {
        return userFunction;
    }
    ...
}
```
此外还提供了 userFunction 初始化以及状态持久化的抽象方法。下面我们简单介绍 AbstractUdfStreamOperator 提供的主要方法。

### 3.1 setup

在 setup 方法中会调用 FunctionUtils#setFunctionRuntimeContext 为 userFunction 设定 RuntimeContext 变量。只有当 userFunction 为富函数 RichFunction 才能够获取 RuntimeContext 变量，然后实现获取状态数据等操作：
```java
public void setup(StreamTask<?, ?> containingTask, StreamConfig config,
        Output<StreamRecord<OUT>> output) {
    super.setup(containingTask, config, output);
    FunctionUtils.setFunctionRuntimeContext(userFunction, getRuntimeContext());
}
// FunctionUtils#setFunctionRuntimeContext
public static void setFunctionRuntimeContext(Function function, RuntimeContext context) {
    if (function instanceof RichFunction) {
        RichFunction richFunction = (RichFunction) function;
        richFunction.setRuntimeContext(context);
    }
}
```

### 3.2 open

在 open 方法中调用了 FunctionUtils#openFunction() 方法。当用户自定义并实现 RichFunction 时，FunctionUtils.openFunction() 方法会调用 RichFunction.open() 方法，完成用户自定义状态的创建和初始化：
```java
public void open() throws Exception {
    super.open();
    FunctionUtils.openFunction(userFunction, new Configuration());
}

// FunctionUtils#openFunction
public static void openFunction(Function function, Configuration parameters) throws Exception {
    if (function instanceof RichFunction) {
        RichFunction richFunction = (RichFunction) function;
        richFunction.open(parameters);
    }
}
```
可以看出，当用户自定义实现 Function 时，在 AbstractUdfStreamOperator 抽象类中提供了对这些Function的初始化操作，也就实现了Operator和Function之间的关联。Operator也是Function的载体，具体数据处理操作借助Operator中的Function进行。StreamOperator提供了执行Function的环境，包括状态数据管理和处理Watermark、LatencyMarker等信息。

### 3.3

```java
public void close() throws Exception {
    super.close();
    functionsClosed = true;
    FunctionUtils.closeFunction(userFunction);
}
```

### 3.4

```java
public void dispose() throws Exception {
    super.dispose();
    if (!functionsClosed) {
        functionsClosed = true;
        FunctionUtils.closeFunction(userFunction);
    }
}
```



```java


@Override
public void snapshotState(StateSnapshotContext context) throws Exception {
    super.snapshotState(context);
    StreamingFunctionUtils.snapshotFunctionState(context, getOperatorStateBackend(), userFunction);
}

@Override
public void initializeState(StateInitializationContext context) throws Exception {
    super.initializeState(context);
    StreamingFunctionUtils.restoreFunctionState(context, userFunction);
}
```

## 4. OneInputStreamOperator

```java
public interface OneInputStreamOperator<IN, OUT> extends StreamOperator<OUT>, Input<IN> {
    @Override
    default void setKeyContextElement(StreamRecord<IN> record) throws Exception {
        setKeyContextElement1(record);
    }
}
```

## 5. TwoInputStreamOperator

```java
public interface TwoInputStreamOperator<IN1, IN2, OUT> extends StreamOperator<OUT> {
    // 处理到达第一个输入的元素 需要保证不会与算子的其他方法同时调用
    void processElement1(StreamRecord<IN1> element) throws Exception;
    // 处理到达第二个输入的元素 需要保证不会与算子的其他方法同时调用
    void processElement2(StreamRecord<IN2> element) throws Exception;
    // 处理到达第一个输入的 Watermark 需要保证不会与算子的其他方法同时调用
    void processWatermark1(Watermark mark) throws Exception;
    // 处理到达第二个输入的 Watermark 需要保证不会与算子的其他方法同时调用
    void processWatermark2(Watermark mark) throws Exception;
    // 处理到达第一个输入的 LatencyMarker 需要保证不会与算子的其他方法同时调用
    void processLatencyMarker1(LatencyMarker latencyMarker) throws Exception;
    // 处理到达第二个输入的 LatencyMarker 需要保证不会与算子的其他方法同时调用
    void processLatencyMarker2(LatencyMarker latencyMarker) throws Exception;
}
```



```java
public class StreamMap<IN, OUT> extends AbstractUdfStreamOperator<OUT, MapFunction<IN, OUT>>
          implements OneInputStreamOperator<IN, OUT> {
    private static final long serialVersionUID = 1L;
    public StreamMap(MapFunction<IN, OUT> mapper) {
        super(mapper);
        chainingStrategy = ChainingStrategy.ALWAYS;
    }

    @Override
    public void processElement(StreamRecord<IN> element) throws Exception {
        output.collect(element.replace(userFunction.map(element.getValue())));
    }
}
```
