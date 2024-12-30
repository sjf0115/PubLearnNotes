## 1. 执行路径

在 MySQL 的 JDBC 驱动中，`executeBatch` 方法有三种执行路径：
-  `multi-value` 批量插入 `executeBatchedInserts`
- `multi-queries` 多语句批处理 `executePreparedBatchAsMultiStatement`
- 串行批处理 `executeBatchSerially`

```java
protected long[] executeBatchInternal() throws SQLException {
    synchronized (checkClosed().getConnectionMutex()) {
        ...
        // 是否是批处理
        if (!this.batchHasPlainStatements && this.rewriteBatchedStatements.getValue()) {
            // 批量插入
            if (((PreparedQuery<?>) this.query).getParseInfo().canRewriteAsMultiValueInsertAtSqlLevel()) {
                return executeBatchedInserts(batchTimeout);
            }
            // 多语句批量执行
            if (!this.batchHasPlainStatements && this.query.getBatchedArgs() != null && this.query.getBatchedArgs().size() > 3) {
                return executePreparedBatchAsMultiStatement(batchTimeout);
            }
        }
        // 串行执行批处理
        return executeBatchSerially(batchTimeout);
        ...
    }
}
```
批处理执行路径取决于两个条件：
- `batchHasPlainStatements`：批处理
- `rewriteBatchedStatements`：批处理重写

### 1.1 纯SQL批处理 batchHasPlainStatements

> 纯 SQL 语句还是参数化语句

`batchHasPlainStatements` 用于指示批处理操作是否包含纯 SQL 语句，默认值为 `false`。当设置为 `true` 时，批处理操作包含纯 SQL 语句；设置为 `false` 时，批处理操作将包含参数化语句。这个参数主要用于优化批处理操作的性能和兼容性。

`addBatch()` 方法中使用的是默认值，表示批处理操作使用参数化语句；`addBatch(String sql)` 方法设置为 `true`，表示批处理操作使用纯 SQL 语句：
```java
protected boolean batchHasPlainStatements = false;

@Override
public void addBatch(String sql) throws SQLException {
    synchronized (checkClosed().getConnectionMutex()) {
        this.batchHasPlainStatements = true;
        super.addBatch(sql);
    }
}

@Override
public void addBatch() throws SQLException {
    synchronized (checkClosed().getConnectionMutex()) {
        QueryBindings<?> queryBindings = ((PreparedQuery<?>) this.query).getQueryBindings();
        queryBindings.checkAllParametersSet();
        this.query.addBatch(queryBindings.clone());
    }
}
```
如果 `batchHasPlainStatements` 为 `true`，即不能使用 `multi-value` 或者 `multi-queries` 批处理重写来优化执行语句。在 `PreparedStatement` 中使用的是参数化语句，此时 `batchHasPlainStatements` 为 `false`。

### 1.2 批处理重写 rewriteBatchedStatements

这里的 `rewriteBatchedStatements` 对应 JDBC 连接 URL 中的 `rewriteBatchedStatements` 参数，用于启用或禁用在 MySQL 中的批处理重写特性：
```java
// StatementImpl
protected RuntimeProperty<Boolean> rewriteBatchedStatements;
this.rewriteBatchedStatements = pset.getBooleanProperty(PropertyKey.rewriteBatchedStatements);
```

> PropertyKey.rewriteBatchedStatements 枚举为 rewriteBatchedStatements("rewriteBatchedStatements", true),

因此这里的 `rewriteBatchedStatements` 变量完全取决于 JDBC 连接 URL 中的 `rewriteBatchedStatements` 参数。

当 `rewriteBatchedStatements` 设置为 `true` 时，JDBC 驱动程序会尝试把多个 SQL 语句一次性发送到数据库执行，这样可以减少网络开销和数据库的处理，从而提高性能。这个参数默认是关闭的，因为不是所有的 SQL 语句都能被成功重写。只有当你确信你的 SQL 可以被正确重写时才应该开启它。以下是如何在 JDBC URL 中设置 rewriteBatchedStatements 参数的例子：
```java
String URL = "jdbc:mysql://localhost:3306/test?rewriteBatchedStatements=true";
```

### 2. 批量插入

先介绍一下 `multi-value` 批量插入模式，通常指的是一个查询可以返回多个值。在 MySQL 中，你可以使用 `INSERT` 语句同时插入多行数据：
```sql
INSERT INTO tb_test(id, name) VALUES(1,'1'),(2,'2'),(3,'3')
```

在 JDBC 连接 URL 中设置 `rewriteBatchedStatements` 参数并且使用的是 `PreparedStatement` 参数化语句时可能会是如下两种执行路径：
- `executeBatchedInserts`
- `executePreparedBatchAsMultiStatement`

