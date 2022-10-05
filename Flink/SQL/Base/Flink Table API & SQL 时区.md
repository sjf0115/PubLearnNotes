https://zhuanlan.zhihu.com/p/266526305
https://blog.csdn.net/hyunbar/article/details/121682399
https://mp.weixin.qq.com/s/KaWJ99oGn3WJysfc5OcmTA


Flink 提供了丰富的 Date 和 Time 数据类型，包括 DATE、TIME、TIMESTAMP、TIMESTAMP_LTZ、INTERVAL YEAR TO MONTH、INTERVAL DAY TO SECOND（详见日期和时间）。 Flink 支持在会话级别设置时区（详见 table.local-time-zone）。 Flink 的这些时间戳数据类型和时区支持使得跨时区处理业务数据变得容易。

## 1. TIMESTAMP vs TIMESTAMP_LTZ

### 1.1 TIMESTAMP

- TIMESTAMP(p) 是 TIMESTAMP(p) WITHOUT TIME ZONE 的缩写，精度 p 支持的范围是 0 到 9，默认为 6。
- TIMESTAMP 描述了一个时间戳，表示年、月、日、小时、分钟、秒和小数秒。
- TIMESTAMP 可以从字符串文字中指定，例如
```
Flink SQL> SELECT TIMESTAMP '1970-01-01 00:00:04.001';
+----+-------------------------+
| op |                  EXPR$0 |
+----+-------------------------+
| +I | 1970-01-01 00:00:04.001 |
+----+-------------------------+
Received a total of 1 row
```

### 1.2 TIMESTAMP_LTZ

- TIMESTAMP_LTZ(p) 是 TIMESTAMP(p) WITH LOCAL TIME ZONE 的缩写，精度 p 支持范围为 0 到 9，默认为 6。
- TIMESTAMP_LTZ 描述时间线上的一个绝对时间点，表示从时间原点流逝过的时间。用一个表示纪元毫秒的 long 值和一个表示纳秒毫秒的 int 值表示。同一时刻，从时间原点流逝的时间在所有时区都是相同的，所以这个 Long 值是绝对时间的概念。当我们在不同的时区去观察这个值，我们会用本地的时区去解释成 “年-月-日-时-分-秒” 的可读格式。TIMESTAMP_LTZ 类型也更加符合用户在不同时区下的使用习惯。每个 TIMESTAMP_LTZ 类型的数据都在当前会话中配置的本地时区进行解释，以进行计算和可视化。
- TIMESTAMP_LTZ 没有字符串表示形式，因此不能从字符串中指定。
- TIMESTAMP_LTZ 可以用于跨时区业务，因为是绝对时间点描述了不同时区的同一瞬时点。在同一时间点，世界上所有机器的 System.currentTimeMillis() 返回的值都是一样的。这两者是一样的逻辑。

```sql
Flink SQL> SET table.local-time-zone=UTC;
[INFO] Session property has been set.

Flink SQL> SELECT TO_TIMESTAMP_LTZ(1652453226541, 3);
+----+-------------------------+
| op |                  EXPR$0 |
+----+-------------------------+
| +I | 2022-05-13 14:47:06.541 |
+----+-------------------------+
Received a total of 1 row

Flink SQL> SET table.local-time-zone=Asia/Shanghai;
[INFO] Session property has been set.

Flink SQL> SELECT TO_TIMESTAMP_LTZ(1652453226541, 3);
+----+-------------------------+
| op |                  EXPR$0 |
+----+-------------------------+
| +I | 2022-05-13 22:47:06.541 |
+----+-------------------------+
Received a total of 1 row
```

## 2. Time Zone

本地时区定义当前会话时区 ID。你可以在 Sql Client 或 Applications 中配置时区。可以使用如下方式在 Sql Client 中设置时区：
```sql
-- set to UTC time zone
Flink SQL> SET 'table.local-time-zone' = 'UTC';

-- set to Shanghai time zone
Flink SQL> SET 'table.local-time-zone' = 'Asia/Shanghai';

-- set to Los_Angeles time zone
Flink SQL> SET 'table.local-time-zone' = 'America/Los_Angeles';
```
你也可以在 Java 程序中设置时区：
```java
EnvironmentSettings envSetting = EnvironmentSettings.inStreamingMode();
TableEnvironment tEnv = TableEnvironment.create(envSetting);

// set to UTC time zone
tEnv.getConfig().setLocalTimeZone(ZoneId.of("UTC"));

// set to Shanghai time zone
tEnv.getConfig().setLocalTimeZone(ZoneId.of("Asia/Shanghai"));

// set to Los_Angeles time zone
tEnv.getConfig().setLocalTimeZone(ZoneId.of("America/Los_Angeles"));
```
在会话中设置时区在 Flink SQL 中很有用。

