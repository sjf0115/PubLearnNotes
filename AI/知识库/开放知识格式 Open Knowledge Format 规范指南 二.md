> 原文：[GoogleCloudPlatform/open-knowledge-format · SPEC.md](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md)
> 规范版本：v0.2

> **版本 0.2**

Open Knowledge Format(OKF) 是一种开放、对人类和智能体都友好的 **知识** 表示格式，用于描述围绕数据与系统的元数据、上下文和经过整理的洞察。它既可以由人编写，也可以由智能体生成；既能在组织之间交换，也能被人和智能体共同使用。

这种格式刻意保持极简：一个由带 YAML 前置元数据的 Markdown 文件组成的目录。它没有 Schema 注册中心，没有中央管理机构，也不要求使用特定工具。只要能用 `cat` 查看文件，就能阅读 OKF；只要能用 `git clone` 克隆仓库，就能分发 OKF。

---

## 1. 动机

面向 AI 智能体的知识表示领域正在快速演进，同时也出现了许多彼此不兼容的约定。OKF 主张使用普遍可访问、成熟稳定的格式来表示知识，并满足以下特征：
- **可读**：人类无需借助工具即可阅读。
- **可解析**：智能体无需专用 SDK 即可解析。
- **可比较差异**：可以在版本控制系统中查看变更。
- **可移植**：可以跨工具、跨组织、跨时间使用。

如今，知识语料库越来越不是一次编写后仅供读取的静态内容，而是由智能体 **持续编写和维护**。当大多数概念由机器生成时，消费者需要回答一些仅靠普通 Markdown 加前置元数据约定无法作为一等信息表达的问题：
- 它基于什么创建，又是如何验证的？（**来源追溯**）
- 我应该在多大程度上信任它？（**信任**）
- 它现在仍然正确吗？（**时效性**）
- 它是当前版本吗？（**生命周期**）
- 这个数值是否按规定方式计算得出？（**证明**）

OKF v0.2 将来源追溯、信任、生命周期和证明提升为一等信息，同时仍对内容模型保持最小约束。它只标准化一组使知识语料库能够自描述所必需的结构约定，其他内容均由生产者决定。

### 1.1 目标

- 定义一种通用格式，使 **生产者**（人、智能体、导出流水线）都能写入。
- 指导 **消费者**（智能体、UI、搜索索引、确定性代码）如何读取和遍历知识。
- 促进知识在系统和组织之间 **交换**。
- 标准化一小部分前置元数据字段，使智能体维护的语料库具备 **可信性**，但不规定任何运行时。

### 1.2 非目标

- 定义固定的概念类型分类体系。
- 规定存储、服务或查询基础设施。
- 取代特定领域的 Schema（Avro、Protobuf、OpenAPI 等）。OKF 只*引用*它们，而不将其纳入自身规范。
- 为执行器或证明器所指向的代码规定打包或调用标准。OKF 固定的是接口，而不是打包方式。

---

## 2. 术语

- **知识包（Knowledge Bundle，简称 bundle）**：自包含、分层组织的知识文档集合，是分发的基本单元。
- **概念（Concept）**：知识包中的一个独立知识单元，以一份 Markdown 文档表示。它可以描述实体资产（如数据表、API）、抽象概念（如指标、业务流程），或介于两者之间的任何事物。
- **概念 ID（Concept ID）**：概念文件在知识包内的路径，不含 `.md` 后缀。
- **前置元数据（Frontmatter）**：Markdown 文件顶部由 `---` 分隔的 YAML 元数据块。
- **正文（Body）**：文件中前置元数据之后的所有内容。
- **链接（Link）**：从一个概念指向另一个概念的标准 Markdown 链接，用于表达隐式父子层级之外的关系。
- **来源（Source）**：概念所依据的材料，可以位于知识包内部或外部，记录在前置元数据的 `sources` 字段中。
- **来源追溯（Provenance）**：概念所依据的一组来源。
- **可信度信号（Credibility signal）**：用于推断信任程度的客观、来源级事实，如 `author`、`usage_count`、`last_modified`。OKF 记录信号，而不记录结论（见 §5.1）。
- **参与者（Actor）**：标识动作执行者的字符串。智能体采用 `<producer>/<version>` 约定，人采用 `human:<id>`，自动化进程采用 `process:<id>`（见 §7）。
- **信任层级（Trust tier）**：根据概念的 `verified` 字段推导出的级别：未验证、机器确认或人工审核（见 §5.3）。
- **可证明计算（Attested Computation）**：携带受认可数值计算方式的概念（`type: Attested Computation`），使消费者能够确认该数值确实通过运行这项计算产生（见 §10）。
- **执行器（Executor）**：执行计算并返回执行凭证的运行说明或代码（见 §10.2）。
- **执行凭证（Receipt）**：一次运行返回的证据，其结构由 `executor.receipt` 定义。它是运行时制品，不存储在知识包中（见 §10）。
- **证明器（Attester）**：检查执行凭证并返回判定结果的确定性代码，不使用 LLM（见 §10.2）。

---

