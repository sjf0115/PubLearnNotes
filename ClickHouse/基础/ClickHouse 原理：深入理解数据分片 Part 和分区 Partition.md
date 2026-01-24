在 ClickHouse 中，磁盘上存储表数据一部分的物理文件被称为数据分片 `part`。数据分区 `partition` 则是通过分区键创建表的数据逻辑划分。通过分区，用户可以更高效地存储、查询和操作数据的子集，从而提升大表的性能和可管理性。在本博客系列的第一篇中，我们将介绍 ClickHouse 中的数据分片 part 与分区 partition，以及它们的使用方式和区别。

## 1. Part

如前所述，`Part` 是磁盘上的物理文件。默认情况下，所有与数据相关的文件都位于 `/var/lib/clickhouse` 目录下。ClickHouse 中的每个 MergeTree 表都有一个唯一目录路径来存储 `Part`。你可以通过 `system.parts` 系统表查询到 `Part` 的实际存储位置、片段名称、分区信息（如果有的话）以及其他一些有用的信息。

下方展示了从 `system.parts` 表中查询结果的一个示例。其中，`part_type` 字段中的 `Wide` 表示每列在文件系统中以单独的文件形式存储；而 `Compact` 则表示所有列都存储在同一个文件中。此外，在 `partition` 列中，`tuple()` 表示该表未进行分区。

```sql
SELECT
    substr(table, 1, 22),
    partition AS prt,
    name,
    part_type,
    path
FROM system.parts
WHERE database = 'sampleDatasets'
ORDER BY
    table ASC,
    partition ASC,
    name ASC

Query id: 2a9462a8-7e74-4c0f-a89a-0bd2a31d0a46

┌─substring(table, 1, 22)─┬─prt─────┬─name──────────┬─part_type─┬─path──────────────────────────────────────────────────────────────────────────────┐
│ .inner_id.ca612a5e-5ee  │ tuple() │ all_1_1_1     │ Compact   │ /var/lib/clickhouse/store/4c6/4c6dfe9a-b697-4f9a-928f-f829bf44fb5c/all_1_1_1/     │
│ opensky                 │ tuple() │ all_1_1_1_5   │ Wide      │ /var/lib/clickhouse/store/1af/1afc664b-0a25-443a-a317-532532434753/all_1_1_1_5/   │
│ opensky                 │ tuple() │ all_2_2_1_5   │ Wide      │ /var/lib/clickhouse/store/1af/1afc664b-0a25-443a-a317-532532434753/all_2_2_1_5/   │
│ opensky                 │ tuple() │ all_3_3_0_5   │ Wide      │ /var/lib/clickhouse/store/1af/1afc664b-0a25-443a-a317-532532434753/all_3_3_0_5/   │
│ opensky                 │ tuple() │ all_4_4_0_5   │ Compact   │ /var/lib/clickhouse/store/1af/1afc664b-0a25-443a-a317-532532434753/all_4_4_0_5/   │
│ openskyDeletedRecord    │ tuple() │ all_2_2_2     │ Compact   │ /var/lib/clickhouse/store/5b0/5b0e6758-ae46-4c25-9599-f2cddc362b5e/all_2_2_2/     │
│ opensky_1000000         │ tuple() │ all_1_1_0     │ Wide      │ /var/lib/clickhouse/store/a2a/a2aa62d7-65bb-4bb2-bc5b-2c3d1befa147/all_1_1_0/     │
│ opensky_freeze_restore  │ tuple() │ all_1_1_1     │ Wide      │ /var/lib/clickhouse/store/2d0/2d0e6ad7-6fd4-408e-8c18-b39416ea8ff1/all_1_1_1/     │
│ opensky_freeze_restore  │ tuple() │ all_2_2_1     │ Wide      │ /var/lib/clickhouse/store/2d0/2d0e6ad7-6fd4-408e-8c18-b39416ea8ff1/all_2_2_1/     │
│ opensky_freeze_restore  │ tuple() │ all_3_3_0     │ Wide      │ /var/lib/clickhouse/store/2d0/2d0e6ad7-6fd4-408e-8c18-b39416ea8ff1/all_3_3_0/     │
│ opensky_freeze_restore  │ tuple() │ all_4_4_0     │ Compact   │ /var/lib/clickhouse/store/2d0/2d0e6ad7-6fd4-408e-8c18-b39416ea8ff1/all_4_4_0/     │
│ opensky_redo_test       │ tuple() │ all_1_2_1     │ Compact   │ /var/lib/clickhouse/store/e99/e99f1ab9-6d21-4d01-8f02-9f2aa0e6b45a/all_1_2_1/     │
│ opensky_redo_test2      │ tuple() │ all_103_104_1 │ Compact   │ /var/lib/clickhouse/store/fac/facadfc3-1c5b-4775-bea7-53c262f7e237/all_103_104_1/ │
│ test_table              │ tuple() │ all_1_2_1     │ Compact   │ /var/lib/clickhouse/store/024/024a3a77-4ca9-4761-a2f1-4b36eb4ece0e/all_1_2_1/     │
└─────────────────────────┴─────────┴───────────────┴───────────┴───────────────────────────────────────────────────────────────────────────────────┘
```

