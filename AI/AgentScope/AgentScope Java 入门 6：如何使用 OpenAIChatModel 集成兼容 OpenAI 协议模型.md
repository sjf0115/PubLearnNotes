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
    .modelName("deepseek-v4-flash")
    .baseUrl("https://api.deepseek.com")
    .build();
```

| 模型 | 适用场景 | 备注 |
|------|---------|---------|
| `deepseek-chat` | 通用对话、工具调用 | 将于 2026/07/24 弃用，对应 deepseek-v4-flash 的非思考模式 |
| `deepseek-reasoner` | 复杂推理（含思维链） | 将于 2026/07/24 弃用，对应 deepseek-v4-flash 的思考模式 |
| `deepseek-v4-flash` | 日常对话、简单 Agent 任务、工具调用 | |
| `deepseek-v4-pro` | 复杂推理 | |

### 4.2 Moonshot（Kimi）

Moonshot 长上下文能力突出，适合长文档处理：
```java
OpenAIChatModel model = OpenAIChatModel.builder()
        .apiKey(System.getenv("MOONSHOT_API_KEY"))
        .modelName("moonshot-v1-32k")        // 32K 上下文
        .baseUrl("https://api.moonshot.cn/v1")
        .build();
```

### 4.3 SiliconFlow（硅基流动）

SiliconFlow 聚合了 Qwen、DeepSeek、GLM 等多家模型，是国内开发者快速试用各类模型的便捷入口：
```java
OpenAIChatModel model = OpenAIChatModel.builder()
    .apiKey(System.getenv("SILICON_FlOW_API_KEY"))
    .modelName("Pro/deepseek-ai/DeepSeek-V3.2")
    .baseUrl("https://api.siliconflow.cn/v1")
    .build();
```

> SiliconFlow 模型名格式为 `供应商/模型名`，详见 [SiliconFlow 模型列表](https://siliconflow.cn/models)。

---

## 5. 生成参数调优

通过 `defaultOptions` 精细控制生成行为：
```java
import io.agentscope.core.model.GenerateOptions;
import io.agentscope.core.model.ToolChoice;

GenerateOptions options = GenerateOptions.builder()
    .temperature(0.7)           // // 随机性 (0.0-2.0)
    .topP(0.9)                  // 核采样(0.0-1.0)
    .topK(40)                   // Top-K 采样
    .maxTokens(2000)            // 最大输出 token 数
    .seed(42L)                  // 随机种子
    .toolChoice(new ToolChoice.Auto())  // 工具选择策略
    .build();

OpenAIChatModel model = OpenAIChatModel.builder()
    .apiKey(System.getenv("SILICON_FlOW_API_KEY"))
    .modelName("Pro/deepseek-ai/DeepSeek-V3.2")
    .baseUrl("https://api.siliconflow.cn/v1")
    .generateOptions(options)
    .build();
```

关键参数解读：

| 参数 | 类型 | 说明 |
|------|------|------|
| `temperature` | Double | 控制随机性，0.0-2.0 |
| `topP` | Double | 核采样阈值，0.0-1.0 |
| `topK` | Integer | 限制候选 token 数量 |
| `maxTokens` | Integer | 最大生成 token 数 |
| `maxCompletionTokens` | Integer | 最大完成 token 数 |
| `thinkingBudget` | Integer | 思考 token 预算 |
| `reasoningEffort` | String | 推理强度（如 `low`、`medium`、`high`） |
| `frequencyPenalty` | Double | 频率惩罚，-2.0-2.0 |
| `presencePenalty` | Double | 存在惩罚，-2.0-2.0 |
| `seed` | Long | 随机种子 |
| `toolChoice` | ToolChoice | 工具选择策略 |

---

## 6. 与 ReActAgent 结合的完整示例

整合工具、超时重试、生成参数的完整示例（以 DeepSeek 为例）：
```java
public static void main(String[] args) {
    // 1. 模型
    GenerateOptions options = GenerateOptions.builder()
            .temperature(0.7)           // // 随机性 (0.0-2.0)
            .topP(0.9)                  // 核采样(0.0-1.0)
            .topK(40)                   // Top-K 采样
            .maxTokens(2000)            // 最大输出 token 数
            .seed(42L)                  // 随机种子
            .toolChoice(new ToolChoice.Auto())  // 工具选择策略
            .build();

    OpenAIChatModel model = OpenAIChatModel.builder()
            .apiKey(System.getenv("SILICON_FlOW_API_KEY"))
            .modelName("Pro/deepseek-ai/DeepSeek-V3.2")
            .baseUrl("https://api.siliconflow.cn/v1")
            .generateOptions(options)
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
    Msg msg = Msg.builder()
            .role(MsgRole.USER)
            .textContent("北京今天天气如何？")
            .build();
    Msg response = agent.call(msg).block();
    System.out.println(response.getTextContent());
}

// 定义工具
public static class WeatherTools {
    @Tool(name = "get_weather", description = "获取指定城市的天气")
    public String getWeather(
            @ToolParam(name = "city", description = "城市名称") String city) {
        return String.format("%s：晴天，气温 25 ℃", city);
    }
}
```

---

## 9. 总结

`OpenAIChatModel` 是 AgentScope Java 中 **最通用的模型集成入口**，核心要点：

| 要点 | 说明 |
|------|------|
| **核心类** | `OpenAIChatModel` |
| **最小配置** | `apiKey` + `modelName`（OpenAI 官方）或 + `baseUrl`（兼容平台） |
| **兼容平台** | DeepSeek、Moonshot、SiliconFlow 等 |
| **生成控制** | 通过 `defaultOptions` 调节 temperature、maxTokens、frequencyPenalty 等 |

**核心价值**：一套 API、N 个平台。这种统一性极大降低了多模型切换的成本，使得开发者可以根据成本、能力、隐私需求灵活选择底层模型。

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
