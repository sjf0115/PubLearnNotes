

### 4.2 SSE 传输

通过 HTTP Server-Sent Events 建立长连接，适合部署在局域网或云上的 MCP Server：

```java
McpClientWrapper sseClient = McpClientBuilder.create("remote-mcp")
        .sseTransport("https://mcp.example.com/sse")
        .header("Authorization", "Bearer " + apiToken)
        .buildAsync()
        .block();
```

**原理**：Client 先向 `/sse` 端点建立 SSE 连接接收消息，再通过 POST 请求发送消息。

### 4.3 HTTP 传输

基于可流式 HTTP 的请求 / 响应模式，适合无状态的云服务和网关代理：

```java
McpClientWrapper httpClient = McpClientBuilder.create("http-mcp")
        .streamableHttpTransport("https://mcp.example.com/http")
        .header("X-API-Key", apiKey)
        .buildAsync()
        .block();
```

### 4.4 如何选择？

```
本地有现成 MCP Server 二进制？  ──Yes──▶ StdIO
   │
   No
   ▼
需要长连接 + 实时双向消息？     ──Yes──▶ SSE
   │
   No
   ▼
是无状态服务 / 需经过 LB？      ──Yes──▶ HTTP
```

---





## 7. 实战：多 MCP Server 组合开发助手

以下示例展示如何同时接入文件系统和 Git 两个 MCP Server，构建一个开发助手 Agent：

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

        // 3. 注册文件系统工具（只读，安全可控）
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
                        .modelName("qwen3-max")
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

**这个示例展示了**：

| 能力 | 体现 |
|------|------|
| 多 MCP Server 协作 | 同时连接 fs-mcp 和 git-mcp |
| 白名单过滤 | 文件系统只暴露只读工具，避免误删 |
| 黑名单过滤 | Git 排除 `reset`、`clean` 等危险操作 |
| 工具组 | 按场景分组，便于动态启停 |
| 路径限制 | filesystem-server 限定根目录，沙箱安全 |

---

## 8. MCP 与本地工具选型指南

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| 核心业务逻辑（订单、支付） | 本地 `@Tool` | 性能高、可控性强、与业务代码紧密集成 |
| 文件系统操作 | MCP（filesystem-server） | 社区已有成熟实现，安全沙箱控制 |
| Git 操作 | MCP（git-server） | 复用社区工具，专注业务逻辑 |
| 数据库查询 | 本地 `@Tool` + 连接池 | 需要事务控制、性能优化 |
| 搜索引擎 | MCP / 本地均可 | 根据是否有现成 MCP Server 决定 |
| 第三方 SaaS（Slack、Notion） | MCP | 社区已有对应 MCP Server |
| 需要精确控制的敏感操作 | 本地 `@Tool` + Hook 审批 | 安全可控，便于审计 |
| 跨语言团队协作 | MCP | Server 一次开发，Java/Python/Node 多端复用 |

---

## 9. 最佳实践

### 9.1 传输方式选择

| 场景 | 推荐传输 | 原因 |
|------|---------|------|
| 本地 Node.js / Python MCP Server | StdIO | 简单直接，无需网络配置 |
| 局域网内的 MCP Server | SSE | 长连接，实时性好 |
| 云端无状态 MCP 服务 | HTTP | 易扩展，适合负载均衡 |
| 通过网关访问多个 Server | HTTP（如 Higress） | 统一入口，语义路由 |

### 9.2 安全建议

```java
// 1. 始终过滤危险工具
toolkit.registration()
        .mcpClient(mcpClient)
        .disableTools(List.of("delete_file", "exec_command", "git_reset"))
        .apply();

// 2. 文件系统 Server 限制访问范围
McpClientBuilder.create("fs-mcp")
        .stdioTransport("npx", "-y",
                "@modelcontextprotocol/server-filesystem",
                "/safe/workspace");      // 限制根目录，沙箱化

// 3. HTTP 传输使用 HTTPS 和认证
McpClientBuilder.create("remote-mcp")
        .sseTransport("https://mcp.example.com/sse")
        .header("Authorization", "Bearer " + token);
```

| 安全策略 | 实施方式 |
|---------|---------|
| 最小权限原则 | 通过 `enableTools` 精确暴露所需工具 |
| 沙箱隔离 | filesystem-server 限定根目录 |
| 网络加密 | 远程 MCP 必须 HTTPS |
| 身份认证 | 通过 `header()` 注入 Token / API Key |
| 工具审计 | 配合 [Hook 机制](https://smartsi.blog.csdn.net/article/details/161203988)记录所有调用 |

### 9.3 性能优化

- **超时控制**：根据工具特性设置合理的 `timeout`，避免长时间挂起
- **工具过滤**：只注册 Agent 真正需要的工具，减少 LLM 决策负担和上下文 token 消耗
- **连接复用**：MCP Client 连接是有状态的，应作为单例长期持有，避免频繁创建销毁
- **并发上限**：StdIO 传输是单进程子进程，并发请求会串行化，必要时启动多个实例

### 9.4 常见问题排查

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| `IOException: Cannot run program "npx"` | 系统未安装 Node.js | 安装 Node.js 18+，确保 `npx` 在 PATH 中 |
| 连接超时 | `initializationTimeout` 太短 | 增大到 30 ~ 60 秒（首次启动需下载 Server） |
| 工具调用永久挂起 | 未设置 `timeout` | 显式设置 `timeout(Duration.ofSeconds(60))` |
| LLM 找不到工具 | 工具被 `disableTools` 排除 | 检查白名单 / 黑名单配置 |
| 传输不一致报错 | StdIO 用了 `.header()` | StdIO 不支持 HTTP 头，仅 SSE / HTTP 有效 |
| 子进程崩溃 | MCP Server 自身异常 | 单独跑命令验证，查看 stderr 日志 |
| Token 过期 | Bearer Token 静态写死 | 使用 Token Provider 动态刷新 |

---

## 10. 本篇小结

| 要点 | 内容 |
|------|------|
| **核心定位** | MCP 是连接 AI 应用与外部工具的开放标准协议 |
| **核心类** | `McpClientBuilder`、`McpClientWrapper`、`Toolkit` |
| **三种传输** | StdIO（本地进程）、SSE（HTTP 长连接）、HTTP（无状态） |
| **工具注册** | `toolkit.registerMcpClient(client)` 或 `toolkit.registration().mcpClient(client).enableTools().apply()` |
| **工具过滤** | `enableTools()` 白名单、`disableTools()` 黑名单（黑优先） |
| **工具组** | 支持将 MCP 工具分配到组，动态激活 / 停用 |
| **高级特性** | 同步 / 异步客户端、Elicitation 交互、HTTP 头 / Query 参数 |
| **生命周期** | `toolkit.removeMcpClient(name)` 清理连接 |

MCP 让 AgentScope Java 的 Agent **不再受限于本地代码**，而是可以接入整个开放的工具生态系统。配合本地 `@Tool` 使用，既能保持核心业务的可控性，又能享受社区生态的便利性——这正是构建生产级 AI 应用的合理姿势。

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
| 八 | AgentScope Java 入门 8：Tool 工具系统——让 Agent 真正"动手做事" |
| **九（本文）** | **MCP 协议集成——连接无限工具生态** |
