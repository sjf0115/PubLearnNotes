Timer（定时器）是 Flink 中一种被严重低估的基础设施。很多开发者只在"超时检测"场景下才想到它，但实际上 Flink 的窗口触发、CEP 超时分支、AsyncIO 超时机制、甚至 Table API 的时间属性列，底层都依赖 Timer。深入掌握 Timer 的使用模式，能让你在面对 Window API 无法直接覆盖的复杂时间驱动逻辑时，游刃有余地用 KeyedProcessFunction 或自定义 Trigger 精确实现。

本文基于 Flink 1.13.6 版本，系统梳理 Timer 在 `KeyedProcessFunction`、`Window Trigger`、`KeyedCoProcessFunction` 等多个场景中的使用方式、底层原理与生产级最佳实践。

## 1. Timer 核心概念与底层原理

### 1.1 什么是 Timer

Timer 是 Flink 提供的定时回调机制：算子向运行时注册一个未来时间点，当时间推进到该时间点时，运行时回调算子的 `onTimer` 方法。Timer 有两种时间语义：
- **处理时间 Timer（Processing Time Timer）**：基于机器系统时钟，到达指定的绝对墙钟时间后触发
- **事件时间 Timer（Event Time Timer）**：基于 Watermark 推进，当 Watermark ≥ 注册时间时触发

### 1.2 Timer 的底层存储与去重

Timer 在 Flink 内部存储于 `InternalTimerService`，底层使用优先级队列（Heap 或 RocksDB）按时间排序：
```
┌──────────────────────────────────────┐
│         InternalTimerService          │
├──────────────────────────────────────┤
│  processingTimeTimersQueue (堆/RocksDB) │
│  eventTimeTimersQueue    (堆/RocksDB) │
└──────────────────────────────────────┘
```

关键特性——**同一 Key + 同一 Namespace + 同一时间戳，只存一个 Timer**：

```java
// InternalTimerServiceImpl.java
public void registerEventTimeTimer(N namespace, long time) {
    InternalTimer<K, N> timer = new TimerHeapInternalTimer<>(time, (K) keyContext.getCurrentKey(), namespace);
    // 如果队列中已有相同的 timer（key+namespace+time 三元组），不会重复插入
    eventTimeTimersQueue.add(timer);
}
```

这意味着：对相同 Key 注册 100 次 `registerEventTimeTimer(windowEnd)`，内部只存储和触发 1 次。这既是性能优势，也是设计 Timer 逻辑时必须理解的前提。

### 1.3 Timer 只能在 Keyed 上下文中使用

Timer 注册时会绑定当前处理元素的 Key，在触发时恢复该 Key 的上下文（切换 KeyedState 的 key namespace）。因此 Timer 只能在以下算子中使用：
- `KeyedProcessFunction`
- `KeyedCoProcessFunction`
- `KeyedBroadcastProcessFunction`
- `Trigger`（Window 的触发器，隐式运行在 KeyedStream 上）

无法在非 Keyed 的 `ProcessFunction` 中使用 Timer。

### 1.4 processElement 与 onTimer 的线程安全

`processElement` 和 `onTimer` 由同一个线程按顺序调用，**不存在并发问题**。但这也意味着 `onTimer` 的执行会阻塞数据处理——如果 `onTimer` 中执行了耗时操作（如同步 IO），会直接拖慢整条链路的吞吐。

## 2. KeyedProcessFunction 中使用 Timer

### 2.1 TimerService API

```java
public interface TimerService {
    // 获取当前处理时间（墙钟）
    long currentProcessingTime();
    // 获取当前事件时间 Watermark
    long currentWatermark();
    // 注册处理时间 Timer
    void registerProcessingTimeTimer(long time);
    // 注册事件时间 Timer
    void registerEventTimeTimer(long time);
    // 删除处理时间 Timer
    void deleteProcessingTimeTimer(long time);
    // 删除事件时间 Timer
    void deleteEventTimeTimer(long time);
}
```

使用入口：`ctx.timerService()`，在 `processElement` 和 `onTimer` 中均可调用。

### 2.2 场景一：自定义事件时间窗口聚合

当内置 Window API 无法满足需求（如需要自定义窗口分配逻辑、或需要在窗口内部做增量 + 全量混合计算）时，可以用 Timer 手动实现窗口语义：

