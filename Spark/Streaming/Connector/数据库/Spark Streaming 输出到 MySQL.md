这一篇文章我们来介绍 Spark Streaming 如何将数据输出到 MySQL 中。MySQL 非常常见，我们简单地概述一下，主要介绍如何在 Spark Streaming 中创建可序列化的类来建立 MySQL 连接。另外我们可以直接建立连接，但对于大规模存储一般要用到连接池，所以也会介绍如何应用 Druid 连接池。

MySQL作为一个关系型数据库管理系统，在各个应用场景是非常常见的，其类似于一张一张的表格，表头需要提前定好，并且每行记录有一个唯一标识的字段，即主键，然后将数据按照表头一条一条地插入；而一个数据库中往往会有多个表格，表格间会有相互依赖关系，存在外键的依赖。

在 Spark Streaming 操作 MySQL 时，与以往使用数据库不同的是，数据量会非常庞大，往往需要考虑同一张表格根据时间进行分表的情况，这样更加便于维护数据。比如对于网上大规模用户评论进行词频统计，然后存储在MySQL数据库中。

因为这是一个长期的过程，如果我们将数据不断更新插入在同一张表格中，这个表格会非常巨大，并且一旦出错很难恢复，而且不容易删除过时数据，所以我们可以按照天的量级建立数据表格 word_freq_yyyy_MM_dd，其中yyyy_MM_dd表示年_月_日。

## 1. 添加依赖

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

假设我们 MySQL 数据库中有一张 `tb_user` 表：
```sql
CREATE TABLE `tb_user` (
  `id` bigint(20) NOT NULL COMMENT '主键ID',
  `name` varchar(30) DEFAULT NULL COMMENT '姓名',
  `age` int(11) DEFAULT NULL COMMENT '年龄',
  `email` varchar(50) DEFAULT NULL COMMENT '邮箱',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1
```

在这个示例中，我们创建了一个 Spark Streaming 应用程序，从本地主机的 9100 端口接收用户数据，并将每条记录插入到 MySQL 数据库 `tb_user` 表中。我们使用上述 `foreachRDD` + `foreachPartition` 的方法来处理每个 RDD，并在其中获取 Druid 连接池的连接，然后执行插入操作：
```java
usersStream.foreachRDD(new VoidFunction<JavaRDD<String>>() {
@Override
public void call(JavaRDD<String> rdd) throws Exception {
    rdd.foreachPartition(new VoidFunction<Iterator<String>>() {
        @Override
        public void call(Iterator<String> iterator) throws Exception {
            // 1. 通过连接池获取连接
            DruidDataSource dataSource = DruidConfig.getDataSource();
            DruidPooledConnection connection = dataSource.getConnection();
            // 2. 遍历 RDD 通过连接与外部存储系统交互
            String sql = "INSERT INTO tb_user (id, name, age, email) VALUES (?, ?, ?, ?)";
            try (PreparedStatement stmt = connection.prepareStatement(sql)) {
                while (iterator.hasNext()) {
                    String record = iterator.next();
                    LOG.info("[INFO] 输入记录：" + record);
                    String[] params = record.split(",");
                    stmt.setInt(1, Integer.parseInt(params[0]));
                    stmt.setString(2, params[1]);
                    stmt.setInt(3, Integer.parseInt(params[2]));
                    stmt.setString(4, params[3]);
                    stmt.addBatch(); // 添加到批处理
                }
                // 执行批量操作
                stmt.executeBatch();
                LOG.info("[INFO] 通过连接与外部存储系统交互");
            } catch (Exception e) {
                LOG.error("[ERROR] 与外部存储系统交互失败：" + e.getMessage());
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
在提交 MySQL 的操作的时候，并不是每条记录提交一次，而是采用了批量提交的形式，这样可以进一步提高 MySQL 的效率。
