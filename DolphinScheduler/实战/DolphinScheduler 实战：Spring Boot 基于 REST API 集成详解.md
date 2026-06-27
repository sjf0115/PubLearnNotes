在企业级数据平台建设中，业务系统与调度平台的深度集成是一个高频需求。Apache DolphinScheduler 作为分布式工作流调度平台，提供了完善的 RESTful API 体系，允许外部系统以编程方式完成项目管理、工作流编排、任务触发、实例监控等全生命周期操作。

本文将从架构设计到代码实现，系统讲解如何在 Spring Boot 项目中基于 DolphinScheduler REST API 构建稳定、可扩展的集成方案。内容覆盖 API 认证机制、客户端封装、核心操作详解以及生产级最佳实践。

本文基于 DolphinScheduler 3.1.9 版本。

## 1. DolphinScheduler REST API 架构概览

DolphinScheduler 的 REST API 采用标准的 HTTP + JSON 协议，API Server 作为统一入口接收所有请求，内部通过 Controller 层路由到对应的 Service 处理。
```
Spring Boot 应用
       │
       ▼ HTTP + JSON
DolphinScheduler API Server (端口 12345)
       │
       ├── ProjectsController      → 项目管理
       ├── ProcessDefinitionController → 工作流定义
       ├── ProcessInstanceController   → 工作流实例
       ├── TaskInstanceController      → 任务实例
       ├── SchedulerController         → 定时调度
       ├── DataSourceController        → 数据源
       └── ...
```

所有 API 请求需要在 Header 中携带 `token` 进行身份认证。Token 通过 Web UI 的 **用户中心 → Token 管理** 页面创建。

### 1.1 核心概念速览

| 概念 | 说明 |
|---|---|
| **项目（Project）** | 工作流的逻辑分组容器，通过 `projectCode` 唯一标识 |
| **工作流定义（Process Definition）** | DAG 描述，由任务定义和任务关系组成 |
| **任务定义（Task Definition）** | 单个节点的执行逻辑，通过 `taskCode` 唯一标识 |
| **工作流实例（Process Instance）** | 一次运行记录，包含状态、起止时间、日志等 |
| **租户（Tenant）** | 任务在 Worker 节点上运行的 Linux 用户 |
| **任务关系（Task Relation）** | 描述 DAG 中节点的前后置依赖 |

## 2. 前置准备

### 2.1 部署 DolphinScheduler

本地开发推荐使用 Standalone 模式快速启动：
```bash
tar -zxvf apache-dolphinscheduler-3.1.9-bin.tar.gz -C /opt/
cd /opt/apache-dolphinscheduler-3.1.9-bin
./bin/dolphinscheduler-daemon.sh start standalone-server
```

Web UI 地址：`http://localhost:12345/dolphinscheduler`，默认账号 `admin` / `dolphinscheduler123`。

### 2.2 创建 API Token

1. 登录 Web UI → 点击右上角头像 → **用户中心**
2. 进入 **Token 管理** → **创建 Token**
3. 设置过期时间，复制 Token 字符串

```
Header: token: 7d3c2b1a9f8e4d6c5b0a2e1f3d4c8b7a
```

> Token 是调用 API 的唯一凭证。生产环境建议通过配置中心注入，并设置 90 天轮换周期。

## 3. Spring Boot 项目搭建

### 3.1 Maven 依赖

```xml
<dependencies>
    <!-- Spring Boot Web -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>

    <!-- 配置属性绑定 -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-configuration-processor</artifactId>
        <optional>true</optional>
    </dependency>

    <!-- JSON 处理 -->
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
    </dependency>

    <!-- HTTP 连接池（生产必备） -->
    <dependency>
        <groupId>org.apache.httpcomponents.client5</groupId>
        <artifactId>httpclient5</artifactId>
    </dependency>

    <!-- Lombok（简化 POJO） -->
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
    connect-timeout: 5000
    read-timeout: 30000
    max-total-connections: 200
    max-per-route: 50
```

## 4. 客户端封装：从简单到完善

### 4.1 配置属性类

