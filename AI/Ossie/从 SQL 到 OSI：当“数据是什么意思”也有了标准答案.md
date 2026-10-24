上一篇文章里，我从一个 OpenClaw Skill 聊起，讲了一个判断：个人认知正在被 `.md` 编译，企业认知需要语义层来编译，而 OSI 标准的发布意味着这件事正在从愿景变成现实。

不少朋友读完后问我：OSI 到底是什么？跟 SQL 是什么关系？全球那些数据巨头为什么突然要联手搞一个标准？这对中国企业意味着什么？这篇文章就来展开聊聊这些问题。

## 1. 先讲一段老故事：SQL 是怎么统一世界的

1970 年代，IBM 的研究员基于关系代数提出了 SEQUEL（后来改名 SQL）。那个年代，每家数据库厂商——DB2、Informix、Sybase——都有自己的私有查询语言。你在 A 系统上写的查询逻辑，换到 B 系统上就得重写一遍。开发者被锁死在特定厂商的生态里，迁移成本极高。

1986 年，SQL 成为 ANSI 标准，次年被 ISO 采纳。标准化之后发生了什么？应用可以跨数据库迁移了，整个 BI、ERP、数据工具的生态在接下来三十年里蓬勃生长——这个生态的底座，就是 SQL 这一层“大家都认”的查询协议。

回头看，SQL 标准化给我们三个启示：
- 第一，标准解决的是协作成本问题，不是纯技术问题。SQL 不是当时技术上最优的查询语言，但它足够好，且大家愿意一起用。
- 第二，标准必须由行业共同推动，不能是一家厂商的私有方案。如果 SQL 只属于 IBM，它不可能成为标准。
- 第三，标准成功依赖实用性，不依赖理论完美性。SQL 到今天还有一堆被人吐槽的设计缺陷，但这不妨碍它统治了四十年。

这段历史之所以重要，是因为我们正在看到一个高度相似的剧本重演。

## 2. OSI：让“数据是什么意思”标准化

SQL 解决了“怎么取数”的标准化问题。但四十年后，一个 SQL 没有回答的问题变得越来越紧迫：同一个指标名称，在不同系统里到底是什么意思？“月度收入”在财务系统里要剔除退款和异常订单，在市场系统里包含所有支付成功的订单，在供应链系统里只算已发货部分。同一个词，三套计算逻辑。人类员工处理这种差异靠三种方式：开会对齐、当面确认、老带新口口相传。原始但管用。但 Agent 不会开会。Agent 不会打电话问“你说的 GMV 包含退款吗”。Agent 拿到一个指标名称，就会按自己理解的逻辑去算——如果三个 Agent 各算各的，协同就失效了。

AI Agent 的规模化落地，把“语义一致性”从一个“有了更好”的优化项，变成了“没有不行”的前提条件。这就是 OSI 要解决的问题。

2026 年 1 月 27 日，Open Semantic Interchange（OSI）首个公开版本规范在 GitHub 正式发布（仓库地址：github.com/open-semantic-interchange/OSI，采用 Apache 2.0 开源许可）。这不是一个概念或倡议——是一份可落地的技术标准，用声明式 YAML 格式定义指标、维度、关系和上下文（context）的统一描述规范，让不同系统可以互相理解对方的语义。简单说，它给“数据是什么意思”提供了一种跨平台、跨工具的通用语言。

更具体地讲：过去你在 dbt 里定义了“净收入”的计算逻辑，想在 Tableau 或 Power BI 里用，得重新定义一遍。OSI 要解决的就是这个问题——定义一次，导出成 OSI 格式，所有兼容的工具都能直接理解和执行。

参与方的阵容本身就是最好的背书：Snowflake、Databricks、Salesforce、dbt Labs、AtScale、Qlik、JetBrains、Collibra、DataHub、Lightdash、Coalesce、Sigma……几十家全球数据技术公司，覆盖了云平台、BI 工具、数据工程、数据治理的完整生态（完整名单见 OSI 官网 open-semantic-interchange.org）。

其中 Snowflake 和 Databricks 两家最引人注目。当两个打得不可开交的对手愿意坐下来联合定标准的时候，说明市场需求已经大到不能再各自为政了。Salesforce 也在官方博客中明确表态：“The agentic future demands an open semantic layer”——Agentic AI 的未来要求一个开放的语义层。

## 3. 全球数据厂商：殊途同归的语义层布局

OSI 的发布不是凭空出现的。过去两年，整个数据技术栈都在向语义层聚拢，只是路径不同。

BI 平台在重构语义内核。Salesforce 旗下的 Tableau 推出 Tableau Next，内置 Tableau Semantics 模块——官方定义为“AI-infused semantic layer”，明确为 AI Agent 提供统一的业务术语，并推出了 Data Pro、Concierge、Inspector 三个内置 AI Agent（见 tableau.com/products/tableau-next）。Google 旗下的 Looker 长期以语义模型 LookML 为核心能力，2025 年进一步推出 Looker MCP Server，让 Gemini CLI、Claude 等外部 AI 平台可以直接查询 Looker 的语义层（见 Google Cloud Blog Opening up the Looker semantic layer）。Microsoft 则在 Power BI 中将“数据集（Dataset）”正式更名为“语义模型（Semantic Model）”，强调它是业务知识的载体而非单纯的数据容器（见 Power BI Blog Datasets renamed to semantic models）。

