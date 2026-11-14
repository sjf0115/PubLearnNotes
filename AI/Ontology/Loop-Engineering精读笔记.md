# Loop Engineering 精读笔记

> 来源：阿里技术《Loop Engineering 概念解析、思考与实践》（2026-06-18）
> 原文：https://mp.weixin.qq.com/s/ael7aIEoomk4AU84E-mpGg
> 阅读时长（原文）：约 20 分钟
> 说明：本文为个人学习整理的结构化精读笔记，非原文复述，如需引用请以原文为准。

---

## 一、这个话题为什么突然变热

作者把 Loop Engineering 放在「Agent 自进化」这条演进线上来看：更早的讨论是 Hermes Agent、Skill 自进化，现在的关注点又往上抬了一层——从"怎么用 Agent"变成"怎么设计让 Agent 自己跑起来的那套循环"。

几个风向标式的表态被列举出来：

- Anthropic Claude Code 负责人 Boris Cherny 说自己已经不再手写 Prompt，而是写 Loop。
- OpenClaw 创始人 Peter Steinberger 主张不要用一次性 Prompt 指挥 Agent，而要通过设计 Loop 引导行为。
- Andrej Karpathy 强调"你必须把自己从 Loop 的执行过程中移除出去"。
- Google AI 总监 Addy Osmani 在 2026 年 6 月初撰文，给这个概念下了一个被广泛引用的定义（原文引用见下）。

## 二、一句话定义（引用）

> "Loop engineering is replacing yourself as the person who prompts the agent. You design the system that does it instead."
> —— Addy Osmani

翻译成中文大意：所谓 Loop Engineering，就是把"给 Agent 写 Prompt 的那个人"这个角色从你自己身上剥离，转而设计一套能替你做这件事的系统。

## 三、Agent Loop ≠ Loop Engineering

这是全文最需要先厘清的一组概念，作者把它单独开了一节。

**Agent Loop（底层循环）**——Agent 之所以能持续运行，靠的就是这个基础机制：模型一次输出要么是 Response（结束），要么是 Function Call（执行工具，把结果再喂回模型，进入下一轮）。ReAct、Ralph Loop 等都属于这个层面的变种；Validation Agent 拉起、Max Steps 兜底这些工程手段也是为它服务的。这一层早就已经是"默认基础设施"。

**Loop Engineering（外层循环）**——大佬们口中所说的 Loop，是构建在 Agent / Harness 之上、由人来设计、用来控制"人怎么使用 Agent"的一层新范式。它关心的不是模型内部怎么调工具，而是"开发—测试—验收—反馈—迭代"这条外部链路能不能自己转起来。

作者用了一个很生动的观察来引出外层循环的必要性：当下用 Claude Code / Codex 的实际体验，被网友总结成几个高频按钮——"说中文""继续""还是报错""你改了啥""先别重构""回滚"。这些"人机协同的催更指令"本身就是可以被自动化掉的环节。

## 四、核心变化：从 HITL 到自动化验收闭环

把上面的问题说清楚：以前叫 Human-in-the-Loop，人在外部大循环里做验证和测试；现在讨论的是，能不能让模型自己在这个外部验收环里闭环。也就是让模型把"检查错误""不符合预期"这些原本由人喊出来的话，自己先对自己说，主动完成验证与再迭代。

作者点出一个关键前提：**你不设计这个 Loop，模型很可能不 Loop 或者瞎 Loop**。所以要把开发需求、验证内容、预期目标都提前定义清楚，Agent 才有条件自己跑到位。

放在 AI Coding 演进线里看这条主线（这大概是全文最适合记忆的一段）：

- 从写代码 → AI 写代码：机器替人写。
- 从短任务 → 长链条 Agent：机器替人跑。
- 从本机 → 云端 / 移动端（如 OpenClaw）：机器换地方跑。
- 从固定 Skill → 自进化 Skill：能力自己长大。
- 从「使用工具」→「设计闭环」：把人从交互链里再撤一步——这就是 Loop Engineering。

作者也给出了 Loop 的两种触发方式：**人工触发**（当下就能实现，写一个 Pipeline 一步步自动执行）和**定时触发**（适合周期性任务，例如 PR 评审合并、周报日报自动汇总、股票定时抓取与交易等）。

**一句最能概括方法论的话：**
Vibe Coding 是"从写代码变成提需求"；Loop Engineering 是"从提一个需求变成提一套闭环流程"。

## 五、Loop Engineering 的六大核心组件

作者按 Addy Osmani 的框架列出六块，我把每一块"要解决什么问题 + 具体做法"提炼成一行，方便复习。

1. **Automations（自动化）**——解决"一次性 vs. 能循环"的问题。Codex 侧有自动化任务（选项目、定 Prompt、定频率、本地或后台分支、发现异常进 Triage 收件箱），配合 `/goal` 可以持续跑到条件满足。Claude Code 侧靠 Cron + Hook 做类似事，`/loop` + 独立小模型判定"是否达成目标"，同样是"定目标、撒手不管"。

