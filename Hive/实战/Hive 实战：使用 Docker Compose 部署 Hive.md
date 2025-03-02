在现代软件开发的众多环节中，容器化技术已经成为了加速开发、简化部署的关键工具。Docker 作为市场上最流行的容器平台之一，提供了一种高效的方式来打包、分发和管理应用。在这片博文中，我们将探索如何利用 Docker Compose 来部署一个 Apache Hive 服务。在开发环境中，使用 Docker Compose 部署 Hive 不仅能够保证环境的一致性，还允许开发者快速部署和撤销实例，极大地提高了开发效率。

## 1. Hive 简介

Apache Hive 是建立在 Hadoop 生态系统之上的一个开源数据仓库工具，主要用于处理大规模结构化或半结构化数据。它将用户编写的类 SQL 查询（称为 HiveQL）转换为底层计算框架（如 MapReduce、Tez 或 Spark）的任务，从而实现对海量数据的分析与处理。Hive 的核心目标是 简化 Hadoop 的数据处理，让熟悉 SQL 的用户无需深入掌握 Java 或 MapReduce 即可操作分布式数据。

## 2. Docker Compose 简介

Docker Compose 是一个用于定义和运行多容器 Docker 应用程序的工具。通过 Compose，您可以通过一个 YAML 文件来配置您的应用的服务。然后，使用一个简单的命令，就可以创建并启动所有配置中的服务。这让组织和管理容器变成了一件轻而易举的事情。

## 3. Docker Compose 部署 Hive

接下来，我们将一步步通过 Docker Compose 来部署一个 Hive 服务。在开始部署之前，请确保以下环境已经准备好：
- 安装 Docker：确保 Docker 已经安装并运行在你的机器上。可以通过以下命令验证 Docker 是否安装：
   ```bash
   docker --version
   ```
- 安装 Docker Compose：确保 Docker Compose 已经安装并配置完成。可以通过以下命令验证 Docker Compose 是否安装：
   ```bash
   docker-compose --version
   ```

### 3.1 创建项目目录

首先为项目创建一个目录。在这里，在我们的工作目录 `/opt/workspace/docker` 下创建一个名为 `hive` 的项目：
```shell
smartsi@localhost docker % mkdir hive
smartsi@localhost docker % cd hive
```

> 该目录是应用程序镜像的上下文。该目录应该只包含用于构建该镜像的资源。

### 3.2 构建 Compose 文件

Docker Compose 简化了对整个应用程序堆栈的控制，使得在一个易于理解的 YAML 配置文件中轻松管理服务、网络和数据卷。要使用 Docker Compose 部署，首先需创建一个`docker-compose.yml`文件，从 [官方]()下载配置文件，按照自己的需求修改即可。在这我们的配置如下所示：
```yaml
version: '3.9'
services:
  postgres:
    image: postgres:15.7
    restart: unless-stopped
    container_name: postgres
    hostname: postgres
    environment:
      POSTGRES_DB: 'hive_metastore'
      POSTGRES_USER: 'admin'
      POSTGRES_PASSWORD: 'admin'
    ports:
      - '5432:5432'
    volumes:
      - pg:/var/lib/postgresql
    networks:
      - hive-network

  metastore:
    image: apache/hive:4.0.0
    depends_on:
      - postgres
    restart: unless-stopped
    container_name: metastore
    hostname: metastore
    environment:
      DB_DRIVER: postgres
      SERVICE_NAME: 'metastore'
      SERVICE_OPTS: '-Xmx1G -Djavax.jdo.option.ConnectionDriverName=org.postgresql.Driver
                     -Djavax.jdo.option.ConnectionURL=jdbc:postgresql://postgres:5432/hive_metastore
                     -Djavax.jdo.option.ConnectionUserName=admin
                     -Djavax.jdo.option.ConnectionPassword=admin'
    ports:
        - '9083:9083'
    volumes:
        - warehouse:/opt/hive/data/warehouse
        - type: bind
          source: ./lib/postgresql-42.5.6.jar
          target: /opt/hive/lib/postgres.jar
    networks:
      - hive-network

  hiveserver2:
    image: apache/hive:4.0.0
    depends_on:
      - metastore
    restart: unless-stopped
    container_name: hiveserver2
    environment:
      HIVE_SERVER2_THRIFT_PORT: 10000
      SERVICE_OPTS: '-Xmx1G -Dhive.metastore.uris=thrift://metastore:9083'
      IS_RESUME: 'true'
      SERVICE_NAME: 'hiveserver2'
    ports:
      - '10000:10000'
      - '10002:10002'
    volumes:
      - warehouse:/opt/hive/data/warehouse
    networks:
      - hive-network

volumes:
  pg:
  warehouse:

networks:
  hive-network:
    name: hive-network
```


#### 3.2.1 服务定义（Services）