```java
if (!this.batchHasPlainStatements && this.rewriteBatchedStatements.getValue()) {
    // 批量插入
    if (((PreparedQuery<?>) this.query).getParseInfo().canRewriteAsMultiValueInsertAtSqlLevel()) {
        return executeBatchedInserts(batchTimeout);
    }
    // 多语句批量执行
    if (!this.batchHasPlainStatements && this.query.getBatchedArgs() != null && this.query.getBatchedArgs().size() > 3) {
        return executePreparedBatchAsMultiStatement(batchTimeout);
    }
}
```
如果 `multi-value` 批量插入时会进入 `executeBatchedInserts` 执行路径，具体取决于 `canRewriteAsMultiValueInsert` 参数：
```java
// 批量插入
if (((PreparedQuery<?>) this.query).getParseInfo().canRewriteAsMultiValueInsertAtSqlLevel()) {
    return executeBatchedInserts(batchTimeout);
}
```
该参数在 ParseInfo 构造函数中进行设置：
```java
// ParseInfo.canRewriteAsMultiValueInsertAtSqlLevel
public boolean canRewriteAsMultiValueInsertAtSqlLevel() {
    return this.canRewriteAsMultiValueInsert;
}

public ParseInfo(String sql, Session session, String encoding, boolean buildRewriteInfo) {
    ...
    if (buildRewriteInfo) {
        this.canRewriteAsMultiValueInsert =
                this.numberOfQueries == 1
                && !this.parametersInDuplicateKeyClause
                && canRewrite(sql, this.isOnDuplicateKeyUpdate, this.locationOfOnDuplicateKeyUpdate, this.statementStartPos);

        if (this.canRewriteAsMultiValueInsert && session.getPropertySet().getBooleanProperty(PropertyKey.rewriteBatchedStatements).getValue()) {
            buildRewriteBatchedParams(sql, session, encoding);
        }
    }
}

protected static boolean canRewrite(String sql, boolean isOnDuplicateKeyUpdate, int locationOfOnDuplicateKeyUpdate, int statementStartPos) {
    // Needs to be INSERT or REPLACE.
    // Can't have INSERT ... SELECT or INSERT ... ON DUPLICATE KEY UPDATE with an id=LAST_INSERT_ID(...).

    if (StringUtils.startsWithIgnoreCaseAndWs(sql, "INSERT", statementStartPos)) {
        if (StringUtils.indexOfIgnoreCase(statementStartPos, sql, "SELECT", "\"'`", "\"'`", StringUtils.SEARCH_MODE__MRK_COM_WS) != -1) {
            return false;
        }
        if (isOnDuplicateKeyUpdate) {
            int updateClausePos = StringUtils.indexOfIgnoreCase(locationOfOnDuplicateKeyUpdate, sql, " UPDATE ");
            if (updateClausePos != -1) {
                return StringUtils.indexOfIgnoreCase(updateClausePos, sql, "LAST_INSERT_ID", "\"'`", "\"'`", StringUtils.SEARCH_MODE__MRK_COM_WS) == -1;
            }
        }
        return true;
    }

    return StringUtils.startsWithIgnoreCaseAndWs(sql, "REPLACE", statementStartPos)
            && StringUtils.indexOfIgnoreCase(statementStartPos, sql, "SELECT", "\"'`", "\"'`", StringUtils.SEARCH_MODE__MRK_COM_WS) == -1;
}
```
可以看到 `rewriteBatchedStatements` 值为 true，必须是插入操作或者 REPLACE 操作，不能是 `INSERT ... SELECT` 或者 `INSERT ... ON DUPLICATE KEY UPDATE` 操作。

### 2. 多语句批处理

先介绍一下 multi-queries 模式，通常是指在一个请求中发送多个查询。常用于当你需要在一个请求中执行多个查询时，可以减少网络往返次数，从而提高性能。例如，你可以在一个请求中发送多个查询：
```sql
SELECT * FROM table1;
UPDATE table2 SET column1 = value1 WHERE column2 = value2;
DELETE FROM table3 WHERE column1 = value1;
```
在使用 multi-queries 时，你需要在每个查询之后添加分号（;），除了最后一个查询。

在 JDBC 连接 URL 中设置 `rewriteBatchedStatements` 参数并且使用的是 `PreparedStatement` 参数化语句时另一个执行路径是 `executePreparedBatchAsMultiStatement`：
```java
// 多语句批量执行
if (!this.batchHasPlainStatements && this.query.getBatchedArgs() != null && this.query.getBatchedArgs().size() > 3) {
    return executePreparedBatchAsMultiStatement(batchTimeout);
}
```
这个执行路径需要判断 `batchedArgs` 不为空，也就是必须为 `PreparedStatement` 设置参数；另一个是判断是设置参数实体的个数，只有超过3次，通俗讲就是至少执行 4 次 `addBatch` 才可以进入这个执行路径批处理。

## 3. 串行批处理

在 `executeBatchSerially` 路径中，JDBC 驱动会将批处理中的所有 SQL 语句逐一发送到数据库服务器执行。这意味着每个 SQL 语句都会单独发送，并且每个语句的执行结果都会单独返回。这种方式相对于其他批量操作方式，效率较低，因为它增加了网络传输的开销和等待时间‌。
