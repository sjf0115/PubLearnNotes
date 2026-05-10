在前面文章中，我们学习了如何接入模型、使用 Hook 监控执行、构建本地工具系统。但一个企业的工具生态远不止几行 Java 代码——文件系统、数据库、Git 仓库、搜索引擎、第三方 SaaS 服务……如何让 Agent 无缝对接这些异构系统？

**MCP（Model Context Protocol，模型上下文协议）** 正是为此而生。它是 Anthropic 发起的开放标准协议，旨在让 AI 应用以统一的方式连接外部数据源和工具。AgentScope Java 对 MCP 提供了完整支持，让你的 Agent 可以一键接入整个 MCP 生态系统的工具。

---

## 1. 什么是 MCP？

**MCP（Model Context Protocol）** 是一个开放标准协议，用于将 AI 应用程序连接到外部数据源和工具。它定义了标准化的通信方式，使得：
- **工具开发者** 只需实现一次 MCP Server，即可被任意 MCP Client 使用
- **Agent 开发者** 只需连接一次 MCP Client，即可获得一整套工具能力

### MCP 的核心价值

- **统一的工具接口**：通过单个协议访问各种工具
- **外部工具服务器**：连接到专门的服务（文件系统、git、数据库等）
- **生态系统集成**：使用不断增长的 MCP 生态系统中的工具
- **灵活的传输**：支持 StdIO、SSE 和 HTTP 传输
- **语言无关**：MCP Server 可以用 Python、Node.js、Java 等任意语言实现

### MCP 工具 vs 本地工具

| 对比维度 | 本地工具（@Tool） | MCP 工具 |
|---------|----------------|---------|
| 实现位置 | 与 Agent 同进程 | 独立的 MCP Server 进程/服务 |
| 通信方式 | 直接方法调用 | StdIO / SSE / HTTP 协议 |
| 语言限制 | 必须是 Java | 任意语言 |
| 部署方式 | 随 Agent 一起部署 | 独立部署，可复用 |
| 适用场景 | 核心业务逻辑、性能敏感 | 通用能力、跨团队复用、第三方集成 |

**最佳实践**：核心业务工具用本地 `@Tool` 实现，通用能力（文件操作、Git、搜索等）通过 MCP 接入。

## 2. 快速开始

### 2.1 连接到 MCP 服务器

```java
// StdIO 传输 - 连接到本地 MCP 服务器
McpClientWrapper mcpClient = McpClientBuilder.create("filesystem-mcp")
        .stdioTransport("npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp")
        .buildAsync()
        .block();
```

### 2.2 注册 MCP 工具

```java
// 注册 MCP 服务器的所有工具
Toolkit toolkit = new Toolkit();
toolkit.registerMcpClient(mcpClient).block();
```

### 2.3 在 Agent 中配置 MCP

```java
ReActAgent agent = ReActAgent.builder()
        .name("Assistant")
        .model(model)
        .toolkit(toolkit)  // MCP 工具现已可用
        .memory(new InMemoryMemory())
        .build();
```


## 3. AgentScope 支持的三种传输方式

AgentScope Java 支持 MCP 协议的三种标准传输机制：

| 传输方式 | 通信机制 | 连接类型 | 典型场景 | 状态   |
|---------|---------|---------|---------|---------|
| **StdIO** | 标准输入输出流 | 启动子进程 | 本地 MCP Server（如 Node.js、Python 脚本） | 有状态 |
| **SSE** | HTTP Server-Sent Events | HTTP 长连接 | 远程 MCP Server（如同局域网服务） | 有状态 |
| **HTTP** | 可流式 HTTP | HTTP 请求/响应 | 无状态云服务、网关代理 | 无状态 |

| 配置方法 | 适用传输 | 说明 |
|---------|---------|------|
| `.stdioTransport(cmd, args...)` | StdIO | 启动子进程的命令和参数 |
| `.sseTransport(url)` | SSE | SSE 端点 URL |
| `.streamableHttpTransport(url)` | HTTP | 可流式 HTTP 端点 URL |
| `.header(key, value)` | SSE / HTTP | 添加 HTTP 请求头 |
| `.queryParam(key, value)` | SSE / HTTP | 添加 URL 查询参数 |
| `.queryParams(map)` | SSE / HTTP | 批量添加查询参数 |
| `.timeout(duration)` | 全部 | 单次请求超时 |
| `.initializationTimeout(duration)` | 全部 | MCP 初始化握手超时 |

### 3.1 StdIO 传输

