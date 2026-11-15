在之前文章中，我们构建了能思考、能监控、能调用本地工具和 MCP 远程工具的 Agent。但随着 Agent 能力不断扩展，一个新的问题浮现：**如何让 Agent 在拥有数十种能力的同时，不因为上下文过长而"失忆"或"混乱"？**

AgentScope Java 的 **Agent Skill（智能体技能包）** 机制正是为解决这一问题而设计。它将 Agent 的能力拆解为独立的模块化技能包，采用 **渐进式披露** 策略——仅在需要时才加载相关能力和上下文，让 Agent 既能"博学多才"，又能"专注当下"。本文将讲清楚：如何把一组"指令 + 参考文档 + 示例 + 脚本"封装成可复用技能，注册给 ReActAgent，并让智能体在需要时才加载、执行或调用。

> 文中 API 均以 **AgentScope Java 1.0.12** 源码为准核实。

---

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

## 2. 核心设计：渐进式披露机制

### 2.1 三阶段按需加载

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
    │  → 调用 load_skill_through_path 加载 SKILL.md，同时激活 Skill
    │  → 激活的同时，绑定的 Tool 自动暴露给 LLM
    │
    ▼
第三阶段：资源按需访问
    │
    │  执行过程中需要参考 API 文档或运行脚本
    │  → 再次调用 load_skill_through_path 加载特定资源文件
    │  → 如路径错误，返回可用资源列表帮助 LLM 纠正
    │
    ▼
完成任务
```

**为什么这很重要？** 假设你的 Agent 拥有 20 个 Skill，每个 Skill 的完整指令 + 资源共 5k tokens：

- **传统方式**：一次性全部加载 → 100k tokens 的上下文 → 成本高、模型易混乱
- **渐进式披露**：只加载用到的 Skill → 可能只需 5-10k tokens → 成本低、更精准

### 2.2 统一加载工具：load_skill_through_path

SkillBox 会自动注册一个统一入口工具，供 LLM 加载技能内容与资源：

```
load_skill_through_path(skillId, path)
```

- **`skillId`**：以枚举（enum）形式生成参数 Schema，LLM 只能从已注册的 Skill 中选择，从根上杜绝幻觉出不存在的技能；
- **`path`**：相对于 Skill 根目录的资源路径（如 `references/api-doc.md`）。注意参数名是 `path` 而不是 `resourcePath`；
- **`path="SKILL.md"` 有特殊语义**：加载入口文档的**同时激活该 Skill**（激活后绑定的 Tool 才会暴露）；
- 路径错误时，工具会返回**所有可用资源的路径列表**，帮助 LLM 自我纠正。

### 2.3 关键标识：name、source 与 skillId

三个概念贯穿全文，先一次性说清（1.0.12 源码 `AgentSkill#getSkillId`）：

| 标识 | 来源 | 用在哪 |
|------|------|--------|
| `name` | frontmatter 或 Builder 指定 | **仓库接口**按 name 读写：`repo.getSkill("data-analysis")` |
| `source` | 创建途径标识，构造器缺省为 `"custom"` | 参与 skillId 拼接，标记技能出处（如 `builtin`/`markdown`/`custom`） |
| `skillId` | **`name + "_" + source`**（如 `data-analysis_builtin`） | **运行时**按 skillId 操作：`load_skill_through_path`、`isSkillActive`、`removeSkill`、资源上传目录名 |

> 仓库层用 `name`、运行时用 `skillId`，两套键不要混用——这是初学者最常见的困惑点。

### 2.4 适应性设计：不依赖文件系统，但兼容文件系统

Skill 的发现和内容加载**不依赖文件系统**，而是由 LLM 通过 Tool 完成；但为了兼容已有的 Skill 生态（如 Claude Skills 目录规范），Skill 的内容与资源**仍按文件系统目录结构来组织**。

**像在文件系统里组织 Skill 目录一样组织 Skill 的内容和资源吧！** 一个目录结构的 Skill 在代码中的等价形式：

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

## 3. Skill 结构与 SKILL.md 规范

### 3.1 目录结构

Agent Skill 的设计不是把所有内容一次性塞进提示词，而是把技能拆成：一个入口文件 `SKILL.md`、若干参考文档 `references/`、若干示例 `examples/`、若干可执行脚本 `scripts/`：

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

