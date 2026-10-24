## 深入解析：Hook 可修改事件——在关键节点"伸手"干预 Agent

在 AgentScope Java 的 12 种事件中，**8 种是可修改事件**。这意味着你不仅能"看到" Agent 的执行过程，还能**直接改变它的走向**。这是实现动态提示词注入、人工审批、结果脱敏、安全拦截等高级能力的核心机制。

---

### 一、可修改事件全景图

| 事件类型 | 触发时机 | 可修改字段 | 修改能力 | 典型用途 |
|---------|---------|-----------|---------|---------|
| `PreCallEvent` | Agent 调用开始前 | `inputMessage` | 修改用户原始输入 | 输入过滤、敏感词检测 |
| `PreReasoningEvent` | 每轮 LLM 推理前 | `inputMessages` | 修改发送给模型的完整消息列表 | **动态注入提示词**、上下文增强 |
| `PostReasoningEvent` | LLM 推理完成后 | `reasoningMessage` | 修改模型的推理输出 | 拦截错误工具调用、修正参数 |
| `PreActingEvent` | 工具执行开始前 | `toolResult` | **提前设置工具结果**（跳过执行） | **权限拦截、人工审批、Mock 测试** |
| `PostActingEvent` | 工具执行完成后 | `toolResult` | 修改工具的实际返回结果 | 结果脱敏、错误包装、格式转换 |
| `PostCallEvent` | Agent 调用完成后 | `finalMessage` | 修改最终返回给用户的消息 | 输出格式化、免责声明追加 |
| `PreSummaryEvent` | 达到最大迭代次数，摘要生成前 | `inputMessages` | 修改摘要阶段的输入消息 | 控制摘要范围 |
| `PostSummaryEvent` | 摘要生成完成后 | `summaryMessage` | 修改摘要结果 | 摘要后处理 |

---

### 二、逐个详解：如何修改，修改什么效果

#### 2.1 PreCallEvent —— 修改用户原始输入

**修改能力**：在 Agent 正式开始处理前，修改用户发来的原始消息。

```java
public class InputFilterHook implements Hook {
    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        if (event instanceof PreCallEvent e) {
            Msg original = e.getInputMessage();
            String text = original.getTextContent();

            // 示例：敏感词过滤
            if (text.contains("机密密码")) {
                Msg filtered = Msg.builder()
                        .role(original.getRole())
                        .textContent("用户询问包含敏感信息，已过滤")
                        .build();
                e.setInputMessage(filtered);
            }
        }
        return Mono.just(event);
    }
}
```

**修改效果**：Agent 后续看到的"用户输入"已经被替换，原消息不会进入 Memory。

---

#### 2.2 PreReasoningEvent —— 动态注入提示词（最常用）

**修改能力**：在每次 LLM 推理前，修改发送给模型的完整消息列表。这是**最强大、最常用的修改点**。

```java
public class PromptEnhancingHook implements Hook {

    @Override
    public int priority() {
        return 50;  // 在日志 Hook 之前执行
    }

    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        if (event instanceof PreReasoningEvent e) {
            List<Msg> messages = new ArrayList<>(e.getInputMessages());

            // 在消息列表开头注入额外的系统提示
            messages.add(0, Msg.builder()
                    .role(MsgRole.SYSTEM)
                    .content(List.of(TextBlock.builder()
                            .text("你是严谨的专家，回答前请充分验证信息准确性。")
                            .build()))
                    .build());

            // 在消息列表末尾注入思维链提示
            messages.add(Msg.builder()
                    .role(MsgRole.SYSTEM)
                    .content(List.of(TextBlock.builder()
                            .text("请使用以下格式回答：\n1. 分析\n2. 结论\n3. 建议")
                            .build()))
                    .build());

            e.setInputMessages(messages);
        }
        return Mono.just(event);
    }
}
```

**消息列表结构说明**：

`PreReasoningEvent.getInputMessages()` 返回的列表通常包含：

```
[0] SYSTEM  - Agent 的系统提示词（sysPrompt）
[1] USER    - 用户输入
[2] ASSISTANT - 上一轮 Agent 回复（如有）
[3] TOOL    - 上一轮工具结果（如有）
...
```

**修改效果**：模型看到的上下文被实时改变，无需重启服务即可调整 Agent 行为。这是实现 **A/B 测试不同提示词策略** 的理想方式。

