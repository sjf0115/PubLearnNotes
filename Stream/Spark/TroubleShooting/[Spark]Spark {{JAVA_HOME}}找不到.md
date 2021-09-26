---
layout: post
author: sjf0115
title: Spark Spark {{JAVA_HOME}}找不到
date: 2018-05-23 15:03:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-java-home-no-such-file
---


在 Yarn 上使用 Spark，以 cluster 模式运行：
```
sudo -uxiaosi spark-submit \
    --class com.sjf.example.sql.SparkHiveExample \
    --master yarn \
    --deploy-mode cluster \
    --driver-memory 10g \
    --executor-memory 12g \
    --num-executors 20 \
    --executor-cores 2 \
    --queue xiaosi \
    --conf spark.driver.extraJavaOptions="-XX:MaxPermSize=6144m -XX:PermSize=1024m" \
   ${baseDir}/${jarDir}
```
出现了以下异常：
```
Application application_1504162679223_27868973 failed 2 times due to AM Container for appattempt_1504162679223_27868973_000002 exited with exitCode: 127 due to: Exception from container-launch: org.apache.hadoop.util.Shell$ExitCodeException:
org.apache.hadoop.util.Shell$ExitCodeException:
at org.apache.hadoop.util.Shell.runCommand(Shell.java:464)
at org.apache.hadoop.util.Shell.run(Shell.java:379)
at org.apache.hadoop.util.Shell$ShellCommandExecutor.execute(Shell.java:589)
at org.apache.hadoop.yarn.server.nodemanager.DefaultContainerExecutor.launchContainer(DefaultContainerExecutor.java:200)
at org.apache.hadoop.yarn.server.nodemanager.containermanager.launcher.ContainerLaunch.call(ContainerLaunch.java:283)
at org.apache.hadoop.yarn.server.nodemanager.containermanager.launcher.ContainerLaunch.call(ContainerLaunch.java:79)
at java.util.concurrent.FutureTask.run(FutureTask.java:266)
at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1142)
at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:617)
at java.lang.Thread.run(Thread.java:745)
.Failing this attempt.. Failing the application.
```
而且 ApplicationMaster 所在机器的日志里面有下面的信息提示：
```
/bin/bash: {{JAVA_HOME}}/bin/java: No such file or directory
```
发现换一台机器提交作业就没有问题，怀疑是版本的问题，经过对比，原来是我编译Spark所使用的Hadoop版本和线上Hadoop版本不一致导致的，当前使用Hadoop版本是`2.7`，而线上是使用的`2.2`。后来使用线上Hadoop版本重新编译了Spark，这个问题就解决了。
