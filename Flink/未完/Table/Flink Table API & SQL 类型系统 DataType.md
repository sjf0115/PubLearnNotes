> Flink 版本：1.13.5

由于历史原因，在 Flink 1.9 之前，Flink 的 Table API & SQL 数据类型与 Flink 的 TypeInformation 紧密耦合。TypeInformation 主要用于 DataStream 和 DataSet API 中，为系统序列化和反序列化基于 JVM 的对象提供必要的信息。

但是，TypeInformation 原本的设计目的并不能表示不同实际 JVM 类的逻辑类型。因此 SQL 的标准类型很难与这种抽象进行映射。此外，某些类型也不符合 SQL 标准。从 Flink 1.9 开始，Table API & SQL 将获得一个新的类型系统 DataType。

## 1. 新的数据类型 DataType

Table API & SQL 中新的数据类型 DataType 描述了 Table 生态系统中值的逻辑类型，可以用来声明操作的输入和输出类型。Flink 的数据类型与 SQL 标准的数据类型比较相似，同时也支持 NULL/NOT NULL，例如如下所示：
- INT
- INT NOT NULL
- INTERVAL DAY TO SECOND(3)
- ROW<myField ARRAY<BOOLEAN>, myOtherField TIMESTAMP(3)>

在使用基于 JVM API 编写 Table API、定义 Connector、Catalogs 或者自定义函数中，需要使用 org.apache.flink.table.types.DataType 数据类型的实例。

### 1.1 作用

DataType 主要有两个作用：
- 声明逻辑类型：并不表达具体物理类型的存储和转换，但是定义了基于 JVM 的语言或者 Python 语言和 Table 编程环境之间的边界。
- 物理表示的提示：向 Planner 提供有关数据物理表示的提示。

对于基于 JVM 的语言，所有预定义的数据类型都在 org.apache.flink.table.api.DataTypes 下。

### 1.2 物理提示

Table 编程环境中，基于 SQL 的类型系统与程序指定的数据类型之间需要物理提示。例如，如下物理提示告诉运行时不要为逻辑 TIMESTAMP 使用 java.time.LocalDateTime 而是使用 java.sql.Timestamp：
```java
DataType t = DataTypes.TIMESTAMP(3).bridgedTo(java.sql.Timestamp.class);
```
如下物理提示告诉运行时不要为 ARRAY 使用装箱的整数数组而是使用基本数据类型的整数数组：
```java
DataType t = DataTypes.ARRAY(DataTypes.INT().notNull()).bridgedTo(int[].class);
```

需要注意的是，通常仅在扩展 API 时才需要物理提示。使用内置的 Source、Sink以及函数时不需要定义物理提示。

## 2. Planner 兼容性

每种数据类型的支持取决于使用的 Planner。Flink 的 Old Planner 在 Flink 1.9 版本之前就引入了，主要支持 TypeInformation，对数据类型的支持有限。Blink Planner 支持 Flink Planner 支持的全部类型，尤其包括 Java 表达式字符串和类型信息，例如 TIME,TIMESTAMP, INTERVAL, ARRAY, MULTISET 等。Blink Planner 支持如下 SQL 类型：

| Data Type | 备注 |
| :------------- | :------------- |
|	CHAR	|		|
|	VARCHAR	|		|
|	STRING	|		|
|	BOOLEAN	|		|
|	BYTES	|	BINARY and VARBINARY 还不支持	|
|	DECIMAL	|	支持固定精度和规模	|
|	TINYINT	|		|
|	SMALLINT	|		|
|	INTEGER	|		|
|	BIGINT	|		|
|	FLOAT	|		|
|	DOUBLE	|		|
|	DATE	|		|
|	TIME	|	精度仅支持 0|
|	TIMESTAMP	|		|
|	TIMESTAMP_LTZ	|		|
|	INTERVAL	|	仅支持 MONTH 和 SECOND(3) 的间隔 |
|	ARRAY	|		|
|	MULTISET	|		|
|	MAP	|		|
|	ROW	|		|
|	RAW	|		|
|	结构化类型	|	仅在用户定义的函数中使用	|

## 3. 常见数据类型

下面我们详细看一下所有内置的数据类型。

> 对于基于 JVM 的 Table API，这些类型也可以在 org.apache.flink.table.api.DataTypes 中使用。

### 3.1 字符串

#### 3.1.1 CHAR

具有固定长度字符串的数据类型：
```sql
CHAR
CHAR(n)
```
其中 n 表示字符数量。n 的值必须在 [1, 2147483647] 之间。如果未指定长度，n 默认为 1。

