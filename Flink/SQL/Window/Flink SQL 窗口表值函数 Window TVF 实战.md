---
layout: post
author: smartsi
title: Flink SQL 窗口表值函数 Window TVF 实战
date: 2022-10-03 21:59:21
tags:
  - Flink SQL

categories: Flink
permalink: flink-sql-table-valued-function-in-action
---

> Flink 1.13.5

窗口 TVF 是 Flink 定义的多态表函数(缩写 PTF)。PTF 是 SQL 2016 标准的一部分，是一个特殊的表函数，可以将表作为参数。因为 PTF 在语义上像表一样使用，所以它们的调用发生在 SELECT 语句的 FROM 子句中。窗口 TVF 是传统 Grouped Window 函数的替代品。窗口 TVF 更符合 SQL 标准，也更强大，可以支持复杂的基于窗口的计算，例如 Window TopN, Window Join。但是，Grouped Window 函数只能支持窗口聚合。

## 1. 窗口函数

Apache Flink 提供了 3 个内置窗口 TVF：TUMBLE、HOP 和 CUMULATE。

### 1.1 TUMBLE TVF

TUMBLE 函数将每个元素分配给指定窗口大小的滚动窗口。滚动窗口有固定的大小，不重叠。例如假设你指定一个大小为 5 分钟的滚动窗口，Flink 会每五分钟启动一个新窗口，如下图所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-sql-table-valued-function-in-action-1.png?raw=true)

TUMBLE 函数根据时间属性字段为表的每一行分配一个窗口。在流模式中，时间属性字段必须是事件或处理时间属性；在批处理模式下，必须为 TIMESTAMP 或者 TIMESTAMP_LTZ 类型的属性。TUMBLE 函数的返回值是一个新表，包含了原表的所有列，以及另外 3 列：window_start、window_end、window_time。window_time 用来指示分配的窗口。原表中的时间属性 timecol 会作为窗口 TVF 之后的一个常规时间戳列。具体如下使用 TUMBLE 函数：
```sql
TUMBLE(TABLE data, DESCRIPTOR(timecol), size [, offset ])
```
可以看到 TUMBLE 函数有三个必选参数，一个可选参数:
- data：是一个表参数，可以是具有时间属性列的任何表。
- timecol：是一个列描述符，表示基于 data 表上的哪个时间属性列来分配滚动窗口。
- size：指定滚动窗口的大小。
- offset：是一个可选参数，指定从一个时刻开始滚动（窗口启动的偏移量）。

#### 1.1.1 基于处理时间

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
  window_start, window_end,
  COUNT(*) AS cnt,
  MIN(`time`) AS min_time,
  MAX(`time`) AS max_time,
  COLLECT(DISTINCT pid) AS pid_set
FROM TABLE(
    TUMBLE(TABLE user_behavior, DESCRIPTOR(process_time), INTERVAL '1' MINUTES)
)
GROUP BY window_start, window_end
```
我们将这个查询的结果，通过 INSERT INTO 语句写到之前定义的 user_behavior_cnt Print 表中。最终执行结果如下所示：
```
+I[2022-10-03T16:10, 2022-10-03T16:11, 10, 2022-10-01 23:02:50, 2022-10-01 23:03:11, {3827899=1, 5153036=1, 266784=1, 2266567=1, 2951368=1, 3745169=1, 598929=1, 1531036=1, 2286574=1, 3658601=1}]
+I[2022-10-03T16:11, 2022-10-03T16:12, 3, 2022-10-01 23:02:59, 2022-10-01 23:04:06, {1046201=1, 3245421=1, 2971043=1}]
```

> 完整代码请查阅[ProcessTimeTumbleWindowTVFExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/function/tvf/ProcessTimeTumbleWindowTVFExample.java)

#### 1.1.2 基于事件时间

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
  window_start, window_end,
  COUNT(*) AS cnt,
  MIN(`time`) AS min_time,
  MAX(`time`) AS max_time,
  COLLECT(DISTINCT pid) AS pid_set
FROM TABLE(
    TUMBLE(TABLE user_behavior, DESCRIPTOR(ts_ltz), INTERVAL '1' MINUTES)
)
GROUP BY window_start, window_end
```
在这里计算消费对应的商品ID列表，只是为了演示基于事件时间在出现乱序时是如何处理的。我们将这个查询的结果通过 INSERT INTO 语句写到之前定义的 user_behavior_cnt Print 表中。最终执行结果如下所示：
```
+I[2022-10-01T23:02, 2022-10-01T23:03, 6, 2022-10-01 23:02:50, 2022-10-01 23:02:57, {3827899=1, 266784=1, 2951368=1, 3745169=1, 1531036=1, 2286574=1}]
+I[2022-10-01T23:03, 2022-10-01T23:04, 4, 2022-10-01 23:03:04, 2022-10-01 23:03:15, {2266567=1, 598929=1, 3245421=1, 3658601=1}]
```
因为 pid = 5153036 和 1046201 的数据记录延迟太长时间，当它到达时它本应该属于的窗口早已触发计算后并销毁，导致该数据记录被丢弃。

