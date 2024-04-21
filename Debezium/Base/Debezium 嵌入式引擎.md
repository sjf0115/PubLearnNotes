---
layout: post
author: wy
title: Debezium 嵌入式引擎
date: 2022-02-01 15:37:21
tags:
  - Debezium

categories: Debezium
permalink: debezium-engine
---

> Debezium 版本: 1.8

Debezium Connector 通常部署到 Kafka Connect 服务并配置一个或多个 Connector 来监控上游数据库，并将看到的所有变更生成变更事件。这些变更事件会被写入 Kafka，然后可以被不同应用程序独立消费。Kafka Connect 提供了出色的容错性和可扩展性，因为它以分布式服务运行并确保所有已注册和配置的 Connector 一直在运行中。例如，即使集群中的一个 Kafka Connect 端点出现故障，其余的 Kafka Connect 端点会重新启动出现故障的 Connector，从而最大限度地减少停机时间并撤销管理权限。

并非每个应用程序都需要这种级别的容错和可靠性，并且我们可能不想依赖 Kafka Broker 和 Kafka Connect 服务的外部集群。相反，一些应用程序更想将 Debezium Connector 直接嵌入到应用程序中。我们仍然想要获取相同的数据变更事件，但更喜欢让 Connector 将它们直接发送到应用程序，而不是将它们保存在 Kafka 中。

debezium-api 模块定义了一个小型的 API，可以让应用程序使用 Debezium 引擎轻松配置和运行 Debezium Connector。

### 1. 依赖

要想使用 Debezium Engine 模块，需要将 debezium-api 模块添加到应用程序的依赖项中。在 debezium-embedded 模块中有一个开箱即用的 API 实现，也需要添加到依赖项中。需要将以下内容添加到应用程序的 POM 中：
```xml
<dependency>
    <groupId>io.debezium</groupId>
    <artifactId>debezium-api</artifactId>
    <version>${version.debezium}</version>
</dependency>

<dependency>
    <groupId>io.debezium</groupId>
    <artifactId>debezium-embedded</artifactId>
    <version>${version.debezium}</version>
</dependency>
```

除此之外我们需要将应用程序使用的 Debezium Connector 添加依赖项中。如果我们想要获取 MySQL 的变更，就需要以下内容添加到依赖项中：
```xml
<dependency>
    <groupId>io.debezium</groupId>
    <artifactId>debezium-connector-mysql</artifactId>
    <version>${version.debezium}</version>
</dependency>
```
> 本文章我们以 MySQL 为例。

### 2. Code

我们的应用程序需要为每个运行的 Connector 实例配置一个嵌入式引擎。Debezium Connector 使用 io.debezium.engine.DebeziumEngine<R> 类作为简单易用的包装器，并管理 Connector 的生命周期。我们使用构建器 API 创建 DebeziumEngine 实例，并提供如下内容：
- 接收到消息的格式，例如 JSON、Avro
- 定义引擎以及 Connector 环境的配置属性（可能从 properties 文件加载）
- 每个数据变更事件调用的方法

以下是配置和运行嵌入式 MySQL Connector 的代码示例：
```java

```
下面一起详细地看一下这段代码，从前几行开始：
```java
final Properties props = config.asProperties();
props.setProperty("name", "engine");
props.setProperty("connector.class", "io.debezium.connector.mysql.MySqlConnector");
props.setProperty("offset.storage", "org.apache.kafka.connect.storage.FileOffsetBackingStore");
props.setProperty("offset.storage.file.filename", "/tmp/offsets.dat");
props.setProperty("offset.flush.interval.ms", 60000);
```
无论使用哪个 Connector 都首先创建一个 Properties 对象来设置引擎所需的参数。第一个是引擎的名称，会在 Connector 生成的源记录内部状态中使用，因此建议在应用程序中使用一个有意义的名称。connector.class 参数是继承自 Kafka Connect org.apache.kafka.connect.source.SourceConnector 的类名；在这我们指定的是 Debezium 的 MySqlConnector 类。

当 Kafka Connect 的 Connector 运行时，从数据源读取信息并定期记录偏移量 Offset。如果 Connector 重新启动，会根据最后记录的 Offset 继续从上次读取的位置的消费。由于 Connector 不知道也不关心 Offset 是如何存储的，因此引擎需要提供一种方法来存储以及恢复 Offset。接下来的几个参数指定引擎使用 FileOffsetBackingStore 类在本地文件系统上的 /tmp/offsets.dat 文件中存储 Offset。此外，虽然 Connector 记录了每个数据源记录的 Offset，但引擎会定期将 Offset 刷新到后端存储中（在我们的例子中，每分钟一次）。这些参数可以根据我们的应用程序的需要进行定制。接下来的几行定义了 Connector 的配置参数，在我们的示例中以 MySqlConnector 为例：
```java
props.setProperty("database.hostname", "localhost")
props.setProperty("database.port", "3306")
props.setProperty("database.user", "root")
props.setProperty("database.password", "root")
props.setProperty("database.server.id", "85744")
props.setProperty("database.server.name", "debezium-mysql-connector")
props.setProperty("database.history",
      "io.debezium.relational.history.FileDatabaseHistory")
props.setProperty("database.history.file.filename",
      "/path/to/storage/dbhistory.dat")
```
在这里，我们设置了 MySQL 的主机名和端口号，并配置连接 MySQL 数据库的用户名和密码。需要注意的是，应该为 MySQL 账号授予如下权限：
- SELECT
- RELOAD
- SHOW DATABASES
- REPLICATION SLAVE
- REPLICATION CLIENT

