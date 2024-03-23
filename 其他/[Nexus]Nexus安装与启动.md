---
layout: post
author: sjf0115
title: Nexus 安装与启动
date: 2018-01-10 12:54:01
tags:
  - Nexus

categories: Nexus
---

### 1. 安装

解压到指定目录:

```
xiaosi@ying:~/opt$ tar -zxvf nexus-3.6.2-01-unix.tar.gz -C /home/xiaosi/opt
```

重命名：

```
xiaosi@ying:~/opt$ mv nexus-3.6.2-01/ nexus
```

如果要更改默认的`nexus`数据目录，请打开`nexus`属性文件并更改数据目录`-Dkaraf.data`参数为你指定的目录，如下所示：

```
xiaosi@ying:~/opt/nexus/bin$ vim nexus.vmoptions
```

示例配置如下所示：

```
-Xms1200M
-Xmx1200M
-XX:MaxDirectMemorySize=2G
-XX:+UnlockDiagnosticVMOptions
-XX:+UnsyncloadClass
-XX:+LogVMOutput
-XX:LogFile=../sonatype-work/nexus3/log/jvm.log
-XX:-OmitStackTraceInFastThrow
-Djava.net.preferIPv4Stack=true
-Dkaraf.home=.
-Dkaraf.base=.
-Dkaraf.etc=etc/karaf
-Djava.util.logging.config.file=etc/karaf/java.util.logging.properties
-Dkaraf.data=../sonatype-work/nexus3
-Djava.io.tmpdir=../sonatype-work/nexus3/tmp
-Dkaraf.startLocalConsole=false
```

### 2. 手动启动

### 3. 自动启动

#### 3.1 运行Nexus为服务

最好有一个`init.d`条目来使用`Linux`服务命令来管理`nexus`服务。按照下面给出的步骤进行设置。

(1) 为`nexus`服务脚本创建一个符号链接到`/etc/init.d`文件夹:

```
xiaosi@ying:~/qunar/company/opt/nexus$ sudo ln -s bin/nexus /etc/init.d/nexus
```

(2) 执行以下命令来添加一个`nexus`服务进行启动:

```
cd /etc/init.d
sudo update-rc.d nexus defaults
sudo service nexus start
```

```
[Unit]
Description=nexus service
After=network.target

[Service]
Type=forking
ExecStart=/home/xiaosi/qunar/company/opt/nexus/bin/nexus start
ExecStop=/home/xiaosi/qunar/company/opt/nexus/bin/nexus stop
User=yoona
Restart=on-abort

[Install]
WantedBy=multi-user.target
```

备注:

```

```

#### 3.2 管理Nexus服务

现在我们有所有的配置。使用如下命令启动`Nexus`服务：

```

```

### 4. 登录

上述两种启动方式将在端口`8081`上启动`nexus`服务。要访问`nexus`页面，请访问`http://localhost:8081`。你将能够看到如下所示的页面：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/Nexus%E5%AE%89%E8%A3%85%E4%B8%8E%E5%90%AF%E5%8A%A8-1.png?raw=true)

使用如下默认的用户与密码进行登录:

```
用户名: admin
密码: admin123
```

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/Nexus%E5%AE%89%E8%A3%85%E4%B8%8E%E5%90%AF%E5%8A%A8-2.png?raw=true)

参考:http://www.sonatype.org/nexus/2017/01/25/how-to-install-latest-sonatype-nexus-3-on-linux/

http://books.sonatype.com/nexus-book/3.5/reference/install.html#service-linux