## 3. 知识包结构

知识包是一棵由 Markdown 文件组成的目录树。目录结构与领域无关，生产者可以按照所记录知识的特点组织概念。
```text
path/to/bundle/
  index.md                      # 可选。用于渐进式披露的目录清单。
  log.md                        # 可选。按时间顺序记录更新历史。
  <concept>.md                  # 位于知识包根目录的概念。
  <subdirectory>/               # 子目录用于对概念分组。
    index.md
    <concept>.md
    <subdirectory>/
      ...
```

知识包 **可以** 通过以下方式分发：
- Git 仓库（推荐，因为它可以提供历史、归属信息和差异比较）。
- 目录的 tar 或 zip 压缩包。
- 大型仓库中的一个子目录。

### 3.1 保留文件名

以下文件名在层级结构的任何位置都有明确定义，**不得** 用于概念文档：

| 文件名 | 用途 |
|---|---|
| `index.md` | 目录清单 |
| `log.md` | 更新历史 |

其他所有 `.md` 文件均为概念文档。

标签仍通过前置元数据中的 `tags` 字段作为一等概念存在。OKF并未规定一种单独的文件格式来聚合不同标签的文档；如果需要实现按标签浏览的功能，它可以在读取 OKF 文档的时候，通过扫描每个文件开头的 YAML 元数据，临时生成这个标签聚合视图。

---

## 4. 概念文档

每个概念(Concept)都是一个 UTF-8 编码的 Markdown 文件，由两部分组成：
- **一个 YAML 格式的元数据块(frontmatter)**：文件开头以单独一行 `---` 起始，并以单独一行 `---` 结束。
- **一个 Markdown 格式的正文(body)**：包含自由格式的内容。

### 4.1 元数据块

```yaml
---
type: <类型名称>                   # 必填
title: <可选显示名称>
description: <可选的单行摘要>
resource: <底层资产可选的规范 URI>
tags: [<标签>, <标签>, ...]         # 可选
# ……信任、生命周期、来源追溯和计算字段组
# ……生产者定义的其他键值对
---
```

- **必填字段：**
  - `type`：
    - 标识概念种类的短字符串。消费者用它进行路由、过滤和展示。示例值包括：`BigQuery Table`、`BigQuery Dataset`、`API Endpoint`、`Metric`、`Playbook`、`Reference`、`Attested Computation`。
    - 类型值 **不** 进行集中注册。生产者 **应** 选择描述清楚、含义明确的值；消费者 **必须** 妥善兼容未知类型，通常将其作为通用概念处理。
    - `type` 是唯一个必填的键，即只包含 `type` 的概念也完全符合规范。
- **推荐字段：**
  - `title`：人类可读的显示名称。如果省略，消费者 **可以** 根据文件名生成标题。
  - `description`：一个概括概念(Concept)的单个句子，供 `index.md` 生成器、搜索摘要和预览使用。
  - `resource`：唯一标识概念(Concept)所描述底层资产的 URI。对于描述抽象思想而非物理资源的概念，该字段可省略。
  - `tags`：用于跨领域分类的短字符串 YAML 列表。
  - 还可以包含可选的 **来源追溯**、**信任** 和 **生命周期** 系列字段，以及已证明计算使用的 **计算** 字段。
- **扩展：**
  - 生产者 **可以** 加入任意其他键。
  - 消费者在往返读写时 **应** 保留未知键，并且 **不得** 因存在无法识别的字段而拒绝文档。

### 4.2 正文

正文采用标准 Markdown。生产者 **应** 优先使用结构化 Markdown（标题、列表、表格、围栏代码块），而非无结构的自由文本，因为结构既便于人类阅读，也有助于智能体检索。正文部分没有必需的结构。以下标题具有常规含义，并在适用时应该使用：

| 标题 | 用途 | 核心目的 |
|---|---|---|
| `# Schema` | 对资产列(字段)进行结构化描述。 | 描述数据资产的结构 |
| `# Examples` | 具体使用示例，通常采用围栏代码块。 | 提供具体的使用方法 |
| `# Computation` | 可证明计算中受认可的计算。 | 记录可信的计算逻辑 |

#### 4.2.1 Schema

如果您的概念（Concept）描述的是一个数据资产（如一张数据库表、一个 BigQuery 数据集、一个 API 返回的 JSON 结构或一个 CSV 文件），那么您应该在正文中使用 `# Schema` 这个标题，并在其下方列出该资产所有字段的详细信息。虽然 OKF 规范对此没有强制格式（因为正文是自由的），但社区通常推荐使用 Markdown 表格 来呈现这种结构化描述，例如：
```markdown
# Schema

| 列 | 类型 | 说明 |
|---|---|---|
| `order_id` | STRING | 全局唯一的订单标识符。 |
| `customer_id` | STRING | 指向 [customers](/tables/customers.md) 的外键。 |
| `total_usd` | NUMERIC | 以美元计价的订单总额。 |
| `placed_at` | TIMESTAMP | 客户提交订单的时间。 |
```

#### 4.2.2 Examples

