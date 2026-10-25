**编者按**

最近，我们在首期 OceanBase Hours 活动上推出了面向 AI 时代的湖库一体 AI 数据库，整套架构分为三层。
- 最底层是存算分离的 OceanBase Lakebase 引擎，为结构化数据、图片、音视频、PDF、向量、JSON 等多模态数据提供统一存储；
- 最上层是我们开发的应用 Agent，包括面向数据开发工程师的 DataStudio 和面向业务分析师的 DataPilot；
- 夹在中间的是 **上下文层** ——数据上下文让 AI 理解企业，应用上下文让 AI 理解用户。

这一篇我们先讲清中间这一层——上下文层里最硬的两块砖：本体（Ontology）和语义层（Semantic Layer）。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/FRE5OkhV0oysbJicN9GFgeP7NV9gX9BNVjur63FPxjggp13Qom5QeFvicnUjwfUAMNdMsQMxyQeNEB0wRkLAT9qbQC66rwg4XebYWGtvL1iawA/640?wx_fmt=png&from=appmsg)

上下文层不是一个独立的产品名，而是把语义定义、领域知识、血缘、治理策略、质量与认证信号打包成人和 AI 都能调用的统一接口。

本体和语义层是它的两块地基。厂商习惯把这两个概念打包成一个词卖，但它们解决的是两件不同的事。团队如果搞错了该先建哪一层，AI 项目就会长期卡在“能 demo、不能上线”的阶段。

## 1. 我们为什么开始盯住上下文层

OceanBase DataPilot 发布以来，我们观察到一个反复出现的现象：同一个数字，不同部门算出的结果不一样。财务说收入 1020 万，市场说 1040 万，Slack 里的 AI 助手报 980 万——三个数字，零共识。过去这种“扯皮”发生在人和人之间，开会拉齐一下就过去了。但 AI Agent 不会打电话问同事“你们口径到底怎么定的”，它拿到一个叫 `rev_ttm_adj_v2` 的字段，遇到歧义要么胡编一个答案，要么随便挑最先看到的定义。

有研究指出，当领域知识被结构化地注入检索流程时，AI 幻觉率可以下降约 40%。但前提是——知识得真的被建模出来，而不是“大家默认都懂”。这就是我们开始把上下文层当成一等公民看待的原因：底层的数据存得再全、上层的 Agent 再聪明，中间这一层如果只有一堆表和 SQL，AI 就永远长不成能被业务信任的样子。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/FRE5OkhV0ozpM7VY1VXL47X1BgU7CH98fv7WVeb84iaHSMLTQgsnjmD6snSLNFA6BozJ5HH8xoSnaspVEJPpKwtW9RHsI78V3QlnX12zQEJQ/640?wx_fmt=png&from=appmsg)  

> *同一份收入，三个数字，零共识——AI 时代无法回避的老问题*

## 2. 本体和语义的分工

一句话概括两者的分工：**语义层告诉你“收入是多少”，本体告诉你“客户是谁”。**

语义层管 **度量**——Revenue、MAU、LTV 这些指标怎么算、从哪张表 join、加哪些过滤条件，要求全团队、全工具口径一致；本体管 **含义** ——Customer 是什么、和 Order 什么关系、Platinum 客户满足哪些规则，机器能不能据此推理出新结论。

两件事都要做。把它们当成一回事，是大多数团队踩坑的起点。

