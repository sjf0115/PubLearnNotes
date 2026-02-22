## 1. 概述

大模型 (LLMs) 是无状态的，这意味着它们不保留有关先前交互的信息。当您想要在多个交互中维护上下文或状态时，这可能是一个限制。为了解决这个问题，Spring AI 提供了 Chat Memory 功能，允许您存储和检索与 LLM 的多个交互中的信息。

`ChatMemory` 接口可以使用使用不同的存储介质实现 Chat Memory。Message 的底层存储由 `ChatMemoryRepository` 处理，其唯一职责是存储和检索 message。由 `ChatMemory` 实现决定保留哪些 message 以及何时删除它们。策略示例可能包括保留最后 N 条 message、保留特定时间段的 message 或保留达到特定令牌限制的 message。

在实现 Chat Memory 实现之前，了解 Chat Memory 和 Chat Hisroty 之间的区别很重要：
- Chat Memory：大模型保留并用于在整个对话中保持上下文感知的信息。
- Chat History：整个对话历史，包括用户和模型之间交换的所有 message。

`ChatMemory` 抽象旨在管理聊天内存。它允许您存储和检索与当前对话上下文相关的 message。但是，它不适合存储聊天历史。如果您需要维护所有交换 message 的完整记录，您应该考虑使用不同的方法，例如依赖 Spring Data 来高效存储和检索完整的聊天历史。

## 2. 快速开始

Spring AI 自动配置一个 `ChatMemory` bean，您可以直接在应用程序中使用它。默认情况下，使用内存存储组件（`InMemoryChatMemoryRepository`）来存储 message 以及使用 `MessageWindowChatMemory` 实现来管理对话历史。如果已经配置了其他的存储组件(例如 Cassandra、JDBC 或 Neo4j)，Spring AI 将使用其存储。
```java
@Autowired
ChatMemory chatMemory;
```
以下部分将详细描述 Spring AI 中可用的不同 Memory 存储策略和存储组件。

## 3. Memory 类型

`ChatMemory` 抽象允许您实现各种类型的 Chat Memory 以适应不同的用例。Chat Memory 的选择会显著影响应用程序的性能和行为。本节描述了 Spring AI 提供的内置 Chat Memory 类型及其特性。

### 3.1 Message Window Chat Memory

`MessageWindowChatMemory` 维护一个最大指定大小的 message 窗口。当 message 数量超过最大值时，会删除较旧的 message，但保留系统 message。默认窗口大小为 20 条 message:
```java
MessageWindowChatMemory memory = MessageWindowChatMemory.builder()
    .maxMessages(10)
    .build();
```
这是 Spring AI 用于自动配置 `ChatMemory` bean 的默认 message 类型。


## 4. Memory 存储

Spring AI 提供 `ChatMemoryRepository` 抽象用于存储聊天消息。本节描述了 Spring AI 提供的内置存储组件以及如何使用它们，但您也可以根据需要自定义实现自己的存储组件。

### 4.1 InMemoryChatMemoryRepository

`InMemoryChatMemoryRepository` 使用 `ConcurrentHashMap` 在内存中存储 message。默认情况下，如果没有配置存储组件，Spring AI 会自动配置一个类型为 `InMemoryChatMemoryRepository` 的 `ChatMemoryRepository` bean，您可以直接在应用程序中使用它:
```java
@Autowired
ChatMemoryRepository chatMemoryRepository;
```
如果您想手动创建 `InMemoryChatMemoryRepository`，可以这样做:
```java
ChatMemoryRepository repository = new InMemoryChatMemoryRepository();
```
### 4.2 JdbcChatMemoryRepository

`JdbcChatMemoryRepository` 是一个内置实现，使用 JDBC 在关系数据库中存储 message。它开箱即用地支持多个数据库，适合需要持久存储 Chat Memory 的应用。

首选添加如下依赖到项目中:
```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-model-chat-memory-repository-jdbc</artifactId>
</dependency>
```
Spring AI 为 `JdbcChatMemoryRepository` 提供自动配置，您可以直接在应用程序中使用它:
```java
@Autowired
JdbcChatMemoryRepository chatMemoryRepository;

ChatMemory chatMemory = MessageWindowChatMemory.builder()
  .chatMemoryRepository(chatMemoryRepository)
  .maxMessages(10)
  .build();
```
如果您想手动创建 `JdbcChatMemoryRepository`，可以通过提供 `JdbcTemplate` 实例和 `JdbcChatMemoryRepositoryDialect` 来实现：
```java
ChatMemoryRepository chatMemoryRepository = JdbcChatMemoryRepository.builder()
    .jdbcTemplate(jdbcTemplate)
    .dialect(new PostgresChatMemoryRepositoryDialect())
    .build();

ChatMemory chatMemory = MessageWindowChatMemory.builder()
    .chatMemoryRepository(chatMemoryRepository)
    .maxMessages(10)
    .build();
```

#### 4.2.1 支持的数据库和方言抽象

Spring AI 通过方言抽象支持多个关系数据库。以下数据库开箱即用地支持：
- PostgreSQL
- MySQL / MariaDB
- SQL Server
- HSQLDB

