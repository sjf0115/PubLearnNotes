随着 LLM 应用的飞速发展，越来越多的 Agent 应用开始走近每个人。围绕着 Agent 应用的核心，目前业界有零代码、低代码和高代码三条主流的技术路线。AgentScope 作为 Python 社区中受到广泛应用的高代码框架，在 Java 生态下的需求也越来越大。


## 1. 第一性原则：透明度

AgentScope 的首要设计目标是对开发者透明。当下，许多 Agent 框架将底层的调度进行了深度的封装，这固然会给用户带来一些概念上的简化，但是也带来了遇到问题时排查的复杂度。AgentScope 不同：
- Prompt Engineering：用户可以自己修改所有提示词相关的内容。
- API 调用：每一次 API 调用都能够被定位。
- Agent 构建：所有 Agent 的配置都来自用户确定性的配置。
- 决策过程：Agent 的推理、执行过程都可以通过 Hook 对外暴露。

## 2. 三分钟构建一个智能体

AgentScope 提供了开箱即用的 ReAct 智能体 `ReActAgent` 供开发者使用。它同时支持以下功能：
- **基础功能**
    - 支持围绕 `reasoning` 和 `acting` 的钩子函数（hooks）
    - 支持结构化输出
- **实时介入（Realtime Steering）**
    - 支持用户中断
    - 支持自定义中断处理
- **工具**
    - 支持同步/异步工具函数
    - 支持流式工具响应
    - 支持并行工具调用
    - 支持 MCP 服务器
- **记忆**
    - 支持智能体自主管理长期记忆
    - 支持"静态"的长期记忆管理

通过下面几个步骤可以轻松搭建一个简单的智能体。

### 2.1 Maven

> AgentScope Java 要求 **JDK 17+**

推荐使用 All-in-one 方式，大多数情况下用 all-in-one 一个依赖就可以搞定：
```xml
<dependency>
    <groupId>io.agentscope</groupId>
    <artifactId>agentscope</artifactId>
    <version>1.0.12</version>
</dependency>
```
All-in-one 包默认带如下依赖，不用额外配置：
- DashScope SDK（通义千问系列模型）
- MCP SDK（模型上下文协议）
- Reactor Core、Jackson、SLF4J（基础框架）