![](https://mmbiz.qpic.cn/mmbiz_png/FRE5OkhV0oxcTZohWsST3oJ5nK6nibUpl1vULAf6kbdIicPpOrITp5ib4h9cSMoD5SjSmRYJzPHefNLehoMY49eQvcE0R6dzzc8BPkuib5huticw/640?wx_fmt=png&from=appmsg)  

> *语义层管“收入是多少”，本体管“客户是谁”*

本体在学术上有一个经典定义：对概念化内容的显式规范说明。拆开看就三件事：
- 类（Classes）——领域里有哪几类东西，如客户、产品、订单、区域；
- 属性与关系（Properties）——它们怎么连，比如客户“下单”、产品“属于”某个品类；
- 公理与规则（Axioms）——逻辑约束，比如每个订单至少有一个产品，一个客户在同一时刻只能归属一个区域。

用 W3C 的 RDF、OWL 等标准写成之后，**机器不仅能读，还能推理**。举个例子：如果本体里写着“Platinum 客户 = 年收入超过 100 万”，同时有事实“Acme 公司年收入 = 200 万”，本体引擎可以自动推断出 Acme 是 Platinum 客户，不需要有人手写 if-else。这是语义层和 BI 工具做不到的：它们执行你预先写好的计算，不会从已有事实里“长”出新事实。

本体的另一个价值在 **跨系统语义统一**。当 CRM 叫 Customer、ERP 叫 Client、财务叫 Account 的时候，本体让这三个名字指向同一个业务对象。

Agent grounded 在本体上，可以把采购历史、监管要求、产品层级自动串起来——它拿到的不是一堆孤立的表，而是一张能走的图。医疗行业的 SNOMED CT、金融行业的 FIBO 是典型例子，在这些强合规领域，形式化本体几乎是刚需。

代价也很明显：Palantir 把本体做到了企业级标杆，但模式很重——派驻工程师深入业务、手工建模、持续维护。全面本体项目常见周期 6-18 个月，还需要形式化逻辑的专业能力，开源工具 Protege 多年缺乏活跃维护，不少从业者干脆手写 Turtle 格式。本体很强，但也贵、也慢。

语义层的思路和历史都更“工程一点”。20 世纪 90 年代 Business Objects 的“Universe”就在干类似的事——把复杂 schema 抽象成业务语言。核心痛点一直没变：不同团队、不同工具各自算“收入”，算出来的数不一样，信任就崩了。AI 时代，这个问题被放大了十倍，因为口径不一致的成本从“开会解释”变成了“AI 幻觉写进决策报告”。

现代语义层通常由四块组成：元数据仓库把 `mrr_calc_v3` 映射成“月经常性收入”；业务逻辑引擎让指标公式集中定义、定义一次处处复用；查询翻译把“按区域看收入”自动 join 哪几张表、加哪些 filter；访问控制把行级、列级权限在语义层统一 enforcement。

2025-2026 年语义层有几个明显的变化。dbt Semantic Layer + MetricFlow 把指标做成了 YAML 版本化管理，编译成各方言 SQL，2025 年 MetricFlow 已 Apache-2.0 开源，“定义一次、到处渲染”从口号变成基础设施。

2025 年 9 月，Snowflake、Salesforce、dbt Labs、BlackRock 等发起 OSI（Open Semantic Interchange），2026 年 1 月 v1.0 发布，目标是厂商中立的语义元数据交换标准——指标不再锁死在某个 BI 或云厂商里，AI Agent 才能跨栈读取治理好的定义。生态里还有 LookML、DAX、Cube、AtScale、Snowflake Semantic Views、Databricks Metric Views 等，方向一致：**语义层正在成为 AI-ready 数据栈的标配**。

但语义层也有天花板。它能精确告诉你 Revenue 怎么算，但回答不了“客户和市场、监管框架是什么关系”“某个账户该不该按领域规则标为高风险”。

语义层的元数据偏结构，逻辑留在 SQL 和计算引擎里，不在概念网络里。用 Metadata Weekly 里 Jessica Talisman 的说法：语义层用于查找（lookup），本体用于语境与推理（context & reasoning）。

![](https://mmbiz.qpic.cn/mmbiz_png/FRE5OkhV0oyo58LrlgvDcUOq90VrlukwhZqcNJ6nVSrXv0Z5q0wh8f5cnvnNrAqukzNKMiaxpFiaLDQWulDAs3ibibfo12k0L6guj1kxM3Eibicek/640?wx_fmt=png&from=appmsg)

## 3. 只建其中一层，AI会怎么半瘫

只建语义层的 AI 通常表现是“算得准但很浅”——像只会按公式的计算器。你问它“上个月哪个渠道 GMV 最高”，它能给出精确到小数点的数字；但你追问“这个渠道为什么会跌”“要不要调高投放”，它就走不动了，因为它不知道“渠道”和“投放策略”“客户画像”之间的关系。

只建本体的 AI 则相反，“懂概念但数对不上”——像懂业务却不会做账的顾问。你问它“Acme 是不是 Platinum 客户”“这个客户和监管框架什么关系”，它能推理得头头是道；但你问它“Acme 上个月的收入是多少”，它可能给出三个不同数字，因为它不知道从哪张事实表算、按什么口径聚合。

行业信号已经很明确。Gartner 预测到 2027 年底，超过 40% 的 Agentic AI 项目会因成本、价值不清晰或风控不足被取消；一项对 248 位数据管理负责人的调查显示，63% 的组织缺乏（或不确定是否具备）支撑 AI 的数据管理实践。

很多项目不是模型选错了，是数据缺少语义 grounding。反过来看，Gartner 2026 峰会预测到 2030 年，通用语义层将与数据平台、网络安全同级，成为关键基础设施；Futurum 预测语义层增速将从 2026 年的 16% 升至 2031 年的 30%，成为 Data Intelligence 栈里增长最快的 segment。Microsoft Fabric IQ 预览原生本体支持，Timbr.ai 等厂商在做“带推理的语义层”——两条路正在朝同一个目标汇合。

## 4. 知识图谱和分类法在这套图里的位置

围绕本体和语义层，还有两个经常被混用的概念：知识图谱（Knowledge Graph）和分类法（Taxonomy）。

**知识图谱** 存的是实例。每一个真实客户、每一张真实订单，是图上的节点。本体是 schema，知识图谱是 data。Agent 要在运行时“沿关系走”，靠的通常是图谱。本体和知识图谱经常一起出现，但不是同一件事——可以只有其一，也可以组合使用。

**分类法** 是精简版本体，只有父子层级，没有推理、没有横向关系。产品类目、数据域划分、PII 标签，这些治理工作往往从分类法开始。一旦 Agent 需要跨类目推理（比如“品类 A 的降级会不会影响品类 B 的库存策略”），就要往本体方向升级。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/FRE5OkhV0owrWuD1m7W71quQkpTDd3esQRbHI8dlyAtPrPcSsrichbbNYNcUwhfOia0sniaTffTS87J5TrUft0n5yUOW3ma8aicEaSCteCiaWTyk/640?wx_fmt=png&from=appmsg)

## 5. 上下文层：把碎片打包成一个统一接口

单独谈本体或语义层都容易只见树木。行业里近两年逐渐形成一个上层概念：**上下文层（Context Layer）**——把语义定义、领域知识、血缘、治理策略、质量与认证信号，打包成人和 AI 都能调用的统一接口。OceanBase AI 数据库把上下文层做成了架构里的一等公民，正是同一个判断的产物。

我们把上下文层进一步拆成两块：
- **数据上下文** 围绕数据语义和数据治理展开，回答“AI 面对的是什么样的企业”——它包含本体、语义层、知识图谱、血缘、质量分和访问策略。
- **应用上下文** 围绕 Memory 和 RAG 展开，回答“AI 面对的是什么样的用户”——它包含用户偏好、历史对话、领域文档和检索得到的具体事实。

两块解决的是不同的问题：数据上下文让 AI 理解企业，应用上下文让 AI 理解用户。本文讨论的本体和语义层都属于数据上下文。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/FRE5OkhV0oxUJJOS8FrhPXbMNjkicCeY9vO90cVr3csCeYaibGRqUWEl5NxyNqQL7uYEJ3jwtzCALlJ4HHYu5beZI6bF4JQicEVM3LaicuQIIc8/640?wx_fmt=png&from=appmsg)  

