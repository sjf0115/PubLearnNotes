在之前的文章中，我们的 Agent 已经具备了推理、工具调用、知识检索和人工审核的能力。但当面对复杂任务时——比如"帮我制定一份北京三日游攻略"或"分析公司 Q3 财报并给出建议"——一个常见问题浮现了：

> **Agent 想到哪做到哪，缺乏全局规划，容易遗漏关键步骤。**

想象一个无规划的 Agent 帮你写代码：它可能先写前端界面，发现缺少 API，回头补后端，又发现数据库设计不合理，最终代码结构混乱。而人类开发者会先画架构图、分模块、定接口，再逐块实现。

**PlanNotebook** 正是为解决这一问题而生。它为 Agent 提供了"任务规划"能力：先分解复杂任务为结构化的子任务列表，再按顺序执行，每一步都记录状态和结果。本文将详细介绍这一核心组件的设计与使用。

---

## 1. 为什么需要任务规划？

### 1.1 无规划执行的困境

```
用户: "帮我建一个电商网站"

无规划 Agent:
  → 先写用户登录... 不对，得先有数据库
  → 回去建数据库... 发现表结构没设计好
  → 重新设计表... 又发现缺少商品分类字段
  → 来回折腾，代码一团糟

问题：遗漏功能、顺序混乱、无法追踪进度
```

### 1.2 有规划执行的优势

```
用户: "帮我建一个电商网站"

有规划 Agent:
  1. 创建计划：电商网站开发
     ├─ [x] 1. 数据库设计（用户表、商品表、订单表）
     ├─ [x] 2. 用户认证模块（注册/登录/权限）
     ├─ [ ] 3. 商品管理系统（CRUD/分类/搜索）
     ├─ [ ] 4. 购物车功能（添加/删除/结算）
     ├─ [ ] 5. 支付集成（支付宝/微信）
     └─ [ ] 6. 部署上线（Docker/Nginx）

  → 有序执行、进度可视、可追溯、不遗漏
```

### 1.3 PlanNotebook 的定位

PlanNotebook 不是让人类预先写好任务列表交给 Agent 执行，而是 **让 Agent 自己在推理过程中动态创建、调整和追踪计划**。它是 Agent 的"任务管理器"，也是"进度看板"。

---

## 2. Plan 系统核心架构

### 2.1 核心组件

| 组件 | 说明 | 职责 |
|-----|------|------|
| **Plan** | 计划模型 | 包含名称、描述、预期结果和子任务列表 |
| **SubTask** | 子任务模型 | 单个工作单元，有独立的状态和结果 |
| **PlanNotebook** | 计划管理器 | 提供工具方法管理计划，自动注入提示 |
| **PlanStorage** | 存储接口 | 持久化历史计划 |
| **PlanToHint** | 提示生成器 | 将计划状态转换为 Agent 上下文提示 |

### 2.2 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      ReActAgent                              │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   PlanNotebook                       │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │  工具方法（自动注册为 Agent 工具）            │    │    │
│  │  │  - create_plan(创建计划)                      │    │    │
│  │  │  - revise_plan(修改计划)                      │    │    │
│  │  │  - update_subtask(更新子任务)                 │    │    │
│  │  │  - finish_subtask(完成子任务)                 │    │    │
│  │  │  - finish_plan(完成计划)                      │    │    │
│  │  │  - view_subtasks(查看子任务)                  │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  │                          ↓                          │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │  Plan (当前计划)                             │    │    │
│  │  │  ├── name: "电商网站开发"                     │    │    │
│  │  │  ├── state: IN_PROGRESS                      │    │    │
│  │  │  └── subtasks:                               │    │    │
│  │  │       ├── [DONE] 数据库设计                  │    │    │
│  │  │       ├── [IN_PROGRESS] 用户认证             │    │    │
│  │  │       └── [TODO] 商品管理...                 │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   ChatModel  │  │   Toolkit    │  │   Memory     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 状态流转

**Plan 状态**：

```
TODO → IN_PROGRESS → DONE
            ↓
         ABANDONED（放弃）
```

**SubTask 状态**：

```
TODO → IN_PROGRESS → DONE
            ↓
         ABANDONED
```

---

## 3. Plan 与 SubTask 模型

### 3.1 Plan 模型

