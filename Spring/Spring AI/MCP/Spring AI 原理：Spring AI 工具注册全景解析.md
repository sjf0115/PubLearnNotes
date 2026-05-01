
## 1. 从一个代码差异说起

同一个 Spring AI MCP 项目中，Server 端和 Client 端的工具注入写法截然不同：

```java
// MCP Server：暴露本地工具
@Autowired
private MethodToolCallbackProvider toolCallbackProvider;

// MCP Client：消费远程工具
@Autowired
private ToolCallbackProvider toolCallbackProvider;
```

两者都能通过 `.getToolCallbacks()` 获取工具列表，但背后的实现逻辑天差地别。这个差异引出了 Spring AI 工具生态的核心设计—— **`ToolCallbackProvider` 接口及其四大实现类**。

---

## 2. `ToolCallbackProvider` 接口定位

`ToolCallbackProvider` 是 Spring AI 工具链的顶层契约：
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

它的设计意图是 **解耦工具的来源与消费**。`ChatClient` 不关心工具是本地方法、远程 MCP 服务还是静态实例，只需要通过统一接口获取 `ToolCallback[]`。Spring AI 1.1.5 中，这个接口有四大家族成员。

---

## 3. 四大实现详解

### 3.1 MethodToolCallbackProvider：本地方法的反射工厂

**职责**：扫描对象中的 `@Tool` 注解方法，包装为 `MethodToolCallback`。

**构建方式**：
```java
@Bean
public MethodToolCallbackProvider weatherTools(WeatherService service) {
    return MethodToolCallbackProvider.builder()
            .toolObjects(service)
            .build();
}
```

**核心源码**：
```
public ToolCallback[] getToolCallbacks() {
    return this.toolObjects.stream()
        .map(toolObject -> Stream.of(ReflectionUtils.getDeclaredMethods(
                AopUtils.isAopProxy(toolObject)
                    ? AopUtils.getTargetClass(toolObject)  // 解包 Spring 代理
                    : toolObject.getClass()))
            .filter(this::isToolAnnotatedMethod)           // 筛选 @Tool
            .map(toolMethod -> MethodToolCallback.builder()
                .toolDefinition(ToolDefinitions.from(toolMethod))
                .toolMethod(toolMethod)
                .toolObject(toolObject)                    // 绑定调用目标
                .build())
            .toArray(ToolCallback[]::new))
        .flatMap(Stream::of)
        .toArray(ToolCallback[]::new);
}
```

**关键特性**：
- 构造阶段强制校验：必须存在 `@Tool` 方法，且工具名不能重复
- 兼容 Spring AOP 代理：通过 `AopUtils.getTargetClass()` 解包
- 无网络 I/O，纯本地反射

---

### 3.2 SyncMcpToolCallbackProvider：同步 MCP 远程发现

**职责**：通过 `McpSyncClient` 向远程 MCP Server 发起同步调用，发现可用工具。

**核心源码**：
```java
public ToolCallback[] getToolCallbacks() {
    if (this.invalidateCache) {
        this.lock.lock();
        try {
            this.cachedToolCallbacks = this.mcpClients.stream()
                .flatMap(mcpClient -> mcpClient.listTools()   // 同步网络 I/O
                    .tools()
                    .stream()
                    .map(tool -> SyncMcpToolCallback.builder()
                        .mcpClient(mcpClient)
                        .tool(tool)
                        .build()))
                .toList();
            this.invalidateCache = false;
        } finally {
            this.lock.unlock();
        }
    }
    return this.cachedToolCallbacks.toArray(new ToolCallback[0]);
}
```

**关键特性**：
- 内部使用 `McpSyncClient.listTools()`，**本质阻塞**
- 双重检查锁缓存，避免重复网络请求
- 监听 `McpToolsChangedEvent` 刷新缓存
- Spring Boot 自动配置注入（依赖 `spring-ai-starter-mcp-client`）

---

### 3.3 AsyncMcpToolCallbackProvider：异步 MCP 远程发现

**职责**：通过 `McpAsyncClient` 向远程 MCP Server 发起异步调用，但 `getToolCallbacks()` 接口仍是同步的。

**核心源码**：
```java
public ToolCallback[] getToolCallbacks() {
    if (this.invalidateCache) {
        this.lock.lock();
        try {
            for (McpAsyncClient mcpClient : this.mcpClients) {
                ToolCallback[] toolCallbacks = mcpClient.listTools()
                    .map(response -> /* 构建 AsyncMcpToolCallback */)
                    .block();  // 注意：接口同步，最终仍调 block()
                // ...
            }
        } finally {
            this.lock.unlock();
        }
    }
    return this.cachedToolCallbacks.toArray(new ToolCallback[0]);
}
```