用于提供概念的具体使用示例，以帮助读者（尤其是 AI Agent）快速理解如何应用该知识。规范明确建议，此部分的内容通常采用围栏代码块（fenced code blocks） 来呈现。这能确保示例的格式清晰、易于复制和解析。

#### 4.2.3 Computation

这个是 OKF v0.2 引入的核心特性 “已证明计算”（Attested Computation） 紧密相关。它的核心目标是确保一个数值或结果是通过官方认可（sanctioned）的方式计算出来的，而非由 AI 随意编造的。

专门用于 `type: Attested Computation` 的概念文档中，用来记录其受认可的计算逻辑。通常会包含计算本身的具体内容，可以是一个 SQL 查询、一段 Python 代码或一个完整的脚本路径。一个“已证明计算”自身就是一个独立的概念文档（`type: Attested Computation`）。当一个指标（Metric）或数据表（Table）需要引用这个计算结果时，只需通过普通的 Markdown 链接指向这个计算文档即可。这种设计将“数值的定义”与“数值的计算方式”解耦，保证了计算逻辑的可复用性和可审计性。

### 4.3 示例

#### 4.3.1 示例：绑定到资源的概念

```markdown
---
type: BigQuery Table
title: 客户订单
description: 每行代表一笔来自任意渠道的已完成客户订单。
resource: https://console.cloud.google.com/bigquery?p=acme&d=sales&t=orders
tags: [sales, orders, revenue]
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-05-28T14:30:00Z }
---

# Schema

| 列 | 类型 | 说明 |
|---|---|---|
| `order_id` | STRING | 全局唯一的订单标识符。 |
| `customer_id` | STRING | 指向 [customers](/tables/customers.md) 的外键。 |
| `total_usd` | NUMERIC | 以美元计价的订单总额。 |
| `placed_at` | TIMESTAMP | 客户提交订单的时间。 |

# Joins

通过 `customer_id` 与 [customers](/tables/customers.md) 关联。
```

#### 4.3.2 示例：未绑定到资源的概念

```markdown
---
type: Playbook
title: "事故响应：数据时效性告警"
description: 对订单流水线时效性告警进行分诊的步骤。
tags: [oncall, incident]
generated: { by: human:ahormati, at: 2026-04-12T09:00:00Z }
---

# Trigger

当 `orders` 落后于预期 SLA 超过 30 分钟时，触发时效性告警。参见 [orders 表](/tables/orders.md)。

# Steps

1. 检查[数据摄取作业仪表盘](https://example.com/dash)。
2. ……
```

---

## 5. 来源追溯、信任与生命周期

元数据块 frontmatter 的系列字段(来源追溯、信任与生命周期)使消费者可以直接根据元数据块回答“内容来自哪里”、“应该在多大程度上信任它”以及“它是否仍然有效”。所有字段均为可选，字段的缺失本身也带有含义：一个未经验证的概念与一个已验证的概念是可以区分的，但绝不会因此被拒绝。

OKF 中所有时间戳类型的键均采用带明确 UTC 偏移量的 ISO 8601 日期时间，例如 `2026-06-30T14:00:00Z`。

### 5.1 来源追溯：`sources`

`sources` 记录了一个概念所来源的资料，这些资料可以位于该知识包内部或外部：
```
sources:
  - id: ga4-schema
    resource: https://developers.google.com/analytics/bigquery/export-schema
    title: GA4 BigQuery 导出 Schema
    author: team:ga4-docs
    usage_count: 5000
    last_modified: 2026-05-30T00:00:00Z
usage_window: { from: 2026-06-01T00:00:00Z, to: 2026-06-30T00:00:00Z }
```

每个 `sources` 包括：
- `resource`：条目中的 **必填** 字段。可以指向消费者能够访问的具体工件（可以是绝对 URL、知识包相对路径，或 `references/` 子目录中的路径），也可以表示消费者无法直接访问的整体或范围描述符，例如“BigQuery 项目 X 中的所有查询”。
- `id`：可选。用于归因单个声明（见下文）的稳定键。当正文中引用了该来源时，应该提供此字段。
- `title`：可选。人类可读的来源标签。
- 可选的 **可信度信号**： `author`、`usage_count` 和 `last_modified`，详见下文。

**可信度信号：** OKF 记录客观的、基于每个来源的信号，使消费者能够通过评估来源来判断概念的 **可信程度**。它不存储可信度分数（credibility score）：因为分数具有主观性，无法在消费者之间移植，而且会随时间失效。可信度是从这些信号中推断（inferred）出来的，方式与信任层级（trust tiers）相同，而不是直接存储。每个信号都是可选的，位于 `sources` 条目中：
- `author`：谁或什么产生了该来源，遵循参与者约定（§7），属于权威性信号。
- `usage_count`：在 `usage_window` 时间窗口内，该资源被使用（仪表盘查看、查询执行、页面阅读）的次数。这是一个采用度和活跃度信号。对于单个工件，它表示该工件自身的使用次数；对于范围描述符，它表示范围内涉及该概念的使用次数。
- `last_modified`：来源自身最后变更的时间，这是一个新鲜度信号。区别于 `generated.at`（参见 §5.2），后者记录的是概念撰写的时间。
- `usage_window`：作为 `sources` 的同级字段只写一次，它为每个 `usage_count` 划定一个 `{ from, to }` 日期时间范围。单个条目 **可以** 携带自己的 `usage_window` 来覆盖共享的窗口。

