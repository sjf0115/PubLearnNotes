
## 1. MinIO 简介

MinIO 是一个高性能、兼容 AWS S3 的开源对象存储解决方案。它适用于存储大量非结构化数据，比如照片、视频、日志文件等。MinIO 可以在单机模式下运行，也可以配置为高可用的分布式模式。在本教程中，我们将使用 Docker Compose 在本地环境中部署一个四节点的 MinIO 集群。

## 2. Docker Compose 简介

Docker Compose 是一个用于定义和运行多容器 Docker 应用程序的工具。通过 Compose，您可以通过一个 YAML 文件来配置您的应用的服务。然后，使用一个简单的命令，就可以创建并启动所有配置中的服务。这让组织和管理容器变成了一件轻而易举的事情。

在开始之前，首先需要确保已经安装了 Docker Compose，如果没有安装或者不熟悉 Compose 的具体查阅 Docker 实战：使用 Docker Compose 实现高效的多容器部署。

## 3. Docker Compose 部署 MinIO

接下来，我们将一步步通过 Docker Compose 来部署 WordPress 博客站点 以及依赖的 MySQL 数据库。

### 3.1 创建项目目录

首先为项目创建一个目录。在这里，在我们的工作目录 /opt/workspace/docker 下创建一个名为 minio 的项目 ：
```shell
smartsi@localhost docker % mkdir minio
smartsi@localhost docker % cd minio
```
> 该目录是应用程序镜像的上下文。该目录应该只包含用于构建该镜像的资源。

### 3.2 构建 Compose 文件

Docker Compose 简化了对整个应用程序堆栈的控制，使得在一个易于理解的 YAML 配置文件中轻松管理服务、网络和数据卷。要使用 Docker Compose 部署，首先需创建一个 docker-compose.yml 文件，如下所示：
```yml
services:
  minio1:
    image: minio/minio:RELEASE.2024-05-10T01-41-38Z
    volumes:
      - m1_data:/data
    networks:
      - pub-network
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=admin
      - MINIO_ROOT_PASSWORD=12345678
    command: server http://minio{1...3}/data --console-address ":9001"

  minio2:
    image: minio/minio:RELEASE.2024-05-10T01-41-38Z
    volumes:
      - m2_data:/data
    networks:
      - pub-network
    environment:
      - MINIO_ROOT_USER=admin
      - MINIO_ROOT_PASSWORD=12345678
    command: server http://minio{1...3}/data --console-address ":9001"

  minio3:
    image: minio/minio:RELEASE.2024-05-10T01-41-38Z
    volumes:
      - m3_data:/data
    networks:
      - pub-network
    environment:
      - MINIO_ROOT_USER=admin
      - MINIO_ROOT_PASSWORD=12345678
    command: server http://minio{1...3}/data --console-address ":9001"

volumes:
  m1_data:
  m2_data:
  m3_data:

networks:  # 加入公共网络
  pub-network:
      external: true
```

> 可以为使用 .yml 或 .yaml 扩展名

这个文件定义了一个 MinIO 集群，其中包含三个节点：minio1、minio2 和 minio3。每个节点都使用 MinIO 的官方 Docker 镜像，并将 MinIO 服务暴露在 9000、9001 端口上。此外，每个节点都设置了管理员用户名和密码。下面详细介绍具体配置。

services 用于定义不同的应用服务。上边的例子定义了三个服务：`minio1`、`minio2` 以及 `minio3`，分别作为集群的三个节点。Docker Compose 会将每个服务部署在各自的容器中。在这里我们没有自定义了容器名称，因此 Docker Compose 会部署默认名称的容器，在这分别为 `minio1-1`、`minio2-1` 以及 `minio3-1`。

networks 用于声明服务要连接的网络 `pub-network`。`external: true` 表示网络是在 Docker Compose 配置文件之外定义的，即它已经存在了，Docker Compose 不需要尝试创建它。只要加入这个网络的服务就能够实现彼此通信。具体可以查阅 [Docker 实战：使用 Docker Compose 部署实现跨项目网络访问](https://smartsi.blog.csdn.net/article/details/138734487)。

volumes 用于声明 Docker Compose 创建新的数据卷 `m1_data`、`m2_data` 以及 `m3_data`。我们只负责声明，不需要手动创建，Docker Compose 会自动管理。默认情况下，在容器删除之后数据会丢失。为了解决这个问题，我们需要三个服务分别使用声明中的数据卷来将数据保存在宿主机上。




minio/minio:latest: 表示最新稳定版镜像。使用这个标签会确保每次拉取都是最新的稳定版，但在生产环境中可能带来不确定性，因为“最新版”会随新版本发布而变化。选择特定版本的标签可以提供更多的控制和预测性，减少意外的更新可能造成的问题。minio/minio:RELEASE.2024-05-10T01-41-38Z 指定一个特定的发布版本，这里的日期时间戳代表了该版本的构建时间。这种命名方式适用于需要固定版本以保证环境稳定性的场景。

services: 定义要运行的服务。在我们的案例中，我们创建了3个 MinIO 服务（minio1 到 minio3）。
environment: 设置环境变量。这里，我们设置了访问 MinIO 实例所需的根用户和密码 (MINIO_ROOT_USER 和 MINIO_ROOT_PASSWORD)。
command: 指定容器启动时运行的命令。在这个案例中，它告诉 MinIO 以分布式模式启动，并且包括所有四个定义的节点。--console-address ":9001" 指定了 MinIO 管理控制台的地址。



从 MinIO RELEASE.2020-06-18T02-23-35Z 版本开始，MinIO 引入了一个全新的管理控制台（即 MinIO Console），这需要额外的端口。这就是为什么你会在其他方案中看到映射 9001 端口。9001 端口用于访问 MinIO Console，提供了一个用户友好的图形界面用于管理 MinIO 集群。

因此，如果你想利用 MinIO Console，确实需要映射 9001 端口。再次强调，如果你正在使用的 MinIO 版本支持 MinIO Console 功能，那么如下配置是推荐的：
```
ports:
  - "9000:9000" # MinIO API 和客户端SDK交互端口
  - "9001:9001" # MinIO Console 管理界面端口
```


### 3.3 创建公共网络

上述配置文件中我们申明加入一个 `pub-network` 的网络：
```shell
networks:  # 加入公共网络
  pub-network:
      external: true
```
首先确保你已经创建了该网络，如果没有创建可以使用如下命令来创建：
```shell

```

### 3.4 部署

确保你在 docker-compose.yml 文件所在的目录内。然后在终端中运行以下命令来启动你的 MinIO 分布式集群：
```shell
docker-compose up -d
```


### 3.5 验证部署

一旦部署完成，你可以通过访问任一个 MinIO 节点的管理控制台来验证你的集群。默认情况下，管理控制台通过端口 9001 访问。假设你希望访问 minio1 的管理界面，可以在浏览器中输入：
```shell
http://localhost:9001
```
使用环境变量中设置的 MINIO_ROOT_USER 和 MINIO_ROOT_PASSWORD 登录。






...
