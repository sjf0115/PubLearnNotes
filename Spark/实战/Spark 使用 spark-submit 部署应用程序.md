---
layout: post
author: sjf0115
title: Spark 使用 spark-submit 部署应用程序
date: 2018-04-07 11:28:01
tags:
  - Spark

categories: Spark
permalink: spark-base-launching-applications-with-spark-submit
---

> Spark版本：3.1.3

### 1. 简介

Spark 的 bin 目录下的 spark-submit 脚本用来在集群上启动应用程序。可以通过一个统一的接口使用 Spark 支持的所有[集群管理器](https://spark.apache.org/docs/3.1.3/submitting-applications.html)，这样就不必为每个集群管理器单独配置提交应用程序。

### 2. 语法

```
xiaosi@yoona:~/opt/spark-2.1.0-bin-hadoop2.7$ spark-submit --help
Usage: spark-submit [options] <app jar | python file> [app arguments]
Usage: spark-submit --kill [submission ID] --master [spark://...]
Usage: spark-submit --status [submission ID] --master [spark://...]
Usage: spark-submit run-example [options] example-class [example args]

Options:
  --master MASTER_URL         spark://host:port, mesos://host:port, yarn, or local.
  --deploy-mode DEPLOY_MODE   Whether to launch the driver program locally ("client") or
                              on one of the worker machines inside the cluster ("cluster")
                              (Default: client).
  --class CLASS_NAME          Your application's main class (for Java / Scala apps).
  --name NAME                 A name of your application.
  --jars JARS                 Comma-separated list of local jars to include on the driver
                              and executor classpaths.
  --packages                  Comma-separated list of maven coordinates of jars to include
                              on the driver and executor classpaths. Will search the local
                              maven repo, then maven central and any additional remote
                              repositories given by --repositories. The format for the
                              coordinates should be groupId:artifactId:version.
  --exclude-packages          Comma-separated list of groupId:artifactId, to exclude while
                              resolving the dependencies provided in --packages to avoid
                              dependency conflicts.
  --repositories              Comma-separated list of additional remote repositories to
                              search for the maven coordinates given with --packages.
  --py-files PY_FILES         Comma-separated list of .zip, .egg, or .py files to place
                              on the PYTHONPATH for Python apps.
  --files FILES               Comma-separated list of files to be placed in the working
                              directory of each executor.

  --conf PROP=VALUE           Arbitrary Spark configuration property.
  --properties-file FILE      Path to a file from which to load extra properties. If not
                              specified, this will look for conf/spark-defaults.conf.

  --driver-memory MEM         Memory for driver (e.g. 1000M, 2G) (Default: 1024M).
  --driver-java-options       Extra Java options to pass to the driver.
  --driver-library-path       Extra library path entries to pass to the driver.
  --driver-class-path         Extra class path entries to pass to the driver. Note that
                              jars added with --jars are automatically included in the
                              classpath.

  --executor-memory MEM       Memory per executor (e.g. 1000M, 2G) (Default: 1G).

  --proxy-user NAME           User to impersonate when submitting the application.
                              This argument does not work with --principal / --keytab.

  --help, -h                  Show this help message and exit.
  --verbose, -v               Print additional debug output.
  --version,                  Print the version of current Spark.

 Spark standalone with cluster deploy mode only:
  --driver-cores NUM          Cores for driver (Default: 1).

 Spark standalone or Mesos with cluster deploy mode only:
  --supervise                 If given, restarts the driver on failure.
  --kill SUBMISSION_ID        If given, kills the driver specified.
  --status SUBMISSION_ID      If given, requests the status of the driver specified.

 Spark standalone and Mesos only:
  --total-executor-cores NUM  Total cores for all executors.

 Spark standalone and YARN only:
  --executor-cores NUM        Number of cores per executor. (Default: 1 in YARN mode,
                              or all available cores on the worker in standalone mode)

 YARN-only:
  --driver-cores NUM          Number of cores used by the driver, only in cluster mode
                              (Default: 1).
  --queue QUEUE_NAME          The YARN queue to submit to (Default: "default").
  --num-executors NUM         Number of executors to launch (Default: 2).
                              If dynamic allocation is enabled, the initial number of
                              executors will be at least NUM.
  --archives ARCHIVES         Comma separated list of archives to be extracted into the
                              working directory of each executor.
  --principal PRINCIPAL       Principal to be used to login to KDC, while running on
                              secure HDFS.
  --keytab KEYTAB             The full path to the file that contains the keytab for the
                              principal specified above. This keytab will be copied to
                              the node running the Application Master via the Secure
                              Distributed Cache, for renewing the login tickets and the
                              delegation tokens periodically.
```

### 3. 打包应用依赖

如果你的代码依赖于其他项目，则需要将它们与应用程序一起打包，以便将代码分发到 Spark 集群上。为此，需要创建一个包含代码及其依赖关系的 uber jar，可以将 Spark 和 Hadoop 的依赖设置为 provided。它们不需要打包到 jar 中，因为它们在运行时由集群管理器提供。一旦创建好 jar，就可以调用 bin/spark-submit 脚本来启动应用程序。

对于 Python，你可以使用 spark-submit 脚本的 --py-files 参数来添加 '.py'，'.zip' 或者 '.egg' 文件。如果你依赖于多个 Python 文件，我们建议将它们打包成一个 '.zip' 或 '.egg' 文件。

### 4. 使用 spark-submit 启动应用程序

应用程序打包成功后，就可以使用 bin/spark-submit 脚本启动应用程序。脚本负责设置 Spark 及其依赖的 classpath，并且可以支持不同集群管理器和部署模式，具体语法如下：
```shell
./bin/spark-submit \
  --class <main-class> \
  --master <master-url> \
  --deploy-mode <deploy-mode> \
  --conf <key>=<value> \
  ... # other options
  <application-jar> \
  [application-arguments]
```

下面一起看一些常用的配置参数：
- --class: 应用程序入口，例如：com.sjf.open.spark.Java.JavaWordCount 包含包名的全路径名称
- --master: 集群的 master URL，例如：spark://23.195.26.187:7077
- --deploy-mode: 部署模式
  - cluster 模式：在 Worker 节点上部署 driver
  - client 模式：在本地作为一个外部的客户端部署你的 driver，这是默认的部署方式
- --conf: key=value 格式的 Spark 配置属性。对于包含空格的 value 可以使用双引号包起来，例如，"key=value"。
- application-jar: 包含应用程序以及依赖的 jar 路径。URL 必须在集群内部全局可见，例如，对所有节点可见的 'hdfs://' 路径或者 'file://' 路径。
- application-arguments: 传递给主类 main 方法的参数（如果有的话）

Example:
```shell
bin/spark-submit --class com.sjf.open.spark.Java.JavaWordCount --master local common-tool-jar-with-dependencies.jar /home/xiaosi/click_uv.txt
```

常见的部署策略是在与 Worker 节点机器物理位置相近的 gateway 机器上提交应用程序。这种设置非常适合 client 部署模式。在 client 部署模式中，driver 作为集群的客户端直接在 spark-submit 进程中启动。应用程序的输入和输出直接连到控制台。因此，这个模式特别适合那些涉及 REPL（例如，Spark shell）的应用程序。

如果你的应用程序是在远离 Worker 节点的机器上提交的，例如在你笔记本电脑本地提交，则通常使用 cluster 部署模式来最小化 drivers 和 executors 之间的网络延迟。目前，对于 Python 应用程序而言，在 Standalone 模式上不支持 cluster 部署模式。

有几个可用选项是特定用于集群管理器。例如，对于具有集群部署模式的Spark独立集群，可以指定 `--supervise` 参数以确保如果驱动程序以非零退出码失败时，可以自动重新启动。如果要列举 spark-submit 所有可用选项，可以使用 `spark-submit --help` 命令来查看。以下是常见选项的几个示例：

```
# 在本地运行 8 核
./bin/spark-submit \
  --class org.apache.spark.examples.SparkPi \
  --master local[8] \
  /path/to/examples.jar \
  100

# 以客户端部署模式在Spark独立集群上运行
./bin/spark-submit \
  --class org.apache.spark.examples.SparkPi \
  --master spark://207.184.161.138:7077 \
  --executor-memory 20G \
  --total-executor-cores 100 \
  /path/to/examples.jar \
  1000

# 在集群部署模式下使用supervise在Spark独立集群上运行
./bin/spark-submit \
  --class org.apache.spark.examples.SparkPi \
  --master spark://207.184.161.138:7077 \
  --deploy-mode cluster \
  --supervise \
  --executor-memory 20G \
  --total-executor-cores 100 \
  /path/to/examples.jar \
  1000

# 在 YARN 集群上运行
export HADOOP_CONF_DIR=XXX
./bin/spark-submit \
  --class org.apache.spark.examples.SparkPi \
  --master yarn \
  --deploy-mode cluster \  # can be client for client mode
  --executor-memory 20G \
  --num-executors 50 \
  /path/to/examples.jar \
  1000

# 在 Spark 独立集群上运行Python程序
./bin/spark-submit \
  --master spark://207.184.161.138:7077 \
  examples/src/main/python/pi.py \
  1000

# 在集群部署模式下使用supervise在Mesos集群上运行
./bin/spark-submit \
  --class org.apache.spark.examples.SparkPi \
  --master mesos://207.184.161.138:7077 \
  --deploy-mode cluster \
  --supervise \
  --executor-memory 20G \
  --total-executor-cores 100 \
  http://path/to/examples.jar \
  1000
```

### 5. Master Urls

传递给 Spark 的 master url 可以采用如下格式：

Master URL | 描述
---|---
local | 在本地使用一个 Worker 线程来运行 Spark
`local[K]` | 在本地使用 K 个 Worker 线程来运行 Spark，理想情况下，这个值设置为你机器内核的数量
`local[K,F]`| 在本地使用 K 个 Worker 线程和 F 个 maxFailures 来运行 Spark
`local[*]` | 在本地使用与你机器内核一样多的 Worker 线程来运行 Spark
`local[*,F]`| 在本地使用与你机器内核一样多的 Worker 线程以及 F 个 maxFailures 来运行 Spark
spark://HOST:PORT | 连接到给定的 Spark Standalone 集群的 master。端口必须是 master 配置可使用的端口，默认为 7077
spark://HOST1:PORT1,HOST2:PORT2 | 连接到具有备用 masters 的 Spark Standalone 集群。主机列表必须包含使用 Zookeeper 搭建的高可用集群中的所有 master 主机。端口必须是每个 master 可以配置使用的端口，默认情况下为7077
mesos://HOST:PORT | 连接到给定的 Mesos 集群。端口必须是配置可用的端口，默认为5050；对于使用 ZooKeeper 的 Mesos 集群，可以借助 --deploy-mode cluster 参数使用 mesos://zk:// .... 提交
yarn | 以 client 或者 cluster 部署模式连接到 YARN 集群。可以根据 HADOOP_CONF_DIR 或 YARN_CONF_DIR 变量找到集群位置
k8s://HOST:PORT | 以 client 或者 cluster 部署模式连接到 Kubernetes 集群。HOST 和 PORT 指的是 Kubernetes API 服务器。默认使用 TLS 连接。

### 6. 从文件加载配置

spark-submit 脚本可以从 properties 文件加载默认的 Spark 配置选项，并将它们传递到应用程序。默认情况下，spark 从 spark 目录下的 conf/spark-defaults.conf 配置文件中读取配置选项。有关更多详细信息，请参考[加载默认配置](https://spark.apache.org/docs/3.1.3/configuration.html#loading-default-configurations)。

以这种方式加载 Spark 默认配置可以不用在 spark-submit 上添加配置选项。例如，如果默认配置文件中设置了 spark.master 属性，那么可以在 spark-submit 脚本中省略 --master 参数。一般来说，在 SparkConf 上显式设置的配置选项拥有最高优先级，然后是传递到 spark-submit 的配置选项，最后是默认配置文件中的配置选项。

> 如果不清楚配置选项来自哪里，可以通过使用 --verbose 选项运行 spark-submit 打印出细粒度的调试信息。

### 7. 高级依赖管理

使用 spark-submit 时，需要上传并放到应用 CLASSPATH 中的 Jar 包列表，可以使用参数 --jars 提供。包含在 --jars 选项中的应用程序 jar 以及其他 jar 将会自动分发到集群中。在 --jars 之后提供的 Jar 包列表必须用逗号分隔。需要注意的是 --jars 参数不支持目录。

Spark 使用如下 URL 来以不同策略分发 Jar：
- file：由 driver HTTP 文件服务器提供的绝对路径或者 file:/URI。每个 executor 都可以从 driver HTTP 服务器上拉取文件。
- 'hdfs:', 'http:', 'https:', 'ftp:'：正如你看到的，从这些 URI 拉取文件和 Jar。
- local：以 'local:/' 开头的 URI 应该作为每个 Worker 节点上的本地文件存在。这意味着不会产生网络IO，适用于推送大文件或者 Jar 到每个工作线程或通过 NFS，GlusterFS 等方式共享这些大文件或者 Jar。

请注意，Jar 和文件被复制到 executor 节点上每个 SparkContext 的工作目录下。随着时间的推移，这可能会占用大量的空间，需要定时清理。使用 YARN，清理会自动执行；使用 Spark 独立集群，可以使用 `spark.worker.cleanup.appDataTtl` 属性配置自动清理。

原文: https://spark.apache.org/docs/3.1.3/submitting-applications.html