`usage_count` 是一种粗粒度信号。它适合比较来源是否活跃、数量级差异，以及同一来源随时间的历史变化，但不适合在不同类型来源之间进行精确排名：定时查询的执行次数与人主动查看仪表盘的次数并不具有相同权重。消费者 **应** 将它理解为活跃度和趋势，而不是分数。

血缘关系通过链接表达，而不是专用字段。当 `resource` 指向另一个 OKF 概念时，知识包图中已经存在派生关系边（§6），因此消费者 **可以** 递归读取该来源自身的 `sources`，让可信度沿关系传播。外部叶子来源只携带自身信号。更深层的血缘关系，例如显式的外部 `derived_from` 或数据血缘，不在 v0.2 范围内。

**逐项声明归属：** 如需将某个具体声明归因到特定来源，请使用 Markdown 脚注，其标签（label）即为 `sources[]` 中的 id：
```markdown
`events_` 表每天按 `events_YYYYMMDD` 分片。[^ga4-schema]

[^ga4-schema]: GA4 BigQuery 导出 Schema
```

脚注标签是关联 `sources` 的键。消费者应通过匹配条目解析来源归属，而不是解析脚注文本。标签采用键而非位置索引（如 `sources[0]`），因为智能体会不断改写这些文档：列表一旦重新排序，位置索引就会悄无声息地指向错误来源，而稳定的 `id` 不受排序影响。

### 5.2 信任：`generated` 与 `verified`

> 两者相互独立，因为概念的 **编写者** 不一定是其 **确认者**。

`generated` 记录当前内容是如何产生的，关注的是这段内容是怎么来的：
```
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-06-20T22:53:05Z }
```
- `generated.by`：`generated` 的 **必填** 字段，值为参与者，遵循第 7 节的“参与者约定”。
- `generated.at`：ISO 8601 日期时间，标记内容上一次有意义的变更。消费者用它来区分“近期的编辑”和“过时的事实”。特意强调了 "last meaningful change"（最后一次有意义的变更），而非简单的"文件最后保存时间"。

`verified` 记录谁或什么（即哪个主体）已根据其来源（`sources`）或资源（`resource`）对内容进行了确认，关注的是这段内容可不可信（相对于原始来源）：
```
verified:
  - { by: human:ahormati, at: 2026-06-25T09:00:00Z }
  - { by: process:finance-nightly, at: 2026-06-26T02:00:00Z }
```
- `verified`：一个验证事件列表，每个事件包含 by（一个参与者）和 at（一个 ISO 8601 日期时间）。多个条目表示相互独立的检查，例如人工签批加夜间自动化流程。最新的 `at` 表示“最近一次验证时间”。
- `verified` 独立于 `generated.at`：内容可能发生变更但未重新确认，事实也可能在内容未重新生成时再次得到确认。
- 单个验证者 **可以** 直接写成一个不带列表短横线的 `{ by, at }` 映射。消费者 **必须** 将这种视为仅含一个元素的列表：
```
verified: { by: human:ahormati, at: 2026-06-25T09:00:00Z }
```

### 5.3 信任层级

消费者根据 `verified` 推导信任层级，由低到高依次为：
- 没有 `verified` 键 ⇒ **未验证（unverified）**。
- 由非人类参与者（仅限 actor 类型）执行 `verified` ⇒ **机器确认（machine-confirmed）**。
- 由 `human:<id>` 参与者执行 `verified` ⇒ **人工审核（human-reviewed）**。

一个没有任何信任相关 `frontmatter` 的概念仍然是可消费的；消费者绝不能拒绝它（参见第11节）。信任层级是建议性信号，而非访问控制。

### 5.4 生命周期：`status`

描述的是概念在其生命周期中的成熟度阶段：
```
status: stable        # draft | stable | deprecated
```
- `draft`（草稿）：尚未经过审核，可能不完整。
- `stable`（稳定）：默认状态；可供使用。
- `deprecated`（已弃用）：为保留链接和历史记录而保留；不再是最新的。

缺少 `status` ⇒ `stable`。


### 5.5 生命周期：`stale_after`

```
stale_after: 2026-09-23T00:00:00Z   # 在此时刻及之后，内容视为过时
```
可选，表示一个绝对的时间点。当当前时间（now）大于或等于 stale_after 时，该概念被视为已过时（stale）。它是一个绝对的时间点，而非相对的 TTL（生存时间），这使得判断是否过时仅需进行一次简单的时间比较，而无需参考该概念被读取的时间。

---

## 6. 交叉链接与路径

### 6.1 概念之间的链接

概念**可以**使用标准 Markdown 链接指向其他概念，支持两种形式：

