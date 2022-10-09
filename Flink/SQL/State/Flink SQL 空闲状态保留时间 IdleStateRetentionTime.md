## 1. 简介

许多 Flink SQL 查询在一个或多个 Key 上做聚合或关联。当在流上执行这样的查询时，Flink 需要处理数据记录并维护每个 Key 的中间结果。如果输入流的 Key 是变化的，即随着时间的推移而变化，那么随着处理过的 Key 越来越多，查询会积累越来越多的状态。然而，通常在一段时间后，这些 Key 不会再出现，相应的状态也不在有用。例如，下面的查询计算每次会话的点击次数：
```SQL
SELECT sessionId, COUNT(*) AS cnt
FROM clicks
GROUP BY sessionId;
```
会话标识 sessionId 被用作分组 Key 来计算每次会话的点击次数，Flink 会维护处理过的每次会话的点击次数 cnt。sessionId 属性会随着时间的推移而发生变化，sessionId 值只在会话结束前是有效的，即在一段有限的时间内是有效的，会话结束之后不会再出现该 sessionId 值。然而，Flink 是不可能知道 sessionId 这个特性的，它认为每个 sessionId 值在未来任何时间点都可能出现。所以它为处理过的每个 sessionId 值维护一个点击次数。因此，随着处理过的 sessionId 值越来越多，查询的总状态大小也在不断增长。

即随着时间的推移，内存中积累的状态会越来越多。在这种情况下，如果不做处理，那么迟早有一天作业的状态就会达到存储系统的容量极限，从而造成作业的崩溃。Flink 提出了空闲状态保留时间（Idle State Retention Time）特性来解决这个问题。Flink SQL 空闲状态保留时间是针对 SQL 中聚合 Key 而言的，空闲的时间也就是 Key 没有更新的时间。如果在 Flink SQL 任务中设置了空闲状态的保留时间，那么当 Key 对应的状态在空闲状态保留时间之内没有被更新就会被删除，即状态空闲超过一定的时间后状态就会被清理。

对于前面的示例查询，只要 sessionId 在空闲状态保留时间内没有更新，它的点击次数就会被删除。删除 Key 的状态之后，该查询就认为以前没有见过这个 Key。如果再次处理具有这个 Key 的记录(其状态之前已被删除)，那么该记录会被认为是该 Key 出现的第一个记录。对于上面的例子，这意味着 sessionId 的计数将再次从 0 开始。

## 2. 如何使用

旧版本 Flink SQL 空闲状态保留时间有两个参数，状态空闲最小保留时间和状态空闲最大保留时间：
- 最小空闲状态保留时间：定义了一个 Key 的状态在删除之前最小保留时间
- 最大空闲状态保留时间：定义了一个 Key 的状态在删除之前最大保留时间

很多人会问，为什么会设置两个时间参数呢，设置一个参数不就好了吗？更早版本 Flink 确实只设置了一个参数，表示最小和最大闲状态保留时间相同，但是这样可能会导致同一时间内有很多状态到期，从而造成瞬间的处理压力。后来版本中要求两个参数之间的差距至少要达到 5 分钟，从而避免大量状态瞬间到期，对系统造成的冲击：
```java
public void setIdleStateRetentionTime(Time minTime, Time maxTime) {
    if (maxTime.toMilliseconds() - minTime.toMilliseconds() < 300000
            && !(maxTime.toMilliseconds() == 0 && minTime.toMilliseconds() == 0)) {
        throw new IllegalArgumentException(
                "Difference between minTime: "
                        + minTime.toString()
                        + " and maxTime: "
                        + maxTime.toString()
                        + "shoud be at least 5 minutes.");
    }
    minIdleStateRetentionTime = minTime.toMilliseconds();
    maxIdleStateRetentionTime = maxTime.toMilliseconds();
}
```

在最新版本中最大空闲状态保留时间会被忽略，只需要提供最小空闲状态保留时间即可
```java
@Deprecated
public void setIdleStateRetentionTime(Time minTime, Time maxTime) {
    if (maxTime.toMilliseconds() - minTime.toMilliseconds() < 300000
            && !(maxTime.toMilliseconds() == 0 && minTime.toMilliseconds() == 0)) {
        throw new IllegalArgumentException(
                "Difference between minTime: "
                        + minTime.toString()
                        + " and maxTime: "
                        + maxTime.toString()
                        + " should be at least 5 minutes.");
    }
    setIdleStateRetention(Duration.ofMillis(minTime.toMilliseconds()));
}

public void setIdleStateRetention(Duration duration) {
    configuration.set(ExecutionConfigOptions.IDLE_STATE_RETENTION, duration);
}
```
最大空闲状态保留时间会自动根据最小空闲状态保留时间乘以1.5来计算。

如果要在 Flink SQL 中使用，只需要调用 setIdleStateRetention 即可，参数为最小空闲状态保留时间：
```java
// Table 运行环境配置
EnvironmentSettings settings = EnvironmentSettings
        .newInstance()
        .inStreamingMode()
        .build();
StreamTableEnvironment tEnv = StreamTableEnvironment.create(env, settings);
// 设置状态空闲时间
TableConfig config = tEnv.getConfig();
config.setIdleStateRetention(Duration.ofMinutes(1));
```
> 完整代码请查阅 []()

## 3. 实现原理

```java
public interface CleanupState {
    default void registerProcessingCleanupTimer(ValueState<Long> cleanupTimeState, long currentTime, long minRetentionTime, long maxRetentionTime, TimerService timerService) throws Exception {
        // 状态清理时间
        Long curCleanupTime = (Long)cleanupTimeState.value();
        //
        if(curCleanupTime == null || currentTime + minRetentionTime > curCleanupTime.longValue()) {
            long cleanupTime = currentTime + maxRetentionTime;
            timerService.registerProcessingTimeTimer(cleanupTime);
            if(curCleanupTime != null) {
                timerService.deleteProcessingTimeTimer(curCleanupTime.longValue());
            }
            cleanupTimeState.update(Long.valueOf(cleanupTime));
        }
    }
}
```
从上面可以知道，每个 key 对应的状态清理时间都会维护在 ValueState 中。如果满足以下两条件之一：

状态清理时间为空，即这个 key 是第一次出现
或者当前时间加上 minRetentionTime 已经超过了状态清理时间



参考：
- [query_configuration](https://nightlies.apache.org/flink/flink-docs-release-1.12/dev/table/streaming/query_configuration.html)
