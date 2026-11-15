
在前之前文章中，我们介绍了如何通过 `DashScopeChatModel` 集成百炼模型，以及如何利用 **思考模式** 窥探模型的推理过程。本篇我们将深入 AgentScope 最核心的设计特性之一——**Hook（钩子机制）**。

如果说模型是 Agent 的"大脑"，那么 Hook 就是 AgentScope 框架的 **神经系统**：它让你能够监听 Agent 执行的每一个关键节点、捕获每一拍心跳、甚至在必要时直接干预决策。

---

## 1. 为什么需要 Hook？

在构建生产级 Agent 应用时，开发者常常面临这些需求：

| 需求 | 传统方案的痛点 | Hook 如何解决 |
|------|-------------|-------------|
| 追踪 Agent 的完整执行链路 | 日志分散，难以串联 | 在关键节点统一接收事件 |
| 审计工具调用参数和结果 | 需要侵入业务代码 | 非侵入式监听 Pre/Post Acting |
| 动态注入系统提示词 | 重启服务才能生效 | 在 PreReasoning 阶段实时修改输入 |
| 捕获异常并告警 | try-catch 块遍布各处 | 统一的 ErrorEvent 处理 |
| 人机协作（HITL） | 框架层面难以插入人工审批 | 在任意阶段暂停并等待人类输入 |

Hook 的本质是 **事件驱动的扩展点**，用于在特定执行阶段监控和修改智能体行为。——AgentScope 在 ReAct 循环的关键位置抛出事件，你的代码决定如何响应。

---

## 2. Hook 的核心设计

AgentScope Java 使用 **统一事件模型**，所有 Hook 都需要实现 `onEvent(HookEvent)` 方法：
```java
public interface Hook {
    // 优先级：数字越小优先级越高（默认 100）
    default int priority() { return 100; }

    // 统一事件入口
    <T extends HookEvent> Mono<T> onEvent(T event);
}
```
设计特点：
- **基于事件**：Agent 的所有活动都会生成对应的事件对象
- **类型安全**：对事件类型进行模式匹配。通过 Java 的 `instanceof` 模式匹配进行事件分发。
- **优先级排序**：多个 Hook 按优先级顺序执行（值越小优先级越高）
- **可修改**：特定事件允许修改执行上下文，实现干预能力

---

## 3. Hook 事件类型

AgentScope 目前提供 **12 种事件类型**，完整覆盖 Agent 从启动到结束的全生命周期：

| 事件类型 | 触发时机 | 可修改 | 描述 | 核心用途 |
| :------------- || :------------- | :------------- | :------------- | :-------------
| `PreCallEvent` | Agent 调用前 | ✅ | Agent 开始处理之前（可修改输入消息） | 初始化监控、注入上下文 |
| `PreReasoningEvent` | LLM 推理前 | ✅ | LLM 推理之前（可修改输入消息） | **动态修改输入消息、注入提示词** |
| `ReasoningChunkEvent` | 推理流式期间 | ❌ | 流式推理的每个块（仅通知）| 实时展示思考过程（配合 enableThinking） |
| `PostReasoningEvent` | LLM 推理完成后 | ✅ | LLM 推理完成之后（可修改推理结果） | 审查推理结果、修改工具调用决策 |
| `PreActingEvent` | 工具执行前 | ✅ | 工具执行之前（可修改工具参数） | **参数校验、权限检查、人工审批** |
| `ActingChunkEvent` | 工具流式期间 | ❌ | 工具执行进度块（仅通知）| 监控长耗时工具的实时进度 |
| `PostActingEvent` | 工具执行完成后 | ✅ | 工具执行之后（可修改工具结果） | 结果处理、错误包装、数据脱敏 |
| `PostCallEvent` | Agent 调用完成后 | ✅ | Agent 完成响应之后（可修改最终消息） | 最终回答加工、会话收尾 |
| `PreSummaryEvent` | 摘要生成前 | ✅ | 达到最大迭代次数时，摘要生成之前 | 控制摘要行为 |
| `PostSummaryEvent` | 摘要生成完成后 | ✅ | 摘要生成完成之后（可修改摘要结果）| 修改摘要结果 |
| `SummaryChunkEvent` | 流式摘要的每个数据块 | ❌ | 摘要流式生成的每个块（仅通知） | 实时展示摘要进度 |
| `ErrorEvent` | 发生错误时 | ❌ | 发生错误时（仅通知） | 统一异常捕获与告警 |

