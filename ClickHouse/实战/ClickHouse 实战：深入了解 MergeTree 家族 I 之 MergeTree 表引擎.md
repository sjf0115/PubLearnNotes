
在当今的大数据时代，高效的数据存储与查询是每个数据工程师面临的挑战。ClickHouse 作为一款开源的列式数据库管理系统，凭借其卓越的查询性能在 OLAP 场景中脱颖而出。而这一切的核心基础，正是 MergeTree 引擎家族。作为 ClickHouse 中最重要、最复杂的表引擎，MergeTree 的设计哲学值得每一个数据从业者深入理解。

## 1. 概览

在 ClickHouse 中，按照特点可以将表引擎大致分为合并树(MergeTree)、外部存储、内存、文件、接口等表引擎，每一个系列的表引擎都有着独自的特点与使用场景。在它们之中，最为核心的当属 MergeTree 系列，因为它们拥有最为强大的性能和最广泛的使用场合。其中 MergeTree 有两层含义：
- 一是指 MergeTree 表引擎家族；
- 二是指 MergeTree 表引擎家族中最基础的 MergeTree 表引擎。

在整个家族中，除了基础表引擎 MergeTree 之外，常用的表引擎还有 `ReplacingMergeTree`、`SummingMergeTree`、`AggregatingMergeTree`、`CollapsingMergeTree` 和 `VersionedCollapsingMergeTree`。尽管名称相似，但是 Merge 引擎与 `*MergeTree` 引擎是不同的。MergeTree 系列的其他引擎在继承了基础 MergeTree 的能力之后，都为特定使用场景添加了额外功能。

MergeTree 作为家族系列最基础的表引擎，提供了弹性和高性能数据检索所需的大部分功能：列式存储、自定义分区、稀疏主索引、二级数据跳过索引等。MergeTree 基础表引擎可以视为单节点 ClickHouse 实例的默认表引擎，因为它功能全面且适用于各种使用场景。

## 2. 语法

```sql
CREATE TABLE [IF NOT EXISTS] [db.]table_name [ON CLUSTER cluster] (
    name1 [type1] [[NOT] NULL] [DEFAULT|MATERIALIZED|ALIAS|EPHEMERAL expr1] [COMMENT ...] [CODEC(codec1)] [STATISTICS(stat1)] [TTL expr1] [PRIMARY KEY] [SETTINGS (name = value, ...)],
    name2 [type2] [[NOT] NULL] [DEFAULT|MATERIALIZED|ALIAS|EPHEMERAL expr2] [COMMENT ...] [CODEC(codec2)] [STATISTICS(stat2)] [TTL expr2] [PRIMARY KEY] [SETTINGS (name = value, ...)],
    ...
    INDEX index_name1 expr1 TYPE type1(...) [GRANULARITY value1],
    INDEX index_name2 expr2 TYPE type2(...) [GRANULARITY value2],
    ...
    PROJECTION projection_name_1 (SELECT <COLUMN LIST EXPR> [GROUP BY] [ORDER BY]),
    PROJECTION projection_name_2 (SELECT <COLUMN LIST EXPR> [GROUP BY] [ORDER BY])
)
ENGINE = MergeTree()
ORDER BY expr
[PARTITION BY expr]
[PRIMARY KEY expr]
[SAMPLE BY expr]
[TTL expr
    [DELETE|TO DISK 'xxx'|TO VOLUME 'xxx' [, ...] ]
    [WHERE conditions]
    [GROUP BY key_expr [SET v1 = aggr_func(v1) [, v2 = aggr_func(v2) ...]] ] ]
[SETTINGS name = value, ...]
```
从上面可以看到创建一张 `MergeTree` 表的方法很简单，只需要设置 Engine 为 `MergeTree`：
```sql
ENGINE = MergeTree()
```
> MergeTree 引擎没有参数。

## 3. 关键特性

### 3.1 分区键

分区是 MergeTree 最核心的概念之一，它影响数据存储、查询性能和维护操作。分区键通过 `PARTITION BY` 语句来声明。分区是一个可选选项，在大多数情况下不需要分区键；
  - 即使需要分区，通常按月分区已经足够，无需使用比'按月'更细粒度的分区键。
  - 不要使用过于细粒度的分区。不要按客户端标识符或名称对数据进行分区（应将客户端标识符或名称作为 ORDER BY 表达式中的第一列）。
  - 要按月进行分区，使用 `toYYYYMM(date_column)` 表达式，其中 date_column 是一个类型为 Date 的日期列。此处的分区名称采用 "YYYYMM" 格式。

分区键既可以是单个列字段，也可以通过元组的形式使用多个列字段，同时它也支持使用列表达式。如果不声明分区键，则 ClickHouse 会生成一个名为 `all` 的分区。合理使用数据分区，可以有效减少查询时数据文件的扫描范围。

### 3.2 排序键

排序键通过 `ORDER BY` 语句来声明，用于指定在一个数据片段内，数据以何种标准排序。排序键既可以是单个列字段，例如 `ORDER BY column1`，也可以通过元组的形式使用多个列字段，例如 `ORDER BY(column1, column2)`。当使用多个列字段排序时，以 `ORDER BY(column1, column2)` 为例，在单个数据片段内，数据首先会以 column1 排序，相同 column1 的数据再按 column2 排序。如果不需要排序，可以使用语法 `ORDER BY tuple()`。

### 3.3 主键

主键通过 `PRIMARY KEY` 语句来声明。如果未定义主键（即未指定 `PRIMARY KEY`），ClickHouse 会将排序键用作主键。通常无需在排序键之外再单独指定主键，即无须刻意通过 `PRIMARY KEY` 声明。声明主键后会依照主键字段生成一级索引，用于加速表查询。

