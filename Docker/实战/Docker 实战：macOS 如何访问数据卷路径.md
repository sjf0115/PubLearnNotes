## 1. 背景

在 macOS 上，Docker 运行在一个以 LinuxKit 技术构建的轻量级虚拟机（VM）上，而非直接在宿主操作系统上。因此，当你使用 `docker volume inspect` 命令查看数据卷的 Mountpoint 时，这个路径是相对于 VM 的文件系统，而不是 macOS 的物理文件系统。这就是为什么你在 macOS 上无法直接找到这个路径的。例如，使用 `docker volume inspect` 命令显示的 Mountpoint 如下：
```shell
smartsi@smartsi ~ % docker volume inspect wordpress_data
[
    {
        "CreatedAt": "2024-05-10T02:42:16Z",
        "Driver": "local",
        "Labels": {
            "com.docker.compose.project": "wordpress",
            "com.docker.compose.version": "2.26.1",
            "com.docker.compose.volume": "data"
        },
        "Mountpoint": "/var/lib/docker/volumes/wordpress_data/_data",
        "Name": "wordpress_data",
        "Options": null,
        "Scope": "local"
    }
]
```
当我们去查找 Mountpoint 所在的路径时却发现找不到：
```
smartsi@smartsi ~ % cd /var/lib/docker/volumes/wordpress_data/
cd: no such file or directory: /var/lib/docker/volumes/wordpress_data/
```
此路径实际上是虚拟机内的路径，不会直接映射到 macOS 的路径中。

## 2. 如何访问数据卷内容？

要访问这个路径中的内容，你可以运行一个新的容器，将数据卷挂载到这个容器，并通过容器来操作这些数据。例如，你可以运行一个带有 shell 环境的 Alpine 容器来访问：
```shell
smartsi@smartsi ~ % docker run -it --rm -v wordpress_data:/data alpine sh
Unable to find image 'alpine:latest' locally
latest: Pulling from library/alpine
9b3977197b4f: Already exists
Digest: sha256:21a3deaa0d32a8057914f36584b5288d2e5ecc984380bc0118285c70fa8c9300
Status: Downloaded newer image for alpine:latest
/ #
```
> 首次运行会 pull 镜像

然后在容器的 shell 环境中，你可以使用 `ls /data`、`cat`、`vim` 或其他命令来浏览和编辑 `/data` 目录中的文件（这个目录实际上是你数据卷的内容）：
```shell
smartsi@smartsi ~ % docker run -it --rm -v wordpress_data:/data alpine sh
/ # ls -al
total 68
drwxr-xr-x    1 root     root          4096 May 13 01:26 .
drwxr-xr-x    1 root     root          4096 May 13 01:26 ..
-rwxr-xr-x    1 root     root             0 May 13 01:26 .dockerenv
drwxr-xr-x    2 root     root          4096 Nov 24  2021 bin
drwxr-xr-x    5 xfs      xfs           4096 May 10 02:42 data
drwxr-xr-x    5 root     root           360 May 13 01:26 dev
drwxr-xr-x    1 root     root          4096 May 13 01:26 etc
drwxr-xr-x    2 root     root          4096 Nov 24  2021 home
drwxr-xr-x    7 root     root          4096 Nov 24  2021 lib
drwxr-xr-x    5 root     root          4096 Nov 24  2021 media
drwxr-xr-x    2 root     root          4096 Nov 24  2021 mnt
drwxr-xr-x    2 root     root          4096 Nov 24  2021 opt
dr-xr-xr-x  219 root     root             0 May 13 01:26 proc
drwx------    1 root     root          4096 May 13 01:26 root
drwxr-xr-x    2 root     root          4096 Nov 24  2021 run
drwxr-xr-x    2 root     root          4096 Nov 24  2021 sbin
drwxr-xr-x    2 root     root          4096 Nov 24  2021 srv
dr-xr-xr-x   11 root     root             0 May 13 01:26 sys
drwxrwxrwt    2 root     root          4096 Nov 24  2021 tmp
drwxr-xr-x    7 root     root          4096 Nov 24  2021 usr
drwxr-xr-x   12 root     root          4096 Nov 24  2021 var
/ #
```
这时候你就能访问数据卷下的文件了。

现在我们详细讲解一下这个命令：
- `docker run`: 这是 Docker CLI 的核心命令之一，用来运行一个新的容器实例。
- `it`: 这实际上是 `-i` 和 `-t` 两个选项的组合。`-i` 表示以交互模式运行容器，`-t` 分配一个伪终端。整体上 `-it` 使你能够在运行的容器内进行交互式操作，例如使用 shell 进行命令输入。
- `--rm`: 该选项用于在容器停止时自动删除容器。这样，在你结束交互式会话并退出容器时，容器不会留在系统上占用空间，而是被清理掉。
- `-v wordpress_data:/data`: 这是容器的卷挂载选项，使用 `-v` 表示。`wordpress_data` 是你的数据卷名称，`/data` 是容器内的挂载点路径。这意味着 `wordpress_data` 数据卷会被挂载到容器的 `/data` 目录下，因此容器通过 `/data` 路径就可以访问到 `wordpress_data` 中的数据。
- `alpine`: 这是 Docker 镜像的名称，`alpine` 指的是一个小巧而且功能完备的 Linux 发行版。因为体积小，Alpine Linux 非常适合用作运行临时命令的容器基础。
- `sh`: 这是你要在容器内运行的命令。sh 是 shell 的一种，它允许你在容器内执行进一步的命令行操作。

这个命令整体的功能是启动一个新的以 Alpine Linux 为基础，交互式的临时容器，其中将你指定的 Docker 数据卷 `wordpress_data` 挂载在容器的 `/data` 目录。你可以在这个 shell 中执行各种操作，比如查看文件内容、编辑文件、运行应用程序等等。完成操作后，退出容器（例如输入 exit 命令或按 Ctrl+D），容器就会被自动删除。

## 3. 数据管理

此外你还可以实现在容器和本地文件系统之间复制文件。你可以使用如下命令将容器上的 `/var/www/html` 文件夹复制到当前路径 backup 目录下：
```shell
docker cp docker_wordpress:/var/www/html backup/
```
当然你也可以将宿主机(本地)上的文件复制到容器上。使用如下格式命令即可：
```shell
docker cp [OPTIONS] SRC_PATH|- CONTAINER:DEST_PATH
```
