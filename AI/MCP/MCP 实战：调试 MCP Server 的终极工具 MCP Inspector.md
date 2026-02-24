## 1. 什么是 MCP Inspector？

MCP Inspector 是 Model Context Protocol（MCP）官方提供的可视化调试工具，专为开发和测试 MCP 服务器而设计。它通过一个直观的 Web 界面，让你可以轻松地检查服务器的能力、调用工具、读取资源、获取提示，并实时查看通信日志。无论你是 MCP 服务器的新手还是经验丰富的开发者，Inspector 都能帮助你快速定位问题，理解服务器的行为。

本文将详细介绍如何安装、启动和使用 MCP Inspector，并通过实际示例演示其核心功能。

## 2. 安装 MCP Inspector

MCP Inspector 作为一个 Node.js 包发布，你可以通过 `npx` 直接运行，无需全局安装。确保你的系统已安装 Node.js（版本 18 或更高）和 npm。

### 2.1 快速启动命令

基本语法如下：
```bash
npx @modelcontextprotocol/inspector <command>
```
其中 `<command>` 是启动你的 MCP Server 的命令。Inspector 会自动启动服务器并与它建立通信。

检查一个用 Node.js 编写的 MCP 服务器使用如下命令：
```
npx @modelcontextprotocol/inspector node my-server.js
```
检查一个用 Python 编写的 MCP 服务器使用如下命令：
```
npx @modelcontextprotocol/inspector python my_server.py
```
检查一个用 Java 编写的 MCP 服务器使用如下命令：
```
npx @modelcontextprotocol/inspector java -jar my-server.jar
```
在这我们以 Java 编写的 MCP 服务器为例说明。Inspector 启动后，会输出类似如下的信息：
```
Starting MCP inspector...
⚙️ Proxy server listening on localhost:6277
🔑 Session token: 7403b0167c11c2fe70821154b9b302428cdc89ed5cf1d7c75cdef14af533c3df
   Use this token to authenticate requests or set DANGEROUSLY_OMIT_AUTH=true to disable auth

🚀 MCP Inspector is up and running at:
   http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=7403b0167c11c2fe70821154b9b302428cdc89ed5cf1d7c75cdef14af533c3df

🌐 Opening browser...
```

打开浏览器访问 `http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=7403b0167c11c2fe70821154b9b302428cdc89ed5cf1d7c75cdef14af533c3df` 即可开始调试。

## 3. Inspector 界面概览

Inspector 的界面主要分为以下几个区域：

- **服务器信息面板**：显示服务器的名称、版本、协议版本以及已声明的功能（工具、资源、提示）。
- **通信日志**：实时显示客户端与服务器之间的 JSON-RPC 消息，包括请求和响应。
- **工具测试区**：列出所有可用的工具，并提供表单输入参数，点击即可调用。
- **资源测试区**：列出所有可用的资源 URI，点击即可读取资源内容。
- **提示测试区**：列出所有提示模板，可填入参数并获取生成的提示。


## 4. 核心功能详解

### 1. 查看服务器能力

启动 Inspector 后，左侧面板会立即显示服务器通过 `initialize` 响应上报的功能列表。你可以快速确认服务器是否正确声明了所有预期的工具、资源和提示。

### 2. 调用工具

在“工具”标签页中，你会看到每个工具的名称、描述和输入模式（JSON Schema）。点击工具名称展开表单，填写参数后点击“调用工具”按钮，Inspector 会发送 `tools/call` 请求并显示结果。如果工具执行出错，错误信息也会清晰展示。

**示例**：调用一个名为 `add` 的工具，传入 `{ "a": 5, "b": 3 }`，预期返回 `{ "result": 8 }`。

### 3. 读取资源

在“资源”标签页中，服务器提供的资源列表会以 URI 形式展示。点击任意 URI，Inspector 会发送 `resources/read` 请求，并在下方显示资源内容（通常是文本或二进制数据的 Base64 编码）。这对于验证静态资源（如配置文件、文档片段）是否正确暴露非常有用。

### 4. 获取提示

在“提示”标签页中，你可以选择提示模板，输入参数（如变量值），然后点击“获取提示”。Inspector 会调用 `prompts/get` 并返回生成的提示消息列表。这可以帮助你调试提示模板的动态生成逻辑。

### 5. 实时日志分析