来自 OLTP 数据库的用户通常会在 ClickHouse 中寻找对应的概念。注意到 ClickHouse 支持 PRIMARY KEY 语法后，用户可能会倾向于直接沿用源 OLTP 数据库中的主键来理解 ClickHouse 的主键。这种做法有问题，因为 ClickHouse 主键是允许存在重复数据 (ReplacingMergeTree可以去重) 。

### 3.4 TTL

TTL 即 Time To Live，顾名思义，它表示数据的存活时间，用于指定数据值的生命周期。在 MergeTree 中，可以为某个列字段或整张表设置 TTL。当时间到达时：
- 如果是列字段级别的 TTL，则会删除这一列的数据，将该列的值替换为其数据类型的默认值；
- 如果是表级别的 TTL，则会删除那些满足过期时间的整行数据；
- 如果同时设置了列级别和表级别的 TTL，则会以先到期的那个为主。

无论是列级别还是表级别的 TTL，都需要依托某个 DateTime 或 Date 类型的字段，通过对这个时间字段的 INTERVAL 操作，来表述 TTL 的过期时间，例如：
```sql
TTL time_col + INTERVAL 3 DAY
```
上述语句表示数据列的生存时间为 3 天，从 time_col 列的时间开始计算，当该时间间隔结束时，该列会过期。又例如：
```sql
TTL time_col + INTERVAL 1 MONTH
```
上述语句表示数据列的生存时间为 1 个月，从 time_col 列的时间开始计算。INTERVAL 完整的操作包括 SECOND、MINUTE、HOUR、DAY、WEEK、MONTH、QUARTER 和 YEAR。

#### 3.5.1 列级别TTL

如果想要设置列级别的 TTL，则需要在定义表字段的时候，为字段声明 TTL 表达式，需要注意的是 **主键字段不能被声明 TTL**。以下面的语句为例：
```sql
CREATE TABLE t_column_ttl (
    id String,
    create_time DateTime,
    code String TTL create_time + INTERVAL 10 SECOND
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(create_time)
ORDER BY id;
```
其中，`create_time` 是日期类型，列字段 `code` 被设置了 TTL，存活时间是在 `create_time` 的取值基础之上向后延续 10秒。

现在写入测试数据，其中第一行数据 `create_time` 取当前的系统时间，而第二行数据的时间比第一行增加10分钟：
```sql
INSERT INTO TABLE t_column_ttl VALUES
  ('1', now(),'C1'),
  ('1', now()+ INTERVAL 10 MINUTE,'C1');

SELECT * FROM t_column_ttl;
┌─id─┬─────────create_time─┬─code─┐
│ 1  │ 2026-01-17 14:29:46 │ C1   │
│ 1  │ 2026-01-17 14:39:46 │ C1   │
└────┴─────────────────────┴──────┘
```
接着心中默数10秒，然后执行 `optimize` 命令强制触发 TTL 清理：
```sql
optimize TABLE t_column_ttl FINAL;
```
再次查询 `t_column_ttl` 则能够看到，由于第一行数据满足 TTL 过期条件（当前系统时间 >=create_time+10秒），code 列会被还原为数据类型的默认值：
```sql
SELECT * FROM t_column_ttl;
┌─id─┬─────────create_time─┬─code─┐
│ 1  │ 2026-01-17 14:29:46 │      │
│ 1  │ 2026-01-17 14:39:46 │ C1   │
└────┴─────────────────────┴──────┘
```
如果想要修改列字段的 TTL，或是为已有字段添加 TTL，则可以使用 ALTER 语句，示例如下：
```sql
ALTER TABLE t_column_ttl MODIFY COLUMN code String TTL create_time + INTERVAL 1 MINUTE;
```
> 目前 ClickHouse 没有提供取消列级别 TTL 的方法。

#### 3.5.2 表级别 TTL

如果想要为整张数据表设置 TTL，需要在 MergeTree 的表参数中增加 TTL 表达式，例如下面的语句：
```sql
CREATE TABLE t_table_ttl (
    id String,
    create_time DateTime,
    code String
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(create_time)
ORDER BY create_time
TTL create_time + INTERVAL 1 MINUTE;
```

现在写入测试数据，其中第一行数据 `create_time` 取当前的系统时间，而第二行数据的时间比第一行增加 10 分钟：
```sql
INSERT INTO TABLE t_table_ttl VALUES
  ('1', now(),'C1'),
  ('1', now()+ INTERVAL 10 MINUTE,'C1');

SELECT * FROM t_table_ttl;
┌─id─┬─────────create_time─┬─code─┐
│ 1  │ 2026-01-17 15:38:09 │ C1   │
│ 1  │ 2026-01-17 15:48:09 │ C1   │
└────┴─────────────────────┴──────┘
```
`t_table_ttl` 整张表被设置了 TTL，当触发 TTL 清理时，那些满足过期时间的数据行将会被整行删除。

表示数据行的生存时间为 1 分钟，从 create_time 列的时间开始计算，当1分钟结束时，该行会过期。`15:39:09`之后：
```sql
┌─id─┬─────────create_time─┬─code─┐
│ 1  │ 2026-01-17 15:48:09 │ C1   │
└────┴─────────────────────┴──────┘
```
`15:49:09`之后所有行都被删除。

同样，表级别的 TTL 也支持修改，修改的方法如下：
```sql
ALTER TABLE t_table_ttl MODIFY TTL create_time + INTERVAL 10 MINUTE;
```
> 表级别TTL目前也没有取消的方法。
