在人工智能技术深度渗透企业数字化转型的当下，如何让传统 Java 开发者快速掌握大模型应用开发能力，成为企业智能化升级的关键命题。虽然当前 AI Agent 框架基本被 Python 生态垄断，但 Java 团队在落地时面临技术栈割裂、安全难保障、运维不兼容等诸多痛点。AgentScope Java 的出现，正是为 Java 开发者提供了一把打开 AI Agent 世界的钥匙。

AgentScope 是阿里巴巴通义实验室推出的一款以开发者为核心、专注于智能体开发的开源框架，其 Java 版本专为企业级场景设计，采用 ReAct（推理-行动）范式，支持高效的工具调用，并允许开发者对 Agent 执行过程进行实时介入，实现了自主性与可控性的完美平衡。

在构建企业 AI 问答系统时，如果只是把用户问题直接转发给大模型，模型虽然具备强泛化能力，但企业制度、流程、产品细节等私域知识它根本不了解，很容易给出“听起来合理但其实错误”的回答。**RAG（Retrieval-Augmented Generation，检索增强生成）** 正是为解决这个问题而生。它让 Agent 能够连接外部知识库，在回答前先从文档中检索相关信息，再基于检索结果生成答案。AgentScope Java 提供了内置的 RAG 支持，从本地简单知识库到企业级云端知识库，覆盖全场景需求：

| 类型 | 实现类 | 文档管理 | 适用场景 |
|------|--------|---------|---------|
| **本地知识库** | `SimpleKnowledge` | 代码管理（Reader） | 开发测试、数据完全自主控制 |
| **阿里云百炼** | `BailianKnowledge` | 百炼控制台 | 企业级、需重排序/查询改写/多轮对话 |
| **Dify 知识库** | `DifyKnowledge` | Dify 控制台 | 多检索模式、重排序、元数据过滤 |
| **RAGFlow** | `RAGFlowKnowledge` | RAGFlow 控制台 | 强大 OCR、知识图谱、多数据集 |

本文将带你入门 AgentScope Java，通过 SimpleKnowledge 本地知识库，一步步搭建一个知识问答助手。

## 1. SimpleKnowledge

SimpleKnowledge 是 AgentScope RAG 模块的标准实现。它充当嵌入模型（Embedding Model）与向量数据库（Vector Database）之间的编排器，将两者连接起来，提供端到端的 RAG 功能。具体来说，SimpleKnowledge 组合了以下两个核心部件：
- EmbeddingModel：负责将文本转化为向量表示，例如 DashScopeTextEmbedding、OpenAITextEmbedding。
- VDBStoreBase：向量数据库后端，负责向量的持久化存储和相似度检索，例如 InMemoryStore、QdrantStore 等

SimpleKnowledge 提供两个核心方法：
- addDocuments：将文档批量索引到向量存储中
- retrieve：根据查询文本进行语义检索，返回最相关的文档块

这种设计使得开发者无需关心底层的向量化和存储细节，只需几行代码即可完成知识库的搭建。

---

## 2. 环境准备

创建 Embedding 模型: 使用硅基流动向量化模型

### 2.1 Maven 依赖

AgentScope Java 要求 **JDK 17+**，在 `pom.xml` 中添加核心依赖：
```xml
<properties>
    <agentscope.version>1.0.12</agentscope.version>
    <openai.version>4.33.0</openai.version>
</properties>

<dependencies>
      <!-- AgentScope All-in-One 方式 -->
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

### 2.2 获取 API Key

对话模型

前往 [阿里云百炼控制台](https://bailian.console.aliyun.com/) 创建 API Key，建议通过环境变量注入：
```bash
export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

向量化模型

---

## 3. 构建本地知识库

构建一个基于 SimpleKnowledge 的知识问答助手，分三步走：
- 创建嵌入模型（EmbeddingModel）：负责将文本转化为向量
- 创建向量存储（VectorStore）：负责存储和检索向量
- 创建知识库（SimpleKnowledge）：将嵌入模型和向量存储组合在一起，然后导入文档

### 3.1 创建嵌入模型

嵌入模型负责将文本转化为向量表示。在这我们使用硅基流动提供的文本嵌入模型：
```java
// 1. 创建 Embedding 模型: 使用硅基流动向量化模型
EmbeddingModel embeddingModel = OpenAITextEmbedding.builder()
        .baseUrl("https://api.siliconflow.cn/v1")           // 硅基流动端点
        .apiKey(System.getenv("SILICON_FLOW_API_KEY"))       // API Key
        .modelName("BAAI/bge-m3")                          // 模型名称
        .build();
```

**设计意图**：将知识库与对话模型解耦。Embedding 负责"理解语义"，ChatModel 负责"组织语言"。两者可以来自不同厂商——这里用硅基流动的开源模型做向量化，用百炼的千问模型做对话。