---

#### 2.3 PostReasoningEvent —— 拦截并修正推理结果

**修改能力**：LLM 推理完成后，在工具调用执行前，修改模型的推理输出。

```java
public class ReasoningInterceptorHook implements Hook {
    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        if (event instanceof PostReasoningEvent e) {
            Msg reasoningMsg = e.getReasoningMessage();

            // 遍历消息内容块，查找工具调用
            for (ContentBlock block : reasoningMsg.getContent()) {
                if (block instanceof ToolUseBlock toolUse) {
                    String toolName = toolUse.getName();

                    // 拦截高风险工具调用
                    if ("delete_database".equals(toolName)) {
                        System.out.println("⚠️ 拦截危险操作: " + toolName);

                        // 将工具调用替换为普通文本回复
                        Msg safeReply = Msg.builder()
                                .role(MsgRole.ASSISTANT)
                                .textContent("抱歉，删除数据库操作需要人工确认，请联系管理员。")
                                .build();

                        e.setReasoningMessage(safeReply);
                        return Mono.just(event);
                    }
                }
            }
        }
        return Mono.just(event);
    }
}
```

**修改效果**：Agent 原本打算调用 `delete_database`，但被我们替换为安全回复，工具不会被执行。

---

#### 2.4 PreActingEvent —— 权限拦截与人工审批（最强控制点）

**修改能力**：在工具**即将执行前**，提前设置工具结果。这意味着你可以**完全跳过工具的实际执行**，直接给 Agent 一个"伪造"的结果。

这是实现**人机协作（HITL）**和**权限控制**的核心机制。

```java
public class ToolApprovalHook implements Hook {

    private static final Set<String> SENSITIVE_TOOLS = Set.of(
            "transfer_money", "delete_user", "execute_sql"
    );

    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        if (event instanceof PreActingEvent e) {
            ToolUseBlock toolUse = e.getToolUse();
            String toolName = toolUse.getName();

            if (SENSITIVE_TOOLS.contains(toolName)) {
                // 展示审批信息
                System.out.println("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                System.out.println("⚠️ 敏感操作待审批");
                System.out.println("工具: " + toolName);
                System.out.println("参数: " + toolUse.getInput());
                System.out.print("是否执行？(y/n): ");

                Scanner scanner = new Scanner(System.in);
                String decision = scanner.nextLine().trim().toLowerCase();

                if (!"y".equals(decision)) {
                    // 拒绝执行：直接设置工具结果，跳过实际调用
                    ToolResultBlock rejectedResult = ToolResultBlock.builder()
                            .name(toolName)
                            .output(List.of(TextBlock.builder()
                                    .text("操作被管理员拒绝执行")
                                    .build()))
                            .build();

                    e.setToolResult(rejectedResult);
                    System.out.println("❌ 已拒绝");
                } else {
                    System.out.println("✅ 已批准，继续执行");
                }
                System.out.println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
            }
        }
        return Mono.just(event);
    }
}
```

**修改效果**：

| 场景 | 是否设置 `toolResult` | 结果 |
|------|---------------------|------|
| 未设置 | 否 | 框架正常执行工具，结果进入下一轮推理 |
| 已设置 | 是 | **工具不会被执行**，你设置的 `toolResult` 直接进入 Memory |

这是 Hook 机制中最强的控制手段——在工具执行前"截胡"。

---

#### 2.5 PostActingEvent —— 结果后处理

**修改能力**：工具已经执行完成，但在结果进入 Agent Memory 前，修改返回内容。

```java
public class ResultSanitizationHook implements Hook {
    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        if (event instanceof PostActingEvent e) {
            ToolResultBlock original = e.getToolResult();

            // 遍历工具结果内容
            List<ContentBlock> sanitizedOutput = original.getOutput().stream()
                    .map(block -> {
                        if (block instanceof TextBlock text) {
                            String content = text.getText();
                            // 脱敏处理：隐藏手机号
                            String masked = content.replaceAll(
                                    "(\\d{3})\\d{4}(\\d{4})",
                                    "$1****$2");
                            return TextBlock.builder().text(masked).build();
                        }
                        return block;
                    })
                    .collect(Collectors.toList());

            // 替换为脱敏后的结果
            ToolResultBlock sanitized = ToolResultBlock.builder()
                    .name(original.getName())
                    .output(sanitizedOutput)
                    .build();

            e.setToolResult(sanitized);
        }
        return Mono.just(event);
    }
}
```

