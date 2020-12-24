
如果计划将 Flink 与 Hadoop 一起使用（在 YARN 上运行 Flink，连接到 HDFS，HBase，或使用一些基于 Hadoop 的文件系统连接器），需要下载捆绑对应 Hadoop 版本的下载包，下载可选的 Pre -bundled Hadoop 匹配你的版本并将其放在 Flink 的 lib 文件夹中，或 Export HADOOP_CLASSPATH。

https://flink.apache.org/downloads.html


在启动 Flink 组件（如Client，JobManager或TaskManager）之前，需要使用环境变量 HADOOP_CLASSPATH 来配置 classpath。大多数 Hadoop 发行版和云环境在默认情况下都不会设置此变量，因此如果 Flink 选择 Hadoop 类路径，则必须在运行Flink组件的所有计算机上导出环境变量。

在 YARN 上运行时，这通常不是问题，因为在 YARN 中运行的组件将使用 Hadoop 类路径启动，但是在向 YARN 提交作业时，Hadoop 依赖项必须位于类路径中。为此，通常就足够了。
```
export HADOOP_CLASSPATH=`hadoop classpath`
```
