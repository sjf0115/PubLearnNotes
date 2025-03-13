
## 1. 入口
```java
@Slf4j
@RequestMapping("/seatunnel/api/v1/job/executor")
@RestController
public class JobExecutorController {

    @Resource IJobExecutorService jobExecutorService;
    @Resource private IJobInstanceService jobInstanceService;
    @Resource private ITaskInstanceService<SeaTunnelJobInstanceDto> taskInstanceService;

    @PostMapping("/execute")
    @ApiOperation(value = "Execute synchronization tasks", httpMethod = "POST")
    public Result<Long> jobExecutor(
           @ApiParam(value = "jobDefineId", required = true) @RequestParam("jobDefineId") Long jobDefineId,
           @RequestBody(required = false) JobExecParam executeParam) {
        return jobExecutorService.jobExecute(jobDefineId, executeParam);
    }
    ...
}
```



```java
public class JobExecutorServiceImpl implements IJobExecutorService {
    @Resource private IJobInstanceService jobInstanceService;
    @Resource private IJobInstanceDao jobInstanceDao;
    @Autowired private AsyncTaskExecutor taskExecutor;

    @Override
    public Result<Long> jobExecute(Long jobDefineId, JobExecParam executeParam) {
        JobExecutorRes executeResource = jobInstanceService.createExecuteResource(jobDefineId, executeParam);
        String jobConfig = executeResource.getJobConfig();

        String configFile = writeJobConfigIntoConfFile(jobConfig, jobDefineId);

        try {
            executeJobBySeaTunnel(configFile, executeResource.getJobInstanceId());
            return Result.success(executeResource.getJobInstanceId());
        } catch (RuntimeException e) {
            Result<Long> failure = Result.failure(SeatunnelErrorEnum.JOB_EXEC_SUBMISSION_ERROR, e.getMessage());
            failure.setData(executeResource.getJobInstanceId());
            return failure;
        }
    }
    ...
}
```

### 2. createExecuteResource

```java
public class JobInstanceServiceImpl extends SeatunnelBaseServiceImpl implements IJobInstanceService {
    ...
    @Override
    public JobExecutorRes createExecuteResource(@NonNull Long jobDefineId, JobExecParam executeParam) {
        // 获取当前登录用户
        int userId = ServletUtils.getCurrentUserId();
        // 权限验证
        funcPermissionCheck(SeatunnelFuncPermissionKeyConstant.JOB_EXECUTOR_RESOURCE, userId);
        // 根据作业ID获取作业信息
        JobDefinition job = jobDefinitionDao.getJob(jobDefineId);
        JobVersion latestVersion = jobVersionDao.getLatestVersion(job.getId());

        // 创建作业实例
        JobInstance jobInstance = new JobInstance();
        String jobConfig = createJobConfig(latestVersion, executeParam);
        try {
            jobInstance.setId(CodeGenerateUtils.getInstance().genCode());
        } catch (CodeGenerateUtils.CodeGenerateException e) {
            throw new SeatunnelException(SeatunnelErrorEnum.JOB_RUN_GENERATE_UUID_ERROR);
        }
        jobInstance.setJobDefineId(job.getId());
        jobInstance.setEngineName(latestVersion.getEngineName());
        jobInstance.setEngineVersion(latestVersion.getEngineVersion());
        jobInstance.setJobConfig(jobConfig);
        jobInstance.setCreateUserId(userId);
        jobInstance.setJobType(latestVersion.getJobMode());
        jobInstanceDao.insert(jobInstance);

        // 封装 JobExecutorRes 返回
        return new JobExecutorRes(
                jobInstance.getId(),
                jobInstance.getJobConfig(),
                jobInstance.getEngineName(),
                null,
                null,
                jobInstance.getJobType());
    }
    ...
}
```

## 3. writeJobConfigIntoConfFile


## 4. executeJobBySeaTunnel

