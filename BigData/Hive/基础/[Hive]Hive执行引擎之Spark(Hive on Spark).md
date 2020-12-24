`Hive on Spark`为Hive提供了使用`Apache Spark`作为执行引擎的能力。
```
set hive.execution.engine = spark;
```
`Hive on Spark`可从`Hive 1.1`版本开始使用。 `Hive On Spark`也一直在`spark`和`spark2`分支上开发，并定期合并到`master`分支上。见[HIVE-7292](https://issues.apache.org/jira/browse/HIVE-7292)及其子任务和相关问题。


### 1. Spark安装

按照说明安装Spark：

[YARN模式](http://spark.apache.org/docs/latest/running-on-yarn.html)

[单机模式](https://spark.apache.org/docs/latest/spark-standalone.html)

默认情况下，`Hive on Spark`支持`Spark on YARN`模式。



### 3. Hive配置

#### 3.1 Hive中添加Spark依赖

(1) 在Hive 2.2.0版本之前，将`spark-assembly jar`添加到`HIVE_HOME/lib`中。

(2) 从Hive 2.2.0版本开始，`Hive On Spark`可以在Spark2.0.0版本以及更高版本上运行，并且不需要`spark-assembly jar`(which doesn't have an assembly jar.)

使用YARN模式（无论是`yarn-client`或`yarn-cluster`）运行，需要将以下jar添加到`HIVE_HOME/lib`中：
```
scala-library
spark-core
spark-network-common
```
要使用LOCAL模式运行（仅用于调试），请将除上述之外的以下jar添加到`HIVE_HOME/lib`中：
```
chill-java  chill  jackson-module-paranamer  jackson-module-scala  jersey-container-servlet-core
jersey-server  json4s-ast  kryo-shaded  minlog  scala-xml  spark-launcher
spark-network-shuffle  spark-unsafe  xbean-asm5-shaded

```

#### 3.2 配置Hive执行引擎

配置Hive执行引擎使用Spark：
```
set hive.execution.engine=spark;
```

有关配置Hive和远程Spark驱动程序的其他属性，请参阅[Hive配置属性的Spark部分](https://cwiki.apache.org/confluence/display/Hive/Configuration+Properties#ConfigurationProperties-Spark)。

#### 3.3 配置Hive的Spark-application配置

配置Hive的Spark-application配置，具体请参阅：http：//spark.apache.org/docs/latest/configuration.html。这可以通过将带有这些属性的文件`spark-defaults.conf`添加到Hive classpath上，或者通过在Hive配置`hive-site.xml`上进行设置来完成。 例如：

```
set spark.master=<Spark Master URL>
set spark.eventLog.enabled=true;
set spark.eventLog.dir=<Spark event log folder (must exist)>
set spark.executor.memory=512m;             
set spark.serializer=org.apache.spark.serializer.KryoSerializer;
```


配置项 | 描述
---|---
spark.executor.memory|Amount of memory to use per executor process.
spark.executor.cores|Number of cores per executor.
spark.yarn.executor.memoryOverhead|The amount of off heap memory (in megabytes) to be allocated per executor, when running Spark on Yarn. This is memory that accounts for things like VM overheads, interned strings, other native overheads, etc. In addition to the executor's memory, the container in which the executor is launched needs some extra memory for system processes, and this is what this overhead is for.
spark.executor.instances|The number of executors assigned to each application.
spark.driver.memory|The amount of memory assigned to the Remote Spark Context (RSC). We recommend 4GB.
spark.yarn.driver.memoryOverhead|We recommend 400 (MB).


#### 3.4 

允许Yarn在节点上缓存必需的spark依赖jar，以便每次应用程序运行时不需要分发。

(1) 在Hive 2.2.0版本之前，将`spark-assembly jar`上传到hdfs文件（例如：hdfs://xxxx:8020/spark-assembly.jar），并在hive-site.xml中添加以下内容：
```
<property>
  <name>spark.yarn.jar</name>
  <value>hdfs://xxxx:8020/spark-assembly.jar</value>
</property>
```
(2) Hive 2.2.0版本，将`$SPARK_HOME/jars`中的所有jar上传到hdfs文件夹（例如：hdfs:///xxxx:8020/spark-jars），并在hive-site.xml中添加以下内容

```
<property>
 <name>spark.yarn.jars</name>
 <value>hdfs://xxxx:8020/spark-jars/*</value>
</property>
```


