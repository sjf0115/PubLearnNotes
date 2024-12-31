这一篇文章我们来介绍 Spark Streaming 如何将数据输出到 MySQL 中。主要介绍如何在 Spark Streaming 中创建可序列化的类来建立 MySQL 连接。另外我们可以直接建立连接，但对于大规模存储一般要用到连接池，所以也会介绍如何应用 Druid 连接池。

## 1. 添加依赖

如果输出数据到 MySQL 中需要添加 `mysql-connector-java` 依赖。此外为了更好的性能采用了 Druid 连接池，需要添加 `druid` 依赖：
```xml
<dependency>
    <groupId>mysql</groupId>
    <artifactId>mysql-connector-java</artifactId>
    <version>8.0.26</version> <!-- 请使用最新版本 -->
</dependency>

<dependency>
    <groupId>com.alibaba</groupId>
    <artifactId>druid</artifactId>
    <version>1.2.4</version> <!-- 请使用最新版本 -->
</dependency>
```

## 2. 在 Spark Streaming 中使用 Druid 连接池‌

在你的 Spark Streaming 应用程序中，你可以使用 foreachRDD 方法来处理每个 RDD，并在其中使用 Druid 连接池来执行数据库操作。你可以通过编程方式或者配置文件方式来配置 Druid 连接池。如下所示是通过编程方式建立一个数据库连接的 Druid 通用配置类：
```java
public class DruidConfig {
    public static DruidDataSource getDataSource() {
        DruidDataSource dataSource = new DruidDataSource();

        // 配置数据库连接参数
        dataSource.setUrl("jdbc:mysql://localhost:3306/test?useSSL=false&serverTimezone=UTC");
        dataSource.setUsername("root");
        dataSource.setPassword("root");

        // 配置连接池参数
        dataSource.setInitialSize(5); // 初始化连接数
        dataSource.setMinIdle(5);     // 最小空闲连接数
        dataSource.setMaxActive(20);  // 最大活跃连接数
        dataSource.setMaxWait(60000); // 获取连接的最大等待时间（毫秒）

        // 其他可选配置
        dataSource.setTimeBetweenEvictionRunsMillis(60000); // 连接池检查连接的间隔时间
        dataSource.setMinEvictableIdleTimeMillis(300000);  // 连接池中连接空闲的最小时间
        dataSource.setValidationQuery("SELECT 1");         // 验证连接是否有效的 SQL 语句
        dataSource.setTestWhileIdle(true);                 // 空闲时是否进行连接的验证

        return dataSource;
    }
}
```
## 3. MySQL 输出操作