```java
public class CustomWindowFunction extends KeyedProcessFunction<String, Event, Result> {
    private ValueState<Long> sumState;
    private ValueState<Boolean> timerRegistered;
    private static final long WINDOW_SIZE = 60_000L; // 1分钟

    @Override
    public void open(Configuration parameters) {
        sumState = getRuntimeContext().getState(
            new ValueStateDescriptor<>("sum", Long.class));
        timerRegistered = getRuntimeContext().getState(
            new ValueStateDescriptor<>("registered", Boolean.class));
    }

    @Override
    public void processElement(Event event, Context ctx, Collector<Result> out) throws Exception {
        // 累加
        long current = sumState.value() == null ? 0L : sumState.value();
        sumState.update(current + event.getValue());

        // 每个窗口只注册一次 Timer（利用 State 判断，也可利用 Timer 去重特性省略此判断）
        if (timerRegistered.value() == null || !timerRegistered.value()) {
            long windowEnd = getWindowEnd(ctx.timestamp(), WINDOW_SIZE);
            ctx.timerService().registerEventTimeTimer(windowEnd);
            timerRegistered.update(true);
        }
    }

    @Override
    public void onTimer(long timestamp, OnTimerContext ctx, Collector<Result> out) throws Exception {
        // 窗口触发：输出结果并清理状态
        out.collect(new Result(ctx.getCurrentKey(), sumState.value(), timestamp));
        sumState.clear();
        timerRegistered.clear();
    }

    private long getWindowEnd(long timestamp, long windowSize) {
        long start = timestamp - timestamp % windowSize;
        return start + windowSize;
    }
}
```

**要点**：
- 利用 Timer 去重特性，即使不用 `timerRegistered` 状态，多次注册同一个 `windowEnd` 也只会触发一次
- `onTimer` 中清理状态是必须的，否则状态会无限膨胀

### 2.3 场景二：超时检测（心跳/会话超时）

这是 Timer 最经典的使用场景——"如果某个 Key 在指定时间内没有新数据到达，则触发告警"：

```java
public class TimeoutDetector extends KeyedProcessFunction<String, Event, Alert> {
    private ValueState<Long> lastSeenTimer;
    private static final long TIMEOUT = 60_000L; // 1分钟超时

    @Override
    public void open(Configuration parameters) {
        lastSeenTimer = getRuntimeContext().getState(
            new ValueStateDescriptor<>("lastTimer", Long.class));
    }

    @Override
    public void processElement(Event event, Context ctx, Collector<Alert> out) throws Exception {
        // 每来一条数据，先删除旧的超时 Timer
        if (lastSeenTimer.value() != null) {
            ctx.timerService().deleteProcessingTimeTimer(lastSeenTimer.value());
        }
        // 注册新的超时 Timer
        long newTimeout = ctx.timerService().currentProcessingTime() + TIMEOUT;
        ctx.timerService().registerProcessingTimeTimer(newTimeout);
        lastSeenTimer.update(newTimeout);
    }

    @Override
    public void onTimer(long timestamp, OnTimerContext ctx, Collector<Alert> out) throws Exception {
        // 进入 onTimer 说明已超时
        out.collect(new Alert(ctx.getCurrentKey(), "Heartbeat timeout at " + timestamp));
        lastSeenTimer.clear();
    }
}
```
> 直播间超时下线

**要点**：
- 必须用 State 记录已注册 Timer 的时间，因为 Flink 不提供查询 Timer 注册状态的 API
- 删除旧 Timer + 注册新 Timer = "重置倒计时"语义
- 如果使用事件时间，要注意 Watermark 不推进时 Timer 不会触发

### 2.4 场景三：去抖动（Debounce）

"收到数据后不立即输出，等待 N 秒，如果期间有新数据则用新数据覆盖旧数据，N 秒后输出最新值"：

