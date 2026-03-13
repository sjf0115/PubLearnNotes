## 前言：AI 数据分析的“最后一公里”

在企业数字化转型的浪潮中，我们发现很多公司依然面临着“数据深渊”：业务人员想看数据，却受限于复杂的 SQL 语法；开发者虽然尝试了 Text-to-SQL，但生成的代码逻辑常有偏差，同时也无法应对复杂的统计分析、根因定位等场景。

DataAgent 应运而生。 这不是简单的指令翻译器，而是我们基于 Spring AI Alibaba 生态构建的一位“虚拟 AI 数据分析师”。它能够像专家一样思考、规划、纠错，并最终输出一份带图表、带逻辑、带深度洞察的行业级报告。

从架构上，DataAgent 是一款基于 Spring AI Alibaba 生态构建的、面向企业级复杂场景的“虚拟 AI 数据分析师”。它通过 Spring AI Alibaba Graph & Agent Framework 构建了一套具备自我规划、工具调用、反思纠错及人类干预能力的数据智能体（Agent），通过 graph、multi-agent 模式将确定性流程与模型推理结合在一起，搭建了一套兼具流程确定性与智能化的数据智能体产品。

## 1. 降维打击：为什么 DataAgent 不止是 Text-to-SQL？

![](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naLR8ibrR7GHUqVSoB6kXUoqo8tQMiaeCvpjyatm4zW8TibWQKgf7754pTs6uvo0XUnQDtUs4AGJibTg7g/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=1)

## 2. 整体架构

![](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naLR8ibrR7GHUqVSoB6kXUoqo6Z3486ClYekAxLgyJKiaM62TsXuJyMWazbchiaUenicTpeUJA48oWvLug/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=2)

## 3. 核心黑科技：DataAgent 是如何解决企业难题的？

我们不只是在写代码，而是在解决企业数据决策中的“深水区”难题。以下是 DataAgent 攻克研发痛点、实现架构突破的几大核心战役。

### 3.1 人类反馈机制 (Human-In-The-Loop)

**遇到问题**：担心 AI 智商掉线？一个错误的执行计划可能瞬间拖垮生产库，甚至“一步错步步错”。

**解决方案**：
- 入口：运行时请求参数 humanFeedback=true（GraphController → GraphServiceImpl）。
- 数据字段：agent.human_review_enabled 用于保存配置，运行时以请求参数为准。
- 图编排：PlanExecutorNode 检测 HUMAN_REVIEW_ENABLED，转入 HumanFeedbackNode。
- 暂停与恢复：CompiledGraph 使用 interruptBefore(HUMAN_FEEDBACK_NODE)，无反馈时进入“等待”，反馈到达后通过 threadId 继续执行。

**反馈结果**：给 AI 穿上约束衣！同意、修改或驳回，都在你一念之间。让 AI 既有速度，又懂规矩。

![](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naLR8ibrR7GHUqVSoB6kXUoqoia5ngC5FEpHWO23ZYflcwwfbhsOI3eIhPXANW2zjRmSIDIbTicee61rQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=3)

![](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naLR8ibrR7GHUqVSoB6kXUoqoGia89LPV2MZARZ7GPz6Jn4H6tZngPCDs9Bg36iaJYTf0Aeo9ogib2ONrQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=4)

### 3.2 Prompt 动态配置与自动优化

**遇到问题**：修改一句 Prompt 就要重启系统？不同模型对 Prompt 脾气不同，一套模板走天下根本行不通。

**解决方案**：
- 配置入口：`/api/prompt-config/*`，数据表 user_prompt_config。
- 作用范围：支持按 agentId 绑定或全局配置（agentId 为空）。
- Prompt 类型：report-generator、planner、sql-generator、python-generator、rewrite。
- 自动优化方式：ReportGeneratorNode 拉取启用配置（按 priority 与 display_order 排序），通过 PromptHelper.buildReportGeneratorPromptWithOptimization 拼接“优化要求”。
- 当前实现重点：报告生成节点已落地优化；其他类型为预留能力。

**获得效果**： 像配置 Excel 一样调优 AI。运维人员无需重启，即可让 DataAgent 瞬间从“菜鸟分析师”变身“首席架构师”。

![](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naLR8ibrR7GHUqVSoB6kXUoqoQUu8R2pSh3xXT8jRy5HicfJdhZGrNSBUFqSuVtvibAwN8cpQibFxshrRg/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=5)

![](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naLR8ibrR7GHUqVSoB6kXUoqoVDEpujFl6jOLhENibsSFS3ERBursdzZhSicgtgIfiahRteIR2icbbJghEQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=6)

### 3.3 深度 RAG 与混合检索增强

**遇到问题**： 纯向量检索常召回一堆废话？AI 不认识你的业务缩写？表结构太复杂，AI 搜不到。

