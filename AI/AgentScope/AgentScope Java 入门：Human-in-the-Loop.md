在之前的文章中，我们构建了一个能够自主调用工具、检索知识库的智能 Agent。但有一个关键问题始终存在：**当 Agent 准备执行敏感操作（如转账、删除数据、发送邮件）时，谁来把关？**

完全自主的 Agent 在演示环境中很酷，但在生产环境中却充满风险。Human-in-the-Loop（HITL，人在回路）机制正是为了解决这一矛盾而生——它让 Agent 在执行过程中插入人工审核环节，即在 **关键决策点暂停执行，等待人类确认后再继续**，既保留了自动化的效率，又确保了关键操作的可控性。

AgentScope Java 的 Human-in-the-Loop 并非一套独立的复杂框架，而是巧妙地复用了我们已经熟悉的 **Hook 机制**，在工具执行的特定时机插入人工审核点。本文将详细介绍如何在 AgentScope Java 中实现 Human-in-the-Loop。

---

## 1. 为什么需要 Human-in-the-Loop？

### 1.1 完全自主 Agent 的风险场景

| 场景 | Agent 行为 | 风险 |
|-----|-----------|------|
| 智能客服退款 | Agent 调用 `refund_order` 工具 | 可能误操作，将正确订单退款 |
| 数据库运维助手 | Agent 调用 `execute_sql` 执行 DELETE | 可能误删生产数据 |
| 合同审核助手 | Agent 调用 `send_email` 发送合同 | 可能将未审核版本发给客户 |
| 财务报告助手 | Agent 调用 `transfer_money` 转账 | 资金损失风险极高 |

### 1.2 核心价值

- **安全兜底**：高危操作必须经过人类确认
- **错误纠正**：Agent 理解偏差时，人类可以及时干预
- **合规要求**：金融、医疗等行业监管要求关键决策有人工审核
- **信任建立**：用户更愿意使用"可控"的 AI 系统

---

## 2. AgentScope HITL 的设计哲学

AgentScope 没有为 HITL 引入新的 API 或复杂的配置，而是基于已有的 **Hook 事件系统**实现：

```
用户提问 → Agent 思考 → 准备调用工具 → Hook 触发
                                              ↓
                                    [PreActingEvent]
                                              ↓
                                    是否有人工审批 Hook？
                                              ↓
                                    是 → 暂停，等待人类决策
                                    否 → 继续执行工具
                                              ↓
                                    工具执行完成 → Hook 触发
                                              ↓
                                    [PostActingEvent]
                                              ↓
                                    是否有人工审核 Hook？
                                              ↓
                                    是 → 人类审核结果，决定修正/接受
                                    否 → 将结果返回给 Agent
```

这种设计的优雅之处在于：**HITL 只是 Hook 的一种特殊用法**，没有额外的学习成本。

---

## 3. Human-in-the-Loop 实现


- 恢复方法：
  - agent.call() — 继续执行待处理的工具
  - agent.call(toolResultMsg) — 提供自定义的工具结果后继续
- 判断暂停原因：
  - response.getGenerateReason() 返回 REASONING_STOP_REQUESTED 或 ACTING_STOP_REQUESTED

AgentScope 基于已有的 **Hook 事件系统** 实现

### 3.1 两个暂停时机

智能体的执行分为”推理”和”行动”两个阶段，你可以选择在不同时机暂停：
- 推理后暂停：模型决定要调用哪些工具后，在实际执行前暂停。此时你可以看到工具名称和参数，让用户决定是否允许执行。
- 行动后暂停：工具执行完毕后，在进入下一轮推理前暂停。此时你可以看到执行结果，让用户决定是否继续。

| 时机 | 事件类型 | 时机 | 适用场景 | 干预能力 |
|-----|---------|---------|---------|---------|
| **推理后** | `PostReasoningEvent` | 模型决定要调用哪些工具后，在实际执行前暂停 | 适用于 **"该不该做"** 的决策：审批敏感操作、权限校验等 | 可以阻止执行、修改参数、让 Agent 重新思考或返回拒绝信息 |
| **行动后** | `PostActingEvent` | 工具执行完毕后，在进入下一轮推理前暂停 | 适用于 **"做得对不对"** 的校验：审核结果质量、数据校验 | 可以修正结果、要求重试 |

