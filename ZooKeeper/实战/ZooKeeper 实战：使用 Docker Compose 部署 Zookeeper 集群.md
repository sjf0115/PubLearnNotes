在现代软件开发的众多环节中，容器化技术已经成为了加速开发、简化部署的关键工具。Docker 作为市场上最流行的容器平台之一，提供了一种高效的方式来打包、分发和管理应用。在这片博文中，我们将探索如何利用 Docker Compose 来部署一个 Zookeeper 集群。在开发环境中，使用 Docker Compose 部署 Zookeeper 不仅能够保证环境的一致性，还允许开发者快速部署和撤销实例，极大地提高了开发效率。

## 1. ZooKeeper 简介

ZooKeeper是一个开源的分布式协调服务，用于管理大型分布式系统中的数据。它由Apache软件基金会提供，最初是Hadoop的一个子项目，但后来发展成为一个独立的顶级项目。ZooKeeper提供的一致性协调服务对于构建分布式应用和服务非常重要，特别是在需要精确的领导选举、配置管理、命名服务、分布式同步和提供分布式锁等功能时。

## 2. Docker Compose 简介

Docker Compose 是一个用于定义和运行多容器 Docker 应用程序的工具。通过 Compose，您可以通过一个 YAML 文件来配置您的应用的服务。然后，使用一个简单的命令，就可以创建并启动所有配置中的服务。这让组织和管理容器变成了一件轻而易举的事情。