`services` 用于定义 Hadoop 集群的各个组件，每个组件对应一个容器。上面的配置定义了5个服务：
- `postgres`：HDFS 的 NameNode，负责管理文件系统的元数据。
- `metastore`：YARN 的 ResourceManager，负责集群资源管理和任务调度。
- `hiveserver2`：YARN 的 NodeManager，负责管理单个节点上的资源和任务。

Docker Compose 会将每个服务部署在各自的容器中，在这里我们自定义了与服务名称一致的容器名称，因此 Docker Compose 会部署3个名为 `namenode`、`datanode`、`resourcemanager`、`nodemanager` 以及 `historyserver` 的容器。

##### 3.2.1.1 Postgres 服务

```yaml
postgres:
  image: postgres:15.7
  restart: unless-stopped
  container_name: postgres
  hostname: postgres
  environment:
    POSTGRES_DB: 'hive_metastore'
    POSTGRES_USER: 'admin'
    POSTGRES_PASSWORD: 'admin'
  ports:
    - '5432:5432'
  volumes:
    - pg:/var/lib/postgresql
  networks:
    - hive-network
```

核心配置：
- `image`：使用预构建的 15.7 版本 `postgres` 镜像部署 `Postgres` 服务。
- `container_name`：容器名称固定为 `postgres`，便于其他服务引用。
- `networks`：连接到自定义桥接网络 `hive-network`，确保容器间通信。
- `restart`：`unless-stopped` 指定容器异常退出时自动重启（除非手动停止）。
- `environment`：
  - `POSTGRES_DB`：创建名为 `hive_metastore` 的数据库，用于存储 Hive 元数据。
  - `POSTGRES_USER/POSTGRES_PASSWORD`：为数据库设置用户名与密码。
- `ports`：
  - `5432:5432`：暴露 PostgreSQL 默认端口，允许外部访问。
- `volumes`：
  - `pg:/var/lib/postgresql`：将宿主机数据卷 `pg` 挂载到容器内的 `/var/lib/postgresql`。将数据库数据持久化到名为 pg 的数据卷中，避免容器重启后数据丢失。

##### 3.2.1.2 Metastore 服务

```yaml
metastore:
  image: apache/hive:4.0.0
  depends_on:
    - postgres
  restart: unless-stopped
  container_name: metastore
  hostname: metastore
  environment:
    DB_DRIVER: postgres
    SERVICE_NAME: 'metastore'
    SERVICE_OPTS: '-Xmx1G -Djavax.jdo.option.ConnectionDriverName=org.postgresql.Driver
                   -Djavax.jdo.option.ConnectionURL=jdbc:postgresql://postgres:5432/hive_metastore
                   -Djavax.jdo.option.ConnectionUserName=admin
                   -Djavax.jdo.option.ConnectionPassword=admin'
  ports:
      - '9083:9083'
  volumes:
      - warehouse:/opt/hive/data/warehouse
      - ./lib/postgresql-42.5.6.jar:/opt/hive/lib/postgres.jar
  networks:
    - hive-network
```

核心配置：
- `image`：使用预构建的 4.0.0 版本 `apache/hive` 镜像部署 `Metastore` 服务。
- `container_name`：容器名称固定为 `metastore`，便于其他服务引用。
- `networks`：连接到自定义桥接网络 `hive-network`，确保容器间通信。
- `restart`：`unless-stopped` 指定容器异常退出时自动重启（除非手动停止）。
- `depends_on`:
  - `postgres`：确保 PostgreSQL 服务先启动。
- `environment`：
  - `DB_DRIVER`：指定元数据存储使用 `PostgreSQL`。
  - `ERVICE_NAME`：声明服务角色为元数据存储。
  - `SERVICE_OPTS`: JVM 启动参数
    - `-Xmx1G`: 分配最大 1GB 堆内存。
    - `-Djavax.jdo...`: 配置 JDBC 连接参数，指向 `PostgreSQL` 服务。
- `ports`：
  - `9083:9083`：暴露 Metastore 的 Thrift 服务端口。
- `volumes`：
  - `warehouse`：持久化 Hive 数据仓库目录
  - `./lib/postgresql-42.5.6.jar:/opt/hive/lib/postgres.jar`：挂载 PostgreSQL JDBC 驱动到 Hive 的 lib 目录。


需要注意的是 Hive 需要通过 PostgreSQL JDBC 驱动连接 PostgreSQL。在这里必须手动下载驱动并放到 `./lib` 目录中。你还可以选择另外一种方式：
```yaml
volumes:
  - type: bind
  - source: `mvn help:evaluate -Dexpression=settings.localRepository -q -DforceStdout`/org/postgresql/postgresql/42.5.1/postgresql-42.5.6.jar
  - target: /opt/hive/lib/postgres.jar
```

