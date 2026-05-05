在前之前的文章中，我们的 Agent 已经具备了模型推理、Hook 监控、本地工具、MCP 远程工具和模块化 Skill 等能力。但这些都解决的是"怎么做"的问题——当用户问"我们公司去年的营收增长率是多少"时，Agent 依然无能为力，因为这类信息存在于企业的私有文档中，而非模型的训练数据里。

**RAG（Retrieval-Augmented Generation，检索增强生成）** 正是为解决这个问题而生。它让 Agent 能够连接外部知识库，在回答前先从文档中检索相关信息，再基于检索结果生成答案。AgentScope Java 提供了内置的 RAG 支持，从本地简单知识库到企业级云端知识库，覆盖全场景需求。

---

## 1. 为什么需要 RAG？

大语言模型有两个固有局限：

| 局限 | 说明 | RAG 如何解决 |
|------|------|------------|
| **知识截止** | 模型训练数据有截止日期，不知道最新信息 | 从实时知识库中检索最新文档 |
| **幻觉问题** | 模型可能"一本正经地胡说八道" | 基于检索到的真实文档生成答案，有据可查 |
| **私有数据** | 模型未见过企业内部文档 | 将企业文档构建为知识库，按需检索 |

**RAG 的核心流程**：

```
用户提问 → 向量化查询 → 从知识库检索相关文档 → 将文档注入提示词 → LLM 基于文档生成答案
```

---

## 2. AgentScope RAG 架构概览

AgentScope 的 RAG 模块由两个核心组件构成：

| 组件 | 职责 | 类比 |
|------|------|------|
| **Reader** | 读取和切分输入文档，转换为可处理的 Document 单元 | 图书管理员（整理书籍） |
| **Knowledge** | 存储文档、生成向量 Embedding、执行检索 | 图书馆检索系统 |

### 2.1 支持的知识库类型

AgentScope 支持多种类型的知识库实现：

| 类型 | 实现类 | 文档管理 | 适用场景 |
|------|--------|---------|---------|
| **本地知识库** | `SimpleKnowledge` | 代码管理（Reader） | 开发测试、数据完全自主控制 |
| **阿里云百炼** | `BailianKnowledge` | 百炼控制台 | 企业级、需重排序/查询改写/多轮对话 |
| **Dify 知识库** | `DifyKnowledge` | Dify 控制台 | 多检索模式、重排序、元数据过滤 |
| **RAGFlow** | `RAGFlowKnowledge` | RAGFlow 控制台 | 强大 OCR、知识图谱、多数据集 |

### 2.2 集成模式

AgentScope 提供了两种将 RAG 集成到 Agent 的方式：

| 模式 | 机制 | 优点 | 缺点 |
|------|------|------|------|
| **Generic 模式** | 每次推理前自动检索并注入知识 | 简单，对任何 LLM 都有效 | 即使不需要也会检索，浪费 token |
| **Agentic 模式** | Agent 自主决定何时调用检索工具 | 灵活，按需检索，更省 token | 需要模型具备较强的推理能力 |

#### 2.2.1 Generic 模式：自动检索注入

在 Generic 模式下，每次用户提问时，AgentScope 会自动从知识库检索相关文档，并将文档内容追加到用户消息中
```java
ReActAgent agent = ReActAgent.builder()
    .name("助手")
    .sysPrompt("你是一个可以访问知识库的有用助手。")
    .model(chatModel)
    .toolkit(new Toolkit())
    // 启用 Generic RAG 模式
    .knowledge(knowledge)
    .ragMode(RAGMode.GENERIC)
    .retrieveConfig(
        RetrieveConfig.builder()
            .limit(3)
            .scoreThreshold(0.3)
            .build())
    //.enableOnlyForUserQueries(true)  // 仅为用户消息检索
    .build();
```

**工作原理**：
- 用户发送查询
- 知识库自动检索相关文档
- 检索到的文档被添加到用户消息之前
- Agent 处理增强后的消息并响应

**适用场景**：客服问答、文档助手、FAQ 系统——大多数查询都需要知识库支持的场景。

#### 2.2.2 Agentic 模式：Agent 自主决定检索

