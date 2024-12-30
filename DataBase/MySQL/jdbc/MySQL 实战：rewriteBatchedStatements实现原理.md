https://www.jianshu.com/p/7eb8eec78b9a















```java
protected long[] executeBatchInternal() throws SQLException {
    synchronized (checkClosed().getConnectionMutex()) {
        ...
        // 是否设置 rewriteBatchedStatements 参数
        if (!this.batchHasPlainStatements && this.rewriteBatchedStatements.getValue()) {
            // 批量插入
            if (((PreparedQuery<?>) this.query).getParseInfo().canRewriteAsMultiValueInsertAtSqlLevel()) {
                return executeBatchedInserts(batchTimeout);
            }
            // 批量更新
            if (!this.batchHasPlainStatements && this.query.getBatchedArgs() != null && this.query.getBatchedArgs().size() > 3) {
                return executePreparedBatchAsMultiStatement(batchTimeout);
            }
        }
        // 单独执行
        return executeBatchSerially(batchTimeout);
        ...
    }
}
```
批量执行模式取决于两个条件：
- batchHasPlainStatements
- rewriteBatchedStatements

```java
PreparedStatement ps = conn.prepareStatement(sql);
for (int i = 1; i <= n;i++) {
    ...
    ps.addBatch();
}
ps.executeBatch();
```


```java
PreparedStatement ps = conn.prepareStatement();
for (int i = 1; i <= n;i++) {
    ...
    ps.addBatch(sql);
}
ps.executeBatch();
```


`batchHasPlainStatements` 表示是否使用 `Statement.addBatch(String sql)` 模式显示添加 SQL 语句，而不是使用 ``。如果使用的是 `addBatch(String sql)`，即不能使用 `multi-value` 或者 `multi-queries` 批量重写模式：
```java
/**
 * Does the batch (if any) contain "plain" statements added by
 * Statement.addBatch(String)?
 *
 * If so, we can't re-write it to use multi-value or multi-queries.
 */
protected boolean batchHasPlainStatements = false;
```

前提条件是设置了 `rewriteBatchedStatements` 参数：
```sql
jdbc:mysql://localhost:3306/test?rewriteBatchedStatements=true
```

### 2.

### 1. 批量插入 multi-value

先介绍一下 multi-value 模式，通常指的是一个查询可以返回多个值。在 MySQL 中，你可以使用 INSERT 语句同时插入多行数据：
```sql
INSERT INTO tb_test(id, name) VALUES(1,'1'),(2,'2'),(3,'3')
```



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
```

没有使用批量模式：
```sql
2024-12-30T02:51:57.363670Z       492 Query     INSERT INTO tb_test(id, name) VALUES(1,'1')
2024-12-30T02:51:57.378809Z       492 Query     INSERT INTO tb_test(id, name) VALUES(2,'2')
2024-12-30T02:51:57.384909Z       492 Query     INSERT INTO tb_test(id, name) VALUES(3,'3')
```
使用批量模式：
```sql
2024-12-30T02:54:32.865632Z       493 Query     INSERT INTO tb_test(id, name) VALUES(1,'1'),(2,'2'),(3,'3')
```

### 2. 批量更新 multi-queries

先介绍一下 multi-queries 模式，通常是指在一个请求中发送多个查询。常用于当你需要在一个请求中执行多个查询时，可以减少网络往返次数，从而提高性能。例如，你可以在一个请求中发送多个查询：
```sql
SELECT * FROM table1;
UPDATE table2 SET column1 = value1 WHERE column2 = value2;
DELETE FROM table3 WHERE column1 = value1;
```
在使用 multi-queries 时，你需要在每个查询之后添加分号（;），除了最后一个查询。另外，为了防止 SQL 注入，默认情况下，MySQL 的 multi-queries 功能是禁用的。




executePreparedBatchAsMultiStatement方法中有几个参数，先简单介绍一下就知道具体的执行逻辑了，numBatchedArgs 就是getBatchedArgs().size()，numValuesPerBatch是根据maxAllowedPacket(单次允许提交的最大的数据包的大小)、originalSql的长度和numBatchedArgs的大小共同计算出的单次提交最大数量，然后结合下面的代码就可以看出批量提交的逻辑





第二个是判断batchedArgs不为空，也就是必须为PreparedStatement设置参数，第三个判断是设置参数实体的个数，只有超过4次，通俗讲就是至少执行4次addBatch才可以进行批量操作；




没有使用批量模式：
```sql
2024-12-30T03:55:52.917277Z	  507 Query	update tb_test set name = '1_1' where id = 1
2024-12-30T03:55:52.918694Z	  507 Query	update tb_test set name = '2_2' where id = 2
2024-12-30T03:55:52.919027Z	  507 Query	update tb_test set name = '3_3' where id = 3
2024-12-30T03:55:52.919288Z	  507 Query	update tb_test set name = '4_4' where id = 4
2024-12-30T03:55:52.919533Z	  507 Query	update tb_test set name = '5_5' where id = 5
```
使用批量模式：
```sql
2024-12-30T03:41:45.897247Z	  505 Query	update tb_test set name = '1_1' where id = 1;
2024-12-30T03:41:45.897511Z	  505 Query	update tb_test set name = '2_2' where id = 2;
2024-12-30T03:41:45.897654Z	  505 Query	update tb_test set name = '3_3' where id = 3;
2024-12-30T03:41:45.897761Z	  505 Query	update tb_test set name = '4_4' where id = 4
```

## 3. 单独执行
