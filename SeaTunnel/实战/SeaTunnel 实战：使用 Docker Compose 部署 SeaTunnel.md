在现代软件开发的众多环节中，容器化技术已经成为了加速开发、简化部署的关键工具。Docker 作为市场上最流行的容器平台之一，提供了一种高效的方式来打包、分发和管理应用。在这片博文中，我们将探索如何利用 Docker Compose 来部署一个 Apache SeaTunnel 集群。在开发环境中，使用 Docker Compose 部署 SeaTunnel 不仅能够保证环境的一致性，还允许开发者快速部署和撤销实例，极大地提高了开发效率。

## 1. SeaTunnel 简介

SeaTunnel（原名 Waterdrop）是一个开源的、分布式、高性能的数据集成工具，旨在简化大规模数据的抽取、转换和加载（ETL）过程。它支持多种数据源和数据目的地，能够处理批处理和流处理任务，适用于大数据环境。SeaTunnel 的设计目标是提供简单易用、灵活且高效的数据集成解决方案，帮助企业快速构建数据管道，满足复杂的数据处理需求。

## 2. Docker Compose 简介

Docker Compose 是一个用于定义和运行多容器 Docker 应用程序的工具。通过 Compose，您可以通过一个 YAML 文件来配置您的应用的服务。然后，使用一个简单的命令，就可以创建并启动所有配置中的服务。这让组织和管理容器变成了一件轻而易举的事情。

