Flink 从 1.9 版本开始支持支持 Hive，不过作为 beta 版，不推荐在生产环境中使用。在 Flink 1.10 版本中，对 Hive 的集成也达到了生产级别的要求。值得注意的是，不同版本的 Flink 对于 Hive 的集成有所差异。

## 1. 什么是 Hive Dialect

当使用 Hive Dialect(方言)时，可以在 Flink 中使用 Hive 语法编写 SQL 语句。通过提供与 Hive 语法的兼容性，我们的目标是提高与 Hive 的互操作性，减少用户为了执行不同的语句而需要在 Flink 和 Hive 之间切换的情况。

## 2. 如何使用 Hive Dialect

Flink 目前支持两种 SQL 方言：default 和 hive。如果要使用 Hive 语法编写 SQL 语句，你需要切换到 Hive 方言。下面介绍如何使用 SQL Client 和 Table API 设置方言。还需要注意，可以为执行的每个语句动态切换方言，不需要重新启动会话来使用不同的方言。

### 2.1 SQL Client

SQL 方言可以通过 table.sql-dialect 指定。因此，我们可以在 SQL Client 的 yaml 文件中设置要使用的初始方言：
```xml
execution:
  type: streaming

configuration:
  table.sql-dialect: hive
```
还可以在 SQL Client 启动后为当前会话设置方言：
```sql
Flink SQL> SET 'table.sql-dialect' = 'hive'; -- to use hive dialect
[INFO] Session property has been set.

Flink SQL> SET 'table.sql-dialect' = 'default'; -- to use default dialect
[INFO] Session property has been set.
```
### 2.2 Table API

可以使用 Table API 为 TableEnvironment 设置方言：
```java
EnvironmentSettings settings = EnvironmentSettings.inStreamingMode();
TableEnvironment tableEnv = TableEnvironment.create(settings);
// to use hive dialect
tableEnv.getConfig().setSqlDialect(SqlDialect.HIVE);
// to use default dialect
tableEnv.getConfig().setSqlDialect(SqlDialect.DEFAULT);
```

## 3. DDL

下面一起看一下 Hive 方言支持的 DDL。这里我们主要关注语法。你可以参考 Hive 文档了解每个 DDL 语句的语义。

### 3.1 CATALOG

#### 3.1.1 Show

使用如下语句展示当前 CATALOG：
```sql
SHOW CURRENT CATALOG;
```

### 3.2 DATABASE

#### 3.2.1 Show

```sql
SHOW DATABASES;
SHOW CURRENT DATABASE;
```

#### 3.2.2 Create

```sql
CREATE (DATABASE|SCHEMA) [IF NOT EXISTS] database_name
  [COMMENT database_comment]
  [LOCATION fs_path]
  [WITH DBPROPERTIES (property_name=property_value, ...)];
```
#### 3.2.3 Alter

更新属性：
```
ALTER (DATABASE|SCHEMA) database_name SET DBPROPERTIES (property_name=property_value, ...);
```




参考：[Hive Dialect](https://nightlies.apache.org/flink/flink-docs-release-1.14/docs/connectors/table/hive/hive_dialect/)