在 Agentic 模式下，Agent 将 `retrieve_knowledge` 作为一个工具来使用，自主判断是否需要检索：
```java
ReActAgent agent = ReActAgent.builder()
    .name("智能体")
    .sysPrompt("你是一个拥有知识检索工具的有用助手。" +
               "需要信息时使用 retrieve_knowledge 工具。")
    .model(chatModel)
    .toolkit(new Toolkit())
    // 启用 Agentic RAG 模式
    .knowledge(knowledge)
    .ragMode(RAGMode.AGENTIC)
    .retrieveConfig(
        RetrieveConfig.builder()
            .limit(3)
            .scoreThreshold(0.5)
            .build())
    .build();
```

**工作原理：**
- 用户发送查询
- Agent 推理并决定是否检索知识
- 如果需要，Agent 调用 `retrieve_knowledge(query="...")`
- 检索到的文档作为工具结果返回
- Agent 使用检索到的信息再次推理

**适用场景**：通用对话 Agent、闲聊 + 知识问答混合场景——避免对每个问题都进行检索浪费 token。

---

## 3. 本地知识库 SimpleKnowledge

`SimpleKnowledge` 是 AgentScope 内置的本地知识库实现，适合开发测试和对数据有完全控制权的场景。

### 3.1 快速开始

```java
// 1. 创建 Embedding 模型
EmbeddingModel embeddingModel = DashScopeTextEmbedding.builder()
        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
        .modelName("text-embedding-v3")
        .dimensions(1024)
        .build();

// 2. 创建本地知识库
Knowledge knowledge = SimpleKnowledge.builder()
        .embeddingModel(embeddingModel)
        .embeddingStore(InMemoryStore.builder().dimensions(1024).build())
        .build();

// 3. 读取并切分文档并添加文档到知识库
TextReader reader = new TextReader(512, SplitStrategy.PARAGRAPH, 50);
List<Document> docs = reader.read(
                ReaderInput.fromString("""
                AgentScope Java 是一个面向智能体的编程框架，用于构建 LLM 驱动的应用程序。
                它提供了创建智能体所需的一切：ReAct 推理、工具调用、内存管理、多智能体协作等。
                AgentScope 采用 ReAct（推理-行动）范式，使智能体能够自主规划和执行复杂任务。
                """))
        .block();
knowledge.addDocuments(docs).block();

// 4. 检索
List<Document> results = knowledge.retrieve(
        "AgentScope 的核心范式是什么？",
        RetrieveConfig.builder()
                .limit(3)           // 返回最多 3 条结果
                .scoreThreshold(0.5) // 相似度阈值
                .build()
).block();

// 5. 输出结果
for (Document doc : results) {
    System.out.println("相似度: " + doc.getScore());
    System.out.println("内容: " + doc.getMetadata().getContent());
}
```

### 3.2 Reader 详解：文档读取与切分

Reader 负责将原始文档读取并切分为适合向量化的片段（Chunk）。

#### 3.2.1 切分策略 SplitStrategy

Reader支持如下四种分割策略：

| 策略 | 说明 | 适用场景 |
|------|------|---------|
| `CHARACTER` | 按字符数切分 | 简单文本，无结构要求 |
| `PARAGRAPH` | 按段落切分 | 文章、报告，保留段落完整性 |
| `SENTENCE` | 按句子切分 | 精确控制粒度 |
| `TOKEN` | 按 token 数切分 | 需要精确控制向量长度 |

#### 3.2.2 多种文档 Reader

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

**Reader 参数说明**：

| 参数 | 说明 | 建议 |
|------|------|------|
| `chunkSize` | 每个文档块的最大字符/ token 数 | 根据 Embedding 模型限制设置，通常 256-1024 |
| `splitStrategy` | 切分策略 | 结构化文档用 PARAGRAPH，精确控制用 TOKEN |
| `overlap` | 相邻 chunk 的重叠字符数 | 50-100，确保上下文连贯性 |

#### 3.2.3 从多种来源读取

```java
// 从字符串读取
List<Document> docs1 = reader.read(ReaderInput.fromString("文本内容...")).block();

// 从文件读取
List<Document> docs2 = reader.read(ReaderInput.fromPath(Path.of("/path/to/file.txt"))).block();
```

### 3.3 Vector Store：向量存储

SimpleKnowledge 需要搭配向量存储来保存文档的 Embedding。

#### 3.3.1 InMemoryStore（内存存储）

适合开发和测试，数据不持久化：
```java
InMemoryStore.builder()
        .dimensions(1024)  // 向量维度，需与 Embedding 模型一致
        .build();
```

