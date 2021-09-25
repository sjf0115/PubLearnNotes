
从数据库获取数据到 Apache Kafka 无疑是 Kafka Connect 最流行的用例。Kafka Connect 提供了将数据导入和导出 Kafka 的可扩展且可靠的方式。由于只用到了 Connector 的特定 Plugin 以及一些配置（无需编写代码），因此这是一个比较简单的数据集成方案。

> 如果想了解 Kafka Connect 是什么以及做什么的，可以阅读 [Kafka Connect 构建大规模低延迟的数据管道](http://smartsi.club/announcing-kafka-connect-building-large-scale-low-latency-data-pipelines.html) 博文；如果想了解 Kafka Connect 是如何使用的，可以阅读 [Kafka Connect 如何构建实时数据管道](http://smartsi.club/how-to-build-a-pipeline-with-kafka-connect.html) 博文。





### 1. 安装 Connect 插件

从 Confluent hub 下载 [Kafka Connect JDBC](https://www.confluent.io/hub/confluentinc/kafka-connect-jdbc) 插件并将 zip 文件解压到 /opt/share/kafka/plugins 目录下：
```
/opt/share/kafka/plugins
└── confluentinc-kafka-connect-jdbc-10.2.2
    ├── doc
    │   ├── LICENSE
    │   └── README.md
    ├── etc
        …
    ├── lib
        …
    │   ├── kafka-connect-jdbc-10.2.2.jar
    │   ├── sqlite-jdbc-3.25.2.jar
    │   ├── postgresql-42.2.19.jar
    │   ├── xmlparserv2-19.7.0.0.jar
        …
    └── manifest.json
```
在 Kafka Connect 配置文件 connect-standalone.properties（或 connect-distributed.properties）中，修改 plugin.path 配置参数指向我们存放插件的目录：
```
plugin.path=/opt/share/kafka/plugins
```

> 有关详安装 Connect 插件细信息，请查阅 [Kafka Connect 如何安装 Connect 插件](http://smartsi.club/how-to-install-connector-plugins-in-kafka-connect)

### 2. 安装 JDBC 驱动

因为 Connector 需要与数据库进行通信，所以还需要 JDBC 驱动程序。JDBC Connector 插件也没有内置 MySQL 驱动程序，需要我们单独下载驱动程序。MySQL 为许多平台提供了 [JDBC 驱动程序](https://downloads.mysql.com/archives/c-j/)。

![](1)

选择 Platform Independent 选项，然后下载压缩的 TAR 文件。该文件包含 JAR 文件和源代码。将此 tar.gz 文件的内容解压到一个临时目录。将 jar 文件（例如，mysql-connector-java-8.0.17.jar），并且仅将此 JAR 文件复制到与 kafka-connect-jdbc jar 文件相同的文件夹下：
```
cp mysql-connector-java-8.0.17.jar /opt/share/kafka/plugins/confluentinc-kafka-connect-jdbc-10.2.2/lib/
```

### 3. 运行 Connect

我们可以使用位于 kafka bin 目录中的 connect-distributed.sh 脚本运行 Kafka Connect。我们需要在运行此脚本时提供一个 worker 配置文件：
```
bin/connect-distributed.sh config/connect-distributed.properties
```
我们使用 config 目录下的默认 connect-distributed.properties 配置文件来指定 worker 属性，但做一下修改，如下所示：
```
bootstrap.servers=localhost:9092
group.id=connect-cluster
key.converter.schemas.enable=true
value.converter.schemas.enable=true
offset.storage.topic=connect-offsets
offset.storage.replication.factor=1
offset.storage.partitions=1
config.storage.topic=connect-configs
config.storage.replication.factor=1
status.storage.topic=connect-status
status.storage.replication.factor=1
status.storage.partitions=1
offset.flush.interval.ms=10000
# 核心配置
plugin.path=/opt/share/kafka/plugins
```

需要特别注意的是 plugin.path 参数是我们需要放置我们下载插件的路径。运行 Connect 后，我们可以通过调用 http://localhost:8083/connector-plugins REST API 来确认 JDBC 插件是否安装成功：
```json
[
  {
    "class": "io.confluent.connect.jdbc.JdbcSinkConnector",
    "type": "sink",
    "version": "10.2.2"
  },
  {
    "class": "io.confluent.connect.jdbc.JdbcSourceConnector",
    "type": "source",
    "version": "10.2.2"
  },
  {
    "class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
    "type": "sink",
    "version": "2.4.0"
  },
  {
    "class": "org.apache.kafka.connect.file.FileStreamSourceConnector",
    "type": "source",
    "version": "2.4.0"
  },
  {
    "class": "org.apache.kafka.connect.mirror.MirrorCheckpointConnector",
    "type": "source",
    "version": "1"
  },
  {
    "class": "org.apache.kafka.connect.mirror.MirrorHeartbeatConnector",
    "type": "source",
    "version": "1"
  },
  {
    "class": "org.apache.kafka.connect.mirror.MirrorSourceConnector",
    "type": "source",
    "version": "1"
  }
]
```
### 4. 创建 MySQL 表

准备测试数据，如下创建 kafka_connect_sample 数据库，并创建 student、address、course 三张表：
```sql
CREATE DATABASE kafka_connect_sample;
USE kafka_connect_sample;

CREATE TABLE IF NOT EXISTS `student`(
   `id` INT NOT NULL,
   `name` VARCHAR(100) NOT NULL,
   `address_id` INT NOT NULL,
   PRIMARY KEY (`id` )
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `address`(
   `id` INT NOT NULL,
   `prov` VARCHAR(100) NOT NULL,
   `city` VARCHAR(100) NOT NULL,
   PRIMARY KEY (`id` )
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `course`(
   `id` INT NOT NULL,
   `name` VARCHAR(100) NOT NULL,
   PRIMARY KEY (`id` )
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```
每个表都插入一些测试数据：
```sql
INSERT INTO address VALUES (1, '山东省', '青岛市'),
  (2, '北京市', '朝阳区');

INSERT INTO student VALUES (1, 'Bill', 1),
  (2, 'Lucy', 1), (3, 'Tom', 2), (4, 'Lily', 2), (5, 'Rock', 1);

INSERT INTO course VALUES (1, '语文'),
    (2, '英文'), (3, '物理'), (4, '数学');
```

### 5. 指定要获取的表

现在我们已经正确安装了 Connect JDBC 插件、驱动程序并成功运行了 Connect，我们可以配置 Kafka Connect 以从数据库中获取数据。如下是最少的配置：
```json
curl -X POST http://localhost:9083/connectors \
-H "Content-Type: application/json" -d '{
    "name": "jdbc_source_connector_mysql_bulk",
    "config": {
            "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
            "connection.url": "jdbc:mysql://localhost:3306/kafka_connect_sample",
            "connection.user": "root",
            "connection.password": "root",
            "topic.prefix": "connect-mysql-bulk-",
            "mode":"bulk"
        }
    }'
```
mode 参数指定了工作模式，在这我们使用 bulk 批量模式来同步全量数据（mode 还可以指定 timestamp、incrementing 或者 timestamp+incrementing 模式来实现增量同步，后续系列文章会单独介绍如何使用 Connect 实现 MySQL 的增量同步）。除了 mode 参数之外其他都是我们经常用到最小集合配置参数：
- connector.class：Connector 对应的 Java 类
- connection.url：JDBC 连接 URL。
- connection.user：JDBC 连接账号。
- connection.password：JDBC 连接密码。
- topic.prefix：为每个表创建一个 kafka Topic。Topic 以 topic.prefix + <table_name> 的格式命名。

> 当我们在分布式模式下运行时，我们需要使用 REST API 以及 JOSN 配置来创建 Connector。

使用此配置，每个表（用户有权访问的）都将被完整复制到 Kafka 中。通过如下命令列出 Kafka 集群上的 Topic，我们可以很容易地看到这一点：
```
localhost:kafka wy$ bin/kafka-topics.sh --bootstrap-server localhost:9092 --list --topic "connect-mysql-bulk.*"
connect-mysql-bulk-address
connect-mysql-bulk-course
connect-mysql-bulk-student
connect-mysql-bulk-test_table
```

请注意 onnect-mysql-bulk- 前缀。表内容的完整副本默认每 5 秒发生一次：

![](2)

我们可以通过将 poll.interval.ms 设置为每 10s 一次：
```json
curl -X POST http://localhost:8083/connectors \
-H "Content-Type: application/json" -d '{
    "name": "jdbc_source_connector_mysql_bulk",
    "config": {
            "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
            "connection.url": "jdbc:mysql://localhost:3306/kafka_connect_sample",
            "connection.user": "root",
            "connection.password": "root",
            "topic.prefix": "connect-mysql-bulk-",
            "mode":"bulk",
            "poll.interval.ms" : 10000
        }
    }'
```
上述配置获取了所有有权限的表，这可能不是我们想要的。也许我们只想包含来自特定模式的表，通过 catalog.pattern 配置从指定的数据库获取表：
```json
curl -X POST http://localhost:9083/connectors \
-H "Content-Type: application/json" -d '{
    "name": "jdbc_source_connector_mysql_catalog",
    "config": {
            "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
            "connection.url": "jdbc:mysql://localhost:3306/kafka_connect_sample",
            "connection.user": "root",
            "connection.password": "root",
            "topic.prefix": "connect-mysql-catalog-",
            "mode":"bulk",
            "poll.interval.ms" : 10000,
            "catalog.pattern" : "kafka_connect_sample"
        }
    }'
```
现在我们只从 kafka_connect_sample 数据库中获取表：
```
localhost:kafka wy$ bin/kafka-topics.sh --bootstrap-server localhost:9092 --list --topic "connect-mysql-catalog.*"
connect-mysql-catalog-address
connect-mysql-catalog-course
connect-mysql-catalog-student
```

还可以使用 table.whitelist（白名单）或 table.blacklist（黑名单）配置来控制获取的表。如下所示只把 student 表导入到 Kafka：
```json
curl -X POST http://localhost:9083/connectors \
-H "Content-Type: application/json" -d '{
    "name": "jdbc_source_connector_mysql_whitelist",
    "config": {
            "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
            "connection.url": "jdbc:mysql://localhost:3306/kafka_connect_sample",
            "connection.user": "root",
            "connection.password": "root",
            "topic.prefix": "connect-mysql-whitelist-",
            "mode":"bulk",
            "poll.interval.ms" : 10000,
            "catalog.pattern" : "kafka_connect_sample",
            "table.whitelist" : "student"
        }
    }'
```
正如预期的那样，现在只有 student 表从数据库流式传输到 Kafka：
```
localhost:kafka wy$ bin/kafka-topics.sh --bootstrap-server localhost:9092 --list --topic "connect-mysql-whitelist.*"
connect-mysql-whitelist-student
```

由于只是一张表，所以这个配置：
```
"catalog.pattern" : "kafka_connect_sample",
"table.whitelist" : "student",
```
上述配置跟如下配置效果一样：
```
"table.whitelist" : "kafka_connect_sample.student",
```
我们可以在单个 schema 中指定多个表，如下所示：
```
"catalog.pattern" : "kafka_connect_sample",
"table.whitelist" : "student, address",
```
或跨多个数据库：
```
"table.whitelist" : "kafka_connect_sample.student, test.test_db",
```


相关推荐：
- [Kafka Connect 构建大规模低延迟的数据管道](http://smartsi.club/announcing-kafka-connect-building-large-scale-low-latency-data-pipelines.html)
- [Kafka Connect 如何构建实时数据管道](http://smartsi.club/how-to-build-a-pipeline-with-kafka-connect.html)
