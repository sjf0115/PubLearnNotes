
日常开发中，当遇到数据的批量插入和更新等问题时经常会使用到 JDBC 的 `executeBatch()` 方法，来实现批量执行语句的功能。近期在项目开发过程中，遇到了一个奇怪的现象，使用 `executeBatch()` 方法进行批量插入时，发现数据库端日志收到的请求 SQL 仍是逐条收到的，并不是预期的批量收到请求批量执行。


## 1. 服务端日志

为了更好的验证执行 SQL 是否是批量执行，我们需要通过 MySQL 服务端日志进行判断。首先查看日志开关是否打开：
```sql
mysql> show variables like "general_log%";
+------------------+-------------------------------------+
| Variable_name    | Value                               |
+------------------+-------------------------------------+
| general_log      | OFF                                 |
| general_log_file | /usr/local/mysql/data/localhost.log |
+------------------+-------------------------------------+
2 rows in set (0.12 sec)
```
通过上面可以看到 `general_log` 通用日志处于 OFF 关闭状态，对应的文件实际也不存在：
```sql
(base) localhost:~ wy$ sudo cat /usr/local/mysql/data/localhost.log
cat: /usr/local/mysql/data/localhost.log: No such file or directory
```
需要通过 `SET GLOBAL general_log = 'ON'` 语句打开通用日志开关：
```sql
mysql> SET GLOBAL general_log = 'ON';
Query OK, 0 rows affected (0.04 sec)

mysql> show variables like "general_log%";
+------------------+-------------------------------------+
| Variable_name    | Value                               |
+------------------+-------------------------------------+
| general_log      | ON                                  |
| general_log_file | /usr/local/mysql/data/localhost.log |
+------------------+-------------------------------------+
2 rows in set (0.01 sec)
```

## 2. 批量执行

现在简单的还原实际执行：通过循环的方式批量执行 3 条 INSERT 语句：
```sql
public class JdbcBatchInsertExample {

    private static final String URL = "jdbc:mysql://localhost:3306/test?useSSL=false&characterEncoding=utf8";

    public static void main(String[] args) {
        Connection conn = null;
        try {
            // 获得数据库连接
            conn = DriverManager.getConnection(URL, "root", "root");
            // 查询 SQL
            String sql = "INSERT INTO tb_test(id, name) VALUES(?,?)";
            // 创建 PreparedStatement
            PreparedStatement ps = conn.prepareStatement(sql);
            for (int i = 1; i < 4 ;i++) {
                ps.setInt(1, i);
                ps.setString(2, i+"");
                ps.addBatch();
            }
            // 执行更新
            int[] result = ps.executeBatch();
        } catch (SQLException e) {
            e.printStackTrace();
        } finally {
            // 关闭连接
            try {
                if (conn != null) {
                    conn.close();
                }
            } catch (SQLException e) {
                e.printStackTrace();
            }
        }
    }
}
```
通过数据库服务端日志可以看到，三条 INSERT 是分别收到的，如下所示:
```sql
...
2024-12-30T09:52:20.786904Z	  522 Query	SHOW WARNINGS
2024-12-30T09:52:20.801171Z	  522 Query	SET NAMES utf8mb4
2024-12-30T09:52:20.802880Z	  522 Query	SET character_set_results = NULL
2024-12-30T09:52:20.803407Z	  522 Query	SET autocommit=1
2024-12-30T09:52:20.840384Z	  522 Query	SELECT @@session.transaction_read_only
2024-12-30T09:52:20.840860Z	  522 Query	INSERT INTO tb_test(id, name) VALUES(1,'1')
2024-12-30T09:52:20.861923Z	  522 Query	INSERT INTO tb_test(id, name) VALUES(2,'2')
2024-12-30T09:52:20.867722Z	  522 Query	INSERT INTO tb_test(id, name) VALUES(3,'3')
2024-12-30T09:52:20.890768Z	  522 Quit
```
这是什么原因呢？代码中明明是通过 `executeBatch()` 来设置批量执行的，但是没生效？带着这个问题查阅 MySQL 驱动源码(8.0.22)从源头查起。我们查阅 `PrepareStatement` 的 `executeBatch()` 实现逻辑：
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
> executeBatch 的详细逻辑请参阅[MySQL JDBC 实战: PreparedStatement rewriteBatchedStatements 实现原理](https://smartsi.blog.csdn.net/article/details/144839563)

从上面发现要实现批处理执行效果，前提条件是需要在 JDBC URL 中添加 `rewriteBatchedStatements` 参数(由于使用的是 `addBatch()` 方法，`batchHasPlainStatements` 为 `false`)：
```java
String URL = "jdbc:mysql://localhost:3306/test?rewriteBatchedStatements=true";
```
对于 INSERT 语句而言，如果要实现批量插入重写优化，SQL 语句中必须只能有一条 SQL，INSERT 语句中不能包含 SELECT 关键词，此外 `ON DUPLICATE KEY UPDATE` 语句后不能出现占位符，也不能使用 `LAST_INSERT_ID`。

> 对于非 INSERT 语句还有其他要求，具体参阅[MySQL JDBC 实战: PreparedStatement rewriteBatchedStatements 实现原理](https://smartsi.blog.csdn.net/article/details/144839563)

## 3. 批量处理重写优化

从上面分析知道要实现批处理重写优化效果，需要在 JDBC URL 中添加 `rewriteBatchedStatements` 参数：
```java
public class JdbcBatchInsertRewriteBatchExample {

    private static final String URL = "jdbc:mysql://localhost:3306/test?rewriteBatchedStatements=true&useSSL=false&characterEncoding=utf8";

    public static void main(String[] args) {
        Connection conn = null;
        try {
            // 获得数据库连接
            conn = DriverManager.getConnection(URL, "root", "root");
            // 查询 SQL
            String sql = "INSERT INTO tb_test(id, name) VALUES(?,?)";
            // 创建 PreparedStatement
            PreparedStatement ps = conn.prepareStatement(sql);
            for (int i = 1; i < 4 ;i++) {
                ps.setInt(1, i);
                ps.setString(2, i+"");
                ps.addBatch();
            }
            // 执行更新
            int[] result = ps.executeBatch();
        } catch (SQLException e) {
            e.printStackTrace();
        } finally {
            // 关闭连接
            try {
                if (conn != null) {
                    conn.close();
                }
            } catch (SQLException e) {
                e.printStackTrace();
            }
        }
    }
}
```
相对第一版本代码只在 JDBC URL 中添加了 `rewriteBatchedStatements` 参数。执行上述代码通过数据库服务端日志可以看到，三条 INSERT 合并为一条语句执行的，如下所示:
```java
...
2024-12-31T02:41:21.264470Z	  548 Query	SHOW WARNINGS
2024-12-31T02:41:21.275973Z	  548 Query	SET NAMES utf8mb4
2024-12-31T02:41:21.276325Z	  548 Query	SET character_set_results = NULL
2024-12-31T02:41:21.276804Z	  548 Query	SET autocommit=1
2024-12-31T02:41:21.318997Z	  548 Query	SELECT @@session.transaction_read_only
2024-12-31T02:41:21.320111Z	  548 Query	INSERT INTO tb_test(id, name) VALUES(1,'1'),(2,'2'),(3,'3')
2024-12-31T02:41:21.369262Z	  548 Quit
```