#### 3.3.2 QdrantStore（生产级）

适合生产环境，支持持久化和高性能检索：
```java
QdrantStore.builder()
        .location("localhost:6334")     // Qdrant 服务地址
        .collectionName("my_docs")      // 集合名称
        .dimensions(1024)               // 向量维度
        .build();
```

---

## 4. 云托管知识库（Bailian）

阿里云百炼知识库，支持重排序、查询改写、多轮对话。通过 [百炼控制台](https://bailian.console.aliyun.com/) 管理文档。**百炼知识库优势**：
- **混合检索**：向量相似度 + 关键词匹配，召回率更高
- **重排序（Rerank）**：二次精排，提升检索结果相关性
- **查询改写**：理解多轮对话中的指代和省略，自动补全查询意图

### 4.1 快速开始

```java
// 创建知识库
BailianConfig config = BailianConfig.builder()
    .accessKeyId(System.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"))
    .accessKeySecret(System.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"))
    .workspaceId("llm-xxx")
    .indexId("mymxbdxxxx")
    .build();

BailianKnowledge knowledge = BailianKnowledge.builder().config(config).build();

// 检索
List<Document> results = knowledge.retrieve("查询内容",
    RetrieveConfig.builder().limit(5).scoreThreshold(0.3).build()).block();
```

### 4.2 高级配置

```java
BailianConfig config = BailianConfig.builder()
    .accessKeyId(accessKeyId).accessKeySecret(accessKeySecret)
    .workspaceId("llm-xxx").indexId("mymxbdxxxx")
    .denseSimilarityTopK(20)
    .enableReranking(true)
    .rerankConfig(RerankConfig.builder()
        .modelName("gte-rerank-hybrid").rerankMinScore(0.3f).rerankTopN(5).build())
    .enableRewrite(true)
    .rewriteConfig(RewriteConfig.builder().modelName("conv-rewrite-qwen-1.8b").build())
    .build();
```

### 4.3 多轮对话检索

```java
RetrieveConfig config = RetrieveConfig.builder()
    .limit(5).scoreThreshold(0.3)
    .conversationHistory(conversationHistory)  // 自动重写查询
    .build();
```

### 4.4 完整配置示例

```java
BailianConfig config = BailianConfig.builder()
    // === 连接配置（必填）===
    .accessKeyId(System.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"))
    .accessKeySecret(System.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"))
    .workspaceId("llm-xxx")                    // 百炼工作空间 ID
    .indexId("mymxbdxxxx")                     // 知识库索引 ID

    // === 端点配置（可选）===
    .endpoint("bailian.cn-beijing.aliyuncs.com")  // 默认值
    // 其他可用端点：
    // - bailian.cn-shanghai-finance-1.aliyuncs.com (金融云)
    // - bailian-vpc.cn-beijing.aliyuncs.com (VPC)

    // === 检索配置（可选）===
    .denseSimilarityTopK(100)                  // 向量检索 Top K，范围 0-100，默认 100
    .sparseSimilarityTopK(100)                 // 关键词检索 Top K，范围 0-100，默认 100
    // 注意：denseSimilarityTopK + sparseSimilarityTopK <= 200

    // === 重排序配置（可选）===
    .enableReranking(true)                     // 启用重排序，默认 true
    .rerankConfig(RerankConfig.builder()
        .modelName("gte-rerank-hybrid")        // 重排序模型
        .rerankMinScore(0.3f)                  // 最小分数阈值
        .rerankTopN(5)                         // 返回结果数量
        .build())

    // === 查询重写配置（可选，用于多轮对话）===
    .enableRewrite(true)                       // 启用查询重写，默认 false
    .rewriteConfig(RewriteConfig.builder()
        .modelName("conv-rewrite-qwen-1.8b")   // 重写模型
        .build())

    // === 其他配置（可选）===
    .searchFilters(List.of(Map.of("tag", "value")))  // 搜索过滤条件
    .saveRetrieverHistory(false)               // 保存检索历史，默认 false

    .build();
```

## 5. Dify 知识库集成

支持云服务和自托管，提供关键词、语义、混合、全文四种检索模式。通过 [Dify 控制台](https://cloud.dify.ai) 管理文档。

### 5.1 快速开始

```java
DifyRAGConfig config = DifyRAGConfig.builder()
    .apiKey(System.getenv("DIFY_RAG_API_KEY"))
    .datasetId("your-dataset-id")
    .retrievalMode(RetrievalMode.HYBRID_SEARCH)
    .topK(10).scoreThreshold(0.5)
    .build();

DifyKnowledge knowledge = DifyKnowledge.builder().config(config).build();

List<Document> results = knowledge.retrieve("查询内容",
    RetrieveConfig.builder().limit(5).build()).block();
```

### 5.2 检索模式

```java
.retrievalMode(RetrievalMode.KEYWORD)         // 关键词搜索
.retrievalMode(RetrievalMode.SEMANTIC_SEARCH) // 语义搜索
.retrievalMode(RetrievalMode.HYBRID_SEARCH)   // 混合搜索（推荐）
.retrievalMode(RetrievalMode.FULLTEXT)        // 全文搜索
```

### 5.3 高级配置

```java
DifyRAGConfig config = DifyRAGConfig.builder()
    .apiKey(apiKey).datasetId(datasetId)
    .retrievalMode(RetrievalMode.HYBRID_SEARCH)
    .weights(0.6)  // 混合搜索语义权重
    // Reranking
    .enableRerank(true)
    .rerankConfig(RerankConfig.builder()
        .providerName("cohere").modelName("rerank-english-v2.0").build())
    // 元数据过滤
    .metadataFilter(MetadataFilter.builder()
        .logicalOperator("AND")
        .addCondition(MetadataFilterCondition.builder()
            .name("category").comparisonOperator("=").value("AI").build())
        .build())
    .build();
```


### 5.2 Dify 知识库



#### 快速开始

```java
import io.agentscope.core.rag.knowledge.DifyKnowledge;
import io.agentscope.core.rag.knowledge.dify.DifyRAGConfig;
import io.agentscope.core.rag.knowledge.dify.RetrievalMode;

DifyRAGConfig config = DifyRAGConfig.builder()
        .apiKey(System.getenv("DIFY_RAG_API_KEY"))
        .datasetId("your-dataset-uuid")
        .retrievalMode(RetrievalMode.HYBRID_SEARCH)  // 混合检索
        .topK(10)
        .scoreThreshold(0.5)
        .build();

DifyKnowledge knowledge = DifyKnowledge.builder().config(config).build();
```

#### 四种检索模式

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| `KEYWORD` | 关键词搜索 | 精确匹配、术语查询 |
| `SEMANTIC_SEARCH` | 语义搜索 | 自然语言问题、同义词理解 |
| `HYBRID_SEARCH` | 混合搜索（推荐） | 兼顾精确和语义理解 |
| `FULLTEXT` | 全文搜索 | 大段文本匹配 |

#### 高级配置

```java
DifyRAGConfig config = DifyRAGConfig.builder()
        .apiKey(apiKey)
        .datasetId(datasetId)
        .apiBaseUrl("https://api.dify.ai/v1")  // 或自建实例

        // 检索配置
        .retrievalMode(RetrievalMode.HYBRID_SEARCH)
        .weights(0.6)  // 混合检索语义权重

        // 重排序
        .enableRerank(true)
        .rerankConfig(RerankConfig.builder()
                .providerName("cohere")
                .modelName("rerank-english-v2.0")
                .build())

        // 元数据过滤
        .metadataFilter(MetadataFilter.builder()
                .logicalOperator("AND")
                .addCondition(MetadataFilterCondition.builder()
                        .name("category")
                        .comparisonOperator("=")
                        .value("AI")
                        .build())
                .build())
        .build();
```





### 5.4 完整配置示例

```java
DifyRAGConfig config = DifyRAGConfig.builder()
    // === 连接配置（必填）===
    .apiKey(System.getenv("DIFY_RAG_API_KEY"))  // Dataset API Key
    .datasetId("your-dataset-uuid")             // 数据集 ID（UUID 格式）

    // === 端点配置（可选）===
    .apiBaseUrl("https://api.dify.ai/v1")       // Dify Cloud（默认）
    // .apiBaseUrl("https://your-dify.com/v1")  // 自托管实例

    // === 检索配置（可选）===
    .retrievalMode(RetrievalMode.HYBRID_SEARCH) // 检索模式，默认 HYBRID_SEARCH
    // 可选模式：KEYWORD（关键词）、SEMANTIC_SEARCH（语义）、HYBRID_SEARCH（混合）、FULLTEXT（全文）
    .topK(10)                                   // 检索返回数量，范围 1-100，默认 10
    .scoreThreshold(0.5)                        // 相似度阈值，范围 0.0-1.0，默认 0.0
    .weights(0.6)                               // 混合搜索语义权重，范围 0.0-1.0

    // === 重排序配置（可选）===
    .enableRerank(true)                         // 启用重排序，默认 false
    .rerankConfig(RerankConfig.builder()
        .providerName("cohere")                 // Rerank 模型提供商
        .modelName("rerank-english-v2.0")       // Rerank 模型名称
        .topN(5)                                // 重排序后返回数量
        .build())

    // === 元数据过滤（可选）===
    .metadataFilter(MetadataFilter.builder()
        .logicalOperator("AND")                 // 逻辑运算符：AND 或 OR
        .addCondition(MetadataFilterCondition.builder()
            .name("category")                   // 元数据字段名
            .comparisonOperator("=")            // 比较运算符
            .value("documentation")             // 过滤值
            .build())
        .build())

    // === HTTP 配置（可选）===
    .connectTimeout(Duration.ofSeconds(30))     // 连接超时，默认 30s
    .readTimeout(Duration.ofSeconds(60))        // 读取超时，默认 60s
    .maxRetries(3)                              // 最大重试次数，默认 3
    .addCustomHeader("X-Custom-Header", "value") // 自定义请求头

    .build();
```

## 6. RAGFlow 知识库集成

开源 RAG 引擎，支持 Docker 部署、强大 OCR、知识图谱、多数据集检索。

### 6.1 部署

```bash
git clone https://github.com/infiniflow/ragflow.git && cd ragflow
docker compose up -d  
```

### 6.2 快速开始

```java
RAGFlowConfig config = RAGFlowConfig.builder()
    .apiKey("ragflow-your-api-key")             // 必填：API Key
    .baseUrl("http://address")           // 必填：RAGFlow 服务地址
    .addDatasetId("dataset-id")                 // 必填：至少设置 dataset_ids 或 document_ids
    .topK(10).similarityThreshold(0.3)
    .build();

RAGFlowKnowledge knowledge = RAGFlowKnowledge.builder().config(config).build();

List<Document> results = knowledge.retrieve("查询内容",
    RetrieveConfig.builder().limit(5).build()).block();
```

### 6.3 多数据集和文档过滤

> **注意**：`dataset_ids` 和 `document_ids` **至少要设置一个**。如果只设置 `document_ids`，确保所有文档使用相同的嵌入模型。

```java
// 方式1：只设置数据集（搜索整个数据集）
RAGFlowConfig config1 = RAGFlowConfig.builder()
    .apiKey("ragflow-your-api-key")
    .baseUrl("http://localhost:9380")
    .addDatasetId("dataset-1")
    .addDatasetId("dataset-2")
    .build();

// 方式2：只设置文档（直接搜索指定文档，需使用相同嵌入模型）
RAGFlowConfig config2 = RAGFlowConfig.builder()
    .apiKey("ragflow-your-api-key")
    .baseUrl("http://localhost:9380")
    .addDocumentId("doc-id-1")
    .addDocumentId("doc-id-2")
    .build();

// 方式3：同时设置（在数据集中搜索指定文档）
RAGFlowConfig config3 = RAGFlowConfig.builder()
    .apiKey("ragflow-your-api-key")
    .baseUrl("http://localhost:9380")
    .addDatasetId("dataset-1")
    .addDocumentId("doc-id-1")  // 限定在该数据集中的指定文档
    .build();
```

### 6.4 元数据筛选

```java
Map<String, Object> condition = Map.of(
    "logic", "and",
    "conditions", List.of(
        Map.of("name", "author", "comparison_operator", "=", "value", "Toby"),
        Map.of("name", "date", "comparison_operator", "=", "value", "2024-01-01")
    )
);

RAGFlowConfig config = RAGFlowConfig.builder()
    .apiKey("ragflow-your-api-key")
    .baseUrl("http://localhost:9380")
    .addDatasetId("dataset-id")
    .metadataCondition(condition)
    .build();
```

### 完整配置示例

```java
RAGFlowConfig config = RAGFlowConfig.builder()
    // === 连接配置（必填）===
    .apiKey("ragflow-your-api-key")             // RAGFlow API Key
    .baseUrl("http://address")           // RAGFlow 服务地址（必填）


    // === 数据集/文档配置（至少设置一个）===
    .addDatasetId("datasetId1")
    .addDatasetId("datasetId2")  // 支持多数据集
    // 或批量设置：.datasetIds(List.of("id1", "id2"))

    // === 文档过滤（可选，限定检索范围）===
    .addDocumentId("documentId1")
    .addDocumentId("documentId2")
    // 或批量设置：.documentIds(List.of("doc1", "doc2"))
    // 注意：如果只设置 document_ids，确保所有文档使用相同的嵌入模型

    // === 检索配置（可选）===
    .topK(1024)                                 // 参与向量计算的 chunk 数量，默认 1024
    .similarityThreshold(0.2)                   // 相似度阈值，范围 0.0-1.0，默认 0.2
    .vectorSimilarityWeight(0.3)                // 向量相似度权重，范围 0.0-1.0，默认 0.3
                                                // (1 - weight) 为词项相似度权重
    //=== 分页参数 ===
    .page(1)                                    // 页码，默认 1
    .pageSize(30)                               // 每页数量，默认 30

    // === 高级检索功能（可选）===
    .useKg(false)                               // 知识图谱多跳查询，默认 false
    .tocEnhance(false)                          // 目录增强检索，默认 false
    .rerankId(1)                                // 重排序模型 ID
    .keyword(false)                             // 关键词匹配，默认 false
    .highlight(false)                           // 高亮匹配结果，默认 false
    .addCrossLanguage("en")                     // 添加目标语言
    // 或批量设置：.crossLanguages(List.of("en", "zh", "ja"))

    // === 元数据过滤（可选）===
    .metadataCondition(Map.of(
        "logic", "and",                         // 逻辑运算符：and 或 or
        "conditions", List.of(
            Map.of(
                "name", "author",               // 元数据字段名
                "comparison_operator", "=",     // 比较运算符
                "value", "Toby"                 // 过滤值
            ),
            Map.of(
                "name", "date",
                "comparison_operator", ">=",
                "value", "2024-01-01"
            )
        )
    ))

    // === HTTP 配置（可选）===
    .timeout(Duration.ofSeconds(30))            // HTTP 超时，默认 30s
    .maxRetries(3)                              // 最大重试次数，默认 3
    .addCustomHeader("X-Custom-Header", "value") // 自定义请求头

    .build();
```

**支持的比较操作符：**
- `=` - 等于
- `≠`  - 不等于
- `>`, `<`, `≥`, `≤` - 数值比较
- `contains` - 包含
- `not contains` - 不包含
- `start with` - 以...开头
- `empty` - 为空
- `not empty` - 不为空

## 6. 自定义 RAG 组件

AgentScope 鼓励自定义 RAG 组件。你可以扩展以下基类：

| 基类 | 描述 | 抽象方法 |
|------|------|----------|
| `Reader` | 文档读取器基类 | `read()`, `getSupportedFormats()` |
| `VDBStoreBase` | 向量存储基类 | `add()`, `search()` |
| `Knowledge` | 知识库实现基类 | `addDocuments()`, `retrieve()` |

### 自定义 Reader 示例

```java
public class CustomReader implements Reader {
    @Override
    public Mono<List<Document>> read(ReaderInput input) throws ReaderException {
        return Mono.fromCallable(() -> {
            // 你的自定义读取逻辑
            String content = processInput(input);
            List<String> chunks = chunkContent(content);
            return createDocuments(chunks);
        });
    }

    @Override
    public List<String> getSupportedFormats() {
        return List.of("custom", "fmt");
    }

    private List<Document> createDocuments(List<String> chunks) {
        // 创建带有元数据的 Document 对象
        // ...
    }
}
```


## 最佳实践

1. **分块大小**：根据模型的上下文窗口和使用场景选择分块大小。典型值：256-1024 个字符。

2. **重叠**：使用 10-20% 的重叠以保持块之间的上下文连续性。

3. **分数阈值**：从 0.3-0.5 开始，根据检索质量调整。

4. **Top-K**：初始检索 3-5 个文档，根据上下文窗口限制调整。

5. **模式选择**：
   - 使用 **Generic 模式**：简单问答、一致的检索模式、较弱的 LLM
   - 使用 **Agentic 模式**：复杂任务、选择性检索、强大的 LLM

6. **向量存储选择**：
   - 使用 **InMemoryStore**：开发、测试、小型数据集（<10K 文档）
   - 使用 **QdrantStore**：生产环境、大型数据集、需要持久化
   - 使用 **ElasticsearchStore**: 生产环境、大型数据集、私有部署服务。

## 完整示例

- **本地知识库示例**: [RAGExample.java](https://github.com/agentscope-ai/agentscope-java/blob/main/agentscope-examples/advanced/src/main/java/io/agentscope/examples/advanced/RAGExample.java)
- **百炼知识库示例**: [BailianRAGExample.java](https://github.com/agentscope-ai/agentscope-java/blob/main/agentscope-examples/advanced/src/main/java/io/agentscope/examples/advanced/BailianRAGExample.java)
- **Dify 知识库示例**: [DifyRAGExample.java](https://github.com/agentscope-ai/agentscope-java/blob/main/agentscope-examples/quickstart/src/main/java/io/agentscope/examples/quickstart/DifyRAGExample.java)
- **RAGFlow 知识库示例**: [RAGFlowRAGExample.java](https://github.com/agentscope-ai/agentscope-java/blob/main/agentscope-examples/quickstart/src/main/java/io/agentscope/examples/quickstart/RAGFlowRAGExample.java)
- **Elasticsearch 知识库实例**: [ElasticsearchRAGExample.java](https://github.com/agentscope-ai/agentscope-java/blob/main/agentscope-examples/advanced/src/main/java/io/agentscope/examples/advanced/ElasticsearchRAGExample.java)
- **PgVector 知识库示例**: [PgVectorRAGExample.java](https://github.com/agentscope-ai/agentscope-java/blob/main/agentscope-examples/quickstart/src/main/java/io/agentscope/examples/quickstart/PgVectorRAGExample.java)







### 5.3 RAGFlow 知识库（简要介绍）

RAGFlow 是一个开源的 RAG 引擎，以强大的文档解析能力著称：

- **深度文档理解**：基于视觉的 PDF 解析，保留表格、公式、图表结构
- **知识图谱**：支持基于图谱的增强检索
- **多数据集联合检索**：一次查询跨多个知识库

```java
// RAGFlow 集成（简要示例）
RAGFlowConfig config = RAGFlowConfig.builder()
        .apiKey(apiKey)
        .baseUrl("http://localhost:9380")
        .datasetIds(List.of("dataset-1", "dataset-2"))
        .build();

RAGFlowKnowledge knowledge = RAGFlowKnowledge.builder().config(config).build();
```

---

## 六、完整实战：构建企业文档问答助手

以下示例展示如何构建一个基于本地知识库 + Generic RAG 模式的企业文档问答助手：

```java
public class EnterpriseDocAssistant {

    public static void main(String[] args) {
        // 1. 创建 Embedding 模型
        EmbeddingModel embeddingModel = DashScopeTextEmbedding.builder()
                .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                .modelName("text-embedding-v3")
                .dimensions(1024)
                .build();

        // 2. 创建本地知识库
        Knowledge knowledge = SimpleKnowledge.builder()
                .embeddingModel(embeddingModel)
                .embeddingStore(InMemoryStore.builder().dimensions(1024).build())
                .build();

        // 3. 加载企业文档
        loadDocuments(knowledge, "/path/to/company/docs");

        // 4. 创建 RAG Agent（Generic 模式）
        ReActAgent agent = ReActAgent.builder()
                .name("DocAssistant")
                .sysPrompt("""
                        你是企业文档助手，基于知识库中的参考资料回答用户问题。
                        如果知识库中没有相关信息，请明确告知用户。
                        回答时引用参考资料的来源。
                        """)
                .model(DashScopeChatModel.builder()
                        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                        .modelName("qwen3.6-plus")
                        .build())
                .toolkit(new Toolkit())
                .knowledge(knowledge)
                .ragMode(RAGMode.GENERIC)
                .retrieveConfig(
                        RetrieveConfig.builder()
                                .limit(5)
                                .scoreThreshold(0.4)
                                .build())
                .memory(new InMemoryMemory())
                .build();

        // 5. 交互
        Msg response = agent.call(
                Msg.builder()
                        .role(MsgRole.USER)
                        .textContent("我们公司 2025 年的营收目标是什么？")
                        .build()
        ).block();

        System.out.println(response.getTextContent());
    }

    private static void loadDocuments(Knowledge knowledge, String docsPath) {
        TextReader reader = new TextReader(512, SplitStrategy.PARAGRAPH, 50);
        Path path = Path.of(docsPath);

        try {
            Files.walk(path)
                    .filter(Files::isRegularFile)
                    .filter(p -> p.toString().endsWith(".txt") || p.toString().endsWith(".md"))
                    .forEach(filePath -> {
                        try {
                            List<Document> docs = reader.read(
                                    ReaderInput.fromPath(filePath)
                            ).block();
                            knowledge.addDocuments(docs).block();
                            System.out.println("已加载: " + filePath);
                        } catch (Exception e) {
                            System.err.println("加载失败: " + filePath + " - " + e.getMessage());
                        }
                    });
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
```

---

## 七、最佳实践

### 7.1 知识库选型建议

| 需求 | 推荐方案 |
|------|---------|
| 快速验证、开发测试 | `SimpleKnowledge` + `InMemoryStore` |
| 生产环境、需要持久化 | `SimpleKnowledge` + `QdrantStore` |
| 企业级、需要重排序/查询改写 | `BailianKnowledge` |
| 已有 Dify 平台 | `DifyKnowledge` |
| 复杂 PDF 解析、知识图谱 | `RAGFlowKnowledge` |

### 7.2 Chunk 大小调优

| 文档类型 | 建议 chunkSize | 建议 overlap | 原因 |
|---------|---------------|-------------|------|
| FAQ / 问答对 | 128-256 | 0 | 每个问答独立，不需要重叠 |
| 技术文档 | 512 | 50 | 保留段落内上下文 |
| 长篇文章 | 1024 | 100 | 减少切分次数，保留更多上下文 |
| 代码文档 | 512 | 50 | 保留函数/类级别的完整性 |

### 7.3 检索参数调优

| 参数 | 调优建议 |
|------|---------|
| `limit` | 一般 3-5 条，过多会引入噪音 |
| `scoreThreshold` | 初始 0.3-0.5，根据实际效果调整。太高导致漏召回，太低引入噪音 |
| `conversationHistory` | 多轮对话场景必传，提升指代消解能力 |

### 7.4 避免常见陷阱

```java
// ❌ 错误：Embedding 模型维度与 Store 维度不一致
EmbeddingModel model = DashScopeTextEmbedding.builder().dimensions(1024).build();
InMemoryStore store = InMemoryStore.builder().dimensions(768).build();  // 维度不匹配！

// ✅ 正确：维度必须一致
EmbeddingModel model = DashScopeTextEmbedding.builder().dimensions(1024).build();
InMemoryStore store = InMemoryStore.builder().dimensions(1024).build();

// ❌ 错误：文档未切分直接入库
List<Document> docs = List.of(new Document("整本书的内容..."));  // 太长！

// ✅ 正确：使用 Reader 切分
List<Document> docs = reader.read(ReaderInput.fromString(content)).block();
```

---

## 八、本篇小结

| 要点 | 内容 |
|------|------|
| **核心组件** | Reader（文档读取切分）+ Knowledge（存储与检索） |
| **本地知识库** | `SimpleKnowledge` 支持 Text/PDF/Word/Image Reader |
| **向量存储** | `InMemoryStore`（开发）、`QdrantStore`（生产） |
| **集成模式** | Generic（自动检索注入）、Agentic（Agent 自主决定） |
| **云端知识库** | 百炼（重排序+查询改写）、Dify（多检索模式）、RAGFlow（OCR+知识图谱） |
| **调优维度** | chunkSize、overlap、limit、scoreThreshold |

RAG 让 Agent 从"靠记忆答题"进化为"开卷考试"——基于真实、可溯源的文档生成答案，这是企业级 Agent 应用落地的必备能力。

---

## 系列预告

掌握了 RAG 知识库后，下一篇我们将介绍 **AgentScope 的多智能体协作系统**——从 Pipeline 顺序执行到 MsgHub 消息共享，让多个 Agent 协同完成复杂任务，敬请期待！

*本文基于 AgentScope Java 1.0.9 版本撰写，RAG API 持续演进中，建议参考[官方文档](https://java.agentscope.io/en/task/rag.html)获取最新信息。*
