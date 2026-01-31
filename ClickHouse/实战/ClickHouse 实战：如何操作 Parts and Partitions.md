## 1. 分离 Detach 或挂载 Attach Part/Partition

通过分离 detach 操作，可以将指定的数据分片 part 或分区 partition 移动到 `detached` 文件夹中。在重新挂载之前，用户无法访问这些被分离的数据分片或分区。默认情况下，`detached` 文件夹位于 `/var/lib/clickhouse/data/<DATABASE_NAME>/<TABLE_NAME>/` 目录下。另一方面，挂载 `attach` 操作则用于将 `detached` 文件夹中的数据分片或分区重新挂载回表中。ClickHouse 中 `detach` 和 `attach` 操作的语法如下所示：
```sql
#DETACH PART/PARTITION
ALTER TABLE <DATABASE_NAME>.<TABLE_NAME> [ON CLUSTER <CLUSTER_NAME>] DETACH PARTITION|PART <PARTITION_EXPRESSION>

#ATTACH PART/PARTITION
ALTER TABLE <DATABASE_NAME>.<TABLE_NAME> [ON CLUSTER <CLUSTER_NAME>] ATTACH PARTITION|PART <PARTITION_EXPRESSION>
```
在这里 `PARTITION_EXPRESSION` 应为分区名称、分区 ID 或分区表达式本身。

假设我们希望从 `opensky_partitioned` 表中分离某个特定日期（例如 2019 年 4 月 15 日）的数据分区。

首先，我们需要找出该日期对应的分区名和数据分片名称。如你所见，该日期数据在 `20190415` 的分区中，并且该分区包含两个数据分片：
```sql
SELECT
    partition,
    name,
    partition_id
FROM system.parts
WHERE (database = 'sampleDatasets') AND (table = 'opensky_partitioned') AND (partition_id IN (
    SELECT DISTINCT _partition_id
    FROM sampleDatasets.opensky_partitioned
    WHERE toDate(lastseen) = '2019-04-15'
))


┌─partition─┬─name─────────────┬─partition_id─┐
│ 20190415  │ 20190415_62_62_0 │ 20190415     │
│ 20190415  │ 20190415_78_78_0 │ 20190415     │
└───────────┴──────────────────┴──────────────┘
```
接下来，我们将分离 `20190415` 分区，再将其重新挂载，并对其中一个数据分片执行相同的操作：
```sql
-- Count related date before detached
SELECT count()
FROM sampleDatasets.opensky_partitioned
WHERE toDate(lastseen) = '2019-04-15'
┌─count()─┐
│   78647 │
└─────────┘

-- detach partition
ALTER TABLE sampleDatasets.opensky_partitioned DETACH PARTITION 20190415
Ok.

-- Count related date after detached
SELECT count()
FROM sampleDatasets.opensky_partitioned
WHERE toDate(lastseen) = '2019-04-15'
┌─count()─┐
│       0 │
└─────────┘
```
如前所述，分区是表的逻辑划分，每个分区至少包含一个数据分片。在我们的示例中，`20190415` 分区包含两个数据分片。当我们分离该分区时，所有相关数据分片都会被移动到 `/var/lib/clickhouse/data/<DATABASE_NAME>/<TABLE_NAME>/detached` 文件夹中：
```
root@server:~# ls -1 /var/lib/clickhouse/data/sampleDatasets/opensky_partitioned/detached
20190415_62_62_0
20190415_78_78_0
```