上述 source 命令是用于通过 Maven 工具处理 PostgreSQL JDBC 驱动依赖，并将其本地存储路径导出为环境变量。第一步是调用 Maven 的 dependency 插件将指定版本的 PostgreSQL 驱动强制下载到本地 Maven 仓库：
```
mvn dependency:copy -Dartifact="org.postgresql:postgresql:42.5.1"
```
第二步是获取本地仓库路径并设置环境变量：
```
export POSTGRES_LOCAL_PATH=`mvn help:evaluate -Dexpression=settings.localRepository -q -DforceStdout`/org/postgresql/postgresql/42.5.1/postgresql-42.5.1.jar
```
> `mvn help:evaluate -Dexpression=settings.localRepository` 获取 Maven 本地仓库路径（默认：`~/.m2/repository`），`-q -DforceStdout` 静默模式并强制标准输出

最终 source 值为：
```
~/.m2/repository/org/postgresql/postgresql/42.5.1/postgresql-42.5.1.jar
```

##### 3.2.1.3 HiveServer 服务

```yaml
hiveserver2:
  image: apache/hive:4.0.0
  depends_on:
    - metastore
  restart: unless-stopped
  container_name: hiveserver2
  environment:
    HIVE_SERVER2_THRIFT_PORT: 10000
    SERVICE_OPTS: '-Xmx1G -Dhive.metastore.uris=thrift://metastore:9083'
    IS_RESUME: 'true'
    SERVICE_NAME: 'hiveserver2'
  ports:
    - '10000:10000'
    - '10002:10002'
  volumes:
    - warehouse:/opt/hive/data/warehouse
  networks:
    - hive-network
```

核心配置：
- `image`：使用预构建的 4.0.0 版本 `apache/hive` 镜像部署 `HiveServer` 服务。
- `container_name`：容器名称固定为 `hiveserver2`，便于其他服务引用。
- `networks`：连接到自定义桥接网络 `hive-network`，确保容器间通信。
- `restart`：`unless-stopped` 指定容器异常退出时自动重启（除非手动停止）。
- `depends_on`:
  - `metastore`：确保 metastore 服务先启动。
- `environment`：
  - `HIVE_SERVER2_THRIFT_PORT`: 指定 Thrift 服务端口为 10000。
  - SERVICE_OPTS:
    - `-Dhive.metastore.uris=thrift://metastore:9083`: 告知 HiveServer2 如何找到 Metastore。
  - `IS_RESUME`：允许服务恢复（用于容器重启后保持会话）
  - `SERVICE_NAME`：声明服务角色为元数据存储。
- `ports`：
  - `10000:10000`: 暴露 Thrift 的服务端口，用于 JDBC/ODBC 连接。
  - `10002:10002`: 暴露 HiveServer2 的 Web UI 端口。
- `volumes`：
  - `warehouse`：持久化 Hive 数据仓库目录

#### 3.2.2 卷定义（Volumes）

```yaml
volumes:
  pg:
  warehouse:
```
声明三个 Docker 数据卷，用于持久化存储 PostgreSQL 数据库数据、Hive 数据仓库数据。

> Docker 会自动管理这些卷的实际存储位置（默认在 /var/lib/docker/volumes/），确保容器重启后数据不丢失。

#### 3.2.3 网络定义（Networks）

```yaml
networks:
  hive-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.23.0.0/24
```

核心配置：
- `hive-network`：创建名为 `hive-network` 的自定义 Docker 网络。
- `driver: bridge`：创建桥接网络，允许容器间通过容器名称通信。
- `ipam`：配置静态 IP 地址范围（172.22.0.0/24），避免容器 IP 变动导致服务不可用。

### 3.3 配置驱动

```
# 创建目录结构
mkdir -p ./lib
wget -P ./lib https://jdbc.postgresql.org/download/postgresql-42.5.6.jar
```

### 3.4 启动集群

在项目目录中执行 `docker-compose up -d` 命令启动 `Hive` 服务：
```bash
smartsi@smartsi:hive wy$ docker compose up -d
[+] Running 6/6
 ✔ Network hive-network     Created 0.6s
 ✔ Volume "hive_pg"         Created 0.0s
 ✔ Volume "hive_warehouse"  Created 0.0s
 ✔ Container postgres       Started 1.3s
 ✔ Container metastore      Started 0.3s
 ✔ Container hiveserver2    Started 0.1s
```
> `-d` 表示后台运行容器。

### 3.5 查看容器状态

通过 `docker-compose ps` 命令查看所有容器的状态：
```bash
localhost:hive wy$ docker-compose ps
WARN[0000] /opt/workspace/docker/hive/docker-compose.yml: `version` is obsolete
NAME          IMAGE               COMMAND                  SERVICE       CREATED         STATUS              PORTS
hiveserver2   apache/hive:4.0.0   "sh -c /entrypoint.sh"   hiveserver2   2 minutes ago   Up About a minute   0.0.0.0:10000->10000/tcp, 9083/tcp, 0.0.0.0:10002->10002/tcp
metastore     apache/hive:4.0.0   "sh -c /entrypoint.sh"   metastore     2 minutes ago   Up About a minute   10000/tcp, 0.0.0.0:9083->9083/tcp, 10002/tcp
postgres      postgres:15.7       "docker-entrypoint.s…"   postgres      2 minutes ago   Up About a minute   0.0.0.0:5432->5432/tcp
```
你会看到所有服务 `namenode`、`datanode`、`resourcemanager`、`nodemanager`、`historyserver` 都处于正常运行 "Up" 状态。

