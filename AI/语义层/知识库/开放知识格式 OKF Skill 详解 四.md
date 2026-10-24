# OKF Skill 技术详解：让每个编码智能体都掌握开放知识格式

> 项目地址：https://github.com/fabricioctelles/skills（okf-open-knowledge-format）
> 官网文档：https://okf.md/skill/
> 本文为个人学习笔记，以第一人称视角还原作者的创作思路，基于公开资料整理。

## 一、为什么我要做这个 Skill

Google Cloud 发布开放知识格式（OKF）之后，我一直在思考一个问题：**OKF 最优雅的地方是它"只是文件"，但这同时也是它的推广难题**——规范再好，如果没人帮用户迈出第一步，它就永远停留在 SPEC.md 里。

与此同时，Agent Skills 生态正在爆发。Claude Code、Codex、Cursor、Kiro、Windsurf 这些编码智能体都支持通过一份 SKILL.md 教会智能体新能力。我突然意识到：**OKF 和 Agent Skills 是天作之合**。

- OKF 的设计哲学是"无需 SDK、无需服务、会 cat 文件就能读"；
- Agent Skill 的设计哲学是"无需训练、无需部署、会读 Markdown 就能学会"。

两者都是纯文本层面的能力注入。于是我做了 OKF Skill：**一份教编码智能体掌握 OKF 的技能包**。你不需要写任何胶水代码，只要把 SKILL.md 交给你的智能体，它立刻就会创建、校验、丰富、转换 OKF 知识包。

一句话定位：

> OKF Skill 是 OKF 规范与编码智能体之间的翻译层——规范面向机器互操作，Skill 面向智能体教学。

## 二、它能做什么：六项能力

OKF Skill 为智能体提供六项核心能力：

| 能力 | 说明 |
| --- | --- |
| **Create（创建）** | 从零生成合规的 OKF 知识包 |
| **Validate（校验）** | 检查三条合规规则，按文件粒度报告错误和警告 |
| **Enrich（丰富）** | 补充 Schema、引用、交叉链接，填充推荐字段 |
| **Generate（生成）** | 自动创建 `index.md` 和 `log.md` 文件 |
| **Convert（转换）** | 把 Notion 导出、Obsidian 库或 CSV 转换为 OKF |
| **Serve（分发）** | 通过 kcmd CLI/MCP 把知识包推送到 Google Cloud Knowledge Catalog |

注意前五项都不需要任何外部依赖——这正是我坚持的设计约束：**Skill 的核心价值必须在一个纯文本编辑器和一个智能体之间闭环**，分发到 Knowledge Catalog 是唯一需要外部服务的环节，且它是可选的。

## 三、安装与接入：三种姿势

### 3.1 Claude Code / Kiro CLI：一条命令

```bash
# 添加到你的项目
npx skills add fabricioctelles/skills/okf-open-knowledge-format
```

或者手动 clone 引用：

```bash
git clone https://github.com/fabricioctelles/skills.git ~/.skills
```

然后在 `.claude/settings.json` 或 `AGENTS.md` 中登记：

```json
{
  "skills": ["~/.skills/skills/okf-open-knowledge-format/SKILL.md"]
}
```

### 3.2 Cursor / Windsurf：写进规则文件

在项目的 rules 或 instructions 文件中加一行：

```text
Read and follow: https://raw.githubusercontent.com/fabricioctelles/skills/main/skills/okf-open-knowledge-format/SKILL.md
```

### 3.3 任意智能体：直接指向原始 URL

任何能读文件的智能体，直接把这个 URL 喂给它即可：

```text
https://raw.githubusercontent.com/fabricioctelles/skills/main/skills/okf-open-knowledge-format/SKILL.md
```

三种姿势覆盖了从"技能注册表"到"纯文本引用"的完整光谱——**接入成本的下限就是一条 URL**，这也是我刻意保持的。

## 四、快速入门：四项核心能力详解

