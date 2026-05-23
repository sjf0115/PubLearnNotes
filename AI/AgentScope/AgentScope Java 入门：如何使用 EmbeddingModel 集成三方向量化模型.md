在上一篇 RAG 文章中，我们使用 `DashScopeTextEmbedding` 将文本转换为向量并构建本地知识库。这引出了一个问题：**AgentScope 的 Embedding 体系是如何设计的？除了百炼，能否接入其他平台的向量模型？**。答案是肯定的。AgentScope 的 `EmbeddingModel` 是一个 **可插拔接口**，只要平台提供 OpenAI 兼容的 Embedding API，就可以无缝接入。本文将以 **硅基流动（SiliconFlow）** 为例，展示如何脱离单一厂商，灵活选择高性价比的向量模型。

---

## 1. EmbeddingModel 核心接口解析

`EmbeddingModel` 是 AgentScope RAG 体系的"发动机"，负责将人类可读的文本转换为机器可计算的向量：
```java
public interface EmbeddingModel {
    /**
     * 将一批文本转换为向量
     * @param texts 待向量化的文本列表
     * @return 每个文本对应的 Embedding 向量列表
     */
    Mono<List<Embedding>> embed(List<String> texts);
    String getModelName();
    int getDimensions();
}
```

### 1.1 为什么需要批量接口？

在实际场景中，RAG 的 `TextReader` 会将一篇文档切分成数十个 `Document` 片段。如果每个片段都发起一次 HTTP 请求，网络开销会非常大。因此 `embed(List<String>)` 的 **批量设计** 允许底层实现一次性发送多个文本，显著提升吞吐。

### 1.2 返回 `Mono<List<Embedding>>` 的意义

AgentScope 全程基于 **Project Reactor** 构建，`Mono` 表示"异步的单个结果"。这意味着：
- 向量计算可能在远程服务器上耗时数百毫秒，`Mono` 保证不会阻塞调用线程
- 可以通过 `.block()` 在同步场景中使用，也可以通过 `.flatMap()` 接入响应式链
- 配合 `Retry` 和 `Timeout` 操作符，可以轻松实现重试和熔断

### 1.3 与 ChatModel 的本质区别

| 维度 | ChatModel | EmbeddingModel |
|-----|-----------|----------------|
| **输入** | 对话消息（messages） | 纯文本列表 |
| **输出** | 生成的文本/结构化数据 | 浮点数向量 |
| **用途** | 推理、对话、决策 | 语义检索、相似度计算 |
| **计算特征** | 自回归生成，逐 token 输出 | 前向传播一次，输出固定维度 |
| **成本** | 按输入+输出 token 计费 | 按输入 token 计费，通常更便宜 |

在 RAG 链路中，两者是 **上下游关系**：
```
Document → TextReader → EmbeddingModel → Vector Store
                                           ↑
Query ─────→ EmbeddingModel ───────────────┘
                                           ↓
                                    Retrieve Top-K
                                           ↓
Context + Query ─────→ ChatModel ───→ Answer
```

---

## 2. AgentScope 内置 Embedding

AgentScope 当前提供了三类 `EmbeddingModel` 实现。

### 2.1 DashScopeTextEmbedding

阿里云百炼的文本向量实现：
```java
EmbeddingModel embeddingModel = DashScopeTextEmbedding.builder()
        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
        .modelName("text-embedding-v3")
        .dimensions(1024)
        .build();
```

**特点**：国内访问速度快，支持自定义维度（`text-embedding-v3`），但 **必须额外引入** `dashscope-sdk-java`。

### 2.2 OpenAITextEmbedding

OpenAI 兼容格式的通用实现，这是我们本文的主角。它不仅仅能调用 OpenAI 官方，还能接入所有 **OpenAI API 兼容** 的平台——包括硅基流动、Azure OpenAI、本地 vLLM、Xinference 等。
```java
EmbeddingModel embeddingModel = OpenAITextEmbedding.builder()
        .baseUrl("https://api.openai.com/v1")   // 可替换为任意兼容端点
        .apiKey(System.getenv("OPENAI_API_KEY"))
        .modelName("text-embedding-3-small")
        .dimensions(1536)
        .build();
```
**特点**：通用性强，一处配置，多端复用。

### 2.3 OllamaEmbeddingModel

面向本地私有化部署，适合数据敏感场景：
```java
EmbeddingModel embeddingModel = OllamaEmbeddingModel.builder()
        .baseUrl("http://localhost:11434")
        .modelName("nomic-embed-text")
        .dimensions(768)
        .build();
```

**特点**：完全离线，零 API 费用，但需要本地 GPU 资源。

---

## 3. 实战：硅基流动 × AgentScope 构建本地知识库

本节将完整演示：使用 `OpenAITextEmbedding` 接入硅基流动的 `BAAI/bge-m3` 模型，构建一个基于 `SimpleKnowledge` 的本地知识库。

### 3.1 硅基流动（SiliconFlow）介绍