**解决方案**：
- 查询重写：EvidenceRecallNode 将多轮上下文与用户问题组装为检索指令，调用 LLM 生成 standaloneQuery，避免上下文遗漏与歧义。
- 召回通道：AgentVectorStoreService 作为统一入口，默认走向量检索；开启混合检索后走 AbstractHybridRetrievalStrategy，将“向量召回 + 关键词召回”进行融合。（用户需要提供混合检索实现。当前默认只支持es）
- 召回过滤：DynamicFilterService 生成基于智能体与知识类型的过滤条件，限制检索范围，避免跨智能体串库。
- 文档类型：业务知识（business_knowledge）+ 智能体知识（agent_knowledge）两类，按 agentId/type 元数据过滤后合并为 evidence，注入后续 prompt。
- 关键配置：spring.ai.alibaba.data-agent.vector-store.enable-hybrid-search 控制是否开启混合检索；相似度阈值与 TopK 通过向量库配置项控制（如 top-k、similarity-threshold）。
- 输出形式：evidence 文档以标题/摘要/片段形式汇总，作为 EvidenceRecallNode 输出内容进入后续规划于 SQL 生成阶段。

**获得效果**： AI 拥有了老员工的“直觉”。它能秒懂你的业务逻辑，即便表名全是乱码，它也能精准命中。

![](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naLR8ibrR7GHUqVSoB6kXUoqowAYicNQl1FlYHico6fxTWBDrubETpMDkLBE46XKWQyc1lA058gl5biaDg/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=7)

![](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naLR8ibrR7GHUqVSoB6kXUoqoicg0xFY8WcWcuFBgtxDGRAKZL8B6rcQ0DQu1SjjicVgAUibRqyagYd64A/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=8)

### 3.4 容器化 Python 执行引擎

**遇到问题**：SQL 只能算数，不能预测。想看趋势图、做线性回归？SQL 此时显得苍白无力。

**解决方案**：
- 代码生成：PythonGenerateNode 根据计划与 SQL 结果生成 Python。
- 代码执行：PythonExecuteNode 使用 CodePoolExecutorService（Docker/Local/AI 模拟）。
- 执行配置：`spring.ai.alibaba.data-agent.code-executor.*`（默认 Docker 镜像 continuumio/anaconda3:latest）。
- 结果回传：执行结果写回 PYTHON_EXECUTE_NODE_OUTPUT，PythonAnalyzeNode 汇总后写入 SQL_EXECUTE_NODE_OUTPUT，用于最终报告。

**获得效果**： 赋予 AI 科学家级的建模能力。不仅能提取数据，还能输出带图表、带算法、带深度预测的高质量产出。

![](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naLR8ibrR7GHUqVSoB6kXUoqosQVC4cJWHTMldXrwicFRDF35WTAhSFh7TwMIVIEk07hcvnd86mf03XQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=9)

![](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naLR8ibrR7GHUqVSoB6kXUoqo6tVe1ichaQibZbSzwldd9Ev2OIAWEeUCibJbubnXOicviavGcmIOicjZvZ3w/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=10)

### 3.5 流式输出 (SSE) 与多轮对话管理

**遇到问题**：分析任务耗时太长，用户盯着屏幕转圈圈，以为系统挂了。

**解决方案**：
- 流式输出：GraphController SSE + GraphServiceImpl 流式处理。
- 文本标记：TextType 在流中标记 SQL/JSON/HTML/Markdown，前端据此渲染。
- 多轮对话：MultiTurnContextManager 记录“用户问题+规划结果”，注入到后续请求。
- 模式切换：spring.ai.alibaba.data-agent.llm-service-type 支持 STREAM/BLOCK

**获得效果**：极致的交互快感！让用户亲眼看到 AI 正在如何“思考”与“推演”，每一秒都有获得感。

![](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naLR8ibrR7GHUqVSoB6kXUoqovUMdtY8NuOITwFO9q9n805w16y5sybSZT9MVvwD9hiaEprSTSiajlhng/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=11)

![](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naLR8ibrR7GHUqVSoB6kXUoqoticicmrUdKX15A0ia1J5235aPpMAzAACcF8f9giam6Lvicl48j0h3ZekMsg/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=12)

### 3.6 MCP 服务器发布与多模型调度

**遇到问题**： DataAgent 虽好，但只能在自研系统用？想集成到 Claude 或 IDE？适配成本高到吓人。

**解决方案**：
- MCP：McpServerService 提供 NL2SQL 与 Agent 列表工具，使用 Mcp Server Boot Starter。
- 多模型调度：ModelConfig 配置模型，AiModelRegistry 缓存当前 Chat/Embedding 模型并支持热切换（同一时间每类仅一个激活模型）。
- 已内置工具：nl2SqlToolCallback、listAgentsToolCallback。

**获得效果**：无处不在的 AI 生产力。它是你的数据中心，也是你办公软件里随叫随到的超强插件。

![](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naLR8ibrR7GHUqVSoB6kXUoqo2tdbLEruODIOdSeFcPyiaJicCnr7hakKbZqQiaXkJQoBKS3BkD2k9sXmA/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=13)

![](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naLR8ibrR7GHUqVSoB6kXUoqofrIqS61gwUicRXaeaqciaa3LMTBk8KabOhjYrHN3LOgSd8BUlYVkanwA/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=14)

