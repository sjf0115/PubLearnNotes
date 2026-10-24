在前十四篇文章中，我们系统性地构建了一个完整的**单 Agent 能力体系**：从 ReAct 循环、模型集成、Hook 监控、Tool 工具、MCP 协议，到 RAG 检索、知识问答、人工审核、任务规划和结构化输出。单 Agent 的能力已经足够强大，但面对真实世界的复杂问题，**单打独斗往往不够**。

想象一下：你要做一个智能客服系统，一个问题可能需要"意图理解 → 知识库检索 → 安全审核 → 答案生成"四个环节；你要做一个 SQL 助手，可能需要"自然语言解析 → SQL 生成 → 质量评分 → 迭代优化"多个步骤。把这些能力塞进一个 Agent，提示词会爆炸，模型会困惑，效果反而变差。

**多智能体协作的本质，就是把复杂任务拆解给多个专业 Agent，每个 Agent 负责一块，通过管道串联起来。** 这正是 AgentScope Java Pipeline 的设计哲学。

本文将深入介绍 AgentScope Java 的三种核心管道模式——**顺序管道、并行管道、循环管道**，并通过完整的代码示例，带你从单 Agent 迈向多智能体协作。

---

## 1. Pipeline 设计哲学

在 AgentScope 中，多智能体协作有两个核心概念：

| 概念 | 作用 | 适用场景 |
|------|------|---------|
| **MsgHub** | 消息广播中心，多个 Agent 共享消息，像群聊 | 讨论、头脑风暴、协作决策 |
| **Pipeline** | 结构化工作流，按固定拓扑编排 Agent 执行 | 数据处理、流水线、任务分解 |

**Pipeline 是生产环境的首选**。它通过预定义的拓扑结构（顺序、并行、循环）控制数据流，让复杂任务变得可控、可观测、可复用。

AgentScope Java 的 Pipeline 基于 **Spring AI Alibaba 的流式智能体**（SequentialAgent、ParallelAgent、LoopAgent），与 **AgentScopeAgent 子智能体** 组合使用。每个子智能体本质上是一个 `ReActAgent`，但包装了指令模板和状态键，使其能在管道中传递数据。

---

## 2. 前置条件

### 2.1 依赖

确保已引入 AgentScope 依赖（版本 1.0.12+）：
```xml
<dependency>
    <groupId>io.agentscope</groupId>
    <artifactId>agentscope</artifactId>
    <version>1.0.12</version>
</dependency>
```


## 快速开始

```
Pipeline 生成3个Agent
  [1] 英文翻译 → [2] 生成摘要 → [3] 情感分析
Pipeline 执行结果：
情感：中性
理由：该文本仅陈述任务要求与执行规范，语气客观且不含褒贬色彩，属于纯粹的功能性指令。
总结：本请求要求我作为专业摘要生成者，对给定内容进行 2-3 句的精简概括。摘要需完整保留原文的主要观点与关键信息，并严格使用与输入相同的语言版本。输出时须遵守仅限摘要正文的规定，绝不添加任何形式的额外评论或解释说明。
```

---

## 实战



## 3. SequentialAgent：顺序管道

### 3.1 场景

用户用自然语言描述查询需求，管道按顺序执行：

1. **SQL 生成器**：将自然语言转为 MySQL SQL
2. **SQL 评分器**：评估 SQL 与用户意图的匹配度（0~1）

**示例输入**：「列出过去 30 天总金额大于 500 的所有订单。」

### 3.2 核心概念

在 Pipeline 中，子智能体通过 **状态键（State Key）** 传递数据：

- `instruction("{input}")`：定义子智能体的输入指令，支持 `{key}` 占位符引用状态
- `outputKey("sql")`：将子智能体的输出写入指定状态键，供下游使用
- `includeContents(false)`：不包含历史对话内容，避免干扰

### 3.3 完整代码

