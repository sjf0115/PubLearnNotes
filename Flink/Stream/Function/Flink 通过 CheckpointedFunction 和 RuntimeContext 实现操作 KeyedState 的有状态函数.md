## 3. Keyed 状态

可以通过 RuntimeContext 方法访问 KeyedState：
```java
public class CountPerKeyFunction<T> extends RichMapFunction<T, T> {
    private ValueState<Long> count;

    public void open(Configuration cfg) throws Exception {
    count = getRuntimeContext().getState(new ValueStateDescriptor<>("myCount", Long.class));
    }

    public T map(T value) throws Exception {
    Long current = count.value();
    count.update(current == null ? 1L : current + 1);

    return value;
    }
}
```
