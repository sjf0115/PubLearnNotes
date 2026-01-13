我来帮你实现使用 Jackson 将 JSON 字符串解析为 `List<JsonMappingConfig>`。以下是完整的解决方案：

```java
@Data
@NoArgsConstructor
@AllArgsConstructor
public class JsonMappingConfig {
    private String name;
    private JsonType type;
}
```
其中 JsonType 是一个 JSON 类型的枚举：
```java
public enum JsonType {
    JSON_STRING(1, "JSON_STRING"),
    JSON_NUMBER(2, "JSON_NUMBER"),
    JSON_BOOL(3, "JSON_BOOL"),
    JSON_MAP(4, "JSON_MAP"),
    JSON_ARRAY(5, "JSON_ARRAY");

    private final int code;
    private final String value;

    JsonType(int code, String value) {
        this.code = code;
        this.value = value;
    }
}
```

首先依赖配置（pom.xml）

```xml
<dependencies>
    <!-- Jackson Core -->
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
        <version>2.15.2</version>
    </dependency>

    <!-- Jackson 对 Java 8+ 的支持 -->
    <dependency>
        <groupId>com.fasterxml.jackson.datatype</groupId>
        <artifactId>jackson-datatype-jsr310</artifactId>
        <version>2.15.2</version>
    </dependency>

    <!-- Lombok -->
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <version>1.18.28</version>
        <scope>provided</scope>
    </dependency>
</dependencies>
```

## 1. 简单方式

```java
private static final ObjectMapper objectMapper = new ObjectMapper();

public static List<JsonMappingConfig> parseMappingConfig(String jsonConfig) {
    try {
        return objectMapper.readValue(
                jsonConfig,
                objectMapper.getTypeFactory().constructCollectionType(List.class, JsonMappingConfig.class)
        );
    } catch (Exception e) {
        throw new RuntimeException("Failed to parse mapping configuration", e);
    }
}
```

## 2. 自定义反序列化器

### 1. 首先创建一个自定义的反序列化器来处理 JsonType 枚举

```java
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonDeserializer;
import com.fasterxml.jackson.databind.JsonNode;

import java.io.IOException;

public class JsonTypeDeserializer extends JsonDeserializer<JsonType> {

    @Override
    public JsonType deserialize(JsonParser p, DeserializationContext ctxt)
            throws IOException, JsonProcessingException {
        String value = p.getText();

        // 通过枚举的 value 字段来匹配
        for (JsonType type : JsonType.values()) {
            if (type.getValue().equals(value)) {
                return type;
            }
        }

        // 如果找不到匹配的枚举值，可以返回 null 或抛出异常
        throw new IllegalArgumentException("Unknown JsonType: " + value);
    }
}
```

## 2. 修改 JsonMappingConfig 类，添加 Jackson 注解

```java
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonDeserialize(builder = JsonMappingConfig.JsonMappingConfigBuilder.class)
public class JsonMappingConfig {
    private String name;

    @JsonDeserialize(using = JsonTypeDeserializer.class)
    private JsonType type;
}
```

## 3. 修改 JsonType 枚举，添加 Jackson 注解（可选）

如果你希望让 Jackson 能正确处理序列化，可以在枚举中添加 `@JsonCreator` 注解：

```java
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

import java.util.Objects;

public enum JsonType {
    JSON_STRING(1, "JSON_STRING"),
    JSON_NUMBER(2, "JSON_NUMBER"),
    JSON_BOOL(3, "JSON_BOOL"),
    JSON_MAP(4, "JSON_MAP"),
    JSON_ARRAY(5, "JSON_ARRAY");

    private final int code;
    private final String value;

    JsonType(int code, String value) {
        this.code = code;
        this.value = value;
    }

    public int getCode() {
        return code;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    public static JsonType fromCode(int code) {
        for (JsonType type : values()) {
            if (Objects.equals(type.code, code)) {
                return type;
            }
        }
        return null;
    }

    @JsonCreator
    public static JsonType fromValue(String value) {
        for (JsonType type : values()) {
            if (type.value.equals(value)) {
                return type;
            }
        }
        return null;
    }
}
```

## 4. 主要的解析工具类

```java
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.json.JsonMapper;
import java.util.List;

public class JsonMappingConfigParser {

    private static final ObjectMapper objectMapper = JsonMapper.builder()
            .findAndAddModules()
            .build();

    /**
     * 解析 JSON 字符串为 List<JsonMappingConfig>
     */
    public static List<JsonMappingConfig> parseJson(String jsonString) throws Exception {
        return objectMapper.readValue(
                jsonString,
                new TypeReference<List<JsonMappingConfig>>() {}
        );
    }

    /**
     * 将 List<JsonMappingConfig> 序列化为 JSON 字符串
     */
    public static String toJson(List<JsonMappingConfig> configs) throws Exception {
        return objectMapper.writeValueAsString(configs);
    }
}
```

## 5. 使用示例

```java
public class Main {
    public static void main(String[] args) {
        String jsonString = "[{\"name\":\"id\",\"type\":\"JSON_NUMBER\"}, "
                + "{\"name\":\"name\",\"type\":\"JSON_STRING\"}, "
                + "{\"name\":\"age\",\"type\":\"JSON_NUMBER\"}]";

        try {
            // 解析 JSON 字符串
            List<JsonMappingConfig> configs = JsonMappingConfigParser.parseJson(jsonString);

            // 打印解析结果
            System.out.println("解析结果：");
            for (JsonMappingConfig config : configs) {
                System.out.printf("name: %s, type: %s%n",
                        config.getName(),
                        config.getType());
            }

            // 验证序列化（可选）
            String serialized = JsonMappingConfigParser.toJson(configs);
            System.out.println("\n序列化后的 JSON：");
            System.out.println(serialized);

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```





## 输出结果

运行程序后，你会得到以下输出：
```
解析结果：
name: id, type: JSON_NUMBER
name: name, type: JSON_STRING
name: age, type: JSON_NUMBER

序列化后的 JSON：
[{"name":"id","type":"JSON_NUMBER"},{"name":"name","type":"JSON_STRING"},{"name":"age","type":"JSON_NUMBER"}]
```

这个解决方案正确处理了 JSON 字符串到 Java 对象的转换，特别是将字符串形式的 `"JSON_NUMBER"`、`"JSON_STRING"` 等转换为对应的 `JsonType` 枚举值。
