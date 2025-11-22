ClickHouse 作为一款高性能的 OLAP 数据库，近年来在 Java 生态中的应用越来越广泛。本文将详细介绍如何使用**新版本ClickHouse JDBC驱动**进行连接和基本 CRUD 操作。

---

## 1. 添加依赖

首先，确保你的项目中包含了 ClickHouse 的 [JDBC](https://mvnrepository.com/artifact/com.clickhouse/clickhouse-jdbc) 驱动。如果你使用的是 Maven，可以在 pom.xml 文件中添加如下依赖：
```xml
<dependency>
  <groupId>com.clickhouse</groupId>
  <artifactId>clickhouse-jdbc</artifactId>
  <version>0.7.2</version>
</dependency>
```

---

### 2. 建立连接

在 Java 代码中，你需要注册驱动并建立到 ClickHouse 数据库的连接。示例代码如下：
```java
String url = "jdbc:ch:http://localhost:8123/default";
Properties properties = new Properties();
properties.setProperty("user", "default");
properties.setProperty("password", "");

try (Connection connection = new ClickHouseDataSource(url, properties).getConnection()) {
    String catalog = connection.getCatalog();
    System.out.println("Connected to ClickHouse " + catalog + " Successful !");
} catch (SQLException e) {
    e.printStackTrace();
}
```

---

## 3. 基础操作

### 3.1 创建表

在演示基本操作之前我们先创建如下 test 表:
```java
String createSQL = "CREATE TABLE default.test (\n" +
        "              `entity_id` String,\n" +
        "              `value` String\n" +
        "          ) ENGINE = MergeTree\n" +
        "          PRIMARY KEY entity_id\n" +
        "          ORDER BY entity_id SETTINGS index_granularity = 8192";

String url = "jdbc:ch:http://localhost:8123/default";
Properties properties = new Properties();
properties.setProperty("user", "default");
properties.setProperty("password", "");

try (Connection connection = new ClickHouseDataSource(url, properties).getConnection()) {
    Statement st = connection.createStatement();
    st.execute(createSQL);
} catch (SQLException e) {
    e.printStackTrace();
}
```

### 3.2 插入数据

插入数据可以使用 PreparedStatement，以提高安全性并防止SQL注入。

#### 3.2.1 单条插入

```java
String insertSQL = "INSERT INTO test VALUES (?, ?)";

String url = "jdbc:ch:http://localhost:8123/default";
Properties properties = new Properties();
properties.setProperty("user", "default");
properties.setProperty("password", "");

try (Connection connection = new ClickHouseDataSource(url, properties).getConnection();
     PreparedStatement pt = connection.prepareStatement(insertSQL)) {
    pt.setString(1, "a");
    pt.setString(2, "男");
    pt.execute();
} catch (SQLException e) {
    e.printStackTrace();
}
```

#### 3.2.2 批量插入

推荐批量插入来提升性能：
```java
String insertSQL = "INSERT INTO test VALUES (?, ?, ?, ?)";

String url = "jdbc:ch:http://localhost:8123/default";
Properties properties = new Properties();
properties.setProperty("user", "default");
properties.setProperty("password", "");

try (Connection connection = new ClickHouseDataSource(url, properties).getConnection();
     PreparedStatement pt = connection.prepareStatement(insertSQL)) {
    for (int i = 0; i < 10; i++) {
        pt.setString(1, "a"+i);
        pt.setString(2, "男");
        pt.addBatch();
    }
    pt.executeBatch(); // 执行批量操作

} catch (SQLException e) {
    e.printStackTrace();
}
```

---

### 3.3 查询数据

使用 Statement 或 PreparedStatement 执行 SQL 查询。这里以查询为例：
```java
String selectSQL = "SELECT value, count(*) AS num\n" +
                "FROM test\n" +
                "GROUP BY value";

String url = "jdbc:ch:http://localhost:8123/default";
Properties properties = new Properties();
properties.setProperty("user", "default");
properties.setProperty("password", "");

try (Connection connection = new ClickHouseDataSource(url, properties).getConnection();
     PreparedStatement pt = connection.prepareStatement(selectSQL)) {
    ResultSet rs = pt.executeQuery();
    while (rs.next()) {
        String value = rs.getString("value");
        int num = rs.getInt("num");
        System.out.printf("性别 %s: %d 名%n", value, num);
    }
} catch (SQLException e) {
    e.printStackTrace();
}
```
输出结果如下所示:
```
性别 女: 1 名
性别 男: 11 名
```

---

### 3.4 更新数据

可以执行 executeUpdate 方法来更新数据:
```java
String updateSQL = "UPDATE test SET value = ? WHERE entity_id = ?";

String url = "jdbc:ch:http://localhost:8123/default";
Properties properties = new Properties();
properties.setProperty("user", "default");
properties.setProperty("password", "");

try (Connection connection = new ClickHouseDataSource(url, properties).getConnection();
     PreparedStatement pt = connection.prepareStatement(updateSQL)) {
    pt.setString(1, "女");
    pt.setString(2, "a0");
    pt.executeUpdate();
} catch (SQLException e) {
    e.printStackTrace();
}
```

---

### 3.5 删除数据

删除操作与更新类似，只需要更改 SQL 语句即可:
```java
String deleteSQL = "DELETE FROM test WHERE entity_id = ?";

String url = "jdbc:ch:http://localhost:8123/default";
Properties properties = new Properties();
properties.setProperty("user", "default");
properties.setProperty("password", "");

try (Connection connection = new ClickHouseDataSource(url, properties).getConnection();
     PreparedStatement pt = connection.prepareStatement(deleteSQL)) {
    pt.setString(1, "a9");
    pt.executeUpdate();
} catch (SQLException e) {
    e.printStackTrace();
}
```

---

## 4. 高级技巧-使用连接池

推荐使用 HikariCP 连接池。需要在 pom 中添加如下依赖:
```
<!-- HikariCP 依赖 -->
<dependency>
    <groupId>com.zaxxer</groupId>
    <artifactId>HikariCP</artifactId>
    <version>4.0.3</version>
</dependency>
```
连接池配置如下所示:
```java
public class ClickHousePool {
    private static final String JDBC_URL = "jdbc:ch://localhost:8123/default";
    private static final String USER = "default";
    private static final String PASSWORD = "";
    private static HikariDataSource dataSource;

    static {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(JDBC_URL);
        config.setUsername(USER);
        config.setPassword(PASSWORD);

        // 核心参数优化
        config.setMaximumPoolSize(20);          // 根据CPU核心数调整
        config.setMinimumIdle(5);               // 最小空闲连接
        config.setConnectionTimeout(30000);      // 30秒连接超时
        config.setIdleTimeout(30000);          // 30秒空闲超时
        config.setMaxLifetime(60000);         // 1分钟连接生命周期
        config.setValidationTimeout(5000);      // 5秒验证超时
        config.setConnectionTestQuery("SELECT 1"); // 保活查询
        config.setPoolName("HikariPool");

        // ClickHouse专用参数
        config.addDataSourceProperty("socket_timeout", "600000"); // 10分钟Socket超时
        config.addDataSourceProperty("compress", "true");         // 启用压缩

        dataSource = new HikariDataSource(config);
    }

    public static Connection getConnection() throws SQLException {
        return dataSource.getConnection();
    }
}
```
下面通过连接池5个线程并发插入数据，每批数据10000条，共10批：
```
public class BulkInsert {
    private final static Integer INSERT_BATCH_SIZE = 10000;
    private final static Integer INSERT_BATCH_NUM = 10;

    /**
     * 批量插入
     * @param conn
     * @throws SQLException
     */
    public static void batchInsert(Connection conn) throws SQLException {
        String insertSQL = "INSERT INTO test VALUES (?, ?, ?, ?)";
        PreparedStatement pt = conn.prepareStatement(insertSQL);

        String[] genders = {"男", "女"};
        Random random = new Random();
        for (int i = 0; i < INSERT_BATCH_NUM; i++) {
            long insertStartTime = System.currentTimeMillis();
            for (int j = 0; j < INSERT_BATCH_SIZE; j++) {
                int id = i * 1000000 + j;
                pt.setString(1, "user_" + id);
                pt.setString(2, genders[random.nextInt(genders.length)]);
                pt.addBatch();
            }
            pt.executeBatch();

            System.out.printf("[%d] insert batch [%d/%d] success, cost %d ms\n",
                    Thread.currentThread().getId(), i + 1, INSERT_BATCH_NUM, System.currentTimeMillis() - insertStartTime);
        }
    }

    /**
     * 条数
     * @param conn
     * @throws Exception
     */
    public static void count(Connection conn) throws Exception {
        ResultSet resultSet = conn.createStatement().executeQuery("SELECT count(*) as cnt FROM test");
        if (resultSet.next()) {
            System.out.printf("table `test` has %d rows\n", resultSet.getInt("cnt"));
        }
    }

    public static void main(String[] args) {
        try(Connection connection = ClickHousePool.getConnection()) {
            // 并发插入数据
            int concurrentNum = 5;
            //开启5个线程
            CountDownLatch countDownLatch = new CountDownLatch(concurrentNum);
            ExecutorService executorService = Executors.newFixedThreadPool(concurrentNum);
            for (int i = 0; i < concurrentNum; i++) {
                executorService.submit(() -> {
                    System.out.printf("[%d] Thread start inserting\n", Thread.currentThread().getId());
                    try {
                        //插入数据
                        batchInsert(connection);
                    } catch (Exception e) {
                        e.printStackTrace();
                    } finally {
                        System.out.printf("[%d] Thread stop inserting\n", Thread.currentThread().getId());
                        countDownLatch.countDown();
                    }
                });
            }
            // 等待每个线程完成数据插入
            countDownLatch.await();
            // 插入后查看结果
            count(connection);
        } catch (SQLException e) {
            e.printStackTrace();
        } catch (InterruptedException e) {
            e.printStackTrace();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```
