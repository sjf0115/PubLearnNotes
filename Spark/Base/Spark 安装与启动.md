---
layout: post
author: sjf0115
title: Spark 安装与启动
date: 2022-03-26 08:54:01
tags:
  - Spark

categories: Spark
permalink: spark-how-to-install-and-run
---

版本：
- Scala 版本：2.12.15
- Spark 版本：3.1.3
- Hadoop 版本：2.7.7

## 1. Scala 安装

我们从官网 https://www.scala-lang.org/download/all.html 下载 2.12.15 版本：

![](https://github.com/sjf0115/ImageBucket/blob/main/Spark/spark-how-to-install-and-run-1.png?raw=true)

解压到 /opt 目录：
```
tar -zxvf scala-2.12.15.tgz -C /opt
```
创建软连接便于升级：
```
ln -s scala-2.12.15/ scala
```
修改 /etc/profile 文件设置环境变量，便于后续操作：
```
# scala
export SCALA_HOME=/opt/scala
export PATH=${SCALA_HOME}/bin:$PATH
```
可以与 scala 进行交互来验证安装是否成功：

![](https://github.com/sjf0115/ImageBucket/blob/main/Spark/spark-how-to-install-and-run-2.png?raw=true)

## 2. Hadoop 安装

如果没有安装 Hadoop，可以参考：[Hadoop 安装与启动](http://smartsi.club/hadoop-setup-and-start.html)。在这我们 Hadoop 版本为 2.7.7 版本。

## 3. Spark 安装

第一步是选择 Spark 版本，在这我们选择的是 3.1.3 (Feb 18 2022) 版本。第二步是选择 Package 类型，官方目前提供了四种类型：
- Pre-built for Apache Hadoop 3.2 and later：基于 Hadoop 3.2 的预先编译版，可以支持 Hadoop 3.2+版本。
- Pre-built for Apache Hadoop 2.7：基于 Hadoop 2.7 的预先编译版，需要与本机安装的 Hadoop 版本对应。
- Pre-built with user-provided Apache Hadoop：'Hadoop free' 版，可使用任意 Hadoop 版本;
- Source Code：Spark 源码，需要编译才能使用;

> Spark 版本选择的不同，提供的 Package 类型也会不一样。

Spark 与 Hadoop 需要配合使用，所以 Spark 必须按照我们目前安装的 Hadoop 版本来选择 Package 类型。如果你事先安装了 Spark 对应版本的 Hadoop，那么可以选择 for Hadoop x.x 类型，如果你安装的 Hadoop 版本没有对应的 Spark，可以选择 Pre-built with user-provided Apache Hadoop 类型。由于我们使用的 Hadoop 版本为 2.7.7 版本，所以可以选择 Pre-built for Apache Hadoop 2.7 类型。

选择 Spark 版本和 Package 类型之后，自动会为你生成 spark-3.1.3-bin-hadoop2.7.tgz 包地址，直接点击下载即可。

![](https://github.com/sjf0115/ImageBucket/blob/main/Spark/spark-how-to-install-and-run-3.png?raw=true)

> Spark 3 通常是使用 Scala 2.12 预先构建，从 Spark 3.2+ 版本开始提供了基于 Scala 2.13 预先构建的发行版。

从官网上下载 spark-3.1.3-bin-hadoop2.7.tgz 后解压到 /opt 目录下：
```
tar -zxvf spark-3.1.3-bin-hadoop2.7.tgz -C /opt
```
为了升级方便，创建软连接：
```
ln -s spark-3.1.3-bin-hadoop2.7/ spark
```
设置环境变量，指向 Spark 目录，便于后续操作：
```
# spark
export SPARK_HOME=/opt/spark
export PATH=${SPARK_HOME}/bin:$PATH
```

需要在 spark-env.sh 中修改 Spark 的 Classpath，执行如下命令拷贝一个配置文件：
```
cd /opt/spark
cp spark-env.sh.template spark-env.sh
```
编辑 spark-env.sh ，在最后面加上如下一行：
```
export SPARK_DIST_CLASSPATH=$(/opt/hadoop/bin/hadoop classpath)
```
> 替换为你的 Hadoop 安装路径

保存后，Spark 就可以启动、运行了。

## 4. 运行示例和 Shell

在 examples/src/main 目录下有一些 Spark 的示例程序，有 Scala、Java、Python 以及 R 等语言的版本。如果要运行 Java 或 Scala 示例程序，可以使用 bin/run-example <class> [params] 命令。在内部会调用更通用的 spark-submit 脚本来启动应用程序。如下所示我们运行一个计算 π 的近似值的示例程序 SparkPi：
```
cd /opt/spark
bin/run-example SparkPi
```
执行时会输出非常多的运行信息，输出结果不容易找到，可以通过 grep 命令进行过滤：
```
localhost:spark wy$ ./bin/run-example SparkPi 2>&1 | grep "Pi is roughly"
Pi is roughly 3.135835679178396
```
你还可以通过 Scala shell 以交互方式运行 Spark：
```
cd /opt/spark
./bin/spark-shell --master local[2]
```
--master 选项可以指定：
- 分布式集群的 master URL，
- local：使用一个线程在本地运行
- local[N]：使用 N 个线程在本地运行

![](https://github.com/sjf0115/ImageBucket/blob/main/Spark/spark-how-to-install-and-run-4.png?raw=true)