云平台在向上延伸语义能力。Snowflake 2025 年 4 月推出 Native Semantic Views（语义视图），把语义定义变成数据平台的原生功能，2026 年 2 月进一步发布 Semantic View Autopilot，用 AI 自动从查询历史和 BI 资产中生成语义视图（见 Snowflake Engineering Blog Native Semantic Views: AI-Powered BI）。Databricks 在 Unity Catalog 中推出 Metric Views，用 YAML 格式定义指标并注册到统一目录中，实现“一次定义，处处可信”——在 Dashboard、Genie、Notebook、SQL 中均可直接调用（见 Databricks Blog What's new with Unity Catalog）。

现代数据栈在推动语义中立。dbt Labs 2025 年 10 月宣布将 MetricFlow 完全开源（Apache 2.0），作为对 OSI 标准的直接承诺，推动指标定义的标准化和可移植——MetricFlow 的 YAML 格式也是 OSI 规范的底层标准之一（见 dbt Labs Blog dbt Labs Affirms Commitment to OSI by Open Sourcing MetricFlow）。Cube.dev 被 GigaOm 2025 年语义层雷达报告评为“Leader and Outperformer”，定位“Agentic Analytics Platform”，提供 REST、GraphQL、SQL、MDX、DAX 等多种 API 供各类系统调用（见 Cube Blog Named Leader in 2025 GigaOm Radar）。

这些动作方向一致：语义层正在从应用层的附属功能，下沉为基础设施层的核心能力。而 OSI 做的事，是在这些厂商各自的语义层之间建立一种“互译协议”——你在 Snowflake 上定义的“净收入”，导出成 OSI 格式后，dbt、Tableau、Power BI 都能直接理解和使用，不需要重新定义一遍。根据 OSI 路线图，Phase 2 的原生平台支持计划在 2026 年 Q2-Q4 推进，目标覆盖 50+ 平台。

## 4. 对中国企业意味着什么

看到这里，可能有人会问：这是硅谷的事，跟中国企业有什么关系？关系很大。
- 第一，Agent 的落地速度在中国可能更快。中国企业对新技术的采纳速度一直领先全球——从移动支付到短视频到直播电商，莫不如此。AI Agent 也一样。当 Agent 在企业内部大规模部署的时候，语义一致性的问题会比硅谷更早、更猛烈地爆发出来。
- 第二，中国企业的数据治理现状更需要语义层。很多大型企业经历了十年的信息化和数据中台建设，积累了大量数据资产，但指标定义散落在众多系统里，口径差异是常态。这些“技术债”在传统 BI 时代还能靠人力弥补，到了 Agent 时代就成了硬伤。
- 第三，OSI 作为开放标准，为中国厂商提供了参与全球生态的机会。它不是某一家公司的私有格式，而是一个开放协议（Apache 2.0 许可）。中国的数据语义层产品完全可以兼容 OSI 标准，进入全球技术生态的互操作网络。

## 5. OSI 之后，真正的挑战才开始

最后我想说一个 OSI 没有解决的问题——这也是我认为下一阶段最关键的问题。OSI v1.0 解决的是“定义”层面的标准化：用什么格式描述一个指标、一个维度、一个关系。这很重要，是基础。但企业真正要用起来，光有定义不够。你还需要：
- 动态组装能力。业务需求千变万化，Agent 可能需要实时组合“过去 24 小时一线城市 35 岁以上女性用户对促销活动的响应率”——这种指标不可能预先定义好，需要从原子指标和维度动态组装。
- 执行可验证。从自然语言到语义查询到 SQL 到结果，每一步都应该可追溯、可审计。业务负责人不需要懂 SQL，但他需要能点开看到“这个数是怎么算出来的”。
- 性能与精度的平衡。百亿级数据下的亚秒级响应，同时计算逻辑 100% 准确——这两个要求经常矛盾，需要智能的物化加速和查询路由来协调。

这些，正是“定义”之上的“执行”层需要解决的问题。上一篇文章里我把它概括为一句话：定义是协议的前半段，执行是协议的后半段。OSI 做了前半段，Aloudata 的 Semantic Fabric（语义编织）则把前后两段都做了。

传统的“数仓 + BI”两层架构，正在被“数据湖 + 语义层 + 消费层”三层架构替代。语义层成为连接原始数据与业务价值的核心枢纽——它对下屏蔽数据源的复杂性，对上为 Agent、BI、应用提供统一的语义接口。

## 6. 站在标准化的起点上

标准协议的价值，往往在普及之后才被充分认知。回想 1986 年 SQL 成为标准的时候，大多数人没有意识到这会催生接下来三十年的整个数据库和 BI 生态。今天 OSI v1.0 刚刚发布一个月，它能走多远、多快，还有很多不确定性。但有几件事是确定的：
- AI Agent 对语义一致性的依赖，远远高于传统应用对查询语言的依赖——这意味着标准化的驱动力比 SQL 时代更强。
- 现代数据生态的开放程度，远高于四十年前的封闭竞争时代——这意味着标准推进的阻力更小。
- Git、API、Schema Registry 等工程基础设施已经成熟——这意味着标准落地的工具链已经就绪。
- 当企业开始将“指标定义”视为与“财务制度”同等重要的治理资产，当语义描述变成一种可交换、可审计、可版本管理的协议——我们就真正站在了智能决策的新起点上。
- 从 SQL 到 OSI，间隔了四十年。SQL 让机器听懂了人类的查询指令，OSI 要让机器理解人类的业务语言。

这一步，比上一步更难，也更值得。

> 原文：[从 SQL 到 OSI：当“数据是什么意思”也有了标准答案](https://mp.weixin.qq.com/s/qP64-1ygOvVRgaIlt86wEQ)
