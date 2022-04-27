---
layout: post
author: smartsi
title: Flink SQL CLI 与 Hive 集成
date: 2022-04-27 12:07:21
tags:
  - Flink
  - Flink SQL

categories: Flink
permalink: flink-sql-cli-hive-integration
---

> Flink 版本：1.13.5
> Hive 版本：2.3.4

Apache Hive 已经成为实现数据仓库生态系统的标准手段。不仅作为大数据分析和 ETL 的 SQL 引擎，而且还是一个数据管理平台。Flink 提供了与 Hive 的双向集成：
- 第一个是利用 Hive 的 Metastore 作为一个持久化 Catalog。利用 Flink 的 HiveCatalog 实现跨会话存储 Flink 元数据。例如，用户可以使用 HiveCatalog 将 Kafka 或 ElasticSearch 表存储在 Hive Metastore 中，然后在 SQL 查询中复用（不用重复创建表）。
- 第二个是为 Hive 提供 Flink 引擎来读写数据。

Flink 从 1.9 版本开始支持支持 Hive，不过作为 beta 版，不推荐在生产环境中使用。在 Flink 1.10 版本中，对 Hive 的集成也达到了生产级别的要求。值得注意的是，不同版本的 Flink 对于 Hive 的集成有所差异。本文以 Flink 1.13.5 版本为例，阐述 SQL CLI 如何与 Hive 集成。

## 1. 支持的 Hive 版本

| Hive 大版本 | Hive 小版本 |
| :------------- | :------------- |
| 1.0       | 1.0.0 <br> 1.0.1 |
| 1.1       | 1.1.0 <br> 1.1.1 |
| 1.2       | 1.2.0 <br> 1.2.1 <br> 1.2.2 |
| 2.0       | 2.0.0 <br> 2.0.1 |
| 2.1       | 2.1.0 <br> 2.1.1 |
| 2.2       | 2.2.0 |
| 2.3       | 2.3.0 <br> 2.3.1 <br> 2.3.2 <br> 2.3.3 <br> 2.3.4 <br> 2.3.5 <br> 2.3.6 |
| 3.1       | 3.1.0 <br> 3.1.1 <br> 3.1.2 |

需要注意 Hive 在不同版本会有不同的功能：
- 1.2.0 及更高版本支持 Hive 内置函数。
- 3.1.0 及更高版本支持列约束，即 PRIMARY KEY 和 NOT NULL。
- 1.2.0 及更高版本支持更改表统计信息。
- 1.2.0 及更高版本支持 DATE 列统计信息。
- 2.0.x 不支持写入 ORC 表。

## 2. 依赖

要与 Hive 集成，需要在 Flink 的 /lib/ 目录中添加一些额外的依赖项，以便在 Table API 或 SQL Client 中与 Hive 集成。也可以将这些依赖项放在一个专门文件夹下，在使用 Table API 或者 SQL Client 时候分别使用 -C 或 -l 选项将它们添加到类路径中。Apache Hive 构建在 Hadoop 之上，因此需要通过设置 HADOOP_CLASSPATH 环境变量来提供 Hadoop 依赖项：
```
export HADOOP_CLASSPATH=`hadoop classpath`
```
有两种方法可以添加 Hive 依赖项。第一种是使用 Flink 捆绑的 Hive jars。根据使用的 Metastore 版本选择对应的 Hive jar。第二种是分别添加每个所需的 jar。如果你使用的 Hive 版本在上面表格未列出，那么第二种方法比较适合。

> 推荐使用 Flink 捆绑的 Hive jars 的方式添加依赖项。仅当捆绑方式不能满足你的需求时，才应使用单独的 jar。每个版本所依赖的 Hive 相关 jar 也不同，使用起来比较麻烦。使用 Flink 提供好的捆绑 jar 比较省事。

#### 2.1 捆绑方式

下面列举了可用的 jar 包及其适用的 Hive 版本，我们可以根据使用的 Hive 版本，下载对应的 jar 包即可：

