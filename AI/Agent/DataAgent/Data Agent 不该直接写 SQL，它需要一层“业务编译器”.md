过去几年，自然语言查询数据库的技术路线看起来非常直接：用户提出一个问题，大模型读取数据库 Schema、生成 SQL，数据库执行查询，再把结果返回给用户。随着模型代码能力提高，这条链路迅速成为 Data Agent 最常见的产品形态。

但当 Data Agent 从演示环境进入企业生产系统后，问题很快发生了变化。企业并不只需要一段“可以运行”的 SQL，而是需要一段在业务含义、指标口径、表关系、访问权限和执行成本上都正确的 SQL。语法错误通常会被数据库直接拦截，业务语义错误却可能返回一份看似合理、实际上无法用于决策的结果。

大模型看到的是 customer_id、order_table、revenue_amount 和 risk_score，业务人员看到的却是客户生命周期、合同状态、历史交易、流失风险和下一步经营动作。两者之间缺少的不是更长的提示词，而是一套稳定、统一、可复用、可以被机器执行的 **业务语义**。

Semantic Layer 因此开始承担新的角色：它不再只是 BI 系统中统一指标口径的一层模型，而正在成为 Data Agent 理解企业数据、生成业务查询并调用底层执行引擎的中间语言。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/1IxFwEbkQDq8wMAGD0mRnFIrnuC7Lmo11P8DJScrPVVmmib7OaZeexnHcibeY3SWofNBlFZXG1FGHwfgsTU6RKrsm7DZ8F95zQicM2ZQCOnFjE/640?wx_fmt=png&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=1)

> 图 1｜传统 NL2SQL 与 Semantic Layer 中介架构的职责差异

## 1. NL2SQL 的瓶颈，不只是模型不会写 SQL

在结构简单、表数量有限的测试环境中，大模型可以直接读取 Schema，根据用户问题生成 SQL。但真实企业数据仓库通常包含数百张表、上千个字段、多种 SQL 方言，以及散落在文档、报表和分析师经验中的业务规则。Spider 2.0 就是为这种企业级 Text-to-SQL 工作流设计的评测框架，其数据库经常包含超过 1000 个字段，任务还可能要求理解元数据、方言文档和项目代码。基于 o1-preview 的代码 Agent 在 Spider 2.0 上只完成了 17.0% 的任务，而在传统 Spider 1.0 上达到 91.2%。

这组差异说明，企业 NL2SQL 并不是学术基准的简单放大版。模型不仅要生成代码，还要在庞大的物理结构中完成业务概念落地、数据关系发现和执行路径选择。
- 业务词汇无法与物理字段直接对应
  - 用户询问“今年高价值客户的流失风险”，数据库中通常没有一列直接叫作“高价值客户”。这一概念可能来自过去 12 个月消费金额、购买频率、利润贡献、客户等级和合同状态的组合。模型即使找到了客户表，也未必知道企业内部对“高价值”使用的是哪一套正式定义。
- 同一个指标可能存在多个合法口径
  - “收入”可以表示下单金额、确认收入、回款金额、含税收入，也可以表示扣除退款和折扣后的净收入。不同部门使用的时间字段、订单状态和汇率规则也可能不同。模型生成的 SQL 在语法上完全正确，结果却可能与财务或经营口径不一致。
- JOIN 不是字段匹配，而是业务关系
  - 客户、订单、合同、商品、库存和渠道之间并不总是通过清晰主外键连接。某些关系需要经过映射表，某些连接键需要清洗，某些事实表只能在特定时间范围内关联。直接让模型从字段名称猜测 JOIN 路径，很容易生成能够执行但重复计数、漏数或扩大数据范围的查询。
- 权限与治理无法只靠 Prompt
  - 企业查询还受到行级权限、列级权限、敏感数据分级、数据域边界和计算资源限制约束。随着 Schema 扩大，把全部规则塞进上下文不仅成本高，也很难保证每一次生成都严格遵守。权限必须成为查询规划与编译过程中的正式约束，而不是模型“应该记得”的提示。