```java
@Configuration
public class SequentialPipelineConfig {

    private static final String SQL_GENERATOR_PROMPT = """
        You are a MySQL database expert. Given the user's natural language request,
        output the corresponding SQL statement. Only output valid MySQL SQL.
        Do not include explanations.
        """;

    private static final String SQL_RATER_PROMPT = """
        You are a SQL quality reviewer. Given the user's natural language request
        and the generated SQL, output a single float score between 0 and 1.
        The score indicates how well the SQL matches the user intent.
        Output ONLY the number, no other text. Example: 0.85
        """;

    @Bean("sequentialSqlAgent")
    public SequentialAgent sequentialSqlAgent(Model dashScopeChatModel) {
        // ========== 子智能体 1：SQL 生成器 ==========
        ReActAgent.Builder sqlGenBuilder = ReActAgent.builder()
                .name("sql_generator")
                .model(dashScopeChatModel)
                .description("Converts natural language to MySQL SQL")
                .sysPrompt(SQL_GENERATOR_PROMPT)
                .memory(new InMemoryMemory());

        AgentScopeAgent sqlGenerateAgent = AgentScopeAgent.fromBuilder(sqlGenBuilder)
                .name("sql_generator")
                .description("Converts natural language to MySQL SQL")
                .instruction("{input}")          // 接收用户输入
                .includeContents(false)
                .outputKey("sql")                // 输出写入状态键 sql
                .build();

        // ========== 子智能体 2：SQL 评分器 ==========
        ReActAgent.Builder sqlRaterBuilder = ReActAgent.builder()
                .name("sql_rater")
                .model(dashScopeChatModel)
                .description("Scores SQL against user intent")
                .sysPrompt(SQL_RATER_PROMPT)
                .memory(new InMemoryMemory());

        AgentScopeAgent sqlRatingAgent = AgentScopeAgent.fromBuilder(sqlRaterBuilder)
                .name("sql_rater")
                .description("Scores SQL against user intent")
                .instruction("""                 // 接收上一步的 sql 和原始 input
                    Here's the generated SQL:
                    {sql}.

                    Here's the original user request:
                    {input}.
                    """)
                .includeContents(false)
                .outputKey("score")              // 输出写入状态键 score
                .build();

        // ========== 组装顺序管道 ==========
        return SequentialAgent.builder()
                .name("sequential_sql_agent")
                .description("Natural language to SQL pipeline")
                .subAgents(List.of(sqlGenerateAgent, sqlRatingAgent))
                .build();
    }
}
```

### 3.4 数据流图解

```
用户输入: "列出过去30天总金额大于500的所有订单"
        │
        ▼
┌──────────────────┐
│  SQL 生成器       │
│  instruction:    │
│  {input}         │
│  outputKey: sql  │
└────────┬─────────┘
         │ 生成: "SELECT * FROM orders..."
         ▼
┌──────────────────┐
│  SQL 评分器       │
│  instruction:    │
│  {sql} + {input} │
│  outputKey: score│
└────────┬─────────┘
         │ 评分: 0.92
         ▼
   最终结果: score=0.92
```

**关键理解**：`outputKey("sql")` 将第一个 Agent 的输出写入状态；第二个 Agent 通过 `{sql}` 占位符读取该状态。这就是管道中的**数据传递机制**。

---

## 4. ParallelAgent：并行管道

### 4.1 场景

用户给出一个主题，管道从技术、金融、市场三个角度**并行调研**，最后合并为一份综合报告。

**示例输入**：「调研大语言模型在企业软件中的当前发展状况。」

### 4.2 核心概念

- **`subAgents`**：多个子智能体同时接收相同的输入
- **`mergeStrategy`**：合并策略，将多个子智能体的输出合并为一份结果
- **`mergeOutputKey`**：合并后的结果写入指定状态键
- **`maxConcurrency`**：最大并发数

### 4.3 完整代码

