在上一篇[文章](https://smartsi.blog.csdn.net/article/details/161324334)中，我们介绍了如何使用 `OpenAIChatModel` 接入 OpenAI 及其兼容平台。本篇将聚焦 **本地自托管** 场景——通过 `OllamaChatModel` 集成 Ollama，让你在 **完全离线、零成本** 的环境下运行 AI 智能体。

Ollama 是当前最流行的本地 LLM 运行工具，它将模型权重、配置和依赖打包为一个统一包，通过简单的命令行即可拉取和运行模型。更重要的是，Ollama 内置了兼容 OpenAI 的 API 服务——这也是 AgentScope 能够无缝集成它的基础。

这是 AgentScope Java 支持接入多种主流大语言模型系列介绍的第三篇：

| 文章 | 模型平台 | 核心类 | 特点 |
|------|---------|--------|------|
| 模型集成系列第 1 篇 | 阿里云百炼（DashScope） | `DashScopeChatModel` | 云端、中文生态强 |
| 模型集成系列第 2 篇 | OpenAI / DeepSeek / vLLM | `OpenAIChatModel` | 通用协议、多平台 |
| **模型集成系列第 3 篇** | **Ollama 本地部署** | **`OllamaChatModel`** | **离线、零成本、隐私安全** |

---

## 1. 为什么选择 Ollama？

| 优势 | 说明 |
|------|------|
| **数据隐私** | 所有推理在本地完成，数据不出机器，满足敏感数据合规要求 |
| **零成本** | 无 API 调用费用，仅需硬件支持 |
| **离线可用** | 模型下载后可完全断网运行 |
| **灵活切换** | 一条命令切换模型（Qwen、Llama、DeepSeek、Gemma、Mistral 等） |
| **开发友好** | 内置 OpenAI 兼容 API，无缝对接各类框架 |

**适用场景**：
- 企业内网 / 无外网环境
- 隐私敏感数据处理（医疗、金融、法律）
- 本地开发调试（免费无限调用）
- 边缘设备部署

---

## 2. 环境准备

### 2.1 安装 Ollama

> 详细安装流程请参阅：[Ollama 实战：从零开始本地运行大语言开源模型](https://smartsi.blog.csdn.net/article/details/158265330)

**macOS（推荐 Homebrew）：**
```bash
brew install ollama
```

**Linux：**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows：**
从 [Ollama 官网](https://ollama.com/download/windows) 下载安装包。

**验证安装：**
```bash
ollama --version
# ollama version is 0.16.2
```

### 2.2 下载模型

```bash
# 推荐：通义千问 Qwen3 8B（中文优秀，支持工具调用和思考模式）
ollama pull qwen3:8b

# 其他热门模型
ollama pull llama3.2:3b        # Meta Llama 3.2（轻量）
ollama pull deepseek-r1:8b     # DeepSeek R1（推理增强）
ollama pull gemma3:4b           # Google Gemma 3（轻量）
ollama pull mistral:7b          # Mistral 7B（欧洲开源）
```

**查看已下载模型：**
```bash
ollama list
```

> 模型大小参考：7B 参数模型约 4-5 GB，建议至少 8GB 内存（16GB+ 更流畅）。

### 2.3 启动 Ollama 服务

Ollama 安装后通常自动运行。如需手动启动：
```bash
ollama serve
```

默认监听 `http://localhost:11434`。验证服务是否正常：
```bash
curl http://localhost:11434/v1/models
```

### 2.4 Maven 依赖

> AgentScope Java 要求 **JDK 17+**

```xml
<dependency>
    <groupId>io.agentscope</groupId>
    <artifactId>agentscope</artifactId>
    <version>1.0.12</version>
</dependency>
```

> All-in-one 包默认包含 Ollama 集成，无需额外依赖。详见 [AgentScope Java 入门 3：如何安装 AgentScope](https://smartsi.blog.csdn.net/article/details/160694030)。

---

## 3. 快速开始：本地调用模型

通过 `OllamaChatModel` 集成本地模型，最小配置只需 `modelName`：
```java
// 1. 创建模型
OllamaChatModel model = OllamaChatModel.builder()
        .modelName("qwen2.5:7b")
        .baseUrl("http://localhost:11434")  // 默认值，可省略
        .build();

// 2. 创建 Agent
ReActAgent agent = ReActAgent.builder()
        .name("LocalAssistant")
        .model(model)
        .build();

// 3. 调用
Msg msg = Msg.builder()
        .role(MsgRole.USER)
        .textContent("你好，请用三句话介绍一下 AgentScope Java")
        .build();
Msg response = agent.call(msg).block();
System.out.println(response.getTextContent());
```

> **注意**：与 `DashScopeChatModel` 和 `OpenAIChatModel` 不同，`OllamaChatModel` **无需 API Key**——这是本地部署最大的便利。

---

## 4. OllamaChatModel 核心配置

```java
import io.agentscope.core.model.OllamaChatModel;
import io.agentscope.core.model.OllamaOptions;

OllamaChatModel model = OllamaChatModel.builder()
        .modelName("qwen2.5:7b")                           // 模型名称（必填）
        .baseUrl("http://localhost:11434")               // Ollama 服务地址（默认值）
        .defaultOptions(OllamaOptions.builder()
                .temperature(0.7)
                .numCtx(4096)
                .build())
        .build();
```

| 配置项 | 是否必填 | 说明 |
|--------|----------|------|
| `modelName` | 必填 | 模型名称，如 qwen2.5:7b |
| `baseUrl` | 可选 | Ollama 服务端点，默认 `http://localhost:11434`。远程部署时需修改 |
| `defaultOptions` | 可选 | 默认生成选项，类型为 `OllamaOptions` |
| `formatter` | 可选 | 消息格式化器（默认 `OllamaChatFormatter`） |
| `httpTransport` | 可选 | HTTP 传输配置（超时、代理等） |

---

## 5. OllamaOptions 高级配置

`OllamaChatModel` 拥有独有的 `OllamaOptions` 配置体系，支持超过 40 个精细调优参数。

### 5.1 基础生成参数

```java
OllamaOptions options = OllamaOptions.builder()
        .temperature(0.7)       // 生成随机性 (0.0-2.0)
        .topK(40)               // Top-K 采样
        .topP(0.9)              // 核采样
        .minP(0.05)             // 最小概率阈值
        .numCtx(4096)           // 上下文窗口大小
        .repeatPenalty(1.1)     // 重复惩罚
        .frequencyPenalty(0.5)  // 频率惩罚
        .presencePenalty(0.5)   // 存在惩罚
        .seed(42)              // 随机种子
        .build();

OllamaChatModel model = OllamaChatModel.builder()
        .modelName("qwen2.5:7b")
        .defaultOptions(options)
        .build();
```

| 参数 | 说明 | 建议 |
|------|------|------|
| `temperature` | 控制随机性 | 0.0-2.0 |
| `topK` | 限制候选 token 数量 | 默认：40 |
| `topP` | 核采样阈值 | 0.0-1.0，默认：0.9|
| `minP` | 最小概率阈值 | 默认：0.0 |
| `numCtx` | 上下文窗口大小 | 默认 2048 |
| `repeatPenalty` | 重复惩罚 | 默认：1.1 |
| `presencePenalty` | 基于 token 存在性的惩罚 |  |
| `frequencyPenalty` | 基于 token 频率的惩罚 |  |
| `numPredict` | 生成的最大 token 数 | -1 表示无限 |
| `seed` | 可重现结果的随机种子 | |
| `stop` | 立即停止生成的字符串 |  |

### 5.2 模型加载参数（GPU/内存调优）

```java
OllamaOptions options = OllamaOptions.builder()
        .numBatch(512)          // 批处理大小
        .numGPU(-1)             // GPU 层数：-1 表示全部卸载到 GPU
        .numThread(8)           // CPU 线程数
        .lowVRAM(false)         // 低显存模式
        .useMMap(true)          // 内存映射加载
        .useMLock(false)        // 锁定内存防交换
        .f16KV(true)            // 16 位 KV 缓存（省显存）
        .build();
```

| 参数 | 说明 | 建议 |
|------|------|------|
| `numBatch` | 提示处理的批处理大小 | 默认：512 |
| `numGPU` | 卸载到 GPU 的层数 | `-1` 全部 GPU、`0` 纯 CPU |
| `numThread` | CPU 线程数 | 设为物理核心数，不要超过 |
| `lowVRAM` | 为有限 GPU 内存启用低显存模式 | 显存不足 8GB 时开启 |
| `useMMap` | 使用内存映射加载模型 | 推荐 `true`，加速模型加载 |
| `useMLock` | 锁定模型在内存中以防止交换 | |
| `f16KV` | 16 位 KV 缓存 | 推荐开启，节省约 50% 显存 |

### 5.3 采样策略参数

```java
OllamaOptions options = OllamaOptions.builder()
        .mirostat(2)            // Mirostat v2 采样
        .mirostatTau(5.0)      // Mirostat 目标熵
        .mirostatEta(0.1)      // Mirostat 学习率
        .tfsZ(1.0)              // 尾部自由采样
        .build();
```

| 参数 | 说明 | 建议 |
|------|------|------|
| `mirostat` | Mirostat 采样 | 0 表示禁用，1 表示Mirostat v1，2 表示Mirostat v2 |
| `mirostatTau` | Mirostat 目标熵 | 默认：5.0 |
| `mirostatEta` | Mirostat 学习率 | 默认：0.1 |
| `tfsZ` | 尾部自由采样 | 默认：1.0 禁用 |
| `typicalP` | 典型概率采样 | 默认：1.0 |

### 5.4 通过 GenerateOptions 统一配置

如果你希望代码在不同模型间通用，可以使用 `GenerateOptions` + `OllamaOptions.fromGenerateOptions()` 转换：
```java
GenerateOptions options = GenerateOptions.builder()
        .temperature(0.7)           // 映射到 Ollama 的 temperature
        .topP(0.9)                  // 映射到 Ollama 的 top_p
        .topK(40)                   // 映射到 Ollama 的 top_k
        .maxTokens(2000)            // 映射到 Ollama 的 num_predict
        .seed(42L)                  // 映射到 Ollama 的 seed
        .frequencyPenalty(0.5)      // 映射到 Ollama 的 frequency_penalty
        .presencePenalty(0.5)       // 映射到 Ollama 的 presence_penalty
        .additionalBodyParam(OllamaOptions.ParamKey.NUM_CTX.getKey(), 4096)      // 上下文窗口大小
        .additionalBodyParam(OllamaOptions.ParamKey.NUM_GPU.getKey(), -1)        // 将所有层卸载到 GPU
        .additionalBodyParam(OllamaOptions.ParamKey.REPEAT_PENALTY.getKey(), 1.1) // 重复惩罚
        .additionalBodyParam(OllamaOptions.ParamKey.MAIN_GPU.getKey(), 0)        // 主 GPU 索引
        .additionalBodyParam(OllamaOptions.ParamKey.LOW_VRAM.getKey(), false)    // 低显存模式
        .additionalBodyParam(OllamaOptions.ParamKey.F16_KV.getKey(), true)       // 16位 KV 缓存
        .additionalBodyParam(OllamaOptions.ParamKey.NUM_THREAD.getKey(), 8)      // CPU 线程数
        .build();

OllamaChatModel model = OllamaChatModel.builder()
        .modelName("qwen2.5:7b")
        .baseUrl("http://localhost:11434")
        .defaultOptions(OllamaOptions.fromGenerateOptions(options))  // 内部转换为 OllamaOptions
        .build();
```

> **映射关系说明**：`GenerateOptions` 的标准字段会自动映射到 Ollama 对应参数；Ollama 独有参数（如 `numCtx`、`numGPU`）通过 `additionalBodyParam` 传递。

---

## 6. 思考模式

Ollama 上运行支持思考模式的模型（如 `qwen3:8b`、`deepseek-r1:8b`）时，可通过 `ThinkOption` 启用：

```java
import io.agentscope.core.model.OllamaChatModel;
import io.agentscope.core.model.OllamaOptions;
import io.agentscope.core.model.OllamaOptions.ThinkOption;

OllamaChatModel model = OllamaChatModel.builder()
        .modelName("qwen3:8b")
        .baseUrl("http://localhost:11434")
        .defaultOptions(OllamaOptions.builder()
                .thinkOption(ThinkOption.ThinkBoolean.ENABLED)
                .temperature(0.8)
                .numCtx(8192)       // 思考模式消耗更多上下文，建议增大
                .build())
        .build();
```

| ThinkOption | 说明 |
|-------------|------|
| `ThinkOption.ThinkBoolean.ENABLED` | 开启思考模式 |
| `ThinkOption.ThinkBoolean.DISABLED` | 关闭思考模式（默认） |

> **前提**：模型本身必须支持思考模式。

---

## 7. 实战：本地天气助手

整合工具、思考模式、超时配置的完整本地 Agent 示例：
```java
public class OllamaModelExample {
    public static void main(String[] args) {
        // 1. 模型参数
        OllamaOptions options = OllamaOptions.builder()
                .numCtx(4096)           // 上下文窗口大小
                .temperature(0.7)       // 生成随机性
                .topK(40)               // Top-K 采样
                .topP(0.9)              // 核采样
                .repeatPenalty(1.1)     // 重复惩罚
                .build();

        // 2. Ollama 千问模型
        OllamaChatModel model = OllamaChatModel.builder()
                .modelName("qwen3:8b")
                .baseUrl("http://localhost:11434")  // 默认值
                .defaultOptions(options)
                .build();

        // 3. 注册工具
        Toolkit toolkit = new Toolkit();
        toolkit.registerTool(new WeatherTools());

        // 4. 创建 ReActAgent
        ReActAgent agent = ReActAgent.builder()
                .name("Assistant")
                .sysPrompt("你是一个本地运行的天气助手，可以查询城市天气。请用中文回答。")
                .model(model)
                .toolkit(toolkit) // 绑定工具
                .maxIters(10)
                .modelExecutionConfig(ExecutionConfig.builder()
                        .timeout(Duration.ofMinutes(5))    // 本地推理较慢，超时设长
                        .maxAttempts(2)
                        .initialBackoff(Duration.ofSeconds(2))
                        .maxBackoff(Duration.ofSeconds(10))
                        .backoffMultiplier(2.0)
                        .build())
                .build();

        // 5. 调用智能体
        Msg msg = Msg.builder()
                .role(MsgRole.USER)
                .textContent("北京今天天气怎么样？适合跑步吗？")
                .build();

        Msg response = agent.call(msg).block();
        System.out.println(response.getTextContent());
    }

    // 定义工具
    public static class WeatherTools {
        @Tool(name = "get_weather", description = "获取指定城市的天气信息")
        public String getWeather(
                @ToolParam(name = "city", description = "城市名称") String city) {
            return String.format("%s：多云，气温 22 ℃，湿度 65%%", city);
        }
    }
}
```

---

## 8. 总结

`OllamaChatModel` 是 AgentScope Java 中 **本地化部署的最佳选择**：

| 要点 | 说明 |
|------|------|
| **核心类** | `OllamaChatModel` |
| **最小配置** | `modelName`（甚至 `baseUrl` 都可省略） |
| **无需 API Key** | 本地服务，零成本无限调用 |
| **专属调优** | 40+ 参数精细控制 GPU/内存/采样策略 |
| **思考模式** | `ThinkOption.ThinkBoolean.ENABLED` |

**核心价值**：数据不出机器、推理零成本、完全可控。对于隐私敏感场景和本地开发调试，`OllamaChatModel` + Ollama 是最理想的组合。

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
