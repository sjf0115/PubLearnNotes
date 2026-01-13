MergeTree 引擎以及 MergeTree 家族中的其他引擎（例如 ReplacingMergeTree、AggregatingMergeTree）是 ClickHouse 中最常用、也最健壮的表引擎。

MergeTree 家族表引擎专为高数据摄取速率和海量数据规模而设计。 插入操作会创建表部件（part），这些部件会由后台进程与其他表部件进行合并。

MergeTree 家族表引擎的主要特性：

表的主键决定了每个表部件内部的排序顺序（聚簇索引）。主键并不引用单独的行，而是引用称为粒度（granule）的 8192 行数据块。这样可以使超大数据集的主键足够小，从而始终保留在主内存中，同时仍然能够快速访问磁盘上的数据。

表可以使用任意分区表达式进行分区。分区裁剪可以在查询条件允许的情况下跳过读取某些分区。

数据可以在多个集群节点之间进行复制，以实现高可用、故障切换以及零停机升级。参见 Data replication。

MergeTree 表引擎支持多种统计信息种类和采样方法，以帮助进行查询优化。

> 尽管名称相似，Merge 引擎与 `*MergeTree` 引擎是不同的。


## 2. 语法

```sql
CREATE TABLE [IF NOT EXISTS] [db.]table_name [ON CLUSTER cluster]
(
    name1 [type1] [[NOT] NULL] [DEFAULT|MATERIALIZED|ALIAS|EPHEMERAL expr1] [COMMENT ...] [CODEC(codec1)] [STATISTICS(stat1)] [TTL expr1] [PRIMARY KEY] [SETTINGS (name = value, ...)],
    name2 [type2] [[NOT] NULL] [DEFAULT|MATERIALIZED|ALIAS|EPHEMERAL expr2] [COMMENT ...] [CODEC(codec2)] [STATISTICS(stat2)] [TTL expr2] [PRIMARY KEY] [SETTINGS (name = value, ...)],
    ...
    INDEX index_name1 expr1 TYPE type1(...) [GRANULARITY value1],
    INDEX index_name2 expr2 TYPE type2(...) [GRANULARITY value2],
    ...
    PROJECTION projection_name_1 (SELECT <COLUMN LIST EXPR> [GROUP BY] [ORDER BY]),
    PROJECTION projection_name_2 (SELECT <COLUMN LIST EXPR> [GROUP BY] [ORDER BY])
) ENGINE = MergeTree()
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

- ENGINE：引擎名称和参数
  - `ENGINE = MergeTree()`。MergeTree 引擎没有参数。
- ORDER BY：排序键
  - 由列名或任意表达式组成的元组。示例：`ORDER BY (CounterID + 1, EventDate)`。
  - 如果未定义主键（即未指定 PRIMARY KEY），ClickHouse 会将排序键用作主键。
  - 如果不需要排序，可以使用语法 `ORDER BY tuple()`。
- PARTITION BY：分区键  
  - 可选。在大多数情况下不需要分区键；
  - 即使需要分区，通常按月分区已经足够，无需使用比'按月'更细粒度的分区键。
  - 分区并不会加速查询（与 ORDER BY 表达式不同）。
  - 不要使用过于细粒度的分区。不要按客户端标识符或名称对数据进行分区（应将客户端标识符或名称作为 ORDER BY 表达式中的第一列）。
  - 要按月进行分区，使用 `toYYYYMM(date_column)` 表达式，其中 date_column 是一个类型为 Date 的日期列。此处的分区名称采用 "YYYYMM" 格式。
- PRIMARY KEY：主键
  - 如果它与排序键不同。可选。
  - 指定排序键（使用 ORDER BY 子句）会隐式地指定主键。通常无需在排序键之外再单独指定主键。
- SAMPLE BY：采样表达式
  - 如果指定该表达式，则它必须包含在主键中。采样表达式的结果必须为无符号整数。
  - 示例：`SAMPLE BY intHash32(UserID) ORDER BY (CounterID, EventDate, intHash32(UserID))`。
- TTL：

## 3. 说明

### 3.1 TTL

TTL 即 Time To Live，顾名思义，它表示数据的存活时间，用于指定数据值的生命周期。在 MergeTree 中，可以为某个列字段或整张表设置 TTL。当时间到达时：
- 如果是列字段级别的 TTL，则会删除这一列的数据；
- 如果是表级别的 TTL，则会删除整张表的数据；
- 如果同时设置了列级别和表级别的 TTL，则会以先到期的那个为主。

无论是列级别还是表级别的 TTL，都需要依托某个 DateTime 或 Date 类型的字段，通过对这个时间字段的 INTERVAL 操作，来表述 TTL 的过期时间，例如：
```sql
TTL time_col + INTERVAL 3 DAY
```
上述语句表示数据的存活时间是 `time_col` 时间的 3 天之后。又例如：
```sql
TTL time_col + INTERVAL 1 MONTH
```
上述语句表示数据的存活时间是 time_col 时间的 1 月之后。INTERVAL 完整的操作包括 SECOND、MINUTE、HOUR、DAY、WEEK、MONTH、QUARTER 和 YEAR。

#### 3.1.1 列级别TTL

如果想要设置列级别的 TTL，则需要在定义表字段的时候，为它们声明 TTL 表达式，**主键字段不能被声明 TTL**。以下面的语句为例：
```sql
CREATE TABLE ttl_table_v1 (
    id String,
    create_time DateTime,
    code String TTL create_time + INTERVAL 10 SECOND,
    type UInt8 TTL create_time + INTERVAL 10 SECOND
)
ENGINE = MergeTree
PARTITION BY toYYYYMM (create_time)
ORDER BY id
```
其中，create_time 是日期类型，列字段 code 与 type 均被设置了 TTL，它们的存活时间是在 create_time 的取值基础之上向后延续 10秒。

现在写入测试数据，其中第一行数据 create_time 取当前的系统时间，而第二行数据的时间比第一行增加10分钟：
```sql
INSERT INTO TABLE ttl_table_v1 VALUES
  ('A000', now(),'C1',1),
  ('A000',now()+ INTERVAL 10 MINUTE,'C1',1)

