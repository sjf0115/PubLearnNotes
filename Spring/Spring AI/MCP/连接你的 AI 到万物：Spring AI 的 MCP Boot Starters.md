模型上下文协议（MCP）标准化了 AI 应用程序与外部工具和资源的交互方式。Spring 早期加入了 MCP 生态系统并成为关键贡献者，协助开发以及维护[官方 MCP Java SDK](https://github.com/modelcontextprotocol/java-sdk)(Java 版 MCP 基础实现)。基于此贡献，Spring AI 通过专用[Boot Starters](https://docs.spring.io/spring-ai/reference/1.1-SNAPSHOT/api/mcp/mcp-overview.html#_spring_ai_mcp_integration)和[MCP Java注解](https://docs.spring.io/spring-ai/reference/1.1-SNAPSHOT/api/mcp/mcp-annotations-overview.html)全面拥抱 MCP，从而使构建能够无缝连接外部系统的复杂AI应用变得前所未有的简单。

本篇博客将介绍 MCP 的核心组件，并演示使用 Spring AI 构建 MCP Server和客户端的基础与高级功能。完整源代码请访问：[MCP天气示例](https://github.com/tzolov/spring-ai-mcp-blogpost)。

> **注意：** 本文内容仅适用于 Spring AI `1.1.0-SNAPSHOT`或 Spring `AI 1.1.0-M1+` 版本。

## 1. 什么是模型上下文协议？

[模型上下文协议（MCP）](https://modelcontextprotocol.org/docs/concepts/architecture)是一个标准化协议，使 AI 模型能够以结构化方式与外部工具和资源交互。可以将其视为 AI 模型与现实世界之间的桥梁——允许它们通过统一接口访问数据库、API、文件系统和其他外部服务。

---

## 2. MCP 客户端-服务器架构

![](https://raw.githubusercontent.com/spring-io/spring-io-static/refs/heads/main/blog/tzolov/20250911/MCP-CLIENT-SERVER-ARCHITECTURE.svg)

模型上下文协议遵循客户端-服务器架构，确保职责明确分离。MCP服务器从第三方服务暴露特定能力（工具、资源、提示）。MCP 客户端由宿主应用程序实例化，用于与特定 MCP Server 通信。每个客户端处理与一个服务器的直接通信。

宿主（Host）是用户交互的 AI 应用程序，而客户端是支持服务器连接的协议级组件。MCP 协议确保客户端和服务器之间实现完全的与语言无关的交互。您可以用 Java、Python 或 TypeScript 编写的客户端与任何语言的服务器通信，反之亦然。

这种架构在客户端和服务器端开发之间建立了清晰的边界和职责，自然形成了两个不同的开发者社区：

**AI 应用程序/宿主开发者**

负责协调多个 MC P服务器（通过 MCP 客户端连接）并与 AI 模型集成的复杂性。AI 开发者构建的应用程序能够：
- 使用 MCP 客户端与多个 MCP Server通信的能力
- 处理 AI 模型集成和提示词工程
- 管理对话上下文和用户交互
- 编排跨不同服务的复杂工作流
- 专注于创建引人入胜的用户体验

**MCP Server（提供者）开发者**

专注于将第三方服务（数据库、文件系统、外部API）的特定能力暴露为 MCP Server。服务器开发者创建的服务器能够：
- 封装第三方服务和 API
- 通过标准化的 MCP 原语（工具、资源、提示）暴露服务能力
- 处理特定服务的认证和授权

这种分离确保服务器开发者可以专注于封装其领域特定服务，而无需担心 AI 编排。同时，AI 应用开发者可以复用现有 MCP Server，而无需理解每个第三方服务的内部细节。这种分工意味着数据库专家可以创建 PostgreSQL 的 MCP Server 而无需理解 LLM 提示词，而 AI 应用开发者可以使用该 PostgreSQL MCP Server 而无需了解 SQL 内部机制。MCP 协议成为他们之间的通用语言。

**Spring AI** 通过[MCP Client](https://docs.spring.io/spring-ai/reference/1.1-SNAPSHOT/api/mcp/mcp-client-boot-starter-docs.html)和[MCP Server](https://docs.spring.io/spring-ai/reference/1.1-SNAPSHOT/api/mcp/mcp-server-boot-starter-docs.html) Boot Starters 拥抱这一架构。这意味着 Spring 开发者均可以参与 MCP 生态系统的双方——构建消费 MCP Server 的 AI 应用，以及创建将基于 Spring 的服务的 MCP Server。

---

## 3. MCP 特性

![MCP Capabilities](https://raw.githubusercontent.com/spring-io/spring-io-static/refs/heads/main/blog/tzolov/20250911/MCP-FEATURES.svg)

MCP（模型上下文协议）应用于 Client 和 Server 之间，提供全套功能集以实现 AI 应用与外部服务的无缝衔接：
- 暴露 AI 模型可调用的[工具](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
- 与 AI 应用共享[资源](https://modelcontextprotocol.io/specification/2025-06-18/server/resources)和数据
- 提供一致交互的[Prompt](https://modelcontextprotocol.io/specification/2025-06-18/server/prompts)模板
- 为 Prompt 和资源 URI 提供参数[自动补全](https://modelcontextprotocol.io/specification/2025-06-18/server/utilities/completion)建议
- 处理实时通知和[进度](https://modelcontextprotocol.io/specification/2025-06-18/basic/utilities/progress)更新
- 支持客户端[采样](https://modelcontextprotocol.io/specification/2025-06-18/client/sampling)、[启发](https://modelcontextprotocol.io/specification/2025-06-18/client/elicitation)、[结构化日志](https://modelcontextprotocol.io/specification/2025-06-18/server/utilities/logging)和[进度追踪](https://modelcontextprotocol.io/specification/2025-06-18/basic/utilities/progress)
- 支持多种传输协议：[STDIO](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports#stdio)、[Streamable-HTTP](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports#streamable-http)和[SSE](https://modelcontextprotocol.io/specification/2024-11-05/basic/transports#http-with-sse)

> **重要提示：** 与其他 MCP 功能（如 Prompt 和资源）不同，工具由 LLM 拥有。LLM（而非宿主）决定是否、何时以及以何种顺序调用工具。宿主仅控制向 LLM 提供哪些工具描述。

---

## 4. 构建 MCP Server

让我们构建一个[Streamable-HTTP MCP Server](https://docs.spring.io/spring-ai/reference/1.1-SNAPSHOT/api/mcp/mcp-streamable-http-server-boot-starter-docs.html)，提供实时天气预报信息。

### 4.1 Spring Boot 服务器应用

创建一个新的（`mcp-weather-server`）Spring Boot 应用：
```java
@SpringBootApplication
public class McpServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(McpServerApplication.class, args);
    }
}
```
添加 Spring AI MCP Server 依赖：
```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-mcp-server-webmvc</artifactId>
</dependency>
```
> 了解更多可用的 [Server 依赖参数](https://docs.spring.io/spring-ai/reference/1.1-SNAPSHOT/api/mcp/mcp-server-boot-starter-docs.html#_mcp_server_boot_starters)。

在 `application.properties` 中启用 [Streamable HTTP](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports#streamable-http) 服务器传输：
```
spring.ai.mcp.server.protocol=STREAMABLE
```
您可以选择 `STREAMABLE`、`STATELESS` 或 `SSE` 传输启动 MCP Server。要启用 `STDIO` 传输，则需设置 `spring.ai.mcp.server.stdio=true`。

### 4.2 天气服务

利用免费的[天气 REST API](https://open-meteo.com/) 构建通过坐标位置获取天气预报的服务。添加 `@McpTool` 和 `@McpToolParam` 注解，将 `getTemperature` 方法注册为 MCP Server 工具：
```java
@Service
public class WeatherService {

	public record WeatherResponse(Current current) {
		public record Current(LocalDateTime time, int interval, double temperature_2m) {}
	}

	@McpTool(description = "Get the temperature (in celsius) for a specific location")
	public WeatherResponse getTemperature(
      @McpToolParam(description = "The location latitude") double latitude,
      @McpToolParam(description = "The location longitude") double longitude) {

		return RestClient.create()
				.get()
				.uri("https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m",
						latitude, longitude)
				.retrieve()
				.body(WeatherResponse.class);
	}
}
```
### 4.3 构建与运行

```
./mvnw clean install -DskipTests

java -jar target/mcp-weather-server-0.0.1-SNAPSHOT.jar
```
运行上述命令会启动 `mcp-weather-server`，监听端口默认为 `8080`。

### 4.5 使用 MCP Server

天气 MCP Server 启动运行后，您可以使用各种 MCP 兼容的客户端应用与之交互：

#### 4.5.1 MCP Inspector

MCP Inspector 是用于测试和调试 MCP Server 的交互式开发者工具。运行以下命令启动 MCP Inspector：
```
npx @modelcontextprotocol/inspector
```
在浏览器中，设置传输类型为 `Streamable HTTP`，URL为 `http://localhost:8080/mcp`。点击 `Connect` 建立连接。然后列出工具并运行 `getTemperature`：

![](https://raw.githubusercontent.com/spring-io/spring-io-static/refs/heads/main/blog/tzolov/20250911/MCP-INSPECTOR.png)

#### 4.5.2 MCP Java SDK

使用 MCP Java SDK 客户端以编程方式连接 MCP Server：
```java
var client = McpClient.sync(
HttpClientStreamableHttpTransport
	.builder("http://localhost:8080").build())
.build();

client.initialize();

CallToolResult weather = client.callTool(
	new CallToolRequest("getTemperature",
			Map.of("latitude", "47.6062",
					"longitude", "-122.3321")));
```

#### 4.5.3 Claude Desktop

要与 Claude Desktop 集成，使用本地 [STDIO](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports#stdio) 传输，在 Claude Desktop 设置中添加以下配置：
```json
{
 "mcpServers": {
  "spring-ai-mcp-weather": {
  "command": "java",
  "args": [
    	"-Dspring.ai.mcp.server.stdio=true",
    	"-Dspring.main.web-application-type=none",
    	"-Dlogging.pattern.console=",
    	"-jar",
    	"/path/to/mcp-weather-server-0.0.1.jar"]
  }
 }
}
```
将 `/absolute/path/to/` 替换为您的 JAR 文件实际路径。

遵循 [Claude Desktop 的 MCP Server 安装指南](https://www.anthropic.com/engineering/desktop-extensions) 获取进一步指导。Claude Desktop 免费版不支持采样功能！

### 4.6 高级功能

让我们扩展天气 MCP Server 以演示日志记录、进度跟踪和采样等高级 MCP 功能。这些功能丰富了 Server 与 Client 之间的交互：
- 日志记录：向连接的 Client 发送结构化日志消息用于调试和监控
- 进度跟踪：为长时间运行的操作报告实时进度更新
- 采样：基于 Server 数据请求 Client 的LLM生成内容

在这个增强版本中，我们的天气 MCP Server 将向 Client 记录操作以提升透明度，实时反馈天气数据获取与处理的进度，并请求 Client 的 LLM 生成关于天气预报的史诗诗歌。

以下是更新后的 Server 实现：
```java
@Service
public class WeatherService {

	public record WeatherResponse(Current current) {
		public record Current(LocalDateTime time, int interval, double temperature_2m) {}
	}

	@McpTool(description = "Get the temperature (in celsius) for a specific location")
	public String getTemperature(
			McpSyncServerExchange exchange, // (1)
			@McpToolParam(description = "The location latitude") double latitude,
			@McpToolParam(description = "The location longitude") double longitude,
			@McpProgressToken String progressToken) { // (2)

		exchange.loggingNotification(LoggingMessageNotification.builder() // (3)
			.level(LoggingLevel.DEBUG)
			.data("Call getTemperature Tool with latitude: " + latitude + " and longitude: " + longitude)
			.meta(Map.of()) // non null meta as a workaround for bug: ...
			.build());

		WeatherResponse weatherResponse = RestClient.create()
				.get()
				.uri("https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m",
						latitude, longitude)
				.retrieve()
				.body(WeatherResponse.class);


		String epicPoem = "MCP Client doesn't provide sampling capability.";

		if (exchange.getClientCapabilities().sampling() != null) {
			// 50% progress
			exchange.progressNotification(new ProgressNotification(progressToken, 0.5, 1.0, "Start sampling"));	// (4)

			String samplingMessage = """
					For a weather forecast (temperature is in Celsius): %s.
					At location with latitude: %s and longitude: %s.
					Please write an epic poem about this forecast using a Shakespearean style.
					""".formatted(weatherResponse.current().temperature_2m(), latitude, longitude);

			CreateMessageResult samplingResponse = exchange.createMessage(CreateMessageRequest.builder()
					.systemPrompt("You are a poet!")
					.messages(List.of(new SamplingMessage(Role.USER, new TextContent(samplingMessage))))
					.build()); // (5)

			epicPoem = ((TextContent) samplingResponse.content()).text();
		}

		// 100% progress
		exchange.progressNotification(new ProgressNotification(progressToken, 1.0, 1.0, "Task completed"));

		return """
			Weather Poem: %s			
			about the weather: %s°C at location: (%s, %s)		
			""".formatted(epicPoem, weatherResponse.current().temperature_2m(), latitude, longitude);
  }
}
```
- `McpSyncServerExchange`: exchange 参数提供访问 Server - Client 通信能力，允许 Server 向 Client 发送通知和请求。
- `@ProgressToken`: progressToken 参数启用进度跟踪。Client 提供此令牌，Server 用它发送进度更新。
- 日志通知: 向 Client 发送结构化日志消息用于调试和监控。
- 进度更新: 向 Client 报告操作进度（此处为50%）及描述性消息。

![](https://raw.githubusercontent.com/spring-io/spring-io-static/refs/heads/main/blog/tzolov/20250911/MCP-SAMPLING-SEQ.svg)

- 采样功能: 最强大的功能，Server 可以请求 Client 的 LLM 生成内容。

这允许 Server 利用 Client 的 AI 能力，创建双向 AI 交互模式。增强后的天气 MCP Server 现在不仅返回天气数据，还返回关于预报的创意诗歌，展示了 MCP Server 与 AI 模型之间的强大协同作用。

## 5. 构建 MCP Client

让我们构建一个使用 LLM 并通过 MCP Client 连接 MCP Server 的 AI 应用。

### 5.1 客户端配置

创建一个新的 Spring Boot 项目（mcp-weather-client），包含以下依赖：
```xml
<dependency>
  <groupId>org.springframework.ai</groupId>
  <artifactId>spring-ai-starter-mcp-client</artifactId>
</dependency>

<dependency>
  <groupId>org.springframework.ai</groupId>
  <artifactId>spring-ai-starter-model-anthropic</artifactId>
</dependency>
```
在 `application.yml` 中配置到 MCP Server 的连接：
```
spring:
  main:
    web-application-type: none

  ai:
    # Set credentials for your Anthropic API account
    anthropic:
      api-key: ${ANTHROPIC_API_KEY}

    # Connect to the MCP Weather Server using streamable-http client transport
    mcp:
      client:
        streamable-http:
          connections:
            my-weather-server:
              url: http://localhost:8080    
```
注意配置中已为 Server 连接分配了 my-weather-server 名称。

### 5.2 Spring Boot 客户端应用

创建一个使用 ChatClient 连接 LLM 和天气 MCP Server 的客户端应用：
```java
@SpringBootApplication
public class McpClientApplication {

	public static void main(String[] args) {
		SpringApplication.run(McpClientApplication.class, args).close(); // (1)
	}

	@Bean
	public ChatClient chatClient(ChatClient.Builder chatClientBuilder) { // (2)
		return chatClientBuilder.build();
	}

	String userPrompt = """
		Check the weather in Amsterdam right now and show the creative response!
		Please incorporate all creative responses from all LLM providers.
		""";

	@Bean
	public CommandLineRunner predefinedQuestions(ChatClient chatClient, ToolCallbackProvider mcpToolProvider) { // (3)
		return args -> System.out.println(
			chatClient.prompt(userPrompt) // (4)
				.toolContext(Map.of("progressToken", "token-" + new Random().nextInt())) // (5)
				.toolCallbacks(mcpToolProvider) // (6)
				.call()
				.content());
	}
}
```



> 原文：[Connect Your AI to Everything: Spring AI's MCP Boot Starters](https://spring.io/blog/2025/09/16/spring-ai-mcp-intro-blog)
