---
layout: post
author: smartsi
title: Hive 如何启动 HiveServer2
date: 2020-09-12 15:15:01
tags:
  - Hive

categories: Hive
permalink: how-to-config-and-start-hiveserver2
---

HiveServer2 是一种可选的 Hive 内置服务，可以允许远程客户端使用不同编程语言向 Hive 提交请求并返回结果。HiveServer2 是 HiveServer1 的改进版，主要解决了无法处理来自多个客户端的并发请求以及身份验证问题。具体可以参阅 [Hive 一起了解一下 HiveServer2](https://smartsi.blog.csdn.net/article/details/75322177)。下面我们具体看一下如何配置 HiveServer2。

### 1. Thrift 服务配置

假设我们已经成功安装了 Hive，如果没有安装，可以参阅 [Hive 安装与配置](https://smartsi.blog.csdn.net/article/details/126198200)。在启动 HiveServer2 之前，我们需要先进行一些配置：
```xml
<property>
  <name>hive.server2.transport.mode</name>
  <value>binary</value>
  <description>
    Expects one of [binary, http]. Transport mode of HiveServer2.
  </description>
</property>

<property>
    <name>hive.server2.thrift.port</name>
    <value>10000</value>
    <description>Port number of HiveServer2 Thrift interface when hive.server2.transport.mode is 'binary'.</description>
</property>
```
默认情况下，HiveServer2 启动使用的是默认配置。这些配置主要是服务启动的 Host 和端口号以及客户端和后台操作运行的线程数。我们可以重写 hive-site.xml 配置文件中的配置项来修改 HiveServer2 的默认配置：

| 配置项   | 默认值     | 说明 |
| :------------- | :------------- | :------------- |
| hive.server2.transport.mode | binary | HiveServer2 的传输模式，binary或者http |
| hive.server2.thrift.port | 10000 | HiveServer2 传输模式设置为 binary 时，Thrift 接口的端口号 |
| hive.server2.thrift.http.port | 10001 | HiveServer2 传输模式设置为 http 时，Thrift 接口的端口号 |
| hive.server2.thrift.bind.host | localhost | Thrift服务绑定的主机 |
| hive.server2.thrift.min.worker.threads | 5 | Thrift最小工作线程数 |
| hive.server2.thrift.max.worker.threads | 500 | Thrift最大工作线程数 |
| hive.server2.authentication | NONE | 客户端认证类型，NONE、LDAP、KERBEROS、CUSTOM、PAM、NOSASL |
| hive.server2.thrift.client.user | anonymous | Thrift 客户端用户名 |
| hive.server2.thrift.client.password | anonymous | Thrift 客户端密码 |

### 2. 启动

启动 HiveServer2 非常简单，我们需要做的只是运行如下命令即可：
```
$HIVE_HOME/bin/hiveserver2 &
```
或者
```
$HIVE_HOME/bin/hive --service hiveserver2 &
```
检查 HiveServer2 是否启动成功的最快捷的办法就是使用 netstat 命令查看 10000 端口是否打开并监听连接：
```
netstat -nl | grep 10000
```

### 3. 验证

可以通过如下 Beeline 命令连接到 HiveServer2 来验证我们的 HiveServer2 是否成功：
```
`beeline -u  <url> -n <username> -p <Password>`
```
![](https://github.com/sjf0115/ImageBucket/blob/main/Hive/how-to-config-and-start-hiveserver2-1.jpg?raw=true)

### 4. Web UI

Hive 从 2.0.0 版本开始，为 HiveServer2 提供了一个简单的 WEB UI 页面，在页面中我们可以直观的看到当前链接的会话、历史日志、配置参数以及度量信息。默认情况下，Web UI 端口为 10002。

如果要开启 Web UI 需要在 `hive-site.xml` 配置文件中修改配置：
- hive.server2.webui.host
- hive.server2.webui.port

```xml
<property>
  <name>hive.server2.webui.host</name>
  <value>127.0.0.1</value>
</property>

<property>
  <name>hive.server2.webui.port</name>
  <value>10002</value>
</property>
```

配置完成之后启动 hiveserver2 通过 `http://localhost:10002/` 地址访问 Web UI：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hive/how-to-config-and-start-hiveserver2-2.jpg?raw=true)
