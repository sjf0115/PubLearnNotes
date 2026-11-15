在之前的系列文章中，Agent 的输出都是 **自由文本** —— 用户问"今天天气怎么样"，Agent 回复一段描述性文字。这种方式在对话场景下很自然，但在很多业务场景中却捉襟见肘：
- **电商导购**：需要提取商品名称、价格、评分，存入数据库
- **智能表单**：需要将用户的自然语言描述转换为结构化的 JSON
- **数据分析**：需要将分析结果按固定格式输出，供下游系统解析
- **配置生成**：需要根据用户需求生成标准化的 YAML/JSON 配置

如果让 Agent 自由输出文本，然后用正则表达式或二次解析提取字段，不仅脆弱易错，还增加了系统复杂度。AgentScope Java 的 **Structured Output（结构化输出）** 功能正是为解决这一问题而生——它让 Agent 直接输出符合预定义 Schema 的类型化数据，一步到位，稳定可靠。

> 文中 API 均以 **AgentScope Java 1.0.12** 源码为准核实。

---

## 1. 为什么需要结构化输出？

假设需求是提取手机产品评价中的关键信息，如果采用自由文本输出：`"这款手机的优点是屏幕很大、电池续航不错，缺点是价格偏高、拍照一般。"`。这段文字对人很好理解，但对程序处处是黑洞：“续航持久” 到底对应什么指标？屏幕大是多少英寸？没有量化、没有固定字段。如果下游要做商品评价分析，工程师必须编写大量启发式规则去提取信息，容错极低。而结构化输出返回的是带有强类型约束的数据：
```json
{
  "productName": "iPhone 16 Pro",
  "price": 7999.0,
  "pros": ["屏幕大", "续航好"],
  "cons": ["价格高", "拍照一般"],
  "score": 4.2
}
```
它带来三个核心收益：
- 字段明确，可直接映射到 Java 对象
- 类型安全，price 一定是 Double，score 一定是 Double
- 下游系统无需解析，直接 getScore()、getPrice()

它不是锦上添花的美化功能，而是把 Agent 从 “对话助手” 推向业务自动化链路的基础设施。电商信息抽取、简历解析、自然语言表单、BI 数据分析、K8s / 业务配置生成，都离不开它。

---

## 2. 快速开始：三步实现结构化抽取

结构化输出对外 API 设计刻意轻量化，只需要定义 Schema、调用、读取结果。

### 2.1 定义 Java Schema

普通 Java POJO 描述你想要的数据结构：
```java
// 产品信息
public static class ProductInfo {
    public String productType;      // 产品类型
    public String brand;            // 品牌
    public Integer minRam;          // 最小内存
    public Double maxBudget;        // 最大预算
    public List<String> features;   // 特征
}
```
一个非常关键的约束：如果 Schema 定义为内部类，必须标记为 `static`，否则 Jackson 无法实例化，抛出非静态内部类实例化异常：
```java
Caused by: java.lang.IllegalArgumentException: Cannot construct instance of
`com.example.output.StructuredOutputExample$ProductInfo`: non-static inner classes
like this can only by instantiated using default, no-argument constructor
```

### 2.2 调用 Agent，绑定目标类型

和普通对话调用不同，`agent.call` 支持传入目标 Class，框架自动接管结构化流程：
```java
// 用户消息
Msg userMsg = Msg.builder()
        .role(MsgRole.USER)
        .textContent("从这个查询中提取出产品需求: 我正在寻找一台笔记本电脑。"
                + "我需要至少 16GB 的内存，最好是有苹果品牌的产品，"
                + "而且我的预算在 8000 人民币左右。它还要便于携带以便于旅行使用。")
        .build();

// 调用 Agent，指定期望的输出类型为 ProductInfo.class
Msg response = agent.call(userMsg, ProductInfo.class).block();
```
除了传入 Class，框架同样支持直接传入动态构造的 JSON Schema（`JsonNode`），适合运行时动态变更抽取结构的场景。

