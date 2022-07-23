### 1. 使用

我们先看一下在MapReduce程序中如何使用Job类的：在main函数通过`getInstance(conf)`方法创建Job类，并给Job实例设置相应的参数，最终调用waitForCompletion函数来执行Job。

```
String inputPath = args[0];
String outputPath = args[1];

// 创建新作业Job
Job job = Job.getInstance();

// 指定各种作业特定参数
job.setJarByClass(MaxTemperature.class);
job.setMapperClass(MaxTemperatureMapper.class);
job.setReducerClass(MaxTemperatureReducer.class);

job.setMapOutputKeyClass(Text.class);
job.setMapOutputValueClass(IntWritable.class);
job.setOutputKeyClass(Text.class);
job.setOutputValueClass(IntWritable.class);

FileInputFormat.addInputPath(job, new Path(inputPath));
FileOutputFormat.setOutputPath(job, new Path(outputPath));

// 提交作业，然后轮询进度，直到作业完成
boolean success = job.waitForCompletion(true);
return success ? 0 : 1;
```

### 2. 组织关系

![image](http://img.blog.csdn.net/20170607194251611?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

Job类继承了`JobContextImpl`类，并实现了`JobContext`接口。`JobContextImpl`本身又是`JobContext`接口的一个简单实现，给Job类中的相关方法提供了一系列方法的默认实现(基本都是get方法)。

下面列举一部分方法：
```
getConfiguration()
getJobID()
setJobID(JobID jobId)
getJobName()
getNumReduceTasks()
getOutputKeyClass()
getOutputValueClass()
getMapOutputKeyClass()
getMapOutputValueClass()
getInputFormatClass()
getOutputFormatClass()
getMapperClass()
getReducerClass()
getJar()
```


### 3. 构造函数

```
Job()
Job(Configuration conf)
Job(Configuration conf, String jobName)
```
上面三个构造函数已经废弃，相应的由下面三个构造函数代替：
```
getInstance()
getInstance(Configuration)
getInstance(Configuration, String)
```
另外还有一个构造函数：
```
getInstance(JobStatus, Configuration)
```

#### 3.1 getInstance()

创建一个新的没有指定群集的作业`Job`。将使用通用配置创建集群。
```
public static Job getInstance() throws IOException {
    return getInstance(new Configuration());
}
```
该构造函数调用`getInstance(conf)`构造函数．

#### 3.2 getInstance(Configuration)

根据给定的配置创建一个新的没有指定集群的作业．`Job`创建配置的副本，以便任何必要的内部修改(necessary internal modifications)不会影响输入参数(incoming parameter)。 只有在需要时，才能根据conf参数创建集群。

```
public static Job getInstance(Configuration conf) throws IOException {
    JobConf jobConf = new JobConf(conf);
    return new Job(jobConf);
}
```
根据给定的配置`conf`创建JobConf对象，调用内部构造函数创建作业`Job`．
```
Job(JobConf conf) throws IOException {
    super(conf, null);
    this.credentials.mergeAll(this.ugi.getCredentials());
    this.cluster = null;
}
```

#### 3.3 getInstance(Configuration, String)

这个构造函数与上面的构造函数基本一致，增加给定JobName．

```
public static Job getInstance(Configuration conf, String jobName) throws IOException {
    Job result = getInstance(conf);
    result.setJobName(jobName);
    return result;
}
```
创建好Job之后，根据给定的作业名称，通过`setJobName`方法设置作业名称．

#### 3.4 getInstance(JobStatus, Configuration)

根据给定的配置和作业状态`JobStatus`创建一个新的没有指定集群的作业．

```
public static Job getInstance(JobStatus status, Configuration conf) throws IOException {
    return new Job(status, new JobConf(conf));
}
```
调用内部构造函数创建作业`Job`，设置作业ID以及状态:
```
Job(JobStatus status, JobConf conf) throws IOException {
    this(conf);
    setJobID(status.getJobID());
    this.status = status;
    state = JobState.RUNNING;
}
```
### 4. 方法

#### 4.1 检查状态JobState

一个Job对象有两种状态(DEFINE和RUNNING)，Job对象被创建时的状态为`DEFINE`．当且仅当Job对象处于`DEFINE`状态时，才可以设置作业的一些配置，如Reduce　task的个数，InputFormat类等等．当作业提交之后，Job对象的状态改为`RUNNING`，作业处于调度运行阶段，这时不能给配置进行修改．

Job对象状态默认设置为`DEFINE`：
```
private JobState state = JobState.DEFINE;
```
Job对象状态检查：
```
private void ensureState(JobState state) throws IllegalStateException {
    if (state != this.state) {
      throw new IllegalStateException("Job in state "+ this.state +
                                      " instead of " + state);
    }

    if (state == JobState.RUNNING && cluster == null) {
      throw new IllegalStateException
        ("Job in state " + this.state
         + ", but it isn't attached to any job tracker!");
    }
}
```
如果与当前的Job对象状态`state`不一致，会抛异常；如果Job对象状态为`RUNNING`，但是没有指定集群也会抛出异常；

Set方法一般都会调用该方法，来检查Job对象的状态`state`，来判断是否可以设置配置项．

#### 4.2 设置Jar包

通过给定的Java类来寻找所在的Jar包，从而设置运行Jar包

```
public void setJarByClass(Class<?> cls) {
    ensureState(JobState.DEFINE);
    conf.setJarByClass(cls);
}
```
或者给定Jar包所在路径来进行设置：
```
public void setJar(String jar) {
    ensureState(JobState.DEFINE);
    conf.setJar(jar);
}
```

#### 4.3 设置Mapper和Reducer

为Job设置Mapper：
```
public void setMapperClass(Class<? extends Mapper> cls) throws IllegalStateException {
    ensureState(JobState.DEFINE);
    conf.setClass(MAP_CLASS_ATTR, cls, Mapper.class);
}
```
MRJobConfig.MAP_CLASS_ATTR：`mapreduce.job.map.class`

为Job设置Reducer：
```
public void setReducerClass(Class<? extends Reducer> cls) throws IllegalStateException {
    ensureState(JobState.DEFINE);
    conf.setClass(REDUCE_CLASS_ATTR, cls, Reducer.class);
}
```
MRJobConfig.REDUCE_CLASS_ATTR：`mapreduce.job.reduce.class`

#### 4.4 指定Map和Reduce输出键值类型

通过指定类，设置Map输出`key`的数据类型。 这允许用户将Map输出`key`的数据类型不同于最终输出`value`的数据类型(This allows the user to specify the map output key class to be different than the final output value class.)。

```
public void setMapOutputKeyClass(Class<?> theClass) throws IllegalStateException {
    ensureState(JobState.DEFINE);
    conf.setMapOutputKeyClass(theClass);
}
```
通过指定类，设置Map输出`value`的数据类型。 这允许用户将Map输出`value`的数据类型不同于最终输出`value`的数据类型．
```
public void setMapOutputValueClass(Class<?> theClass) throws IllegalStateException {
    ensureState(JobState.DEFINE);
    conf.setMapOutputValueClass(theClass);
}
```
设置作业`Job`输出`key`的数据类型。
```
public void setOutputKeyClass(Class<?> theClass) throws IllegalStateException {
    ensureState(JobState.DEFINE);
    conf.setOutputKeyClass(theClass);
}
```
设置作业`Job`输出`value`的数据类型。
```
public void setOutputValueClass(Class<?> theClass) throws IllegalStateException {
    ensureState(JobState.DEFINE);
    conf.setOutputValueClass(theClass);
}
```

#### 4.5 提交作业等待完成


将作业提交到群集，并等待完成。

```
public boolean waitForCompletion(boolean verbose) throws IOException, InterruptedException, ClassNotFoundException {
    if (state == JobState.DEFINE) {
      submit();
    }
    if (verbose) {
      monitorAndPrintJob();
    } else {
      // get the completion poll interval from the client.
      int completionPollIntervalMillis =
        Job.getCompletionPollInterval(cluster.getConf());
      while (!isComplete()) {
        try {
          Thread.sleep(completionPollIntervalMillis);
        } catch (InterruptedException ie) {
        }
      }
    }
    return isSuccessful();
  }
```
只有当Job对象状态为`DEFINE`时，才能提交作业，执行`submit`函数．boolean变量`verbose`表示是否将进度打印给用户．如果将进度打印给用户，将执行`monitorAndPrintJob`函数，检查Job和Task的运行状况，否则自身进入循环，以一定的时间间隔轮询检查所提交的Job是是否执行完成。如果执行完成，跳出循环，调用isSuccessful()函数返回执行后的状态。

##### 4.5.1 submit

将作业提交到群．

```
public void submit() throws IOException, InterruptedException, ClassNotFoundException {
    ensureState(JobState.DEFINE);
    setUseNewAPI();
    connect();
    final JobSubmitter submitter =
        getJobSubmitter(cluster.getFileSystem(), cluster.getClient());
    status = ugi.doAs(new PrivilegedExceptionAction<JobStatus>() {
      public JobStatus run() throws IOException, InterruptedException,
      ClassNotFoundException {
        return submitter.submitJobInternal(Job.this, cluster);
      }
    });
    state = JobState.RUNNING;
    LOG.info("The url to track the job: " + getTrackingURL());
}
```
首先调用`ensureState`函数判断Job对象状态；


```
private synchronized void connect() throws IOException, InterruptedException, ClassNotFoundException {
    if (cluster == null) {
        cluster = ugi.doAs(new PrivilegedExceptionAction<Cluster>() {
            public Cluster run() throws IOException, InterruptedException, ClassNotFoundException {
                return new Cluster(getConfiguration());
            }
        });
    }
}
```
之后调用JobSubmitter类下的submitJobInternal()函数，获取作业状态．同时设置`JobState`为`Running`，最后直接退出。


==备注==

`UserGroupInformation ugi` Hadoop的用户和组信息。 此类包装JAAS主题，并提供确定用户的用户名和组的方法。


##### 4.5.2 监控打印进度

随着进度和任务的进行，实时监控作业和打印状态．

```
public boolean monitorAndPrintJob()
      throws IOException, InterruptedException {
    String lastReport = null;
    Job.TaskStatusFilter filter;
    Configuration clientConf = getConfiguration();
    filter = Job.getTaskOutputFilter(clientConf);
    JobID jobId = getJobID();
    LOG.info("Running job: " + jobId);
    int eventCounter = 0;
    boolean profiling = getProfileEnabled();
    IntegerRanges mapRanges = getProfileTaskRange(true);
    IntegerRanges reduceRanges = getProfileTaskRange(false);
    int progMonitorPollIntervalMillis =
      Job.getProgressPollInterval(clientConf);
    /* make sure to report full progress after the job is done */
    boolean reportedAfterCompletion = false;
    boolean reportedUberMode = false;
    while (!isComplete() || !reportedAfterCompletion) {
      if (isComplete()) {
        reportedAfterCompletion = true;
      } else {
        Thread.sleep(progMonitorPollIntervalMillis);
      }
      if (status.getState() == JobStatus.State.PREP) {
        continue;
      }      
      if (!reportedUberMode) {
        reportedUberMode = true;
        LOG.info("Job " + jobId + " running in uber mode : " + isUber());
      }      
      String report =
        (" map " + StringUtils.formatPercent(mapProgress(), 0)+
            " reduce " +
            StringUtils.formatPercent(reduceProgress(), 0));
      if (!report.equals(lastReport)) {
        LOG.info(report);
        lastReport = report;
      }

      TaskCompletionEvent[] events =
        getTaskCompletionEvents(eventCounter, 10);
      eventCounter += events.length;
      printTaskEvents(events, filter, profiling, mapRanges, reduceRanges);
    }
    boolean success = isSuccessful();
    if (success) {
      LOG.info("Job " + jobId + " completed successfully");
    } else {
      LOG.info("Job " + jobId + " failed with state " + status.getState() +
          " due to: " + status.getFailureInfo());
    }
    Counters counters = getCounters();
    if (counters != null) {
      LOG.info(counters.toString());
    }
    return success;
}
```

##### 4.5.3 作业是否完成

判断作业是否完成，如果完成则直接退出，返回完成情况，否则一定时间之后再次轮询作业是否完成．
```
public boolean isComplete() throws IOException {
    ensureState(JobState.RUNNING);
    updateStatus();
    return status.isJobComplete();
}
```
调用`updateStatus`函数从集群获取最新的作业状态；只要作业状态为`SUCCEEDED`，`FAILED`，`KILLED`即表示作业执行完成．

##### 4.5.4 作业是否执行成功

判断作业是否执行成功；

```
public boolean isSuccessful() throws IOException {
    ensureState(JobState.RUNNING);
    updateStatus();
    return status.getState() == JobStatus.State.SUCCEEDED;
}
```
调用`updateStatus`函数从集群获取最新的作业状态；只要作业状态为`SUCCEEDED`即表示作业执行完成．

##### 4.5.5 更新作业状态

某些方法需要立即更新状态． 所以，调用此方法立即刷新作业状态．

```
synchronized void updateStatus() throws IOException {
    try {
      this.status = ugi.doAs(new PrivilegedExceptionAction<JobStatus>() {
        @Override
        public JobStatus run() throws IOException, InterruptedException {
          return cluster.getClient().getJobStatus(status.getJobID());
        }
      });
    }
    catch (InterruptedException ie) {
      throw new IOException(ie);
    }
    if (this.status == null) {
      throw new IOException("Job status not available ");
    }
    this.statustime = System.currentTimeMillis();
}
```
根据当作业前状态中的作业ID，从集群中获取最新作业状态．


==备注==

Hadoop版本　2.7.2
