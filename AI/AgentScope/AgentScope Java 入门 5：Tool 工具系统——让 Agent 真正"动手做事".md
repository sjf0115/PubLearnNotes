AgentScope Java 自发布以来，迅速成为 Java 生态中构建企业级 AI Agent 应用的首选框架之一。其核心优势在于对 ReAct（Reasoning + Acting，推理+行动） 范式的深度实践，而这一范式的灵魂，便是 Tool（工具） 系统。

如果把大语言模型比作 Agent 的“大脑”，那么 Tool 系统就是 Agent 的“手脚”，让它不仅能“思考”，更能“行动”——查询天气、操作数据库、调用外部 API，甚至控制物理设备。本文将带您深入剖析 AgentScope Java 中的 Tool 工具系统，从设计哲学到实战用法，全方位解读这一核心模块。

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

- **注解驱动**：使用 `@Tool` 和 `@ToolParam` 快速定义工具
- **响应式编程**：原生支持 `Mono`/`Flux` 异步执行
- **自动 Schema**：自动生成 JSON Schema 供 LLM 理解
- **工具组管理**：动态激活/停用工具集合
- **预设参数**：隐藏敏感参数（如 API Key）
- **并行执行**：支持多工具并行调用

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

注册时需要关注几个配置选项：
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

注册之后可以通过如下几种方式实现工具动态管理：
```java
// 查询已注册的工具
Collection<AgentTool> tools = toolkit.getTools();

// 动态移除工具
toolkit.removeTool("get_weather");

// 检查工具是否存在
boolean exists = toolkit.hasTool("calculate");
```

### 3.3 创建带工具的 Agent

最后，通过 Builder 模式将装配好的 Toolkit 注入到 ReActAgent 中，Agent 便拥有了使用工具的能力:
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
                .textContent("北京今天天气如何？")
                .build()
).block();

System.out.println(response.getTextContent());
```

执行流程：
```
用户：北京今天天气如何？
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
回答：根据查询，北京今天天气晴朗，气温 25°C，适合出门！
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
    description = "城市名称"     // 参数描述（必填）
)
String city
```

| 属性 | 必填 | 说明 |
|------|:----:|------|
| `name` | **是** | 参数名。**必须显式指定**，因为 Java 运行时默认不保留参数名 |
| `description` | **是** | 参数描述。帮助 LLM 理解该参数的含义和格式 |

**重要提示**：`@ToolParam` 的 `name` 和 `description` 直接影响 LLM 能否正确传参。如果描述不清，模型可能会传入错误格式的数据。

---

## 5. 工具类型

根据工具返回类型可以分为三类工具：

| 工具 | 返回类型 | 说明
| :------------- | :------------- | :------------- |
| 同步工具 | `String`, `int`, `Object` 等 | 同步执行，自动转换为 `ToolResultBlock` |
| 异步工具 | `Mono<T>`, `Flux<T>` | 异步执行 |
| 流式工具 | `ToolResultBlock` | 直接控制返回格式（文本、图片、错误等） |

### 5.1 同步工具

直接返回结果，适合快速操作（计算、内存查询等）：
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

使用 `ToolEmitter` 发送中间进度，适合长时间任务（进度仅对 Hook 可见，不会发送给 LLM）：
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

**应用场景**：
- **权限控制**：普通用户只激活 `basic` 组，管理员额外激活 `admin` 组
- **场景切换**：客服场景激活 `query` 组，运维场景激活 `deploy` 组
- **性能优化**：减少 LLM 可见的工具数量，降低模型选择工具的决策负担

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

// 注册时预设敏感参数
toolkit.registration()
        .tool(new EmailService())
        .presetParameters(Map.of(
                "send", Map.of("apiKey", System.getenv("EMAIL_API_KEY"))
        ))
        .apply();
```

**效果**：
- LLM 看到的参数列表：`to`、`subject`、`content`、`apiKey`
- LLM 实际传入的参数：`to`、`subject`、`content`（由模型根据上下文生成）
- `apiKey` 由框架自动填充为预设值，**模型无法看到真实值**

---

### 6.3 工具执行上下文

在实际业务中，经常传递业务对象（如访问用户身份、数据库连接、请求上下文等信息）给工具。AgentScope 支持通过 `ToolExecutionContext` 自动注入这些对象，**无需暴露给 LLM**：
```java
// 1. 定义上下文类
public class UserContext {
    private final String userId;
    public UserContext(String userId) { this.userId = userId; }
    public String getUserId() { return userId; }
}

// 2. 注册到 Agent
ToolExecutionContext context = ToolExecutionContext.builder()
    .register(new UserContext("user-123"))
    .build();

ReActAgent agent = ReActAgent.builder()
    .name("助手")
    .model(model)
    .toolkit(toolkit)
    .toolExecutionContext(context) // 绑定上下文
    .build();

// 3. 工具中使用（自动注入）
@Tool(description = "查询用户数据")
public String query(
        @ToolParam(name = "sql") String sql,
        UserContext ctx) {  // 自动注入，无需 @ToolParam
    // ctx 中包含了用户身份信息
    return "用户 " + ctx.getUserId() + " 的数据";
}
```

