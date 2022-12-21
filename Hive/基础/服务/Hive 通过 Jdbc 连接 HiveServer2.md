---
layout: post
author: smartsi
title: Hive 通过 Jdbc 连接 HiveServer2
date: 2020-09-13 21:57:01
tags:
  - Hive

categories: Hive
permalink: hiveserver2-client-jdbc
---

> Hive 版本：2.3.7

### 1. 配置

如果想通过 JDBC 来访问 HiveServer2，需要开启 HiveServer2 服务，具体请参阅 [如何启动 HiveServer2](http://smartsi.club/how-to-config-and-start-hiveserver2.html)。

### 2. URL格式

JDBC客户端允许使用 Java 代码连接到 HiveServer2。可以在远程，嵌入式或 HTTP 模式下建立 JDBC 连接。以下是不同模式的配置：
- 远程模式下 Url 格式为 `jdbc:hive2://<host>:<port>/<database>`，默认情况下 HiveServer2 的端口为 10000。
- 内嵌模式下 Url 格式为 `jdbc:hive2://`，不需要提供主机与端口号。
- 如果 HiveServer2 以 http 模式运行，Url 格式为 `jdbc:hive2://<host>:<port>/<db>?
hive.server2.transport.mode=http;hive.server2.thrift.http.path=
<http_endpoint>`，<http_endpoint> 在 hive-site.xml 配置文件中进行配置，默认值为 cliservice。HTTP 传输模式的默认端口为 10001。

### 3. Maven 依赖

如果你使用的是 Maven，需要在 pom.xml 中添加以下依赖项：
```xml
<dependency>
    <groupId>org.apache.hive</groupId>
    <artifactId>hive-jdbc</artifactId>
    <version>2.3.7</version>
</dependency>
```

### 4. 开发

第一步加载 JDBC 驱动类：
```java
Class.forName("org.apache.hive.jdbc.HiveDriver");
```
第二步通过使用 JDBC 驱动创建 Connection 对象来连接到数据库：
```java
Connection conn = DriverManager.getConnection("jdbc:hive2://<host>:<port>/<database>","<user>","<password>");
```
默认情况下端口为 10000，如果 HiveServer2 在非安全环境中运行，密码可以忽略不写：
```java
Connection conn = DriverManager.getConnection("jdbc:hive2://127.0.0.1:10000/default","hadoop","");
```
第三步通过执行如下代码来执行查询：
```java
Statement	stmt	=	conn.createStatement();
ResultSet	resultSet	=	stmt.executeQuery("SELECT	*	FROM tmp_table");
```
最后一步处理 ResultSet 返回的结果：
```java
int columns= resultSet.getMetaData().getColumnCount();
int rowIndex = 1;
while (resultSet.next()) {
    for(int i = 1;i <= columns; i++) {
        System.out.println("RowIndex: " + rowIndex + ", ColumnIndex: " + i + ", ColumnValue: " + resultSet.getString(i));
    }
}
```
详细代码请参阅：[JdbcExample](https://github.com/sjf0115/data-example/blob/master/hive-example/src/main/java/com/hive/example/JdbcExample.java)

### 5. JDBC数据类型

下表为 HiveServer2 列出了 Hive数据类型与 Java 数据类型之间的映射关系：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hive/hiveserver2-client-jdbc-1.jpg?raw=true)