### 2.3 读取结构化实体

返回消息内置结构化数据，通过专用方法反序列化，同时配套存在性检查：
```java
// 从响应中提取结构化数据
ProductInfo result = response.getStructuredData(ProductInfo.class);
System.out.println("产品需求:");
System.out.println("  产品类型: " + result.productType);
System.out.println("  品牌: " + result.brand);
System.out.println("  最小内存: " + result.minRam + " GB");
System.out.println("  最大预算: " + result.maxBudget + " 元");
System.out.println("  特征: " + result.features);
```

三步就这么简单。但"简单调用"的背后，AgentScope 做了一整套精巧的机制设计——理解它，才能在生产环境中用对、用稳。

---

## 3. 底层原理：临时工具 + Hook 驱动，是它真正的巧思

很多人会误解：结构化输出只是在系统提示词里塞一段 JSON Schema，要求模型输出 JSON。AgentScope 的实现完全不是这样。它的核心思想一句话概括：**结构化输出不是"让模型直接吐 JSON"，而是"让模型调用一个参数 Schema 恰好是你目标结构的工具，利用 Function Calling 的参数 Schema 约束模型，让模型通过调用该工具返回目标结构"。**

### 3.1 generate_response：动态生成的临时工具

当你调用 `agent.call(msg, ProductInfo.class)` 时，框架内部（`StructuredOutputCapableAgent`）依次做了四件事：
- 框架将你传入的 Java Class，借助 `JsonSchemaUtils` 翻译成标准 JSON Schema。
- 动态注册临时工具 `generate_response`，工具入参刚好包裹目标 Schema。
- 该工具注册进 Toolkit，只对这一次调用可见。
- 调用结束后通过 `removeToolIfSame` 从 Toolkit 移除，不污染后续对话。

所以模型视角看到的就是一个普通工具——**只要它成功调用 `generate_response`，参数里的 `response` 字段就是你要的结构化数据**。借助 Function Calling 的原生约束能力，字段的类型和必填性由模型侧保证，比"提示词祈祷 + 正则解析"可靠得多。

### 3.2 StructuredOutputHook：四拍事件驱动的流程控制

工具注册好了，但模型不一定"听话"——它可能自顾自地输出文本，不去调用 `generate_response`。`StructuredOutputHook` 挂在 Agent 的事件流上，负责把流程"扳回来"，它在四个关键节点介入流程：

| 事件时机 | Hook 的动作 |
|---------|------------|
| **PostReasoning**（推理结束） | 本轮推理结束，检查模型是否调用目标工具；如果模型只输出自由文本、没有调用工具，且还没达到最大重试次数（上限固定为 3），注入提醒消息，重新进入推理； |
| **PreReasoning**（推理开始） | 如果上一轮是提醒消息，在支持的模型上强制设置 `tool_choice = generate_response`，引导模型必须调用这个工具； |
| **PostActing**（工具执行后） | 一旦成功执行这个临时工具，标记任务完成，提前终止 Agent 的 ReAct 循环； |
| **PostCall**（调用结束） | **压缩记忆**：删除 `generate_response` 相关的中间消息（提醒消息、工具调用消息等），只保留最终响应；同时把被删消息的 ChatUsage（输入/输出 token、耗时）累加合并、保留最后一个 ThinkingBlock |

两个值得注意的设计：
- **重试上限 MAX_RETRIES = 3**：提醒不是无限的，三次仍不调用就放弃并报错——生产环境要意识到结构化输出存在失败路径；
- **记忆压缩**：结构化输出的中间过程对后续对话是噪音，Hook 会主动清掉。副作用是：调用结束后你在 memory 里 **看不到** `generate_response` 的调用痕迹，只能看到最终结果（token 用量已聚合进最终消息）。

### 3.3 数据如何回到你手里