### 2.1 决定时间函数返回值

如下时间函数会受到配置的时区影响：
- LOCALTIME
- LOCALTIMESTAMP
- CURRENT_DATE
- CURRENT_TIME
- CURRENT_TIMESTAMP
- CURRENT_ROW_TIMESTAMP()
- NOW()
- PROCTIME()

```sql
Flink SQL> SET 'sql-client.execution.result-mode' = 'tableau';
Flink SQL> CREATE VIEW MyView1 AS SELECT LOCALTIME, LOCALTIMESTAMP, CURRENT_DATE, CURRENT_TIME, CURRENT_TIMESTAMP, CURRENT_ROW_TIMESTAMP(), NOW(), PROCTIME();
Flink SQL> DESC MyView1;

+------------------------+-----------------------------+-------+-----+--------+-----------+
|                   name |                        type |  null | key | extras | watermark |
+------------------------+-----------------------------+-------+-----+--------+-----------+
|              LOCALTIME |                     TIME(0) | false |     |        |           |
|         LOCALTIMESTAMP |                TIMESTAMP(3) | false |     |        |           |
|           CURRENT_DATE |                        DATE | false |     |        |           |
|           CURRENT_TIME |                     TIME(0) | false |     |        |           |
|      CURRENT_TIMESTAMP |            TIMESTAMP_LTZ(3) | false |     |        |           |
|CURRENT_ROW_TIMESTAMP() |            TIMESTAMP_LTZ(3) | false |     |        |           |
|                  NOW() |            TIMESTAMP_LTZ(3) | false |     |        |           |
|             PROCTIME() | TIMESTAMP_LTZ(3) *PROCTIME* | false |     |        |           |
+------------------------+-----------------------------+-------+-----+--------+-----------+

Flink SQL> SET 'table.local-time-zone' = 'UTC';
Flink SQL> SELECT * FROM MyView1;
+-----------+-------------------------+--------------+--------------+-------------------------+-------------------------+-------------------------+-------------------------+
| LOCALTIME |          LOCALTIMESTAMP | CURRENT_DATE | CURRENT_TIME |       CURRENT_TIMESTAMP | CURRENT_ROW_TIMESTAMP() |                   NOW() |              PROCTIME() |
+-----------+-------------------------+--------------+--------------+-------------------------+-------------------------+-------------------------+-------------------------+
|  15:18:36 | 2021-04-15 15:18:36.384 |   2021-04-15 |     15:18:36 | 2021-04-15 15:18:36.384 | 2021-04-15 15:18:36.384 | 2021-04-15 15:18:36.384 | 2021-04-15 15:18:36.384 |
+-----------+-------------------------+--------------+--------------+-------------------------+-------------------------+-------------------------+-------------------------+


Flink SQL> SET 'table.local-time-zone' = 'Asia/Shanghai';
Flink SQL> SELECT * FROM MyView1;
+-----------+-------------------------+--------------+--------------+-------------------------+-------------------------+-------------------------+-------------------------+
| LOCALTIME |          LOCALTIMESTAMP | CURRENT_DATE | CURRENT_TIME |       CURRENT_TIMESTAMP | CURRENT_ROW_TIMESTAMP() |                   NOW() |              PROCTIME() |
+-----------+-------------------------+--------------+--------------+-------------------------+-------------------------+-------------------------+-------------------------+
|  23:18:36 | 2021-04-15 23:18:36.384 |   2021-04-15 |     23:18:36 | 2021-04-15 23:18:36.384 | 2021-04-15 23:18:36.384 | 2021-04-15 23:18:36.384 | 2021-04-15 23:18:36.384 |
+-----------+-------------------------+--------------+--------------+-------------------------+-------------------------+-------------------------+-------------------------+
```

### 2.2 TIMESTAMP_LTZ 字符串表示形式

