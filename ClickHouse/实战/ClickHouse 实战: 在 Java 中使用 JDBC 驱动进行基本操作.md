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
```
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
```sql
String createSQL = """
  CREATE TABLE default.test (
      `entity_id` String,
      `value` String
  ) ENGINE = MergeTree
  PRIMARY KEY entity_id
  ORDER BY entity_id SETTINGS index_granularity = 8192
""";

try (Connection connection = new ClickHouseDataSource(url, properties).getConnection()) {
    Statement st = connection.createStatement();
    st.executeQuery(createSQL);
} catch (SQLException e) {
    e.printStackTrace();
}
```

### 3.2 插入数据

插入数据可以使用 PreparedStatement，以提高安全性并防止SQL注入。

#### 3.2.1 单条插入

```java
String insertSQL = "INSERT INTO test VALUES (?, ?, ?, ?)";

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

```java
try (PreparedStatement pstmt = conn.prepareStatement(insertSQL)) {
    for (int i = 0; i < 1000; i++) {
        pstmt.setLong(1, i);
        pstmt.setTimestamp(2, new Timestamp(System.currentTimeMillis()));
        pstmt.setString(3, "view");
        pstmt.setObject(4, Collections.emptyMap());
        pstmt.addBatch();
    }
    pstmt.executeBatch(); // 执行批量操作
}
```

---

### 3.3 查询数据

使用 Statement或 PreparedStatement执行SQL查询。这里以查询为例：
```java
String querySQL = """
    SELECT user_id, count(*) AS event_count
    FROM user_behavior
    WHERE event_time > ?
    GROUP BY user_id
    ORDER BY event_count DESC
    LIMIT 10
""";

try (PreparedStatement pstmt = conn.prepareStatement(querySQL)) {
    pstmt.setTimestamp(1, Timestamp.valueOf("2024-01-01 00:00:00"));

    ResultSet rs = pstmt.executeQuery();
    while (rs.next()) {
        long userId = rs.getLong("user_id");
        int count = rs.getInt("event_count");
        System.out.printf("User %d: %d events%n", userId, count);
    }
}
```

---

### 3.4 更新数据
```java
String updateSQL = """
    ALTER TABLE user_behavior
    UPDATE properties = {'source': 'mobile'}
    WHERE user_id = ?
""";

try (PreparedStatement pstmt = conn.prepareStatement(updateSQL)) {
    pstmt.setLong(1, 12345L);
    pstmt.executeUpdate();  // 返回受影响的行数
}
```

---

### 3.5 删除数据
```java
String deleteSQL = "ALTER TABLE user_behavior DELETE WHERE user_id = ?";

try (PreparedStatement pstmt = conn.prepareStatement(deleteSQL)) {
    pstmt.setLong(1, 12345L);
    int deletedRows = pstmt.executeUpdate();
    System.out.println("Deleted " + deletedRows + " rows");
}
```

---

## 高级技巧

### 1. 使用连接池
推荐使用HikariCP：
```java
HikariConfig config = new HikariConfig();
config.setJdbcUrl("jdbc:ch:https://localhost:8123/default");
config.setUsername("default");
config.setPassword("");

HikariDataSource ds = new HikariDataSource(config);
```

### 2. 处理数组类型
```java
// 插入数组
String insertArraySQL = "INSERT INTO table (tags) VALUES (?)";
pstmt.setArray(1, conn.createArrayOf("String", new String[]{"tag1", "tag2"}));

// 读取数组
String[] tags = (String[]) rs.getArray("tags").getArray();
```

---

## 注意事项

1. **事务支持**：ClickHouse主要面向分析场景，对事务支持有限
2. **批量写入**：建议批量提交（每次1000-10000行）
3. **时区处理**：建议统一使用UTC时区
4. **连接参数**：
   ```properties
   socket_timeout=300000
   connect_timeout=30000
   ```

---

## 总结

新版ClickHouse JDBC驱动（0.4.x+）通过优化实现了：
- 更好的类型映射
- 更高效的批量写入
- 增强的SSL/TLS支持
- 改进的连接池兼容性

官方文档参考：[ClickHouse JDBC Driver Documentation](https://github.com/ClickHouse/clickhouse-jdbc)

---

通过本文的示例，您应该已经掌握了使用Java操作ClickHouse的基本方法。实际应用中请根据具体场景调整参数和优化策略。
