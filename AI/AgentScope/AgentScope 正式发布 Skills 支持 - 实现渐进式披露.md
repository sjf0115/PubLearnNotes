## 1. 背景：多能力 Agent 的挑战

在大语言模型驱动的 Agent 系统中，存在一个核心矛盾：我们希望 Agent 拥有尽可能多的能力，但在任何时刻它只会用到其中一小部分, 同时 Agent 的上下文空间是有限的。

以一个客服系统为例：我们希望它能同时处理订单查询、退款申请、产品推荐、技术支持等多个领域的问题，但在任何一次对话中，用户通常只会涉及其中一两个领域。但是又要支持Agent同时具有这些能力如何在有限的上下文中高效管理这些能力？

### 1.1 三种常见上下文加载方案

- 方案 1：全量加载
  - 核心思路：将所有领域的知识预先加载到 SystemPrompt 中
  - 优势：简单直接，无需额外机制
  - 局限：上下文占用 15k+ tokens，资源浪费，可扩展性差
- 方案 2：多 Agent 架构
  - 核心思路：每个 Agent 独立加载专业领域知识
  - 优势：隔离不同领域的上下文
  - 局限：局部看某个 Agent 时，本质上还是全量加载，只是每个 Agent 只加载自己专业领域的知识
- 方案 3：RAG（检索增强生成）
  - 核心思路：通过向量检索动态加载知识
  - 优势：灵活高效，按需获取
  - 局限：流程性知识检索失真，上下文碎片化，准确率上限 70-80%

