

## 1. addBatch(String sql)

```java
// Statement.addBatch
void addBatch(String sql) throws SQLException;
```
> 这个方法不能在 PreparedStatement 或 CallableStatement 上调用。





## 2. addBatch()

向 PreparedStatement 对象的命令批添加一组参数。
```java
// PreparedStatement.addBatch
void addBatch() throws SQLException;
```
将给定的 SQL 命令添加到 Statement 对象的当前命令列表中。可以通过调用 executeBatch 方法批量执行此列表中的命令。
