## 1. 问题

在运行 Hive SQL 程序时抛出异常，查看 YARN 的 resourcemanager 日志发现如下异常：
```java
2024-06-09 19:09:36,268 INFO org.apache.hadoop.yarn.server.resourcemanager.rmapp.RMAppImpl: Application application_1717931052858_0002 failed 2 times due to AM Container for appattempt_1717931052858_0002_000002 exited with  exitCode: 1
Failing this attempt.Diagnostics: [2024-06-09 19:09:36.249]Exception from container-launch.
Container id: container_1717931052858_0002_02_000001
Exit code: 1

[2024-06-09 19:09:36.250]Container exited with a non-zero exit code 1. Error file: prelaunch.err.
Last 4096 bytes of prelaunch.err :
Last 4096 bytes of stderr :
错误: 找不到或无法加载主类 org.apache.hadoop.mapreduce.v2.app.MRAppMaster


[2024-06-09 19:09:36.250]Container exited with a non-zero exit code 1. Error file: prelaunch.err.
Last 4096 bytes of prelaunch.err :
Last 4096 bytes of stderr :
错误: 找不到或无法加载主类 org.apache.hadoop.mapreduce.v2.app.MRAppMaster


For more detailed output, check the application tracking page: http://localhost:8088/cluster/app/application_1717931052858_0002 Then click on links to logs of each attempt.
. Failing the application.
```

## 2. 解决方案

这个错误通常发生在使用 Hadoop 启动 MapReduce 作业时。它表示 Hadoop 无法找到或加载用于作业的主类 `org.apache.hadoop.mapreduce.v2.app.MRAppMaster`。一般是类路径（Classpath）设置不正确，导致 Hadoop 无法找到相应的类。在 Hadoop 的配置文件 `mapred-site.xml` 中，`mapreduce.application.classpath` 项的作用是指定 MapReduce 作业在运行时查找所需 Java 类的 classpath。查看配置文件中 `mapreduce.application.classpath` 项发现确实配置有问题。那如何配置 `mapreduce.application.classpath` 项呢？通常会被设置为包含 Hadoop 核心库和常用的第三方库路径的表达式，确保 JVM 启动 MapReduce 作业时能加载到必要的类。可以通过执行 `hadoop classpath` 命令查看具体的 classpath：
```
(base) localhost:hadoop wy$ hadoop classpath
/opt/hadoop-2.10.1/etc/hadoop:/opt/hadoop-2.10.1/share/hadoop/common/lib/*:/opt/hadoop-2.10.1/share/hadoop/common/*:/opt/hadoop-2.10.1/share/hadoop/hdfs:/opt/hadoop-2.10.1/share/hadoop/hdfs/lib/*:/opt/hadoop-2.10.1/share/hadoop/hdfs/*:/opt/hadoop-2.10.1/share/hadoop/yarn:/opt/hadoop-2.10.1/share/hadoop/yarn/lib/*:/opt/hadoop-2.10.1/share/hadoop/yarn/*:/opt/hadoop-2.10.1/share/hadoop/mapreduce/lib/*:/opt/hadoop-2.10.1/share/hadoop/mapreduce/*:/opt/hadoop-2.10.1/etc/hadoop:/opt/hadoop-2.10.1/share/hadoop/common/lib/*:/opt/hadoop-2.10.1/share/hadoop/common/*:/opt/hadoop-2.10.1/share/hadoop/hdfs:/opt/hadoop-2.10.1/share/hadoop/hdfs/lib/*:/opt/hadoop-2.10.1/share/hadoop/hdfs/*:/opt/hadoop-2.10.1/share/hadoop/yarn:/opt/hadoop-2.10.1/share/hadoop/yarn/lib/*:/opt/hadoop-2.10.1/share/hadoop/yarn/*:/opt/hadoop-2.10.1/share/hadoop/mapreduce/lib/*:/opt/hadoop-2.10.1/share/hadoop/mapreduce/*:/opt/hadoop/contrib/capacity-scheduler/*.jar:/opt/hadoop/contrib/capacity-scheduler/*.jar
```
然后将 `mapreduce.application.classpath` 项修改为上述 classpath 如下所示：
```xml
<property>
    <name>mapreduce.application.classpath</name>
    <value>$HADOOP_HOME/etc/hadoop:$HADOOP_HOME/share/hadoop/common/lib/*:$HADOOP_HOME/share/hadoop/common/*:$HADOOP_HOME/share/hadoop/hdfs:$HADOOP_HOME/share/hadoop/hdfs/lib/*:$HADOOP_HOME/share/hadoop/hdfs/*:$HADOOP_HOME/share/hadoop/yarn:$HADOOP_HOME/share/hadoop/yarn/lib/*:$HADOOP_HOME/share/hadoop/yarn/*:$HADOOP_HOME/share/hadoop/mapreduce/lib/*:$HADOOP_HOME/share/hadoop/mapreduce/*:$HADOOP_HOME/etc/hadoop:$HADOOP_HOME/share/hadoop/common/lib/*:$HADOOP_HOME/share/hadoop/common/*:$HADOOP_HOME/share/hadoop/hdfs:$HADOOP_HOME/share/hadoop/hdfs/lib/*:$HADOOP_HOME/share/hadoop/hdfs/*:$HADOOP_HOME/share/hadoop/yarn:$HADOOP_HOME/share/hadoop/yarn/lib/*:$HADOOP_HOME/share/hadoop/yarn/*:$HADOOP_HOME/share/hadoop/mapreduce/lib/*:$HADOOP_HOME/share/hadoop/mapreduce/*:/opt/hadoop/contrib/capacity-scheduler/*.jar:/opt/hadoop/contrib/capacity-scheduler/*.jar</value>
</property>
```

> 需要注意的是修改classpath时，要确保新增加的路径不会引起类冲突或覆盖已有的类定义。在大型集群中，确保所有节点的 Hadoop 配置同步，以防止运行时故障。

设置完毕后重启 Hadoop 集群，重新运行刚才的 MapReduce 程序，成功运行。
