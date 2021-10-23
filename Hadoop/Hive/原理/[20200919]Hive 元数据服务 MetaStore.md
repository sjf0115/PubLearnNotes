---
layout: post
author: smartsi
title: Hive 元数据服务 MetaStore
date: 2020-09-19 20:48:01
tags:
  - Hive

categories: Hive
permalink: hive-metastore-service
---


### 1. 概念

MetaSore 是 Hive 元数据存储的地方。Hive 数据库、表、函数等的定义都存储在 MetaStore 中。根据系统配置方式，统计信息和授权记录也可以存储在这。Hive 或者其他执行引擎在运行时可以使用这些数据来确定如何解析，授权以及有效执行用户的查询。MetaStore 分为两个部分：服务和后台数据的存储。

### 2. 配置参数

这里只会展示与 MetaStore 相关的配置参数，与 MetaSote 不相关的配置参数可以在[这](https://cwiki.apache.org/confluence/display/Hive/AdminManual+Configuration)查阅。

| 配置参数     | 参数说明     |
| :------------- | :------------- |
| hive.metastore.local | 本地或远程元数据存储。该配置项从 Hive 0.10 废弃，而是通过 hive.metastore.uris 来判断，如果为空，则假定为本地模式，否则为远程模式。|
| hive.metastore.uris | 远程元数据存储的 Thrift URI。元数据服务客户端通过该配置连接远程元数据。|
| javax.jdo.option.ConnectionURL | 元数据存储的 JDBC 连接 URL |
| javax.jdo.option.ConnectionDriverName | 元数据存储的 JDBC 驱动类 |
| javax.jdo.option.ConnectionUserName | 元数据存储数据库用户名 |
| javax.jdo.option.ConnectionPassword | 元数据存储数据库密码 |
| hive.metastore.warehouse.dir | 数据仓库存储位置 |

Hive MetaSote 是无状态的，因此可以有多个实例来实现高可用性。使用 hive.metastore.uris 可以指定多个远程 MetaStore。Hive 将默认使用列表中的第一个，但会在连接失败时随机选择一个，并尝试重新连接。

### 3. 部署模式

MetaStore 分为三种部署模式：内嵌模式、本地模式以及远程模式。

#### 3.1 内嵌 MetaStore

默认情况下，MetaStore 服务和 Hive 服务运行在同一个 JVM 中，包含一个内嵌的以本地磁盘作为存储的 Derby 数据库实例。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/hive-metastore-service-1.png?raw=true)

使用内嵌的 MetaStore 是 Hive 入门最简单的方法。但是，每次只有一个内嵌的 Derby 数据库可以访问某个磁盘上的数据库文件，这就意味着一次只能为每个 MetaStore 打开一个 Hive 会话。如果试着启动第二个会话，在它试图连接 MetaStore 时，会得到错误信息。因此它并不是一个实际的解决方案，并不适合在生产环境使用，但对于单元测试来说效果很好。

```xml
<!-- 本地模式不需要配置 -->
<property>
  <name>hive.metastore.uris</name>
  <value/>
</property>

<property>  
  <name>javax.jdo.option.ConnectionURL</name>  
  <value>jdbc:derby:;databaseName=metastore_db;create=true</value>  
</property>  

<property>  
  <name>javax.jdo.option.ConnectionDriverName</name>  
  <value>org.apache.derby.jdbc.EmbeddedDriver</value>  
</property>

<property>
  <name>hive.metastore.warehouse.dir</name>
  <value>/user/hive/warehouse</value>
</property>
```

#### 3.2 本地 MetaStore

如果要支持多会话（以及多租户），需要使用一个独立的数据库。这种配置方式成为本地配置，因为 MetaStore 服务仍然和 Hive 服务运行在同一个进程中，但连接的却是另一个进程中运行的数据库，在同一台机器上或者远程机器上。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/hive-metastore-service-2.png?raw=true)

