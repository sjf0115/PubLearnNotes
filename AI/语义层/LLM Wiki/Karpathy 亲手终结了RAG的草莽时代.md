在“每一枚 Token 都要精打细算”的共识下，AI 圈一度流行一种略带调侃的说法：真正的高手，不是把 Token 用在写代码上，而是用在更高杠杆的事情上。最近，这一理念被再次推向台前——主角是患上了“AI 精神病”的 Andrej Karpathy。

## 1. Karpathy 新项目爆火，技术细节完整披露

几天前，Karpathy 在 X 上分享了一套自己正在实践的工作流，称之为“LLM Wiki”：他不再把大模型主要用于写代码，而是将绝大多数 Token 消耗，转向构建一个围绕个人研究兴趣的“可演化知识库”（以 Markdown 和图片形式存储）。这条帖子在 x 上浏览量超 1700 万，围观者众多。Karpathy 详细介绍了 LLM Wiki 项目的工程实现、数据采集、工具选择等技术细节。

> 项目地址：https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

![](https://mmbiz.qpic.cn/mmbiz_png/hLLZnAbUwNia0KXa2N0ibCUFOvYWB1oj52KmwpON0ljiacrwdHmHuOnpOJBQKqkicLN4dl4B5hBicohFibwY2qFOEicGE15KgtKaZMDTeL8zaqmn0s/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=2)

从工程实现上看，Karpathy 的方法并不依赖复杂的基础设施，甚至可以说极其“朴素”。一切始于一个名为 raw/ 的原始目录。在这个目录中，他将与研究主题相关的所有素材一股脑地收集进来——包括论文、技术博客、代码仓库、数据集，乃至图片等多模态内容。这一步并没有任何结构设计，核心目标只有一个：最大化原始信息的完整性。

接着，Karpathy 调用 LLM 对这些素材进行 **增量“编译”**，生成一个 Wiki。这个 Wiki 本质上是一个具备清晰目录结构的 Markdown 文件集合，类似一个由 AI 自动撰写和维护的知识百科系统。

Karpathy 把 Obsidian 作为这个系统的“前端 IDE”，在这里他可以查看原始数据、编译好的 Wiki 以及衍生的可视化内容。Karpathy 介绍，这么做的 核心点在于：Wiki 中的所有数据都由 LLM 编写和维护，自己极少直接动手修改。他还尝试了一些 Obsidian 插件来以不同方式展示数据，比如用 Marp 插件生成演示幻灯片。

当知识库规模逐渐扩大，这一系统开始展现出更强的能力。Karpathy 提到，在一个包含约 100 篇文章、总计 40 万字的研究项目中，他已经可以直接向 LLM Agent 提出复杂的系统性问题。与传统认知不同，他并没有引入复杂的 RAG 架构，而是依赖 LLM 对 Wiki 的“内生理解”能力——模型通过自动维护的索引与摘要，可以高效定位相关信息并进行综合分析。

这一点尤为关键。过去一年，RAG 几乎成为企业级 AI 应用的“标配”，但 Karpathy 的实践表明，在中等规模的数据集上，LLM 本身已经具备足够强的“自检索”与“自组织”能力。这意味着，一部分复杂的系统设计，可能正在被模型能力的提升所“吞噬”。

![](https://mmbiz.qpic.cn/mmbiz_png/hLLZnAbUwNiaBicJlR8yxPNgaQr1ZOeJH4aMfmCDdxYobMrIrwB5pL9ggMgqsuiaFgIgjgGl1r9qHhnP4p2RSmUIS5jsGVfiaiakERErOnN60nmk/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=3)

在输出层面，Karpathy 同样不满足于传统的文本回答。他将 LLM 生成能力进一步扩展到多种格式：包括 Markdown 文档、基于 Marp 的演示幻灯片，甚至是通过 Matplotlib 绘制的数据图表。这些结果统一在 Obsidian 中进行可视化呈现，使知识不再停留在“答案”，而是转化为可以复用、传播和沉淀的资产。

更重要的是，这些输出并不会被丢弃。相反，它们会被重新归档进 Wiki，成为知识库的一部分。换言之，每一次提问与探索，都会对系统进行“增量训练”——尽管不是传统意义上的模型训练，但在知识层面，系统的能力确实在持续累积。

为了维持这一系统的长期健康运行，Karpathy 还设计了一套 **“自动化运维”机制**。他会定期调用 LLM 对整个 Wiki 进行“体检”：检测数据不一致、补全缺失信息、通过联网搜索引入新资料，甚至主动挖掘潜在的关联关系并生成新的专题文章。

此外，他还通过“Vibe Coding”的方式快速开发了一些辅助工具。例如，一个用于检索 Wiki 的简易搜索引擎，可以通过网页界面或命令行调用。在更复杂的场景下，这些工具甚至可以作为 LLM 的外部能力接口，由模型自主调用完成任务。

随着知识库规模的进一步扩大，Karpathy 也在思考下一阶段的演化方向：是否可以通过合成数据生成与微调，将这些结构化知识“压缩”进模型权重之中。换句话说，从依赖上下文窗口的外部知识系统，迈向模型内部的长期记忆。

简单总结一下，该架构设计极简，仅包含三个组件：
- **一个 Markdown 文件文件夹**。这是你的知识库。它可以包含任何内容：研究笔记、会议纪要、项目文档、读书笔记、个人参考资料、带有解释的代码片段。
- 每个文件内部 **结构一致**。优秀的 LLM Wiki 文档采用一致的内部格式——标题、简短摘要、标签主题以及正文内容。模型利用这种结构更快地找到相关信息。
- 使用 Claude Code 作为查询界面。打开终端，导航到你的 wiki 文件夹，启动 Claude Code，然后向它提出问题。Claude 会读取所需的文件，综合生成答案，甚至可以根据你的要求更新或添加注释。

就是这样，无需数据库，无需向量嵌入也无需服务器。只需文件和一个功能强大的模型。

## 2. LLM Wiki “杀死了”RAG？

Karpathy 的这一实践之所以能够迅速引发关注，是因为它并非只是一个效率工具的升级，而更像是对“个人知识管理”（PKM）体系的一次重构。从 Notion、Roam Research 到 Obsidian，过去十年里，人们始终在寻找更好的知识组织方式，而在 LLM 的加持下，这一问题的解法，正在从“如何记录”转向“如何自动生成与演化”。

因此有 X 用户认为，LLM Wiki “杀死了”RAG。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/hLLZnAbUwNgiaMKrmMibwwnM3DebR7ibrgWIupkOZ6vOvDf6V43c1e6CTbGo3YeUAibXZ2wUfWQBdfnI4GHFmZR3RhzxlewUJaGS1CED6DkbEOc/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=4)

过去三年，为 LLM 提供专有数据访问的主要范式是检索增强生成（RAG）。在标准的 RAG 设置中，文档被分割成任意的“块”，转换为数学向量（嵌入），并存储在专门的数据库中。

当用户提出问题时，系统会执行“相似性搜索”来查找最相关的数据块，并将它们输入到 LLM 中。Karpathy 的方法，他称之为 LLM 知识库，摒弃了中等规模数据集的向量数据库的复杂性。相反，它依赖于 LLM 对结构化文本进行推理能力的不断提高。

系统架构（由 X 用户 @himanshu 在对 Karpathy 帖子的广泛回应中可视化呈现）分三个不同的阶段运行：
- 数据导入：原始资料——研究论文、GitHub 代码库、数据集和网络文章——被导入到一个 raw/ 目录中。Karpathy 使用 Obsidian Web Clipper 将网页内容转换为 Markdown.md 文件，确保即使是图像也存储在本地，以便 LLM 可以通过视觉功能引用它们。
- 编译步骤：这是核心创新点。LLM 不仅仅是对文件进行索引，而是对文件进行“编译”。它读取原始数据并生成结构化的维基百科页面。这包括生成摘要、识别关键概念、撰写百科全书式条目，以及——至关重要的是——在相关概念之间创建反向链接。
- 主动维护（代码检查）：该系统并非一成不变。Karpathy 描述了运行“健康检查”或“代码检查”的过程，LLM 会扫描 wiki 以查找不一致之处、缺失数据或新连接。正如社区成员 Charly Wargnier 所观察到的，“它就像一个活的 AI 知识库，能够自我修复。”

Karpathy 将 Markdown 文件视为“真理之源”，从而避免了向量嵌入的“黑箱”问题。AI 做出的每一项声明都可以追溯到特定的.md 文件，而这些文件可以由人阅读、编辑或删除。

![](https://mmbiz.qpic.cn/mmbiz_png/hLLZnAbUwNgoneTSCQEdiaeSnib7L2sl6tuma18TVJH4UkDvRUobV1wciab98FXic1TKkFbnBUpe0W8N3uqI9n8csfw5Sicqicts3j8AF4OEFDfw8/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=5)

在 Youtube 上，也有不少关于 “LLM Wiki killed RAG” 相关话题的讨论。一位 ID 名为 DIY Smart Code 的博主阐述了为什么他认为有了 LLM Wiki 后，就不再需要 RAG 了。

该博主表示：人类并不缺少信息，缺的是对信息的持续组织与有效利用。研究显示，人类在获取新知识后的短时间内就会遗忘其中的大部分内容，而现代知识工作者每天平均需要花费近两个小时，去查找那些“自己曾经读过”的信息。这不仅意味着巨大的时间浪费，也揭示了一个现实困境——无论是笔记工具、收藏夹，还是所谓的“第二大脑”，在长期使用后，往往都会演变为一个信息堆积却难以调用的“知识墓地”。

过去几年，AI 行业尝试通过 RAG 等技术路径解决这一问题，即通过向量数据库对海量文档进行索引，在需要时检索相关片段并生成答案。然而在实际应用中，这类方案往往面临落地难题：检索可以做到，但理解不足；信息可以找到，但难以形成结构化认知。某种程度上，这类系统只是让用户“更快地搜索混乱”，却没有真正解决知识组织的问题。

Karpathy 的思路则截然不同。他并没有继续优化“检索”，而是从源头出发，提出“写出更好的文档”。在他的体系中，原始数据被视为“源代码”，大语言模型则充当“编译器”，而最终生成的 Wiki 知识库，则是可以直接使用的“可执行产物”。

> 在这种情况下，基本就不会再需要 RAG 了。

## 3. 技术社区和企业反响热烈

虽然 Karpathy 自己将 LLM Wiki 描述为“一堆蹩脚的脚本”，但它在技术社区和企业级市场还是引发了不少的关注。企业家 Vamshi Reddy (@tammireddy) 在回应 Karpathy 帖子时表示：“每个企业都有一个原始目录。从来没有人把它整理过。这就是产品。”

![](https://mmbiz.qpic.cn/sz_mmbiz_png/hLLZnAbUwNjFCt8siacVlDOvBJKwjHeDXkSxomyMT2j3ZwQlW2vPyXRjkzVGwGM5iaqFdqojJnqvKic5EIKtgg0BvBW8IXA6bJkIu6KVyPZNok/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=6)

Karpathy 对此表示赞同，并认为这种方法代表了一种“令人难以置信的新产品”类别。目前大多数公司都“淹没”在非结构化数据中——Slack 日志、内部维基和 PDF 报告，没有人有时间去进行综合分析。“Karpathy 式”企业层不仅会搜索这些文档，还会主动编写实时更新的“公司圣经”。

AI 教育家兼简报作者 Ole Lehmann 在 x 上发帖称：“我认为，谁能把这个功能打包成普通用户都能用的东西，就掌握了一项巨大的技术。一个应用就能与你已经使用的工具、书签、稍后阅读应用、播客应用、保存的讨论串同步。”

![](https://mmbiz.qpic.cn/sz_mmbiz_png/hLLZnAbUwNj43GZWDUBmxopiaEhVtiaibxJSP2bb8XlbZlEKQicLRDQb19bISSNHlhGakWzgOjaVUJbhq5MZh5Cv9J0OmiaYjQ8dIB4vv4KDVbN4/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=7)

AI 企业 Agent 构建和编排初创公司 Edra 的联合创始人兼首席执行官 Eugen Alpeza 在一篇 X 帖子中指出： “从个人研究维基到企业运营的飞跃才是真正的挑战所在。成千上万的员工，数百万条记录，以及团队间相互矛盾的经验知识。的确，企业级市场需要一款新产品，而我们正在打造它。”

![](https://mmbiz.qpic.cn/sz_mmbiz_png/hLLZnAbUwNjJpFzrjz86sql2y3ZBm1icib23VexLibd6gWfvxuWbh5quFXvslKfoAcAJxl6LZUdoZtuQBeQ23Ra0LrIWLFDm4ahAxuCGeJAyIY/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=8)

AI 代理创建平台 Secondmate 的创始人 @jumperz 最近发布的一份架构分解报告，通过“群体知识库”展示了这一演变过程，该知识库将 wiki 工作流程扩展到通过 OpenClaw 管理的 10 个代理系统。

![](https://mmbiz.qpic.cn/mmbiz_png/hLLZnAbUwNgzFqZIic2jQJ7MVNLkDFPBIcI6FPa4HuV7WlaBPOibR0RgxBosOHCVzia3HegePyzWV47GP3QlbJrahey1LlTqb3JcyT0icgvkAgo/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=9)

另一位 x 用户还将 Karpathy 的脚本方案成功“产品化”了。她推出了一款名为：Claudeopedia（Claude 百科）的产品，并说明了她构建该产品的几大步骤，她写道：
- 我采纳了 @karpathy 的 “llm-wiki” 构想（这占了本项目 90% 的功劳，所以大头要归功于 Karpathy）；
- 结合了过去 30 天的技能（感谢 @mvanhorn 的灵感）；
- 新增了一个 /wiki 技能，支持截图和下载参数，能更飞速地传输原始素材；
- 构建了一个交互式可视化界面来搜索我的知识库（甚至带日期范围，可以对比知识随时间演进的变化！）；
- 设置了一个“质疑自我假设”的定时任务（cron job），自动将我最近的随笔和客户邮件与 Wiki 内容进行比对复核。

目前这一切都在 Obsidian 中运行。包括测试在内，所有这些都是在这个周末搞定的。我会继续添加更多功能。我重点构建的是：企业级 AI。我已经非常期待了。

![](https://mmbiz.qpic.cn/mmbiz_png/hLLZnAbUwNjsWq2E6yZRVTiciaMuwaI1ibGpsK0mgARRdtibI9yyu4jCe89Oe7MBzxMtzOVMKiaB3OXyBKeXkmuh11aRA1t5micqm2dFclLMn6XRQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=10)

整体来看，Karpathy 提出的这一方法的意义不仅在于提升效率，更在于重构知识工作的底层逻辑。当大模型能够持续维护并扩展一个结构化知识体系时，传统意义上的“笔记”正在演变为一种动态系统。对于个体而言，这意味着可以将认知能力部分外包给机器；而对于行业而言，这也预示着一个潜在的新产品方向——将“知识编译”本身，作为核心能力进行产品化。

在信息不断膨胀的时代，这种从“存储信息”到“演化知识”的转变，或许正是下一阶段 AI 应用的重要突破口。

> 原文：[Karpathy 亲手终结了RAG的草莽时代](https://mp.weixin.qq.com/s/y0JLrC_Af9X0cA_t08ymjg)