### 3.2 SKILL.md 格式规范

`SKILL.md` 是入口，包含 YAML frontmatter 和正文指令：

```
---
name: data-analysis                     # 必需：技能名称
description: This skill should be used when...  # 必需：触发描述，说明何时使用
homepage: https://example.com/docs      # 可选：额外 metadata，会暴露到智能体提示词中
metadata:
  requires:
    env:
      - API_KEY
---

# 数据分析技能

## 功能概述
提供数据清洗、统计分析、可视化报告生成等能力。

## 使用方法
1. 读取 assets/ 下的数据文件
2. 运行 scripts/analyze.py 进行统计分析
3. 结合 references/ 中的公式文档解释结果

## 可用资源
- references/formulas.md: 常用统计公式速查
- scripts/analyze.py: 数据分析脚本
- assets/sample-sales.csv: 示例数据
```

> SKILL.md 既承担元数据声明，也承担"给智能体看的操作说明"。

**必需字段：**

| 字段 | 要求 | 说明 |
|------|------|------|
| `name` | 必需 | Skill 名称。1.0.12 源码**没有强制字符集校验**（仅在落盘时检查路径穿越），连字符、下划线均可（官方示例即用 `data-analysis`）；建议遵循社区惯例：小写字母、数字、连字符 |
| `description` | 必需 | **最关键字段**。描述 Skill 的使用场景，帮助 LLM 判断何时调用 |

**Metadata 说明：**

- YAML frontmatter 中除 `name`、`description` 外的字段都会作为 Skill metadata 保留，不再局限于固定字段；
- 支持嵌套 `Map/List`，并保留原有层级结构和插入顺序；
- frontmatter 使用 SnakeYAML `SafeConstructor` 解析，只接受顶层为 `Map` 的 YAML 对象；
- 非法 frontmatter 或超过解析器码点限制的 frontmatter 会被忽略，并按空 metadata 处理。

## 4. 如何创建 Skill

AgentScope Java 提供了 `AgentSkill` 类，创建方式很灵活。

### 4.1 Builder 内联构建

适合小技能或快速原型：

```java
// 通过 Builder 链式构建一个技能
//    - putMetadata：写入自定义元数据（键值对）
//    - addResource：为技能附加参考资源（相对路径 -> 文本内容）
//    - source：来源标识，参与 skillId 拼接（缺省 "custom"）
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

### 4.2 从 Markdown 创建

复用标准 SKILL.md 文本（如从 Git 仓库、配置中心拉取的内容）：

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

// 3. 解析创建（第三个参数是 source，该技能的 skillId 为 data_analysis_markdown）
AgentSkill skill = SkillUtil.createFrom(skillMd, resources, "markdown");
```

`SkillUtil.createFrom` 会解析 frontmatter 中的 `name` / `description`，正文作为 `skillContent`，并把传入的 `resources` 合并进技能；缺少 `name` 或 `description` 会直接抛 `IllegalArgumentException`。

### 4.3 直接构造函数：两个重载

```java
// 重载一：4 参构造，source 缺省为 "custom"，resources 允许为 null
AgentSkill skill = new AgentSkill(
        "data_analysis",                    // name
        "Use when analyzing data...",       // description
        "# Data Analysis\n...",             // skillContent
        null                                // resources（可为 null）
);

// 重载二：5 参构造，显式指定 source（skillId = data_analysis_builtin）
AgentSkill skill2 = new AgentSkill(
        "data_analysis",                    // name
        "Use when analyzing data, computing statistics, or generating reports",
        "# 数据分析技能\n\n## 工作流程\n1. 读取数据\n2. 计算统计量",  // skillContent
        Map.of("references/formulas.md", "# 常用公式\nmean = Σx / n"),
        "builtin"                           // source
);
```

三种方式本质一样，选顺手的即可。实际项目中，更推荐把技能做成目录，用仓库加载（见第 7 节），而不是全部内联在代码里。

## 5. 集成到 ReActAgent：SkillBox

技能创建好后，注册到 SkillBox，再交给 ReActAgent：