![](https://mmbiz.qpic.cn/mmbiz_png/1IxFwEbkQDoN8Piagwic8C2VYVANeIsmdda92ib7ib9Mibsa1W2ngj1oqVbfNXibEYMaUOUwMpFhRLh0HB3fmluakyQoLpN0ibIyVSs1xnZ5fsrUZY/640?wx_fmt=png&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=4)

> 图 2｜用户使用业务语言提问，数据库却使用物理结构存储数据

## 2. 为什么 Semantic Layer 正在成为“业务编译器”

2026 年 6 月发布的一项研究提出了 Semantic Layer 中介的企业 NL2SQL Agent。系统没有让大模型直接读取原始 Schema 并生成最终 SQL，而是先让模型基于经过整理的语义层生成一种中间表示——Semantic Model Query（SMQ），再由确定性引擎将 SMQ 编译为 SQLite、BigQuery 或 Snowflake 方言的 SQL。

这套架构最重要的地方，不是多加了一个组件，而是重新划分了大模型与确定性软件的职责。

### 2.1 模型负责理解和表达意图

- 识别用户要分析的业务对象、指标、维度、时间范围与筛选条件；
- 把自然语言转换为结构化的业务查询；
- 在复杂任务中规划子问题，并组合编译器返回的可靠构件。

### 2.2 Compiler 负责把意图落到物理数据

- 把业务指标映射到正式计算表达式；
- 根据已声明的关系图选择物理表与 JOIN 路径；
- 注入过滤、时间、去重和权限规则；
- 生成目标数据库方言的 SQL，并提供查询预览或验证结果。

![](https://mmbiz.qpic.cn/mmbiz_png/1IxFwEbkQDpfw1edP9vs31sa70ibHa3n26VuEict91q4liciaw7vxzC8bgCESUIYQ6w5AxsxBxV72a0JicOOborreIRCTOASVW6qNSpOZYNFbvRk/640?wx_fmt=png&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=7)

> 图 3｜SMQ 只表达“查什么”，Compiler 决定“如何在物理数据库中执行”

这种设计与程序编译器的逻辑相似。开发者使用高级语言表达程序意图，再由编译器转换成机器可执行指令；Data Agent 则使用业务中间表示描述查询意图，再由 Semantic Layer 和编译器转换成数据库可执行 SQL。

论文中的语义模型把物理表包装为带有业务名称的模型，并暴露维度、度量和指标。每一个元素同时包含给模型阅读的人类可读描述，以及用于编译的精确物理表达式。抽象名称与物理字段被分离之后，模型可以围绕业务含义推理，编译器则负责处理真实表名、列名和方言。

论文还把跨模型 JOIN 维护为独立关系图。连接路径、连接键和必要的清洗表达式只声明一次，编译器便可以在后续查询中重复使用，避免模型每次重新发现 JOIN。

### 2.3 为什么中间表示比直接 SQL 更容易治理

自由 SQL 的搜索空间几乎不受约束。模型需要一次完成表选择、列选择、JOIN、聚合、过滤、排序、窗口函数和方言适配，任何一个错误都可能使结果失效。SMQ 这类中间表示则把查询约束在指标、筛选条件和分组维度等有限结构内，使系统能够在执行前完成结构校验、权限检查和规则展开。

中间表示还提供了可观测性。系统可以记录模型选择了哪个指标、使用了哪些筛选条件、编译器展开了哪些表关系，以及最终 SQL 如何形成。当结果异常时，团队能够区分问题来自用户意图解析、语义定义、编译规则，还是复杂 SQL 的组合过程。

## 3. 94.15% 的结果说明了什么，又不能说明什么

上述研究使用 Gemini 3 Pro，在 547 项 Spider2-snow 任务上完成 515 项，报告 94.15% 的执行准确率，在当时官方榜单中位列第三。这一结果明显高于直接围绕原始 Schema 工作的多种公开方案，但不能简单写成“Gemini 3 Pro 的 NL2SQL 准确率达到 94.15%”。

结果来自一个完整系统：强推理模型、逐数据库整理的语义层、SMQ 中间表示、确定性编译器、受约束的 Agent 循环和多后端执行框架。论文也明确指出，语义层包含零样本基线无法获得的领域知识，因此对比反映的是整套系统的价值，而不是模型的独立能力。

![](https://mmbiz.qpic.cn/mmbiz_png/1IxFwEbkQDpoZwgNgnFBmwH2fibgXOiazvqFA3Hw0soPMMaRLL0J6Zbs9Dib6ribMQ4SLibIiaOmOA4mvsccnPaWXlcRjsPQnFp0eCqBEmicpHOnqg/640?wx_fmt=png&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=10)

> 图 4｜研究报告的分来源执行准确率；原生 Snowflake 类样本仅 18 项

结果背后的三点启示：
- 第一，企业 NL2SQL 的性能杠杆可能不只在模型，而在语义层质量。论文将语义层描述为主要维护面：补充缺失字段、改进元素描述、声明 JOIN 关系，能够直接改善对应数据库上的准确率。
- 第二，确定性编译并不意味着所有 SQL 都能被模板化。论文中的 SMQ 只覆盖选择、过滤、分组和已声明 JOIN 等常见分析核心，窗口函数、递归 CTE 和复杂子查询仍可能由 Agent 基于编译器构件进一步组合。业务编译器的目标不是消灭模型推理，而是把最容易出错、最应该稳定的部分从自由生成中剥离出来。
- 第三，语义层同样存在过拟合风险。如果团队为了提高某一评测集的准确率，把问题特定线索不断写进字段描述，语义层可能从通用业务知识退化为隐藏答案。论文因此提出，应把语义层当作代码管理：描述用于表达可复用知识，结构信息进入类型化字段，并接受评审和回归测试。

## 4. 从 BI 语义层到 Agent 语义层

Semantic Layer 并不是一个新概念。传统 BI 架构已经长期使用语义层统一指标、维度、数据关系和过滤规则，使不同报表围绕同一份业务定义计算结果。但 BI 语义层主要回答的是“这个指标怎么算”。当使用者从 BI 工具变成能够规划、调用工具和执行任务的 Agent 后，语义层需要回答的问题明显扩大：这是什么业务对象、对象之间是什么关系、当前处于什么状态、哪些规则必须遵守、当前用户能访问什么，以及分析完成后可以执行什么动作。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/1IxFwEbkQDq7Jfx55ryWR1sicVzczAwyk46z5lAYfoEmeGuiapz8uHJpVvqL0OSdSIcRHX13VVGEerZfDSicJmBwfJyiaShFqZz0hIC1TT85J08/640?wx_fmt=png&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=13)

> 图 5｜Agent 需要的语义资产，从指标计算扩展到实体、规则、权限与行动

Agent 语义层需要增加的五类能力：
- Entity：把分散在多张表中的数据抽象为客户、订单、合同、设备、供应商和库存等稳定业务对象。
- Relationship：明确客户拥有哪些订单、订单对应哪些商品、商品由哪些供应商提供，而不是让模型临时猜测字段连接。
- Rule：把高价值客户、库存异常、合同逾期、有效订单等判断条件编码为可复用规则。
- Permission：定义用户和 Agent 可以读取哪些实体、字段与记录，以及可以执行哪些类型的操作。
- Action：把创建工单、调整状态、触发审批、通知负责人等操作定义为受控接口，并配套审计、审批与回滚机制。

因此，面向 Agent 的 Semantic Layer 正在与 Ontology 靠近。前者通常从指标、维度和查询逻辑出发，后者从业务对象、关系、状态与动作出发。两者结合后，企业才能形成一个既能回答问题，又能够在治理边界内推动业务流程的 AI 基础层。

## 5. Palantir、Databricks、Microsoft 与 Snowflake 正在走向哪里

主流数据平台和企业 AI 厂商的产品起点不同，但它们正在共同解决同一个问题：如何在物理数据与 AI Agent 之间建立一个受治理的业务语义接口。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/1IxFwEbkQDq9gwVOM8LKS54jsqY6EeUOzXsmxU9aWMaFbibY2Gibia2k9ENH4LOjzH3yQHhW3EugIpApjw2vUDDUxQudxQwSJg2hDcaGoUH1JI/640?wx_fmt=png&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=16)

> 图 6｜四条路线的起点不同，但共同方向都是为 Agent 提供业务上下文与治理边界

- Palantir：从业务对象与 Action 出发
  - Palantir Ontology 将现有数据源映射为对象、属性和关系，并通过 Object Type、Link Type 和 Action Type 描述企业业务世界。Palantir 文档把 Action Type 定义为一组对对象、属性和链接进行修改的事务性操作，Action 还可以包含提交后触发的副作用。这使 Ontology 不只是查询语义层，也成为业务应用和行动执行的基础。
- Databricks：从湖仓治理与指标语义出发
  - Databricks 的 Unity Catalog business semantics 用于集中定义和管理业务指标与 KPI，并把 Metric View 作为核心实现。Metric View 将度量定义与用于分组、筛选和聚合的维度分离，使指标能够定义一次、在运行时被统一查询。Databricks 还增加了显示名称、格式与同义词等 Agent 元数据，帮助 Genie Agents 等自然语言工具更准确地解释数据。
- Microsoft：从 Semantic Model 走向跨域 Ontology
  - Microsoft Fabric IQ 的 Ontology 被定义为供团队、Agent 和工作流共同使用的受治理业务模型，包含实体类型、关系、属性、规则和约束，并可绑定 OneLake 中的真实数据。Microsoft 还支持从现有 Semantic Model 生成 Ontology，把已经沉淀在 BI 模型中的表、关系和业务定义进一步转化为 Agent 可使用的企业上下文。
- Snowflake：把语义概念直接存入数据库
  - Snowflake Semantic Views 是数据库 Schema 级对象，可以定义逻辑表、业务实体关系、事实、维度和指标。Cortex Analyst 读取 Semantic View 中的业务定义，并针对物理表生成 SQL。Snowflake 还通过 Verified Query Repository、评估和建议机制，把经过人工验证的问题与 SQL 用于提高结果准确性和可信度。

不是简单的“谁像谁”：Palantir 更强调业务对象和行动系统；Databricks 与 Snowflake 更靠近指标、查询和数据平台治理；Microsoft 正在连接 Power BI Semantic Model、Ontology 与 Data Agent。它们并不完全等价，但都在承认同一个事实：Agent 不能只面对裸表。

## 6. 下一代企业 Data Agent 的架构会发生什么变化

传统 Data Agent 原型通常可以简化为“数据源—LLM Agent—SQL—查询结果”。这套架构开发快，却把大量复杂性推给模型：Schema 变化、指标定义、权限规则和方言差异都需要通过上下文临时注入。

更稳定的企业架构会将职责拆成多个可治理层：数据湖仓负责存储与计算；Semantic Layer 负责指标、维度、逻辑关系和查询规则；Compiler 将业务查询转换为可验证 SQL；Ontology 描述业务实体、状态、权限和 Action；Agent Runtime 负责理解意图、规划任务、调用工具和组合结果；最终业务动作通过受控接口执行。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/1IxFwEbkQDo1jqfOf8DDFPP5mL6mXbudschUAuSOH8t0icOLMYyoBmop0RRTJtSRFkvxF6JTsBaVw9ql6c4C6NRLXLORuC8bkjBb63o5hx9o/640?wx_fmt=png&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=19)

