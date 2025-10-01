
### 1. Skewed Tables

Skewed Tables 语法从 Hive 0.10.0 版本开始引入，详细参阅 [HIVE-3072](https://issues.apache.org/jira/browse/HIVE-3072) 、 [HIVE-3649](https://issues.apache.org/jira/browse/HIVE-3649) 以及 [HIVE-3026](https://issues.apache.org/jira/browse/HIVE-3026)。如果表中一个或多个列具有倾斜值，可以通过 Skewed Tables 来提升性能。通过指定哪些值经常出现，即出现了严重倾斜，Hive 会自动将这些值拆分为单独的文件（如果使用[ListBucketing](https://cwiki.apache.org/confluence/display/Hive/ListBucketing)时拆分为一个目录），基于此查询时可以选择跳过或包含整个文件（目录）。

#### 1.1 创建

可以在表创建期间在每个表上指定。如下示例展示了具有三个倾斜值的列：
```sql
CREATE TABLE list_bucket_single (
  key STRIN,
  value STRING
)
SKEWED BY (key) ON (1,5,6) [STORED AS DIRECTORIES];
```
> 可选子句 `STORED AS DIRECTORIES` 指定是否是 ListBucketing

上面示例只有一列发生了倾斜，如果有多个列发生倾斜怎么处理？如下所示 col1, col2 两列出现了数据倾斜：
```sql
CREATE TABLE list_bucket_multiple (
  col1 STRING,
  col2 int,
  col3 STRING
)
SKEWED BY (col1, col2) ON (
  ('s1',1),
  ('s3',3),
  ('s13',13),
  ('s78',78)
) [STORED AS DIRECTORIES];
```

#### 1.2 修改

可以使用 ALTER TABLE 语句更改表的 SKEWED 和 STORED AS DIRECTORIES 选项。

如下所示将 table_a 修改为 Skewed 表：
```sql
ALTER TABLE table_a
SKEWED BY (col1_name, col2_name, col3_name) ON (
  (col1_value_1, col2_value_1, col2_value_1),
  (col1_value_2, col2_value_2, col2_value_2)
[STORED AS DIRECTORIES];
```

如下所示将 table_b 修改为非 Skewed 表：
```sql
ALTER TABLE table_b NOT SKEWED;
```
NOT SKEWED 选项修改表为普通表并关闭 ListBucketing 功能（因为 ListBucketing 表总是倾斜）。这会影响在 ALTER 语句之后创建的分区，但不会影响在 ALTER 语句之前创建的分区。

如下所示关闭 table_c 表的 ListBucketing 功能：
```sql
ALTER TABLE table_c NOT STORED AS DIRECTORIES;
```
关闭 ListBucketing 功能，但仍然是一个倾斜表。

如下所示修改 table_d 表倾斜的位置：
```sql
ALTER TABLE table_d
SET SKEWED LOCATION (
  col_name1="location1", col_name2="location2"
);
```
这会更改 ListBucketing 的映射位置。

### 2. List Bucketing Table

如下表中字段 c 存在数据倾斜，一般情况下 c 的值中大约有 10 个值严重倾斜，其他值基数都很小，当然，每天 x 字段值倾斜的值也可能不一样：
```sql
CREATE TABLE partition_table (
  a STRIN,
  b STRING,
  c STRING
)
PARTITIONED BY (dt STRING);
```
假设我们有如下查询：
```sql
SELECT a, b
FROM partition_table
WHERE c = 10;
```
如何更有效的执行上述查询呢？可以通过以下方式解决。

#### 2.1 分区

为 c 字段创建一个分区：
```sql
CREATE TABLE partition_table (
  a STRIN,
  b STRING
)
PARTITIONED BY (
  dt STRING
  c STRING
);
```
但是上述方案有如下缺点：
- HDFS 可扩展性：
  - HDFS 中的文件数量会增加。
  - HDFS 中的中间文件数量会增加。假设我们有 1000 个 Mapper 和 1000 个分区，并且每个 Mapper 下每个 Key 至少有 1 行，那么我们最终会创建 100 万个中间文件。
- Metastore 可扩展性：Metastore 是否会随着分区数量而增大。

#### 2.2 List Bucketing

上边方法将有数据倾斜的列作为分区存储，但是这种方法会产生大量的文件，那我们为什么不把倾斜的 Key 放在一个目录中呢，于是有了 List Bucketing。基本思想是：识别倾斜严重的 Key 并为每个 Key 创建一个目录，其余 Key 进入一个单独的目录。此映射关系在 MetaStore 中维护，Hive 编译器根据这些信息进行输入裁剪。

例如，表维护了 c 字段的倾斜 Key：6, 20, 30, 40。当加载新分区时，会创建 5 个目录（倾斜 Key 的 4 个目录 + 其他剩余 Key 的默认目录）。加载的表/分区将具有以下映射：6, 20, 30, 40, others。这非常类似于 Bucket，桶号决定了文件号。由于倾斜 Key 不需要连续，因此需要将整个倾斜键列表存储在每个表/分区中。

```sql
SELECT a, b
FROM partition_table
WHERE dt = '2012-04-15' AND c = 30;
```

```sql
SELECT a, b
FROM partition_table
WHERE dt = '2012-04-15' AND c = 50;
```
Hive 编译器只会将对应于 c = others 的文件用于 map-reduce 作业。

发出后，Hive 编译器只会将 c = 30 对应的目录用于 map-reduce 作业。




### 2. Skewed Join优化

两个大数据表的 Join 由一组 MapReduce 作业完成，这些作业首先根据 Join 的 key 对表进行排序，然后将它们连接起来。Mapper 将具有相同 key 的所有行发送到同一个 Reducer。

假设表A有一个id列，值为 `1，2，3，4`，并且表B也含有id列，值为 `1，2，3`。我们使用如下语句来进行 Join：
```sql
SELECT A.id
FROM A
JOIN B
ON A.id = B.id
```
一组 Mappers 读取表数据并根据 key 将它们发送给对应 Reducers。例如，带有 id 为1的行进入 Reducer R1，带有id为 2 的行进入 Reducer R2，依此类推。这些 Reducers 执行A和B值的交叉乘积，并输出。Reducer R4 从 A 获取行数据，但不会产生任何结果（B没有对应的数据）。

现在让我们假设A表中id为1的值出现数据倾斜。Reduce R2 和 R3 可以很快完成，但 R1 将持续很长时间，从而成为瓶颈。如果用户了解倾斜信息，可以手动避免瓶颈，如下所示：
```sql
# 单独处理出现数据倾斜的Key
SELECT A.id
FROM A
JOIN B
ON A.id = B.id
WHERE A.id = 1 AND B.id = 1;
# 处理其他Key
SELECT A.id
FROM A
JOIN B
ON A.id = B.id
WHERE A.id <> 1;
```
第二个查询没有任何的数据倾斜，所以所有 Reducers 都会在大致相同的时间内完成。如果我们假设B表中`B.id = 1`的只有几行，那么可以将其放入内存。通过将B的数据存储到内存中的哈希表中，Join 可以高效的完成，这样可以在 Mappper 端进行 Join，而不用将数据发送到 Reducer。然后合并两个查询的部分结果以获得最终结果。

优点
- 如果少量倾斜的 key 占据了相当大比例的数据，这样就不会成为瓶颈。
缺点
- 表A和B必须被读取和处理两次。
- 由于是部分结果，结果数据也必须读取和写入两次。
- 用户需要了解数据中的倾斜并手动执行上述过程。

我们可以通过尝试对倾斜 key 的处理来进一步改进。首先读取B表数据并将 id 为1的行存储在内存中的 HashTable 中。然后运行一组 Mappers 来读取A表并执行以下操作：
- 如果 id 为1，则使用Hash版本的B表来计算结果。
- 对于所有其他key，将其发送到执行 Join 的Reducer。Reducer会从 Mapper 获取B表的行数据。

这样，我们最终只能读取B两次。A中的偏斜键仅由Mapper读取和处理，不会发送到reducer。 A中的其余键只经过一次Map / Reduce。
假设B有几行带有在A中倾斜的键。因此这些行可以加载到内存中。




参考：
- https://cwiki.apache.org/confluence/display/Hive/LanguageManual+DDL#LanguageManualDDL-SkewedTables
- https://cwiki.apache.org/confluence/display/Hive/Skewed+Join+Optimization
