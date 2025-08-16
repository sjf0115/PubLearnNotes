在 Hadoop 生态中，Hive 作为经典的数据仓库工具，其核心是将类 SQL 查询（HQL）转化为分布式计算任务（如 MapReduce、Tez、Spark）来执行。这为处理海量数据（PB 级）提供了强大的能力。然而，启动这些分布式任务本身是有显著开销的：资源调度（YARN）、启动 JVM 容器、任务初始化、中间结果 Shuffle 等。想象一下，你只是想看一眼表的前 10 行数据，或者快速查询某个特定分区的几条记录，却需要等待几十秒甚至几分钟，仅仅因为系统启动了一整套“重装武器”来处理这个“小目标”——这无疑是巨大的资源浪费和体验痛点。

## 1. FetchTask 应运而生：轻量高效的解决方案

FetchTask 正是 Hive 为了解决上述“大炮打蚊子”问题而设计的核心优化机制。它的核心思想非常简单却极其有效：对于满足特定条件的简单查询，完全绕过复杂的 MapReduce/Tez/Spark 执行引擎，直接从数据存储（HDFS）或元存储（Metastore）读取所需数据并返回给客户端。

FetchTask 的价值：为什么它如此重要？
- 极致的低延迟：这是 FetchTask 最核心的价值。避免了分布式任务的启动和管理开销，使得简单查询的响应时间从秒级甚至分钟级骤降至毫秒级或亚秒级。用户体验提升是质的飞跃。
- 降低资源消耗：无需申请和占用 YARN 资源（Containers）、减少 JVM 启动/销毁开销、避免不必要的网络传输（Shuffle）。这对集群的整体资源利用率和稳定性有积极影响，尤其是在高并发执行大量小查询的场景下。
- 提升开发与探索效率：数据分析师和工程师在进行数据探查（Data Exploration）、数据质量检查、调试 SQL 语句时，经常需要执行 SELECT * FROM ... LIMIT N 或带简单过滤的查询。FetchTask 让这些操作变得极其迅捷，大大提升了工作效率。
- 优化元数据操作： 像 SHOW TABLES, SHOW PARTITIONS, DESCRIBE TABLE 这类仅需访问 Metastore 的元数据操作，天生就通过 FetchTask 执行，快速返回结果。

## 2. 配置

### 2.1 hive.fetch.task.conversion

FetchTask 并非对所有查询都生效。它的行为由关键参数 `hive.fetch.task.conversion` 严格掌控：
```xml
<property>
  <name>hive.fetch.task.conversion</name>
  <value>none|minimal|more</value>
</property>
```
可支持的选项有 `none`,`minimal` 和 `more`，从 Hive 0.10.0 版本到 Hive 0.13.1 版本起，默认值为 `minimal`，Hive 0.14.0版本以及更高版本默认值改为 `more`。理解这个参数的不同模式至关重要。

#### 2.1.1 none

> 在 0.14.0 版本中引入

禁用任何形式的 Fetch Task 优化。所有查询，无论多么简单（包括 `SELECT * FROM table LIMIT 1`），都强制走 MapReduce（或 Tez/Spark）执行引擎。

优点：
- 行为绝对一致，完全避免了直接 Fetch 大量数据的风险。

缺点：
- 对简单查询的性能影响极其巨大。即使是看一眼表的前几行数据，也可能需要等待几十秒甚至几分钟（等待资源调度、启动任务等）。
- 用户体验极差，不适合交互式操作。

#### 2.1.2 minimal

> 从 Hive 0.10.0 版本到 Hive 0.13.1 版本起，默认值为 `minimal`。

- 投影限制：
  - 仅 `SELECT *` 或列投影
- 过滤限制：
  - 无 WHERE 条件
  - 或仅分区列常量过滤
- 可选 LIMIT：
  - 有无 LIMIT 均可触发

> 注意不同版本语义不一致，注意版本

优点：
- 适用范围非常窄，几乎不会出现意外行为。

缺点：
- 对大多数常见的简单查询（如带非分区字段过滤或 LIMIT 的查询）无效，优化效果有限。

#### 2.1.3 more

> Hive 0.14.0 版本以及更高版本默认值改为 `more`。推荐值，最常用且最实用。

在 minimal 的基础上更强大，SELECT 不仅仅是查看，还可以单独选择列，FILTER 也不再局限于分区字段，同时支持虚拟列（别名）。

优点：
- 覆盖了绝大多数交互式查询、数据探查场景，性能提升效果显著。

缺点：
- 无 LIMIT 且可能返回大量数据的查询，直接 Fetch 可能对 HS2 或客户端造成压力（OOM/网络拥堵）。强烈建议配合 `hive.fetch.task.conversion.threshold` 使用！

### 2.2 hive.fetch.task.conversion.threshold

为了防止 more 模式下对“语法简单但数据量巨大”的查询意外触发 FetchTask（导致 HS2 尝试扫描海量文件），Hive 提供了 `hive.fetch.task.conversion.threshold` 参数作为安全阀：
```xml
<property>
  <name>hive.fetch.task.conversion.threshold</name>
  <value>1073741824</value>
</property>
```

> 从 Hive 0.13.0 版本到 Hive 0.13.1 版本起，默认值为`-1`（表示没有任何的限制），Hive 0.14.0 版本以及更高版本默认值改为 `1073741824`(1G)。

使用 `hive.fetch.task.conversion` 的输入阈值（以字节为单位）。如果目标表在本机，则输入长度通过文件长度的总和来计算。如果不在本机，则表的存储处理程序可以选择实现 `org.apache.hadoop.hive.ql.metadata.InputEstimator` 接口。负阈值意味着使用 `hive.fetch.task.conversion` 没有任何的限制。

## 3. 设置 Fetch 任务

第一种方式是直接在命令行中使用 `set` 命令进行设置:
```
hive> set hive.fetch.task.conversion=more;
```
第二种方式是使用 `hiveconf` 进行设置:
```
bin/hive --hiveconf hive.fetch.task.conversion=more
```
上面的两种方法虽然都可以开启 Fetch Task，但是都是临时的。如果你想一直启用这个功能，可以在 `${HIVE_HOME}/conf/hive-site.xml` 里面修改配置：
```xml
<property>
  <name>hive.fetch.task.conversion</name>
  <value>more</value>
</property>
```

## 4. 如何确认查询使用了 Fetch Task？

可以通过 EXPLAIN 确认是否触发 Fetch Task：
```sql
EXPLAIN SELECT uid, pid FROM user_behavior LIMIT 100;
```
执行计划输出如下所示：
```sql
STAGE DEPENDENCIES:
  Stage-0 is a root stage

STAGE PLANS:
  Stage: Stage-0
    Fetch Operator
      limit: 100
      Processor Tree:
        TableScan
          alias: user_behavior
          Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
          Select Operator
            expressions: uid (type: string), pid (type: string)
            outputColumnNames: _col0, _col1
            Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
            Limit
              Number of rows: 100
              Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
              ListSink
```
当你看到 `Stage-0` 时表示使用了 Fetch Task，`Stage-0` 是 `Fetch Task` 专属阶段：
```
STAGE DEPENDENCIES:
  Stage-0 is a root stage    # Fetch Task 路径!
```
