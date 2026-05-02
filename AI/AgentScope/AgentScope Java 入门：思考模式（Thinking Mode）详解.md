## 1. 什么是思考模式？

**思考模式（Thinking Mode）** 是通义千问 3 系列模型（`qwen3.6-max-preview`、`qwen3.6-plus`、`qwen3-max` 等）独有的能力。启用后，模型在给出最终回答之前，会先输出一段 **内部推理过程**（Chain-of-Thought），展示它是如何一步步分析问题、拆解任务、做出决策的。

你可以把它理解为：模型在回答你之前，先在草稿纸上写了一遍"解题思路"。

### 思考模式 vs 普通模式的区别

**普通模式**：
```
用户：为什么 1+1=2？

模型：1+1=2 是皮亚诺算术公理的基本结论...
```

**思考模式**：
```
用户：为什么 1+1=2？

[思考过程]
我需要从数学基础角度回答这个问题。首先，1+1=2 不是"证明"出来的，
而是基于皮亚诺公理的定义。让我梳理一下：
1. 皮亚诺公理定义了自然数和后继函数 S()
2. 1 被定义为 S(0)，2 被定义为 S(1)
3. 因此 1+1 = 1+S(0) = S(1+0) = S(1) = 2
这属于定义性真理，不是经验归纳。

[最终回答]
1+1=2 是皮亚诺算术公理的基本结论...
```

---

## 2. 为什么 Agent 开发特别需要思考模式？

在 ReActAgent 的场景下，思考模式的价值被放大了：

| 价值点 | 说明 |
|--------|------|
| **调试 Agent 决策链** | 你能看到 Agent 为什么要调用某个工具、参数是怎么确定的 |
| **优化提示词（Prompt）** | 通过观察模型的推理路径，发现提示词中的歧义或缺失 |
| **建立用户信任** | 向用户展示"AI 不是瞎猜的"，提高透明度 |
| **发现推理缺陷** | 当 Agent 做出错误决策时，能快速定位是推理问题还是工具问题 |
| **教学与审计** | 在教育、金融、医疗等场景，推理过程本身就是价值输出 |

---

## 3. AgentScope 中开启思考模式

### 3.1 基础配置

```java
DashScopeChatModel model = DashScopeChatModel.builder()
        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
        .modelName("qwen3.6-max-preview")  // 或 qwen3.6-plus / qwen3-max
        .enableThinking(true)               // 启用思考模式
        .defaultOptions(GenerateOptions.builder()
                .thinkingBudget(5000)        // 思考 token 预算（可选）
                .build())
        .build();
```

**关键配置说明**：

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `enableThinking` | `boolean` | 是否启用思考模式，默认 `false` |
| `thinkingBudget` | `int` | 分配给思考过程的最大 token 数，默认由模型自动决定 |

> 注意：启用 `enableThinking` 后，框架会自动开启**流式输出**（`stream=true`），因为思考过程通常需要实时展示。

### 3.2 支持的模型

并非所有百炼模型都支持思考模式，目前主要支持：

| 模型 | 支持思考模式 |
|------|:-----------:|
| `qwen3.6-max-preview` | ✅ |
| `qwen3.6-plus` | ✅ |
| `qwen3.6-flash` | ✅ |
| `qwen3-max` | ✅ |
| `qwen3-max-2026-01-23` | ✅ |
| `qwen-plus` | ❌ |
| `qwen-turbo` | ❌ |

---

## 4. 捕获并展示思考过程：Hook + ThinkingBlock

启用思考模式后，AgentScope 会将模型的推理内容包装为 `ThinkingBlock`，你可以通过 **Hook 机制** 捕获并展示。

### 4.1 完整示例：实时显示 Agent 的"内心独白"