> 完整代码请查阅[EventTimeTumbleWindowTVFExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/function/tvf/EventTimeTumbleWindowTVFExample.java)

### 1.2 HOP TVF

与 TUMBLE 函数一样，HOP 函数也是将元素分配给指定窗口大小的窗口，在这称之为跳跃窗口(或者滑动窗口)。不一样的地方是，可以通过窗口滑动参数控制窗口启动的频率(滑动步长)。如果滑动步长小于窗口大小，那么跳跃窗口会发生重叠。在本例中，元素会被分配给多个窗口。例如，将数据记录分配给窗口大小为 10 分钟的窗口，并且每 5 分钟滑动一次。这样，每隔 5 分钟就会有一个新窗口，包含了最近 10 分钟内到达的事件，如下图所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-sql-table-valued-function-in-action-2.png?raw=true)

HOP 函数分配的窗口覆盖了窗口大小间隔内的行，并基于时间属性字段进行滑动。在流模式中，时间属性字段必须是事件或处理时间属性；在批处理模式下，必须为 TIMESTAMP 或者 TIMESTAMP_LTZ 类型的属性。HOP 的返回值是一个新表，包含了原表的所有列，以及另外 3 列：window_start、window_end、window_time。window_time 用来指示分配的窗口。原表中的时间属性 timecol 会作为窗口 TVF 之后的一个常规时间戳列。具体如下使用 HOP 函数：
```sql
HOP(TABLE data, DESCRIPTOR(timecol), slide, size [, offset ])
```
可以看到 HOP 函数有四个必选参数，一个可选参数:
- data：是一个表参数，可以是具有时间属性列的任何表。
- timecol：是一个列描述符，表示基于 data 表上的哪个时间属性列来分配滚动窗口。
- slide：指定窗口的滑动步长（启动的频率）。
- size：指定窗口的大小。
- offset：是一个可选参数，指定从一个时刻开始滚动（窗口启动的偏移量）。

#### 1.2.1 基于处理时间

输入、输出与 TUMBLE 函数中一样，在这不再赘述。假设我们的需求是基于处理时间每 30 秒计算最近一分钟内用户的消费次数，最早消费时间和最后消费时间以及消费对应的商品ID列表，如下所示：
```sql
INSERT INTO user_behavior_cnt
SELECT
  window_start, window_end,
  COUNT(*) AS cnt,
  MIN(`time`) AS min_time,
  MAX(`time`) AS max_time,
  COLLECT(DISTINCT pid) AS pid_set
FROM TABLE(
    HOP(TABLE user_behavior, DESCRIPTOR(process_time), INTERVAL '30' SECONDS, INTERVAL '1' MINUTES)
)
GROUP BY window_start, window_end
```
我们将这个查询的结果通过 INSERT INTO 语句写到之前定义的 user_behavior_cnt Print 表中。最终执行结果如下所示：
```
+I[2022-10-03T16:46:30, 2022-10-03T16:47:30, 11, 2022-10-01 23:02:50, 2022-10-01 23:03:15, {3827899=1, 5153036=1, 266784=1, 2266567=1, 2951368=1, 598929=1, 3745169=1, 1531036=1, 3245421=1, 2286574=1, 3658601=1}]
+I[2022-10-03T16:47, 2022-10-03T16:48, 8, 2022-10-01 23:02:56, 2022-10-01 23:04:06, {5153036=1, 2266567=1, 2951368=1, 1046201=1, 598929=1, 3245421=1, 2971043=1, 3658601=1}]
+I[2022-10-03T16:47:30, 2022-10-03T16:48:30, 2, 2022-10-01 23:02:59, 2022-10-01 23:04:06, {1046201=1, 2971043=1}]
```