在[Spark Streaming 与外部存储系统交互](https://smartsi.blog.csdn.net/article/details/144643428)文章中我们一步一步的介绍如何使用 `DStream.foreachRDD` 实现与外部存储系统交互。为了避免在 RDD 的每条记录进行外部存储操作时都需要建立和关闭连接，我们配合使用了 `foreachPartition` 来优化。按照 RDD 的不同分区来遍历 RDD，这样可以在分区遍历时通过连接池获取连接，从而实现每个分区只建立和关闭连接一次的目的，缩减建立连接的开销。然后在每个分区遍历每条记录实现与外部存储系统交互：
```java
dStream.foreachRDD(new VoidFunction<JavaRDD<String>>() {
    @Override
    public void call(JavaRDD<String> rdd) throws Exception {
        rdd.foreachPartition(new VoidFunction<Iterator<String>>() {
            @Override
            public void call(Iterator<String> iterator) throws Exception {
                // 1. 通过连接池获取连接
                DruidDataSource dataSource = DruidConfig.getDataSource();
                DruidPooledConnection connection = dataSource.getConnection();
                // 2. 通过连接与外部存储系统交互
                while (iterator.hasNext()) {
                    String record = iterator.next();
                    String sql = "xxx";
                    PreparedStatement stmt = null;
                    try {
                        PreparedStatement stmt = connection.prepareStatement(sql);
                        ...
                        stmt.executeUpdate();
                    } catch (Exception e) {
                        LOG.error("[ERROR] 与外部存储系统交互失败：" + e.getMessage());
                    } finally {
                        if (stmt != null) {
                            stmt.close();
                        }
                    }
                }
                // 3. 关闭连接
                if(connection != null) {
                    connection.close();
                }
            }
        });
    }
});
```

## 4. 示例

假设我们 MySQL 数据库中有一张 `tb_test` 表：
```sql
CREATE TABLE `tb_test` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `gmt_create` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `gmt_modified` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8
```

在这个示例中，我们创建了一个 Spark Streaming 应用程序，从本地主机的 9100 端口接收用户数据，并将每条记录插入到 MySQL 数据库 `tb_test` 表中。我们使用上述 `foreachRDD` + `foreachPartition` 的方法来处理每个 RDD，并在其中获取 Druid 连接池的连接，然后执行插入操作：
```java
dStream.foreachRDD(new VoidFunction<JavaRDD<String>>() {
    @Override
    public void call(JavaRDD<String> rdd) throws Exception {
        rdd.foreachPartition(new VoidFunction<Iterator<String>>() {
            @Override
            public void call(Iterator<String> iterator) throws Exception {
                // 1. 通过连接池获取连接
                DruidDataSource dataSource = DruidConfig.getDataSource();
                DruidPooledConnection connection = dataSource.getConnection();
                while (iterator.hasNext()) {
                    String record = iterator.next();
                    LOG.info("[INFO] 输入记录：" + record);
                    // 2. 遍历 RDD 通过连接与外部存储系统交互
                    String[] params = record.split(",");
                    String sql = "INSERT INTO tb_test (id, name) VALUES (?, ?)";
                    PreparedStatement stmt = null;
                    try {
                        stmt = connection.prepareStatement(sql);
                        // 设置参数并执行插入操作
                        stmt.setInt(1, Integer.parseInt(params[0]));
                        stmt.setString(2, UUID.randomUUID().toString().replace("-", ""));
                        stmt.executeUpdate();
                        LOG.info("[INFO] 通过连接与外部存储系统交互");
                    } catch (Exception e) {
                        LOG.error("[ERROR] 与外部存储系统交互失败：" + e.getMessage());
                    } finally {
                        if (stmt != null) {
                            stmt.close();
                        }
                    }
                }
                // 3. 关闭连接
                if(connection != null) {
                    connection.close();
                    LOG.info("[INFO] 关闭连接");
                }
                if (dataSource != null) {
                    dataSource.close();
                }
            }
        });
    }
});
```
在提交 MySQL 的操作的时候，并不是每条记录提交一次，而是采用了批量提交的形式，这样可以进一步提高 MySQL 的效率。首先在 DruidConfig 类中修改 JDBC URL，如下所示添加 `rewriteBatchedStatements` 参数开启批处理重写特性：
```java
dataSource.setUrl("jdbc:mysql://localhost:3306/test?rewriteBatchedStatements=true&useSSL=false&serverTimezone=UTC");
```
然后在应用程序中使用 `executeBatch` 批处理执行：
```java
try (PreparedStatement stmt = connection.prepareStatement(sql)) {
    while (iterator.hasNext()) {
        String record = iterator.next();
        LOG.info("[INFO] 输入记录：" + record);
        String[] params = record.split(",");
        stmt.setInt(1, Integer.parseInt(params[0]));
        stmt.setString(2, UUID.randomUUID().toString().replace("-", ""));
        stmt.addBatch();
    }
    // 执行批量操作
    stmt.executeBatch();
    LOG.info("[INFO] 通过连接与外部存储系统交互 批次执行");
} catch (Exception e) {
    LOG.error("[ERROR] 与外部存储系统交互失败：" + e.getMessage());
}
```
通过 MySQL 服务端日志可以看出批处理执行的效果：
```sql
2024-12-31T03:46:30.879538Z	  732 Query	SHOW WARNINGS
2024-12-31T03:46:30.879858Z	  732 Query	SET NAMES latin1
2024-12-31T03:46:30.880043Z	  732 Query	SET character_set_results = NULL
2024-12-31T03:46:30.880256Z	  732 Query	SET autocommit=1
2024-12-31T03:46:30.880558Z	  732 Query	SELECT 1
2024-12-31T03:46:30.881403Z	  732 Query	SELECT @@session.transaction_read_only
2024-12-31T03:46:30.882222Z	  732 Query	SELECT @@session.transaction_isolation
2024-12-31T03:46:30.885779Z	  732 Query	SELECT @@session.transaction_read_only
2024-12-31T03:46:30.886213Z	  732 Query	INSERT INTO tb_test (id, name) VALUES (1, '549bbef3bfcc4da18fa481d09151b025'),(2, '5c9fa50fdee84020804dca25da9f51af'),(3, '41ccc33ea13c40e48957c67ebe49b5af'),(4, '55f4c255b651476d9ce31205d4d15da9'),(5, '882df32846754f548f4d636172d8c0be'),(6, '00e67bf3b7e2485db417ae02ce62313e'),(7, 'ce670a4da9b248d586f823285c41339d'),(8, 'da8fcade10d44ae98d2cd69a182674e8'),(9, '3d4aba7170b24bf3b2f972f3a5e163ff'),(10, 'ec38b79f10bc4199967b4a232df075df')
```