```
-- 设置拥有同步权限的用户
CREATE USER 'cdc_user' IDENTIFIED BY 'cdc_root';
-- 赋予同步相关权限
GRANT SELECT, RELOAD, SHOW DATABASES, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'cdc_user';
```

```sql
CREATE DATABASE debezium_sample;
USE debezium_sample;

CREATE TABLE IF NOT EXISTS `stu`(
   `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
   `name` VARCHAR(100) NOT NULL,
   `gmt_create` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
   `gmt_modified` DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
   PRIMARY KEY (`id` )
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```

```sql
INSERT INTO stu (name) VALUES ('Bill');
INSERT INTO stu (name) VALUES ('Lucy');
```


> 读取数据库的一致性快照需要前三个权限。最后两个权限可以允许数据库读取服务器的 binlog。

该配置还包括 server.id 的数字标识符。由于 MySQL 的 binlog 是 MySQL 副本机制的一部分，为了读取 binlog，MySqlConnector 实例必须加入 MySQL 服务器组，这也就意味着该 Server ID 在组成 MySQL 服务器组的所有进程中必须是唯一的，并且是 1 到 2^32-1 之间的任意整数。在我们的代码中，我们设置为一个比较大的随机值。

该配置还为 MySQL 服务器指定了一个逻辑名称。Connector 在生成的每个数据源记录的 topic 字段中包含此逻辑名称，这样能使我们的应用程序识别这些记录的来源。在这我们命名为 'debezium-mysql-connector'。

当 MySqlConnector 类运行时，会读取 MySQL 服务器的 binlog，其中包括数据库所有的数据变更以及 Schema 变更。由于所有的数据变更都是根据记录变更时所属表 Schema 来构建的，因此 Connector 需要跟踪所有 Schema 变更，以便可以正确解码变更。Connector 记录 Schema 信息，以便 Connector 重新启动并从上次记录的 Offset 继续读取时，可以确切地知道该 Offset 所处的数据库 Schema 是什么样的。我们配置的最后两个参数定义了 Connector 如何记录数据库 Schema 历史，在我们的示例中 Connector 使用 FileDatabaseHistory 类将数据库 Schema 变更历史存储在本地文件系统的 /path/to/storage/dbhistory.dat 文件中。最后，使用 build() 方法构建不可变配置。我们也可以使用 Configuration.read(… ) 方法从 properties 文件中读取配置，来替换现在以编程方式构建。

配置好之后就可以创建我们的引擎，如下代码所示：
```java
DebeziumEngine.Builder<ChangeEvent<String, String>> builder = DebeziumEngine.create(Json.class);
builder.using(props);
builder.notifying(record -> {
    System.out.println(record);
});
DebeziumEngine<ChangeEvent<String, String>> engine = builder.build();

