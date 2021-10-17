---
layout: post
author: sjf0115
title: Linux rsync配置指南
date: 2018-03-20 15:17:17
tags:
  - Linux
  - Linux 命令

categories: Linux
permalink: rsync-config-usage
---

### 1. 概述

`rsync` 命令是一个远程数据同步工具，可通过 LAN/WAN 快速同步多台主机间的文件。`rsync` 使用所谓的 "rsync算法" 来使本地和远程两个主机之间的文件达到同步，这个算法只传送两个文件的不同部分，而不是每次都整份传送，因此速度相当快。`rsync` 是一个功能非常强大的工具，其命令也有很多功能特色选项。

### 2. 安装

在 ubuntu 下安装 rsync 通过以步骤可以实现：
```
sudo apt-get install rsync xinetd
```
默认情况下 ubuntu 安装了 rsync，因此只需安装 xinetd即可:
```
sudo apt-get install xinetd
```
### 3. 配置

(1) 编辑 `/etc/default/rsync` 启动 rsync 作为使用 xinetd 的守护进程：
```
# 打开rsync
sudo vim /etc/default/rsync
# 编辑rsync
RSYNC_ENABLE=inetd
```

(2) 创建 `/etc/xinetd.d/rsync`, 通过 xinetd 使 rsync 开始工作
```
# 创建并打开文件
sudo vim /etc/xinetd.d/rsync
# 编辑内容
service rsync
{
    disable         = no
    socket_type     = stream
    wait            = no
    user            = root
    server          = /usr/bin/rsync
    server_args     = --daemon
    log_on_failure  += USERID
}
```

(3) 创建 `/etc/rsyncd.conf` ,并填写配置信息
```
# 创建并打开文件
sudo vim /etc/rsyncd.conf
# 编辑配置信息
max connections = 2
log file = /var/log/rsync.log
timeout = 300

[share] # 模块名
comment = Public Share
# path为需要同步的文件夹路径
path = /home/share
read only = no
list = yes
uid = root
gid = root
# 必须和 rsyncd.secrets中的用户名对应
auth users = test
secrets file = /etc/rsyncd.secrets
```

(4) 创建 `/etc/rsyncd.secrets`，配置用户名和密码.
```
# 创建并打开文件
sudo vim /etc/rsyncd.secrets
# 配置用户名和密码，密码可以任意设置
test:123
```

(5) 修改 `rsyncd.secrets` 文件的权限
```
sudo chmod 600 /etc/rsyncd.secrets
```

(6) 启动/重启 `xinetd`
```
sudo /etc/init.d/xinetd restart
```

### 4. 测试

在客户端运行下面的命令以及输入密码，确认 rsync 是否配置成功：
```
xiaosi@ying:/etc/apt$ rsync  test@123.206.187.64::share
Password:
drwxr-xr-x          4,096 2018/03/20 18:44:51 .
-rw-r--r--             17 2018/03/20 18:44:51 remote_content.txt
```
> test 是在服务器中 rsyncd.secrets 文件中配置的用户名。 xx.xx.xx.xx 是服务器的ip地址，也可以填写服务器对应的域名。share 是 rsyncd.conf 中定义的模块


### 5. 问题

在测试的时候出现如下问题：
```
xiaosi@ying:/etc/apt$ rsync test@xxx:xxx:xxx:xxx::share
rsync: failed to connect to xxx:xxx:xxx:xxx (xxx:xxx:xxx:xxx): Connection refused (111)
rsync error: error in socket IO (code 10) at clientserver.c(128) [Receiver=3.1.1]
```
首先判断 873 端口是否开放，如果没有开启一下：
```
telnet 192.168.xxx.xxx 873
```
或者查看 rsync 服务是否启动：
```
ubuntu@VM-0-7-ubuntu:~$  ps -ef | grep rsync
root     18848     1  0 17:29 ?        00:00:00 rsync --daemon --config=/etc/rsyncd.conf
ubuntu   18850 12214  0 17:29 pts/0    00:00:00 grep --color=auto rsync
```
如果没有启动，启动一下 rsync 服务：
```
sudo rsync --daemon --config=/etc/rsyncd.conf
```

转载于： https://segmentfault.com/a/1190000010310496

参考于： http://ju.outofmemory.cn/entry/27665
