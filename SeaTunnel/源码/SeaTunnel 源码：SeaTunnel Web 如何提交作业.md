通过深入分析 SeaTunnel Web 的源码，本文将详细介绍其作业提交的核心流程，涵盖从用户请求到作业执行的全链路实现。本文基于 SeaTunnel 2.3.0 版本，修正此前对代码逻辑的误解，并补充关键实现细节。

## 1. 入口

用户通过前端界面提交作业配置（数据源、转换逻辑、输出目标）。前端发送 POST 请求到 `/seatunnel/api/v1/job/executor/execute`，调用服务层 JobExecutorService 触发作业提交流程：
```java
@Slf4j
@RequestMapping("/seatunnel/api/v1/job/executor")
@RestController
public class JobExecutorController {

    @Resource IJobExecutorService jobExecutorService;

    @PostMapping("/execute")
    @ApiOperation(value = "Execute synchronization tasks", httpMethod = "POST")
    public Result<Long> jobExecutor(@ApiParam(value = "jobDefineId", required = true) @RequestParam("jobDefineId") Long jobDefineId,
      @RequestBody(required = false) JobExecParam executeParam) {
        return jobExecutorService.jobExecute(jobDefineId, executeParam);
    }
    ...
}
```

## 2. 作业提交流程


```java
public class JobExecutorServiceImpl implements IJobExecutorService {
    @Resource private IJobInstanceService jobInstanceService;
    @Resource private IJobInstanceDao jobInstanceDao;
    @Autowired private AsyncTaskExecutor taskExecutor;

    @Override
    public Result<Long> jobExecute(Long jobDefineId, JobExecParam executeParam) {
        // 1. 创建执行资源
        JobExecutorRes executeResource = jobInstanceService.createExecuteResource(jobDefineId, executeParam);
        String jobConfig = executeResource.getJobConfig();
        // 2. 写入配置文件
        String configFile = writeJobConfigIntoConfFile(jobConfig, jobDefineId);
        try {
            // 3. 提交作业
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

### 2.1 创建执行资源

创建执行资源是 SeaTunnel Web 作业提交流程的核心前置步骤，完成了从权限校验、配置生成到实例持久化的关键操作：
```java
public class JobInstanceServiceImpl extends SeatunnelBaseServiceImpl implements IJobInstanceService {
    ...
    @Override
    public JobExecutorRes createExecuteResource(@NonNull Long jobDefineId, JobExecParam executeParam) {
        // 1. 权限验证
        int userId = ServletUtils.getCurrentUserId();
        funcPermissionCheck(SeatunnelFuncPermissionKeyConstant.JOB_EXECUTOR_RESOURCE, userId);
        // 2. 加载作业版本 JobVersion
        JobDefinition job = jobDefinitionDao.getJob(jobDefineId);
        JobVersion latestVersion = jobVersionDao.getLatestVersion(job.getId());
        // 3. 生成作业实例配置
        String jobConfig = createJobConfig(latestVersion, executeParam);
        // 4. 创建作业实例 JobInstance
        JobInstance jobInstance = new JobInstance();
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
        // 5. 返回作业执行资源 JobExecutorRes
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
根据上述代码可以看到创建执行资源流程如下所示：
- 创建执行资源之前需要通过 `ServletUtils` 方法从请求上下文中提取用户身份来验证用户是否拥有 `JOB_EXECUTOR_RESOURCE` 权限。
- 根据 jobDefineId 从数据库查询作业定义（JobDefinition）来获取该作业的最新版本（JobVersion）。
- 根据上述生成的 JobVersion 以及传递过来的 JobExecParam 来生成作业实例配置。
- 创建作业实例对象
  - 基于 Snowflake 变体算法生成实例唯一ID。
  - 根据当前登录用户、JobVersion 以及生成的作业实例配置来填充作业实例属性
  - 将 JobInstance 对象插入数据库表
- 最后将 JobInstance 组装成作业执行资源 JobExecutorRes 对象返回

### 2.2 写入配置文件

使用 `BufferedWriter` 将 jobConfig（YAML 格式）写入本地文件系统 `{项目根目录}/profile/{jobDefineId}.conf` 配置文件中：
```java
public String writeJobConfigIntoConfFile(String jobConfig, Long jobDefineId) {
    String projectRoot = System.getProperty("user.dir");
    String filePath = projectRoot + File.separator + "profile" + File.separator + jobDefineId + ".conf";
    try {
        File file = new File(filePath);
        if (!file.exists()) {
            file.getParentFile().mkdirs();
        }

        FileWriter fileWriter = new FileWriter(file);
        BufferedWriter bufferedWriter = new BufferedWriter(fileWriter);

        bufferedWriter.write(jobConfig);
        bufferedWriter.close();
    } catch (IOException e) {
        throw new RuntimeException(e);
    }
    return filePath;
}
```
上述代码将动态生成的作业配置持久化到文件系统，供 SeaTunnel 客户端加载。此外通过 `jobDefineId` 隔离不同作业模板的配置，避免文件名冲突。

### 2.3 作业提交

SeaTunnel Web 通过 `executeJobBySeaTunnel` 方法实现了从配置解析、作业提交到状态监控的全流程管理：
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
具体流程如下：
- 初始化作业配置: 加载客户端与引擎配置。
- 创建 SeaTunnel 客户端:
- 加载引擎配置 SeaTunnelConfig:
- 构建执行环境并提交作业：构建执行计划并提交到 Zeta 集群。
- 异步等待作业执行结果：轮询作业状态直至终态，保障可观测性。


设置部署模式:
```java
Common.setDeployMode(DeployMode.CLIENT);
```
指定作业以 客户端模式（CLIENT） 运行，此模式下：
- 客户端进程（SeaTunnel Web）负责与 Zeta 集群通信并监控作业状态。
- 客户端需保持运行直至作业完成，适合实时查看日志的场景。

#### 2.3.1 初始化作业配置

初始化作业配置 JobConfig：
```java
JobConfig jobConfig = new JobConfig();
jobConfig.setName(jobInstanceId + "_job");
```
定义作业的基本元数据，此处通过 `jobInstanceId` 生成唯一作业名(jobInstanceId 和 `_job` 拼接)，便于日志追踪与状态管理。

#### 2.3.2 创建 SeaTunnel 客户端

通过 `createSeaTunnelClient()` 需返回一个配置好的客户端实例，负责与 `SeaTunnel` 引擎通信：
```java
SeaTunnelClient seaTunnelClient = createSeaTunnelClient();
```

创建 `SeaTunnelClient` 需要通过 `ConfigProvider.locateAndGetClientConfig()` 加载客户端配置：
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
首先调用 `validateSuffixInSystemProperty` 方法，验证系统属性中指定的配置文件后缀是否合法，是否为 xml、yaml 或者 yml 格式。

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

#### 2.3.3 加载引擎全局配置

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
#### 2.3.4 构建执行环境并提交作业

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

#### 2.3.5 等待作业执行结果

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