```java
@Configuration
public class ParallelPipelineConfig {

    private static final String TECH_RESEARCH_PROMPT = """
        You are a technology analyst. Research the given topic from a technology perspective.
        Provide a concise 2-3 paragraph analysis covering: key technologies, trends, and innovations.
        Focus on technical aspects only.
        """;

    private static final String FINANCE_RESEARCH_PROMPT = """
        You are a financial analyst. Research the given topic from a finance and business perspective.
        Provide a concise 2-3 paragraph analysis covering: market size, investment trends, business models.
        Focus on financial and business aspects only.
        """;

    private static final String MARKET_RESEARCH_PROMPT = """
        You are a market analyst. Research the given topic from an industry and market perspective.
        Provide a concise 2-3 paragraph analysis covering: competitive landscape, growth drivers, challenges.
        Focus on market and industry aspects only.
        """;

    @Bean("parallelResearchAgent")
    public ParallelAgent parallelResearchAgent(Model dashScopeChatModel) {
        // ========== 子智能体 1：技术分析师 ==========
        ReActAgent.Builder techBuilder = ReActAgent.builder()
                .name("tech_researcher")
                .model(dashScopeChatModel)
                .sysPrompt(TECH_RESEARCH_PROMPT)
                .memory(new InMemoryMemory());

        AgentScopeAgent techResearcher = AgentScopeAgent.fromBuilder(techBuilder)
                .name("tech_researcher")
                .instruction("Research the following topic: {input}.")
                .includeContents(false)
                .outputKey("tech_analysis")
                .build();

        // ========== 子智能体 2：金融分析师 ==========
        ReActAgent.Builder financeBuilder = ReActAgent.builder()
                .name("finance_researcher")
                .model(dashScopeChatModel)
                .sysPrompt(FINANCE_RESEARCH_PROMPT)
                .memory(new InMemoryMemory());

        AgentScopeAgent financeResearcher = AgentScopeAgent.fromBuilder(financeBuilder)
                .name("finance_researcher")
                .instruction("Research the following topic: {input}.")
                .includeContents(false)
                .outputKey("finance_analysis")
                .build();

        // ========== 子智能体 3：市场分析师 ==========
        ReActAgent.Builder marketBuilder = ReActAgent.builder()
                .name("market_researcher")
                .model(dashScopeChatModel)
                .sysPrompt(MARKET_RESEARCH_PROMPT)
                .memory(new InMemoryMemory());

        AgentScopeAgent marketResearcher = AgentScopeAgent.fromBuilder(marketBuilder)
                .name("market_researcher")
                .instruction("Research the following topic: {input}.")
                .outputKey("market_analysis")
                .build();

        // ========== 组装并行管道 ==========
        return ParallelAgent.builder()
                .name("parallel_research_agent")
                .description("Multi-topic research: tech, finance, and market")
                .subAgents(List.of(techResearcher, financeResearcher, marketResearcher))
                .mergeStrategy(new ParallelAgent.DefaultMergeStrategy())
                .mergeOutputKey("research_report")   // 合并结果写入 research_report
                .maxConcurrency(3)                   // 最多 3 个并发
                .build();
    }
}
```

### 4.4 执行图解

```
用户输入: "调研大语言模型在企业软件中的发展"
        │
        ├──────────────┬──────────────┬──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ 技术分析师    │ │ 金融分析师    │ │ 市场分析师    │
│ outputKey:   │ │ outputKey:   │ │ outputKey:   │
│ tech_analysis│ │finance_analysis│ │market_analysis│
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────┬───────┴────────────────┘
                ▼
       ┌────────────────┐
       │ DefaultMerge   │
       │ 合并三份报告    │
       └───────┬────────┘
               │
               ▼
    mergeOutputKey: research_report
```

**核心优势**：三个分析师**同时执行**，总耗时 = 最慢的那个 Agent，而非三个串行之和。这在需要多角度分析的场景下效率极高。

---

## 5. LoopAgent：循环管道

### 5.1 场景

从自然语言生成 SQL，并**迭代优化**直到质量得分超过 0.5。每次迭代执行内层 SequentialAgent（SQL 生成器 → SQL 评分器），循环直到满足条件或达到最大迭代次数。

**示例输入**：「找出 2024 年下单超过 3 次的客户。」

### 5.2 核心概念

- **`subAgent`**：LoopAgent 包装一个子 Agent（通常是 SequentialAgent）
- **`loopStrategy`**：循环策略，定义何时结束循环
- **`LoopMode.condition()`**：条件循环，接收消息列表，返回 `true` 表示结束