> 图 7｜从数据源到业务行动的分层架构：每一层都有明确责任与治理边界

这套架构带来的四个变化：
- 第一，Agent 与物理数据结构解耦。只要业务语义接口保持稳定，底层表结构、字段名称和计算引擎发生变化时，Agent 不需要重新读取全部 Schema。
- 第二，查询过程从黑盒生成变成可审查编译。团队可以在执行前检查指标、筛选条件、JOIN 路径、权限和资源预算，并在问题出现后定位到具体层。
- 第三，业务知识从散落的 SQL 和文档变成可复用资产。指标、实体、关系和规则能够同时服务 BI、应用、Agent 和自动化流程。
- 第四，Data Agent 才可能安全地从问数走向行动。只有当实体、状态、权限和 Action 被正式定义之后，Agent 才能在明确边界内创建工单、触发审批或修改业务状态。

## 7. 企业应该如何建设这层“业务编译器”

Semantic Layer 不是把现有数据目录换一个名字，也不是一次性整理全部企业数据。更现实的路径是从业务价值高、数据边界清晰、评价标准明确的主题域开始，建立可以被真实问题反复验证的语义闭环。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/1IxFwEbkQDq3MbYjKy0WKbyMgVWnwRK48LFCjibpOSSe1GRBajxUvc5rqwc48EfpT69ibEicNYWKSLqugZVCbibxlQoejwzetV2ML7VdvT5vgs4/640?wx_fmt=png&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=22)