### 3.6 查看日志

如果需要查看某个服务的日志，可以执行以下命令：
```bash
docker-compose logs <service_name>
```
例如，查看 metastore 的日志：
```bash
localhost:hive wy$ docker-compose logs metastore
metastore  | + : postgres
metastore  | + SKIP_SCHEMA_INIT=false
metastore  | + [[ '' = \t\r\u\e ]]
metastore  | + VERBOSE_MODE=
metastore  | + export HIVE_CONF_DIR=/opt/hive/conf
metastore  | + HIVE_CONF_DIR=/opt/hive/conf
metastore  | + '[' -d '' ']'
metastore  | + export 'HADOOP_CLIENT_OPTS= -Xmx1G -Xmx1G -Djavax.jdo.option.ConnectionDriverName=org.postgresql.Driver -Djavax.jdo.option.ConnectionURL=jdbc:postgresql://postgres:5432/hive_metastore -Djavax.jdo.option.ConnectionUserName=admin -Djavax.jdo.option.ConnectionPassword=admin'
metastore  | + HADOOP_CLIENT_OPTS=' -Xmx1G -Xmx1G -Djavax.jdo.option.ConnectionDriverName=org.postgresql.Driver -Djavax.jdo.option.ConnectionURL=jdbc:postgresql://postgres:5432/hive_metastore -Djavax.jdo.option.ConnectionUserName=admin -Djavax.jdo.option.ConnectionPassword=admin'
metastore  | + [[ false == \f\a\l\s\e ]]
metastore  | + initialize_hive
metastore  | + COMMAND=-initOrUpgradeSchema
metastore  | ++ echo 4.0.0
metastore  | ++ cut -d . -f1
metastore  | + '[' 4 -lt 4 ']'
metastore  | + /opt/hive/bin/schematool -dbType postgres -initOrUpgradeSchema
...
metastore  | Metastore connection URL:	 jdbc:postgresql://postgres:5432/hive_metastore
metastore  | Metastore connection Driver :	 org.postgresql.Driver
metastore  | Metastore connection User:	 admin
metastore  | Initializing the schema to: 4.0.0
metastore  | Metastore connection URL:	 jdbc:postgresql://postgres:5432/hive_metastore
metastore  | Metastore connection Driver :	 org.postgresql.Driver
metastore  | Metastore connection User:	 admin
metastore  | Starting metastore schema initialization to 4.0.0
metastore  | Initialization script hive-schema-4.0.0.postgres.sql
...
metastore  | Initialization script completed
metastore  | Initialized schema successfully..
metastore  | + '[' 0 -eq 0 ']'
metastore  | + echo 'Initialized schema successfully..'
metastore  | + '[' metastore == hiveserver2 ']'
metastore  | + '[' metastore == metastore ']'
metastore  | + export METASTORE_PORT=9083
metastore  | + METASTORE_PORT=9083
metastore  | + exec /opt/hive/bin/hive --skiphadoopversion --skiphbasecp --service metastore
metastore  | 2025-03-01 06:43:53: Starting Hive Metastore Server
```

## 4. 验证集群运行状态

### 4.1 Web UI 验证集群

| 服务           | 访问地址                   | 默认账号密码 |
|----------------|---------------------------|-------------|
| hiveserver2  | http://localhost:10002     | 无需认证    |




### 4.2 使用 HiveSQL 验证

执行 `docker-compose exec namenode /bin/bash` 命令进入 `NameNode` 容器来检查 HDFS、YARN 状态：
```bash
localhost:hive wy$ docker exec -it hiveserver2 beeline -u 'jdbc:hive2://hiveserver2:10000/'
...
Connecting to jdbc:hive2://hiveserver2:10000/
Connected to: Apache Hive (version 4.0.0)
Driver: Hive JDBC (version 4.0.0)
Transaction isolation: TRANSACTION_REPEATABLE_READ
Beeline version 4.0.0 by Apache Hive
0: jdbc:hive2://hiveserver2:10000/>
0: jdbc:hive2://hiveserver2:10000/>
0: jdbc:hive2://hiveserver2:10000/>
```
Run some queries

