2025年12月，阿里巴巴正式发布了 [AgentScope Java v1.0](https://smartsi.blog.csdn.net/article/details/158778778)。这一消息在 Java 开发者社区引起了广泛关注——终于，Java 开发者可以用自己熟悉的技术栈，构建企业级的智能体应用了。

作为一名长期关注 AI 基础设施的开发者，我认为 AgentScope Java 的发布标志着智能体开发的一个重要转折点：AI 智能体正在从“实验室原型”走向“企业生产环境”。本文将带你全面了解 AgentScope Java 是什么、它解决了什么问题，以及如何用它构建生产级的 AI 智能体应用。

## 1. 什么是 AgentScope Java？

> 用 Java 构建生产级 AI 智能体

AgentScope 是阿里巴巴推出的一款以开发者为核心，专注于智能体开发的开源编程框架，用于构建 LLM 驱动的应用程序。AgentScope 是继 ModelScope（魔搭社区）后在 Agent 层的战略产品。它提供了创建智能体所需的一切：ReAct 推理、工具调用、内存管理、多智能体协作等。核心目标是解决智能体在构建、运行和管理中的难题，提供一套覆盖“开发、部署、调优”全生命周期的生产级解决方案，让智能体应用的开发更简单、运行更稳定、效果更卓越。

一直以来，Java 语言在金融、政务、电商等领域开发中都占着主导地位，开发者社区对于 AgentScope Java 版本的呼声也非常高。AgentScope Java 的发布，面向 Java 开发者提供企业级 Agentic 应用构建的能力。

简单来说，AgentScope Java 为 Java 开发者提供了构建 AI 智能体所需的一切，让开发者可以像编写普通 Java 应用一样，构建复杂的 AI 智能体系统。

## 2. 核心亮点

### 2.1 智能体自主，全程可控

AgentScope 采用 ReAct（推理-行动）范式，使智能体能够自主规划和执行复杂任务。与传统的工作流方法不同，ReAct 智能体能够动态决定使用哪些工具以及何时使用，实时适应不断变化的需求。

然而，在生产环境中，没有控制的自主性是一种隐患。AgentScope 提供了全面的运行时干预机制：

- **安全中断** - 在任意时刻暂停智能体执行，同时保留完整的上下文和工具状态，支持无数据丢失的无缝恢复
- **优雅取消** - 终止长时间运行或无响应的工具调用，而不会破坏智能体状态，允许立即恢复和重定向
- **人机协作** - 通过 Hook 系统在任何推理步骤注入修正、额外上下文或指导，保持人类对关键决策的监督

### 内置工具

AgentScope 包含生产就绪的工具，解决智能体开发中的常见挑战：

- **PlanNotebook** - 结构化任务管理系统，将复杂目标分解为有序、可追踪的步骤。智能体可以创建、修改、暂停和恢复多个并发计划，确保多步骤工作流的系统化执行。
- **结构化输出** - 自纠错输出解析器，保证类型安全的响应。当 LLM 输出偏离预期格式时，系统会自动检测错误并引导模型生成有效输出，将结果直接映射到 Java POJO，无需手动解析。
- **长期记忆** - 跨会话的持久化内存存储，支持语义搜索。支持自动管理、智能体控制记录或混合模式。支持多租户隔离，满足企业部署中智能体服务多用户的需求。
- **RAG（检索增强生成）** - 与企业知识库无缝集成。支持自托管的基于嵌入的检索和阿里云百炼等托管服务，使智能体响应基于权威数据源。

### 无缝集成

AgentScope 设计为与现有企业基础设施集成，无需大量修改：

- **MCP 协议** - 与任何 MCP 兼容服务器集成，即时扩展智能体能力。连接到不断增长的 MCP 工具和服务生态系统——从文件系统和数据库到 Web 浏览器和代码解释器——无需编写自定义集成代码。
- **A2A 协议** - 通过标准服务发现实现分布式多智能体协作。将智能体能力注册到 Nacos 或类似注册中心，允许智能体像调用微服务一样自然地发现和调用彼此。

### 生产级别

为企业部署需求而构建：

- **高性能** - 基于 Project Reactor 的响应式架构确保非阻塞执行。GraalVM 原生镜像编译实现 200ms 冷启动时间，使 AgentScope 适用于 Serverless 和自动扩缩容环境。
- **安全沙箱** - AgentScope Runtime 为不受信任的工具代码提供隔离的执行环境。包括用于 GUI 自动化、文件系统操作和移动设备交互的预构建沙箱，防止未授权访问系统资源。
- **可观测性** - 原生集成 OpenTelemetry，实现整个智能体执行管道的分布式追踪。AgentScope Studio 为开发和生产环境提供可视化调试、实时监控和全面的日志记录。

## 系统要求

- **JDK 17 或更高版本**
- Maven 或 Gradle

## 快速开始

按照以下步骤开始使用 AgentScope Java：

1. **[安装](quickstart/installation.md)** - 在您的项目中配置 AgentScope Java
2. **[核心概念](quickstart/key-concepts.md)** - 理解核心概念和架构
3. **[构建第一个智能体](quickstart/agent.md)** - 创建一个可工作的智能体

## 快速示例

```java
import io.agentscope.core.ReActAgent;
import io.agentscope.core.model.DashScopeChatModel;
import io.agentscope.core.message.Msg;

// 创建智能体并内联配置模型
ReActAgent agent = ReActAgent.builder()
    .name("Assistant")
    .sysPrompt("你是一个有帮助的 AI 助手。")
    .model(DashScopeChatModel.builder()
        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
        .modelName("qwen3-max")
        .build())
    .build();

Msg response = agent.call(Msg.builder()
        .textContent("你好！")
        .build()).block();
System.out.println(response.getTextContent());
```

## 进阶指南

熟悉基础后，可以探索以下功能：

### 模型集成
- **[模型集成](task/model.md)** - 配置不同的 LLM 提供商
- **[多模态](task/multimodal.md)** - 视觉和多模态能力

### 工具与知识
- **[工具系统](task/tool.md)** - 使用基于注解的工具注册创建和使用工具
- **[MCP](task/mcp.md)** - 模型上下文协议支持，实现高级工具集成
- **[RAG](task/rag.md)** - 检索增强生成，提供知识增强的响应
- **[结构化输出](task/structured-output.md)** - 类型安全的输出解析，支持自动纠错

### 行为控制
- **[钩子系统](task/hook.md)** - 使用事件钩子监控和定制智能体行为
- **[内存管理](task/memory.md)** - 管理对话历史和长期内存
- **[计划](task/plan.md)** - 复杂多步骤任务的计划管理
- **[智能体配置](task/agent-config.md)** - 高级智能体配置选项

### 多智能体系统
- **[管道](multi-agent/pipeline.md)** - 使用顺序和并行执行构建多智能体工作流
- **[MsgHub](multi-agent/msghub.md)** - 多智能体消息广播机制
- **[A2A 协议](task/a2a.md)** - Agent2Agent 协议支持
- **[状态管理](task/state.md)** - 跨会话持久化和恢复智能体状态

### 可观测性与调试
- **[AgentScope Studio](task/studio.md)** - 可视化调试和监控

## AI 辅助开发

AgentScope 文档支持 [`llms.txt` 标准](https://llmstxt.org/)，使 Claude Code、Cursor、Windsurf 等 AI 编程助手能够理解 AgentScope API 并生成准确的代码。

**Cursor 快速设置：**

1. 打开 Cursor 设置 -> Features -> Docs
2. 点击 "+ Add new Doc"
3. 添加 URL：`https://java.agentscope.io/llms-full.txt`

更多工具和详细配置，请参阅 **[使用 AI 编程](task/ai-coding.md)**。

## 社区

- **GitHub**: [agentscope-ai/agentscope-java](https://github.com/agentscope-ai/agentscope-java)

| [Discord](https://discord.gg/eYMpfnkG8h) | DingTalk                                 |    WeChat    |
|------------------------------------------|------------------------------------------|------------------------------------------|
| ![QR Code](../imgs/discord.png)          |   ![QR Code](../imgs/dingtalk_qr_code.jpg)   |  ![QR Code](../imgs/wechat.png)   |


## 核心概念

### 消息（Message）

**解决的问题**：智能体需要一种统一的数据结构来承载各种类型的信息——文本、图像、工具调用等。Message 是 AgentScope 最核心的数据结构，用于：
- 在智能体之间交换信息
- 在记忆中存储对话历史
- 作为与 LLM API 交互的统一媒介

**核心字段**：

| 字段 | 说明 |
|-----|------|
| `id` | 消息唯一标识符（自动生成 UUID） |
| `name` | 发送者名称，多智能体场景用于区分身份 |
| `role` | 角色：`USER`、`ASSISTANT`、`SYSTEM` 或 `TOOL` |
| `content` | 内容块列表，支持多种类型 |
| `timestamp` | 消息时间戳 |
| `metadata` | 可选的结构化数据 |

**内容类型**：
- `TextBlock` - 纯文本
- `ImageBlock` / `AudioBlock` / `VideoBlock` - 多模态内容
- `ThinkingBlock` - 推理过程（用于推理模型）
- `ToolUseBlock` - LLM 发起的工具调用
- `ToolResultBlock` - 工具执行结果

**响应元信息**：Agent 返回的消息包含额外的元信息，帮助理解执行状态：

| 方法 | 说明 |
|-----|------|
| `getGenerateReason()` | 消息生成原因，用于判断后续操作 |
| `getChatUsage()` | Token 用量统计（输入/输出 Token 数、耗时） |

**GenerateReason 枚举值**：

| 值 | 说明 |
|----|------|
| `MODEL_STOP` | 任务正常完成 |
| `TOOL_CALLS` | 模型返回工具调用（内部工具，框架继续执行） |
| `STRUCTURED_OUTPUT` | 结构化输出完成 |
| `TOOL_SUSPENDED` | 工具需要外部执行，等待提供结果 |
| `REASONING_STOP_REQUESTED` | Reasoning 阶段被 Hook 暂停（HITL） |
| `ACTING_STOP_REQUESTED` | Acting 阶段被 Hook 暂停（HITL） |
| `INTERRUPTED` | Agent 被中断 |
| `MAX_ITERATIONS` | 达到最大迭代次数 |

**示例**：

```java
// 创建文本消息
Msg msg = Msg.builder()
    .name("user")
    .textContent("今天北京天气怎么样？")
    .build();

// 创建多模态消息
Msg imgMsg = Msg.builder()
    .name("user")
    .content(List.of(
        TextBlock.builder().text("这张图片是什么？").build(),
        ImageBlock.builder().source(new URLSource("https://example.com/photo.jpg")).build()
    ))
    .build();
```

---

### 智能体（Agent）

**解决的问题**：需要一个统一的抽象来封装"接收消息 → 处理 → 返回响应"的逻辑。Agent 接口定义了智能体的核心契约：
```java
public interface Agent extends CallableAgent, StreamableAgent, ObservableAgent {
    String getAgentId();
    String getName();
    void interrupt();
    void interrupt(Msg msg);
}
```

#### 有状态设计

AgentScope 中的 Agent 是 **有状态的对象**。每个 Agent 实例持有自己的：
- **Memory**：对话历史
- **Toolkit**：工具集合及其状态
- **配置**：系统提示、模型设置等

> **重要**：由于 Agent 和 Toolkit 都是有状态的，**同一个实例不能被并发调用**。如果需要处理多个并发请求，应该为每个请求创建独立的 Agent 实例，或使用对象池管理。

```java
// ❌ 错误：多线程共享同一个 agent 实例
ReActAgent agent = ReActAgent.builder()...build();
executor.submit(() -> agent.call(msg1));  // 并发问题！
executor.submit(() -> agent.call(msg2));  // 并发问题！

// ✅ 正确：每个请求使用独立的 agent 实例
executor.submit(() -> {
    ReActAgent agent = ReActAgent.builder()...build();
    agent.call(msg1);
});
```

#### ReActAgent

`ReActAgent` 是框架提供的主要实现，使用 ReAct 算法（推理 + 行动循环）：
```java
ReActAgent agent = ReActAgent.builder()
    .name("Assistant")
    .model(DashScopeChatModel.builder()
        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
        .modelName("qwen3-max")
        .build())
    .sysPrompt("你是一个有帮助的助手。")
    .toolkit(toolkit)  // 可选：添加工具
    .build();

// 调用智能体
Msg response = agent.call(userMsg).block();
```

---

### 工具（Tool）

**解决的问题**：LLM 本身只能生成文本，无法执行实际操作。工具让智能体能够查询数据库、调用 API、执行计算等。

AgentScope 中的"工具"是带有 `@Tool` 注解的 Java 方法，支持：
- 实例方法、静态方法、类方法
- 同步或异步调用
- 流式或非流式返回

**示例**：
```java
public class WeatherService {
    @Tool(name = "get_weather", description = "获取指定城市的天气")
    public String getWeather(@ToolParam(name = "city", description = "城市名称") String city) {
        // 调用天气 API
        return "北京：晴，25°C";
    }
}

// 注册工具
Toolkit toolkit = new Toolkit();
toolkit.registerTool(new WeatherService());
```

> **重要**：`@ToolParam` 必须显式指定 `name` 属性，因为 Java 运行时不保留方法参数名。

---

### 记忆（Memory）

**解决的问题**：智能体需要记住对话历史，才能进行有上下文的对话。Memory 管理对话历史，`ReActAgent` 会自动：
- 将用户消息加入记忆
- 将工具调用和结果加入记忆
- 将智能体响应加入记忆
- 在推理时读取记忆作为上下文

默认使用 `InMemoryMemory`（内存存储）。如需跨会话持久化，请参考 [状态管理](https://java.agentscope.io/zh/task/state.html)。

### 格式化器（Formatter）

**解决的问题**：不同的 LLM 提供商有不同的 API 格式，需要一个适配层来屏蔽差异。Formatter 负责将 AgentScope 的消息转换为特定 LLM API 所需的格式，包括：
- 提示词工程（添加系统提示、格式化多轮对话）
- 消息验证
- 多智能体场景的身份处理

**内置实现**：
- `DashScopeChatFormatter` - 阿里云百炼（通义千问系列）
- `OpenAIChatFormatter` - OpenAI 及兼容 API
- `AnthropicChatFormatter` - Anthropic（Claude 系列）
- `GeminiChatFormatter` - Google Gemini
- `OllamaChatFormatter` - Ollama 本地模型
- `DeepSeekFormatter` - DeepSeek
- `GLMFormatter` - GLM（智谱）

> 格式化器根据 Model 类型自动选择，通常无需手动配置。

---

### 钩子（Hook）

**解决的问题**：需要在智能体执行的各个阶段插入自定义逻辑，如日志、监控、消息修改等。Hook 通过事件机制在 ReAct 循环的关键节点提供扩展点：

| 事件类型 | 触发时机 | 可修改 |
|---------|---------|--------|
| `PreCallEvent` | 智能体开始处理前 | ✓ |
| `PostCallEvent` | 智能体处理完成后 | ✓ |
| `PreReasoningEvent` | 调用 LLM 前 | ✓ |
| `PostReasoningEvent` | LLM 返回后 | ✓ |
| `ReasoningChunkEvent` | LLM 流式输出时 | - |
| `PreActingEvent` | 执行工具前 | ✓ |
| `PostActingEvent` | 工具执行后 | ✓ |
| `ActingChunkEvent` | 工具流式输出时 | - |
| `PreSummaryEvent` | 摘要生成前 | ✓ |
| `PostSummaryEvent` | 摘要生成后 | ✓ |
| `SummaryChunkEvent` | 摘要流式输出时 | - |
| `ErrorEvent` | 发生错误时 | - |

**Hook 优先级**：Hook 按优先级执行，数值越小优先级越高，默认 100。

**示例**：

```java
Hook loggingHook = new Hook() {
    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        return switch (event) {
            case PreCallEvent e -> {
                System.out.println("智能体开始处理...");
                yield Mono.just(event);
            }
            case ReasoningChunkEvent e -> {
                System.out.print(e.getIncrementalChunk().getTextContent());  // 打印流式输出
                yield Mono.just(event);
            }
            case PostCallEvent e -> {
                System.out.println("处理完成: " + e.getFinalMessage().getTextContent());
                yield Mono.just(event);
            }
            default -> Mono.just(event);
        };
    }

    @Override
    public int priority() {
        return 50;  // 高优先级
    }
};

ReActAgent agent = ReActAgent.builder()
    // ... 其他配置
    .hook(loggingHook)
    .build();
```

> 详细用法请参考 [Hook 系统](https://java.agentscope.io/zh/task/hook.html)。

---

### 状态管理与会话

**解决的问题**：智能体的对话历史、配置等状态需要能够保存和恢复，以支持会话持久化。AgentScope 将对象的"初始化"与"状态"分离，通过 `StateModule` 接口管理：
- `saveTo(Session, SessionKey)` - 将当前状态保存到 Session
- `loadFrom(Session, SessionKey)` - 从 Session 恢复状态
- `loadIfExists(Session, SessionKey)` - 如果存在则恢复状态

**Session** 提供跨运行的持久化存储：

```java
// 保存会话
SessionManager.forSessionId("user123")
    .withSession(new JsonSession(Path.of("sessions")))
    .addComponent(agent)
    .saveSession();

// 恢复会话
SessionManager.forSessionId("user123")
    .withSession(new JsonSession(Path.of("sessions")))
    .addComponent(agent)
    .loadIfExists();
```

---

### 响应式编程

**解决的问题**：LLM 调用和工具执行通常涉及 I/O 操作，同步阻塞会浪费资源。AgentScope 基于 [Project Reactor](https://projectreactor.io/) 构建，使用：
- `Mono<T>` - 返回 0 或 1 个结果
- `Flux<T>` - 返回 0 到 N 个结果（用于流式）

```java
// 非阻塞调用
Mono<Msg> responseMono = agent.call(msg);

// 需要结果时阻塞
Msg response = responseMono.block();

// 或异步处理
responseMono.subscribe(response ->
    System.out.println(response.getTextContent())
);
```

---