### 5.3 完整代码

```java
@Configuration
public class LoopPipelineConfig {

    private static final double QUALITY_THRESHOLD = 0.5;

    @Bean("loopSqlAgent")
    public LoopAgent loopSqlAgent(Model dashScopeChatModel) {
        // ========== SQL 生成器（同 SequentialPipelineConfig）==========
        ReActAgent.Builder sqlGenBuilder = ReActAgent.builder()
                .name("sql_generator")
                .model(dashScopeChatModel)
                .sysPrompt(SQL_GENERATOR_PROMPT)
                .memory(new InMemoryMemory());

        AgentScopeAgent sqlGenerateAgent = AgentScopeAgent.fromBuilder(sqlGenBuilder)
                .name("sql_generator")
                .instruction("{input}")
                .includeContents(false)
                .outputKey("sql")
                .build();

        // ========== SQL 评分器（同 SequentialPipelineConfig）==========
        ReActAgent.Builder sqlRaterBuilder = ReActAgent.builder()
                .name("sql_rater")
                .model(dashScopeChatModel)
                .sysPrompt(SQL_RATER_PROMPT)
                .memory(new InMemoryMemory());

        AgentScopeAgent sqlRatingAgent = AgentScopeAgent.fromBuilder(sqlRaterBuilder)
                .name("sql_rater")
                .instruction("SQL: {sql}\nRequest: {input}")
                .includeContents(false)
                .outputKey("score")
                .build();

        // ========== 内层顺序管道 ==========
        SequentialAgent sqlAgent = SequentialAgent.builder()
                .name("sql_agent")
                .description("Generates SQL and scores its quality")
                .subAgents(List.of(sqlGenerateAgent, sqlRatingAgent))
                .build();

        // ========== 外层循环管道 ==========
        return LoopAgent.builder()
                .name("loop_sql_refinement_agent")
                .description("Iteratively refines SQL until quality score exceeds " + QUALITY_THRESHOLD)
                .subAgent(sqlAgent)
                .loopStrategy(LoopMode.condition(messages -> {
                    // 读取最后一条消息（评分器的输出）
                    if (messages == null || messages.isEmpty()) {
                        return false;
                    }
                    String text = messages.get(messages.size() - 1).getText();
                    if (text == null || text.isBlank()) {
                        return false;
                    }
                    try {
                        double score = Double.parseDouble(text.trim());
                        return score > QUALITY_THRESHOLD;  // 得分 > 0.5 时结束循环
                    } catch (NumberFormatException e) {
                        return false;
                    }
                }))
                .build();
    }
}
```

### 5.4 执行图解

```
第 1 次迭代:
  SQL 生成器 → "SELECT * FROM ..."
  SQL 评分器 → score = 0.3
  0.3 < 0.5? → 继续循环

第 2 次迭代:
  SQL 生成器 → "SELECT customer_id, COUNT(*) ..."
  SQL 评分器 → score = 0.6
  0.6 > 0.5? → 满足条件，循环结束

最终输出: score = 0.6 的 SQL
```

**关键理解**：LoopAgent 实现了**"执行 → 评估 → 反馈 → 再执行"**的闭环。每次循环的输入包含了之前的结果，模型有机会根据评分反馈改进输出。

---

## 6. 调用管道：PipelineService

定义好管道后，通过 `PipelineService` 调用：

```java
@Service
public class PipelineService {

    @Autowired
    @Qualifier("sequentialSqlAgent")
    private SequentialAgent sequentialSqlAgent;

    @Autowired
    @Qualifier("parallelResearchAgent")
    private ParallelAgent parallelResearchAgent;

    @Autowired
    @Qualifier("loopSqlAgent")
    private LoopAgent loopSqlAgent;

    public void runSequential() {
        String result = sequentialSqlAgent.call("列出过去30天总金额大于500的所有订单");
        System.out.println("Sequential Result: " + result);
    }

    public void runParallel() {
        String result = parallelResearchAgent.call("调研大语言模型在企业软件中的发展");
        System.out.println("Parallel Result: " + result);
    }

    public void runLoop() {
        String result = loopSqlAgent.call("找出2024年下单超过3次的客户");
        System.out.println("Loop Result: " + result);
    }
}
```