```java
// 1. 创建 Toolkit 和 SkillBox
Toolkit toolkit = new Toolkit();
SkillBox skillBox = new SkillBox(toolkit);

// 2. 注册 Skill
skillBox.registerSkill(skill);

// 3. 创建 Agent（必须同时传 toolkit 和 skillBox，技能才会被真正激活）
ReActAgent agent = ReActAgent.builder()
        .name("Friday")
        .sysPrompt("You are a helpful assistant called Friday. 当任务匹配已注册技能时，请激活该技能并按其说明执行。")
        .model(DashScopeChatModel.builder()
                .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                .modelName(MODEL_NAME)
                // qwen3.8 系列需显式指定 MULTIMODAL 端点，
                // AUTO 启发式会误判为纯文本导致 DashScope 返回 "url error"
                .endpointType(EndpointType.MULTIMODAL)
                .build())
        .toolkit(toolkit)
        .skillBox(skillBox) // 自动注册 skill 加载工具和 hook
        .memory(new InMemoryMemory())
        .build();

// 4. 查看已注册技能的 skillId 集合
System.out.println("已注册技能ID: " + skillBox.getAllSkillIds());
```

> SkillBox 是管理 Skill 的核心容器，负责注册 Skill、管理加载工具、处理渐进式披露，依赖 Toolkit。

**SkillBox 会自动完成**：

- 注册 `load_skill_through_path` 工具，供 LLM 加载 Skill 内容和资源；
- 注册 Hook，管理 Skill 的激活状态；
- 维护 Skill 元数据列表，注入系统提示词供 LLM 决策（见第 8 节）。

运行期还有一组管理 API：`isSkillActive(skillId)`、`deactivateAllSkills()`、`removeSkill(skillId)`、`getSkill(skillId)`。

---

## 6. 让技能真正跑起来：代码执行与安全边界

Skill 经常需要执行代码（Python 脚本、Shell 命令等）。AgentScope 提供了隔离的代码执行环境，用 Builder 模式按需组合工具和配置：

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

- `withShell()`：启用 Shell 命令执行，暴露给 LLM 的工具名是 **`execute_shell_command`**；
- `withRead()`：启用读文件；
- `withWrite()`：启用写文件。

### 6.1 Shell 的内置安全机制

直接开 Shell 是有风险的。`ShellCommandTool`（`io.agentscope.core.tool.coding` 包）内部已实现多道防线：

- **命令白名单校验**：仅允许预先放行的可执行文件；
- **多命令拼接拦截**：`&`、`|`、`;` 拼接的命令直接拒绝，防止绕过白名单；
- **人工审批回调**：白名单之外的命令走 `approvalCallback`，由人确认是否放行；
- **命令超时**：默认 300s；
- **工作目录限制**：所有相对路径解析到 `baseDir` 沙箱内。

```java
// 创建带审批回调的自定义 Shell 工具
ShellCommandTool customShell = new ShellCommandTool(
        null,                                       // baseDir 会被自动覆盖为 workDir
        Set.of("python3", "ls", "cat"),             // 允许执行的命令白名单
        command -> {                                // 审批回调
            System.out.print("执行命令: " + command + " ? (y/n): ");
            return new Scanner(System.in).nextLine().trim().equalsIgnoreCase("y");
        }
);

skillBox.codeExecution()
        .workDir("/data/agent-workspace")              // 工作目录
        .uploadDir("/data/agent-workspace/skills")     // Skill 资源上传位置
        .includeFolders(Set.of("scripts/", "assets/")) // 允许上传的资源文件夹
        .includeExtensions(Set.of(".py", ".sh"))       // 允许上传的文件扩展名
        .withShell(customShell)
        .withRead()
        .withWrite()
        .enable();
```

> **生产环境安全建议**：禁止使用无参 `new ShellCommandTool()`（无白名单 + 无审批，等同任意命令执行）；推荐 `new ShellCommandTool(baseDir, allowedCommands, approvalCallback)` 三参构造。

### 6.2 配置项与默认值

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `workDir` | 代码执行的工作目录，所有工具共享。指定时自动创建；未指定时延迟创建临时目录，JVM 退出自动清理 | 临时目录 `agentscope-code-execution-*` |
| `uploadDir` | Skill 资源文件的上传位置 | `workDir/skills` |
| `includeFolders` | 允许上传的资源文件夹 | `scripts/`、`assets/` |
| `includeExtensions` | 允许上传的文件扩展名 | `.py`、`.js`、`.sh` |
| `fileFilter()` | 完全自定义的文件过滤逻辑 | - |

