## `datavines-engine-api` 接口详解

`datavines-engine-api` 是整个引擎层的 **契约层**，定义了一套"引擎无关"的 SPI 扩展点。共有 5 个核心接口/类，层次关系如下：

```
Plugin（基础配置契约）
  └── Component（可被环境准备的组件：Source/Transform/Sink）
  └── RuntimeEnvironment（运行时环境）
        └── Execution（执行模型，驱动 Source→Transform→Sink 流水线）

EngineExecutor（执行器，面向调度层的顶层入口）
EngineConstants（键名常量）
```

---

### 1. `Plugin` — 插件基础契约

**文件**：Plugin
```java
public interface Plugin extends Serializable {
    void setConfig(Config config);   // 注入配置
    Config getConfig();              // 读取配置
    CheckResult checkConfig();       // 校验配置合法性
}
```

**作用**：所有引擎插件的 **最底层契约**，规定了每个插件必须支持"配置注入 + 配置校验"。`Config` 是一个 `Map<String, Object>` 的包装，框架在加载插件后立即调用 `setConfig` 把配置推入插件。

---

### 2. `Component` — 可执行组件（Source / Transform / Sink）

**文件**：Component

```java
@SPI
public interface Component extends Plugin {
    void prepare(RuntimeEnvironment env) throws Exception;
}
```

**作用**：Source（数据读取）、Transform（数据转换）、Sink（数据写出）三类组件的 **统一抽象**。`prepare(env)` 在执行前被调用，让组件从运行时环境（Spark/Flink Context 等）中拿到所需资源，例如 SparkSession。

**插件名称约定**：框架在加载时按 `{engine}-{type}-{plugin}-source/transform/sink` 的格式拼 SPI key，例如 `spark-batch-jdbc-source`，由 [ConfigParser.java](file:///Users/smartsi/学习/Code/source/datavines/datavines-engine/datavines-engine-core/src/main/java/io/datavines/engine/core/config/ConfigParser.java) 负责解析和加载。

---

### 3. `RuntimeEnvironment` — 运行时环境

**文件**：[RuntimeEnvironment.java](file:///Users/smartsi/学习/Code/source/datavines/datavines-engine/datavines-engine-api/src/main/java/io/datavines/engine/api/env/RuntimeEnvironment.java)

```java
@SPI
public interface RuntimeEnvironment extends Plugin {
    void prepare();             // 初始化运行时（如创建 SparkSession）
    Execution getExecution();   // 返回与此环境配套的 Execution 实例
}
```

**作用**：封装引擎底层运行环境的差异。Spark 引擎的实现会在 `prepare()` 里创建 `SparkSession`，Local 引擎的实现直接在 JVM 内运行。`getExecution()` 返回与当前环境绑定的执行器。

---

### 4. `Execution` — 执行模型

**文件**：[Execution.java](file:///Users/smartsi/学习/Code/source/datavines/datavines-engine/datavines-engine-api/src/main/java/io/datavines/engine/api/env/Execution.java)

```java
public interface Execution<SR extends Component, TF extends Component, SK extends Component> {
    void prepare() throws Exception;                                    // 执行前准备
    void execute(List<SR> sources, List<TF> transforms, List<SK> sinks) // 驱动完整流水线
        throws Exception;
    void stop() throws Exception;                                       // 停止执行
}
```

**作用**：驱动 `Source → Transform → Sink` 完整流水线的核心接口。泛型参数让不同引擎可以指定具体的组件类型（例如 Spark 引擎会用 `SparkSource extends Component`）。`execute()` 是数据流真正流动的地方：从 sources 读取 → 经 transforms 处理 → 写入 sinks。

---

### 5. `EngineExecutor` — 执行器（面向调度层的顶层入口）

**文件**：[EngineExecutor.java](file:///Users/smartsi/学习/Code/source/datavines/datavines-engine/datavines-engine-api/src/main/java/io/datavines/engine/api/engine/EngineExecutor.java)

```java
@SPI
public interface EngineExecutor {
    void init(JobExecutionRequest request, Logger logger, Configurations conf) throws Exception;
    void execute() throws Exception;
    void after() throws Exception;
    void cancel() throws Exception;
    boolean isCancel() throws Exception;
    ProcessResult getProcessResult();
    JobExecutionRequest getTaskRequest();
}
```

这是**调度层与引擎层之间唯一的边界接口**，每个方法的职责：

| 方法 | 职责 | 典型实现 |
|------|------|----------|
| `init()` | 初始化执行上下文，解析 `applicationParameter`，准备底层进程/Client | 设置线程名，构造 `ShellCommandProcess` 或 `LivyCommandProcess` |
| `execute()` | 同步阻塞执行，等待完成 | Spark：`shellCommandProcess.run(command)`；Local：`bootstrap.execute(args)` |
| `after()` | 执行后清理工作（释放连接、删除临时文件等） | 通常为空或写日志 |
| `cancel()` | 外部中断，停止正在执行的作业 | Yarn：`yarn application -kill appId`；Local：`bootstrap.stop()` |
| `isCancel()` | 查询取消状态（轮询用） | 返回 `volatile boolean cancel` |
| `getProcessResult()` | 返回执行结果（退出码、行数、错误信息） | 返回内部 `ProcessResult` 实例 |
| `getTaskRequest()` | 返回本次执行的请求上下文 | 返回 `this.jobExecutionRequest` |

---

### 6. `EngineConstants` — 键名常量

**文件**：[EngineConstants.java](file:///Users/smartsi/学习/Code/source/datavines/datavines-engine/datavines-engine-api/src/main/java/io/datavines/engine/api/EngineConstants.java)

```java
OUTPUT_TABLE = "output_table"   // Source 输出的临时表名（传递给 Transform）
INPUT_TABLE  = "input_table"    // Transform/Sink 读取的临时表名
TMP_TABLE    = "tmp_table"      // 中间临时表
PID          = "pid"            // 进程 ID
PLUGIN_TYPE  = "plugin_type"    // 组件类型标识（source/transform/sink）
TYPE         = "type"           // 数据批/流类型标识
```

这些常量在 Config 传递链路中作为约定键名使用，避免各插件硬编码字符串。

---

## 画像平台如何对接

由于 **`profile-engine` 是独立模块，不直接实现 Datavines 的 `EngineExecutor`**，而是定义了自己的 `ProfileEngineExecutor`，对接关系如下：

```
Datavines 调度层
  └── EngineExecutor（Datavines 的 SPI）
      └── 实现类：Spark/Local/Flink Executor
          └── 内部调用 applicationParameter 中的配置驱动 Execution

画像平台
  └── ProfileJobCoordinator（调度入口）
      └── ProfileJobRunner（生命周期管理）
          └── ProfileEngineExecutor（画像平台自己的 SPI）
              ├── ClickHouseEngineExecutor（人群圈选/分析）
              ├── DataXEngineExecutor（数据集同步/群组导出）
              └── SeaTunnelEngineExecutor（数据集同步/群组导出）
```

画像平台**不需要实现** Datavines 的 `EngineExecutor`，`profile-engine` 已经是独立的引擎层。画像平台服务只需要调用 [`ProfileJobCoordinator.submitAsync()`](file:///Users/smartsi/学习/Code/source/datavines/profile-engine/profile-engine-core/src/main/java/io/datavines/profile/engine/core/coordinator/ProfileJobCoordinator.java) 提交执行请求即可，具体引擎的选择和执行细节由 `profile-engine` 内部路由处理。