通过启动子进程，使用标准输入输出进行通信。适合本地安装的 MCP Server（如通过 npm 或 pip 安装的官方 Server）。
```java
// 文件系统服务器
McpClientWrapper fsClient = McpClientBuilder.create("fs-mcp")
        .stdioTransport("npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp")
        .buildAsync()
        .block();

// Git 服务器
McpClientWrapper gitClient = McpClientBuilder.create("git-mcp")
        .stdioTransport("python", "-m", "mcp_server_git")
        .buildAsync()
        .block();

// 自定义命令
McpClientWrapper customClient = McpClientBuilder.create("custom-mcp")
        .stdioTransport("/path/to/executable", "arg1", "arg2")
        .buildAsync()
        .block();
```
**原理**：以 `fsClient` 为例说明，AgentScope 启动 `npx -y @modelcontextprotocol/server-filesystem /tmp` 子进程，通过 stdin/stdout 与 Server 交换 JSON-RPC 消息。

### 3.2 SSE 传输

通过 HTTP Server-Sent Events 建立长连接，适合部署在局域网或云上的 MCP Server：
```java
McpClientWrapper sseClient = McpClientBuilder.create("remote-mcp")
        .sseTransport("https://mcp.example.com/sse")
        .header("Authorization", "Bearer " + apiToken)
        .buildAsync()
        .block();
```
**原理**：Client 先向 `/sse` 端点建立 SSE 连接接收消息，再通过 POST 请求发送消息。

### 3.3 HTTP 传输

基于可流式 HTTP 的请求/响应模式，适合无状态的云服务和网关代理：
```java
McpClientWrapper httpClient = McpClientBuilder.create("http-mcp")
        .streamableHttpTransport("https://mcp.example.com/http")
        .header("X-API-Key", apiKey)
        .buildAsync()
        .block();
```


## 4. 配置选项

### 4.1 超时设置

```java
import java.time.Duration;

McpClientWrapper client = McpClientBuilder.create("mcp")
        .stdioTransport("npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp")
        .timeout(Duration.ofSeconds(120))      // 请求超时
        .initializationTimeout(Duration.ofSeconds(30)) // 初始化超时
        .buildAsync()
        .block();
```

### 4.2 HTTP 头

```java
McpClientWrapper client = McpClientBuilder.create("mcp")
        .sseTransport("https://mcp.example.com/sse")
        .header("Authorization", "Bearer " + token)
        .header("X-Client-Version", "1.0")
        .header("X-Custom-Header", "value")
        .buildAsync()
        .block();
```

### 4.3 Query 参数

为 HTTP 传输添加 URL 查询参数：

```java
// 单个参数
McpClientWrapper client = McpClientBuilder.create("mcp")
        .sseTransport("https://mcp.example.com/sse")
        .queryParam("queryKey1", "queryValue1")
        .queryParam("queryKey2", "queryValue2")
        .buildAsync()
        .block();

// 批量参数
McpClientWrapper client = McpClientBuilder.create("mcp")
        .streamableHttpTransport("https://mcp.example.com/http")
        .queryParams(Map.of("queryKey1", "queryValue1", "queryKey2", "queryValue2"))
        .buildAsync()
        .block();

// 与 URL 中已有参数合并（额外参数优先）
McpClientWrapper client = McpClientBuilder.create("mcp")
        .sseTransport("https://mcp.example.com/sse?version=v1")
        .queryParam("queryKey", "queryValue")  // 最终: ?version=v1&queryKey=queryValue
        .buildAsync()
        .block();
```

> **注意**：Query 参数和 HTTP 头仅对 HTTP 传输（SSE 和 HTTP）有效，对 StdIO 传输会被静默忽略。

### 4.4 同步 vs 异步客户端

AgentScope 支持两种 MCP 客户端构建方式：

| 特性 | 异步客户端 | 同步客户端 |
|------|-----------|-----------|
| 构建方法 | `.buildAsync()` | `.buildSync()` |
| 返回值 | `Mono<McpClientWrapper>` | `McpClientWrapper` |
| 适用场景 | 生产环境、Web 应用 | 脚本、测试、命令行工具 |
| 阻塞性 | 非阻塞（需 `.block()` 订阅） | 阻塞 |

#### 4.4.1 异步客户端（推荐）

基于 Project Reactor，非阻塞，适合高并发场景：
```java
McpClientWrapper asyncClient = McpClientBuilder.create("async-mcp")
        .stdioTransport("npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp")
        .buildAsync()
        .block();  // 阻塞等待连接建立
```

### 4.4.2 同步客户端

