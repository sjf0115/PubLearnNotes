---
layout: post
author: sjf0115
title: Grafana 安装与启动
date: 2019-08-03 12:22:34
tags:
  - Grafana

categories: Grafana
permalink: how-to-install-and-run-grafana
---

### 1. Homebrew 安装

#### 1.1 下载与安装

安装最新稳定版：
```
brew update
brew install grafana
```
如果要升级 `Grafana`，可以使用如下命令重新安装：
```
brew update
brew reinstall grafana
```
你也可以从 Git 安装最新非稳定版 `Grafana`：
```
brew install --HEAD grafana/grafana/grafana
```
如果我们已从 HEAD 分支安装过，需要升级 `Grafana`：
```
brew reinstall --HEAD grafana/grafana/grafana
```
#### 1.2 启动

如果要使用 homebrew 服务启动 `Grafana`，首先要确保安装了 `homebrew/services`：
```
brew tap homebrew/services
```
使用如下命令启动`Grafana`：
```
brew services start grafana
```

#### 1.3 配置

配置文件位于 `/usr/local/etc/grafana/grafana.ini`。详细配置请参考:[如何配置Grafana](http://smartsi.club/how-to-configiure-grafana.html)

#### 1.4 日志

日志文件位于 `/usr/local/var/log/grafana/grafana.log`。

#### 1.5 插件

如果你想手动安装一个插件，需要将它放在这里：`/usr/local/var/lib/grafana/plugins`。

#### 1.6 数据库

默认数据库 Sqlite 文件位于 `/usr/local/var/lib/grafana`。

### 2. 二进制方式安装

#### 2.1 下载与安装

下载最新的[.tar.gz](https://grafana.com/get)文件并解压缩：
```
tar -zxvf grafana-6.2.5.darwin-amd64.tar.gz -C .
```
这将会解压到以我们下载的版本命名的文件夹中。此文件夹包含运行 `Grafana` 所需的所有文件，但不包含 init 脚本或安装脚本：
```
smartsi:grafana smartsi$ ll
total 56
drwxr-xr-x  11 smartsi  staff    352  8  2 11:29 ./
drwxrwxrwx  24 smartsi  staff    768  8  2 11:31 ../
-rw-r--r--   1 smartsi  staff  11343  6 26 02:12 LICENSE
-rw-r--r--   1 smartsi  staff    108  6 26 02:12 NOTICE.md
-rw-r--r--   1 smartsi  staff   5743  6 26 02:12 README.md
-rw-r--r--   1 smartsi  staff      5  6 26 02:23 VERSION
drwxr-xr-x   6 smartsi  staff    192  6 26 02:23 bin/
drwxr-xr-x   6 smartsi  staff    192  8  3 20:14 conf/
drwxr-xr-x  13 smartsi  staff    416  6 26 02:23 public/
drwxr-xr-x  22 smartsi  staff    704  6 26 02:23 scripts/
drwxr-xr-x   3 smartsi  staff     96  6 26 02:23 tools/
```
#### 2.2 配置

要配置 `Grafana`，需要将名为 `custom.ini` 的配置文件添加到 conf 文件夹，这将会覆盖 `conf/defaults.ini` 中定义的任何配置。详细配置请参考:[如何配置Grafana](http://smartsi.club/how-to-configiure-grafana.html)

下面是我们以 MySQL 作为 `Grafana` 的数据库的一些配置(`custom.ini`)：
```
[paths]
data = ${GRAFANA_HOME}/data
temp_data_lifetime = 24h
logs = ${GRAFANA_HOME}/logs
plugins = ${GRAFANA_HOME}/plugins
provisioning = conf/provisioning

[database]
type = mysql
host = 127.0.0.1:3306
name = grafana
user = root
password = zxcvbnm1
url = mysql://root:zxcvbnm1@localhost:3306/grafana
```

#### 2.3 启动

通过执行 `./bin/grafana-server web` 来启动 `Grafana`。
```
smartsi:grafana smartsi$ ./bin/grafana-server web
INFO[08-03|22:39:24] Starting Grafana                         logger=server version=6.2.5 commit=6082d19 branch=HEAD compiled=2019-06-26T01:56:19+0800
INFO[08-03|22:39:24] Config loaded from                       logger=settings file=/Users/smartsi/opt/grafana/conf/defaults.ini
INFO[08-03|22:39:24] Config loaded from                       logger=settings file=/Users/smartsi/opt/grafana/conf/custom.ini
INFO[08-03|22:39:24] Path Home                                logger=settings path=/Users/smartsi/opt/grafana
INFO[08-03|22:39:24] Path Data                                logger=settings path=/Users/smartsi/opt/grafana/data
INFO[08-03|22:39:24] Path Logs                                logger=settings path=/Users/smartsi/opt/grafana/logs
INFO[08-03|22:39:24] Path Plugins                             logger=settings path=/Users/smartsi/opt/grafana/plugins
INFO[08-03|22:39:24] Path Provisioning                        logger=settings path=/Users/smartsi/opt/grafana/conf/provisioning
INFO[08-03|22:39:24] App mode production                      logger=settings
INFO[08-03|22:39:24] Initializing SqlStore                    logger=server
...
```

### 3. 登录

要运行 `Grafana`，请打开浏览器并转到 `http://localhost:3000/`。如果你尚未配置其他端口，则 `Grafana` 侦听的默认 Http 端口为 3000。

![](https://github.com/sjf0115/ImageBucket/blob/main/Grafana/how-to-install-and-run-grafana-1.png?raw=true)

> 默认登录账号与密码为: admin/ admin

![](https://github.com/sjf0115/ImageBucket/blob/main/Grafana/how-to-install-and-run-grafana-2.png?raw=true)

原文:[Installing on Mac](https://grafana.com/docs/installation/mac/)