当使用 `JdbcChatMemoryRepositoryDialect.from(DataSource)` 时，可以从 JDBC URL 自动检测正确的方言。您可以通过实现 `JdbcChatMemoryRepositoryDialect` 接口来扩展对其他数据库的支持。


#### 4.2.2 配置属性

| 属性 | 描述 | 默认值 |
| :------------- | :------------- | :------------- |
| `spring.ai.chat.memory.repository.jdbc.initialize-schema`	| 控制何时初始化架构。值: `embedded`(默认)、`always`、`never`。	| `embedded` |
| `spring.ai.chat.memory.repository.jdbc.schema` | 用于初始化的架构脚本的位置。支持 `classpath: URL` 和平台占位符。| `classpath:org/springframework/ai/chat/memory/repository/jdbc/schema-@@platform@@.sql` |
| `spring.ai.chat.memory.repository.jdbc.platform` | 如果在初始化脚本中使用了 `@@platform@@` 占位符，则使用的平台。|	自动检测 |

#### 4.2.3 架构初始化

自动配置将在启动时使用特定于供应商的 SQL 脚本自动创建 `SPRING_AI_CHAT_MEMORY` 表。默认情况下，架构初始化仅针对嵌入式数据库 (H2、HSQL、Derby 等)。

你可以使用 `spring.ai.chat.memory.repository.jdbc.initialize-schema` 属性控制架构初始化:
```
spring.ai.chat.memory.repository.jdbc.initialize-schema=embedded # Only for embedded DBs (default)
spring.ai.chat.memory.repository.jdbc.initialize-schema=always   # Always initialize
spring.ai.chat.memory.repository.jdbc.initialize-schema=never    # Never initialize (useful with Flyway/Liquibase)
```
要覆盖架构脚本位置，请使用：
```
spring.ai.chat.memory.repository.jdbc.schema = classpath:/custom/path/schema-mysql.sql
```

#### 4.2.4 扩展方言

要添加对新数据库的支持，需要实现 `JdbcChatMemoryRepositoryDialect` 接口并提供用于选择、插入和删除 message 的 SQL。然后，您可以将自定义方言传递给存储组件构建器：
```java
ChatMemoryRepository chatMemoryRepository = JdbcChatMemoryRepository.builder()
    .jdbcTemplate(jdbcTemplate)
    .dialect(new MyCustomDbDialect())
    .build();
```




### 4.3 CassandraChatMemoryRepository

`CassandraChatMemoryRepository` 使用 Apache Cassandra 存储 message。它适合需要持久存储聊天内存的应用程序，特别是在可用性、持久性、扩展性方面，以及利用生存时间 (TTL) 功能时。

`CassandraChatMemoryRepository` 具有时间序列架构，保留所有过去的聊天窗口记录，对治理和审计很有价值。建议将生存时间设置为某个值，例如三年。

首选添加如下依赖到项目中:
```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-model-chat-memory-repository-cassandra</artifactId>
</dependency>
```
Spring AI 为 `CassandraChatMemoryRepository` 提供自动配置，您可以直接在应用程序中使用它：
```java
@Autowired
CassandraChatMemoryRepository chatMemoryRepository;

ChatMemory chatMemory = MessageWindowChatMemory.builder()
    .chatMemoryRepository(chatMemoryRepository)
    .maxMessages(10)
    .build();
```
如果您想手动创建 `CassandraChatMemoryRepository`，可以通过提供 `CassandraChatMemoryRepositoryConfig` 实例来实现：
```java
ChatMemoryRepository chatMemoryRepository = CassandraChatMemoryRepository
    .create(CassandraChatMemoryRepositoryConfig.builder().withCqlSession(cqlSession));

ChatMemory chatMemory = MessageWindowChatMemory.builder()
    .chatMemoryRepository(chatMemoryRepository)
    .maxMessages(10)
    .build();
```

### 4.4 Neo4j ChatMemoryRepository

`Neo4jChatMemoryRepository` 是一个内置实现，使用 Neo4j 将聊天 message 作为节点和关系存储在属性图数据库中。它适合想要利用 Neo4j 的图功能进行聊天内存持久化的应用程序。

首选添加如下依赖到项目中:
```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-model-chat-memory-repository-neo4j</artifactId>
</dependency>
```
Spring AI 为 `Neo4jChatMemoryRepository` 提供自动配置，您可以直接在应用程序中使用它：
```java
@Autowired
Neo4jChatMemoryRepository chatMemoryRepository;

ChatMemory chatMemory = MessageWindowChatMemory.builder()
    .chatMemoryRepository(chatMemoryRepository)
    .maxMessages(10)
    .build();
```
如果您想手动创建 Neo4jChatMemoryRepository，可以通过提供 Neo4j Driver 实例来实现：
```java
ChatMemoryRepository chatMemoryRepository = Neo4jChatMemoryRepository.builder()
    .driver(driver)
    .build();

ChatMemory chatMemory = MessageWindowChatMemory.builder()
    .chatMemoryRepository(chatMemoryRepository)
    .maxMessages(10)
    .build();
```