ExecutorService executor = Executors.newSingleThreadExecutor();
executor.execute(engine);
```
所有变更事件都会传递给指定的处理方法，该方法必须实现 java.util.function.Consumer<R> 接口，其中 <R> 必须匹配调用 create() 时指定的格式类型。需要注意的是，应用程序的处理函数不能抛出任何异常。如果抛出异常，引擎会记录该方法抛出的异常，并继续对下一个数据源记录进行操作，但应用程序已经没有了再次处理异常数据源记录的机会，这也就意味着应用程序可能会与数据库不一致。

到目前为止，我们有了一个 DebeziumEngine 对象，该对象已完成配置并准备好运行，但它不执行任何操作。DebeziumEngine 设计由 Executor 或 ExecutorService 异步执行：
```java
ExecutorService executor = Executors.newSingleThreadExecutor();
executor.execute(engine);
```

应用程序可以通过调用 close() 方法安全优雅地停止引擎：
```java
engine.close();
```
或者当引擎支持 Closeable 接口时，会在 try 块离开时自动调用。

引擎的 Connector 停止从数据源系统读取信息，将所有剩余的变更事件转发到我们的处理函数，并将最新的 Offset 刷新到后端存储。只有在所有这些都完成之后，引擎的 run() 方法才会返回。如果应用程序需要在退出之前等待引擎完全停止，我们可以使用 ExecutorService shutdown 和 awaitTermination 方法来做到这一点：
```java
try {
    executor.shutdown();
    while (!executor.awaitTermination(5, TimeUnit.SECONDS)) {
        logger.info("Waiting another 5 seconds for the embedded engine to shut down");
    }
}
catch ( InterruptedException e ) {
    Thread.currentThread().interrupt();
}
```
或者，我们可以在创建 DebeziumEngine 时注册 CompletionCallback 作为回调，以便在引擎终止时收到通知。回想一下，当 JVM 关闭时，它只等待守护线程。因此，如果我们的应用程序退出，请确保等待引擎完成或在守护线程上运行引擎。我们的应用程序应正确停止引擎以确保正常且完全关闭，并且每个数据源记录都准确地发送到应用程序一次。例如，不要依赖于关闭 ExecutorService，因为这会中断正在运行的线程。虽然 DebeziumEngine 在其线程中断时确实会终止，但引擎可能不会完全终止，并且当我们的应用程序重新启动时，可能会看到一些在关闭之前处理过的相同数据源记录。

### 3. 输出消息格式

DebeziumEngine.create() 可以接收多个不同的参数，这些参数会影响消费者接收消息的格式。可允许的值有：
- Connect.class：输出值是包装为 Kafka Connect SourceRecord 的变更事件
- Json.class：输出值是一对键值对，编码为 JSON 字符串
- Avro.class：输出值是一对键值对，编码为 Avro 序列化记录
- CloudEvents.class：输出值是一对键值对，编码为 Cloud Events 消息

在内部，引擎使用适当的 Kafka Connect 转换器实现。可以对引擎进行配置以改变转换器的行为。JSON 输出格式的一个例子：
```
final Properties props = new Properties();
...
props.setProperty("converter.schemas.enable", "false");
...
final DebeziumEngine<ChangeEvent<String, String>> engine = DebeziumEngine.create(Json.class)
    .using(props)
    .notifying((records, committer) -> {
        for (ChangeEvent<String, String> r : records) {
            System.out.println("Key = '" + r.key() + "' value = '" + r.value() + "'");
            committer.markProcessed(r);
        }
```

### 4. Message transformations

在将消息传递给处理程序之前，可以通过 Kafka Connect Kafka Connect Simple Message Transforms 管道处理它们。每个 Simple Message Transforms 都可以原封不动的传递消息，也可以修改或者过滤。该链是使用属性转换配置的。 该属性包含要应用的转换的逻辑名称的逗号分隔列表。 属性 transforms.<logical_name>.type 然后定义每个转换的实现类的名称，transforms.<logical_name>.* 传递给转换的配置选项。

### 5. Advanced Record Consuming

对于某些用例，例如，尝试批量写入记录或使用异步 API 写入记录时，上述功能接口可能具有挑战性。在这些情况下，使用 io.debezium.engine.DebeziumEngine.ChangeConsumer<R> 接口可能更容易。此接口只有一个方法：
```java
void handleBatch(List<R> records, RecordCommitter<R> committer) throws InterruptedException;
```
RecordCommitter 对象将在每条记录和每批记录完成后被调用。RecordCommitter 接口是线程安全的，允许灵活处理记录。你可以选择覆盖已处理记录的偏移量。 这是通过首先通过调用 RecordCommitter#buildOffsets() 构建一个新的 Offsets 对象来完成的，使用 Offsets#set(String key, Object value) 更新偏移量，然后调用 RecordCommitter#markProcessed(SourceRecord record, Offsets sourceOffsets)，使用更新的 偏移量。

要使用 ChangeConsumer API，必须将接口的实现传递给 notifying API，如下所示：
```java
class MyChangeConsumer implements DebeziumEngine.ChangeConsumer<RecordChangeEvent<SourceRecord>> {
  public void handleBatch(List<RecordChangeEvent<SourceRecord>> records, RecordCommitter<RecordChangeEvent<SourceRecord>> committer) throws InterruptedException {
    ...
  }
}
// Create the engine with this configuration ...
DebeziumEngine<RecordChangeEvent<SourceRecord>> engine = DebeziumEngine.create(ChangeEventFormat.of(Connect.class))
        .using(props)
        .notifying(new MyChangeConsumer())
        .build();
```
如果使用 JSON 格式，则代码如下所示：
```java
class JsonChangeConsumer implements DebeziumEngine.ChangeConsumer<ChangeEvent<String, String>> {
  public void handleBatch(List<ChangeEvent<String, String>> records,
    RecordCommitter<ChangeEvent<String, String>> committer) throws InterruptedException {
    ...
  }
}
// Create the engine with this configuration ...
DebeziumEngine<ChangeEvent<String, String>> engine = DebeziumEngine.create(Json.class)
        .using(props)
        .notifying(new JsonChangeConsumer())
        .build();
```




原文：[Debezium Engine](https://debezium.io/documentation/reference/1.8/development/engine.html)