#### 3.1.2 VARCHAR / STRING

可变长度字符串的数据类型：
```sql
VARCHAR
VARCHAR(n)
STRING
```
其中 n 表示字符的最大数量。n 的值必须在 [1, 2147483647] 之间。如果未指定长度，n 默认为 1。STRING 等价于 VARCHAR(2147483647)。

### 3.2 二进制字符串

#### 3.2.1 BINARY

具有固定长度的二进制字符串数据类型（字节序列）：
```sql
BINARY
BINARY(n)
```
其中 n 是字节数量。n 的值必须在 [1, 2147483647] 之间。如果未指定长度，n 默认为 1。

#### 3.2.2 VARBINARY / BYTES

可变长度的二进制字符串数据类型（字节序列）：
```sql
VARBINARY
VARBINARY(n)
BYTES
```
其中 n 是字节的最大数量。n 的值必须在 [1, 2147483647] 之间。如果未指定长度，n 默认为 1。BYTES 等价于 VARBINARY(2147483647)。

### 3.3 精确数值

#### 3.3.1 DECIMAL

具有固定精度和小数位数的十进制数数据类型：
```sql
DECIMAL
DECIMAL(p)
DECIMAL(p, s)

DEC
DEC(p)
DEC(p, s)

NUMERIC
NUMERIC(p)
NUMERIC(p, s)
```
其中 p 是数字的位数（精度），s 是数字小数点右边的位数（尾数）。p 的值必须在 [1, 38] 之间。s 的值必须在 [0, p]。如果不指定 p，默认为是 10，同样 s 默认值为 0。

NUMERIC 和 DEC 都等价于这个类型。

#### 3.3.2 TINYINT

1 字节有符号整数的数据类型，取值范围 [-128, 127]：
```sql
TINYINT
```

#### 3.3.3 SMALLINT

2 字节有符号整数的数据类型，取值范围 [-32768, 32767]：
```sql
SMALLINT
```

#### 3.3.4 INT

4 字节有符号整数的数据类型，取值范围 [-2147483648, 2147483647]：
```sql
INT
INTEGER
```

INTEGER 与 INT 数据类型等价。

#### 3.3.5 BIGINT

8 字节有符号整数的数据类型，取值范围 [-9223372036854775808, 9223372036854775807]：
```sql
BIGINT
```

### 3.4 近似数值

#### 3.4.1 FLOAT

4 字节单精度浮点数的数据类型。与标准 SQL 相比，该类型不带参数：
```sql
FLOAT
```

#### 3.4.2 DOUBLE

8 字节双精度浮点数的数据类型：
```sql
DOUBLE

DOUBLE PRECISION
```
DOUBLE PRECISION 与 DOUBLE 等价。

### 3.4 日期和时间

#### 3.4.1 DATE

日期数据类型，格式为 '年-月-日'，取值范围 [0000-01-01, 9999-12-31]。与标准 SQL 相比，年的范围从 0000 开始：
```sql
DATE
```

#### 3.4.2 TIME

不带时区的时间数据类型，格式为 '小时:分钟:秒[.小数]'，精度可达纳秒，取值范围为 [00:00:00.000000000, 23:59:59.999999999]。与标准 SQL 相比，不支持闰秒（23:59:60 和 23:59:61），在语义上更接近于 java.time.LocalTime：
```sql
TIME
TIME(p)
```
使用 TIME(p) 来声明，其中 p 是秒的小数部分的位数（精度）。p 的值必须在 [0, 9] 之间。如果未指定精度，p 默认为 0。

#### 3.4.3 TIMESTAMP

不带时区的时间戳数据类型，格式为 '年-月-日 小时:分钟:秒[.小数]'，精度达到纳秒，取值范围为 [0000-01-01 00:00:00.000000000, 9999-12-31 23:59:59.999999999]。与标准 SQL 相比，不支持闰秒（23:59:60 和 23:59:61），语义上更接近于 java.time.LocalDateTime：
```sql
TIMESTAMP
TIMESTAMP(p)

TIMESTAMP WITHOUT TIME ZONE
TIMESTAMP(p) WITHOUT TIME ZONE
```
使用 TIMESTAMP(p) 来声明类型，其中 p 是秒的小数部分的位数（精度）。p 的值必须在 [0, 9] 之间。如果未指定精度，p 默认为 6。TIMESTAMP(p) WITHOUT TIME ZONE 与 TIMESTAMP(p) 等价。

#### 3.4.4 TIMESTAMP WITH TIME ZONE

