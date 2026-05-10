在之前的系列文章中，Agent 的输出都是 **自由文本** —— 用户问"今天天气怎么样"，Agent 回复一段描述性文字。这种方式在对话场景下很自然，但在很多业务场景中却捉襟见肘：
- **电商导购**：需要提取商品名称、价格、评分，存入数据库
- **智能表单**：需要将用户的自然语言描述转换为结构化的 JSON
- **数据分析**：需要将分析结果按固定格式输出，供下游系统解析
- **配置生成**：需要根据用户需求生成标准化的 YAML/JSON 配置

如果让 Agent 自由输出文本，然后用正则表达式或二次解析提取字段，不仅脆弱易错，还增加了系统复杂度。AgentScope 的 **Structured Output（结构化输出）** 功能正是为解决这一问题而生——它让 Agent 直接输出符合预定义 Schema 的类型化数据，一步到位，稳定可靠。

---

## 1. 为什么需要结构化输出？

### 1.1 自由文本的痛点

```
用户: "帮我分析这款手机的优缺点"
Agent 自由输出:
"这款手机的优点是屏幕很大、电池续航不错，缺点是价格偏高、拍照一般。"

问题：
- "屏幕很大" → 屏幕尺寸是多少？无法量化
- "电池续航不错" → 续航时间是多久？无法提取
- 下游系统需要写复杂的正则表达式来解析这段文本
```

### 1.2 结构化输出的优势

```
用户: "帮我分析这款手机的优缺点"
Agent 结构化输出:
{
  "productName": "iPhone 16 Pro",
  "price": 7999.0,
  "pros": ["屏幕大", "续航好"],
  "cons": ["价格高", "拍照一般"],
  "score": 4.2
}

优势：
- 字段明确，可直接映射到 Java 对象
- 类型安全，price 一定是 Double，score 一定是 Double
- 下游系统无需解析，直接 getScore()、getPrice()
```

---

## 2. 快速开始：三步搞定结构化输出

AgentScope 的结构化输出使用非常简单，只需三步：

### 2.1 第一步：定义 Schema 类

```java
// 产品信息
public static class ProductInfo {
    public String productType; // 产品类型
    public String brand; // 品牌
    public Integer minRam; // 最小内存
    public Double maxBudget; // 最大预算
    public List<String> features; // 特征
}
```

**关键要求** 必须是静态类，否则会出现如下异常：
```java
Caused by: java.lang.IllegalArgumentException: Cannot construct instance of `com.example.output.StructuredOutputExample$ProductInfo`: non-static inner classes like this can only by instantiated using default, no-argument constructor
```

### 2.2 第二步：调用 Agent 时指定输出类型

```java
// 用户消息
Msg userMsg = Msg.builder()
        .role(MsgRole.USER)
        .textContent("从这个查询中提取出产品需求: 我正在寻找一台笔记本电脑。我需要至少 16GB 的内存，最好是有苹果品牌的产品，而且我的预算在 8000 人民币左右。它还要便于携带以便于旅行使用。")
        .build();

// 调用 Agent，指定期望的输出类型为 ProductInfo.class
Msg response = agent.call(userMsg, ProductInfo.class).block();
```

### 2.3 第三步：提取结构化数据

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

---

## 3. 两种输出模式详解

AgentScope 提供两种结构化输出模式，适用于不同的模型和场景：

| 模式 | 机制 | 优点 | 缺点 | 适用模型 |
|-----|------|------|------|---------|
| **TOOL_CHOICE**（默认） | 利用模型的 Function Calling 能力，将 Schema 作为工具参数强制输出 | 一次 API 调用，稳定可靠，严格遵循 Schema | 需要模型支持 tool_choice | qwen3-max, gpt-4, claude-3 |
| **PROMPT** | 通过提示词引导模型输出 JSON，框架做后处理和校验 | 兼容性好，老模型也能用 | 可能需多次调用，稳定性略低 | 所有模型 |

### 3.1 TOOL_CHOICE 模式（推荐）

这是默认模式，利用模型原生的 Function Calling 能力：
```java
ReActAgent agent = ReActAgent.builder()
    .name("智能助手")
    .sysPrompt("你是一名智能分析助手。对用户请求进行分析，并给出条理清晰的回复。")
    .model(model)
    .structuredOutputReminder(StructuredOutputReminder.TOOL_CHOICE)
    .build();
```

**原理**：AgentScope 将你的 Schema 类转换为 JSON Schema，通过模型的 `tool_choice` 机制强制模型输出符合该 Schema 的数据。模型会把结构化输出当作一次"工具调用"来完成。

**优点**：
- 一次 API 调用即可完成
- 模型严格遵循 Schema，字段不会遗漏
- 类型匹配度高

### 3.2 PROMPT 模式（兼容）

当模型不支持 tool_choice 时使用：
```java
ReActAgent agent = ReActAgent.builder()
    .name("智能助手")
    .sysPrompt("你是一名智能分析助手。对用户请求进行分析，并给出条理清晰的回复。")
    .model(model)
    .structuredOutputReminder(StructuredOutputReminder.PROMPT)
    .build();
```