现在，我们将按如下方式挂载 `20190415` 分区：
```sql
--attach partition
ALTER TABLE sampleDatasets.opensky_partitioned
    ATTACH PARTITION 20190415

Ok.
--Count related date after attach partition
SELECT count()
FROM sampleDatasets.opensky_partitioned
WHERE toDate(lastseen) = '2019-04-15'
┌─count()─┐
│   78647 │
└─────────┘
```
让我们对数据分片 part 执行相同的测试：
```sql
--find parts for given date
SELECT
    partition,
    name,
    partition_id
FROM system.parts
WHERE (database = 'sampleDatasets') AND (table = 'opensky_partitioned') AND (partition_id IN (
    SELECT DISTINCT _partition_id
    FROM sampleDatasets.opensky_partitioned
    WHERE toDate(lastseen) = '2019-04-15'
))
┌─partition─┬─name───────────────┬─partition_id─┐
│ 20190415  │ 20190415_142_142_0 │ 20190415     │
│ 20190415  │ 20190415_143_143_0 │ 20190415     │
└───────────┴────────────────────┴──────────────┘

-- Count before detach part operation
SELECT count()
FROM sampleDatasets.opensky_partitioned
WHERE toDate(lastseen) = '2019-04-15'
┌─count()─┐
│   78647 │
└─────────┘

-- detach any of the parts
ALTER TABLE sampleDatasets.opensky_partitioned
    DETACH PART '20190415_142_142_0'
Ok.

-- Count after detach part operation
SELECT count()
FROM sampleDatasets.opensky_partitioned
WHERE toDate(lastseen) = '2019-04-15'
┌─count()─┐
│   78517 │
└─────────┘

-- Attach related part
ALTER TABLE sampleDatasets.opensky_partitioned
    ATTACH PART '20190415_142_142_0'

-- Count after attach the part
SELECT count()
FROM sampleDatasets.opensky_partitioned
WHERE toDate(lastseen) = '2019-04-15'
┌─count()─┐
│   78647 │
└─────────┘
```
我们还可以使用以下命令将分区从源表挂载到目标表。在此方法中，数据不会从源表或目标表中删除。
```sql
ALTER TABLE <DESTINATION_TABLE> [ON CLUSTER <CLUSTER_NAME>] ATTACH PARTITION <PARTITION EXPRESSION> FROM <SOURCE_TABLE>
```

执行此操作时，源表和目标表必须满足以下条件：
- 表结构相同；
- 分区键、排序键（ORDER BY key）和主键（primary key）完全一致；
- 存储策略（storage policy）相同。


## 2. 删除 Part/Partition

该操作会从表中删除指定的数据分片或分区。被删除的数据分片或分区会在 `system.parts` 系统表中标记为非活跃状态。

执行删除操作后，该数据分片/分区的数据文件仍会在 `/var/lib/clickhouse/data/<database_name>/<table_name>/` 目录下保留大约 10 分钟。

下方展示了 `drop` 命令的语法及操作示例：
```sql
-- Drop from table itself
ALTER TABLE <DATABASE_NAME>.<TABLE_NAME> [ON CLUSTER <CLUSTER_NAME>] DROP PARTITION|PART 'PART/PARTITON EXPRESSION'

-- Remove specified part/partition from detached folder
ALTER TABLE <DATABASE_NAME>.<TABLE_NAME> [ON CLUSTER <CLUSTER_NAME>] DROP DETACHED PARTITION|PART 'PART/PARTITON EXPRESSION'
```

```sql
-- Specified part/partition is active before drop operation
┌─partition─┬─name───────────────┬─partition_id─┬─active─┐
│ 20190415  │ 20190415_147_147_0 │ 20190415     │      1 │
└───────────┴────────────────────┴──────────────┴────────┘

-- Drop partition
ALTER TABLE sampleDatasets.opensky_partitioned
    DROP PARTITION 20190415

-- Specified part/partition is not active(active=0) after drop partition
┌─partition─┬─name───────────────┬─partition_id─┬─active─┐
│ 20190415  │ 20190415_147_147_1 │ 20190415     │      0 │
└───────────┴────────────────────┴──────────────┴────────┘

-- Specified part/partition is completely deleted after 10 minutes
```

## 3. 移动 Part/Partition

在 ClickHouse 中，你可以将分区移动到另一张表中。此时，源表和目标表必须具有相同的结构、分区键、排序键、主键、存储策略以及引擎家族。`move` 操作的另一种用途是将数据分片或分区移动到 MergeTree 引擎表的另一个磁盘或卷（volume）上。

