## 1. DatabaseMetaData

```java
DatabaseMetaData meta = conn.getMetaData();
```
获取 DatabaseMetaData 对象，该对象包含数据库的全局元数据信息（如数据库名称、版本、支持特性等）和结构信息（如表、列、索引等）。

```java
// 获取数据库产品名称和版本
String productName = metaData.getDatabaseProductName(); // 如 "Hive"
String productVersion = metaData.getDatabaseProductVersion(); // 如 "3.1.2"

// 获取 JDBC 驱动信息
String driverName = metaData.getDriverName(); // 如 "Hive JDBC"
int driverVersion = metaData.getDriverVersion(); // 如 12345

// 检查数据库功能支持
boolean supportsTransactions = metaData.supportsTransactions(); // Hive 返回 false
```




# Spring Boot 访问Hive元数据的详细实现方案

## 1. 背景与方案选型

Hive元数据通常存储在独立的关系型数据库（如MySQL/PostgreSQL）中，Spring Boot可通过两种方式访问：

### 方案一：直接访问Hive元数据库
- **原理**：直连Hive的元数据库，执行SQL查询元数据表
- **优点**：查询效率高，可深度定制查询
- **缺点**：需了解Hive元数据表结构，耦合数据库实现

### 方案二：通过Hive JDBC API
- **原理**：使用Hive JDBC驱动执行`SHOW`、`DESCRIBE`等HQL命令
- **优点**：官方推荐方式，与Hive版本解耦
- **缺点**：依赖HiveServer2服务状态

**推荐方案**：采用Hive JDBC方式，更适合生产环境维护。以下详细讲解此方案实现。

---

## 2. 环境准备

### 2.1 依赖配置
```xml
<!-- pom.xml -->
<dependencies>
    <dependency>
        <groupId>org.apache.hive</groupId>
        <artifactId>hive-jdbc</artifactId>
        <version>3.1.2</version> <!-- 与Hive服务版本一致 -->
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-jdbc</artifactId>
    </dependency>
</dependencies>
```

### 2.2 数据源配置
```properties
# application.properties
spring.datasource.url=jdbc:hive2://hive-server:10000/default
spring.datasource.driver-class-name=org.apache.hive.jdbc.HiveDriver
spring.datasource.username=hive_user
spring.datasource.password=hive_pass
```

---

## 3. 核心实现代码

### 3.1 基础DAO层
```java
@Repository
public class HiveMetaDao {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    // 获取所有数据库
    public List<String> getDatabases() {
        return jdbcTemplate.query("SHOW DATABASES", (rs, rowNum) -> rs.getString(1));
    }

    // 获取指定数据库的表
    public List<String> getTables(String dbName) {
        return jdbcTemplate.query("SHOW TABLES IN " + dbName,
            (rs, rowNum) -> rs.getString(1));
    }

    // 获取表结构详情
    public List<ColumnMeta> getColumns(String dbName, String tableName) {
        return jdbcTemplate.query("DESCRIBE " + dbName + "." + tableName,
            (rs, rowNum) -> {
                ColumnMeta meta = new ColumnMeta();
                meta.setName(rs.getString(1));
                meta.setType(rs.getString(2));
                meta.setComment(rs.getString(3));
                return meta;
            });
    }
}
```

### 3.2 使用DatabaseMetaData接口（可选）
```java
public List<TableMeta> getTablesViaJdbcMeta(String dbName) throws SQLException {
    try (Connection conn = dataSource.getConnection()) {
        DatabaseMetaData meta = conn.getMetaData();
        ResultSet rs = meta.getTables(dbName, null, "%", new String[]{"TABLE"});

        List<TableMeta> tables = new ArrayList<>();
        while (rs.next()) {
            TableMeta table = new TableMeta();
            table.setName(rs.getString("TABLE_NAME"));
            table.setComment(rs.getString("REMARKS"));
            tables.add(table);
        }
        return tables;
    }
}
```

---

## 4. 元数据结构对象封装

```java
@Data
public class ColumnMeta {
    private String name;
    private String type;
    private String comment;
}

@Data
public class TableMeta {
    private String name;
    private String comment;
    private List<ColumnMeta> columns;
}
```

---

## 5. 服务层与控制层