- **绝对路径（知识包相对路径）**：以 `/` 开头，相对于知识包根目录解释。这是**推荐**形式，因为文档在其子目录内移动时链接仍然稳定。

  ```markdown
  关联键请参见 [customers 表](/tables/customers.md)。
  ```

- **相对路径**：标准 Markdown 相对路径。

  ```markdown
  请参见[相邻概念](./other.md)。
  ```

从概念 A 到概念 B 的链接表示一种*关系*。具体关系类型，如父子关系、引用、关联或依赖，由链接周围的文本表达，而非链接本身。构建图视图的消费者通常将所有链接视为无类型关系的有向边。

消费者**必须**容忍断开的链接：如果链接目标在知识包中不存在，并不表示该链接格式错误，它可能只是指向尚未编写的知识。

### 6.2 路径类型字段

多个字段可以表示路径或 URI：`resource`、`sources[].resource`、`computation`、`executor.resource` 和 `attester.resource`（§10）。`sources[].resource` 也可以是范围描述符（§5.1），此时它不是路径。每个路径类型字段都接受：

- 绝对 URL，例如 `https://...`；
- 以 `/` 开头的知识包相对路径；
- 相对路径，例如 `../computations/revenue.md`。

### 6.3 `references/` 约定

按照约定，`references/` 子目录用于将外部材料、运行说明或代码映射为知识包内的一等概念。来源、执行器和证明器通常指向此目录，例如 `references/attesters/revenue.py`。这只是命名约定，不是强制要求。

---

## 7. 参与者约定

记录身份的字段（`generated.by`、`verified[].by`）统一采用以下参与者约定：

- 智能体和工具使用 `<producer>/<version>`，例如 `reference_agent/gemini-2.5-pro`。
- 人使用 `human:<id>`，例如 `human:ahormati`。
- 自动化进程使用 `process:<id>`，例如 `process:finance-nightly`。

消费者在划分信任层级时（§5.3）依赖 `human:` 前缀，因此生产者对人工编写或人工确认的内容**必须**使用该前缀。

---

## 8. 索引文件

`index.md` 文件**可以**出现在任意目录中，包括知识包根目录。它列出目录内容，以支持**渐进式披露**：让人或智能体先了解有哪些内容，再打开单独的文档。

索引文件不包含前置元数据，只有一个例外：知识包根目录的 `index.md` **可以**包含 `okf_version` 键（§12）。正文使用一个或多个章节，每个章节通过标题对概念分组：

```markdown
# 章节或分组标题

* [标题 1](relative-url-1) - 条目 1 的简短说明
* [标题 2](relative-url-2) - 条目 2 的简短说明

# 另一章节

* [子目录](subdir/) - 子目录的简短说明
```

条目**应**包含被链接概念前置元数据中的 `description`。生产者**可以**自动生成 `index.md`；如果不存在，消费者**可以**动态生成。

---

## 9. 日志文件

`log.md` 文件**可以**出现在层级结构的任意位置，用于记录该范围内的变更历史。其格式是按日期分组的扁平条目列表，最新内容位于最前：

```markdown
# 目录更新日志

## 2026-05-22
* **更新**：新增 [Customer Metrics](/tables/customer-metrics.md) 的 BigQuery 表参考。
* **创建**：建立 [Dataplex Playbook](/playbooks/dataplex.md)。

## 2026-05-15
* **初始化**：创建基础目录结构。
```

日期标题**必须**采用 ISO 8601 `YYYY-MM-DD` 格式。日志条目使用自然语言；开头的加粗词（`**更新**`、`**创建**`、`**弃用**`）只是一种约定，不是强制要求。

---

## 10. 可证明计算概念

可证明计算概念不仅描述一个值的*含义*，还携带一种受认可的*计算*方式，使消费者能够确认智能体运行了指定计算，而不是自行临时编写计算逻辑。来源追溯（§5.1）回答“这项声明来自哪里”；证明回答“这个数值是否按我们规定的方式生成”。OKF 记录计算及其检查方式，但自身不执行任何操作。

### 10.1 一项计算就是一个独立概念

受认可的计算是一个 `type: Attested Computation` 的独立概念。需要该值的概念（如 `Metric`、`BigQuery Table`）通过普通 Markdown 链接指向它（§6）。将计算建模为独立概念有三个原因：

- **`runtime` 定义 `parameters` 的含义。** 参数可能是 SQL 绑定变量、dbt var 或 Python 参数，具体取决于运行时。将 `runtime` 和 `parameters` 放在同一前置元数据中，可以让绑定语义一目了然。
- **一项计算，多个消费者。** 同一项计算可以支持指标、仪表盘概念和报表；将其建模为概念后，只需定义一次即可复用。
- **信任状态属于单项计算。** `verified`、`stale_after` 和单个 `attester` 描述的是同一项计算。收入、利润和利润率需要分别验证和证明，因此应建模为三个概念，而不是同一前置元数据中的三个条目。

### 10.2 契约字段

契约就是概念的顶层前置元数据。除来源追溯、信任和生命周期字段组（§5）外，可证明计算概念还包含：

