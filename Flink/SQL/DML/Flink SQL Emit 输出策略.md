假设现在遇到这样一个场景，我们需要实时统计每分钟、每小时甚至每天的 PV 或者 UV。如果使用 Flink SQL 中的滚动窗口来计算，那么只能在每分钟、每小时或者每天结束的时候才能把结果输出。这种输出显然不满足我们的需求，有没有一种更实时的输出方案，例如，1 分钟的时间窗口，窗口触发之前希望每 10 秒都能看到最新的结果。针对这类提前输出的场景，可以在 Flink SQL 使用添加 EMIT 输出策略，如下所示启用提前输出策略：
```sql
table.exec.emit.early-fire.enabled = true
table.exec.emit.early-fire.delay = 10s
```
## 1. 什么是 EMIT 输出策略

EMIT 输出策略是指在 Flink SQL 中，QUERY 根据不同场景选择不同的输出策略（例如最大延迟时长），从而达到控制延迟或提高数据准确性的效果。例如，1 小时的时间窗口，窗口触发之前希望每分钟都能看到最新的结果，窗口触发之后希望不丢失迟到一天内的数据。如果 1 小时窗口内的统计结果无变化，则不更新输出结果；如果1小时窗口内的统计结果有变化，则更新输出结果。需要注意的是添加了 EMIT 输出策略后会由原来输出 Append 流变成输出 Retract 流。检查当前的 key 下的聚合结果跟上次输出的结果是否有变化，如果有变化，就发送 `-[old], +[new]` 两条结果到下游；如果没有变化，则不做任何处理。

> 传统的 ANSI SQL语法不支持该类输出策略。

需要注意的是这个功能并没有在官方文档里面写出来，目前还是一个实验性质的功能，在生产环境中使用要慎重。此外，EMIT 输出策略只支持 TUMBLE 和 HOP 窗口，暂不支持 SESSION 窗口：
```java
if (isSessionWindow && (earlyFireDelayEnabled || lateFireDelayEnabled)) {
  throw new TableException("Session window doesn't support EMIT strategy currently.")
}
```

目前 EMIT 输出策略支持如下两个策略：
- BEFORE WATERMARK 策略
- AFTER WATERMARK 策略

你可以只配置一个 BEFORE WATERMARK 策略或者 AFTER WATERMARK 策略，也可以同时配置一个 BEFORE WATERMARK 策略和一个 AFTER WATERMARK 策略。但是不能同时配置多个 BEFORE WATERMARK 策略或者多个 AFTER WATERMARK 策略。

## 2. DELAY 概念

再讲解具体的 EMIT 输出策略之前，我们先一起看一下 DELAY 概念，有助于你更快的理解 EMIT 的两大输出策略。EMIT 输出策略中的 DELAY 指的是用户可接受的数据延迟时长，该延迟是指从用户的数据进入 Flink，到看到结果数据的时间（可以是事件时间也可以是处理时间）。延迟的计算基于系统时间。动态表（流式数据在实时计算内部的存储）中的数据发生变化的时间和结果表（实时计算外部的存储）中显示新记录的时间的间隔，称为延迟。

假设，实时计算系统的处理耗时是0，那么在流式数据积攒和 Window 等待窗口数据的过程可能会导致延迟。如果您指定了最多延迟 30 秒，那么 30 秒可用于流式数据的积攒。如果 Query 是 1 小时的窗口，那么最多延迟 30 秒的含义是每隔 30 秒更新结果数据。

如果 DELAY 配置为 1 分钟，对于 Group By 聚合，系统会在 1 分钟内积攒流式数据。如果有 Window 并且 Window 的 Size 大于 1 分钟，Window 就每隔 1 分钟更新一次结果数据。如果 Window 的 Size 小于 1 分钟，因为窗口依靠 Watermark 的输出就能保证 Latency SLA，所以系统就会忽略这个配置；如果 DELAY 配置为 0，对于 Group By 聚合，不会启用 minibatch 参数来增加延迟，每来一条数据都会触发计算和输出。对于 Window 函数，也是每来一条数据都触发计算和输出。