右侧的日志面板实时记录所有发送和接收的 JSON-RPC 消息。每条消息都带有时间戳，你可以展开查看详细内容。这是排查协议兼容性问题和跟踪数据流的利器。

### 6. 服务器控制

Inspector 底部有一个“重启服务器”按钮，可以随时重启被调试的服务器进程（如果支持）。这在修改服务器代码后需要重新测试时非常方便。

## 实战演练：调试一个简单的 MCP 服务器

假设我们有一个 Node.js 编写的服务器 `math-server.js`，它提供了一个加法工具 `add` 和一个静态资源 `info://version`。

### 服务器代码（math-server.js）

```javascript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  { name: "math-server", version: "1.0.0" },
  { capabilities: { tools: {}, resources: {} } }
);

// 实现工具列表
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "add",
      description: "Add two numbers",
      inputSchema: {
        type: "object",
        properties: {
          a: { type: "number" },
          b: { type: "number" },
        },
        required: ["a", "b"],
      },
    },
  ],
}));

// 实现工具调用
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "add") {
    const { a, b } = request.params.arguments;
    return { content: [{ type: "text", text: String(a + b) }] };
  }
  throw new Error("Tool not found");
});

// 实现资源读取（简单示例）
server.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: [{ uri: "info://version", name: "Version Info", mimeType: "text/plain" }],
}));

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  if (request.params.uri === "info://version") {
    return { contents: [{ uri: request.params.uri, text: "1.0.0" }] };
  }
  throw new Error("Resource not found");
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

### 启动 Inspector

```bash
npx @modelcontextprotocol/inspector node math-server.js
```

浏览器自动打开 Inspector 界面。

### 测试步骤

1. **检查工具列表**：在左侧工具标签页中应看到 `add` 工具及其描述。
2. **调用工具**：在 `add` 工具的表单中输入 `a=5`，`b=3`，点击调用。结果区域应显示 `8`。
3. **查看日志**：在右侧日志中，你可以看到发送的 `tools/call` 请求和返回的响应。
4. **读取资源**：切换到资源标签页，点击 `info://version`，下方应显示文本 `1.0.0`。
5. **尝试重启**：修改服务器代码（例如将版本号改为 `1.0.1`），点击“重启服务器”，再次读取资源，版本应更新。

## 高级用法与技巧

### 1. 使用环境变量调试

如果你需要为服务器设置特定的环境变量，可以在命令前添加：

```bash
npx @modelcontextprotocol/inspector LOG_LEVEL=debug node server.js
```

### 2. 连接远程 MCP 服务器

Inspector 默认通过 stdio 与本地子进程通信。如果你有一个运行在远程的 MCP 服务器（通过 SSE 传输），你需要使用一个适配器。目前 Inspector 主要针对 stdio 设计，但你可以通过 `mcp-client` 等工具桥接。

### 3. 调试服务器启动错误

如果服务器启动时崩溃，Inspector 会捕获 stderr 并显示在日志中。你也可以在终端中查看原始输出。

### 4. 保存和分享测试用例

虽然 Inspector 本身不提供保存功能，但你可以利用浏览器开发者工具的网络面板记录请求，或手动记录测试参数。

## 常见问题解答

**Q: Inspector 启动后无法打开浏览器怎么办？**  
A: 手动访问 `http://localhost:5173` 即可。如果端口冲突，Inspector 会自动寻找可用端口，请查看终端输出的实际 URL。

**Q: 我的服务器是用其他语言编写的，Inspector 支持吗？**  
A: 只要服务器遵循 MCP stdio 传输协议，并可通过命令行启动，Inspector 就可以通过指定解释器来运行（如 `python`, `java -jar` 等）。

**Q: 调用工具时一直超时怎么办？**  
A: 检查服务器是否在合理时间内响应。如果服务器逻辑复杂，考虑增加 Inspector 的超时设置（目前默认为 60 秒，可在源码中调整）。

**Q: 为什么我看不到资源列表？**  
A: 确保服务器在初始化时正确声明了 `resources` 能力，并实现了 `resources/list` 和 `resources/read` 请求处理。

## 总结

MCP Inspector 是开发和测试 MCP 服务器不可或缺的助手。它通过友好的图形界面，让你无需编写客户端代码即可全面验证服务器的功能，同时提供详细的通信日志帮助排查问题。掌握 Inspector 的使用，将极大提升你的 MCP 开发效率。