### 4.5 CosmosDBChatMemoryRepository



## 5. 在 Chat Client 中使用 Memory

使用 ChatClient API 时，您可以提供 `ChatMemory` 实现来维护多个交互之间的对话上下文。Spring AI 提供了几个内置的 Advisors，您可以使用它们来根据您的需求配置 `ChatClient` 的内存行为:
- `MessageChatMemoryAdvisor`：此 advisor 使用提供的 `ChatMemory` 实现管理对话内存。在每次交互时，它从内存中检索对话历史并将其作为 message 集合包含在 prompt 中。
- `PromptChatMemoryAdvisor`：此 advisor 使用提供的 `ChatMemory` 实现管理对话内存。在每次交互时，它从内存中检索对话历史并将其作为纯文本附加到系统 prompt 中。
- `VectorStoreChatMemoryAdvisor`：此 advisor 使用提供的 `VectorStore` 实现管理对话内存。在每次交互时，它从向量存储中检索对话历史并将其作为纯文本附加到系统 message 中。

> 目前，在执行工具调用时与大模型交换的中间 message 不会存储在内存中。这是当前实现的弊端，将在未来的版本中解决。如果您需要存储这些 message，请参阅[用户控制的工具执行的说明](https://docs.spring.io/spring-ai/reference/api/tools.html#_user_controlled_tool_execution)。

例如，如果您想将 `MessageWindowChatMemory` 与 `MessageChatMemoryAdvisor` 一起使用，可以这样配置：
```java
ChatMemory chatMemory = MessageWindowChatMemory.builder().build();

ChatClient chatClient = ChatClient.builder(chatModel)
    .defaultAdvisors(MessageChatMemoryAdvisor.builder(chatMemory).build())
    .build();
```
当对 ChatClient 执行调用时，内存将由 `MessageChatMemoryAdvisor` 自动管理。对话历史将根据指定的会话 ID 从内存中检索：
```java
String conversationId = "007";

chatClient.prompt()
    .user("Do I have license to code?")
    .advisors(a -> a.param(ChatMemory.CONVERSATION_ID, conversationId))
    .call()
    .content();
```

### 5.1 PromptChatMemoryAdvisor

> 自定义模板

`PromptChatMemoryAdvisor` 使用默认模板将检索到的对话内存来增强系统 message。您可以通过 `.promptTemplate()` 构建器方法提供自己的 `PromptTemplate` 对象来自定义此行为。

> 这里提供的 PromptTemplate 自定义 advisor 如何将检索到的内存与系统 message 合并。这与在 ChatClient 本身上配置 TemplateRenderer(使用 .templateRenderer())不同，后者影响 advisor 运行之前初始用户/系统提示内容的渲染。有关客户端级模板渲染的更多详细信息，请参阅 ChatClient 提示模板。

自定义 `PromptTemplate` 可以使用任何 `TemplateRenderer` 实现(默认情况下，它使用基于 `StringTemplate` 引擎的 `StPromptTemplate`)。重要要求是模板必须包含以下两个占位符：
- 一个 instructions 占位符，用于接收原始系统 message。
- 一个 memory 占位符，用于接收检索到的对话内存。

### 5.2 VectorStoreChatMemoryAdvisor 自定义模板

`VectorStoreChatMemoryAdvisor` 使用默认模板将检索到的对话内存来增强系统 message。您可以通过 `.promptTemplate()` 构建器方法提供自己的 PromptTemplate 对象来自定义此行为。

> 这里提供的 PromptTemplate 自定义 advisor 如何将检索到的内存与系统 message 合并。这与在 ChatClient 本身上配置 TemplateRenderer(使用 .templateRenderer())不同，后者影响 advisor 运行之前初始用户/系统提示内容的渲染。有关客户端级模板渲染的更多详细信息，请参阅 ChatClient 提示模板。

自定义 `PromptTemplate` 可以使用任何 `TemplateRenderer` 实现(默认情况下，它使用基于 `StringTemplate` 引擎的 `StPromptTemplate`)。重要要求是模板必须包含以下两个占位符：
- 一个 instructions 占位符，用于接收原始系统 message。
- 一个 long_term_memory 占位符，用于接收检索到的对话内存。

## 6. 在 ChatModel 中使用 Memory

如果您直接使用 `ChatModel` 而不是 `ChatClient`，您可以显式管理内存：
```java
// Create a memory instance
ChatMemory chatMemory = MessageWindowChatMemory.builder().build();
String conversationId = "007";

// First interaction
UserMessage userMessage1 = new UserMessage("My name is James Bond");
chatMemory.add(conversationId, userMessage1);
ChatResponse response1 = chatModel.call(new Prompt(chatMemory.get(conversationId)));
chatMemory.add(conversationId, response1.getResult().getOutput());

// Second interaction
UserMessage userMessage2 = new UserMessage("What is my name?");
chatMemory.add(conversationId, userMessage2);
ChatResponse response2 = chatModel.call(new Prompt(chatMemory.get(conversationId)));
chatMemory.add(conversationId, response2.getResult().getOutput());

// The response will contain "James Bond"
```



> []()
