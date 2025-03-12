
入口：
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

### createExecuteResource

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

### writeJobConfigIntoConfFile


### executeJobBySeaTunnel

```java
private void executeJobBySeaTunnel(String filePath, Long jobInstanceId) {
    Common.setDeployMode(DeployMode.CLIENT);
    JobConfig jobConfig = new JobConfig();
    jobConfig.setName(jobInstanceId + "_job");
    SeaTunnelClient seaTunnelClient;
    ClientJobProxy clientJobProxy;
    try {
        seaTunnelClient = createSeaTunnelClient();
        SeaTunnelConfig seaTunnelConfig = new YamlSeaTunnelConfigBuilder().build();
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

创建 JobConfig：
- jobInstanceId 和 `_job` 设置名称

创建 SeaTunnelClient：
  ```java
  private SeaTunnelClient createSeaTunnelClient() {
      ClientConfig clientConfig = ConfigProvider.locateAndGetClientConfig();
      return new SeaTunnelClient(clientConfig);
  }
  ```

## 加载配置文件

首先验证系统属性后缀，确保配置文件名合法。  
然后设置三级配置加载策略：  
- 优先级1：系统属性指定的外部 YAML 文件。  
- 优先级2：工作目录或类路径中的 YAML 文件。  
- 优先级3：内嵌的默认 YAML 文件。  

```java
@NonNull public static ClientConfig locateAndGetClientConfig() {
    // (1) 文件后缀合法性验证
    validateSuffixInSystemProperty(SYSPROP_CLIENT_CONFIG);

    ClientConfig config;
    YamlClientConfigLocator yamlConfigLocator = new YamlClientConfigLocator();

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

调用 `validateSuffixInSystemProperty` 方法，验证系统属性中指定的配置文件后缀是否合法，是否为 xml、yaml 或者 yml。`SYSPROP_CLIENT_CONFIG` 是系统属性键为 `hazelcast.client.config`。

创建 `YamlClientConfigLocator` 实例 `yamlConfigLocator`，用于定位 YAML 格式的客户端配置文件。

调用 `locateFromSystemProperty()`，尝试从系统属性（如 `-Dhazelcast.client.config=path/to/config.yaml`）指定的路径加载配置文件。若成功，进入分支。

```java
        config = new YamlClientConfigBuilder(yamlConfigLocator.getIn()).build();
```
- 使用 `YamlClientConfigBuilder` 构建配置：通过 `yamlConfigLocator.getIn()` 获取输入流，解析 YAML 文件并生成 `ClientConfig` 实例。

```java
    } else if (yamlConfigLocator.locateInWorkDirOrOnClasspath()) {
```
- 若未通过系统属性找到配置，尝试从工作目录（项目根目录）或类路径（如 `resources` 目录）查找默认配置文件（如 `seatunnel-client.yaml`）。

```java
        config = new YamlClientConfigBuilder(yamlConfigLocator.getIn()).build();
```
- 同样构建配置，但数据源为工作目录或类路径中的文件。

```java
    } else {
        yamlConfigLocator.locateDefault();
        config = new YamlClientConfigBuilder(yamlConfigLocator.getIn()).build();
    }
```
- 若前两步均失败，调用 `locateDefault()` 加载内嵌的默认配置文件（可能位于项目资源中），确保总能获取配置。

```java
    String stDockerMemberList = System.getenv("ST_DOCKER_MEMBER_LIST");
```
- 读取环境变量 `ST_DOCKER_MEMBER_LIST`，该变量可能用于 Docker 集群环境，指定成员地址列表。

```java
    if (stDockerMemberList != null) {
        config.getNetworkConfig().setAddresses(Arrays.asList(stDockerMemberList.split(",")));
    }
```
- 若环境变量存在，按逗号分割为地址列表，并覆盖 `ClientConfig` 中的网络地址配置。实现动态地址注入。

```java
    return config;
}
```
- 返回构建好的 `ClientConfig` 实例，完成配置加载。

---



**设计意图**  
- **灵活性**：支持多种配置来源，便于不同环境（开发、生产、测试）切换。  
- **容错性**：确保总能加载默认配置，避免因配置缺失导致应用崩溃。  
- **扩展性**：通过环境变量覆盖部分配置，适应云原生场景的动态需求。