## 4. 创建与使用 Hook

在 AgentScope Java 中，创建 Hook 的核心是实现 `io.agentscope.core.hook.Hook` 接口。一个最基础的 Hook 只需要实现 onEvent 方法：
```java
public class SimpleHook implements Hook {
    // 统一事件处理入口
    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        if (event instanceof PreCallEvent preCall) {
            // Agent 执行前
            System.out.println("Agent 调用前: " + preCall.getAgent().getName());
        } else if (event instanceof PreReasoningEvent preReasoning) {
            // LLM 推理前
            System.out.println("LLM 推理前: " + preReasoning.getAgent().getName());
        } else if (event instanceof PostReasoningEvent postReasoning) {
            // LLM 推理完成后
            System.out.println("LLM 推理完成后: " + postReasoning.getAgent().getName());
        }
        else if (event instanceof PostCallEvent postCall) {
            // Agent 调用完成后
            System.out.println("Agent 调用完成后: " + postCall.getAgent().getName());
        }
        return Mono.just(event);
    }
}
```
在 onEvent 方法中，使用 Java 17+ 的 instanceof 模式匹配来区分不同事件。

如何使用 Hook 呢？只需要在构建智能体时通过 `hook()` 或者 `hooks()` 方法注册 Hook 即可：
```java
ReActAgent agent = ReActAgent.builder()
    .name("Assistant")
    .model(model)
    // 配置 Hook
    .hooks(List.of(new HighPriorityHook(), new LowPriorityHook()))
    .build();
```
> 智能体构造后 Hook 不可变。

对于可修改事件，可以直接调用事件对象的 setter 方法：
```java
public class PromptEnhancingHook implements Hook {
    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        if (event instanceof PreReasoningEvent e) {
            List<Msg> messages = new ArrayList<>(e.getInputMessages());
            messages.add(0, Msg.builder()
                    .role(MsgRole.SYSTEM)
                    .content(List.of(TextBlock.builder().text("逐步思考。").build()))
                    .build());
            e.setInputMessages(messages);
            return Mono.just(event);
        }
        return Mono.just(event);
    }
}
```

## 5. Hook 优先级机制：控制 Hook 执行顺序

可以通过重写 `priority()` 方法可以控制 Hook 的执行顺序：
```java
public class HighPriorityHook implements Hook {

    @Override
    public int priority() {
        return 10;  // 数字越小优先级越高（默认为 100）
    }

    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        // 此钩子在优先级 > 10 的钩子之前执行
        return Mono.just(event);
    }
}
```
当多个 Hook 同时注册时，AgentScope 按照 **优先级数值从小到大** 的顺序执行。
```java
ReActAgent agent = ReActAgent.builder()
        .name("Assistant")
        .model(model)
        .toolkit(toolkit)
        .hooks(List.of(
                new ToolApprovalHook(),        // priority: 10 (安全审批)
                new PromptEnhancingHook(),     // priority: 50 (提示词增强)
                new MonitoringHook(),          // priority: 100 (监控日志)
                new ErrorHandlingHook(alert)   // priority: 100 (错误处理)
        ))
        .build();
```
> **重要**：Agent 构造完成后，Hook 集合不可变。如需动态调整，需要重新构建 Agent 实例。

执行顺序如下所示：
```
ToolApprovalHook: Assistant
PromptEnhancingHook: Assistant
MonitoringHook: Assistant
ErrorHandlingHook: Assistant
```

Hook 优先级策略可以参考如下：

| 优先级范围 | Hook 类型 | 说明 |
|-----------|----------|------|
| 1-20 | 安全/审批类 | 最先执行，确保在业务逻辑前拦截 |
| 21-50 | 输入修改类 | 在监控前修改消息内容 |
| 51-100 | 监控/日志类 | 默认级别，观察但不干预 |
| 101-200 | 后置处理类 | 最后执行，如结果格式化、数据上报 |


