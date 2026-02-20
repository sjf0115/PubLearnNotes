模型上下文协议（MCP）标准化了 AI 应用程序与外部工具和资源的交互方式。Spring 早期加入了 MCP 生态系统并成为关键贡献者，协助开发以及维护[官方 MCP Java SDK](https://modelcontextprotocol.io/sdk/java/mcp-overview)(Java 版 MCP 基础实现)。基于此贡献，Spring AI 通过专用[Boot Starters](https://docs.spring.io/spring-ai/reference/1.1-SNAPSHOT/api/mcp/mcp-overview.html#_spring_ai_mcp_integration)和[MCP Java注解](https://docs.spring.io/spring-ai/reference/1.1-SNAPSHOT/api/mcp/mcp-annotations-overview.html)全面拥抱 MCP，从而使构建能够无缝连接外部系统的复杂AI应用变得前所未有的简单。

本篇博客将介绍 MCP 的核心组件，并演示使用 Spring AI 构建 MCP 服务器和客户端的基础与高级功能。完整源代码请访问：[MCP天气示例](https://github.com/tzolov/spring-ai-mcp-blogpost)。

> **注意：** 本文内容仅适用于 Spring AI `1.1.0-SNAPSHOT`或 Spring `AI 1.1.0-M1+` 版本。

## 1. 什么是模型上下文协议？
-------------------------------------------------------------------------------------------------------------------------------------

[模型上下文协议（MCP）](https://modelcontextprotocol.org/docs/concepts/architecture)是一个标准化协议，使 AI 模型能够以结构化方式与外部工具和资源交互。可以将其视为 AI 模型与现实世界之间的桥梁——允许它们通过统一接口访问数据库、API、文件系统和其他外部服务。

## 2. MCP 客户端-服务器架构

![](https://raw.githubusercontent.com/spring-io/spring-io-static/refs/heads/main/blog/tzolov/20250911/MCP-CLIENT-SERVER-ARCHITECTURE.svg)

模型上下文协议遵循客户端-服务器架构，确保职责明确分离。MCP服务器从第三方服务暴露特定能力（工具、资源、提示）。MCP 客户端由宿主应用程序实例化，用于与特定 MCP 服务器通信。每个客户端处理与一个服务器的直接通信。

宿主（Host）是用户交互的 AI 应用程序，而客户端是支持服务器连接的协议级组件。MCP 协议确保客户端和服务器之间实现完全的与语言无关的交互。您可以用 Java、Python 或 TypeScript 编写的客户端与任何语言的服务器通信，反之亦然。

这种架构在客户端和服务器端开发之间建立了清晰的边界和职责，自然形成了两个不同的开发者社区：

**AI 应用程序/宿主开发者**

负责协调多个 MC P服务器（通过 MCP 客户端连接）并与 AI 模型集成的复杂性。AI 开发者构建的应用程序能够：
- 使用 MCP 客户端与多个 MCP 服务器通信的能力
- 处理 AI 模型集成和提示词工程
- 管理对话上下文和用户交互
- 编排跨不同服务的复杂工作流
- 专注于创建引人入胜的用户体验

**MCP 服务器（提供者）开发者**

专注于将第三方服务（数据库、文件系统、外部API）的特定能力暴露为MCP服务器。服务器开发者创建的服务器能够：
*   封装第三方服务和API
*   通过标准化的MCP原语（工具、资源、提示）暴露服务能力
*   处理特定服务的认证和授权

这种分离确保服务器开发者可以专注于封装其领域特定服务，而无需担心AI编排。同时，AI应用开发者可以复用现有MCP服务器，而无需理解每个第三方服务的内部细节。

分工意味着数据库专家可以创建PostgreSQL的MCP服务器而无需理解LLM提示，而AI应用开发者可以使用该PostgreSQL服务器而无需了解SQL内部机制。MCP协议成为他们之间的通用语言。

**Spring AI**通过[MCP客户端](https://docs.spring.io/spring-ai/reference/1.1-SNAPSHOT/api/mcp/mcp-client-boot-starter-docs.html)和[MCP服务器](https://docs.spring.io/spring-ai/reference/1.1-SNAPSHOT/api/mcp/mcp-server-boot-starter-docs.html)Boot Starters拥抱这一架构。这意味着Spring开发者可以参与MCP生态系统的双方——构建消费MCP服务器的AI应用，以及创建将基于Spring的服务暴露给更广泛AI社区的MCP服务器。

### [](https://spring.io/blog/2025/09/16/spring-ai-mcp-intro-blog#mcp-features)
#### MCP功能特性

![MCP Capabilities](https://raw.githubusercontent.com/spring-io/spring-io-static/refs/heads/main/blog/tzolov/20250911/MCP-FEATURES.svg)

MCP在客户端和服务器之间提供了一套广泛的功能，实现AI应用与外部服务的无缝通信：
*   暴露AI模型可调用的[工具](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
*   与AI应用共享[资源](https://modelcontextprotocol.io/specification/2025-06-18/server/resources)和数据
*   提供一致交互的[提示](https://modelcontextprotocol.io/specification/2025-06-18/server/prompts)模板
*   为提示和资源URI提供参数[自动补全](https://modelcontextprotocol.io/specification/2025-06-18/server/utilities/completion)建议
*   处理实时通知和[进度](https://modelcontextprotocol.io/specification/2025-06-18/basic/utilities/progress)更新
*   支持客户端[采样](https://modelcontextprotocol.io/specification/2025-06-18/client/sampling)、[启发](https://modelcontextprotocol.io/specification/2025-06-18/client/elicitation)、[结构化日志](https://modelcontextprotocol.io/specification/2025-06-18/server/utilities/logging)和[进度追踪](https://modelcontextprotocol.io/specification/2025-06-18/basic/utilities/progress)
*   支持多种传输协议：[STDIO](http://localhost:3000/specification/2025-06-18/basic/transports#stdio)、[Streamable-HTTP](http://localhost:3000/specification/2025-06-18/basic/transports#streamable-http)和[SSE](http://localhost:3000/specification/2024-11-05/basic/transports#http-with-sse)

> **重要提示：** 与其他MCP功能（如提示和资源）不同，工具由LLM拥有。LLM（而非宿主）决定是否、何时以及以何种顺序调用工具。宿主仅控制向LLM提供哪些工具描述。

[](https://spring.io/blog/2025/09/16/spring-ai-mcp-intro-blog#build-an-mcp-server)
## 构建MCP服务器
------------------------------------------------------------------------------------------------------

让我们构建一个[Streamable-HTTP MCP服务器](https://docs.spring.io/spring-ai/reference/1.1-SNAPSHOT/api/mcp/mcp-streamable-http-server-boot-starter-docs.html)，提供实时天气预报信息。

#### [](https://spring.io/blog/2025/09/16/spring-ai-mcp-intro-blog#spring-boot-server-application)
Spring Boot服务器应用

创建一个新的（`mcp-weather-server`）Spring Boot应用：

```java
@SpringBootApplication
public class McpServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(McpServerApplication.class, args);
    }
}