```java
@Data
@Configuration
@ConfigurationProperties(prefix = "dolphinscheduler.api")
public class DolphinSchedulerConfig {
    private String baseUrl;
    private String token;
    private int connectTimeout = 5000;
    private int readTimeout = 10000;
    private int maxTotalConnections = 200;
    private int maxPerRoute = 50;
}
```

### 4.2 响应结果统一封装

DolphinScheduler API 的响应格式统一为 `{code, msg, data, success}`：

```java
@Data
@NoArgsConstructor
@AllArgsConstructor
public class DolphinSchedulerResponse<T> {
    private Integer code;
    private String msg;
    private T data;
    private Boolean success;

    public boolean isSuccess() {
        return code != null && code == 0;
    }
}

@Data
public class PageInfo<T> {
    private Integer total;
    private Integer totalList;
    private List<T> totalList;
}
```

### 4.3 核心客户端实现

```java
@Component
@Slf4j
public class DolphinSchedulerRestClient {

    private final RestTemplate restTemplate;
    private final DolphinSchedulerProperties props;
    private final ObjectMapper objectMapper;

    public DolphinSchedulerRestClient(DolphinSchedulerProperties props) {
        this.props = props;
        this.objectMapper = new ObjectMapper()
            .setSerializationInclusion(JsonInclude.Include.NON_NULL);

        // 使用连接池的 HTTP Client
        PoolingHttpClientConnectionManager cm =
            new PoolingHttpClientConnectionManager();
        cm.setMaxTotal(props.getMaxTotalConnections());
        cm.setDefaultMaxPerRoute(props.getMaxPerRoute());

        CloseableHttpClient httpClient = HttpClients.custom()
            .setConnectionManager(cm)
            .setKeepAliveStrategy((response, context) -> 30000L)
            .evictIdleConnections(TimeValue.ofSeconds(30))
            .build();

        HttpComponentsClientHttpRequestFactory factory =
            new HttpComponentsClientHttpRequestFactory(httpClient);
        factory.setConnectTimeout(props.getConnectTimeout());
        factory.setReadTimeout(props.getReadTimeout());

        this.restTemplate = new RestTemplate(factory);

        // Token 拦截器 + 日志拦截器
        this.restTemplate.setInterceptors(Arrays.asList(
            (request, body, execution) -> {
                request.getHeaders().add("token", props.getToken());
                return execution.execute(request, body);
            },
            (request, body, execution) -> {
                log.debug("[DS-API] {} {}", request.getMethod(), request.getURI());
                return execution.execute(request, body);
            }
        ));
    }

    private String url(String path) {
        return props.getBaseUrl() + path;
    }

    // ==================== 通用 HTTP 方法 ====================

    private <T> DolphinSchedulerResponse<T> post(String path, MultiValueMap<String, String> params,
                                  Class<T> responseType) {
        ResponseEntity<DolphinSchedulerResponse> response = restTemplate.postForEntity(
            url(path), params, DolphinSchedulerResponse.class);
        return response.getBody();
    }

    private <T> DolphinSchedulerResponse<T> get(String path, Class<T> responseType, Object... uriVars) {
        return restTemplate.getForObject(url(path), DolphinSchedulerResponse.class, uriVars);
    }

    private <T> DolphinSchedulerResponse<T> getWithParams(String path, Map<String, Object> params,
                                           Class<T> responseType) {
        String uri = UriComponentsBuilder.fromHttpUrl(url(path))
            .queryParams(toMultiValueMap(params))
            .toUriString();
        return restTemplate.getForObject(uri, DolphinSchedulerResponse.class);
    }

    private MultiValueMap<String, String> toMultiValueMap(Map<String, Object> map) {
        MultiValueMap<String, String> result = new LinkedMultiValueMap<>();
        map.forEach((k, v) -> result.add(k, v != null ? v.toString() : ""));
        return result;
    }

    // ==================== 项目管理 ====================

    /**
     * 创建项目
     */
    public DolphinSchedulerResponse<Long> createProject(String projectName, String description) {
        MultiValueMap<String, String> params = new LinkedMultiValueMap<>();
        params.add("projectName", projectName);
        params.add("description", description);
        return post("/projects", params, Long.class);
    }

    /**
     * 查询项目列表
     */
    public DolphinSchedulerResponse<PageInfo<Project>> listProjects(int pageNo, int pageSize) {
        Map<String, Object> params = new HashMap<>();
        params.put("pageNo", pageNo);
        params.put("pageSize", pageSize);
        return getWithParams("/projects", params, PageInfo.class);
    }

    /**
     * 删除项目
     */
    public DolphinSchedulerResponse<Void> deleteProject(Long projectCode) {
        restTemplate.delete(url("/projects/" + projectCode));
        return new DolphinSchedulerResponse<>(0, "success", null, true);
    }

    // ==================== 工作流定义 ====================

    /**
     * 创建工作流定义
     */
    public DolphinSchedulerResponse<String> createProcessDefinition(
            Long projectCode, String processName,
            List<TaskDefinitionJson> tasks, List<TaskRelationJson> relations) {

        MultiValueMap<String, String> params = new LinkedMultiValueMap<>();
        params.add("name", processName);
        params.add("description", "Created via REST API");
        params.add("globalParams", "[]");
        params.add("tasks", toJson(tasks));
        params.add("taskRelation", toJson(relations));
        params.add("executionType", "PARALLEL");
        params.add("timeout", "0");

        return post("/projects/" + projectCode + "/process-definition",
            params, String.class);
    }

    /**
     * 查询工作流定义列表
     */
    public DolphinSchedulerResponse<PageInfo<ProcessDefinition>> listProcessDefinitions(
            Long projectCode, int pageNo, int pageSize) {
        Map<String, Object> params = new HashMap<>();
        params.put("pageNo", pageNo);
        params.put("pageSize", pageSize);
        return getWithParams("/projects/" + projectCode + "/process-definition",
            params, PageInfo.class);
    }

    /**
     * 上线/下线工作流
     */
    public DolphinSchedulerResponse<Void> releaseProcessDefinition(
            Long projectCode, Long processCode, String releaseState) {
        MultiValueMap<String, String> params = new LinkedMultiValueMap<>();
        params.add("name", "");
        params.add("releaseState", releaseState); // ONLINE / OFFLINE
        return post("/projects/" + projectCode + "/process-definition/"
            + processCode + "/release", params, Void.class);
    }

    /**
     * 删除工作流定义
     */
    public DolphinSchedulerResponse<Void> deleteProcessDefinition(Long projectCode, Long processCode) {
        restTemplate.delete(url("/projects/" + projectCode
            + "/process-definition/" + processCode));
        return new DolphinSchedulerResponse<>(0, "success", null, true);
    }

    // ==================== 工作流实例 ====================

    /**
     * 启动工作流实例
     */
    public DolphinSchedulerResponse<String> startProcessInstance(
            Long projectCode, Long processCode,
            Map<String, String> startParams) {

        MultiValueMap<String, String> params = new LinkedMultiValueMap<>();
        params.add("processDefinitionCode", String.valueOf(processCode));
        params.add("failureStrategy", "END");
        params.add("warningType", "NONE");
        params.add("execType", "START_PROCESS");
        params.add("runMode", "RUN_MODE_PARALLEL");

        if (startParams != null) {
            params.add("startParams", toJson(startParams));
        }

        return post("/projects/" + projectCode + "/executors/start-process-instance",
            params, String.class);
    }

    /**
     * 查询工作流实例列表
     */
    public DolphinSchedulerResponse<PageInfo<ProcessInstance>> listProcessInstances(
            Long projectCode, int pageNo, int pageSize, String stateType) {
        Map<String, Object> params = new HashMap<>();
        params.put("pageNo", pageNo);
        params.put("pageSize", pageSize);
        if (stateType != null) {
            params.put("stateType", stateType); // SUCCESS / FAILURE / RUNNING
        }
        return getWithParams("/projects/" + projectCode + "/process-instances",
            params, PageInfo.class);
    }

    /**
     * 停止工作流实例
     */
    public DolphinSchedulerResponse<Void> stopProcessInstance(Long projectCode, int processInstanceId) {
        MultiValueMap<String, String> params = new LinkedMultiValueMap<>();
        params.add("processInstanceId", String.valueOf(processInstanceId));
        params.add("executeType", "STOP");
        return post("/projects/" + projectCode + "/executors/execute",
            params, Void.class);
    }

    // ==================== 定时调度 ====================

    /**
     * 创建定时调度
     */
    public DolphinSchedulerResponse<Integer> createSchedule(
            Long projectCode, Long processCode, String cron) {

        MultiValueMap<String, String> params = new LinkedMultiValueMap<>();
        params.add("processDefinitionCode", String.valueOf(processCode));

        Map<String, String> schedule = new HashMap<>();
        schedule.put("startTime", "2024-01-01 00:00:00");
        schedule.put("endTime", "2099-12-31 23:59:59");
        schedule.put("crontab", cron);
        schedule.put("timezoneId", "Asia/Shanghai");
        params.add("schedule", toJson(schedule));

        params.add("warningType", "NONE");
        params.add("failureStrategy", "END");
        params.add("processInstancePriority", "MEDIUM");
        params.add("workerGroup", "default");

        return post("/projects/" + projectCode + "/schedules",
            params, Integer.class);
    }

    // ==================== 工具方法 ====================

    private String toJson(Object obj) {
        try {
            return objectMapper.writeValueAsString(obj);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("JSON 序列化失败", e);
        }
    }
}
```

