https://blog.csdn.net/nazeniwaresakini/article/details/115235119


## 1. MapBundleFunction

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

## 2. 批次结束触发器

### 2.1 BundleTriggerCallback

```java
public interface BundleTriggerCallback {
    // 当触发器触发时结束当前批次并开始一个新的批次
    void finishBundle() throws Exception;
}
```
### 2.2 BundleTrigger

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



## 4.


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