**关键特性**：
- 上下文对象 **不需要** 加 `@ToolParam` 注解
- LLM 看不到上下文参数，不会尝试传入
- 框架在调用工具时自动从 `ToolExecutionContext` 中查找并注入

### 6.4 工具挂起（Tool Suspend）

工具执行时抛出 `ToolSuspendException`，可暂停 Agent 执行并返回给调用方：
```java
@Tool(description = "提交审批申请")
public ToolResultBlock submitApproval(
        @ToolParam(name = "amount", description = "审批金额") double amount) {

    if (amount > 10000) {
        // 大额审批需要人工确认，挂起执行
        throw new ToolSuspendException("大额审批需要人工确认，金额: " + amount);
    }

    return ToolResultBlock.text("审批已通过");
}
```
由外部完成实际执行后 **恢复执行**：
```java
Msg response = agent.call(userMsg).block();

// 检查是否被挂起
if (response.getGenerateReason() == GenerateReason.TOOL_SUSPENDED) {
    // 获取待执行的工具调用
    List<ToolUseBlock> pendingTools = response.getContentBlocks(ToolUseBlock.class);

    for (ToolUseBlock toolUse : pendingTools) {
        // 在外部完成实际执行后，构造结果消息
        Msg toolResult = Msg.builder()
                .role(MsgRole.TOOL)
                .content(ToolResultBlock.builder()
                        .id(toolUse.getId())
                        .name(toolUse.getName())
                        .output(List.of(TextBlock.builder()
                                .text("人工审批已通过")
                                .build()))
                        .build())
                .build();

        // 恢复 Agent 执行
        response = agent.call(toolResult).block();
    }
}
```

**使用场景**：
- 工具需要外部系统执行（如远程 API、用户手动操作）
- 需要异步等待外部结果

### 6.5 仅 Schema 工具（Schema Only Tool）

只注册工具的 Schema（名称、描述、参数），不提供执行逻辑。当 LLM 调用该工具时，框架自动触发挂起，返回给调用方执行。

**使用场景**：
- 工具由外部系统实现（如前端、其他服务）
- 动态注册第三方工具

**使用方式**：

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

调用流程与工具挂起相同：LLM 调用 → 返回 `TOOL_SUSPENDED` → 外部执行 → 提供结果恢复。

---

## 7. 内置工具

AgentScope 提供了开箱即用的内置工具，覆盖常见的开发需求。

### 7.1 文件工具

| 工具 | 方法 | 说明 |
|------|------|------|
| `ReadFileTool` | `view_text_file` | 按行范围查看文件 |
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

### 7.2 Shell 命令工具

| 工具 | 特性 |
|------|------|
| `ShellCommandTool` | 执行 Shell 命令，支持命令白名单和回调批准机制，并支持超时控制 |

```java
// 定义允许执行的命令白名单
Set<String> allowedCommands = Set.of("ls", "cat", "grep", "pwd");

// 审批回调：每个命令执行前询问确认
Function<String, Boolean> approvalCallback = cmd -> {
    System.out.print("是否执行命令: " + cmd + " ? (y/n): ");
    return new Scanner(System.in).nextLine().trim().equalsIgnoreCase("y");
};

toolkit.registerTool(new ShellCommandTool(allowedCommands, approvalCallback));
```
> allowedCommands: 命令白名单；callback：回调函数

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

## AgentTool 接口

需要精细控制时，直接实现接口：
```java
public class CustomTool implements AgentTool {
    @Override
    public String getName() { return "custom_tool"; }

    @Override
    public String getDescription() { return "自定义工具"; }

    @Override
    public Map<String, Object> getParameters() {
        return Map.of(
            "type", "object",
            "properties", Map.of(
                "query", Map.of("type", "string", "description", "查询")
            ),
            "required", List.of("query")
        );
    }

    @Override
    public Mono<ToolResultBlock> callAsync(ToolCallParam param) {
        String query = (String) param.getInput().get("query");
        return Mono.just(ToolResultBlock.text("结果：" + query));
    }
}
```

## 配置选项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `parallel` | 是否并行执行多个工具 | `true` |
| `allowToolDeletion` | 是否允许删除工具 | `true` |
| `executionConfig.timeout` | 工具执行超时时间 | 5 分钟 |

```java
Toolkit toolkit = new Toolkit(ToolkitConfig.builder()
    .parallel(true)                    // 并行执行多个工具
    .allowToolDeletion(false)          // 禁止删除工具
    .executionConfig(ExecutionConfig.builder()
        .timeout(Duration.ofSeconds(30))
        .build())
    .build());
```

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

    // ===== 工具类 =====
    public static class OrderTools {
        @Tool(description = "查询当前用户的订单列表")
        public String queryOrders(
                @ToolParam(name = "status") String status,
                UserContext ctx) {
            return String.format("用户 %s 的订单（状态=%s）：3 笔订单",
                    ctx.getUserId(), status);
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