## 6. 实战：从监控到干预

### 6.1 基础示例：日志追踪 Hook

最基础的用法——记录 Agent 的启动和结束：
```java
public class LoggingHook implements Hook {
    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        if (event instanceof PreCallEvent e) {
            System.out.println("[日志] Agent 启动: " + e.getAgent().getName());
        }
        if (event instanceof PostCallEvent e) {
            System.out.println("[日志] Agent 完成，耗时: " + e.getDuration() + "ms");
        }
        return Mono.just(event);
    }
}
```

### 6.2 进阶示例：完整执行链路监控

结合项目中的实际代码，构建一个能追踪 Agent 完整生命周期的 Hook：
```java
public class MonitoringHook implements Hook {
    private final long startTime = System.currentTimeMillis();

    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        switch (event) {
            case PreCallEvent e -> {
                System.out.println("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                System.out.println("🚀 [PreCall] Agent 启动: " + e.getAgent().getName());
            }
            case PreReasoningEvent e -> {
                System.out.println("🧠 [PreReasoning] 开始第 " + e.getIteration() + " 轮推理");
            }
            case ReasoningChunkEvent e -> {
                // 捕获流式思考内容（需模型开启 enableThinking）
                Msg chunk = e.getIncrementalChunk();
                // 实时输出思考片段...
            }
            case PreActingEvent e -> {
                System.out.println("🔧 [PreActing] 准备调用工具: " + e.getToolUse().getName());
                System.out.println("   参数: " + e.getToolUse().getInput());
            }
            case ActingChunkEvent e -> {
                System.out.println("⏳ [ActingChunk] 工具执行中: " + e.getToolUse().getName());
            }
            case PostActingEvent e -> {
                ToolResultBlock result = e.getToolResult();
                System.out.println("✅ [PostActing] 工具执行完成: " + e.getToolUse().getName());
                System.out.println("   结果: " + result.getOutput());
            }
            case PostReasoningEvent e -> {
                System.out.println("📝 [PostReasoning] 推理完成");
            }
            case PostCallEvent e -> {
                long duration = System.currentTimeMillis() - startTime;
                System.out.println("🏁 [PostCall] Agent 执行完成，总耗时: " + duration + "ms");
                System.out.println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
            }
            case ErrorEvent e -> {
                System.err.println("❌ [Error] 发生错误: " + e.getError().getMessage());
            }
            default -> {}
        }
        return Mono.just(event);
    }
}
```

### 6.3 高阶示例：动态修改输入消息

某些事件是 **可修改** 的，这意味着你可以直接干预 Agent 的行为。以下示例在每次推理前自动注入"逐步思考"的系统提示：
```java
public class PromptEnhancingHook implements Hook {

    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        if (event instanceof PreReasoningEvent e) {
            // 获取当前输入消息列表
            List<Msg> messages = new ArrayList<>(e.getInputMessages());

            // 在消息列表开头注入额外的系统提示
            messages.add(0, Msg.builder()
                    .role(MsgRole.SYSTEM)
                    .content(List.of(TextBlock.builder()
                            .text("请逐步思考，先分析再回答。")
                            .build()))
                    .build());

            // 修改事件中的消息列表
            e.setInputMessages(messages);
        }
        return Mono.just(event);
    }
}
```
**应用场景**：
- A/B 测试不同提示词策略
- 根据用户等级动态调整 Agent 的行为风格
- 在特定业务场景下注入领域知识

### 6.4 安全示例：工具调用审批（人机协作）

