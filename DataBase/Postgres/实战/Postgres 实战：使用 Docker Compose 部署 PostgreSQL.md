在现代软件开发的众多环节中，容器化技术已经成为了加速开发、简化部署的关键工具。Docker 作为市场上最流行的容器平台之一，提供了一种高效的方式来打包、分发和管理应用。在这片博文中，我们将探索如何利用 Docker Compose 来部署一个 PostgreSQL 数据库。PostgreSQL 是广泛使用的开源关系数据库之一，它可以为各种应用程序提供数据库服务。在开发环境中，使用 Docker Compose 部署 PostgreSQL 不仅能够保证环境的一致性，还允许开发者快速部署和撤销实例，极大地提高了开发效率。

## 1. PostgreSQL 简介

在众多的数据库管理系统中，PostgreSQL（通常简称为Postgres）以其先进的特性、卓越的稳定性、丰富的数据类型及其开源性质而脱颖而出。作为一个对象关系数据库，Postgres不仅提供了传统的表格数据库所具备的功能，还在此基础上加入了对复杂数据结构的支持，比如JSON、地理空间数据等。

## 2. Docker Compose 简介

Docker Compose 是一个用于定义和运行多容器 Docker 应用程序的工具。通过 Compose，您可以通过一个 YAML 文件来配置您的应用的服务。然后，使用一个简单的命令，就可以创建并启动所有配置中的服务。这让组织和管理容器变成了一件轻而易举的事情。

