在上一篇[文章](https://smartsi.blog.csdn.net/article/details/160694030)中，我们搭建了第一个 ReAct 智能体，让它能思考、能行动。但 Agent 的能力上限取决于它的"大脑"——**大语言模型**。推理能力、工具调用能力、多模态理解能力，都由底层模型决定。

AgentScope Java 支持接入多种主流大语言模型，本系列将逐一介绍：

| 文章 | 模型平台 | 核心类 |
|------|---------|--------|
| **本篇** | 阿里云百炼（DashScope） | `DashScopeChatModel` |
| 下一篇 | OpenAI / DeepSeek / vLLM | `OpenAIChatModel` |
| 后续 | Ollama 本地部署 | `OllamaChatModel` |
| 后续 | Anthropic Claude | `AnthropicChatModel` |
| 后续 | Google Gemini / Vertex AI | `GeminiChatModel` |

开篇选择 **DashScope（阿里云百炼）**，原因很务实：它是国内开发者最容易获取、最稳定、模型能力最强的平台之一，通义千问（Qwen）系列在工具调用、推理和多模态方面表现优异，与 AgentScope 的 ReAct 范式配合默契。

---

## 1. 环境准备

### 1.1 Maven 依赖

> AgentScope Java 要求 **JDK 17+**

推荐使用 All-in-one 方式，大多数情况下一个依赖即可搞定：
```xml
<dependency>
    <groupId>io.agentscope</groupId>
    <artifactId>agentscope</artifactId>
    <version>1.0.12</version>
</dependency>
```

All-in-one 包默认包含 DashScope SDK，无需额外配置。如果你需要精细控制依赖，也可以使用 `agentscope-core` + `agentscope-model-dashscope` 的方式，详见 [AgentScope Java 入门 3：如何安装 AgentScope](https://smartsi.blog.csdn.net/article/details/160694030)。

### 1.2 获取 API Key

前往 [阿里云百炼控制台](https://bailian.console.aliyun.com/) 创建 API Key，建议通过环境变量注入：
```bash
export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

---

## 2. 快速开始：3 行代码调用百炼模型

阿里云百练 LLM 平台，提供通义千问系列模型。通过 DashScopeChatModel 来集成通义千问系列模型：
```java
DashScopeChatModel model = DashScopeChatModel.builder()
        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
        .modelName("qwen3.5-35b-a3b")
        .build();
```
最简配置下，你只需要 3 行代码就能让 Agent 跑起来：
- 创建模型
- 创建 Agent
- Agent 调用

```java
public class DashScopeQuickStart {
    public static void main(String[] args) {
        // 1. 创建模型
        DashScopeChatModel model = DashScopeChatModel.builder()
                .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                .modelName("qwen3.5-35b-a3b")
                .build();

        // 2. 创建 Agent
        ReActAgent agent = ReActAgent.builder()
                .name("Assistant")
                .model(model)
                .build();

        // 3. 调用
        Msg msg = Msg.builder()
                .role(MsgRole.USER)
                .textContent("你好，请用三句话介绍一下 AgentScope Java")
                .build();
        Msg response = agent.call(msg).block();
        System.out.println(response.getTextContent());
    }
}
```
> **关于 `.block()`**：AgentScope 基于 Project Reactor 实现响应式编程，`agent.call()` 返回 `Mono<Msg>`，调用 `.block()` 阻塞等待结果。详见第 4 篇文章中的说明。

> **关于消息构造**：`Msg.builder()` 有两种常用方式构造内容：
> - `.content(TextBlock.builder().text("...").build())` — 标准方式，支持多模态扩展
> - `.textContent("...")` — 快捷方式，等价于 `.content(TextBlock.builder().text("...").build())`

就是这么简单。`DashScopeChatModel` 负责与百炼平台通信，`ReActAgent` 负责编排推理与行动。最小配置只需 `apiKey` + `modelName` 两个必填参数。
---

## 3. DashScopeChatModel 核心配置

`DashScopeChatModel` 提供了丰富的配置选项，让你能够精确控制模型的行为。

### 3.1 配置参数

```java
DashScopeChatModel model = DashScopeChatModel.builder()
        .apiKey(System.getenv("DASHSCOPE_API_KEY"))      // API 密钥（必填）
        .modelName("qwen3.5-35b-a3b")                        // 模型名称（必填）
        //.baseUrl("https://dashscope.aliyuncs.com/...")   // 自定义 API 端点（可选）
        .stream(true)                                     // 是否启用流式输出，默认 true
        .enableThinking(true)                             // 启用思考模式，展示推理过程
        .enableSearch(true)                               // 启用联网搜索，获取实时信息
        .endpointType(EndpointType.AUTO)                  // API 端点类型，默认自动识别
        .defaultOptions(GenerateOptions.builder()          // 生成参数（温度、token 数等）
                .temperature(0.7)
                .maxTokens(2000)
                .build())
        .formatter(new DashScopeChatFormatter())          // 消息格式化器（通常默认即可）
        .build();
```

| 配置项 | 是否必填 | 说明 |
|--------|------|------|
| `apiKey` | 必填 | DashScope API 密钥。**强烈建议通过环境变量注入**，避免硬编码泄露。 |
| `modelName` | 必填 | 模型名称，如 `qwen3-max`、`qwen-vl-max` |
| `baseUrl` | 可选 | 自定义 API 端点（可选）。大多数情况下无需配置。如果你需要通过私有网关、代理或 VPC 内网访问百炼服务，可以自定义。 |
| `stream` | 可选 | 是否启用流式输出，默认 `true`。启用后模型会以流式方式返回内容，适合实时展示。如果关闭（`false`），则等待完整响应后一次性返回。 |
| `enableThinking` | 可选 | 启用思考模式，模型会展示推理过程 |
| `enableSearch` | 可选 | 启用联网搜索，获取实时信息 |
| `endpointType` | 可选 | API 端点类型（默认 AUTO 自动识别），可选 TEXT（强制文本 API）或 MULTIMODAL（强制多模态 API）|
| `defaultOptions` | 可选 | 默认生成选项（temperature、maxTokens 等）|
| `formatter` | 可选 | 消息格式化器（默认 DashScopeChatFormatter）。负责在 AgentScope 内部消息格式与 DashScope API 格式之间转换。只有在接入非标准兼容 API 时才可能需要自定义。|

### 3.2 百练模型

百炼提供了丰富的模型矩阵，覆盖从旗舰到轻量的全场景，可以通过 `modelName` 配置指定：

| 模型名称 | 定位 | 特点 | 适用场景 |
|---------|------|------|---------|
| `qwen3.6-max-preview` | 旗舰 | 能力最强，推理、代码、Agent 效果最佳 | 复杂推理、高质量输出 |
| `qwen3.6-plus` | 主力 | 速度快、成本低，多模态能力强 | 日常对话、视觉理解、生产环境首选 |
| `qwen3.6-flash` | 轻量 | 极速响应，成本最低 | 简单问答、高并发场景 |
| `qwen3.5-omni-plus` | 多模态 | 支持文本、图像、音频、视频统一理解 | 多媒体内容分析 |
| `qwen-plus` | 经典 | 稳定可靠，性价比高 | 通用对话、工具调用 |

此外，百炼还接入了第三方模型：`deepseek-v4-pro`、`kimi-k2.6`、`glm-5.1` 等，都可以通过 DashScope API 调用。

### 3.3 思考模式

思考模式（Thinking Mode） 是通义千问 3 系列模型（qwen3-max、qwen3-plus 等）独有的能力。可以通过 `enableThinking` 配置来启用。模型在给出最终回答之前，会先输出一段内部推理过程（Chain-of-Thought），展示它是如何一步步分析问题、拆解任务、做出决策的。你可以把它理解为：模型在回答你之前，先在草稿纸上写了一遍"解题思路"。

启用后模型会在回答前展示完整的推理过程（类似 Chain-of-Thought），对 ReActAgent 的调试和可解释性极有价值：
```java
DashScopeChatModel model = DashScopeChatModel.builder()
        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
        .modelName("qwen3.5-35b-a3b")
        .enableThinking(true)  // 启用思考模式（自动开启流式）
        .defaultOptions(GenerateOptions.builder()
                .thinkingBudget(5000)  // 控制思考 token 预算
                .build())
        .build();
```

启用思考模式后，AgentScope 会将模型的推理内容包装为 ThinkingBlock，你可以通过 Hook 机制 捕获并展示：
```java
public class ThinkingHook implements Hook {
    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        if (event instanceof PreReasoningEvent preReasoning) {
            // LLM 推理前 - 开始思考
            String name = preReasoning.getAgent().getName();
            System.out.println("\n--------------------------------------------");
            System.out.println("Agent [" + name + "] 开始思考 ....");
        } else if (event instanceof PostReasoningEvent postReasoning) {
            // LLM 推理完成后 - 输出思考内容
            String name = postReasoning.getAgent().getName();
            Msg reasoningMsg = postReasoning.getReasoningMessage();
            for (ContentBlock block : reasoningMsg.getContent()) {
                if (block instanceof ThinkingBlock thinking) {
                    System.out.println("\n--------------------------------------------");
                    System.out.println("Agent [" + name + "] 思考\n" + thinking.getThinking());
                }
            }
        }
        return Mono.just(event);
    }
}
```
> **进阶阅读**：思考模式的详细配置与输出解析，详见 [思考模式（Thinking Mode）详解](#)。

### 3.4 联网搜索

启用 `enableSearch` 后模型可以实时检索互联网信息，回答时效性问题：
```java
public class EnableSearchExample {
    public static void main(String[] args) {
        // 模型
        DashScopeChatModel model = DashScopeChatModel.builder()
                .apiKey(System.getenv("DASHSCOPE_API_KEY")) // API 密钥
                .modelName("qwen3.5-35b-a3b") // 模型名称
                .enableSearch(true) // 启用联网搜索，获取实时信息
                .build();

        // 创建 ReActAgent
        ReActAgent agent = ReActAgent.builder()
                .name("Assistant")
                .sysPrompt("你是一个可以联网搜索的助手，能够回答最新的信息。")
                .model(model)
                .build();

        // 调用智能体
        Msg msg = Msg.builder()
                .role(MsgRole.USER)
                .textContent("你好，请问一下截止到2026年5月21号马来西亚羽毛球大师赛最新结果，简单几句话说一下结果")
                .build();
        Msg response = agent.call(msg).block();
        System.out.println(response.getTextContent());
    }
}
```
回答结果如下所示：
```
根据知识库信息，以下是截止到**2026年5月21日马来西亚羽毛球大师赛**的简要赛况：

## 🏸 最新比赛结果摘要

| 项目 | 国羽成绩 | 说明 |
|------|---------|------|
| **整体战绩** | 12胜1负 | 首轮全部结束 |
| **男单** | 4胜1负 | 翁泓阳遗憾首轮出局 |
| **女单** | 2场全胜 | 陈雨菲相对轻松，韩千禧惊险过关 |
| **混双** | 4对全部晋级 | 过程都比较艰难 |
| **双打** | 多场比赛晋级 | 女双胡珂源/林祥毅成功复仇印尼组合 |
```
可以看到模型实时检索到互联网最新信息来回答问题。

### 3.5 端点类型控制

DashScope 模型支持 **文本 API** 和 **多模态 API** 两种端点。框架默认根据模型名自动识别（如 `qwen-vl-*`、`qwen3.5-omni-*` 自动走多模态端点）。当自动识别不准确时（例如使用自定义模型名称或兼容 API），可以手动指定端点类型：
```java
// 强制使用多模态 API（适用于包含图片/音频等内容的场景）
DashScopeChatModel model = DashScopeChatModel.builder()
        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
        .modelName("qwen3.5-35b-a3b")
        .endpointType(EndpointType.MULTIMODAL)
        .build();

// 强制使用文本 API
DashScopeChatModel model = DashScopeChatModel.builder()
        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
        .modelName("qwen3.5-35b-a3b")
        .endpointType(EndpointType.TEXT)
        .build();
```

## 4. 生成参数调优：让模型输出更符合预期

通过 `defaultOptions` 可以精细控制模型的生成行为：
```java
GenerateOptions options = GenerateOptions.builder()
        .temperature(0.7)           // 随机性 (0.0-2.0)，越低越确定性
        .topP(0.9)                  // 核采样，控制输出多样性
        .topK(40)                   // Top-K 采样
        .maxTokens(2000)            // 最大输出 token 数
        .seed(42L)                  // 随机种子，固定后可复现结果
        .toolChoice(new ToolChoice.Auto())  // 工具选择策略
        .build();

DashScopeChatModel model = DashScopeChatModel.builder()
        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
        .modelName("qwen3.6-plus")
        .defaultOptions(options)
        .build();
```

### 关键参数解读

| 参数 | 作用 | 建议 |
|------|------|------|
| `temperature` | 控制输出随机性 | 创意写作 0.8-1.0，精确任务 0.1-0.3，通用对话 0.5-0.7 |
| `topP` | 核采样阈值 | 通常 0.9-0.95，与 temperature 配合使用 |
| `maxTokens` | 最大生成 token 数 | 根据任务复杂度设置，长文档摘要可设 4096 或更高 |
| `seed` | 随机种子 | 需要可复现结果时设置固定值 |
| `toolChoice` | 工具调用策略 | `Auto()` 让模型自主决定，`None()` 禁用工具，`Required()` 强制调用 |

---

## 5. 与 ReActAgent 结合的完整示例

将前面所有知识整合，以下是一个生产级的配置示例：
```java
public class DashScopeAgentDemo {
    public static void main(String[] args) {
        // 1. 配置百炼模型
        DashScopeChatModel model = DashScopeChatModel.builder()
                .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                .modelName("qwen3.6-plus")
                .stream(true)
                .enableThinking(true)
                .defaultOptions(GenerateOptions.builder()
                        .temperature(0.5)
                        .maxTokens(2000)
                        .build())
                .build();

        // 2. 构建 ReActAgent
        ReActAgent agent = ReActAgent.builder()
                .name("DashScopeAgent")
                .sysPrompt("你是一位专业的技术助手，擅长使用工具解决复杂问题。")
                .model(model)
                .maxIters(10)
                .build();

        // 3. 调用
        Msg response = agent.call(
                Msg.builder()
                        .role(MsgRole.USER)
                        .textContent("解释 ReAct 范式在 Agent 开发中的作用")
                        .build()
        ).block();

        System.out.println(response.getTextContent());
    }
}
```

---

## 6. 总结

DashScope（阿里云百炼）是 AgentScope Java 在国内场景下最推荐的模型平台，核心要点回顾：

| 要点 | 说明 |
|------|------|
| **核心类** | `DashScopeChatModel` |
| **最小配置** | `apiKey` + `modelName`，3 行代码即可运行 |
| **特色功能** | `enableThinking`（思考模式）、`enableSearch`（联网搜索） |
| **模型选择** | `qwen3.6-plus` 是日常首选，`qwen3.6-max-preview` 用于复杂推理 |
| **生成控制** | 通过 `defaultOptions` 精细调节 temperature、maxTokens 等 |
| **多模态** | 支持文本、图像、音频、视频统一输入 |

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
| 七 | [AgentScope Java 入门7：如何使用 OllamaChatModel 集成 Ollama 自托管平台](https://smartsi.blog.csdn.net/article/details/161335847) |
