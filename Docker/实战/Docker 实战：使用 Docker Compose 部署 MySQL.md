在现代软件开发的众多环节中，容器化技术已经成为了加速开发、简化部署的关键工具。Docker 作为市场上最流行的容器平台之一，提供了一种高效的方式来打包、分发和管理应用。在这片博文中，我们将探索如何利用 Docker Compose 来部署一个 MySQL 数据库。MySQL 是广泛使用的开源关系数据库之一，它可以为各种应用程序提供数据库服务。在开发环境中，使用 Docker Compose 部署 MySQL 不仅能够保证环境的一致性，还允许开发者快速部署和撤销实例，极大地提高了开发效率。

## 1. Docker Compose 简介

Docker Compose 是一个用于定义和运行多容器 Docker 应用程序的工具。通过 Compose，您可以通过一个 YAML 文件来配置您的应用的服务。然后，使用一个简单的命令，就可以创建并启动所有配置中的服务。这让组织和管理容器变成了一件轻而易举的事情。

在开始之前，首先需要确保已经安装了 Docker Compose，如果没有安装或者不熟悉 Compose 的具体查阅 [Docker 实战：使用 Docker Compose 实现高效的多容器部署](https://smartsi.blog.csdn.net/article/details/138414972)。

## 2. Docker Compose 部署 MySQL

接下来，我们将一步步通过 Docker Compose 来部署 MySQL 数据库。

### 2.1 创建项目目录

首先为项目创建一个目录。在这里，在我们的工作目录 `/opt/workspace/docker`下创建一个名为 `mysql` 的项目 ：

```shell
smartsi@localhost docker % mkdir mysql
smartsi@localhost docker % cd mysql
```

> 该目录是应用程序镜像的上下文。该目录应该只包含用于构建该镜像的资源。

### 2.2 构建Compose 文件

Docker Compose 简化了对整个应用程序堆栈的控制，使得在一个易于理解的 YAML 配置文件中轻松管理服务、网络和数据卷。要使用 Docker Compose 部署 MySQL，首先需创建一个`docker-compose.yml`文件，如下所示：

```shell
services:  # 定义你需要运行的服务
  db:  # 服务名称
    image: mysql:8.4  # 指定镜像及其版本
    container_name: docker_mysql # 指定容器的名称
    environment:  # 定义环境变量
      MYSQL_ROOT_PASSWORD: root  # 设置 MySQL 的 root 用户密码
      MYSQL_DATABASE: test  # 创建一个初始数据库
      MYSQL_USER: admin  # 创建一个MySQL用户
      MYSQL_PASSWORD: admin  # 为新用户设置密码
    ports: # 端口映射
      - "3307:3306"
    volumes:  # 数据持久化的配置
      - mysql_data:/var/lib/mysql  # 将命名数据卷挂载到容器内的指定目录
      - mysql_logs:/var/log/mysql
    networks:  # 网络配置
      - backend-network  # 加入到 backend-network 网络

volumes:  # 定义数据卷 自动创建/管理
  mysql_data:  # 命名数据卷，Docker Compose将在宿主机上自动管理此卷
  mysql_logs:

networks:  # 定义网络 自动创建/管理
  backend-network:  # 自动创建一个名为 backend-network 的网络
```

下面详细介绍一下配置：

- `services`：定义需要运行的服务，我们只定义了一个叫做`db`的 MySQL 服务。

- `image`：指定了要使用的 Docker 镜像及其版本。在这里，我们使用了官方的 MySQL 8.4 版本镜像。

- `container_name`：自定义的容器名称，便于识别。

- `environment`：提供环境变量以配置 MySQL 实例。通过环境变量，我们能以无交互的方式初始化数据库配置。设置MySQL的环境变量，包括root密码、初始数据库及其用户和密码。

- `ports`：将容器的`3306`端口映射到宿主机的`3307`端口，使外部可访问 MySQL 服务。宿主机上 3306 已经被占用，所以使用 3307 端口。

- `volumes`：实现数据持久化的关键部分。在容器内部，MySQL 存储数据在`/var/lib/mysql`路径，日志在 `/var/log/mysql` 路径。将这两个路径映射到宿主机的数据卷（这里分别对应命名卷`mysql_data` 和 `mysql_logs`，不需要手动创建）上，意味着即使容器被删除，存储在这个数据卷上的数据也不会丢失，实现了数据的持久化。

- `networks`: 构建服务间通信的机制。通过定义一个网络（在这里命名为`backend-network`，不需要手动创建），将 MySQL 服务加入这个网络，它允许其他服务（假如它们也连接到了`backend-network`网络）通过服务名（`db`）找到并连接到 MySQL 服务，从而实现容器间的网络访问。这对于构建由多个服务组成的应用非常重要。

> 出于演示目的，我们直接在`docker-compose.yml`文件中硬编码了环境变量如密码等。在生产环境中，考虑使用更安全的方法来管理这些敏感数据，如 Docker 秘钥管理。

这个`docker-compose.yml`文件是 MySQL 部署的基础模板，它涵盖了启动、配置和持久化MySQL 实例的基本方面，同时还考虑了服务间网络连接的需求。根据具体需求，可能需要对配置进行调整（比如，环境变量的值或者镜像版本）。

### 2.3 部署

在有了`docker-compose.yml`文件后，您需要在包含此文件的目录中运行如下命令启动服务：

```shell
smartsi@localhost mysql % docker compose up -d
[+] Running 2/2
 ✔ Container mysql-db-1    Recreated                                                                                                                  1.4s
 ✔ Container docker_mysql  Started                                                                                                                    0.1s
```

这将以守护进程模式启动 MySQL 服务。你可以通过以下命令来停止服务：

```shell
smartsi@localhost mysql % docker compose down
[+] Running 2/2
 ✔ Container docker_mysql         Removed                                                                                                             1.4s
 ✔ Network mysql_backend-network  Removed                                                                                                             0.1s
```

### 2.4. 验证

部署后，使用以下命令检查容器状态：

```shell
smartsi@localhost mysql % docker compose ps
NAME           IMAGE       COMMAND                   SERVICE   CREATED              STATUS              PORTS
docker_mysql   mysql:8.4   "docker-entrypoint.s…"   db        About a minute ago   Up About a minute   33060/tcp, 0.0.0.0:3307->3306/tcp
```

从上面可以看到 MySQL 容器正在运行中。你可以先通过 `docker exec` 命令进入容器：
```shell
localhost:mysql wy$ docker exec -it docker_mysql bash
bash-4.4#
```
MySQL 连接信息如下：
- 主机：localhost
- 端口：3307
- 用户名：admin（在`docker-compose.yml`中设置）
- 密码：admin（在`docker-compose.yml`中设置）

现在您就可以使用任何 MySQL 客户端工具连接到数据库：
```shell
bash-4.4# mysql -h localhost -P 3307 -u admin -p
Enter password:
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 13
Server version: 8.4.0 MySQL Community Server - GPL

Copyright (c) 2000, 2024, Oracle and/or its affiliates.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql>
```
通过 MySQL 客户端登录之后创建一个 `user` 表并插入一条记录：

```sql
CREATE TABLE `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `age` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `user` (`name`, `age`) VALUES ('张三', 25);
```

先通过 `docker compose down` 删除服务之后再通过 `docker compose up -d` 启动服务，观察到 `user` 表中的记录还存在证明存储在这个数据卷上的数据也不会丢失，实现了数据的持久化。