在开始之前，首先需要确保已经安装了 Docker Compose，如果没有安装或者不熟悉 Compose 的具体查阅 [Docker 实战：使用 Docker Compose 实现高效的多容器部署](https://smartsi.blog.csdn.net/article/details/138414972)。

## 3. Docker Compose 部署 SeaTunnel

接下来，我们将一步步通过 Docker Compose 来部署一个包含三个节点的 SeaTunnel 集群。

### 3.1 创建项目目录

首先为项目创建一个目录。在这里，在我们的工作目录 `/opt/workspace/docker` 下创建一个名为 `seatunnel` 的项目：
```shell
smartsi@localhost docker % mkdir seatunnel
smartsi@localhost docker % cd seatunnel
```

> 该目录是应用程序镜像的上下文。该目录应该只包含用于构建该镜像的资源。

### 3.2 构建 Compose 文件

Docker Compose 简化了对整个应用程序堆栈的控制，使得在一个易于理解的 YAML 配置文件中轻松管理服务、网络和数据卷。要使用 Docker Compose 部署，首先需创建一个`docker-compose.yml`文件，如下所示：
```yaml
version: '3.8'

services:
  master:
    image: apache/seatunnel
    container_name: seatunnel_master
    environment:
      - ST_DOCKER_MEMBER_LIST=172.16.0.2,172.16.0.3,172.16.0.4
    entrypoint: >
      /bin/sh -c "
      /opt/seatunnel/bin/seatunnel-cluster.sh -r master
      "    
    ports:
      - "5801:5801"
    networks:
      seatunnel_network:
        ipv4_address: 172.16.0.2

  worker1:
    image: apache/seatunnel
    container_name: seatunnel_worker_1
    environment:
      - ST_DOCKER_MEMBER_LIST=172.16.0.2,172.16.0.3,172.16.0.4
    entrypoint: >
      /bin/sh -c "
      /opt/seatunnel/bin/seatunnel-cluster.sh -r worker
      "
    depends_on:
      - master
    networks:
      seatunnel_network:
        ipv4_address: 172.16.0.3

  worker2:
    image: apache/seatunnel
    container_name: seatunnel_worker_2
    environment:
      - ST_DOCKER_MEMBER_LIST=172.16.0.2,172.16.0.3,172.16.0.4
    entrypoint: >
      /bin/sh -c "
      /opt/seatunnel/bin/seatunnel-cluster.sh -r worker
      "
    depends_on:
      - master
    networks:
      seatunnel_network:
        ipv4_address: 172.16.0.4

networks:
  seatunnel_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.16.0.0/24
```



```yaml
services:
  zk1:
    image: zookeeper:3.6.3
    container_name: docker_zk1
    environment:
      ZOO_MY_ID: 1
      ZOO_SERVERS: server.1=zk1:2888:3888;2181 server.2=zk2:2888:3888;2181 server.3=zk3:2888:3888;2181
    ports:
      - "2181:2181"
    volumes:
      - zk1_data:/data
      - zk1_datalog:/datalog
    networks:
      - pub-network

  zk2:
    image: zookeeper:3.6.3
    container_name: docker_zk2
    environment:
      ZOO_MY_ID: 2
      ZOO_SERVERS: server.1=zk1:2888:3888;2181 server.2=zk2:2888:3888;2181 server.3=zk3:2888:3888;2181
    volumes:
      - zk2_data:/data
      - zk2_datalog:/datalog
    networks:
      - pub-network

  zk3:
    image: zookeeper:3.6.3
    container_name: docker_zk3
    environment:
      ZOO_MY_ID: 3
      ZOO_SERVERS: server.1=zk1:2888:3888;2181 server.2=zk2:2888:3888;2181 server.3=zk3:2888:3888;2181
    volumes:
      - zk3_data:/data
      - zk3_datalog:/datalog
    networks:
      - pub-network

volumes:
  zk1_data:
  zk1_datalog:
  zk2_data:
  zk2_datalog:
  zk3_data:
  zk3_datalog:

networks:  # 网络
  pub-network:
      external: true
```

> 可以为使用 `.yml` 或 `.yaml` 扩展名

第一行 `version: '3.8'` 定义了 Docker Compose 文件格式版本。3.x 版本可以支持更多新特性（如资源限制、网络配置等）。

`services` 用于定义不同的应用服务。上边的例子定义了三个服务(`master`、`worker1`、`worker2`)，分别对应 SeaTunnel 集群的三个节点（一个 master 节点，2个 worker 节点）。Docker Compose 会将每个服务部署在各自的容器中，在这里我们自定义了容器名称，因此 Docker Compose 会部署三个名为 `seatunnel_master`、`seatunnel_worker_1` 和 `seatunnel_worker_2` 的容器。

`networks` 配置用于声明服务要连接的网络 `seatunnel_network`：
```yaml
networks:
  seatunnel_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.16.0.0/24
```

`external: true` 表示网络是在 Docker Compose 配置文件之外定义的，即它已经存在了，Docker Compose 不需要尝试创建它。只要加入这个网络的服务就能够实现项目容器间以及跨项目通信。具体可以查阅 [Docker 实战：使用 Docker Compose 部署实现跨项目网络访问](https://smartsi.blog.csdn.net/article/details/138734487)。

`volumes` 用于声明 Docker Compose 创建新的数据卷 `zk1_data`、`zk1_datalog` 等。我们只负责声明，不需要手动创建，Docker Compose 会自动管理。默认情况下，在容器删除之后容器中的数据将丢失。为了解决这个问题，我们需要三个服务分别使用声明中的数据卷来将数据保存在宿主机上。

> Docker Compose 默认使用 {项目名}_{数据卷名} 的格式来命名数据卷，以此避免不同项目间的数据卷名冲突。在用 `docker volume ls` 命令查看数据卷时数据卷名为 zookeeper_zk1_data 和 zookeeper_zk1_datalog 等。

`services` 定义的服务中包含如下指令：
- `image`：指定了要使用的 Docker 镜像及其版本。三个服务均使用 `apache/seatunnel` 镜像确保所有节点运行同一版本的 Seatunnel，保持集群的一致性。这里的版本 3.6.3 可以根据需求替换为最新或特定版本。
- `container_name`：自定义的容器名称 `seatunnel_master`、`seatunnel_worker_1` 和 `seatunnel_worker_2`，避免自动生成随机名称便于识别。
- `environment`：
  - `ST_DOCKER_MEMBER_LIST`：这个环境变量指定了每个 SeaTunnel 实例节点的 IP。
- `entrypoint`：覆盖默认启动命令
  - `-r master`：指定节点角色为 Master
  - `-r worker`：指定节点角色为 Worker
- `ports`：配置用来将容器的端口映射到宿主机的端口，使得宿主机能够与集群进行通信。通常，只有服务需要直接从宿主机的网络访问时，我们才会映射端口。对于 SeaTunnel 分布式集群来说，节点之间的通信是在内部 Docker 网络中进行的，无需额外的端口映射。只有外部客户端需要访问集群时，才需要一个入口点，所以不需要为集群中的每个节点都映射端口到宿主机。我们只需要为集群中的一个节点映射端口即可。这个例子中，我们只将 `5801` 端口映射到了 `Master` 节点，这足以让外部客户端通过宿主机的 `5801` 端口来访问到 SeaTunnel 集群。
- `networks`: 将服务连接到 `seatunnel_network` 网络上。这个网络在 `networks` 一级key中声明已经创建，Docker Compose 不需要尝试创建它。加入这个网络之后，不同服务就可以通过服务名（`master`、`worker1`、`worker2`）找到并实现容器间以及跨项目的网络访问。在每个服务中都会指定 `ipv4_address`，目的是使用静态 IP 分配保障节点间稳定通信。


### 3.3 创建公共网络

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

### 3.4 部署

在有了`docker-compose.yml`文件后，您需要在包含此文件的目录中运行 `docker compose up -d` 命令启动服务：
```shell
(base) localhost:zookeeper wy$ docker compose up -d
[+] Running 9/9
 ✔ Volume "zookeeper_zk2_data"     Created                                      0.0s
 ✔ Volume "zookeeper_zk2_datalog"  Created                                      0.0s
 ✔ Volume "zookeeper_zk3_data"     Created                                      0.0s
 ✔ Volume "zookeeper_zk3_datalog"  Created                                      0.0s
 ✔ Volume "zookeeper_zk1_data"     Created                                      0.0s
 ✔ Volume "zookeeper_zk1_datalog"  Created                                      0.0s
 ✔ Container docker_zk1            Started                                      0.1s
 ✔ Container docker_zk2            Started                                      0.1s
 ✔ Container docker_zk3            Started                                      0.1s
```

上述命令会在后台启动 ZooKeeper 集群的三个服务。

### 3.5 验证

部署后，使用以下命令检查服务状态：
```shell
(base) localhost:zookeeper wy$ docker compose ps
NAME         IMAGE             COMMAND                  SERVICE   CREATED              STATUS              PORTS
docker_zk1   zookeeper:3.6.3   "/docker-entrypoint.…"   zk1       About a minute ago   Up About a minute   2888/tcp, 3888/tcp, 0.0.0.0:2181->2181/tcp, 8080/tcp
docker_zk2   zookeeper:3.6.3   "/docker-entrypoint.…"   zk2       About a minute ago   Up About a minute   2181/tcp, 2888/tcp, 3888/tcp, 8080/tcp
docker_zk3   zookeeper:3.6.3   "/docker-entrypoint.…"   zk3       About a minute ago   Up About a minute   2181/tcp, 2888/tcp, 3888/tcp, 8080/tcp
```
可以看到有三个服务已经启动成功，然后我们就可以用 `zkServer.sh status` 命令来查看每个 ZooKeeper 实例的状态：
```shell
(base) localhost:zookeeper wy$ docker exec -it docker_zk1 zkServer.sh status
ZooKeeper JMX enabled by default
Using config: /conf/zoo.cfg
Client port found: 2181. Client address: localhost. Client SSL: false.
Mode: follower

(base) localhost:zookeeper wy$ docker exec -it docker_zk2 zkServer.sh status
ZooKeeper JMX enabled by default
Using config: /conf/zoo.cfg
Client port found: 2181. Client address: localhost. Client SSL: false.
Mode: follower

(base) localhost:zookeeper wy$ docker exec -it docker_zk3 zkServer.sh status
ZooKeeper JMX enabled by default
Using config: /conf/zoo.cfg
Client port found: 2181. Client address: localhost. Client SSL: false.
Mode: leader
```



https://seatunnel.apache.org/zh-CN/docs/2.3.9/start-v2/docker/#%E4%BD%BF%E7%94%A8docker-compose
