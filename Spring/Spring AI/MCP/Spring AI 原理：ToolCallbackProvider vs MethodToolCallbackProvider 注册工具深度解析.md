## 1. 从一个代码差异说起

在 Spring AI 项目中注册工具时，你可能会遇到两种截然不同的注入写法：

**写法 A：MCP Server 端（本地工具暴露）**
```java
@Autowired
private MethodToolCallbackProvider toolCallbackProvider;
```

**写法 B：MCP Client 端（远程工具调用）**
```java
@Autowired
private ToolCallbackProvider toolCallbackProvider;
```

表面看只是"注入接口"和"注入实现类"的区别，但背后涉及的是 **本地方法级工具**与**远程协议级工具** 两种完全不同的架构模式。本文基于 Spring AI 1.1.5 源码，彻底拆解两者的设计意图、实现原理与选型策略。

---

## 2. `ToolCallbackProvider`：工具发现的统一抽象

`ToolCallbackProvider` 是 Spring AI 工具生态的顶层接口，定义极简：
```java
public interface ToolCallbackProvider {

	ToolCallback[] getToolCallbacks();

	static ToolCallbackProvider from(List<? extends ToolCallback> toolCallbacks) {
		return new StaticToolCallbackProvider(toolCallbacks);
	}

	static ToolCallbackProvider from(ToolCallback... toolCallbacks) {
		return new StaticToolCallbackProvider(toolCallbacks);
	}

}
```

它的职责只有一个：**向 `ChatClient` 提供一组可供大模型调用的 `ToolCallback`**。至于这些工具从何而来，接口并不关心。

Spring AI 1.1.5 中，该接口有四个主要实现：

| 实现类 | 工具来源 | 核心机制 |
|--------|---------|---------|
| `MethodToolCallbackProvider` | 本地 `@Tool` 注解方法 | 反射扫描 + `MethodToolCallback` 包装 |
| `SyncMcpToolCallbackProvider` | 远程 MCP Server（同步） | `McpSyncClient.listTools()` + 缓存 |
| `AsyncMcpToolCallbackProvider` | 远程 MCP Server（异步） | `McpAsyncClient.listTools().block()` + 缓存 |
| `StaticToolCallbackProvider` | 预构建的 `ToolCallback` 数组 | 直接持有，无动态发现 |

**关键洞察**：当你注入 `ToolCallbackProvider` 时，实际拿到的实现类由 classpath 上的依赖和自动配置决定。在 `spring-ai-starter-mcp-client` 场景下，Spring Boot 自动配置会注入 `SyncMcpToolCallbackProvider`（或 `AsyncMcpToolCallbackProvider`），它通过网络协议从远程 MCP Server 发现工具。

---

## 3. `MethodToolCallbackProvider`：本地方法的反射工厂

`MethodToolCallbackProvider` 是 `ToolCallbackProvider` 的最典型实现，负责将 Java 方法转化为大模型可调用的工具。

### 3.1 构建方式

```java
@Bean
public MethodToolCallbackProvider weatherTools(WeatherService weatherService) {
    return MethodToolCallbackProvider.builder()
            .toolObjects(weatherService)
            .build();
}
```
> `toolObjects()` 接受一个或多个对象，构造器会立即执行**全量验证**：

```java
private MethodToolCallbackProvider(List<Object> toolObjects) {
    assertToolAnnotatedMethodsPresent(toolObjects);  // 必须存在 @Tool 方法
    this.toolObjects = toolObjects;
    validateToolCallbacks(getToolCallbacks());        // 校验工具名唯一性
}
```

### 3.2 核心原理：运行时反射组装

`getToolCallbacks()` 的每一步都经过精密设计：
```
public ToolCallback[] getToolCallbacks() {
    return this.toolObjects.stream()
        .map(toolObject -> Stream
            .of(ReflectionUtils.getDeclaredMethods(
                AopUtils.isAopProxy(toolObject)
                    ? AopUtils.getTargetClass(toolObject)  // 关键：解开 Spring 代理
                    : toolObject.getClass()))
            .filter(this::isToolAnnotatedMethod)          // 筛选 @Tool 方法
            .filter(toolMethod -> !isFunctionalType(toolMethod)) // 排除 Function/Supplier
            .filter(ReflectionUtils.USER_DECLARED_METHODS::matches) // 排除 Object 方法
            .map(toolMethod -> MethodToolCallback.builder()
                .toolDefinition(ToolDefinitions.from(toolMethod))   // 解析 @Tool 描述
                .toolMetadata(ToolMetadata.from(toolMethod))        // 解析 @ToolParam
                .toolMethod(toolMethod)
                .toolObject(toolObject)                            // 绑定调用目标
                .toolCallResultConverter(ToolUtils.getToolCallResultConverter(toolMethod))
                .build())
            .toArray(ToolCallback[]::new))
        .flatMap(Stream::of)
        .toArray(ToolCallback[]::new);
}
```

