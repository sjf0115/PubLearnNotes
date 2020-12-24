
### 1. Flink Table API

`Apache Flink` 对 `SQL` 的支持可以追溯到一年前发布的 `0.9.0-milestone1` 版本。此版本通过引入 `Table API` 来提供类似于 `SQL` 查询的功能，此功能可以操作分布式的数据集，并且可以自由地和 `Flink` 其他API进行组合。`Tables` 在发布之初就支持静态的以及流式数据(也就是提供了 `DataSet` 和 `DataStream` 相关APIs)。我们可以将 `DataSet` 或 `DataStream` 转成 `Table`；同时也可以将 `Table` 转换成 `DataSet`或 `DataStream`，正如下面的例子所展示的：
```Scala
val execEnv = ExecutionEnvironment.getExecutionEnvironment
val tableEnv = TableEnvironment.getTableEnvironment(execEnv)

// obtain a DataSet from somewhere
val tempData: DataSet[(String, Long, Double)] =

// convert the DataSet to a Table
val tempTable: Table = tempData.toTable(tableEnv, 'location, 'time, 'tempF)
// compute your result
val avgTempCTable: Table = tempTable
 .where('location.like("room%"))
 .select(
   ('time / (3600 * 24)) as 'day,
   'Location as 'room,
   (('tempF - 32) * 0.556) as 'tempC
  )
 .groupBy('day, 'room)
 .select('day, 'room, 'tempC.avg as 'avgTempC)
// convert result Table back into a DataSet and print it
avgTempCTable.toDataSet[Row].print()
```
上面的例子是通过Scala语言展示的，不过我们也可以在Java中使用Table API。

### 2. 为什么需要引入SQL

大家可以看出，虽然 `Table API` 提供了类似于 `SQL` 的功能来操作分布式的数据，但是其有以下几点问题：
- `Table API` 不能独立使用。`Table API` 必须包含在 `DataSet` 或 `DataStream` 的程序中。
- 对于批处理表(batch Tables)的查询并不支持外连接(outer joins)、排序以及其他很多在SQL查询中经常会使用到的标量函数(scalar functions)；
- 在流数据表(streaming tables)上的查询只支持 `fiter`、`union` 以及 `projections` 操作，并不支持 `aggregations` 或者 `joins` 操作。
- `Table` 查询语句的翻译(应该是翻译成逻辑计划)并没用使用到查询优化技术，只有在物理计划的时候会有相应的优化，因为物理优化会应用到所有的 `DataSet` 程序。
- 在程序中使用 `Table API` 远没有直接使用 `SQL` 来的方便。

针对以上的各种缺陷，在 `Apache Flink` 中引入 `SQL` 的支持势在必行。`Flink 0.9` 引入的 `Table API`、关系表达式的代码生成以及运行操作符(runtime operators)等技术都为SQL的引入奠定了基础。那为什么最初 `Flink` 社区没有选择先开发出一套新的 `SQL-on-Hadoop` 解决方案呢？那是因为社区认为在整个 `Hadoop` 生态环境下已经存在了大量的 `SQL-on-Hadoop` 解决方案；比如 `Apache Hive`, `Apache Drill`, `Apache Impala,` `Apache Tajo` 等等，所以集中精力提升 `Flink` 的其他方面的性能更重要。

但是随着流处理系统在业界的广泛使用以及 `Flink` 受到的关注越来越多，`Flink`社区最终决定很有必要为用户提供一个简单的 SQL 接口来操作分布式数据。于是在半年前，`Flink`开始着手于扩展 `Table API` 使得用户可以直接在流数据（当然静态的数据更可以使用）上使用 SQL。`Flink`开始使用 `Apache Calcite` 来为用户提供SQL功能，并基于 `Apache Calcite` 重新设计 `Table API` 的架构。`Apache Calcite` 是一个流行的 SQL 解析和优化框架，并且被许多项目使用，包括 `Apache Hive`, `Apache Drill`, `Cascading` 、`Apache Kylin`、`Apache Storm` 等等；而且 `Apache Calcite` 社区将 `SQL on streams` 作为他们的未来规划，尤其适合 `Flink` 的SQL接口。

SQL 的支持在 `Flink 1.1.0` 版本正式发布。因为刚刚开始引入，所以最初版本 SQL 只支持在流数据上进行`select`、`filter`、`union` 等操作；和 `Flink 1.0.0` 相比，`Table API` 将支持更多的 `scalar functions`，支持从外部数据源读取数据并且支持写入到外部数据源。

在 `Flink 1.2.0` 版本，SQL 的将会支持更多的特性。比如支持各种类型的 `window aggregates` 以及 `Streaming join`。当然，这些开发是和 `Apache Calcite` 社区共同合作的结果。


### 3. 如何在程序中使用SQL

在 `Flink` 程序中使用 SQL 查询只需要使用 `TableEnvironment` 的 `sql()` 方法。这个方法将会返回 SQL 查询的结果，结果的类型是 `Table`，我们可以将它转换成 `DataSet` 或者 `DataStream`、或者使用 `Table API` 操作它、或者将他写入到 `TableSink` 中。SQL 和 Table 的查询API可以无缝地进行整合。

任何的 `Table`, `DataSet`, `DataStream` 或者 `TableSource` 都需要通过 `TableEnvironment` 进行注册，使得可以在其之上使用 SQL 查询。

#### 3.1 SQL on Batch Tables

下面是介绍如何在Batch Tables上使用SQL的例子：
```scala
val env = ExecutionEnvironment.getExecutionEnvironment
val tableEnv = TableEnvironment.getTableEnvironment(env)

// read a DataSet from an external source
val ds: DataSet[(Long, String, Integer)] = env.readCsvFile(...)
// register the DataSet under the name "Orders"
tableEnv.registerDataSet("Orders", ds, 'user, 'product, 'amount)
// run a SQL query on the Table and retrieve the result as a new Table
val result = tableEnv.sql(
  "SELECT SUM(amount) FROM Orders WHERE product LIKE '%Rubber%'")
```

目前 `Batch Tables` 只支持 `select`、`filter`、`projection`, `inner equi-joins`, `grouping`, `non-distinct aggregates` 以及 `sorting`。

下面特性目前在 `Batch Tables` 不支持：
- 时间类型(DATE, TIME, TIMESTAMP, INTERVAL)以及DECIMAL类型
- Distinct aggregates (比如：COUNT(DISTINCT name))
- 非等值Join以及笛卡儿乘积；
- 通过order里面的位置选择结果 (ORDER BY OFFSET FETCH)
- Grouping sets
- INTERSECT以及EXCEPT集合操作。

#### 3.2 SQL on Streaming Tables

SQL查询可以扩展到 Streaming Tables上，我们只需要将SELECT关键字用SELECT STREAM 替换即可。下面是使用示例：
```scala
val env = StreamExecutionEnvironment.getExecutionEnvironment
val tEnv = TableEnvironment.getTableEnvironment(env)

// read a DataStream from an external source
val ds: DataStream[(Long, String, Integer)] = env.addSource(...)
// register the DataStream under the name "Orders"
tableEnv.registerDataStream("Orders", ds, 'user, 'product, 'amount)
// run a SQL query on the Table and retrieve the result as a new Table
val result = tableEnv.sql(
  "SELECT STREAM product, amount FROM Orders WHERE product LIKE '%Rubber%'")
  ```
目前在Streaming Tables上执行SQL只支持SELECT, FROM, WHERE以及UNION； Aggregations和joins暂时不支持。


原文： https://www.iteblog.com/archives/1691.html