也可以在目录 `/var/lib/clickhouse/data/<DBNAME>/<TABLENAME>` 中查看表的数据分片 `Part`，会发现该目录下存放都是符号链接，通过链接可以查看表包含的数据分片 `Part`。比如，进入表 `mytest_of_ti` 所在目录查看：
```
root@clickhouse01:/var/lib/clickhouse/data/sampleDatasets/opensky# ls -al
total 36
drwxr-x--- 7 clickhouse clickhouse 4096 Nov 21 10:00 .
drwxr-x--- 3 clickhouse clickhouse 4096 Oct 16 13:13 ..
drwxr-x--- 2 clickhouse clickhouse 4096 Nov 21 09:49 all_1_1_1_5
drwxr-x--- 2 clickhouse clickhouse 4096 Nov 21 09:49 all_2_2_1_5
drwxr-x--- 2 clickhouse clickhouse 4096 Nov 21 09:49 all_3_3_0_5
drwxr-x--- 2 clickhouse clickhouse 4096 Nov 21 09:49 all_4_4_0_5
drwxr-x--- 2 clickhouse clickhouse 4096 Nov  9 11:33 detached
-rw-r----- 1 clickhouse clickhouse    1 Oct 16 13:13 format_version.txt
-rw-r----- 1 clickhouse clickhouse  100 Nov 21 09:49 mutation_5.txt
```

如上例所示，`sampleDatasets` 数据库中的 `opensky` 表包含 4 个数据分片 `Part`。每个数据分片 `Part` 都有其独立的目录，且目录名称均以 `all_` 开头。以名为 `all_3_3_0_5` 的数据分片 `Part` 为例：
- 第一个 3 表示数据分片 `Part` 所包含数据块的最小编号；
- 第二个 3 表示数据分片 `Part` 所包含数据块的最大编号；
- 0 表示合并层级（即数据分片 `Part` 由合并树的第几层生成）；
- 5 表示变更版本号（mutation version），用于标识数据分片 `Part` 是否经过了数据变更（mutation）操作。

此外，这些信息也可以通过 `system.parts` 系统表进行查询获取：
```sql
SELECT
    name,
    partition_id,
    min_block_number,
    max_block_number,
    level,
    data_version
FROM system.parts
WHERE (database = 'sampleDatasets') AND (table = 'opensky') AND (name = 'all_3_3_0_5')

Query id: 0f2bb404-11a0-4df3-b1c1-7941698b9560

┌─name────────┬─partition_id─┬─min_block_number─┬─max_block_number─┬─level─┬─data_version─┐
│ all_3_3_0_5 │ all          │                3 │                3 │     0 │            5 │
└─────────────┴──────────────┴──────────────────┴──────────────────┴───────┴──────────────┘
```

