# Agent什么都能做，却总差一步？狍子AI拆解知识与记忆工程

> 作者：DataFunSummit　|　发布日期：2026-10-25　|　原文链接：https://mp.weixin.qq.com/s/BznlDme8CHQ8HfYuGc9mLQ

---

**导读** 本文整理自王思懿在 DataFun Agentic AI 超级智能体系统架构峰会上的分享。狍子AI团队围绕企业知识底座的建设，介绍如何处理结构化数仓、非结构化文档和对话记忆，让 Agent 获取有来源、可检索、可治理的上下文。文章依照演讲顺序，梳理知识生产、消费、治理的工程实践及未来思考。

**主要内容包括以下几个部分：**

1. 结构化数仓：从知识图谱构建到可信取数

2. 非结构化文档：多路检索与知识生命周期治理

3. 记忆工程：让Agent记住经验，也学会更新与遗忘

4. 未来演进：从知识沉淀到持续进化的AI伙伴

---

**Context is All Agent Need**

狍子最初希望把知识变成可消费的生产资料：通过 **数仓 MCP、腾讯文档** 等连接不同来源，再生成 HTML、PPT、Dashboard 等成果，并支持跨端云端存储。这使产品获得了一批内部用户，也让团队看到丰富上下文能够拓展 Agent 的任务范围。

但在数据分析场景中，问题很快出现。使用文本知识时，用户通常比较满意；一旦涉及数仓取数和分析报告，分析师需要反复校准口径，不熟悉口径的运营同学则会质疑数据准确性。Agent 看似能处理很多任务，却未必能把每件事做好。团队由此将关注点转向高质量、可持续沉淀和治理的上下文，而不只是增加知识数量。PPT借用“算法和数据同等重要”的说法提醒大家：对一个以知识为基础的 Agent 来说，**上下文质量会直接影响任务结果**。

**知识建模**

狍子将知识来源分为三类：**结构化数仓**，包括元数据、SQL 资产池、看板和血缘；**非结构化文件**，包括业务知识文档、周报日报和外部事件；以及人脑中的 **隐性知识**，即在日常对话中不断产生的记忆。三类知识形态不同：数仓需要理解指标口径和数据依赖，文档需要解决不同格式与检索问法，对话记忆则要区分临时信息和可长期复用的经验。最终，这些知识都要能够进入员工的工作流，被 Agent 准确调用。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/1IxFwEbkQDojsYWBaYWynt6pC7ibhKZ1H7icvllyibEUq04WicAAbAKQyMNCApmvicCRkW0H5unuMwKSn6Czc4JygLKuzC1eT6CMaNYHzCicIYCL4/640?from=appmsg)

## 1. **结构化数仓：从知识图谱构建到可信取数**

### **1.1 从数据到图谱**

结构化数仓是狍子 **投入最重的知识工程部分**。图谱的原料不仅有引擎元数据、表字段、血缘、SQL 和看板，还包括库表说明、业务术语以及与数仓紧密相关的工作流文档。不同来源的信息被组织到同一张图中，既描述业务概念，也保留实际取数的依据。

建图分四步。先接入数据源；再用规则和查表完成确定性解码，把算子、变量和字段等翻译成模型更容易理解的形式，**只有业务概念抽象交给 LLM**。这样既利用了结构化数据可规则处理的部分，又减少模型直接面对原始 SQL、字段名时产生的歧义。抽取受有界本体约束，预定义 **8 类节点、15 种关系**，例如“分析步骤—作用于—业务指标”，超出类型边界的结果不能直接入图。

抽取后加入独立的对抗性质量审查：**确定性 Validator** 检查证据、类型、关系白名单等，**Adversary** 重点识别误判、漏抽和关系问题，经过裁决及有限轮修正才允许入图。最后对看板、SQL、文档中的同一指标做跨源归一，并通过 Grounding 接回图卡、库表字段等真实取数坐标。这两步采用确定性处理，**避免出现有指标名称却找不到数据来源的情况**。归一处理同一概念在不同系统中的多种叫法，Grounding 则将概念固定到真实来源，两者解决的是不同的问题。