> 完整代码请查阅[ProcessTimeHopWindowTVFExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/function/tvf/ProcessTimeHopWindowTVFExample.java)

#### 1.2.2 基于事件时间

输入、输出与 TUMBLE 函数中一样，在这不再赘述。假设我们的需求是基于事件时间每 30 秒计算最近一分钟内用户的消费次数，最早消费时间和最后消费时间以及消费对应的商品ID列表，如下所示：
```sql
INSERT INTO user_behavior_cnt
SELECT
  window_start, window_end,
  COUNT(*) AS cnt,
  MIN(`time`) AS min_time,
  MAX(`time`) AS max_time,
  COLLECT(DISTINCT pid) AS pid_set
FROM TABLE(
    HOP(TABLE user_behavior, DESCRIPTOR(ts_ltz), INTERVAL '30' SECONDS, INTERVAL '1' MINUTES)
)
GROUP BY window_start, window_end
```
我们将这个查询的结果通过 INSERT INTO 语句写到之前定义的 user_behavior_cnt Print 表中。最终执行结果如下所示：
```
+I[2022-10-01T23:02, 2022-10-01T23:03, 6, 2022-10-01 23:02:50, 2022-10-01 23:02:57, {3827899=1, 266784=1, 2951368=1, 3745169=1, 1531036=1, 2286574=1}]
+I[2022-10-01T23:02:30, 2022-10-01T23:03:30, 12, 2022-10-01 23:02:50, 2022-10-01 23:03:15, {3827899=1, 5153036=1, 266784=1, 2266567=1, 2951368=1, 1046201=1, 598929=1, 3745169=1, 1531036=1, 3245421=1, 2286574=1, 3658601=1}]
+I[2022-10-01T23:03, 2022-10-01T23:04, 4, 2022-10-01 23:03:04, 2022-10-01 23:03:15, {2266567=1, 598929=1, 3245421=1, 3658601=1}]
```
> 完整代码请查阅[EventTimeHopWindowTVFExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/function/tvf/EventTimeHopWindowTVFExample.java)

### 1.3 CUMULATE TVF

累积窗口在某些情况下非常有用。例如，每日仪表盘绘制从 00:00 到每分钟的累计 UV, 10:00 的 UV 表示从 00:00 到 10:00 的UV总数。这可以通过 CUMULATE 窗口轻松地实现。

CUMULATE 函数将元素分配给窗口，这些窗口覆盖了初始步长间隔内的行，并每一步扩展一个步长(窗口起始时间不变，只改变窗口结束时间)，直到到达窗口大小。你可以认为 CUMULATE 函数本质上分配给一个有最大窗口大小的 TUMBLE 窗口，只是一开始窗口的大小不是最大窗口大小，只是一个步长的大小。每一次都会扩大一个步长，直到到达窗口大小。这些窗口具有相同的窗口起始时间以及步长差异的窗口结束时间。所以可以通过累积窗口实现提前输出 TUMBLE 窗口的能力。

例如，你有一个窗口大小为1天的累积窗口，步长设置为一个小时。在这种情况下你每小时都会得到一个新的窗口：`[00:00,01:00)`，`[00:00,02:00)`，`[00:00,03:00)`，…，`[00:00,24:00)`。这些窗口都有相同的起始时间，窗口结束时间有几个步长的差异。由于步长设置为1小时，所以每小时都会产生一个新的窗口，窗口结束时间都在前一个窗口结束时间基础之上再添加一个小时。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-sql-table-valued-function-in-action-3.png?raw=true)

CUMULATE 函数根据时间属性列分配窗口，并提前滑动输出窗口截止到当前的计算结果。在流模式中，时间属性字段必须是事件或处理时间属性；在批处理模式下，必须为 TIMESTAMP 或者 TIMESTAMP_LTZ 类型的属性。CUMULATE 函数的返回值是一个新表，包含了原表的所有列，以及另外 3 列：window_start、window_end、window_time。window_time 用来指示分配的窗口。原表中的时间属性 timecol 会作为窗口 TVF 之后的一个常规时间戳列。具体如下使用 CUMULATE 函数：
```sql
CUMULATE(TABLE data, DESCRIPTOR(timecol), step, size)
```
可以看到 CUMULATE 函数有一共有四个必选参数：
- data：是一个表参数，可以是具有时间属性列的任何表。
- timecol：是一个列描述符，表示基于 data 表上的哪个时间属性列来分配滚动窗口。
- step：指定在累积窗口结束之间每次窗口增加的窗口大小（窗口大小动态变化）。
- size：指定窗口的大小。