### 3.2 创建向量存储

SimpleKnowledge 需要搭配向量存储来持久化文档向量并提供相似度检索。AgentScope 支持多种后端，对于开发测试，推荐使用 InMemoryStore（内存模式），不需要额外部署外部服务。

#### 3.2.1 InMemoryStore（内存存储）

适合开发和测试，数据不持久化：
```java
InMemoryStore.builder()
        .dimensions(1024)  // 向量维度，需与 Embedding 模型一致
        .build();
```
> `InMemoryStore` 是开发调试阶段的最佳选择：**零配置、零外部依赖、启动即可用**。但它的数据随进程结束而消失，不适合生产环境。

#### 3.2.2 QdrantStore（生产级）

QdrantStore 适合生产环境，支持持久化和高性能检索：
```java
QdrantStore.builder()
        .location("localhost:6334")     // Qdrant 服务地址
        .collectionName("my_docs")      // 集合名称
        .dimensions(1024)               // 向量维度
        .build();
```
生产环境你还可以使用：
- `PgVectorStore` → PostgreSQL 扩展，事务友好
- `MilvusStore` → 分布式大规模向量检索

> 替换时只需改这一行，`Knowledge` 和 `Agent` 的代码完全不需要动。

### 3.3 创建本地知识库

有了嵌入模型和向量存储，就可以创建 SimpleKnowledge 本地知识库：
```java
Knowledge knowledge = SimpleKnowledge.builder()
        .embeddingModel(embeddingModel)
        .embeddingStore(vectorStore)
        .build();
```
`SimpleKnowledge` 是 AgentScope 提供的"一站式"本地知识库实现，内部封装了：
- 调用 `EmbeddingModel` 将文档转为向量
- 将向量写入 `EmbeddingStore`
- 根据查询向量执行相似度检索

### 3.4 文档读取与切分

使用 Reader 读取本地文档并切分为适合向量化的片段（Chunk）：
```java
// 读取并切分文档
TextReader reader = new TextReader(512, SplitStrategy.PARAGRAPH, 50);
List<Document> docs = reader.read(
                ReaderInput.fromString("""
                AgentScope Java 是一个面向智能体的编程框架，用于构建 LLM 驱动的应用程序。
                它提供了创建智能体所需的一切：ReAct 推理、工具调用、内存管理、多智能体协作等。
                AgentScope 采用 ReAct（推理-行动）范式，使智能体能够自主规划和执行复杂任务。
                """))
        .block();
```

**`TextReader` 三个参数的含义**：

| 参数 | 值 | 含义 |
|-----|---|------|
| `chunkSize` | 512 | 每个文档块的最大字符/ token 数 |
| `splitStrategy` | `PARAGRAPH` | 切分策略：按段落切分，尽量保持语义完整 |
| `chunkOverlap` | 50 | 相邻 chunk 的重叠字符数，防止断句丢失上下文 |

> **为什么需要重叠？** 假设原文是："AgentScope 采用 ReAct 范式使智能体能够自主规划。"如果在"范式"处切断，下一个块从"使智能体"开始，两个块各自都失去了完整语义。50 个 token 的重叠确保关键信息在相邻块中重复出现，提高检索召回率。

#### 3.4.1 切分策略 SplitStrategy

Reader 支持如下四种分割策略：

| 策略 | 说明 | 适用场景 |
|------|------|---------|
| `CHARACTER` | 按字符数切分 | 简单文本，无结构要求 |
| `PARAGRAPH` | 按段落切分 | 文章、报告，保留段落完整性 |
| `SENTENCE` | 按句子切分 | 精确控制粒度 |
| `TOKEN` | 按 token 数切分 | 需要精确控制向量长度 |

#### 3.4.2 多种文档 Reader

AgentScope 为 SimpleKnowledge 提供了多种内置 Reader：
```java
// 文本
// 参数：chunkSize=512, splitStrategy=PARAGRAPH, overlap=50
new TextReader(512, SplitStrategy.PARAGRAPH, 50);

// PDF
new PDFReader(512, SplitStrategy.PARAGRAPH, 50);

// Word（支持图片和表格）
// 参数：chunkSize, splitStrategy, overlap, extractImages, extractTables, tableFormat
WordReader wordReader = new WordReader(
        512,
        SplitStrategy.PARAGRAPH,
        50,
        true,                           // 提取图片
        true,                           // 提取表格
        TableFormat.MARKDOWN            // 表格转为 Markdown 格式
);

// 图像（需配合多模态嵌入模型）
new ImageReader(false);
```

#### 3.4.3 从多种来源读取