![](https://mmbiz.qpic.cn/sz_mmbiz_png/j7RlD5l5q1wDtqB6ZROZKml5CCMwccDY9DKYz0Z86Zgcv0GPmaRvAKPUpHpvts1KVgJKpo2QAkibv7MAOAgB1xszeeVF848OXxcvUpc6HwM0/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=1)

### 1.2 问题的本质

这三种方案的困境本质上源于同一个问题：缺乏灵活的上下文加载机制。它们在三个维度上都存在不足：
- 空间维度：无法区分"必需知识"与"潜在知识"，导致过度加载
- 时间维度：无法实现"按需加载"，只能选择"全量加载"或"检索加载"
- 结构维度：无法保持知识的完整性，在碎片化和全量化之间缺少中间态

用一个类比来说明：想象你是一位电商平台的全能客服，需要处理订单、退款、技术故障、投诉等各类问题。
- 全量加载：就像入职培训时把几十本产品手册、退款流程、技术文档全部背下来，即使用户只是问个快递单号也要承载所有复杂退款规则的记忆负担；
- 多 Agent 方案：就像把你拆分成订单客服、退款客服、技术客服，每通电话都需要"语音导航"判断转给谁，用户说不清问题时就在各个专员之间来回转接；
- RAG 方案：就像有个助手根据用户问题去知识库搜索，但可能搜到过期的退款政策，或者只搜到零散的操作步骤却漏掉关键的前置条件。

我们需要的是：让 Agent 像一个经验丰富的客服一样，脑子里有个清晰的"目录"——平时只记住"退款问题看《退款处理手册》、技术问题看《故障排查指南》"（元数据），遇到退款咨询时快速调出完整的退款流程和话术（按需加载），碰到罕见的特殊情况再去查阅详细的政策文档（资源按需）。这就是 Skill 机制要解决的问题：**让 Agent 知道有哪些知识，需要时才调用，调用时保持完整**。

## 2. Skill 机制：渐进式披露

**核心思想**：让 Agent 先知道"有什么能力"，需要时再学习"如何使用"，而不是一开始就把所有知识装进上下文。

### 2.1 核心定义

Skill（技能） 是一个独立的、可复用的知识和能力单元，包含三个核心组成部分：
- 结构化指令：用 Markdown 编写的标准作业流程（SOP）
  - 定义何时使用此 Skill（触发条件）
  - 描述具体的执行步骤（操作流程）
  - 说明可用的工具和资源（支撑材料）
- 资源文件：支撑指令执行的参考材料
  - 详细的 API 文档和技术规范
  - 使用示例和最佳实践指南
  - 模板文件和配置样例
- 可执行脚本：提供确定性操作的代码
  - 数据处理和转换脚本
  - 验证和校验工具
  - 与外部系统的集成接口

渐进式披露（Progressive Disclosure） 是一种上下文管理策略，将知识加载分为三个层次：

![](https://mmbiz.qpic.cn/sz_mmbiz_png/j7RlD5l5q1yic8pMojmbZsDtq3ZkxEdGwW3ODtr6WSGOjXQxX4LzKUqjSia6kAYulBbho1fMSFRu4H3xRLcAzq8yNNrYyicD0Bv5iaA4uox2NYc/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=2)

- 启动时轻量：只加载必要的元数据，支持大量 Skill 注册
- 执行时精准：只加载相关的 Skill，避免无关知识干扰
- 使用时完整：保持 SOP 的逻辑连贯性，不碎片化

![](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJ9VUlHGU1AqQWWtjhZuN5h4WZ1g2mkEN5vLHp7CpzsiboCuMQXOc0t3eUjicxxBHRRQLCKxbS25pkw/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=3)

### 2.2 Skill 的结构规范

Skill 以文件系统的目录结构组织，核心是 `SKILL.md` 文件：
```
skill-name/
├── SKILL.md          # 必需：包含元数据和指令
├── references/       # 可选：详细参考文档
│   └── api-doc.md
├── scripts/          # 可选：可执行脚本
│   └── process.py
└── assets/           # 可选：模板和资源
    └── template.html
```
`SKILL.md` 的最小结构：
```
---
name: skill-name
description: 何时使用此 Skill 的描述
---

# Skill 指令内容
...
```

### 2.3 渐进式披露的工作机制

以订单处理场景为例，说明三层加载的过程：

![](https://mmbiz.qpic.cn/mmbiz_png/j7RlD5l5q1zLZ4eia9HY2dKqkdT8cQialI1UmOOuKTvVIPticyoXAliaDK5o2dRgatW9CibMiaMAVsOAVyLA6lMjPukkvVjVP77x8DAiamcyhTyDr0/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=4)

#### 2.3.1 第 1 层：元数据加载（启动时）

Agent 启动时，上下文中仅包含所有 Skill 的元数据：
```
# 上下文占用：~100 tokens/Skill
skills:
  - name: order_processing
    description: 处理订单查询、修改、取消操作
  - name: payment_processing
    description: 处理支付、退款操作
  - name: product_recommendation
    description: 产品推荐和库存查询
  # ... 共 10 个 Skill
```
上下文成本：10 个 Skill × 100 tokens = 1k tokens

此时 Agent 知道"有哪些能力可用"，但不知道"如何执行这些能力"。这种设计支持注册任意数量的 Skill，因为每个 Skill 只占用约 100 tokens 的元数据空间。

#### 2.3.2 第 2 层：指令加载（触发时）

当用户询问"订单 123456 什么时候到？"，Agent 识别需要 `order_processing` Skill，加载其完整指令：
```
# 新增上下文：~2k tokens
## 订单处理标准流程

### 查询订单
1. 调用 queryOrder(orderId) 获取订单详情
2. 判断订单状态：
   - 待支付 → 提供支付链接
   - 已发货 → 返回物流信息
   - 已完成 → 询问是否需要售后

### 修改地址
前置条件：订单状态为「待发货」
步骤：
1. 验证订单状态
2.
...

### 可用资源
- references/error-codes.md：错误码对照表
- scripts/validate.py：订单号校验脚本
```

上下文成本：1k（元数据）+ 2k（指令）= 3k tokens

加载的是完整的 SOP 文档，保持了逻辑连贯性，不会像 RAG 那样出现碎片化。同时只加载当前任务相关的 Skill，相比全量加载节省 85% 的上下文空间（3k vs 20k）。

#### 2.3.3 第 3 层：资源加载（按需时）

执行过程中遇到错误码 E1001，Agent 加载错误码说明：
```
# 新增上下文：~1k tokens
## 错误码对照表
- E1001: 订单不存在，请检查订单号
- E1002: 订单状态不允许修改
- E1003: 地址格式不正确
...
```
或执行脚本（不占用上下文）：
```
# Agent 调用 scripts/validate.py
# 脚本执行，仅返回结果
result = validate_order_id("123456")
# 返回: {"valid": true, "order_type": "standard"}
```
上下文成本：
- 文档资源：累加到上下文（1k + 2k + 1k = 4k tokens）
- 脚本执行：不占上下文，仅返回结果（约 50 tokens）

资源文件按需加载，避免预先加载所有参考文档。脚本执行提供确定性操作，不依赖 LLM 生成代码，且执行结果不占用上下文空间。理论上可以支持无限数量的资源文件（通过文件系统存储）。

## 3. AgentScope-Java 中的 Skill 机制实现

![](https://mmbiz.qpic.cn/sz_mmbiz_jpg/j7RlD5l5q1xzKLhYib9vgFCicZDlsrWLqHeiccyBEcuRsEf0oljNdQxBiceaCzTU6OtFxibMicYrsdOSmO3Rt3lofdLtkrXKot2aGFRbic8Xtx3mnw/640?wx_fmt=jpeg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=5)

> 详细文档: https://java.agentscope.io/zh/task/agent-skill.html

存储层抽象：解耦 Skill 与文件系统
- 原生 Skill 机制基于文件系统，Agent 通过文件系统 Tool 直接访问磁盘文件，难以在云端、容器等环境中灵活部署。
- 我们将 Skill 进行了进一步的抽象,使其的发现和内容加载不再依赖于文件系统, 只是将文件系统作为一个 LLM 通过 Tool 来发现和加载 Skill 的内容和资源。同时为了兼容已有的 Skill 生态与资源,Skill 的组织形式依旧按照文件系统的结构来组织它的内容和资源。

### 3.1 创建 Skill 对象

对于结构是如下的 Skill:
```
skill-name/
├── SKILL.md          # 必需：包含元数据和指令
├── references/       # 可选：详细参考文档
│   └── api-doc.md
├── scripts/          # 可选：可执行脚本
│   └── process.py
```
我们可以创建一个 Skill 对象:
```java
AgentSkill skill = AgentSkill.builder()
    .name("data_analysis")
    .description("Use when analyzing data...")
    .skillContent("# Data Analysis\n...")
    .addResource("references/api-doc.md", "# API ...")
    .addResource("scripts/process.py", "def process(data): ...")
    .build();
```
AgentScope-Java 提供了 Repository 抽象层，使能从外部系统中批量创建Skill。
```java
// 从文件系统加载 Skill
AgentSkillRepository fileRepo = new FileSystemSkillRepository(Path.of("./skills"));
AgentSkill skill = fileRepo.getSkill("data_analysis");
skillBox.registerSkill(skill);

// 保存 Skill 到文件系统
fileRepo.save(List.of(skill), false);
// 未来的扩展：从数据库、远程 API 等加载
// AgentSkillRepository dbRepo = new DatabaseSkillRepository(dataSource);
```
### 3.2 基于 SystemPrompt 的一级披露

```java
Toolkit toolkit = new Toolkit();
SkillBox skillBox = new SkillBox(toolkit);
skillBox.registerSkill(skill);
ReActAgent agent = ReActAgent.builder()
    .name("Assistant")
    .model(model)
    .skillBox(skillBox)
    .toolkit(toolkit)
    .build();
```
将 Skill 注册到 SkillBox 中, 再将 SkillBox 注册到 ReActAgent 使技能生效。

在对话时, 对于持有了 SkillBox 的 Agent, 会在 SystemPrompt 中注入 Skill 的提示词模板(告知模型什么时候使用 Skill, 怎么加载 Skill)和 Skill 的元数据, 用于一级暴露。
```xml
<available_skills>
  <skill>
      <name>data_analysis</name>
      <description>Use when analyzing data...</description>
      <skill-id>data_analysis</skill-id>
  </skill>
</available_skills>
```

### 3.3 基于 Tool 的二级披露和三级披露

在对话时, LLM 判断要使用 Skill, 将通过自动注册好的 load_skill_through_path Tool 来加载 Skill 的指令和资源, 用于二级披露和三级披露
```java
load_skill_through_path(skillId="data_analysis", path="SKILL.md")
load_skill_through_path(skillId="data_analysis", path="references/api-doc.md")
load_skill_through_path(skillId="data_analysis", path="scripts/process.py")
```

Tool 的渐进式披露：AgentScope-Java 将 Tool(Mcp/Function Call) 也作为 Skill 的一种资源，实现 Tool 的渐进式披露。在agent代码中将skill和Tool绑定. 当Skill 未激活时绑定的 Tool 不会出现在 Agent 的工具列表中，Skill 激活后 Tool 自动激活, 在接下来的对话中对 Agent 可见。
```java
// 注册 Skill 并绑定 Tool
skillBox.registration()
    .skill(dataSkill)              // 注册 Skill
    .tool(new DataAnalysisTool())  // 绑定 Tool（仅 Skill 激活时可用）
    .apply();
```

### 3.4 代码执行能力

在 AgentScope-Java 中，Skill 的所有资源（包括脚本文件）都存储在内存中。这带来了分发便捷性，但也意味着脚本无法直接执行——操作系统需要文件系统路径来运行代码。

解决方案是使用 `SkillBox.codeExecution()` 启用代码执行能力，将脚本资源输出到工作目录：
```java
// 自定义 Shell 命令白名单和审批回调
ShellCommandTool customShell = new ShellCommandTool(
    null,  // baseDir 会被自动设置为 workDir
    Set.of("python3", "node", "npm"),      // 命令白名单
    command -> askUserApproval(command)    // 可选的命令审批回调
);

skillBox.codeExecution()
    .workDir("/path/to/workdir")  // 指定工作目录
    .includeFolders("scripts/", "assets/")
    .includeExtensions(".py", ".js", ".sh")
    .withShell(customShell)
    .withRead()
    .withWrite()
    .enable();
```
配合 Docker 沙箱实现安全执行：将 workDir 指向 Docker 容器挂载的卷目录，Skill 脚本会被写入该目录，随后在隔离的沙箱环境中执行。这种方式既保留了 Skill 打包分发的便捷性，又通过容器隔离确保了代码执行的安全性。

## 4. 总结：Skill 是及时雨，但不是万金油

### 4.1 为什么说是"及时雨"

Skill 机制为拓展单个 Agent 能力提供了一种简单而强大的方式，让我们在不引入架构复杂度的前提下，构建具备多领域知识的智能 Agent：
- 隔离启动上下文：支持无限扩展领域数量，拓宽有效 Prompt 空间，让 Agent 有更多上下文用于推理和对话历史；
- 赋予模型自主性：Agent 可以自主决定何时加载哪个 Skill，并动态组合解决复杂问题；
- 降低维护成本：业务流程调整时，修改 Skill 文件即可更新，无需重训模型或重建索引；

适合使用 Skill 的场景：
- 多领域知识密集型应用：客服系统、代码助手、医疗咨询等，需要掌握多个领域但单次对话只涉及一两个；
- SOP 频繁迭代：业务流程经常调整，修改 Skill 文件即可更新，无需重训模型或重建索引；
- 需要确定性操作：通过脚本资源保证关键步骤准确性，避免 LLM 行为的不确定性；

与其他技术组合使用：
- Skill + RAG：结构化 SOP + 非结构化知识库；
- Skill + Multi-Agent：Skill 提供领域知识，Multi-Agent 隔离运行时上下文；
- Skill + 长上下文：多领域按需加载 + 单领域深度分析。

### 4.2 为什么说"不是万金油"

Skill 机制有其固有的局限性，并非所有场景都适用。

机制层面的局限：
- 只能隔离启动上下文，无法隔离运行时上下文：多个领域的知识会存在于同一个 Agent 的记忆/上下文窗口中，模型在推理时需要同时处理多个领域的知识，可能导致混淆甚至错误；
- Skill 之间没有优先级：所有 Skill 对模型而言是平等的，无法设置权重或优先级。即使业务上某个 Skill 更重要、期望更高频触发，它与其他 Skill 的触发机会实际上是相同的；
- 触发条件依赖 LLM 能力：Skill 的加载时机由模型自主判断，不同模型表现差异较大；

不适合使用 Skill 的场景：
- 实时性要求极高：Skill 加载需要额外 Tool 调用，增加约 100-200ms 延迟；
- 单一领域简单任务：直接在 SystemPrompt 中编写更简单，无需引入额外复杂度；
- 深度推理场景：数学证明、复杂算法设计等更适合长上下文，Skill 擅长流程性知识而非推理性知识；
- 技能使用频率失衡：当存在少量高频技能和大量低频技能时（长尾分布），高频技能每次都需 Tool 调用加载，增加不必要的延迟；而大量低频技能使 Skill 列表过长，增加模型选择负担。此时应将高频内容压缩后直接写入 SystemPrompt。

未来，我们将在 Skill 的完整生命周期管理和便捷分发机制上持续优化和探索，进一步降低 Skill 的创建、共享和复用成本。

参考文档
- Agent Skills 使用指南：https://java.agentscope.io/en/task/agent-skill.html
- Integrate Skills：https://agentskills.io/integrate-skills
- Equipping Agents for the Real World with Agent Skills：https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
