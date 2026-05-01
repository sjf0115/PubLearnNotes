## 1. 手动创建实例，绕过 Spring 代理（最简洁）

`WeatherService` 是无状态的，直接在 `ChatController` 里 `new` 一个实例传给 `.tools()`：

```java
@RestController
public class ChatController {
    @Autowired
    private ChatClient chatClient;

    // 手动创建，不是 Spring Bean，没有代理问题
    private final WeatherService weatherService = new WeatherService();

    @GetMapping("/chat")
    public String chat(@RequestParam String message) {
        return chatClient
                .prompt()
                .user(message)
                .tools(weatherService)  // 直接传入，最自然
                .call()
                .content();
    }
}
```

**优点**：代码最少，最直观，没有代理问题  
**缺点**：`WeatherService` 不能注入其他 Spring Bean（当前它本来也没注入）

---

## 2. 直接用 `ToolCallbackProvider`（次简洁）

保留 `MethodToolCallbackProvider` Bean，但调用时直接传 Provider，不用手动 `getToolCallbacks()`：

```java
// 配置类（只需定义一次）
@Bean
public ToolCallbackProvider weatherTools(WeatherService weatherService) {
    return MethodToolCallbackProvider.builder().toolObjects(weatherService).build();
}

// ChatController
@Autowired
private ToolCallbackProvider toolCallbackProvider;

chatClient.prompt()
    .user(message)
    .toolCallbacks(toolCallbackProvider)  // 直接传 Provider
    .call()
    .content();
```

**优点**：Spring 管理生命周期，WeatherService 可以注入其他 Bean  
**缺点**：需要多定义一个 Bean

---


```java
@Autowired
private MethodToolCallbackProvider toolCallbackProvider;

@GetMapping(value = "/chat", produces = "text/plain;charset=UTF-8")
public Flux<String> askWeather(
        @RequestParam(value = "message", defaultValue = "你是谁") String message) {

    // 从 MethodToolCallbackProvider 获取所有已注册的 MCP Tool
    List<ToolCallback> tools = Arrays.asList(toolCallbackProvider.getToolCallbacks());
    for (ToolCallback toolCallback : tools) {
        log.info("注册工具：{}", toolCallback.getToolDefinition().name());
    }

    Flux<String> result = chatClient
            .prompt()
            .user(message)
            .toolCallbacks(tools.toArray(new ToolCallback[0]))  // ToolCallback 用 toolCallbacks() 方法
            .stream()
            .content();
    log.info("chat: {}", message);
    return result;
}
```

注意使用 MethodToolCallbackProvider 方式，需要 toolCallbacks() 方法配合，而不是之前常见的 tools() 方法。

`ChatClient` 的 `.tools()` 方法期望传入**带有 `@Tool` 注解的原始对象**（如 `WeatherService`），而不是已经包装好的 `ToolCallback`。传入 `ToolCallback` 时应该用 `.toolCallbacks()`。

| 方法 | 期望参数 | 内部行为 |
|------|---------|---------|
| `.tools()` | 带有 `@Tool` 注解的原始对象（如 `WeatherService`） | 调用 `ToolCallbacks.from()` 扫描 `@Tool` 方法 |
| `.toolCallbacks()` | 已经包装好的 `ToolCallback` 或 `ToolCallbackProvider` | 直接使用，不再扫描 |

> 传入的是已经包装好的 `MethodToolCallback`，所以必须用 `.toolCallbacks()`。





## 3. 通过 MCP Client 协议调用（最正规）

如果你的 Chat 应用和 MCP Server 是 **两个独立服务**，就必须走网络：

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

```
server:
  port: 9999

spring:
  application:
    name: chat-mcp-tool
  ai:
    mcp:
      client:
        enabled: true
        sse:
          connections:
            weather-server:
              url: http://localhost:8888
    openai:
      api-key: ${DASHSCOPE_API_KEY}
      base-url: https://dashscope.aliyuncs.com/compatible-mode
      chat:
        options:
          model: qwen3.5-35b-a3b
          temperature: 0.7
```