> `fileFilter()` 与 `includeFolders`/`includeExtensions` **互斥**，同时设置会直接抛异常，只能二选一。
>
> 注意默认 `includeFolders` 只上传 `scripts/` 和 `assets/`——技能里的数据文件应放在 `assets/`（而非 `examples/`），否则不会进入执行环境。

## 7. 技能仓库：让技能可管理、可复用

技能多了以后，需要仓库统一管理。AgentScope Java 提供了统一的 `AgentSkillRepository` 接口（`AutoCloseable`，建议 try-with-resources）与五种实现。接口层面按 **name** 读写：`getSkill(name)`、`getAllSkillNames()`、`getAllSkills()`、`skillExists(name)`、`save(...)`。

> **依赖提示**：文件系统与 Classpath 仓库在核心包内；**Git、MySQL、Nacos 仓库是独立扩展包**，需分别引入 `agentscope-extensions-skill-git-repository`、`agentscope-extensions-skill-mysql-repository`、`agentscope-extensions-nacos-skill`。

### 7.1 文件系统存储

```java
// baseDir 必须已存在且为目录，否则抛 IllegalArgumentException
// 第二个参数 writeable：是否允许写操作
try (FileSystemSkillRepository repo = new FileSystemSkillRepository(Path.of("./skills"), true)) {
    // 保存 Skill
    repo.save(List.of(dataSkill, emailSkill), false);
    // 读取 Skill（按 name）
    AgentSkill loaded = repo.getSkill("data_analysis");
    List<AgentSkill> allSkills = repo.getAllSkills();
}
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

### 7.2 MySQL 数据库存储

```java
DataSource dataSource = createDataSource();  // 你的数据源

// 方式一：简单构造函数（使用默认数据库/表名）
MysqlSkillRepository repo = new MysqlSkillRepository(dataSource, true, true);

// 方式二：Builder 自定义配置
MysqlSkillRepository repo2 = MysqlSkillRepository.builder(dataSource)
        .databaseName("my_database")
        .skillsTableName("my_skills")
        .resourcesTableName("my_resources")
        .createIfNotExist(true)   // 表不存在时自动创建
        .writeable(true)          // 允许写入
        .build();

// 保存和读取
repo2.save(List.of(skill), false);
AgentSkill loaded = repo2.getSkill("data_analysis");
```

### 7.3 Git 仓库（只读）

用于从 Git 仓库加载 Skills（只读），支持 HTTPS 和 SSH，适合团队共享 Skills：

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

**加载约定**：如果仓库中存在 `skills/` 子目录，优先从该目录加载，否则使用仓库根目录。

**同步机制**：

- 默认每次读取都会做轻量化的远端引用检查；
- 仅当远端 HEAD 变化时才会执行 `git pull`；
- 可通过构造函数关闭自动同步，改为手动调用 `sync()`。

### 7.4 Classpath 仓库（只读）

用于从 classpath 资源中加载预打包的 Skills（只读），自动兼容标准 JAR 和 Spring Boot Fat JAR：

```java
try (ClasspathSkillRepository repository = new ClasspathSkillRepository("skills")) {
    AgentSkill skill = repository.getSkill("data-analysis");
    List<AgentSkill> allSkills = repository.getAllSkills();
}
```

资源目录结构：`src/main/resources/skills/` 下放置多个 Skill 子目录，每个子目录包含 `SKILL.md`。

> 注意：`JarSkillRepositoryAdapter` 已废弃，请使用 `ClasspathSkillRepository`。

### 7.5 Nacos 仓库（只读）

通过已构建的 `AiService` 从 Nacos 拉取或订阅 Skill，Agent 运行时实时获取，支持变更订阅与自动感知，适合需要与 Nacos 保持同步的在线场景：

```java
// namespaceId 为空时按 "public" 处理
try (NacosSkillRepository repository = new NacosSkillRepository(aiService, "namespace")) {
    AgentSkill skill = repository.getSkill("data-analysis");
    boolean exists = repository.skillExists("data-analysis");
}
```

## 8. 提示词注入：别让技能列表撑爆上下文

SkillBox 会把技能清单注入系统提示词。默认注入的头部（`DEFAULT_AGENT_SKILL_INSTRUCTION`）包含用法说明和 `<available_skills>` 列表，每个技能渲染为一个 `<skill>` 元素：

```
<available_skills>
<skill>
  <name>data-analysis</name>
  <description>Use this skill when analyzing tabular data...</description>
  <!-- 其余 metadata 逐项渲染 -->
  <skill-id>data-analysis_builtin</skill-id>
