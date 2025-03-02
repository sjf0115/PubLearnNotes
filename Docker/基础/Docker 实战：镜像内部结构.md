为什么我们要讨论镜像的内部结构？如果只是使用镜像，当然不需要了解，直接通过 docker 命令下载和运行就可以了。但如果我们想要创建自己的镜像，或者想理解 Docker 为什么是轻量级的，就非常有必要学习这部分知识了。我们以两个镜像为例来讲解一个镜像的内部构成。

## 1. hello-world 镜像

首先我们以最小的 hello-world 镜像为例讲解一下其内部结构。hello-world 镜像是 Docker 官方提供的一个镜像，通常用来验证 Docker 是否安装成功。我们在[Docker 实战：使用 Docker Desktop 在 MacOS 上安装 Docker](https://smartsi.blog.csdn.net/article/details/138279554) 一文中讲解如何安装 Docker 时，就是使用这个镜像来验证 Docker 是否成功。

我们先通过 docker pull 从 Docker Hub 下载这个镜像，如下所示：
```
docker pull hello-world
```
输出信息如下所示：
```
smartsi@localhost ~ % docker pull hello-world
Using default tag: latest
latest: Pulling from library/hello-world
93288797bd35: Pull complete
Digest: sha256:2498fce14358aa50ead0cc6c19990fc6ff866ce72aeb5546e1d59caac3d0d60f
Status: Downloaded newer image for hello-world:latest
docker.io/library/hello-world:latest
```
用 `docker images` 命令查看镜像信息，如下所示：
```
smartsi@localhost ~ % docker images hello-world
REPOSITORY    TAG       IMAGE ID       CREATED       SIZE
hello-world   latest    18e5af790473   2 years ago   9.14kB
```
可以看到 hello-world 镜像大小不足 10 KB。通过 `docker run` 命令运行，如下所示：
```
smartsi@localhost ~ % docker run hello-world

Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
    (arm64v8)
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.

To try something more ambitious, you can run an Ubuntu container with:
 $ docker run -it ubuntu bash

Share images, automate workflows, and more with a free Docker ID:
 https://hub.docker.com/

For more examples and ideas, visit:
 https://docs.docker.com/get-started/
```
通过上面几个命令我们下载并运行了 hello-world 镜像，其实我们更关心的是 hello-world 镜像都包含了哪些内容，都不足 10KB。

Dockerfile 是镜像的描述文件，定义了如何构建 Docker 镜像。hello-world 镜像的 dockerfile 内容如下所示：
```
FROM scrath
COPY hello /
CMD ["/hello"]
```
可以看到只有短短的三条指令：
- 第一行指令表示镜像是从 0 开始构建
- 第二行指令表示将文件 `hello` 复制到镜像的根目录下
- 第三行指令表示容器启动时执行 `/hello` 脚本

可以看出 hello-world 镜像只有一个可执行文件 `hello`，这个脚本的主要目的就是打印出 `Hello from Docker ...` 等信息。这个文件是文件系统的全部内容，甚至连最基本的 `/bin`，`/usr`，`/lib` 等都没有。

## 2. Base 镜像

hello-world 镜像虽然是一个完整的镜像，但它并没有实际用途。通常来说，我们希望镜像能提供一个基本的操作系统环境，用户根据需要来安装和配置软件。提供最基础的操作系统环境的镜像我们一般称之为 Base 镜像。

Base 镜像有两层含义：不依赖其他镜像，从 scratch 构建；其他镜像依赖进行构建；所以能称作 Base 镜像的通常都是各种 Linux 发行版的 Docker 镜像，比如 CentOS 等。我们以 CentOS 为例具体看一下基础镜像包含哪些内容。

我们先通过 docker pull 从 Docker Hub 下载这个镜像，如下所示：
```
docker pull centos
```
输出信息如下所示：
```
smartsi@localhost ~ % docker pull centos
Using default tag: latest
latest: Pulling from library/centos
52f9ef134af7: Pull complete
Digest: sha256:a27fd8080b517143cbbbab9dfb7c8571c40d67d534bbdee55bd6c473f432b177
Status: Downloaded newer image for centos:latest
docker.io/library/centos:latest
```
用 `docker images` 命令查看镜像信息，如下所示：
```
smartsi@localhost ~ % docker images centos
REPOSITORY   TAG       IMAGE ID       CREATED       SIZE
centos       latest    e6a0117ec169   2 years ago   272MB
```
可以看到 centos 镜像大小不足 300 MB。是不是感觉太不可思议了，一个 CentOS 竟然不到 300MB，遥想我们用虚拟机安装 CentOS 时至少有几个 GB 吧。

首先我们先来了解一下基础知识。Linux 操作系统是由内核空间和用户空间组成。内核空间是 kernel，在 Linux 刚启动时会加载 bootfs 文件系统，之后就会卸载 bootfs。用户空间的文件系统是 rootfs，包含我们熟悉的 `/dev`，`/bin` 等目录。对于 Base 镜像而言，底层直接复用 host 的 kernel，用户只需要提供用户空间文件系统 rootfs 即可。对于一个精简的操作系统，rootfs 可以很小，只需要包含最基本的命令、工具、程序就可以了。我们平时安装的 CentOS 除了 rootfs 还会选择装很多软件、服务、图形桌面等，需要几个 GB 就很正常了。

现在我们看一下 CentOS 镜像的 dockerfile：
```
FROM scrath
ADD centos-7-docker.tar.xz /
CMD ["/bin/bash"]
```
第一行指令表示镜像是从 0 开始构建。第二行 ADD 指令表示添加 CentOS 7 的 rootfs 到镜像。在制作这个镜像时，这个 tar 包会自动解压到 `/` 目录下，生成 `/dev`，`/proc`，`/bin` 等目录。