接入之后，所有操作都是自然语言。本节详细介绍前四项核心能力——Create、Validate、Enrich、Generate，掌握它们就足以完成从"零"到"合规知识包"的完整旅程。推荐的入门顺序：**Create → Enrich → Generate → Validate**（先建出来、再丰富、再补索引、最后校验）。

### 4.1 Create：从零创建知识包

**做什么**：根据你的描述生成完整的 OKF 知识包——目录结构、概念文档（frontmatter + 正文）、概念间交叉链接一步到位。

**怎么用**，直接对智能体说：

```text
"Create an OKF bundle documenting our API endpoints: /users, /orders, /payments"
```

智能体的执行过程大致是：

1. **规划目录结构**：按概念分组决定子目录划分；
2. **逐概念写文档**：每个概念一个 `.md` 文件，frontmatter 至少包含必填的 `type`，并尽量填充 `title`、`description`、`tags` 等推荐字段；
3. **建立交叉链接**：在正文中用标准 Markdown 链接关联相关概念；
4. **生成 index**：为目录生成 `index.md` 清单。

以上面的提示词为例，产出大致是：

```text
api-bundle/
├── index.md
└── endpoints/
    ├── index.md
    ├── users.md
    ├── orders.md
    └── payments.md
```

其中 `orders.md` 的内容形如：

```markdown
---
type: API Endpoint
title: /orders
description: Create and query customer orders.
tags: [orders, sales]
---

# Overview

Order management endpoint. Orders reference the
[users endpoint](./users.md) via `user_id`, and payments are
settled through the [payments endpoint](./payments.md).
```

**提示词技巧**：给出的信息越具体，产出质量越高。除了概念清单，最好同时说明：期望的类型名（如 `API Endpoint`、`Table`、`Metric`）、概念间的已知关系、以及知识包的目标读者（人还是智能体）。

### 4.2 Validate：合规校验

**做什么**：检查知识包是否满足 OKF 的三条硬性合规规则，并按文件粒度报告错误（error）与警告（warning）。

三条硬规则回顾：

1. 每个非保留的 `.md` 文件都包含可解析的 YAML frontmatter；
2. 每个 frontmatter 都有非空的 `type` 字段；
3. 保留文件名（`index.md`、`log.md`）在存在时遵循规范结构。

**怎么用**，两种方式：

方式一，自然语言让智能体检查：

```text
"Validate this folder against OKF spec"
```

方式二，绕过智能体直接跑零依赖的校验脚本（适合 CI）：

```bash
chmod +x scripts/validate.sh
./scripts/validate.sh ./my-bundle/
# 输出：
# ✅ Bundle is OKF v0.1 conformant
# ⚠️  2 warning(s)
```

**结果怎么读**：违反三条硬规则会报 error，必须修复；缺少 `title`、`description` 等推荐字段只报 warning，不阻断——这与规范"消费者不得拒绝缺少可选字段的文档"的宽容精神一致。建议把 `validate.sh` 挂进知识仓库的 CI，让每次 PR 都过一次合规门禁。

### 4.3 Enrich：丰富已有内容

**做什么**：对骨架文档做语义增强——补全 `description` 和 `tags`、在正文添加 Schema 表格、补充引用出处、建立遗漏的交叉链接。

**怎么用**：

```text
"Enrich this OKF bundle: fill missing descriptions, add schema sections and cross-links"
```

丰富前后的对比示例——丰富前：

```markdown
---
type: Table
title: orders
---

订单表。
```

丰富后：

```markdown
---
type: Table
title: orders
description: One row per completed customer order across all channels.
tags: [sales, orders, revenue]
---

# Schema

| Column | Type | Description |
| --- | --- | --- |
| `order_id` | STRING | Globally unique order identifier. |
| `customer_id` | STRING | Foreign key into [customers](/tables/customers.md). |
| `total_usd` | NUMERIC | Order total in US dollars. |

# Joins

Joined with [customers](/tables/customers.md) on `customer_id`.
```

**使用原则**：丰富必须**基于事实**——Schema 来自真实的建表语句、引用来自真实文档，智能体不应凭空编造字段含义。这也是为什么在 DataAgent 场景中，推荐把原始 DDL/SQL 语料一起提供给智能体作为丰富的依据。

