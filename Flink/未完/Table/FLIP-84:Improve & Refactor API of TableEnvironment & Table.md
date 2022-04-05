
在 Flink 1.9 中，TableEnvironment 引入了 `void execute(String jobName)` 接口来触发 Flink Table 程序执行，并扩展了 `void sqlUpdate(String sql)` 接口，不仅可以执行 INSERT 语句，还可以执行 DDL 语句和 USE 语句。但是随着越来越多的场景，当前 API 设计存在一些问题：
- sqlUpdate() 的执行语义不一致。目前，当一个 DDL 语句传递给该方法时会立即执行，而当我们调用 execute() 方法时，实际上会执行一个 INSERT INTO 语句，这让用户很困惑。
- 不支持从 execute 中获取返回值。FLIP-69[1] 引入了很多常见的 DDL，例如，SHOW TABLES，要求 TableEnvironment 可以有一个接口来获取一个 DDL 的执行结果。SQL CLI 对这个特性也有强烈的需求，这样我们就可以很容易地统一 SQL CLI 和 TableEnvironemt 的执行方式。此外，方法名称 sqlUpdate 与 SHOW TABLES 之类的操作不一致。
- 不明确和错误的支持缓冲 SQL/表执行[2]。Blink planner 提供了优化多个 sink 的能力，但是我们没有一个明确的机制通过 TableEnvironment API 来控制整个流程。
- 不清楚 Flink Table 程序触发点。TableEnvironment.execute() 和 StreamExecutionEnvironment.execute() 都可以触发 Flink Table 程序执行。
  - 如果使用 TableEnvironment 来构建 Flink Table 程序，则必须使用 TableEnvironment.execute() 触发执行，因为无法获取 StreamExecutionEnvironment 实例。
  - 如果使用 StreamTableEnvironment 来构建 Flink Table 程序，这两种方式都可以来触发执行。
  - 如果将 Table 程序转换为 DataStream 程序（使用 StreamExecutionEnvironment.toAppendStream/toRetractStream），也可以使用这两种方式来触发执行。
所以很难解释应该使用哪种 execute 方法。与 StreamTableEnvironment 类似，BatchTableEnvironment 也有同样的问题。
- 不支持多行语句。目前，TableEnvironment 仅支持单条语句。多行语句也是 SQL 客户端和第三方基于 SQL 的平台的一个重要特性。

TableEnvironment#sqlUpdate() 方法对于 DDL 会立即执行，但对于 INSERT INTO DML 语句却是 buffer 住的，直到调用 TableEnvironment#execute() 才会被执行，所以在用户看起来顺序执行的语句，实际产生的效果可能会不一样。

触发作业提交有两个入口，一个是 TableEnvironment#execute()，另一个是 StreamExecutionEnvironment#execute()，于用户而言很难理解应该使用哪个方法触发作业提交。

单次执行不接受多个 INSERT INTO 语句。




让我们举个例子来解释缓冲 SQL/Tables 执行问题：
```sql
tEnv.sqlUpdate("CREATE TABLE test (...) with (path = '/tmp1')");
tEnv.sqlUpdate("INSERT INTO test SELECT ...");
tEnv.sqlUpdate("DROP TABLE test");
tEnv.sqlUpdate("CREATE TABLE test (...) with (path = '/tmp2')");
tEnv.execute()
```
- 一次执行哪些 SQL 以及在 execute 方法执行之前需要缓冲哪些 SQL，用户对此会比较困惑。
- 缓存 SQL/Table 可能会导致未知行为。我们可能想将数据插入到 `test` 表中下的 `/tmp1` 路径，但可能会插入到 `/tmp2` 路径的错误结果。

本次 FLIP 的目标是解决上面提到的问题，使 TableEnvironment & Table 中的 API 更加清晰和稳定。此 FLIP 不支持多行语句，这需要在进一步的 FLIP 中进行更多讨论。

## 2. Public Interfaces

我们建议弃用如下方法：
- TableEnvironment.sqlUpdate(String)
- TableEnvironment.insertInto(String, Table)
- TableEnvironment.execute(String)
- TableEnvironment.explain(boolean)
- TableEnvironment.fromTableSource(TableSource<?>)
- Table.insertInto(String)

同时，我们建议引入以下新方法：
- TableEnvironment.executeSql：执行单条语句并返回执行结果
- TableEnvironment.explainSql：获取单条语句的 AST 和执行计划
- TableEnvironment.createStatementSet：创建一个 StatementSet 实例，可以将 DML 语句或 Table 添加到集合中并批量 explain 或 execute。

```java
// Table 中添加新方法
interface Table {
    TableResult executeInsert(String tablePath);
    TableResult executeInsert(String tablePath, boolean overwrite);
    String explain(ExplainDetail... extraDetails);
    TableResult execute();
}
// 添加接口类 TableResult
interface TableResult {
    Optional<JobClient> getJobClient();
    TableSchema getTableSchema();
    ResultKind getResultKind();
    Iterator<Row> collect();
    void print();
}
// 添加枚举类 ResultKind
public enum ResultKind {
    SUCCESS,
    SUCCESS_WITH_CONTENT
}

// 添加接口类 StatementSet
interface StatementSet  {
    StatementSet addInsertSql(String statement);
    StatementSet addInsert(String targetPath, Table table);
    String explain(ExplainDetail... extraDetails);
    TableResult execute();
}
```