| Hive 版本  | Maven 依赖  | SQL Client JAR |
| :------------- | :----------------------------- | :------------- |
| 1.0.0 - 1.2.2	 | flink-sql-connector-hive-1.2.2 |	[下载](https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-hive-1.2.2_2.11/1.13.5/flink-sql-connector-hive-1.2.2_2.11-1.13.5.jar) |
| 2.0.0 - 2.2.0	 | flink-sql-connector-hive-2.2.0	| [下载](https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-hive-2.2.0_2.11/1.13.5/flink-sql-connector-hive-2.2.0_2.11-1.13.5.jar) |  
| 2.3.0 - 2.3.6	 | flink-sql-connector-hive-2.3.6	| [下载](https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-hive-2.3.6_2.11/1.13.5/flink-sql-connector-hive-2.3.6_2.11-1.13.5.jar) |
| 3.0.0 - 3.1.2	 | flink-sql-connector-hive-3.1.2	| [下载](https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-hive-3.1.2_2.11/1.13.5/flink-sql-connector-hive-3.1.2_2.11-1.13.5.jar) |

#### 2.1 用户自定义依赖

在下面找到不同 Hive 主要版本所需的依赖项：
- Hive 3.1.0：
 - flink-connector-hive_2.11-1.13.5.jar：Flink 的 Hive Connector
 - hive-exec-3.1.0.jar：Hive 依赖
 - libfb303-0.9.3.jar：在部分版本中没有打包到 hive-exec 中，需要单独添加
 - antlr-runtime-3.5.2.jar：使用 hive 方言需要添加
- Hive 2.3.4：
  - flink-connector-hive_2.11-1.13.5.jar：Flink 的 Hive Connector。包含 flink-hadoop-compatibility 和 flink-orc jars
  - hive-exec-2.3.4.jar：Hive 依赖
  - antlr-runtime-3.5.2.jar：使用 hive 方言需要添加
- Hive 2.2.0：
  - flink-connector-hive_2.11-1.13.5.jar：Flink 的 Hive Connector
  - hive-exec-2.2.0.jar：Hive 依赖
  - orc-core-1.4.3.jar：Orc 依赖
  - aircompressor-0.8.jar：orc-core 传递依赖
  - antlr-runtime-3.5.2.jar：使用 hive 方言需要添加
- Hive 2.1.0
  - flink-connector-hive_2.11-1.13.5.jar：Flink 的 Hive Connector
  - hive-exec-2.1.0.jar：Hive 依赖
  - antlr-runtime-3.5.2.jar：使用 hive 方言需要添加
- Hive 2.0.0
  - flink-connector-hive_2.11-1.13.5.jar：Flink 的 Hive Connector
  - hive-exec-2.0.0.jar：Hive 依赖
  - antlr-runtime-3.5.2.jar：使用 hive 方言需要添加
- Hive 1.2.1
  - flink-connector-hive_2.11-1.13.5.jar：Flink 的 Hive Connector
  - hive-metastore-1.2.1.jar：Hive 依赖
  - hive-exec-1.2.1.jar：Hive 依赖
  - libfb303-0.9.2.jar：在部分版本中没有打包到 hive-exec 中，需要单独添加
  - orc-core-1.4.3-nohive.jar：Orc 依赖
  - aircompressor-0.8.jar：orc-core 传递依赖
  - antlr-runtime-3.5.2.jar：使用 hive 方言需要添加
- Hive 1.1.0
  - flink-connector-hive_2.11-1.13.5.jar：Flink 的 Hive Connector
  - hive-metastore-1.1.0.jar：Hive 依赖
  - hive-exec-1.1.0.jar：Hive 依赖
  - libfb303-0.9.2.jar：在部分版本中没有打包到 hive-exec 中，需要单独添加
  - orc-core-1.4.3-nohive.jar：Orc 依赖
  - aircompressor-0.8.jar：orc-core 传递依赖
  - antlr-runtime-3.5.2.jar：使用 hive 方言需要添加
- Hive 1.0.0
  - flink-connector-hive_2.11-1.13.5.jar：Flink 的 Hive Connector
  - hive-metastore-1.0.0.jar：Hive 依赖
  - hive-exec-1.0.0.jar：Hive 依赖
  - libfb303-0.9.0.jar：在部分版本中没有打包到 hive-exec 中，需要单独添加
  - orc-core-1.4.3-nohive.jar：Orc 依赖
  - aircompressor-0.8.jar：orc-core 传递依赖
  - antlr-runtime-3.5.2.jar：使用 hive 方言需要添加

下面列举了可用的jar包及其适用的Hive版本，我们可以根据使用的Hive版本，下载对应的jar包即可。