**硅基流动（SiliconFlow）** 是一家专注于开源大模型推理加速的云服务平台，其最大特点是 **完全兼容 OpenAI API 格式**，并且提供了一系列高性价比的开源 Embedding 模型。硅基流动支持如下 Embedding 模型：

![]()

### 3.2 API 端点与认证

- **Base URL**：`https://api.siliconflow.cn/v1`
- **认证方式**：`Authorization: Bearer <SILICONFLOW_API_KEY>`
- **Embedding 端点**：`POST /v1/embeddings`

请求示例：

```bash
curl -X POST https://api.siliconflow.cn/v1/embeddings \
  -H "Authorization: Bearer $SILICONFLOW_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello, world!",
    "model": "Qwen/Qwen3-Embedding-8B",
    "dimensions": 1024
  }'
```

### 3.3 依赖配置

`OpenAITextEmbedding` 依赖 OpenAI 的 Java SDK，需要显式引入：
```xml
<properties>
    <agentscope.version>1.0.12</agentscope.version>
    <openai.version>0.31.0</openai.version>
</properties>

<dependencies>
    <!-- AgentScope All-in-One -->
    <dependency>
        <groupId>io.agentscope</groupId>
        <artifactId>agentscope</artifactId>
        <version>${agentscope.version}</version>
    </dependency>

    <!-- OpenAI SDK（OpenAITextEmbedding 所需） -->
    <dependency>
        <groupId>com.openai</groupId>
        <artifactId>openai-java</artifactId>
        <version>${openai.version}</version>
    </dependency>
</dependencies>
```

### 3.4 环境准备

注册硅基流动账号，获取 API Key，并配置环境变量：
```bash
export SILICONFLOW_API_KEY="sk-your-siliconflow-api-key"
```

### 3.5 完整代码

```java
// 1. 创建硅基流动 Embedding 模型
// 使用 BAAI/bge-m3：支持 8192 tokens，多语言效果优秀
EmbeddingModel embeddingModel = OpenAITextEmbedding.builder()
        .baseUrl("https://api.siliconflow.cn/v1")           // 硅基流动端点
        .apiKey(System.getenv("SILICONFLOW_API_KEY"))       // API Key
        .modelName("BAAI/bge-m3")                           // 模型名称
        .build();

// 2. 创建本地知识库
// bge-m3 输出维度为 1024，InMemoryStore 需要匹配
Knowledge knowledge = SimpleKnowledge.builder()
        .embeddingModel(embeddingModel)
        .embeddingStore(InMemoryStore.builder().dimensions(1024).build())
        .build();

// 3. 读取文档并添加到知识库
TextReader reader = new TextReader(512, SplitStrategy.PARAGRAPH, 50);
List<Document> docs = reader.read(
        ReaderInput.fromString("""
        硅基流动（SiliconFlow）是一家专注于开源大模型推理加速的云服务平台。
        平台提供百余种开源模型的 API 服务，覆盖文本、图像、语音、视频等多种模态。
        硅基流动的核心优势在于高性能推理引擎，能够将开源模型的推理速度提升数倍。
        同时，平台完全兼容 OpenAI API 格式，开发者可以零成本迁移现有应用。
        """))
        .block();
knowledge.addDocuments(docs).block();

// 4. 检索测试
List<Document> results = knowledge.retrieve(
        "SiliconFlow 支持哪些模态？",
        RetrieveConfig.builder()
                .limit(3)
                .scoreThreshold(0.5)
                .build()
).block();

// 5. 输出结果
System.out.println("===== 检索结果 =====");
for (Document doc : results) {
    System.out.println("相似度: " + doc.getScore());
    System.out.println("内容: " + doc.getMetadata().getContent());
    System.out.println("---");
}
```

### 3.6 代码解析

**关键配置点**：

| 参数 | 值 | 说明 |
|-----|---|------|
| `baseUrl` | `https://api.siliconflow.cn/v1` | 硅基流动 OpenAI 兼容端点，**注意末尾不要加 `/embeddings`**，`OpenAITextEmbedding` 会自动拼接 |
| `apiKey` | 环境变量读取 | 建议不要硬编码，使用环境变量或配置中心 |
| `modelName` | `BAAI/bge-m3` | 硅基流动平台上的模型 ID，必须完全匹配 |
| `dimensions` | 未设置 | `bge-m3` 不支持自定义维度，固定输出 1024 维 |

### 3.7 运行验证

```bash
mvn clean compile exec:java \
    -Dexec.mainClass="com.example.rag.SiliconFlowEmbeddingQuickStart"
```

预期输出：

```
===== 检索结果 =====
相似度: 0.8234
内容: 平台提供百余种开源模型的 API 服务，覆盖文本、图像、语音、视频等多种模态。
---
相似度: 0.7812
内容: 硅基流动（SiliconFlow）是一家专注于开源大模型推理加速的云服务平台。
---
```

---

## 八、总结

本文深入解析了 AgentScope 的 `EmbeddingModel` 接口设计，并以**硅基流动**为例，展示了如何通过 `OpenAITextEmbedding` 接入第三方向量模型。