#### 1.3.1 基于处理时间

输入、输出与 TUMBLE 函数中一样，在这不再赘述。假设我们的需求是基于处理时间计算每一分钟内用户的消费次数，最早消费时间和最后消费时间以及消费对应的商品ID列表，但是我们不想等到窗口结束才输出计算结果，而是每 10 秒钟输出一次窗口截止到当前的结果，如下所示：
```sql
INSERT INTO user_behavior_cnt
SELECT
  window_start, window_end,
  COUNT(*) AS cnt,
  MIN(`time`) AS min_time,
  MAX(`time`) AS max_time,
  COLLECT(DISTINCT pid) AS pid_set
FROM TABLE(
    CUMULATE(TABLE user_behavior, DESCRIPTOR(process_time), INTERVAL '10' SECONDS, INTERVAL '1' MINUTES)
)
GROUP BY window_start, window_end
```
我们将这个查询的结果通过 INSERT INTO 语句写到之前定义的 user_behavior_cnt Print 表中。最终执行结果如下所示：
```
+I[2022-10-03T17:36, 2022-10-03T17:36:50, 2, 2022-10-01 23:02:50, 2022-10-01 23:02:52, {3827899=1, 3745169=1}]
+I[2022-10-03T17:36, 2022-10-03T17:37, 4, 2022-10-01 23:02:50, 2022-10-01 23:02:54, {3827899=1, 266784=1, 3745169=1, 2286574=1}]
+I[2022-10-03T17:37, 2022-10-03T17:37:10, 2, 2022-10-01 23:02:57, 2022-10-01 23:03:04, {2266567=1, 1531036=1}]
+I[2022-10-03T17:37, 2022-10-03T17:37:20, 4, 2022-10-01 23:02:56, 2022-10-01 23:03:06, {2266567=1, 2951368=1, 1531036=1, 3658601=1}]
+I[2022-10-03T17:37, 2022-10-03T17:37:30, 6, 2022-10-01 23:02:56, 2022-10-01 23:03:11, {5153036=1, 2266567=1, 2951368=1, 598929=1, 1531036=1, 3658601=1}]
+I[2022-10-03T17:37, 2022-10-03T17:37:40, 8, 2022-10-01 23:02:56, 2022-10-01 23:03:15, {5153036=1, 2266567=1, 2951368=1, 1046201=1, 598929=1, 1531036=1, 3245421=1, 3658601=1}]
+I[2022-10-03T17:37, 2022-10-03T17:37:50, 9, 2022-10-01 23:02:56, 2022-10-01 23:04:06, {5153036=1, 2266567=1, 2951368=1, 1046201=1, 598929=1, 1531036=1, 3245421=1, 3658601=1, 2971043=1}]
+I[2022-10-03T17:37, 2022-10-03T17:38, 9, 2022-10-01 23:02:56, 2022-10-01 23:04:06, {5153036=1, 2266567=1, 2951368=1, 1046201=1, 598929=1, 1531036=1, 3245421=1, 3658601=1, 2971043=1}]
```

> 完整代码请查阅[ProcessTimeCumulateWindowTVFExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/function/tvf/ProcessTimeCumulateWindowTVFExample.java)

#### 1.3.2 基于事件时间

