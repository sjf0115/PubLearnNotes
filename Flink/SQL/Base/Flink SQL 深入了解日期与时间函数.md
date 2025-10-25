https://mp.weixin.qq.com/s/lVxzv-YJwVvFmYwzgi8lXg


在实时数据处理中，时间是一个核心概念。Flink SQL 提供了一系列强大的日期和时间函数，帮助开发者进行时间相关的计算和转换。无论是用于窗口聚合、事件时间处理，还是简单的日期格式调整，这些函数都至关重要。


## 1. 当前时间函数

这些函数用于获取当前的系统时间：
- LOCALTIME: 以本地时区返回当前 SQL 时间，返回类型为 `time(0)`
- LOCALTIMESTAMP: 以本地时区返回当前 SQL 时间戳，返回类型为 `timestamp(3)`
- CURRENT_DATE: 以本地时区返回当前 SQL 日期，返回类型为 `DATE`
- CURRENT_TIME: 与 LOCALTIME 功能相同
- CURRENT_TIMESTAMP: 以本地时区返回当前 SQL 时间戳，返回类型为 `TIMESTAMP_LTZ(3)`
- NOW(): 与 CURRENT_TIMESTAMP 功能相同

### 1.1 LOCALTIME/CURRENT_TIME

> LOCALTIME 与 LOCAL_TIME 相同语义(同义词)

以本地时区返回当前 SQL 时间：
```sql
Flink SQL> SELECT LOCALTIME, CURRENT_TIME;
+----+-----------+--------------+
| op | LOCALTIME | CURRENT_TIME |
+----+-----------+--------------+
| +I |  23:04:52 |     23:04:52 |
+----+-----------+--------------+
Received a total of 1 row
```
返回类型为 `time(0)`：
```sql
Flink SQL> CREATE VIEW view1 AS SELECT LOCALTIME, CURRENT_TIME;
[INFO] Execute statement succeed.

Flink SQL> DESC view1;
+--------------+---------+-------+-----+--------+-----------+
|         name |    type |  null | key | extras | watermark |
+--------------+---------+-------+-----+--------+-----------+
|    LOCALTIME | TIME(0) | false |     |        |           |
| CURRENT_TIME | TIME(0) | false |     |        |           |
+--------------+---------+-------+-----+--------+-----------+
2 rows in set
```
需要注意的是在流模式下对每个记录进行计算。但是在批处理模式下，只在查询开始时计算一次，并对每一行使用相同的计算结果。

### 1.2 LOCALTIMESTAMP

以本地时区返回当前 SQL 时间戳：
```sql
Flink SQL> SELECT LOCALTIMESTAMP;
+----+-------------------------+
| op |          LOCALTIMESTAMP |
+----+-------------------------+
| +I | 2025-10-25 22:54:03.639 |
+----+-------------------------+
Received a total of 1 row
```
返回类型为 `timestamp(3)`：
```sql
Flink SQL> CREATE VIEW view2 AS SELECT LOCALTIMESTAMP;
[INFO] Execute statement succeed.

Flink SQL> DESC view2;
+----------------+--------------+-------+-----+--------+-----------+
|           name |         type |  null | key | extras | watermark |
+----------------+--------------+-------+-----+--------+-----------+
| LOCALTIMESTAMP | TIMESTAMP(3) | false |     |        |           |
+----------------+--------------+-------+-----+--------+-----------+
1 row in set
```
需要注意的是在流模式下对每个记录进行计算。但是在批处理模式下，只在查询开始时计算一次，并对每一行使用相同的计算结果。

### 1.3 CURRENT_DATE

以本地时区返回当前 SQL 日期：
```sql
Flink SQL> SELECT CURRENT_DATE;
+----+--------------+
| op | CURRENT_DATE |
+----+--------------+
| +I |   2025-10-25 |
+----+--------------+
Received a total of 1 row
```
返回类型为 `DATE`：
```sql
Flink SQL> CREATE VIEW view3 AS SELECT CURRENT_DATE;
[INFO] Execute statement succeed.

Flink SQL> DESC view3;
+--------------+------+-------+-----+--------+-----------+
|         name | type |  null | key | extras | watermark |
+--------------+------+-------+-----+--------+-----------+
| CURRENT_DATE | DATE | false |     |        |           |
+--------------+------+-------+-----+--------+-----------+
1 row in set
```
需要注意的是在流模式下对每个记录进行计算。但是在批处理模式下，只在查询开始时计算一次，并对每一行使用相同的计算结果。

### 1.4 CURRENT_TIMESTAMP/NOW()

> 与 LOCALTIMESTAMP 一样均是返回当前 SQL 时间戳，但是 CURRENT_TIMESTAMP 返回带时区的时间戳。
> CURRENT_TIMESTAMP 与 NOW() 相同语义(同义词)

以本地时区返回当前 SQL 时间戳：
```sql
Flink SQL> SELECT CURRENT_TIMESTAMP;
+----+-------------------------+
| op |       CURRENT_TIMESTAMP |
+----+-------------------------+
| +I | 2025-10-25 23:08:29.348 |
+----+-------------------------+
Received a total of 1 row
```
返回类型为 `TIMESTAMP_LTZ(3)`：
```sql
Flink SQL> CREATE VIEW view4 AS SELECT CURRENT_TIMESTAMP;
[INFO] Execute statement succeed.

Flink SQL> DESC view4;
+-------------------+------------------+-------+-----+--------+-----------+
|              name |             type |  null | key | extras | watermark |
+-------------------+------------------+-------+-----+--------+-----------+
| CURRENT_TIMESTAMP | TIMESTAMP_LTZ(3) | false |     |        |           |
+-------------------+------------------+-------+-----+--------+-----------+
1 row in set
```
需要注意的是在流模式下对每个记录进行计算。但是在批处理模式下，只在查询开始时计算一次，并对每一行使用相同的计算结果。