带时区的时间戳数据类型，格式为 '年-月-日 小时:分钟:秒[.小数] 时区'，精度达到纳秒，取值范围为 [0000-01-01 00:00:00.000000000 +14:59, 9999-12-31 23:59:59.999999999 -14:59]：
```sql
TIMESTAMP WITH TIME ZONE
TIMESTAMP(p) WITH TIME ZONE
```

#### 3.4.5 TIMESTAMP_LTZ

带本地时区的时间戳数据类型，'年-月-日 小时:分钟:秒[.小数] 时区'，精度可达纳秒，取值范围为 [0000-01-01 00:00:00.000000000 +14:59, 9999-12-31 23:59:59.999999999 -14:59]。与标准 SQL 相比，不支持闰秒（23:59:60 和 23:59:61），在语义上更接近于 java.time.OffsetDateTime：
```sql
TIMESTAMP_LTZ
TIMESTAMP_LTZ(p)

TIMESTAMP WITH LOCAL TIME ZONE
TIMESTAMP(p) WITH LOCAL TIME ZONE
```
使用 TIMESTAMP_LTZ(p) 来声明类型，其中 p 是秒的小数部分的位数（精度）。p 的值必须在 [0, 9] 之间。如果未指定精度，那么 p 默认为 6。TIMESTAMP(p) WITH LOCAL TIME ZONE 与 TIMESTAMP_LTZ(p) 等价。

TIMESTAMP_LTZ 与 TIMESTAMP WITH TIME ZONE 的区别在于：TIMESTAMP WITH TIME ZONE 的时区信息是携带在数据中的，例如 2022-01-01 00:00:00.000000000 +08:00；而 TIMESTAMP_LTZ 的时区信息不是携带在数据中的，而是由 Flink SQL 任务的全局配置决定的，我们可以由 table.local-time-zone 参数来设置时区。

#### 3.4.6 INTERVAL YEAR TO MONTH

以年和月表示的粗粒度时间间隔，精度为月份。时间间隔记录的是一段时间长度，例如1年零3个月(或者理解为时间偏移量)。时间间隔范围从 -9999-11 到 +9999-11。可以使用如下几种格式来表示：
```sql
INTERVAL YEAR
INTERVAL YEAR(p)
INTERVAL YEAR(p) TO MONTH
INTERVAL MONTH
```
其中 p 是年的位数(年的精度)。p 的值是一个 1~4 的整数，默认精度为 2。例如 p 为 3，表示可以在时间间隔中为年数存储三位数字，即范围从 -999 到 999。

年时间间隔语法格式如下：
```
INTERVAL '[+|-]年数' YEAR
INTERVAL '[+|-]年数' YEAR(年精度)
```
如下所示为示例：
```sql
-- 年
SELECT
    ts + INTERVAL '-1' YEAR        AS year_minus,  -- 1年    -- 2021-05-01 12:10:15.456
    ts + INTERVAL '+1' YEAR        AS year_add,    -- 1年    -- 2023-05-01 12:10:15.456
    ts + INTERVAL '10' YEAR(2)     AS year_p2,     -- 10年   -- 2032-05-01 12:10:15.456
    ts + INTERVAL '1000' YEAR(4)   AS year_p4      -- 1000年 -- 3022-05-01 12:10:15.456
FROM (
  -- 2022-05-01 12:10:15.456
  SELECT TO_TIMESTAMP_LTZ(1651378215456, 3) AS ts
);
```
> 默认为 `+`，可以省略。

输出结果如下：
```
+----+-------------------------+-------------------------+-------------------------+-------------------------+
| op |              year_minus |                year_add |                 year_p2 |                 year_p4 |
+----+-------------------------+-------------------------+-------------------------+-------------------------+
| +I | 2021-05-01 12:10:15.456 | 2023-05-01 12:10:15.456 | 2032-05-01 12:10:15.456 | 3022-05-01 12:10:15.456 |
+----+-------------------------+-------------------------+-------------------------+-------------------------+
```