```
0: jdbc:hive2://hiveserver2:10000/> show tables;
INFO  : Compiling command(queryId=hive_20250301065122_f0174fa8-3a56-446d-aeaf-d7427a59ad46): show tables
INFO  : Semantic Analysis Completed (retrial = false)
INFO  : Created Hive schema: Schema(fieldSchemas:[FieldSchema(name:tab_name, type:string, comment:from deserializer)], properties:null)
INFO  : Completed compiling command(queryId=hive_20250301065122_f0174fa8-3a56-446d-aeaf-d7427a59ad46); Time taken: 2.884 seconds
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Executing command(queryId=hive_20250301065122_f0174fa8-3a56-446d-aeaf-d7427a59ad46): show tables
INFO  : Starting task [Stage-0:DDL] in serial mode
INFO  : Completed executing command(queryId=hive_20250301065122_f0174fa8-3a56-446d-aeaf-d7427a59ad46); Time taken: 0.211 seconds
+-----------+
| tab_name  |
+-----------+
+-----------+
No rows selected (4.288 seconds)
```
```
0: jdbc:hive2://hiveserver2:10000/> create table hive_example(a string, b int) partitioned by(c int);
INFO  : Compiling command(queryId=hive_20250301065138_46ea9481-dbc5-42d9-806f-3915c16c1a1a): create table hive_example(a string, b int) partitioned by(c int)
INFO  : Semantic Analysis Completed (retrial = false)
INFO  : Created Hive schema: Schema(fieldSchemas:null, properties:null)
INFO  : Completed compiling command(queryId=hive_20250301065138_46ea9481-dbc5-42d9-806f-3915c16c1a1a); Time taken: 0.063 seconds
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Executing command(queryId=hive_20250301065138_46ea9481-dbc5-42d9-806f-3915c16c1a1a): create table hive_example(a string, b int) partitioned by(c int)
INFO  : Starting task [Stage-0:DDL] in serial mode
INFO  : Completed executing command(queryId=hive_20250301065138_46ea9481-dbc5-42d9-806f-3915c16c1a1a); Time taken: 0.373 seconds
No rows affected (0.453 seconds)
0: jdbc:hive2://hiveserver2:10000/> alter table hive_example add partition(c=1);
INFO  : Compiling command(queryId=hive_20250301065157_86a88ca3-5e66-40ab-ba56-1143304098de): alter table hive_example add partition(c=1)
INFO  : Semantic Analysis Completed (retrial = false)
INFO  : Created Hive schema: Schema(fieldSchemas:null, properties:null)
INFO  : Completed compiling command(queryId=hive_20250301065157_86a88ca3-5e66-40ab-ba56-1143304098de); Time taken: 0.206 seconds
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Executing command(queryId=hive_20250301065157_86a88ca3-5e66-40ab-ba56-1143304098de): alter table hive_example add partition(c=1)
INFO  : Starting task [Stage-0:DDL] in serial mode
INFO  : Completed executing command(queryId=hive_20250301065157_86a88ca3-5e66-40ab-ba56-1143304098de); Time taken: 0.137 seconds
No rows affected (0.361 seconds)
0: jdbc:hive2://hiveserver2:10000/> insert into hive_example partition(c=1) values('a', 1), ('a', 2),('b',3);
INFO  : Compiling command(queryId=hive_20250301065158_dc4cd1a9-6200-4e20-8ad2-01c7af90200b): insert into hive_example partition(c=1) values('a', 1), ('a', 2),('b',3)
INFO  : Semantic Analysis Completed (retrial = false)
INFO  : Created Hive schema: Schema(fieldSchemas:[FieldSchema(name:col1, type:string, comment:null), FieldSchema(name:col2, type:int, comment:null)], properties:null)
INFO  : Completed compiling command(queryId=hive_20250301065158_dc4cd1a9-6200-4e20-8ad2-01c7af90200b); Time taken: 3.322 seconds
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Executing command(queryId=hive_20250301065158_dc4cd1a9-6200-4e20-8ad2-01c7af90200b): insert into hive_example partition(c=1) values('a', 1), ('a', 2),('b',3)
INFO  : Query ID = hive_20250301065158_dc4cd1a9-6200-4e20-8ad2-01c7af90200b
INFO  : Total jobs = 1
INFO  : Launching Job 1 out of 1
INFO  : Starting task [Stage-1:MAPRED] in serial mode
INFO  : Subscribed to counters: [] for queryId: hive_20250301065158_dc4cd1a9-6200-4e20-8ad2-01c7af90200b
INFO  : Tez session hasn't been created yet. Opening session
INFO  : Dag name: insert into hive_exam...... ('a', 2),('b',3) (Stage-1)
INFO  : HS2 Host: [a74a6639c373], Query ID: [hive_20250301065158_dc4cd1a9-6200-4e20-8ad2-01c7af90200b], Dag ID: [dag_1740811924044_0001_1], DAG Session ID: [application_1740811924044_0001]
INFO  : Status: Running (Executing on YARN cluster with App id application_1740811924044_0001)

----------------------------------------------------------------------------------------------
        VERTICES      MODE        STATUS  TOTAL  COMPLETED  RUNNING  PENDING  FAILED  KILLED
----------------------------------------------------------------------------------------------
Map 1 .......... container     SUCCEEDED      1          1        0        0       0       0
Reducer 2 ...... container     SUCCEEDED      1          1        0        0       0       0
----------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------
        VERTICES      MODE        STATUS  TOTAL  COMPLETED  RUNNING  PENDING  FAILED  KILLED
----------------------------------------------------------------------------------------------
Map 1 .......... container     SUCCEEDED      1          1        0        0       0       0
Reducer 2 ...... container     SUCCEEDED      1          1        0        0       0       0  rehouse/hive_example/c=1/.hive-staging_hive_2025-03-01_06-51-58_764_1941847568859089208-1/-ext-10000
----------------------------------------------------------------------------------------------
VERTICES: 02/02  [==========================>>] 100%  ELAPSED TIME: 5.20 s
----------------------------------------------------------------------------------------------
INFO  : Completed executing command(queryId=hive_20250301065158_dc4cd1a9-6200-4e20-8ad2-01c7af90200b); Time taken: 9.382 seconds
3 rows affected (12.721 seconds)
0: jdbc:hive2://hiveserver2:10000/> select sum(b) from hive_example;
INFO  : Compiling command(queryId=hive_20250301065229_a832e894-16a7-41d3-9107-6620eb97c90a): select sum(b) from hive_example
INFO  : Semantic Analysis Completed (retrial = false)
INFO  : Created Hive schema: Schema(fieldSchemas:[FieldSchema(name:_c0, type:bigint, comment:null)], properties:null)
INFO  : Completed compiling command(queryId=hive_20250301065229_a832e894-16a7-41d3-9107-6620eb97c90a); Time taken: 0.444 seconds
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Executing command(queryId=hive_20250301065229_a832e894-16a7-41d3-9107-6620eb97c90a): select sum(b) from hive_example
INFO  : Query ID = hive_20250301065229_a832e894-16a7-41d3-9107-6620eb97c90a
INFO  : Total jobs = 1
INFO  : Launching Job 1 out of 1
INFO  : Starting task [Stage-1:MAPRED] in serial mode
INFO  : Subscribed to counters: [] for queryId: hive_20250301065229_a832e894-16a7-41d3-9107-6620eb97c90a
INFO  : Session is already open
INFO  : Dag name: select sum(b) from hive_example (Stage-1)
INFO  : HS2 Host: [a74a6639c373], Query ID: [hive_20250301065229_a832e894-16a7-41d3-9107-6620eb97c90a], Dag ID: [dag_1740811924044_0001_2], DAG Session ID: [application_1740811924044_0001]
INFO  : Status: Running (Executing on YARN cluster with App id application_1740811924044_0001)

INFO  : Completed executing command(queryId=hive_20250301065229_a832e894-16a7-41d3-9107-6620eb97c90a); Time taken: 0.9 seconds
+------+
| _c0  |
+------+
| 6    |
+------+
1 row selected (1.382 seconds)
0: jdbc:hive2://hiveserver2:10000/>
```

