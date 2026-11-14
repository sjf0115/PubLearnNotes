# 本体驱动：企业级DataAgent 的效果优化之路

> 作者：DataFunTalk　|　发布日期：2026-11-13　|　原文链接：https://mp.weixin.qq.com/s/SEHPI3Jl_UbBpoA_yUxgpw

---

**导读** 银行管理者问“经营情况怎么样”，AI 可能只找回净利润，却漏掉存贷款余额、不良率等关键指标；继续追问“存款为什么下降”，系统又停在表层数字。问题并不完全出在模型：企业有数据、有指标，也有大量 SQL 和报表，却**缺少把这些信息连起来的业务关系**。

OceanBase 选择从本体入手，**将业务对象、关联、属性和计算口径组织成图**，再让 DataAgent 沿图找数、分析原因。

**主要内容包括以下几个部分：**
- 问“经营情况”，为什么只找回一个指标
- 把业务关系接回数据，指标才有来路
- Agent 沿图找口径，也沿图追原因
- 从一个业务域开始，让本体越用越准确


---

## 1. **问“经营情况”，为什么只找回一个指标**

企业问数的难处，往往在查询开始之前就已经出现了。管理者提的是业务问题，系统拿到的却是字段、指标名称和文档片段。若中间缺乏一套稳定的业务映射，即使模型能理解提问，也可能拿错材料。OceanBase 在银行客户的实践中，把这种偏差归结为两类：**相关知识找不全**，**找到数字后又无法继续解释原因**。