</skill>
...
</available_skills>
```

metadata 的 XML 渲染规则（源码约定）：

- 标量 metadata → 简单子元素；
- 嵌套 Map → 嵌套 XML 元素；
- List → 重复的 `<item>` 元素；
- **`<skill-id>` 总是被追加**，供 `load_skill_through_path` 使用。

这意味着每注册一个技能，就有一段元数据进入提示词。技能多的时候，全部暴露会占用大量上下文。AgentScope 提供了三个控制手段。

### 8.1 自定义 instruction 头部

用你自己的话告诉模型"技能列表在哪、怎么用"（构造函数第二参，null 或空白则用默认头部）：

```java
String customInstruction = """
    ## 可用技能
    当任务匹配某个技能时，使用 load_skill_through_path 加载它。
    """;

SkillBox skillBox = new SkillBox(toolkit, customInstruction);
```

自定义之后你可以：用更短的话减少 token；针对业务场景写更明确的触发指引；把"先判断是否需要技能，再加载"的流程写进 instruction，引导模型按需加载而不是一次性全看。

### 8.2 只暴露核心 metadata

默认暴露全部 metadata，关闭后提示词只保留 `name`、`description` 和 `skill-id`，减少提示词膨胀和不必要的元数据泄露：

```java
skillBox.setExposeAllSkillMetadata(false);
```

### 8.3 自定义代码执行说明

开启代码执行后，默认会注入一段 `execute_shell_command` 使用说明（`DEFAULT_CODE_EXECUTION_INSTRUCTION`），告诉模型：技能脚本位于 `{uploadDir}/<skill-id>/scripts/` 与 `{uploadDir}/<skill-id>/assets/`，工作流是"先 ls 探索目录 → 用绝对路径执行脚本 → 失败则诊断重试而非口头描述命令"。可以整体替换：

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

> `codeExecutionInstruction` 中所有 `%s` 占位符都会被替换为 `uploadDir` 的绝对路径（默认说明里每个目录示例各占一个 `%s`，自定义时注意占位符数量与用法一致）。

## 9. Tool 的渐进式披露

这是 Skill 系统最强大的特性——**将能力与 Skill 绑定，实现按需激活**：避免预先注册所有 Tool 导致的上下文污染，仅在 Skill 被 LLM 使用时才暴露相关能力。

> **渐进式暴露的 Tool 生命周期**：Tool 与 Skill 生命周期保持一致，Skill 激活后 Tool 在整个会话期间保持可用，避免了旧机制中每轮对话后 Tool 失活导致的调用失败问题。

### 9.1 为什么需要渐进式披露？

传统方式下，所有 Tool 都预先注册到 Toolkit 中：

```java
// 传统方式：所有工具一开始就暴露给 LLM
Toolkit toolkit = new Toolkit();
toolkit.registerTool(new DataLoadTool());      // 数据分析
toolkit.registerTool(new EmailSendTool());     // 邮件发送
toolkit.registerTool(new GitCommitTool());     // Git 操作
// ... 20 个工具全部注册
```

**问题**：上下文冗长（20 个工具的 Schema 占用大量 tokens）、决策困难（LLM 容易选错工具）、安全隐患（所有工具始终可用，无法按需管控）。

### 9.2 registration() DSL：四种能力都能绑

`skillBox.registration()` 返回的 `SkillRegistration` 支持绑定四种能力（每次注册只能选一种类型，多选会抛异常）：

| 方法 | 绑定对象 | 说明 |
|------|---------|------|
| `.tool(Object)` | 含 `@Tool` 注解方法的对象 | 扫描注解方法注册 |
| `.agentTool(AgentTool)` | `AgentTool` 接口实例 | 编程式工具 |
| `.mcpClient(McpClientWrapper)` | MCP 客户端 | **把整个 MCP Server 的工具绑到 Skill 上**，与上一篇 MCP 集成直接衔接 |
| `.subAgent(...)` | 子 Agent | 把子 Agent 封装为该 Skill 激活后可调用的工具 |

另支持 `.enableTools(...)` / `.disableTools(...)` 对绑定能力做黑白名单收敛（与 Toolkit 的 registration DSL 同款语义）。

以绑定 `AgentTool` 为例：

```java
Toolkit toolkit = new Toolkit();
SkillBox skillBox = new SkillBox(toolkit);