`generate_response` 执行成功后，模型填的参数被写入最终 Msg 的 **metadata**（键 `STRUCTURED_OUTPUT`）。`getStructuredData(Class)` 底层就是使用 Jackson 将 metadata 反序列化为目标 Java 对象。。因此健壮性检查有配套 API：先用 `hasStructuredData()` 判断，再取值；不想定义类时还有返回 `Map` 的重载。

---

## 4. 两种提醒策略：TOOL_CHOICE 与 PROMPT

`StructuredOutputReminder` 常被误读为"两种输出模式"。对照源码注释，它的准确定义是：**当模型没有主动调用 `generate_response` 工具时，用什么手段提醒它**。两种策略底层都是同一套临时工具机制，区别只在"兜底方式"：

| 策略 | 兜底手段 | 特点 | 要求 |
|------|---------|------|------|
| **TOOL_CHOICE**（默认，推荐） | 注入提醒消息后，下一轮通过 `tool_choice` API 参数 **强制** 模型调用 `generate_response` | 确定性高，通常一轮提醒即收敛 | 模型/服务商需支持 `tool_choice` 参数，主流模型均支持 |
| **PROMPT**（legacy） | 不使用强制参数，只依靠注入提示词引导模型调用工具。| 温和、不依赖 `tool_choice` 参数，但可能多次迭代仍不收敛 | 模型需支持 Function Calling（`generate_response` 本身就是工具调用） |

```java
ReActAgent agent = ReActAgent.builder()
        .name("智能助手")
        .sysPrompt("你是一名智能分析助手。对用户请求进行分析，并给出条理清晰的回复。")
        .model(model)
        .structuredOutputReminder(StructuredOutputReminder.TOOL_CHOICE) // 缺省即此值
        .build();
```

**两点澄清**（都是常见误解）：
- TOOL_CHOICE **不等于** "一次 API 调用完成"。第一轮模型可以自由调用业务工具做多步任务（这正是设计意图：先干活、后产出结构化结果）；只有当模型不调用 `generate_response` 时，下一轮才会被 `tool_choice` 强制收敛。所以一次完整的结构化调用可能包含多轮推理；
- PROMPT **不是** "往系统提示词注入 Schema 引导模型输出 JSON"。Schema 始终通过 `generate_response` 工具的参数传递，PROMPT 模式仅仅是把 "强制 tool_choice" 换成 "注入提醒消息重试"。**它同样依赖模型的 Function Calling 能力**，完全不支持工具调用的模型两种策略都用不了。

**选型建议**：默认用 TOOL_CHOICE；只有当服务商对 `tool_choice` 参数支持不佳（强制后仍报错或行为异常）时，降级到 PROMPT。

---

## 5. Schema 进阶：用好注解，降低模型理解偏差

简单 POJO 已经够用；但对于生产级抽取，字段语义、单位、枚举、格式约定，都需要显式写入 Schema，否则模型容易产生歧义。

### 5.1 支持的类型

AgentScope 支持丰富的 Java 类型映射：
```java
public static class Schema {
    // 基础类型
    public String name;
    public Integer count;
    public Double score;
    public Boolean active;

    // 集合类型
    public List<String> tags;
    public Map<String, Object> metadata;

    // 嵌套对象
    public Address address;
}
```

复杂业务对象通常需要嵌套定义（嵌套类同样必须是 `static`）：
```java
public static class Person {
    public String name;
    public Address address;
    public List<String> hobbies;
}

public static class Address {
    public String city;
    public String street;
}
```

### 5.2 用注解给 Schema "写说明书"

AgentScope 复用 Jackson 的注解体系，生成带有描述信息的 JSON Schema：
- `@JsonProperty`：自定义 JSON 输出字段名；
- `@JsonPropertyDescription`：字段描述，写入 Schema 的 `description`，告诉模型字段含义、单位、格式；
- `@JsonClassDescription`：给整个实体增加说明；
- `@JsonIgnore`：排除不需要进入 Schema 的内部字段。

