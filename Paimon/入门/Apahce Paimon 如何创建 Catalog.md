Paimon Catalog 目前支持三种类型的元存储：
- 文件系统元存储：这是一种默认元存储方式，将元数据和表文件存储在文件系统中。
- Hive 元存储：它将元数据额外存储在 Hive 元存储中。用户可以直接从 Hive 访问表。
- JDBC 元存储：它将元数据额外存储在 MySQL、Postgres 等关系型数据库中。

## 1. Filesystem Catalog

以下 Flink SQL 注册并使用一个名为 my_catalog 的 Paimon Catalog。元数据和表文件存储在 hdfs:///path/to/warehouse 下。
```sql
CREATE CATALOG my_catalog WITH (
    'type' = 'paimon',
    'warehouse' = 'hdfs:///path/to/warehouse'
);

USE CATALOG my_catalog;
```
您可以为 Catalog 中创建的表使用 `table-default.` 前缀定义任何默认表选项。

## 2. JDBC Catalog

通过使用 Paimon JDBC Catalog，可以将元数据直接存储在 SQLite、MySQL、postgres 等关系型数据库中。

目前，仅 MySQL 和 SQLite 支持锁配置。如果您使用的是其他类型的数据库进行目录存储，请不要配置 `lock.enabled`。

在 Flink 中的 Paimon JDBC Catalog 需要正确添加用于连接数据库的相应 jar 包。您应该首先下载 JDBC 连接器 jar 文件，并将其添加到 classpath 中。例如 MySQL、postgres。

| 数据库类型 | Jar 包 |
| :------------- | :------------- |
| mysql  | [mysql-connector-java](https://mvnrepository.com/artifact/mysql/mysql-connector-java) |
| postgres | [postgresql](https://mvnrepository.com/artifact/org.postgresql/postgresql) |

```sql
CREATE CATALOG my_jdbc WITH (
    'type' = 'paimon',
    'metastore' = 'jdbc',
    'uri' = 'jdbc:mysql://<host>:<port>/<databaseName>',
    'jdbc.user' = '...',
    'jdbc.password' = '...',
    'catalog-key'='jdbc',
    'warehouse' = 'hdfs:///path/to/warehouse'
);

USE CATALOG my_jdbc;
```
您可以通过 `jdbc.` 来配置 JDBC 声明的任何连接参数，不同的数据库连接参数可能不同，请根据实际情况进行配置。您还可以通过指定 `catalog-key` 来对多个 Catalog 下的数据库进行逻辑隔离。


## 3. Hive Catalog