// 1. 创建 Skill
AgentSkill dataSkill = AgentSkill.builder()
        .name("data_analysis")
        .description("Comprehensive data analysis capabilities")
        .skillContent("# Data Analysis\n...")
        .build();

// 2. 创建 AgentTool 实例
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

// 3. 将 Tool 绑定到 Skill（注意：AgentTool 实例用 agentTool()，
//    @Tool 注解对象才用 tool()，用错会注册失败）
skillBox.registration()
        .skill(dataSkill)
        .agentTool(loadDataTool)
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
Agent 看到 <available_skills> 中 data_analysis 的元数据
    │
    ▼
Agent 调用 load_skill_through_path(skillId="data_analysis_custom", path="SKILL.md")
    │
    ▼
data_analysis Skill 激活 → load_data Tool 自动暴露给 LLM
    │
    ▼
Agent 调用 load_data Tool 加载数据 → 完成分析
```

## 10. 实战：构建数据分析 Agent

完整走一遍"创建技能 → 注册 → 开代码执行 → 持久化 → 运行"。本例让 Agent 通过 `execute_shell_command` 真正运行技能自带的 Python 脚本完成分析（而非引用不存在的工具）：

```java
public class SkillAgentDemo {
    public static void main(String[] args) {
        // 1. 创建 Skill：指令、参考文档、数据、脚本齐备
        //    注意：数据放 assets/、脚本放 scripts/，才能被默认过滤规则上传到执行环境
        AgentSkill dataSkill = AgentSkill.builder()
                .name("data_analysis")
                .description("""
                        Use this skill when analyzing data, calculating statistics, \
                        generating reports, or working with CSV files
                        """)
                .skillContent("""
                        # 数据分析技能

                        ## 功能概述
                        对 CSV 销售数据做描述性统计并给出趋势结论。

                        ## 使用方法
                        1. 用 execute_shell_command 运行 scripts/analyze.py，
                           数据文件为 assets/sample-sales.csv（均在技能目录下，用绝对路径）
                        2. 结合脚本输出总结增长趋势
                        3. 需要公式口径时，加载 references/statistics-guide.md

                        ## 可用资源
                        - references/statistics-guide.md: 统计方法指南
                        - assets/sample-sales.csv: 销售数据
                        - scripts/analyze.py: 统计分析脚本
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
                .addResource("assets/sample-sales.csv", """
                        month,sales,region
                        2024-01,150000,East
                        2024-02,180000,West
                        2024-03,165000,East
                        """)
                .addResource("scripts/analyze.py", """
                        import csv, statistics, sys
                        with open(sys.argv[1]) as f:
                            rows = list(csv.DictReader(f))
                        sales = [float(r["sales"]) for r in rows]
                        print("months :", [r["month"] for r in rows])
                        print("sales  :", sales)
                        print("mean   :", statistics.mean(sales))
                        print("stdev  :", round(statistics.stdev(sales), 2))
                        print("trend  :", " -> ".join(f"{r['month']}:{r['sales']}" for r in rows))
                        """)
                .build();
        // skillId = data_analysis_custom（source 缺省为 custom）

        // 2. 创建 Toolkit 和 SkillBox，注册 Skill
        Toolkit toolkit = new Toolkit();
        SkillBox skillBox = new SkillBox(toolkit);
        skillBox.registerSkill(dataSkill);

        // 3. 启用代码执行：白名单只放行 python3/ls/cat，其余命令走人工审批
        ShellCommandTool customShell = new ShellCommandTool(
                null,
                Set.of("python3", "ls", "cat"),
                command -> {
                    System.out.print("执行命令: " + command + " ? (y/n): ");
                    return new Scanner(System.in).nextLine().trim().equalsIgnoreCase("y");
                });
        skillBox.codeExecution()
                .withShell(customShell)
                .withRead()
                .workDir("/tmp/agent-workspace")
                .enable();

        // 4. 持久化到文件系统（可选；目录需已存在）
        try (FileSystemSkillRepository repo =
                     new FileSystemSkillRepository(Path.of("./skills"), true)) {
            repo.save(List.of(dataSkill), false);
        }

        // 5. 创建 Agent
        ReActAgent agent = ReActAgent.builder()
                .name("DataAnalyst")
                .sysPrompt("你是一位专业的数据分析师，擅长使用工具分析数据并生成洞察。")
                .model(DashScopeChatModel.builder()
                        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                        .modelName(MODEL_NAME)
                        // qwen3.8 系列必须显式 MULTIMODAL，否则 DashScope 报 url error
                        .endpointType(EndpointType.MULTIMODAL)
                        .build())
                .toolkit(toolkit)
                .skillBox(skillBox)
                .memory(new InMemoryMemory())
                .maxIters(15)
                .build();

        System.out.println("已注册技能ID: " + skillBox.getAllSkillIds());

        // 6. 调用
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

**预期执行流程**（可在控制台看到完整 tool_call 序列）：

```
用户：分析 2024 年前三月的销售数据，找出增长趋势
    │
    ▼
Agent 在 <available_skills> 中匹配到 data_analysis 的 description
    │
    ▼
tool_call: load_skill_through_path(skillId="data_analysis_custom", path="SKILL.md")
    │        → Skill 激活，资源上传至 {uploadDir}/data_analysis_custom/
    │        → 返回完整指令 + execute_shell_command 等工具暴露
    ▼
tool_call: execute_shell_command(command="ls /tmp/agent-workspace/skills/data_analysis_custom/scripts/")
    │
    ▼
tool_call: execute_shell_command(
             command="python3 /tmp/agent-workspace/skills/data_analysis_custom/scripts/analyze.py
                      /tmp/agent-workspace/skills/data_analysis_custom/assets/sample-sales.csv")
    │        → 输出 mean=165000.0、stdev=15000.0、trend=2024-01:150000 -> 2024-02:180000 -> 2024-03:165000
    ▼
（可选）tool_call: load_skill_through_path(skillId="data_analysis_custom",
             path="references/statistics-guide.md")
    │
    ▼
生成回答：2 月达峰值 18 万、3 月回落至 16.5 万，整体呈"升-降"波动，均值 16.5 万
```

---

## 11. 总结

| 要点 | 内容 |
|------|------|
| **核心概念** | Agent Skill 是包含指令、元数据和资源的模块化能力包 |
| **核心设计** | **渐进式披露**：元数据 → 完整指令 → 按需资源，三阶段加载 |
| **关键标识** | `skillId = name + "_" + source`；仓库接口按 name 读写，运行时按 skillId 操作 |
| **加载工具** | `load_skill_through_path(skillId, path)`；`path="SKILL.md"` 加载即激活；路径错误返回可用资源列表 |
| **创建方式** | Builder（推荐）、`SkillUtil.createFrom`（Markdown）、构造函数（4 参缺省 source="custom" / 5 参显式 source） |
| **集成方式** | `SkillBox` 注册到 ReActAgent，自动注册加载工具、Hook 与提示词 |
| **能力绑定** | `registration()` 支持 `tool()`（@Tool 对象）/ `agentTool()` / `mcpClient()` / `subAgent()` 四种，Skill 激活后才暴露 |
| **代码执行** | `skillBox.codeExecution()` 提供隔离的 Shell/读写环境；Shell 内置白名单、拼接拦截、审批回调、300s 超时 |
| **提示词治理** | 自定义 instruction 头部、`setExposeAllSkillMetadata(false)`、自定义 `codeExecutionInstruction` |
| **持久化** | 五种仓库：文件系统、MySQL、Git、Classpath、Nacos（后四种中 Git/MySQL/Nacos 为扩展包） |

Agent Skill 让 Agent 的能力管理从"堆工具"进化为"装技能包"——按需加载、按需激活、按需执行。这是构建真正"博学而专注"的企业级 Agent 的基石。
