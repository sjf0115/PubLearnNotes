---
layout: post
author: sjf0115
title: Redis 安装与启动
date: 2018-11-25 15:28:06
tags:
  - Redis

categories: Redis
permalink: how-install-and-startup-redis
---

在安装 Redis 前需要了解 Redis 的版本规则以选择最合适自己的版本，Redis 约定次版本（即第一个小数点后的数字）为偶数的版本是稳定版本(如 2.4版本，2.6版本)，奇数版本是非稳定版本(如2.5版本，2.7版本)，推荐使用稳定版本进行开发和在生产环境中使用．

## 1. 下载

当前最新版本为 6.0.6：

官网下载：https://redis.io/

中文官网下载：http://www.redis.cn/download.html

## 2. 安装

解压缩文件到指定目录：
```
tar -zxvf redis-6.0.6.tar.gz -C /opt/
```
创建软连接，便于升级：
```
ln -s redis-6.0.6 redis
```
在 /etc/profile 文件下添加如下配置信息：
```
# Redis
export REDIS_HOME=/opt/redis
export PATH=${REDIS_HOME}/bin:$PATH
```
配置完成之后，运行 source /etc/profile 使之生效。

进入解压之后的目录，进行编译
```
cd /opt/redis/
make
```
看到如下信息，表示可以继续下一步：
```
...
LINK redis-server
INSTALL redis-sentinel
CC redis-cli.o
LINK redis-cli
CC redis-benchmark.o
LINK redis-benchmark
INSTALL redis-check-rdb
INSTALL redis-check-aof

Hint: It's a good idea to run 'make test' ;)
```
二进制文件编译完成后在 src 目录下，进入 src 目录之后进行安装操作:
```
localhost:src wy$ make install

Hint: It's a good idea to run 'make test' ;)

    INSTALL install
    INSTALL install
    INSTALL install
    INSTALL install
    INSTALL install
```

> 备注: 一般情况下，在 Ubuntu 系统中，都是需要使用 sudo 提升权限。

在安装成功之后，可以运行测试，确认 Redis 的功能是否正常：
```
make test
```
看到如下信息，表示 Redis 已经安装成功：
```
\o/ All tests passed without errors!
Cleanup: may take some time... OK
```
## 3. 启动

安装完 Redis 后的下一步就是启动它。在这之前，我们先了解一下 Redis 包含的可执行文件都有哪些，如下表所示：

文件名你|说明
---|---
redis-server|Redis服务器
redis-cli|Redis命令行客户端
redis-benchmark|Redis性能测试工具
redis-check-aof|AOF文件修复工具

我们最常使用的两个程序是 redis-server 和　redis-cli，其中 redis-server 是 Redis 的服务器，启动 Redis 即运行它；而 redis-cli 是 Redis 自带的 Redis 命令行客户端．

### 3.1 启动 Redis

启动 Redis 有直接启动和通过初始化脚本启动两种方式，分别适用于开发环境和生产环境。

#### 3.1.1 直接启动

直接运行 redis-server 即可启动 Redis：
```
localhost:src wy$ redis-server
32391:C 15 Nov 2021 14:41:46.569 # oO0OoO0OoO0Oo Redis is starting oO0OoO0OoO0Oo
32391:C 15 Nov 2021 14:41:46.569 # Redis version=6.0.6, bits=64, commit=00000000, modified=0, pid=32391, just started
32391:C 15 Nov 2021 14:41:46.569 # Warning: no config file specified, using the default config. In order to specify a config file use redis-server /path/to/redis.conf
32391:M 15 Nov 2021 14:41:46.570 * Increased maximum number of open files to 10032 (it was originally set to 4864).
                _._
           _.-``__ ''-._
      _.-``    `.  `_.  ''-._           Redis 6.0.6 (00000000/0) 64 bit
  .-`` .-```.  ```\/    _.,_ ''-._
 (    '      ,       .-`  | `,    )     Running in standalone mode
 |`-._`-...-` __...-.``-._|'` _.-'|     Port: 6379
 |    `-._   `._    /     _.-'    |     PID: 32391
  `-._    `-._  `-./  _.-'    _.-'
 |`-._`-._    `-.__.-'    _.-'_.-'|
 |    `-._`-._        _.-'_.-'    |           http://redis.io
  `-._    `-._`-.__.-'_.-'    _.-'
 |`-._`-._    `-.__.-'    _.-'_.-'|
 |    `-._`-._        _.-'_.-'    |
  `-._    `-._`-.__.-'_.-'    _.-'
      `-._    `-.__.-'    _.-'
          `-._        _.-'
              `-.__.-'

32391:M 15 Nov 2021 14:41:46.576 # Server initialized
32391:M 15 Nov 2021 14:41:46.577 * Ready to accept connections
```
可以看到直接使用 redis-server 启动 Redis 后，会打印出一些日志，通过日志可以看到一些信息，上例中可以看到：
- 当前 Redis 版本的是 6.0.6。
- Redis 的默认端口是 6379。
- Redis 建议要使用配置文件来启动。

因为直接启动无法自定义配置，所以这种方式是不会在生产环境中使用的。

#### 3.1.2 运行启动

在 redis-server 后面加上要修改的配置名和值（可以是多对），没有设置的配置将使用默认配置：
```
redis-server --configKey1 configValue1 --configKey2 configValue2
```
例如，如果要用 6380 作为端口启动 Redis，那么可以执行：
```
redis-server --port 6380
```
虽然运行配置可以自定义配置，但是如果需要修改的配置较多或者希望将配置保存到文件中，不建议使用这种方式。

#### 3.1.3 配置文件启动

将配置写到指定文件里，例如，我们将配置写到了 /opt/redis/conf/redis.conf 中，那么只需要执行如下命令即可启动 Redis：
```
redis-server /opt/redis/conf/redis.conf
```
在 Redis 目录下都会有一个默认的 redis.conf 配置文件，里面是 Redis 的默认配置。通常来讲我们会在一台机器上启动多个 Redis，并且将配置集中管理在指定目录下(比如，在这使用 conf 目录)，而且配置不是完全手写的，而是将 redis.conf 作为模板进行修改。

显然通过配置文件启动的方式提供了更大的灵活性，所以大部分生产环境会使用这种方式启动 Redis。

### 3.2 客户端

可以使用内置的客户端命令 redis-cli 进行启动:
```
localhost:~$ redis-cli
127.0.0.1:6379>
```
在上面的提示中，127.0.0.1 是计算机的IP地址，6379 是运行 Redis 服务器的端口。现在键入以下PING命令:
```
127.0.0.1:6379> ping
PONG
```
这表明 Redis 已成功在您的计算机上安装了。

### 3.3 停止 Redis

考虑到 Redis 有可能正在将内存中的数据同步到磁盘中，强行终止 Redis 进程可能会导致数据丢失。正确停止 Redis 的方式应该是向 Redis 发送 SHUTDOWN 命令，方法为：
```
redis-cli SHUTDOWN
```
当 Redis 收到 SHUTDOWN 命令后，会先断开所有客户端连接，然后根据配置执行持久化，最后完成退出。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

参考：
- Redis入门指南
- Redis 开发与运维