2. **Worktrees（工作树隔离）**——解决"多 Agent 同仓库互相踩脚"的问题。基于 Git Worktree：一个独立工作目录 + 各自分支 + 共享仓库历史。Codex 内置 Worktree 支持；Claude Code 提供 `--worktree` 参数或 `isolation: worktree` 给子 Agent 分配一次性代码副本，用完自动清理。

3. **Skills（可进化的技能包）**——解决"每次都在同一个坑里跌倒"的问题。在 Loop 的每一轮里，Skill 如果能自我沉淀，就变成了"活的知识"，让 Agent 越跑越聪明。

4. **Connectors / Plugins（连接器 / 插件）**——本质是 MCP 及其延伸。没有它 Agent 只是封闭推理引擎，有了它 Agent 才能"伸手"触达外部服务与数据。

5. **Sub Agents（子智能体）**——解决"当局者迷"的质量问题。作者特别强调**验收 Sub Agent 必须独立**，不能既当运动员又当裁判员；探索、设计、实现类的子任务可以并行拆分，但最终必须回到主 Agent 汇总；Sub Agent 不是越多越好，缺乏主 Agent 调度就会各干各的。

6. **State（状态管理）**——解决"跑到哪一步了、哪些已经做完"。轻量方案用 Markdown（AGENTS.md / 进度文件）；有项目管理工具（Linear 等）的话用 MCP 连接器自动同步。

## 六、一个可上手的小实践：文本分类 Loop

作者举了一个 Claude Code / Codex 都能跑通的小例子，用来说明 Loop 和传统方式的差异：

**传统做法**：写 Prompt → 模型输出分类结果 → 人肉看准确率 → 手改 Prompt → 沉淀成 Skill。人在中间承担全部校验。

**Loop 做法**：把"验证 + 迭代"直接写进任务定义。例如：完成分类后严格按标准自评、有错就修正逻辑或标准、最终把稳定能力沉淀为 Skill；并且给出量化目标（如"100 条测试样本、准确率 ≥95% 或错误率 ≤5%"）。目标进入 Loop 后，Agent 自己打磨到达成，中途不需要人喊。

**与 EvoSkill / SkillOpt 这类方案的区别**：Loop 版完全由 Agent 自主驱动，不依赖外部开源框架，模型会在循环中自己搭一套类似的验证与优化机制。

**由此延伸出的一个趋势判断**：AI 时代，很多原来需要工程化封装的能力，只要用 Claude Code / Codex 写一个结构化 Loop 就能"跑出来"，未必先造一个新框架。

**作者的实操建议（很值得记住）**：如果流程是固定的、不需要模型每次都重新推理，**直接写成脚本**；如果确实需要模型每天介入做动态判断，**沉淀成 Skill**。原因是每天重跑 Loop 费 token，且模型每次实现路径不一样，结果容易漂移、难以复现。

## 七、避坑：Loop 不是银弹

作者最后给了一段冷静的提醒，我认为这是整篇文章最值得贴在显示器边上的一段：

1. **它不是全新技术**，只是把自动化又往前推了一步；AI 演进一直是量变引起质变。
2. **对"需求 + 验收标准"的表达能力要求反而更高了**。以前需求模糊没关系，人在 HITL 里可以不断纠偏；用了 Loop 之后，中间人不参与，一开始没写清楚 → 从一开始就跑偏 → 烧一大圈 token → 拿到不想要的结果。
3. **对自己把控不住 Loop 效果的人，先老实回到 Human-in-the-Loop**。技术方法论没有对错，只有适不适合；AI 时代没有万金油。

一句总结：**需求明确 + 验证清晰 = 效率神器；需求模糊 + 验证模糊 = 人还在环里更省钱。**

## 八、我的复盘要点（可脱离原文独立记忆）

- Loop Engineering 讨论的不是 Agent 内部循环，而是"开发—验证—迭代"这条外部循环的自动化。
- 它的核心动作：把人从"发 Prompt 的那个人"这个位置撤下来，交给一套设计好的系统。
- 六件套：Automations、Worktrees、Skills、Connectors/Plugins、Sub Agents、State——分别对应节奏、隔离、沉淀、触达、制衡、追踪。
- 独立验收 Sub Agent 是 Loop 里最重要的质量闸门，绝不能让主 Agent 自评自过。
- 稳定流程 → 脚本；动态判断 → Skill；探索性一次性任务 → 才用 Loop 现跑。
- Loop 用得越狠，对"清晰需求 + 明确验收标准"的依赖就越强；写不清楚就别开 Loop。

## 九、References

- Addy Osmani, "Loop Engineering" — https://addyosmani.com/blog/loop-engineering/
- "Loop Engineering: Build Self-Running Coding Agents 2026" — https://www.the-ai-corner.com/p/loop-engineering-coding-agents-2026
- 原文（阿里技术公众号）：https://mp.weixin.qq.com/s/ael7aIEoomk4AU84E-mpGg
