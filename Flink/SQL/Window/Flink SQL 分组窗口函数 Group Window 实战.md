
在 Flink 1.12 之前的版本中，Table API 和 SQL 提供了一组分组窗口 Group Window 函数，常用的时间窗口如滚动窗口、滑动窗口、会话窗口都有对应的实现，具体在 SQL 中调用 TUMBLE()、HOP()、SESSION() 分组窗口函数即可。分组窗口的功能比较有限，只支持窗口聚合，所以在 Flink 1.12 之后的版本中不再推荐使用 Group Window 函数。而是推荐使用功能更加强大以及更有效的 Window TVF，具体请查阅 [Flink SQL 窗口表值函数 Window TVF 实战](https://smartsi.blog.csdn.net/article/details/127162902)。

Group Window 函数通过 SQL 查询的 GROUP BY 子句来定义。就像使用常规 GROUP BY 子句一样查询，但是 GROUP BY 子句会包含一个分组窗口函数。

下面我们详细看一下三个分组窗口 Group Window 函数具体是如何使用的。

## 1. TUMBLE

滚动窗口的窗口大小是固定不变的，并且窗口和窗口之间的数据不会重合。在 Flink SQL 中通过 `TUMBLE(time_attr, interval)` 窗口函数来定义滚动窗口，其中参数 time_attr 用于指定时间属性，参数 interval 用于指定窗口的固定大小。例如，如下所示定义一个 1 分钟大小的滚动窗口：
```sql
TUMBLE(process_time, INTERVAL '1' MINUTE)
```
上述窗口会以 1 分钟的时间间隔对行进行分组。

> 对于流表上的 SQL 查询，分组窗口函数的 time_attr 参数必须引用一个有效的时间属性，该属性指定行的处理时间或事件时间。具体可以查阅 [Flink Table API & SQL 如何定义时间属性](https://smartsi.blog.csdn.net/article/details/127173096)，了解如何定义时间属性。

窗口元数据信息可以通过在 Select 语句中使用相关的函数获取，并且窗口元数据信息可用于后续的 SQL 操作。例如可以通过 TUMBLE_START 获取窗口起始时间，TUMBLE_END 获取窗口结束时间，TUMBLE_ROWTIME 获取窗口事件时间，TUMBLE_PROCTIME 获取窗口数据中的处理时间：
- `TUMBLE_START(time_attr, interval)`
- `TUMBLE_END(time_attr, interval)`
- `TUMBLE_ROWTIME(time_attr, interval)`
- `TUMBLE_PROCTIME(time_attr, interval)`

如下实例所示，分别创建基于不同时间属性的 Tumble 窗口。

### 1.1 基于处理时间

我们准备了一份测试数据集，数据以 CSV 格式编码，具体如下所示：
```
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
  cid BIGINT COMMENT '商品类目Id',
  type STRING COMMENT '行为类型',
  `timestamp` BIGINT COMMENT '行为时间',
  `time` STRING COMMENT '行为时间',
  process_time AS PROCTIME() -- 处理时间
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
  window_start TIMESTAMP(3) COMMENT '窗口开始时间',
  window_end TIMESTAMP(3) COMMENT '窗口结束时间',
  cnt BIGINT COMMENT '次数',
  min_time STRING COMMENT '最小行为时间',
  max_time STRING COMMENT '最大行为时间',
  pid_set MULTISET<BIGINT> COMMENT '商品集合'
) WITH (
  'connector' = 'print'
)
```
需要注意的是输入表中必须具有一个时间属性的字段，在这里 process_time 是基于处理时间的时间属性字段。

假设我们的需求是基于处理时间计算每一分钟内用户的消费次数、窗口内最早消费时间、最后消费时间以及消费对应的商品ID列表，如下所示：
```sql
INSERT INTO user_behavior_cnt
SELECT
  TUMBLE_START(process_time, INTERVAL '1' MINUTE) AS window_start,
  TUMBLE_END(process_time, INTERVAL '1' MINUTE) AS window_end,
  COUNT(*) AS cnt,
  MIN(`time`) AS min_time,
  MAX(`time`) AS max_time,
  COLLECT(DISTINCT pid) AS pid_set
FROM user_behavior
GROUP BY TUMBLE(process_time, INTERVAL '1' MINUTE)
```
我们将这个查询的结果，通过 INSERT INTO 语句写到之前定义的 user_behavior_cnt Print 表中。最终执行结果如下所示：
```
+I[2022-10-05T14:47, 2022-10-05T14:48, 8, 2022-10-01 23:02:50, 2022-10-01 23:03:06, {3827899=1, 266784=1, 2266567=1, 2951368=1, 3745169=1, 1531036=1, 2286574=1, 3658601=1}]
+I[2022-10-05T14:48, 2022-10-05T14:49, 5, 2022-10-01 23:02:58, 2022-10-01 23:04:06, {5153036=1, 1046201=1, 598929=1, 3245421=1, 2971043=1}]
```

> 完整代码请查阅[ProcessTimeTumbleGroupWindowExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/function/window/ProcessTimeTumbleGroupWindowExample.java)

需要注意的是基于处理时间计算，每次运行的结果都具有不确定性，可能会得到不同的计算结果。上述输出是在如下输入时间点下计算的结果：
```java
// 处理时间 pid
14:47:20,337 3827899
14:47:25,308 3745169
14:47:30,315 266784
14:47:35,318 2286574
14:47:40,321 1531036
14:47:45,325 2266567
14:47:50,331 2951368
14:47:55,333 3658601
14:48:00,337 5153036
14:48:05,348 598929
14:48:10,344 3245421
14:48:15,350 1046201
14:48:20,355 2971043
```

### 1.2 基于事件时间

在这里还是继续使用上述示例的数据，使用如下所示 DDL 去创建并连接 Kafka 中的 Topic，将计算结果输出到控制台打印。需要注意的是在事件时间属性字段 ts_ltz 上定义 Watermark，设置最大乱序时间为 5s，如果数据记录事件时间戳小于当前 Watermark 5秒钟，就会出现数据记录的丢失：
```sql
-- 输入表
CREATE TABLE user_behavior (
  uid BIGINT COMMENT '用户Id',
  pid BIGINT COMMENT '商品Id',
  cid BIGINT COMMENT '商品类目Id',
  type STRING COMMENT '行为类型',
  `timestamp` BIGINT COMMENT '行为时间',
  `time` STRING COMMENT '行为时间',
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
  window_start TIMESTAMP(3) COMMENT '窗口开始时间',
  window_end TIMESTAMP(3) COMMENT '窗口结束时间',
  cnt BIGINT COMMENT '次数',
  min_time STRING COMMENT '最小行为时间',
  max_time STRING COMMENT '最大行为时间',
  pid_set MULTISET<BIGINT> COMMENT '商品集合'
) WITH (
  'connector' = 'print'
)
```
> 需要注意的是输入表中必须具有一个时间属性的字段，在这里 ts_ltz 是时间属性字段。

假设我们的需求是基于事件时间计算每一分钟内用户的消费次数，最早消费时间和最后消费时间以及消费对应的商品ID列表，如下所示：
```sql
INSERT INTO user_behavior_cnt
SELECT
  TUMBLE_START(ts_ltz, INTERVAL '1' MINUTE) AS window_start,
  TUMBLE_END(ts_ltz, INTERVAL '1' MINUTE) AS window_end,
  COUNT(*) AS cnt,
  MIN(`time`) AS min_time,
  MAX(`time`) AS max_time,
  COLLECT(DISTINCT pid) AS pid_set
FROM user_behavior
GROUP BY TUMBLE(ts_ltz, INTERVAL '1' MINUTE)
```
在这里计算消费对应的商品ID列表，只是为了演示基于事件时间在出现乱序时是如何处理的。我们将这个查询的结果通过 INSERT INTO 语句写到之前定义的 user_behavior_cnt Print 表中。最终执行结果如下所示：
```
+I[2022-10-01T23:02, 2022-10-01T23:03, 6, 2022-10-01 23:02:50, 2022-10-01 23:02:57, {3827899=1, 266784=1, 2951368=1, 3745169=1, 1531036=1, 2286574=1}]
+I[2022-10-01T23:03, 2022-10-01T23:04, 4, 2022-10-01 23:03:04, 2022-10-01 23:03:15, {2266567=1, 598929=1, 3245421=1, 3658601=1}]
```
因为 pid = 5153036 和 1046201 的数据记录延迟太长时间，当它到达时它本应该属于的窗口早已触发计算后并销毁，导致该数据记录被丢弃。

> 完整代码请查阅[EventTimeTumbleGroupWindowExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/function/window/EventTimeTumbleGroupWindowExample.java)

## 2. HOP

滑动窗口的窗口大小固定，但是窗口和窗口之间的数据可以重合。在 Flink SQL 中通过 `HOP(time_attr, interval1, interval2)` 窗口函数来定义滑动窗口，其中参数 time_attr 用于指定使用的时间属性，参数 interval1 用于指定窗口滑动的时间间隔(窗口滑动步长)，参数 interval2 用于指定窗口的固定大小。例如，如下所示定义一个 1 分钟大小的滑动窗口，每 30 秒滑动一次：
```sql
HOP(process_time, INTERVAL '30' SECOND, INTERVAL '1' MINUTE)
```
如果 interval1 小于 interval2，窗口就会发生重叠。

窗口元数据信息可以通过在 Select 语句中使用相关的函数获取，并且窗口元数据信息可用于后续的 SQL 操作。例如可以通过 HOP_START 获取窗口起始时间，HOP_END 获取窗口结束时间，HOP_ROWTIME 获取窗口事件时间，HOP_PROCTIME 获取窗口数据中的处理时间：
- `HOP_START(time_attr, interval, interval)`
- `HOP_END(time_attr, interval, interval)`
- `HOP_ROWTIME(time_attr, interval, interval)`
- `HOP_PROCTIME(time_attr, interval, interval)`

如下实例所示，分别创建基于不同时间属性的 HOP 窗口。

### 2.1 基于处理时间

输入、输出与 TUMBLE 函数中一样，在这不再赘述。假设我们的需求是基于处理时间每 30 秒计算最近一分钟内用户的消费次数，最早消费时间和最后消费时间以及消费对应的商品ID列表，如下所示：
```sql
INSERT INTO user_behavior_cnt
SELECT
  HOP_START(process_time, INTERVAL '30' SECOND, INTERVAL '1' MINUTE) AS window_start,
  HOP_END(process_time, INTERVAL '30' SECOND, INTERVAL '1' MINUTE) AS window_end,
  COUNT(*) AS cnt,
  MIN(`time`) AS min_time,
  MAX(`time`) AS max_time,
  COLLECT(DISTINCT pid) AS pid_set
FROM user_behavior
GROUP BY HOP(process_time, INTERVAL '30' SECOND, INTERVAL '1' MINUTE)
```
我们将这个查询的结果通过 INSERT INTO 语句写到之前定义的 user_behavior_cnt Print 表中。最终执行结果如下所示：
```
+I[2022-10-05T16:25, 2022-10-05T16:26, 4, 2022-10-01 23:02:50, 2022-10-01 23:02:54, {3827899=1, 266784=1, 3745169=1, 2286574=1}]
+I[2022-10-05T16:25:30, 2022-10-05T16:26:30, 10, 2022-10-01 23:02:50, 2022-10-01 23:03:11, {3827899=1, 5153036=1, 266784=1, 2266567=1, 2951368=1, 3745169=1, 598929=1, 1531036=1, 2286574=1, 3658601=1}]
+I[2022-10-05T16:26, 2022-10-05T16:27, 9, 2022-10-01 23:02:56, 2022-10-01 23:04:06, {5153036=1, 2266567=1, 2951368=1, 1046201=1, 598929=1, 1531036=1, 3245421=1, 3658601=1, 2971043=1}]
```
> 完整代码请查阅[ProcessTimeHopGroupWindowExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/function/window/ProcessTimeHopGroupWindowExample.java)

需要注意的是基于处理时间计算，每次运行的结果都具有不确定性，可能会得到不同的计算结果。上述输出是在如下输入时间点下计算的结果：
```
16:25:41,991 3827899
16:25:46,965 3745169
16:25:51,971 266784
16:25:56,975 2286574
16:26:01,978 1531036
16:26:06,982 2266567
16:26:11,987 2951368
16:26:16,992 3658601
16:26:21,998 5153036
16:26:27,002 598929
16:26:32,008 3245421
16:26:37,019 1046201
16:26:42,019 2971043
```

### 2.2 基于事件时间

输入、输出与 TUMBLE 函数中一样，在这不再赘述。假设我们的需求是基于事件时间每 30 秒计算最近一分钟内用户的消费次数，最早消费时间和最后消费时间以及消费对应的商品ID列表，如下所示：
```sql
INSERT INTO user_behavior_cnt
SELECT
  HOP_START(ts_ltz, INTERVAL '30' SECOND, INTERVAL '1' MINUTE) AS window_start,
  HOP_END(ts_ltz, INTERVAL '30' SECOND, INTERVAL '1' MINUTE) AS window_end,
  COUNT(*) AS cnt,
  MIN(`time`) AS min_time,
  MAX(`time`) AS max_time,
  COLLECT(DISTINCT pid) AS pid_set
FROM user_behavior
GROUP BY HOP(ts_ltz, INTERVAL '30' SECOND, INTERVAL '1' MINUTE)
```
我们将这个查询的结果通过 INSERT INTO 语句写到之前定义的 user_behavior_cnt Print 表中。最终执行结果如下所示：
```
+I[2022-10-01T23:02, 2022-10-01T23:03, 6, 2022-10-01 23:02:50, 2022-10-01 23:02:57, {3827899=1, 266784=1, 2951368=1, 3745169=1, 1531036=1, 2286574=1}]
+I[2022-10-01T23:02:30, 2022-10-01T23:03:30, 12, 2022-10-01 23:02:50, 2022-10-01 23:03:15, {3827899=1, 5153036=1, 266784=1, 2951368=1, 2266567=1, 1046201=1, 3745169=1, 598929=1, 1531036=1, 2286574=1, 3245421=1, 3658601=1}]
+I[2022-10-01T23:03, 2022-10-01T23:04, 4, 2022-10-01 23:03:04, 2022-10-01 23:03:15, {2266567=1, 598929=1, 3245421=1, 3658601=1}]
```
> 完整代码请查阅 [EventTimeHopGroupWindowExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/function/window/EventTimeHopGroupWindowExample.java)

## 3. SESSION

Session 窗口没有固定的窗口长度，而是根据指定时间间隔内数据的活跃性来切分窗口，例如当 10min 内数据不接入 Flink 系统则切分窗口并触发计算。在 Flink SQL 中通过 `SESSION(time_attr, interval)` 窗口函数来定义会话窗口，其中参数 time_attr 用于指定时间属性，参数 interval 用于指定 Session Gap。例如，如下所示定义一个 6 秒间隔大小的会话窗口：
```sql
SESSION(process_time, INTERVAL '6' SECOND)
```
窗口元数据信息可以通过在 Select 语句中使用相关的函数获取，并且窗口元数据信息可用于后续的 SQL 操作。例如可以通过 SESSION_START 获取窗口起始时间，SESSION_END 获取窗口结束时间，SESSION_ROWTIME 获取窗口事件时间，SESSION_PROCTIME 获取窗口数据中的处理时间：
- `SESSION_START(time_attr, interval)`
- `SESSION_END(time_attr, interval)`
- `SESSION_ROWTIME(time_attr, interval)`
- `SESSION_PROCTIME(time_attr, interval)`

如下实例所示，分别创建基于不同时间属性的 SESSION 窗口。

### 3.1 基于处理时间

输入、输出与 TUMBLE 函数中一样，只不过为了演示效果在第二个和第六个元素之后相比其他都增加了一秒的休眠时间，即其他数据记录之间都是5秒的休眠时间，第二个和第六个元素需要休眠6秒钟，如下所示：
```
23:12:45,668 3827899
23:12:50,654 3745169 // 注意 6秒之后才有下一个数据记录
23:12:56,658 266784
23:13:01,664 2286574
23:13:06,667 1531036
23:13:11,673 2266567 // 注意 6秒之后才有下一个数据记录
23:13:17,677 2951368
23:13:22,683 3658601
23:13:27,686 5153036
23:13:32,691 598929
23:13:37,696 3245421
23:13:42,701 1046201
23:13:47,705 2971043
```
我们的需求是基于处理时间计算每个会话内用户的消费次数，最早消费时间和最后消费时间以及消费对应的商品ID列表，如下所示：
```sql
INSERT INTO user_behavior_cnt
SELECT
  SESSION_START(process_time, INTERVAL '6' SECOND) AS window_start,
  SESSION_END(process_time, INTERVAL '6' SECOND) AS window_end,
  COUNT(*) AS cnt,
  MIN(`time`) AS min_time,
  MAX(`time`) AS max_time,
  COLLECT(DISTINCT pid) AS pid_set
FROM user_behavior
GROUP BY SESSION(process_time, INTERVAL '6' SECOND)
```
我们将这个查询的结果通过 INSERT INTO 语句写到之前定义的 user_behavior_cnt Print 表中。最终执行结果如下所示：
```
+I[2022-10-05T23:12:45.704, 2022-10-05T23:12:56.697, 2, 2022-10-01 23:02:50, 2022-10-01 23:02:52, {3827899=1, 3745169=1}]
+I[2022-10-05T23:12:56.722, 2022-10-05T23:13:17.739, 4, 2022-10-01 23:02:53, 2022-10-01 23:03:04, {266784=1, 2266567=1, 1531036=1, 2286574=1}]
+I[2022-10-05T23:13:17.770, 2022-10-05T23:13:53.755, 7, 2022-10-01 23:02:56, 2022-10-01 23:04:06, {5153036=1, 2951368=1, 1046201=1, 598929=1, 3245421=1, 3658601=1, 2971043=1}]
```
> 完整代码请查阅 [ProcessTimeSessionGroupWindowExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/function/window/ProcessTimeSessionGroupWindowExample.java)

### 3.2 基于事件时间

输入、输出与基于处理时间示例中一样，在这不再赘述。假设我们的需求是基于事件时间计算每个会话内用户的消费次数，最早消费时间和最后消费时间以及消费对应的商品ID列表，如下所示：
```sql
INSERT INTO user_behavior_cnt
SELECT
  SESSION_START(ts_ltz, INTERVAL '6' SECOND) AS window_start,
  SESSION_END(ts_ltz, INTERVAL '6' SECOND) AS window_end,
  COUNT(*) AS cnt,
  MIN(`time`) AS min_time,
  MAX(`time`) AS max_time,
  COLLECT(DISTINCT pid) AS pid_set
FROM user_behavior
GROUP BY SESSION(ts_ltz, INTERVAL '6' SECOND)
```
我们将这个查询的结果通过 INSERT INTO 语句写到之前定义的 user_behavior_cnt Print 表中。最终执行结果如下所示：
```
+I[2022-10-01T23:02, 2022-10-01T23:03, 6, 2022-10-01 23:02:50, 2022-10-01 23:02:57, {3827899=1, 266784=1, 2951368=1, 3745169=1, 1531036=1, 2286574=1}]
+I[2022-10-01T23:03, 2022-10-01T23:04, 4, 2022-10-01 23:03:04, 2022-10-01 23:03:15, {2266567=1, 598929=1, 3245421=1, 3658601=1}]
```

> 完整代码请查阅 [EventTimeSessionGroupWindowExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/function/window/EventTimeSessionGroupWindowExample.java)

参考：
- [Group Window Aggregation](https://nightlies.apache.org/flink/flink-docs-release-1.13/docs/dev/table/sql/queries/window-agg/#group-window-aggregation)