DELAY 需要通过 `table.exec.emit.xxx-fire.delay` 参数指定，下面会具体讲解。

## 3. BEFORE WATERMARK 策略

BEFORE WATERMARK 策略(或者称之为 Early Fire 策略)是窗口结束之前（即 Watermark 触发之前）的配置策略。BEFORE WATERMARK 策略核心作用就是控制延迟：针对窗口，设置窗口触发之前的 EMIT 输出频率（提前输出当前窗口结果），降低结果输出延迟。

如果要使用 BEFORE WATERMARK 策略，需要配置如下两个参数：
- `table.exec.emit.early-fire.enabled`
- `table.exec.emit.early-fire.delay`

`table.exec.emit.early-fire.enabled` 参数指定了是否启用 BEFORE WATERMARK 策略（Early Fire），即在 Watermark 到达窗口结束之间之前的输出策略：
```java
@Experimental
val TABLE_EXEC_EMIT_EARLY_FIRE_ENABLED: ConfigOption[JBoolean] =
  key("table.exec.emit.early-fire.enabled")
    .booleanType()
    .defaultValue(Boolean.box(false))
    .withDescription("Specifies whether to enable early-fire emit." +
      "Early-fire is an emit strategy before watermark advanced to end of window.")
```
`table.exec.emit.early-fire.delay` 参数指定了 DELAY 时间：
```java
@Experimental
val TABLE_EXEC_EMIT_EARLY_FIRE_DELAY: ConfigOption[Duration] =
  key("table.exec.emit.early-fire.delay")
    .durationType()
    .noDefaultValue()
    .withDescription(
      "The early firing delay in milli second, early fire is " +
        "the emit strategy before watermark advanced to end of window. " +
        "< 0 is illegal configuration. " +
        "0 means no delay (fire on every element). " +
        "> 0 means the fire interval. ")
```
该参数配置必须大于等于 0：如果等于 0 表示没有提前输出延迟，每个元素都会触发输出；如果大于 0 表示触发的时间间隔。例如参数配置为 10s，即在 Watermark 到达窗口结束之间之前每 10 秒输出一次。

