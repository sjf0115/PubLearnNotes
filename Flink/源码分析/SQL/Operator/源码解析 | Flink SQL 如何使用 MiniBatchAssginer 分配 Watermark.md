https://zhuanlan.zhihu.com/p/463194259

本文基于 Flink 1.13.5 源码详细分析 MiniBatch 机制的核心实现，重点剖析 RowTimeMiniBatchAssignerOperator 和 ProcTimeMiniBatchAssignerOperator 两个关键算子。

## 1. MiniBatch 架构设计
在 Flink SQL 优化器中，MiniBatch 通过物理计划节点 StreamExecMiniBatchAssigner 实现：
```java
public class StreamExecMiniBatchAssigner extends ExecNodeBase<RowData> implements StreamExecNode<RowData>, SingleTransformationTranslator<RowData> {
    public static final String FIELD_NAME_MINI_BATCH_INTERVAL = "miniBatchInterval";
    @JsonProperty("miniBatchInterval")
    private final MiniBatchInterval miniBatchInterval;

    public StreamExecMiniBatchAssigner(MiniBatchInterval miniBatchInterval, InputProperty inputProperty, RowType outputType, String description) {
        this(miniBatchInterval, getNewNodeId(), Collections.singletonList(inputProperty), outputType, description);
    }

    @JsonCreator
    public StreamExecMiniBatchAssigner(@JsonProperty("miniBatchInterval") MiniBatchInterval miniBatchInterval, @JsonProperty("id") int id, @JsonProperty("inputProperties") List<InputProperty> inputProperties, @JsonProperty("outputType") RowType outputType, @JsonProperty("description") String description) {
        super(id, inputProperties, outputType, description);
        this.miniBatchInterval = (MiniBatchInterval)Preconditions.checkNotNull(miniBatchInterval);
    }

    protected Transformation<RowData> translateToPlanInternal(PlannerBase planner) {
        Transformation<RowData> inputTransform = ((ExecEdge)this.getInputEdges().get(0)).translateToPlan(planner);
        Object operator;
        if (this.miniBatchInterval.getMode() == MiniBatchMode.ProcTime) {
            operator = new ProcTimeMiniBatchAssignerOperator(this.miniBatchInterval.getInterval());
        } else {
            if (this.miniBatchInterval.getMode() != MiniBatchMode.RowTime) {
                throw new TableException(String.format("MiniBatchAssigner shouldn't be in %s mode this is a bug, please file an issue.", this.miniBatchInterval.getMode()));
            }

            operator = new RowTimeMiniBatchAssginerOperator(this.miniBatchInterval.getInterval());
        }

        return new OneInputTransformation(inputTransform, this.getDescription(), (OneInputStreamOperator)operator, InternalTypeInfo.of(this.getOutputType()), inputTransform.getParallelism());
    }
}
```
> org.apache.flink.table.planner.plan.nodes.exec.stream.StreamExecMiniBatchAssigner





```java
public class RowTimeMiniBatchAssginerOperator extends AbstractStreamOperator<RowData> implements OneInputStreamOperator<RowData, RowData> {

    private static final long serialVersionUID = 1L;

    /** The event-time interval for emitting watermarks. */
    private final long minibatchInterval;

    /** Current watermark of this operator, but may not be emitted. */
    private transient long currentWatermark;

    /** The next watermark to be emitted. */
    private transient long nextWatermark;

    public RowTimeMiniBatchAssginerOperator(long minibatchInterval) {
        this.minibatchInterval = minibatchInterval;
    }

    @Override
    public void open() throws Exception {
        super.open();
        currentWatermark = 0;
        nextWatermark = getMiniBatchStart(currentWatermark, minibatchInterval) + minibatchInterval - 1;
    }

    @Override
    public void processElement(StreamRecord<RowData> element) throws Exception {
        // forward records
        output.collect(element);
    }

    @Override
    public void processWatermark(Watermark mark) throws Exception {
        // if we receive a Long.MAX_VALUE watermark we forward it since it is used
        // to signal the end of input and to not block watermark progress downstream
        if (mark.getTimestamp() == Long.MAX_VALUE && currentWatermark != Long.MAX_VALUE) {
            currentWatermark = Long.MAX_VALUE;
            output.emitWatermark(mark);
            return;
        }

        currentWatermark = Math.max(currentWatermark, mark.getTimestamp());
        if (currentWatermark >= nextWatermark) {
            advanceWatermark();
        }
    }

    private void advanceWatermark() {
        output.emitWatermark(new Watermark(currentWatermark));
        long start = getMiniBatchStart(currentWatermark, minibatchInterval);
        long end = start + minibatchInterval - 1;
        nextWatermark = end > currentWatermark ? end : end + minibatchInterval;
    }

    @Override
    public void close() throws Exception {
        super.close();

        // emit the buffered watermark
        advanceWatermark();
    }

    // ------------------------------------------------------------------------
    //  Utilities
    // ------------------------------------------------------------------------
    /** Method to get the mini-batch start for a watermark. */
    private static long getMiniBatchStart(long watermark, long interval) {
        return watermark - (watermark + interval) % interval;
    }
}
```
