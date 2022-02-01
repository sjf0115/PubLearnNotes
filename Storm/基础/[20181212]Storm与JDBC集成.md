
### 2. ConnectionProvider

由不同连接池机制实现的接口 `org.apache.storm.jdbc.common.ConnectionProvider`:
```java
public interface ConnectionProvider extends Serializable {
    /**
     * method must be idempotent.
     */
    void prepare();

    /**
     *
     * @return a DB connection over which the queries can be executed.
     */
    Connection getConnection();

    /**
     * called once when the system is shutting down, should be idempotent.
     */
    void cleanup();
}
```
我们可以自己实现一个 `ConnectionProvider`，或者使用 Storm 提供的 `org.apache.storm.jdbc.common.HikariCPConnectionProvider` 实现，这是一个使用`HikariCP`的实现:
```java
Map hikariConfigMap = Maps.newHashMap();
hikariConfigMap.put("dataSourceClassName","com.mysql.jdbc.jdbc2.optional.MysqlDataSource");
hikariConfigMap.put("dataSource.url", "jdbc:mysql://localhost/test");
hikariConfigMap.put("dataSource.user","root");
hikariConfigMap.put("dataSource.password","password");
ConnectionProvider connectionProvider = new HikariCPConnectionProvider(hikariConfigMap);
```

### 3. JdbcMapper

使用JDBC在表中插入数据的主要API是 `org.apache.storm.jdbc.mapper.JdbcMapper` 接口：
```java
public interface JdbcMapper  extends Serializable {
    List<Column> getColumns(ITuple tuple);
}
```
`getColumns()` 方法定义了 storm tuple 如何映射为数据库中表示一行的 `List<Column>`。返回的列表的顺序很重要。给定查询中的占位符以返回列表相同的顺序进行解析。例如，如果用户提供的插入查询是 `insert into user(user_id, user_name, create_date) values (?,?, now())`, `getColumns` 方法返回列表中的第一个映射到第一个占位符，第二个映射到第二个占位符，依此类推。我们不会通过列名来尝试解析给定查询的占位符。不会对查询语法做任何假设，以允许这个连接器可以被一些非标准的SQL框架（如仅支持upsert的Pheonix）使用。

### 4. SimpleJdbcMapper

storm-jdbc 包含一个名为 `SimpleJdbcMapper` 的通用 `JdbcMapper` 实现，可以将 Storm tuple 映射到数据库行。`SimpleJdbcMapper` 假定 storm tuple 中的字段名称与你要写入的数据库表的列名相同。要使用 `SimpleJdbcMapper`，你只需要告诉它要写入的 `tableName` 并提供一个 `connectionProvider` 实例。

以下代码创建一个 `SimpleJdbcMapper` 实例：
- 允许映射器将 storm tuple 映射到 `test.user_details` 表一行的列的列表。
- 使用 HikariCP 配置与指定数据库配置建立连接池，自动找出你要写入表的列名和相应的数据类型。关于更多 HikariCP 配置请参考[HikariCP](https://github.com/brettwooldridge/HikariCP#configuration-knobs-baby)
```java
...
ConnectionProvider connectionProvider = new HikariCPConnectionProvider(hikariConfigMap);
String tableName = "user_details";
JdbcMapper simpleJdbcMapper = new SimpleJdbcMapper(tableName, connectionProvider);
```

### 5. JdbcInsertBolt

如果要使用 `JdbcInsertBolt`，你可以通过指定 `ConnectionProvider` 实例和将 storm tuple 转换为 DB 行的 `JdbcMapper` 实例来构造。另外，你要么使用 `withTableName` 方法提供表名，要么使用 `withInsertQuery` 提供插入查询。如果你指定了一个插入查询，那么你应该确保你的 `JdbcMapper` 实例将按照插入查询中的顺序返回一列列表。你可以选择指定查询超时秒参数，指定插入查询可以执行的最大秒数。`topology.message.timeout.secs` 默认设置为 -1 表示不设置任何查询超时。你应该将查询超时值设置小于等于 `topology.message.timeout.secs`。
```java
Map hikariConfigMap = Maps.newHashMap();
hikariConfigMap.put("dataSourceClassName","com.mysql.jdbc.jdbc2.optional.MysqlDataSource");
hikariConfigMap.put("dataSource.url", "jdbc:mysql://localhost/test");
hikariConfigMap.put("dataSource.user","root");
hikariConfigMap.put("dataSource.password","password");
ConnectionProvider connectionProvider = new HikariCPConnectionProvider(hikariConfigMap);

String tableName = "user_details";
JdbcMapper simpleJdbcMapper = new SimpleJdbcMapper(tableName, connectionProvider);

JdbcInsertBolt userPersistanceBolt = new JdbcInsertBolt(connectionProvider, simpleJdbcMapper)
        .withTableName("user")
        .withQueryTimeoutSecs(30);

JdbcInsertBolt userPersistanceBolt = new JdbcInsertBolt(connectionProvider, simpleJdbcMapper)
        .withInsertQuery("insert into user values (?,?)")
        .withQueryTimeoutSecs(30);
```









> Storm版本：1.2.2

原文：[Storm JDBC Integration](http://storm.apache.org/releases/1.2.2/storm-jdbc.html)