针对目前杂乱的 Flink Table 程序触发点，我们建议：对于 TableEnvironment 和 StreamTableEnvironment，一旦将 Table 程序转换为 DataStream 程序（通过 toAppendStream 或 toRetractStream 方法），必须使用 StreamExecutionEnvironment.execute 来触发 DataStream 程序。BatchTableEnvironment 规则类似，必须使用 TableEnvironment.execute() 触发 Table 批处理程序执行，一旦将 Table 程序（通过 toDataSet 方法）转换为 DataSet 程序，必须使用 ExecutionEnvironment.execute 触发 DataSet 程序。

## 3. 提议变更

Flink SQL 1.11 提供了新 API，即 TableEnvironment#executeSql()，它统一了执行 SQL 的行为， 无论接收 DDL、查询 query 还是 INSERT INTO 都会立即执行。针对多 sink 场景提供了 StatementSet 和 TableEnvironment#createStatementSet() 方法，允许用户添加多条 INSERT 语句一起执行。

除此之外，新的 execute 方法都有返回值，用户可以在返回值上执行 print，collect 等方法。


### 3.1 TableEnvironment.sqlUpdate(String)

`void sqlUpdate(String sql)` 方法会立即执行 DDL，而 DML 会被缓存并由 TableEnvironment.execute() 触发。两种行为都应保持一致。所以这种方法将被弃用。我们提出了一种新的可以返回执行结果的阻塞方法：
```java
interface TableEnvironment {
    TableResult executeSql(String statement);
}
```
该方法只支持执行单条语句，可以是 DDL、DML、DQL、SHOW、DESCRIBE、EXPLAIN 或者 USE 语句。对于 DML 和 DQL 语句，一旦提交作业，此方法就会返回 TableResult。对于 DDL 和 DCL 语句，一旦操作完成，就会返回 TableResult。TableResult 表示执行结果，包含结果数据和结果 Schema。如果是 DML 语句，TableResult 包含一个关联作业的 JobClient。
```java
interface TableResult {
  Optional<JobClient> getJobClient();
  TableSchema getTableSchema();
  ResultKind getResultKind();
  Iterator<Row> collect();
  void print();
}

public enum ResultKind {
    SUCCESS,
    SUCCESS_WITH_CONTENT
}
```
下表描述了每种语句的结果：

### 3.2 TableEnvironment.insertInto(String, Table) & Table.insertInto(String)

TableEnvironment.insertInto(String, Table) & Table.insertInto(String) 与 sqlUpdate 方法一样，TableEnvironment.insertInto(String, Table) 和 Table.insertInto(String) 也会对 Tables 进行缓存，会导致缓存问题。所以这两种方法将被弃用。


### 3.3 TableEnvironment.execute(String) & TableEnvironment.explain(boolean)

由于我们将禁用缓存 SQL/Table 以及执行计划，因此提供 `execute(String)` 作为触发入口点是没有意义的，并且也不应该再使用 explain(boolean) 方法。所以我们建议弃用这两种方法。我们引入了一个名为 createStatementSet 的新方法以及一个名为 StatementSet 的新类，以支持多个 SQL/Table 的优化。只有 DML 语句和 Table 可以添加到 StatementSet 中。对于 DML，现在只支持 INSERT，以后也可以支持 DELETE 和 UPDATE。

StatementSet 支持通过 addXX 方法添加 DM L和 Tables 列表，通过 explain 方法获取所有语句和表的计划，通过 execute 方法优化整个语句和表并提交作业。调用 execute 方法时，添加的语句和表将被清除。
```java
interface TableEnvironment {
    StatementSet createStatementSet();
}

interface StatementSet  {
    StatementSet addInsertSql(String statement);
    StatementSet addInsert(String targetPath, Table table);
    StatementSet addInsert(String targetPath, Table table, boolean overwrite);
    String explain(ExplainDetail... extraDetails);
    TableResult execute();
}

public enum ExplainDetail {
   STATE_SIZE_ESTIMATE,
   UID,
   HINTS,
   ...
}
```
每个语句和 Table 都有一个返回值，表示语句或 Table 的受影响行数。所以 TableResult 有多列。所有列类型都是 BIGINT，列名是 'affected_rowcount_' 加上语句或 Table 的下标。例如
```java
StatementSet stmtSet = tEnv.createStatementSet();
stmtSet.addInsertSql("insert into xx ...");
stmtSet.addInsert("yy", tEnv.sqlQuery("select ..."));
stmtSet.execute("test")
```
TableResult 中的 Schema 和数据：

![]()

### 3.4 TableEnvironment.fromTableSource(TableSource<?>)

