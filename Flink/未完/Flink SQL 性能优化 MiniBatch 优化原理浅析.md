https://blog.csdn.net/nazeniwaresakini/article/details/115235119

## 1. MapBundleOperator

```java
public abstract class AbstractMapBundleOperator<K, V, IN, OUT> extends AbstractStreamOperator<OUT>
        implements OneInputStreamOperator<IN, OUT>, BundleTriggerCallback {
          ...
    AbstractMapBundleOperator(MapBundleFunction<K, V, IN, OUT> function, BundleTrigger<IN> bundleTrigger) {
        chainingStrategy = ChainingStrategy.ALWAYS;
        this.function = checkNotNull(function, "function is null");
        this.bundleTrigger = checkNotNull(bundleTrigger, "bundleTrigger is null");
    }
}
```
在 open 函数完成初始化：
```java
super.open();
// 处理接收到的元素
function.open(new ExecutionContextImpl(this, getRuntimeContext()));
this.numOfElements = 0;
// 用于输出
this.collector = new StreamRecordCollector<>(output);
// 存储一批次数据
this.bundle = new HashMap<>();
// 触发器
bundleTrigger.registerCallback(this);
bundleTrigger.reset();
```
在 processElement 方法中处理每一条到达的数据记录：
```java
// 数据记录值
final IN input = element.getValue();
// 获取批次Key
final K bundleKey = getKey(input);
// 获取批次Key对应的批次值
final V bundleValue = bundle.get(bundleKey);
// 将一个数据记录添加到批次中并返回一个新的批次值
final V newBundleValue = function.addInput(bundleValue, input);
// 更新批次
bundle.put(bundleKey, newBundleValue);
// 数据记录数加1
numOfElements++;
// 是否触发
bundleTrigger.onElement(input);
```
当一个批次结束的时候调用 finishBundle：
```java
if (bundle != null && !bundle.isEmpty()) {
    numOfElements = 0;
    function.finishBundle(bundle, collector);
    bundle.clear();
}
bundleTrigger.reset();
```

```java
public abstract class AbstractMapBundleOperator<K, V, IN, OUT> extends AbstractStreamOperator<OUT> implements OneInputStreamOperator<IN, OUT>, BundleTriggerCallback {
    private static final long serialVersionUID = 5081841938324118594L;
    private transient Map<K, V> bundle;
    private final BundleTrigger<IN> bundleTrigger;
    private final MapBundleFunction<K, V, IN, OUT> function;
    private transient Collector<OUT> collector;
    private transient int numOfElements = 0;

    AbstractMapBundleOperator(MapBundleFunction<K, V, IN, OUT> function, BundleTrigger<IN> bundleTrigger) {
        this.chainingStrategy = ChainingStrategy.ALWAYS;
        this.function = (MapBundleFunction)Preconditions.checkNotNull(function, "function is null");
        this.bundleTrigger = (BundleTrigger)Preconditions.checkNotNull(bundleTrigger, "bundleTrigger is null");
    }

    public void open() throws Exception {
        super.open();
        this.function.open(new ExecutionContextImpl(this, this.getRuntimeContext()));
        this.numOfElements = 0;
        this.collector = new StreamRecordCollector(this.output);
        this.bundle = new HashMap();
        this.bundleTrigger.registerCallback(this);
        this.bundleTrigger.reset();
        LOG.info("BundleOperator's trigger info: " + this.bundleTrigger.explain());
        this.getRuntimeContext().getMetricGroup().gauge("bundleSize", () -> {
            return this.numOfElements;
        });
        this.getRuntimeContext().getMetricGroup().gauge("bundleRatio", () -> {
            int numOfKeys = this.bundle.size();
            return numOfKeys == 0 ? 0.0D : 1.0D * (double)this.numOfElements / (double)numOfKeys;
        });
    }

    public void processElement(StreamRecord<IN> element) throws Exception {
        IN input = element.getValue();
        K bundleKey = this.getKey(input);
        V bundleValue = this.bundle.get(bundleKey);
        V newBundleValue = this.function.addInput(bundleValue, input);
        this.bundle.put(bundleKey, newBundleValue);
        ++this.numOfElements;
        this.bundleTrigger.onElement(input);
    }

    protected abstract K getKey(IN var1) throws Exception;

    public void finishBundle() throws Exception {
        if (!this.bundle.isEmpty()) {
            this.numOfElements = 0;
            this.function.finishBundle(this.bundle, this.collector);
            this.bundle.clear();
        }

        this.bundleTrigger.reset();
    }

    public void processWatermark(Watermark mark) throws Exception {
        this.finishBundle();
        super.processWatermark(mark);
    }

    public void prepareSnapshotPreBarrier(long checkpointId) throws Exception {
        this.finishBundle();
    }

    public void close() throws Exception {
        boolean var11 = false;

        try {
            var11 = true;
            this.finishBundle();
            var11 = false;
        } finally {
            if (var11) {
                Object exception = null;

                try {
                    super.close();
                    if (this.function != null) {
                        FunctionUtils.closeFunction(this.function);
                    }
                } catch (InterruptedException var12) {
                    exception = var12;
                    Thread.currentThread().interrupt();
                } catch (Exception var13) {
                    exception = var13;
                }

                if (exception != null) {
                    LOG.warn("Errors occurred while closing the BundleOperator.", (Throwable)exception);
                }

            }
        }

        Object exception = null;

        try {
            super.close();
            if (this.function != null) {
                FunctionUtils.closeFunction(this.function);
            }
        } catch (InterruptedException var14) {
            exception = var14;
            Thread.currentThread().interrupt();
        } catch (Exception var15) {
            exception = var15;
        }

        if (exception != null) {
            LOG.warn("Errors occurred while closing the BundleOperator.", (Throwable)exception);
        }

    }
}
```

