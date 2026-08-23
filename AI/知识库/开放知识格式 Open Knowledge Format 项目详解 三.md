# 开放知识格式（Open Knowledge Format）项目详解：为什么要做、能做什么、怎么用

> 项目地址：https://github.com/GoogleCloudPlatform/open-knowledge-format
> 规范版本：OKF v0.2
> 系列文章：[入门介绍（一）](开放知识格式%20Open%20Knowledge%20Format%20入门介绍%20一.md)、[规范指南（二）](开放知识格式%20Open%20Knowledge%20Format%20规范指南%20二.md)

## 一、这个仓库里到底有什么

先说清楚一件事：**open-knowledge-format 这个仓库的主体不是代码，而是一份格式规范**。

仓库的核心贡献是 `SPEC.md` —— 开放知识格式（Open Knowledge Format，简称 OKF）v0.2 的完整规范。OKF 是一种通用的、厂商中立的格式，用于把知识表示为**带 YAML frontmatter 的纯 Markdown 文件**。它不绑定任何特定的智能体、框架、模型提供商或服务系统。目标只有一个：

> 任何人都能生产 OKF，任何人都能消费 OKF。

围绕这份规范，仓库还提供了三样"让格式变得可触摸"的东西：

1. **参考生产智能体（reference_agent）**：一个概念验证级别的 Python 智能体，演示"如何自动生产 OKF 知识包"——从 BigQuery 元数据出发，再让 LLM 像爬虫一样抓取权威文档做增量丰富。
2. **可视化工具（visualize）**：把任意 OKF 知识包渲染成一个自包含的交互式 HTML 关系图，单文件、无后端、打开即用。
3. **四个现成的示例知识包（bundles/）**：GA4 电商数据集、Stack Overflow 公共数据集、Bitcoin 区块链数据集、Acme Retail 模拟场景。下载仓库就能直接浏览，每个都附带 `viz.html` 可视化页面。

用项目自己的话说：**格式本身才是贡献；智能体和可视化工具存在的意义，是让格式在"生产"和"消费"两端都变得具体可感。**

## 二、为什么要创建 OKF：从"知识碎片化"说起

### 2.1 问题：智能体不缺模型能力，缺上下文

在构建 AI 智能体时，限制模型能力的往往不是模型本身，而是缺少正确的上下文。当智能体需要回答"如何根据事件流计算周活跃用户数"时，它需要的知识散落在：

- 各个厂商互不兼容的元数据目录（各有私有 API 和 SDK）；
- 内部 Wiki、共享云盘、PDF 报告；
- 代码注释、文档字符串、Notebook 单元格；
- 少数资深工程师的头脑中。

结果是：每个智能体团队都在重复解决同一个上下文组装问题，每个目录厂商都在重复设计相同的数据模型，而知识本身被锁死在创建它的系统里。

### 2.2 契机：LLM Wiki 模式爆发，但各自为政

Andrej Karpathy 的 LLM Wiki 实践（详见本知识库另一篇笔记《Karpathy 亲手终结了RAG的草莽时代》）让"用 LLM 持续编写和维护 Markdown 知识库"的模式爆火。类似的模式正以各种形态反复出现：

- 与编程智能体相连的 Obsidian 知识库；
- `AGENTS.md`、`CLAUDE.md` 这类约定文件；
- 包含大量 `index.md` 和 `log.md` 供智能体先读后做的代码仓库；
- 数据团队的"元数据即代码"仓库。

这些实践都很强大，**但它们在设计时从未考虑过彼此协作**：每家对"文档必须有哪些字段""保留文件名叫什么"都没有共识。Karpathy 的 Wiki、你团队的 Wiki、厂商导出的目录，看起来都很像——都是 Markdown + frontmatter + 交叉链接——却无法互相读取。

### 2.3 答案：缺的是格式，不是又一个服务

OKF 的创建目的可以概括为一句话：**给 LLM 时代的知识交换定义一个通用语言**。这个格式必须满足：

- 任何人都能生产——人手写、任何框架的智能体（Google ADK、LangChain、自研）、现有目录的导出流水线（Dataplex、Unity Catalog、Collibra……）、甚至遍历数据库的脚本；
- 任何人都能消费——静态文件服务器、知识管理 UI（Obsidian、Notion、MkDocs）、把文件直接读进上下文的 LLM、搜索索引、图查看器；
- 跨工具、跨组织、跨时间迁移后依然有效；
- 和它所描述的代码一起待在版本控制里。