```java
public class ThinkingModeDemo {

    public static void main(String[] args) {
        // 1. 创建启用思考模式的模型
        DashScopeChatModel model = DashScopeChatModel.builder()
                .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                .modelName("qwen3.6-max-preview")
                .enableThinking(true)
                .defaultOptions(GenerateOptions.builder()
                        .thinkingBudget(5000)
                        .build())
                .build();

        // 2. 定义调试 Hook：捕获思考过程
        Hook debugHook = new Hook() {
            @Override
            public <T extends HookEvent> Mono<T> onEvent(T event) {
                switch (event) {
                    case PreReasoningEvent e -> {
                        System.out.println("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                        System.out.println("🧠 [Agent 开始思考]");
                        System.out.println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                    }
                    case PostReasoningEvent e -> {
                        Msg reasoningMsg = e.getReasoningMessage();
                        for (ContentBlock block : reasoningMsg.getContent()) {
                            if (block instanceof ThinkingBlock thinking) {
                                System.out.println("\n💭 [思考内容]");
                                System.out.println(thinking.getThinking());
                            }
                        }
                    }
                    case PostActingEvent e -> {
                        System.out.println("\n🔧 [工具执行] → " + e.getToolResult().getName());
                    }
                    case PostCallEvent e -> {
                        System.out.println("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                        System.out.println("✅ [最终回答]");
                        System.out.println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                        System.out.println(e.getFinalMessage().getTextContent());
                    }
                    default -> {}
                }
                return Mono.just(event);
            }
        };

        // 3. 创建带 Hook 的 ReActAgent
        ReActAgent agent = ReActAgent.builder()
                .name("ThinkingAgent")
                .sysPrompt("你是一位严谨的助手，回答前请充分思考。")
                .model(model)
                .hook(debugHook)
                .maxIters(10)
                .build();

        // 4. 调用
        Msg response = agent.call(
                Msg.builder()
                        .role(MsgRole.USER)
                        .textContent("杭州明天适合户外运动吗？")
                        .build()
        ).block();
    }
}
```

### 4.2 预期输出效果

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 [Agent 开始思考]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💭 [思考内容]
用户问的是杭州明天是否适合户外运动。我需要先获取杭州明天的天气信息，
然后基于天气条件判断是否适合户外运动。

让我分析一下需要什么信息：
1. 杭州明天的天气状况（晴/雨/多云）
2. 气温范围
3. 风力情况

我有 getWeather 工具可以查询天气。让我调用它。

🔧 [工具执行] → getWeather

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 [Agent 开始思考]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💭 [思考内容]
工具返回了杭州明天的天气：多云，18-26°C，东北风2级。
这个条件非常适合户外运动：
- 不是雨天
- 温度适中（18-26°C）
- 风力较小（2级）

我可以直接给出肯定回答了。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ [最终回答]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
杭州明天天气多云，气温 18-26°C，东北风 2 级，非常适合户外运动！
建议穿着轻便透气的衣物，注意防晒。
```

---

## 5. 通过流式输出实时展示思考过程

如果你希望像 ChatGPT 的 o1 模型那样，**实时看到模型一边思考一边打字**，可以使用 `stream()` 方法：

```java
import io.agentscope.core.message.content.ThinkingBlock;
import io.agentscope.core.message.content.TextBlock;
import io.agentscope.core.stream.EventType;
import io.agentscope.core.stream.StreamOptions;

public class StreamThinkingDemo {