```java
public class MapBundleOperator<K, V, IN, OUT> extends AbstractMapBundleOperator<K, V, IN, OUT> {
    private static final long serialVersionUID = 1L;
    private final KeySelector<IN, K> keySelector;

    public MapBundleOperator(MapBundleFunction<K, V, IN, OUT> function, BundleTrigger<IN> bundleTrigger, KeySelector<IN, K> keySelector) {
        super(function, bundleTrigger);
        this.keySelector = keySelector;
    }

    protected K getKey(IN input) throws Exception {
        return this.keySelector.getKey(input);
    }
}
```

```java
public class KeyedMapBundleOperator<K, V, IN, OUT> extends AbstractMapBundleOperator<K, V, IN, OUT> {
    private static final long serialVersionUID = 1L;

    public KeyedMapBundleOperator(MapBundleFunction<K, V, IN, OUT> function, BundleTrigger<IN> bundleTrigger) {
        super(function, bundleTrigger);
    }

    protected K getKey(IN input) throws Exception {
        return this.getCurrentKey();
    }
}
```
> org.apache.flink.table.runtime.operators.bundle.KeyedMapBundleOperator


## 2. MapBundleFunction

```java
public abstract class MapBundleFunction<K, V, IN, OUT> implements Function {
    private static final long serialVersionUID = -6672219582127325882L;
    protected transient ExecutionContext ctx;
    public void open(ExecutionContext ctx) throws Exception {
        this.ctx = Preconditions.checkNotNull(ctx);
    }
    // 添加新输入到指定的批次值中并返回一个新的批次值
    public abstract V addInput(@Nullable V value, IN input) throws Exception;
    // 当完成一个批次的时候调用 将一个批次转换为0个,1个或者多个输出数据记录
    public abstract void finishBundle(Map<K, V> buffer, Collector<OUT> out) throws Exception;
    public void close() throws Exception {}
}
```

## 3. 批次结束触发器

### 3.1 BundleTriggerCallback

```java
public interface BundleTriggerCallback {
    // 当触发器触发时结束当前批次并开始一个新的批次
    void finishBundle() throws Exception;
}
```
### 3.2 BundleTrigger

```java
public interface BundleTrigger<T> extends Serializable {
    // 如果结束攒批注册一个回调函数
    void registerCallback(BundleTriggerCallback callback);
    // 每个元素到达时调用该函数 如果决定结束攒批则需要调用 BundleTriggerCallback 的 finishBundle 函数
    void onElement(final T element) throws Exception;
    // 重置触发器
    void reset();
    String explain();
}
```

```java
public class CountBundleTrigger<T> implements BundleTrigger<T> {
    private static final long serialVersionUID = -3640028071558094814L;
    private final long maxCount;
    private transient BundleTriggerCallback callback;
    private transient long count = 0L;

    public CountBundleTrigger(long maxCount) {
        Preconditions.checkArgument(maxCount > 0L, "maxCount must be greater than 0");
        this.maxCount = maxCount;
    }

    public void registerCallback(BundleTriggerCallback callback) {
        this.callback = (BundleTriggerCallback)Preconditions.checkNotNull(callback, "callback is null");
    }

    public void onElement(T element) throws Exception {
        ++this.count;
        if (this.count >= this.maxCount) {
            this.callback.finishBundle();
            this.reset();
        }

    }

    public void reset() {
        this.count = 0L;
    }

    public String explain() {
        return "CountBundleTrigger with size " + this.maxCount;
    }
}
```

## 4. MiniBatchGroupAggFunction

```java
public class MiniBatchGroupAggFunction extends MapBundleFunction<RowData, List<RowData>, RowData, RowData> {
    @Override
    public List<RowData> addInput(@Nullable List<RowData> value, RowData input) throws Exception {
        return null;
    }

    @Override
    public void finishBundle(Map<RowData, List<RowData>> buffer, Collector<RowData> out) throws Exception {

    }
}
```