> *上下文层把本体、语义层、知识图谱、血缘和治理策略打包成 AI 可调用的接口*

上下文层的工作方式可以拆成四步：

本体定义“收入确认”这个概念及其规则属性；语义层把它翻译成计算逻辑——join 哪些表、怎么聚合；知识图谱把概念、指标定义、血缘、下游消费者串成一张网；MCP 等协议在推理时把上述语境一次性喂给 Agent。

2025-2026 年兴起的 **Context Engineering**，核心主张就是：AI 要可靠输出，必须先有结构化语境。本体和语义层，就是这块地基里最硬的两块砖。MCP 协议解决的是“怎么把上下文送到 Agent 面前”，但如果送过去的是一堆没治理过的表和 SQL，协议本身救不了幻觉。

## 6. OceanBase OSI：让数据上下文一次定义、多出复用

上下文层作为架构概念是清楚的，落到产品层面就要解决一个具体问题：企业里的指标口径、业务对象、数据关系已经散落在 dbt YAML、BI 语义模型、数据字典、SOP 文档和一堆临时 SQL 里。

如果做 AI 数据库的团队再造一套自己的 BI 语义，等于让企业再多维护一份分裂的定义。OceanBase 的选择是不再造轮子，而是把 **指标、口径、原始数据、上下文图谱、本体层统一起来**，一起放进一个开放的语义栈里。这套栈我们叫做 OceanBase OSI（Open Semantic Interchange）。