**修改效果**：Agent 看到的是脱敏后的数据（`138****1234`），而非原始数据。这在金融、医疗等隐私敏感场景至关重要。

---

#### 2.6 PostCallEvent —— 修改最终输出

**修改能力**：Agent 调用完全结束后，修改返回给调用方的最终消息。

```java
public class OutputEnhancementHook implements Hook {
    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        if (event instanceof PostCallEvent e) {
            Msg finalMsg = e.getFinalMessage();
            String originalText = finalMsg.getTextContent();

            // 追加免责声明
            String enhanced = originalText + "\n\n---\n" +
                    "免责声明：本回答由 AI 生成，仅供参考，不构成专业建议。";

            Msg enhancedMsg = Msg.builder()
                    .role(finalMsg.getRole())
                    .name(finalMsg.getName())
                    .textContent(enhanced)
                    .build();

            e.setFinalMessage(enhancedMsg);
        }
        return Mono.just(event);
    }
}
```

**修改效果**：用户看到的最终回答末尾自动追加了免责声明，无需修改 Agent 的 sysPrompt。

---

#### 2.7 PreSummaryEvent / PostSummaryEvent —— 控制摘要行为

当 Agent 达到 `maxIters` 最大迭代次数仍未完成任务时，会触发**摘要生成**流程。这两个事件让你能控制摘要阶段的行为。

```java
public class SummaryControlHook implements Hook {
    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        if (event instanceof PreSummaryEvent e) {
            // 在摘要前精简消息列表，只保留关键信息
            List<Msg> messages = e.getInputMessages();
            List<Msg> essential = messages.stream()
                    .filter(m -> m.getRole() == MsgRole.USER
                            || m.getRole() == MsgRole.TOOL)
                    .collect(Collectors.toList());

            e.setInputMessages(essential);
        }

        if (event instanceof PostSummaryEvent e) {
            Msg summary = e.getSummaryMessage();
            // 可以在摘要结果后追加额外信息
            String enhanced = summary.getTextContent()
                    + "\n[注：由于复杂度超出，任务未能完全完成]";

            e.setSummaryMessage(Msg.builder()
                    .role(summary.getRole())
                    .textContent(enhanced)
                    .build());
        }

        return Mono.just(event);
    }
}
```

---

### 三、可修改事件的修改链效应

需要注意的是，**多个 Hook 对同一事件的修改是链式的**。例如：

```java
// Hook A (priority 10): 在 PreReasoningEvent 中添加系统提示 A
// Hook B (priority 20): 在 PreReasoningEvent 中添加系统提示 B
// Hook C (priority 30): 在 PreReasoningEvent 中记录日志（只读）

// 执行顺序：
// 1. Hook A 修改 inputMessages -> [系统A, 原始消息...]
// 2. Hook B 修改 inputMessages -> [系统A, 系统B, 原始消息...]
// 3. Hook C 读取到的是已经被 A 和 B 修改后的消息列表
```

**最佳实践**：优先级高的 Hook 做"修改"，优先级低的 Hook 做"观测"。

---

### 四、修改的边界与限制

#### 4.1 不能修改的事件

以下 4 种事件是**只读**的，任何修改尝试都会导致编译错误或运行时异常：

| 事件类型 | 原因 |
|---------|------|
| `ReasoningChunkEvent` | 流式数据块，只负责通知 |
| `ActingChunkEvent` | 流式进度块，只负责通知 |
| `SummaryChunkEvent` | 流式摘要块，只负责通知 |
| `ErrorEvent` | 错误已发生，不可回溯修改 |

#### 4.2 修改的生效时机

| 事件 | 修改何时生效 |
|------|------------|
| `PreCallEvent` | 立即生效，影响本轮整个调用 |
| `PreReasoningEvent` | 本轮推理的输入被修改 |
| `PostReasoningEvent` | 本轮推理的输出被替换 |
| `PreActingEvent` | 如设置 `toolResult`，**工具不会执行** |
| `PostActingEvent` | 工具结果进入 Memory 前被替换 |
| `PostCallEvent` | 最终返回的消息被替换 |
| `PreSummaryEvent` | 摘要阶段的输入被修改 |
| `PostSummaryEvent` | 摘要结果进入最终输出前被替换 |