阻塞式，适合简单的脚本场景：
```java
// 同步客户端（用于阻塞操作）
McpClientWrapper syncClient = McpClientBuilder.create("sync-mcp")
        .stdioTransport("npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp")
        .buildSync();
```

### 4.5 elicitation 支持

MCP 的 elicitation 功能允许在调用工具过程中，向用户发起交互式信息收集请求。这在工具需要额外确认或补充参数时非常有用。

### 7.1 异步 Elicitation

```java
McpClientWrapper client = McpClientBuilder.create("mcp-async")
        .stdioTransport("python", "-m", "mcp_server")
        .asyncElicitation(request -> {
            // 处理 elicitation 请求
            System.out.println("收到补充请求: " + request.message());

            // 返回用户输入
            return Mono.just(ElicitResult.builder()
                    .action(ElicitResult.Action.ACCEPT)
                    .data(Map.of("response", "用户补充的信息"))
                    .build());
        })
        .buildAsync()
        .block();
```

### 7.2 同步 Elicitation

```java
McpClientWrapper client = McpClientBuilder.create("mcp-sync")
        .stdioTransport("python", "-m", "mcp_server")
        .syncElicitation(request -> {
            System.out.print("需要补充信息 [" + request.message() + "]: ");
            String input = new Scanner(System.in).nextLine();

            return ElicitResult.builder()
                    .action(ElicitResult.Action.ACCEPT)
                    .data(Map.of("response", input))
                    .build();
        })
        .buildSync();
```

**应用场景**：
- 文件删除前需要用户确认
- 数据库查询缺少必要参数，需要追问用户
- 敏感操作需要二次认证

## 5. 高级特性

### 5.1 工具过滤

MCP Server 通常会暴露大量工具，但 Agent 并不需要全部使用。AgentScope 提供了精细的工具控制能力。

#### 5.1.1 启用特定工具（白名单）

```java
// 仅启用特定工具
List<String> enableTools = List.of("read_file", "write_file", "list_directory");

toolkit.registration()
        .mcpClient(mcpClient)
        .enableTools(enableTools)  // 仅注册白名单中的工具
        .apply();
```

#### 5.1.2 禁用特定工具（黑名单）

```java
// 启用除黑名单外的所有工具
List<String> disableTools = List.of("delete_file", "move_file");

toolkit.registration()
        .mcpClient(mcpClient)
        .disableTools(disableTools)  // 注册除黑名单外的所有工具
        .apply();
```

#### 5.1.3 同时使用启用和禁用（白名单 + 黑名单组合）

```java
// 白名单与黑名单结合
List<String> enableTools = List.of("read_file", "write_file", "list_directory", "delete_file");
List<String> disableTools = List.of("delete_file");  // 最终 delete_file 仍被禁用

toolkit.registration()
        .mcpClient(mcpClient)
        .enableTools(enableTools)
        .disableTools(disableTools)
        .apply();
```

> 优先级：`disableTools` > `enableTools`。即使工具在白名单中，如果在黑名单中也会被排除。



### 5.2 工具组

将 MCP 工具分配到组以进行选择性激活：

```java
// 创建工具组并激活
Toolkit toolkit = new Toolkit();
String groupName = "filesystem";
toolkit.createToolGroup(groupName, "Tools for operating system files", true);

// 将 MCP 工具注册到指定组
toolkit.registration()
        .mcpClient(mcpClient)
        .group("filesystem")
        .apply();

// 创建使用工具包的智能体（仅 active 组中的工具可用）
ReActAgent agent = ReActAgent.builder()
        .name("Assistant")
        .model(model)
        .toolkit(toolkit)
        .build();

// 后续可动态控制
toolkit.updateToolGroups(List.of("filesystem"), false);  // 停用
```

### 5.3 管理 MCP 客户端

#### 5.3.1 列出 MCP 服务器的工具

```java
// 注册后，工具会出现在工具包中
Set<String> toolNames = toolkit.getToolNames();
System.out.println("可用工具: " + toolNames);
```

#### 5.3.2 移除 MCP 客户端

```java
// 移除 MCP 客户端及其所有工具
toolkit.removeMcpClient("filesystem-mcp").block();
```

---

## 6. 实战：多 MCP Server 组合使用

以下示例展示如何同时接入文件系统和 Git 两个 MCP Server：