### 4.4 数据模型定义

```java
@Data
public class Project {
    private Long id;
    private Long code;
    private String name;
    private String description;
    private String userName;
    private Date createTime;
    private Date updateTime;
}

@Data
public class ProcessDefinition {
    private Long code;
    private String name;
    private Long projectCode;
    private String releaseState; // ONLINE / OFFLINE
    private String description;
    private Date createTime;
    private Date updateTime;
}

@Data
public class ProcessInstance {
    private Integer id;
    private String name;
    private Long processDefinitionCode;
    private String state; // SUCCESS / FAILURE / RUNNING / STOP
    private Date startTime;
    private Date endTime;
    private Integer commandType;
}

/**
 * 任务定义 JSON（创建工作流时使用）
 */
@Data
@Builder
public class TaskDefinitionJson {
    private Long code;
    private Long version;
    private String name;
    private String taskType; // SHELL / SQL / HIVE / SPARK / HTTP 等
    private String taskParams; // JSON 字符串
    private String flag; // YES / NO
    private String description;
    private Integer timeout;
    private String timeoutNotifyStrategy;
}

/**
 * 任务关系 JSON（创建工作流时使用）
 */
@Data
@Builder
public class TaskRelationJson {
    private String name;
    private Integer preTaskVersion;
    private Long preTaskCode; // 0 表示无前置
    private Integer postTaskVersion;
    private Long postTaskCode;
    private String conditionType; // NONE / JUDGE
    private String conditionParams;
}
```

