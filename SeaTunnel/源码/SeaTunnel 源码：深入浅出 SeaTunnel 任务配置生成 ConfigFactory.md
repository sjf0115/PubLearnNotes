## 1. 背景介绍

SeaTunnel 作业的运行依赖于 HOCON 格式的配置文件。在实际应用中，我们往往需要动态生成这些配置，而非手动编写。SeaTunnel Web 通过 **Typesafe Config** 库的 `ConfigFactory` 实现了从数据库存储的任务定义到最终配置文件的动态生成。

本文将深入源码，揭示 `ConfigFactory` 如何帮助 SeaTunnel Web 将可视化编排的作业转换为 SeaTunnel Engine 可执行的配置文件。

---

## 2. 整体架构

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    SeaTunnel Web 配置生成架构                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│   ┌─────────────────┐                                                        │
│   │   Web UI        │  用户可视化编排作业                                      │
│   │   (DAG 编辑器)   │                                                        │
│   └────────┬────────┘                                                        │
│            │                                                                  │
│            ▼                                                                  │
│   ┌─────────────────┐      ┌─────────────────┐                              │
│   │  JobDefinition  │      │   JobVersion    │                              │
│   │  (作业定义)      │─────►│   (版本信息)     │                              │
│   └─────────────────┘      └────────┬────────┘                              │
│                                     │                                         │
│            ┌────────────────────────┼────────────────────────┐              │
│            ▼                        ▼                        ▼              │
│   ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐   │
│   │   JobTask       │      │    JobLine      │      │    EnvConfig    │   │
│   │  (插件配置)      │      │   (DAG 连线)    │      │   (环境配置)    │   │
│   └────────┬────────┘      └────────┬────────┘      └────────┬────────┘   │
│            │                        │                        │              │
│            └────────────────────────┼────────────────────────┘              │
│                                     ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │              JobInstanceServiceImpl.generateJobConfig()              │  │
│   │                                                                       │  │
│   │   1. ConfigFactory.parseString(envStr)  → 解析 env                   │  │
│   │   2. parseConfigWithOptionRule()        → 解析插件配置               │  │
│   │   3. mergeTaskConfig()                  → 合并数据源配置             │  │
│   │   4. getConnectorConfig()               → 渲染 HOCON 字符串         │  │
│   │   5. SeaTunnelConfigUtil.generateConfig() → 拼接完整配置            │  │
│   │   6. replaceJobConfigPlaceholders()     → 替换占位符               │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                     │                                         │
│                                     ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                         最终配置文件 (.conf)                          │  │
│   │                                                                       │  │
│   │   env { job.mode = "BATCH" ... }                                     │  │
│   │   source { Jdbc { ... } }                                            │  │
│   │   transform { Sql { ... } }                                          │  │
│   │   sink { Jdbc { ... } }                                              │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                     │                                         │
│                                     ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │              SeaTunnelClient.createExecutionContext()                │  │
│   │                         提交到 SeaTunnel 集群                         │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 核心组件：Typesafe Config

### 3.1 ConfigFactory 简介

