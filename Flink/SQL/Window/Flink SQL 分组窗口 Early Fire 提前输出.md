假设现在遇到这样一个场景，我们需要实时统计每分钟、每小时甚至每天的 PV 或者 UV。如果使用 Flink SQL 中的滚动窗口来计算，那么只能在每分钟、每小时或者每天结束的时候才能把结果输出。这种输出显然不满足我们的需求，有没有一种更实时的输出方案，例如，1分钟的时间窗口，窗口触发之前希望每 10 秒都能看到最新的结果。如果1分钟窗口内的统计结果无变化，则不更新输出结果；如果1分钟窗口内的统计结果有变化，则更新输出结果。

针对这类提前输出的场景，可以在 Flink SQL 使用添加 emit 输出策略，如下所示启用提前输出策略：
```sql
table.exec.emit.early-fire.enabled = true
table.exec.emit.early-fire.delay = 10s
```
需要注意的是这个功能并没有在官方文档里面写出来，目前还是一个实验性质的功能，在生产环境中使用要慎重。

## 1. 提前触发 Early Fire

table.exec.emit.early-fire.enabled 参数指定了是否启用提前输出策略，即在 Watermark或者处理时间到达窗口结束之间之前的输出策略：
```java
@Experimental
val TABLE_EXEC_EMIT_EARLY_FIRE_ENABLED: ConfigOption[JBoolean] =
  key("table.exec.emit.early-fire.enabled")
    .booleanType()
    .defaultValue(Boolean.box(false))
    .withDescription("Specifies whether to enable early-fire emit." +
      "Early-fire is an emit strategy before watermark advanced to end of window.")
```
table.exec.emit.early-fire.delay 参数指定了提前输出的延迟时间：
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
该参数配置必须大于等于 0：如果等于 0 表示没有提前输出延迟，每个元素都会触发输出；如果大于 0 表示触发的时间间隔。例如，该参数配置为 10s，即在 Watermark或者处理时间到达窗口结束之间之前，每 10 秒输出一次。