## 三、OKF 的核心设计：为什么选"Markdown + YAML"

选择"纯 Markdown 文件 + YAML frontmatter + 目录层级"这个看似朴素的组合，换来了一组服务型元数据库很难同时具备的特性：

| 特性 | 含义 |
| --- | --- |
| **人机双可读** | 读取内容不需要任何 SDK 或查询语言。工程师可以直接 `cat` 一个概念，LLM 可以原样读进上下文 |
| **天然版本可控** | 知识包就是一个 git 仓库：PR、逐行 diff、blame、评审流程开箱即用，知识整理变成常规软件工程活动 |
| **可移植、零锁定** | 知识包就是一个目录：打成 tarball 发送、托管在任何仓库、挂载在任何文件系统。你和你的元数据之间没有任何专有 API |
| **结构化与非结构化有意混合** | frontmatter 只放需要查询、过滤、索引的少数字段（`type`、`resource`、`tags`、`generated`、`status`）；正文放人和 LLM 真正会读的散文、Schema、示例查询 |
| **信任、来源、新鲜度是一等公民** | v0.2 把可查询信号放进 frontmatter：概念从哪来（`sources` 及按来源的可信度信号）、谁生产和确认了它（`generated`、`verified`，由此派生信任等级）、它是否仍然有效（`status`、`stale_after`）——智能体维护的语料因此无需定制运行时即可保持可信 |
| **最小主张、自由扩展** | 一小撮必填键保证互操作性，但知识包可以携带任意额外的 frontmatter 键和正文章节，而不会破坏消费者 |
| **与现有工具链兼容** | Notion、Obsidian、MkDocs、Hugo、Jekyll 本来就认 Markdown + YAML frontmatter，知识包无需定制 UI 即可浏览、编辑、渲染 |
| **渐进式披露** | 自动生成的 `index.md` 让智能体或人可以逐层浏览层级，而不必把整个知识包塞进上下文 |
| **图状而非树状** | 概念之间通过普通 Markdown 链接相连，表达比目录隐含的父子关系更丰富的关系 |

最终效果是：**参考智能体、消费智能体和人类，以他们协作源代码的同样方式，在同一批知识工件上协作。**

一句话记住 OKF 的设计哲学（规范原文）：

> 如果你会 `cat` 一个文件，你就能读 OKF；如果你会 `git clone` 一个仓库，你就能分发它。

## 四、应用场景：谁应该用 OKF

### 4.1 给 AI 智能体提供可信上下文（核心场景）

智能体回答问题前，与其每次都去搜索同一批文档、拼装同一批事实，不如给它一个持续演进的共享知识库。OKF 让这个知识库可以被任何框架的智能体直接消费——不需要向量数据库、不需要嵌入流水线，LLM 顺着 `index.md` 逐层定位即可。这正是 Karpathy 式"知识编译"思路在企业场景的标准化版本。

### 4.2 数据目录与元数据管理

把 BigQuery 数据集、表 Schema、指标定义、join 关系沉淀为 OKF 知识包。参考智能体已经演示了从 BigQuery 元数据自动生成概念文档的完整路径。数据团队的"元数据即代码"仓库可以直接迁移到这个格式，获得 git 评审、diff、blame 全套工程实践。

### 4.3 跨组织知识交换

当两家公司的智能体需要互相理解对方的数据资产时，私有 API 走不通，OKF 知识包可以直接作为交换单元：一个目录，打包发走，对方任何工具都能读。

### 4.4 可审计、可认证的关键指标（v0.2 新能力）

v0.2 引入的**认证计算（Attested Computation）**解决了一个尖锐问题："这个数字是按我们规定的方式算出来的吗？"财务收入、利润这类关键数字，可以各自成为一个 `type: Attested Computation` 的概念，携带运行时（`runtime`）、参数（`parameters`）、执行器（`executor`）和认证器（`attester`）。智能体只能填参数、不能改计算，消费者可以机械地验证"被认可的计算是否真的被执行"。适合财务、合规等对数字可追溯性要求极高的场景。

### 4.5 个人/团队知识库

