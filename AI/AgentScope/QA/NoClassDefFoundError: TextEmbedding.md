## 1. 问题

运行如下代码：
```java
// 1. 创建 Embedding 模型
EmbeddingModel embeddingModel = DashScopeTextEmbedding.builder()
        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
        .modelName("tongyi-embedding-vision-plus-2026-03-06")
        .dimensions(1024)
        .build();

// 2. 创建本地知识库
Knowledge knowledge = SimpleKnowledge.builder()
        .embeddingModel(embeddingModel)
        // 向量存储: InMemoryStore 内存存储
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
抛出如下异常：
```java
Exception in thread "main" java.lang.NoClassDefFoundError: com/alibaba/dashscope/embeddings/TextEmbedding
	at io.agentscope.core.embedding.dashscope.DashScopeTextEmbedding.lambda$embed$0(DashScopeTextEmbedding.java:117)
	at reactor.core.publisher.MonoCallable$MonoCallableSubscription.request(MonoCallable.java:134)
	at reactor.core.publisher.Operators$MultiSubscriptionSubscriber.set(Operators.java:2361)
	at reactor.core.publisher.FluxOnErrorResume$ResumeSubscriber.onSubscribe(FluxOnErrorResume.java:75)
	at reactor.core.publisher.MonoCallable.subscribe(MonoCallable.java:48)
	at reactor.core.publisher.InternalMonoOperator.subscribe(InternalMonoOperator.java:75)
	at reactor.core.publisher.FluxRetryWhen.subscribe(FluxRetryWhen.java:81)
	at reactor.core.publisher.MonoRetryWhen.subscribeOrReturn(MonoRetryWhen.java:47)
	at reactor.core.publisher.Mono.subscribe(Mono.java:4553)
	at reactor.core.publisher.MonoIgnoreThen$ThenIgnoreMain.subscribeNext(MonoIgnoreThen.java:268)
	at reactor.core.publisher.MonoIgnoreThen.subscribe(MonoIgnoreThen.java:51)
	at reactor.core.publisher.Mono.subscribe(Mono.java:4569)
	at reactor.core.publisher.FluxFlatMap$FlatMapMain.onNext(FluxFlatMap.java:432)
	at reactor.core.publisher.FluxIterable$IterableSubscription.slowPath(FluxIterable.java:335)
	at reactor.core.publisher.FluxIterable$IterableSubscription.request(FluxIterable.java:294)
	at reactor.core.publisher.FluxFlatMap$FlatMapMain.onSubscribe(FluxFlatMap.java:375)
	at reactor.core.publisher.FluxIterable.subscribe(FluxIterable.java:200)
	at reactor.core.publisher.FluxIterable.subscribe(FluxIterable.java:82)
	at reactor.core.publisher.Mono.subscribe(Mono.java:4569)
	at reactor.core.publisher.Mono.block(Mono.java:1772)
	at com.example.rag.SimpleKnowledgeQuickStart.main(SimpleKnowledgeQuickStart.java:49)
Caused by: java.lang.ClassNotFoundException: com.alibaba.dashscope.embeddings.TextEmbedding
	at java.base/jdk.internal.loader.BuiltinClassLoader.loadClass(BuiltinClassLoader.java:641)
	at java.base/jdk.internal.loader.ClassLoaders$AppClassLoader.loadClass(ClassLoaders.java:188)
	at java.base/java.lang.ClassLoader.loadClass(ClassLoader.java:525)
	... 21 more
```

## 2. 分析

> 问题很明确：缺少阿里云 DashScope Java SDK 依赖。

DashScopeTextEmbedding 虽然属于 AgentScope 框架，但它在内部需要调用阿里云官方的 DashScope SDK 中的 com.alibaba.dashscope.embeddings.TextEmbedding 类来完成实际的 Embedding 计算。你的 pom.xml 中引入了 io.agentscope:agentscope（all-in-one 包），但这个包没有将 DashScope SDK 作为传递依赖引入。因此：
- AgentScope 自身的类（如 DashScopeTextEmbedding）能找到 ✅
- DashScope SDK 的类（如 TextEmbedding）找不到 ❌ → NoClassDefFoundError

## 3. 方案

在 pom.xml 中显式添加阿里云 DashScope Java SDK 依赖：
```xml
<dependencies>
    <!-- AgentScope All-in-One -->
    <dependency>
        <groupId>io.agentscope</groupId>
        <artifactId>agentscope</artifactId>
        <version>1.0.12</version>
    </dependency>

    <!-- 阿里云 DashScope SDK（Embedding 功能所需） -->
    <dependency>
        <groupId>com.alibaba</groupId>
        <artifactId>dashscope-sdk-java</artifactId>
        <version>${dashscope.version}</version>
    </dependency>
</dependencies>
```
官网提及 `All-in-one: Single dependency with DashScope SDK and MCP SDK included, get started quickly`，但 agentscope-1.0.12 的实际依赖没有 com.alibaba:dashscope-sdk-java。
