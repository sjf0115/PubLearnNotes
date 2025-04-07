在 MyBatis 中实现 Java 对象中的 `List` 属性与数据库表 JSON 数组的映射，可以通过 **自定义 TypeHandler** 或 **MyBatis Plus 的自动类型转换** 实现。以下是完整解决方案：

---

### 1. 原生 MyBatis 方案（自定义 TypeHandler）

#### 1. 添加 JSON 序列化依赖（如 Jackson）

```xml
<!-- pom.xml -->
<dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
    <version>2.15.2</version>
</dependency>
```

#### 2. 定义 Java 实体类

```java
public class DataSourceSchema {
    private List<SchemaConfigItem> configTemplate; // 需要映射的 List 属性
    // 其他字段...
}

public class SchemaConfigItem {
    @JsonProperty("show_name") // JSON字段名与Java属性名不一致时需指定
    private String showName;
    private String key;
    private String value;
    private int required;
    private int encrypt;
    private String tip;
    // Getter/Setter省略...
}
```

#### 3. 创建自定义 TypeHandler

```java
public class ListTypeHandler<T> extends BaseTypeHandler<List<T>> {
    private final Gson gson = new Gson();
    private final Type type;

    /**
     * 构造函数：通过泛型类型初始化
     * @param clazz
     */
    public ListTypeHandler(Class<T> clazz) {
        this.type = TypeToken.getParameterized(List.class, clazz).getType();
    }

    /**
     * 序列化：Java对象 → JSON字符串（写入数据库）
     * @param ps
     * @param i
     * @param parameter
     * @param jdbcType
     * @throws SQLException
     */
    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, List<T> parameter, JdbcType jdbcType) throws SQLException {
        String json = gson.toJson(parameter);
        ps.setString(i, json);
    }

    /**
     * 反序列化：JSON字符串 → Java对象（从数据库读取）
     * @param rs
     * @param columnName
     * @return
     * @throws SQLException
     */
    @Override
    public List<T> getNullableResult(ResultSet rs, String columnName) throws SQLException {
        String json = rs.getString(columnName);
        return parseJson(json);
    }

    @Override
    public List<T> getNullableResult(ResultSet rs, int columnIndex) throws SQLException {
        String json = rs.getString(columnIndex);
        return parseJson(json);
    }

    @Override
    public List<T> getNullableResult(CallableStatement cs, int columnIndex) throws SQLException {
        String json = cs.getString(columnIndex);
        return parseJson(json);
    }

    /**
     * 解析Json
     * @param json
     * @return
     */
    private List<T> parseJson(String json) {
        if (StringUtils.isBlank(json)) {
            return Collections.emptyList();
        }
        return gson.fromJson(json, type);
    }
}
```

#### 4. 注册 TypeHandler

在 `mybatis-config.xml` 中全局注册：
```xml
<typeHandlers>
  <typeHandler
    handler="com.example.handler.ListTypeHandler"
    javaType="java.util.List<com.example.model.SchemaConfigItem>"
    jdbcType="VARCHAR"/>
</typeHandlers>
```
或者

```
mybatis.type-handlers-package=com.data.profile.handler
```

#### 5. 配置 Mapper XML

```xml
<resultMap id="DataSourceSchemaMap" type="DataSourceSchema">
  <result column="config_template" property="configTemplate" typeHandler="com.data.profile.common.handler.ListTypeHandler"/>
</resultMap>

<select id="selectById" resultMap="DataSourceSchemaMap">
  SELECT * FROM profile_meta_datasource_schema WHERE id = #{id}
</select>
```

---

### 2. MyBatis Plus 简化方案（推荐）

#### 1. 添加 MyBatis Plus 依赖

```xml
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-boot-starter</artifactId>
    <version>3.5.3.1</version>
</dependency>
```

#### 2. 在实体类中使用注解

```java
public class DataSourceSchema {
    @TableField(typeHandler = JacksonTypeHandler.class)
    private List<SchemaConfigItem> configTemplate;
}
```

#### 3. 配置全局类型处理器（Spring Boot）

```java
@Configuration
public class MybatisConfig {

    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
        // 添加JSON类型处理器
        interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL));
        return interceptor;
    }

    @Bean
    public ConfigurationCustomizer configurationCustomizer() {
        return configuration -> {
            // 注册全局类型处理器
            configuration.setDefaultEnumTypeHandler(JacksonTypeHandler.class);
            configuration.setDefaultScriptingLanguage(MybatisXMLLanguageDriver.class);
        };
    }
}
```

---

### 三、关键注意事项

1. **字段名映射**：
   - 若 JSON 字段名与 Java 属性名不一致（如 `show_name` → `showName`），需通过 `@JsonProperty` 或配置 `ObjectMapper` 的命名策略：
     ```java
     objectMapper.setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE);
     ```

2. **枚举类型处理**：
   - 如果 `List` 中包含枚举类型，需在枚举类上添加 `@JsonFormat(shape = JsonFormat.Shape.OBJECT)` 或自定义序列化逻辑。

3. **空值处理**：
   - 数据库字段为 `NULL` 时，`List` 属性会返回 `null`，建议在实体类中初始化空集合：
     ```java
     private List<SchemaConfigItem> configTemplate = new ArrayList<>();
     ```

4. **性能优化**：
   - 将 `ObjectMapper` 声明为静态变量避免重复创建。
   - 使用 `TypeReference` 处理复杂泛型：
     ```java
     List<SchemaConfigItem> list = objectMapper.readValue(json, new TypeReference<List<SchemaConfigItem>>() {});
     ```

---

### 四、扩展场景

#### 1. 嵌套对象处理

若 `SchemaConfigItem` 包含嵌套对象：
```java
public class SchemaConfigItem {
    private SubConfig subConfig;
}

// JSON示例
{"key": "host", "subConfig": {"name": "test"}}
```

需确保 `SubConfig` 类有无参构造器和 Getter/Setter。

#### 2. 动态 JSON 结构
如果 JSON 结构不固定，可直接映射为 `List<Map<String, Object>>`：
```java
@TableField(typeHandler = JacksonTypeHandler.class)
private List<Map<String, Object>> dynamicConfig;
```

---

通过以上方案，无论是原生 MyBatis 还是 MyBatis Plus，均可高效实现 Java 对象 `List` 属性与数据库 JSON 数组字段的自动映射。