```java
// 从字符串读取
List<Document> docs1 = reader.read(ReaderInput.fromString("文本内容...")).block();

// 从文件读取
List<Document> docs2 = reader.read(ReaderInput.fromPath(Path.of("/path/to/file.txt"))).block();
```

### 3.5 添加文档到知识库

```java
// 添加文档到知识库
knowledge.addDocuments(docs).block();
```
这一步是 **耗时操作** 的本质所在：每个 `Document` 都要调用一次 Embedding API（或批量调用）。对于 1000 篇文档，就是 1000 次向量计算。AgentScope 内部会自动做批量聚合，但首次构建知识库时仍建议耐心等待。

## 4. 集成到 ReActAgent：构建知识问答助手

ReActAgent 是 AgentScope Java 的核心入口，它实现了“推理-行动”循环：Agent 先分析当前状况决定下一步做什么（推理），然后执行相应的工具调用或检索操作（行动），通过不断迭代来完成任务。采用建造者模式，配置非常直观。

### 4.1 创建对话模型

对话模型负责"最后一公里"——把检索到的知识片段组织成通顺的人类语言。选择 `qwen3-max` 或 `qwen3.5` 系列可以获得更好的中文理解和生成能力：
```java
DashScopeChatModel chatModel = DashScopeChatModel.builder()
    .apiKey(System.getenv("DASHSCOPE_API_KEY")) // API 密钥
    .modelName(MODEL_NAME) // 模型名称
    .build();
```

### 4.2 创建 RAG 智能体

```java
ReActAgent agent = ReActAgent.builder()
                .name("RAGAssistant")
                .sysPrompt(
                        "You are a helpful assistant with access to a knowledge retrieval"
                                + " tool. When you need information from the knowledge base,"
                                + " use the retrieve_knowledge tool. Always explain what you're"
                                + " doing.")
                .model(chatModel)
                .memory(new InMemoryMemory())
                .toolkit(new Toolkit())
                .knowledge(knowledge) // 本地知识库
                .ragMode(RAGMode.AGENTIC)
                .retrieveConfig(
                        RetrieveConfig.builder()
                                .limit(3)
                                .scoreThreshold(0.3)
                                .build()
                        )
                .build();
```

通过 `.knowledge(knowledge)` 将本地知识库绑定到 Agent。这是 Agent 能够"查资料"的根本。

**最关键的配置**。`RAGMode` 有两种模式：

| 模式 | 机制 | 优点 | 缺点 |
|------|------|------|------|
| **Generic 模式** | 每次推理前自动检索并注入知识 | 简单，对任何 LLM 都有效 | 即使不需要也会检索，浪费 token |
| **Agentic 模式** | Agent 自主决定何时调用检索工具 | 灵活，按需检索，更省 token | 需要模型具备较强的推理能力 |

`Agentic` 模式的优势在于 **智能性**：如果用户问"你好"，Agent 不会无脑检索知识库；如果问"AgentScope 的核心范式是什么"，Agent 会主动调用 `retrieve_knowledge`。在这使用 Agentic 模式。

配置检索行为：
```java
RetrieveConfig.builder()
        .limit(3)           // 最多返回 3 个相关片段
        .scoreThreshold(0.3) // 相似度低于 0.3 的片段会被过滤
        .build()
```

**调参建议**：
- **`limit`**：取决于文档密度和 LLM 的上下文窗口。3~5 个片段通常足够，太多会挤占对话上下文。
- **`scoreThreshold`**：
  - 设得太高（如 0.8）→ 可能漏掉相关内容，Agent 得不到足够信息
  - 设得太低（如 0.1）→ 噪声过多，Agent 被无关信息干扰
  - **0.3~0.5 是大多数场景的甜点区**

### 4.3 交互调用

Agent 构建完成后，就可以发送问题进行测试了：
```java
Msg response = agent.call(
        Msg.builder()
                .role(MsgRole.USER)
                .textContent("AgentScope Java 的核心范式是什么")
                .build()
).block();

System.out.println(response.getTextContent());
```
`agent.call()` 返回一个 `Mono<Msg>`，`.block()` 阻塞等待结果。在 Web 应用中，你应该返回 `Mono<Msg>` 给 WebFlux，让框架处理异步。

---

## 5. 完整的入门示例