由于 Flip-64 在 TableEnvironment 已经弃用了通过 ConnectTableDescriptor#createTemporaryTable 注册 TableSource。所以这种方法也应该被弃用。

### 3.5 其他新提议的方法

目前，我们不能直接在 TableEnvironment 中对语句 explain，必须通过 TableEnvironment.sqlQuery 方法将语句转换为 Table。同时，我们也无法对 INSERT 语句进行 explain，因为我们无法将 INSERT 语句转换为 Table。我们引入了 TableEnvironment.explainSql() 方法来直接支持对 DQL 和 DML 语句的 explain。explainSql 方法只接受单个语句。

```java
interface TableEnvironment {
    String explainSql(String statement, ExplainDetail... extraDetails);
}
```
我们还介绍了如下方法，以使对 Table 的编程更加流畅：
```java
interface Table {
    TableResult executeInsert(String tablePath);
    TableResult executeInsert(String tablePath, boolean overwrite);
    String explain(ExplainDetail... extraDetails);
    TableResult execute();
}
```
### 3.6 如何纠正执行行为？

首先，让我们深入讨论缓冲区问题。实际上有两级缓冲，TableEnvironment 会缓冲 SQLs/Tables，StreamExecutionEnvironment 会缓冲 transformations 以生成 StreamGraph。每个 TableEnvironment 实例都包含一个 StreamExecutionEnvironment 实例。目前，当将 FlinkRelNode 转换为 Flink operator 时，生成的 transformations 会添加到 StreamExecutionEnvironment 的缓冲区。bug[2] 也是由这种行为引起的。我们再举一个简单的例子来说明 StreamExecutionEnvironment 的缓冲区问题。
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
StreamTableEnvironment tEnv = StreamTableEnvironment.create(env);

// will add transformations to env when translating to execution plan
tEnv.sqlUpdate("INSERT INTO sink1 SELECT a, b FROM MyTable1")

Table table = tEnv.sqlQuery("SELECT c, d from MyTable2")
DataStream dataStream = tEnv.toAppendStream(table, Row.class)
dataStream…

env.execute("job name");
// or tEnv.execute("job name")
```
每个 execute 方法提交的作业包含两个查询的拓扑。用户对这种行为感到困惑。正如公共接口中所建议的，StreamExecutionEnvironment.execute 只触发 DataStream 程序执行，而 TableEnvironment.execute 只触发 Table 程序执行。因此，上述示例的预期行为是 `env.execute("job name")` 提交第二个查询，而 `tEnv.execute("job name") ` 提交第一个查询。

为了满足需求，我们改变 TableEnvironment 的当前行为：TableEnvironment 实例缓冲 SQL/Tables，并且在转换为执行计划时不会将生成的 transformations 添加到 StreamExecutionEnvironment 实例。解决方案类似于 DummyStreamExecutionEnvironment。我们可以使用 StreamGraphGenerator 根据转换生成 StreamGraph。这要求 StreamTableSink 始终返回 DataStream，并且应该删除 StreamTableSink.emitDataStream 方法，因为它在 Flink 1.9 中已被弃用。 StreamExecutionEnvironment 实例仅缓冲从 DataStream 转换的转换。
BatchTableEnvironment 的解决方案类似于 StreamExecutionEnvironment，`BatchTableSink.emitDataSet` 方法应该返回 DataSink，可以通过基于 DataSinks 的计划生成器创建 DataSet 计划。 ExecutionEnvironment 实例仅缓冲从 DataSet 转换的 DataSink。

现在，我们引入 `StatementSet` 来要求用户显式缓冲 SQL/表以支持多个接收器优化。虽然 `insertInto`、`sqlUpdate` 和 `execute` 方法已弃用，但它们不会立即被删除，因此弃用方法和新方法必须在一个或多个版本中协同工作。删除不推荐使用的方法后，将删除 TableEnvironment 的缓冲区。

在我们纠正了`execute`方法的行为之后，即使混合使用不推荐使用的方法、新方法和`to DataStream`方法，用户也可以轻松正确地编写表程序。


我们将列出一些使用旧 API 和提议 API 的示例，以便在本节中进行直接比较。


新旧 API 对比如下表所示：

| 当前接口 | 新接口 |
| :------------- | :------------- |
| tEnv.sqlUpdate("CREATE TABLE..."); | TableResult result = tEnv.executeSql("CREATE TABLE..."); |
| tEnv.sqlUpdate("INSERT INTO...SELECT...");<br>tEnv.execute(); | TableResult result = tEnv.executeSql("INSERT INTO ... SELECT..."); |
| tEnv.sqlUpdate("insert into xx ...");<br>tEnv.sqlUpdate("insert into yy ...");<br>tEnv.execute();| StatementSet ss =tEnv.createStatementSet();<br>ss.addInsertSql("insert into xx ...");<br>ss.addInsertSql("insert into yy ...");<br>TableResult result = ss.execute();|




[FLIP-84: Improve & Refactor API of TableEnvironment & Table](https://cwiki.apache.org/confluence/pages/viewpage.action?pageId=134745878)