OSI 内部分三层，正好覆盖本文讨论的两大主题——语义层和本体：
- 最底层是语义层：指标定义、口径规则、维度和原始数据映射。这一层基于 Ant-OSI 语义层标准设计，兼容业界的 OSI 开放标准，已经在蚂蚁集团得到大量实践验证。
- 中间是上下文图谱：把指标、对象、事件、血缘、下游消费者串成一张关系网。大模型基于这张图谱做推理，比只看表结构或只看指标 YAML 都要准。
- 最上层是本体层：统一业务语义和底层数据库语义，做到全局语义与局部语义的平衡——空间里的自定义术语和企业级的核心业务概念能挂得起来，也能各自演进。

OSI 的核心理念概括为一句话：**语义即代码**（Semantic as Code）。数据语义一次定义，BI 渲染报表、Agent 生成 SQL、治理工具做血缘分析，读的是同一份定义。企业不再需要在 BI、AI、治理三处各维护一套语义，也不再担心 Agent 和 BI 报表口径打架。

我们基于 OceanBase OSI 开发了 OceanBase DataPilot。在不同行业的客户 POC 测试中，DataPilot 的自然语言问数准确率明显好于业界其他产品。这背后不是模型的差异——大家用的都是市面上主流的 LLM——而是语义上下文的质量差异。当 AI 拿到的是准确的业务口径定义而不是一堆裸表，从自然语言到 SQL 的翻译准确率会本质性地提升。

## 7. 团队路径：先建哪一层

没有标准答案，但有常见路径。

![](https://mmbiz.qpic.cn/mmbiz_png/FRE5OkhV0oxH9rYEtlViaDic9eEfIqSxQO8VXVNWZxiapYw1ImRrrIiaMjsjbYnt38TeahH0jCdiaXrkrP7T2KIq6ADEAF10o4npfgWVHXqJQ6W0/640?wx_fmt=png&from=appmsg)  
*本体与语义层的常见建设路径*

如果团队面对的是各部门对“收入”“活跃用户”口径不一致、要上“对话式问数 / Chat with Data”、数据栈相对集中（一个主仓 + 少量 BI），并且希望 2-6 个月看到 ROI——**优先做语义层**。

如果团队面对的是金融、医疗、政务等强合规场景、AI 用例需要跨客户/产品/监管多域推理、几十个异构系统里同一概念有 N 种叫法、还需要自动分类和基于规则的异常检测——**优先做本体**。

大多数企业的务实路线是：先做语义层，把核心指标集中治理，让 BI 和 AI 读同一套定义；用业务词汇表起步做轻量本体，不必一上来就上 OWL 工程；补上治理信号——血缘、质量分、Owner、认证——让定义可审计；再通过 MCP 等协议暴露给 Agent，让上下文层从概念变成基础设施。dbt 替代不了本体，Palantir 式本体也不适合所有团队。从词汇表演化到形式本体，比一步到位现实得多。

## 8. 我们下一步做什么

上下文层是 OceanBase AI 数据库架构里的中间层，OceanBase OSI 是我们给这一层的产品化答案，也是 DataPilot 长期押注的地基。

往下走，我们有几件事要做。

**短期** 要把 OSI 语义层能力铺到 DataPilot 的每一个空间。指标定义以 Ant-OSI 标准的形式集中管理，让第一批业务用户在自由对话里不再自己发明口径；同时把术语、指标、维度的可视化和搜索做出来，让空间里“有哪些资产、还缺什么”看得见、摸得着。

**中期** 要把 OSI 的本体层做扎实。业务词汇表、类目层级、实体关系先从产品化的分类法起步，逐步补上跨系统语义对齐和基础推理。这一块我们不打算走 Palantir 全面本体那条路，而是让本体从子域使用中长出来。

**更长期的问题** 是：不同子域各自沉淀出来的语义资产（术语、指标、对象关系），如何治理冲突和合并？这也是 OSI 上下文图谱要解答的核心问题——把子域和全局的语义关系维护成一张能演进的网。

欢迎带着你自己业务场景的样例找我们聊——真实场景是这条路走得通的唯一验证方式。

> 原文：[本体和语义层，到底差在哪？AI 问数对不上，问题多半出在这](https://mp.weixin.qq.com/s/lhSxisseQkjj_1QqV4FAew)