#### 4.3 线程安全注意

修改事件对象本身是**线程安全的**（单个事件只在一个线程中处理），但要注意你修改的内容是否线程安全：

```java
// ❌ 错误：使用共享的可变状态
private final List<String> sharedList = new ArrayList<>();  // 线程不安全！

@Override
public <T extends HookEvent> Mono<T> onEvent(T event) {
    if (event instanceof PreReasoningEvent e) {
        sharedList.add("something");  // 并发冲突！
    }
    return Mono.just(event);
}

// ✅ 正确：每个事件独立处理，不依赖共享可变状态
@Override
public <T extends HookEvent> Mono<T> onEvent(T event) {
    if (event instanceof PreReasoningEvent e) {
        List<Msg> newList = new ArrayList<>(e.getInputMessages());  // 新建列表
        newList.add(Msg.builder()...build());
        e.setInputMessages(newList);
    }
    return Mono.just(event);
}
```

---

### 五、实战：可修改事件的组合策略

以下示例展示了如何在生产环境中组合使用多个可修改事件：

```java
public class ProductionHookBundle implements Hook {

    @Override
    public int priority() {
        return 10;  // 高优先级，确保最先执行修改
    }

    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        switch (event) {
            // 1. 输入阶段：注入审计上下文
            case PreCallEvent e -> {
                Msg original = e.getInputMessage();
                // 在 metadata 中注入追踪 ID（如果 Msg 支持）
            }

            // 2. 推理阶段：动态调整提示词
            case PreReasoningEvent e -> {
                List<Msg> messages = new ArrayList<>(e.getInputMessages());

                // 如果是第 3 轮以上，追加"尽快收敛"提示
                if (e.getIteration() >= 3) {
                    messages.add(Msg.builder()
                            .role(MsgRole.SYSTEM)
                            .textContent("已进行多轮推理，请尽快给出最终结论。")
                            .build());
                }

                e.setInputMessages(messages);
            }

            // 3. 工具阶段：拦截敏感操作
            case PreActingEvent e -> {
                if ("high_risk_tool".equals(e.getToolUse().getName())) {
                    e.setToolResult(ToolResultBlock.builder()
                            .name(e.getToolUse().getName())
                            .output(List.of(TextBlock.builder()
                                    .text("高风险操作已拦截")
                                    .build()))
                            .build());
                }
            }

            // 4. 结果阶段：数据脱敏
            case PostActingEvent e -> {
                ToolResultBlock result = e.getToolResult();
                // 脱敏逻辑...
            }

            // 5. 输出阶段：追加合规声明
            case PostCallEvent e -> {
                Msg finalMsg = e.getFinalMessage();
                String withDisclaimer = finalMsg.getTextContent()
                        + "\n\n[AI 生成内容，仅供参考]";
                e.setFinalMessage(Msg.builder()
                        .role(finalMsg.getRole())
                        .textContent(withDisclaimer)
                        .build());
            }

            default -> {}
        }

        return Mono.just(event);
    }
}
```

---

### 六、总结：可修改事件速查表

| 你想做什么 | 使用哪个事件 | 修改方法 |
|-----------|------------|---------|
| 过滤用户输入 | `PreCallEvent` | `setInputMessage(Msg)` |
| 动态注入提示词 | `PreReasoningEvent` | `setInputMessages(List<Msg>)` |
| 拦截错误工具调用 | `PostReasoningEvent` | `setReasoningMessage(Msg)` |
| 跳过工具执行（Mock/审批） | `PreActingEvent` | `setToolResult(ToolResultBlock)` |
| 修改工具返回结果 | `PostActingEvent` | `setToolResult(ToolResultBlock)` |
| 格式化最终输出 | `PostCallEvent` | `setFinalMessage(Msg)` |
| 控制摘要输入 | `PreSummaryEvent` | `setInputMessages(List<Msg>)` |
| 修改摘要结果 | `PostSummaryEvent` | `setSummaryMessage(Msg)` |

可修改事件是 AgentScope Hook 机制的灵魂所在。它们将 Agent 从"只能观测的黑盒"变成了"随时可干预的白盒"——在合适的时机，于合适的节点，做出合适的修改，这正是构建企业级 Agent 应用的基石能力。
