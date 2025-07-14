## 1. 问题

```java
Exception in thread "main" org.apache.flink.table.api.TableException: Could not instantiate the executor. Make sure a planner module is on the classpath
	at org.apache.flink.table.api.bridge.java.internal.StreamTableEnvironmentImpl.lookupExecutor(StreamTableEnvironmentImpl.java:185)
	at org.apache.flink.table.api.bridge.java.internal.StreamTableEnvironmentImpl.create(StreamTableEnvironmentImpl.java:148)
	at org.apache.flink.table.api.bridge.java.StreamTableEnvironment.create(StreamTableEnvironment.java:128)
	at com.flink.example.sql.tuning.MiniBatchExample.main(MiniBatchExample.java:32)
Caused by: org.apache.flink.table.api.ValidationException: Could not find any factories that implement 'org.apache.flink.table.delegation.ExecutorFactory' in the classpath.
	at org.apache.flink.table.factories.FactoryUtil.discoverFactory(FactoryUtil.java:387)
	at org.apache.flink.table.api.bridge.java.internal.StreamTableEnvironmentImpl.lookupExecutor(StreamTableEnvironmentImpl.java:176)
	... 3 more
```
这通常表示 **Flink 无法找到 SQL 执行引擎（Planner）**。本文将深入解析原因并提供完整解决方案。


---

## 2. 原因

从 Flink 1.11 版本开始，Table API/SQL 模块进行了重大重构：
- **Planner 模块化**  
  - Flink 将执行引擎从核心模块中分离，需显式添加依赖。
- **新旧 Planner 并存**  
  - **Blink Planner**（新，推荐）：`flink-table-planner-blink`
  - **Old Planner**（旧）：`flink-table-planner`
- **依赖缺失或冲突**
  - 未正确引入 Planner 依赖，或多个 Planner 冲突导致加载失败。

关键错误信息分析：
```java
Caused by: org.apache.flink.table.api.ValidationException:
Could not find any factories that implement 'org.apache.flink.table.delegation.ExecutorFactory'
```
👉 **核心问题：JVM 类路径中缺少有效的 Planner 实现。**

---

## 3. 解决方案

根据 Flink 版本选择对应方案，在项目的构建文件中添加对应依赖：

### 3.1 Flink 1.11 ~ 1.13 版本
```xml
<!-- 使用 Blink Planner（推荐） -->
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-table-planner-blink_${scala.version}</artifactId>
    <version>${flink.version}</version>
</dependency>

<!-- 桥接器（必选） -->
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-table-api-java-bridge_${scala.version}</artifactId>
    <version>${flink.version}</version>
</dependency>
```

### 3.2 Flink 1.14+ 版本
```xml
<!-- 1.14+ 后 Blink Planner 成为默认引擎 -->
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-table-planner_${scala.version}</artifactId>
    <version>${flink.version}</version>
</dependency>

<!-- 桥接器（必选） -->
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-table-api-java-bridge_${scala.version}</artifactId>
    <version>${flink.version}</version>
</dependency>
```

> **重要参数说明**：
> - `${scala.version}`：Scala 主版本（`2.11` 或 `2.12`）
> - `${flink.version}`：如 `1.14.4`

---

需要注意的是若同时存在新旧 Planner 会导致冲突：
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-table-planner-blink_2.12</artifactId>
    <version>1.13.6</version>
    <!-- 排除旧 Planner -->
    <exclusions>
        <exclusion>
            <groupId>org.apache.flink</groupId>
            <artifactId>flink-table-planner_2.12</artifactId>
        </exclusion>
    </exclusions>
</dependency>
```

---

#### 四、验证环境初始化代码
确保正确创建 `TableEnvironment`：
```java
import org.apache.flink.table.api.EnvironmentSettings;
import org.apache.flink.table.api.TableEnvironment;

public class FlinkSQLDemo {
    public static void main(String[] args) {
        // 1. 使用 Blink Planner 初始化
        EnvironmentSettings settings = EnvironmentSettings
            .newInstance()
            .useBlinkPlanner()    // 明确指定 Planner
            .inStreamingMode()    // 流模式
            .build();

        // 2. 创建 TableEnvironment
        TableEnvironment tEnv = TableEnvironment.create(settings);

        // 3. 执行 SQL 操作...
        tEnv.executeSql("CREATE TABLE KafkaSource (...)");
    }
}
```

---