> 图 8｜从一个主题域开始，先建立可验证查询，再逐步开放业务行动

- 第一步：选择有边界的业务域
  - 不要从“让 Agent 回答企业所有数据问题”开始。可以选择销售经营、供应链库存、客户流失或设备运维等主题域，明确用户、数据源、核心问题和结果验收标准。
- 第二步：把语义资产当作正式产品
  - 为每一个指标、实体、关系和规则指定定义、负责人、版本和适用范围。语义层需要像代码一样经历评审、测试、发布和变更管理，而不是由个人在 Prompt 中临时维护。
- 第三步：设计受约束的业务查询语言
  - 中间表示不一定必须采用论文中的 SMQ 格式，但应具备相同原则：模型表达业务目标，不直接填写任意物理表名和字段名；查询结构能够被静态检查；指标、维度和实体引用来自受治理目录。
- 第四步：将确定性规则收回系统
  - 指标展开、JOIN 选择、时间口径、默认过滤、权限判断、SQL 方言和资源限制，都应该尽量由确定性组件实现。模型适合处理模糊意图和长尾组合，不应该重复猜测已经能够被规则化的知识。
- 第五步：建立真实问题验证集
  - 评估不能只看 SQL 是否执行成功。企业需要沉淀真实业务问题、标准结果、允许误差、权限角色、查询成本和失败类型，并在语义定义或编译器升级后持续回归。
