## 1. 问题

> Hive 版本：3.1.3
> Hadoop 版本：3.2.1

执行 `schematool -initSchema -dbType mysql --verbose` 命令初始化时遇到如下异常：

```java
192:bin smartsi$ schematool -initSchema -dbType mysql --verbose
SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/opt/workspace/apache-hive-3.1.3-bin/lib/log4j-slf4j-impl-2.17.1.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/opt/workspace/hadoop-3.2.1/share/hadoop/common/lib/slf4j-log4j12-1.7.25.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]
Exception in thread "main" java.lang.NoSuchMethodError: com.google.common.base.Preconditions.checkArgument(ZLjava/lang/String;Ljava/lang/Object;)V
	at org.apache.hadoop.conf.Configuration.set(Configuration.java:1357)
	at org.apache.hadoop.conf.Configuration.set(Configuration.java:1338)
	at org.apache.hadoop.mapred.JobConf.setJar(JobConf.java:536)
	at org.apache.hadoop.mapred.JobConf.setJarByClass(JobConf.java:554)
	at org.apache.hadoop.mapred.JobConf.<init>(JobConf.java:448)
	at org.apache.hadoop.hive.conf.HiveConf.initialize(HiveConf.java:5144)
	at org.apache.hadoop.hive.conf.HiveConf.<init>(HiveConf.java:5107)
	at org.apache.hive.beeline.HiveSchemaTool.<init>(HiveSchemaTool.java:96)
	at org.apache.hive.beeline.HiveSchemaTool.main(HiveSchemaTool.java:1473)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at org.apache.hadoop.util.RunJar.run(RunJar.java:323)
	at org.apache.hadoop.util.RunJar.main(RunJar.java:236)
```

这个错误表明在运行时找不到 `com.google.common.base.Preconditions.checkArgument` 方法的实现。

## 2. 分析

`com.google.common.base.Preconditions.checkArgument` 是 Guava 库下的一个方法。`NoSuchMethodError` 通常是由于类路径中存在同一个库的多个版本，而 JVM 加载了不兼容的版本导致的。

查找 Hadoop 的 Guava 包:
```bash
192:workspace smartsi$ find /opt/workspace/hadoop-3.2.1 -name "guava*.jar"
/opt/workspace/hadoop-3.2.1/share/hadoop/common/lib/guava-27.0-jre.jar
/opt/workspace/hadoop-3.2.1/share/hadoop/hdfs/lib/guava-27.0-jre.jar
```
查找 Hive 中的 Guava 包:
```bash
192:workspace smartsi$ find /opt/workspace/apache-hive-3.1.3-bin/ -name "guava*.jar"
/opt/workspace/apache-hive-3.1.3-bin//lib/guava-19.0.jar
```

在这出现 `NoSuchMethodError` 异常是因为：
- Hive 3.1.3 依赖了 Guava 19.0 版本
- Hadoop 3.2.1 依赖了 Guava 27.0 版本，但版本与 Hive 不兼容

## 3. 解决方案

解决方案是统一 Guava 版本，使用 Hadoop 中版本 Guava 库：
- 删除 Hive 的 `lib` 路径下的 `guava-19.0.jar`
- 将 Hadoop 中 `share/hadoop/common/lib` 路径下的 `guava-27.0-jre.jar` 复制到 Hive 的 `lib` 下

执行如下命令统一 Guava 版本：
```bash
# 1. 备份原有jar包
mv /opt/workspace/hive/lib/guava-*.jar /tmp/
# 2. 复制 Hadoop 的 Guava jar 到 Hive 的 lib 目录
cp /opt/workspace/hadoop/share/hadoop/common/lib/guava-*.jar /opt/workspace/hive/lib/
```

执行如下命令验证问题是否解决：
```bash
schematool -initSchema -dbType mysql --verbose
```
如果一切正常，应该能看到 Schema 初始化成功的消息，而不再有 Guava 相关的错误。