| 字段 | 类型 | 说明 |
|-----|------|------|
| `id` | UUID | 唯一标识 |
| `name` | String | 计划名称（简洁，建议不超过 10 词） |
| `description` | String | 详细描述（含约束和目标） |
| `expectedOutcome` | String | 预期结果（具体可衡量） |
| `subtasks` | List<SubTask> | 子任务列表 |
| `state` | PlanState | 计划状态 |
| `createdAt` | String | 创建时间 |
| `finishedAt` | String | 完成时间 |
| `outcome` | String | 实际结果 |

### 3.2 SubTask 模型

| 字段 | 类型 | 说明 |
|-----|------|------|
| `name` | String | 子任务名称 |
| `description` | String | 详细描述 |
| `expectedOutcome` | String | 预期结果 |
| `state` | SubTaskState | 任务状态 |
| `outcome` | String | 实际结果 |
| `createdAt` | String | 创建时间 |
| `finishedAt` | String | 完成时间 |

---

## 启用计划功能

一种推荐的方式是使用默认配置启用计划功能：
```java
ReActAgent agent = ReActAgent.builder()
        .name("Assistant")
        .model(model)
        .toolkit(toolkit)
        .enablePlan()  // 启用计划功能
        .build();
```
自定义配置
```java
PlanNotebook planNotebook = PlanNotebook.builder()
        .maxSubtasks(10)  // 限制子任务数量
        .build();

ReActAgent agent = ReActAgent.builder()
        .name("Assistant")
        .model(model)
        .toolkit(toolkit)
        .planNotebook(planNotebook)
        .build();
```

## 计划工具

## 工作流程

- 创建计划：智能体分析任务，调用 create_plan 创建包含多个子任务的计划
- 执行子任务：按顺序执行每个子任务
- 更新状态：完成子任务后调用 finish_subtask 更新状态
- 完成计划：所有子任务完成后调用 finish_plan

执行过程中，系统会自动在每次推理前注入计划提示，引导智能体按计划执行。

## 4. PlanNotebook 的工作机制

### 4.1 自动注入提示

PlanNotebook 最核心的机制是 **PlanToHint**——它会在每次 Agent 推理前，将当前计划的状态自动转换为 Markdown 格式的提示文本，注入到 Agent 的上下文中：

```markdown
# 当前计划：电商网站开发
**Description**: 构建一个包含用户系统、商品系统、订单系统的电商网站
**Expected Outcome**: 可正常访问的完整电商网站
**State**: in_progress

## Subtasks
- [x] 1. 数据库设计
  - **Expected**: 设计用户表、商品表、订单表
  - **State**: done
  - **Outcome**: 已完成，包含5张核心表

- [ ] 2. 用户认证模块
  - **Expected**: 实现注册、登录、JWT 鉴权
  - **State**: in_progress
  - **Outcome**:

- [ ] 3. 商品管理系统
  - **Expected**: 商品增删改查、分类管理
  - **State**: todo
```

Agent 看到这份提示后，就能清楚知道：
- 当前处于哪个阶段
- 已经完成了什么
- 下一步该做什么

### 4.2 内置工具方法

PlanNotebook 会自动向 Agent 的 Toolkit 中注册一组工具方法，Agent 可以通过调用这些工具来管理计划：

| 工具方法 | 功能 | 使用时机 |
|---------|------|---------|
| `create_plan` | 创建新计划及子任务 | 用户提出复杂任务时 |
| `revise_plan` | 修改现有计划 | 发现原计划不合理时 |
| `update_subtask` | 更新子任务状态或信息 | 子任务进行中 |
| `finish_subtask` | 标记子任务完成 | 子任务执行完毕 |
| `finish_plan` | 标记整个计划完成 | 所有子任务完成后 |
| `view_subtasks` | 查看当前子任务列表 | 随时查看进度 |

---

## 五、实战：让 Agent 学会规划

### 5.1 基础配置