### 3.7 多数据源接入

**遇到问题**：企业数据散落在 MySQL、PostgreSQL 等各类库中，跨库取数像是在做“情报搜集”，配置繁琐且标准不一。

**解决方案**：
- 元数据存储：数据源配置写入 datasource，智能体绑定写入 agent_datasource，选表写入 agent_datasource_tables，逻辑外键写入 logical_relation。
- 类型扩展：BizDataSourceTypeEnum 定义数据源类型；
- 对应的 Accessor + DBConnectionPool 负责不同数据库协议与方言的访问。
- Schema 初始化：AgentDatasourceController 触发初始化，SchemaService 通过 AccessorFactory 拉取表/列/外键并写入向量库。
- 运行时选择：DatabaseUtil 从当前智能体获取激活数据源，动态选择 Accessor 执行 SQL。
- 约束：同一智能体同一时间仅允许启用一个数据源（AgentDatasourceService.toggleDatasourceForAgent）。

**获得效果**：一个智能体，纵览全司数据！无论数据在哪儿，DataAgent 都能精准“路由”。它是数据孤岛的终结者，让跨库分析像查询单表一样简单。

![](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naLR8ibrR7GHUqVSoB6kXUoqob3cTss7g4zglMWuozobXZWrrTCZFFiaibp4MswUzwfPLE80Ac7fenAcQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=15)

![](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naLR8ibrR7GHUqVSoB6kXUoqomYPnIcWXiaahb2zAjpXa3uKQE5JoBYwia7h1yoEAiaWIKVoQGlYnZ7V7w/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=16)

### 3.8 报告生成与摘要建议

**遇到问题**： 查出来一堆数字有什么用？领导要的是洞察，是结论，是能直接发在群里的 HTML 报告。

**解决方案**：
- 报告节点：ReportGeneratorNode 读取计划、SQL/Python 结果与摘要建议（summary_and_recommendations）。
- 输出格式：默认 HTML，plainReport=true 输出 Markdown（简洁报告）。
- 优化提示词：自动拼接优化配置后生成报告。

**获得效果**：把分析师的一天缩短为 10 秒。从查数到成稿，DataAgent 承包了所有体力活，让你只负责最后的一锤定音。

![](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naLR8ibrR7GHUqVSoB6kXUoqoYkIVQs4JUhew8ic1VFeOZWyS41TjYM8SSE0vfUryTVXdlSMs7gPanjw/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=17)

### 3.9 NL2SQL 转换, 语义模型，逻辑外键引擎

**遇到问题**： 纯大模型写 SQL 经常“盲目自信”，不是字段写错，就是不懂业务术语。语法错误导致的执行中断更是家常便饭。

**解决方案**：
- 语义模型层：通过管理端定义的术语映射规则，在生成阶段强制约束。
- 两阶段校验：SqlGenerateNode 生成后接 SemanticConsistencyNode 检查语义一致性。
- 自愈循环：SqlExecuteNode 捕获执行错误并反馈给 Graph 状态机，触发重定向至重写节点进行纠错。
- 逻辑外键：写入外部的业务逻辑的外键，不写入业务数据库。增强对表的理解能力。

**获得效果**：让 AI 拥有“职业分析师”的严谨。 告别报错，告别幻觉。它不仅懂 SQL 语法，更懂你的业务逻辑，让每一次查询都精准命中。

### 3.10 API Key 与权限管理

**遇到问题**：接口裸奔？权限失控？想对外开放能力却怕费用爆炸或数据泄露。

**解决方案**:
- 管理端：AgentController 支持生成、重置、删除与启用/禁用 API Key。
- 数据字段：agent.api_key 与 agent.api_key_enabled。
- 调用方式：请求头 X-API-Key。
- 注意：默认不开启鉴权拦截；生产需开启 spring.ai.alibaba.data-agent.api-key.enabled=true。

**获得效果**：生产级安全防护。让你的 DataAgent 不仅是业务利器，更是安全可控的企业级数字资产。

![](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naLR8ibrR7GHUqVSoB6kXUoqoIPuDrqsHwMmWciarF7WrIhumtGP0RY1jSH61TgZibL0WFGtBic7AJXK7w/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=18)

## 4. 结语：让数据价值触手可及

DataAgent 的核心价值在于，它不仅仅是完成了一次查询，而是将“数据处理的工程化”与“大模型的推理能力”深度结合。结合 Spring AI Alibaba  的 Graph 编排与 Agentic 推理能力，DataAgent 将确定性流程与模型推理结合在一起，将原本碎片化的分析过程，转化为了兼具流程确定性与智能化的数据智能体。

未来，数据不再是冷冰冰的行列，而是每一位业务决策者都能随手调用的“智库”。

> [告别传统 Text-to-SQL：基于 Spring AI Alibaba 的数据分析智能体 DataAgent 深度解析](https://mp.weixin.qq.com/s/xPB9y5Wvl5_ZJck0ZeJulA)