```java
public class DebounceFunction extends KeyedProcessFunction<String, Event, Event> {
    private ValueState<Event> pendingEvent;
    private ValueState<Long> timerTimestamp;
    private static final long DEBOUNCE_INTERVAL = 5_000L; // 5秒去抖

    @Override
    public void open(Configuration parameters) {
        pendingEvent = getRuntimeContext().getState(
            new ValueStateDescriptor<>("pending", Event.class));
        timerTimestamp = getRuntimeContext().getState(
            new ValueStateDescriptor<>("timer", Long.class));
    }

    @Override
    public void processElement(Event event, Context ctx, Collector<Event> out) throws Exception {
        // 保留最新的事件
        pendingEvent.update(event);

        // 如果已有 Timer，不重新注册（保持首次触发时间不变）
        // 如果需要"每次都重置倒计时"，则先 delete 再 register
        if (timerTimestamp.value() == null) {
            long fireTime = ctx.timerService().currentProcessingTime() + DEBOUNCE_INTERVAL;
            ctx.timerService().registerProcessingTimeTimer(fireTime);
            timerTimestamp.update(fireTime);
        }
    }

    @Override
    public void onTimer(long timestamp, OnTimerContext ctx, Collector<Event> out) throws Exception {
        // 去抖窗口结束，输出最新事件
        out.collect(pendingEvent.value());
        pendingEvent.clear();
        timerTimestamp.clear();
    }
}
```

### 2.5 场景四：周期性输出（固定频率采样）

"每隔 10 秒输出当前聚合状态的快照"——区别于窗口的"触发后清空"，这里是"触发后保留，继续累加"：

```java
public class PeriodicEmitter extends KeyedProcessFunction<String, Event, Snapshot> {
    private ValueState<Long> countState;
    private static final long EMIT_INTERVAL = 10_000L;

    @Override
    public void open(Configuration parameters) {
        countState = getRuntimeContext().getState(
            new ValueStateDescriptor<>("count", Long.class, 0L));
    }

    @Override
    public void processElement(Event event, Context ctx, Collector<Snapshot> out) throws Exception {
        countState.update(countState.value() + 1);
        // 首条数据时启动周期性 Timer
        if (countState.value() == 1) {
            long firstFire = ctx.timerService().currentProcessingTime() + EMIT_INTERVAL;
            ctx.timerService().registerProcessingTimeTimer(firstFire);
        }
    }

    @Override
    public void onTimer(long timestamp, OnTimerContext ctx, Collector<Snapshot> out) throws Exception {
        // 输出快照但不清空
        out.collect(new Snapshot(ctx.getCurrentKey(), countState.value(), timestamp));
        // 注册下一次 Timer，实现周期性触发
        ctx.timerService().registerProcessingTimeTimer(timestamp + EMIT_INTERVAL);
    }
}
```

**要点**：在 `onTimer` 中注册下一个 Timer 是实现周期性触发的唯一方式（Flink 没有原生的 "periodic timer" API）。

## 3. Window Trigger 中使用 Timer

### 3.1 Trigger 生命周期与 TriggerContext

Window 的 `Trigger` 决定了窗口何时触发计算。它通过 `TriggerContext` 访问 Timer：

```java
public abstract class Trigger<T, W extends Window> {
    // 每条数据到达时调用
    public abstract TriggerResult onElement(T element, long timestamp, W window, TriggerContext ctx);
    // 处理时间 Timer 触发时调用
    public abstract TriggerResult onProcessingTime(long time, W window, TriggerContext ctx);
    // 事件时间 Timer 触发时调用
    public abstract TriggerResult onEventTime(long time, W window, TriggerContext ctx);
    // 窗口清除时调用（清理 Timer 和状态）
    public abstract void clear(W window, TriggerContext ctx);
}

public interface TriggerContext {
    long getCurrentProcessingTime();
    long getCurrentWatermark();
    void registerProcessingTimeTimer(long time);
    void registerEventTimeTimer(long time);
    void deleteProcessingTimeTimer(long time);
    void deleteEventTimeTimer(long time);
    // 获取窗口级别的 PartitionedState
    <S extends State> S getPartitionedState(StateDescriptor<S, ?> stateDescriptor);
}
```

### 3.2 内置 EventTimeTrigger 源码解读

Flink 事件时间窗口默认使用的 `EventTimeTrigger`，核心逻辑极其简洁：