```java
package com.example.plan;

import io.agentscope.core.ReActAgent;
import io.agentscope.core.message.Msg;
import io.agentscope.core.message.MsgRole;
import io.agentscope.core.model.DashScopeChatModel;
import io.agentscope.core.plan.PlanNotebook;
import io.agentscope.core.tool.Tool;
import io.agentscope.core.tool.ToolParam;
import io.agentscope.core.tool.Toolkit;

/**
 * 功能：PlanNotebook 使用示例
 */
public class PlanNotebookExample {

    // 工具类
    private static class DevTools {
        @Tool(name = "init_database", description = "初始化数据库")
        public String initDatabase(
                @ToolParam(name = "schema", description = "数据库架构") String schema) {
            return "数据库初始化完成: " + schema;
        }

        @Tool(name = "create_api", description = "创建后端 API 接口")
        public String createApi(
                @ToolParam(name = "endpoint", description = "接口路径") String endpoint,
                @ToolParam(name = "method", description = "HTTP 方法") String method) {
            return "API " + method + " " + endpoint + " 创建完成";
        }

        @Tool(name = "create_ui", description = "创建前端页面组件")
        public String createUi(
                @ToolParam(name = "component", description = "组件名称") String component) {
            return "前端组件 " + component + " 创建完成";
        }

        @Tool(name = "deploy", description = "部署应用")
        public String deploy(
                @ToolParam(name = "environment", description = "部署环境") String env) {
            return "应用已部署到 " + env;
        }
    }

    public static void main(String[] args) {
        // 1. 创建 PlanNotebook
        // maxSubtasks: 限制 Agent 创建的最大子任务数，防止计划过于庞大
        PlanNotebook planNotebook = PlanNotebook.builder()
                .maxSubtasks(10)   // 最多 10 个子任务
                .build();

        // 2. 创建工具集
        Toolkit toolkit = new Toolkit();
        toolkit.registerTool(new DevTools());

        // 3. 创建 Agent
        ReActAgent agent = ReActAgent.builder()
                .name("DevPlanner")
                .model(DashScopeChatModel.builder()
                        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                        .modelName("qwen3.5-35b-a3b")
                        .build())
                .sysPrompt(
                        "你是一个全栈开发工程师，擅长规划和执行复杂的软件开发任务。"
                        + "面对复杂需求时，请先创建详细的开发计划，然后按步骤执行。"
                        + "每完成一个步骤，更新计划状态。")
                .toolkit(toolkit)
                .planNotebook(planNotebook)  // 绑定 PlanNotebook
                .maxIters(20)                // 计划执行可能需要更多轮次
                .build();

        // 4. 用户提出复杂任务
        Msg userMsg = Msg.builder()
                .role(MsgRole.USER)
                .textContent("帮我构建一个简单的用户管理系统，包含注册、登录和个人资料编辑功能")
                .build();

        // 5. 执行
        Msg response = agent.call(userMsg).block();
        System.out.println(response.getTextContent());
    }
}
```

### 5.2 运行流程分析

当用户提出"构建用户管理系统"这个复杂任务时，Agent 内部会发生以下过程：

**第一轮：创建计划**

```
[Agent 推理] 这是一个复杂任务，需要先创建计划
[调用工具] create_plan(
    name: "用户管理系统开发",
    description: "构建包含注册、登录和个人资料编辑的用户管理系统",
    expectedOutcome: "可正常运行的用户管理系统",
    subtasks: [
        {name: "数据库设计", description: "设计用户表结构", expectedOutcome: "用户表包含id/用户名/密码/邮箱等字段"},
        {name: "注册API", description: "实现用户注册接口", expectedOutcome: "POST /api/register 可用"},
        {name: "登录API", description: "实现用户登录接口", expectedOutcome: "POST /api/login 可用"},
        {name: "个人资料API", description: "实现个人资料编辑接口", expectedOutcome: "PUT /api/profile 可用"},
        {name: "前端页面", description: "创建注册/登录/编辑页面", expectedOutcome: "三个功能页面可用"},
        {name: "部署", description: "部署应用到服务器", expectedOutcome: "系统可访问"}
    ]
)
```

**第二轮：执行第一个子任务**

```
[PlanToHint 注入] 当前计划状态提示
[Agent 推理] 子任务1 "数据库设计" 状态为 TODO，需要执行
[调用工具] init_database(schema: "users(id, username, password, email, created_at)")
[调用工具] finish_subtask(name: "数据库设计", outcome: "用户表创建完成")
```

**第三轮：执行第二个子任务**

```
[PlanToHint 注入] 子任务1 [DONE]，子任务2 [IN_PROGRESS]
[Agent 推理] 子任务2 "注册API" 需要执行
[调用工具] create_api(endpoint: "/api/register", method: "POST")
[调用工具] finish_subtask(name: "注册API", outcome: "注册接口创建完成")
```

**...后续轮次**