```java
private void executeJobBySeaTunnel(String filePath, Long jobInstanceId) {
    Common.setDeployMode(DeployMode.CLIENT);
    // 1. 创建作业配置 JobConfig
    JobConfig jobConfig = new JobConfig();
    jobConfig.setName(jobInstanceId + "_job");
    SeaTunnelClient seaTunnelClient;
    ClientJobProxy clientJobProxy;
    try {
        // 2. 创建 SeaTunnel 客户端
        seaTunnelClient = createSeaTunnelClient();
        // 3. 创建 SeaTunnel 配置 SeaTunnelConfig
        SeaTunnelConfig seaTunnelConfig = new YamlSeaTunnelConfigBuilder().build();
        // 4. 创建作业执行环境
        ClientJobExecutionEnvironment jobExecutionEnv =
                seaTunnelClient.createExecutionContext(filePath, jobConfig, seaTunnelConfig);
        clientJobProxy = jobExecutionEnv.execute();
    } catch (Throwable e) {
        log.error("Job execution submission failed.", e);
        JobInstance jobInstance = jobInstanceDao.getJobInstance(jobInstanceId);
        jobInstance.setJobStatus(JobStatus.FAILED);
        jobInstance.setEndTime(new Date());
        String jobInstanceErrorMessage = JobUtils.getJobInstanceErrorMessage(e.getMessage());
        jobInstance.setErrorMessage(jobInstanceErrorMessage);
        jobInstanceDao.update(jobInstance);
        throw new RuntimeException(e.getMessage(), e);
    }
    JobInstance jobInstance = jobInstanceDao.getJobInstance(jobInstanceId);
    jobInstance.setJobEngineId(Long.toString(clientJobProxy.getJobId()));
    jobInstanceDao.update(jobInstance);
    // Use Spring thread pool to handle asynchronous user retrieval
    CompletableFuture.runAsync(
            () -> {
                waitJobFinish(
                        clientJobProxy,
                        jobInstanceId,
                        Long.toString(clientJobProxy.getJobId()),
                        seaTunnelClient);
            },
            taskExecutor);
}
```

### 4.1 初始化作业配置 JobConfig

创建 JobConfig：
```java
JobConfig jobConfig = new JobConfig();
jobConfig.setName(jobInstanceId + "_job");
```
定义作业的基本元数据，此处通过 jobInstanceId 生成唯一作业名(jobInstanceId 和 `_job` 拼接)，便于日志追踪与状态管理。

### 4.2 创建 SeaTunnel 客户端

通过 `createSeaTunnelClient()` 需返回一个配置好的客户端实例，负责与 SeaTunnel 引擎通信：
```java
SeaTunnelClient seaTunnelClient = createSeaTunnelClient();
```

创建 `SeaTunnelClient` 需要通过 `ConfigProvider.locateAndGetClientConfig()` 加载配置文件：
```java
private SeaTunnelClient createSeaTunnelClient() {
    ClientConfig clientConfig = ConfigProvider.locateAndGetClientConfig();
    return new SeaTunnelClient(clientConfig);
}
```
加载配置文件首先验证系统属性后缀，确保配置文件名合法。然后通过三级配置加载策略来尝试加载配置文件：
```java
@NonNull public static ClientConfig locateAndGetClientConfig() {
    // 1. 文件后缀合法性验证
    validateSuffixInSystemProperty(SYSPROP_CLIENT_CONFIG);

    ClientConfig config;
    YamlClientConfigLocator yamlConfigLocator = new YamlClientConfigLocator();
    // 2. 加载配置文件
    if (yamlConfigLocator.locateFromSystemProperty()) {
        // 1. Try loading config if provided in system property, and it is an YAML file
        config = new YamlClientConfigBuilder(yamlConfigLocator.getIn()).build();
    } else if (yamlConfigLocator.locateInWorkDirOrOnClasspath()) {
        // 2. Try loading YAML config from the working directory or from the classpath
        config = new YamlClientConfigBuilder(yamlConfigLocator.getIn()).build();
    } else {
        // 3. Loading the default YAML configuration file
        yamlConfigLocator.locateDefault();
        config = new YamlClientConfigBuilder(yamlConfigLocator.getIn()).build();
    }
    String stDockerMemberList = System.getenv("ST_DOCKER_MEMBER_LIST");
    if (stDockerMemberList != null) {
        config.getNetworkConfig().setAddresses(Arrays.asList(stDockerMemberList.split(",")));
    }
    return config;
}
```
首先调用 `validateSuffixInSystemProperty` 方法，验证系统属性中指定的配置文件后缀是否合法，是否为 xml、yaml 或者 yml。