- `runtime`：此类型的**必填**字段。它说明如何运行计算，从而决定执行器和证明器如何解释计算，以及 `parameters` 的含义。示例值：`bigquery`、`postgres`、`dbt`、`python`、`Looker`。
- `parameters`：智能体可以填充的具名、强类型参数列表。每个条目为 `{ name, type, required }`。绑定语义取决于 `runtime`。
- `computation`：可选。指向计算文件的路径（§6.2），用于代替正文中的内联围栏代码块（见 §10.3）。缺失时，正文 `# Computation` 下的代码块就是计算内容。
- `executor`：说明如何运行计算。`resource` 指向运行说明或代码，由运行程序（智能体或确定性消费者代码）遵循；`receipt` 声明一次运行必须返回的字段，即证明器检查的证据，例如 BigQuery `job_id` 和作业实际执行的 SQL。
- `attester`：确定性检查。`resource` 指向接收执行凭证并返回判定结果的代码（不使用 LLM），预期在消费者一侧运行。

`resource` 背后的内容可以是 Skill、脚本或容器，这是打包方式的选择；OKF 固定接口，而不固定打包方式（§1）。

```markdown
---
type: Attested Computation
title: 财政年度收入
description: 根据财务部门定义计算的某财政年度确认收入。
status: stable
runtime: bigquery
parameters:
  - { name: year, type: integer, required: true }
executor:
  resource: references/skills/run-on-bq.md
  receipt: [job_id, executed_sql, result]
attester:
  resource: references/attesters/revenue.py
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-06-20T22:53:05Z }
verified: { by: human:ahormati, at: 2026-06-25T09:00:00Z }
stale_after: 2026-09-23T00:00:00Z
sources:
  - id: rev-policy
    resource: https://wiki.acme/finance/revenue-recognition
    title: 收入确认政策
---

# Computation

    SELECT SUM(amount) AS revenue
    FROM finance.recognized_revenue
    WHERE fiscal_year = @year

根据收入确认政策，该计算只绑定已声明的 `parameters`。[^rev-policy]

[^rev-policy]: 收入确认政策
```

### 10.3 计算内容

可以通过以下两种方式之一提供计算：

- **内联**：在正文 `# Computation` 下提供单个围栏代码块。适合与契约一起审核的短计算。
- **文件**：将 `computation` 设置为路径（§6.2），并省略正文代码块。适合较长或自动生成的计算，或者已经作为真实文件与非 OKF 工具共享的计算。

```yaml
runtime: bigquery
computation: references/computations/lib/revenue.sql
parameters:
  - { name: year, type: integer, required: true }
```

智能体**只能**为声明的 `parameters` 提供*值*，**不得**编写或编辑计算。将 `computation` 与参数值绑定为可执行制品是消费者的职责；证明器会独立重新生成相同绑定，并与实际运行内容进行比较。由于比较对象是执行凭证携带的展开、编译后制品（`executed_sql`、`compiled_sql`），重写查询、替换计算文件或修改依赖项都会导致检查失败。只开放强类型参数的接口，才能把“是否运行了受认可计算”转化为机械比较，而非主观判断。

### 10.4 使用计算的概念

一份文档通常不会只涉及一项计算。讨论收入、利润和利润率的损益表概览仍然可以作为一个可读概念，同时为每个数值链接一项可证明计算：

```markdown
---
type: Metric
title: 收入
description: 某财政年度的确认收入。
tags: [finance, revenue]
status: stable
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-06-20T22:53:05Z }
---

# 定义

确认收入是对归入该财政年度的记录中的 `amount` 求和，并通过[收入计算](../computations/revenue.md)得出。
```

由于每项计算都是独立概念，收入可以仍处于有效期内，而利润已经超过其 `stale_after`；每项计算也分别证明自身的运行。将它们放在一起只是目录组织选择，例如带 `index.md` 的 `computations/` 文件夹，而不是前置元数据层面的设计。

### 10.5 消费者如何使用可证明计算（资料性）

本小节仅提供资料，不属于规范性要求。以下运行时制品**不**存储在知识包中。

1. **发现**：通过 `type: Attested Computation` 发现计算。该前置元数据信号可以提升到 `index.md`；消费者既可以直接进入该概念，也可以从使用它的概念沿链接进入。
2. **加载**：从前置元数据加载契约，从正文或 `computation` 指定的文件加载计算。
3. **参数化**：智能体为已声明参数提供值。
4. **执行**：执行器运行绑定后的计算，并返回符合 `executor.receipt` 结构的执行凭证。
5. **证明**：消费者使用证明器检查执行凭证。证明器确认来源真实性（实际运行的计算等于 `computation` 与声明参数绑定后的结果，而不是智能体编写的 SQL）和结果保真度（显示值与执行凭证中的权威来源一致；应按作业 ID 重新读取，而不是直接采用智能体文本中的数值）。
6. **准入控制**：证明失败时拒绝展示；当 `now >= stale_after` 时发出警告或拒绝展示。成功时应呈现判定结果，例如提供作业日志链接，让信任状态清晰可见。

