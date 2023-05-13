


## 3. Descriptor

对于可供flink application直接使用的state，在获取对应state时需要使用对应的Descriptor来描述State，比如ValueStateDescriptor、MapStateDescriptor。下面我们首先看下Descriptor的抽象基类 StateDescriptor:
```java
public abstract class StateDescriptor<S extends State, T> implements Serializable {
    // 所支持的 State 类型
    public enum Type {
        @Deprecated
        UNKNOWN,
        VALUE,
        LIST,
        REDUCING,
        FOLDING,
        AGGREGATING,
        MAP
    }
}
```
S 是 StateDescriptor 所支持的 State 类型，必须是 State 的子类，T 是 value 的类型。

### 3.1 ValueStateDescriptor

ValueStateDescriptor 是 ValueState 所对应的 StateDescriptor。ValueStateDescriptor 只是指定了构造方法以及对应的 State 类型，其它默认都继承自 StateDescriptor：

```java
public class ValueStateDescriptor<T> extends StateDescriptor<ValueState<T>, T> {
    public ValueStateDescriptor(String name, Class<T> typeClass) {
        super(name, typeClass, null);
    }

    public ValueStateDescriptor(String name, TypeInformation<T> typeInfo) {
        super(name, typeInfo, null);
    }

    public ValueStateDescriptor(String name, TypeSerializer<T> typeSerializer) {
        super(name, typeSerializer, null);
    }

    @Override
    public Type getType() {
        // 对应 ValueState
        return Type.VALUE;
    }
}
```

### 3.2 AggregatingStateDescriptor

AggregatingStateDescriptor 是 AggregatingState 所对应的 StateDescriptor。对于 AggregatingState、FoldingState 这类聚合类 State，需要指定聚合的 Function 给对应的 Descriptor。
```java
public class AggregatingStateDescriptor<IN, ACC, OUT> extends StateDescriptor<AggregatingState<IN, OUT>, ACC> {

    private final AggregateFunction<IN, ACC, OUT> aggFunction;

    public AggregatingStateDescriptor(
            String name, AggregateFunction<IN, ACC, OUT> aggFunction, Class<ACC> stateType) {

        super(name, stateType, null);
        this.aggFunction = checkNotNull(aggFunction);
    }

    public AggregatingStateDescriptor(
            String name,
            AggregateFunction<IN, ACC, OUT> aggFunction,
            TypeInformation<ACC> stateType) {

        super(name, stateType, null);
        this.aggFunction = checkNotNull(aggFunction);
    }

    public AggregatingStateDescriptor(
            String name,
            AggregateFunction<IN, ACC, OUT> aggFunction,
            TypeSerializer<ACC> typeSerializer) {

        super(name, typeSerializer, null);
        this.aggFunction = checkNotNull(aggFunction);
    }

    public AggregateFunction<IN, ACC, OUT> getAggregateFunction() {
        return aggFunction;
    }

    @Override
    public Type getType() {
        //
        return Type.AGGREGATING;
    }
}
```
IN 代表输入到AggregatingState的数据类型。

OUT代表从AggregatingState中获取的数据类型。

ACC代表中间的聚合状态类型。

### 3.3

## 4. Operator State

我们知道Flink将state分为Keyed state和Operator state，而Operator state相较KeyedState简单很多。通过OperatorStateStore定义Operator state所支持的state类型，Operator state目前只提供了BroadcastState和ListState。

...