![](https://mmbiz.qpic.cn/mmbiz_png/1IxFwEbkQDqiaZyrctrym8m4w7nu2Ewc6nmdDLAqQsfV3HywvBysBU9NN8bU7r9VsImfrRYyJ95iaic6YV5GeeVVRrEIeO2ciaENQTZoHIZsYVQ/640?from=appmsg)

例如“有效消费 UV”可以关联“每日 Top 内容查询”这一分析步骤，节点里保存取数参数、排序方式、输出格式以及底层明细表和 SQL。**图谱保存的并非孤立的指标名称**，还包括指标怎么计算、用于哪一步分析、能够从哪里取数。也就是说，检索到一个节点时，Agent 可以继续找到所需的步骤和底层数据，而不用重新猜测指标与 SQL 的对应关系。

![](https://mmbiz.qpic.cn/mmbiz_png/1IxFwEbkQDpKyVNBMV3HYWxlOCBmWyAQMhtoLrzE0lQNcIDAHHWiaEHC63ZHwLUiaarbW7HJ87mk5Lcf7bSr0iaNHKZu1yKMaVhRrDFicX9hGicw/640?from=appmsg)

### **1.2 图检索与问答**

当用户询问“品类播放 UV 为什么下跌、怎么归因”时，系统先通过 NER 识别业务名词，再将名词 Grounding 到真实的 Metric、Dimension 或分析方法节点，随后利用 **PPR 扩展相关图卡、工作流和文档证据**。检索结果被组装成结构化上下文，保留 field_key、cardId、bizId、筛选变量等取数坐标。

Agent 依据这些信息沿分析步骤调用 MCP，读取图卡或执行 SQL，并检查数据及筛选条件后作答。图谱提供分析路径，MCP 返回真实数据；**取不到数据时不编造数字，也不让模型仅凭召回文本推断结果**。例如图卡取数时，还要核对筛选是否真正生效，最后回答才能带上对应的图卡或查询依据。

![](https://mmbiz.qpic.cn/mmbiz_png/1IxFwEbkQDqGNH5Oib3FmGlD9QS193zkfPYe3Pd8GBhR8CS5wSxUicZpI2wFqxNCFPWjrVJG0ZPo5OChg4tB9BA0GAI3esSsdHWBmia6m5w3QI/640?from=appmsg)

### **1.3 图谱治理**

数仓不断变化，图谱也需要随之更新。狍子将更新统一为 **replace、add、remove** 三种操作：明确目标数据源后，分别执行覆盖、增量并入或下线。由于节点保留来源接线，相关子图可以按来源调整，而不必让模型重新解释整张图。

业务中也可能出现预定义 Schema 以外的概念或同名异义的字段。**越界类型先进入待审核列表，软冲突进入治理台**，由人判断是否扩展类型或修正关系，不让模型自行扩大本体、静默覆盖冲突。这样既保留了平台通用节点类型的稳定性，也给具体业务留下人工补充和调整的入口。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/1IxFwEbkQDor4xxvHNm8pJ4jf5l5jlfWEMGILCQiaJuicuDtIibAj0WnmP7AoiaFjpPFtD8GAnEjg2DhbmKwmn1Kx1sbQibdQcACVQh6Nd4UicJxY/640?from=appmsg)

### **1.4 知识底座的 Loop Engineering**

以上构成数仓知识的“**生产—消费—治理**”循环：生产时用有界 Schema 抽取业务概念；消费时沿指标、维度、口径和工作流检索、取数；治理时校准冲突与过期内容。知识会被使用，也能根据数据源变化和人工反馈持续修正。

![](https://mmbiz.qpic.cn/mmbiz_png/1IxFwEbkQDrbPZ4ySHVibs21y9lCjtDlMib2DCWHibfWYG6DPkhFydEJHzgysBREnWN0Km8gzpNyOWloEDVmomibIsau3SjA0G69enmoyCyDbs8/640?from=appmsg)

**02**

**非结构化文档：多路检索与知识生命周期治理**

**1. 原始文件与多类型预处理**

非结构化文件的重点是让不同内容都能被检索。狍子对 PDF、Excel/CSV、HTML/JSON、PPT、图片和视频分别做解析，保留文档结构、表格、幻灯片层级或经 OCR、语音转写得到的内容，为后续知识化提供原料。解析完成后，原始内容仍需保留：**后续无论采用关键词定位还是模型阅读，都要能够回到原文**，而不能只有改写后的摘要。

![](https://mmbiz.qpic.cn/mmbiz_png/1IxFwEbkQDogUatbYvx9S1UxNznNbWPIt0I4EkWqvPfYhiaCMGNtvM1JnGYefyFewytsDh7XiauD496f7KhTDutHEtozrNBXlPXa7wEYE1Ofc/640?from=appmsg)

**2. 非结构化文档知识化**

同一份文档入库时保留三种结构：**原始段落、稠密向量、知识图谱**，对应三种检索。**Grep 直接做字面或正则匹配**，适合合同编号、错误码等不能错一个字符的查询；向量检索解决提问与原文表述不同的问题；图检索沿实体关系查找跨文档的归属、依赖和影响范围。Agent 根据问题选择检索路径。比如相邻的两个合同编号在向量空间里可能很相似，却绝不能互相替代；反过来，要回答一个条款影响了哪些产品，仅靠匹配条款原文又可能找不全关系。

这里的图谱相对 **Schema-free**，允许 LLM 从文档中抽取实体和关系；与数仓有界本体相比，侧重点是“**轻治理、强检索**”，但仍保留必要的前后校验，避免无约束地扩展知识。

![](https://mmbiz.qpic.cn/mmbiz_png/1IxFwEbkQDr1XWmQF7yJcCXPUbYicKqjPNyYcPjOIA89VibvUPBVYaMCmfn560SkDeDAsibzuLMdKLCO6mzlIB06gXbhaU43yx8icvft3wxcEtk/640?from=appmsg)

**3. 生命周期治理**

文档知识入库后并非永久等权。系统为知识库 Chunk 设置 **Vitality Index**，综合脉动、呼吸、循环、代谢、免疫五类信号；图谱则检查过时页、别名冲突、弱关系及孤立节点等问题。治理依次经过评分、检索加权和清理：高活力内容优先召回，长期未引用或发生冲突的内容逐步降权、归档或清理。其中，知识库五类信号的权重分别为 **25%、20%、20%、20% 和 15%**。原始文档与图谱采用不同指标，但都希望让检索结果随使用和维护而更新；清理动作也包括诊断、实体归档和冲突合并，不只是删除文件。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/1IxFwEbkQDrwjg5YTLZ4t8QxiajJ4gLYYGXl3eUdIoDP9x6WNQNW4pT9bV0hiciaet5ibXKsdHZUCs6oF4mAfcicj4icPmVruvSP0leHkXURJQkm8/640?from=appmsg)

**03**

**记忆工程：让Agent记住经验，也学会更新与遗忘**

**1. 记忆机制**

记忆工程先要回答：哪些对话内容值得长期留下？狍子区分三类记忆。**个人记忆**记录跨项目的沟通风格、偏好和行为规则；**项目记忆**沉淀团队共享的项目事实、技术决策和架构约定；**每日日志**按 Session 摘要讨论、决策及结论，作为按天归档的事件流。个人和项目记忆可以由 Agent 主动洞察，但需要用户确认后落库，也允许用户主动管理；每日日志则由系统自动归档。个人记忆面向用户级、跨项目使用；项目记忆属于团队空间；每日日志关注近期发生的事实，三者的作用范围不能混用。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/1IxFwEbkQDqMqpbA1THbxKr6dhHK3zrFnIbjbDriaosbBLFvibqQ5TyDN1HH5v50a5wPy84CsnFUWQvRWwbWwQvs4a8eqLI12iafdHP4SssI0M/640?from=appmsg)

**2. 记忆的三种使用方式**

记忆的消费分为直接入上下文、向量检索和图检索。硬性偏好、项目约定及最近一天的日志可以按预算注入 Prompt；向量检索用于召回换了说法的历史记录；图检索依照预定义的 **identity、goal、decision、preference、fact、event** 等节点类型及关系，追溯决策为什么发生、后来如何变化。向量和图检索还可采用 **RRF 混合召回**，记忆场景不依赖 Grep 式精确字符串搜索。图中的关系可以表达 updates、contradicts、caused\_by、result\_of 等含义，因此能够追问某项约定为何变化，而不仅是找到当时说过的那句话。

![](https://mmbiz.qpic.cn/mmbiz_png/1IxFwEbkQDp8F452WTze9Rk3V9Xxqiaic6vyEYuPfNfAbibshxPq84TIcLrIJrfhMYhXwia2UnHQSpPOlxribjoM8X6Ov5QCqcdFDd6oa3ibHbialc/640?from=appmsg)

**3. 记忆的生命周期治理**

记忆如果只进不出，很容易积累过期偏好与重复条目。狍子将其治理分为五步：Encode 写入并赋初始重要度，Reinforce 随召回强化，Decay 随时间衰减，Consolidate 合并语义重复的记忆，Prune 对低活力记忆作软删除。这里的**“遗忘”是停止召回并保留溯源，并非直接物理删除**；身份类记忆也不会自动清理。重复记忆合并时会保留溯源关系，时间衰减与召回强化共同影响健康度，避免把“很久没提过”和“已经不再正确”简单视为同一种情况。

![](https://mmbiz.qpic.cn/mmbiz_png/1IxFwEbkQDqeg3ocAg1BWBh4qxVQCZWElBxq9azs1lxdUUerTOz0Dl9jum1Kcquw0wvnHmx38TxUYaniaDSTJkGVfhGlHgmqk8DQVJiaKcO8g/640?from=appmsg)

**4. 记忆应用示例**

在图谱界面中，用户可以查看目标、决策等记忆及其动态分数，并参与修正。比如撰写公众号文章时，狍子根据既有写作记录指出已覆盖的主题，同时提示尚未写过的方向。这个例子展示了**记忆如何参与连续任务**，而不只是保存会话摘要。对于经常持续推进同一项工作的用户，曾经的成果和未完成事项可以成为下一轮任务的线索。

![](https://mmbiz.qpic.cn/mmbiz_png/1IxFwEbkQDqNcyWNPoHWj14oqrxeaty6ZB0j2wPnia0CsBqouEDnibY8aKvmNJv9vc2aLpCEljGoDUCu92WRD23nM3BiaOUHrVpjn8N4UCeuRU/640?from=appmsg)

**04**

**未来演进：从知识沉淀到持续进化的AI伙伴**

三类知识遵循同一条“生产—消费—治理”主线，但处理策略有所区别：**数仓依靠确定性解码和 Schema-driven 图谱**，强调业务口径和取数可信；非结构化文档保留 Grep、向量及相对开放的图检索；记忆则聚焦值得保留的用户、项目与事件信息，并通过上下文注入和检索参与任务。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/1IxFwEbkQDrlaTUiaiaFCiaIh78HmL8ADpUjohd3A562S9YRd9YAYz0LcicDwcbKCE6AxhcjN7xpm1ADHc8qAY2kToj7xmAI2Dw40Lb21dFUb10/640?from=appmsg)

目前狍子的界面涵盖知识库、数据连接、长记忆及多类型 AI 产物。团队希望**让知识与数据进一步结合**：除数仓和业务文档外，也逐步考虑将外部知识、日常情报和持续产生的记忆纳入同一知识底座，让这些信息在实际工作中被检索、验证和使用。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/1IxFwEbkQDrNf04jTXOOicD7luvdwdGkGE0aR2jia3QqEcxqCr37bwicLnibticmVAIElicQibBSMkyOh2X1IlFjibZta1tCaVbu6SWKKFcCPhic4ibFk/640?from=appmsg)

![](https://mmbiz.qpic.cn/sz_mmbiz_png/1IxFwEbkQDqEd4MDjZEQiaLxYkqnDYx08fNUsJFrdiahVYiaY00YmTed39pSogIXBJIBOMMRDPhuia5YpDwG6yw3wEqfdyfSTOy1mGotDyuswXI/640?wx_fmt=png&from=appmsg)
