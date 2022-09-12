
```java
public interface StreamOperator<OUT> extends CheckpointListener, KeyContext, Disposable, Serializable {
    void open() throws Exception;
    void close() throws Exception;
    @Override
    void dispose() throws Exception;

    // 状态快照
    void prepareSnapshotPreBarrier(long checkpointId) throws Exception;
    OperatorSnapshotFutures snapshotState(
            long checkpointId,
            long timestamp,
            CheckpointOptions checkpointOptions,
            CheckpointStreamFactory storageLocation)
            throws Exception;

    void initializeState(StreamTaskStateInitializer streamTaskStateManager) throws Exception;

    void setKeyContextElement1(StreamRecord<?> record) throws Exception;
    void setKeyContextElement2(StreamRecord<?> record) throws Exception;
    MetricGroup getMetricGroup();
    OperatorID getOperatorID();
}
```

```java
public interface OneInputStreamOperator<IN, OUT> extends StreamOperator<OUT>, Input<IN> {
    @Override
    default void setKeyContextElement(StreamRecord<IN> record) throws Exception {
        setKeyContextElement1(record);
    }
}
```


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


AbstractUdfStreamOperator 作为具有用户自定义函数算子的基类，主要用来处理作为算子生命周期的一部分的用户自定义函数的 open 和 close 方法：
```java
public abstract class AbstractUdfStreamOperator<OUT, F extends Function>
        extends AbstractStreamOperator<OUT> implements OutputTypeConfigurable<OUT> {
    private static final long serialVersionUID = 1L;
    // 用户自定义函数
    protected final F userFunction;
    // 避免在 close() 和 dispose() 中重复调用 function.close() 的标记
    private transient boolean functionsClosed = false;

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
算子生命周期处理：
```java
@Override
public void setup(
        StreamTask<?, ?> containingTask,
        StreamConfig config,
        Output<StreamRecord<OUT>> output) {
    super.setup(containingTask, config, output);
    FunctionUtils.setFunctionRuntimeContext(userFunction, getRuntimeContext());
}

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

@Override
public void open() throws Exception {
    super.open();
    FunctionUtils.openFunction(userFunction, new Configuration());
}

@Override
public void close() throws Exception {
    super.close();
    functionsClosed = true;
    FunctionUtils.closeFunction(userFunction);
}

@Override
public void dispose() throws Exception {
    super.dispose();
    if (!functionsClosed) {
        functionsClosed = true;
        FunctionUtils.closeFunction(userFunction);
    }
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