`ConfigFactory` 是 [Typesafe Config](https://github.com/lightbend/config) 库的核心类，提供了强大的配置解析和生成能力：

```java
import org.apache.seatunnel.shade.com.typesafe.config.Config;
import org.apache.seatunnel.shade.com.typesafe.config.ConfigFactory;
import org.apache.seatunnel.shade.com.typesafe.config.ConfigRenderOptions;
import org.apache.seatunnel.shade.com.typesafe.config.ConfigValueFactory;
```

### 3.2 常用 API

| 方法 | 用途 |
|------|------|
| `ConfigFactory.parseString(str)` | 从字符串解析配置 |
| `ConfigFactory.parseMap(map)` | 从 Map 解析配置 |
| `ConfigFactory.empty()` | 创建空配置 |
| `config.withValue(key, value)` | 添加配置项 |
| `config.withoutPath(key)` | 删除配置项 |
| `config.root().render(options)` | 渲染为 HOCON 字符串 |

---

## 4. 配置生成核心流程

### 4.1 入口方法

`JobInstanceServiceImpl.generateJobConfig()` 是配置生成的核心入口：
```java
@Override
public String generateJobConfig(
    Long jobId,
    List<JobTask> tasks,      // 所有插件任务
    List<JobLine> lines,      // DAG 连线关系
    String envStr,            // 环境配置 JSON
    JobExecParam executeParam // 运行时参数
) {
    // 1. 解析 env 配置
    Config envConfig = filterEmptyValue(ConfigFactory.parseString(envStr));

    // 2. 初始化三个配置容器
    Map<String, List<Config>> sourceMap = new LinkedHashMap<>();
    Map<String, List<Config>> transformMap = new LinkedHashMap<>();
    Map<String, List<Config>> sinkMap = new LinkedHashMap<>();

    // 3. 遍历任务生成配置...
    // 4. 渲染最终配置...
}
```

### 4.2 Step 1：解析环境配置

```java
// 解析 JSON 格式的 env 配置
Config envConfig = filterEmptyValue(ConfigFactory.parseString(envStr));

// filterEmptyValue 过滤空值
private Config filterEmptyValue(Config config) {
    List<String> removeKeys = config.entrySet().stream()
        .filter(entry -> isEmptyValue(entry.getValue()))
        .map(Map.Entry::getKey)
        .collect(Collectors.toList());

    for (String removeKey : removeKeys) {
        config = config.withoutPath(removeKey);
    }
    return config;
}
```

**示例转换**：

输入 envStr (JSON)：
```json
{
  "job.mode": "BATCH",
  "job.name": "mysql_to_mysql",
  "checkpoint.interval": "",
  "parallelism": 2
}
```
输出 envConfig (过滤空值后)：
```hocon
{
  "job.mode": "BATCH",
  "job.name": "mysql_to_mysql",
  "parallelism": 2
}
```

### 4.3 Step 2：遍历任务生成插件配置

```java
for (JobTask task : tasks) {
    PluginType pluginType = PluginType.valueOf(task.getType().toUpperCase());

    // 解析插件配置
    Config config = filterEmptyValue(parseConfigWithOptionRule(
        pluginType,
        task.getConnectorType(),
        task.getConfig(),
        optionRule
    ));

    switch (pluginType) {
        case SOURCE:
            // 添加 plugin_output 表名
            config = addTableName(
                ConnectorCommonOptions.PLUGIN_OUTPUT.key(),
                inputLines.get(pluginId),
                config
            );
            // 合并数据源配置
            Config mergeConfig = mergeTaskConfig(task, pluginType, ...);
            sourceMap.get(task.getConnectorType()).add(mergeConfig);
            break;

        case TRANSFORM:
            // 添加 plugin_input / plugin_output
            config = addTableName(PLUGIN_INPUT.key(), ...);
            config = addTableName(PLUGIN_OUTPUT.key(), ...);
            transformMap.get(task.getConnectorType()).add(config);
            break;

        case SINK:
            // 添加 plugin_input 表名
            config = addTableName(PLUGIN_INPUT.key(), ...);
            sinkMap.get(task.getConnectorType()).add(mergeConfig);
            break;
    }
}
```

### 4.4 Step 3：解析复杂类型配置

[parseConfigWithOptionRule()](file:///Users/smartsi/学习/Code/source/seatunnel-web/seatunnel-server/seatunnel-app/src/main/java/org/apache/seatunnel/app/service/impl/JobInstanceServiceImpl.java#L571-L638) 处理 List/Map 等复杂类型：

```java
private Config parseConfigWithOptionRule(
    PluginType pluginType,
    String connectorType,
    Config config,
    OptionRule optionRule
) {
    // 从 OptionRule 获取字段类型信息
    Map<String, TypeReference<?>> typeReferenceMap = new HashMap<>();
    optionRule.getOptionalOptions()
        .forEach(option -> typeReferenceMap.put(option.key(), option.typeReference()));
    optionRule.getRequiredOptions()
        .forEach(options -> options.getOptions()
            .forEach(option -> typeReferenceMap.put(option.key(), option.typeReference())));

    // 处理复杂类型
    config.entrySet().forEach(entry -> {
        String key = entry.getKey();
        ConfigValue configValue = entry.getValue();

        if (typeReferenceMap.containsKey(key) && isComplexType(typeReferenceMap.get(key))) {
            String valueStr = configValue.unwrapped().toString();

            // List 类型：将字符串解析为 List
            if (typeReferenceMap.get(key).getType().getTypeName().startsWith("java.util.List")) {
                String valueWrapper = "{key=" + valueStr + "}";
                ConfigValue configList = ConfigFactory.parseString(valueWrapper).getList("key");
                needReplaceList.put(key, configList);
            }
            // Map 类型：将字符串解析为对象
            else {
                Config configObject = ConfigFactory.parseString(valueStr);
                needReplaceMap.put(key, configObject.root());
            }
        }
    });

    // 替换配置值
    for (Map.Entry<String, ConfigObject> entry : needReplaceMap.entrySet()) {
        config = config.withValue(entry.getKey(), entry.getValue());
    }
    return config;
}
```

### 4.5 Step 4：合并数据源配置

[mergeTaskConfig()](file:///Users/smartsi/学习/Code/source/seatunnel-web/seatunnel-server/seatunnel-app/src/main/java/org/apache/seatunnel/app/service/impl/JobInstanceServiceImpl.java#L398-L449) 将数据源实例配置与任务配置合并：

```java
private Config mergeTaskConfig(
    JobTask task,
    PluginType pluginType,
    String connectorType,
    BusinessMode businessMode,
    Config connectorConfig,
    OptionRule optionRule
) {
    // 1. 获取数据源实例配置
    Long datasourceInstanceId = task.getDataSourceId();
    DatasourceDetailRes datasourceDetailRes =
        datasourceService.queryDatasourceDetailById(datasourceInstanceId.toString());

    // 2. 解析数据源配置
    Config datasourceConf = parseConfigWithOptionRule(
        pluginType, connectorType,
        datasourceDetailRes.getDatasourceConfig(),
        optionRule
    );

    // 3. 获取表选项和字段选择
    DataSourceOption dataSourceOption = JsonUtils.parseObject(
        task.getDataSourceOption(), DataSourceOption.class);
    SelectTableFields selectTableFields = JsonUtils.parseObject(
        task.getSelectTableFields(), SelectTableFields.class);

    // 4. 合并配置
    return DataSourceConfigSwitcherUtils.mergeDatasourceConfig(
        pluginName,
        datasourceConf,        // 数据源连接配置
        virtualTableDetailRes, // 虚拟表配置
        dataSourceOption,      // 表选项
        selectTableFields,     // 字段选择
        businessMode,
        pluginType,
        connectorConfig        // 插件特有配置
    );
}
```

### 4.6 Step 5：渲染 HOCON 字符串

[getConnectorConfig()](file:///Users/smartsi/学习/Code/source/seatunnel-web/seatunnel-server/seatunnel-app/src/main/java/org/apache/seatunnel/app/service/impl/JobInstanceServiceImpl.java#L458-L475) 将 Config 对象渲染为 HOCON 格式：

```java
private String getConnectorConfig(Map<String, List<Config>> connectorMap) {
    List<String> configs = new ArrayList<>();

    // 渲染选项：非 JSON 格式，无注释
    ConfigRenderOptions configRenderOptions = ConfigRenderOptions.defaults()
        .setJson(false)           // HOCON 格式
        .setComments(false)       // 不包含注释
        .setOriginComments(false);

    for (Map.Entry<String, List<Config>> entry : connectorMap.entrySet()) {
        for (Config c : entry.getValue()) {
            // 将配置包装为 "Jdbc { ... }" 格式
            configs.add(
                ConfigFactory.empty()
                    .withValue(entry.getKey(), c.root())  // Jdbc -> config
                    .root()
                    .render(configRenderOptions)
            );
        }
    }
    return StringUtils.join(configs, "\n");
}
```

**渲染示例**：

```java
// 输入：Config 对象
{
    url: "jdbc:mysql://localhost:3306/test"
    driver: "com.mysql.cj.jdbc.Driver"
    username: "root"
    password: "root"
    database: "test"
    table: "user_source"
    plugin_output: "Table123456"
}

// 输出：HOCON 字符串
Jdbc {
    url = "jdbc:mysql://localhost:3306/test"
    driver = "com.mysql.cj.jdbc.Driver"
    username = "root"
    password = "root"
    database = "test"
    table = "user_source"
    plugin_output = "Table123456"
}
```

### 4.7 Step 6：拼接完整配置

[SeaTunnelConfigUtil.generateConfig()](file:///Users/smartsi/学习/Code/source/seatunnel-web/seatunnel-server/seatunnel-app/src/main/java/org/apache/seatunnel/app/utils/SeaTunnelConfigUtil.java) 拼接最终配置：

```java
public class SeaTunnelConfigUtil {

    private static final String CONFIG_TEMPLATE =
        "env {\n"
        + "env_placeholder"
        + "}\n"
        + "source {\n"
        + "source_placeholder"
        + "}\n"
        + "transform {\n"
        + "transform_placeholder"
        + "}\n"
        + "sink {\n"
        + "sink_placeholder"
        + "}\n";

    public static String generateConfig(
        String env, String sources, String transforms, String sinks
    ) {
        return CONFIG_TEMPLATE
            .replace("env_placeholder", env)
            .replace("source_placeholder", sources)
            .replace("transform_placeholder", transforms)
            .replace("sink_placeholder", sinks);
    }
}
```

### 4.8 Step 7：替换占位符

[JobUtils.replaceJobConfigPlaceholders()](file:///Users/smartsi/学习/Code/source/seatunnel-web/seatunnel-server/seatunnel-app/src/main/java/org/apache/seatunnel/app/utils/JobUtils.java#L73-L103) 支持运行时参数替换：

```java
// 占位符格式：${placeholder_name:default_value}
private static final Pattern placeholderPattern =
    Pattern.compile("(\\\\{0,2})\\$\\{(\\w+)(?::(.*?))?\\}");

public static String replaceJobConfigPlaceholders(
    String jobConfigString,
    JobExecParam jobExecParam
) {
    Map<String, String> placeholderValues =
        jobExecParam.getPlaceholderValues();

    Matcher matcher = placeholderPattern.matcher(jobConfigString);
    StringBuffer result = new StringBuffer();

    while (matcher.find()) {
        String placeholderName = matcher.group(2);  // 占位符名称
        String defaultValue = matcher.group(3);     // 默认值

        // 从参数中获取值，否则使用默认值
        String replacement = placeholderValues
            .getOrDefault(placeholderName, defaultValue);

        matcher.appendReplacement(result, replacement);
    }

    matcher.appendTail(result);
    return result.toString();
}
```

**使用示例**：

```hocon
# 原始配置
source {
  Jdbc {
    url = "jdbc:mysql://${db_host:localhost}:3306/test"
    password = "${db_password}"
  }
}

# 运行时参数
placeholderValues: {
  "db_host": "192.168.1.100",
  "db_password": "secret123"
}

# 替换后
source {
  Jdbc {
    url = "jdbc:mysql://192.168.1.100:3306/test"
    password = "secret123"
  }
}
```

---

## 五、提交作业到集群

### 5.1 作业执行流程

[JobExecutorServiceImpl.jobExecute()](file:///Users/smartsi/学习/Code/source/seatunnel-web/seatunnel-server/seatunnel-app/src/main/java/org/apache/seatunnel/app/service/impl/JobExecutorServiceImpl.java#L72-L92) 负责提交作业：

```java
@Override
public Result<Long> jobExecute(Long jobDefineId, JobExecParam executeParam) {
    // 1. 生成作业配置
    JobExecutorRes executeResource =
        jobInstanceService.createExecuteResource(jobDefineId, executeParam);
    String jobConfig = executeResource.getJobConfig();

    // 2. 写入配置文件
    String configFile = writeJobConfigIntoConfFile(jobConfig, jobDefineId);

    // 3. 提交到 SeaTunnel 集群
    executeJobBySeaTunnel(configFile, executeResource.getJobInstanceId());

    return Result.success(executeResource.getJobInstanceId());
}
```

### 5.2 SeaTunnel 客户端提交

```java
private void executeJobBySeaTunnel(String filePath, Long jobInstanceId) {
    // 设置部署模式
    Common.setDeployMode(DeployMode.CLIENT);

    // 创建作业配置
    JobConfig jobConfig = new JobConfig();
    jobConfig.setName(jobInstanceId + "_job");

    // 创建 SeaTunnel 客户端
    SeaTunnelClient seaTunnelClient = createSeaTunnelClient();
    SeaTunnelConfig seaTunnelConfig = new YamlSeaTunnelConfigBuilder().build();

    // 创建执行上下文
    ClientJobExecutionEnvironment jobExecutionEnv =
        seaTunnelClient.createExecutionContext(filePath, jobConfig, seaTunnelConfig);

    // 提交执行
    ClientJobProxy clientJobProxy = jobExecutionEnv.execute();

    // 异步等待完成
    CompletableFuture.runAsync(() -> {
        waitJobFinish(clientJobProxy, jobInstanceId, ...);
    }, taskExecutor);
}
```

---

## 六、完整配置生成示例

### 6.1 数据库存储的任务定义

```
t_st_job_task 表:
┌──────────────────────────────────────────────────────────────────────┐
│ id=1, plugin_id="source_001", type="SOURCE", connector_type="Jdbc"  │
│ data_source_id=100, config='{"query":"SELECT * FROM users"}'        │
├──────────────────────────────────────────────────────────────────────┤
│ id=2, plugin_id="sink_001", type="SINK", connector_type="Jdbc"      │
│ data_source_id=200, config='{"table":"users_backup"}'               │
└──────────────────────────────────────────────────────────────────────┘

t_st_job_line 表:
┌──────────────────────────────────────────────────────────────────────┐
│ input_plugin_id="source_001", target_plugin_id="sink_001"           │
└──────────────────────────────────────────────────────────────────────┘

t_st_datasource 表:
┌──────────────────────────────────────────────────────────────────────┐
│ id=100, plugin_name="MySQL",                                        │
│ config='{"url":"jdbc:mysql://localhost:3306/src","username":"root"}'│
├──────────────────────────────────────────────────────────────────────┤
│ id=200, plugin_name="MySQL",                                        │
│ config='{"url":"jdbc:mysql://localhost:3306/dst","username":"root"}'│
└──────────────────────────────────────────────────────────────────────┘
```

### 6.2 生成的最终配置

```hocon
env {
    job.mode = "BATCH"
    job.name = "mysql_to_mysql_job"
    parallelism = 2
}

source {
    Jdbc {
        url = "jdbc:mysql://localhost:3306/src"
        driver = "com.mysql.cj.jdbc.Driver"
        username = "root"
        password = "******"
        database = "source_db"
        table = "users"
        query = "SELECT * FROM users"
        plugin_output = "Table_source_001"
    }
}

transform {
    # 无转换
}

sink {
    Jdbc {
        url = "jdbc:mysql://localhost:3306/dst"
        driver = "com.mysql.cj.jdbc.Driver"
        username = "root"
        password = "******"
        database = "target_db"
        table = "users_backup"
        plugin_input = "Table_source_001"
        batch_size = 1000
    }
}
```

---

## 七、核心设计模式

### 7.1 策略模式 — 数据源配置切换

不同数据源有不同的配置合并逻辑：

```
DataSourceConfigSwitcher (接口)
    │
    ├── MysqlDatasourceConfigSwitcher
    ├── PostgresqlDataSourceConfigSwitcher
    ├── OracleDataSourceConfigSwitcher
    ├── KafkaDataSourceConfigSwitcher
    └── ...
```

```java
// 根据数据源类型获取对应的配置切换器
DataSourceConfigSwitcher switcher =
    DatasourceConfigSwitcherProvider.INSTANCE.getConfigSwitcher("MYSQL");

// 合并配置
Config mergedConfig = switcher.mergeDatasourceConfig(
    dataSourceInstanceConfig,
    virtualTableDetail,
    dataSourceOption,
    selectTableFields,
    businessMode,
    pluginType,
    connectorConfig
);
```

### 7.2 建造者模式 — Config 链式构建

```java
Config config = ConfigFactory.empty()
    .withValue("url", ConfigValueFactory.fromAnyRef("jdbc:mysql://..."))
    .withValue("driver", ConfigValueFactory.fromAnyRef("com.mysql.cj.jdbc.Driver"))
    .withValue("username", ConfigValueFactory.fromAnyRef("root"))
    .withValue("password", ConfigValueFactory.fromAnyRef("secret"));
```

### 7.3 模板方法模式 — 配置生成骨架

```java
// 模板结构
String CONFIG_TEMPLATE =
    "env { env_placeholder }\n" +
    "source { source_placeholder }\n" +
    "transform { transform_placeholder }\n" +
    "sink { sink_placeholder }\n";

// 填充各部分
String jobConfig = CONFIG_TEMPLATE
    .replace("env_placeholder", env)
    .replace("source_placeholder", sources)
    .replace("transform_placeholder", transforms)
    .replace("sink_placeholder", sinks);
```

---

## 八、最佳实践

### 8.1 配置隔离

| 配置层级 | 来源 | 说明 |
|----------|------|------|
| 数据源配置 | `t_st_datasource` | 连接信息，可复用 |
| 任务配置 | `t_st_job_task.config` | 任务特有配置 |
| 表选项 | `data_source_option` | 表名、字段选择 |
| 运行时参数 | `JobExecParam` | 占位符替换值 |

### 8.2 敏感信息处理

```java
// 加密敏感配置
configShadeUtil.encryptData(config);

// 最终配置中密码会被加密
password = "encrypted:AES:xxxxxx"
```

### 8.3 空值过滤

```java
// 避免生成空配置项
config = filterEmptyValue(config);

// 过滤前
{ url = "", username = "root" }

// 过滤后
{ username = "root" }
```

---

## 九、总结

SeaTunnel Web 通过 `ConfigFactory` 实现了一套完整的配置生成体系：

1. **解析层**：`ConfigFactory.parseString/parseMap` 将各种格式转换为统一的 Config 对象
2. **处理层**：`withValue/withoutPath` 实现 Config 的增删改操作
3. **合并层**：`DataSourceConfigSwitcher` 实现不同数据源的配置合并策略
4. **渲染层**：`ConfigRenderOptions` 将 Config 渲染为 HOCON 字符串
5. **增强层**：占位符替换、敏感信息加密等后处理

这种设计使得 SeaTunnel Web 能够将用户可视化编排的作业无缝转换为 SeaTunnel Engine 可执行的配置文件，实现了"所见即所得"的数据集成体验。
