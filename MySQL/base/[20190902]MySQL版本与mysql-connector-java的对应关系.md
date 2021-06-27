---
layout: post
author: sjf0115
title: MySQL版本与mysql-connector-java的对应关系
date: 2019-09-02 13:21:45
tags:
  - MySQL

categories: MySQL
permalink: connector-j-versions-in-mysql
---

### 1. Connector/J

> MySQL `Connector/J` 是 `MySQL` 官方JDBC驱动程序。

MySQL `Connector/J` 有两个版本:
- `Connector/J` 5.1
- `Connector/J` 8.0

#### 1.1 Connector/J 5.1

`Connector/J` 5.1 是 Type 4 纯 Java JDBC 驱动程序，符合JDBC 3.0,4.0,4.1和4.2规范。与 MySQL 的所有功能都兼容，包括 5.6 和 5.7。`Connector/J` 5.1 提供了易于开发的功能，包括使用 Driver Manager 进行自动注册，标准化有效性检查，分类SQLExceptions，支持大量更新计数，支持java.time包中的本地和偏移日期时间变体，支持 JDBC-4.x XML处理，支持每个连接客户端信息，并支持NCHAR，NVARCHAR和NCLOB数据类型。

#### 1.2 Connector/J 8.0

`Connector/J` 8.0 是 Java 8 平台的 Type 4纯Java JDBC 4.2驱动程序。与 MySQL 5.6、5.7以及8.0所有功能兼容。有关详细信息，请参阅 [MySQL Connector/J 8.0 开发指南](https://dev.mysql.com/doc/connector-j/8.0/en/)。

> 建议将 MySQL `Connector/J` 8.0 与 MySQL Server 8.0、5.7以及5.6版本一起使用。

### 1.3 总结

下表总结了可用 `Connector/J` 版本，JDBC 驱动程序类型，它们支持的 JDBC API 版本，MySQL 服务器版本以及它们当前的开发状态等详细信息:

| Connector/J版本 | Driver Type | JDBC版本 | MySQL Server 版本 | 状态 |
| --- | --- | --- |
| 5.1	| 4	| 3.0, 4.0, 4.1, 4.2 | 5.6*, 5.7*, 8.0*	| 通用 |
| 8.0 |	4	| 4.2	| 5.6, 5.7, 8.0 |	通用、推荐版本 |

### 2. 支持的Java版本

下表总结了每个 `Connector/J` 版本所需的 JRE 版本，以及从源代码构建每个 `Connector/J` 版本所需的JDK版本:

| Connector/J 版本 | 支持的JRE |	编译源代码所需要的JDK |
| --- | --- | --- |
| 5.1 |	1.5.x, 1.6.x, 1.7.x*, 1.8.x**	| 1.5.x and 1.8.x |
| 8.0	| 1.8.x	| 1.8.x |

备注:
- * JRE 1.7 版本支持 `Connector/J` 5.1.21及更高版本。
- ** 当使用某些密码套件时，`Connector/J` 5.1需要 JRE 1.8 才能连接 MySQL 5.6.27及更高版本以及使用 SSL/TLS 连接5.7。
- ***

先贴出来以前旧版本（5.1.34）的连接方式：
```
db.driverClassName=com.mysql.jdbc.Driver
db.url=jdbc:mysql://localhost:3306/test1?useUnicode=true&characterEncoding=utf8&useSSL=true12
```
而升级后的新版本的连接方式为:
```
db.driverClassName=com.mysql.cj.jdbc.Driver
db.url=jdbc:mysql://localhost:3306/test1?useUnicode=true&characterEncoding=utf8&useSSL=true&serverTimezone=GMT12
```
在这里，升级后主要做的修改有两个：
- 其一、数据库驱动的连接地址，由之前的com.mysql.jdbc.Driver升级为com.mysql.cj.jdbc.Driver。
- 其二、数据库的url地址在末尾加上时区，即加上&serverTimezone=GMT。


查看MySQL版本:
```
smartsi:~ smartsi$ mysql -uroot -pzxcvbnm1
mysql: [Warning] Using a password on the command line interface can be insecure.
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 16
Server version: 8.0.17 MySQL Community Server - GPL

Copyright (c) 2000, 2018, Oracle and/or its affiliates. All rights reserved.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql>
```