- 第六步：按照风险等级开放 Action
  - 先从只读查询开始，再增加建议生成、人工确认、审批后执行和自动执行。每一种 Action 都需要明确前置条件、权限、审计日志、幂等性和回滚方案。Agent 能否行动，不应由模型自我判断，而应由业务规则和授权系统决定。

## 8. Semantic Layer 也不是万能答案

把语义层放到 Agent 与数据库之间，并不会自动解决企业数据质量、组织协作和知识维护问题。相反，它把原来隐藏在 SQL 和个人经验中的问题集中暴露出来：
- 首先，错误的语义定义会被大规模复用。如果“净收入”本身定义错误，确定性编译器只会更稳定地生成错误结果。因此，业务负责人、数据团队与治理团队需要共同承担语义资产的准确性。
- 其次，语义覆盖度与维护成本存在张力。覆盖太少，Agent 仍然频繁回到自由 SQL；覆盖太多，团队可能陷入庞大而难以持续更新的建模工程。语义层应优先覆盖高频、高价值和高风险问题。
- 再次，中间表示必须保留逃生通道。企业分析存在大量窗口函数、复杂时间逻辑和临时探索，完全封闭的 DSL 可能限制能力。更合理的方式是让编译器提供经过验证的基础构件，由 Agent 在严格规则下完成长尾组合。
- 最后，Semantic Layer 与 Ontology 的融合会带来新的治理问题。当系统从“定义指标”扩展到“定义可以执行的动作”，错误的影响将从回答不准确升级为业务状态被修改。查询治理与行动治理必须分层设计。

结语：Data Agent 的竞争，正在从模型能力转向语义系统能力
SQL 不会消失，它仍然是企业数据系统最重要的执行语言之一。变化在于，SQL 不应该继续承担业务语义的全部表达责任，大模型也不应该直接面对不断变化、缺少业务含义的物理 Schema。

未来更合理的分工是：用户使用自然语言表达业务问题；模型把问题转换为结构化业务意图；Semantic Layer 提供指标、维度、关系和规则；确定性编译器生成并验证 SQL；Ontology 补充实体、状态、权限和 Action；Agent 在治理边界内完成分析与执行。

因此，Semantic Layer 正在从 BI 时代的指标层，升级为 Agent 时代的中间语言。下一代 Data Agent 的核心竞争力，也许不再是谁能生成最复杂的 SQL，而是谁能够建立一套更准确、更完整、更可验证的企业语义系统。

> [Data Agent 不该直接写 SQL，它需要一层“业务编译器”](https://mp.weixin.qq.com/s/Y_EmQ5sXcgxZazRGcfZRUQ)