> `SYSPROP_CLIENT_CONFIG` 是系统属性键为 `hazelcast.client.config`。

然后创建 `YamlClientConfigLocator` 实例 `yamlConfigLocator`，用于定位 YAML 格式的客户端配置文件。通过三级配置加载策略来尝试加载配置文件：  
- 优先级1：系统属性指定的外部 YAML 文件
  - 调用 `locateFromSystemProperty()`，尝试从系统属性（如 `-Dhazelcast.client.config=path/to/config.yaml`）指定的路径加载配置文件。
  - 使用 `YamlClientConfigBuilder` 构建配置：通过 `yamlConfigLocator.getIn()` 获取输入流，解析 YAML 文件并生成 `ClientConfig` 实例。
- 优先级2：工作目录或类路径中的 YAML 文件
  - 若未通过系统属性找到配置，尝试从工作目录或类路径查找默认配置文件（如 `seatunnel-client.yaml`）。
  - 同样构建配置，但数据源为工作目录或类路径中的文件。
- 优先级3：内嵌的默认 YAML 文件
  - 若前两步均失败，调用 `locateDefault()` 加载内嵌的默认配置文件（可能位于项目资源中），确保总能获取配置。

### 4.3 加载引擎配置 SeaTunnelConfig

从默认路径（如 conf/seatunnel.yaml）或类路径加载 YAML 格式的引擎配置，定义线程池、序列化方式等运行时参数：
```java
SeaTunnelConfig seaTunnelConfig = new YamlSeaTunnelConfigBuilder().build();
```
实质上：
```java
public SeaTunnelConfig() {
    hazelcastConfig = new Config();
    hazelcastConfig
            .getNetworkConfig()
            .getJoin()
            .getMulticastConfig()
            .setMulticastPort(Constant.DEFAULT_SEATUNNEL_MULTICAST_PORT);
    hazelcastConfig
            .getHotRestartPersistenceConfig()
            .setBaseDir(new File(seatunnelHome(), "recovery").getAbsoluteFile());
    System.setProperty("hazelcast.compat.classloading.cache.disabled", "true");
}
```
### 4.4 构建执行环境并提交作业

通过 `createExecutionContext()` 整合作业配置与引擎配置，生成可执行上下文环境：
```java
ClientJobExecutionEnvironment jobExecutionEnv =
        seaTunnelClient.createExecutionContext(filePath, jobConfig, seaTunnelConfig);
```
> filePath 为作业配置文件路径（如 job.yaml），定义数据源、转换逻辑、输出目标。

然后通过 `execute()` 提交作业到 SeaTunnel 引擎，返回 ClientJobProxy 用于状态监控和生命周期管理：
```java
ClientJobProxy clientJobProxy = jobExecutionEnv.execute();
```

### 4.5 等待作业执行结果

使用 `CompletableFuture` 结合 Spring 线程池 `taskExecutor`，异步查询作业执行结果，避免阻塞主线程：
```java
CompletableFuture.runAsync(
    () -> {
        waitJobFinish(clientJobProxy, jobInstanceId, Long.toString(clientJobProxy.getJobId()), seaTunnelClient);
    },
    taskExecutor
);
```
`waitJobFinish` 需轮询 `clientJobProxy.waitForJobCompleteV2()`，更新数据库状态至 SUCCESS/FAILED。
```java
public void waitJobFinish(ClientJobProxy clientJobProxy, Long jobInstanceId,
        String jobEngineId, SeaTunnelClient seaTunnelClient) {
    ExecutorService executor = Executors.newFixedThreadPool(1);
    CompletableFuture<JobResult> future = CompletableFuture.supplyAsync(clientJobProxy::waitForJobCompleteV2, executor);
    JobResult jobResult = new JobResult(JobStatus.FAILED, "");
    try {
        jobResult = future.get();
        executor.shutdown();
    } catch (InterruptedException e) {
        ...
    } catch (ExecutionException e) {
        ...
    } finally {
        seaTunnelClient.close();
        ...
    }
}
```
