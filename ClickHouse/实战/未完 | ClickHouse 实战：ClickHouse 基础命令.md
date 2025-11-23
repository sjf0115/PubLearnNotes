作为一款高性能的列式数据库管理系统，ClickHouse 在大数据分析领域表现出色。本文将全面介绍 ClickHouse 的常用命令，帮助您快速掌握日常操作和高级功能。

## 1. 连接 ClickHouse

如果你已经安装了 ClickHouse 的客户端，可以使用以下命令连接 ClickHouse：
```bash
clickhouse-client --host <hostname> --port <port> --user <username> --password <password>
```
其中，`<hostname>`、`<port>`、`<username>` 和 `<password>` 分别代表 ClickHouse 服务器的地址、端口、用户名和密码。如果没有提供用户名和密码，clickhouse-client 默认尝试以 default 用户进行连接，而且默认的端口是 9000。如下所示通过我们创建的 `test` 用户登录：

```bash
smarsi:~ smartsi$ cd /opt/workspace/docker/clickhouse/
smarsi:clickhouse smartsi$
root@e729684b70f2:/# clickhouse-client --host ck1 --port 9000 --user test --password test
ClickHouse client version 23.3.13.6 (official build).
Connecting to ck1:9000 as user default.
Connected to ClickHouse server version 23.3.13 revision 54462.

Warnings:
 * Linux is not using a fast clock source. Performance can be degraded. Check /sys/devices/system/clocksource/clocksource0/current_clocksource
 * Linux transparent hugepages are set to "always". Check /sys/kernel/mm/transparent_hugepage/enabled

e729684b70f2 :)
```
可以使用 `--database` 参数指定数据库连接
```bash
# 使用指定数据库连接
clickhouse-client --database=mydb
```

## 2. 数据库操作

### 2.1 基础信息查询

【1】可以使用 `version()` 函数来查看 ClickHouse 的版本：
```sql
e729684b70f2 :) SELECT version();

SELECT version()

Query id: f152fdd6-c5e8-4ad2-9d92-c9aca29a4029

┌─version()─┐
│ 23.3.13.6 │
└───────────┘

1 row in set. Elapsed: 0.004 sec.
```

【2】可以使用 `currentDatabase()` 函数来查看当前数据库：
```sql
e729684b70f2 :) SELECT currentDatabase();

SELECT currentDatabase()

Query id: b77a5a44-4720-49cb-8a5d-a23cbdf1d419

┌─currentDatabase()─┐
│ default           │
└───────────────────┘

1 row in set. Elapsed: 0.005 sec.
```
【3】可以使用 `SHOW DATABASES` 命令来查看所有数据库：
```sql
e729684b70f2 :) SHOW DATABASES;

SHOW DATABASES

Query id: 9a056e8f-5e86-461a-a33d-ed66578e6804

┌─name───────────────┐
│ INFORMATION_SCHEMA │
│ default            │
│ information_schema │
│ system             │
└────────────────────┘

4 rows in set. Elapsed: 0.004 sec.
```

### 2.2 创建和管理数据库

#### 2.2.1 创建数据库

可以使用如下命令来创建一个新的数据库：
```sql
CREATE DATABASE [IF NOT EXISTS] db_name [ON CLUSTER cluster] [ENGINE = engine(...)] [COMMENT 'Comment']
```
`ON CLUSTER cluster` 子句在指定集群的所有服务器上创建 db_name 数据库。
`ENGINE = engine(...)` 子句自己动数据库引擎。默认情况下，ClickHouse 使用其自己的 Atomic 数据库引擎。还提供 Lazy、MySQL、PostgresSQL、MaterializedPostgreSQL、Replicated、SQLite 等引擎。