## 5. 核心操作实战

### 5.1 创建并运行一个 Shell 工作流

```java
@Service
@Slf4j
public class WorkflowService {

    @Autowired
    private DolphinSchedulerRestClient dsClient;

    private static final Long PROJECT_CODE = 123456789L;

    /**
     * 创建单节点 Shell 工作流并上线
     */
    public Long createShellWorkflow(String workflowName, String script) {
        try {
            // 1. 使用自定义唯一标识作为任务 Code（3.1.x 支持自动分配或自定义）
            Long taskCode = System.currentTimeMillis();
            log.info("任务 Code: {}", taskCode);

            // 2. 构建任务定义
            Map<String, Object> shellParams = new HashMap<>();
            shellParams.put("rawScript", script);
            shellParams.put("localParams", Collections.emptyList());
            shellParams.put("resourceList", Collections.emptyList());

            TaskDefinitionJson task = TaskDefinitionJson.builder()
                .code(taskCode)
                .version(1)
                .name("shell-task")
                .taskType("SHELL")
                .taskParams(dsClient.toJson(shellParams))
                .flag("YES")
                .description("Shell task created by API")
                .timeout(0)
                .build();

            // 3. 构建任务关系（单节点，前置为 0）
            TaskRelationJson relation = TaskRelationJson.builder()
                .preTaskCode(0L)
                .preTaskVersion(0)
                .postTaskCode(taskCode)
                .postTaskVersion(1)
                .conditionType("NONE")
                .build();

            // 4. 创建工作流定义
            DolphinSchedulerResponse<String> createResult = dsClient.createProcessDefinition(
                PROJECT_CODE, workflowName,
                Collections.singletonList(task),
                Collections.singletonList(relation)
            );

            if (!createResult.isSuccess()) {
                throw new RuntimeException("创建工作流失败: " + createResult.getMsg());
            }

            Long processCode = Long.valueOf(createResult.getData());
            log.info("工作流创建成功, processCode: {}", processCode);

            // 5. 上线工作流
            DolphinSchedulerResponse<Void> releaseResult =
                dsClient.releaseProcessDefinition(PROJECT_CODE, processCode, "ONLINE");
            if (releaseResult.isSuccess()) {
                log.info("工作流 [{}] 已上线", workflowName);
            }

            return processCode;

        } catch (Exception e) {
            log.error("创建工作流异常", e);
            throw new RuntimeException("创建工作流失败", e);
        }
    }

    /**
     * 触发工作流运行
     */
    public String triggerWorkflow(Long processCode) {
        DolphinSchedulerResponse<String> result = dsClient.startProcessInstance(
            PROJECT_CODE, processCode, null);

        if (result.isSuccess()) {
            log.info("工作流启动成功, instanceId: {}", result.getData());
            return result.getData();
        } else {
            throw new RuntimeException("启动失败: " + result.getMsg());
        }
    }
}
```

