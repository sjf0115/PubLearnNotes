在前面的文章中，我们学习了如何接入大语言模型、使用 [Tool 工具系统](https://smartsi.blog.csdn.net/article/details/161324334)让 Agent "动手做事"。但一个企业的工具生态远不止几行 Java 代码——文件系统、数据库、Git 仓库、搜索引擎、第三方 SaaS 服务……如何让 Agent 无缝对接这些异构系统？

**MCP（Model Context Protocol，模型上下文协议）** 正是为此而生。它是 Anthropic 发起的开放标准协议，旨在让 AI 应用以统一的方式连接外部数据源和工具。AgentScope Java 对 MCP 提供了完整支持，让你的 Agent 可以一键接入整个 MCP 生态系统。

如果说 Tool 系统让 Agent 长出了"手脚"，那么 MCP 就是把 Agent 接入了 **全球工具生态网络**——你不再需要为每个外部系统单独编写工具，而是直接复用社区数百个已有的 MCP Server。

---

## 1. 什么是 MCP？

> 关于 MCP 的详细信息请查阅 [MCP 入门：什么是 MCP 模型上下文协议](https://smartsi.blog.csdn.net/article/details/158430845)

### 1.1 协议定位

**MCP（Model Context Protocol）** 是一个开放标准协议，用于将 AI 应用程序与外部数据源、工具进行连接。可以把它类比为：

| 类比 | 解决的问题 |
|------|---------|
| AI 世界的 **USB 接口** | 任何 MCP Server 都能被任何 MCP Client 即插即用 |
| AI 工具的 **Maven 仓库** | 工具开发一次，全球 AI 应用复用 |
| AI 应用的 **HTTP 协议** | 标准化的通信，跨语言、跨平台 |

### 1.2 核心价值

- **统一的工具接口**：通过单个协议访问各种工具
- **外部工具服务器**：连接到专门的服务（文件系统、Git、数据库等）
- **生态系统集成**：使用不断增长的 MCP 生态系统中的工具
- **灵活的传输**：支持 StdIO、SSE 和 HTTP 传输
- **语言无关**：MCP Server 可以用 Python、Node.js、Java 等任意语言实现

### 1.3 MCP 工具 vs 本地 @Tool

| 对比维度 | 本地 `@Tool` | MCP 工具 |
|---------|----------------|---------|
| 实现位置 | 与 Agent 同进程 | 独立的 MCP Server 进程 / 服务 |
| 通信方式 | 直接方法调用 | StdIO / SSE / HTTP 协议 |
| 语言限制 | 必须是 Java | 任意语言（Python、Node.js、Go……） |
| 部署方式 | 随 Agent 一起部署 | 独立部署，可复用 |
| 性能开销 | 极低（方法调用） | 有 IPC / 网络开销 |
| 生态规模 | 项目内自研 | 社区数百个开源 MCP Server |
| 适用场景 | 核心业务逻辑、性能敏感 | 通用能力、跨团队复用、第三方集成 |

> **最佳实践**：核心业务工具用本地 `@Tool` 实现，通用能力（文件操作、Git、搜索等）通过 MCP 接入。**两者并存，各司其职**。

## 2. 快速开始

> 三步接入 MCP

### 2.1 连接到 MCP 服务器

```java
// StdIO 传输 - 连接到本地 MCP 服务器
McpClientWrapper fsClient = McpClientBuilder.create("fs-mcp")
        .stdioTransport("npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp")
        .buildAsync()
        .block();
```

### 2.2 注册 MCP 工具

```java
// 注册 MCP 服务器的所有工具
Toolkit toolkit = new Toolkit();
toolkit.registerMcpClient(fsClient).block();
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

仅需 3 步，Agent 就拥有了 MCP Server 提供的所有工具能力——这就是协议标准化带来的红利。

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


示例：
```java
// 1. 准备沙箱工作目录，MCP filesystem server 只能在该目录内读写
Path workspace = Paths.get("agentscope/quickstart/target/mcp-fs-workspace")
        .toAbsolutePath().normalize();
Files.createDirectories(workspace);
String baseDir = workspace.toString();

// 2. 通过 stdio 启动 MCP filesystem server
//    npx 会拉起一个子进程，AgentScope 通过标准输入输出与其通信
McpClientWrapper fsClient = McpClientBuilder.create("fs-mcp")
        .stdioTransport("npx", "-y", "@modelcontextprotocol/server-filesystem", baseDir)
        .buildAsync()
        .block();

try {
    // 3. 把 MCP server 暴露的所有工具一次性注册到 Toolkit
    //    registerMcpClient 内部会调用 listTools 并把每个工具适配为 AgentTool
    Toolkit toolkit = new Toolkit();
    toolkit.registerMcpClient(fsClient).block();

    // 4. 创建 Agent，绑定 toolkit
    ReActAgent agent = ReActAgent.builder()
            .name("文件助手")
            .sysPrompt("你是一个文件操作助手，并把最终结果用一句话告知用户。")
            .model(DashScopeChatModel.builder()
                    .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                    .modelName(MODEL_NAME)
                    .build())
            .toolkit(toolkit)
            .build();

    // 5. 调用智能体：组合任务（预计触发 write → list → read 三次 MCP 工具调用）
    Msg msg = Msg.builder()
            .role(MsgRole.USER)
            .textContent("把《Hello MCP，来自 AgentScope》写入 mcp-demo.txt，"
                    + "再列出当前目录下的所有文件，最后读取 mcp-demo.txt 的内容返回给我。")
            .build();

    Msg response = agent.call(msg).block();
    if (response != null) {
        System.out.println("助手: " + response.getTextContent());
    }
} finally {
    // 6. 关闭 MCP 客户端，停止 npx 子进程
    if (fsClient != null) {
        fsClient.close();
    }
}
```
效果输出如下所示：
```java
[main] INFO io.agentscope.core.tool.McpClientManager - Registering MCP client: fs-mcp
[main] INFO io.agentscope.core.tool.mcp.McpAsyncClientWrapper - Initializing MCP async client: fs-mcp
[boundedElastic-1] INFO io.modelcontextprotocol.client.transport.StdioClientTransport - MCP server starting.
[boundedElastic-1] INFO io.modelcontextprotocol.client.transport.StdioClientTransport - MCP server started
[pool-4-thread-1] INFO io.modelcontextprotocol.client.transport.StdioClientTransport - STDERR Message received: Secure MCP Filesystem Server running on stdio
[pool-1-thread-1] INFO io.modelcontextprotocol.client.LifecycleInitializer - Server response with Protocol: 2024-11-05, Capabilities: ServerCapabilities[completions=null, experimental=null, logging=null, prompts=null, resources=null, tools=ToolCapabilities[listChanged=true]], Info: Implementation[name=secure-filesystem-server, title=null, version=0.2.0] and Instructions null
[pool-4-thread-1] INFO io.modelcontextprotocol.client.transport.StdioClientTransport - STDERR Message received: Client does not support MCP Roots, using allowed directories set from server args: [
[pool-4-thread-1] INFO io.modelcontextprotocol.client.transport.StdioClientTransport - STDERR Message received:   '/Users/smartsi/学习/Code/spring-ai-example/agentscope/quickstart/target/mcp-fs-workspace'
[pool-4-thread-1] INFO io.modelcontextprotocol.client.transport.StdioClientTransport - STDERR Message received: ]
[pool-1-thread-1] INFO io.agentscope.core.tool.Toolkit - Registered tool 'read_file' in group 'ungrouped'
[pool-1-thread-1] INFO io.agentscope.core.tool.Toolkit - Registered tool 'read_text_file' in group 'ungrouped'
[pool-1-thread-1] INFO io.agentscope.core.tool.Toolkit - Registered tool 'read_media_file' in group 'ungrouped'
[pool-1-thread-1] INFO io.agentscope.core.tool.Toolkit - Registered tool 'read_multiple_files' in group 'ungrouped'
[pool-1-thread-1] INFO io.agentscope.core.tool.Toolkit - Registered tool 'write_file' in group 'ungrouped'
[pool-1-thread-1] INFO io.agentscope.core.tool.Toolkit - Registered tool 'edit_file' in group 'ungrouped'
[pool-1-thread-1] INFO io.agentscope.core.tool.Toolkit - Registered tool 'create_directory' in group 'ungrouped'
[pool-1-thread-1] INFO io.agentscope.core.tool.Toolkit - Registered tool 'list_directory' in group 'ungrouped'
[pool-1-thread-1] INFO io.agentscope.core.tool.Toolkit - Registered tool 'list_directory_with_sizes' in group 'ungrouped'
[pool-1-thread-1] INFO io.agentscope.core.tool.Toolkit - Registered tool 'directory_tree' in group 'ungrouped'
[pool-1-thread-1] INFO io.agentscope.core.tool.Toolkit - Registered tool 'move_file' in group 'ungrouped'
[pool-1-thread-1] INFO io.agentscope.core.tool.Toolkit - Registered tool 'search_files' in group 'ungrouped'
[pool-1-thread-1] INFO io.agentscope.core.tool.Toolkit - Registered tool 'get_file_info' in group 'ungrouped'
[pool-1-thread-1] INFO io.agentscope.core.tool.Toolkit - Registered tool 'list_allowed_directories' in group 'ungrouped'
[pool-1-thread-1] INFO io.agentscope.core.tool.McpClientManager - MCP client 'fs-mcp' registered successfully
助手: 文件 `mcp-demo.txt` 已成功写入内容，当前目录下包含该文件，其内容为：“Hello MCP，来自 AgentScope”。
[main] INFO io.agentscope.core.tool.mcp.McpAsyncClientWrapper - Closing MCP async client: fs-mcp
[ForkJoinPool.commonPool-worker-1] WARN io.modelcontextprotocol.client.transport.StdioClientTransport - Process terminated with code 143
[agentscope-jvm-shutdown-hook] INFO io.agentscope.core.shutdown.GracefulShutdownManager - Graceful shutdown initiated, 0 active request(s), timeout=infinite
[agentscope-jvm-shutdown-hook] INFO io.agentscope.core.model.transport.HttpTransportFactory - Shutting down 1 managed HttpTransport(s)
```

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
McpClientWrapper fsClient = McpClientBuilder.create("fs-mcp")
    .stdioTransport("npx", "-y", "@modelcontextprotocol/server-filesystem", baseDir)
    .timeout(Duration.ofSeconds(120))      // 请求超时
    .initializationTimeout(Duration.ofSeconds(30)) // 初始化超时
    .buildAsync()
    .block();
```

| 配置项 | 作用 | 推荐值 |
|------|------|------|
| `timeout` | 单次工具调用的超时时间 | 30 ~ 120 秒 |
| `initializationTimeout` | 连接建立 + 协议握手超时 | 10 ~ 30 秒 |

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

异步客户端（推荐）基于 Project Reactor，非阻塞，适合高并发场景：
```java
McpClientWrapper asyncClient = McpClientBuilder.create("async-mcp")
        .stdioTransport("npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp")
        .buildAsync()
        .block();  // 阻塞等待连接建立
```

同步客户端是阻塞式的，适合简单的脚本场景：
```java
// 同步客户端（用于阻塞操作）
McpClientWrapper syncClient = McpClientBuilder.create("sync-mcp")
        .stdioTransport("npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp")
        .buildSync();
```

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

完整示例：
```java
// 1. 准备沙箱目录
Path workspace = Paths.get("agentscope/quickstart/target/mcp-fs-workspace")
        .toAbsolutePath().normalize();
Files.createDirectories(workspace);
String baseDir = workspace.toString();

// 2. 启动 MCP filesystem server（stdio）
McpClientWrapper fsClient = McpClientBuilder.create("fs-mcp")
        .stdioTransport("npx", "-y", "@modelcontextprotocol/server-filesystem", baseDir)
        .buildAsync()
        .block();

try {
    // 白名单与黑名单结合
    //    enableTools  ：声明哪些 MCP 工具会被注册（不在列表中的工具直接被忽略）
    //    disableTools ：在白名单的基础上再屏蔽（最终对 LLM 不可见）
    //    delete_file 同时出现在白/黑名单 → 最终仍被禁用（黑名单优先级更高）
    //    list_allowed_directories "自我发现"机制，给 LLM 用来回答"我能在哪些目录里操作"的，解决了相对路径问题
    List<String> enableTools = List.of("read_file", "write_file", "list_directory", "list_allowed_directories", "delete_file");
    List<String> disableTools = List.of("delete_file");

    // 4. 使用 Toolkit#registration() DSL 一次性完成「注册 MCP 客户端 + 白/黑名单过滤」
    Toolkit toolkit = new Toolkit();
    toolkit.registration()
            .mcpClient(fsClient)
            .enableTools(enableTools)
            .disableTools(disableTools)
            .apply();

    // 5. 打印最终对 LLM 可见的工具集，验证过滤效果：
    //    预期 → [read_file, write_file, list_directory]，delete_file 被剔除
    System.out.println("===== 过滤后对 LLM 可见的工具 =====");
    toolkit.getToolNames().forEach(name -> System.out.println("  - " + name));

    // 6. 创建 Agent，绑定过滤后的 toolkit
    ReActAgent agent = ReActAgent.builder()
            .name("文件助手")
            .sysPrompt("你是一个文件操作助手，并把最终结果用一句话告知用户。")
            .model(DashScopeChatModel.builder()
                    .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                    .modelName(MODEL_NAME)
                    .build())
            .toolkit(toolkit)
            .build();

    // 7. 调用智能体：组合任务（预计触发 write_file → list_directory → read_file）
    Msg msg = Msg.builder()
            .role(MsgRole.USER)
            .textContent("把《Hello MCP，来自 AgentScope》写入 mcp-demo.txt，"
                    + "再列出当前目录下的所有文件，最后读取 mcp-demo.txt 的内容返回给我。")
            .build();

    Msg response = agent.call(msg).block();
    if (response != null) {
        System.out.println("\n助手: " + response.getTextContent());
    }
} finally {
    if (fsClient != null) {
        fsClient.close();
    }
}
```

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

列出 MCP 服务器的工具：
```java
// 注册后，工具会出现在工具包中
Set<String> toolNames = toolkit.getToolNames();
System.out.println("可用工具: " + toolNames);
```

移除 MCP 客户端：
```java
// 移除 MCP 客户端及其所有工具
toolkit.removeMcpClient("filesystem-mcp").block();
```

---

## 6. 实战：本地 + 远程混合传输的多 MCP Server Agent

### 6.1 实战目标与架构

前面的示例都只接入了单个 MCP Server。真实场景中，Agent 往往需要同时使用多种来源的工具：本地文件操作、远程知识检索、数据库查询等。本实战让一个 ReActAgent 同时接入两条不同的传输链路：

| MCP Server | 传输方式 | 提供的能力 | 工具组 |
|-----------|---------|-----------|--------|
| `@modelcontextprotocol/server-filesystem` | 本地 StdIO（npx 拉起子进程） | 沙箱目录内读写文件 | `filesystem` |
| DeepWiki MCP（`https://mcp.deepwiki.com/mcp`） | 远程 Streamable HTTP（连接已在线服务） | 公开 GitHub 仓库问答 | `wiki` |

给 Agent 下达一个必须跨两个 Server 才能完成的任务：

> 先用 DeepWiki 查询 `spring-projects/spring-ai` 仓库中 ChatClient 的用途，再把结论写入沙箱目录的 `notes/spring-ai-chatclient.md`，最后读回文件内容验证。

这个任务链（检索 → 沉淀 → 验证）覆盖了三个关键能力点：
1. **混合传输共存**：StdIO 子进程与 HTTP 远程服务注册进同一个 Toolkit；
2. **工具组隔离**：不同来源的工具分属不同组，便于按需激活/停用；
3. **白名单收敛**：filesystem server 暴露十多个工具，只放行读写查相关的几个，`edit_file`/`move_file` 等危险工具不进入 LLM 视野。

### 6.2 完整代码

```java
public class MixedTransportMcpExample {

    public static void main(String[] args) throws IOException {
        // 1. 准备沙箱工作目录，filesystem server 只能在该目录内读写
        Path workspace = Paths.get("agentscope/quickstart/target/mcp-fs-workspace")
                .toAbsolutePath().normalize();
        Files.createDirectories(workspace);
        String baseDir = workspace.toString();

        // 2. 本地 StdIO：拉起 filesystem MCP Server 子进程
        McpClientWrapper fsClient = McpClientBuilder.create("fs-mcp")
                .stdioTransport("npx", "-y", "@modelcontextprotocol/server-filesystem", baseDir)
                .timeout(Duration.ofSeconds(120))                  // 单次工具调用超时
                .initializationTimeout(Duration.ofSeconds(30))     // 连接 + 握手超时
                .buildAsync()
                .block();

        // 3. 远程 Streamable HTTP：连接已在线的 DeepWiki MCP Server（不启动任何子进程）
        McpClientWrapper wikiClient = McpClientBuilder.create("deepwiki-http")
                .streamableHttpTransport("https://mcp.deepwiki.com/mcp")
                .timeout(Duration.ofSeconds(120))
                .initializationTimeout(Duration.ofSeconds(30))
                .buildAsync()
                .block();

        try {
            // 4. 创建两个工具组，把不同来源的工具隔离开
            Toolkit toolkit = new Toolkit();
            toolkit.createToolGroup("filesystem", "本地沙箱目录的文件读写工具", true);
            toolkit.createToolGroup("wiki", "公开仓库 Wiki 问答工具", true);

            // 5. filesystem：白名单收敛，只保留读写/建目录/列目录/允许目录查询，
            //    edit_file、move_file 等危险工具不注册，LLM 根本看不到
            toolkit.registration()
                    .mcpClient(fsClient)
                    .enableTools(List.of("read_file", "write_file", "create_directory",
                            "list_directory", "list_allowed_directories"))
                    .group("filesystem")
                    .apply();

            // 6. DeepWiki：全量注册（其工具本身都是只读问答类，无危险操作）
            toolkit.registration()
                    .mcpClient(wikiClient)
                    .group("wiki")
                    .apply();

            // 7. 打印最终对 LLM 可见的工具集，验证分组与过滤效果
            System.out.println("===== 对 LLM 可见的工具 =====");
            toolkit.getToolNames().forEach(name -> System.out.println("  - " + name));

            // 8. 创建 Agent，绑定聚合了两个 Server 工具的 toolkit
            ReActAgent agent = ReActAgent.builder()
                    .name("研究助手")
                    .sysPrompt("你是一个研究助手：可以用 ask_question 等工具查询公开 GitHub 仓库文档，"
                            + "用 read_file/write_file 等工具在沙箱目录读写文件，"
                            + "完成任务后用一句话告知用户结果。")
                    .model(DashScopeChatModel.builder()
                            .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                            .modelName(MODEL_NAME)
                            .endpointType(EndpointType.MULTIMODAL)
                            .build())
                    .toolkit(toolkit)
                    .maxIters(10)
                    .build();

            // 9. 跨 Server 任务：wiki 检索 → 写入文件 → 读回验证
            Msg msg = Msg.builder()
                    .role(MsgRole.USER)
                    .textContent("请先查询 GitHub 仓库 spring-projects/spring-ai 中 ChatClient 是用来做什么的，"
                            + "然后把结论写入 notes/spring-ai-chatclient.md，最后读回该文件内容验证。")
                    .build();

            Msg response = agent.call(msg).block();
            if (response != null) {
                System.out.println("\n助手: " + response.getTextContent());
            }
        } finally {
            // 10. 关闭两个 MCP 客户端：停止 npx 子进程、释放 HTTP 连接
            if (fsClient != null) {
                fsClient.close();
            }
            if (wikiClient != null) {
                wikiClient.close();
            }
        }
    }
}
```

几点说明：
- **两个 client 都配置了 `timeout` / `initializationTimeout`**：StdIO 首次运行需要 npx 下载 server 包，远程 HTTP 需要完成握手，默认超时在弱网环境下容易失败；
- **`createToolGroup` 必须在 `registration().group(...)` 之前调用**，否则工具会落入 `ungrouped` 组；
- **多 Server 同名工具冲突**：不同 Server 可能暴露同名工具（如都有 `read_file`），注册后建议先用 `toolkit.getToolNames()` 检查实际工具集，必要时用白名单错开，只保留一侧的同名工具。

预期的工具调用序列（ReAct 循环三轮 tool_call）：
- `ask_question`（wiki 组）：向 DeepWiki 提问 ChatClient 的用途；
- `create_directory` + `write_file`（filesystem 组）：建 `notes/` 目录并写入结论；
- `read_file`（filesystem 组）：读回文件验证。

---

## 7. 总结

本文沿着「协议概念 → 三种传输方式 → 快速开始与配置 → 工具治理（过滤/分组）→ 混合传输实战」的路径，完整走了一遍 AgentScope Java 接入 MCP 生态的全流程。核心要点回顾：

| 要点 | 内容 |
|------|------|
| **核心类分工** | `McpClientBuilder` 构建连接、`McpClientWrapper` 封装客户端、`Toolkit` 聚合工具、`ReActAgent` 消费工具 |
| **传输选型** | StdIO：本地子进程（npx/pip 安装的 Server）；SSE：有状态长连接（部分服务已下线）；Streamable HTTP：无状态远程服务，新接入首选 |
| **客户端构建** | `buildAsync()` 返回 `Mono`（生产推荐）/ `buildSync()` 直接返回（脚本场景）；务必配置 `timeout` / `initializationTimeout` |
| **工具注册与治理** | `registerMcpClient` 全量注册；`registration()` DSL 支持 `enableTools` 白名单、`disableTools` 黑名单（优先级更高）、`group` 分组（需先 `createToolGroup`） |
| **混合传输实战** | 单 Agent 同时接入本地 StdIO + 远程 Streamable HTTP，工具组隔离 + 白名单收敛，完成跨 Server 任务编排（检索 → 沉淀 → 验证） |
| **生命周期** | `client.close()` 停止子进程/释放连接（放 try/finally）；`toolkit.removeMcpClient(name)` 运行期动态移除 |

MCP 让 AgentScope Java 的 Agent 不再受限于本地代码，而是可以接入整个开放的工具生态系统。配合本地 `@Tool` 使用，既能保持核心业务的可控性，又能享受社区生态的便利性。

---

## 系列文章导航

| 篇目 | 主题 |
|------|------|
| 一 | [AgentScope Java 入门 1：用 Java 构建生产级 AI 智能体的全新范式](https://smartsi.blog.csdn.net/article/details/158778778) |
| 二 | [AgentScope Java 入门 2：Spring AI Alibaba 与 AgentScope 的定位与区别](https://smartsi.blog.csdn.net/article/details/160955593) |
| 三 | [AgentScope Java 入门 3：如何安装 AgentScope](https://smartsi.blog.csdn.net/article/details/160694030) |
| 四 | [AgentScope Java 入门 4：搭建第一个 ReAct 智能体](https://smartsi.blog.csdn.net/article/details/161203988) |
| 五 | [AgentScope Java 入门 5：如何使用 DashScopeChatModel 集成百练模型](https://smartsi.blog.csdn.net/article/details/161300535) |
| 六 | [AgentScope Java 入门 6：如何使用 OpenAIChatModel 集成兼容 OpenAI 协议模型](https://smartsi.blog.csdn.net/article/details/161324334) |
| 七 | [AgentScope Java 入门 7：如何使用 OllamaChatModel 集成 Ollama 自托管平台](https://smartsi.blog.csdn.net/article/details/161335847) |
| 八 | [AgentScope Java 入门 8：Tool 工具系统——让 Agent 真正"动手做事"](https://smartsi.blog.csdn.net/article/details/161359990) |
