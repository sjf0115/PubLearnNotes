在之前文章中，我们构建了能思考、能监控、能调用本地工具和 MCP 远程工具的 Agent。但随着 Agent 能力不断扩展，一个新的问题浮现：**如何让 Agent 在拥有数十种能力的同时，不因为上下文过长而"失忆"或"混乱"？**

AgentScope Java 的 **Agent Skill（智能体技能包）** 机制正是为解决这一问题而设计。它将 Agent 的能力拆解为独立的模块化技能包，采用 **渐进式披露** 策略——仅在需要时才加载相关能力和上下文，让 Agent 既能"博学多才"，又能"专注当下"。

---

> 如何把一组“指令 + 参考文档 + 示例 + 脚本”封装成可复用技能，并注册给 ReActAgent，让智能体在需要时加载、执行或调用

## 1. 什么是 Agent Skill？

**Agent Skill 是扩展智能体能力的模块化技能包。** 每个 Skill 包含：

| 组成部分 | 说明 |
|---------|------|
| **指令（Instruction）** | Skill 的核心能力说明，告诉 Agent 何时以及如何使用 |
| **元数据（Metadata）** | 技能的描述信息，帮助 Agent 判断是否需要使用该技能 |
| **资源（Resources）** | 可选的参考文档、示例代码、脚本等，按需加载 |

