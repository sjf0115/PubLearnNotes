https://zhuanlan.zhihu.com/p/463194259

本文基于 Flink 1.13.5 源码详细分析 MiniBatch 机制的核心实现，重点剖析 RowTimeMiniBatchAssignerOperator 和 ProcTimeMiniBatchAssignerOperator 两个关键算子。

## 1. MiniBatch 架构设计

Mini-Batch机制底层对应的优化器规则名为MiniBatchIntervalInferRule(代码略去)，产生的物理节点为StreamExecMiniBatchAssigner，直接附加在 Source 节点的后面。其 translateToPlanInternal() 方法的源码如下：
```java
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
```
> org.apache.flink.table.planner.plan.nodes.exec.stream.StreamExecMiniBatchAssigner

可见，根据作业时间语义的不同，产生的算子也不同(本质上都是 OneInputStreamOperator)：
- 处理时间语义: ProcTimeMiniBatchAssignerOperator
- 事件时间语义: RowTimeMiniBatchAssginerOperator

## 2. ProcTimeMiniBatchAssignerOperator

```java
public class ProcTimeMiniBatchAssignerOperator extends AbstractStreamOperator<RowData>
        implements OneInputStreamOperator<RowData, RowData>, ProcessingTimeCallback {

    //------------------------------------------------------------------------------------------------------------------
    // AbstractStreamOperator

    @Override
    public void open() throws Exception {
        ...
    }

    @Override
    public void close() throws Exception {
        ...
    }

    @Override
    public void processWatermark(Watermark mark) throws Exception {
        ...
    }

    //------------------------------------------------------------------------------------------------------------------
    // OneInputStreamOperator

    @Override
    public void processElement(StreamRecord<RowData> element) throws Exception {
        ...
    }

    //------------------------------------------------------------------------------------------------------------------
    // ProcessingTimeCallback

    @Override
    public void onProcessingTime(long timestamp) throws Exception {
        ...
    }
}
```
### 2.1 初始化

在初始化操作中
- Watermark 初始化：从0开始标识初始 Watermark
- 定时器策略：注册一个处理时间定时器，首次触发时间为当前时间加上间隔（intervalMs）。
- 监控设计：实时暴露 currentBatch 指标

```java
public void open() throws Exception {
    super.open();

    currentWatermark = 0;
    // 当前处理时间
    long now = getProcessingTimeService().getCurrentProcessingTime();
    // 注册处理时间定时器: 当前时间+微批时间间隔
    getProcessingTimeService().registerTimer(now + intervalMs, this);
    // 监控指标
    getRuntimeContext().getMetricGroup()
            .gauge("currentBatch", (Gauge<Long>) () -> currentWatermark);
}
```

### 2.2 数据驱动的批次推进

`processElement` 方法核心是数据驱动的批次推进：
- 对于每个到达的元素，获取当前处理时间 now。
- 计算当前元素所属的批次 currentBatch：`currentBatch = now - now % intervalMs`。
  - 实际上是将当前时间对齐到最近的间隔边界（向下取整）。
- 批次推进：如果计算出的所属批次 currentBatch 大于当前水印 currentWatermark，则更新当前水印为 currentBatch，并向下游发送一个水印（值为currentBatch）。
  - 不对数据做修改，仅控制水印
- 最后，将元素原样输出
  - 这里并没有给元素附加任何批次ID，而是通过水印来驱动批次划分。

```java
public void processElement(StreamRecord<RowData> element) throws Exception {
    // 当前处理时间
    long now = getProcessingTimeService().getCurrentProcessingTime();
    // 计算所属批次
    long currentBatch = now - now % intervalMs;
    // 水印推进条件
    if (currentBatch > currentWatermark) {
        currentWatermark = currentBatch;
        // 发送 Watermark
        output.emitWatermark(new Watermark(currentBatch));
    }
    // 发送元素
    output.collect(element);
}
```

### 2.3 定时器驱动的批次推进

`onProcessingTime` 方法的核心是定时器驱动的批次推进：
- 获取当前处理时间 now。
- 计算所属批次 currentBatch：`currentBatch = now - now % intervalMs`。
  - 实际上是将当前时间对齐到最近的间隔边界（向下取整）。
- 批次推进：如果计算出的所属批次 currentBatch 大于当前水印 currentWatermark，则更新当前水印为 currentBatch，并向下游发送一个水印（值为currentBatch）。
  - 不对数据做修改，仅控制水印
- 然后注册下一个定时器：当前批次的时间加上间隔（currentBatch + intervalMs）。

```java
public void onProcessingTime(long timestamp) throws Exception {
    // 当前处理时间
    long now = getProcessingTimeService().getCurrentProcessingTime();
    // 计算所属批次
    long currentBatch = now - now % intervalMs;
    if (currentBatch > currentWatermark) {
        currentWatermark = currentBatch;
        // 发送 Watermark
        output.emitWatermark(new Watermark(currentBatch));
    }
    getProcessingTimeService().registerTimer(currentBatch + intervalMs, this);
}
```

### 2.4 水印处理策略

`processWatermark` 方法的核心水印处理策略：
- 该算子会忽略上游传递过来的水印（因为处理时间与事件时间无关）
- 除了一个特例：当收到一个 Long.MAX_VALUE 的水印（表示输入结束）时，会将其转发给下游。

```java
public void processWatermark(Watermark mark) throws Exception {
    if (mark.getTimestamp() == Long.MAX_VALUE && currentWatermark != Long.MAX_VALUE) {
        currentWatermark = Long.MAX_VALUE;
        output.emitWatermark(mark);
    }
}
```

- 在Flink的流处理中，水印是用于推动事件时间进展的，但在这里被借用为处理时间下批次结束的信号。
- 下游算子收到水印时，会触发窗口计算（注意：这里的水印并不是事件时间水印，而是处理时间批次结束的信号）。下游算子需要能够区分事件时间水印和这种处理时间的水印吗？
实际上，在MiniBatch机制中，下游的聚合算子会使用水印作为触发计算的信号，不管这个水印是来自事件时间还是处理时间。但是，事件时间的MiniBatch会使用事件时间水印（由RowTimeMiniBatchAssignerOperator产生），而处理时间的MiniBatch则使用这个算子产生的水印。
重要：该算子产生的水印值等于批次结束的时间戳（对齐到intervalMs的整数倍）。例如，如果intervalMs=1000ms，那么水印值可能是0,1000,2000,...。注意，水印的含义是“所有小于该时间戳的批次都已经结束”，所以下游聚合算子会在收到水印时触发上一个批次的计算。


## 3. RowTimeMiniBatchAssginerOperator

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