    public static void main(String[] args) {
        DashScopeChatModel model = DashScopeChatModel.builder()
                .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                .modelName("qwen3.6-max-preview")
                .enableThinking(true)
                .build();

        ReActAgent agent = ReActAgent.builder()
                .name("StreamAgent")
                .model(model)
                .build();

        Msg msg = Msg.builder()
                .role(MsgRole.USER)
                .textContent("解释量子纠缠的原理")
                .build();

        // 配置流式选项：同时接收推理事件和最终结果
        StreamOptions streamOptions = StreamOptions.builder()
                .eventTypes(EventType.REASONING, EventType.TOOL_RESULT)
                .incremental(true)        // 增量输出，像打字机效果
                .includeReasoningResult(true)  // 包含推理结果
                .build();

        System.out.println("🧠 思考中...\n");

        agent.stream(msg, streamOptions)
                .doOnNext(event -> {
                    Msg chunk = event.getMessage();
                    for (ContentBlock block : chunk.getContent()) {
                        if (block instanceof ThinkingBlock t) {
                            System.out.print(t.getThinking());  // 实时打印思考内容
                        } else if (block instanceof TextBlock text) {
                            System.out.print(text.getText());   // 实时打印回答内容
                        }
                    }
                })
                .doOnComplete(() -> System.out.println("\n\n✅ 完成"))
                .blockLast();
    }
}
```

---

## 六、思考模式的最佳实践

### 6.1 合理设置 thinkingBudget

思考模式会消耗额外的 token，建议根据任务复杂度设置预算：

| 任务类型 | 建议 thinkingBudget | 说明 |
|---------|-------------------|------|
| 简单问答 | 1000-2000 | 事实性问题，推理链路短 |
| 工具调用 | 2000-4000 | ReAct 迭代，需要规划工具使用 |
| 复杂推理 | 4000-8000 | 数学证明、代码生成、多步分析 |
| 开放创作 | 2000-3000 | 创意写作，不需要过度推理 |

```java
// 复杂推理场景
.defaultOptions(GenerateOptions.builder()
        .thinkingBudget(8000)
        .maxTokens(4000)  // 最终回答也要给足空间
        .build())
```

### 6.2 生产环境建议

思考模式虽然强大，但在生产环境需要注意：

| 注意事项 | 建议 |
|---------|------|
| **成本** | 思考 token 也计费，复杂任务成本可能翻倍 |
| **延迟** | 思考过程增加响应时间，高并发场景谨慎使用 |
| **日志存储** | 思考内容可能很长，日志存储需预留空间 |
| **用户体验** | 思考过程可折叠展示，避免干扰最终回答 |
| **调试 vs 生产** | 开发阶段全开思考模式，生产环境可关闭或仅记录 |

### 6.3 思考内容过滤展示

如果你只想在开发调试时看到思考过程，给用户只展示最终回答：

```java
Hook productionHook = new Hook() {
    @Override
    public <T extends HookEvent> Mono<T> onEvent(T event) {
        if (event instanceof PostCallEvent e) {
            // 只输出最终回答，不输出思考过程
            // 思考过程已记录到日志系统
            System.out.println(e.getFinalMessage().getTextContent());
        }
        return Mono.just(event);
    }
};
```

---

## 七、思考模式与 ReAct 范式的关系

思考模式和 ReAct 范式是**互补**的：

| 维度 | ReAct 范式 | 思考模式 |
|------|-----------|---------|
| **层面** | Agent 框架层（AgentScope） | 模型层（通义千问） |
| **作用** | 编排"推理 → 行动"的外部循环 | 展示模型内部的推理链条 |
| **粒度** | 跨工具的宏观决策 | 单次模型调用内的微观思考 |
| **可控性** | 开发者控制迭代逻辑 | 模型自主生成 |

**实际效果**：ReActAgent 在每次 `Reasoning` 阶段调用模型时，如果开启了思考模式，你能看到模型**内部是如何决定调用哪个工具的**——这是调试 Agent 行为最锐利的武器。

---

## 八、总结

| 要点 | 内容 |
|------|------|
| **核心作用** | 让模型展示内部推理过程，提高透明度和可调试性 |
| **开启方式** | `.enableThinking(true)` + 可选 `.thinkingBudget(n)` |
| **捕获方式** | 通过 Hook 监听 `PostReasoningEvent`，解析 `ThinkingBlock` |
| **展示方式** | 流式实时输出（`stream()`）或事后完整展示 |
| **适用模型** | qwen3.6 系列、qwen3-max 系列 |
| **注意事项** | 增加 token 消耗和延迟，生产环境按需开启 |

思考模式是 AgentScope Java 中最有价值的调试工具之一。当你遇到 Agent"莫名其妙地调用了错误的工具"或"给出了不合理的回答"时，打开思考模式，看看模型到底在想什么——答案往往就在它的"内心独白"里。