SELECT * FROM ttl_table_v1
┌─id───┬─────create_time──┬─code─┬─type─┐
│ A000  │ 2019-06-12 22:49:00    │ C1    │     1 │
│ A000  │ 2019-06-12 22:59:00    │ C1    │     1 │
└────┴───────────────┴────┴─────┘
```
接着心中默数10秒，然后执行 optimize 命令强制触发 TTL 清理：
```
optimize TABLE ttl_table_v1 FINAL
```
再次查询 ttl_table_v1 则能够看到，由于第一行数据满足 TTL 过期条件 （当前系统时间 >=create_time+10秒） ，它们的 code 和 type 列会被还原为数据类型的默认值：
```

```
如果想要修改列字段的 TTL，或是为已有字段添加 TTL，则可以使用 ALTER 语句，示例如下：
```sql
ALTER TABLE ttl_table_v1 MODIFY COLUMN code String TTL create_time + INTERVAL 1 DAY
```
目前ClickHouse没有提供取消列级别TTL的方法。

#### 3.1.2 表级别TTL

如果想要为整张数据表设置TTL，需要在MergeTree的表参数中增加TTL表达式，例如下面的语句：
```sql
CREATE TABLE ttl_table_v2 (
    id String,
    create_time DateTime,
    code String TTL create_time + INTERVAL 1 MINUTE,
    type UInt8
)
ENGINE = MergeTree
PARTITION BY toYYYYMM (create_time)
ORDER BY create_time
TTL create_time + INTERVAL 1 DAY;
```
ttl_table_v2 整张表被设置了 TTL，当触发 TTL 清理时，那些满足过期时间的数据行将会被整行删除。同样，表级别的 TTL 也支持修改，修改的方法如下：
```sql
ALTER TABLE ttl_table_v2 MODIFY TTL create_time + INTERVAL 3 DAY
```
> 表级别TTL目前也没有取消的方法。





https://clickhouse.com/docs/zh/engines/table-engines/mergetree-family/mergetree  