会话时区可以用于将 TIMESTAMP_LTZ 值用字符串形式表示的时，即打印值时：将值转换为 STRING 类型、将值转换为 TIMESTAMP或者将 TIMESTAMP 值转换为 TIMESTAMP_LTZ：
```sql
Flink SQL> CREATE VIEW MyView2 AS SELECT TO_TIMESTAMP_LTZ(4001, 3) AS ltz, TIMESTAMP '1970-01-01 00:00:01.001'  AS ntz;
Flink SQL> DESC MyView2;
+------+------------------+-------+-----+--------+-----------+
| name |             type |  null | key | extras | watermark |
+------+------------------+-------+-----+--------+-----------+
|  ltz | TIMESTAMP_LTZ(3) |  true |     |        |           |
|  ntz |     TIMESTAMP(3) | false |     |        |           |
+------+------------------+-------+-----+--------+-----------+
```

## 3. 时间属性和时区

### 3.1 处理时间和时区

Flink SQL 通过函数 PROCTIME() 定义处理时间属性，函数返回类型为 TIMESTAMP_LTZ。

> 在 Flink 1.13 之前，PROCTIME() 的函数返回类型为 TIMESTAMP，返回值为 UTC 时区的 TIMESTAMP，例如在上海时间为 2021-03-01 12:00:00，但是 PROCTIME() 返回的是 2021-03-01 04:00:00，这是错误的。Flink 1.13 修复了这个问题，并使用 TIMESTAMP_LTZ 类型作为 PROCTIME() 的返回类型，用户不再需要处理时区问题。

PROCTIME() 始终代表我们的本地时间戳值，使用 TIMESTAMP_LTZ 类型也可以很好地支持夏令时。

```sql
Flink SQL> SET 'table.local-time-zone' = 'UTC';
Flink SQL> SELECT PROCTIME();

+-------------------------+
|              PROCTIME() |
+-------------------------+
| 2021-04-15 14:48:31.387 |
+-------------------------+

Flink SQL> SET 'table.local-time-zone' = 'Asia/Shanghai';
Flink SQL> SELECT PROCTIME();

+-------------------------+
|              PROCTIME() |
+-------------------------+
| 2021-04-15 22:48:31.387 |
+-------------------------+


Flink SQL> CREATE TABLE MyTable1 (
                  item STRING,
                  price DOUBLE,
                  proctime as PROCTIME()
            ) WITH (
                'connector' = 'socket',
                'hostname' = '127.0.0.1',
                'port' = '9999',
                'format' = 'csv'
           );

Flink SQL> CREATE VIEW MyView3 AS
            SELECT
                TUMBLE_START(proctime, INTERVAL '10' MINUTES) AS window_start,
                TUMBLE_END(proctime, INTERVAL '10' MINUTES) AS window_end,
                TUMBLE_PROCTIME(proctime, INTERVAL '10' MINUTES) as window_proctime,
                item,
                MAX(price) as max_price
            FROM MyTable1
                GROUP BY TUMBLE(proctime, INTERVAL '10' MINUTES), item;

Flink SQL> DESC MyView3;


+-----------------+-----------------------------+-------+-----+--------+-----------+
|           name  |                        type |  null | key | extras | watermark |
+-----------------+-----------------------------+-------+-----+--------+-----------+
|    window_start |                TIMESTAMP(3) | false |     |        |           |
|      window_end |                TIMESTAMP(3) | false |     |        |           |
| window_proctime | TIMESTAMP_LTZ(3) *PROCTIME* | false |     |        |           |
|            item |                      STRING | true  |     |        |           |
|       max_price |                      DOUBLE |  true |     |        |           |
+-----------------+-----------------------------+-------+-----+--------+-----------+
```
使用以下命令在终端中提取 MyTable1 的数据：
```
> nc -lk 9999
A,1.1
B,1.2
A,1.8
B,2.5
C,3.8

Flink SQL> SET 'table.local-time-zone' = 'UTC';
Flink SQL> SELECT * FROM MyView3;

+-------------------------+-------------------------+-------------------------+------+-----------+
|            window_start |              window_end |          window_procime | item | max_price |
+-------------------------+-------------------------+-------------------------+------+-----------+
| 2021-04-15 14:00:00.000 | 2021-04-15 14:10:00.000 | 2021-04-15 14:10:00.005 |    A |       1.8 |
| 2021-04-15 14:00:00.000 | 2021-04-15 14:10:00.000 | 2021-04-15 14:10:00.007 |    B |       2.5 |
| 2021-04-15 14:00:00.000 | 2021-04-15 14:10:00.000 | 2021-04-15 14:10:00.007 |    C |       3.8 |
+-------------------------+-------------------------+-------------------------+------+-----------+

Flink SQL> SET 'table.local-time-zone' = 'Asia/Shanghai';
Flink SQL> SELECT * FROM MyView3;
```