> 详细请参考上一篇博文：[AgentScope Java 入门系列：如何安装 AgentScope](https://smartsi.blog.csdn.net/article/details/160694030)

### 2.2 获取 API Key

前往 [阿里云百炼控制台](https://bailian.console.aliyun.com/) 创建 API Key，建议通过环境变量注入：

```bash
export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

### 2.3 ReActAgent

```java
public class HelloAgentScope {
    public static void main(String[] args) {
        // 创建 ReActAgent
        ReActAgent agent = ReActAgent.builder()
            .name("Assistant")
            .model(DashScopeChatModel.builder()
                .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                .modelName("qwen3-max")
                .build())
            .build();

        // 调用智能体
        Msg response = agent.call(
            Msg.builder()
                .role(MsgRole.USER)
                .content(TextBlock.builder()
                        .text("你好，请介绍一下自己")
                        .build())
                .build()
        ).block();
        System.out.println(response.getTextContent());
    }
}
```

至此，一个 Agent 就构建完成了。在这个示例中，ReActAgent 是 AgentScope 的核心，我们后面几乎所有的功能都是基于它的。在这个示例中我们只应用到了2个必需参数 `name` 和 `model`，除此之外你还可以应用其他参数来完成后续功能：

| 参数 | 是否必填 | 描述 |
|------|-----------|------|
| `name` | 必需 | 智能体的名称 |
| `model` | 必需 | 智能体用于生成响应的模型 |
| `sysPrompt` | 建议设置 | 智能体的系统提示 |
| `toolkit` |  | 用于注册/调用工具函数的工具模块 |
| `memory` |  | 用于存储对话历史的短期记忆 |
| `description` | | 智能体的描述信息 |
| `generateOptions` | | LLM 生成参数（temperature、topP、maxTokens 等） |
| `toolExecutionContext` |  | 工具执行上下文，用于向工具注入依赖 |
| `planNotebook` |  | 计划管理器 |
| `longTermMemory` |  | 长期记忆 |
| `longTermMemoryMode` |  | 长期记忆的管理模式：`AGENT_CONTROL`（智能体自主控制）、`STATIC_CONTROL`（静态管理）、`BOTH`（两者皆有） |
| `maxIters` | | 智能体生成响应的最大迭代次数（默认：10） |
| `hooks` |  | 用于自定义智能体行为的事件钩子 |
| `modelExecutionConfig` | | 模型调用的超时/重试配置 |
| `toolExecutionConfig` | | 工具调用的超时/重试配置 |

## 3. 架构概览

和 Python 版本类似，AgentScope Java 采用分层架构。

![](https://mmecoa.qpic.cn/sz_mmecoa_png/qdzZBE73hWtmaYEia6DbKxQ8JcJ98tu6D1B8VmlUuqgzxzyjScjEYBiah882iaEI5qb7uuW6pcPRicY02AI10MK7Og/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=10005&wx_lazy=1#imgIndex=1)

### 3.1 基础组件层（Foundational Components）

- Message：统一的消息抽象对象，通过一套数据结构支持文本、图像、音频、视频。
- Model API：支持 DashScope、OpenAI 等主流模型提供商。通过 Formatter 机制屏蔽不同模型提供商的格式差异。
- Tool：允许用户定义工具给 LLM 使用，支持同步/异步、流式/非流式等 API 风格。

### 3.2 智能体基础设施层（Agent-level Infrastructure）

- ReAct 范式：核心 Agentic 实现，通过推理（Reasoning）再行动（Acting）的迭代循环。
- Agent Hooks：运行于 ReActAgent 内部，允许用户对 Agent 执行的过程进行监测、修改。
- 状态管理：会话持久化组件，支持用户对话状态的保存和恢复。

### 3.3 多智能体协作层（Multi-Agent Cooperation）

- MsgHub：支持多个 Agent 之间共享消息，实现多 Agent 沟通协作的工具。
- Pipeline：组合多个 Agent 按照特定（顺序、并行等）策略执行的工具。

### 3.4 部署层（Deployment）

- AgentScope Runtime：解决分布式部署与安全隔离问题的企业级运行时基础设施，提供工具运行沙箱、A2A 协议、远程部署等能力。
- AgentScope Studio：提供开发阶段到运行阶段的可视化调试、观测能力，为开发者从 0 到 1 的开发提速。

## 4. Reasoning and Acting

ReAct（Reasoning and Acting）是 AgentScope 最核心的实现范式。其设计思路很简单：**将思考和执行分离，通过迭代循环解决问题**。

### 4.1 工作原理

**Reasoning（推理）阶段**：Agent 会基于当前的上下文分析，决定下一步行动：
- 理解用户意图
- 评估已有信息（上下文）
- 确定需要调用的工具及参数

**Acting（行动）阶段**：执行 Reasoning 阶段所需的获取数据行为。
- 并行执行工具调用
- 收集执行结果
- 将结果计入记忆

**迭代控制**：ReActAgent 会不断执行 Reasoning 和 Acting 的迭代，如果模型在最大迭代轮内完成迭代则会正常结束，如果未完成则会触发 summary 的能力，进行会话总结。

### 4.2 为 ReActAgent 添加工具

为了让 ReActAgent 真正可以实现 Acting，需要为 ReActAgent 添加对应的工具。这里以一个 Weather Assistant 为例子：
```java
// 定义工具类
public class WeatherTools {
    @Tool(description = "获取指定城市的天气信息")
    public String getWeather(
        @ToolParam(name = "city", description = "城市名称") String city) {
        // 实际应用中调用天气 API
        return String.format("%s：晴天，气温 25 ℃", city);
    }
}

// 注册工具
Toolkit toolkit = new Toolkit();
toolkit.registerTool(new WeatherTools());

// 构建带工具的 ReActAgent
ReActAgent agent = ReActAgent.builder()
    .name("WeatherAssistant")
    .sysPrompt("你是一个天气助手，可以查询城市天气信息。")
    .model(DashScopeChatModel.builder()
        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
        .modelName("qwen3-max")
        .build())
    .toolkit(toolkit)
    .build();

// 调用智能体
Msg response = agent.call(
    Msg.builder()
                .role(MsgRole.USER)
                .content(TextBlock.builder()
                        .text("北京今天天气如何？")
                        .build())
                .build()
).block();
```

执行流程：
```
用户问题：北京今天天气如何？
    ↓
[推理] 需要查天气，决定调用 getWeather("北京")
    ↓
[行动] 执行工具 → "北京：晴天，气温 25℃"
    ↓
[推理] 已获取信息，生成回答
    ↓
回答：根据查询结果，北京今天晴天，气温 25℃
```

## 5. ReActAgent 核心特性

除了基础的 Reasoning 和 Acting 能力，AgentScope 的 ReActAgent 还具备多个特性。

### 5.1 多模态消息支持

ReActAgent 可以处理多模态输入，不限于纯文本：
```java
// 创建支持视觉的 ReActAgent（使用视觉模型）
ReActAgent visionAgent = ReActAgent.builder()
    .name("VisionAssistant")
    .model(DashScopeChatModel.builder()
        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
        .modelName("qwen3-vl-plus")  // 视觉模型
        .build())
    .build();
// 发送包含图片的消息
Msg response = visionAgent.call(
    Msg.builder()
        .role(MsgRole.USER)
        .content(List.of(
            TextBlock.builder().text("请分析这张图片的内容").build(),
            ImageBlock.builder().source(URLSource.builder().url("https://example.com/image.jpg").build()).build()
        ))
        .build()
).block();
```
支持的多模态内容类型：TextBlock、ImageBlock、AudioBlock、VideoBlock。

### 5.2 钩子机制

为 ReActAgent 添加钩子，监控和扩展其行为。这里以前文中用到的 WeatherAssistant 为例子添加钩子，实时看到智能体的思考和执行过程：
```java
// 定义调试钩子，显示完整的 ReAct 执行过程
Hook debugHook = new Hook() {
    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        try {
            switch (event) {
                case PreReasoningEvent e -> {
                    System.out.println("\n[推理] 智能体开始思考...");
                }
                case PostReasoningEvent e -> {
                    System.out.println("[推理] 推理结果：" + new ObjectMapper().writeValueAsString(e.getReasoningMessage()));
                }
                case PostActingEvent e -> {
                    System.out.println("[行动] 执行工具 → " + new ObjectMapper().writeValueAsString(e.getToolResult()));
                }
                case PostCallEvent e -> {
                    System.out.println("[推理] 已获取信息，生成回答");
                    System.out.println("回答：" + e.getFinalMessage().getTextContent());
                }
                default -> {}
            } ;
        } catch (JsonProcessingException e) {
            ...
        }
        return Mono.just(event);
    }
};

// 将钩子添加到 WeatherAssistant
ReActAgent weatherAgent = ReActAgent.builder()
    .name("WeatherAssistant")
    .sysPrompt("你是一个天气助手，可以查询城市天气信息。")
    .model(DashScopeChatModel.builder()
           .apiKey(System.getenv("DASHSCOPE_API_KEY"))
           .modelName("qwen3-max")
           .build())
    .toolkit(toolkit) // 前文中定义的 Toolkit
    .hook(debugHook)  // 添加调试钩子
    .build();

// 查询天气
Msg response = weatherAgent.call(
    Msg.builder()
    .role(MsgRole.USER)
    .content(TextBlock.builder()
             .text("北京今天天气如何？")
             .build())
    .build()
).block();

// 输出示例：
// [推理] 智能体开始思考...
// [推理] 推理结果：{"id":"xxx","name":"WeatherAssistant","role":"ASSISTANT","content":[{"type":"tool_use","id":"call_xxx","name":"getWeather","input":{"city":"北京"},"content":null}],"metadata":null,"timestamp":"xxx"}
// [行动] 执行工具 → {"type":"tool_result","id":"call_xxx","name":"getWeather","output":[{"type":"text","text":"\"北京：晴天，气温 25 ℃\""}],"metadata":{}}
// [推理] 智能体开始思考...
// [推理] 推理结果：{"id":"xxx","name":"WeatherAssistant","role":"ASSISTANT","content":[{"type":"text","text":"北京今天天气晴朗，气温为25℃。建议外出时注意防晒，祝您拥有愉快的一天！"}],"metadata":null,"timestamp":"xxx"}
// [推理] 已获取信息，生成回答
// 回答：北京今天天气晴朗，气温为25℃。建议外出时注意防晒，祝您拥有愉快的一天！
```

### 5.3 会话持久化

保存和恢复 ReActAgent 的状态：
```java
// 创建 ReActAgent
ReActAgent agent = ReActAgent.builder()
    .name("PersistentAgent")
    .model(DashScopeChatModel.builder()
        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
        .modelName("qwen3-max")
        .build())
    .memory(new InMemoryMemory())
    .build();

// 保存会话
SessionManager.forSessionId("session-001")
    .withJsonSession(Path.of("./sessions"))
    .addComponent(agent)
    .saveSession();

// 下次启动时恢复
SessionManager.forSessionId("session-001")
    .withJsonSession(Path.of("./sessions"))
    .addComponent(agent)
    .loadIfExists();

// agent 现在恢复到了之前的状态，可以继续对话
```

### 5.4 结构化输出

让 ReActAgent 返回类型安全的结构化数据：
```java
// 定义输出结构
public class WeatherReport {
    public String city;
    public int temperature;
    public String condition;
    public List<String> suggestions;
}

// ReActAgent 调用时指定输出类型
Msg response = agent.call(
    Msg.builder()
                .role(MsgRole.USER)
                .content(TextBlock.builder()
                        .text("分析北京的天气并给出建议")
                        .build())
                .build(),
    WeatherReport.class  // 指定结构化输出类型
).block();

// 提取结构化数据
WeatherReport report = response.getStructuredData(WeatherReport.class);
System.out.println("城市: " + report.city);
System.out.println("温度: " + report.temperature);
```
避免了文本解析的不确定性，编译期就能发现类型错误。

### 5.5 多智能体协作

多个 ReActAgent 可以通过 Pipeline 协作：
```java
// 创建模型配置
DashScopeChatModel model = DashScopeChatModel.builder()
    .apiKey(System.getenv("DASHSCOPE_API_KEY"))
    .modelName("qwen3-max")
    .build();

// 创建多个 ReActAgent
ReActAgent dataCollector = ReActAgent.builder()
    .name("DataCollector")
    .model(model)
    .build();
ReActAgent dataAnalyzer = ReActAgent.builder()
    .name("DataAnalyzer")
    .model(model)
    .build();
ReActAgent reportGenerator = ReActAgent.builder()
    .name("ReportGenerator")
    .model(model)
    .build();

// 顺序执行：智能体依次处理
Msg result = Pipelines.sequential(
    List.of(dataCollector, dataAnalyzer, reportGenerator),
    inputMsg
).block();

// 并行执行：多个智能体同时处理
List<Msg> results = Pipelines.fanout(
    List.of(dataCollector, dataAnalyzer, reportGenerator),
    inputMsg
).block();
```
