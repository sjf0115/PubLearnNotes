


如果您对作业进行了修改，且希望修改生效，则需要先上线，然后停止再启动。另外，如果作业无法复用 State，希望作业全新启动时，也需要停止后再启动作业。本文为您介绍如何优雅的停止作业。






## 1. 取消作业



第一种方式可以通过 `cancel` 命令来取消作业：
```
Syntax: cancel [OPTIONS] <Job ID>
  "cancel" action options:
     -s,--withSavepoint <targetDirectory>   **DEPRECATION WARNING**: Cancelling
                                            a job with savepoint is deprecated.
                                            Use "stop" instead.
                                            Trigger savepoint and cancel job.
                                            The target directory is optional. If
                                            no directory is specified, the
                                            configured default directory
                                            (state.savepoints.dir) is used.
```



```
$ ./bin/flink cancel $JOB_ID . $
```

```
Cancelling job cca7bc1061d61cf15238e92312c2fc20.
Cancelled job cca7bc1061d61cf15238e92312c2fc20.
```

相应的作业状态将从'运行'转换为'取消'。任何计算都将停止。

`--withSavepoint` 标志允许创建一个保存点作为作业取消的一部分。此功能已弃用。使用 stop 操作代替。


## 停止前创建一次快照

停止作业的一个操作是 `stop`:
```shell
Action "stop" stops a running program with a savepoint (streaming jobs only).

  Syntax: stop [OPTIONS] <Job ID>
  "stop" action options:
     -d,--drain                           Send MAX_WATERMARK before taking the
                                          savepoint and stopping the pipelne.
     -p,--savepointPath <savepointPath>   Path to the savepoint (for example
                                          hdfs:///flink/savepoint-1537). If no
                                          directory is specified, the configured
                                          default will be used
                                          ("state.savepoints.dir").                                            
```


当从数据源流停止消费数据时，这是一种更优雅的停止正在运行的流作业的方式。当用户请求停止作业时，所有的数据源请求发送最后一个检查点 Barrier，这将会触发生成保存点。并且在成功完成该保存点之后，将通过调用 `cancel()` 方法来完成作业的停止。

```
$ ./bin/flink stop \
      --savepointPath /tmp/flink-savepoints \
      $JOB_ID
```

```
Suspending job "cca7bc1061d61cf15238e92312c2fc20" with a savepoint.
Savepoint completed. Path: file:/tmp/flink-savepoints/savepoint-cca7bc-bb1e257f0dab
```

需要注意的是如果没有设置 `execution.checkpointing.savepoint-dir` 配置，我们必须使用 `--savepointPath` 参数来指定执行检查点时生成保存点的路径。

如果指定了 `--drain` 选项，那么将在最后一个检查点 Barrier 发出之前，输出 `MAX_WATERMARK`。这将触发所有注册的事件时间计时器，从而刷写正在等待特定 Watermark 的任何状态，例如窗口中的状态，即 `--drain` 参数会导致窗口提前触发(可能导致与预期不符合的结果)。作业将会继续运行，直到所有数据源正确关闭。这允许作业完成对所有正在处理中的数据的处理。

> 如果要永久停止作业，可以使用 `--drain` 选项。如果您希望在稍后的某个时间点再次恢复作业，那么不要使用该选项，因为在恢复作业时可能会导致预期不符合或者不正确的结果。


```java
protected void stop(String[] args) throws Exception {
    // 解析参数
    final Options commandOptions = CliFrontendParser.getStopCommandOptions();
    final CommandLine commandLine = getCommandLine(commandOptions, args, false);
    final StopOptions stopOptions = new StopOptions(commandLine);
    final String[] cleanedArgs = stopOptions.getArgs();

    // 对应 jobId 参数
    final JobID jobId =
            cleanedArgs.length != 0
                    ? parseJobId(cleanedArgs[0])
                    : parseJobId(stopOptions.getTargetDirectory());
    // 对应 -p,--savepointPath 参数
    final String targetDirectory =
            stopOptions.hasSavepointFlag() && cleanedArgs.length > 0
                    ? stopOptions.getTargetDirectory()
                    : null; // the default savepoint location is going to be used in this case.
    // 对应 -d,--drain 参数
    final boolean advanceToEndOfEventTime = stopOptions.shouldAdvanceToEndOfEventTime();

    final CustomCommandLine activeCommandLine = validateAndGetActiveCommandLine(commandLine);
    runClusterAction(
            activeCommandLine,
            commandLine,
            clusterClient -> {
                final String savepointPath;
                try {
                    savepointPath =
                            clusterClient
                                    .stopWithSavepoint(
                                            jobId, advanceToEndOfEventTime, targetDirectory)
                                    .get(clientTimeout.toMillis(), TimeUnit.MILLISECONDS);
                } catch (Exception e) {
                    throw new FlinkException(
                            "Could not stop with a savepoint job \"" + jobId + "\".", e);
                }
                logAndSysout("Savepoint completed. Path: " + savepointPath);
            });
}
```

### 2.1 Suspending job

### 2.2 Draining job


## 3. 区别

取消和停止一个作业的区别如下：
- 调用取消作业时，作业中的算子立即收到一个调用`cancel()`方法的指令以尽快取消它们。如果算子在调用取消操作后没有停止，`Flink` 将定期开启中断线程来取消作业直到作业停止。
- 停止作业是一种停止正在运行的流作业的更加优雅的方法。停止仅适用于使用实现`StoppableFunction`接口的数据源的那些作业。当用户请求停止作业时，所有数据源将收到调用`stop()`方法指令。但是作业还是会继续运行，直到所有数据源正确关闭。这允许作业处理完所有正在传输的数据(inflight data)。
