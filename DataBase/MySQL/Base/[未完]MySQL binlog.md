---
layout: post
author: smartsi
title: MySQL Binlog
date: 2021-09-27 21:56:00
tags:
  - MySQL

categories: MySQL
permalink: mysql-binlog
---

> MySQL 版本：5.7.20

### 1. 如何开启 Binlog

通常情况 MySQL 是默认关闭 Binlog 的。登录之后使用如下命令查看是否开启 Binlog：
```
SHOW VARIABLES LIKE 'log_bin%';
```
![](1)

我们可以看到 log_bin 变量是 OFF，表示还没有开启 Binlog，需要我们手动启动。

在 MySQL 配置文件 my.cnf 或 my.ini 中的 [mysqld] 标签下增加如下内容：
```
[mysqld]
# server-id 比较大的随机值
server-id = 85744
# Binlog 文件的前缀
log-bin = mysql-bin
# 必须为ROW
binlog_format = ROW
```

Mac my.cnf 配置路径请查阅 [Location of my.cnf file on macOS](https://stackoverflow.com/questions/10757169/location-of-my-cnf-file-on-macos)，我的是在 /etc/ 目录下配置。

配置好之后重启 MySQL 服务，再次使用上述命令查看是否开启 Binlog：

![](2)

从上面可知 Binlog 的存储路径为 /usr/local/mysql/data/:

### 2. 






...