Spring AI 自动配置会帮你做三件事：
根据 spring.ai.mcp.client.sse.connections 创建 McpSyncClient
自动 initialize() 并 listTools()
创建 SyncMcpToolCallbackProvider Bean（即 ToolCallbackProvider）
你只需注入 ToolCallbackProvider 传给 ChatClient.toolCallbacks() 即可


**优点**：服务解耦，符合 MCP 设计初衷  
**缺点**：代码最多，有网络开销

---

## 4. 推荐选择

| 场景 | 推荐方式 |
|------|---------|
| 单应用（Server + Chat 在一起） | **方式一** `new WeatherService()` 传给 `.tools()` |
| 单应用，但 WeatherService 需要注入其他 Bean | **方式二** `ToolCallbackProvider` |
| 多应用（Chat 和 MCP Server 分离） | **方式三** MCP Client |

你当前的 `WeatherService` 构造器是空的（`new WeatherService()`），没有任何 Spring 依赖，所以**方式一最清爽**：

```java
private final WeatherService weatherService = new WeatherService();

// 调用时
.tools(weatherService)
```

需要我把 `ChatController` 改成方式一吗？







## 6. 客户端如何调用这个 MCP Server？

MCP Server 启动后，会在 `/mcp` 路径暴露 SSE（Server-Sent Events）端点。客户端通过 SSE 与 Server 建立长连接，然后收发 JSON-RPC 消息。

### 6.1 用 Spring AI MCP Client 连接

```java
// 1. 创建 SSE 传输层，指向 MCP Server
WebFluxSseClientTransport transport = new WebFluxSseClientTransport(
        WebClient.builder().baseUrl("http://localhost:8888"),
        McpJsonMapper.createDefault()
);
// 2. 创建同步客户端
McpSyncClient client = io.modelcontextprotocol.client.McpClient.sync(transport).build();

// 3. 初始化连接
client.initialize();
client.ping();

// 4. 列出 Server 暴露的所有工具
McpSchema.ListToolsResult tools = client.listTools();
System.out.println("可用工具: " + tools);

// 5. 调用 get_weather 工具
McpSchema.CallToolResult result = client.callTool(
        new McpSchema.CallToolRequest(
                "get_weather",           // Tool 名称
                Map.of("cityName", "北京")  // 参数
        )
);
System.out.println("天气结果: " + result.content());

// 6. 关闭连接
client.closeGracefully();
```

### 5.2 在 Dify 中使用 MCP 工具

> 在 Dify 中如何使用 MCP 工具，详细请查阅[Dify 实战：通过 Dify 快速接入 MCP Server](https://smartsi.blog.csdn.net/article/details/157619776)

首选在 Dify 中添加天气 MCP 服务：

![](img-spring-ai-mcp-1.png)

创建之后可以看到 MCP 服务包含的 get_weather 工具：

![](img-spring-ai-mcp-2.png)

在 Dify 中以创建一个 Agent 应用为例，验证接入 MCP Server 效果。输入合适的提示词并配置工具：

![](img-spring-ai-mcp-3.png)

当用户问"北京天气如何？"时，Spring AI 会自动：
- 把问题发送给大模型
- 大模型读到 `get_weather` 的 description，判断需要调用
- Spring AI 执行 `WeatherService.getWeatherByCity("北京")`
- 拿到结果后再次发给大模型，让模型组织成自然语言回复

通过查看天气 MCP 服务日志输出如下，可以证明大模型调用 MCP 工具成功：
```
2026-05-01T11:10:11.351+08:00  INFO 53569 --- [oundedElastic-1] com.mcp.example.server.WeatherService    : 天气 MCP 查询结果：城市: 北京
天气情况: 局部多云
气压: 1011（mb）
温度: 25°C (体感温度: 24°C)
湿度: 36%
降水量:0.0 (mm)
风速: 12 km/h (E)
能见度: 10 公里
紫外线指数: 5
观测时间: 2026-05-01 10:54 AM
```
