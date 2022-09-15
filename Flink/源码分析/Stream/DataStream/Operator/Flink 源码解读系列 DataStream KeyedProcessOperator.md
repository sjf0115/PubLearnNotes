
```java
public class KeyedProcessOperator<K, IN, OUT>
        extends AbstractUdfStreamOperator<OUT, KeyedProcessFunction<K, IN, OUT>>
        implements OneInputStreamOperator<IN, OUT>, Triggerable<K, VoidNamespace> {
}
```
继承自 AbstractUdfStreamOperator，同时实现了 OneInputStreamOperator 和 Triggerable 接口。

## 1. Triggerable

```java
@Override
public void onEventTime(InternalTimer<K, VoidNamespace> timer) throws Exception {
    collector.setAbsoluteTimestamp(timer.getTimestamp());
    invokeUserFunction(TimeDomain.EVENT_TIME, timer);
}

@Override
public void onProcessingTime(InternalTimer<K, VoidNamespace> timer) throws Exception {
    collector.eraseTimestamp();
    invokeUserFunction(TimeDomain.PROCESSING_TIME, timer);
}
```

## 2. OneInputStreamOperator

实际上会调用 KeyedProcessFunction 来处理到达的元素 StreamRecord：
```java
@Override
public void processElement(StreamRecord<IN> element) throws Exception {
    collector.setTimestamp(element);
    context.element = element;
    userFunction.processElement(element.getValue(), context, collector);
    context.element = null;
}
```

## 3. AbstractUdfStreamOperator

完成 KeyedProcessOperator 的初始化：
```java
@Override
public void open() throws Exception {
    super.open();
    collector = new TimestampedCollector<>(output);
    // 初始化 InternalTimerService
    InternalTimerService<VoidNamespace> internalTimerService =
            getInternalTimerService("user-timers", VoidNamespaceSerializer.INSTANCE, this);
    // 创建 TimerService 实例
    TimerService timerService = new SimpleTimerService(internalTimerService);
    // 创建 ContextImpl
    context = new ContextImpl(userFunction, timerService);
    // 创建 OnTimerContextImpl
    onTimerContext = new OnTimerContextImpl(userFunction, timerService);
}
```

## 4. KeyedProcessFunction#Context

在讲 KeyedProcessFunction 如何使用的时候，我们提到通过其的内部抽象类 Context 可以获取到当前的时间戳，也可以获取 TimeService 来查询当前时间或者注册定时器，以及可以将数据发送到侧输出流（side output）：
```java
public abstract class Context {
    public abstract Long timestamp();
    public abstract TimerService timerService();
    public abstract <X> void output(OutputTag<X> outputTag, X value);
    public abstract K getCurrentKey();
}
```
KeyedProcessFunction 中只是提供的接口并没有实现，实际是在 KeyedProcessOperator#ContextImpl 中实现的：
```java
private class ContextImpl extends KeyedProcessFunction<K, IN, OUT>.Context {
    private final TimerService timerService;
    private StreamRecord<IN> element;
    // 构造器
    ContextImpl(KeyedProcessFunction<K, IN, OUT> function, TimerService timerService) {
        function.super();
        this.timerService = checkNotNull(timerService);
    }
    // 时间戳
    @Override
    public Long timestamp() {
        checkState(element != null);
        // 判断元素是否分配了时间戳 如果分配了直接返回否则返回null
        if (element.hasTimestamp()) {
            return element.getTimestamp();
        } else {
            return null;
        }
    }
    // 定时器服务
    @Override
    public TimerService timerService() {
        // 直接返回构造器传递进来的 timerService
        return timerService;
    }
    // 侧输出
    @Override
    public <X> void output(OutputTag<X> outputTag, X value) {
        if (outputTag == null) {
            throw new IllegalArgumentException("OutputTag must not be null.");
        }
        // 指定 OutputTag 输出
        output.collect(outputTag, new StreamRecord<>(value, element.getTimestamp()));
    }
    // 当前Key
    @Override
    @SuppressWarnings("unchecked")
    public K getCurrentKey() {
        return (K) KeyedProcessOperator.this.getCurrentKey();
    }
}
```