> 详细请查阅  [WindowEmitStrategy](https://github.com/apache/flink/blob/master/flink-table/flink-table-planner/src/main/scala/org/apache/flink/table/planner/plan/utils/WindowEmitStrategy.scala)

## 4. AFTER WATERMARK 策略

AFTER WATERMARK 策略（或者称之为 Late Fire）是窗口结束之后（即 Watermark 触发之后）的配置策略。AFTER WATERMARK 策略核心作用是提高数据精确性：不丢弃窗口触发之后的迟到的数据，修正输出结果。

需要注意的是如果配置了 AFTER WATERMARK 策略，需要声明 table.exec.state.ttl 标识最大延迟时长。因为 AFTER WATERMARK 策略允许接收迟到的数据，所以窗口的状态（State）需要保留一定时长，等待迟到的数据。例如，table.exec.state.ttl = 3600000 表示状态允许保留超时时长为 1 小时内的数据，超时时长大于 1 小时的数据不被录入状态。

如果要使用 AFTER WATERMARK 策略，需要配置如下两个参数：
- `table.exec.emit.late-fire.enabled`
- `table.exec.emit.late-fire.delay`
- `table.exec.state.ttl`

`table.exec.emit.late-fire.enabled` 参数指定了是否启用迟到输出策略，即在 Watermark 到达窗口结束时间之后的输出策略：
```java
@Experimental
val TABLE_EXEC_EMIT_LATE_FIRE_ENABLED: ConfigOption[JBoolean] =
  key("table.exec.emit.late-fire.enabled")
    .booleanType()
    .defaultValue(Boolean.box(false))
    .withDescription("Specifies whether to enable late-fire emit. " +
      "Late-fire is an emit strategy after watermark advanced to end of window.")
```
`table.exec.emit.late-fire.delay` 参数指定了迟到输出的延迟时间：
```java
@Experimental
val TABLE_EXEC_EMIT_LATE_FIRE_DELAY: ConfigOption[Duration] =
  key("table.exec.emit.late-fire.delay")
    .durationType()
    .noDefaultValue()
    .withDescription(
      "The late firing delay in milli second, late fire is " +
        "the emit strategy after watermark advanced to end of window. " +
        "< 0 is illegal configuration. " +
        "0 means no delay (fire on every element). " +
        "> 0 means the fire interval.")
```
该参数配置必须大于等于 0：如果等于 0 表示没有迟到输出延迟，每个元素都会触发输出；如果大于 0 表示触发的时间间隔。例如该参数配置为 10s，即在 Watermark 到达窗口结束时间之后每 10 秒输出一次。

目前在新版本中添加了 `table.exec.emit.allow-lateness` 参数，可以用来指定 Watermark 到达窗口结束时间之后可允许的延迟时间：
```java
@Experimental
val TABLE_EXEC_EMIT_ALLOW_LATENESS: ConfigOption[Duration] =
  key("table.exec.emit.allow-lateness")
    .durationType()
    .noDefaultValue()
    .withDescription("Sets the time by which elements are allowed to be late. " +
      "Elements that arrive behind the watermark by more than the specified time " +
      "will be dropped. " +
      "Note: use the value if it is set, else use 'minIdleStateRetentionTime' in table config." +
      "< 0 is illegal configuration. " +
      "0 means disable allow lateness. " +
      "> 0 means allow-lateness.")
```

> 详细请查阅  [WindowEmitStrategy](https://github.com/apache/flink/blob/master/flink-table/flink-table-planner/src/main/scala/org/apache/flink/table/planner/plan/utils/WindowEmitStrategy.scala)

## 5. 示例

假设我们有窗口大小为 1 分钟的滚动窗口，如下所示：
```sql
INSERT INTO user_behavior_cnt
SELECT
  DATE_FORMAT(TUMBLE_START(ts_ltz, INTERVAL '1' MINUTE), 'yyyy-MM-dd HH:mm:ss') AS window_start,
  DATE_FORMAT(TUMBLE_END(ts_ltz, INTERVAL '1' MINUTE), 'yyyy-MM-dd HH:mm:ss') AS window_end,
  COUNT(*) AS cnt
FROM user_behavior
GROUP BY TUMBLE(ts_ltz, INTERVAL '1' MINUTE)
```
为了验证 BEFORE 和 AFTER WATERMARK 策略的实际效果，我们准备了一份测试数据集，数据以 CSV 格式编码，具体如下所示：
```
-- uid,pid,cid,type,timestamp,time
1001,3827899,2920476,pv,1664636572000,2022-10-01 23:02:52
1001,3745169,2891509,pv,1664636570000,2022-10-01 23:02:50
1001,266784,2520771,pv,1664636573000,2022-10-01 23:02:53
1001,2286574,2465336,pv,1664636574000,2022-10-01 23:02:54
1001,1531036,2920476,pv,1664636577000,2022-10-01 23:02:57
1001,2266567,4145813,pv,1664636584000,2022-10-01 23:03:04
1001,2951368,1080785,pv,1664636576000,2022-10-01 23:02:56
1001,3658601,2342116,pv,1664636586000,2022-10-01 23:03:06
1001,5153036,2342116,pv,1664636578000,2022-10-01 23:02:58
1001,598929,2429887,pv,1664636591000,2022-10-01 23:03:11
1001,3245421,2881542,pv,1664636595000,2022-10-01 23:03:15
1001,1046201,3002561,pv,1664636579000,2022-10-01 23:02:59
1001,2971043,4869428,pv,1664636646000,2022-10-01 23:04:06
```
为了模拟真实的 Kafka 数据源，我们还特地写了一个 [UserBehaviorSimpleProducer](https://github.com/sjf0115/data-example/blob/master/kafka-example/src/main/java/com/kafka/example/producer/UserBehaviorSimpleProducer.java) 任务，每 5 秒钟会自动读取一条数据灌到 Kafka 的 user_behavior Topic 中。有了数据源后，我们就可以用 DDL 去创建并连接这个 Kafka 中的 Topic，将计算结果输出到控制台打印：
```sql
-- 输入表
CREATE TABLE user_behavior (
  uid BIGINT COMMENT '用户Id',
  pid BIGINT COMMENT '商品Id',
  type STRING COMMENT '行为类型',
  `timestamp` BIGINT COMMENT '行为时间',
  ts_ltz AS TO_TIMESTAMP_LTZ(`timestamp`, 3), -- 事件时间
  WATERMARK FOR ts_ltz AS ts_ltz - INTERVAL '5' SECOND -- 在 ts_ltz 上定义watermark，ts_ltz 成为事件时间列
) WITH (
  'connector' = 'kafka',
  'topic' = 'user_behavior',
  'properties.bootstrap.servers' = 'localhost:9092',
  'properties.group.id' = 'user_behavior',
  'scan.startup.mode' = 'latest-offset',
  'format' = 'json',
  'json.ignore-parse-errors' = 'false',
  'json.fail-on-missing-field' = 'true'
)

-- 输出表
CREATE TABLE user_behavior_cnt (
  window_start STRING COMMENT '窗口开始时间',
  window_end STRING COMMENT '窗口结束时间',
  cnt BIGINT COMMENT '次数'
) WITH (
  'connector' = 'print'
)
```

### 5.1 提前输出

默认滚动窗口的输出需要等到 1 分钟结束后才能输出结果：
```
+I[2022-10-01 23:02:00, 2022-10-01 23:03:00, 6]
+I[2022-10-01 23:03:00, 2022-10-01 23:04:00, 4]
```
> 不添加 BEFORE WATERMARK 对应的参数

如果你需要尽早看到窗口的输出结果（即使是不完整的结果），例如每 10 秒看到最新的窗口结果，可以添加如下代码：
```java
TableEnvironment tEnv = TableEnvironment.create(settings);
Configuration config = tEnv.getConfig().getConfiguration();
// 开启 BEFORE WATERMARK 策略
config.setBoolean("table.exec.emit.early-fire.enabled", true);
config.setString("table.exec.emit.early-fire.delay", "10s");
```
添加上述代码，在窗口结束之前每隔 10 秒输出一次更新结果：
```
+I[2022-10-01 23:02:00, 2022-10-01 23:03:00, 3]
-U[2022-10-01 23:02:00, 2022-10-01 23:03:00, 3]
+U[2022-10-01 23:02:00, 2022-10-01 23:03:00, 5]
-U[2022-10-01 23:02:00, 2022-10-01 23:03:00, 5]
+U[2022-10-01 23:02:00, 2022-10-01 23:03:00, 6]
+I[2022-10-01 23:03:00, 2022-10-01 23:04:00, 1]
-U[2022-10-01 23:03:00, 2022-10-01 23:04:00, 1]
+U[2022-10-01 23:03:00, 2022-10-01 23:04:00, 2]
-U[2022-10-01 23:03:00, 2022-10-01 23:04:00, 2]
+U[2022-10-01 23:03:00, 2022-10-01 23:04:00, 4]
+I[2022-10-01 23:04:00, 2022-10-01 23:05:00, 1]
```
> 完整代码请查阅 [EarlyFireEventTimeTumbleWindowExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/function/window/EarlyFireEventTimeTumbleWindowExample.java)

如果 DELAY 时间配置为 0，即每个数据记录元素都会触发输出，如下所示：
```
+I[2022-10-01 23:02:00, 2022-10-01 23:03:00, 1]
-U[2022-10-01 23:02:00, 2022-10-01 23:03:00, 1]
+U[2022-10-01 23:02:00, 2022-10-01 23:03:00, 2]
-U[2022-10-01 23:02:00, 2022-10-01 23:03:00, 2]
+U[2022-10-01 23:02:00, 2022-10-01 23:03:00, 3]
-U[2022-10-01 23:02:00, 2022-10-01 23:03:00, 3]
+U[2022-10-01 23:02:00, 2022-10-01 23:03:00, 4]
-U[2022-10-01 23:02:00, 2022-10-01 23:03:00, 4]
+U[2022-10-01 23:02:00, 2022-10-01 23:03:00, 5]
+I[2022-10-01 23:03:00, 2022-10-01 23:04:00, 1]
-U[2022-10-01 23:02:00, 2022-10-01 23:03:00, 5]
+U[2022-10-01 23:02:00, 2022-10-01 23:03:00, 6]
-U[2022-10-01 23:03:00, 2022-10-01 23:04:00, 1]
+U[2022-10-01 23:03:00, 2022-10-01 23:04:00, 2]
-U[2022-10-01 23:03:00, 2022-10-01 23:04:00, 2]
+U[2022-10-01 23:03:00, 2022-10-01 23:04:00, 3]
-U[2022-10-01 23:03:00, 2022-10-01 23:04:00, 3]
+U[2022-10-01 23:03:00, 2022-10-01 23:04:00, 4]
+I[2022-10-01 23:04:00, 2022-10-01 23:05:00, 1]
```

### 5.2 迟到输出

默认滚动会忽略并丢弃窗口结束后到达的数据：
```
+I[2022-10-07 16:16:01, 2022-10-01 23:02:00, 2022-10-01 23:03:00, 6]
+I[2022-10-07 16:16:26, 2022-10-01 23:03:00, 2022-10-01 23:04:00, 4]
```
> 不添加 AFTER WATERMARK 对应的参数

因为 pid = 5153036 和 1046201 的数据记录延迟太长时间，当它到达时它本应该属于的窗口早已触发计算后并销毁，导致该数据记录被丢弃。

如果您需要将窗口结束后 10 分钟到达的数据统计进入结果，并且每隔 5 秒更新一次结果，可以添加如下代码：
```java
TableEnvironment tEnv = TableEnvironment.create(settings);
Configuration config = tEnv.getConfig().getConfiguration();
// 窗口提前触发
config.setBoolean("table.exec.emit.late-fire.enabled", true);
config.setString("table.exec.emit.late-fire.delay", "5s");
```
此外，您还需要在作业参数中配置 table.exec.state.ttl（增加10分钟的状态生命周期）：
```java
// 状态保留 10 分钟
config.setString("table.exec.state.ttl", "600000");
```
添加上述代码，在窗口结束之后会继续输出迟到数据（pid = 5153036 和 1046201 的数据记录）并更新结果：
```
+I[2022-10-07 16:26:45, 2022-10-01 23:02:00, 2022-10-01 23:03:00, 6]
-U[2022-10-07 16:26:55, 2022-10-01 23:02:00, 2022-10-01 23:03:00, 6]
+U[2022-10-07 16:26:55, 2022-10-01 23:02:00, 2022-10-01 23:03:00, 7]
-U[2022-10-07 16:27:05, 2022-10-01 23:02:00, 2022-10-01 23:03:00, 7]
+U[2022-10-07 16:27:05, 2022-10-01 23:02:00, 2022-10-01 23:03:00, 8]
+I[2022-10-07 16:27:11, 2022-10-01 23:03:00, 2022-10-01 23:04:00, 4]
```
> 完整代码请查阅 [LateFireEventTimeTumbleWindowExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/function/window/LateFireEventTimeTumbleWindowExample.java)
