---
layout: post
author: smartsi
title: Flink SQL 客户端如何使用
date: 2021-06-27 12:07:21
tags:
  - Flink
  - Flink SQL

categories: Flink
permalink: flink-sql-client
---

> Flink 版本 1.13.0

Flink 的 Table & SQL API 可以处理 SQL 语言编写的查询语句，但是这些查询需要嵌入用 Java 或 Scala 编写的 Table 程序中。此外，这些程序在提交到集群前需要用构建工具打包。这或多或少限制了 Java/Scala 程序员对 Flink 的使用。

SQL 客户端的目的是提供一种简单的方式来编写、调试和提交表程序到 Flink 集群上，不需写 Java 或 Scala 代码。SQL 客户端命令行界面（CLI） 能够在命令行中检索和可视化分布式应用的实时结果。

### 1. 入门

本节介绍如何在命令行里启动和运行你的第一个 Flink SQL 程序。SQL 客户端绑定在常规的 Flink 发行包中，因此可以直接运行。仅需要一个正在运行的 Flink 集群就可以在上面执行 Table 程序。如果仅想试用 SQL 客户端，也可以使用以下命令启动本地集群：
```
./bin/start-cluster.sh
```

#### 1.1 启动SQL客户端CLI

SQL 客户端脚本也位于 Flink 的 bin 目录中。将来，用户有两种方式来启动 SQL 客户端命令行界面：通过嵌入式独立进程或者通过连接到远程 SQL 客户端网关。目前仅支持嵌入式模式，现在默认模式就是嵌入式。可以通过以下方式启动 CLI：
```
./bin/sql-client.sh
```
> 注意低版本不能使用该命令

或者显式使用嵌入式模式:
```
./bin/sql-client.sh embedded
```
![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-sql-client-1.png?raw=true)

#### 1.2 执行SQL查询

CLI 启动后，你可以使用 HELP 命令列出所有可用的 SQL 语句。为了验证你的设置及集群连接是否正确，可以输入一条 SQL 查询语句并按 Enter 键执行：
```
SELECT 'Hello World';
```
该查询不需要数据表，并且只会产生一行结果。CLI 将从集群中检索结果并将其可视化。可以按 Q 键退出结果视图。CLI 为维护和可视化结果提供三种模式。下面具体看一下。

> 注意：Flink 1.24.0 版本使用 execution.result-mode 参数。

##### 1.2.1 表格模式

表格模式（table mode）在内存中物化结果，并将结果用规则的分页表格的形式可视化展示出来。执行如下命令启用：
```
SET sql-client.execution.result-mode = table;
```
> 文档中 SET 'sql-client.execution.result-mode' = 'xxx' 方式配置不生效

可以使用如下查询语句查看不同模式的的运行结果：
```sql
SELECT name, COUNT(*) AS cnt FROM (VALUES ('Bob'), ('Alice'), ('Greg'), ('Bob')) AS NameTable(name) GROUP BY name;
```

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-sql-client-2.png?raw=true)

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-sql-client-3.png?raw=true)

##### 1.2.2 变更日志模式

变更日志模式（changelog mode）不会物化结果。可视化展示由插入（+）和撤销（-）组成的持续查询结果流。
```
SET sql-client.execution.result-mode = changelog;
```

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-sql-client-4.png?raw=true)

##### 1.2.3 Tableau模式

Tableau模式（tableau mode）更接近传统的数据库，会将执行的结果以制表的形式直接打在屏幕之上。具体显示的内容取决于作业执行模式(execution.type)：
```
SET sql-client.execution.result-mode = tableau;
```
![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-sql-client-5.png?raw=true)

> 注意：当你在流式查询上使用这种模式时，Flink 会将结果持续的打印在当前的控制台上。如果流式查询的输入是有限数据集，那么 Flink 在处理完所有的输入数据之后，作业会自动停止，同时控制台上的打印也会自动停止。如果你想提前结束这个查询，那么可以直接使用 CTRL-C 按键，这个会停止作业同时停止在控制台上的打印。

### 2. 配置

#### 2.1 启动选项

