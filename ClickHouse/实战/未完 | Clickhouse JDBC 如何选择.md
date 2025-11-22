

```xml
<dependency>
    <groupId>ru.yandex.clickhouse</groupId>
    <artifactId>clickhouse-jdbc</artifactId>
    <version>0.3.0</version>
</dependency>
```

```xml
<dependency>
    <groupId>com.github.housepower</groupId>
    <artifactId>clickhouse-native-jdbc</artifactId>
    <version>1.6-stable</version>
</dependency>
```







两者间的主要区别如下：
- 驱动类加载路径不同，分别为 ru.yandex.clickhouse.ClickHouseDriver 和 com.github.housepower.jdbc.ClickHouseDriver
- 默认连接端口不同，分别为 8123 和 9000
- 连接协议不同，官方驱动使用 HTTP 协议，而三方驱动使用 TCP 协议



选择正确的 JDBC 驱动版本对于确保应用的稳定性、性能和功能至关重要。ClickHouse 社区主要有两个广泛使用的 JDBC 驱动：
- **官方驱动（推荐）**：`com.clickhouse:clickhouse-jdbc`
- **旧版/社区驱动**：`ru.yandex.clickhouse:clickhouse-jdbc`

**我们的建议是：对于所有新项目，请毫不犹豫地选择官方驱动 `com.clickhouse:clickhouse-jdbc`。**

---

## 1. 官方驱动

> 强烈推荐

这是由 ClickHouse 官方团队开发和维护的下一代 JDBC 驱动。它功能更全面，性能更好，并且与 ClickHouse 新版本特性保持同步。

### 1.1 核心 Maven 依赖

在你的 `pom.xml` 中，你需要添加两个依赖：
```xml
<dependencies>
    <!-- 核心JDBC驱动 -->
    <dependency>
        <groupId>com.clickhouse</groupId>
        <artifactId>clickhouse-jdbc</artifactId>
        <version>0.9.4</version> <!-- 请检查并使用最新版本 -->
    </dependency>

    <!-- 连接池实现（可选但强烈推荐） -->
    <dependency>
        <groupId>com.clickhouse</groupId>
        <artifactId>clickhouse-client</artifactId>
        <version>0.9.4</version> <!-- 版本应与驱动保持一致 -->
    </dependency>
</dependencies>
```

需要注意的是：
- `clickhouse-jdbc` 是驱动的主要工件。
- `clickhouse-client` 包含了底层的 HTTP 或 gRPC 客户端实现以及**内置的连接池**。在生产环境中，务必引入此依赖以获得最佳性能。

### 1.2 如何选择版本？

选择版本的策略如下：

