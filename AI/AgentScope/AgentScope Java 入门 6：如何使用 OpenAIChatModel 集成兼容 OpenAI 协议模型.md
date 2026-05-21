在上一篇[文章](https://smartsi.blog.csdn.net/article/details/160694030)中，我们详细介绍了如何使用 `DashScopeChatModel` 集成阿里云百炼平台。本篇将聚焦另一个更通用的模型集成方式——`OpenAIChatModel`。

OpenAI 不仅是一个模型平台，更是一套 **事实标准的 API 协议**。从 vLLM、Ollama 到 DeepSeek、Moonshot、SiliconFlow 等众多模型平台，都兼容 OpenAI API 规范。这意味着：**只要会用 `OpenAIChatModel`，你就能接入半个国内外 LLM 生态**。

| 文章 | 模型平台 | 核心类 |
|------|---------|--------|
| 上一篇 | 阿里云百炼（DashScope） | `DashScopeChatModel` |
| **本篇** | **OpenAI / DeepSeek / vLLM / SiliconFlow** | **`OpenAIChatModel`** |
| 后续 | Ollama 本地部署 | `OllamaChatModel` |

---

## 1. 环境准备

### 1.1 Maven 依赖

> AgentScope Java 要求 **JDK 17+**

推荐使用 All-in-one 方式：
```xml
<dependency>
    <groupId>io.agentscope</groupId>
    <artifactId>agentscope</artifactId>
    <version>1.0.12</version>
</dependency>
```

> All-in-one 包默认包含 OpenAI SDK 集成，无需额外配置。详见 [AgentScope Java 入门 3：如何安装 AgentScope](https://smartsi.blog.csdn.net/article/details/160694030)。

### 1.2 获取 API Key

根据你要接入的平台，前往对应控制台获取 API Key：

| 平台 | 控制台 |
|------|-------|
| OpenAI 官方 | [OpenAI Platform](https://platform.openai.com/api-keys) |
| DeepSeek | [DeepSeek 开放平台](https://platform.deepseek.com/api_keys) |
| SiliconFlow（硅基流动） | [SiliconFlow](https://cloud.siliconflow.cn/) |
| 智普 | [智普 开放平台](http://open.bigmodel.cn/) |

建议通过环境变量注入：
```bash
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

---

## 2. 快速开始：调用 OpenAI 模型

通过 `OpenAIChatModel` 集成 OpenAI 模型，最小配置只需 `apiKey` + `modelName`：
```java
import io.agentscope.core.ReActAgent;
import io.agentscope.core.model.OpenAIChatModel;
import io.agentscope.core.message.Msg;
import io.agentscope.core.message.MsgRole;
import io.agentscope.core.message.content.TextBlock;

public class OpenAIQuickStart {
    public static void main(String[] args) {
        // 1. 创建模型
        OpenAIChatModel model = OpenAIChatModel.builder()
                .apiKey(System.getenv("OPENAI_API_KEY"))
                .modelName("gpt-4o")
                .build();

        // 2. 创建 Agent
        ReActAgent agent = ReActAgent.builder()
                .name("Assistant")
                .model(model)
                .build();

        // 3. 调用
        Msg response = agent.call(
                Msg.builder()
                        .role(MsgRole.USER)
                        .content(TextBlock.builder()
                                .text("你好，请用三句话介绍一下 OpenAI GPT-4o")
                                .build())
                        .build()
        ).block();

        System.out.println(response.getTextContent());
    }
}
```

> **关于 `.block()`**：AgentScope 基于 Project Reactor 实现响应式编程，`agent.call()` 返回 `Mono<Msg>`，调用 `.block()` 阻塞等待结果。详见第 4 篇说明。

---

## 3. OpenAIChatModel 核心配置

### 3.1 配置参数全解

```java
import io.agentscope.core.model.OpenAIChatModel;
import io.agentscope.core.model.GenerateOptions;
import io.agentscope.core.model.format.OpenAIChatFormatter;

OpenAIChatModel model = OpenAIChatModel.builder()
        .apiKey(System.getenv("OPENAI_API_KEY"))         // API 密钥（必填）
        .modelName("gpt-4o")                              // 模型名称（必填）
        .baseUrl("https://api.openai.com/v1")            // API 端点（兼容平台时必填）
        .stream(true)                                     // 是否启用流式输出，默认 true
        .organization("org-xxxx")                         // OpenAI 组织 ID（可选）
        .defaultOptions(GenerateOptions.builder()
                .temperature(0.7)
                .maxTokens(2000)
                .build())
        .formatter(new OpenAIChatFormatter())             // 消息格式化器（通常默认即可）
        .build();
```

| 配置项 | 是否必填 | 说明 |
|--------|----------|------|
| `apiKey` | 必填 | API 密钥。**强烈建议通过环境变量注入**。对于自托管 vLLM 等无需鉴权的服务，可填写任意非空字符串。 |
| `modelName` | 必填 | 模型名称，如 `gpt-4o`、`gpt-4o-mini`、`deepseek-chat` |
| `baseUrl` | 可选 | API 端点。OpenAI 官方默认 `https://api.openai.com/v1`，**接入兼容平台时必填**（如 DeepSeek 的 `https://api.deepseek.com`） |
| `stream` | 可选 | 是否启用流式输出，默认 `true` |
| `organization` | 可选 | OpenAI 组织 ID，仅 OpenAI 官方使用 |
| `defaultOptions` | 可选 | 默认生成选项（temperature、maxTokens 等） |
| `formatter` | 可选 | 消息格式化器（默认 `OpenAIChatFormatter`），仅在多智能体场景或非标准 API 时需要自定义 |

### 3.2 OpenAI 模型矩阵

| 模型名称 | 定位 | 特点 | 适用场景 |
|---------|------|------|---------|
| `gpt-4o` | 旗舰多模态 | 文本、视觉、音频统一理解 | 复杂推理、多模态任务 |
| `gpt-4o-mini` | 主力轻量 | 速度快、成本低 | 日常对话、生产首选 |
| `gpt-4-turbo` | 经典旗舰 | 高质量推理 | 长文档处理、复杂分析 |
| `o1-preview` | 推理专家 | 深度推理（思考模式） | 数学、代码、科学问题 |
| `o1-mini` | 推理轻量 | 推理能力 + 低成本 | 编码任务 |

> **模型选择建议**：
> - **快速验证 / 日常开发**：`gpt-4o-mini` — 性价比最高
> - **多模态 / 视觉理解**：`gpt-4o` — 原生支持图像、音频
> - **深度推理 / 复杂决策**：`o1-preview` — 内置 Chain-of-Thought

---

## 4. 接入 OpenAI 兼容平台

`OpenAIChatModel` 最大的价值不在于 OpenAI 本身，而在于它 **作为通用接入器** ——只需修改 `baseUrl` 和 `modelName`，即可接入任何兼容 OpenAI 协议的平台。

### 4.1 DeepSeek

DeepSeek 在推理与代码任务上表现出色，且价格极具竞争力：
```java
OpenAIChatModel model = OpenAIChatModel.builder()
        .apiKey(System.getenv("DEEPSEEK_API_KEY"))
        .modelName("deepseek-chat")           // 通用对话
        // .modelName("deepseek-reasoner")    // 推理增强（R1 系列）
        .baseUrl("https://api.deepseek.com")
        .build();
```

| 模型 | 适用场景 |
|------|---------|
| `deepseek-chat` | 通用对话、工具调用 |
| `deepseek-reasoner` | 复杂推理（含思维链） |

### 4.2 Moonshot（Kimi）

Moonshot 长上下文能力突出，适合长文档处理：
```java
OpenAIChatModel model = OpenAIChatModel.builder()
        .apiKey(System.getenv("MOONSHOT_API_KEY"))
        .modelName("moonshot-v1-32k")        // 32K 上下文
        // .modelName("moonshot-v1-128k")    // 128K 长上下文
        .baseUrl("https://api.moonshot.cn/v1")
        .build();
```

### 4.3 SiliconFlow（硅基流动）

SiliconFlow 聚合了 Qwen、DeepSeek、GLM 等多家模型，是国内开发者快速试用各类模型的便捷入口：
```java
OpenAIChatModel model = OpenAIChatModel.builder()
        .apiKey(System.getenv("SILICONFLOW_API_KEY"))
        .modelName("Qwen/Qwen2.5-72B-Instruct")
        .baseUrl("https://api.siliconflow.cn/v1")
        .build();
```

> SiliconFlow 模型名格式为 `供应商/模型名`，详见 [SiliconFlow 模型列表](https://siliconflow.cn/zh-cn/models)。

### 4.5 智普

```java
OpenAIChatModel model = OpenAIChatModel.builder()
        .apiKey(System.getenv("XAI_API_KEY"))
        .modelName("grok-2-latest")
        .baseUrl("https://api.x.ai/v1")
        .build();
```

### 4.6 主流兼容平台速查表

| 平台 | `baseUrl` | 典型 `modelName` | 特点 |
|------|-----------|------------------|------|
| OpenAI 官方 | `https://api.openai.com/v1` | `gpt-4o` | 标准、稳定 |
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` | 推理强、价格低 |
| Moonshot | `https://api.moonshot.cn/v1` | `moonshot-v1-32k` | 长上下文 |
| SiliconFlow | `https://api.siliconflow.cn/v1` | `Qwen/Qwen2.5-72B-Instruct` | 多模型聚合 |
| xAI | `https://api.x.ai/v1` | `grok-2-latest` | Grok 系列 |
| vLLM 自托管 | `http://localhost:8000/v1` | 取决于加载模型 | 私有化、高性能 |
| Together AI | `https://api.together.xyz/v1` | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | 开源模型托管 |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` | 极速推理 |

---

## 5. 生成参数调优

通过 `defaultOptions` 精细控制生成行为：

```java
import io.agentscope.core.model.GenerateOptions;
import io.agentscope.core.model.ToolChoice;

GenerateOptions options = GenerateOptions.builder()
        .temperature(0.7)               // 随机性 (0.0-2.0)
        .topP(0.9)                      // 核采样
        .maxTokens(2000)                // 最大输出 token 数
        .seed(42L)                      // 随机种子
        .frequencyPenalty(0.5)          // 频率惩罚（-2.0 到 2.0）
        .presencePenalty(0.5)           // 存在惩罚（-2.0 到 2.0）
        .toolChoice(ToolChoice.auto())  // 工具选择策略
        .build();

OpenAIChatModel model = OpenAIChatModel.builder()
        .apiKey(System.getenv("OPENAI_API_KEY"))
        .modelName("gpt-4o-mini")
        .defaultOptions(options)
        .build();
```

### 5.1 关键参数解读

| 参数 | 作用 | 建议 |
|------|------|------|
| `temperature` | 控制输出随机性 | 创意写作 0.8-1.0，精确任务 0.1-0.3，通用对话 0.5-0.7 |
| `topP` | 核采样阈值 | 通常 0.9-0.95，与 temperature 配合使用 |
| `maxTokens` | 最大生成 token 数 | 根据任务复杂度设置 |
| `frequencyPenalty` | 减少重复 token 出现频率 | 0.3-0.7 减少啰嗦 |
| `presencePenalty` | 鼓励引入新话题 | 0.3-0.7 增加多样性 |
| `seed` | 随机种子 | 需要可复现结果时设置固定值 |
| `toolChoice` | 工具调用策略 | `auto()` 自主决定，`none()` 禁用，`required()` 强制 |

### 5.2 工具选择策略

```java
ToolChoice.auto()                  // 模型自行决定（默认）
ToolChoice.none()                  // 禁止工具调用
ToolChoice.required()              // 强制调用工具（任意工具）
ToolChoice.specific("get_weather") // 强制调用指定工具
```

### 5.3 扩展参数

支持传递平台特有的参数（如 DeepSeek 的特殊字段、自定义 Header）：

```java
GenerateOptions options = GenerateOptions.builder()
        .additionalHeader("X-Custom-Header", "value")    // 自定义 HTTP 头
        .additionalBodyParam("custom_param", "value")    // 自定义请求体字段
        .additionalQueryParam("version", "v2")           // 自定义查询参数
        .build();
```
---

## 6. 与 ReActAgent 结合的完整示例

整合工具、超时重试、生成参数的完整示例（以 DeepSeek 为例）：
```java
import io.agentscope.core.ReActAgent;
import io.agentscope.core.model.OpenAIChatModel;
import io.agentscope.core.model.GenerateOptions;
import io.agentscope.core.model.ExecutionConfig;
import io.agentscope.core.message.Msg;
import io.agentscope.core.message.MsgRole;
import io.agentscope.core.message.content.TextBlock;
import io.agentscope.core.tool.Tool;
import io.agentscope.core.tool.ToolParam;
import io.agentscope.core.tool.Toolkit;
import java.time.Duration;

public class OpenAIAgentDemo {

    // 定义工具
    public static class WeatherTools {
        @Tool(name = "get_weather", description = "获取指定城市的天气")
        public String getWeather(
                @ToolParam(name = "city", description = "城市名称") String city) {
            return String.format("%s：晴天，气温 25 ℃", city);
        }
    }

    public static void main(String[] args) {
        // 1. 配置 DeepSeek 模型（兼容 OpenAI 协议）
        OpenAIChatModel model = OpenAIChatModel.builder()
                .apiKey(System.getenv("DEEPSEEK_API_KEY"))
                .modelName("deepseek-chat")
                .baseUrl("https://api.deepseek.com")
                .stream(true)
                .defaultOptions(GenerateOptions.builder()
                        .temperature(0.3)
                        .maxTokens(2000)
                        .build())
                .build();

        // 2. 注册工具
        Toolkit toolkit = new Toolkit();
        toolkit.registerTool(new WeatherTools());

        // 3. 构建 ReActAgent
        ReActAgent agent = ReActAgent.builder()
                .name("OpenAIAgent")
                .sysPrompt("你是一个天气助手，可以查询城市天气信息。")
                .model(model)
                .toolkit(toolkit)
                .maxIters(10)
                .modelExecutionConfig(ExecutionConfig.builder()
                        .timeout(Duration.ofMinutes(2))
                        .maxAttempts(3)
                        .initialBackoff(Duration.ofSeconds(1))
                        .maxBackoff(Duration.ofSeconds(10))
                        .backoffMultiplier(2.0)
                        .build())
                .build();

        // 4. 调用
        Msg response = agent.call(
                Msg.builder()
                        .role(MsgRole.USER)
                        .content(TextBlock.builder()
                                .text("北京今天天气如何？")
                                .build())
                        .build()
        ).block();

        System.out.println(response.getTextContent());
    }
}
```

> **替换说明**：将示例中的 DeepSeek 配置替换为 `apiKey` + `modelName` + `baseUrl` 即可切换到任意兼容平台，业务代码无需变动。这正是 OpenAI 协议作为"事实标准"的价值。

---

## 7. 多智能体协作下的 Formatter

在多智能体协作（Pipeline、MsgHub）场景下，需要使用 `OpenAIMultiAgentFormatter` 替代默认的 `OpenAIChatFormatter`：

```java
import io.agentscope.core.model.format.OpenAIMultiAgentFormatter;

OpenAIChatModel model = OpenAIChatModel.builder()
        .apiKey(System.getenv("OPENAI_API_KEY"))
        .modelName("gpt-4o")
        .formatter(new OpenAIMultiAgentFormatter())  // 多智能体格式化器
        .build();
```

| 场景 | 推荐 Formatter |
|------|----------------|
| 单智能体对话 | `OpenAIChatFormatter`（默认） |
| Pipeline 顺序执行 | `OpenAIMultiAgentFormatter` |
| MsgHub 群聊 | `OpenAIMultiAgentFormatter` |
| 多智能体辩论 | `OpenAIMultiAgentFormatter` |

> **进阶阅读**：多智能体协作详见 [通过 Pipeline 管道部署多智能体](#)。

---

## 9. 总结

`OpenAIChatModel` 是 AgentScope Java 中**最通用的模型集成入口**，核心要点：

| 要点 | 说明 |
|------|------|
| **核心类** | `OpenAIChatModel` |
| **最小配置** | `apiKey` + `modelName`（OpenAI 官方）或 + `baseUrl`（兼容平台） |
| **兼容平台** | DeepSeek、Moonshot、SiliconFlow、xAI、vLLM、Together AI、Groq 等 |
| **多模态支持** | `gpt-4o` 原生支持视觉，部分兼容平台需确认 |
| **工具调用** | 主流模型均支持，部分小模型可能受限 |
| **生成控制** | 通过 `defaultOptions` 调节 temperature、maxTokens、frequencyPenalty 等 |
| **Formatter** | 多智能体场景使用 `OpenAIMultiAgentFormatter` |

**核心价值**：一套 API、N 个平台。这种统一性极大降低了多模型切换的成本，使得开发者可以根据成本、能力、隐私需求灵活选择底层模型。

---

## 系列文章导航

| 篇目 | 主题 |
|------|------|
| 一 | AgentScope Java 入门：用 Java 构建生产级 AI 智能体的全新范式 |
| 二 | Spring AI Alibaba 与 AgentScope 的定位与区别 |
| 三 | AgentScope Java 入门：如何安装 AgentScope |
| 四 | 搭建第一个 ReAct 智能体 |
| 五 | DashScopeChatModel 百炼模型集成 |
| **六（本文）** | **OpenAIChatModel 集成兼容 OpenAI 协议模型** |
| 七 | 思考模式（Thinking Mode）详解 |
| 八 | Hook 钩子机制详解 |
| 九 | Tool 工具系统详解 |
| 十 | MCP 协议集成 |
| 十一 | Agent Skills 模块化技能包 |
| 十二 | RAG 检索增强生成 |
| 十三 | EmbeddingModel 与硅基流动实战 |
| 十四 | 本地知识库问答助手 |
| 十五 | Human-in-the-Loop 人工审核 |
| 十六 | PlanNotebook 任务规划 |
| 十七 | Structured Output 结构化输出 |
| 十八 | Pipeline 管道部署多智能体 |