### 5.2 创建多节点依赖工作流

```java
@Service
public class DagWorkflowService {

    @Autowired
    private DolphinSchedulerRestClient dsClient;

    private static final Long PROJECT_CODE = 123456789L;

    /**
     * 创建 DAG: Shell-A → (SQL-B, SQL-C) → Spark-D
     *        B 和 C 并行执行，都完成后执行 D
     */
    public Long createMultiTaskWorkflow() throws JsonProcessingException {
        ObjectMapper mapper = new ObjectMapper();

        // 1. 分配 4 个任务 Code（3.1.x 使用自定义唯一标识即可）
        long baseCode = System.currentTimeMillis();
        Long taskA = baseCode;
        Long taskB = baseCode + 1;
        Long taskC = baseCode + 2;
        Long taskD = baseCode + 3;

        // 2. 构建 4 个任务定义
        List<TaskDefinitionJson> tasks = new ArrayList<>();

        // Task A: Shell - 数据准备
        tasks.add(buildTask(taskA, "prepare-data", "SHELL",
            Map.of("rawScript", "echo 'prepare data'")));

        // Task B: SQL - 清洗
        tasks.add(buildTask(taskB, "clean-sql", "SQL",
            Map.of("type", "POSTGRESQL", "datasource", "1",
                   "sql", "UPDATE orders SET status='CLEANED'")));

        // Task C: SQL - 校验
        tasks.add(buildTask(taskC, "validate-sql", "SQL",
            Map.of("type", "POSTGRESQL", "datasource", "1",
                   "sql", "SELECT COUNT(*) FROM orders")));

        // Task D: Spark - 分析
        tasks.add(buildTask(taskD, "spark-analyze", "SPARK",
            Map.of("programType", "JAVA", "mainClass", "com.example.Analyze",
                   "mainJar", "{\"id\":1}", "deployMode", "cluster")));

        // 3. 构建任务关系
        List<TaskRelationJson> relations = new ArrayList<>();
        // A → B
        relations.add(buildRelation(taskA, taskB));
        // A → C
        relations.add(buildRelation(taskA, taskC));
        // B → D
        relations.add(buildRelation(taskB, taskD));
        // C → D
        relations.add(buildRelation(taskC, taskD));

        // 4. 创建工作流
        DolphinSchedulerResponse<String> result = dsClient.createProcessDefinition(
            PROJECT_CODE, "multi-task-dag", tasks, relations);

        Long processCode = Long.valueOf(result.getData());
        dsClient.releaseProcessDefinition(PROJECT_CODE, processCode, "ONLINE");

        return processCode;
    }

    private TaskDefinitionJson buildTask(Long code, String name, String type,
                                          Map<String, Object> params) throws JsonProcessingException {
        ObjectMapper mapper = new ObjectMapper();
        return TaskDefinitionJson.builder()
            .code(code).version(1).name(name)
            .taskType(type).taskParams(mapper.writeValueAsString(params))
            .flag("YES").timeout(3600).build();
    }

    private TaskRelationJson buildRelation(Long preCode, Long postCode) {
        return TaskRelationJson.builder()
            .preTaskCode(preCode).preTaskVersion(1)
            .postTaskCode(postCode).postTaskVersion(1)
            .conditionType("NONE").build();
    }
}
```