> **参考资料**: [Claude Agent Skills 官方文档](https://platform.claude.com/docs/zh-CN/agents-and-tools/agent-skills/overview)

**与本地 Tool 的核心区别**：

| 维度 | 本地 Tool | Agent Skill |
|------|----------|-------------|
| **定位** | 单一功能的方法 | 完整的能力模块（指令 + 工具 + 资源） |
| **上下文管理** | 始终占用上下文 | **渐进式加载**，需要时才展开 |
| **资源支持** | 无 | 可附带文档、脚本、示例 |
| **工具绑定** | 独立注册 | Skill 激活时才暴露相关 Tool |
| **适用场景** | 高频、通用操作 | 专业领域、复杂任务、需要参考材料的场景 |

---

## 2. 核心设计理念：渐进式披露机制

Agent Skill 最核心的设计是 **三阶段按需加载**：
```
第一阶段：元数据暴露（~100 tokens/Skill）
    │
    │  Agent 初始化时，只加载每个 Skill 的名称和 description
    │  → 让 Agent 知道"我会什么"，但不知道"具体怎么做"
    │
    ▼
用户提问："帮我分析一下这份销售数据"
    │
    ▼
第二阶段：完整指令加载（< 5k tokens）
    │
    │  Agent 识别到需要 data_analysis Skill
    │  → 调用 load_skill_through_path 加载完整指令
    │  → 同时激活绑定的 Tool
    │
    ▼
第三阶段：资源按需访问
    │
    │  执行过程中需要参考 API 文档或示例代码
    │  → 再次调用 load_skill_through_path 加载特定资源文件
    │  → 如路径错误，返回可用资源列表帮助 LLM 纠正
    │
    ▼
完成任务
```

**为什么这很重要？** 假设你的 Agent 拥有 20 个 Skill，每个 Skill 的完整指令 + 资源共 5k tokens：
- **传统方式**：一次性全部加载 → 100k tokens 的上下文 → 成本高、模型易混乱
- **渐进式披露**：只加载用到的 Skill → 可能只需 5-10k tokens → 成本低、更精准

---

## 3. 核心特性

### 3.1 渐进式披露机制

采用 **三阶段按需加载** 优化上下文: 初始化时仅加载元数据(~100 tokens/Skill) → AI 判断需要时加载完整指令(<5k tokens) → 按需访问资源文件。Tool 同样渐进式披露,仅在 Skill 激活时生效。

**工作流程:** 用户提问 → AI 识别相关 Skill → 调用 `load_skill_through_path` 工具加载内容并激活绑定的 Tool → 按需访问资源 → 完成任务

**统一加载工具**: `load_skill_through_path(skillId, resourcePath)` 提供单一入口加载技能资源
- `skillId` 使用枚举字段, 确保只能从已注册的 Skill 中选择, 保证准确性
- `resourcePath` 是相对于 Skill 根目录的资源路径(如 `references/api-doc.md`)
- 路径错误时会返回所有可用的资源路径列表,帮助 LLM 纠正

### 3.2 适应性设计

我们将 Skill 进行了进一步的抽象,使其的发现和内容加载不再依赖于文件系统,而是 LLM 通过 Tool 来发现和加载 Skill 的内容和资源。同时为了兼容已有的 Skill 生态与资源,Skill 的组织形式依旧按照文件系统的结构来组织它的内容和资源。

**像在文件系统里组织 Skill 目录一样组织 Skill 的内容和资源吧!**

以 [Skill 结构](#skill-结构) 为例,这种目录结构的 Skill 在我们的系统中的表现形式就是:

```java
AgentSkill skill = AgentSkill.builder()
    .name("data_analysis")
    .description("Use this skill when analyzing data, calculating statistics, or generating reports")
    .skillContent("# Data Analysis\n...")
    .addResource("references/api-doc.md", "# API Reference\n...")
    .addResource("references/best-practices.md", "# Best Practices\n...")
    .addResource("examples/example1.java", "public class Example1 {\n...\n}")
    .addResource("scripts/process.py", "def process(data): ...\n")
    .build();
```

## 4. Skill 介绍

### 4.1 Skill 结构

Agent Skill 的设计不是把所有内容一次性塞进提示词，而是把技能拆成：
- 一个入口文件 `SKILL.md`
- 若干参考文档 `references/`
- 若干示例 `examples/`
- 若干可执行脚本 `scripts/`

```
skill-name/                      # Skill 根目录
├── SKILL.md                     # 必需：入口文件，包含 YAML frontmatter + 指令
├── references/                  # 可选：参考文档
│   ├── api-doc.md
│   └── best-practices.md
├── examples/                    # 可选：示例
│   └── example1.java
└── scripts/                     # 可选：可执行脚本
    └── process.py
```

### 4.2 SKILL.md 格式规范

`SKILL.md` 是入口，包含 YAML frontmatter 和正文指令：
```
---
name: skill-name                    # 必需: 技能名称(小写字母、数字、下划线)
description: This skill should be used when...  # 必需: 触发描述,说明何时使用
homepage: https://example.com/docs  # 可选: 额外 metadata,会暴露到智能体提示词中
metadata:
  clawdbot:
    requires:
      env:
        - API_KEY
---

# 技能名称

## 功能概述
[详细说明该技能的功能]

## 使用方法
[使用步骤和最佳实践]

## 可用资源
- references/api-doc.md: API 参考文档
- scripts/process.py: 数据处理脚本
```

**必需字段:**

| 字段 | 要求 | 说明 |
|------|------|------|
| `name` | 必需 | Skill 名称，只能包含小写字母、数字、下划线 |
| `description` | 必需 | **最关键字段**。描述 Skill 的使用场景，帮助 LLM 判断何时调用 |

**Metadata 说明:**
- YAML frontmatter 中除 `name`、`description` 外的字段都会作为 Skill metadata 保留，不再局限于固定字段
- 支持嵌套 `Map/List`，并保留原有层级结构和插入顺序
- frontmatter 使用 SnakeYAML `SafeConstructor` 解析，只接受顶层为 `Map` 的 YAML 对象
- 非法 frontmatter 或超过解析器限制的 frontmatter 会被忽略，并按空 metadata 处理

> SKILL.md 既承担元数据声明，也承担“给智能体看的操作说明”。

Skill 示例：
```
---
name: data_analysis              # 必需：技能名称（小写字母、数字、下划线）
description: Use this skill when analyzing data, calculating statistics, or generating reports
homepage: https://example.com/docs  # 可选：额外 metadata
metadata:
  requires:
    env:
      - API_KEY
---

# 数据分析技能

## 功能概述
提供数据清洗、统计分析、可视化报告生成等能力。

## 使用方法
1. 使用 load_data 工具加载数据
2. 使用 analyze 工具进行统计分析
3. 使用 generate_report 工具生成可视化报告

## 可用资源
- references/api-doc.md: API 参考文档
- scripts/process.py: 数据处理脚本
- examples/sample.csv: 示例数据
```

## 5. 如何创建 Skill

AgentScope Java 提供了 AgentSkill 类，创建方式很灵活。

### 5.1 Builder 内联构建

适合小技能或快速原型：
```java
// 1. 通过 Builder 链式构建一个技能
//    - putMetadata：写入自定义元数据（键值对）
//    - addResource：为技能附加参考资源（相对路径 -> 文本内容）
AgentSkill skill = AgentSkill.builder()
        .name("data_analysis")
        .description("Use when analyzing data, computing statistics, or generating reports")
        .putMetadata("homepage", "https://example.com/docs")
        .putMetadata("version", "1.0.0")
        .skillContent("# 数据分析技能\n\n本技能用于对表格数据做描述性统计并生成简要报告。\n\n## 工作流程\n1. 读取数据\n2. 计算均值 / 方差 / 标准差\n3. 总结趋势与异常值")
        .addResource("references/formulas.md", "# 常用公式\nmean = Σx / n")
        .addResource("examples/sample.csv", "name,value\nA,100\nB,200")
        .source("custom")
        .build();
```

### 5.2 从 Markdown 创建

```java
// 1. 一段带 YAML frontmatter 的 SKILL.md 文本
String skillMd = """
    ---
    name: data_analysis
    description: Use this skill when analyzing data, calculating statistics, or generating reports
    ---
    # 数据分析技能

    本技能用于对表格数据做描述性统计并生成简要报告。

    ## 工作流程
    1. 读取数据
    2. 计算均值 / 方差 / 标准差
    3. 总结趋势与异常值
    """;

// 2. 技能附带的参考资源（相对路径 -> 文本内容）
Map<String, String> resources = Map.of(
        "references/formulas.md", "# 常用公式\nmean = Σx / n",
        "examples/sample.csv", "name,value\nA,100\nB,200"
);

// 3. 解析创建
AgentSkill skill = SkillUtil.createFrom(skillMd, resources, "markdown");
```

### 5.3 直接构造函数

```java
// 1. 四参构造：resources 允许为 null
Map<String, String> resources = Map.of(
        "references/formulas.md", "# 常用公式\nmean = Σx / n",
        "examples/sample.csv", "name,value\nA,100\nB,200"
);
AgentSkill skill = new AgentSkill(
        "data_analysis",                    // name
        "Use when analyzing data, computing statistics, or generating reports",       // description
        "# 数据分析技能\n\n本技能用于对表格数据做描述性统计并生成简要报告。\n\n## 工作流程\n1. 读取数据\n2. 计算均值 / 方差 / 标准差\n3. 总结趋势与异常值", // skillContent
        resources,  // resources（可为 null）
        "builtin"   // 可选 source
);
```
三种方式本质一样，选顺手的即可。实际项目中，更推荐把技能做成目录，用仓库加载，而不是全部内联在代码里。

## 6. 集成到 ReActAgent：SkillBox

技能创建好后，需要注册到 SkillBox，再交给 ReActAgent：
```java
// 1. 创建 Toolkit 和 SkillBox
Toolkit toolkit = new Toolkit();
SkillBox skillBox = new SkillBox(toolkit);

// 2. 注册 Skill
skillBox.registerSkill(skill);

// 3. 创建 Agent
ReActAgent agent = ReActAgent.builder()
        .name("Friday")
        .sysPrompt("You are a helpful assistant called Friday. 当任务匹配已注册技能时，请激活该技能并按其说明执行。")
        .model(DashScopeChatModel.builder()
                .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                .modelName(MODEL_NAME)
                .endpointType(EndpointType.MULTIMODAL)
                .build())
        .toolkit(toolkit)
        .skillBox(skillBox) // 自动注册 skill 加载工具和 hook
        .memory(new InMemoryMemory())
        .build();
```
> SkillBox 是管理 Skill 的核心容器，负责注册 Skill、管理加载工具、处理渐进式披露。SkillBox 依赖 Toolkit。通过 registerSkill(skill) 注册技能。

**SkillBox 会自动完成**：
- 注册 `load_skill_through_path` 工具，供 LLM 加载 Skill 内容和资源
- 注册 Hook，管理 Skill 的激活状态
- 维护 Skill 元数据列表，供 LLM 决策时使用

---

## 7. 让技能真正跑起来：代码执行与安全边界

Skill 经常需要执行代码（Python 脚本、Shell 命令等）。AgentScope 提供了隔离的代码执行环境。使用 Builder 模式按需组合工具和配置：
```java
SkillBox skillBox = new SkillBox(toolkit);
// 启用所有代码执行工具（Shell、读文件、写文件）
skillBox.codeExecution()
        .withShell()
        .withRead()
        .withWrite()
        .enable();
```
对应能力：
- withShell()：启用 Shell 命令执行；
- withRead()：启用读文件；
- withWrite()：启用写文件。

但直接开 Shell 是有风险的。AnentScope 给出了不少安全控制手段：
```java
// 创建带审批回调的自定义 Shell 工具
ShellCommandTool customShell = new ShellCommandTool(
        null,  // baseDir 会被自动覆盖为 workDir
        Set.of("python3", "node", "npm"),           // 允许执行的命令白名单
        command -> {                                // 审批回调
            System.out.print("执行命令: " + command + " ? (y/n): ");
            return new Scanner(System.in).nextLine().trim().equalsIgnoreCase("y");
        }
);

skillBox.codeExecution()
        .workDir("/data/agent-workspace")              // 工作目录
        .uploadDir("/data/agent-workspace/skills")     // Skill 资源上传位置
        .includeFolders(Set.of("scripts/", "data/"))   // 允许上传的文件夹
        .includeExtensions(Set.of(".py", ".js", ".sh")) // 允许上传的文件扩展名
        .withShell(customShell)
        .withRead()
        .withWrite()
        .enable();
```

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `workDir` | 代码执行的工作目录。所有工具共享的工作目录。指定时自动创建，未指定时延迟创建临时目录 `agentscope-code-execution-*`,JVM 退出自动清理 | 临时目录 `agentscope-code-execution-*` |
| `uploadDir` | Skill 资源文件的上传位置 | `workDir/skills` |
| `includeFolders` | 允许上传的资源文件夹 | `scripts/`、`assets/` |
| `includeExtensions` | 允许上传的文件扩展名 | `.py`、`.js`、`.sh` |
| `fileFilter()` | 完全自定义的文件过滤逻辑 | - |

> `includeFolders`/`includeExtensions` 与 `fileFilter()` 互斥，只能选一种方式。

## 8. 技能仓库：让技能可管理、可复用

技能多了以后，需要仓库来统一管理。AgentScope Java 提供了统一的 AgentSkillRepository 接口，以及多种实现。

### 8.1 文件系统存储

```java
// 创建仓库
AgentSkillRepository repo = new FileSystemSkillRepository(Path.of("./skills"));
// 保存 Skill
repo.save(List.of(dataSkill, emailSkill), false);
// 读取 Skill
AgentSkill loaded = repo.getSkill("data_analysis");
List<AgentSkill> allSkills = repo.getAllSkills();
```

Skill 会被保存为如下目录结构：
```
skills/
├── data_analysis/
│   ├── SKILL.md
│   ├── references/
│   │   └── formulas.md
│   └── examples/
│       └── sample.csv
└── email_service/
    └── SKILL.md
```

### 8.2 MySQL数据库存储

```java
// 使用简单构造函数（使用默认数据库/表名）
DataSource dataSource = createDataSource();  // 你的数据源

// 方式一：简单构造函数（使用默认数据库/表名）
MysqlSkillRepository repo = new MysqlSkillRepository(dataSource, true, true);

// 方式二：Builder 自定义配置
MysqlSkillRepository repo = MysqlSkillRepository.builder(dataSource)
        .databaseName("my_database")
        .skillsTableName("my_skills")
        .resourcesTableName("my_resources")
        .createIfNotExist(true)   // 表不存在时自动创建
        .writeable(true)          // 允许写入
        .build();

// 保存和读取
repo.save(List.of(skill), false);
AgentSkill loaded = repo.getSkill("data_analysis");
```

### 8.3 Git仓库 (只读)

用于从 Git 仓库加载 Skills (只读)。支持 HTTPS 和 SSH。适合团队共享 Skills，支持自动同步。
```java
// 自动同步（默认）：每次读取时检查远端更新
AgentSkillRepository repo = new GitSkillRepository(
        "https://github.com/your-org/your-skills-repo.git");

AgentSkill skill = repo.getSkill("data-analysis");
List<AgentSkill> allSkills = repo.getAllSkills();

// 手动同步模式
GitSkillRepository manualRepo = new GitSkillRepository(
        "https://github.com/your-org/your-skills-repo.git",
        false);  // 关闭自动同步

// 需要时手动刷新
manualRepo.sync();
```

如果仓库中存在 `skills/` 子目录，会优先从该目录加载，否则使用仓库根目录。

**同步机制**：
- 默认每次读取都会做轻量化的远端引用检查
- 仅当远端 HEAD 变化时才会执行 `git pull`
- 可通过构造函数关闭自动同步，改为手动调用 `sync()`

### 8.4 Classpath 仓库 (只读)

用于从 classpath 资源中加载预打包的 Skills (只读)。自动兼容标准 JAR 和 Spring Boot Fat JAR。
```java
try (ClasspathSkillRepository repository = new ClasspathSkillRepository("skills")) {
    AgentSkill skill = repository.getSkill("data-analysis");
    List<AgentSkill> allSkills = repository.getAllSkills();
} catch //...
```

资源目录结构: `src/main/resources/skills/` 下放置多个 Skill 子目录,每个子目录包含 `SKILL.md`

> 注意: `JarSkillRepositoryAdapter` 已废弃,请使用 `ClasspathSkillRepository`。

### 8.5 Nacos 仓库 (只读)

通过已构建的 `AiService`（或 Nacos 连接配置）从 Nacos 拉取或订阅 Skill，Agent 运行时从 Nacos 实时获取，支持变更订阅与自动感知，适合需要与 Nacos 保持同步的在线场景。

```java
// 使用已构建的 AiService 创建 Nacos 技能仓库
try (NacosSkillRepository repository = new NacosSkillRepository(aiService, "namespace")) {
    AgentSkill skill = repository.getSkill("data-analysis");
    boolean exists = repository.skillExists("data-analysis");
} catch //...
```

> 注意: 需引入 `agentscope-extensions-nacos-skill` 依赖


## 9. 提示词注入：别让技能列表撑爆上下文

SkillBox 在注入给 Agent 的系统提示词中，会为每个已注册的 Skill 生成一个 XML `<skill>` 条目，供 LLM 判断何时加载哪个 Skill：
```
<skill>
  ...
  <skill-id>...</skill-id>
  instruction
  <item>...</item>
</skill>
```
以及技能列表：
```
<available_skills>
...
</available_skills>
```
这意味着每注册一个技能，就有一段元数据进入提示词。技能多的时候，全部暴露会占用大量上下文。AgentScope 提供了多个控制手段。

### 9.1 自定义 instruction 头部

自定义 SkillBox 的技能说明头部可以替换默认说明头部，用你自己的话告诉模型“技能列表在哪、怎么用”。可以强调 `load_skill_through_path` 的调用说明。
```java
String customInstruction = """
## 可用技能
当任务匹配某个技能时，使用 load_skill_through_path 加载它。
""";

SkillBox skillBox = new SkillBox(toolkit, customInstruction);
```
默认头部可能比较通用。自定义之后，你可以：
- 用更短的话减少 token；
- 针对业务场景写更明确的触发指引；
- 把“先判断是否需要技能，再加载”的流程写进 instruction，引导模型按需加载而不是一次性全看。

### 9.2 只暴露核心 metadata

默认可能暴露全部 metadata，关闭后可将提示词限制为只暴露 `name`、`description` 和 `skill-id`，减少提示词膨胀和不必要的元数据泄露：
```
skillBox.setExposeAllSkillMetadata(false);
```

### 9.3 自定义代码执行说明

开启代码执行后，默认会有一段说明告诉模型“脚本在哪、怎么执行”：
```java
skillBox.codeExecution()
    .workDir("/data/workspace")
    .codeExecutionInstruction("""
      ## 脚本执行
      技能脚本根目录: %s
      执行时请使用绝对路径。
      """)
    .withShell()
    .enable();
```
`codeExecutionInstruction` 允许你替换这段说明，所有 `%s` 占位符都会被替换为 `uploadDir` 的绝对路径。

## 10. Tool 的渐进式披露

这是 Skill 系统最强大的特性——**将 Tool 与 Skill 绑定，实现按需激活**。避免预先注册所有 Tool 导致的上下文污染，仅在 Skill 被 LLM 使用时才传递相关 Tool。

> **渐进式暴露的Tool的生命周期**: Tool 与 Skill 生命周期保持一致, Skill 激活后 Tool 在整个会话期间保持可用, 避免了旧机制中每轮对话后 Tool 失活导致的调用失败问题。

### 10.1 为什么需要渐进式披露？

传统方式下，所有 Tool 都预先注册到 Toolkit 中：
```java
// 传统方式：所有工具一开始就暴露给 LLM
Toolkit toolkit = new Toolkit();
toolkit.registerTool(new DataLoadTool());      // 数据分析
toolkit.registerTool(new EmailSendTool());     // 邮件发送
toolkit.registerTool(new GitCommitTool());     // Git 操作
// ... 20 个工具全部注册
```

**问题**：
- 上下文冗长：20 个工具的 Schema 占用大量 tokens
- 决策困难：LLM 容易选错工具
- 安全隐患：所有工具始终可用，无法按需管控

### 10.2 Skill 绑定 Tool 实现按需激活

```java
Toolkit toolkit = new Toolkit();
SkillBox skillBox = new SkillBox(toolkit);

// 1. 创建 Skill
AgentSkill dataSkill = AgentSkill.builder()
        .name("data_analysis")
        .description("Comprehensive data analysis capabilities")
        .skillContent("# Data Analysis\n...")
        .build();

// 2. 创建与 Skill 绑定的 Tool
AgentTool loadDataTool = new AgentTool() {
    @Override
    public String getName() { return "load_data"; }

    @Override
    public String getDescription() { return "Load data from file"; }

    @Override
    public Mono<ToolResultBlock> callAsync(ToolCallParam param) {
        String path = (String) param.getInput().get("path");
        // 加载数据逻辑...
        return Mono.just(ToolResultBlock.text("Data loaded: " + path));
    }
};

// 3. 将 Tool 绑定到 Skill
skillBox.registration()
        .skill(dataSkill)
        .tool(loadDataTool)
        .apply();  // Tool 此时不会暴露给 LLM

// 4. 构建 Agent
ReActAgent agent = ReActAgent.builder()
        .name("Assistant")
        .model(model)
        .toolkit(toolkit)
        .skillBox(skillBox)
        .build();
```

**执行流程**：

```
用户：分析这份销售数据
    │
    ▼
Agent 看到 data_analysis Skill 的元数据
    │
    ▼
Agent 调用 load_skill_through_path("data_analysis", "SKILL.md")
    │
    ▼
data_analysis Skill 激活 → load_data Tool 自动暴露给 LLM
    │
    ▼
Agent 调用 load_data Tool 加载数据 → 完成分析
```

**Tool 生命周期**：
- Skill 激活后，绑定的 Tool 在整个会话期间保持可用
- 避免了旧机制中每轮对话后 Tool 失活导致的调用失败问题

---

## 11. 实战：构建数据分析 Agent

以下示例展示了 Skill 系统的完整使用流程：

```java
public class SkillDemo {
    public static void main(String[] args) {
        // 1. 创建 Skill
        AgentSkill dataSkill = AgentSkill.builder()
                .name("data_analysis")
                .description("""
                        Use this skill when analyzing data, calculating statistics, \
                        generating reports, or working with CSV/Excel files
                        """)
                .skillContent("""
                        # 数据分析技能

                        ## 功能概述
                        提供数据清洗、统计分析、可视化报告生成。

                        ## 使用方法
                        1. 使用 load_data 工具加载数据文件
                        2. 使用 analyze 工具进行统计分析
                        3. 使用 generate_report 工具生成报告

                        ## 可用资源
                        - references/statistics-guide.md: 统计方法指南
                        - examples/sample-sales.csv: 销售数据示例
                        - scripts/visualize.py: 可视化脚本
                        """)
                .addResource("references/statistics-guide.md", """
                        # 统计方法指南

                        ## 描述性统计
                        - 均值：数据的平均水平
                        - 中位数：数据的中间值，不受异常值影响
                        - 标准差：数据的离散程度

                        ## 注意事项
                        分析前务必检查数据缺失值。
                        """)
                .addResource("examples/sample-sales.csv", """
                        month,sales,region
                        2024-01,150000,East
                        2024-02,180000,West
                        2024-03,165000,East
                        """)
                .addResource("scripts/visualize.py", """
                        import matplotlib.pyplot as plt
                        def plot_sales(data):
                            plt.plot(data['month'], data['sales'])
                            plt.savefig('sales.png')
                        """)
                .build();

        // 2. 创建 Toolkit 和 SkillBox
        Toolkit toolkit = new Toolkit();
        SkillBox skillBox = new SkillBox(toolkit);

        // 3. 注册 Skill
        skillBox.registerSkill(dataSkill);

        // 4. 启用代码执行（让 Agent 能运行 scripts/visualize.py）
        skillBox.codeExecution()
                .withShell()
                .withRead()
                .withWrite()
                .workDir("/tmp/agent-workspace")
                .enable();

        // 5. 持久化到文件系统（可选）
        FileSystemSkillRepository repo = new FileSystemSkillRepository(Path.of("./skills"));
        repo.save(List.of(dataSkill), false);

        // 6. 创建 Agent
        ReActAgent agent = ReActAgent.builder()
                .name("DataAnalyst")
                .sysPrompt("你是一位专业的数据分析师，擅长使用工具分析数据并生成洞察。")
                .model(DashScopeChatModel.builder()
                        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                        .modelName("qwen3.6-plus")
                        .build())
                .toolkit(toolkit)
                .skillBox(skillBox)
                .memory(new InMemoryMemory())
                .maxIters(15)
                .build();

        // 7. 调用
        Msg response = agent.call(
                Msg.builder()
                        .role(MsgRole.USER)
                        .textContent("分析 2024 年前三月的销售数据，找出增长趋势")
                        .build()
        ).block();

        System.out.println(response.getTextContent());
    }
}
```

**执行流程**：

```
用户：分析 2024 年前三月的销售数据，找出增长趋势
    │
    ▼
Agent 看到 data_analysis Skill 的 description
    │
    ▼
调用 load_skill_through_path("data_analysis", "SKILL.md")
    │
    ▼
加载完整指令 → 发现需要 load_data、analyze、generate_report 工具
    │
    ▼
调用 load_data 加载 examples/sample-sales.csv
    │
    ▼
分析数据：1月 15万 → 2月 18万 → 3月 16.5万，2月峰值，整体波动
    │
    ▼
可选：调用 load_skill_through_path 加载 references/statistics-guide.md
    │
    ▼
生成回答：包含数据趋势分析和业务建议
```

---

## 12. 总结

| 要点 | 内容 |
|------|------|
| **核心概念** | Agent Skill 是包含指令、元数据和资源的模块化能力包 |
| **核心设计** | **渐进式披露**：元数据 → 完整指令 → 按需资源，三阶段加载 |
| **创建方式** | Builder 模式（推荐）、Markdown 加载、直接构造 |
| **集成方式** | 通过 `SkillBox` 注册到 ReActAgent |
| **渐进式 Tool** | Tool 与 Skill 绑定，Skill 激活后才暴露 |
| **代码执行** | `skillBox.codeExecution()` 提供隔离的 Shell/读写环境 |
| **持久化** | 支持文件系统、MySQL、Git 三种存储方式 |

Agent Skill 让 Agent 的能力管理从"堆工具"进化为"装技能包"——按需加载、按需激活、按需执行。这是构建真正"博学而专注"的企业级 Agent 的基石。