推荐用两个 **description 注解**，它们会写进 JSON Schema 的 `description`，直接决定模型对字段语义的理解质量：
```java
@JsonClassDescription("用户的笔记本采购需求")
public static class ProductInfo {
    @JsonProperty("product_type")
    @JsonPropertyDescription("目标硬件品类")
    public String productType;

    @JsonPropertyDescription("预算上限，单位：人民币元")
    public Double maxBudget;
}
```

**实践经验**：描述注解是性价比最高的准确率提升手段：字段名能自解释的就不用写 `description`；凡是存在口径歧义、带单位、特殊时间格式、编码规则的字段，都建议补充说明。

---

## 6. 错误处理与健壮性

结构化输出不是 100% 可靠，它存在明确的失败路径，工程代码必须覆盖。三类典型异常：
- **重试超限**：连续三次引导，模型依然拒绝调用目标工具；此时不会生成结构化载荷，`hasStructuredData` 返回 false；
- **元数据缺失**：尝试读取结构化数据，但消息中不存在对应的载荷，抛出 `IllegalStateException`；
- **类型转换失败**：模型返回的数据结构和 Java 实体不匹配，反序列化抛出 `IllegalArgumentException`。

```java
try {
    Msg msg = agent.call(userMsg, Resume.class).block();
    // 结构化输出
    if (msg == null) {
        System.out.println("无回复");
    } else if (!msg.hasStructuredData()) {
        // 结构化抽取失败，触发降级
        // ...
        throw new IllegalStateException("结构化输出未生成");
    } else {
        Resume resume = msg.getStructuredData(Resume.class);
        ObjectMapper objectMapper = new ObjectMapper();
        String jsonString = objectMapper.writeValueAsString(resume);
        System.out.println(jsonString);
    }
} catch (Exception e) {
    System.err.println("处理失败: " + e.getMessage());
}
```

## 7. 实战：简历信息结构化解析

我们用一个贴近业务的例子，完整展示从 Schema 定义到结果落地的流程。目标是把自由文本简历，抽取成可入库的简历实体。

定义实体：
```java
@JsonClassDescription("简历")
public static class Resume {
    public String name; // 姓名
    public String email; // 邮箱
    public String phone; // 手机
    @JsonProperty("experience_years")
    @JsonPropertyDescription("总工作年限，整数")
    public Integer yearsOfExperience; // 工作年限
    @JsonProperty("experiences")
    public List<WorkExperience> workExperiences; // 工作经验
    @JsonPropertyDescription("工作技能")
    public List<String> skills; // 技能
    @JsonPropertyDescription("家庭地址")
    public Address address; // 家庭地址
}

@JsonClassDescription("工作经验")
public static class WorkExperience {
    public String company; // 公司
    public String position; // 职位
    @JsonPropertyDescription("工作年限，整数")
    public int duration; // 工作年限
    @JsonProperty("start_time")
    @JsonPropertyDescription("工作开始时间，格式为 yyyy-MM-dd")
    public String startTime; // 工作开始时间
    @JsonProperty("end_time")
    @JsonPropertyDescription("工作截止时间，格式为 yyyy-MM-dd")
    public String endTime; // 工作截止时间
}

@JsonClassDescription("家庭地址")
public static class Address {
    public String prov;
    public String city;
}
```