在生产环境中，某些敏感工具（如转账、删除数据）需要人工确认后才能执行：
```java
public class ToolApprovalHook implements Hook {

    private static final Set<String> SENSITIVE_TOOLS = Set.of(
            "transfer_money", "delete_user", "update_database"
    );

    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        if (event instanceof PreActingEvent e) {
            String toolName = e.getToolUse().getName();

            if (SENSITIVE_TOOLS.contains(toolName)) {
                String input = e.getToolUse().getInput();
                System.out.println("⚠️ 敏感操作待审批！");
                System.out.println("工具: " + toolName);
                System.out.println("参数: " + input);
                System.out.print("是否执行？(y/n): ");

                Scanner scanner = new Scanner(System.in);
                String decision = scanner.nextLine().trim().toLowerCase();

                if (!"y".equals(decision)) {
                    // 拒绝执行：将工具结果修改为空，Agent 会收到"操作被拒绝"的反馈
                    e.setToolResult(ToolResultBlock.builder()
                            .name(toolName)
                            .output(List.of(TextBlock.builder()
                                    .text("操作被管理员拒绝")
                                    .build()))
                            .build());
                }
            }
        }
        return Mono.just(event);
    }
}
```

### 6.5 错误处理示例：统一异常捕获

```java
public class ErrorHandlingHook implements Hook {

    private final AlertService alertService;  // 你的告警服务

    public ErrorHandlingHook(AlertService alertService) {
        this.alertService = alertService;
    }

    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        if (event instanceof ErrorEvent e) {
            String agentName = e.getAgent().getName();
            Throwable error = e.getError();

            // 记录详细错误日志
            System.err.println("Agent [" + agentName + "] 执行异常:");
            error.printStackTrace();

            // 发送告警
            alertService.sendAlert(agentName, error.getMessage());
        }
        return Mono.just(event);
    }
}
```

---

## 7. Hook 的边界与注意事项

### 7.1 不可修改事件（只读通知）

`ReasoningChunkEvent`、`ActingChunkEvent`、`SummaryChunkEvent`、`ErrorEvent` 是 **不可修改** 的——它们只在发生时通知你，你无法干预：
```java
// ❌ 错误：试图修改只读事件
if (event instanceof ReasoningChunkEvent e) {
    e.setSomething(...);  // 编译错误或运行时异常！
}
```

### 7.2 Agent 的线程安全

AgentScope 的 Agent 是 **有状态对象**（持有 Memory、Toolkit、配置等），**同一实例不能并发调用**：
```java
// ❌ 错误：多线程共享同一个 Agent
ReActAgent agent = ReActAgent.builder()...build();
executor.submit(() -> agent.call(msg1));  // 并发冲突！
executor.submit(() -> agent.call(msg2));  // 并发冲突！

// ✅ 正确：每个请求创建独立实例
executor.submit(() -> {
    ReActAgent agent = ReActAgent.builder()...build();
    agent.call(msg1);
});
```

### 7.3 Hook 中的阻塞操作

Hook 的 `onEvent` 返回 `Mono<T>`，基于 Project Reactor 的响应式编程。避免在 Hook 中执行长时间阻塞操作：
```java
// ❌ 错误：阻塞操作
public Mono<T> onEvent(T event) {
    Thread.sleep(5000);  // 阻塞事件循环！
    return Mono.just(event);
}

// ✅ 正确：使用响应式操作
public Mono<T> onEvent(T event) {
    return Mono.fromCallable(() -> {
        // 异步执行耗时操作
        return event;
    }).subscribeOn(Schedulers.boundedElastic());
}
```
---

## 8. 总结

Hook 是 AgentScope Java 实现 **透明度和可控性** 的核心机制，关键要点回顾：

| 要点 | 内容 |
|------|------|
| **核心接口** | `Hook.onEvent(HookEvent)`，统一事件入口 |
| **事件数量** | 12 种事件，覆盖 Agent 全生命周期 |
| **可修改事件** | Pre/PostCall、Pre/PostReasoning、Pre/PostActing、Pre/PostSummary |
| **不可修改事件** | Chunk 类事件（ReasoningChunk、ActingChunk、SummaryChunk）、ErrorEvent |
| **优先级** | 数字越小优先级越高，默认 100 |
| **线程安全** | Agent 实例不可并发使用，每个请求独立创建 |

Hook 让 Agent 从"黑盒"变成了"白盒"——你不仅能看到它在做什么，还能在关键时刻伸手干预。