## 5. 集成 Hadoop 集群

如果 Hadoop 集群是远程独立部署的（与 Hive 不在同一 Docker 网络内），需要确保 Hive 服务能正确访问 Hadoop 的 HDFS 和 YARN 服务。

如果没有配置与 Hadoop 集群的链接，Hive 仍然可以运行，但它的行为会退化为 **本地模式**（Local Mode）。此时，Hive 的数据存储和计算均依赖于本地文件系统和本地执行引擎（如本地 MapReduce），而非分布式存储（HDFS）和分布式计算框架（如 YARN）。

Hive 的默认数据存储路径由 `hive.metastore.warehouse.dir` 配置项控制。如果未显式配置 Hadoop 的 `core-site.xml` 或 `hive-site.xml`，该路径默认指向本地文件系统：
```xml
<property>
  <name>hive.metastore.warehouse.dir</name>
  <value>/user/hive/warehouse</value>
</property>
```
在用户提供的 `docker-compose.yml` 中，Hive 服务挂载了名为 `warehouse` 的卷到容器路径 `/opt/hive/data/warehouse`，因此实际数据会存储在此挂载卷中。

进入 Hive 容器并检查数据目录来验证数据存储位置：
```
localhost:hive wy$ docker exec -it metastore bash
hive@metastore:/opt/hive$
hive@metastore:/opt/hive$ ls /opt/hive/data/warehouse
hive_example
```
如果未配置 Hadoop 的 `mapred-site.xml`，Hive 会使用本地执行引擎：
- 本地 MapReduce：任务在单个 JVM 中运行，不涉及分布式计算。
- 本地文件系统：所有输入/输出操作直接读写本地文件（而非 HDFS）。


在用户提供的 docker-compose.yml 中，Hive 未挂载 Hadoop 配置文件，因此实际行为如下：
- 数据存储：通过 warehouse 卷挂载到本地路径 /opt/hive/data/warehouse。
- 执行引擎：使用本地 MapReduce（无 YARN 调度）。
- HDFS 交互：完全缺失，所有数据操作基于本地文件系统。

### 5.1 调整 docker-compose 配置文件