```java
public class MultiMcpAgentDemo {
    public static void main(String[] args) {
        Toolkit toolkit = new Toolkit();

        // 1. 连接文件系统 MCP Server
        McpClientWrapper fsClient = McpClientBuilder.create("fs-mcp")
                .stdioTransport("npx", "-y",
                        "@modelcontextprotocol/server-filesystem",
                        "/home/user/projects")
                .buildAsync()
                .block();

        // 2. 连接 Git MCP Server
        McpClientWrapper gitClient = McpClientBuilder.create("git-mcp")
                .stdioTransport("python", "-m", "mcp_server_git")
                .buildAsync()
                .block();

        // 3. 注册文件系统工具（只读）
        toolkit.registration()
                .mcpClient(fsClient)
                .enableTools(List.of("read_file", "list_directory"))
                .group("filesystem")
                .apply();

        // 4. 注册 Git 工具（排除危险操作）
        toolkit.registration()
                .mcpClient(gitClient)
                .disableTools(List.of("git_reset", "git_clean"))
                .group("git")
                .apply();

        // 5. 创建 Agent
        ReActAgent agent = ReActAgent.builder()
                .name("DevAssistant")
                .sysPrompt("你是开发助手，可以帮助用户查看代码和 Git 历史。")
                .model(DashScopeChatModel.builder()
                        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                        .modelName("qwen3.6-plus")
                        .build())
                .toolkit(toolkit)
                .maxIters(10)
                .build();

        // 6. 调用
        Msg response = agent.call(
                Msg.builder()
                        .role(MsgRole.USER)
                        .textContent("查看最近 3 次 Git 提交，并读取最新提交修改的文件内容")
                        .build()
        ).block();

        System.out.println(response.getTextContent());
    }
}
```

---

## 7. MCP 与本地工具对比选型

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| 核心业务逻辑（订单、支付） | 本地 `@Tool` | 性能高、可控性强、与业务代码紧密集成 |
| 文件系统操作 | MCP (filesystem-server) | 社区已有成熟实现，安全沙箱控制 |
| Git 操作 | MCP (git-server) | 复用社区工具，专注业务逻辑 |
| 数据库查询 | 本地 `@Tool` + 连接池 | 需要事务控制、性能优化 |
| 搜索引擎 | MCP / 本地均可 | 根据是否有现成 MCP Server 决定 |
| 第三方 SaaS（Slack、Notion） | MCP | 社区已有对应 MCP Server |
| 需要精确控制的敏感操作 | 本地 `@Tool` + Hook 审批 | 安全可控，便于审计 |

---

## 8. 最佳实践

### 8.1 传输方式选择

| 场景 | 推荐传输 | 原因 |
|------|---------|------|
| 本地 Node.js/Python MCP Server | StdIO | 简单直接，无需网络配置 |
| 局域网内的 MCP Server | SSE | 长连接，实时性好 |
| 云端无状态 MCP 服务 | HTTP | 易扩展，适合负载均衡 |
| 通过网关访问多个 Server | HTTP (Higress) | 统一入口，语义路由 |

### 8.2 安全建议

```java
// 1. 始终过滤危险工具
toolkit.registration()
        .mcpClient(mcpClient)
        .disableTools(List.of("delete_file", "exec_command", "git_reset"))
        .apply();

// 2. 文件系统 Server 限制访问范围
.stdioTransport("npx", "-y",
        "@modelcontextprotocol/server-filesystem",
        "/safe/workspace")  // 限制根目录

// 3. HTTP 传输使用 HTTPS 和认证
.sseTransport("https://mcp.example.com/sse")
.header("Authorization", "Bearer " + token)
```

### 8.3 性能优化

- **超时控制**：根据工具特性设置合理的超时，避免长时间挂起
- **工具过滤**：只注册 Agent 需要的工具，减少 LLM 决策负担
- **连接复用**：MCP Client 连接可复用，避免频繁创建和销毁

---

## 9. 总结

| 要点 | 内容 |
|------|------|
| **核心类** | `McpClientBuilder`、`McpClientWrapper` |
| **传输方式** | StdIO（本地进程）、SSE（HTTP 长连接）、HTTP（无状态） |
| **工具注册** | `toolkit.registerMcpClient(client)` 或 `toolkit.registration().mcpClient(client).enableTools().apply()` |
| **工具过滤** | `enableTools()` 白名单、`disableTools()` 黑名单 |
| **工具组** | 支持将 MCP 工具分配到组，动态激活/停用 |
| **高级特性** | 同步/异步客户端、elicitation 交互、Higress 网关 |
| **生命周期** | `toolkit.removeMcpClient(name)` 清理连接 |

MCP 让 AgentScope Java 的 Agent 不再受限于本地代码，而是可以接入整个开放的工具生态系统。配合本地 `@Tool` 使用，既能保持核心业务的可控性，又能享受社区生态的便利性。

---