与 UTC 时区中的计算相比，返回不同的窗口开始、窗口结束和窗口 proctime。

```
+-------------------------+-------------------------+-------------------------+------+-----------+
|            window_start |              window_end |          window_procime | item | max_price |
+-------------------------+-------------------------+-------------------------+------+-----------+
| 2021-04-15 22:00:00.000 | 2021-04-15 22:10:00.000 | 2021-04-15 22:10:00.005 |    A |       1.8 |
| 2021-04-15 22:00:00.000 | 2021-04-15 22:10:00.000 | 2021-04-15 22:10:00.007 |    B |       2.5 |
| 2021-04-15 22:00:00.000 | 2021-04-15 22:10:00.000 | 2021-04-15 22:10:00.007 |    C |       3.8 |
+-------------------------+-------------------------+-------------------------+------+-----------+
```
处理时间窗口是不确定的，因此每次运行都会得到不同的窗口和不同的聚合。 上面的例子只是为了解释时区如何影响处理时间窗口。

### 3.2 事件时间和时区

Flink 支持在 TIMESTAMP 列和 TIMESTAMP_LTZ 列上定义事件时间属性。

#### 3.2.1 TIMESTAMP 上的事件时间属性

如果源中的时间戳数据表示为年-月-日-时-分-秒，通常是没有时区信息的字符串值，例如 2020-04-15 20:13:40.564，建议将事件时间属性定义为 TIMESTAMP 列：
```
Flink SQL> CREATE TABLE MyTable2 (
                  item STRING,
                  price DOUBLE,
                  ts TIMESTAMP(3), -- TIMESTAMP data type
                  WATERMARK FOR ts AS ts - INTERVAL '10' SECOND
            ) WITH (
                'connector' = 'socket',
                'hostname' = '127.0.0.1',
                'port' = '9999',
                'format' = 'csv'
           );

Flink SQL> CREATE VIEW MyView4 AS
            SELECT
                TUMBLE_START(ts, INTERVAL '10' MINUTES) AS window_start,
                TUMBLE_END(ts, INTERVAL '10' MINUTES) AS window_end,
                TUMBLE_ROWTIME(ts, INTERVAL '10' MINUTES) as window_rowtime,
                item,
                MAX(price) as max_price
            FROM MyTable2
            GROUP BY TUMBLE(ts, INTERVAL '10' MINUTES), item;

Flink SQL> DESC MyView4;


+----------------+------------------------+------+-----+--------+-----------+
|           name |                   type | null | key | extras | watermark |
+----------------+------------------------+------+-----+--------+-----------+
|   window_start |           TIMESTAMP(3) | true |     |        |           |
|     window_end |           TIMESTAMP(3) | true |     |        |           |
| window_rowtime | TIMESTAMP(3) *ROWTIME* | true |     |        |           |
|           item |                 STRING | true |     |        |           |
|      max_price |                 DOUBLE | true |     |        |           |
+----------------+------------------------+------+-----+--------+-----------+
```
使用以下命令在终端中提取 MyTable2 的数据：
```
> nc -lk 9999
A,1.1,2021-04-15 14:01:00
B,1.2,2021-04-15 14:02:00
A,1.8,2021-04-15 14:03:00
B,2.5,2021-04-15 14:04:00
C,3.8,2021-04-15 14:05:00
C,3.8,2021-04-15 14:11:00
```

