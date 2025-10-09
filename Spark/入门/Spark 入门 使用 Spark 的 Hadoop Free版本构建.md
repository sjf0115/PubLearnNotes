Spark 为 HDFS 和 YARN 使用 Hadoop 客户端库。从 Spark 1.4 版本开始，该项目打包了 Hadoop free 构建包，使您可以更轻松地将不同 Spark 二进制文件与任何 Hadoop 版本集成。要使用这些构建包，您需要修改 `SPARK_DIST_CLASSPATH` 以包含 Hadoop 的包jar。最方便的方法是在 `conf/spark-env.sh` 中添加一个条目。

本文介绍在不同类型的发行版中 Spark如何与 Hadoop 集成。

## 1. Apache Hadoop

对于Apache发行版，您可以使用Hadoop的 `classpath` 命令。例如:
```
### in conf/spark-env.sh ###

# If 'hadoop' binary is on your PATH
export SPARK_DIST_CLASSPATH=$(hadoop classpath)

# With explicit path to 'hadoop' binary
export SPARK_DIST_CLASSPATH=$(/path/to/hadoop/bin/hadoop classpath)

# Passing a Hadoop configuration directory
export SPARK_DIST_CLASSPATH=$(hadoop --config /path/to/configs classpath)
```
## 2. Hadoop Free Build Setup for Spark on Kubernetes

要在 Kubernetes 上运行 Spark 的 Hadoop Free 版本，Executor Image 必须具有合适的 Hadoop 二进制文件版本和正确的 `SPARK_DIST_CLASSPATH` 值设置。查看下面的示例，查看 executor Dockerfile 中需要进行的相关更改：
```
### Set environment variables in the executor dockerfile ###

ENV SPARK_HOME="/opt/spark"  
ENV HADOOP_HOME="/opt/hadoop"  
ENV PATH="$SPARK_HOME/bin:$HADOOP_HOME/bin:$PATH"  
...  

#Copy your target hadoop binaries to the executor hadoop home   

COPY /opt/hadoop3  $HADOOP_HOME  
...

#Copy and use the Spark provided entrypoint.sh. It sets your SPARK_DIST_CLASSPATH using the hadoop binary in $HADOOP_HOME and starts the executor. If you choose to customize the value of SPARK_DIST_CLASSPATH here, the value will be retained in entrypoint.sh

ENTRYPOINT [ "/opt/entrypoint.sh" ]
...  
```
