# 全文翻译：按 CTRL + K 搜索

模型上下文协议 (MCP)
============================

|     |     |
| --- | --- |
|     | **MCP 新手？** 从我们的 [MCP 入门指南](https://docs.spring.io/spring-ai/reference/guides/getting-started-mcp.html)<br>开始，快速了解并实践示例。 |

[模型上下文协议 (MCP)](https://modelcontextprotocol.org/docs/concepts/architecture) 是一种标准化协议，使 AI 模型能够以结构化方式与外部工具和资源交互。可将其视为 AI 模型与现实世界之间的桥梁——允许它们通过一致的接口访问数据库、API、文件系统和其他外部服务。它支持多种传输机制，以提供跨不同环境的灵活性。

[MCP Java SDK](https://modelcontextprotocol.io/sdk/java/mcp-overview) 提供了模型上下文协议的 Java 实现，通过同步和异步通信模式实现与 AI 模型和工具的标准化交互。

Spring AI 通过专用的 Boot Starter 和 MCP Java 注解全面支持 MCP，使构建能够无缝连接外部系统的复杂 AI 应用程序变得前所未有的简单。这意味着 Spring 开发者可以同时参与 MCP 生态系统的两端——构建使用 MCP 服务器的 AI 应用程序，以及创建向更广泛的 AI 社区公开基于 Spring 的服务的 MCP 服务器。通过 [Spring Initializer](https://start.spring.io/) 引导支持 MCP 的 AI 应用程序。

[](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-overview.html#_mcp_java_sdk_architecture)
## MCP Java SDK 架构
-----------------------------------------------------------------------------------------------------------------------------

|     |     |
| --- | --- |
|     | 本节概述了 [MCP Java SDK 架构](https://modelcontextprotocol.io/sdk/java/mcp-overview)<br>。关于 Spring AI MCP 集成，请参阅 [Spring AI MCP Boot Starter](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-overview.html#_spring_ai_mcp_integration)<br>文档。 |

Java MCP 实现遵循三层架构，分离关注点以提高可维护性和灵活性：

![MCP 堆栈架构](https://docs.spring.io/spring-ai/reference/_images/mcp/mcp-stack.svg)

图 1. MCP 堆栈架构

### [](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-overview.html#_clientserver_layer_top)
客户端/服务器层（顶层）

顶层处理主应用程序逻辑和协议操作：

*   **McpClient** - 管理客户端操作和服务器连接
*   **McpServer** - 处理服务器端协议操作和客户端请求
*   两个组件均利用下层的会话层进行通信管理

### [](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-overview.html#_session_layer_middle)
会话层（中层）

中层管理通信模式并维护连接状态：

*   **McpSession** - 核心会话管理接口
*   **McpClientSession** - 特定于客户端的会话实现
*   **McpServerSession** - 特定于服务器的会话实现

### [](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-overview.html#_transport_layer_bottom)
传输层（底层）

底层处理实际的消息传输和序列化：

*   **McpTransport** - 管理 JSON-RPC 消息的序列化和反序列化
*   支持多种传输实现（STDIO、HTTP/SSE、Streamable-HTTP 等）
*   为所有高层通信提供基础


| [MCP 客户端](https://modelcontextprotocol.io/sdk/java/mcp-client) |     |
| --- | --- |
| MCP 客户端是模型上下文协议（MCP）架构中的关键组件，负责与 MCP 服务器建立和管理连接。它实现了协议的客户端，处理：<br><br>*   协议版本协商以确保与服务器的兼容性<br>    <br>*   能力协商以确定可用功能<br>    <br>*   消息传输和 JSON-RPC 通信<br>    <br>*   工具发现和执行<br>    <br>*   资源访问和管理<br>    <br>*   提示系统交互<br>    <br>*   可选功能：<br>    <br>    *   根管理<br>        <br>    *   采样支持<br>        <br>    <br>*   同步和异步操作<br>    <br>*   传输选项：<br>    <br>    *   基于标准输入/输出的传输，用于基于进程的通信<br>        <br>    *   基于 Java HttpClient 的 SSE 客户端传输<br>        <br>    *   WebFlux SSE 客户端传输，用于响应式 HTTP 流 | ![Java MCP 客户端架构](https://docs.spring.io/spring-ai/reference/_images/mcp/java-mcp-client-architecture.jpg) |


| [MCP 服务器](https://modelcontextprotocol.io/sdk/java/mcp-server) |     |
| --- | --- |
| MCP 服务器是模型上下文协议（MCP）架构中的基础组件，向客户端提供工具、资源和能力。它实现了协议的服务器端，负责：<br><br>*   服务器端协议操作的实现<br>    <br>    *   工具暴露和发现<br>        <br>    *   基于 URI 的资源管理<br>        <br>    *   提示模板的提供和处理<br>        <br>    *   与客户端的能力协商<br>        <br>    *   结构化日志记录和通知<br>        <br>    <br>*   并发客户端连接管理<br>    <br>*   同步和异步 API 支持<br>    <br>*   传输实现：<br>    <br>    *   STDIO、Streamable-HTTP、Stateless Streamable-HTTP、SSE | ![Java MCP 服务器架构](https://docs.spring.io/spring-ai/reference/_images/mcp/java-mcp-server-architecture.jpg) |

有关详细实现指南（使用低层 MCP 客户端/服务器 API），请参阅 [MCP Java SDK 文档](https://modelcontextprotocol.io/sdk/java/mcp-overview)。要使用 Spring Boot 简化设置，请使用下文所述的 MCP Boot Starter。

[](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-overview.html#_spring_ai_mcp_integration)
## Spring AI MCP 集成
-----------------------------------------------------------------------------------------------------------------------------

Spring AI 通过以下 Spring Boot starter 提供 MCP 集成：

### [](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-overview.html#_client_starters)
[客户端 Starter](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-client-boot-starter-docs.html)

*   `spring-ai-starter-mcp-client` - 核心 starter，提供 `STDIO`、基于 Servlet 的 `Streamable-HTTP`、`Stateless Streamable-HTTP` 和 `SSE` 支持
*   `spring-ai-starter-mcp-client-webflux` - 基于 WebFlux 的 `Streamable-HTTP`、`Stateless Streamable-HTTP` 和 `SSE` 传输实现

### [](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-overview.html#_server_starters)
[服务器 Starter](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-server-boot-starter-docs.html)

#### [](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-overview.html#_stdio)
STDIO


| 服务器类型 | 依赖项 | 属性 |
| --- | --- | --- |
| [标准输入/输出 (STDIO)](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-stdio-sse-server-boot-starter-docs.html) | `spring-ai-starter-mcp-server` | `spring.ai.mcp.server.stdio=true` |

#### [](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-overview.html#_webmvc)
WebMVC

|     |     |     |
| --- | --- | --- |  
| 服务器类型 | 依赖项 | 属性 |
| [SSE WebMVC](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-stdio-sse-server-boot-starter-docs.html#_sse_webmvc_serve) | `spring-ai-starter-mcp-server-webmvc` | `spring.ai.mcp.server.protocol=SSE` 或为空 |
| [Streamable-HTTP WebMVC](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-streamable-http-server-boot-starter-docs.html#_streamable_http_webmvc_server) | `spring-ai-starter-mcp-server-webmvc` | `spring.ai.mcp.server.protocol=STREAMABLE` |
| [Stateless Streamable-HTTP WebMVC](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-stateless-server-boot-starter-docs.html#_stateless_webmvc_server) | `spring-ai-starter-mcp-server-webmvc` | `spring.ai.mcp.server.protocol=STATELESS` |

#### [](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-overview.html#_webmvc_reactive)
WebMVC (响应式)

|     |     |     |
| --- | --- | --- |  
| 服务器类型 | 依赖项 | 属性 |
| [SSE WebFlux](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-stdio-sse-server-boot-starter-docs.html#_sse_webflux_serve) | `spring-ai-starter-mcp-server-webflux` | `spring.ai.mcp.server.protocol=SSE` 或为空 |
| [Streamable-HTTP WebFlux](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-streamable-http-server-boot-starter-docs.html#_streamable_http_webflux_server) | `spring-ai-starter-mcp-server-webflux` | `spring.ai.mcp.server.protocol=STREAMABLE` |
| [Stateless Streamable-HTTP WebFlux](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-stateless-server-boot-starter-docs.html#_stateless_webflux_server) | `spring-ai-starter-mcp-server-webflux` | `spring.ai.mcp.server.protocol=STATELESS` |

[](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-overview.html#_spring_ai_mcp_annotations)
[Spring AI MCP 注解](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-annotations-overview.html)

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

除了编程式 MCP 客户端和服务器配置外，Spring AI 还通过 [MCP 注解](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-annotations-overview.html)模块为 MCP 服务器和客户端提供基于注解的方法处理。这种方法通过简洁的声明式编程模型和 Java 注解，简化了 MCP 操作的创建和注册。

MCP 注解模块使开发者能够：

*   使用简单的注解创建 MCP 工具、资源和提示
*   以声明方式处理客户端通知和请求
*   减少样板代码并提高可维护性
*   自动生成工具参数的 JSON 模式
*   访问特殊参数和上下文信息

关键特性包括：

*   [服务器注解](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-annotations-server.html)：`@McpTool`, `@McpResource`, `@McpPrompt`, `@McpComplete`
*   [客户端注解](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-annotations-client.html)：`@McpLogging`, `@McpSampling`, `@McpElicitation`, `@McpProgress`
*   [特殊参数](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-annotations-special-params.html)：`McpSyncServerExchange`, `McpAsyncServerExchange`, `McpTransportContext`, `McpMeta`
*   **自动发现**：通过可配置的包包含/排除进行注解扫描
*   **Spring Boot 集成**：与 MCP Boot Starter 无缝集成

[](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-overview.html#_additional_resources)
## 其他资源
-------------------------------------------------------------------------------------------------------------------

*   [MCP 注解文档](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-annotations-overview.html)
*   [MCP 客户端 Boot Starter 文档](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-client-boot-starter-docs.html)
*   [MCP 服务器 Boot Starter 文档](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-server-boot-starter-docs.html)
*   [MCP 工具文档](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-helpers.html)
*   [模型上下文协议规范](https://modelcontextprotocol.github.io/specification/)

Cookie 使用说明
-------

点击“允许全部”，即表示您理解 Broadcom 及第三方合作伙伴使用技术（包括 Cookie）来查看和保留您的网站互动、改善您的体验以及帮助我们进行广告投放等。更多详情请参阅我们的 [Cookie 声明](https://www.broadcom.com/company/legal/cookie-policy)。

允许全部

请勿出售或分享我的个人信息

Cookie 设置

![公司 Logo](https://cdn.cookielaw.org/logos/8153b982-ae11-46a0-b7c2-6e4e3b591d72/b2b73549-dd48-4805-83af-94b66f64fe57/d4a96bff-e4ff-44f4-a5af-efee8da0e3f9/Broadcom_Logo_Red-Black_no-tag.png)

隐私偏好中心
-------------------------

隐私偏好中心
-------------------------

*   ### 您的隐私

*   ### 严格必要的 Cookie

*   ### 出售或分享个人数据


#### 您的隐私

当您按照《隐私政策》的规定与 Broadcom 互动时，通过访问任何网站，它可能会在您的浏览器上存储或检索信息，主要是以 Cookie 的形式。这些信息可能与您本人、您的偏好或您的设备有关，主要用于使网站按照您的预期运行。这些信息通常不会直接识别您的身份，但可以为您提供更个性化的网络体验。  
[Cookie 政策](https://www.broadcom.com/company/legal/cookie-policy)
[隐私政策](https://www.broadcom.com/company/legal/privacy/policy)

#### 严格必要的 Cookie

始终启用

这些 Cookie 对网站功能正常运行是必要的，无法在 Broadcom 的系统中关闭。它们通常仅在您发出服务请求的操作时设置，例如设置您的隐私偏好、登录或填写表单。您可以将浏览器设置为阻止或提醒您这些 Cookie，但网站的某些部分将无法正常工作。这些 Cookie 不存储任何个人身份信息。

#### 出售或分享个人数据

出售或分享个人数据

根据加州法律，某些 Cookie 的使用可能被视为“出售”或“分享”个人信息。您可以通过选择退出这些 Cookie 来选择不参与此类“出售”或“分享”。

*   ##### 定向 Cookie

     切换标签 label

    这些 Cookie 可能由 Broadcom 的网站通过其广告合作伙伴设置。这些公司可能使用它们来建立您的兴趣档案，并在其他网站上向您展示相关广告。它们不直接存储个人信息，而是基于唯一标识您的浏览器和互联网设备。如果您不允许这些 Cookie，您将体验较少的定向广告。


*   ##### 性能 Cookie

     切换标签 label

    这些 Cookie 允许 Broadcom 统计访问量和流量来源，以便衡量和改进其网站的性能。它们帮助 Broadcom 了解哪些页面最受欢迎和最不受欢迎，并查看访问者如何在网站中移动。这些 Cookie 收集的所有信息都是汇总的，因此是匿名的。如果您不允许这些 Cookie，Broadcom 将不知道您何时访问了我们的网站，也无法监控其性能。


返回按钮

### Cookie 列表

筛选按钮

同意法律利益

 复选框标签 label

 复选框标签 label

 复选框标签 label

清除

*    复选框标签 label


应用 取消

确认我的选择

仅需必要项 允许全部

[![由 Onetrust 提供支持](https://cdn.cookielaw.org/logos/static/powered_by_logo.svg "由 OneTrust 提供支持，在新标签页中打开")](https://www.onetrust.com/products/cookie-consent/)