### 10.6 验证与证明的区别

`verified`（§5.2）与证明并不相同，两者都不可或缺：

- `verified` 确认*定义*是否仍然符合政策。它作用于文档级别，执行频率较低，并记录在知识包中。
- 证明确认某*一次运行*是否以受认可的方式生成了结果。它针对每次调用，在运行时执行，不存储在知识包中。

定义已经过时的概念仍可能顺利通过某次运行证明；刚刚验证过的定义也仍需在每次运行时执行证明。因此，两者都需要存在。

---

## 11. 一致性

知识包满足以下条件时，即**符合** OKF v0.2 规范：

1. 目录树中每个非保留的 `.md` 文件都包含可解析的 YAML 前置元数据块。
2. 每个前置元数据块都包含非空 `type` 字段。
3. 每个保留文件名（`index.md`、`log.md`）存在时，分别遵循 §8 和 §9 的结构。

当信任、生命周期、来源追溯或计算字段组存在时，生产者**应**遵循 §5 至 §10，消费者则：

- **必须**将裸 `verified` 映射视为单元素列表（§5.2）。
- **不得**因缺少任何可选字段组而拒绝概念（§5.3）。
- **应**仅根据本文规定的字段推导信任层级和过时状态；证明失败时，**应**明确呈现，而不是静默丢弃（§10.5）。

消费者**应**将其他所有约束视为软性指导。特别是，消费者**不得**因以下原因拒绝知识包：

- 缺少可选前置元数据字段。
- 存在未知 `type` 值。
- 存在未知的额外前置元数据键。
- 存在断开的交叉链接。
- 缺少 `index.md` 文件。

---

## 12. 版本管理

本文档规定 OKF **0.2** 版。修订版本采用 `<major>.<minor>` 格式：

- **次版本号**增加表示引入向后兼容的新增内容，如新的可选字段、新的约定章节标题。
- **主版本号**增加可能包含破坏性变更，如重命名必填字段、修改保留文件名。

知识包**可以**在根目录 `index.md` 的前置元数据块中使用 `okf_version: "0.2"` 声明目标版本，这是 `index.md` 中唯一允许出现前置元数据的位置。不理解所声明版本的消费者**应**尽最大努力尝试消费，而不是拒绝整个知识包。

### 已考虑但暂缓的内容

以下内容有意留待后续版本处理：

- 完整的运行时协议：执行凭证和判定结果的传输格式，以及围绕单次运行的证明生命周期。
- 证明器 ABI、可移植性和沙箱机制，可能与未来的服务化及 Skills 工作一并推进。
- 证明缓存。
- 语义层模板（Looker、dbt）。在这些模板中，证明器的比较对象将从 SQL 等价性转为模型与绑定等价性。

---

## 13. 相比 v0.1 的变更

v0.2 取代 OKF v0.1。根据 §12，它属于次版本升级，但包含下文明确指出的两项有意引入的破坏性变更，因为它们重命名或废弃了 v0.1 字段。v0.2 消费者仍可根据此处所述的回退规则消费 v0.1 知识包。

### 13.1 破坏性变更

- **`generated.at` 取代 `timestamp`。** 概念最后一次内容变更现在记录为 `generated: { by, at }`（§5.2）。缺少 `generated` 时，消费者**可以**回退读取旧版 `timestamp`。
- **`sources` 取代正文 `# Citations` 列表。** 来源追溯移至前置元数据（§5.1）。消费者**应**读取 `sources`，同时仍**可以**解析 v0.1 文档正文中的旧版 `# Citations` 列表。

### 13.2 增量变更

以下变更均为增量新增：新的可选键、一个新概念类型和一个新的约定标题。缺少这些内容时，文档就是普通的 v0.1 概念。

- 新增前置元数据字段组：`sources` 及其来源级可信度信号（`author`、`usage_count`、`last_modified`），以及同级字段 `usage_window`；`generated`、`verified`；`status`、`stale_after`（§5）。
- 新增概念类型 `Attested Computation` 及其计算键：`runtime`、`parameters`、`computation`、`executor`、`attester`（§10）。
- 新增约定正文标题 `# Computation`（§4.2）。
- 新增适用于 `generated.by` 和 `verified[].by` 的参与者约定（§7）。

其他所有内容均保持不变，包括知识包结构、保留文件名、必填字段 `type`、推荐字段 `title`/`description`/`resource`/`tags`、交叉链接、索引文件、日志文件和宽松的一致性要求。

---

## 附录 A：完整示例——损益表

下面通过一个知识包展示所有字段组。示例将包含收入和毛利润两个数值的损益表从 v0.1 迁移到 v0.2。

### v0.1 形式

所有内容位于一份文档中：两个数值共用一个概念；SQL 以自然语言正文形式存在，智能体可以读取、忽略或重写；引用是扁平列表；唯一的时间戳字段是 `timestamp`。