```java
public class EventTimeTrigger extends Trigger<Object, TimeWindow> {
    @Override
    public TriggerResult onElement(Object element, long timestamp, TimeWindow window, TriggerContext ctx) {
        if (window.maxTimestamp() <= ctx.getCurrentWatermark()) {
            // 窗口已经应该被触发（迟到数据场景）
            return TriggerResult.FIRE;
        } else {
            // 注册窗口结束时间的事件时间 Timer
            ctx.registerEventTimeTimer(window.maxTimestamp());
            return TriggerResult.CONTINUE;
        }
    }

    @Override
    public TriggerResult onEventTime(long time, TimeWindow window, TriggerContext ctx) {
        // 当 Watermark 推进到 window.maxTimestamp() 时触发
        return time == window.maxTimestamp() ? TriggerResult.FIRE : TriggerResult.CONTINUE;
    }

    @Override
    public TriggerResult onProcessingTime(long time, TimeWindow window, TriggerContext ctx) {
        return TriggerResult.CONTINUE;
    }

    @Override
    public void clear(TimeWindow window, TriggerContext ctx) {
        ctx.deleteEventTimeTimer(window.maxTimestamp());
    }
}
```

**设计要点**：
- `window.maxTimestamp()` = `windowEnd - 1`（窗口最大时间戳，区间左闭右开）
- 利用 Timer 去重——窗口内多条数据都调用 `registerEventTimeTimer(window.maxTimestamp())`，只注册一个 Timer
- `clear` 中删除 Timer，避免窗口被清除后 Timer 仍残留

### 3.3 内置 ProcessingTimeTrigger 源码解读

```java
public class ProcessingTimeTrigger extends Trigger<Object, TimeWindow> {
    @Override
    public TriggerResult onElement(Object element, long timestamp, TimeWindow window, TriggerContext ctx) {
        ctx.registerProcessingTimeTimer(window.maxTimestamp());
        return TriggerResult.CONTINUE;
    }

    @Override
    public TriggerResult onProcessingTime(long time, TimeWindow window, TriggerContext ctx) {
        return TriggerResult.FIRE;
    }

    @Override
    public TriggerResult onEventTime(long time, TimeWindow window, TriggerContext ctx) {
        return TriggerResult.CONTINUE;
    }

    @Override
    public void clear(TimeWindow window, TriggerContext ctx) {
        ctx.deleteProcessingTimeTimer(window.maxTimestamp());
    }
}
```

### 3.4 自定义 Trigger：提前触发 + 最终触发

业务场景：事件时间窗口 1 小时，但希望每 1 分钟提前输出一次中间结果，最终窗口关闭时输出最终结果：

```java
public class EarlyFiringTrigger extends Trigger<Object, TimeWindow> {
    private static final long EARLY_INTERVAL = 60_000L; // 每分钟提前触发

    // 用于记录下一次提前触发时间的状态
    private final StateDescriptor<ValueState<Long>, Long> nextFireDesc =
        new ValueStateDescriptor<>("next-fire", Long.class);

    @Override
    public TriggerResult onElement(Object element, long timestamp, TimeWindow window, TriggerContext ctx) throws Exception {
        // 注册窗口结束的最终 Timer
        ctx.registerEventTimeTimer(window.maxTimestamp());

        // 注册第一次提前触发的处理时间 Timer
        ValueState<Long> nextFireState = ctx.getPartitionedState(nextFireDesc);
        if (nextFireState.value() == null) {
            long firstFire = ctx.getCurrentProcessingTime() + EARLY_INTERVAL;
            ctx.registerProcessingTimeTimer(firstFire);
            nextFireState.update(firstFire);
        }
        return TriggerResult.CONTINUE;
    }

    @Override
    public TriggerResult onProcessingTime(long time, TimeWindow window, TriggerContext ctx) throws Exception {
        ValueState<Long> nextFireState = ctx.getPartitionedState(nextFireDesc);
        // 提前触发：输出但不清除窗口（FIRE 不 PURGE）
        long nextFire = time + EARLY_INTERVAL;
        ctx.registerProcessingTimeTimer(nextFire);
        nextFireState.update(nextFire);
        return TriggerResult.FIRE;
    }

    @Override
    public TriggerResult onEventTime(long time, TimeWindow window, TriggerContext ctx) throws Exception {
        if (time == window.maxTimestamp()) {
            // 窗口最终触发：输出并清除
            return TriggerResult.FIRE_AND_PURGE;
        }
        return TriggerResult.CONTINUE;
    }

    @Override
    public void clear(TimeWindow window, TriggerContext ctx) throws Exception {
        ctx.deleteEventTimeTimer(window.maxTimestamp());
        ValueState<Long> nextFireState = ctx.getPartitionedState(nextFireDesc);
        if (nextFireState.value() != null) {
            ctx.deleteProcessingTimeTimer(nextFireState.value());
        }
        nextFireState.clear();
    }
}
```