```java
// 1. 创建 Embedding 模型: 使用硅基流动向量化模型
EmbeddingModel embeddingModel = OpenAITextEmbedding.builder()
        .baseUrl("https://api.siliconflow.cn/v1")           // 硅基流动端点
        .apiKey(System.getenv("SILICON_FlOW_API_KEY"))       // API Key
        .modelName("BAAI/bge-m3")                           // 模型名称
        .dimensions(1024)
        .build();

// 2. 向量化存储
InMemoryStore vectorStore = InMemoryStore.builder()
        .dimensions(1024)
        .build();

// 3. 创建本地知识库
// 3.1 创建知识库
Knowledge knowledge = SimpleKnowledge.builder()
        .embeddingModel(embeddingModel)
        .embeddingStore(vectorStore)
        .build();

// 3.2 读取并切分文档
TextReader reader = new TextReader(512, SplitStrategy.PARAGRAPH, 50);
List<Document> docs = reader.read(
                ReaderInput.fromString("""
                AgentScope Java 是一个面向智能体的编程框架，用于构建 LLM 驱动的应用程序。
                它提供了创建智能体所需的一切：ReAct 推理、工具调用、内存管理、多智能体协作等。
                AgentScope 采用 ReAct（推理-行动）范式，使智能体能够自主规划和执行复杂任务。
                """))
        .block();

// 3.3 添加文档到知识库
knowledge.addDocuments(docs).block();

// 4. 创建对话模型: 使用百练对话模型
DashScopeChatModel chatModel = DashScopeChatModel.builder()
        .apiKey(System.getenv("DASHSCOPE_API_KEY")) // API 密钥
        .modelName(MODEL_NAME) // 模型名称
        .build();

// 5. 创建智能体
ReActAgent agent = ReActAgent.builder()
                .name("RAGAssistant")
                .sysPrompt(
                        "You are a helpful assistant with access to a knowledge retrieval"
                                + " tool. When you need information from the knowledge base,"
                                + " use the retrieve_knowledge tool. Always explain what you're"
                                + " doing.")
                .model(chatModel)
                .memory(new InMemoryMemory())
                .toolkit(new Toolkit())
                .knowledge(knowledge) // 本地知识库
                .ragMode(RAGMode.AGENTIC)
                .retrieveConfig(
                        RetrieveConfig.builder()
                                .limit(3)
                                .scoreThreshold(0.3)
                                .build()
                        )
                .build();

// 6. 交互
Msg response = agent.call(
        Msg.builder()
                .role(MsgRole.USER)
                .textContent("AgentScope Java 的核心范式是什么")
                .build()
).block();

System.out.println(response.getTextContent());
```
当你运行这段代码时，Agent 内部会发生以下 ReAct 循环：

### Round 1：思考

```
[Agent] 用户问"AgentScope Java 的核心范式是什么"，
        这是一个关于 AgentScope 框架的具体问题，
        我应该使用 retrieve_knowledge 工具查询知识库。
```

### Round 2：行动（工具调用）

```json
{
  "tool_use": {
    "name": "retrieve_knowledge",
    "input": {
      "query": "AgentScope Java 的核心范式"
    }
  }
}
```

### Round 3：观察（检索结果）

AgentScope 内部执行向量检索，返回：
```
[Document 1] score=0.87: AgentScope 采用 ReAct（推理-行动）范式...
[Document 2] score=0.65: 它提供了创建智能体所需的一切：ReAct 推理...
[Document 3] score=0.42: AgentScope Java 是一个面向智能体的编程框架...
```

### Round 4：最终回答

```
AgentScope Java 的核心范式是 **ReAct（推理-行动，Reasoning + Acting）范式**。

基于这一范式：
1. **自主规划**：智能体能够根据当前状态进行推理，决定下一步的行动。
2. **循环执行**：智能体会反复进行“思考 -> 行动 -> 观察 -> 再思考”的闭环过程，从而处理复杂的任务。
3. **灵活协作**：该范式支持多智能体之间的协作、工具调用以及内存管理，使 AgentScope 能够构建出能够自主交互和执行任务的复杂应用。

简而言之，AgentScope Java 通过 ReAct 范式赋予智能体自主规划和执行决策的能力，使其成为构建 LLM（大语言模型）驱动应用的强大框架。
```

如果你配置了 Hook，可以完整观察到 `PreCallEvent → PreActingEvent → PostActingEvent → PostCallEvent` 的全链路事件。

---

## 6. 总结

本文基于 `SimpleKnowledgeAgentExample` 完整拆解了 AgentScope 知识问答助手的搭建流程：

1. **Embedding 层**：硅基流动的 `BAAI/bge-m3` 负责语义向量化
2. **存储层**：`InMemoryStore` 提供零配置的向量存储
3. **知识层**：`SimpleKnowledge` 封装了文档切分、向量化和检索
4. **Agent 层**：`ReActAgent` 通过 `AGENTIC` 模式自主决策何时检索、如何回答
5. **配置层**：`sysPrompt`、`retrieveConfig` 和 `ragMode` 共同决定了 Agent 的行为边界

从"能检索"到"会问答"，核心在于 **让 Agent 拥有调用知识库的意识和能力**。AgentScope 的 `knowledge + ragMode` 设计将这一复杂度封装在框架内部，开发者只需几行配置，就能让智能体真正"读得懂资料、回答得了问题"。