在这我们使用推荐的第一种方式，并根据 Hive Metastore 的版本选择对应的 Hive jar。比如本文使用的 Hive 版本为 2.3.4，所以只需要下载 flink-sql-connector-hive-2.3.6 对应的 jar 即可（flink-sql-connector-hive-2.3.6_2.11-1.13.5.jar），并将其放置在 Flink 安装目录的 lib 文件夹下：
```
cp flink-sql-connector-hive-2.3.6_2.11-1.13.5.jar /opt/flink/lib/
```

## 2. SQL CLI 连接 Hive

将上面的 jar 包添加至 Flink 的 lib 目录下之后，就可以使用 Flink 操作 Hive 的数据表了。现在我们可以启动 SQL 客户端来与 Hive 进行交互。SQL 客户端脚本位于 Flink 的 bin 目录中，可以通过嵌入式模式来启动 SQL 客户端 CLI：
```
./bin/sql-client.sh embedded
```
Flink 1.13 版本不再通过 YAML 的方式来配置 SQL 客户端，而是使用一个初始化脚本在主 SQL 脚本执行前来配置环境，使用 -i 参数执行。具体参考[Flink SQL 客户端如何使用](https://mp.weixin.qq.com/s/6hXHlLx9ihS_bOo1Pgh5zA)。如下使用 DDL 方式直接创建 HiveCatalog：
```sql
-- 创建 Catalog
CREATE CATALOG my_hive_catalog WITH (
    'type' = 'hive',
    'default-database' = 'default',
    'hive-conf-dir' = '/opt/hive/conf'
);
-- 设置 HiveCatalog 为当前会话的 Catalog
USE CATALOG my_hive_catalog;
```

![](1)

除了上述几个配置选项之外，在使用 DDL 创建 HiveCatalog 时还支持其他选项：

| 选项 | 是否必填 | 默认值 | 类型 | 描述 |
| :--------------- | :------ | :------ | :------ | :------ |
| type             | 是 | (none)  | String | Catalog 的类型。创建 HiveCatalog 时必须设置为 'hive' |
| name             | 是 | (none)  | String | Catalog 的唯一名称。仅适用于 YAML 文件 |
| hive-conf-dir    | 否 | (none)  | String | 包含 hive-site.xml 的配置文件的 conf 目录路径。如果未指定该选项，则在类路径中搜索 hive-site.xml |
| default-database | 否 | default | String | 将 Catalog 设置为当前 Catalog 时使用的默认数据库 |
| hive-version     | 否 | (none)  | String | HiveCatalog 能够自动检测正在使用的 Hive 版本。建议不要指定 Hive 版本，除非自动检测失败 |
| hadoop-conf-dir  | 否 | (none)  | String | Hadoop conf 目录的路径。仅支持本地文件系统路径。设置 Hadoop conf 的推荐方法是通过 HADOOP_CONF_DIR 环境变量。仅当环境变量不起作用时才使用该选项，例如如果要单独配置每个 HiveCatalog。|

## 3. 操作 Hive 中的表

接下来，我们可以查看注册的catalog：
```sql
Flink SQL> SHOW CATALOGS;
+-----------------+
|    catalog name |
+-----------------+
| default_catalog |
| my_hive_catalog |
+-----------------+
2 rows in set
```
假设 Hive 中有一张 behavior 表，我们在 Flink 中查询该表：
```sql
Flink SQL> SELECT * FROM behavior LIMIT 2;
2022-04-27 23:44:40,827 INFO  org.apache.hadoop.mapred.FileInputFormat                     [] - Total input paths to process : 1
[INFO] Result retrieval cancelled.
```
![](2)

现在我们在 Flink 中向 Hive behavior 表中插入一条数据：
```sql
Flink SQL> INSERT INTO behavior SELECT 'uid-a', 'wid-a', '2022-04-27 23:12:01', 'Hello Flink';
[INFO] Submitting SQL update statement to the cluster...
[INFO] SQL update statement has been successfully submitted to the cluster:
Job ID: 840f5ea8e5cc7c15f3a0e3d0ac78e6e4
```
我们通过在 Hive 中查询 behavior 表，观察是否插入成功：
```sql
hive> SELECT * FROM behavior WHERE uid = 'uid-a';
OK
uid-a	wid-a	2022-04-27 23:12:01	Hello Flink
Time taken: 0.608 seconds, Fetched: 1 row(s)
```
从上面可以知道我们插入成功了。


..