---

## 7. 三种模式对比与选型指南

| 特性 | SequentialAgent | ParallelAgent | LoopAgent |
|------|----------------|---------------|-----------|
| **执行方式** | 顺序执行 | 并行执行 | 循环执行 |
| **数据流** | 前一输出 → 后一输入 | 同一输入 → 多个 Agent | 迭代优化，反馈驱动 |
| **适用场景** | 流水线、步骤依赖 | 多角度分析、A/B 测试 | 迭代优化、直到达标 |
| **典型用例** | NL→SQL→评分 | 技术+金融+市场研报 | SQL 迭代优化 |
| **时间复杂度** | O(n) | O(max) | O(k × n) |
| **关键配置** | `subAgents` | `mergeStrategy`, `maxConcurrency` | `loopStrategy` |

### 7.1 组合使用：混合工作流

三种管道可以**嵌套组合**，构建更复杂的工作流：

```java
// 外层循环 + 内层顺序：SQL 迭代优化
LoopAgent(
    subAgent = SequentialAgent(
        subAgents = [sqlGenerator, sqlRater]
    ),
    loopStrategy = score > 0.5
)

// 外层顺序 + 内层并行：先并行分析，再汇总报告
SequentialAgent(
    subAgents = [
        ParallelAgent([tech, finance, market]),  // 并行调研
        SummaryAgent                              // 汇总报告
    ]
)
```

---

## 八、Pipeline 与单 Agent 的本质区别

| 维度 | 单 Agent | Pipeline 多智能体 |
|------|---------|------------------|
| **职责** | 一个 Agent 做所有事 | 每个 Agent 只做一件事 |
| **提示词** | 超长 sysPrompt，容易混乱 | 每个子 Agent 提示词精简专注 |
| **可控性** | 黑盒，难以调试 | 白盒，每个步骤可观测 |
| **复用性** | 提示词和工具绑定在一起 | 子 Agent 可复用、可组合 |
| **并发性** | 串行 | ParallelAgent 支持并行 |
| **错误处理** | 一错全错 | 可在管道中插入审核/降级步骤 |

**核心原则**：当任务可以拆分为**多个独立子任务**，且子任务之间有**明确的数据依赖关系**时，使用 Pipeline；当任务是**开放式对话**或**单一领域问题**时，单 Agent 更合适。

---

## 九、总结

本文系统介绍了 AgentScope Java 的三种核心管道模式：

| 模式 | 核心能力 | 关键配置 |
|------|---------|---------|
| **SequentialAgent** | 顺序执行，数据接力 | `subAgents`, `instruction`, `outputKey` |
| **ParallelAgent** | 并行执行，结果合并 | `subAgents`, `mergeStrategy`, `mergeOutputKey` |
| **LoopAgent** | 循环执行，条件终止 | `subAgent`, `loopStrategy` |

通过 Pipeline，你可以将复杂问题拆解为多个专业 Agent 的协作，每个 Agent 专注一个领域，通过状态键传递数据，实现**高内聚、低耦合**的多智能体系统。

### 系列文章回顾

| 篇目 | 主题 |
|------|------|
| 一 | AgentScope Java 入门：安装与对比 |
| 二 | 搭建第一个 ReAct 智能体 |
| 三 | DashScopeChatModel 百炼模型集成 |
| 四 | 思考模式（Thinking Mode） |
| 五 | Hook 机制详解 |
| 六 | Tool 工具系统 |
| 七 | MCP 协议集成 |
| 八 | Agent Skills 技能包 |
| 九 | RAG 检索增强生成 |
| 十 | EmbeddingModel 与硅基流动实战 |
| 十一 | 本地知识库问答助手 |
| 十二 | Human-in-the-Loop 人工审核 |
| 十三 | PlanNotebook 任务规划 |
| 十四 | Structured Output 结构化输出 |
| **十五（本文）** | **Pipeline 管道部署多智能体** |

下一篇我们将介绍 **MsgHub 消息广播与多智能体群聊**，敬请期待！