*   **最新稳定版**：通常，你应该选择 Maven Central 上可用的最新稳定版本。你可以在 [Maven Central](https://central.sonatype.com/artifact/com.clickhouse/clickhouse-jdbc) 上查看。
*   **与 ClickHouse Server 版本兼容**：虽然新驱动设计为向后兼容，但为了获得最佳体验，建议参考官方发布的兼容性矩阵。通常来说：
    *   驱动版本 `0.3.2+` 可以很好地支持 ClickHouse server `20.7+`。
    *   驱动版本 `0.4.0+` 引入了更多优化和新特性，支持更新的 ClickHouse 版本。
*   **避免使用 `SNAPSHOT` 版本**：除非你在测试预览功能，否则不要在生产环境中使用 `-SNAPSHOT` 版本。

**版本选择示例：**
*   如果你的 ClickHouse 服务是 `22.8+`，可以使用 `0.4.6`。
*   如果你的服务稍旧（如 `21.8`），可以从 `0.3.6` 开始尝试，并尽快升级到更新的稳定版驱动。

### 1.3 JDBC URL 格式

官方驱动支持两种协议：

*   **HTTP（默认且最常用）**:
    ```java
    jdbc:ch://<host>:<port>[/<database>]?param1=value1&param2=value2
    ```
    *   示例：`jdbc:ch://localhost:8123/my_database`
    *   示例（带参数）：`jdbc:ch://localhost:8123/my_database?user=default&password=123&compress=true`

*   **gRPC（实验性，性能可能更好）**:
    ```java
    jdbc:ch:grpc://<host>:<port>[/<database>]?param1=value1&param2=value2
    ```
    *   端口通常是 `9100`。

---

## 2. 旧版社区驱动

> `ru.yandex.clickhouse:clickhouse-jdbc` 不推荐用于新项目

这是最初的社区驱动，曾经是标准选择。但**其开发已经基本停滞**，官方已不再积极维护。它缺少对新特性（如嵌套数据类型、gRPC协议等）的支持。目前已经停滞在 2021 年 更新的 0.3.2 版本。		

### 2.1 Maven 依赖

```xml
<dependency>
    <groupId>ru.yandex.clickhouse</groupId>
    <artifactId>clickhouse-jdbc</artifactId>
    <version>0.3.2</version> <!-- 这是最后一个广泛使用的版本 -->
</dependency>
```

**为什么不推荐？**
*   **维护停滞**：长期没有重大更新。
*   **功能缺失**：不支持很多 ClickHouse 新版本的高级功能。
*   **性能**：不如新的官方驱动优化得好。

**仅在你维护一个非常老旧的、无法轻易升级驱动的项目时，才考虑使用它。**

---

### 3. 版本选择决策流程与实践建议

#### 决策流程图

```mermaid
graph TD
    A[为新项目选择JDBC驱动] --> B{选择官方驱动 com.clickhouse}；
    B --> C[查看ClickHouse Server版本]；
    C --> D{Server >= 21.x?}；
    D -- 是 --> E[选择最新稳定版， 如 0.4.6]；
    D -- 否（旧版Server） --> F[尝试 0.3.x 版本]；
    F --> G[并计划升级Server和驱动]；
    B --> H(切勿选择旧版ru.yandex驱动)；
```

#### 最佳实践与关键配置参数

1.  **始终使用连接池**：通过引入 `clickhouse-client` 依赖，你可以轻松配置内置连接池。
    ```java
    // 在JDBC URL中指定连接池参数
    String url = "jdbc:ch://localhost:8123/my_database?user=default&password=123&socket_timeout=300000&connection_timeout=10000";
    ```

2.  **重要的连接参数**：
    *   `compress=true`：启用数据压缩，对网络性能有巨大提升。
    *   `socket_timeout`：Socket 超时（毫秒）。
    *   `connection_timeout`：建立连接超时（毫秒）。
    *   `keepAlive=true`：保持连接活跃。

3.  **在Spring Boot中配置**：
    在 `application.properties` 或 `application.yml` 中配置：
    ```properties
    # application.properties
    spring.datasource.url=jdbc:ch://localhost:8123/default
    spring.datasource.username=default
    spring.datasource.password=
    spring.datasource.driver-class-name=com.clickhouse.jdbc.ClickHouseDriver # 驱动类名
    ```

    ```yaml
    # application.yml
    spring:
      datasource:
        url: "jdbc:ch://localhost:8123/default"
        username: default
        password:
        driver-class-name: com.clickhouse.jdbc.ClickHouseDriver
    ```

4.  **检查最新版本**：
    定期访问 [Maven Central](https://central.sonatype.com/artifact/com.clickhouse/clickhouse-jdbc) 或项目的 [GitHub Repository](https://github.com/ClickHouse/clickhouse-java) 来查看版本更新和发布说明。

## 3. 总结

| 特性 | 官方驱动 (`com.clickhouse`) | 旧版驱动 (`ru.yandex`) |
| :--- | :--- | :--- |
| **推荐度** | **★★★★★（强烈推荐）** | ★☆☆☆☆（仅用于遗留系统） |
| **维护状态** | 积极维护 | 基本停滞 |
| **性能** | 优秀，支持gRPC | 一般 |
| **功能完整性** | 支持所有新特性 | 缺失新特性 |
| **版本选择** | 选择最新稳定版（如 `0.4.6`） | 锁定在 `0.3.2` |

**最终建议：** 立即将你的项目迁移或初始化为使用 `com.clickhouse:clickhouse-jdbc`，并选择与你的 ClickHouse 服务版本兼容的最新稳定版。同时，务必引入 `clickhouse-client` 以获得连接池支持。