将分区移动到另一张表的语法如下：
```sql
-- Usage: ALTER TABLE <DATABASE_NAME.SOURCE_TABLE> [ON CLUSTER <CLUSTER_NAME>] MOVE PARTITION <PARTITION EXPRESSION> TO TABLE <DATABASE_NAME.DESTINATION_TABLE>

-- 1. Create empty opensky_partitioned_new table same as the opensky_partitioned

-- 2. Move 20190415 partition from opensky_partitioned to opensky_partitioned_new
ALTER TABLE sampleDatasets.opensky_partitioned
    MOVE PARTITION '20190415' TO TABLE sampleDatasets.opensky_partitioned_new
Ok.
--3. Take partition count for 20190415 in source table
SELECT count()
FROM sampleDatasets.opensky_partitioned
WHERE _partition_id = '20190415'
┌─count()─┐
│       0 │
└─────────┘

--4 Take partition count for 20190415 in destination table
SELECT count()
FROM sampleDatasets.opensky_partitioned_new
WHERE _partition_id = '20190415'

Query id: 49319c73-c84f-4fbf-838d-ab787971eaad

┌─count()─┐
│   78647 │
└─────────┘
```

若要将数据分片或分区移动到另一个磁盘或卷，则需要先配置存储策略（storage policy），并使用该策略创建新表。不过，存储策略和数据分层（data tiering）超出了本文的讨论范围，因此本文不会深入介绍存储策略，仅展示移动操作的基本概念。
```sql
-- Our table's(opensky_partitioned_with_storage_policy) policy is "ssd_to_hdd"
-- and this volume contain 2 disks(ssd and hdd)
SELECT *
FROM system.storage_policies
WHERE policy_name = (
    SELECT storage_policy
    FROM system.tables
    WHERE (database = 'sampleDatasets') AND (name = 'opensky_partitioned_with_storage_policy')

┌─policy_name─┬─volume_name─┬─volume_priority─┬─disks───┬─volume_type─┬─max_data_part_size─┬─move_factor─┬─prefer_not_to_merge─┐
│ ssd_to_hdd  │ ssd_volume  │               1 │ ['ssd'] │ JBOD        │                  0 │         0.1 │                   0 │
│ ssd_to_hdd  │ hdd_volume  │               2 │ ['hdd'] │ JBOD        │                  0 │         0.1 │                   0 │
└─────────────┴─────────────┴─────────────────┴─────────┴─────────────┴────────────────────┴─────────────┴─────────────────────┘

-- The 20190415 partition is stored under ssd disk.
SELECT
    partition,
    name,
    path
FROM system.parts
WHERE (database = 'sampleDatasets') AND (table = 'opensky_partitioned_with_storage_policy') AND (partition = '20190415')


┌─partition─┬─name───────────────┬─path────────────────────────────────────────────────────────────────────┐
│ 20190415  │ 20190415_107_107_0 │ /ssd/store/300/3005efb6-244d-473f-93ac-944233d79a55/20190415_107_107_0/ │
└───────────┴────────────────────┴─────────────────────────────────────────────────────────────────────────┘

-- Let's move it to the hdd disk
ALTER TABLE sampleDatasets.opensky_partitioned_with_storage_policy
    MOVE PARTITION '20190415' TO DISK 'hdd'

-Check the new volume
SELECT
    partition,
    name,
    path
FROM system.parts
WHERE (database = 'sampleDatasets') AND (table = 'opensky_partitioned_with_storage_policy') AND (partition = '20190415')

┌─partition─┬─name───────────────┬─path────────────────────────────────────────────────────────────────────┐
│ 20190415  │ 20190415_107_107_0 │ /hdd/store/300/3005efb6-244d-473f-93ac-944233d79a55/20190415_107_107_0/ │
└───────────┴────────────────────┴─────────────────────────────────────────────────────────────────────────┘

-- You can move parts and also you can move volume instead of disk
```

## 4. 冻结（Freeze）或解冻（Unfreeze） Part/Partition

我们使用 `freeze` 命令来备份数据分片、分区，甚至整张表。关于 freeze 操作的详细说明，请参阅[此处](https://chistadata.com/how-to-use-freeze-command-in-clickhouse/)的博客文章。

## 5. 结论

ClickHouse 提供了多种针对分区和数据分片的操作。在本文中，我们介绍了分区的 attach、detach、move、drop 和 freeze 操作。此外，分区操作还包括 replace、update、delete 和 fetch 等。在本系列的下一篇（也是最后一篇）文章中，我们将讨论分区表达式和数据变更（mutations）。
