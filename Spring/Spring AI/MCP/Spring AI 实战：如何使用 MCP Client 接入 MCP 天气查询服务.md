上一篇[文章](https://smartsi.blog.csdn.net/article/details/160687102)，我们搭建了一个 MCP 天气服务（Server），它运行在 `localhost:8888`，对外暴露了 `get_weather` 工具。但 Server 本身不会说话——它只会安静地等待被调用。

本文将构建一个 **MCP Client** 应用，让它连接天气服务，并通过大模型实现这样的对话：

> **用户**：北京今天天气怎么样？
>
> **大模型**：（自动调用 get_weather 工具）北京今天局部多云，温度 25°C...

---

## 1. MCP Client 的职责

如果把 MCP 比作 USB-C，那么：
- **MCP Server** = 外接设备（U盘、显示器）
- **MCP Client** = 电脑上的 USB 接口

Client 的核心职责：
- **发现**：连接到 Server，获取它暴露了哪些工具
- **代理**：把这些工具"翻译"成大模型能理解的格式
- **执行**：当大模型决定调用工具时，帮它把请求转发给 Server

在 Spring AI 中，这一切几乎都是自动的。MCP 基于 SSE（Server-Sent Events） 传输，但 SSE 只是载体。真正的通信发生在 JSON-RPC 2.0 消息层。

---

## 2. 项目搭建

### 2.1 POM 依赖

#### 2.1.1 Spring Boot 依赖管理

Spring Boot 本身提供 BOM（spring-boot-dependencies）管理 Boot 生态，通常由父 POM 管理：
```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.5.14</version>
    <relativePath/>
</parent>
```

#### 2.1.2 Spring AI 依赖管理

Spring AI 也提供 BOM 来管理 Spring AI 生态，声明了 Spring AI 指定所有依赖的推荐版本：
```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework.ai</groupId>
            <artifactId>spring-ai-bom</artifactId>
            <version>1.1.5</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```
统一管理 Spring AI 生态下所有组件的版本，你在 dependencies 中引入具体模块时无需再写版本号。

> Spring AI 是一个多模块项目，包含：spring-ai-core、spring-ai-openai、spring-ai-mcp-server-webmvc 等。这些模块之间有严格的版本兼容关系。如果没有 BOM，你需要手动确保每个模块版本一致，容易出错。

#### 2.1.3 添加依赖

添加 Spring Boot Web 和 Spring AI MCP 等相关依赖：
```xml
<dependencies>
    <!-- Spring Boot Web -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>

    <!-- Spring AI OpenAI协议 模型 -->
    <dependency>
        <groupId>org.springframework.ai</groupId>
        <artifactId>spring-ai-starter-model-openai</artifactId>
    </dependency>

    <!-- Spring AI MCP Client WebFlux -->
    <dependency>
        <groupId>org.springframework.ai</groupId>
        <artifactId>spring-ai-starter-mcp-client-webflux</artifactId>
    </dependency>

    <!-- Spring Boot Lombok -->
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <optional>true</optional>
    </dependency>
</dependencies>
```
**注意**：Client 应用本身使用 Spring MVC（`spring-boot-starter-web`），但 MCP Client 传输层使用 WebFlux SSE（`spring-ai-starter-mcp-client-webflux`）。两者可以共存——MCP 的 WebFlux 传输是独立的响应式 HTTP 客户端，不会影响主应用的 Servlet 模型。

> 完整 POM 如下所示：
```xml
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <!-- 第一层：Spring Boot 父 POM，管理 Boot 生态 -->
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.5.14</version>
        <relativePath/>
    </parent>

    <artifactId>chat-mcp-tool</artifactId>
    <name>chat-mcp-tool</name>

    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <java.version>17</java.version>
        <spring-ai.version>1.1.5</spring-ai.version>
    </properties>

    <!-- 第二层：导入 Spring AI BOM，管理 AI 生态 -->
    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>org.springframework.ai</groupId>
                <artifactId>spring-ai-bom</artifactId>
                <version>${spring-ai.version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>

    <!-- 依赖 -->
    <dependencies>
        <!-- Spring Boot Web -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>

        <!-- Spring AI OpenAI协议 模型 -->
        <dependency>
            <groupId>org.springframework.ai</groupId>
            <artifactId>spring-ai-starter-model-openai</artifactId>
        </dependency>

        <!-- Spring AI MCP Client WebFlux -->
        <dependency>
            <groupId>org.springframework.ai</groupId>
            <artifactId>spring-ai-starter-mcp-client-webflux</artifactId>
        </dependency>

        <!-- Spring Boot Lombok -->
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <configuration>
                    <annotationProcessorPaths>
                        <path>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok</artifactId>
                        </path>
                    </annotationProcessorPaths>
                </configuration>
            </plugin>

            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <configuration>
                    <excludes>
                        <exclude>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok</artifactId>
                        </exclude>
                    </excludes>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

### 2.2 配置文件

在 `application.yml` 中配置 MCP Client 配置：
```yaml
server:
  port: 9999

spring:
  application:
    name: chat-mcp-tool
  ai:
    # MCP客户端配置
    mcp:
      client:
        enabled: true
        sse:
          connections:
            weather-server:
              url: http://localhost:8888
    # 模型配置
    openai:
      api-key: ${DASHSCOPE_API_KEY}
      base-url: https://dashscope.aliyuncs.com/compatible-mode
      chat:
        options:
          model: qwen3.5-35b-a3b
          temperature: 0.7
```

配置说明：

| 属性 | 含义 |
|------|------|
| `mcp.client.enabled` | 启用 MCP Client |
| `sse.connections` | 定义 SSE 连接的 Server 列表，key（`weather-server`）是连接标识 |
| `url` | MCP Server 的 SSE 端点地址，即上一篇启动的服务 |

支持同时连接多个 MCP Server：
```
sse:
  connections:
    weather-server:
      url: http://localhost:8888
    stock-server:
      url: http://localhost:8889
```

---

### 2.3 ChatClient 配置

`ChatClient` 是 Spring AI 的对话入口。这里不需要额外配置 MCP 工具，工具由 MCP Client 自动发现，并在 Controller 层动态注入：
```java
@Configuration
public class ChatConfig {
    // 远程 OpenAI 兼容协议大模型：百练
    @Bean
    public ChatClient chatClient(OpenAiChatModel chatModel) {
        return ChatClient.builder(chatModel)
                .build();
    }
}
```

---

### 2.4 对话控制器

在 ChatController 中定义对话入口：
```java
@Slf4j
@RestController
@RequestMapping("/api/v1/")
public class ChatController {

    @Autowired
    private ChatClient chatClient;

    @Autowired
    private ToolCallbackProvider toolCallbackProvider;

    @GetMapping(value = "/chat", produces = "text/plain;charset=UTF-8")
    public Flux<String> chatStream(
            @RequestParam(value = "message", defaultValue = "你是谁") String message) {

        Flux<String> result = chatClient
                .prompt()
                .user(message)
                .toolCallbacks(toolCallbackProvider)
                .stream()
                .content();

        log.info("chat: {}", message);
        return result;
    }
}
```

核心逻辑拆解：

| 代码 | 作用 |
|------|------|
| `chatClient.prompt()` | 开启一次对话请求 |
| `.user(message)` | 设置用户输入 |
| `.toolCallbacks(toolCallbackProvider)` | **关键**：把 MCP Client 发现的工具注入本次对话 |
| `.stream().content()` | 流式输出大模型的回复文本 |

`ToolCallbackProvider` 是 Spring AI 自动装配的 Bean，它封装了所有通过 MCP Client 发现的远程工具。当大模型判断需要调用工具时，Spring AI 会自动：
- 暂停文本生成
- 向 MCP Server 发起工具调用请求
- 拿到结果后，将结果送回大模型继续生成回复
- 最终返回给用户

整个过程对开发者完全透明。

---

## 3. 运行与验证

### 3.1 启动服务

> 请先确保 MCP Server 已启动（端口 8888）。具体参考第一篇[博文](https://smartsi.blog.csdn.net/article/details/160687102)。

直接运行主应用类 `ChatMcpApplication`：
```java
@SpringBootApplication
public class ChatMcpApplication {

    public static void main(String[] args) {
        SpringApplication.run(ChatMcpApplication.class, args);
    }
}
```
或者使用如下命令启动 MCP Client（端口 9999）：
```bash
mvn spring-boot:run
```

### 3.2 测试对话

浏览器中输入如下命令来查询北京天气：
```bash
http://localhost:9999/api/v1/chat?message=北京天气如何
```
预期会收到如下信息：
```
北京的天气情况如下：
- 天气状况: 晴天
- 温度: 23°C (体感温度: 23°C)
- 湿度: 44%
- 风速: 11 km/h (SSE)
- 降水量: 0.0 mm
- 能见度: 10 公里
- 紫外线指数: 1

观测时间: 2026-05-01 05:37 PM
```

> 完整代码：[chat-mcp-tool](https://github.com/sjf0115/spring-ai-example/tree/main/spring-ai/mcp/chat-mcp-tool)