年月时间间隔语法格式如下：
```
INTERVAL '[+|-]年数-月数' YEAR(年精度) TO MONTH
INTERVAL '[+|-]月数' MONTH
```
如下所示为示例：
```sql
-- 月
SELECT
    ts + INTERVAL '1-03' YEAR TO MONTH AS year_month,    -- 1年3个月 -- 2023-08-01 12:10:15.456
    ts + INTERVAL '15' MONTH           AS month_simple,  -- 15个月  -- 2023-08-01 12:10:15.456
    ts + INTERVAL '+3' MONTH          AS month_add,      -- 3个月   -- 2022-08-01 12:10:15.456
    ts + INTERVAL '-3' MONTH          AS month_minus     -- 3个月   -- 2022-02-01 12:10:15.456
FROM (
  -- 2022-05-01 12:10:15.456
  SELECT TO_TIMESTAMP_LTZ(1651378215456, 3) AS ts
);
```
输出结果如下：
```
+----+-------------------------+-------------------------+-------------------------+-------------------------+
| op |              year_month |            month_simple |               month_add |             month_minus |
+----+-------------------------+-------------------------+-------------------------+-------------------------+
| +I | 2023-08-01 12:10:15.456 | 2023-08-01 12:10:15.456 | 2022-08-01 12:10:15.456 | 2022-02-01 12:10:15.456 |
+----+-------------------------+-------------------------+-------------------------+-------------------------+
```

#### 3.4.7 INTERVAL DAY TO SECOND

以天、时、分、秒、纳秒表示的细粒度时间间隔，最高精度为纳秒。时间间隔范围是[-999999 23:59:59.999999999，+999999 23:59:59.999999999]。可以使用如下几种格式来表示：
```sql
INTERVAL DAY
INTERVAL DAY(p1)
INTERVAL DAY(p1) TO HOUR
INTERVAL DAY(p1) TO MINUTE
INTERVAL DAY(p1) TO SECOND(p2)
INTERVAL HOUR
INTERVAL HOUR TO MINUTE
INTERVAL HOUR TO SECOND(p2)
INTERVAL MINUTE
INTERVAL MINUTE TO SECOND(p2)
INTERVAL SECOND
INTERVAL SECOND(p2)
```
其中 p1 表示天数精度的位数，p1 的取值范围是[1，6]，默认为2。p2 表示秒的小数位数，p2 的取值范围是[0，9]，默认为6。

日时间间隔语法格式如下：
```
INTERVAL '[+|-]日数' DAY
INTERVAL '[+|-]日数' DAY(日精度)
```
如下所示日时间间隔的示例：
```sql
-- 日
SELECT
    ts + INTERVAL '+1' DAY     AS day_add,    -- 1天    -- 2022-05-02 12:10:15.456
    ts + INTERVAL '-1' DAY     AS day_minus,  -- 1天    -- 2022-04-30 12:10:15.456
    ts + INTERVAL '10' DAY(2)  AS day_p2,     -- 10天   -- 2022-05-11 12:10:15.456
    ts + INTERVAL '365' DAY(3) AS day_p3      -- 365天  -- 2023-05-01 12:10:15.456
FROM (
  -- 2022-05-01 12:10:15.456
  SELECT TO_TIMESTAMP_LTZ(1651378215456, 3) AS ts
);
```
输出结果如下：
```
+----+-------------------------+-------------------------+-------------------------+-------------------------+
| op |                 day_add |               day_minus |                  day_p2 |                  day_p3 |
+----+-------------------------+-------------------------+-------------------------+-------------------------+
| +I | 2022-05-02 12:10:15.456 | 2022-04-30 12:10:15.456 | 2022-05-11 12:10:15.456 | 2023-05-01 12:10:15.456 |
+----+-------------------------+-------------------------+-------------------------+-------------------------+
```
小时时间间隔语法格式如下：
```
INTERVAL '[+|-]日数 小时数' DAY TO HOUR
INTERVAL '[+|-]日数 小时数' DAY(日精度) TO HOUR
INTERVAL '[+|-]小时数' HOUR
```
如下所示小时时间间隔的示例：
```sql
-- 小时
SELECT
    ts + INTERVAL '-1 03' DAY TO HOUR      AS day_hour_minus, -- 1天3小时  -- 2022-05-02 15:10:15.456
    ts + INTERVAL '1 03' DAY TO HOUR       AS day_hour,    -- 1天3小时  -- 2022-05-02 15:10:15.456
    ts + INTERVAL '10 03' DAY(2) TO HOUR   AS day_p2_hour, -- 10天3小时 -- 2022-05-11 15:10:15.456
    ts + INTERVAL '+3' HOUR                AS hour_add,    -- 3小时    -- 2022-05-01 15:10:15.456
    ts + INTERVAL '-3' HOUR                AS hour_minus   -- 3小时    -- 2022-05-01 09:10:15.456
FROM (
  -- 2022-05-01 12:10:15.456
  SELECT TO_TIMESTAMP_LTZ(1651378215456, 3) AS ts
);
```
输出结果如下：
```
+----+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+
| op |          day_hour_minus |                day_hour |             day_p2_hour |                hour_add |              hour_minus |
+----+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+
| +I | 2022-04-30 09:10:15.456 | 2022-05-02 15:10:15.456 | 2022-05-11 15:10:15.456 | 2022-05-01 15:10:15.456 | 2022-05-01 09:10:15.456 |
+----+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+
```
分钟时间间隔语法格式如下：
```
INTERVAL '[+|-]日数 小时数:分钟数' DAY TO MINUTE
INTERVAL '[+|-]日数 小时数:分钟数' DAY(日精度) TO MINUTE
INTERVAL '[+|-]小时数:分钟数' HOUR TO MINUTE
INTERVAL '[+|-]分钟数' MINUTE
```
如下所示小时时间间隔的示例：
```
+----+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+
| op |              day_minute |        day_minute_minus |          hour_to_minute |         hour_to_minute0 |    hour_to_minute_minus |              minute_add |            minute_minus |
+----+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+
| +I | 2022-05-02 15:30:15.456 | 2022-04-30 08:50:15.456 | 2022-05-01 15:30:15.456 | 2022-05-01 15:30:15.456 | 2022-05-01 08:50:15.456 | 2022-05-01 12:30:15.456 | 2022-05-01 11:50:15.456 |
+----+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+
Received a total of 1 row
```