现在，打开终端，用 Inspector 启动你的第一个 MCP 服务器，开始愉快的调试之旅吧！










[MCP Inspector](https://github.com/modelcontextprotocol/inspector) 是一个用于测试和调试 MCP 服务器的交互式开发工具。虽然 [调试指南](https://modelcontextprotocol.io/legacy/tools/debugging) 涵盖了 Inspector 作为整体调试工具包的一部分，但本文件详细介绍了 Inspector 的功能与能力。

## 开始使用
--------------------------------------------------------------------------------------------

### 安装与基本用法
Inspector 可以直接通过 `npx` 运行，无需单独安装：
```shell
npx @modelcontextprotocol/inspector <command>
```
或者带有参数：
```shell
npx @modelcontextprotocol/inspector <command> <arg1> <arg2>
```

### 从 npm 或 PyPI 检查服务器
一种常见的方法是通过 [npm](https://npmjs.com/) 或 [PyPI](https://pypi.org/) 启动服务器包。
- npm 包：
```shell
npx -y @modelcontextprotocol/inspector npx <package-name> <args>
# 例如
npx -y @modelcontextprotocol/inspector npx @modelcontextprotocol/server-filesystem /Users/username/Desktop
```
- PyPI 包：
```shell
npx @modelcontextprotocol/inspector uvx <package-name> <args>
# 例如
npx @modelcontextprotocol/inspector uvx mcp-server-git --repository ~/code/mcp/servers.git
```

### 检查本地开发的服务器
要检查本地开发或作为仓库下载的服务器，最常见的方法是：
- TypeScript
- Python

```shell
npx @modelcontextprotocol/inspector node path/to/server/index.js args...
```
或者：
```shell
npx @modelcontextprotocol/inspector \
  uv \
  --directory path/to/server \
  run \
  package-name \
  args...
```

请仔细阅读任何附带的 README，以获取最准确的指示。

## 功能概述
----------------------------------------------------------------------------------------------

![](https://mintcdn.com/mcp/4ZXF1PrDkEaJvXpn/images/mcp-inspector.png?w=2500&fit=max&auto=format&n=4ZXF1PrDkEaJvXpn&q=85&s=4fbcddae467e84daef4739e0816ab698)

MCP Inspector 界面

Inspector 提供多种与 MCP 服务器交互的功能：

### 服务器连接面板
- 允许选择用于连接到服务器的 [传输方式](https://modelcontextprotocol.io/legacy/concepts/transports)
- 支持自定义本地服务器的命令行参数和环境变量

### 资源标签页
- 列出所有可用资源
- 显示资源元数据（MIME 类型，描述）
- 允许检查资源内容
- 支持订阅测试

### 提示标签页
- 展示可用提示模板
- 显示提示参数和描述
- 通过自定义参数启用提示测试
- 预览生成的消息

### 工具标签页
- 列出所有可用工具
- 显示工具方案和描述
- 使用自定义输入启用工具测试
- 展示工具执行结果

### 通知面板
- 呈现来自服务器的所有日志记录
- 显示从服务器接收到的通知

## 最佳实践
------------------------------------------------------------------------------------------

### 开发流程
1. 启动开发：
   - 使用 Inspector 启动服务器
   - 验证基本连接性
   - 检查能力协商
2. 迭代测试：
   - 修改服务器
   - 重建服务器
   - 重新连接 Inspector
   - 测试受影响的功能
   - 监控消息
3. 测试边界情况：
   - 无效输入
   - 缺少提示参数
   - 并发操作
   - 验证错误处理和错误响应

## 下一步
----------------------------------------------------------------------------------

[Inspector 仓库](https://github.com/modelcontextprotocol/inspector)
- 查看 MCP Inspector 源代码

[调试指南](https://modelcontextprotocol.io/legacy/tools/debugging)
- 学习更广泛的调试策略

您认为此页面是否有帮助？

是 | 否
[安全最佳实践](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices)

![](https://mintcdn.com/mcp/4ZXF1PrDkEaJvXpn/images/mcp-inspector.png?w=2500&fit=max&auto=format&n=4ZXF1PrDkEaJvXpn&q=85&s=4fbcddae467e84daef4739e0816ab698)