输入、输出与 TUMBLE 函数中一样，在这不再赘述。假设我们的需求是基于事件时间计算每一分钟内用户的消费次数，最早消费时间和最后消费时间以及消费对应的商品ID列表，但是我们不想等到窗口结束才输出计算结果，而是每 10 秒钟输出一次窗口截止到当前的结果，如下所示：
```sql
INSERT INTO user_behavior_cnt
SELECT
  window_start, window_end,
  COUNT(*) AS cnt,
  MIN(`time`) AS min_time,
  MAX(`time`) AS max_time,
  COLLECT(DISTINCT pid) AS pid_set
FROM TABLE(
    CUMULATE(TABLE user_behavior, DESCRIPTOR(ts_ltz), INTERVAL '10' SECONDS, INTERVAL '1' MINUTES)
)
GROUP BY window_start, window_end
```
我们将这个查询的结果通过 INSERT INTO 语句写到之前定义的 user_behavior_cnt Print 表中。最终执行结果如下所示：
```
+I[2022-10-01T23:02, 2022-10-01T23:03, 6, 2022-10-01 23:02:50, 2022-10-01 23:02:57, {3827899=1, 266784=1, 2951368=1, 3745169=1, 1531036=1, 2286574=1}]
+I[2022-10-01T23:03, 2022-10-01T23:03:10, 2, 2022-10-01 23:03:04, 2022-10-01 23:03:06, {2266567=1, 3658601=1}]
+I[2022-10-01T23:03, 2022-10-01T23:03:20, 4, 2022-10-01 23:03:04, 2022-10-01 23:03:15, {2266567=1, 598929=1, 3245421=1, 3658601=1}]
+I[2022-10-01T23:03, 2022-10-01T23:03:30, 4, 2022-10-01 23:03:04, 2022-10-01 23:03:15, {2266567=1, 598929=1, 3245421=1, 3658601=1}]
+I[2022-10-01T23:03, 2022-10-01T23:03:40, 4, 2022-10-01 23:03:04, 2022-10-01 23:03:15, {2266567=1, 598929=1, 3245421=1, 3658601=1}]
+I[2022-10-01T23:03, 2022-10-01T23:03:50, 4, 2022-10-01 23:03:04, 2022-10-01 23:03:15, {2266567=1, 598929=1, 3245421=1, 3658601=1}]
+I[2022-10-01T23:03, 2022-10-01T23:04, 4, 2022-10-01 23:03:04, 2022-10-01 23:03:15, {2266567=1, 598929=1, 3245421=1, 3658601=1}]
```

> 完整代码请查阅[EventTimeCumulateWindowTVFExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/function/tvf/EventTimeCumulateWindowTVFExample.java)

## 2. 窗口偏移量

Offset 是一个可选参数，表示窗口的偏移量。可以是正数也可以是负数，Offset 的默认值为 0。如果设置不同的偏移值，同一条记录可能会分配给不同的窗口中。例如，对于一个窗口大小为 10 分钟的 Tumble 窗口，时间戳为 `2021-06-30 00:00:04` 的记录会分配到哪个窗口中呢?具体如下图所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-sql-table-valued-function-in-action-4.png?raw=true)

时间戳为 `2021-06-30 00:00:04` 的记录分配到的窗口就是红色虚线穿过的窗口，可以看到：
- 如果 Offset 值为 -16 MINUTE，则将记录分配给窗口 `[2021-06-29 23:54:00,2021-06-30 00:04:00)`。
- 如果 Offset 值为 -6 MINUTE，则将记录分配给窗口 `[2021-06-29 23:54:00,2021-06-30 00:04:00)`。
- 如果 Offset 值为 -4 MINUTE，记录分配给窗口 `[2021-06-29 23:56:00,2021-06-30 00:06:00)`。
- 如果 Offset 值为 0，则将记录分配给窗口 `[2021-06-30 00:00:00,2021-06-30 00:10:00)`。
- 如果 Offset 值为 4 MINUTE，记录分配给窗口 `[2021-06-29 23:54:00,2021-06-30 00:04:00)`。
- 如果 Offset 值为 6 MINUTE，则记录分配给窗口 `[2021-06-29 23:56:00,2021-06-30 00:06:00)`。
- 如果 Offset 值为 16 MINUTE，则记录分配给窗口 `[2021-06-29 23:56:00,2021-06-30 00:06:00)`。

从中可以看出 Offset 值本质上是相对于 Offset = 0 窗口的偏移量。例如 Offset 值为 -16 MINUTE 表示相对于 Offset = 0 的窗口向左偏移 16 分钟。我们还可以发现，一些窗口偏移量参数对窗口有相同的影响。在上面的例子中，-16 分钟，-6 分钟和 4 分钟对于 10 分钟大小的滚动窗口具有相同的效果（数据记录分配到的窗口时间区间完全一样）。