OKF 与 Obsidian、Notion、MkDocs 天然兼容，Karpathy 式的个人 LLM Wiki 直接用 OKF 约定组织文件，就能获得跨工具可移植性——换工具时知识不用重写。

## 五、快速上手：三步跑通生产、浏览、消费

以下流程基于仓库 README，需要 Python 3.13。

### 5.1 安装

```bash
python3.13 -m venv .venv
.venv/bin/pip install --index-url https://pypi.org/simple/ -e .[dev]
```

凭证准备：

- **BigQuery**：`gcloud auth application-default login`，并设置计费项目（`gcloud config set project <id>`）。公共数据集可读，但查询字节数计入调用方项目账单。
- **Gemini**：设置 `GEMINI_API_KEY`（AI Studio），或使用 Vertex AI（设置 `GOOGLE_GENAI_USE_VERTEXAI=true`、`GOOGLE_CLOUD_PROJECT=<id>`、`GOOGLE_CLOUD_LOCATION=<region>`）。

### 5.2 生产：用参考智能体生成知识包

最小调用方式——指定一个 BigQuery 数据集和输出目录。网页抓取的种子 URL 需要显式提供；不提供种子（或传 `--no-web`）则只跑 BigQuery 阶段：

```bash
.venv/bin/python -m reference_agent enrich \
  --source bq \
  --dataset <project>.<dataset> \
  --web-seed-file <path/to/seeds.txt> \
  --out ./bundles/<name>
```

参考智能体分两个阶段（pass）工作：

1. **BQ 阶段**：仅用 BigQuery 元数据，为源系统声明的每个概念写一份 OKF 文档。
2. **Web 阶段**：把 LLM 当作自己的爬虫。它拿到种子 URL 列表，通过 `fetch_url` 工具抓取页面，并自行判断哪些出链值得跟进（标准：看起来像现有概念的权威文档）。对每个抓取的页面，智能体三选一：(a) 丰富一个或多个已有概念文档；(b) 单独铸造一份 `references/<slug>` 文档；(c) 跳过。

安全边界在工具内部强制执行：`--web-max-pages` 硬性限制抓取页数，`--web-allowed-host` 配置同域白名单过滤，智能体不可能失控越界。用 `--no-web` 可完全跳过网页阶段。

迭代打磨单个概念时，加 `--concept <type>/<name>`（例如 `--concept tables/events_`），可重复传多个。

### 5.3 浏览：生成可视化关系图

`visualize` 子命令把任意 OKF 知识包渲染为单个自包含的交互式 HTML——无后端、查看方零安装，用任何现代浏览器打开即可：

```bash
.venv/bin/python -m reference_agent visualize --bundle ./bundles/<name>
```

输出写入 `bundles/<name>/viz.html`。主要参数：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--bundle` | （必填） | 知识包根目录 |
| `--out` | `<bundle>/viz.html` | 输出 HTML 路径 |
| `--name` | 知识包目录名 | 查看器头部显示的标题 |

示例：输出到别处并自定义标题：

```bash
.venv/bin/python -m reference_agent visualize \
  --bundle ./bundles/crypto_bitcoin \
  --out /tmp/btc.html \
  --name "Bitcoin OKF"
```

查看器提供：

- **力导向关系图**：知识包内所有概念按类型着色（数据集、表、引用……），有向边取自 Markdown 正文中的交叉链接；
- **详情面板**：选中概念显示其 frontmatter（description、resource、tags）和渲染后的正文，内部链接被改写为查看器内导航；
- **"被引用"反向链接列表**：由链接图反向计算得出；
- **搜索框**（匹配标题、概念 id、标签）、类型过滤器和多种可切换的图布局（cose / concentric / breadth-first / circle / grid）。

实现上，HTML 把知识包作为 JSON 内嵌，图用 Cytoscape.js、Markdown 渲染用 marked（均从 CDN 加载）。数据不离开页面：知识包在生成时解析一次并序列化进文件。

### 5.4 消费：最朴素也最强大的方式

不需要任何工具——打开终端进入知识包目录，启动 Claude Code（或任何能读文件的智能体），直接提问即可。智能体按需读取文件、综合生成答案，还能按你的要求更新文档。

### 5.5 手写一个最小知识包

不想跑智能体？手写也只需几分钟。目录结构随意，每个概念一个文件，唯一硬性要求是 frontmatter 里有非空的 `type`：

```markdown
---
type: Metric
title: 周活跃用户数
description: 按事件流统计的周活跃用户口径。
tags: [growth, wau]
status: stable
generated: { by: human:yourname, at: 2026-08-20T10:00:00Z }
---