> 详细请查阅  [WindowEmitStrategy](https://github.com/apache/flink/blob/master/flink-table/flink-table-planner/src/main/scala/org/apache/flink/table/planner/plan/utils/WindowEmitStrategy.scala)

### 1.1 基于处理时间

```
19:14:54,942 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 295
19:14:59,912 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 296
19:15:04,917 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 297
19:15:09,918 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 298
19:15:14,926 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 299
19:15:19,929 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 300
19:15:24,932 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 301
19:15:29,938 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 302
19:15:34,941 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 303
19:15:39,948 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 304
19:15:44,954 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 305
19:15:49,955 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 306
19:15:54,960 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 307
```

```
+I[2022-10-06 19:14:00, 2022-10-06 19:15:00, 2]
+I[2022-10-06 19:15:00, 2022-10-06 19:16:00, 2]
-U[2022-10-06 19:15:00, 2022-10-06 19:16:00, 2]
+U[2022-10-06 19:15:00, 2022-10-06 19:16:00, 5]
-U[2022-10-06 19:15:00, 2022-10-06 19:16:00, 5]
+U[2022-10-06 19:15:00, 2022-10-06 19:16:00, 7]
-U[2022-10-06 19:15:00, 2022-10-06 19:16:00, 7]
+U[2022-10-06 19:15:00, 2022-10-06 19:16:00, 8]
-U[2022-10-06 19:15:00, 2022-10-06 19:16:00, 8]
+U[2022-10-06 19:15:00, 2022-10-06 19:16:00, 10]
-U[2022-10-06 19:15:00, 2022-10-06 19:16:00, 10]
+U[2022-10-06 19:15:00, 2022-10-06 19:16:00, 11]
```

### 1.2 基于事件时间


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


## 2. Late Fire 迟到触发

table.exec.emit.late-fire.enabled 参数指定了是否启用迟到输出策略，即在 Watermark或者处理时间到达窗口结束时间之后的输出策略：
```java
@Experimental
val TABLE_EXEC_EMIT_LATE_FIRE_ENABLED: ConfigOption[JBoolean] =
  key("table.exec.emit.late-fire.enabled")
    .booleanType()
    .defaultValue(Boolean.box(false))
    .withDescription("Specifies whether to enable late-fire emit. " +
      "Late-fire is an emit strategy after watermark advanced to end of window.")
```
table.exec.emit.late-fire.delay 参数指定了迟到输出的延迟时间：
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
该参数配置必须大于等于 0：如果等于 0 表示没有迟到输出延迟，每个元素都会触发输出；如果大于 0 表示触发的时间间隔。例如，该参数配置为 10s，即在 Watermark或者处理时间到达窗口结束时间之后，每 10 秒输出一次。

> 详细请查阅  [WindowEmitStrategy](https://github.com/apache/flink/blob/master/flink-table/flink-table-planner/src/main/scala/org/apache/flink/table/planner/plan/utils/WindowEmitStrategy.scala)


```
22:39:00,012 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 334
22:39:04,965 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 335
22:39:09,969 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 336
22:39:14,974 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 337
22:39:19,978 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 338
22:39:24,984 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 339
22:39:29,988 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 340
22:39:34,993 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 341
22:39:39,999 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 342
22:39:45,000 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 343
22:39:50,005 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 344
22:39:55,013 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 345
22:40:00,016 INFO  kafka [] - 返回结果 topic: user_behavior, partition: 0, offset: 346
```

```
+I[2022-10-06 22:39:00, 2022-10-06 22:40:00, 12]
+I[2022-10-06 22:40:00, 2022-10-06 22:41:00, 1]
```


```
+I[2022-10-01 23:02:00, 2022-10-01 23:03:00, 6]
-U[2022-10-01 23:02:00, 2022-10-01 23:03:00, 6]
+U[2022-10-01 23:02:00, 2022-10-01 23:03:00, 7]
-U[2022-10-01 23:02:00, 2022-10-01 23:03:00, 7]
+U[2022-10-01 23:02:00, 2022-10-01 23:03:00, 8]
+I[2022-10-01 23:03:00, 2022-10-01 23:04:00, 4]
```
如果不配置：
```
+I[2022-10-01 23:02:00, 2022-10-01 23:03:00, 6]
+I[2022-10-01 23:03:00, 2022-10-01 23:04:00, 4]
```


Emit 输出策略原理如下所示：
- 当某个 Key 来了第一条数据记录时，注册一个延迟输出时间(table.exec.emit.early-fire.delay 参数指定)之后的处理时间定时器；
- 当定时器触发时
  - 检查当前的 key 下的聚合结果跟上次输出的结果是否有变化，
     - 如果有变化，就发送 `-[old], +[new]` 两条结果到下游；
     - 如果没有变化，则不做任何处理；
  - 再次注册一个新的延迟输出时间之后的处理时间定时器。

通过上面可以知道，窗口添加了 emit 输出策略后会由原来输出 Append 流结果变成输出 Retract 流。



1、Emit策略
Emit 策略是指在Flink SQL 中，query的输出策略（如能忍受的延迟）可能在不同的场景有不同的需求，而这部分需求，传统的 ANSI SQL 并没有对应的语法支持。比如用户需求：1小时的时间窗口，窗口触发之前希望每分钟都能看到最新的结果，窗口触发之后希望不丢失迟到一天内的数据。针对这类需求，抽象出了EMIT语法，并扩展到了SQL语法。

2、用途
EMIT语法的用途目前总结起来主要提供了：控制延迟、数据精确性，两方面的功能。

控制延迟。针对大窗口，设置窗口触发之前的EMIT输出频率，减少用户看到结果的延迟(WITH| WITHOUT DELAY)。
数据精确性。不丢弃窗口触发之后的迟到的数据，修正输出结果(minIdleStateRetentionTime，在WindowEmitStrategy中生成allowLateness)。
在选择EMIT策略时，还需要与处理开销进行权衡。因为越低的输出延迟、越高的数据精确性，都会带来越高的计算开销。

3、语法
EMIT 语法是用来定义输出的策略，即是定义在输出（INSERT INTO）上的动作。当未配置时，保持原有默认行为，即 window 只在 watermark 触发时 EMIT 一个结果。

语法：
INSERT INTO tableName
query
EMIT strategy [, strategy]*

strategy ::= {WITH DELAY timeInterval | WITHOUT DELAY}
[BEFORE WATERMARK |AFTER WATERMARK]

timeInterval ::=‘string’ timeUnit

WITH DELAY：声明能忍受的结果延迟，即按指定 interval 进行间隔输出。
WITHOUT DELAY：声明不忍受延迟，即每来一条数据就进行输出。
BEFORE WATERMARK：窗口结束之前的策略配置，即watermark 触发之前。
AFTER WATERMARK：窗口结束之后的策略配置，即watermark 触发之后。
注：

其中 strategy可以定义多个，同时定义before和after的策略。 但不能同时定义两个 before 或 两个after 的策略。
若配置了AFTER WATERMARK 策略，需要显式地在TableConfig中配置minIdleStateRetentionTime标识能忍受的最大迟到时间。
minIdleStateRetentionTime在window中只影响窗口何时清除，不直接影响窗口何时触发， 例如配置为3600000，最多容忍1小时的迟到数据，超过这个时间的数据会直接丢弃
4、示例
如果我们已经有一个TUMBLE（ctime, INTERVAL ‘1’ HOUR）的窗口，tumble_window 的输出是需要等到一小时结束才能看到结果，我们希望能尽早能看到窗口的结果（即使是不完整的结果）。例如，我们希望每分钟看到最新的窗口结果：
INSERT INTO result
SELECT * FROM tumble_window
EMIT WITH DELAY ‘1’ MINUTE BEFORE WATERMARK – 窗口结束之前，每隔1分钟输出一次更新结果

tumble_window 会忽略并丢弃窗口结束后到达的数据，而这部分数据对我们来说很重要，希望能统计进最终的结果里。而且我们知道我们的迟到数据不会太多，且迟到时间不会超过一天以上，并且希望收到迟到的数据立刻就更新结果：
INSERT INTO result
SELECT * FROM tumble_window
EMIT WITH DELAY ‘1’ MINUTE BEFORE WATERMARK,
WITHOUT DELAY AFTER WATERMARK --窗口结束之后，每条到达的数据都输出

tEnv.getConfig.setIdleStateRetentionTime(Time.days(1), Time.days(2))//min、max，只有Time.days(1)这个参数直接对window生效

补充一下WITH DELAY '1’这种配置的周期触发策略（即DELAY大于0），最后都是由ProcessingTime系统时间触发：