### 4.4 Generate：生成索引与日志

**做什么**：自动生成两类保留文件——`index.md`（目录清单，支持渐进式披露）和 `log.md`（变更历史）。

**怎么用**：

```text
"Generate index.md and log.md for this bundle"
```

生成的 `index.md` 遵循规范结构：无 frontmatter，用标题分组，每个条目是"链接 + 简短描述"，描述取自对应概念 frontmatter 的 `description`：

```markdown
# Tables

* [Orders](tables/orders.md) - One row per completed customer order across all channels.
* [Customers](tables/customers.md) - Customer master data.
```

生成的 `log.md` 是按日期分组的扁平列表，最新在前，日期标题使用 ISO 8601 的 `YYYY-MM-DD` 形式：

```markdown
# Directory Update Log

## 2026-08-20
* **Creation**: Established the [orders](tables/orders.md) concept.
* **Update**: Added cross-links between orders and customers.
```

**为什么重要**：`index.md` 是渐进式披露的入口——智能体浏览知识包时先读索引、再按需打开具体文档，而不必把整个知识包灌进上下文。知识包规模越大，索引的价值越高。建议在每次批量新增概念后都重新生成一次。

### 4.5 其他能力速览

除上述四项外，Skill 还提供 Convert（转换存量知识库）和 Serve（推送到 Knowledge Catalog）：

```text
"Convert my Obsidian vault at ./knowledge/ to OKF format"
```

智能体把 wikilink 转成标准 Markdown 链接、确保每个文档都有 `type` 字段、生成 index/log 文件。Notion 导出和 CSV 同样支持，详见 Skill 内置的转换指南（`references/conversion.md`）；Serve 能力（经 kcmd 推送到 Google Cloud Knowledge Catalog）见本文第五节。

## 五、实现原理：一份 Skill 的内部构造

这一节是重点。很多人以为 Agent Skill 就是"一份提示词"，但 OKF Skill 的内部构造体现了几个刻意的设计决策。

### 5.1 整体结构：SKILL.md + 按需加载的参考资料

```text
okf-open-knowledge-format/
├── SKILL.md                    # 入口：能力声明 + 操作规程
├── references/
│   ├── spec-v01.md             # OKF v0.1 规范全文（451 行）
│   ├── examples.md             # 3 个完整示例知识包
│   └── conversion.md           # Notion / Obsidian / CSV 转换指南
└── scripts/
    └── validate.sh             # 零依赖 Bash 校验脚本
```

关键在 `references/` 的存在理由：**451 行的规范全文绝不能一次性塞进智能体上下文**。SKILL.md 只写操作规程和判断逻辑，当智能体真正需要规范细节、示例或转换规则时，再按文件路径加载对应的参考资料。这是 Agent Skills 的渐进式披露（progressive disclosure）模式——讽刺的是，这与 OKF 用 `index.md` 让智能体逐层浏览知识包是同一个设计思想：**上下文是最贵的资源，按需加载而非全量灌入**。

### 5.2 validate.sh：三条合规规则的可执行化

OKF 规范对合规性的要求刻意极简，只有三条：

1. 每个非保留的 `.md` 文件都有可解析的 YAML frontmatter；
2. 每个 frontmatter 都有非空的 `type` 字段；
3. 保留文件名（`index.md`、`log.md`）在存在时遵循规定结构。

我把这三条规则实现为一个**零依赖的 Bash 脚本**——不需要 Python、不需要 Node、不需要任何包管理器。设计意图很明确：**校验必须能在任何环境里发生**，包括 CI 容器、受限沙箱和临时机器。合规门槛低是 OKF 的优点，校验工具就必须把这个优点贯彻到底。

脚本区分错误（error）和警告（warning）：违反三条硬规则报错，缺少 `title`/`description` 等推荐字段只警告——与规范"消费者必须不拒绝缺选字段文档"的宽容精神一致。

### 5.3 转换指南：把迁移成本压到一次对话

