在前面的[模型集成系列](https://smartsi.blog.csdn.net/article/details/161335847)中，我们详细介绍了如何让 AgentScope Java 接入各类大语言模型——这相当于为 Agent 装上了"大脑"。但只有大脑还不够，本篇我们将聚焦 Agent 的另一关键能力：**Tool（工具）系统**——也就是 Agent 的"手脚"。

如果把大语言模型比作 Agent 的"大脑"，那么 Tool 系统就是 Agent 的"手脚"，让它不仅能"思考"，更能"行动"——查询天气、操作数据库、调用外部 API，甚至控制物理设备。本文将带你深入剖析 AgentScope Java 中的 Tool 工具系统，从设计哲学到实战用法，全方位解读这一核心模块。

---

## 1. 为什么 Agent 需要工具？

大语言模型的本质能力是"生成文本"，但它无法：
- 获取实时信息（今天杭州天气？）
- 执行计算（123 × 456 = ?）
- 操作外部系统（查询订单、发送邮件）
- 读写本地文件

**工具（Tool）弥补了 LLM 的这三个短板：**

| 短板 | 工具如何解决 |
|------|------------|
| 知识截止 | 调用搜索引擎或知识库 API 获取实时信息 |
| 计算不准 | 调用精确的计算器或代码执行器 |
| 无法行动 | 调用业务 API 完成实际操作 |

AgentScope 的 ReActAgent 通过 **Reasoning（推理）→ Acting（行动）** 的循环，让模型自主决定何时调用什么工具、传入什么参数，从而实现"能思考、会行动"的完整智能体。

---

## 2. 工具核心特性

| 特性 | 说明 |
|------|------|
| **注解驱动** | `@Tool` + `@ToolParam` 几行注解即可定义工具 |
| **响应式编程** | 原生支持 `Mono` / `Flux` 异步执行 |
| **自动 Schema** | 框架自动生成 JSON Schema 供 LLM 理解 |
| **工具组管理** | 按场景分组，支持动态激活 / 停用 |
| **预设参数** | 隐藏敏感参数（API Key、连接串）不暴露给 LLM |
| **执行上下文** | 自动注入业务对象（用户身份、租户信息） |
| **并行执行** | 支持模型一次返回多个工具时并行调用 |
| **工具挂起** | 支持人工审批、外部异步执行 |

---

## 3. 快速开始：你的第一个工具

### 3.1 定义一个工具 Tool

创建一个 Java 类，用 `@Tool` 和 `@ToolParam` 注解标记方法：
```java
public class WeatherService {
    @Tool(name = "get_weather", description = "获取指定城市的天气")
    public String getWeather(@ToolParam(name = "city", description = "城市名称") String city) {
        return city + " 的天气：晴天，25°C";
    }
}
```

> **注意**：`@ToolParam` 的 `name` 属性必须指定，因为 Java 默认不保留参数名。

### 3.2 注册工具到工具集

`Toolkit` 是工具的容器，负责管理工具的生命周期和调用。定义好工具后，需要将其注册到工具集 Toolkit 中：
```java
Toolkit toolkit = new Toolkit();

// 方式一：注册单个工具实例
toolkit.registerTool(new WeatherService());
toolkit.registerTool(new Calculator());

// 方式二：链式注册
toolkit.registerTool(new WeatherService())
       .registerTool(new Calculator());
```

注册时可通过 `ToolkitConfig` 控制全局行为：
```java
Toolkit toolkit = new Toolkit(ToolkitConfig.builder()
        .parallel(true)                           // 并行执行多个工具
        .allowToolDeletion(true)                  // 允许动态删除工具
        .executionConfig(ExecutionConfig.builder()
                .timeout(Duration.ofSeconds(30))  // 工具执行超时
                .maxAttempts(1)                   // 失败重试次数
                .build())
        .build());
```

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `parallel` | 当模型一次请求调用多个工具时，是否并行执行 | `false` |
| `allowToolDeletion` | 是否允许动态删除已注册的工具 | `true` |
| `executionConfig.timeout` | 单个工具的最大执行时间 | 5 分钟 |
| `executionConfig.maxAttempts` | 工具失败后的重试次数 | 1 |

注册后可动态管理工具：
```java
// 查询已注册的工具
Collection<AgentTool> tools = toolkit.getTools();

// 动态移除工具
toolkit.removeTool("get_weather");

// 检查工具是否存在
boolean exists = toolkit.hasTool("calculate");
```

### 3.3 创建带工具的 Agent

最后，将装配好的 Toolkit 注入到 ReActAgent 中，这样 Agent 便拥有了使用工具的能力：
```java
ReActAgent agent = ReActAgent.builder()
    .name("天气助手")
    .model(model)
    .toolkit(toolkit) // 绑定工具集
    .build();
```
当用户询问天气时，Agent 会自动推理并调用 get_weather 工具获取天气：
```java
Msg response = agent.call(
        Msg.builder()
                .role(MsgRole.USER)
                .textContent("北京明天的天气如何？")
                .build()
).block();

System.out.println(response.getTextContent());
```

执行流程：
```
用户：北京明天的天气如何？
    │
    ▼
Agent 推理：用户问天气 → 我有 get_weather 工具 → 需要传入 city="北京"
    │
    ▼
调用工具：get_weather("北京") → "北京：晴天，气温 25°C，微风"
    │
    ▼
Agent 再次推理：已获得天气信息 → 组织语言回答
    │
    ▼
回答：根据查询，北京明天天气晴朗，气温 25°C，适合出门！
```

---

## 4. 核心注解详解

### 4.1 @Tool —— 标记工具方法

```java
@Tool(
    name = "get_weather",        // 工具名称（可选，默认方法名）
    description = "获取指定城市的天气"      // 工具描述（必填，LLM 靠它理解用途）
)
public String getWeather(...) { }
```

| 属性 | 必填 | 说明 |
|------|:----:|------|
| `name` | 否 | 工具名称，默认取方法名。建议显式指定，避免方法重命名后 LLM 认知断裂 |
| `description` | **是** | **最关键字段**。LLM 完全依赖它判断何时调用该工具，必须描述清楚用途、场景和返回格式 |

**description 书写最佳实践**：
```java
// ❌ 差：描述过于模糊
@Tool(description = "天气工具")

// ✅ 好：描述清晰、具体、包含使用场景
@Tool(description = "获取指定城市的实时天气信息，包括天气状况、气温、风力。当用户询问天气、出行建议、穿衣指南时使用。")
```

### 4.2 @ToolParam —— 标记工具参数

```java
@ToolParam(
    name = "city",              // 参数名称（必填）
    description = "中文城市名称，例如北京"     // 参数描述（必填）
)
String city
```

| 属性 | 必填 | 说明 |
|------|:----:|------|
| `name` | **是** | 参数名。**必须显式指定**，因为 Java 运行时默认不保留参数名 |
| `description` | **是** | 参数描述。帮助 LLM 理解该参数的含义和格式 |

> **关键提示**：`@ToolParam` 的 `description` 直接影响 LLM 能否正确传参。建议在描述中给出 **示例值** 和 **格式约束**，如 `"日期，格式 YYYY-MM-DD，如 2026-05-20"`。

---

## 5. 工具类型

根据工具返回类型可以分为三类工具：

| 工具 | 返回类型 | 说明
| :------------- | :------------- | :------------- |
| 同步工具 | `String`, `int`, `Object` 等 | 同步执行，自动转换为 `ToolResultBlock` |
| 异步工具 | `Mono<T>`, `Flux<T>` | 异步执行 |
| 流式工具 | `ToolResultBlock` | 直接控制返回格式（文本、图片、错误等） |

### 5.1 同步工具

直接返回结果，框架自动转换为 `ToolResultBlock`，适合快速操作（计算、内存查询等）：
```java
@Tool(description = "计算两数之和")
public int add(
        @ToolParam(name = "a", description = "第一个数") int a,
        @ToolParam(name = "b", description = "第二个数") int b) {
    return a + b;
}
```
**支持的返回类型**：`String`、`int`、`long`、`double`、`boolean`、任意 POJO（自动转为 JSON）。

### 5.2 异步工具

返回 `Mono<T>` 或 `Flux<T>`，适合 I/O 密集型操作（HTTP 调用、数据库查询等）：
```java
@Tool(description = "异步搜索")
public Mono<String> search(@ToolParam(name = "query", description = "搜索词") String query) {
    return webClient.get()
        .uri("/search?q=" + query)
        .retrieve()
        .bodyToMono(String.class);
}
```
AgentScope 会自动订阅 `Mono`，异步等待结果返回给模型。

### 5.3 流式工具

使用 `ToolEmitter` 发送中间进度，适合长时间任务：
```java
@Tool(description = "批量处理数据并生成报告")
public ToolResultBlock batchProcess(
        @ToolParam(name = "count", description = "处理数量") int count,
        ToolEmitter emitter) {  // 自动注入，无需 @ToolParam

        for (int i = 0; i < count; i++) {
            // 发送进度更新（仅对 Hook 可见，不会发送给 LLM）
            emitter.emit(ToolResultBlock.text("进度: " + (i + 1) + "/" + count));

            // 模拟处理耗时
            try { Thread.sleep(100); }
            catch (InterruptedException ignored) {}
        }

        return ToolResultBlock.text("处理完成，共处理 " + count + " 条数据");
    }
}
```
**流式进度监控**：配合 `ActingChunkEvent` Hook，可以实时展示工具执行进度：
```java
if (event instanceof ActingChunkEvent e) {
    ToolResultBlock chunk = e.getChunk();
    String progress = chunk.getOutput().get(0).toString();
    System.out.println("⏳ " + progress);  // 输出: 进度: 3/100
}
```

> **注意**：流式进度仅对 Hook 可见，**不会发送给 LLM**——避免污染上下文。

---

## 6. 高级特性

### 6.1 工具组 ToolGroup

当工具数量增多时，可以通过 **工具组** 按场景分类管理，并支持动态激活/停用：
```java
// 1. 创建工具组
toolkit.createToolGroup("basic", "基础工具", true);    // 默认激活
toolkit.createToolGroup("admin", "管理工具", false);   // 默认停用
toolkit.createToolGroup("finance", "财务工具", false);

// 2. 注册工具到指定组
toolkit.registration()
        .tool(new WeatherService())
        .tool(new Calculator())
        .group("basic")
        .apply();

toolkit.registration()
        .tool(new UserAdminTool())
        .tool(new DataExportTool())
        .group("admin")
        .apply();

toolkit.registration()
        .tool(new InvoiceTool())
        .tool(new ReportTool())
        .group("finance")
        .apply();
```

按场景管理工具，支持动态激活/停用：
```java
// 激活管理工具（用于管理员用户）
toolkit.updateToolGroups(List.of("admin"), true);

// 激活财务工具（用于财务场景）
toolkit.updateToolGroups(List.of("finance"), true);

// 停用基础工具（某些特殊场景不需要）
toolkit.updateToolGroups(List.of("basic"), false);
```

**典型应用场景**：

| 场景 | 用法 |
|------|------|
| **权限控制** | 普通用户只激活 `basic` 组，管理员额外激活 `admin` 组 |
| **场景切换** | 客服场景激活 `query` 组，运维场景激活 `deploy` 组 |
| **性能优化** | 减少 LLM 可见的工具数量，降低决策负担 |

### 6.2 预设参数

有些工具需要 API Key、数据库连接串等敏感参数，但这些信息 **绝不能暴露给 LLM**。AgentScope 提供了 **预设参数** 机制：
```java
public class EmailService {
    @Tool(description = "发送邮件")
    public String send(
            @ToolParam(name = "to", description = "收件人邮箱") String to,
            @ToolParam(name = "subject", description = "邮件主题") String subject,
            @ToolParam(name = "content", description = "邮件正文") String content,
            @ToolParam(name = "apiKey", description = "邮件服务 API Key") String apiKey) {
        // 使用 apiKey 调用邮件服务
        return "邮件已发送至 " + to;
    }
}

public static void main(String[] args) throws Exception {
    // 1. 创建工具集
    Toolkit toolkit = new Toolkit();

    // 2. 注册工具并预设敏感参数
    // presetParameters 结构: Map<工具名, Map<参数名, 参数值>>
    //   - 外层 key  ：@Tool 方法名（这里 EmailService.send，默认以方法名作为工具名）
    //   - 内层 key  ：@ToolParam 参数名（apiKey）
    //   - 内层 value：注入的实际值，来源于环境变量、配置中心、密钥管理服务等
    toolkit.registration()
            .tool(new EmailService())
            .presetParameters(
                    Map.of(
                            "send",
                            Map.of("apiKey", System.getenv("EMAIL_API_KEY"))
                    )
            )
            .apply();

    System.out.println("已注册工具：send（apiKey 已预设，对 LLM 不可见）");

    // 3. 创建 Agent
    ReActAgent agent = ReActAgent.builder()
            .name("邮件小助手")
            .sysPrompt("你是一个邮件助手，当用户请求发送邮件时，使用 send 工具。")
            .model(DashScopeChatModel.builder()
                    .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                    .modelName(MODEL_NAME)
                    .build())
            .toolkit(toolkit) // 绑定工具集
            .build();

    // 4. 调用智能体：用户请求发邮件，无需提供 apiKey
    Msg msg = Msg.builder()
            .role(MsgRole.USER)
            .textContent("请发一封邮件给 zhangsan@example.com，"
                    + "主题是《周会通知》，内容是《本周五下午3点在会议室A召开周会》。")
            .build();

    Msg response = agent.call(msg).block();
    System.out.println(response.getTextContent());
}
```

**效果**：

| 角色 | 看到的参数 |
|------|-----------|
| LLM 看到 Schema | `to`、`subject`、`content`、`apiKey` |
| LLM 实际生成 | `to`、`subject`、`content`（由模型根据上下文生成） |
| `apiKey` | 由框架自动填充为预设值，**模型无法看到真实值** |

---

### 6.3 工具执行上下文

在实际业务中，经常传递业务对象（如访问用户身份、数据库连接、请求上下文等信息）给工具。AgentScope 支持通过 `ToolExecutionContext` 自动注入这些对象，**无需暴露给 LLM**：
```java
// 1. 定义上下文类：承载调用方身份等运行时信息
@Data
@AllArgsConstructor
@NoArgsConstructor
public static class UserContext {
    private String userId;
}

// 2. 工具类：通过参数类型声明对上下文的依赖，框架按类型自动注入
public static class OrderTools {
    @Tool(name = "query_orders", description = "查询当前用户的订单列表")
    public String queryOrders(
            @ToolParam(name = "status", description = "订单状态：待付款/待发货/已完成") String status,
            UserContext ctx) {   // 非 @ToolParam 标注的参数 → 框架按类型从 ToolExecutionContext 自动注入
        // ctx 已包含调用方身份，LLM 无需感知
        return String.format("用户 %s 的订单（状态=%s）：3 笔订单", ctx.getUserId(), status);
    }
}

public static void main(String[] args) {
    // 3. 注册工具
    Toolkit toolkit = new Toolkit();
    toolkit.registerTool(new OrderTools());

    // 4. 构建工具执行上下文，注册 UserContext 实例
    //   - register(...) 接受任意对象，按对象 Class 作为 key 存储
    //   - 工具方法中只要声明同类型参数，即可自动注入
    ToolExecutionContext context = ToolExecutionContext.builder()
            .register(new UserContext("张三"))
            .build();

    // 5. 创建 Agent，绑定 toolkit 与 toolExecutionContext
    ReActAgent agent = ReActAgent.builder()
            .name("订单助手")
            .sysPrompt("你是一个订单查询助手，当用户请求查询订单时，使用 query_orders 工具。")
            .model(DashScopeChatModel.builder()
                    .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                    .modelName(MODEL_NAME)
                    .build())
            .toolkit(toolkit)
            .toolExecutionContext(context) // 绑定上下文
            .build();

    // 6. 调用智能体：用户无需提供 userId，工具中可直接拿到
    Msg msg = Msg.builder()
            .role(MsgRole.USER)
            .textContent("帮我查一下已支付的订单有哪些")
            .build();

    Msg response = agent.call(msg).block();
    System.out.println(response.getTextContent());
}
```

**关键特性**：
- 上下文对象 **不需要** 加 `@ToolParam` 注解
- LLM 看不到上下文参数，不会尝试传入
- 框架在调用工具时自动从 `ToolExecutionContext` 中查找并注入

### 6.4 工具挂起（Tool Suspend）

工具执行时抛出 `ToolSuspendException`，可暂停 Agent 执行并返回给调用方：
```java
/**
 * 审批工具：金额超阈值时抛出 ToolSuspendException 挂起，等待外部人工确认
 */
public static class ApprovalTool {@Tool(name = "submit_approval", description = "提交审批申请，金额单位元")
    public ToolResultBlock submitApproval(@ToolParam(name = "amount", description = "审批金额") double amount) {
        if (amount > 10000) {
            // 大额审批 → 挂起，由外部人工确认后恢复执行
            throw new ToolSuspendException("大额审批需要人工确认，金额: " + amount);
        }
        // 小额审批 → 工具内部直接通过
        return ToolResultBlock.text("审批已通过，金额: " + amount);
    }
}
```
由外部完成实际执行后 **恢复执行**：
```java
// 1. 注册工具
Toolkit toolkit = new Toolkit();
toolkit.registerTool(new ApprovalTool());

// 2. 创建 Agent
ReActAgent agent = ReActAgent.builder()
        .name("审批助手")
        .sysPrompt("你是一个审批助手。当用户提出审批申请时，使用 submit_approval 工具，"
                + "并将用户给出的金额作为参数。如果工具返回审批结果，请用一句话告知用户。")
        .model(DashScopeChatModel.builder()
                .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                .modelName(MODEL_NAME)
                .build())
        .toolkit(toolkit)
        .build();

// 3. 用户发起一笔大额审批（> 10000，将触发挂起）
Msg userMsg = Msg.builder()
        .role(MsgRole.USER)
        .textContent("帮我提交一笔 50000 元的报销审批")
        .build();

Msg response = agent.call(userMsg).block();
Scanner scanner = new Scanner(System.in);

// 4. 检查是否被挂起（GenerateReason.TOOL_SUSPENDED）
while (response != null && response.getGenerateReason() == GenerateReason.TOOL_SUSPENDED) {

    System.out.println("====== Agent 执行被挂起，等待外部确认 ======");

    // 4.1 取出本轮所有待执行的工具调用
    List<ToolUseBlock> pendingTools = response.getContentBlocks(ToolUseBlock.class);

    // 取出挂起态的 ToolResultBlock（包含 ToolSuspendException 传入的 reason），以 toolUseId 建索引
    Map<String, String> suspendReasons = response.getContentBlocks(ToolResultBlock.class).stream()
            .filter(ToolResultBlock::isSuspended)
            .collect(Collectors.toMap(
                    ToolResultBlock::getId,
                    r -> r.getOutput().stream()
                            .filter(b -> b instanceof TextBlock)
                            .map(b -> ((TextBlock) b).getText())
                            .collect(Collectors.joining("\n"))));

    for (ToolUseBlock toolUse : pendingTools) {
        /*System.out.println("待审批工具: " + toolUse.getName());
        System.out.println("调用参数  : " + toolUse.getInput());*/
        // 展示挂起原因（= ToolSuspendException(reason) 中的文本）
        System.out.println("助手: " + suspendReasons.getOrDefault(toolUse.getId(), ""));

        // 4.2 在外部完成实际执行（这里模拟人工确认）
        System.out.print("助手：是否人工通过？(y/n): ");
        String decision = scanner.nextLine().trim().toLowerCase();
        String externalResult = "y".equals(decision) ? "人工审批已通过" : "人工审批被拒绝";

        // 4.3 构造工具结果消息，注入到 Agent
        Msg toolResult = Msg.builder()
                .role(MsgRole.TOOL)
                .content(ToolResultBlock.builder()
                        .id(toolUse.getId())
                        .name(toolUse.getName())
                        .output(List.of(TextBlock.builder()
                                .text(externalResult)
                                .build()))
                        .build())
                .build();

        // 4.4 恢复 Agent 执行（继续 ReAct 循环，让模型基于工具结果作答）
        response = agent.call(toolResult).block();
    }
}

// 5. 最终回答
if (response != null) {
    System.out.println("助手: " + response.getTextContent());
}
```
实际效果如下所示：
```
====== Agent 执行被挂起，等待外部确认 ======
助手: 大额审批需要人工确认，金额: 50000.0
助手：是否人工通过？(y/n): y
助手: 您的50000元报销审批申请已通过人工审批。

====== Agent 执行被挂起，等待外部确认 ======
助手: 大额审批需要人工确认，金额: 50000.0
助手：是否人工通过？(y/n): n
助手: 您的50000元报销审批申请已被人工拒绝。
```

**使用场景**：
- 工具需要外部系统执行（如远程 API、用户手动操作）
- 需要异步等待外部结果

### 6.5 仅 Schema 工具（Schema Only Tool）

只注册工具的 Schema（名称、描述、参数），不提供执行逻辑。当 LLM 调用该工具时，框架自动触发挂起，返回给调用方执行：
```java
// 方式一：使用 ToolSchema
ToolSchema schema = ToolSchema.builder()
    .name("query_database")
    .description("查询外部数据库")
    .parameters(Map.of(
        "type", "object",
        "properties", Map.of("sql", Map.of("type", "string")),
        "required", List.of("sql")
    ))
    .build();

toolkit.registerSchema(schema);

// 方式二：批量注册
toolkit.registerSchemas(List.of(schema1, schema2));

// 检查是否为外部工具
boolean isExternal = toolkit.isExternalTool("query_database");  // true
```

> 调用流程与工具挂起相同：LLM 调用 → 返回 `TOOL_SUSPENDED` → 外部执行 → 提供结果恢复。

**使用场景**：
- 工具由外部系统实现（如前端、其他服务）
- 动态注册第三方工具

---

## 7. 内置工具

AgentScope 提供了开箱即用的内置工具，覆盖常见的开发需求。

### 7.1 文件工具

| 工具 | 方法 | 说明 |
|------|------|------|
| `ReadFileTool` | `view_text_file` | 按行范围查看文件 |
| `ReadFileTool` | `list_directory` | 列出目录下的文件和文件夹 |
| `WriteFileTool` | `write_text_file` | 创建/覆盖/替换文件内容 |
| `WriteFileTool` | `insert_text_file` | 在指定行插入内容 |

```java
// 基础注册
toolkit.registerTool(new ReadFileTool());
toolkit.registerTool(new WriteFileTool());

// 安全模式（推荐）：限制文件访问范围
toolkit.registerTool(new ReadFileTool("/safe/workspace"));
toolkit.registerTool(new WriteFileTool("/safe/workspace"));
```

完整示例：
```java
// 1. 准备沙箱工作目录（target/file-tool-workspace）
//    内置工具会把所有 file_path 解析到 baseDir 内，越界会直接报错
Path workspace = Paths.get("agentscope/quickstart/target/file-tool-workspace")
        .toAbsolutePath().normalize();
Files.createDirectories(workspace);
String baseDir = workspace.toString();

// 2. 注册内置文件工具到 Toolkit
Toolkit toolkit = new Toolkit();
toolkit.registerTool(new ReadFileTool(baseDir));
toolkit.registerTool(new WriteFileTool(baseDir));

// 3. 创建 Agent，系统提示中说明可用的内置工具
ReActAgent agent = ReActAgent.builder()
        .name("文件助手")
        .sysPrompt("你是一个文件操作助手，完成本地文件读写。请完成用户请求，并把最终结果用一句话告知用户。")
        .model(DashScopeChatModel.builder()
                .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                .modelName(MODEL_NAME)
                .build())
        .toolkit(toolkit)
        .build();

// 4. 调用智能体：完成"先写再插再读"的组合任务
//    预计调用链：write_text_file → insert_text_file → view_text_file
Msg msg = Msg.builder()
        .role(MsgRole.USER)
        .textContent("把内容《今日学习：AgentScope 工具调用》写入 notes.txt，"
                + "再在文件末尾插入一行《明日计划：练习 ReActAgent》，"
                + "最后读取并把完整内容返回给我。")
        .build();

Msg response = agent.call(msg).block();
if (response != null) {
    System.out.println("助手: " + response.getTextContent());
}
```
执行效果如下所示：
```
[main] INFO io.agentscope.core.tool.file.ReadFileTool - ReadFileTool initialized with base directory: .../agentscope/quickstart/target/file-tool-workspace
[main] INFO io.agentscope.core.tool.Toolkit - Registered tool 'view_text_file' in group 'ungrouped'
[main] INFO io.agentscope.core.tool.Toolkit - Registered tool 'list_directory' in group 'ungrouped'
[main] INFO io.agentscope.core.tool.file.WriteFileTool - WriteFileTool initialized with base directory: .../agentscope/quickstart/target/file-tool-workspace
[main] INFO io.agentscope.core.tool.Toolkit - Registered tool 'insert_text_file' in group 'ungrouped'
[main] INFO io.agentscope.core.tool.Toolkit - Registered tool 'write_text_file' in group 'ungrouped'
[boundedElastic-3] INFO io.agentscope.core.tool.file.WriteFileTool - Successfully created and wrote to new file: notes.txt
[boundedElastic-1] INFO io.agentscope.core.tool.file.WriteFileTool - Successfully inserted content into 'notes.txt' at line 2
助手: 文件内容已成功写入并添加，完整的笔记内容为：
1: 今日学习：AgentScope 工具调用
2: 明日计划：练习 ReActAgent
```
### 7.2 Shell 命令工具

| 工具 | 特性 |
|------|------|
| `ShellCommandTool` | 执行 Shell 命令，支持命令白名单和回调批准机制，并支持超时控制 |

```java
// 定义允许执行的命令白名单
Set<String> allowedCommands = Set.of("ls", "pwd", "cat", "wc", "echo", "date");

// 审批回调：每个命令执行前询问确认
Scanner scanner = new Scanner(System.in);
Function<String, Boolean> approvalCallback = command -> {
    System.out.println("[审批] 智能体想执行非白名单命令: " + command);
    System.out.print("[审批] 是否放行? (y/n): ");
    String input = scanner.hasNextLine() ? scanner.nextLine().trim() : "";
    return "y".equalsIgnoreCase(input) || "yes".equalsIgnoreCase(input);
};

// 创建并注册内置 Shell 工具
ShellCommandTool shellTool = new ShellCommandTool(baseDir, allowedCommands, approvalCallback);
Toolkit toolkit = new Toolkit();
toolkit.registerTool(shellTool);
```
> allowedCommands: 命令白名单；callback：回调函数

完整示例：
```java
// 1. 准备沙箱工作目录，所有命令的相对路径都解析到这里
Path workspace = Paths.get("agentscope/quickstart/target/shell-tool-workspace")
        .toAbsolutePath().normalize();
Files.createDirectories(workspace);
// 提前准备一个示例文件，供 LLM 读取和统计
Files.writeString(workspace.resolve("hello.txt"),
        "Hello AgentScope\n你好，世界\n第三行示例\n");
String baseDir = workspace.toString();

// 2. 命令白名单：只放行明确安全的"只读"命令
Set<String> allowedCommands = Set.of("ls", "pwd", "cat", "wc", "echo", "date");

// 3. 审批回调：白名单之外的命令会走这里，让人来确认是否放行
//    回调输入是完整命令字符串，返回 true 即放行，false 拒绝
Scanner scanner = new Scanner(System.in);
Function<String, Boolean> approvalCallback = command -> {
    System.out.println("[审批] 智能体想执行非白名单命令: " + command);
    System.out.print("[审批] 是否放行? (y/n): ");
    String input = scanner.hasNextLine() ? scanner.nextLine().trim() : "";
    return "y".equalsIgnoreCase(input) || "yes".equalsIgnoreCase(input);
};

// 4. 创建并注册内置 Shell 工具
ShellCommandTool shellTool = new ShellCommandTool(baseDir, allowedCommands, approvalCallback);
Toolkit toolkit = new Toolkit();
toolkit.registerTool(shellTool);

// 5. 创建 Agent，系统提示中告知工具能力即可（具体白名单工具描述里会自动带上）
ReActAgent agent = ReActAgent.builder()
        .name("小助手")
        .sysPrompt("你是一个操作小助手，请完成用户请求，并把最终结果用一句话告知用户。")
        .model(DashScopeChatModel.builder()
                .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                .modelName(MODEL_NAME)
                .build())
        .toolkit(toolkit)
        .build();

// 6. 调用智能体：组合任务（预计触发 ls / cat / wc 三次工具调用）
Msg msg = Msg.builder()
        .role(MsgRole.USER)
        .textContent("先列出当前目录下的文件，然后查看 hello.txt 的内容，最后告诉我它一共有多少行。最后删除该文件。")
        .build();

Msg response = agent.call(msg).block();
if (response != null) {
    System.out.println("助手: " + response.getTextContent());
}
```
执行效果如下所示：
```
[main] INFO io.agentscope.core.tool.coding.ShellCommandTool - ShellCommandTool initialized with base directory: .../agentscope/quickstart/target/shell-tool-workspace
[main] INFO io.agentscope.core.tool.Toolkit - Registered tool 'execute_shell_command' in group 'ungrouped'
[boundedElastic-2] INFO io.agentscope.core.tool.coding.ShellCommandTool - Command 'rm hello.txt' validation failed: Command 'rm' is not in the allowed whitelist
[审批] 智能体想执行非白名单命令: rm hello.txt
[审批] 是否放行? (y/n): n
[boundedElastic-2] INFO io.agentscope.core.tool.coding.ShellCommandTool - User rejected command execution: rm hello.txt
[boundedElastic-2] WARN io.agentscope.core.tool.coding.ShellCommandTool - Command 'rm hello.txt' execution rejected: SecurityError: Command execution was rejected by user. Reason: Command 'rm' is not in the allowed whitelist
助手: 当前目录下有 hello.txt 文件，其内容为三行：“Hello AgentScope”、“你好，世界”和“第三行示例”，文件共3行。由于安全限制，我无法直接执行删除命令，请您手动删除该文件。
```

**安全特性**：
- 命令白名单：只允许执行预设的安全命令
- 审批回调：每个命令执行前可人工确认
- 超时控制：防止长时间挂起的命令

### 7.3 多模态工具

| 工具 | 能力 |
|------|------|
| `DashScopeMultiModalTool` | 文生图、图生文、文生语音、语音转文字 |
| `OpenAIMultiModalTool` | 文生图、图片编辑、图片变体、图生文、文生语音、语音转文字 |

```java
// 注册多模态工具
toolkit.registerTool(new DashScopeMultiModalTool(System.getenv("DASHSCOPE_API_KEY")));
toolkit.registerTool(new OpenAIMultiModalTool(System.getenv("OPENAI_API_KEY")));
```

### 7.4 子智能体工具

可以将智能体注册为工具，供其他智能体调用。详见 [Agent as Tool](https://java.agentscope.io/zh/task/agent-as-tool.html)。

### 7.5 元工具

让 Agent 能够自主管理工具组：

```java
// 注册元工具
toolkit.registerMetaTool();
```
注册后，Agent 可以调用 `reset_equipped_tools` 方法来激活或切换工具组。这在工具数量较多时特别有用——Agent 可以根据当前任务需求，自主选择加载哪些工具。

---

## 8. 实战：构建一个业务 Agent

以下示例综合展示了工具系统的核心能力：
```java
public class BusinessAgentDemo {

    @Data
    @AllArgsConstructor
    public static class UserContext {
        private String userId;
        private String tenantId;
    }

    // 工具类
    public static class OrderTools {
        @Tool(description = "查询当前用户的订单列表")
        public String queryOrders(
                @ToolParam(name = "status") String status,
                UserContext ctx) {
            return String.format("用户 %s 的订单（状态=%s）有 3 笔：%s", ctx.getUserId(), status, "金额分别为 18, 201, 4");
        }
    }

    public static class Calculator {
        @Tool(description = "计算订单总金额")
        public double calculateTotal(
                @ToolParam(name = "unitPrice") double unitPrice,
                @ToolParam(name = "quantity") int quantity) {
            return unitPrice * quantity;
        }
    }

    public static void main(String[] args) {
        // 1. 创建工具集
        Toolkit toolkit = new Toolkit(ToolkitConfig.builder()
                .parallel(true)
                .executionConfig(ExecutionConfig.builder()
                        .timeout(Duration.ofSeconds(30))
                        .build())
                .build());

        // 2. 创建工具组并注册工具
        toolkit.createToolGroup("business", "业务工具", true);
        toolkit.registration()
                .tool(new OrderTools())
                .tool(new Calculator())
                .group("business")
                .apply();

        // 3. 构建上下文
        ToolExecutionContext context = ToolExecutionContext.builder()
                .register(new UserContext("user-123", "tenant-456"))
                .build();

        // 4. 创建 Agent
        ReActAgent agent = ReActAgent.builder()
                .name("BusinessAgent")
                .sysPrompt("你是智能业务助手，可以帮助用户查询订单和计算金额。")
                .model(DashScopeChatModel.builder()
                        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                        .modelName("qwen3.6-plus")
                        .build())
                .toolkit(toolkit)
                .toolExecutionContext(context)
                .maxIters(10)
                .build();

        // 5. 调用
        Msg response = agent.call(
                Msg.builder()
                        .role(MsgRole.USER)
                        .textContent("帮我查一下所有订单，并计算如果单价 99 元买 5 件要多少钱")
                        .build()
        ).block();

        System.out.println(response.getTextContent());
    }
}
```

---

## 9. 最佳实践与注意事项

### 9.1 工具设计原则

| 原则 | 说明 | 示例 |
|------|------|------|
| **单一职责** | 每个工具只做一件事 | `getWeather` 只查天气，不查空气质量 |
| **描述清晰** | `description` 必须包含使用场景 | "当用户询问天气、出行建议时使用" |
| **参数精简** | 只暴露必要的参数 | 不需要用户传入 API Key |
| **错误处理** | 返回错误信息而非抛出异常 | return "Error: 城市不存在" |
| **幂等性** | 同一参数多次调用结果一致 | 查询类工具天然幂等 |

### 9.2 常见陷阱

```java
// ❌ 陷阱 1：@ToolParam 未指定 name
@Tool(description = "...")
public String bad(@ToolParam String city) { }  // 缺少 name！

// ✅ 正确
@Tool(description = "...")
public String good(@ToolParam(name = "city") String city) { }

// ❌ 陷阱 2：工具方法不是 public
@Tool(description = "...")
private String hidden() { }  // 必须是 public！

// ✅ 正确
@Tool(description = "...")
public String visible() { }

// ❌ 陷阱 3：返回 null
@Tool(description = "...")
public String bad() { return null; }  // 避免返回 null

// ✅ 正确
@Tool(description = "...")
public String good() { return "结果"; }
```

### 9.3 工具数量与性能

| 工具数量 | 建议 |
|---------|------|
| 1-5 个 | 直接使用，无需分组 |
| 5-15 个 | 使用工具组按场景分类 |
| 15+ 个 | 使用元工具让 Agent 自主管理，或精简工具设计 |

过多的工具会增加 LLM 的决策负担，可能导致选错工具或响应变慢。

---

## 10. 总结

| 要点 | 内容 |
|------|------|
| **核心注解** | `@Tool`（标记方法）+ `@ToolParam`（标记参数） |
| **工具类型** | 同步、异步（`Mono<T>`）、流式（`ToolEmitter`） |
| **注册方式** | `Toolkit.registerTool()` 或 `Toolkit.registration().tool().group().apply()` |
| **工具组** | 按场景分类，支持动态激活/停用 |
| **预设参数** | 隐藏敏感信息，不暴露给 LLM |
| **执行上下文** | `ToolExecutionContext` 自动注入业务对象 |
| **内置工具** | 文件操作、Shell 命令、多模态 |
| **高级特性** | 工具挂起、仅 Schema 工具、元工具、并行执行 |

工具系统是 AgentScope 框架的"手脚"，也是让 Agent 从"聊天机器人"进化为"能干实事的助手"的关键。

---

## 系列文章导航

| 篇目 | 主题 |
|------|------|
| 一 | [AgentScope Java 入门 1：用 Java 构建生产级 AI 智能体的全新范式](https://smartsi.blog.csdn.net/article/details/158778778) |
| 二 | [AgentScope Java 入门 2：Spring AI Alibaba 与 AgentScope 的定位与区别](https://smartsi.blog.csdn.net/article/details/160955593) |
| 三 | [AgentScope Java 入门 3：如何安装 AgentScope](https://smartsi.blog.csdn.net/article/details/160694030) |
| 四 | [AgentScope Java 入门 4：搭建第一个 ReAct 智能体](https://smartsi.blog.csdn.net/article/details/161203988) |
| 五 | [AgentScope Java 入门 5：如何使用 DashScopeChatModel 集成百练模型](https://smartsi.blog.csdn.net/article/details/161300535) |
| 六 | [AgentScope Java 入门 6：如何使用 OpenAIChatModel 集成兼容 OpenAI 协议模型](https://smartsi.blog.csdn.net/article/details/161324334) |
| 七 | [AgentScope Java 入门 7：如何使用 OllamaChatModel 集成 Ollama 自托管平台](https://smartsi.blog.csdn.net/article/details/161335847) |
| 八（本文）| [AgentScope Java 入门 8：Tool 工具系统——让 Agent 真正"动手做事"]() |
