### 在Spring Boot中实现驼峰与下划线JSON字段的自动映射：详细指南

#### 引言
在前后端分离的开发模式中，前端与后端常因编程语言的不同导致命名风格的差异。例如，Java使用**驼峰命名法**（如`userName`），而JavaScript更倾向于**下划线命名法**（如`user_name`）。若在接口交互时手动处理这种差异，会显著增加开发成本。  

Spring Boot默认集成了Jackson库处理JSON序列化，通过简单的配置即可实现**驼峰与下划线字段的自动映射**。本文将详细介绍如何通过`spring.jackson.property-naming-strategy`配置实现这一功能，并涵盖多模块项目、常见问题等场景。

---

### 一、快速入门：单模块项目配置

#### 1. 添加依赖  
确保项目中包含`spring-boot-starter-web`，它已默认引入Jackson：
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>
```

#### 2. 配置命名策略  
在`application.properties`中添加：
```properties
spring.jackson.property-naming-strategy=SNAKE_CASE
```
或在`application.yml`中：
```yaml
spring:
  jackson:
    property-naming-strategy: SNAKE_CASE
```

#### 3. 定义实体类  
实体类使用驼峰命名，**无需任何注解**：
```java
public class User {
    private String userName;  // 自动映射JSON中的"user_name"
    private Integer userAge;  // 自动映射JSON中的"user_age"
    // getters/setters
}
```

#### 4. 验证接口  
发送以下JSON请求：
```json
{
    "user_name": "John",
    "user_age": 25
}
```
Controller接收时，字段会自动填充到`userName`和`userAge`：
```java
@PostMapping("/user")
public String createUser(@RequestBody User user) {
    System.out.println(user.getUserName()); // 输出"John"
    return "Success";
}
```

---

### 二、多模块项目配置（以profile-dal和profile-web为例）

#### 1. 模块依赖关系  
- **profile-dal模块**：存放实体类`SchemaConfigItem`。
- **profile-web模块**：主启动模块，依赖`profile-dal`。

在`profile-web/pom.xml`中添加依赖：
```xml
<dependency>
    <groupId>com.example</groupId>
    <artifactId>profile-dal</artifactId>
    <version>1.0.0</version>
</dependency>
```

#### 2. 主模块配置  
在`profile-web`模块的`application.properties`中配置：
```properties
spring.jackson.property-naming-strategy=SNAKE_CASE
```

#### 3. 实体类定义  
`profile-dal`模块中的实体类：
```java
public class SchemaConfigItem {
    private String configName;  // 映射JSON中的"config_name"
    private Integer maxRetry;   // 映射JSON中的"max_retry"
    // getters/setters
}
```

#### 4. 接口测试  
Controller位于`profile-web`模块：
```java
@PostMapping("/config")
public String saveConfig(@RequestBody SchemaConfigItem config) {
    System.out.println(config.getConfigName()); // 输出"timeout_settings"
    return "Success";
}
```
发送JSON：
```json
{
    "config_name": "timeout_settings",
    "max_retry": 3
}
```

---

### 三、高级配置：自定义ObjectMapper

#### 1. 编程式配置  
若需更复杂的规则（如日期格式），可自定义`ObjectMapper`：
```java
@Configuration
public class JacksonConfig {
    @Bean
    public ObjectMapper objectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE);
        mapper.setDateFormat(new SimpleDateFormat("yyyy-MM-dd HH:mm:ss"));
        return mapper;
    }
}
```

#### 2. 注解覆盖全局策略  
使用`@JsonProperty`为特定字段指定名称，优先级高于全局配置：
```java
public class User {
    @JsonProperty("user_name")
    private String userName;  // 明确映射到"user_name"
}
```

---

### 四、常见问题及解决方案

#### 1. 字段未正确映射  
- **检查点**：  
  - 确保`getter/setter`方法命名正确（如`userName`对应`getUserName()`）。  
  - 确认未在实体类中使用`@JsonProperty`覆盖全局配置。

#### 2. 配置未生效  
- **检查点**：  
  - 主模块是否依赖了实体类所在的子模块。  
  - 确认`application.properties`位于`src/main/resources`目录。

#### 3. 日期格式处理  
在`application.properties`中添加：
```properties
spring.jackson.date-format=yyyy-MM-dd HH:mm:ss
spring.jackson.time-zone=GMT+8
```

---

### 五、与其他JSON库的对比（Jackson vs Gson）

| **特性**              | **Jackson**                              | **Gson**                          |
|-----------------------|------------------------------------------|-----------------------------------|
| **默认集成**          | Spring Boot 默认支持                     | 需手动引入并排除Jackson           |
| **配置方式**          | 通过`application.properties`简单配置     | 需自定义`Gson` Bean               |
| **命名策略**          | 支持`PropertyNamingStrategies`           | 支持`FieldNamingPolicy`           |
| **性能**              | 更高效，适合高并发场景                   | 足够应对大多数场景                |
| **注解支持**          | `@JsonIgnore`, `@JsonProperty`等         | `@SerializedName`, `@Expose`等    |

---

### 六、总结

通过`spring.jackson.property-naming-strategy=SNAKE_CASE`配置，Spring Boot项目可轻松实现驼峰与下划线字段的自动映射，显著减少手动转换代码。无论是单模块还是多模块项目，只需在主模块中全局配置一次即可生效。  

**最佳实践建议**：  
- 优先使用全局配置，减少重复注解。  
- 在需要特殊处理的字段上使用`@JsonProperty`。  
- 多模块项目中，确保实体类所在模块被正确依赖。