对于独立的 MetaStore，MySQL 是一种很受欢迎的选择。本实例我们 MySQL 为例，具体看看如何配置：
```xml
<!-- 本地模式不需要配置 -->
<property>
  <name>hive.metastore.uris</name>
  <value/>
</property>

<property>  
  <name>javax.jdo.option.ConnectionURL</name>
  <value>jdbc:mysql://localhost:3306/hive_meta?createDatabaseIfNotExist=true</value>
</property>  

<property>  
  <name>javax.jdo.option.ConnectionDriverName</name>
  <value>com.mysql.cj.jdbc.Driver</value>  
</property>  

<property>  
  <name>javax.jdo.option.ConnectionUserName</name>
  <value>root</value>  
</property>  

<property>  
  <name>javax.jdo.option.ConnectionPassword</name>
  <value>root</value>  
</property>

<property>
  <name>hive.metastore.warehouse.dir</name>
  <value>/user/hive/warehouse</value>
</property>

<property>
  <name>hive.metastore.port</name>
  <value>9083</value>
</property>
```
在本地模式下不需要配置 hive.metastore.uris，默认为空表示是本地模式。

如果选择 MySQL 作为 MetaStore 存储数据库，需要提前将 MySQL 的驱动包拷贝到 $HIVE_HOME/lib目录下。

> JDBC 连接驱动类视情况决定选择 com.mysql.cj.jdbc.Driver 还是 com.mysql.jdbc.Driver。

#### 3.3 远程 MetaStore

在远程模式下，MetaStore 服务和 Hive 服务运行在不同进程中。CLI、HiveServer2、HCatalog 以及其他进程使用 Thrift API（使用 hive.metastore.uris 属性配置）与 MetaStore 服务通信。MetaStore 服务通过 JDBC 与 MetaStore 数据库进行通信（使用 javax.jdo.option.ConnectionURL 属性配置）:

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/hive-metastore-service-3.png?raw=true)

在这种情况下，我们还可以单独部署一台 MetaStore 服务器，以提供更高可用性。这也可以有更好的可管理性/安全性，因为数据库层可以完全防火墙关闭。客户端不再需要与每个 Hiver 用户共享数据库凭据即可访问元存储数据库。

Hive MetaStore 服务端配置：
```xml
<property>  
  <name>javax.jdo.option.ConnectionURL</name>
  <value>jdbc:mysql://localhost:3306/hive_meta?createDatabaseIfNotExist=true</value>
</property>  

<property>  
  <name>javax.jdo.option.ConnectionDriverName</name>
  <value>com.mysql.cj.jdbc.Driver</value>  
</property>  

<property>  
  <name>javax.jdo.option.ConnectionUserName</name>
  <value>root</value>  
</property>  

<property>  
  <name>javax.jdo.option.ConnectionPassword</name>
  <value>root</value>  
</property>

<property>
  <name>hive.metastore.warehouse.dir</name>
  <value>/user/hive/warehouse</value>
</property>

<property>
  <name>hive.metastore.port</name>
  <value>9083</value>
</property>
```

Hive MetaStore 客户端配置：
```xml
<!-- 远程模式需要配置 9083 是默认监听端口号 -->
<property>  
  <name>hive.metastore.uris</name>
  <value>thrift://xxx:9083</value>  
</property>

<property>  
  <name>hive.metastore.warehouse.dir</name>
  <value>/user/hive/warehouse</value>
</property>
```

### 4. 启动服务

我们可以通过执行以下命令来启动 MetaStore 服务：
```
hive --service metastore -p 9083 &
```
如果我们在 hive-site.xml 配置文件中指定了 hive.metastore.uris 的 port：
```xml
<property>
  <name>hive.metastore.uris</name>
  <value>thrift://xxx:9083</value>
</property>
```
我们就可以不指定端口进行启动：
```
hive --service metastore &
```

> 注意客户端中的端口配置需要和启动监听的端口一致。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

参考：
- Hadoop 权威指南
- [AdminManual Metastore Administration](https://cwiki.apache.org/confluence/display/Hive/AdminManual+Metastore+Administration#AdminManualMetastoreAdministration-Introduction)
