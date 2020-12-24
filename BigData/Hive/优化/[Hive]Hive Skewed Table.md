
### 1. Skewed Tables

Skewed Table 可以提高一个或多个列具有倾斜值的表的性能。通过指定经常出现的值（严重倾斜），Hive会自动将这些值拆分为单独的文件（如果使用[ListBucketing](https://cwiki.apache.org/confluence/display/Hive/ListBucketing)时拆分为目录），并在查询期间考虑这一事实，如果可能的话，以便可以跳过或包含整个文件（目录）。

#### 1.1 创建

这可以在表创建期间在每个表上指定。以下示例显示了一个具有三个倾斜值的列，可选子句 `STORED AS DIRECTORIES` 指定 ListBucketing。
```sql
CREATE TABLE list_bucket_single
(
  key STRIN,
  value STRING
)
SKEWED BY (key) ON (1,5,6) [STORED AS DIRECTORIES];
```
下面是一个带有两个倾斜列表的示例：
```sql
CREATE TABLE list_bucket_multiple
(
  col1 STRING,
  col2 int,
  col3 STRING
)
SKEWED BY (col1, col2) ON (('s1',1), ('s3',3), ('s13',13), ('s78',78)) [STORED AS DIRECTORIES];
```

#### 1.2 修改

可以使用 `ALTER TABLE` 语句更改表的 `SKEWED` 和 `STORED AS DIRECTORIES` 选项。

(1) 修改为倾斜表
```sql
ALTER TABLE table_name
SKEWED BY (col_name1, col_name2, ...)
ON ([(col_name1_value, col_name2_value, ...) [, (col_name1_value, col_name2_value), ...]
[STORED AS DIRECTORIES];
```

(2) 修改为非倾斜表
```sql
ALTER TABLE table_name NOT SKEWED;
```
`NOT SKEWED` 选项修改表为普通表并关闭 ListBucketing 功能（因为 ListBucketing 表总是倾斜）。这会影响在 ALTER 语句之后创建的分区，但不会影响在 ALTER 语句之前创建的分区。

(3) 关闭 ListBucketing 功能
```sql
ALTER TABLE table_name NOT STORED AS DIRECTORIES;
```
关闭 ListBucketing 功能，但仍然是一个倾斜表。

(4) 修改表倾斜的位置
```sql
ALTER TABLE table_name
SET SKEWED LOCATION (col_name1="location1" [, col_name2="location2", ...] );
```
这会更改 ListBucketing 的映射位置。

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




参考：https://cwiki.apache.org/confluence/display/Hive/LanguageManual+DDL#LanguageManualDDL-SkewedTables

https://cwiki.apache.org/confluence/display/Hive/Skewed+Join+Optimization