构建 Agent 并调用：
```java
// 模型
DashScopeChatModel model = DashScopeChatModel.builder()
        .apiKey(System.getenv("DASHSCOPE_API_KEY")) // API 密钥
        .modelName(MODEL_NAME) // 模型名称
        .endpointType(EndpointType.MULTIMODAL) // 根据模型选择
        .build();

// 创建 ReActAgent
ReActAgent agent = ReActAgent.builder()
        .name("智能助手")
        .sysPrompt("你是一个专业的简历解析助手。请从用户的简历文本中提取关键信息，输出结构化的简历数据。")
        .model(model)
        .structuredOutputReminder(StructuredOutputReminder.TOOL_CHOICE)
        .build();

// 调用智能体
String resumeText = """
        张三，5年Java开发经验。
        2019-2022 就职于阿里巴巴，担任高级Java工程师，负责电商核心系统开发。
        2022-至今 就职于字节跳动，担任技术专家，负责微服务架构设计。
        精通 Java、Spring Boot、Redis、MySQL、Kubernetes。
        邮箱: zhangsan@mail.com，电话: 1234567890
        住址: 山东省 淄博市
        """;
Msg userMsg = Msg.builder()
        .role(MsgRole.USER)
        .textContent("请解析以下简历: \n" + resumeText)
        .build();

try {
    Msg msg = agent.call(userMsg, Resume.class).block();
    // 结构化输出
    if (msg == null) {
        System.out.println("无回复");
    } else if (!msg.hasStructuredData()) {
        // 结构化抽取失败，触发降级
        // ...
        throw new IllegalStateException("结构化输出未生成");
    } else {
        Resume resume = msg.getStructuredData(Resume.class);
        ObjectMapper objectMapper = new ObjectMapper();
        String jsonString = objectMapper.writeValueAsString(resume);
        System.out.println(jsonString);
    }
} catch (Exception e) {
    System.err.println("处理失败: " + e.getMessage());
}
```

输出结果是标准 JSON，字段严格对齐注解定义，下游不需要任何文本解析：
```json
{
  "name": "张三",
  "email": "zhangsan@mail.com",
  "phone": "1234567890",
  "skills": [
    "Java",
    "Spring Boot",
    "Redis",
    "MySQL",
    "Kubernetes"
  ],
  "address": {
    "prov": "山东省",
    "city": "淄博市"
  },
  "experience_years": 5,
  "experiences": [
    {
      "company": "阿里巴巴",
      "position": "高级Java工程师",
      "duration": 3,
      "start_time": "2019-01-01",
      "end_time": "2022-12-31"
    },
    {
      "company": "字节跳动",
      "position": "技术专家",
      "duration": 2,
      "start_time": "2022-01-01",
      "end_time": "2024-12-31"
    }
  ]
}
```

> 完整代码：[StructuredOutputExample](https://github.com/sjf0115/spring-ai-example/blob/main/agentscope/quickstart/src/main/java/com/example/output/StructuredOutputExample.java)

---

## 8. 总结

| 要点 | 内容 |
|-----|------|
| **核心机制** | Class → JSON Schema → 动态临时工具 `generate_response`，模型以 Function Calling 方式产出结构化数据，用完即焚 |
| **使用方式** | `agent.call(msg, Class)`（或 `call(msgs, JsonNode schema)`）+ `response.getStructuredData(Class)` |
| **流程控制** | `StructuredOutputHook` 四拍驱动：提醒重试（上限 3）→ 强制 tool_choice → 成功即停 → 记忆压缩 + 用量聚合 |
| **提醒策略** | TOOL_CHOICE（默认，强制收敛，需模型支持 tool_choice 参数）/ PROMPT（legacy，注入提醒重试） |
| **Schema 定义** | 静态类 + public 字段；`@JsonProperty` 改名、`@JsonPropertyDescription`/`@JsonClassDescription` 写语义 |
| **健壮性** | `hasStructuredData()` 先检查；IllegalState/IllegalArgument 分类处理；准备降级 Schema |

掌握 Structured Output 后，你的 Agent 不再只是"会说话"，而是能 **稳定、可靠、可预测** 地输出结构化数据，无缝对接数据库、API、配置系统等下游组件。

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
| 八 | [AgentScope Java 入门 8：Tool 工具系统——让 Agent 真正"动手做事"](https://smartsi.blog.csdn.net/article/details/161359990) |
| 九 | [AgentScope Java 入门 9：MCP 协议集成——连接无限工具生态](https://smartsi.blog.csdn.net/article/details/170775428) |
| 十 | [AgentScope Java 入门 10：如何使用 Structured Output 让模型输出结构化数据](https://smartsi.blog.csdn.net/article/details/170821616) |