**原理**：AgentScope 在系统提示词中注入 Schema 定义和输出格式要求，引导模型输出 JSON。如果输出不符合 Schema，框架会自动重试或修正。

**适用场景**：
- 使用较老的模型（如早期版本的千问、GPT-3.5 等）
- 模型明确不支持 `tool_choice` 参数

---

## 4. Schema 定义

### 4.1 支持的类型

AgentScope 支持丰富的 Java 类型映射：
```java
public class Schema {
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

### 4.2 嵌套结构

复杂业务对象通常需要嵌套定义：
```java
public class Person {
    public String name;
    public Address address;
    public List<String> hobbies;
}

public class Address {
    public String city;
    public String street;
}
```

### 4.3 Jackson 注解

AgentScope 底层使用 Jackson 进行序列化/反序列化，因此支持 Jackson 注解：
```java
public class CustomSchema {
    @JsonProperty("product_name")  // 自定义字段名
    public String productName;

    @JsonIgnore  // 忽略字段
    public String internal;
}
```
生成的 JSON Schema 中，`productName` 会映射为 `product_name`，`internalId` 不会出现在 Schema 中。

---

## 5. 实战：智能简历解析

需求：用户上传一段简历文本，Agent 解析为结构化的简历信息。

### 5.1 定义 Schema

```java
// 简历
public static class Resume {
    public String name; // 姓名
    public String email; // 邮箱
    public String phone; // 手机
    public Integer yearsOfExperience; // 工作年限
    public List<WorkExperience> workExperiences; // 工作经验
    public List<String> skills; // 技能
    public Address address; // 家庭地址
}

// 工作经验
public static class WorkExperience {
    public String company; // 公司
    public String position; // 职位
    public String duration; // 工作时长
    public String startTime; // 工作开始时间
    public String endTime; // 工作截止时间
    public List<String> responsibilities; // 职责
}

// 家庭地址
public static class Address {
    public String prov;
    public String city;
}
```

### 5.2 创建 Agent

```java
// 模型
DashScopeChatModel model = DashScopeChatModel.builder()
        .apiKey(System.getenv("DASHSCOPE_API_KEY")) // API 密钥
        .modelName(MODEL_NAME) // 模型名称
        .build();

// 创建 ReActAgent
ReActAgent agent = ReActAgent.builder()
        .name("智能助手")
        .sysPrompt("你是一个专业的简历解析助手。请从用户的简历文本中提取关键信息，输出结构化的简历数据。")
        .model(model)
        .structuredOutputReminder(StructuredOutputReminder.TOOL_CHOICE)
        .build();
```

### 5.3 调用并提取

```java
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
Msg msg = agent.call(userMsg, Resume.class).block();
// 结构化输出
Resume resume = msg.getStructuredData(Resume.class);

ObjectMapper objectMapper = new ObjectMapper();
String jsonString = objectMapper.writeValueAsString(resume);
System.out.println(jsonString);
```

**预期输出**：
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
      "duration": "2019-2022",
      "responsibilities": [
        "负责电商核心系统开发"
      ],
      "start_time": "2019",
      "end_time": "2022"
    },
    {
      "company": "字节跳动",
      "position": "技术专家",
      "duration": "2022-至今",
      "responsibilities": [
        "负责微服务架构设计"
      ],
      "start_time": "2022",
      "end_time": "至今"
    }
  ]
}
```

> 完整代码：[]()

---

## 7. 错误处理与健壮性

结构化输出虽然强大，但生产环境中必须做好错误处理：

### 7.1 基础错误处理

```java
try {
    Msg response = agent.call(userMsg, ProductInfo.class).block();
    ProductInfo data = response.getStructuredData(ProductInfo.class);

    // 业务逻辑验证
    if (data.price == null || data.price < 0) {
        throw new IllegalArgumentException("价格字段无效: " + data.price);
    }
    if (data.name == null || data.name.isBlank()) {
        throw new IllegalArgumentException("商品名称不能为空");
    }

    // 正常业务处理
    saveToDatabase(data);

} catch (Exception e) {
    System.err.println("结构化输出处理失败: " + e.getMessage());
    // 降级处理：记录日志、返回默认值、或转人工处理
}
```

## 7. 总结

本文详细介绍了 AgentScope Java 的结构化输出功能：

| 要点 | 内容 |
|-----|------|
| **核心能力** | 让 Agent 输出符合预定义 Schema 的类型化数据 |
| **使用方式** | `agent.call(msg, Class)` + `response.getStructuredData(Class)` |
| **两种模式** | TOOL_CHOICE（默认，推荐）和 PROMPT（兼容老模型） |
| **Schema 定义** | 普通静态 Java 类，字段 public |
| **高级特性** | 支持嵌套对象、List、Map、Jackson 注解 |

掌握 Structured Output 后，你的 Agent 不再只是"会说话"，而是能 **稳定、可靠、可预测** 地输出结构化数据，无缝对接数据库、API、配置系统等下游组件。