在开始之前，首先需要确保已经安装了 Docker Compose，如果没有安装或者不熟悉 Compose 的具体查阅 [Docker 实战：使用 Docker Compose 实现高效的多容器部署](https://smartsi.blog.csdn.net/article/details/138414972)。

## 3. Docker Compose 部署 PostgreSQL

接下来，我们将一步步通过 Docker Compose 来部署 PostgreSQL 数据库。

### 3.1 创建项目目录

首先为项目创建一个目录。在这里，在我们的工作目录 `/opt/workspace/docker`下创建一个名为 `postgresql` 的项目 ：

```shell
smartsi@localhost docker % mkdir postgresql
smartsi@localhost docker % cd postgresql
```

> 该目录是应用程序镜像的上下文。该目录应该只包含用于构建该镜像的资源。

### 3.2 构建 Compose 文件

Docker Compose 简化了对整个应用程序堆栈的控制，使得在一个易于理解的 YAML 配置文件中轻松管理服务、网络和数据卷。要使用 Docker Compose 部署 MySQL，首先需创建一个`docker-compose.yml`文件，如下所示：

```yml
services:
  postgres_db: # 服务名称
    image: postgres:15.7 # 指定镜像及其版本
    container_name: docker_postgres # 指定容器的名称
    environment:
      POSTGRES_PASSWORD: root
      #POSTGRES_DB: default
    ports: # 端口映射
      - "5432:5432"
    volumes: # 数据持久化的配置
      - data:/var/lib/postgresql/data
      - log:/var/log/postgresql
    logging:
      options:
        max-size: "10m"
        max-file: "3"
    networks:  # 网络配置
      - pub-network  # 加入到 pub-network 网络

volumes: # 数据卷
  data:
  log:

networks:  # 网络
  pub-network:
      external: true
```
`services` 配置用于定义不同的应用服务。上边的例子只定义了一个服务：`postgres_db`。`networks` 配置用于声明服务要连接的网络 `pub-network`。`external: true` 表示网络是在 Docker Compose 配置文件之外定义的，即它已经存在了，Docker Compose 不需要尝试创建它。只要加入这个网络的服务就能够实现项目容器间以及跨项目通信。具体可以查阅 [Docker 实战：使用 Docker Compose 部署实现跨项目网络访问](https://smartsi.blog.csdn.net/article/details/138734487)。`volumes` 用于声明 Docker Compose 创建新的数据卷 `data`、`log`。我们只负责声明，不需要手动创建，Docker Compose 会自动管理。默认情况下，在容器删除之后容器中的数据也将会丢失。为了解决这个问题，我们需要 `postgres_db` 服务使用声明中的数据卷来将数据保存在宿主机上。

> Docker Compose 默认使用 `{项目名}_{数据卷名}` 的格式来命名数据卷，以此避免不同项目间的数据卷名冲突。在这创建的两个数据卷为 `postgressql_data` 和 `postgressql_log`。


配置日志数据卷是一个好的实践，它可以帮助你更好地管理和保存日志文件，以便于问题诊断和性能监控。为了实现这一点，我们可以在Docker Compose文件中为PostgreSQL服务添加专门的日志数据卷配置。

`postgres_db` 的服务定义中，包含如下指令：
- `image`：指定了要使用的 Docker 镜像及其版本。在这里，我们使用了官方的 PostgreSQL 15.7 版本镜像。为了确保系统的稳定性和兼容性，推荐使用 PostgreSQL 官方镜像的一个稳定版本而不是最新版（latest）。通常来说，生产环境中应该避免使用 latest 标签，因为它指向最新的版本，而最新版本可能包含未经充分测试的特性或变化，这可能会影响到生产环境的稳定性。
- `container_name`：自定义的容器名称 `docker_postgres`，便于识别。
- `environment`：设置环境变量。我们为 PostgreSQL 数据库设置了密码 root。请将其更改为更安全的密码。这是postgres默认管理员账户的密码。由于这个值是必需的，如果没有设置，容器将无法启动。
- `ports`：用来将容器的端口映射到宿主机的端口，使得宿主机能够与集群进行通信。通常，只有服务需要直接从宿主机的网络访问时，我们才会映射端口。将容器的 5432 端口映射到宿主机的 5432 端口，使外部可访问 PostgreSQL。
- `volumes`：实现数据持久化的关键部分。PostgreSQL 存储数据在 `/var/lib/postgresql/data` 路径，日志存储在 `/var/log/postgresql` 路径。`postgres_db` 服务将这两个路径映射到宿主机的数据卷的 `data` 和 `log` 的数据卷上。这意味着即使容器被删除，存储在这两个数据卷上的数据也不会丢失，实现了数据的持久化。配置日志数据卷是一个好的实践，它可以帮助你更好地管理和保存日志文件，以便于问题诊断和性能监控。
- `logging`：可以通过 logging 选项对容器日志做了简单的管理配置，例如限制日志文件的最大大小为 10MB，且最多保留3个日志文件。这有助于避免日志文件占用过多的磁盘空间。
- `networks`: 将服务连接到 `pub-network` 网络上。这个网络在 `networks` 一级 key 中声明已经创建，Docker Compose 不需要尝试创建它。加入这个网络之后，不同服务就可以通过服务名 `postgres_db` 找到并实现容器间以及跨项目的网络访问。

> 出于演示目的，我们直接在`docker-compose.yml`文件中硬编码了环境变量如密码等。在生产环境中，考虑使用更安全的方法来管理这些敏感数据，如 Docker 秘钥管理。

这个`docker-compose.yml`文件是 PostgreSQL 部署的基础模板，它涵盖了启动、配置和持久化 PostgreSQL 实例的基本方面，同时还考虑了服务间网络连接的需求。根据具体需求，可能需要对配置进行调整（比如，环境变量的值或者镜像版本）。

### 2.3 部署

在有了`docker-compose.yml`文件后，您需要在包含此文件的目录中运行如下命令启动服务：
```shell
(base) localhost:postgresql wy$ docker compose up -d
[+] Running 15/15
 ✔ postgres_db Pulled                                                           61.9s
   ✔ 09f376ebb190 Pull complete                                                 8.9s
   ✔ 119215dfb3e3 Pull complete                                                 2.0s
   ✔ 94fccb772ad3 Pull complete                                                 10.7s
   ✔ 0fc3acb16548 Pull complete                                                 8.6s
   ✔ d7dba7d03fe8 Pull complete                                                 13.1s
   ✔ 898ae395a1ca Pull complete                                                 12.6s
   ✔ 088e651df7e9 Pull complete                                                 12.4s
   ✔ ed155773e5e0 Pull complete                                                 14.2s
   ✔ 52df7d12fb73 Pull complete                                                 33.4s
   ✔ bab1ecc22dc9 Pull complete                                                 15.2s
   ✔ 1655a257a5b5 Pull complete                                                 16.0s
   ✔ 978f02dfc247 Pull complete                                                 18.0s
   ✔ d715d7d9aee0 Pull complete                                                 17.8s
   ✔ b2e9251b2f8d Pull complete                                                 19.8s
[+] Running 3/3
 ✔ Volume "postgresql_log"    Created                                           0.0s
 ✔ Volume "postgresql_data"   Created                                           0.0s
 ✔ Container docker_postgres  Started                                           0.9s
```
这将以守护进程模式启动 PostgreSQL 服务。

### 2.4. 验证

部署后，使用以下命令检查容器状态：
```shell
(base) localhost:postgresql wy$ docker compose ps
NAME              IMAGE           COMMAND                  SERVICE       CREATED         STATUS         PORTS
docker_postgres   postgres:15.7   "docker-entrypoint.s…"   postgres_db   3 minutes ago   Up 3 minutes   0.0.0.0:5432->5432/tcp
```
从上面可以看到 PostgreSQL 容器正在运行中。可以有两种方式来验证我们部署的 PostgreSQL 数据库是否有问题。

第一种方式你可以从宿主机上访问，即装有 Docker 的机器上访问 PostgreSQL，通常需要使用 localhost 作为主机名（host），并指定你在 docker-compose.yml 文件中映射给宿主机的端口号。上面例子中将容器的 5432 端口映射到了宿主机的 5432 端口，那么你可以使用 localhost:5432 来连接到 PostgreSQL。你可以使用 Navicat 来访问数据库，具体连接信息配置如下：
- 主机：localhost
- 端口：5432
- 用户名：postgres(PostgreSQL 的默认用户名)
- 密码：root（在`docker-compose.yml`中设置）

![](docker-compose-deployment-postgresql-1)

第二种方式从 Docker 容器中访问 PostgreSQL。在这种情况下，你可以使用服务名 `postgres_db` 作为主机名来连接到 PostgreSQL，而不需指定端口，因为网络是内部的，端口是开放的。

你可以先通过 `docker exec` 命令进入容器：
```shell
(base) localhost:postgresql wy$ docker exec -it docker_postgres psql -h postgres_db -p 5432 -U postgres
Password for user postgres:
psql (15.7 (Debian 15.7-1.pgdg120+1))
Type "help" for help.

postgres=# \list
                                                List of databases
   Name    |  Owner   | Encoding |  Collate   |   Ctype    | ICU Locale | Locale Provider |   Access privileges
-----------+----------+----------+------------+------------+------------+-----------------+-----------------------
 postgres  | postgres | UTF8     | en_US.utf8 | en_US.utf8 |            | libc            |
 template0 | postgres | UTF8     | en_US.utf8 | en_US.utf8 |            | libc            | =c/postgres          +
           |          |          |            |            |            |                 | postgres=CTc/postgres
 template1 | postgres | UTF8     | en_US.utf8 | en_US.utf8 |            | libc            | =c/postgres          +
           |          |          |            |            |            |                 | postgres=CTc/postgres
(3 rows)

postgres=#
```