**要点**：
- `FIRE` = 触发窗口函数输出结果，但保留窗口状态（适合提前触发）
- `FIRE_AND_PURGE` = 触发并清除窗口状态（适合最终触发）
- `clear` 中必须清理所有注册过的 Timer，否则窗口销毁后 Timer 仍会触发导致 NPE

### 3.5 自定义 Trigger：会话超时自动关窗

业务场景：使用 GlobalWindows + 自定义 Trigger，实现"如果某个 Key 超过 30 秒无新数据，则触发并关闭当前窗口"：

```java
public class SessionTimeoutTrigger extends Trigger<Object, GlobalWindow> {
    private static final long SESSION_TIMEOUT = 30_000L;

    private final StateDescriptor<ValueState<Long>, Long> timerDesc =
        new ValueStateDescriptor<>("session-timer", Long.class);

    @Override
    public TriggerResult onElement(Object element, long timestamp, GlobalWindow window, TriggerContext ctx) throws Exception {
        ValueState<Long> timerState = ctx.getPartitionedState(timerDesc);
        // 删除旧的超时 Timer
        if (timerState.value() != null) {
            ctx.deleteProcessingTimeTimer(timerState.value());
        }
        // 注册新的超时 Timer
        long timeout = ctx.getCurrentProcessingTime() + SESSION_TIMEOUT;
        ctx.registerProcessingTimeTimer(timeout);
        timerState.update(timeout);
        return TriggerResult.CONTINUE;
    }

    @Override
    public TriggerResult onProcessingTime(long time, GlobalWindow window, TriggerContext ctx) throws Exception {
        // 超时触发，清除窗口
        return TriggerResult.FIRE_AND_PURGE;
    }

    @Override
    public TriggerResult onEventTime(long time, GlobalWindow window, TriggerContext ctx) {
        return TriggerResult.CONTINUE;
    }

    @Override
    public void clear(GlobalWindow window, TriggerContext ctx) throws Exception {
        ValueState<Long> timerState = ctx.getPartitionedState(timerDesc);
        if (timerState.value() != null) {
            ctx.deleteProcessingTimeTimer(timerState.value());
            timerState.clear();
        }
    }
}
```

## 4. KeyedCoProcessFunction 中使用 Timer

### 4.1 双流 Join 超时匹配

典型场景：订单流与支付流关联，如果订单在 15 分钟内没有匹配到支付，输出超时告警：

```java
public class OrderPaymentJoin extends KeyedCoProcessFunction<String, Order, Payment, JoinResult> {
    private ValueState<Order> orderState;
    private ValueState<Payment> paymentState;
    private ValueState<Long> timerState;
    private static final long MATCH_TIMEOUT = 15 * 60_000L;

    @Override
    public void open(Configuration parameters) {
        orderState = getRuntimeContext().getState(new ValueStateDescriptor<>("order", Order.class));
        paymentState = getRuntimeContext().getState(new ValueStateDescriptor<>("payment", Payment.class));
        timerState = getRuntimeContext().getState(new ValueStateDescriptor<>("timer", Long.class));
    }

    @Override
    public void processElement1(Order order, Context ctx, Collector<JoinResult> out) throws Exception {
        Payment payment = paymentState.value();
        if (payment != null) {
            // 已有匹配的支付，直接输出
            out.collect(new JoinResult(order, payment, "MATCHED"));
            paymentState.clear();
            deleteTimer(ctx);
        } else {
            // 暂存订单，注册超时 Timer
            orderState.update(order);
            long timeout = ctx.timerService().currentProcessingTime() + MATCH_TIMEOUT;
            ctx.timerService().registerProcessingTimeTimer(timeout);
            timerState.update(timeout);
        }
    }

    @Override
    public void processElement2(Payment payment, Context ctx, Collector<JoinResult> out) throws Exception {
        Order order = orderState.value();
        if (order != null) {
            out.collect(new JoinResult(order, payment, "MATCHED"));
            orderState.clear();
            deleteTimer(ctx);
        } else {
            paymentState.update(payment);
            long timeout = ctx.timerService().currentProcessingTime() + MATCH_TIMEOUT;
            ctx.timerService().registerProcessingTimeTimer(timeout);
            timerState.update(timeout);
        }
    }

    @Override
    public void onTimer(long timestamp, OnTimerContext ctx, Collector<JoinResult> out) throws Exception {
        if (orderState.value() != null) {
            out.collect(new JoinResult(orderState.value(), null, "TIMEOUT"));
            orderState.clear();
        }
        if (paymentState.value() != null) {
            out.collect(new JoinResult(null, paymentState.value(), "TIMEOUT"));
            paymentState.clear();
        }
        timerState.clear();
    }

    private void deleteTimer(Context ctx) throws Exception {
        if (timerState.value() != null) {
            ctx.timerService().deleteProcessingTimeTimer(timerState.value());
            timerState.clear();
        }
    }
}
```