```
+----+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+
| op |           day_to_second |        day_to_second_ms |          hour_to_second |       hour_to_second_ms |        minute_to_second |     minute_to_second_ms |             only_second |          only_second_ms |
+----+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+
| +I | 2022-05-02 15:30:30.456 | 2022-05-02 15:30:30.567 | 2022-05-01 15:30:30.456 | 2022-05-01 15:30:30.567 | 2022-05-01 12:30:30.456 | 2022-05-01 12:30:30.567 | 2022-05-01 12:10:30.456 | 2022-05-01 12:10:30.567 |
+----+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+-------------------------+
Received a total of 1 row
```

### 3.5 结构化数据类型

#### 3.5.1 ARRAY

具有相同子类型元素的数组数据类型。与标准 SQL 相比，无法指定数组的最大长度，而是固定为 2147483647。另外，任何有效类型都可以作为子类型：
```sql
ARRAY<t>
t ARRAY
```
可以使用 ARRAY<t> 来声明，其中 t 是所包含元素的数据类型。t ARRAY 更接近标准 SQL，并且等价于 ARRAY<t>。例如，INT ARRAY 等价于 ARRAY<INT>。

#### 3.5.2 MAP

键与值映射的关联数组数据类型。键和值都可以为 NULL，但是不能包含重复的键；每个键最多可以映射到一个值；对于元素类型没有限制。Map 类型是标准 SQL 的扩展：
```sql
MAP<kt, vt>
```
可以使用 AMAP<kt, vt> 来声明，其中 kt 是键的数据类型，vt 是值的数据类型。

#### 3.5.3 MULTISET

多重集合的数据类型。与集合不同的是，可以允许具有相同子类型的元素有多个实例。元素类型没有限制：
```sql
MULTISET<t>
t MULTISET
```
可以使用 MULTISET<t> 来声明，其中 t 是元素的数据类型。t MULTISET 更接近标准 SQL，并且等价于 MULTISET<t>。例如，INT MULTISET 等价于 MULTISET<INT>。

#### 3.5.4 ROW

字段序列的数据类型。字段由字段名称、字段类型以及可选的字段描述组成。Table 中一行数据最常用的类型就是 Row 类型。在这种情况下，行中的列数据与 Row 类型中具有相同下标位置的字段对应。与标准 SQL 相比，可选的字段描述简化了复杂结构的处理。Row 类型类似于其他非标准兼容框架中的 STRUCT 类型：
```sql
ROW<n0 t0, n1 t1, ...>
ROW<n0 t0 'd0', n1 t1 'd1', ...>

ROW(n0 t0, n1 t1, ...)
ROW(n0 t0 'd0', n1 t1 'd1', ...)
```
可以使用 ROW<n0 t0 'd0', n1 t1 'd1', ...> 来声明，其中 n 是具有唯一的字段名称，t 是字段的逻辑类型，d 是字段的描述。ROW(...) 更接近标准 SQL。例如，ROW(myField INT, myOtherField BOOLEAN) 等价于 ROW<myField INT, myOtherField BOOLEAN>。

原文：[Data Types](https://ci.apache.org/projects/flink/flink-docs-release-1.9/dev/table/types.html)