### 1.5 CURRENT_ROW_TIMESTAMP()

以本地时区返回当前 SQL 时间戳：
```sql
Flink SQL> SELECT CURRENT_ROW_TIMESTAMP();
+----+-------------------------+
| op |                  EXPR$0 |
+----+-------------------------+
| +I | 2025-10-25 23:11:04.325 |
+----+-------------------------+
Received a total of 1 row
```
返回类型为 `TIMESTAMP_LTZ(3)`：
```sql
Flink SQL> CREATE VIEW view5 AS SELECT CURRENT_ROW_TIMESTAMP();
[INFO] Execute statement succeed.

Flink SQL> DESC view5;
+--------+------------------+-------+-----+--------+-----------+
|   name |             type |  null | key | extras | watermark |
+--------+------------------+-------+-----+--------+-----------+
| EXPR$0 | TIMESTAMP_LTZ(3) | false |     |        |           |
+--------+------------------+-------+-----+--------+-----------+
1 row in set
```
与 CURRENT_TIMESTAMP 一样均是返回当前 SQL 时间戳，但是 `CURRENT_ROW_TIMESTAMP()` 无论在批处理模式还是流模式下，都会对每个记录进行计算。

> 批处理模式下不再是在查询开始时计算一次。

## 2. 时间属性提取函数

提供了一个通用的 `EXTRACT(timeintervalunit FROM temporal)` 方法从日期、时间或时间戳中提取特定部分，例如年、月、日、小时等：
```sql
SELECT
    EXTRACT(YEAR FROM DATE '2025-10-25') AS `year`,
    EXTRACT(QUARTER FROM DATE '2025-10-25') AS `quarter`,
    EXTRACT(MONTH FROM DATE '2025-10-25') AS `month`,
    EXTRACT(WEEK FROM DATE '2025-10-25') AS `week`,
    EXTRACT(DOY FROM DATE '2025-10-25') AS `day_of_year`,
    EXTRACT(DAY FROM DATE '2025-10-25') AS `day_of_month`,
    EXTRACT(HOUR FROM TIMESTAMP '2025-10-25 23:11:04') AS `hour`,
    EXTRACT(MINUTE FROM TIMESTAMP '2025-10-25 23:11:04') AS `minute`,
    EXTRACT(SECOND FROM TIMESTAMP '2025-10-25 23:11:04') AS `second`;
```

![](img-flink-sql-data-time-function-1.png)

除此之外还提供了一些简写模式常用提取方法：
- YEAR(date): 提取年份，等价于 `EXTRACT(YEAR FROM date)`
- QUARTER(date): 提取季度(1-4之间的数值)，等价于 `EXTRACT(QUARTER FROM date)`
- MONTH(date): 提取月份(1-12之间的数值)，等价于 `EXTRACT(MONTH FROM date)`
- WEEK(date): 提取周数(1-53之间的数值)，等价于 `EXTRACT(WEEK FROM date)`
- DAYOFYEAR(date): 提取一年中的第几天(1-366之间的数值)，等价于 `EXTRACT(DOY FROM date)`
- DAYOFMONTH(date): 提取一月中的第几天(1-31之间的数值)，等价于 `EXTRACT(DAY FROM date)`
- HOUR(timestamp): 提取小时(0-23之间的数值)，等价于 `EXTRACT(HOUR FROM timestamp)`
- MINUTE(timestamp): 提取分钟(0-59之间的数值)，等价于 `EXTRACT(MINUTE FROM timestamp)`
- SECOND(timestamp): 提取秒(0-59之间的数值)，等价于 `EXTRACT(SECOND FROM timestamp)`

示例如下所示：
```sql
SELECT
    YEAR(DATE '2025-10-25') AS `year`,
    QUARTER(DATE '2025-10-25') AS `quarter`,
    MONTH(DATE '2025-10-25') AS `month`,
    WEEK(DATE '2025-10-25') AS `week`,
    DAYOFYEAR(DATE '2025-10-25') AS `day_of_year`,
    DAYOFMONTH(DATE '2025-10-25') AS `day_of_month`,
    HOUR(TIMESTAMP '2025-10-25 23:11:04') AS `hour`,
    MINUTE(TIMESTAMP '2025-10-25 23:11:04') AS `minute`,
    SECOND(TIMESTAMP '2025-10-25 23:11:04') AS `second`;
```

![](img-flink-sql-data-time-function-2.png)

## 3. 日期时间格式化与解析

DATE_FORMAT(timestamp, format): 将时间戳格式化为字符串。

DATE_FORMAT(timestamp, format): 将时间戳格式化为字符串。

TO_DATE(string, format): 将字符串解析为日期。

TO_TIMESTAMP(string, format): 将字符串解析为时间戳。


常用格式符号:

yyyy: 四位年份

MM: 两位月份

dd: 两位日期

HH: 24小时制的小时

mm: 分钟

ss: 秒