**源码级的三个关键细节**：
- **AOP 代理兼容**：`AopUtils.isAopProxy(toolObject) ? AopUtils.getTargetClass(toolObject) : toolObject.getClass()` 这一行解决了 Spring `@Service` 代理场景下反射找不到 `@Tool` 方法的问题。若传的是代理对象，必须解包到目标类。
- **功能类型过滤**：`isFunctionalType()` 排除返回 `Function`/`Supplier`/`Consumer` 的方法，防止误扫描。
- **重复名校验**：同一组 `toolObjects` 中若存在同名工具，构造阶段直接抛 `IllegalStateException`。

### 3.3 与 `ToolCallbacks.from()` 的关系

Spring AI 还提供了更上层的便捷方法：
```java
@Bean
public ToolCallbackProvider weatherTools(WeatherService weatherService) {
    return ToolCallbacks.from(weatherService);  // 内部就是 MethodToolCallbackProvider
}
```

`ToolCallbacks.from()` 本质上是对 `MethodToolCallbackProvider.builder()` 的封装。但 **直接使用 `MethodToolCallbackProvider` 的优势在于**：可以合并多个 Service、自定义解析器，且类型明确。

---

## 4. `SyncMcpToolCallbackProvider`：远程工具的发现与缓存

当项目中引入 `spring-ai-starter-mcp-client` 时，自动配置注入的通常是 `SyncMcpToolCallbackProvider`。它的工作方式与 `MethodToolCallbackProvider` 完全不同：
```java
public class SyncMcpToolCallbackProvider implements ToolCallbackProvider, ApplicationListener<McpToolsChangedEvent> {
    private final List<McpSyncClient> mcpClients;
    private volatile boolean invalidateCache = true;
    private volatile List<ToolCallback> cachedToolCallbacks = List.of();

    @Override
    public ToolCallback[] getToolCallbacks() {
        if (this.invalidateCache) {
            this.lock.lock();
            try {
                if (this.invalidateCache) {
                    this.cachedToolCallbacks = this.mcpClients.stream()
                        .flatMap(mcpClient -> mcpClient.listTools()  // 网络 I/O！
                            .tools()
                            .stream()
                            .map(tool -> SyncMcpToolCallback.builder()
                                .mcpClient(mcpClient)
                                .tool(tool)
                                .build()))
                        .toList();
                    this.invalidateCache = false;
                }
            } finally {
                this.lock.unlock();
            }
        }
        return this.cachedToolCallbacks.toArray(new ToolCallback[0]);
    }
}
```

**核心特征**：
- **网络发现**：`mcpClient.listTools()` 通过 SSE/HTTP 向远程 MCP Server 获取工具列表
- **双重检查锁缓存**：首次调用后缓存结果，监听 `McpToolsChangedEvent` 刷新
- **阻塞 I/O**：`McpSyncClient` 内部调用 `.block()`，这也是 WebFlux 环境下报 `IllegalStateException: blocking which is not supported` 的根因。

---

## 5. 本质区别全景对比

| 维度 | `ToolCallbackProvider`（接口） | `MethodToolCallbackProvider`（实现） |
|------|-------------------------------|-------------------------------------|
| **设计层级** | 抽象接口，面向契约 | 具体实现，面向本地方法 |
| **工具来源** | 取决于注入的实现类（本地/远程/静态） | 仅来自当前 JVM 内的 `@Tool` 注解方法 |
| **发现机制** | 动态发现（MCP 场景有网络 I/O） | 静态反射（无网络 I/O） |
| **构建方式** | 通常由 Spring Boot 自动配置注入 | 必须由开发者显式 `builder()` 构建 |
| **阻塞风险** | MCP 实现类内部有 `.block()` | 纯反射，无阻塞 |
| **AOP 代理处理** | 不涉及 | 内部解包 `AopUtils.getTargetClass()` |
| **缓存策略** | MCP 实现带双重检查锁缓存 | 每次 `getToolCallbacks()` 重新反射 |
| **使用场景** | MCP Client 消费远程工具 | MCP Server 暴露本地工具 |

---

## 6. 具体使用场景

### 场景 1：MCP Server 端 —— 必须用 `MethodToolCallbackProvider`

当你要 **把自己的 Service 方法暴露为 MCP 工具** 时：
```java
@Service
public class WeatherService {
    @Tool(name = "get_weather", description = "获取指定城市的天气")
    public String getWeatherByCity(@ToolParam(description = "城市名称") String cityName) {
        // ...
    }
}

@SpringBootApplication
public class McpServerApplication {
    @Bean
    public MethodToolCallbackProvider weatherTools(WeatherService weatherService) {
        return MethodToolCallbackProvider.builder()
                .toolObjects(weatherService)
                .build();
    }
}
```

**为什么不用 `ToolCallbackProvider`？**  
因为 MCP Server 端没有引入 `spring-ai-starter-mcp-client`，classpath 上不存在 MCP 自动配置，注入 `ToolCallbackProvider` 会报 `No qualifying bean`。此时只有手动构建 `MethodToolCallbackProvider` 这条路。