**关键特性**：
- 使用 `McpAsyncClient` 做响应式网络调用
- 但 `ToolCallbackProvider` 接口要求同步返回，内部仍需 `.block()`
- WebFlux 环境下调用同样会触发阻塞异常
- 提供 `asyncToolCallbacks()` 静态方法返回真正的 `Flux<ToolCallback>`

---

### 3.4 StaticToolCallbackProvider：静态实例的直球选手

**职责**：直接持有预构建的 `ToolCallback` 数组，无任何动态发现逻辑。

**源码**：
```java
public class StaticToolCallbackProvider implements ToolCallbackProvider {
    private final ToolCallback[] toolCallbacks;

    public StaticToolCallbackProvider(ToolCallback... toolCallbacks) {
        this.toolCallbacks = toolCallbacks;
    }

    @Override
    public ToolCallback[] getToolCallbacks() {
        return this.toolCallbacks;  // 直接返回，零开销
    }
}
```

**使用方式**：
```java
ToolCallbackProvider provider = ToolCallbackProvider.from(callback1, callback2);
// 或
ToolCallbackProvider provider = new StaticToolCallbackProvider(callbacks);
```

**关键特性**：
- 构造时确定，运行时不变
- 线程安全（数组不可变）
- 零反射、零网络、零缓存逻辑
- `ToolCallbackProvider.from()` 静态工厂的本质

---

## 4. 四大实现全景对比

| 维度 | MethodToolCallbackProvider | SyncMcpToolCallbackProvider | AsyncMcpToolCallbackProvider | StaticToolCallbackProvider |
|------|---------------------------|----------------------------|-----------------------------|---------------------------|
| **工具来源** | 本地 `@Tool` 注解方法 | 远程 MCP Server（同步） | 远程 MCP Server（异步） | 预构建的 `ToolCallback` |
| **发现机制** | 运行时反射扫描 | `McpSyncClient.listTools()` | `McpAsyncClient.listTools()` | 无，直接持有 |
| **网络 I/O** | 无 | 有（同步阻塞） | 有（响应式 + `.block()`） | 无 |
| **缓存策略** | 无缓存，每次反射 | 双重检查锁 + Event 刷新 | 双重检查锁 + Event 刷新 | 无需缓存 |
| **AOP 兼容** | 内部解包代理 | 不涉及 | 不涉及 | 不涉及 |
| **构造方式** | 显式 `builder()` | 自动配置注入 | 自动配置注入 | 显式构造或 `ToolCallbackProvider.from()` |
| **阻塞风险** | 无 | 有（`.block()`） | 有（`.block()`） | 无 |
| **适用角色** | MCP Server | MCP Client | MCP Client | 通用 |

---

## 5. 选型指南

| 场景 | 推荐实现 | 原因 |
|------|---------|------|
| 暴露本地 Service 方法为工具 | `MethodToolCallbackProvider` | 唯一支持 `@Tool` 反射的实现 |
| 消费远程 MCP 工具（Spring MVC） | `ToolCallbackProvider`（自动注入 `SyncMcpToolCallbackProvider`） | 自动发现，线程允许阻塞 |
| 消费远程 MCP 工具（WebFlux） | **不建议直接用 Provider**，考虑 `@PostConstruct` 预加载或切到 Spring MVC | 阻塞问题难以根除 |
| 工具列表固定且已知 | `StaticToolCallbackProvider` | 最简单、零开销 |
| 需要真正响应式工具流 | 绕过 `ToolCallbackProvider`，直接用 `AsyncMcpToolCallbackProvider.asyncToolCallbacks()` | 返回 `Flux<ToolCallback>` |

---

## 6. 总结

回到开头的代码差异：
```java
@Autowired
private MethodToolCallbackProvider toolCallbackProvider;  // 你是生产者，暴露本地方法

@Autowired
private ToolCallbackProvider toolCallbackProvider;        // 你是消费者，接纳远程工具
```

`ToolCallbackProvider` 接口的优雅之处在于**统一了不同来源的工具供给方式**。但在实际选型时，必须深入理解每个实现的底层机制：`MethodToolCallbackProvider` 是纯反射的本地工厂，两个 MCP Provider 是带缓存的远程代理，而 `StaticToolCallbackProvider` 是最直接的静态容器。根据工具来源、运行时环境和性能要求选择正确的实现，才能避免 WebFlux 阻塞异常、AOP 代理失效等陷阱。