可以使用如下可选 CLI 命令启动 SQL 客户端：
```
./bin/sql-client.sh --help

Mode "embedded" (default) submits Flink jobs from the local machine.

  Syntax: [embedded] [OPTIONS]
  "embedded" mode options:
         -d,--defaults <environment file>      Deprecated feature: the environment
                                               properties with which every new
                                               session is initialized. Properties
                                               might be overwritten by session
...
```

#### 2.2 客户端配置

| Key     | 默认值     | 类型 | 说明 |
| :------------- | :------------- | :------------- | :------------- |
| sql-client.execution.max-table-result.rows | 1000000 | Integer | 在表格模式下缓存的行数。如果行数超过指定值，则以 FIFO 样式重试该行。|
| sql-client.execution.result-mode | TABLE | 枚举值，可以是 TABLE, CHANGELOG, TABLEAU | 确定展示查询结果的模式。可以是 table、tableau、changelog。|
| sql-client.verbose | false | Boolean | 确定是否将输出详细信息输出到控制台。如果将选项设置为 true，会打印异常堆栈。否则，只输出原因。 |

#### 2.2 使用SQL文件初始化会话

SQL 查询需要配置执行环境。SQL 客户端支持 -i 启动选项以在启动 SQL 客户端时执行初始化 SQL 文件以设置环境。所谓的初始化 SQL 文件，可以使用 DDL 来定义可用的 catalogs、table source、sink、用户自定义函数以及其他执行和部署所需的属性。

下面给出了此类文件的示例：
```sql
-- 定义 Catalogs

CREATE CATALOG MyCatalog
  WITH (
    'type' = 'hive'
  );

USE CATALOG MyCatalog;

-- 定义 DataBase

CREATE DATABASE MyDatabase;

USE MyDatabase;

-- 定义 TABLE

CREATE TABLE MyTable (
  MyField1 INT,
  MyField2 STRING
) WITH (
  'connector' = 'filesystem',
  'path' = '/path/to/something',
  'format' = 'csv'
);

-- 定义 VIEW

CREATE VIEW MyCustomView AS SELECT MyField2 FROM MyTable;

-- 定义用户自定义函数

CREATE FUNCTION foo.bar.AggregateUDF AS myUDF;

-- 修改属性
SET table.planner = blink; -- planner: either blink (default) or old
SET execution.runtime-mode = streaming; -- execution mode either batch or streaming
SET sql-client.execution.result-mode = table; -- available values: table, changelog and tableau
SET sql-client.execution.max-table-result.rows = 10000; -- optional: maximum number of maintained rows
SET parallelism.default = 1; -- optional: Flinks parallelism (1 by default)
SET pipeline.auto-watermark-interval = 200; --optional: interval for periodic watermarks
SET pipeline.max-parallelism = 10; -- optional: Flink's maximum parallelism
SET table.exec.state.ttl = 1000; -- optional: table program's idle state time
SET restart-strategy = fixed-delay;

SET table.optimizer.join-reorder-enabled = true;
SET table.exec.spill-compression.enabled = true;
SET table.exec.spill-compression.block-size = 128kb;
```
上述配置：
- 连接到 Hive Catalog 并使用 MyCatalog 作为当前 Catalog，使用 MyDatabase 作为目录的当前数据库
- 定义一个可以从 CSV 文件中读取数据的表 MyTable
- 定义一个视图 MyCustomView，它使用 SQL 查询声明一个虚拟表
- 定义了一个可以使用类名实例化的用户定义函数 myUDF
- 在流模式下使用 blink 计划器运行语句，并且设置并行度为 1
- 使用表格模式运行 SQL 进行探索性查询，

使用 -i <init.sql> 选项初始化 SQL 客户端会话时，初始化 SQL 文件中允许使用以下语句：
- DDL（CREATE/DROP/ALTER）
- USE CATALOG/DATABASE
- LOAD/UNLOAD MODULE
- SET 命令
- RESET 命令

执行查询或插入语句时，请进入交互模式或使用-f选项提交SQL语句。如果 SQL 客户端在初始化时遇到错误，SQL 客户端将退出并显示错误信息。

### 3. 使用SQL客户端提交作业

SQL 客户端可以允许用户在交互式命令行中或使用 -f 选项执行 sql 文件来提交作业。在这两种模式下，SQL 客户端都可以支持解析和执行 Flink 支持的所有类型的 SQL 语句。

