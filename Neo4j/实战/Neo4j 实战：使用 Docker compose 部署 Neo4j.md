在今天的这篇文章中，我们将详细介绍如何使用 Docker Compose 来部署 Neo4j 图数据库。使用 Docker Compose 部署，我们可以方便地定义和运行多容器 Docker 应用程序，使部署 Neo4j 变得更为简单和高效。

## 1. Neo4j 简介

Neo4j 是一个高性能的 NoSQL 图数据库，专为存储和处理图形数据而构建。它以节点、关系和属性的形式存储数据，这使得它特别适合于表述和查询复杂的关系数据。在 Neo4j 中，节点通常代表实体，而关系代表实体之间的各种关联，属性则可用来存储关于节点和关系的信息。它是一个嵌入式的、基于磁盘的、具备完全的事务特性的 Java 持久化引擎。Neo4j 因其嵌入式、高性能、轻量级等优势，越来越受到关注.

## 2. Docker Compose 简介

Docker Compose 是一个用于定义和运行多容器 Docker 应用程序的工具。通过 Compose，您可以通过一个 YAML 文件来配置您的应用的服务。然后，使用一个简单的命令，就可以创建并启动所有配置中的服务。这让组织和管理容器变成了一件轻而易举的事情。

在开始之前，首先需要确保已经安装了 Docker Compose，如果没有安装或者不熟悉 Compose 的具体查阅 [Docker 实战：使用 Docker Compose 实现高效的多容器部署](https://smartsi.blog.csdn.net/article/details/138414972)。

## 3. Docker Compose 部署 Neo4j

接下来，我们将一步步通过 Docker Compose 来部署 Neo4j。

### 3.1 创建项目目录

首先为项目创建一个目录。在这里，在我们的工作目录 `/opt/workspace/docker` 下创建一个名为 `neo4j` 的项目 ：
```
smartsi@localhost docker % mkdir neo4j
smartsi@localhost docker % cd neo4j
```
> 该目录是应用程序镜像的上下文。该目录应该只包含用于构建该镜像的资源。

### 3.2 创建配置文件

服务端的配置文件核心包括全局配置文件 `config.xml` 和用户配置文件 `users.xml` 等，不建议你直接修改这两个配置文件。ClickHouse 为我们提供了一种扩展方式，可以灵活的扩展和修改全局配置文件和用户配置文件。ClickHouse 提供了 `config.d` 和 `users.d` 目录，你可以通过添加额外的 `.xml` 文件来引入新的配置设置或修改现有设置，使得配置管理更加模块化和容易维护。这种方式尤其适用于在 Docker 容器中部署，因为你可以通过 Docker 数据卷挂载机制轻松地将自定义的配置文件添加到 `config.d` 和 `users.d` 目录而无需修改容器镜像。当你以这种方式配置时，ClickHouse 会加载目录中的所有 `.xml` 文件并将这些文件中的配置合并到主配置中，这样可以实现添加新的配置项或覆盖现有配置。

在这里，我们在工作目录 `/opt/workspace/docker` 下创建一个名为 `conf` 目录，并分别创建 `config.d` 和 `users.d` 目录来放置自定义配置文件。假设我们想要扩展 `config.xml` 来覆盖已有的配置项，可以在 `config.d` 目录下创建一个名为 `base_config.xml` 的文件：
```xml

```


### 3.3 构建 Compose 文件

Docker Compose 简化了对整个应用程序堆栈的控制，使得在一个易于理解的 YAML 配置文件中轻松管理服务、网络和数据卷。要使用 Docker Compose 部署，首先需创建一个 docker-compose.yml 文件，如下所示：
```yml
version: '3.8'
services:
  neo4j:
    image: neo4j:latest
    container_name: docker_neo4j
    environment:
      NEO4J_AUTH: admin/admin
    ports:
      - "7474:7474"    # HTTP
      - "7687:7687"    # Bolt
    volumes:
      - $PWD/data:/data
      - $PWD/logs:/logs
      - $PWD/import:/var/lib/neo4j/import
      - $PWD/plugins:/plugins
    healthcheck:
      test: ["CMD", "neo4j", "status"]
      interval: 30s
      timeout: 10s
      retries: 10
    networks:
      - pub-network

networks:  # 网络
  pub-network:
      external: true
```
这个文件定义了一个 neo4j，其中包含两个服务：`ck1` 和 `ck2`。每个服务都使用 ClickHouse 的官方 Docker 镜像，同时映射了容器的 8123 端口（HTTP接口）和 9000 端口（原生客户端接口）到宿主机相同的端口上，这样我们就可以从宿主机访问 ClickHouse 服务了。下面详细介绍具体配置。

#### 3.3.1 顶级配置

`services` 配置用于定义不同的应用服务。上边的例子只定义了一个服务：`neo4j`。Docker Compose 会将服务部署在容器中。在这里我们使用自定义容器名称 `docker_neo4j`。

`networks` 配置用于声明服务要连接的网络 `pub-network`。`external: true` 表示网络是在 Docker Compose 配置文件之外定义的，即它已经存在了，Docker Compose 不需要尝试创建它。只要加入这个网络的服务就能够实现项目容器间以及跨项目通信。具体可以查阅 [Docker 实战：使用 Docker Compose 部署实现跨项目网络访问](https://smartsi.blog.csdn.net/article/details/138734487)。

`volumes` 配置用于将宿主机上的文件夹映射到容器内部，用于数据持久化。

#### 3.3.2 service元素配置

`services` 配置只定义一个服务，详细介绍服务的配置。
- `image` 配置指定了要使用的 Docker 镜像及其版本。两个服务均使用 `clickhouse/clickhouse-server:23.3.13.6` 镜像确保所有节点运行同一版本的 ClickHouse。当然你也可以选择 `clickhouse/clickhouse-server:latest` 镜像，这会确保每次拉取都是最新的稳定版，但在生产环境中可能带来不确定性，因为“最新版”会随新版本发布而变化。选择特定版本的标签可以提供更多的控制和预测性，减少意外的更新可能造成的问题。

`volumes` 配置对于生产环境中 ClickHouse 集群的数据持久化是至关重要的。这意味着你需要将容器内的数据绑定到宿主机上的数据卷来存储数据，这样即使容器重启，数据也不会丢失。为每个 ClickHouse 节点提供了独立的数据卷 `xxx_data` 和 `xxx_log`，分别用于存储 ClickHouse 的数据(`/var/lib/clickhouse`)和日志(`/var/log/clickhouse-server/`)。此外还分别映射了本地文件 `./conf/config.d` 和 `./conf/users.d` 到容器内的 `/etc/clickhouse-server/config.d` 和 `/etc/clickhouse-server/users.d` 目录。这意味着本地的配置文件将被用来作为容器内的配置。

`networks` 配置将服务连接到 `pub-network` 网络上。这个网络在 `networks` 一级key中声明已经创建，Docker Compose 不需要尝试创建它。加入这个网络之后，不同服务就可以通过服务名（`ck1`、`ck2`）找到并实现容器间以及跨项目的网络访问。

`ports` 配置用来将容器的端口映射到宿主机的端口，使得宿主机能够与集群进行通信。通常，只有服务需要直接从宿主机的网络访问时，我们才会映射端口。对于 ClickHouse 的分布式集群来说，节点之间的通信是在内部 Docker 网络中进行的，无需额外的端口映射。只有外部客户端需要访问集群时，才需要一个入口点，所以不需要为集群中的每个节点都映射端口到宿主机。我们只需要为集群中的一个节点映射端口即可。这个例子中，我们映射了容器的 `8123` 和 `9000` 端口到宿主机相同的端口上，这样我们就可以从宿主机访问 ClickHouse 服务了。`8123` 是默认的 HTTP 接口，用于接收 HTTP 请求，如 SQL 查询等。`9000` 是 ClickHouse 的本地 TCP 客户端通信端口，主要用于内部节点通信和 clickhouse-client 与服务端的通信。

```
      - $PWD/neo4j/conf:/var/lib/neo4j/conf
```

```
env_file:
  - ./neo4j.env
```

### 3.4 创建公共网络

上述配置文件中我们声明加入一个 `pub-network` 的网络：
```shell
networks:  # 加入公共网络
  pub-network:
      external: true
```

`external: true` 表示网络是在 Docker Compose 配置文件之外定义的，即它已经存在了，Docker Compose 不需要尝试创建它。首先要确保你已经创建了该网络，如果没有创建可以使用如下命令来创建：
```shell
docker network create pub-network
```
### 3.5 部署

在有了 docker-compose.yml 文件后，你需要在包含此文件的目录中运行 `docker compose up -d` 命令启动服务：
```shell
(base) localhost:clickhouse wy$ docker compose up -d
[+] Running 6/6
 ✔ Volume "clickhouse_ck2_data"  Created                                        0.0s
 ✔ Volume "clickhouse_ck2_log"   Created                                        0.0s
 ✔ Volume "clickhouse_ck1_data"  Created                                        0.0s
 ✔ Volume "clickhouse_ck1_log"   Created                                        0.0s
 ✔ Container docker_ck2          Started                                        0.2s
 ✔ Container docker_ck1          Started                                        0.2s
```
上述命令会在后台启动 ClickHouse 集群的三个服务。

### 3.6 验证部署

一旦服务启动，你就可以通过 ClickHouse 客户端或任何支持 HTTP 的客户端连接到 ClickHouse 服务器了。如果你已经安装了 ClickHouse 的客户端，可以使用以下命令连接：
```shell
clickhouse-client --host <hostname> --port <port> --user <username> --password <password>
```
其中，`<hostname>`、`<port>`、`<username>` 和 `<password>` 分别代表 ClickHouse 服务器的地址、端口、用户名和密码。如果没有提供用户名和密码，clickhouse-client 默认尝试以 default 用户进行连接，而且默认的端口是 9000。如下所示通过我们创建的 `test` 用户登录：
```shell
root@473f6e967d7a:/# clickhouse-client --host ck1 --port 9000 --user test --password test
ClickHouse client version 23.3.13.6 (official build).
Connecting to ck1:9000 as user test.
Connected to ClickHouse server version 23.3.13 revision 54462.

473f6e967d7a :)
473f6e967d7a :) SELECT 1

SELECT 1

Query id: e27df6dc-c433-4c6a-97f2-416fd27364a9

┌─1─┐
│ 1 │
└───┘

1 row in set. Elapsed: 0.002 sec.
```
> 注意是否需要添加 `<listen_host>::</listen_host>` 配置，否则有可能抛出 `Code: 210. DB::NetException: Connection refused (ck1:9000). (NETWORK_ERROR)` 异常


此外，ClickHouse 提供了一个 HTTP 接口，用户可以通过任何支持 HTTP 的客户端来执行查询：
```
curl -u <username>:<password> 'http://<hostname>:<port>/' --data-binary '<query>'
```
如下所示通过 curl 用我们创建的 `test` 用户进行查询：
```shell
(base) localhost:clickhouse wy$ curl 'http://localhost:8123/' -d 'SELECT 1'
1
```
> 注意是否需要添加 `<listen_host>::</listen_host>` 配置