- 暂停方法：
  - PostReasoningEvent.stopAgent() — 推理后暂停
  - PostActingEvent.stopAgent() — 行动后暂停

以下示例展示如何在执行删除文件、发送邮件等敏感操作前，先让用户确认：
```java
// 1. 创建确认 Hook
Hook stopHook = new Hook() {
    private static final List<String> SENSITIVE_TOOLS = List.of("delete_file", "send_email");

    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        if (event instanceof PostReasoningEvent e) {
            Msg reasoningMsg = e.getReasoningMessage();
            List<ToolUseBlock> toolCalls = reasoningMsg.getContentBlocks(ToolUseBlock.class);

            // 如果包含敏感工具，暂停等待确认
            boolean hasSensitive = toolCalls.stream()
                .anyMatch(t -> SENSITIVE_TOOLS.contains(t.getName()));

            if (hasSensitive) {
                e.stopAgent();
            }
        }
        return Mono.just(event);
    }
};

// 2. 创建智能体
ReActAgent agent = ReActAgent.builder()
    .name("Assistant")
    .model(model)
    .toolkit(toolkit)
    .hook(confirmationHook)
    .build();
```

### 3.2 处理暂停和恢复

当智能体暂停时，返回的消息会包含待执行的工具信息。你需要展示给用户，并根据用户选择决定下一步：
```
Msg response = agent.call(userMsg).block();

// 检查是否有待确认的工具调用
while (response.hasContentBlocks(ToolUseBlock.class)) {
    // 展示待执行的工具
    List<ToolUseBlock> pending = response.getContentBlocks(ToolUseBlock.class);
    for (ToolUseBlock tool : pending) {
        System.out.println("工具: " + tool.getName());
        System.out.println("参数: " + tool.getInput());
    }

    if (userConfirms()) {
        // 用户确认，继续执行
        response = agent.call().block();
    } else {
        // 用户拒绝，返回取消信息
        Msg cancelResult = Msg.builder()
            .role(MsgRole.TOOL)
            .content(pending.stream()
                .map(t -> ToolResultBlock.of(t.getId(), t.getName(),
                    TextBlock.builder().text("操作已取消").build()))
                .toArray(ToolResultBlock[]::new))
            .build();
        response = agent.call(cancelResult).block();
    }
}

// 最终响应
System.out.println(response.getTextContent());
```

## 4. 实战

### 4.1 推理后审批（PostReasoningEvent）

#### 4.1.1 基础审批 Hook

我们先从一个最简单的审批 Hook 开始——当 Agent 准备调用敏感工具时，在控制台询问用户是否执行：

```java
/**
 * 敏感工具审批 Hook：在工具执行前要求人工确认
 */
public class ToolApprovalHook implements Hook {

    // 定义需要审批的敏感工具名单
    private static final Set<String> SENSITIVE_TOOLS = Set.of(
            "transfer_money",
            "delete_user",
            "update_database",
            "send_email"
    );

    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        if (event instanceof PreActingEvent e) {
            String toolName = e.getToolUse().getName();

            // 只拦截敏感工具
            if (SENSITIVE_TOOLS.contains(toolName)) {
                Map<String, Object> input = e.getToolUse().getInput();

                System.out.println("\n" + "═".repeat(50));
                System.out.println("⚠️  敏感操作待审批");
                System.out.println("═".repeat(50));
                System.out.println("工具名称: " + toolName);
                System.out.println("输入参数: " + input);
                System.out.println("─".repeat(50));
                System.out.print("是否执行？(y/n): ");

                Scanner scanner = new Scanner(System.in);
                String decision = scanner.nextLine().trim().toLowerCase();

                if (!"y".equals(decision)) {
                    // 拒绝执行：构造一个"操作被拒绝"的工具结果
                    // Agent 会收到这个反馈，而不是执行真实工具
                    e.setToolResult(ToolResultBlock.builder()
                            .name(toolName)
                            .output(List.of(TextBlock.builder()
                                    .text("操作被管理员拒绝，未执行 " + toolName)
                                    .build()))
                            .build());
                    System.out.println("❌ 操作已拒绝\n");
                } else {
                    System.out.println("✅ 操作已批准\n");
                }
            }
        }
        return Mono.just(event);
    }
}
```

**核心逻辑**：