```
Flink SQL> SET 'table.local-time-zone' = 'UTC';
Flink SQL> SELECT * FROM MyView4;
+-------------------------+-------------------------+-------------------------+------+-----------+
|            window_start |              window_end |          window_rowtime | item | max_price |
+-------------------------+-------------------------+-------------------------+------+-----------+
| 2021-04-15 14:00:00.000 | 2021-04-15 14:10:00.000 | 2021-04-15 14:09:59.999 |    A |       1.8 |
| 2021-04-15 14:00:00.000 | 2021-04-15 14:10:00.000 | 2021-04-15 14:09:59.999 |    B |       2.5 |
| 2021-04-15 14:00:00.000 | 2021-04-15 14:10:00.000 | 2021-04-15 14:09:59.999 |    C |       3.8 |
+-------------------------+-------------------------+-------------------------+------+-----------+
Flink SQL> SET 'table.local-time-zone' = 'Asia/Shanghai';
Flink SQL> SELECT * FROM MyView4;
```
与 UTC 时区中的计算相比，返回相同的窗口开始、窗口结束和窗口行时间。

```
+-------------------------+-------------------------+-------------------------+------+-----------+
|            window_start |              window_end |          window_rowtime | item | max_price |
+-------------------------+-------------------------+-------------------------+------+-----------+
| 2021-04-15 14:00:00.000 | 2021-04-15 14:10:00.000 | 2021-04-15 14:09:59.999 |    A |       1.8 |
| 2021-04-15 14:00:00.000 | 2021-04-15 14:10:00.000 | 2021-04-15 14:09:59.999 |    B |       2.5 |
| 2021-04-15 14:00:00.000 | 2021-04-15 14:10:00.000 | 2021-04-15 14:09:59.999 |    C |       3.8 |
+-------------------------+-------------------------+-------------------------+------+-----------+
```
#### 3.2.2 TIMESTAMP_LTZ 上的事件时间属性

如果数据源中的时间戳表示为一个纪元时间，通常用一个 Long 值表示，例如 1618989564564，在 1.13 版本之后建议将事件时间属性定义在 TIMESTAMP_LTZ 列上。此时定义在 TIMESTAMP_LTZ 类型上的各种 WINDOW 聚合，都能够自动的解决 8 小时的时区偏移问题，无需按照之前的 SQL 写法额外做时区的修改和订正。
```sql
Flink SQL> CREATE TABLE MyTable3 (
                  item STRING,
                  price DOUBLE,
                  ts BIGINT, -- long time value in epoch milliseconds
                  ts_ltz AS TO_TIMESTAMP_LTZ(ts, 3),
                  WATERMARK FOR ts_ltz AS ts_ltz - INTERVAL '10' SECOND
            ) WITH (
                'connector' = 'socket',
                'hostname' = '127.0.0.1',
                'port' = '9999',
                'format' = 'csv'
           );

Flink SQL> CREATE VIEW MyView5 AS
            SELECT
                TUMBLE_START(ts_ltz, INTERVAL '10' MINUTES) AS window_start,
                TUMBLE_END(ts_ltz, INTERVAL '10' MINUTES) AS window_end,
                TUMBLE_ROWTIME(ts_ltz, INTERVAL '10' MINUTES) as window_rowtime,
                item,
                MAX(price) as max_price
            FROM MyTable3
            GROUP BY TUMBLE(ts_ltz, INTERVAL '10' MINUTES), item;

Flink SQL> DESC MyView5;

+----------------+----------------------------+-------+-----+--------+-----------+
|           name |                       type |  null | key | extras | watermark |
+----------------+----------------------------+-------+-----+--------+-----------+
|   window_start |               TIMESTAMP(3) | false |     |        |           |
|     window_end |               TIMESTAMP(3) | false |     |        |           |
| window_rowtime | TIMESTAMP_LTZ(3) *ROWTIME* |  true |     |        |           |
|           item |                     STRING |  true |     |        |           |
|      max_price |                     DOUBLE |  true |     |        |           |
+----------------+----------------------------+-------+-----+--------+-----------+
```
MyTable3的输入数据为：
```
A,1.1,1618495260000  # The corresponding utc timestamp is 2021-04-15 14:01:00
B,1.2,1618495320000  # The corresponding utc timestamp is 2021-04-15 14:02:00
A,1.8,1618495380000  # The corresponding utc timestamp is 2021-04-15 14:03:00
B,2.5,1618495440000  # The corresponding utc timestamp is 2021-04-15 14:04:00
C,3.8,1618495500000  # The corresponding utc timestamp is 2021-04-15 14:05:00
C,3.8,1618495860000  # The corresponding utc timestamp is 2021-04-15 14:11:00
```