### 5.1 服务实现
```java
@Service
public class HiveMetaService {

    @Autowired
    private HiveMetaDao metaDao;

    public TableMeta getTableDetail(String dbName, String tableName) {
        TableMeta meta = new TableMeta();
        meta.setName(tableName);
        meta.setColumns(metaDao.getColumns(dbName, tableName));
        return meta;
    }
}
```

### 5.2 REST接口
```java
@RestController
@RequestMapping("/hive-meta")
public class HiveMetaController {

    @Autowired
    private HiveMetaService metaService;

    @GetMapping("/tables/{dbName}")
    public List<String> getTables(@PathVariable String dbName) {
        return metaService.getTables(dbName);
    }

    @GetMapping("/table/{dbName}/{tableName}")
    public TableMeta getTableInfo(
        @PathVariable String dbName,
        @PathVariable String tableName
    ) {
        return metaService.getTableDetail(dbName, tableName);
    }
}
```

---

## 6. 高级功能实现

### 6.1 分页查询优化
```java
public List<String> getTablesPaged(String dbName, int page, int size) {
    String sql = "SHOW TABLES IN " + dbName + " LIMIT ? OFFSET ?";
    return jdbcTemplate.query(sql,
        ps -> {
            ps.setInt(1, size);
            ps.setInt(2, (page-1)*size);
        },
        (rs, rowNum) -> rs.getString(1));
}
```

### 6.2 缓存机制
```java
@Cacheable(value = "hiveMeta", key = "#dbName")
public List<String> getTablesWithCache(String dbName) {
    return metaDao.getTables(dbName);
}
```

---

## 7. 配置调优建议

### 7.1 连接池配置
```properties
# HikariCP配置
spring.datasource.hikari.connection-timeout=30000
spring.datasource.hikari.maximum-pool-size=20
```

### 7.2 Kerberos认证
```java
@Configuration
public class HiveConfig {

    @Value("${hive.principal}")
    private String principal;

    @Value("${hive.keytab}")
    private String keytabPath;

    @Bean
    public DataSource hiveDataSource() {
        HikariDataSource ds = new HikariDataSource();
        ds.setJdbcUrl(jdbcUrl);
        // Kerberos认证
        org.apache.hadoop.conf.Configuration conf = new org.apache.hadoop.conf.Configuration();
        UserGroupInformation.setConfiguration(conf);
        UserGroupInformation.loginUserFromKeytab(principal, keytabPath);
        return ds;
    }
}
```

---

## 8. 常见问题排查

### 8.1 连接超时
- 确认HiveServer2服务状态
- 检查防火墙规则
- 增加连接超时时间：
  ```properties
  spring.datasource.hikari.connection-timeout=60000
  ```

### 8.2 驱动类找不到
- 确认hive-jdbc版本是否正确
- 检查依赖冲突：
  ```bash
  mvn dependency:tree -Dincludes=org.apache.hive
  ```

### 8.3 权限不足
- 在HiveServer2配置中增加权限：
  ```xml
  <!-- hive-site.xml -->
  <property>
    <name>hive.security.authorization.enabled</name>
    <value>false</value>
  </property>
  ```

---

## 9. 方案对比总结

| 维度               | JDBC方案                  | 直连元数据库方案         |
|--------------------|--------------------------|-------------------------|
| 实现复杂度          | 低（标准API）             | 高（需解析表结构）       |
| 维护成本            | 低（版本兼容性好）        | 高（Hive升级需适配）     |
| 查询性能            | 中等                     | 高                      |
| 安全控制            | 依赖Hive权限体系         | 需单独管理数据库权限     |
| 扩展性              | 支持所有Hive元数据操作    | 可自定义复杂查询         |

---

## 10. 完整示例项目结构
```
hive-metadata-demo/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/
│   │   │       └── demo/
│   │   │           ├── config/      # 安全配置
│   │   │           ├── controller/  # REST接口
│   │   │           ├── model/       # 元数据模型
│   │   │           ├── dao/         # 数据访问层
│   │   │           └── Application.java
│   │   └── resources/
│   │       ├── application.properties
│   │       └── hive.keytab         # Kerberos认证文件
├── pom.xml
```

通过以上实现，可在Spring Boot应用中高效、安全地访问Hive元数据。建议根据实际业务需求选择合适的缓存策略和连接池配置，并在生产环境中启用Kerberos认证保障数据安全。