#### 3.1 交互式命令行

在交互式命令行中，SQL 客户端读取用户输入并在获取分号 (;) 时执行语句。如果语句成功执行，SQL 客户端会打印成功消息。当出现错误时，SQL 客户端也会打印错误信息。默认情况下，错误消息仅包含错误原因。为了打印完整的异常堆栈以进行调试，需要通过如下命令设置：
```sql
SET sql-client.verbose = true;
```
> 将 sql-client.verbose 设置为 true

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-sql-client-6.png?raw=true)

#### 3.2 执行SQL文件

SQL 客户端支持使用 -f 选项执行 SQL 脚本文件。SQL 客户端会一一执行 SQL 脚本文件中的语句，并为每条执行的语句打印执行信息。一旦一条语句失败，SQL 客户端就会退出，所有剩余的语句也不会执行。

下面给出了此类文件的示例：
```sql
CREATE TEMPORARY TABLE users (
  user_id BIGINT,
  user_name STRING,
  user_level STRING,
  region STRING,
  PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
  'connector' = 'upsert-kafka',
  'topic' = 'users',
  'properties.bootstrap.servers' = '...',
  'key.format' = 'csv',
  'value.format' = 'avro'
);

-- set sync mode
SET table.dml-sync = true;

-- set the job name
SET pipeline.name = SqlJob;

-- set the queue that the job submit to
SET yarn.application.queue = root;

-- set the job parallism
SET parallism.default = 100;

-- restore from the specific savepoint path
SET execution.savepoint.path = /tmp/flink-savepoints/savepoint-cca7bc-bb1e257f0dab;

INSERT INTO pageviews_enriched
SELECT *
FROM pageviews AS p
LEFT JOIN users FOR SYSTEM_TIME AS OF p.proctime AS u
ON p.user_id = u.user_id;
```
这个配置：
- 定义从 CSV 文件读取的时态表 users，
- 设置属性，例如作业名称，
- 设置保存点路径，
- 提交从指定保存点路径加载保存点的 sql 作业。

> 与交互模式相比，SQL 客户端遇到错误会停止执行并退出。

#### 3.3 执行一组SQL语句

SQL 客户端将每个 INSERT INTO 语句作为单个 Flink 作业执行。但是，这有时性能不是最佳，因为 Pipeline 的某些部分可以重复使用。SQL 客户端支持 STATEMENT SET 语法来执行一组 SQL 语句。这与 Table API 中 StatementSet 功能类似。STATEMENT SET 语法包含一个或多个 INSERT INTO 语句。 STATEMENT SET 块中的所有语句都要经过整体优化后作为一个 Flink 作业执行。

具体语法如下：
```sql
BEGIN STATEMENT SET;
  -- one or more INSERT INTO statements
  { INSERT INTO|OVERWRITE <select_statement>; }+
END;
```
> 包含在 STATEMENT SET 中的语句必须用分号 (;) 分隔。

具体看一下示例：
```sql
CREATE TABLE pageviews (
  user_id BIGINT,
  page_id BIGINT,
  viewtime TIMESTAMP,
  proctime AS PROCTIME()
) WITH (
  'connector' = 'kafka',
  'topic' = 'pageviews',
  'properties.bootstrap.servers' = '...',
  'format' = 'avro'
);

CREATE TABLE pageview (
  page_id BIGINT,
  cnt BIGINT
) WITH (
  'connector' = 'jdbc',
  'url' = 'jdbc:mysql://localhost:3306/mydatabase',
  'table-name' = 'pageview'
);

CREATE TABLE uniqueview (
  page_id BIGINT,
  cnt BIGINT
) WITH (
  'connector' = 'jdbc',
  'url' = 'jdbc:mysql://localhost:3306/mydatabase',
  'table-name' = 'uniqueview'
);

BEGIN STATEMENT SET;

INSERT INTO pageviews
SELECT page_id, count(1)
FROM pageviews
GROUP BY page_id;

INSERT INTO uniqueview
SELECT page_id, count(distinct user_id)
FROM pageviews
GROUP BY page_id;

END;
```
#### 3.4 同步/异步执行DML语句