`conversion.md` 覆盖了三种最常见的存量知识形态：

- **Notion 导出**：处理导出物的目录结构和属性字段映射；
- **Obsidian 库**：核心工作是 wikilink → 标准链接的改写，以及补全 `type`；
- **CSV**：每行一个概念的批量生成模式。

我选择把转换逻辑写成"指南"而不是"脚本"，因为迁移场景的差异（字段命名、链接形态、目录习惯）太大，**确定性脚本很快会不够用，而智能体恰好擅长处理这种模糊映射**。脚本负责硬性规则（校验），智能体负责柔性判断（转换）——这是整个 Skill 的职责划分原则。

### 5.4 Knowledge Catalog 集成：打通分发出口

Skill 还内置了与 Google Cloud Knowledge Catalog 的对接知识——它自 2026 年 6 月起原生摄取 OKF。智能体可以引导你完成 `kcmd init`、`kcmd push`，以及为 Claude Desktop、Cursor 等 MCP 兼容客户端配置 kcmd 的 MCP 服务器。Skill 理解 kcmd 的全部 MCP 工具语义：`pull`、`push`、`list-entries`、`lookup-entry`、`modify-entry`。

这样 OKF 的完整生命周期在 Skill 里闭环了：**创建 → 校验 → 丰富 → 转换 → 分发**。

## 六、使用场景

### 6.1 智能体驱动的数据目录

对智能体说"把我们 BigQuery 里的 sales 相关表整理成知识包"，它能起草概念文档、建立交叉链接、生成索引。这正是 DataAgent 类系统构建语义层的冷启动路径——先让 LLM 编译出第一版，再逐步用确定性工具加固。

### 6.2 存量知识库迁移

团队里沉睡的 Notion 空间、个人的 Obsidian 库，都可以一次性对话完成向 OKF 的迁移，获得跨工具可移植性和智能体可读性。

### 6.3 CI 中的知识质量门禁

`validate.sh` 零依赖的特性让它可以直接进 CI：任何向知识仓库提交的 PR 都先过一遍合规校验，把"知识即代码"的工程纪律落到实处。

### 6.4 企业知识资产入湖

通过 kcmd 把治理好的知识包推送到 Knowledge Catalog，供组织内所有智能体消费，完成从"个人文件"到"企业资产"的跃迁。

## 七、设计取舍与已知局限

坦诚地说两个局限：

1. **基于 v0.1 规范**。内置的 `spec-v01.md` 是 v0.1 全文，尚未覆盖 v0.2 的来源溯源（`sources`）、信任字段（`generated`/`verified`）、生命周期（`status`/`stale_after`）和认证计算（Attested Computation）。v0.2 的合规性向后兼容，所以产出物依然有效，但用不上新能力——这是当前最优先的待办事项。
2. **生成依赖 LLM，可复现性弱**。与 okf-skills 那类"确定性抽取二进制"的路线不同，本 Skill 的所有生成动作都经过智能体的 LLM。对小规模语料这是灵活，对大规模语料则需要搭配确定性解析器使用。

这两个取舍背后是同一个判断：**Skill 的价值在于把 OKF 的门槛降到零，而不是成为生产线本身**。生产线可以由使用者按自己的规模另行搭建，Skill 负责的是"让任何人十分钟内拥有第一个合规知识包"。

## 八、写在最后

OKF 的规范作者说"格式本身就是贡献"；我想补充一句：**让格式被用起来，是另一半贡献**。

规范解决的是机器与机器之间的互操作，Skill 解决的是人与智能体之间的能力传递。当你的编码智能体学会 OKF 的那一刻，你团队里所有沉睡的 Markdown、Notion 导出和 Obsidian 笔记，都开始具备成为智能体上下文资产的资格。

欢迎试用、提 Issue、发 PR。

> 参考链接：
> - Skill 文档：https://okf.md/skill/
> - Skill 源码：https://github.com/fabricioctelles/skills
> - OKF v0.1 规范：https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
> - 什么是 Agent Skills：https://okf.md/（站内导航）