# Definition

以 `user_id` 去重统计 7 天滚动窗口内触发任意事件的用户数，
口径详见 [events 表](/tables/events.md)。
```

把它放进一个目录、提交 git，就是一个合规的 OKF 知识包。

## 六、示例知识包：开箱即学的教材

仓库 `bundles/` 目录提交了四个由参考智能体生产的真实知识包，每个都配套一份"配方"（`samples/<name>/`，含种子 URL 和确切的 enrich 命令）：

| 知识包 | 数据源 | 演练重点 |
| --- | --- | --- |
| `bundles/ga4/` | GA4 Google Merchandise Store 电商公共数据集 | 以 GA4 BigQuery Export 官方文档 URL 为种子 |
| `bundles/stackoverflow/` | Stack Overflow 公共数据集（Stack Exchange Data Dump 镜像） | 跨领域文档页面对多个概念的交叉丰富 |
| `bundles/crypto_bitcoin/` | Bitcoin 区块/交易公共数据集（bitcoin-etl 流水线） | 在正文中表达跨表外键关系 |
| `bundles/acme_retail/` | Acme Retail 模拟场景 | 综合示例 |

打开配方可以复现生产过程；打开知识包可以直接浏览结果；打开 `viz.html` 可以看关系图。想验证格式、学习最佳实践，这是最快的路径。

## 七、OKF v0.2 的关键演进（相对 v0.1）

v0.2 是次版本升级（规范 §12），核心主题只有一个：**当知识语料主要由机器生产时，如何让它保持可信**。新增能力：

- **来源溯源（provenance）**：`sources` 字段 + 按来源的可信度信号（`author`、`usage_count`、`last_modified`）+ `usage_window` 统计窗口；正文用脚注做逐条论断归因；
- **信任（trust）**：`generated`（谁写的）与 `verified`（谁确认的）分离记录，由 `verified` 派生三级信任等级（未验证 / 机器确认 / 人工复核）；
- **生命周期（lifecycle）**：`status`（draft / stable / deprecated）与 `stale_after`（绝对过时时刻）；
- **认证计算（Attested Computation）**：新概念类型，配套 `runtime`、`parameters`、`computation`、`executor`、`attester` 契约字段，让"数字是否按认可的方式算出"可以被机械验证；
- **参与者约定（actor convention）**：`<producer>/<version>`、`human:<id>`、`process:<id>` 三种身份格式。

破坏性变更只有两处（都有回退机制）：`timestamp` 被 `generated.at` 取代；正文 `# Citations` 列表被 `sources` frontmatter 取代。

## 八、参与贡献：生态需要你的生产者和消费者

OKF 的价值取决于采用它的参与者数量，而不是谁拥有它。规范采用版本化管理，明确支持向后兼容的持续演进。可以参与的方向：

1. **写一个生产者**：为你的源系统、数据库、文档站点或内部目录编写导出流水线；
2. **写一个消费者**：查看器、搜索索引，或能基于知识包推理的智能体；
3. **用参考实现试跑自己的数据**：`enrich` + `visualize` 两个子命令即可起步；
4. **提交 Issue、发起 PR、提出扩展建议**；
5. **运行测试**：`.venv/bin/pytest`。

## 九、总结

open-knowledge-format 做的事情，用三句话概括：

1. **它把 Karpathy 式的 LLM Wiki 实践，沉淀成一份厂商中立的最小规范**——Markdown + YAML frontmatter，唯一必填项是 `type`；
2. **它在 v0.2 回答了机器生产知识时代的核心问题**——来源可溯、信任分级、新鲜度可查、关键数字可认证；
3. **它刻意不做平台**——没有服务端、没有 SDK、没有锁定，格式就是生产者与消费者之间的契约，两端工具都可以独立替换。

如果你正在构建知识目录、智能体上下文系统、企业 Wiki 或任何 AI 知识基础设施，不妨从 clone 仓库、浏览一个示例知识包开始。

> 参考链接：
> - 项目仓库：https://github.com/GoogleCloudPlatform/open-knowledge-format
> - OKF v0.2 规范：https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md
> - Karpathy LLM Wiki Gist：https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