## 5. 生产级最佳实践

### 5.1 利用 Timer 去重特性简化逻辑

由于同一 Key + 同一时间戳只存一个 Timer，很多场景下不需要用 State 判断"是否已经注册过"：

```java
// 不需要额外 State 判断，直接注册即可
ctx.timerService().registerEventTimeTimer(windowEnd);
```

但有一个前提：你注册的时间戳是固定的（如窗口结束时间）。如果每条数据注册不同的时间戳（如 `currentProcessingTime() + TIMEOUT`），则每条数据都会产生一个新 Timer，此时必须用 State 记录并 delete 旧 Timer。

### 5.2 避免 Timer 风暴

**问题**：数百万个 Key 的 Timer 都注册在整点（如每分钟的 :00 秒），导致瞬间触发海量 onTimer 调用，造成处理延迟甚至背压。

**解决方案**：给注册时间加一个基于 Key 的哈希偏移，把触发时间打散：

```java
long baseTime = getWindowEnd(ctx.timestamp(), WINDOW_SIZE);
// 基于 Key 的哈希值，在 [0, WINDOW_SIZE) 范围内打散
long jitter = Math.abs(ctx.getCurrentKey().hashCode() % WINDOW_SIZE);
// 控制在前后一定范围内
long jitteredTime = baseTime + (jitter % MAX_JITTER);
ctx.timerService().registerProcessingTimeTimer(jitteredTime);
```

### 5.3 Timer 与 Checkpoint/Savepoint 的交互

Timer 会随 Checkpoint/Savepoint 持久化，恢复时需注意：

| 场景 | 行为 |
|---|---|
| 处理时间 Timer 在恢复时已过期 | 恢复后**立即全部触发**，可能产生瞬时高负载 |
| 事件时间 Timer 在恢复时已过期 | 等待 Watermark 推进后才触发，相对平滑 |
| 从 Savepoint 恢复后修改了 Timer 逻辑 | 旧 Timer 仍会触发旧的 onTimer 代码路径，需做兼容处理 |

**建议**：对于处理时间 Timer，恢复后可能出现大量积压 Timer 同时触发的情况，建议在 `onTimer` 中加入限流逻辑或在恢复后设置 warm-up 期。

### 5.4 Timer 状态膨胀的监控与治理

Timer 本身占用 KeyedState，当 Key 基数极大且每个 Key 都持有活跃 Timer 时，状态量不可忽视。

**监控指标**：
- `numTimers`（自定义 Metric）：可在 `open` 中注册 Gauge，统计当前 Timer 数量
- Checkpoint Size：如果 Checkpoint 大小异常增长，排查 Timer 是否过多
- RocksDB 的 `estimate-num-keys`：观察 Timer 相关 Column Family 的 Key 数量

**治理手段**：
- 确保 `onTimer` 中清理不再需要的 Timer（`delete` 或不再注册下一个）
- 对于"一次性"Timer，触发后自动清除，无需额外处理
- 对于"周期性"Timer，确保 Key 不活跃后停止注册下一个周期

### 5.5 有限流场景的特殊行为

在有限流（Bounded Stream）或批处理模式下：
- **事件时间 Timer**：作业结束时 Flink 会推送 `Long.MAX_VALUE` 的 Watermark，所有未触发的事件时间 Timer 都会被触发
- **处理时间 Timer**：作业结束时 **不会触发**未到期的处理时间 Timer——数据会丢失

因此，在有限流场景下优先使用事件时间 Timer。

### 5.6 无 Key 场景的处理方式