```
Flink SQL> SET 'table.local-time-zone' = 'UTC';
Flink SQL> SELECT * FROM MyView5;
+-------------------------+-------------------------+-------------------------+------+-----------+
|            window_start |              window_end |          window_rowtime | item | max_price |
+-------------------------+-------------------------+-------------------------+------+-----------+
| 2021-04-15 14:00:00.000 | 2021-04-15 14:10:00.000 | 2021-04-15 14:09:59.999 |    A |       1.8 |
| 2021-04-15 14:00:00.000 | 2021-04-15 14:10:00.000 | 2021-04-15 14:09:59.999 |    B |       2.5 |
| 2021-04-15 14:00:00.000 | 2021-04-15 14:10:00.000 | 2021-04-15 14:09:59.999 |    C |       3.8 |
+-------------------------+-------------------------+-------------------------+------+-----------+


Flink SQL> SET 'table.local-time-zone' = 'Asia/Shanghai';
Flink SQL> SELECT * FROM MyView5;
+-------------------------+-------------------------+-------------------------+------+-----------+
|            window_start |              window_end |          window_rowtime | item | max_price |
+-------------------------+-------------------------+-------------------------+------+-----------+
| 2021-04-15 22:00:00.000 | 2021-04-15 22:10:00.000 | 2021-04-15 22:09:59.999 |    A |       1.8 |
| 2021-04-15 22:00:00.000 | 2021-04-15 22:10:00.000 | 2021-04-15 22:09:59.999 |    B |       2.5 |
| 2021-04-15 22:00:00.000 | 2021-04-15 22:10:00.000 | 2021-04-15 22:09:59.999 |    C |       3.8 |
+-------------------------+-------------------------+-------------------------+------+-----------+
```
与 UTC 时区计算相比，返回不同的窗口开始、窗口结束和窗口行时间。

## 4. 夏令时支持

Flink SQL 支持在 TIMESTAMP_LTZ 列上定义时间属性，基于此，Flink SQL 在窗口处理中优雅地使用 TIMESTAMP 和 TIMESTAMP_LTZ 类型来支持夏令时。

Flink 使用时间戳字面量来分割窗口，并根据每一行的纪元时间将窗口分配给数据。这意味着 Flink 使用 TIMESTAMP 类型作为窗口开始和窗口结束（例如 TUMBLE_START 和 TUMBLE_END），使用 TIMESTAMP_LTZ 作为窗口时间属性（例如 TUMBLE_PROCTIME、TUMBLE_ROWTIME）。 给定滚动窗口的示例，Los_Angeles 的 DaylightTime 开始于时间 2021-03-14 02:00:00：
```
long epoch1 = 1615708800000L; // 2021-03-14 00:00:00
long epoch2 = 1615712400000L; // 2021-03-14 01:00:00
long epoch3 = 1615716000000L; // 2021-03-14 03:00:00, skip one hour (2021-03-14 02:00:00)
long epoch4 = 1615719600000L; // 2021-03-14 04:00:00
```
滚动窗口 [2021-03-14 00:00:00, 2021-03-14 00:04:00] 将在洛杉矶时区收集 3 小时的数据，但在其他非 DST 时间收集 4 小时的数据，用户要做的只是在 TIMESTAMP_LTZ 列上定义时间属性。

Flink 中的所有窗口，如 Hop 窗口、Session 窗口、Cumulative 窗口都遵循这种方式，并且 Flink SQL 中的所有操作都很好地支持了 TIMESTAMP_LTZ，因此 Flink 优雅地支持了夏令时区。

## 5. 批处理模式和流模式之间的区别

如下时间函数：
- LOCALTIME
- LOCALTIMESTAMP
- CURRENT_DATE
- CURRENT_TIME
- CURRENT_TIMESTAMP
- NOW()

Flink 根据执行模式评估它们的值。它们在流模式下针对每条记录进行评估。但在批处理模式下，它们会在查询开始时评估一次，并为每一行使用相同的结果。

无论是批处理模式还是流模式，都会为每条记录评估以下时间函数：
- CURRENT_ROW_TIMESTAMP()
- PROCTIME()

参考：https://nightlies.apache.org/flink/flink-docs-release-1.13/docs/dev/table/concepts/timezone/