## 2. Partitions

与数据分片 `Part` 一样，也可以从 `system.parts` 表中访问 MergeTree 表的分区信息。不过，在这里分区列不是用 `tuple()` 来表示了，而是具体的分区标识。要创建一个分区表，首先需要在创建表时使用 `PARTITION BY expr` 子句。例如，`PARTITION BY toYYYMMDD(start_time)` 子句会根据 `start_time` 列按天创建分区。在下面的示例中可以看到，Partitions 分区名称和数据分片 `Part` 名称是不同的。此外，数据分片 `Part` 名称不再以 `all` 开头，而是以对应的分区标识作为前缀。分区是一种逻辑上的划分方式，而数据分片 `Part` 则是实际存储在磁盘上的物理文件。一个分区可以包含一个或多个数据分片 `Part`：
```sql
SELECT
    partition,
    name,
    active
FROM system.parts
WHERE (table = 'backups') AND (database = 'RECMAN')

┌─partition─┬─name───────────┬─active─┐
│ 20221017  │ 20221017_1_1_0 │      1 │
│ 20221018  │ 20221018_2_2_0 │      1 │
│ 20221114  │ 20221114_3_3_0 │      1 │
└───────────┴────────────────┴────────┘
```

通常，分区用于提升查询性能，并为我们提供灵活管理数据子集的能力。你可以直接对分区进行查询、删除（DROP）、分离（DETACH）等操作。关于数据分片 `Part` 和分区 `Partitions` 的具体操作，我们将在后续的博客文章中详细讨论。

你可以通过在 `WHERE` 子句中指定条件，或使用隐藏列 `_partition_id` 来查询特定的分区。当然，更推荐使用官方支持的方式，即在 `WHERE` 子句中直接提供分区键的条件。但在某些场景下，我们也需要使用 `_partition_id`。

现在，让我们来看一个分区表的查询示例。假设我们的表 `recoDB.opensky_partitioned` 是按 `lastseen` 列进行分区的。我们既可以通过分区键列（即 `lastseen`），也可以通过隐藏列 `_partition_id` 来访问特定的分区：
```sql
SELECT count()
FROM recoDB.opensky_partitioned
WHERE toDate(lastseen) = '2019-02-25'

┌─count()─┐
│   69480 │
└─────────┘
#####################################

SELECT count()
FROM recoDB.opensky_partitioned
WHERE _partition_id = '20190225'

┌─count()─┐
│   69480 │
└─────────┘
```
此外，我们还可以利用 `_partition_id` 查询前 10 个分区的数据：
```sql
SELECT
    _partition_id,
    count()
FROM recoDB.opensky_partitioned
GROUP BY _partition_id
ORDER BY 2 DESC
LIMIT 10
┌─_partition_id─┬─count()─┐
│ 20190524      │   90358 │
│ 20190531      │   87917 │
│ 20190523      │   87023 │
│ 20190530      │   86945 │
│ 20190425      │   85524 │
│ 20190516      │   85348 │
│ 20190515      │   85287 │
│ 20190522      │   85056 │
│ 20190517      │   84986 │
│ 20190510      │   84585 │
└───────────────┴─────────┘
```

## 3. 结论

数据分片 `Part` 和分区 `Partitions` 是 ClickHouse 数据库的核心组成部分。一般来说，数据分片 `Part` 用于存储表中的一部分数据，是磁盘上的物理文件；而分区 `Partitions` 则是逻辑结构，常用于提升表的查询性能和数据管理效率。在本系列的第一篇文章中，我们介绍了 ClickHouse 中的数据分片 `Part` 与分区 `Partitions`。在后续的文章中，我们将深入探讨对它们的操作、合并（merging）以及变更（mutations）等内容。
