

> 1.13.0

## 1. 初始化脚本和语句集合（Statement Sets）

SQL Client 是一种直接运行和部署 SQL 流或批作业的简便方式，用户不需要编写代码就可以从命令行调用 SQL，或者作为 CI / CD 流程的一部分。

这个版本极大的提高了 SQL Client 的功能。现在基于所有通过 Java 编程（即通过编程的方式调用 TableEnvironment 来发起查询）可以支持的语法，现在 SQL Client 和 SQL 脚本都可以支持。这意味着 SQL 用户不再需要添加胶水代码来部署他们的SQL作业。

### 1.1 配置简化和代码共享

Flink 后续将不再支持通过 Yaml 的方式来配置 SQL Client（注：目前还在支持，但是已经被标记为废弃）。作为替代，SQL Client 现在支持使用一个初始化脚本在主 SQL 脚本执行前来配置环境。这些初始化脚本通常可以在不同团队/部署之间共享。它可以用来加载常用的 catalog，应用通用的配置或者定义标准的视图：
```
./sql-client.sh -i init1.sql init2.sql -f sqljob.sql
```

### 1.2 更多的配置项

通过增加配置项，优化 SET / RESET 命令，用户可以更方便的在 SQL Client 和 SQL 脚本内部来控制执行的流程。

### 1.3 通过语句集合来支持多查询

多查询允许用户在一个 Flink 作业中执行多个 SQL 查询（或者语句）。这对于长期运行的流式 SQL 查询非常有用。语句集可以用来将一组查询合并为一组同时执行。

以下是一个可以通过 SQL Client 来执行的 SQL 脚本的例子。它初始化和配置了执行多查询的环境。这一脚本包括了所有的查询和所有的环境初始化和配置的工作，从而使它可以作为一个自包含的部署组件。
```sql
-- set up a catalog
CREATE CATALOG hive_catalog WITH ('type' = 'hive');
USE CATALOG hive_catalog;

-- or use temporary objects
CREATE TEMPORARY TABLE clicks (
  user_id BIGINT,
  page_id BIGINT,
  viewtime TIMESTAMP
) WITH (
  'connector' = 'kafka',
  'topic' = 'clicks',
  'properties.bootstrap.servers' = '...',
  'format' = 'avro'
);

-- set the execution mode for jobs
SET execution.runtime-mode=streaming;

-- set the sync/async mode for INSERT INTOs
SET table.dml-sync=false;

-- set the job's parallelism
SET parallism.default=10;

-- set the job name
SET pipeline.name = my_flink_job;

-- restore state from the specific savepoint path
SET execution.savepoint.path=/tmp/flink-savepoints/savepoint-bb0dab;

BEGIN STATEMENT SET;

INSERT INTO pageview_pv_sink
SELECT page_id, count(1) FROM clicks GROUP BY page_id;

INSERT INTO pageview_uv_sink
SELECT page_id, count(distinct user_id) FROM clicks GROUP BY page_id;

END;
```

https://issues.apache.org/jira/browse/FLINK-23552
https://issues.apache.org/jira/browse/FLINK-22540