调整之后的配置文件如下所示，下面会具体介绍为什么以及怎么调整：
```yaml
services:
  postgres:
    image: postgres:15.7
    restart: unless-stopped
    container_name: postgres
    hostname: postgres
    environment:
      POSTGRES_DB: 'hive_metastore'
      POSTGRES_USER: 'admin'
      POSTGRES_PASSWORD: 'admin'
    ports:
      - '5432:5432'
    volumes:
      - pg:/var/lib/postgresql
    networks:
      - pub-network

  metastore:
    image: apache/hive:3.1.3
    depends_on:
      - postgres
    restart: unless-stopped
    container_name: metastore
    hostname: metastore
    environment:
      DB_DRIVER: postgres
      SERVICE_NAME: 'metastore'
      SERVICE_OPTS: '-Xmx1G -Djavax.jdo.option.ConnectionDriverName=org.postgresql.Driver
                     -Djavax.jdo.option.ConnectionURL=jdbc:postgresql://postgres:5432/hive_metastore
                     -Djavax.jdo.option.ConnectionUserName=admin
                     -Djavax.jdo.option.ConnectionPassword=admin'
    ports:
        - '9083:9083'
    volumes:
        - warehouse:/opt/hive/data/warehouse
        - ./lib/postgresql-42.5.6.jar:/opt/hive/lib/postgres.jar
        - ./hadoop-conf:/opt/hive/conf  # 覆盖 Hive 的默认配置
    networks:
      - pub-network

  hiveserver2:
    image: apache/hive:3.1.3
    depends_on:
      - metastore
    restart: unless-stopped
    container_name: hiveserver2
    command:
      - /bin/sh
      - -c
      - |
        mkdir -p /home/hive/.beeline && chmod 777 /home/hive/.beeline;
        /opt/hive/bin/hiveserver2
    environment:
      HIVE_SERVER2_THRIFT_PORT: 10000
      SERVICE_OPTS: '-Xmx1G -Dhive.metastore.uris=thrift://metastore:9083'
      IS_RESUME: 'true'
      SERVICE_NAME: 'hiveserver2'
    ports:
      - '10000:10000'
      - '10002:10002'
    volumes:
      - warehouse:/opt/hive/data/warehouse
      - ./hadoop-conf:/opt/hive/conf  # 覆盖 Hive 的默认配置
    networks:
      - pub-network

volumes:
  pg:
  warehouse:

networks:
  pub-network:
    external: true  # 引用Hadoop所在的网络
```

#### 5.1.1 挂载 Hadoop 配置文件到 Hive 容器

Hive 需要 Hadoop 的核心配置文件（`core-site.xml`, `hdfs-site.xml`, `yarn-site.xml`）才能与远程集群通信。需要挂载到 Hive 的配置目录，并确保配置一致性。

第一步在本地创建配置文件目录。例如，在 Docker Compose 文件同级目录下创建 `hadoop-conf` 文件夹：
```bash
mkdir hadoop-conf
```
第二步从 Hadoop 集群复制配置文件到本地配置文件目录。在 Hadoop 集群的任意节点上可以找到如下配置文件（默认路径通常是 `$HADOOP_HOME/etc/hadoop/`）
- `core-site.xml`（包含 HDFS NameNode 地址）
- `hdfs-site.xml`（HDFS 详细配置）
- `yarn-site.xml`（YARN ResourceManager 地址）
- `mapred-site.xml`（MapReduce 配置）

你可以通过如下命令直接提取 Hadoop 配置文件到本地配置文件目录：
```bash
localhost:hive wy$ docker cp namenode:/etc/hadoop/core-site.xml ./hadoop-conf/
Successfully copied 4.1kB to /opt/workspace/docker/hive/hadoop-conf/
localhost:hive wy$
localhost:hive wy$ docker cp namenode:/etc/hadoop/hdfs-site.xml ./hadoop-conf/
Successfully copied 6.14kB to /opt/workspace/docker/hive/hadoop-conf/
localhost:hive wy$
localhost:hive wy$ docker cp resourcemanager:/etc/hadoop/yarn-site.xml ./hadoop-conf/
Successfully copied 39.9kB to /opt/workspace/docker/hive/hadoop-conf/
```
第三步修改 Hive 的 docker-compose.yml 配置文件并挂载配置文件。在 `metastore` 和 `hiveserver2` 服务的 `volumes` 中挂载配置文件：
```yaml
volumes:
 - warehouse:/opt/hive/data/warehouse
 - ./hadoop-conf:/opt/hive/conf  # 覆盖 Hive 的默认配置
```

#### 5.1.2 网络集成：打通 Hive 与 Hadoop 网络

确保 Hive 服务能通过容器名访问 Hadoop 组件（如namenode:9000）。修改 Hive 的 docker-compose.yml：
```yaml
# 使用 Hadoop 的外部网络，移除原 hive-network
networks:
  pub-network:
    external: true  # 引用 Hadoop 所在的 pub-network 网络

services:
  postgres:
    networks:
      - pub-network  # 所有服务加入 Hadoop 所在的 pub-network 网络
  metastore:
    networks:
      - pub-network
  hiveserver2:
    networks:
      - pub-network
```