在开始之前，首先需要确保已经安装了 Docker Compose，如果没有安装或者不熟悉 Compose 的具体查阅 [Docker 实战：使用 Docker Compose 实现高效的多容器部署](https://smartsi.blog.csdn.net/article/details/138414972)。

## 3. Docker Compose 部署 ZooKeeper

接下来，我们将一步步通过 Docker Compose 来部署一个至少包含三个节点的 ZooKeeper 集群。

### 3.1 创建项目目录

首先为项目创建一个目录。在这里，在我们的工作目录 `/opt/workspace/zookeeper`下创建一个名为 `zookeeper` 的项目：
```shell
smartsi@localhost docker % mkdir zookeeper
smartsi@localhost docker % cd zookeeper
```

> 该目录是应用程序镜像的上下文。该目录应该只包含用于构建该镜像的资源。

### 3.2 构建 Compose 文件

Docker Compose 简化了对整个应用程序堆栈的控制，使得在一个易于理解的 YAML 配置文件中轻松管理服务、网络和数据卷。要使用 Docker Compose 部署，首先需创建一个`docker-compose.yml`文件，如下所示：

```shell
services:
  zk1:
    image: zookeeper:3.6.3
    container_name: zk1
    environment:
      ZOO_MY_ID: 1
      ZOO_SERVERS: server.1=zk1:2888:3888;2181 server.2=zk2:2888:3888;2181 server.3=zk3:2888:3888;2181
    ports:
      - "2181:2181"
    volumes:
      - zk1_data:/data
      - zk1_datalog:/datalog
    networks:
      - backend-network

  zk2:
    image: zookeeper:3.6.3
    container_name: zk2
    environment:
      ZOO_MY_ID: 2
      ZOO_SERVERS: server.1=zk1:2888:3888;2181 server.2=zk2:2888:3888;2181 server.3=zk3:2888:3888;2181
    ports:
      - "2182:2181"
    volumes:
      - zk2_data:/data
      - zk2_datalog:/datalog
    networks:
      - backend-network

  zk3:
    image: zookeeper:3.6.3
    container_name: zk3
    environment:
      ZOO_MY_ID: 3
      ZOO_SERVERS: server.1=zk1:2888:3888;2181 server.2=zk2:2888:3888;2181 server.3=zk3:2888:3888;2181
    ports:
      - "2183:2181"
    volumes:
      - zk3_data:/data
      - zk3_datalog:/datalog
    networks:
      - backend-network

volumes:
  zk1_data:
  zk1_datalog:
  zk2_data:
  zk2_datalog:
  zk3_data:
  zk3_datalog:

networks:
  backend-network:
```

> 可以为使用 `.yml` 或 `.yaml` 扩展名

services 用于定义不同的应用服务。上边的例子定义了三个服务(`zk1`、`zk2`、`zk3`)，分别对应 ZooKeeper 集群的三个节点。Docker Compose 会将每个服务部署在各自的容器中，在这里我们自定义了容器名称，因此 Docker Compose 会部署三个名为 `zk1`、`zk2` 和 `zk3` 的容器。

networks 用于声明 Docker Compose 创建新的网络 `wordpress_network`。我们只负责声明，不需要手动创建，Docker Compose 会自动管理。为了实现 `db`服务和 `wordpress` 服务之间的通信，需要这两个服务都加入到这两个网络。在使用 Docker Compose 部署应用时，定义`networks`并不是必须的，但却是一个好的习惯。如果不显式定义和指定网络，Docker Compose 默认会为你的应用创建一个单独的网络，并且所有在`docker-compose.yml`文件中定义的服务都将自动加入这个网络。这意味着，即使你没有明确定义网络，服务之间也能够相互通信。

volumes 用于声明 Docker Compose 创建新的数据卷 `mysql_data`、`mysql_logs`、以及 `wordpress_data`。我们只负责声明，不需要手动创建，Docker Compose 会自动管理。默认情况下，在容器删除之后，MySQL 容器和 WordPress 容器中的数据将丢失。为了解决这个问题，我们需要 `db` 服务 和 `wordpress` 服务分别使用声明中的数据卷来将数据保存在宿主机上。

### 3.2.1 db 服务

db 的服务定义中，包含如下指令：

- `image`：指定了要使用的 Docker 镜像及其版本。在这里，我们使用了官方的 MySQL 8.4 版本镜像。

- `container_name`：自定义的容器名称 `docker_wordpress_mysql`，便于识别。

- `environment`：提供环境变量以配置 MySQL 实例。通过环境变量，我们能以无交互的方式初始化数据库配置。设置MySQL的环境变量，包括root密码、初始数据库及其用户和密码。

- `ports`：将容器的`3306`端口映射到宿主机的`3308`端口，使外部可访问 MySQL 服务。宿主机上 3306 已经被占用，所以使用 3308 端口。

- `volumes`：实现数据持久化的关键部分。MySQL 存储数据在`/var/lib/mysql`路径，日志在 `/var/log/mysql` 路径。`db` 服务将这两个路径映射到宿主机的数据卷的 `mysql_data` 和 `mysql_logs` 的数据卷上。这意味着即使容器被删除，存储在这两个数据卷上的数据也不会丢失，实现了数据的持久化。

- `networks`: 将 db 服务连接到 `wordpress_network`网络上。这个网络在 `networks` 一级key中声明。将 db 服务加入这个网络，允许 `wordpress` 服务（也会连接到`wordpress_network`网络）可以通过服务名（`db`）找到并连接到 MySQL 服务，从而实现容器间的网络访问。

### 3.2.2 wordpress 服务

wordpress 的服务定义中，包含如下指令：

- `depends_on`：表示 WordPress 服务依赖于 MySQL 服务（`db`），确保 MySQL 先启动。    

- `image`：指定了要使用的 Docker 镜像及其版本。在这里，我们使用了官方的 latest 版本镜像。

- `container_name`：自定义的容器名称 `docker_wordpress`，便于识别。

- `environment`：配置 WordPress 连接数据库的环境变量，包括数据库主机（对应服务名`db`），数据库用户名、密码和数据库名。

- `ports`：将宿主机的`8000`端口映射到容器的`80`端口，可以通过`http://localhost:8000`访问 WordPress。

- `volumes`：将 `/var/www/html`（WordPress安装目录）映射到名为`wordpress_data`的数据卷，实现数据持久化。

- `networks`: 将 `wordpress` 服务也连接到 `wordpress_network`网络。这样 `wordpress` 服务可以通过服务名（`db`）找到并连接到 MySQL 服务，从而实现容器间的网络访问。

> 出于演示目的，我们直接在`docker-compose.yml`文件中硬编码了环境变量如密码等。在生产环境中，考虑使用更安全的方法来管理这些敏感数据，如 Docker 秘钥管理。

这个`docker-compose.yml`文件是 WordPress 部署的基础模板，它涵盖了启动、配置和持久化的基本方面，同时还考虑了服务间网络连接的需求。根据具体需求，可能需要对配置进行调整（比如，环境变量的值或者镜像版本）。

### 3.3 部署

在有了`docker-compose.yml`文件后，您需要在包含此文件的目录中运行如下命令启动服务：

```shell
smartsi@localhost wordpress % docker compose up -d
[+] Running 3/3
 ✔ Network wordpress_wordpress_network  Created                                                                                                       0.0s
 ✔ Container docker_wordpress_mysql     Started                                                                                                       0.0s
 ✔ Container docker_wordpress           Started                                                                                                       0.0s
```

上述命令会在后台启动 WordPress 和 MySQL 服务。

### 3.4. 验证

部署后，使用以下命令检查服务状态：

```shell
smartsi@localhost wordpress % docker compose ps
NAME                     IMAGE              COMMAND                   SERVICE     CREATED          STATUS          PORTS
docker_wordpress         wordpress:latest   "docker-entrypoint.s…"   wordpress   11 minutes ago   Up 11 minutes   0.0.0.0:8000->80/tcp
docker_wordpress_mysql   mysql:8.4          "docker-entrypoint.s…"   db          11 minutes ago   Up 11 minutes   33060/tcp, 0.0.0.0:3308->3306/tcp
```

可以看到有两个 `docker_wordpress` 和 `docker_wordpress_mysql` 服务容器已经启动成功。

### 3.5 访问WordPress

服务成功启动后，您可以通过浏览器访问您的 WordPress 站点。因为我们将 WordPress 的 80 端口映射到了宿主机的 8000 端口，您可以打开浏览器并访问`http://localhost:8000`来配置 WordPress。按照页面提示完成安装即可。

![](docker-compose-deployment-wordpress-1.jpeg)

完成安装之后即可登录了：
![](docker-compose-deployment-wordpress-2.jpeg)
