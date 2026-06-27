
在企业系统集成场景中，开发者往往希望以简洁、面向对象的方式与 DolphinScheduler 交互，而非直接处理底层的 HTTP 请求组装和 JSON 解析。社区开源的 [dolphinscheduler-sdk-java](https://github.com/weaksloth/dolphinscheduler-sdk-java) 正是为此而生——它封装了 DolphinScheduler 的 REST API，提供了类型安全的 Java SDK，让开发者可以像操作本地对象一样管理工作流、任务和实例。

本文将从 SDK 设计原理到实战代码，系统讲解如何在 Spring Boot 项目中基于 Java SDK 集成 DolphinScheduler，并深入剖析其核心 API 的使用技巧和边界场景。

本文基于 DolphinScheduler 3.1.9 版本，SDK 版本 3.1.4-RELEASE。

## 1. SDK 设计原理与架构

### 1.1 为什么需要 SDK

直接调用 REST API 虽然灵活，但在实际开发中存在诸多痛点：

| 痛点 | 说明 |
|---|---|
| 参数组装繁琐 | 工作流定义涉及任务定义 JSON、任务关系 JSON、全局参数等多个字段 |
| 类型不安全 | 所有参数都是字符串或 Map，编译期无法检查 |
| 重复代码多 | 每个项目都要封装一套 HTTP 客户端和响应解析 |
| 版本适配困难 | API 升级后参数变化，需要全局搜索替换 |

SDK 通过以下方式解决这些问题：
- **实体类封装**：`ShellTask`、`HttpTask`、`ProcessDefineParam` 等强类型对象
- **工具类辅助**：`TaskDefinitionUtils`、`TaskRelationUtils` 简化 DAG 构建
- **链式 API**：`dolphinClient.opsForProcess().create(...)` 语义清晰
- **版本隔离**：不同 DolphinScheduler 版本对应不同 SDK 分支

### 1.2 SDK 架构

```
DolphinClient (入口)
    ├── opsForProject()       → ProjectOperations
    ├── opsForProcess()       → ProcessOperations
    ├── opsForProcessInstance() → ProcessInstanceOperations
    ├── opsForSchedule()      → ScheduleOperations
    ├── opsForDataSource()    → DataSourceOperations
    ├── opsForResource()      → ResourceOperations
    ├── opsForTaskInstance()  → TaskInstanceOperations
    └── opsForTenant()        → TenantOperations
```

每个 Operations 类封装了对应模块的 API，返回强类型响应对象。

## 2. 前置准备

### 2.1 部署与 Token

与 REST API 方式相同，需要：
1. 部署 DolphinScheduler（Standalone 或集群）
2. 在 Web UI **用户中心 → Token 管理** 创建 API Token

### 2.2 SDK 版本选择

| DolphinScheduler 版本 | SDK 分支/版本 | Maven 坐标 |
|---|---|---|
| 2.0.5 | 2.0.5-release | `com.github.weaksloth:dolphinscheduler-sdk-java:2.0.5-RELEASE` |
| 3.1.4 | 3.1.4-release | `com.github.weaksloth:dolphinscheduler-sdk-java:3.1.4-RELEASE` |
| 3.1.9 | 3.1.4-release | `com.github.weaksloth:dolphinscheduler-sdk-java:3.1.4-RELEASE` |

> 选择 SDK 版本时必须与 DolphinScheduler 服务端版本严格匹配，否则可能出现字段不兼容问题。

## 3. Spring Boot 项目集成

### 3.1 Maven 依赖

```xml
<dependencies>
    <!-- Spring Boot Web -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>

    <!-- DolphinScheduler Java SDK -->
    <dependency>
        <groupId>com.github.weaksloth</groupId>
        <artifactId>dolphinscheduler-sdk-java</artifactId>
        <version>3.1.4-RELEASE</version>
    </dependency>

    <!-- Apache HttpClient（SDK 底层依赖） -->
    <dependency>
        <groupId>org.apache.httpcomponents</groupId>
        <artifactId>httpclient</artifactId>
        <version>4.5.14</version>
    </dependency>

    <!-- Lombok -->
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <optional>true</optional>
    </dependency>
</dependencies>
```

### 3.2 配置文件

```yaml
# application.yml
dolphinscheduler:
  api:
    base-url: http://localhost:12345/dolphinscheduler
    token: ${DS_TOKEN:default-token}
    # 连接超时（毫秒）
    connect-timeout: 5000
    # 读取超时（毫秒）
    read-timeout: 30000
```

### 3.3 配置类：初始化 DolphinClient

```java
@Data
@Configuration
@ConfigurationProperties(prefix = "dolphinscheduler.api")
public class DolphinSchedulerProperties {
    private String baseUrl;
    private String token;
    private int connectTimeout = 5000;
    private int readTimeout = 30000;
}

@Configuration
@Slf4j
public class DolphinSdkConfig {

    @Autowired
    private DolphinSchedulerProperties properties;

    @Bean
    public DolphinClient dolphinClient() {
        // 构建底层 HTTP Client
        RequestConfig requestConfig = RequestConfig.custom()
            .setConnectTimeout(properties.getConnectTimeout())
            .setSocketTimeout(properties.getReadTimeout())
            .build();

        CloseableHttpClient httpClient = HttpClients.custom()
            .addInterceptorLast(new RequestContent(true))
            .setDefaultRequestConfig(requestConfig)
            .build();

        // 包装为 SDK 使用的 RestTemplate
        DolphinsRestTemplate restTemplate = new DolphinsRestTemplate(
            new DefaultHttpClientRequest(httpClient, requestConfig));

        // 创建 DolphinClient
        DolphinClient client = new DolphinClient(
            properties.getToken(),
            properties.getBaseUrl(),
            restTemplate);

        log.info("DolphinScheduler SDK Client 初始化完成, baseUrl: {}",
            properties.getBaseUrl());
        return client;
    }
}
```

### 3.4 注入使用

```java
@Service
public class MyService {

    @Autowired
    private DolphinClient dolphinClient;

    public void doSomething() {
        // 直接使用 dolphinClient 操作 DolphinScheduler
        dolphinClient.opsForProject().list(1, 10);
    }
}
```

## 4. 核心操作详解

### 4.1 项目管理

```java
@Service
@Slf4j
public class ProjectSdkService {

    @Autowired
    private DolphinClient dolphinClient;

    /**
     * 创建项目
     */
    public ProjectCreateResp createProject(String name, String description) {
        ProjectCreateParam param = new ProjectCreateParam();
        param.setProjectName(name);
        param.setDescription(description);

        ProjectCreateResp resp = dolphinClient.opsForProject().create(param);
        log.info("创建项目成功: {}, code: {}", resp.getName(), resp.getCode());
        return resp;
    }

    /**
     * 查询项目列表
     */
    public List<ProjectResp> listProjects(int pageNo, int pageSize) {
        ProjectListParam param = new ProjectListParam();
        param.setPageNo(pageNo);
        param.setPageSize(pageSize);

        ProjectListResp resp = dolphinClient.opsForProject().list(param);
        return resp.getTotalList();
    }

    /**
     * 删除项目
     */
    public void deleteProject(Long projectCode) {
        dolphinClient.opsForProject().delete(projectCode);
        log.info("删除项目: {}", projectCode);
    }
}
```

### 4.2 工作流定义：单节点任务

```java
@Service
@Slf4j
public class SingleTaskWorkflowService {

    @Autowired
    private DolphinClient dolphinClient;

    private static final Long PROJECT_CODE = 123456789L;
    private static final String TENANT_CODE = "default";

    /**
     * 创建单节点 Shell 工作流
     */
    public Long createShellWorkflow(String workflowName, String script) {
        // 1. 使用自定义唯一标识作为任务 Code（3.1.x 中 SDK 自动生成或自定义均可）
        Long taskCode = System.currentTimeMillis();
        log.info("生成任务 Code: {}", taskCode);

        // 2. 构建 Shell 任务对象
        ShellTask shellTask = new ShellTask();
        shellTask.setRawScript(script);
        // 可选：添加资源文件、环境变量等
        // shellTask.setLocalParams(...);
        // shellTask.setResourceList(...);

        // 3. 构建任务定义（使用工具类填充默认值）
        TaskDefinition taskDefinition = TaskDefinitionUtils
            .createDefaultTaskDefinition(taskCode, shellTask);

        // 4. 构建工作流定义参数
        ProcessDefineParam param = new ProcessDefineParam();
        param.setName(workflowName)
            .setDescription("Created by Java SDK")
            .setTenantCode(TENANT_CODE)
            .setTimeout("0")
            .setExecutionType(ProcessDefineParam.EXECUTION_TYPE_PARALLEL)
            .setTaskDefinitionJson(Collections.singletonList(taskDefinition))
            .setTaskRelationJson(TaskRelationUtils.oneLineRelation(taskCode))
            .setGlobalParams(null);

        // 5. 创建工作流
        ProcessDefineResp resp = dolphinClient.opsForProcess()
            .create(PROJECT_CODE, param);
        log.info("创建工作流成功: {}, code: {}", resp.getName(), resp.getCode());

        return resp.getCode();
    }
}
```

### 4.3 工作流定义：多节点依赖 DAG

```java
@Service
@Slf4j
public class DagWorkflowSdkService {

    @Autowired
    private DolphinClient dolphinClient;

    private static final Long PROJECT_CODE = 123456789L;
    private static final String TENANT_CODE = "default";

    /**
     * 创建多节点工作流: Shell → HTTP
     */
    public Long createShellToHttpWorkflow() {
        // 1. 分配 2 个任务 Code
        long baseCode = System.currentTimeMillis();
        Long shellCode = baseCode;
        Long httpCode = baseCode + 1;

        // 2. 构建 Shell 任务
        ShellTask shellTask = new ShellTask();
        shellTask.setRawScript("echo 'Starting data sync...'");
        TaskDefinition shellDef = TaskDefinitionUtils
            .createDefaultTaskDefinition("data-prepare", shellCode, shellTask);

        // 3. 构建 HTTP 任务
        HttpTask httpTask = new HttpTask();
        httpTask.setUrl("http://api.example.com/sync/data")
            .setHttpMethod("POST")
            .setHttpCheckCondition("STATUS_CODE_DEFAULT")
            .setCondition("")
            .setConditionResult(TaskUtils.createEmptyConditionResult());
        TaskDefinition httpDef = TaskDefinitionUtils
            .createDefaultTaskDefinition("api-sync", httpCode, httpTask);

        // 4. 构建工作流参数
        ProcessDefineParam param = new ProcessDefineParam();
        param.setName("shell-to-http-workflow")
            .setDescription("Prepare data then call API")
            .setTenantCode(TENANT_CODE)
            .setTimeout("3600")
            .setExecutionType(ProcessDefineParam.EXECUTION_TYPE_PARALLEL)
            .setTaskDefinitionJson(Arrays.asList(shellDef, httpDef))
            .setTaskRelationJson(
                TaskRelationUtils.oneLineRelation(shellCode, httpCode))
            .setGlobalParams(null);

        // 5. 创建工作流
        ProcessDefineResp resp = dolphinClient.opsForProcess()
            .create(PROJECT_CODE, param);
        log.info("创建多节点工作流成功: {}", resp.getName());

        return resp.getCode();
    }

    /**
     * 创建分支工作流: Shell → Condition → (Success-Shell / Fail-Shell)
     */
    public Long createConditionWorkflow() {
        // 分配 4 个任务 Code
        long baseCode = System.currentTimeMillis();
        Long shell1Code = baseCode;
        Long successCode = baseCode + 1;
        Long failCode = baseCode + 2;
        Long conditionCode = baseCode + 3;

        // Shell-1 任务
        ShellTask shell1 = new ShellTask();
        shell1.setRawScript("echo 'execute main task'");
        TaskDefinition shell1Def = TaskDefinitionUtils
            .createDefaultTaskDefinition("main-task", shell1Code, shell1);

        // 成功分支
        ShellTask successTask = new ShellTask();
        successTask.setRawScript("echo 'Task succeeded'");
        TaskDefinition successDef = TaskDefinitionUtils
            .createDefaultTaskDefinition("success-handler", successCode, successTask);

        // 失败分支
        ShellTask failTask = new ShellTask();
        failTask.setRawScript("echo 'Task failed'");
        TaskDefinition failDef = TaskDefinitionUtils
            .createDefaultTaskDefinition("fail-handler", failCode, failTask);

        // Condition 任务
        ConditionTask conditionTask = TaskUtils.buildConditionTask(
            successCode,    // 成功时跳转
            failCode,       // 失败时跳转
            Collections.singletonList(shell1Code)  // 依赖的前置任务
        );
        TaskDefinition conditionDef = TaskDefinitionUtils
            .createDefaultTaskDefinition("condition-check", conditionCode, conditionTask);

        // 构建任务关系
        TaskRelation relation1 = new TaskRelation();
        relation1.setPreTaskCode(shell1Code);
        relation1.setPostTaskCode(conditionCode);

        TaskRelation relation2 = new TaskRelation();
        relation2.setPreTaskCode(conditionCode);
        relation2.setPostTaskCode(successCode);

        TaskRelation relation3 = new TaskRelation();
        relation3.setPreTaskCode(conditionCode);
        relation3.setPostTaskCode(failCode);

        // 构建工作流
        ProcessDefineParam param = new ProcessDefineParam();
        param.setName("condition-branch-workflow")
            .setDescription("Branch by condition result")
            .setTenantCode(TENANT_CODE)
            .setTimeout("3600")
            .setExecutionType(ProcessDefineParam.EXECUTION_TYPE_PARALLEL)
            .setTaskDefinitionJson(Arrays.asList(
                shell1Def, successDef, failDef, conditionDef))
            .setTaskRelationJson(Arrays.asList(relation1, relation2, relation3))
            .setGlobalParams(null);

        ProcessDefineResp resp = dolphinClient.opsForProcess()
            .create(PROJECT_CODE, param);
        log.info("创建条件分支工作流成功: {}", resp.getName());

        return resp.getCode();
    }
}
```

### 4.4 工作流上线与运行

```java
@Service
@Slf4j
public class WorkflowRuntimeService {

    @Autowired
    private DolphinClient dolphinClient;

    private static final Long PROJECT_CODE = 123456789L;

    /**
     * 上线工作流
     */
    public void releaseWorkflow(Long processCode) {
        dolphinClient.opsForProcess()
            .release(PROJECT_CODE, processCode, "ONLINE");
        log.info("工作流 [{}] 已上线", processCode);
    }

    /**
     * 下线工作流
     */
    public void offlineWorkflow(Long processCode) {
        dolphinClient.opsForProcess()
            .release(PROJECT_CODE, processCode, "OFFLINE");
        log.info("工作流 [{}] 已下线", processCode);
    }

    /**
     * 启动工作流实例
     */
    public Long startWorkflow(Long processCode) {
        StartProcessParam param = new StartProcessParam();
        param.setProcessDefinitionCode(processCode);
        param.setFailureStrategy("END");
        param.setWarningType("NONE");
        param.setExecType("START_PROCESS");

        StartProcessResp resp = dolphinClient.opsForProcessInstance()
            .start(PROJECT_CODE, param);
        log.info("工作流启动成功, instanceId: {}", resp.getId());
        return resp.getId();
    }

    /**
     * 上线并立即运行
     */
    public Long releaseAndStart(Long processCode) {
        releaseWorkflow(processCode);
        return startWorkflow(processCode);
    }
}
```

### 4.5 实例监控与任务日志

```java
@Service
@Slf4j
public class InstanceMonitorSdkService {

    @Autowired
    private DolphinClient dolphinClient;

    private static final Long PROJECT_CODE = 123456789L;

    /**
     * 查询工作流实例列表
     */
    public List<ProcessInstanceResp> listInstances(int pageNo, int pageSize) {
        ProcessInstanceListParam param = new ProcessInstanceListParam();
        param.setPageNo(pageNo);
        param.setPageSize(pageSize);

        ProcessInstanceListResp resp = dolphinClient.opsForProcessInstance()
            .list(PROJECT_CODE, param);
        return resp.getTotalList();
    }

    /**
     * 停止运行中的实例
     */
    public void stopInstance(int instanceId) {
        dolphinClient.opsForProcessInstance().stop(PROJECT_CODE, instanceId);
        log.info("停止实例: {}", instanceId);
    }

    /**
     * 查询任务实例日志
     */
    public String getTaskLog(int taskInstanceId) {
        TaskInstanceLogResp resp = dolphinClient.opsForTaskInstance()
            .queryLog(taskInstanceId, 1, 1000); // 从第1行开始，最多1000行
        return resp.getData();
    }

    /**
     * 查询失败实例并输出日志
     */
    public void diagnoseFailedInstances() {
        List<ProcessInstanceResp> instances = listInstances(1, 50);

        instances.stream()
            .filter(inst -> "FAILURE".equals(inst.getState()))
            .forEach(inst -> {
                log.error("实例 [{}] 执行失败", inst.getName());
                // 获取该实例下的任务实例，查询日志
            });
    }
}
```

### 4.6 定时调度

```java
@Service
@Slf4j
public class ScheduleSdkService {

    @Autowired
    private DolphinClient dolphinClient;

    private static final Long PROJECT_CODE = 123456789L;

    /**
     * 创建定时调度
     */
    public Integer createSchedule(Long processCode, String cron) {
        ScheduleCreateParam param = new ScheduleCreateParam();
        param.setProcessDefinitionCode(processCode);
        param.setCrontab(cron);
        param.setStartTime("2024-01-01 00:00:00");
        param.setEndTime("2099-12-31 23:59:59");
        param.setTimezoneId("Asia/Shanghai");
        param.setFailureStrategy("END");
        param.setWarningType("NONE");
        param.setProcessInstancePriority("MEDIUM");
        param.setWorkerGroup("default");

        ScheduleCreateResp resp = dolphinClient.opsForSchedule()
            .create(PROJECT_CODE, param);
        log.info("定时创建成功, id: {}", resp.getId());
        return resp.getId();
    }

    /**
     * 上线定时
     */
    public void onlineSchedule(int scheduleId) {
        dolphinClient.opsForSchedule().online(PROJECT_CODE, scheduleId);
        log.info("定时 [{}] 已上线", scheduleId);
    }

    /**
     * 下线定时
     */
    public void offlineSchedule(int scheduleId) {
        dolphinClient.opsForSchedule().offline(PROJECT_CODE, scheduleId);
        log.info("定时 [{}] 已下线", scheduleId);
    }

    /**
     * 删除定时
     */
    public void deleteSchedule(int scheduleId) {
        dolphinClient.opsForSchedule().delete(PROJECT_CODE, scheduleId);
        log.info("定时 [{}] 已删除", scheduleId);
    }
}
```

### 4.7 数据源管理

```java
@Service
@Slf4j
public class DataSourceSdkService {

    @Autowired
    private DolphinClient dolphinClient;

    private static final Long PROJECT_CODE = 123456789L;

    /**
     * 创建 MySQL 数据源
     */
    public Long createMySqlDataSource(String name, String host, int port,
                                       String database, String username, String password) {
        DataSourceCreateParam param = new DataSourceCreateParam();
        param.setName(name);
        param.setType("MYSQL");
        param.setNote("MySQL data source");

        // 连接参数
        Map<String, String> connParams = new HashMap<>();
        connParams.put("address", host + ":" + port);
        connParams.put("database", database);
        connParams.put("user", username);
        connParams.put("password", password);
        param.setConnectionParams(connParams);

        DataSourceCreateResp resp = dolphinClient.opsForDataSource()
            .create(PROJECT_CODE, param);
        log.info("创建数据源成功: {}, id: {}", name, resp.getId());
        return resp.getId();
    }

    /**
     * 查询数据源列表
     */
    public List<DataSourceResp> listDataSources() {
        DataSourceListParam param = new DataSourceListParam();
        param.setPageNo(1);
        param.setPageSize(100);

        DataSourceListResp resp = dolphinClient.opsForDataSource()
            .list(PROJECT_CODE, param);
        return resp.getTotalList();
    }
}
```

## 5. 高级技巧与边界场景

### 5.1 任务参数动态传递

```java
@Service
public class DynamicParamService {

    @Autowired
    private DolphinClient dolphinClient;

    private static final Long PROJECT_CODE = 123456789L;

    /**
     * 创建带全局参数的工作流
     * 运行时可以传入具体值
     */
    public Long createWorkflowWithGlobalParams() {
        Long taskCode = System.currentTimeMillis();

        // Shell 任务中使用 ${biz_date} 引用全局参数
        ShellTask shellTask = new ShellTask();
        shellTask.setRawScript("echo 'Processing date: ${biz_date}'");
        TaskDefinition taskDef = TaskDefinitionUtils
            .createDefaultTaskDefinition(taskCode, shellTask);

        // 定义全局参数（默认值可以在运行时覆盖）
        Property bizDateParam = new Property();
        bizDateParam.setProp("biz_date");
        bizDateParam.setDirect("IN");
        bizDateParam.setType("VARCHAR");
        bizDateParam.setValue("${system.biz.date}"); // 使用内置变量

        ProcessDefineParam param = new ProcessDefineParam();
        param.setName("dynamic-param-workflow")
            .setTenantCode("default")
            .setTaskDefinitionJson(Collections.singletonList(taskDef))
            .setTaskRelationJson(TaskRelationUtils.oneLineRelation(taskCode))
            .setGlobalParams(Collections.singletonList(bizDateParam));

        ProcessDefineResp resp = dolphinClient.opsForProcess()
            .create(PROJECT_CODE, param);
        return resp.getCode();
    }
}
```

### 5.2 资源文件管理

```java
@Service
public class ResourceSdkService {

    @Autowired
    private DolphinClient dolphinClient;

    private static final Long PROJECT_CODE = 123456789L;

    /**
     * 上传 Shell 脚本资源文件
     */
    public void uploadScriptResource(String fileName, String content) {
        ResourceCreateParam param = new ResourceCreateParam();
        param.setType("FILE");
        param.setFileName(fileName);
        param.setDescription("Shell script resource");
        // 文件内容需要通过文件上传接口处理

        dolphinClient.opsForResource().create(PROJECT_CODE, param);
    }

    /**
     * 查询资源列表
     */
    public List<ResourceResp> listResources() {
        ResourceListParam param = new ResourceListParam();
        param.setPageNo(1);
        param.setPageSize(100);

        ResourceListResp resp = dolphinClient.opsForResource()
            .list(PROJECT_CODE, param);
        return resp.getTotalList();
    }
}
```

### 5.3 自定义任务类型

SDK 内置支持的任务类型：

| 任务类型 | SDK 类名 | 用途 |
|---|---|---|
| Shell | `ShellTask` | 执行 Shell 脚本 |
| SQL | `SqlTask` | 执行 SQL 语句 |
| Hive | `HiveTask` | Hive SQL |
| Spark | `SparkTask` | Spark 作业 |
| DataX | `DataxTask` | 数据同步 |
| HTTP | `HttpTask` | HTTP 请求 |
| Python | `PythonTask` | Python 脚本 |
| Condition | `ConditionTask` | 条件分支 |
| SubProcess | `SubProcessTask` | 子工作流 |
| Dependent | `DependentTask` | 依赖检查 |

### 5.4 任务位置布局

创建工作流时，任务在画布上的位置由 `locations` 字段控制。SDK 提供了工具类简化布局：

```java
// 垂直排列（一个在上，一个在下）
TaskLocationUtils.verticalLocation(taskCode1, taskCode2);

// 水平排列（从左到右）
TaskLocationUtils.horizontalLocation(taskCode1, taskCode2);

// 自定义坐标
Map<String, Object> location = new HashMap<>();
location.put("taskCode", taskCode);
location.put("x", 100);
location.put("y", 200);
```

## 6. 与 REST API 方式对比

| 维度 | Java SDK | REST API 直连 |
|---|---|---|
| **代码量** | 少，面向对象 | 多，需手动封装 |
| **类型安全** | 强类型，编译期检查 | 弱类型，运行时检查 |
| **版本兼容性** | 需严格匹配 SDK 版本 | 灵活，自行适配字段变化 |
| **依赖** | 引入第三方库 | 仅依赖 Spring Web |
| **调试** | SDK 内部黑盒 | 可直接 curl 复现 |
| **维护** | 社区维护，更新滞后 | 自行维护，可控 |
| **适用场景** | 快速开发、原型验证 | 生产环境、长期维护 |

## 7. 生产最佳实践

### 7.1 SDK 版本锁定

```xml
<!-- 在 properties 中统一定义版本 -->
<properties>
    <dolphinscheduler.sdk.version>3.1.4-RELEASE</dolphinscheduler.sdk.version>
</properties>

<!-- 配合 CI/CD 中的版本校验脚本，确保 SDK 与服务端版本一致 -->
```

### 7.2 封装 Service 层

建议在自己的项目中封装一层 Service，隔离 SDK 的直接调用：

```java
@Service
public class DolphinSchedulerGateway {

    @Autowired
    private DolphinClient dolphinClient;

    // 业务语义方法，而非底层 API 透传
    public void triggerDataSyncJob(String bizDate) { ... }
    public boolean isJobRunning(String jobName) { ... }
    public void waitForCompletion(int instanceId, long timeout) { ... }
}
```

### 7.3 异常处理

```java
@Component
@Slf4j
public class SdkExceptionHandler {

    public <T> T safeExecute(Supplier<T> action, T defaultValue) {
        try {
            return action.get();
        } catch (DsSDKException e) {
            // SDK 内部异常（网络、序列化等）
            log.error("SDK 调用异常: {}", e.getMessage(), e);
            return defaultValue;
        } catch (DsAPIException e) {
            // DolphinScheduler 服务端返回错误
            log.error("DS 服务端错误: code={}, msg={}",
                e.getCode(), e.getMessage());
            return defaultValue;
        }
    }
}
```

### 7.4 版本升级注意事项

1. **升级前**：在测试环境验证 SDK 与新版本服务端的兼容性
2. **升级时**：先升级服务端，再升级 SDK（服务端向后兼容）
3. **升级后**：检查任务定义 JSON 格式是否有字段变更
4. **回滚**：保留旧版本 SDK jar 包，确保可快速回滚

## 8. 总结

Java SDK 是快速集成 DolphinScheduler 的高效方案，核心价值在于：

| 能力 | SDK 优势 |
|---|---|
| 工作流创建 | `TaskDefinitionUtils` + `TaskRelationUtils` 大幅降低 DAG 构建复杂度 |
| 任务类型 | 强类型任务对象，避免 JSON 字符串拼写错误 |
| 版本管理 | SDK 分支与 DS 版本一一对应，减少适配成本 |
| 链式 API | `opsForXxx()` 语义清晰，IDE 自动补全友好 |

一句话总结：**如果你追求开发效率、希望以面向对象的方式操作 DolphinScheduler，且能接受第三方库的维护风险，Java SDK 是理想选择；如果你处于生产环境、对稳定性要求极高，建议优先考虑 REST API 直连方案。**
