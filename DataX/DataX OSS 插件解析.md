
## 1. Job

```java
public static class Job extends Writer.Job {

    @Override
    public void preHandler(Configuration jobConfiguration) {

    }

    @Override
    public void preCheck() {

    }

    @Override
    public void init() {

    }

    @Override
    public void prepare() {

    }

    @Override
    public List<Configuration> split(int mandatoryNumber) {
        return Collections.emptyList();
    }

    @Override
    public void post() {

    }

    @Override
    public void destroy() {

    }
}
```

### 1.1 preHandler

```java
public void preHandler(Configuration jobConfiguration) {
    HandlerUtil.preHandler(jobConfiguration);
}
```

```java
public static void preHandler(Configuration jobConfiguration) {
    LOG.info("================ OssWriter Phase 1 preHandler starting... ================ ");
    Configuration writerOriginPluginConf = jobConfiguration.getConfiguration(
            CoreConstant.DATAX_JOB_CONTENT_WRITER_PARAMETER);
    Configuration writerOssPluginConf = writerOriginPluginConf.getConfiguration(Key.OSS_CONFIG);
    Configuration newWriterPluginConf = Configuration.newDefault();
    jobConfiguration.remove(CoreConstant.DATAX_JOB_CONTENT_WRITER_PARAMETER);
    //将postgresqlwriter的pg配置注入到postgresqlConfig中, 供后面的postHandler使用
    writerOriginPluginConf.remove(Key.OSS_CONFIG);
    newWriterPluginConf.set(Key.POSTGRESQL_CONFIG, writerOriginPluginConf);
    newWriterPluginConf.merge(writerOssPluginConf, true);
    //设置writer的名称为osswriter
    jobConfiguration.set(CoreConstant.DATAX_JOB_CONTENT_WRITER_NAME, "osswriter");
    jobConfiguration.set(CoreConstant.DATAX_JOB_CONTENT_WRITER_PARAMETER, newWriterPluginConf);
    LOG.info("================ OssWriter Phase 1 preHandler end... ================ ");
}
```

### 1.2 init

init: Job对象初始化工作：
```java
public void init() {
    this.writerSliceConfig = this.getPluginJobConf();
    this.basicValidateParameter();
    this.fileFormat = this.writerSliceConfig.getString(
            com.alibaba.datax.plugin.unstructuredstorage.writer.Key.FILE_FORMAT,
            com.alibaba.datax.plugin.unstructuredstorage.writer.Constant.FILE_FORMAT_TEXT);
    this.encoding = this.writerSliceConfig.getString(
            com.alibaba.datax.plugin.unstructuredstorage.writer.Key.ENCODING,
            com.alibaba.datax.plugin.unstructuredstorage.writer.Constant.DEFAULT_ENCODING);
    this.useHdfsWriterProxy  = HdfsParquetUtil.isUseHdfsWriterProxy(this.fileFormat);
    if(useHdfsWriterProxy){
        this.hdfsWriterJob = new HdfsWriter.Job();
        HdfsParquetUtil.adaptConfiguration(this.hdfsWriterJob, this.writerSliceConfig);

        this.hdfsWriterJob.setJobPluginCollector(this.getJobPluginCollector());
        this.hdfsWriterJob.setPeerPluginJobConf(this.getPeerPluginJobConf());
        this.hdfsWriterJob.setPeerPluginName(this.getPeerPluginName());
        this.hdfsWriterJob.setPluginJobConf(this.getPluginJobConf());
        this.hdfsWriterJob.init();
        return;
    }
    this.peerPluginJobConf = this.getPeerPluginJobConf();
    this.isBinaryFile = FileFormat.getFileFormatByConfiguration(this.peerPluginJobConf).isBinary();
    this.syncMode = this.writerSliceConfig
            .getString(com.alibaba.datax.plugin.unstructuredstorage.writer.Key.SYNC_MODE, "");
    this.writeSingleObject = this.writerSliceConfig.getBool(Key.WRITE_SINGLE_OBJECT, false);
    this.header = this.writerSliceConfig
            .getList(com.alibaba.datax.plugin.unstructuredstorage.writer.Key.HEADER, null, String.class);
    this.validateParameter();
    this.ossClient = OssUtil.initOssClient(this.writerSliceConfig);
    this.ossWriterProxy = new OssWriterProxy(this.writerSliceConfig, this.ossClient);
}
```
首先可以通过 `super.getPluginJobConf()` 获取与本插件相关的配置。读插件获得配置中 reader 部分，写插件获得 writer 部分。

读取插件配置之后先要检查基础参数 `endpoint`, `accessId`、`accessKey` 以及 `bucket`


### 1.3 prepare

prepare: 全局准备工作，比如odpswriter清空目标表。

### 1.4 split

split: 拆分Task。参数adviceNumber框架建议的拆分数，一般是运行时所配置的并发度。值返回的是Task的配置列表。

### 1.5 post

post: 全局的后置工作，比如mysqlwriter同步完影子表后的rename操作。



### 1.6 destroy

destroy 完成 Job 对象自身的销毁工作：
```java
public void destroy() {
    if(useHdfsWriterProxy){
        this.hdfsWriterJob.destroy();
        return;
    }
    try {
        // this.ossClient.shutdown();
    } catch (Exception e) {
        LOG.warn("shutdown ossclient meet a exception:" + e.getMessage(), e);
    }
}
```

## 2. Task