### 场景 2：MCP Client 端 —— 注入 `ToolCallbackProvider`

当你要 **消费远程 MCP Server 的工具** 时：
```java
@RestController
public class ChatController {
    @Autowired
    private ToolCallbackProvider toolCallbackProvider;  // 自动配置注入 SyncMcpToolCallbackProvider

    @GetMapping("/chat")
    public Flux<String> chat(@RequestParam String message) {
        return chatClient.prompt()
                .user(message)
                .toolCallbacks(toolCallbackProvider)  // 传递的是 Provider
                .stream()
                .content();
    }
}
```

**为什么不用 `MethodToolCallbackProvider`？**  因为 Client 端根本没有本地 `@Tool` 方法，工具全部来自远程。此时只能依赖 MCP 自动配置注入的 `SyncMcpToolCallbackProvider`。

### 场景 3：静态工具 —— 绕过 Provider 直接传数组

当你有预构建的 `ToolCallback` 时，可以最简化：
```java
ToolCallback[] tools = {new MyCustomToolCallback()};
chatClient.prompt().toolCallbacks(tools).stream().content();
```

---

## 7. 优缺点深度分析

### `ToolCallbackProvider`（接口注入）

**优点**：
- **解耦**：不依赖具体实现，切换 MCP Client 版本无需改代码
- **自动配置**：Spring Boot 自动根据依赖注入正确实现，零配置开箱即用
- **统一入口**：无论工具来自本地还是远程，调用方无感知

**缺点**：
- **黑盒**：不知道注入的是 `SyncMcpToolCallbackProvider` 还是其他实现
- **阻塞隐患**：MCP 实现内部有 `.block()`，在 WebFlux reactor 线程中直接调用会抛异常
- **调试困难**：工具列表在运行时动态获取，启动期无法验证

### `MethodToolCallbackProvider`（显式构建）

**优点**：
- **启动期强校验**：构造时即验证 `@Tool` 方法存在性和名称唯一性，失败早暴露
- **无网络依赖**：纯本地反射，无 I/O 阻塞风险
- **精确控制**：可合并多个 Service、自定义结果转换器
- **类型安全**：编译期确定是本地方法工具，不会误注入 MCP 实现

**缺点**：
- **每次反射**：`getToolCallbacks()` 每次调用都重新遍历方法（虽然开销可控）
- **仅限本地**：无法消费远程 MCP 工具
- **需手动构建**：不能像 MCP 那样自动发现

---

## 8. 常见陷阱与最佳实践

### 陷阱 1：WebFlux + `ToolCallbackProvider` = 阻塞异常

```java
// WebFlux 环境下，这段代码会抛 IllegalStateException
chatClient.prompt().toolCallbacks(toolCallbackProvider).stream().content();
```

**根因**：`SyncMcpToolCallbackProvider.getToolCallbacks()` -> `McpSyncClient.listTools()` 内部调用了 `.block()`。

**解决方案**：将项目从 WebFlux 迁移到 Spring MVC。

### 陷阱 2：混淆 `.tools()` 与 `.toolCallbacks()`

```java
// 错误：MethodToolCallbackProvider 不能传给 .tools()
chatClient.prompt().tools(toolCallbackProvider);

// 正确：Provider 用 .toolCallbacks()，原始 @Tool 对象才用 .tools()
chatClient.prompt().toolCallbacks(toolCallbackProvider);
```

---

## 9. 选型决策树

```
需要暴露本地 @Tool 方法？
├── 是 → 使用 MethodToolCallbackProvider.builder().toolObjects(service)
│        （或 ToolCallbacks.from(service) 简化版）
└── 否 → 需要消费远程 MCP 工具？
         ├── 是 → 依赖 spring-ai-starter-mcp-client
         │        注入 ToolCallbackProvider（自动配置注入 SyncMcpToolCallbackProvider）
         │        ⚠️ 若用 WebFlux，需在 @PostConstruct 预加载或切到 Spring MVC
         └── 否 → 有预构建的 ToolCallback 实例？
                  ├── 是 → 直接传数组，或用 StaticToolCallbackProvider
                  └── 否 → 无需工具调用
```

---

## 10. 总结

`ToolCallbackProvider` 与 `MethodToolCallbackProvider` 不是简单的"接口与实现"关系，而是代表了 **两种完全不同的工具发现哲学**：
- **`MethodToolCallbackProvider`** 是**生产者视角**：你拥有代码，通过反射将方法暴露给大模型。它强调的是**编译期确定、启动期验证、零网络依赖**。
- **`ToolCallbackProvider`（MCP 实现）** 是**消费者视角**：你并不拥有工具的实现，而是通过协议动态发现远程服务。它强调的是**运行时解耦、自动发现、协议无关**。

在实际项目中，MCP Server 端写 `MethodToolCallbackProvider`，MCP Client 端接 `ToolCallbackProvider`，两者配合构成完整的工具生态。理解这层分界，才能在 Spring AI 的工具链路上做出正确的架构选择。