### 5.3 实例监控与干预

```java
@Service
@Slf4j
public class InstanceMonitorService {

    @Autowired
    private DolphinSchedulerRestClient dsClient;

    private static final Long PROJECT_CODE = 123456789L;

    /**
     * 获取所有运行中的实例
     */
    public List<ProcessInstance> getRunningInstances() {
        DolphinSchedulerResponse<PageInfo<ProcessInstance>> result =
            dsClient.listProcessInstances(PROJECT_CODE, 1, 100, "RUNNING");

        if (result.isSuccess() && result.getData() != null) {
            return result.getData().getTotalList();
        }
        return Collections.emptyList();
    }

    /**
     * 自动停止运行超过 N 分钟的实例
     */
    @Scheduled(fixedRate = 300000) // 每 5 分钟执行
    public void autoStopLongRunningInstances() {
        int timeoutMinutes = 60;
        long threshold = System.currentTimeMillis() - timeoutMinutes * 60 * 1000;

        getRunningInstances().stream()
            .filter(inst -> inst.getStartTime().getTime() < threshold)
            .forEach(inst -> {
                log.warn("实例 [{}] 运行超过 {} 分钟，自动停止", inst.getName(), timeoutMinutes);
                dsClient.stopProcessInstance(PROJECT_CODE, inst.getId());
            });
    }

    /**
     * 查询失败实例并告警
     */
    public void alertFailedInstances() {
        DolphinSchedulerResponse<PageInfo<ProcessInstance>> result =
            dsClient.listProcessInstances(PROJECT_CODE, 1, 50, "FAILURE");

        if (result.isSuccess() && result.getData() != null) {
            List<ProcessInstance> failures = result.getData().getTotalList();
            if (!failures.isEmpty()) {
                log.error("发现 {} 个失败实例，请检查", failures.size());
                // 接入企业微信/钉钉告警
            }
        }
    }
}
```

### 5.4 定时调度管理

```java
@Service
public class ScheduleManagerService {

    @Autowired
    private DolphinSchedulerRestClient dsClient;

    private static final Long PROJECT_CODE = 123456789L;

    /**
     * 为工作流创建每日定时调度
     */
    public void scheduleDaily(Long processCode, String cron) {
        DolphinSchedulerResponse<Integer> result = dsClient.createSchedule(
            PROJECT_CODE, processCode, cron);

        if (result.isSuccess()) {
            log.info("定时调度创建成功, scheduleId: {}", result.getData());
        }
    }

    /**
     * 常用调度模板
     */
    public void applyCommonSchedules(Long processCode) {
        // 每小时
        scheduleDaily(processCode, "0 0 * * * ?");
        // 每天凌晨 2 点
        // scheduleDaily(processCode, "0 0 2 * * ?");
        // 每 5 分钟
        // scheduleDaily(processCode, "0 */5 * * * ?");
    }
}
```

## 6. 生产最佳实践

### 6.1 异常分类处理