```markdown
---
type: Metric
title: 损益表（财政年度）
description: 某财政年度损益表的核心数值。
tags: [finance, income-statement]
timestamp: '2026-05-28T22:53:05+00:00'
---

# 定义
损益表报告某财政年度的收入和毛利润。

# 收入
确认收入是对归入该财政年度的记录中的 `amount` 求和：

    SELECT SUM(amount) AS revenue
    FROM finance.recognized_revenue
    WHERE fiscal_year = <year>

# 毛利润
根据成本分摊标准计算各业务分部的毛利润：

    SELECT gross_profit FROM fct_income_statement
    WHERE fiscal_year = <year> AND segment = <segment>

# 引用
- https://wiki.acme/finance/fpa-handbook
- https://wiki.acme/finance/revenue-recognition
- https://wiki.acme/finance/cost-allocation
```

### v0.2 形式

两个数值被拆分为可证明计算，并由一个叙述性概念链接。所有字段组均有值，而且两项计算被有意设置为不同状态，使同一个消费者得到两种不同判定。

```text
bundles/finance/
  metrics/income-statement.md      type: Metric（叙述并链接两项计算）
  computations/revenue.md          type: Attested Computation（runtime: bigquery）
  computations/profit.md           type: Attested Computation（runtime: dbt）
  references/skills/run-on-bq.md, run-dbt.md
  references/attesters/sql-equality.py, dbt-binding.py
```

`metrics/income-statement.md` 是可读文档；信任信息属于它所链接的计算，而不属于此文档：

```markdown
---
type: Metric
title: 损益表（财政年度）
description: 某财政年度损益表的核心数值。
tags: [finance, income-statement]
status: stable
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-06-20T22:53:05Z }
verified: { by: human:ahormati, at: 2026-06-25T09:00:00Z }
stale_after: 2026-12-31T00:00:00Z
sources:
  - id: fpa-handbook
    resource: https://wiki.acme/finance/fpa-handbook
    title: FP&A 报告手册
---

# 定义
损益表根据 FP&A 报告手册，报告某财政年度的[收入](../computations/revenue.md)和[毛利润](../computations/profit.md)。[^fpa-handbook] 每个数值都通过一项受认可且可证明的计算产生；本概念只负责叙述它们。

[^fpa-handbook]: FP&A 报告手册
```

`computations/revenue.md` 使用 BigQuery SQL，经过人工验证，仍处于有效期内，并由带有可信度信号的活跃仪表盘来源提供佐证：

```markdown
---
type: Attested Computation
title: 财政年度收入
description: 根据财务部门定义计算的某财政年度确认收入。
tags: [finance, revenue]
status: stable
runtime: bigquery
parameters:
  - { name: year, type: integer, required: true }
executor:
  resource: references/skills/run-on-bq.md
  receipt: [job_id, executed_sql, result]
attester:
  resource: references/attesters/sql-equality.py
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-06-28T14:00:00Z }
verified: { by: human:ahormati, at: 2026-06-25T09:00:00Z }
stale_after: 2026-12-31T00:00:00Z
sources:
  - id: rev-policy
    resource: https://wiki.acme/finance/revenue-recognition
    title: 收入确认政策
    author: team:finance-fpa
    last_modified: 2026-04-02T00:00:00Z
  - id: exec-rev-dash
    resource: dashboards/exec-revenue
    title: 管理层收入仪表盘
    author: team:finance-fpa
    usage_count: 5000
    last_modified: 2026-06-18T00:00:00Z
usage_window: { from: 2026-06-01T00:00:00Z, to: 2026-06-30T00:00:00Z }
---

# Computation

    SELECT SUM(amount) AS revenue
    FROM finance.recognized_revenue
    WHERE fiscal_year = @year

根据收入确认政策计算确认收入，[^rev-policy]并由管理层收入仪表盘提供佐证。[^exec-rev-dash]

[^rev-policy]: 收入确认政策
[^exec-rev-dash]: 管理层收入仪表盘
```

`computations/profit.md` 使用 dbt 模型，由自动进程验证，并且已超过 `stale_after`：

```markdown
---
type: Attested Computation
title: 财政年度毛利润
description: 根据成本分摊标准计算某财政年度各业务分部的毛利润。
tags: [finance, profit]
status: stable
runtime: dbt
parameters:
  - { name: year, type: integer, required: true }
  - { name: segment, type: string, required: true }
executor:
  resource: references/skills/run-dbt.md
  receipt: [run_id, compiled_sql, result]
attester:
  resource: references/attesters/dbt-binding.py
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-06-14T14:00:00Z }
verified: { by: process:finance-nightly, at: 2026-06-12T08:00:00Z }
stale_after: 2026-06-15T00:00:00Z
sources:
  - id: cost-alloc
    resource: https://wiki.acme/finance/cost-allocation
    title: 成本分摊标准
---

# Computation

    SELECT gross_profit
    FROM {{ ref('fct_income_statement') }}
    WHERE fiscal_year = {{ var('year') }}
      AND segment = {{ var('segment') }}

根据成本分摊标准计算各业务分部的毛利润。[^cost-alloc]

[^cost-alloc]: 成本分摊标准
```


> **原文**：[Open Knowledge Format (OKF) Specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