1. 通过 `PreActingEvent` 在工具执行前拦截
2. 检查工具名是否在敏感名单内
3. 如果是，暂停并打印工具信息，等待用户输入
4. 用户输入 `n` → 调用 `e.setToolResult(...)` 注入"拒绝执行"的结果，**真实工具不会被执行**
5. 用户输入 `y` → 不做任何修改，事件继续传递，工具正常执行

#### 4.1.2 将 Hook 注册到 Agent

```java
ReActAgent agent = ReActAgent.builder()
        .name("FinancialAssistant")
        .model(chatModel)
        .toolkit(toolkit)  // 包含 transfer_money、query_balance 等工具
        .hooks(List.of(new ToolApprovalHook()))  // 注册审批 Hook
        .build();
```

#### 4.1.3 运行效果

```
用户: 给张三转账 1000 元

[Agent 思考] 需要调用 transfer_money 工具
[Hook 触发]

══════════════════════════════════════════════════
⚠️  敏感操作待审批
══════════════════════════════════════════════════
工具名称: transfer_money
输入参数: {recipient=张三, amount=1000, currency=CNY}
──────────────────────────────────────────────────
是否执行？(y/n): n
❌ 操作已拒绝

[Agent 收到结果] "操作被管理员拒绝，未执行 transfer_money"
[Agent 回复] 抱歉，转账操作未获得批准，无法完成该请求。
```

---

### 4.2 工具调用后审核（PostActingEvent）

有些场景不适合在执行前审批，而需要在看到结果后审核。例如：Agent 查询了客户信息，但返回的数据可能包含隐私字段，需要脱敏后才能传给 Agent。
```java
public class ResultReviewHook implements Hook {

    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        if (event instanceof PostActingEvent e) {
            String toolName = e.getToolUse().getName();

            // 只审核查询类工具的结果
            if ("query_customer_info".equals(toolName)) {
                ToolResultBlock result = e.getToolResult();

                System.out.println("\n" + "═".repeat(50));
                System.out.println("🔍 工具执行结果审核");
                System.out.println("═".repeat(50));
                System.out.println("工具: " + toolName);
                System.out.println("原始结果: " + result);
                System.out.println("─".repeat(50));
                System.out.print("是否接受该结果？(y/n/modify): ");

                Scanner scanner = new Scanner(System.in);
                String decision = scanner.nextLine().trim().toLowerCase();

                if ("n".equals(decision)) {
                    // 拒绝结果，让 Agent 知道查询失败
                    e.setToolResult(ToolResultBlock.builder()
                            .name(toolName)
                            .output(List.of(TextBlock.builder()
                                    .text("查询结果被审核员拒绝，请换用其他方式获取信息")
                                    .build()))
                            .build());
                } else if ("modify".equals(decision)) {
                    // 人工修正结果（如脱敏处理）
                    e.setToolResult(ToolResultBlock.builder()
                            .name(toolName)
                            .output(List.of(TextBlock.builder()
                                    .text("客户ID: *****, 姓名: 张三, 电话: 138****8888")
                                    .build()))
                            .build());
                }
                // y → 接受原始结果，不做修改
            }
        }
        return Mono.just(event);
    }
}
```

**执行后审核的典型场景**：

| 场景 | 审核内容 | 干预方式 |
|-----|---------|---------|
| SQL 查询结果 | 是否包含异常数据 | 拒绝或修正结果 |
| 外部 API 返回 | 是否符合预期格式 | 要求重试或降级 |
| 文件读取内容 | 是否包含敏感信息 | 脱敏处理后返回 |

---

## 十、总结

本文详细介绍了 AgentScope Java 中 Human-in-the-Loop 的实现方式：

| 能力 | 实现方式 | 事件类型 |
|-----|---------|---------|
| 执行前审批 | Hook 拦截 + `setToolResult` 注入拒绝结果 | `PreActingEvent` |
| 执行后审核 | Hook 拦截 + `setToolResult` 修正结果 | `PostActingEvent` |
| 分级审批 | 按工具名分类，不同风险等级不同策略 | `PreActingEvent` |
| 异步审批 | Reactor `subscribeOn` + 外部审批系统 | `PreActingEvent` |

AgentScope 的 HITL 设计非常优雅——它没有引入新的概念，而是将人工审核自然地融入了已有的 **Hook 事件系统**。掌握这一点后，你可以轻松地为任何 Agent 添加"安全刹车"，在高风险场景下确保人类始终拥有最终决策权。