```java
@Component
@Slf4j
public class DsApiExceptionHandler {

    public <T> T executeWithRetry(Supplier<T> apiCall, int maxRetries) {
        int attempts = 0;
        while (attempts < maxRetries) {
            try {
                return apiCall.get();
            } catch (HttpClientErrorException e) {
                if (e.getStatusCode() == HttpStatus.UNAUTHORIZED) {
                    log.error("Token 失效，请检查 Token 是否过期");
                    throw new DsAuthException("Token 无效", e);
                }
                if (e.getStatusCode() == HttpStatus.TOO_MANY_REQUESTS) {
                    log.warn("请求频率过高，等待后重试");
                    sleep(1000);
                    attempts++;
                    continue;
                }
                throw new DsApiException("API 调用失败: " + e.getStatusCode(), e);
            } catch (ResourceAccessException e) {
                log.error("连接 DolphinScheduler 失败: {}", e.getMessage());
                sleep(2000);
                attempts++;
                if (attempts >= maxRetries) {
                    throw new DsApiException("连接超时，重试次数耗尽", e);
                }
            }
        }
        throw new DsApiException("重试次数耗尽");
    }

    private void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException ignored) {}
    }
}
```

### 6.2 幂等性保障

```java
@Service
public class IdempotentDsService {

    @Autowired
    private DolphinSchedulerRestClient dsClient;

    @Autowired
    private StringRedisTemplate redisTemplate;

    private static final String WORKFLOW_KEY_PREFIX = "ds:workflow:";

    /**
     * 幂等创建工作流（基于 Redis 分布式锁）
     */
    public Long createWorkflowIdempotent(String workflowName,
                                         List<TaskDefinitionJson> tasks,
                                         List<TaskRelationJson> relations) {
        String lockKey = WORKFLOW_KEY_PREFIX + workflowName;
        Boolean locked = redisTemplate.opsForValue()
            .setIfAbsent(lockKey, "1", Duration.ofMinutes(5));

        if (!Boolean.TRUE.equals(locked)) {
            log.info("工作流 [{}] 正在创建中或已存在", workflowName);
            return null;
        }

        try {
            // 先查询是否已存在
            DolphinSchedulerResponse<PageInfo<ProcessDefinition>> list =
                dsClient.listProcessDefinitions(PROJECT_CODE, 1, 100);

            boolean exists = list.getData().getTotalList().stream()
                .anyMatch(p -> p.getName().equals(workflowName));

            if (exists) {
                log.info("工作流 [{}] 已存在", workflowName);
                return null;
            }

            // 创建
            DolphinSchedulerResponse<String> result = dsClient.createProcessDefinition(
                PROJECT_CODE, workflowName, tasks, relations);
            return Long.valueOf(result.getData());

        } finally {
            redisTemplate.delete(lockKey);
        }
    }
}
```

### 6.3 配置化任务参数

```java
@Configuration
@ConfigurationProperties(prefix = "dolphinscheduler.workflow")
@Data
public class WorkflowConfig {
    private String projectCode;
    private String tenantCode = "default";
    private int defaultTimeout = 3600;
    private Map<String, String> workerGroups = new HashMap<>();
}
```

### 6.4 版本兼容性矩阵

| DolphinScheduler 版本 | API 变化 | 注意事项 |
|---|---|---|
| 2.x | 大 JSON 模式 | 任务定义和关系在一个 JSON 中 |
| 3.0.x | Task Definition 分离 | 引入独立的 Task Definition API |
| 3.1.x | Task Code 引入 | 支持任务版本管理，Code 可选自定义 |

## 7. 总结

基于 REST API 集成 DolphinScheduler 是最通用、最稳定的方案，核心要点：

| 维度 | 建议 |
|---|---|
| **认证** | Token 注入 Header，生产环境配置中心管理 |
| **连接** | 必须使用 HTTP 连接池，配置合理超时 |
| **任务 Code** | 3.1.x 中任务 Code 可自定义传入，系统自动分配版本 |
| **模型** | 任务定义(TaskDefinition)和任务关系(TaskRelation)分离 |
| **异常** | 分类处理 401/429/连接超时，实现重试 |
| **幂等** | 创建操作先查后创，分布式锁防止并发重复 |
| **版本** | 升级前在测试环境验证 API 兼容性 |

REST API 直连方式虽然代码量相对较大，但它不依赖任何第三方库，版本兼容性好，且在问题排查时可以直接通过 curl 复现请求，是生产环境的首选方案。