### 5.2 配置 Hive 的 `hive-site.xml`

Hive 需要知道如何与 Hadoop 集群交互，例如指定 HDFS 仓库路径和 YARN 资源管理。创建或修改 `hive-site.xml`。在 `hadoop-conf` 目录下创建 `hive-site.xml`，添加以下关键配置：
```xml
<!-- hive-site.xml -->
<configuration>
  <!-- Hive 元数据仓库目录（指向 HDFS） -->
  <property>
    <name>hive.metastore.warehouse.dir</name>
    <value>hdfs://namenode:9000/user/hive/warehouse</value>
  </property>

  <!-- 使用 YARN 作为执行引擎 -->
  <property>
    <name>hive.execution.engine</name>
    <value>mr</value>  <!-- 或使用tez -->
  </property>

  <!-- 使用 YARN 作为执行引擎 -->
  <property>
    <name>mapreduce.framework.name</name>
    <value>yarn</value>
  </property>

  <!-- YARN ResourceManager 地址 -->
  <property>
    <name>yarn.resourcemanager.address</name>
    <value>resourcemanager:8032</value>
  </property>
</configuration>
```
> hive-site.xml 中不需要包含全部参数，只需覆盖与 Hadoop 集成相关的核心参数即可。Hive 会默认加载其内置的配置文件，而用户定义的 hive-site.xml 仅用于覆盖需要自定义的部分。

或通过环境变量注入（docker-compose.yml）：
```yaml
services:
  hiveserver2:
    environment:
      SERVICE_OPTS: >
        -Xmx1G
        -Dhive.metastore.uris=thrift://metastore:9083
        -Dhive.execution.engine=mr
        -Dmapreduce.framework.name=yarn
        -Dyarn.resourcemanager.address=resourcemanager:8032
```




#### 5.5 初始化HDFS目录

在Hadoop集群中创建Hive仓库目录并设置权限：
```bash
docker exec namenode hdfs dfs -mkdir -p /user/hive/warehouse
docker exec namenode hdfs dfs -chmod 777 /user/hive/warehouse
docker exec namenode hdfs dfs -mkdir -p /tmp
docker exec namenode hdfs dfs -chmod 777 /tmp
```

### 5.3 启动 Hive 服务

在项目目录中执行 `docker-compose up -d` 命令启动 `Hive` 服务：
```
(base) localhost:hive wy$ docker compose up -d
[+] Running 5/5
 ✔ Volume "hive_warehouse"  Created   0.0s
 ✔ Volume "hive_pg"         Created   0.0s
 ✔ Container postgres       Started   0.3s
 ✔ Container metastore      Started   0.4s
 ✔ Container hiveserver2    Started   0.1s
```

### 5.4 验证 Hadoop 集群连通性

在 Hive 容器内执行以下命令，验证是否能访问 Hadoop 服务。

1. 进入 Hive 容器
    ```bash
    localhost:hive wy$ docker exec -it metastore bash
    hive@metastore:/opt/hive$
    ```

2. 检查 HDFS 连通性：如果成功，会列出 HDFS 根目录内容：
    ```bash
    hive@metastore:/opt/hive$ hdfs dfs -ls hdfs://namenode:9000/
    Found 4 items
    drwxrwxrwt   - root root                0 2025-03-01 13:16 hdfs://namenode:9000/app-logs
    drwxr-xr-x   - root supergroup          0 2025-03-01 13:11 hdfs://namenode:9000/rmstate
    drwx------   - root supergroup          0 2025-03-01 13:43 hdfs://namenode:9000/tmp
    drwxr-xr-x   - root supergroup          0 2025-03-01 13:15 hdfs://namenode:9000/user
    ```

3. 检查 YARN 连通性
   ```bash
   yarn node -list
   ```
   应返回 YARN 集群的节点列表。


### 5.5 验证 Hive 集成 Hadoop**

通过 Beeline 连接 HiveServer2 并执行操作，验证数据是否写入 HDFS。

1. 启动 Beeline 客户端
   ```bash
   docker exec -it hiveserver2 beeline -u 'jdbc:hive2://hiveserver2:10000/'
   ```

2. **创建测试表并插入数据**  
   ```sql
   CREATE TABLE test_remote (id INT, name STRING);
   INSERT INTO test_remote VALUES (1, 'hive'), (2, 'hadoop');
   ```

3. **检查 HDFS 数据目录**  
   在 Hadoop 集群节点上执行：
   ```bash
   hdfs dfs -ls /user/hive/warehouse/test_remote
   ```
   应看到数据文件（如 `000000_0`）。

4. **提交 MapReduce 作业（可选）**  
   在 Beeline 中执行查询，触发 MapReduce 或 Tez 作业：
   ```sql
   SELECT COUNT(*) FROM test_remote;
   ```
   检查 YARN 的 Web UI（通常为 `http://<resourcemanager-host>:8088`）是否有作业记录。