如下所示创建一个 `profile` 数据库并从元数据库中根据数据库名称查询创建是否成功：
```sql
CREATE DATABASE IF NOT EXISTS profile ENGINE = Atomic COMMENT '用户画像数据库';
SELECT name, comment FROM system.databases WHERE name = 'profile';
```
效果如下所示：
```sql
e729684b70f2 :) CREATE DATABASE IF NOT EXISTS profile ENGINE = Atomic COMMENT '用户画像数据库';

CREATE DATABASE IF NOT EXISTS profile
ENGINE = Atomic
COMMENT '用户画像数据库'

Query id: 5fd72cbd-d3e2-4ab7-ade9-b89b634c29e7

Ok.

0 rows in set. Elapsed: 0.004 sec.


e729684b70f2 :) SELECT name, comment FROM system.databases WHERE name = 'profile';

SELECT
    name,
    comment
FROM system.databases
WHERE name = 'profile'

Query id: 5a315ff6-9d88-419a-916e-12a915c30184

┌─name────┬─comment────────┐
│ profile │ 用户画像数据库 │
└─────────┴────────────────┘

1 row in set. Elapsed: 0.004 sec.
```

#### 2.2.2 删除数据库

可以使用如下命令来删除 db 数据库中的所有表，然后删除 db 数据库本身:
```sql
DROP DATABASE [IF EXISTS] db [ON CLUSTER cluster] [SYNC]
```
如下所示删除 `profile` 数据库：
```sql
DROP DATABASE IF EXISTS profile;
```

## 3. 表操作

### 3.1 创建表

```sql
-- 基本表创建
CREATE TABLE IF NOT EXISTS user_behavior
(
    user_id UInt32,
    event_time DateTime,
    event_type String,
    page_url String,
    device String
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_time)
ORDER BY (user_id, event_time);

-- 创建分布式表
CREATE TABLE user_behavior_distributed AS user_behavior
ENGINE = Distributed(my_cluster, mydb, user_behavior, rand());
```

### 3.2 表管理命令
```sql
-- 查看所有表
SHOW TABLES;

-- 查看表结构
DESCRIBE TABLE user_behavior;

-- 查看建表语句
SHOW CREATE TABLE user_behavior;

-- 重命名表
RENAME TABLE old_name TO new_name;

-- 删除表
DROP TABLE IF EXISTS user_behavior;
```

### 3.3 修改表结构
```sql
-- 添加列
ALTER TABLE user_behavior ADD COLUMN country_code String DEFAULT 'US';

-- 删除列
ALTER TABLE user_behavior DROP COLUMN country_code;

-- 修改列类型
ALTER TABLE user_behavior MODIFY COLUMN user_id UInt64;

-- 添加索引
ALTER TABLE user_behavior ADD INDEX idx_device device TYPE set(100) GRANULARITY 4;
```

## 4. 数据操作

### 4.1 数据插入
```sql
-- 单条插入
INSERT INTO user_behavior VALUES
(1, '2023-01-01 10:00:00', 'click', '/home', 'mobile');

-- 批量插入
INSERT INTO user_behavior FORMAT Values
(2, '2023-01-01 10:01:00', 'view', '/products', 'desktop'),
(3, '2023-01-01 10:02:00', 'purchase', '/checkout', 'mobile');

-- 从文件导入
INSERT INTO user_behavior FROM INFILE 'data.csv' FORMAT CSVWithNames;
```

### 4.2 数据查询
```sql
-- 基础查询
SELECT * FROM user_behavior LIMIT 10;

-- 条件查询
SELECT user_id, event_type, event_time
FROM user_behavior
WHERE event_time >= '2023-01-01'
  AND device = 'mobile';

-- 聚合查询
SELECT
    toDate(event_time) as date,
    event_type,
    count(*) as event_count,
    uniq(user_id) as unique_users
FROM user_behavior
WHERE event_time >= '2023-01-01'
GROUP BY date, event_type
ORDER BY date, event_count DESC;

-- 窗口函数
SELECT
    user_id,
    event_time,
    event_type,
    lagInFrame(event_type) OVER (PARTITION BY user_id ORDER BY event_time) as prev_event
FROM user_behavior;
```

### 4.3 数据更新与删除
```sql
-- 删除数据（需要配置 allow_experimental_lightweight_delete）
ALTER TABLE user_behavior DELETE WHERE event_time < '2023-01-01';

-- 更新数据（需要配置 allow_experimental_mutations）
ALTER TABLE user_behavior UPDATE device = 'tablet' WHERE user_id = 1;
```