如果业务需要在无 Key 流上使用 Timer：

| 需求 | 方案 |
|---|---|
| Timer 逻辑与特定字段无关，每条数据独立 | 用数据中的唯一 ID（如 UUID）作为 Key 进行 keyBy |
| 全局共享一个 Timer（全局聚合） | 用常量 Key 进行 keyBy，并将算子并行度设为 1 |

注意：用于 keyBy 的字段必须存在于数据中，不能在 keyBy lambda 内部生成随机值（否则恢复时 Key 不一致）。

## 6. 常见陷阱与排查

### 6.1 Timer 注册了但不触发

| 可能原因 | 排查方法 |
|---|---|
| 事件时间 Timer 但 Watermark 不推进 | 检查数据源是否有 idle partition，使用 `withIdleness` 配置 |
| 注册时间在 `currentWatermark` 之前 | 打印注册时间与当前 Watermark，确认 Timer 注册在未来 |
| 上游任务背压导致 Watermark 无法推进 | 查看 Web UI 的背压指标 |
| 并行度修改导致 Key 分布变化 | 确认 Savepoint 恢复后 Key 是否正确分配到对应 SubTask |

### 6.2 onTimer 中访问不到预期 State

```java
@Override
public void onTimer(long timestamp, OnTimerContext ctx, Collector<Result> out) throws Exception {
    // 此时 ctx.getCurrentKey() 返回的是注册该 Timer 时的 Key
    // KeyedState 访问的也是该 Key 下的状态
    String key = ctx.getCurrentKey();
    Long value = myState.value(); // 该 Key 下的 State
}
```

如果 State 为 null，很可能是在 `onTimer` 触发前该 Key 的 State 被其他逻辑清除了。

### 6.3 Timer 导致 Checkpoint 超时

Timer 数量过多会导致 Checkpoint 时需要序列化大量 Timer 数据。解决方案：
- 减少 Timer 数量：合并逻辑，避免每条数据都注册新 Timer
- 使用 RocksDB StateBackend：Timer 数据可以 spill 到磁盘，避免 OOM
- 增量 Checkpoint：减少每次 Checkpoint 需要持久化的数据量

### 6.4 processElement 中重复注册不同时间的 Timer

```java
// 错误示例：每条数据都注册一个新的 Timer，从不删除旧的
@Override
public void processElement(Event event, Context ctx, Collector<Alert> out) throws Exception {
    long timeout = ctx.timerService().currentProcessingTime() + TIMEOUT;
    ctx.timerService().registerProcessingTimeTimer(timeout);
    // 问题：如果每毫秒都有数据，就会注册上千个 Timer，全部会触发
}
```

正确做法：先 delete 旧 Timer，再 register 新 Timer（参考 2.3 节的超时检测模式）。

## 7. Timer 选型决策树

```
需要定时触发逻辑？
    │
    ├── 是否能用 Window API 满足？
    │     ├── 是 → 优先使用 Window（内置 Timer 管理）
    │     └── 否 ↓
    │
    ├── 是否需要自定义窗口触发策略？
    │     ├── 是 → 自定义 Trigger（在 Window API 框架内使用 Timer）
    │     └── 否 ↓
    │
    ├── 是否需要完全自定义时间驱动逻辑？
    │     └── 是 → KeyedProcessFunction + Timer
    │
    └── 时间语义选择：
          ├── 需要确定性（回放一致）→ Event Time Timer
          └── 需要低延迟（实时墙钟）→ Processing Time Timer
```

## 8. 总结

| 维度 | 要点 |
|---|---|
| 核心机制 | Timer = Key + Namespace + Timestamp 三元组，自动去重 |
| 使用场所 | KeyedProcessFunction、Trigger、KeyedCoProcessFunction、KeyedBroadcastProcessFunction |
| 事件时间 Timer | Watermark ≥ 注册时间时触发，确定性强，适合回放 |
| 处理时间 Timer | 墙钟到达时触发，低延迟，但有限流结束时不触发 |
| 核心模式 | 窗口聚合、超时检测、去抖动、周期性输出、双流超时 Join |
| 关键陷阱 | Timer 风暴、状态膨胀、Checkpoint 超时、有限流丢数 |
| 最佳实践 | 利用去重简化逻辑、打散触发时间、及时清理、优先事件时间 |
