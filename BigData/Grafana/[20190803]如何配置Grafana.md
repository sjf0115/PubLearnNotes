---
layout: post
author: sjf0115
title: 如何配置Grafana
date: 2019-08-04 12:22:34
tags:
  - Grafana

categories: Grafana
permalink: how-to-configiure-grafana
---

Grafana 后端具有许多配置选项，可以在 `.ini` 配置文件中指定或使用环境变量指定。
> 需要重新启动 Grafana 才能使更改的配置生效。

分号 `;` 是 `.ini` 文件中注释行的标准方法。一个常见问题是忘记取消注释 `custom.ini`（或 `grafana.ini`）文件中的某行，这会导致忽略该配置选项。

### 2. 配置文件位置

- 默认配置文件：`$WORKING_DIR/conf/defaults.ini`
- 自定义配置文件：`$WORKING_DIR/conf/custom.ini`
- 自定义配置文件路径可以被 `--config` 参数覆盖。

> 如果我们使用 deb 或 rpm 软件包安装 Grafana，那么我们的配置文件位于 `/etc/grafana/grafana.ini`。这个路径是在 Grafana 的 init.d 脚本中使用 --config 参数指定的。

### 3. 环境变量

可以使用如下语法使用环境变量来覆盖配置文件中的配置选项：
```
GF_<SectionName>_<KeyName>
```
SectionName 是中括号`[]`中的文本信息(例如，下面中的 `security`、`auth.google`)。所有信息都需要大写，并使用 `_` 来替代 `.` 。例如如下配置：
```
# default section
instance_name = ${HOSTNAME}

[security]
admin_user = admin

[auth.google]
client_secret = 0ldS3cretKey
```
那么就可以使用如下环境变量覆盖这些配置：
```
export GF_DEFAULT_INSTANCE_NAME=my-instance
export GF_SECURITY_ADMIN_USER=true
export GF_AUTH_GOOGLE_CLIENT_SECRET=newS3cretKey
```
### 4. 配置选项

#### 4.1 实例名称

设置 grafana-server 实例的名称。可以在日志、内置度量、集群信息中使用。默认值是 `${HOSTNAME}`，这个可以被环境变量 `HOSTNAME` 覆盖。如果获得是是空值或者不存在，Grafana 会尝试使用系统调用来获取机器名称。

#### 4.2 [paths]

(1) data
Grafana 存储 sqlite3 数据库文件(如果使用)，sessions文件(如果使用)以及其他数据的位置。该路径通常在 `init.d` 脚本或者 systemd 服务文件在命令行中指定。

(2) temp_data-lifetime
在 data 目录中的保存临时快照的时间范围。默认为24h。另外支持 `h`(小时)，`m`(分钟)，例如，168h，30m，10h30m。使用 0 表示永久不清除临时文件。

(3) logs
Grafana 存储日志的路径。该路径通常在 `init.d` 脚本或者 `systemd` 服务文件在命令行中指定。可以通过配置文件或者默认环境变量文件进行重写。

(4) plugins
Grafana 自动搜索和查找插件的目录。

#### 4.3 [server]

(1) http_addr

#### 4.4 [database]

Grafana 需要一个数据库来存储用户和仪表板（以及其他东西）。默认情况下，配置使用 Sqlite3，这是一个嵌入式数据库。

(1) URL
使用以下URL或其他字段配置数据库示例：
```
mysql://user:secret@host:port/database
```

(2) type
根据你的需求选择 MySQL、Postgres 或者 Sqlite3。

(3) path
只适用于 Sqlite3 数据库。数据库存储文件路径。

(4) host
只适用于 MySQL 或者 Postgres。包括 IP 地址或者域名和端口号。例如，Grafana 运行在同一台机器上的MySQL：`host = 127.0.0.1:3306` 或者使用 Unix 套接字：`host = /var/run/mysqld/mysqld.sock`。

(5) name
Grafana 数据库的名称。可以设置为 `grafana` 或者其他名字。

(6) user
数据库用户(不适用于 Sqlite3)

(7) password
数据库用户的密码(不适用于 Sqlite3)。如果密码包含 `#` 或者 `;` 则必须使用三个引号，例如，`"""#123456;"""`













原文:[Configuration](https://grafana.com/docs/installation/configuration/)