## 5. 分区和索引操作

### 5.1 分区管理
```sql
-- 查看分区信息
SELECT
    partition,
    name,
    rows,
    bytes_on_disk
FROM system.parts
WHERE table = 'user_behavior';

-- 删除分区
ALTER TABLE user_behavior DROP PARTITION '202301';

-- 移动分区
ALTER TABLE user_behavior MOVE PARTITION '202301' TO DISK 'cold_storage';

-- 冻结分区（用于备份）
ALTER TABLE user_behavior FREEZE PARTITION '202301';
```

## 6. 系统监控和维护

### 系统表查询
```sql
-- 查看查询日志
SELECT
    query,
    query_duration_ms,
    memory_usage,
    read_rows
FROM system.query_log
WHERE event_date = today()
ORDER BY query_duration_ms DESC
LIMIT 10;

-- 查看表大小
SELECT
    table,
    sum(bytes) as size_bytes,
    formatReadableSize(size_bytes) as size
FROM system.parts
WHERE active
GROUP BY table;

-- 查看后台任务
SELECT
    type,
    database,
    table,
    status
FROM system.merges;
```

### 性能监控
```sql
-- 查看当前指标
SELECT
    metric,
    value
FROM system.metrics;

-- 查看异步指标
SELECT
    metric,
    value
FROM system.asynchronous_metrics;

-- 查看事件计数
SELECT
    event,
    value
FROM system.events;
```

## 7. 用户和权限管理

### 用户管理
```sql
-- 创建用户
CREATE USER john IDENTIFIED WITH sha256_password BY 'secure_password';

-- 修改用户密码
ALTER USER john IDENTIFIED WITH sha256_password BY 'new_password';

-- 删除用户
DROP USER john;
```

### 权限管理
```sql
-- 授予权限
GRANT SELECT ON mydb.* TO john;
GRANT INSERT ON mydb.user_behavior TO john;

-- 撤销权限
REVOKE INSERT ON mydb.user_behavior FROM john;

-- 查看权限
SHOW GRANTS FOR john;
```

## 8. 备份和恢复

### 数据备份
```sql
-- 创建备份
BACKUP TABLE mydb.user_behavior TO Disk('backup', 'user_behavior_backup');

-- 恢复备份
RESTORE TABLE mydb.user_behavior FROM Disk('backup', 'user_behavior_backup');
```

## 9. 实用技巧和最佳实践

### 查询优化技巧
```sql
-- 使用 PREWHERE 优化查询
SELECT * FROM user_behavior
PREWHERE user_id = 123
WHERE event_time >= '2023-01-01';

-- 使用 SAMPLE 进行抽样查询
SELECT
    device,
    count(*)
FROM user_behavior
SAMPLE 0.1
GROUP BY device;

-- 使用 FINAL 获取最新数据
SELECT * FROM collapsing_table FINAL;
```

### 数据导出
```sql
-- 导出为 CSV
SELECT * FROM user_behavior
INTO OUTFILE 'export.csv'
FORMAT CSVWithNames;

-- 导出为 JSON
SELECT * FROM user_behavior
LIMIT 100
FORMAT JSONEachRow;
```

## 10. 集群管理

### 分布式操作
```sql
-- 查看集群信息
SELECT * FROM system.clusters;

-- 在集群所有节点上创建数据库
CREATE DATABASE mydb ON CLUSTER my_cluster;

-- 在集群所有节点上创建表
CREATE TABLE mydb.user_behavior ON CLUSTER my_cluster
(...)
ENGINE = ReplicatedMergeTree(...);
```

## 总结

本文涵盖了 ClickHouse 日常使用中最常用的命令，从基础连接到高级集群管理。掌握这些命令将帮助您：

1. 高效地进行数据操作和查询
2. 有效地管理和维护 ClickHouse 实例
3. 优化查询性能和资源使用
4. 实施适当的权限管理和安全措施

ClickHouse 的强大功能结合这些命令的使用，能够帮助您构建高性能的大数据分析平台。建议在实际工作中根据具体需求灵活运用这些命令，并参考官方文档获取最新功能信息。