Agent 会逐个执行子任务，直到所有任务完成，最后调用 `finish_plan`。

### 5.3 最终输出

```
===== Agent 回复 =====
✅ 用户管理系统开发计划已全部完成！

📋 计划执行摘要：
  ✓ 数据库设计 — 用户表创建完成
  ✓ 注册API — POST /api/register 可用
  ✓ 登录API — POST /api/login 可用
  ✓ 个人资料API — PUT /api/profile 可用
  ✓ 前端页面 — 三个功能页面可用
  ✓ 部署 — 系统已部署

系统已可正常访问。
```

---

## 六、进阶：自定义与持久化

### 6.1 限制子任务数量

防止 Agent 创建过于庞大的计划：
```java
PlanNotebook planNotebook = PlanNotebook.builder()
        .maxSubtasks(8)   // 最多 8 个子任务，超出时 Agent 需要合并或精简
        .build();
```

### 6.2 查看计划状态（外部监控）

你可以在 Agent 执行过程中，通过 PlanNotebook 获取当前计划状态：
```java
// 在 Agent 执行后查看
Plan currentPlan = planNotebook.getCurrentPlan();
if (currentPlan != null) {
    System.out.println("当前计划: " + currentPlan.getName());
    System.out.println("计划状态: " + currentPlan.getState());
    System.out.println("完成进度: " +
        currentPlan.getSubtasks().stream()
            .filter(s -> s.getState() == SubTaskState.DONE)
            .count() + "/" + currentPlan.getSubtasks().size());

    for (SubTask subtask : currentPlan.getSubtasks()) {
        System.out.println("  [" + subtask.getState() + "] " + subtask.getName());
    }
}
```

### 6.3 持久化计划（PlanStorage）

PlanNotebook 支持将计划持久化到存储中，以便跨会话恢复：
```java
// 使用内存存储（默认）
PlanNotebook planNotebook = PlanNotebook.builder()
        .storage(new InMemoryPlanStorage())  // 内存存储，进程结束丢失
        .build();

// 使用文件存储
PlanNotebook planNotebook = PlanNotebook.builder()
        .storage(new FilePlanStorage(Path.of("/data/plans")))
        .build();
```

### 6.4 与 Human-in-the-Loop 结合

在关键子任务执行前，插入人工审核：
```java
// 在 Hook 中检查当前子任务
public class PlanApprovalHook implements Hook {
    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        if (event instanceof PreActingEvent e) {
            String toolName = e.getToolUse().getName();

            // 当 Agent 准备执行 deploy 工具时，要求人工确认
            if ("deploy".equals(toolName)) {
                Plan plan = planNotebook.getCurrentPlan();
                System.out.println("准备部署计划: " + plan.getName());
                // ... 审批逻辑
            }
        }
        return Mono.just(event);
    }
}
```

---

## 七、PlanNotebook 的设计哲学

PlanNotebook 的设计体现了 AgentScope 框架的一贯风格：**给 Agent 能力，而非给 Agent 指令**。

| 传统方式 | PlanNotebook 方式 |
|---------|------------------|
| 人类预先写好任务清单 | Agent 自己创建、调整计划 |
| Agent 被动执行 | Agent 主动规划、追踪、汇报 |
| 进度不可见 | 每个子任务状态清晰可查 |
| 一次性的 | 可持久化、可恢复、可审计 |

---

## 八、总结

本文详细介绍了 AgentScope Java 的 PlanNotebook 组件：

| 要点 | 内容 |
|-----|------|
| **核心作用** | 让 Agent 具备"先规划、后执行"的任务管理能力 |
| **核心组件** | Plan（计划）、SubTask（子任务）、PlanNotebook（管理器） |
| **使用方式** | `PlanNotebook.builder().maxSubtasks(10).build()` + `agent.planNotebook(notebook)` |
| **自动机制** | PlanToHint 自动将计划状态注入 Agent 上下文 |
| **内置工具** | create_plan、revise_plan、update_subtask、finish_subtask、finish_plan、view_subtasks |
| **进阶能力** | 持久化存储、外部监控、与 HITL 结合 |

掌握 PlanNotebook 后，你的 Agent 将不再是"走一步看一步"的盲目执行者，而是**有目标、有节奏、可追溯**的智能协作者。这对于处理复杂多步骤任务（如软件开发、数据分析、内容创作）至关重要。