![](https://mmbiz.qpic.cn/mmbiz_jpg/1IxFwEbkQDr9ceB2Fibs3qQB4YqLic1ka3osvicPCkAyHEBrWZQKtOVLygtASmcA3T12eSibQHMcP2aA6qWcM6FwLSluibXJbKqws6gVW2nY1iaH0/640?from=appmsg)

例如行长问“经营情况”，对应的可能是一般性存款余额、各项贷款余额、净利润金额、中间业务收入和贷款不良率五项指标。按向量相似度进行 Top-K 召回，“净利润金额”因为字面接近被选中，其他四项却可能被遗漏。这种遗漏并不说明指标不存在，只是提问与指标名称之间缺少直接的文本联系。究竟应该看哪五项，属于银行的业务知识，**不能让相似度代替判断**。

![](https://mmbiz.qpic.cn/sz_mmbiz_jpg/1IxFwEbkQDovrXedaxhJzzwkY6fDyA13UV7tC3JNIGTpI3m3ibTnZTzxQiaGnPTcGK2gcJUG0aPVz2SYibMhhiclFiciaon94P8ibswj715icdRgko8/640?from=appmsg)

即便回答了五项指标的数值，管理者仍会追问“为什么”。一般性存款余额往下有个人活期、定期、通知存款等细分项目；要解释余额下降，就得**顺着指标的构成关系逐层检查**，最终判断哪个子项、哪个客户或渠道发生了变化。越往下，子指标的名称与最初的“经营情况”越不相似。检索若只负责找表层相关文本，就很难把这条分析路径补齐。

![](https://mmbiz.qpic.cn/mmbiz_jpg/1IxFwEbkQDqZMIJfoRWGLP5cJaMeajpiayu7HYvUk35QabuibJ1oS24HMuzMfJn6kJ0PPOBwrBxiaHuXC4BezWzaPgqKhQ4Yyvq689iceZnHSqU/640?from=appmsg)

两类问题指向同一个缺口：传统 RAG 将完整的企业知识拆成可检索的片段，片段之间的类型、从属关系和计算口径却未必能够保留下来。模型可以读懂一段材料，却不一定知道下一步该去哪里找。OceanBase 因而**把问题放到知识组织方式上**：让企业的业务对象和指标形成一张有结构、可沿关系继续探索的图，先把回答问题所需的知识路径建立起来。

## 2. **把业务关系接回数据，指标才有来路**

企业数据里的“关系”，与业务人员理解的关系并不相同。数据库通过表、字段、主外键和 ID 连接记录，业务人员关心的则是客户开立了哪个账户、账户持有什么存款、交易经过什么渠道、客户归属哪个机构。单凭表之间的连接，Agent 仍需猜测这些数据分别代表什么业务含义。**把底层数据关系映射成业务关系，是本体化语义层要承担的工作**。

![](https://mmbiz.qpic.cn/sz_mmbiz_jpg/1IxFwEbkQDrSq6VCCOMXCKzjdQiauxicTJhHRIbKy27IFoIa0UVLmyGRVRib3DWB98vMjN1GL4vHO4GPibUqiajX85Q4ehE0ibjMtvadrV0iam7fOE/640?from=appmsg)

这一层位于离线数仓、实时数仓、湖仓、OLAP 等数据底座与上层 AI 应用之间。原有数据加工、分析和展示方式可以继续使用；本体语义层负责提供更接近业务的组织方式，让经营分析、数据洞察和成本控制等场景**共享对象、关系和口径**。它需要能够回到原始数据与已有计算逻辑，而不能只在语义上建立一套与数据脱节的描述。

![](https://mmbiz.qpic.cn/sz_mmbiz_jpg/1IxFwEbkQDrrvLyjuYrSUVJrEPCERtEPH5a4PcCnE14y98pD2GFkCKkf12F5icXeucEZppjNRz6hgjj4WHaY6pE4kv4hRNJLUUoHQmvlKyib4/640?from=appmsg)

OceanBase 将本体语义归纳为四个要素。业务对象定义客户、账户、存款、机构等实体；业务关联说明对象之间的“开立”“持有”“归属”等联系；业务属性标识对象的类别、状态和维度；业务口径记录挂在对象上的计算规则。**对象解决“找谁”，关联解决“怎么走”，属性帮助确定“是哪一类”，口径则回答“怎么算”**。四项信息放在同一张图里，业务提问才能逐步落到具体字段和计算条件。

![](https://mmbiz.qpic.cn/mmbiz_jpg/1IxFwEbkQDr7XduCYBTqx0SVZSaf27sflabODTOZOVhWZmwdOlAicyicy40eR9FPa2jiaMMdYAPibQciaRnfN5JDCxrA5BG8Wn8o9npEOL0nEAGE/640?from=appmsg)

“哪些客户导致华东区存款余额下降”就需要走过这样的路径：从客户找到关联账户，再由账户连接存款和交易，通过机构关系确定华东区范围，同时按既定口径计算存款余额。示例里，定期存款到期、活期存款转出分别影响了不同客户的余额。没有对象与关联，AI 难以将“客户”“区域”“余额变化”拼成同一次查询；**没有口径，即使关联正确，也可能算出另一个数**。

## 3. **Agent 沿图找口径，也沿图追原因**

本体图建成后，还要控制模型一次能看到多少知识。把整张图一次性塞进上下文，模型容易被大量无关信息分散注意力；只召回极少数内容，又可能在入口处漏掉答案。OceanBase 采用 **AI 自主探索** 的方式：先浏览有哪些业务对象，再按当前问题需要展开属性、关系和口径。知识沿探索路径逐步提供，既保留继续下钻的可能，也避免每次都读取全部内容。

![](https://mmbiz.qpic.cn/mmbiz_jpg/1IxFwEbkQDpmXITT4ia0OnSrKZ7o0yhElIsUjlWkvb99BoJSCObo7h0fMiaP0Sv9CfmicDFTP8Ze2ibjELo6WCpDyEQg41hqFDjFmA5u7WvrI8M/640?from=appmsg)

探索并不依赖一条事先写死的路径。模型可以先进入某个对象，发现条件不符后转到另一分支，也可以并行考察多个候选方向。例如“存款余额”既可能出现在个人金融域，也可能与综合管理域有关，两条路径都值得检查。只要探索动作仍停留在知识读取和路径判断阶段，**走错一步主要增加信息读取成本，不会直接改变业务数据**；较早停止探索反而可能遗漏正确口径。

![](https://mmbiz.qpic.cn/sz_mmbiz_jpg/1IxFwEbkQDpgoJyaCicSVtWgU8qUkiaPVIyuX5tBKkEQ9U9BFQfaZKI1IYX0WNd3U3wavHk5iaFWSupiaicpUEbYqB4rJ8F2786ODKvDxQQCHFms/640?from=appmsg)

查询“某支行的个人活期存款余额”时，Agent 先定位存款对象，展开口径列表，识别“个人活期存款余额”及其对应的科目编码 2301；随后沿“持有”关系找到相关账户，再通过“归属”关系连接机构，将“某支行”绑定为过滤条件。**对象、口径和限定维度确认之后，相关信息才进入 SQL 生成环节**。自然语言里的几个词由此各有去处：存款对应计算口径，账户提供取数路径，支行决定查询范围。

![](https://mmbiz.qpic.cn/mmbiz_jpg/1IxFwEbkQDpGYSXXwicD3alTNVdR0qBeGRndpVv9MrxicFAElpYQhcyer2eE4rw4ICbxNFOE0RmpuzczOd3SkW6WJB3Jh7icpumlLxyUIcTK8Q/640?from=appmsg)

再往下追问“华东区存款余额为什么下降”，探索方向就从指标向关联对象展开。示例中，**一般性存款余额环比下降 12%**。系统继续查看存款品种、客户等级、机构和渠道等维度，发现 **定期存款下降 22%，手机银行转出占比 68%**；沿相关分支深挖，定期存款中到期未续约占比 68%，并经手机银行转出。两个 68% 分别对应渠道转出与到期未续约的不同口径。归因由一项结果追到具体业务行为，也就有了进一步核实客户情况的方向。

![](https://mmbiz.qpic.cn/sz_mmbiz_jpg/1IxFwEbkQDp6zmeZE2riay1QVQRxGaCynbHEfZPJ6DrId3hdYibpBawGqZjOFs2bia2w8SZhCTr1ic1Zk69GLsv5aMNHmAnol8F9lp19kCSzZt0/640?from=appmsg)

在这种设计中，本体提供的已不只是可供模型引用的文字。RAG 的主要作用是把相关材料交给 AI 阅读；**本体把对象、属性、关联和口径变成可查询、可展开、可追踪的能力**，下一步查看哪一层由模型根据问题决定。这里的“行动”主要指在业务图上探索、取数与推理，并不意味着 Agent 已能够脱离人工控制执行转账、审批等业务操作。

## 4. **从一个业务域开始，让本体越用越准确**

但一张能够正确导航的本体图，最初从哪里来？企业已有指标表、SQL、BI 看板和 ETL 流程，很多计算口径就在这些资产里；还有一些规则不见于任何正式文档，只存在于资深业务人员的经验中。OceanBase 没有选择一开始就建立覆盖全公司的统一大图，而是**先从边界清楚的业务域入手**，让本体在真实问数中经受检验。

![](https://mmbiz.qpic.cn/mmbiz_jpg/1IxFwEbkQDo7jh2wG1chNHnCHwZgUpP1X1xVVhfkcvVrP7Y2NzYqdiald8tlcrJiaVjiacFs50uXqdHegljhOTPQFc6BGaMicvxS2qErMdhvsdk/640?from=appmsg)

其生命周期从业务域冷启动开始，经过加工、生长，再逐步汇聚为全域本体，并尝试让已有知识反过来支持新 Agent。冷启动的任务是把有限范围内的表和知识引入系统；加工负责抽取业务对象、关系、属性和口径；生长依赖业务提问与纠错。**只有一个业务域的问数效果得到验证，相关子本体才适合进入下一步汇聚**。

![](https://mmbiz.qpic.cn/sz_mmbiz_jpg/1IxFwEbkQDq9F4VzlhVTnGvLqBQWibwd9SZQq5aIRsRsN4tCdPrZLZ1FiaIQR7mxpU4jsdZzWKPkUorlotZ2LDYvtXYwJmibaG0ibP4XFQanBGA/640?from=appmsg)

加工并非要求企业重新填完一套业务词典。输入包括表名、字段、类型和外键关系，数据采样得到的真实值，以及已有知识库；历史 SQL、BI 看板和 ETL 血缘也可提供计算依据。OceanBase 使用自研 Agent 从这些材料中识别业务含义，例如将 t\_deposit\_acct 解释为存款账户，将 cust\_id 关联到客户和账户的关系，将 acct\_status 识别为账户状态，并从历史查询中提取余额计算时排除同业存款等条件。**产出的本体是可供校验的初稿，不能跳过业务确认**。

![](https://mmbiz.qpic.cn/mmbiz_jpg/1IxFwEbkQDrvhpIxZNMujseRWbHNC2Ukxt5gdWOj3KDwKM5Pf977hqziaIrhQiav9IFBemSsc7OdWnTCNpEGGK4vreF7VFznV3e3DuxUDoLzs/640?from=appmsg)

校验未必需要专家逐一审核图上的节点。让业务人员直接提出平时关心的问题，再回看 Agent 经过了哪些对象、用了什么口径、如何得到答案，错误更容易暴露。比如专家补充“存款余额通常还要排除保证金存款”，系统需要进一步澄清适用范围，再通过人工确认写入知识。类似规则可能从未出现在既有文档里，**只有业务人员沿着查询结果反复纠错，才会逐渐沉淀出来**。

![](https://mmbiz.qpic.cn/sz_mmbiz_jpg/1IxFwEbkQDoNfRjdFta81cicUe1ZQW6GwA2QSyu2edDPlLJYyQ7aawzqx8865KOZzstVlRRhEC2DVC8Zl1us3p2ibou7aupZuyGgCpibiandZV4/640?from=appmsg)

局部准确之后才谈得上跨域复用。零售存款、对公信贷和风险管理可能都使用“客户”这个词，实际定义、属性与分析口径却不完全一致。各自的子本体经过验证后，**可以尝试提取共同概念并建立跨域连接，同时保留必要的业务区分**。否则，为了让所有部门共用一个名字，反而会让具体问题失去准确的限定条件。

![](https://mmbiz.qpic.cn/sz_mmbiz_jpg/1IxFwEbkQDoGLibUQ1Pt0zOLV9JeAdBzjcVE2mpeaDTqazVh3ABb1hrAFfAlRwphnibSwQJFMH94Gy0ibI1lTQXS4jNXhZn1XcW94ic2cD8JrK8/640?from=appmsg)

更远的目标，是新 Agent 能直接继承积累下来的全域知识，减少反复解释企业概念、重新校准同一口径的成本。不过这一“全域反哺”**仍是 OceanBase 正在探索的方向，尚不能当作已经实现的能力**。子本体怎样合并、概念冲突如何处理、新 Agent 能否稳定复用，都需要在真实业务里继续验证。

![](https://mmbiz.qpic.cn/sz_mmbiz_jpg/1IxFwEbkQDq3bbbFJDUShwkeowSnf3u8bKxtY2RptRcn0mJ8CHTudszx5QODk1TyjllMtG8YVGPjbtoRDUr4wyEGv6ibo8ZicLU7Cn3hiaWVd4/640?from=appmsg)

从一开始就追求全域统一，看起来覆盖面更广，实际容易陷入另一种困境：跨部门讨论“客户”的定义，最终只能得到“与企业发生商业关系的主体”这样宽泛的表述；反复协调消耗大量时间，具体问题却仍无人回答。一次性建好的静态知识体系也可能在业务变化后失效。**先把一个部门经常问的问题答准，再逐步扩展**，能够把每一条知识的适用范围和校验过程保留下来。

![](https://mmbiz.qpic.cn/mmbiz_jpg/1IxFwEbkQDrURUoehLIhK8AK0tmoVdUeU8icF30yH1Hy0E4UOmTrSgSzibQRQ9ibCalb6QMp2QOPONTGO0F4PficlWiaeEv1Mq97Ceu1Wub2icRyA/640?from=appmsg)

随着业务人员持续使用，图上积累的不只是多几张表、多几条关联，更有企业内部对于指标怎么算、异常怎么查、不同部门如何理解同一对象的**共识与分歧**。这些东西原先散落在代码、报表和人的经验里，难以完整交给模型。通过反复提问、追溯和修正，它们才有机会成为下一次分析能够直接利用的业务知识。

![](https://mmbiz.qpic.cn/sz_mmbiz_jpg/1IxFwEbkQDpDIdfzfjDWHJzGPcVI4XiamHdekKhibAU2luVM5PbytHPrdbraNxlQYLtD4aq3ugxHicaP7K7WbkMZuCokTfQtIiaEvVZ5pfibHpIE/640?from=appmsg)

OceanBase 将这套思路用于本体驱动的问数产品 **DataPilot**，让 DataAgent 能够沿业务关系定位指标、追查变化原因。比一次回答更难积累的，是回答背后那套经得起业务追问的知识结构：每澄清一次口径、找准一条关联、追清一次异常，下一次分析就有了可以复用的依据。模型能力还会继续提高，但企业自己的业务定义、经验与判断无法从通用模型中直接取得。让这些知识在真实工作中不断被验证、修正和继承，才可能让 DataAgent 从偶尔答对一个问题，**走向长期可靠地理解企业业务**。