默认情况下，SQL 客户端异步执行 DML 语句。这意味着，SQL 客户端将 DML 语句的作业提交给 Flink 集群即可，不用等待作业完成。所以 SQL 客户端可以同时提交多个作业。这对于通常长时间运行的流作业很有用。SQL 客户端确保语句成功提交到集群。提交语句后，CLI 将显示有关 Flink 作业的信息：
```sql
Flink SQL> INSERT INTO MyTableSink SELECT * FROM MyTableSource;
[INFO] Table update statement has been successfully submitted to the cluster:
Cluster ID: StandaloneClusterId
Job ID: 6f922fe5cba87406ff23ae4a7bb79044
```
SQL 客户端再提交作业后不会跟踪作业的状态。CLI 进程可以在提交后关闭而不影响查询。Flink 的重启策略负责容错。可以使用 Flink 的 Web 界面、命令行或 REST API 取消查询。但是，对于批处理用户，更常见的是下一个 DML 语句需要等待前一个 DML 语句完成才能执行。为了同步执行 DML 语句，我们可以在 SQL 客户端中设置 table.dml-sync 选项为 true：
```sql
Flink SQL> SET table.dml-sync = true;
[INFO] Session property has been set.

Flink SQL> INSERT INTO MyTableSink SELECT * FROM MyTableSource;
[INFO] Submitting SQL update statement to the cluster...
[INFO] Execute statement in sync mode. Please wait for the execution finish...
[INFO] Complete execution of the SQL update statement.
```
> 如果要终止作业，只需键入 CTRL-C 即可取消执行。

#### 3.5 从保存点启动SQL作业

Flink 支持从指定的保存点启动作业。在 SQL 客户端中，允许使用 SET 命令指定保存点的路径：
```sql
Flink SQL> SET execution.savepoint.path = /tmp/flink-savepoints/savepoint-cca7bc-bb1e257f0dab;
[INFO] Session property has been set.

-- all the following DML statements will be restroed from the specified savepoint path
Flink SQL> INSERT INTO ...
```
当指定了保存点的路径时，Flink 会在执行 DML 语句时会尝试从保存点恢复状态。因为指定的保存点路径会影响后面所有的 DML 语句，你可以使用 RESET 命令来重置这个配置选项，即禁用从保存点恢复：
```sql
Flink SQL> RESET execution.savepoint.path;
[INFO] Session property has been reset.
```
#### 3.6 自定义作业名称

SQL 客户端支持通过 SET 命令为查询和 DML 语句定义作业名称：
```sql
Flink SQL> SET pipeline.name = kafka-to-hive;
[INFO] Session property has been set.

-- all the following DML statements will use the specified job name.
Flink SQL> INSERT INTO ...
```
因为指定的作业名会影响后面所有的查询和 DML 语句，你也可以使用 RESET 命令来重置这个配置，即使用默认的作业名：
```sql
Flink SQL> RESET pipeline.name;
[INFO] Session property has been reset.
```
如果未指定选项 pipeline.name，SQL 客户端将为提交的作业生成默认名称，例如 insert-into_<sink_table_name> 用于 INSERT INTO 语句。

### 4. 兼容性

为了与之前版本兼容，SQL 客户端仍然支持使用 YAML 文件进行初始化，并允许在 YAML 文件中设置 key。当在 YAML 文件中定义 key 时，SQL 客户端将打印警告消息以通知：
```sql
Flink SQL> SET execution.type = batch;
[WARNING] The specified key 'execution.type' is deprecated. Please use 'execution.runtime-mode' instead.
[INFO] Session property has been set.

-- all the following DML statements will be restored from the specified savepoint path
Flink SQL> INSERT INTO ...
```
当使用 SET 命令打印属性时，SQL 客户端会打印所有的属性。为了区分不推荐使用的 key，SQL 客户端使用 [DEPRECATED] 作为标识符：
```
Flink SQL>SET;
execution.runtime-mode=batch
sql-client.execution.result-mode=table
table.planner=blink
[DEPRECATED] execution.planner=blink
[DEPRECATED] execution.result-mode=table
[DEPRECATED] execution.type=batch
```

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-sql-client-7.png?raw=true)

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

原文：[SQL Client](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/dev/table/sqlclient/)
