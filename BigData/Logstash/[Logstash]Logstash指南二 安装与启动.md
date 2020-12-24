---
layout: post
author: sjf0115
title: Lagstash 安装与启动
date: 2017-10-13 13:15:00
tags:
  - Logstash

categories: Logstash
permalink: logstash-setup-and-start
---

> Logstash需要Java 8。不支持Java 9。

使用如下命令检查Java版本:
```
java -version
```
在安装Java的系统上，此命令产生类似于以下内容的输出：
```
java version "1.8.0_91"
Java(TM) SE Runtime Environment (build 1.8.0_91-b14)
Java HotSpot(TM) 64-Bit Server VM (build 25.91-b14, mixed mode)
```
在某些Linux系统上，可能还需要在安装之前配置环境变量，尤其是从tarball中安装Java:
```
export JAVA_HOME=/home/xiaosi/opt/jdk-1.8.0(你安装的路径)
```
这是因为Logstash在安装过程中使用Java来自动检测环境并安装正确的启动方法（SysV init脚本，Upstart或systemd）。 如果Logstash在程序包安装时无法找到`JAVA_HOME`环境变量，可能会收到错误消息，Logstash将无法正常启动。

### 1. 下载

#### 1.1 二进制文件安装

下载与您的主机环境相匹配的[Logstash安装文件](https://www.elastic.co/downloads/logstash)。解压文件。 不要将Logstash安装到包含冒号`:`字符的目录路径中。

在支持的Linux操作系统上，您可以使用软件包管理器来安装Logstash。

#### 1.2 从包存储库安装

我们还有可用于APT和YUM的发行版的存储库。请注意，作为Logstash构建的一部分，我们只提供二进制包，但不包含源包(Note that we only provide binary packages, but no source packages, as the packages are created as part of the Logstash build.)。

我们已将Logstash软件包存储库按版本拆分为单独的URL，以避免主要版本之间的意外升级。对于所有5.x.y版本，使用5.x作为版本号。

我们使用PGP密钥D88E42B4，弹性签名密钥，带指纹
```
4609 5ACC 8548 582C 1A26 99A9 D27D 666C D88E 42B4
```
##### 2.1 APT

下载并安装公开登录密钥：
```
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
```
在继续执行之前，您可能需要在Debian上安装apt-transport-https软件包：
```
sudo apt-get install apt-transport-https
```
### 2. 准备logstash.conf文件
