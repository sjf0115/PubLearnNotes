---
layout: post
author: smartsi
title: Kafka 监控工具之 CMAK
date: 2020-10-17 16:04:01
tags:
  - Kafka

categories: Kafka
permalink: cmak-managing-apache-kafka-cluster
---

### 1. 概述

CMAK(Cluster Manager for Apache Kafka) 是由 Yahoo 开源的 Kafka 集群管理平台。我们可能听到更多的是 kafka-manager。主要是因为[误用了 Apache 的商标](https://github.com/yahoo/CMAK/issues/713)，所以才从 kafka-manager 改名为 CMAK。

在 3.0.0.2 版本之前，kafka-manager 是不提供现成的编译包的，需要我们自己编译打包，老版本的安装可以参阅博文 [Kafka 监控工具之Kafka Manager](http://smartsi.club/use-kafka-manager-to-manage-kafka.html)。在 3.0.0.2 版本之后我们可以直接下载编译后的 zip 包：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/cmak-managing-apache-kafka-cluster-5.jpg?raw=true)

### 2. 下载

CMAK 环境要求：
- Kafka 0.8+
- Java 11+
- Zookeeper 3.5+

官方文档中没有明确说明 ZooKeeper 的版本要求，但是在实际实践中小于 3.5 版本会抛出异常。如果你不想升级你的 ZooKeeper 版本，你可以使用 CMAK 的旧版本 Kafka-manager，比如 1.3.3.23 版本。

由于我机器上只安装了 JDK 8，所以需要再安装一个 [JDK 11](https://www.oracle.com/java/technologies/javase-jdk11-downloads.html)：
```
sudo tar -zxvf jdk-11.0.8_osx-x64_bin.tar.gz -C /opt/
ln -s jdk-11.0.8.jdk/ jdk-11
```
> JDK11 只为CMAK使用，其他还是使用 JDK 8。

这里 CMAK 以 3.0.0.5 版本为例：
```
wget https://github.com/yahoo/CMAK/releases/download/3.0.0.5/cmak-3.0.0.5.zip
```
解压安装包：
```
unzip cmak-3.0.0.5.zip
```
创建软连接便于升级：
```
ln -s cmak-3.0.0.5/ cmak
```

### 3. 配置

修改 `/etc/profile` 配置环境变量，添加如下配置：
```
# kafka manager
export CMAK_HOME=/opt/cmak
export PATH=${CMAK_HOME}/bin:$PATH
```
运行命令 `source /etc/profile` 使环境变量生效。

按如下方式修改配置文件 application.conf，修改ZooKeeper服务器地址：
```
cmak.zkhosts="127.0.0.1:2181,127.0.0.1:2181:2182,127.0.0.1:2181:2183"
```
> 由于我们的ZooKeeper集群是伪分布式模式，通过不同的端口号来模拟不同的服务器。如果是正常集群模式应为 cmak.zkhosts="host1:2181,host2:2181,host3:2181...."。

### 4. 启动

默认使用 9000 端口，如果端口占用，可以通过参数指定端口：
```
cmak -Dconfig.file=/opt/cmak/conf/application.conf -Dhttp.port=9000 -java-home /opt/jdk-11/Contents/Home
```
参数解释：
- -Dconfig.file：指明 CMAK 配置文件路径
- -Dhttp.port：Web监听端口，默认9000端口
- -java-home：指定 JDK 路径，也可以不指定。这里由于需要用 JDK11，而我这台服务器上也安装了 JDK8，所以需要指定 JDK11 的路径。

启动 CMAK 服务后，通过 `http://localhost:9000/` 地址进入 WEB UI 界面：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/cmak-managing-apache-kafka-cluster-4.jpg?raw=true)

可以通过 `Add Cluster` 菜单创建我们的 Kafka 集群：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/cmak-managing-apache-kafka-cluster-1.jpg?raw=true)

注意的的是 Cluster Zookeeper Hosts 要配置 Kafka 在 ZooKeeper 中的 NameSpace，在这我们是 `kafka`，具体取决于 Kafka 的配置：
```
zookeeper.connect=localhost:2181/kafka
```
看到如下页面表示我们已经创建好集群了：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/cmak-managing-apache-kafka-cluster-2.jpg?raw=true)

如果你遇到报如下错误：
```
Yikes! KeeperErrorCode = Unimplemented for /kafka-manager/mutex Try again.
```
那么你需要升级 Zookeeper 到 3.5+ 版本。

创建成功后，你就可以看到你的 Kafka 信息：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/cmak-managing-apache-kafka-cluster-3.jpg?raw=true)

参考：
- [CMAK](https://github.com/yahoo/CMAK)
