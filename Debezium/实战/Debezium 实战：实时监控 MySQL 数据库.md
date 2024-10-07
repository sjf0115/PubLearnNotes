## 1. 启动服务

使用 Debezium 需要三个独立的服务：ZooKeeper、Kafka 以及 Debezium Connector 服务。在本教程中，将使用 Docker 和 Debezium 容器镜像来设置每个服务的单个实例。要启动本教程所需的服务，您必须:
- 启动 Zookeeper
- 启动 Kafka
- 启动 MySQL 数据库
- 启动 MySQL 命令行客户端
- 启动 Kafka Connect


### 1.1 启动 Zookeeper

ZooKeeper 是第一个必须启动的服务。打开一个命令行终端，用它来启动容器中的 ZooKeeper。如下命令使用 `quay.io/debezium/zookeeper` 镜像的 2.7 版本运行一个容器:
```shell
docker run -it --rm --name zookeeper -p 2181:2181 -p 2888:2888 -p 3888:3888 quay.io/debezium/zookeeper:2.7
```
下面详细介绍命令中的参数
- `it`
  - 表示启动的是一个交互式的容器，这意味着终端的标准输入和输出连接到容器上。
- `--rm`
  - 当容器停止时会被删除。
- `--name zookeeper`
  - 容器的名称
- `-p 2181:2181 -p 2888:2888 -p 3888:3888`
  - 将容器的三个端口映射到 Docker 主机上的相同端口。这使得其他容器(以及容器外的应用程序)可以与 ZooKeeper 通信。

运行上述命令之后需要监听 2181 端口来验证 ZooKeeper 是否启动。如果你看到类似如下的输出表示你的 ZooKeeper 启动成功了:
```
Starting up in standalone mode
/usr/bin/java
ZooKeeper JMX enabled by default
Using config: /zookeeper/conf/zoo.cfg
2024-10-01 15:23:39,678 - INFO  [main:o.a.z.s.q.QuorumPeerConfig@177] - Reading configuration from: /zookeeper/conf/zoo.cfg
...
2024-10-01 15:23:39,821 - INFO  [main:o.a.z.s.NIOServerCnxnFactory@660] - binding to port 0.0.0.0/0.0.0.0:2181
```

### 1.2 启动 Kafka

启动 ZooKeeper 后，你可以在一个新的容器中启动 Kafka。打开一个命令行终端，用它来启动容器中的 Kafka。如下命令使用 `quay.io/debezium/kafka` 镜像的 2.7 版本运行一个容器:
```shell
docker run -it --rm --name kafka -p 9092:9092 --link zookeeper:zookeeper quay.io/debezium/kafka:2.7
```
下面详细介绍命令中的参数
- `it`
  - 表示启动的是一个交互式的容器，这意味着终端的标准输入和输出连接到容器上。
- `--rm`
  - 当容器停止时会被删除。
- `--name kafka`
  - 容器的名称
- `-p 9092:9092`
  - 将容器中的 9092 端口映射到Docker主机上的相同端口，以便容器外的应用程序可以与Kafka通信。
- `--link zookeeper:zookeeper`
  - 告诉容器它可以在同一个 Docker 主机上运行的 ZooKeeper 容器中找到 ZooKeeper。

运行上述命令之后需要监听 9092 端口来验证 Kafka 是否启动。如果你看到类似如下的输出表示你的 Kafka 启动成功了:
```
Starting in ZooKeeper mode using NODE_ID=1.
Using ZOOKEEPER_CONNECT=172.17.0.2:2181
Using configuration config/server.properties.
Using KAFKA_LISTENERS=PLAINTEXT://172.17.0.3:9092 and KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://172.17.0.3:9092
2024-10-01 15:33:51,948 - INFO  [main:Log4jControllerRegistration$@31] - Registered kafka:type=kafka.Log4jController MBean
2024-10-01 15:33:52,122 - INFO  [main:X509Util@78] - Setting -D jdk.tls.rejectClientInitiatedRenegotiation=true to disable client-initiated TLS renegotiation
2024-10-01 15:33:52,168 - INFO  [main:LoggingSignalHandler@73] - Registered signal handlers for TERM, INT, HUP
2024-10-01 15:33:52,169 - INFO  [main:Logging@66] - starting
2024-10-01 15:33:52,169 - INFO  [main:Logging@66] - Connecting to zookeeper on 172.17.0.2:2181
...
2024-10-01 15:33:53,095 - INFO  [main:AppInfoParser$AppInfo@124] - Kafka version: 3.7.0
2024-10-01 15:33:53,097 - INFO  [main:AppInfoParser$AppInfo@125] - Kafka commitId: 2ae524ed625438c5
2024-10-01 15:33:53,097 - INFO  [main:AppInfoParser$AppInfo@126] - Kafka startTimeMs: 1727796833091
2024-10-01 15:33:53,098 - INFO  [main:Logging@66] - [KafkaServer id=1] started
...
```

### 1.3 启动 MySQL 数据库

到目前为止你已经启动了 ZooKeeper 和 Kafka，但是你仍然需要一个数据库服务器，Debezium 可以从中捕获变化。在这个过程中，你将使用一个示例数据库启动 MySQL 服务器。打开一个新的终端，并使用它启动一个新的容器，该容器运行预先配置了 `inventory` 数据库的 MySQL 数据库服务器。

```shell
docker run -it --rm --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=debezium -e MYSQL_USER=mysqluser -e MYSQL_PASSWORD=mysqlpw quay.io/debezium/example-mysql:2.7
```
下面详细介绍命令中的参数
- `it`
  - 表示启动的是一个交互式的容器，这意味着终端的标准输入和输出连接到容器上。
- `--rm`
  - 当容器停止时会被删除。
- `--name mysql`
  - 容器的名称
- `-p 3306:3306`
  - 将容器中的 3306 端口映射到 Docker 主机上的相同端口，以便容器外的应用程序可以连接数据库。
- `-e MYSQL_ROOT_PASSWORD=debezium -e MYSQL_USER=mysqluser -e MYSQL_PASSWORD=mysqlpw`
  - 创建一个 Debezium MySQL Connector 所需最低权限的用户和密码。

运行上述命令之后来验证 MySQL 服务是否启动。在修改配置时，MySQL 服务会启动和停止几次。您应该看到类似以下的输出:
```
...
2024-10-01T15:26:43.384150Z 0 [System] [MY-011323] [Server] X Plugin ready for connections. Bind-address: '::' port: 33060, socket: /var/run/mysqld/mysqlx.sock
2024-10-01T15:26:43.384224Z 0 [System] [MY-010931] [Server] /usr/sbin/mysqld: ready for connections. Version: '8.2.0'  socket: '/var/run/mysqld/mysqld.sock'  port: 3306  MySQL Community Server - GPL.
```

### 1.4 启动MySQL命令行客户端
启动MySQL后，启动MySQL命令行客户端，以便访问示例库存数据库。



...
