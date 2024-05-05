---
layout: post
author: sjf0115
title: 在Docker中使用Redis
date: 2020-08-12 15:36:43
tags:
  - Docker

categories: Docker
permalink: docker-open-source-redis
---

### 1. 简介

本文章将介绍如何使用 Docker 探索 Redis。我们可以在 Docker for Windows 、Docker for mac 或者 Linux 模式下运行 Docker 命令。

> 本文是基于Docker for mac。

### 2. 查看可用的 Redis 版本

可以在镜像仓库中查看 [Redis](https://hub.docker.com/_/redis?tab=tags) 镜像：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/docker/docker-open-source-redis-2.jpg?raw=true)

### 3. 获取镜像

使用如下命令拉取官方最新版本的镜像：
```
docker pull redis:latest
```

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/docker/docker-open-source-redis-3.jpg?raw=true)

### 4. 查看本地镜像

使用如下命令来查看是否已安装了Redis镜像：
```
docker images
```
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/docker/docker-open-source-redis-4.jpg?raw=true)

在图中我们可以看到我们已经安装了最新版本（latest）的 Redis 镜像。

### 5. 运行容器

我们给容器起一个名字 `docker-redis`，同时公开 6379 端口（Redis 默认值），使用如下命令运行容器:
```
docker run -d -p 6379:6379 --name docker-redis redis
```
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/docker/docker-open-source-redis-1.jpg?raw=true)

> -p 6379:6379：映射容器服务的 6379 端口到宿主机的 6379 端口。外部可以直接通过宿主机ip:6379 访问到 Redis 的服务。

可以通过如下命令查看容器的运行信息来判断容器是否运行成功：
```
docker ps
```
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/docker/docker-open-source-redis-5.jpg?raw=true)

还可以通过如下命令查看日志输出：
```
docker logs docker-redis
```
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/docker/docker-open-source-redis-6.jpg?raw=true)

### 6. 在容器中运行Redis CLI

接着我们通过在容器中运行 redis-cli 来连接 redis 服务。我们将在运行中的容器中用 `-it` 选项来启动一个新的交互式会话，并使用它来运行 `redis-cli`：
```
docker exec -it docker-redis /bin/bash
```

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/docker/docker-open-source-redis-7.jpg?raw=true)

我们已经连接到容器，现在让我们运行 `redis-cli`：
```
root@517350f4f2bb:/data# redis-cli
```
现在我们可以运行一些基本的 Redis 命令：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/docker/docker-open-source-redis-8.jpg?raw=true)

### 7. 清理容器

让我们停止 `docker-redis` 容器并删除：
```
docker stop docker-redis
docker rm docker-redis
```

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/%E5%85%AC%E4%BC%97%E5%8F%B7.jpg?raw=true)