```java
public class MiniBatchGroupAggFunction extends MapBundleFunction<RowData, List<RowData>, RowData, RowData> {
    private static final long serialVersionUID = 7455939331036508477L;
    private final GeneratedAggsHandleFunction genAggsHandler;
    private final GeneratedRecordEqualiser genRecordEqualiser;
    private final LogicalType[] accTypes;
    private final RowType inputType;
    private final RecordCounter recordCounter;
    private final boolean generateUpdateBefore;
    private final long stateRetentionTime;
    private transient JoinedRowData resultRow = new JoinedRowData();
    private transient TypeSerializer<RowData> inputRowSerializer;
    private transient AggsHandleFunction function = null;
    private transient RecordEqualiser equaliser = null;
    private transient ValueState<RowData> accState = null;

    public MiniBatchGroupAggFunction(GeneratedAggsHandleFunction genAggsHandler, GeneratedRecordEqualiser genRecordEqualiser, LogicalType[] accTypes, RowType inputType, int indexOfCountStar, boolean generateUpdateBefore, long stateRetentionTime) {
        this.genAggsHandler = genAggsHandler;
        this.genRecordEqualiser = genRecordEqualiser;
        this.recordCounter = RecordCounter.of(indexOfCountStar);
        this.accTypes = accTypes;
        this.inputType = inputType;
        this.generateUpdateBefore = generateUpdateBefore;
        this.stateRetentionTime = stateRetentionTime;
    }

    public void open(ExecutionContext ctx) throws Exception {
        super.open(ctx);
        StateTtlConfig ttlConfig = StateConfigUtil.createTtlConfig(this.stateRetentionTime);
        this.function = (AggsHandleFunction)this.genAggsHandler.newInstance(ctx.getRuntimeContext().getUserCodeClassLoader());
        this.function.open(new PerKeyStateDataViewStore(ctx.getRuntimeContext(), ttlConfig));
        this.equaliser = (RecordEqualiser)this.genRecordEqualiser.newInstance(ctx.getRuntimeContext().getUserCodeClassLoader());
        InternalTypeInfo<RowData> accTypeInfo = InternalTypeInfo.ofFields(this.accTypes);
        ValueStateDescriptor<RowData> accDesc = new ValueStateDescriptor("accState", accTypeInfo);
        if (ttlConfig.isEnabled()) {
            accDesc.enableTimeToLive(ttlConfig);
        }

        this.accState = ctx.getRuntimeContext().getState(accDesc);
        this.inputRowSerializer = InternalSerializers.create(this.inputType);
        this.resultRow = new JoinedRowData();
    }

    public List<RowData> addInput(@Nullable List<RowData> value, RowData input) throws Exception {
        List<RowData> bufferedRows = value;
        if (value == null) {
            bufferedRows = new ArrayList();
        }

        ((List)bufferedRows).add(this.inputRowSerializer.copy(input));
        return (List)bufferedRows;
    }

    public void finishBundle(Map<RowData, List<RowData>> buffer, Collector<RowData> out) throws Exception {
        Iterator var3 = buffer.entrySet().iterator();

        while(var3.hasNext()) {
            Entry<RowData, List<RowData>> entry = (Entry)var3.next();
            RowData currentKey = (RowData)entry.getKey();
            List<RowData> inputRows = (List)entry.getValue();
            boolean firstRow = false;
            this.ctx.setCurrentKey(currentKey);
            RowData acc = (RowData)this.accState.value();
            RowData newAggValue;
            if (acc == null) {
                Iterator inputIter = inputRows.iterator();

                while(inputIter.hasNext()) {
                    newAggValue = (RowData)inputIter.next();
                    if (!RowDataUtil.isRetractMsg(newAggValue)) {
                        break;
                    }

                    inputIter.remove();
                }

                if (inputRows.isEmpty()) {
                    return;
                }

                acc = this.function.createAccumulators();
                firstRow = true;
            }

            this.function.setAccumulators(acc);
            RowData prevAggValue = this.function.getValue();
            Iterator var13 = inputRows.iterator();

            while(var13.hasNext()) {
                RowData input = (RowData)var13.next();
                if (RowDataUtil.isAccumulateMsg(input)) {
                    this.function.accumulate(input);
                } else {
                    this.function.retract(input);
                }
            }

            newAggValue = this.function.getValue();
            acc = this.function.getAccumulators();
            if (!this.recordCounter.recordCountIsZero(acc)) {
                this.accState.update(acc);
                if (!firstRow) {
                    if (!this.equaliser.equals(prevAggValue, newAggValue)) {
                        if (this.generateUpdateBefore) {
                            this.resultRow.replace(currentKey, prevAggValue).setRowKind(RowKind.UPDATE_BEFORE);
                            out.collect(this.resultRow);
                        }

                        this.resultRow.replace(currentKey, newAggValue).setRowKind(RowKind.UPDATE_AFTER);
                        out.collect(this.resultRow);
                    }
                } else {
                    this.resultRow.replace(currentKey, newAggValue).setRowKind(RowKind.INSERT);
                    out.collect(this.resultRow);
                }
            } else {
                if (!firstRow) {
                    this.resultRow.replace(currentKey, prevAggValue).setRowKind(RowKind.DELETE);
                    out.collect(this.resultRow);
                }

                this.accState.clear();
                this.function.cleanup();
            }
        }

    }

    public void close() throws Exception {
        if (this.function != null) {
            this.function.close();
        }
    }
}
```
