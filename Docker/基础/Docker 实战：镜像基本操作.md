
镜像是运行容器的前提，官方的 Docker Hub 网站已经提供了数十万个镜像供大家开放下载。本文主要介绍 Docker 镜像的基本操作。

## 1. 搜索镜像 search

可以使用 `docker search` 命令搜索 Docker Hub 镜像仓库中的镜像。该命令格式如下所示：

```shell
docker search [option] KEYWORD
```

其中 KEYWORD 表示你要搜索的关键字，option 表示可选的选项。如下示例搜索 Docker Hub 镜像仓库提供的带 busybox 关键字的镜像：

```
smartsi@localhost ~ % docker search busybox
NAME                                DESCRIPTION                                      STARS     OFFICIAL
busybox                             Busybox base image.                              3243      [OK]
rancher/busybox                                                                      0
chainguard/busybox                  Build, ship and run secure software with Cha…   0
openebs/busybox-client                                                               1
antrea/busybox                                                                       1
airbyte/busybox                                                                      0
hugegraph/busybox                   test image                                       2
privatebin/chown                     Docker image providing busybox' chown, stat…   1
yauritux/busybox-curl               Busybox with CURL                                25
radial/busyboxplus                  Full-chain, Internet enabled, busybox made f…   56
vukomir/busybox                     busybox and curl                                 1
arm64v8/busybox                     Busybox base image.                              8
odise/busybox-curl                                                                   4
busybox42/zimbra-docker-centos      A Zimbra Docker image, based in ZCS 8.8.9 an…   2
amd64/busybox                       Busybox base image.                              1
busybox42/alpine-pod                                                                 0
joeshaw/busybox-nonroot             Busybox container with non-root user nobody      2
ppc64le/busybox                     Busybox base image.                              1
p7ppc64/busybox                     Busybox base image for ppc64.                    2
s390x/busybox                       Busybox base image.                              3
i386/busybox                        Busybox base image.                              3
arm32v7/busybox                     Busybox base image.                              10
prom/busybox                        Prometheus Busybox Docker base images            2
busybox42/nginx_php-docker-centos   This is a nginx/php-fpm server running on Ce…   1
spotify/busybox                     Spotify fork of https://hub.docker.com/_/bus…   1
```

此外 `docker search` 命令支持的选项如下所示：

- `-f，--filter filter`：过滤输出内容
- `--format <string>`：格式化输出内容
- `--limit <int>`：限制输出结果个数，默认为 25 个
- `--no-trunc`：不截断输出结果



如果输出内容过多，我们可以使用`-f，--filter filter`选项来对内容进行过滤。过滤选项格式是一个键值对 `key=value`。如果有多个过滤器，则传递多个选项，例如 `--filter is-official=true --filter stars=3`。目前支持的过滤器 Filter 有：

- `stars`：传递一个 Int 值，表示镜像至少的 stars 数
- `is-automated`：传递一个 boolean 值，表示是否处于自动化模式
- `is-official`：传递一个 boolean 值，表示是否是官方镜像

如下所示示例搜索名称中包含 `busybox` 关键字，至少有3颗星，并且是官方版本的镜像：

```shell
smartsi@localhost ~ % docker search --filter is-official=true --filter stars=3 busybox
NAME      DESCRIPTION           STARS     OFFICIAL
busybox   Busybox base image.   3243      [OK]
```

我们还可以对输出内容进行控制，可以使用 `--format <string>` 来使用 Go 模板来格式化输出内容。Go模板的有效占位符如下所示：

| 占位符            | 说明              |
|:-------------- |:--------------- |
| `.Name`        | 镜像名称            |
| `.Description` | 镜像描述            |
| `.StarCount`   | 镜像 Star 数       |
| `.IsOfficial`  | 是否是官方，是展示 OK    |
| `.IsAutomated` | 是否是自动化模式，是展示 OK |

搜索命令将输出与模板声明完全相同的数据。如下示例使用了一个不包含列表头的模板，并输出所有镜像的名称和 Star 数，以冒号(`:`)分隔:

```shell
smartsi@localhost ~ % docker search --format "{{.Name}}: {{.StarCount}}" busybox
busybox: 3243
rancher/busybox: 0
chainguard/busybox: 0
openebs/busybox-client: 1
antrea/busybox: 1
airbyte/busybox: 0
hugegraph/busybox: 2
privatebin/chown: 1
yauritux/busybox-curl: 25
radial/busyboxplus: 56
vukomir/busybox: 1
arm64v8/busybox: 8
odise/busybox-curl: 4
busybox42/zimbra-docker-centos: 2
amd64/busybox: 1
busybox42/alpine-pod: 0
joeshaw/busybox-nonroot: 2
p7ppc64/busybox: 2
ppc64le/busybox: 1
s390x/busybox: 3
i386/busybox: 3
arm32v7/busybox: 10
prom/busybox: 2
busybox42/nginx_php-docker-centos: 1
spotify/busybox: 1
```

如果在模板中添加 `table` 指令还会包含列表头，如下示例添加  `table` 指令来输出列表头：

```shell
smartsi@localhost ~ % docker search --format "table {{.Name}}: {{.StarCount}}" busybox
NAME: STARS
busybox: 3243
rancher/busybox: 0
chainguard/busybox: 0
openebs/busybox-client: 1
antrea/busybox: 1
airbyte/busybox: 0
hugegraph/busybox: 2
privatebin/chown: 1
yauritux/busybox-curl: 25
radial/busyboxplus: 56
vukomir/busybox: 1
arm64v8/busybox: 8
odise/busybox-curl: 4
busybox42/zimbra-docker-centos: 2
amd64/busybox: 1
busybox42/alpine-pod: 0
joeshaw/busybox-nonroot: 2
p7ppc64/busybox: 2
ppc64le/busybox: 1
s390x/busybox: 3
i386/busybox: 3
arm32v7/busybox: 10
prom/busybox: 2
busybox42/nginx_php-docker-centos: 1
spotify/busybox: 1
```

## 2. 获取镜像 image pull

可以使用 `docker [image] pull` 命令直接从 Docker Hub 镜像仓库来下载镜像。该命令格式如下所示:

```shell
docker [image] pull NAME[:TAG]
```

其中，NAME 是镜像仓库名称（用来区分镜像）, TAG是镜像的标签（往往用来表示版本信息）。通常情况下，描述一个镜像需要包括 `NAME+Tag` 信息。如下示例获取一个 ubuntu 系统的基础镜像：

```shell
smartsi@localhost ~ % docker image pull ubuntu
Using default tag: latest
latest: Pulling from library/ubuntu
a39c84e173f0: Pull complete
Digest: sha256:626ffe58f6e7566e00254b638eb7e0f3b11d4da9675088f4781a50ae288f3322
Status: Downloaded newer image for ubuntu:latest
docker.io/library/ubuntu:latest
```

如果不显示指定 TAG，则默认会拉取 latest 标签镜像，下载仓库中最新版本的镜像。一般来说，镜像的 latest 标签意味着该镜像的内容会跟踪最新版本的变更而变化，内容是不稳定的。因此，从稳定性上考虑，不要在生产环境中使用默认的 latest 标记的镜像，而是使用镜像的具体版本标签信息。如下示例拉取 22.04 版本的 ubuntu 镜像：

```shell
smartsi@localhost ~ % docker image pull ubuntu:22.04
22.04: Pulling from library/ubuntu
47ebf8c90525: Pull complete
Digest: sha256:f154feaf13b51d16e2b4b5575d69abc808da40c4b80e3a5055aaa4bcc5099d5b
Status: Downloaded newer image for ubuntu:22.04
docker.io/library/ubuntu:22.04
```

你可能注意到在不同的镜像仓库服务器的情况下，可能会出现镜像重名的情况。严格地讲，镜像的仓库名称中还应该添加仓库地址（即 registry，注册服务器）作为前缀，只是默认使用的是官方 Docker Hub 服务，该前缀可以忽略。例如，`docker image pull ubuntu:22.04` 命令相当于 `docker image pull registry.hub.docker.com/ubuntu:22.04` 命令，即从默认的注册服务器 Docker Hub Registry 中的 ubuntu 仓库来下载标记为 22.04 的镜像。如果从非官方的仓库下载，则需要在仓库名称前指定完整的仓库地址。例如从网易蜂巢的镜像源来下载 `ubuntu:22.04` 镜像，可以使用 `docker image pull hub.c.163.com/public/ubuntu:22.04` 命令。

## 3. 查看镜像信息 images/image ls

可以使用 `docker images` 或者 `docker image ls` 命令列出本地主机上已有镜像的基本信息。如下示例列出了本地主机上目前为止下载的镜像：

```shell
smartsi@localhost ~ % docker images
REPOSITORY    TAG       IMAGE ID       CREATED       SIZE
ubuntu        22.04     2465309f578e   2 years ago   68.7MB
ubuntu        latest    d5ca7a445605   2 years ago   65.6MB
hello-world   latest    18e5af790473   2 years ago   9.14kB
centos        latest    e6a0117ec169   2 years ago   272MB

smartsi@localhost ~ % docker image ls
REPOSITORY    TAG       IMAGE ID       CREATED       SIZE
ubuntu        22.04     2465309f578e   2 years ago   68.7MB
ubuntu        latest    d5ca7a445605   2 years ago   65.6MB
hello-world   latest    18e5af790473   2 years ago   9.14kB
centos        latest    e6a0117ec169   2 years ago   272MB
```

在输出的信息中，可以看到有如下几个字段：

- REPOSITORY：镜像仓库，表示来自于哪个仓库，比如 ubuntu 表示 ubuntu 系列的基础镜像

- TAG：镜像标签，用于标记来自于同一镜像仓库的不同镜像，例如 ubuntu 镜像仓库中有多个镜像，通过 22.04、latest 等标签来表示不同的版本

- IMAGE ID：镜像唯一ID，需要注意的是如果两个镜像的 ID 相同，说明它们实际上是一个镜像，只是具有不同的标签名称而已

- CREATED：镜像创建时间，表示镜像的最后的更新时间

- SIZE：镜像大小，只是镜像的逻辑体积大小，实际上由于相同的镜像层本地只会存储一份，物理上占用的存储空间会小于各逻辑体积之和



上述命令还接收一个可选参数 `[REPOSITORY[:TAG]]`，表示只输出与镜像存储仓库和标签匹配的镜像。如果指定 REPOSITORY 但是没有指定 TAG,  会输出指定存储库中的所有镜像。如下所示示例输出镜像仓库中所有的 ubuntu 镜像:

```shell
smartsi@localhost ~ % docker images ubuntu
REPOSITORY   TAG       IMAGE ID       CREATED       SIZE
ubuntu       22.04     2465309f578e   2 years ago   68.7MB
ubuntu       latest    d5ca7a445605   2 years ago   65.6MB


smartsi@localhost ~ % docker image ls ubuntu
REPOSITORY   TAG       IMAGE ID       CREATED       SIZE
ubuntu       22.04     2465309f578e   2 years ago   68.7MB
ubuntu       latest    d5ca7a445605   2 years ago   65.6MB
```

需要注意的是 `[REPOSITORY[:TAG]]` 值必须是精确匹配的。这意味着 `docker images ubun` 是不能与 `ubuntu` 镜像匹配的。



此外上述命令还支持一些可选的选项，具体如下所示：

- `-a, --all=true|false`：列出所有（包括临时文件）镜像文件，默认为否

- `--digests=true|false`：列出镜像的数字摘要值，默认为否

  ```shell
  smartsi@localhost ~ % docker images ubuntu --digests=false
  REPOSITORY   TAG       IMAGE ID       CREATED       SIZE
  ubuntu       22.04     2465309f578e   2 years ago   68.7MB
  ubuntu       latest    d5ca7a445605   2 years ago   65.6MB

  smartsi@localhost ~ % docker images ubuntu --digests=true
  REPOSITORY   TAG       DIGEST                                                                    IMAGE ID       CREATED       SIZE
  ubuntu       22.04     sha256:f154feaf13b51d16e2b4b5575d69abc808da40c4b80e3a5055aaa4bcc5099d5b   2465309f578e   2 years ago   68.7MB
  ubuntu       latest    sha256:626ffe58f6e7566e00254b638eb7e0f3b11d4da9675088f4781a50ae288f3322   d5ca7a445605   2 years ago   65.6MB
  ```

- `-f, --filter=[]`：过滤列出的镜像，如 `dangling=true`只显示没有被使用的镜像；也可指定带有特定标注的镜像等

- `--format="<string>"`：控制输出格式，如 `.ID` 代表 ID 信息，`.Repository` 代表仓库信息等  

  ```shell
  smartsi@localhost ~ % docker images --format "{{.ID}}: {{.Repository}}"
  2465309f578e: ubuntu
  d5ca7a445605: ubuntu
  18e5af790473: hello-world
  e6a0117ec169: centos
  ```

- `--no-trunc=true|false`：对输出结果中太长的部分是否进行截断，如镜像的ID信息，默认为是

- `-q, --quiet=true|false`：仅输出ID信息，默认为否。



## 4. 查看镜像详细信息 inspect/image inspect

可以使用 `docker [image] inspect` 命令获取镜像的详细信息，包括制作者、适应架构、各层的数字摘要等。该命令格式如下所示:

```shell
docker image inspect [OPTIONS] NAME|ID [NAME|ID...]
```

默认情况下，该命令返回结果会以 JSON 数组的形式呈现。如下所示示例返回 ubuntu 镜像最新版本的详细信息：

```json
smartsi@localhost ~ % docker image inspect ubuntu
[
    {
        "Id": "sha256:d5ca7a4456053674d490803005766890dd19e3f7e789a48737c0d462da531f5d",
        "RepoTags": [
            "ubuntu:latest"
        ],
        "RepoDigests": [
            "ubuntu@sha256:626ffe58f6e7566e00254b638eb7e0f3b11d4da9675088f4781a50ae288f3322"
        ],
        "Parent": "",
        "Comment": "",
        "Created": "2021-10-16T01:47:45.87597179Z",
        "ContainerConfig": {
            "Hostname": "",
            "Domainname": "",
            "User": "",
            "AttachStdin": false,
            "AttachStdout": false,
            "AttachStderr": false,
            "Tty": false,
            "OpenStdin": false,
            "StdinOnce": false,
            "Env": null,
            "Cmd": null,
            "Image": "",
            "Volumes": null,
            "WorkingDir": "",
            "Entrypoint": null,
            "OnBuild": null,
            "Labels": null
        },
        "DockerVersion": "20.10.7",
        "Author": "",
        "Config": {
            "Hostname": "",
            "Domainname": "",
            "User": "",
            "AttachStdin": false,
            "AttachStdout": false,
            "AttachStderr": false,
            "Tty": false,
            "OpenStdin": false,
            "StdinOnce": false,
            "Env": [
                "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            ],
            "Cmd": [
                "bash"
            ],
            "Image": "sha256:0d812b4a843eb3323c988e528edccf15f39c7150697f199bc2504abdbe346d33",
            "Volumes": null,
            "WorkingDir": "",
            "Entrypoint": null,
            "OnBuild": null,
            "Labels": null
        },
        "Architecture": "arm64",
        "Variant": "v8",
        "Os": "linux",
        "Size": 65593591,
        "GraphDriver": {
            "Data": {
                "MergedDir": "/var/lib/docker/overlay2/1fe01abc97e3ba0de9d3ba2252ab71307516ba2e9785754fc9e598695ae6801b/merged",
                "UpperDir": "/var/lib/docker/overlay2/1fe01abc97e3ba0de9d3ba2252ab71307516ba2e9785754fc9e598695ae6801b/diff",
                "WorkDir": "/var/lib/docker/overlay2/1fe01abc97e3ba0de9d3ba2252ab71307516ba2e9785754fc9e598695ae6801b/work"
            },
            "Name": "overlay2"
        },
        "RootFS": {
            "Type": "layers",
            "Layers": [
                "sha256:350f36b271dee3d47478fbcd72b98fed5bbcc369632f2d115c3cb62d784edaec"
            ]
        },
        "Metadata": {
            "LastTagTime": "0001-01-01T00:00:00Z"
        },
        "Container": ""
    }
]
```

上面命令默认返回的是详细信息的全部内容，如果我们只要一项内容时，可以使用 `-f` 或者 `--format` 选项来指定。如下所示示例获取镜像的 Architecture 和 Id 信息：

```shell
smartsi@localhost ~ % docker image inspect -f='{{.Architecture}}: {{.Id}}' ubuntu
arm64: sha256:d5ca7a4456053674d490803005766890dd19e3f7e789a48737c0d462da531f5d
```

`docker inspect` 命令通过 ID 或者名称匹配任何类型的对象。在某些情况下，不同类型的对象(例如，容器和数据卷)有相同的名称，从而导致结果不明确。这时候可以使用 `--type` 选项来限定指定类型的对象，可供选择的类型有 `container`、`image`、`node`、`network`、`secret`、`service`、`volume`、`task`、`plugin`。例如使用 `docker inspect --type=volume myvolume` 查找名为 myvolume 的数据卷。



## 5. 查看镜像历史 history/image history

既然镜像文件由多个层组成，那么怎么知道各个层的内容具体是什么呢？这时候可以使用`docker image history` 命令列出各层的创建信息。该命令格式如下所示：

```shell
docker [image] history [OPTIONS] IMAGE
```

如下示例返回 ubuntu 镜像最新版本各层的创建信息：

```shell
smartsi@localhost ~ % docker image history ubuntu
IMAGE          CREATED       CREATED BY                                       SIZE      COMMENT
d5ca7a445605   2 years ago   /bin/sh -c #(nop)  CMD ["bash"]                  0B
<missing>      2 years ago   /bin/sh -c #(nop) ADD file:ff4909f2124325dac…   65.6MB
```

此外`docker image history` 命令还支持一些可选选项，具体如下所示：

- `--format`：控制输出格式，如`.ID`代表 ID 信息，`.CreatedAt` 代表创建时间，`.CreatedBy` 代表用于创建镜像的命令等

  ```shell
  smartsi@localhost ~ % docker image history --format "{{.ID}}: {{.CreatedSince}}" ubuntu
  d5ca7a445605: 2 years ago
  <missing>: 2 years ago
  ```

- `--no-trunc=true|false`：对输出结果中太长的部分是否进行截断，如镜像的ID信息，默认为是

- `-q, --quiet=true|false`：仅输出ID信息，默认为否。



## 6. 添加镜像标签 tag/image tag

为了方便在后续工作中使用特定镜像，还可以使用 `docker image tag` 命令来为本地镜像任意添加新的标签。该命令格式如下所示：

```shell
docker [image] tag SOURCE_IMAGE[:TAG] TARGET_IMAGE[:TAG]
```

如下示例将本地镜像中名称为 ubuntu ，标签为 22.04 的镜像添加一个新的 `ubuntu:version-22.04` 的镜像标签：

```shell
docker image tag ubuntu:22.04 ubuntu:version-22.04
```

使用 `docker image ls` 命令列出本地主机上的镜像，可以看到多了一个 `version-22.04` 标签的镜像：

```shell
smartsi@localhost ~ % docker image ls
REPOSITORY    TAG             IMAGE ID       CREATED       SIZE
ubuntu        22.04           2465309f578e   2 years ago   68.7MB
ubuntu        version-22.04   2465309f578e   2 years ago   68.7MB
ubuntu        latest          d5ca7a445605   2 years ago   65.6MB
hello-world   latest          18e5af790473   2 years ago   9.14kB
centos        latest          e6a0117ec169   2 years ago   272MB
```

如果只指定镜像名称而不指定标签信息，则在对应 `latest` 标签的镜像上添加标签。你可能注意到， `ubuntu:version-22.04` 镜像的ID跟 `ubuntu:22.04` 完全一致，它们实际上指向了同一个镜像文件，只是别名不同而已。`docker image tag` 命令添加的标签实际上起到了类似链接的作用。



## 7. 删除镜像 image rm

可以使用 `docker image rm` 命令删除镜像。该命令格式如下所示：

```shell
docker image rm [OPTIONS] IMAGE [IMAGE...]
```

如下示例删除本地镜像中名称为 ubuntu ，标签为 version-22.04 的镜像：

```shell
smartsi@localhost ~ % docker image rm ubuntu:version-22.04
Untagged: ubuntu:version-22.04
```

你可能会想到，`ubuntu:22.04` 镜像是否会受到此命令的影响（毕竟 `ubuntu:version-22.04` 是通过 `ubuntu:22.04` 重新打标签生成的）。不用担心，当同一个镜像拥有多个标签的时候，`docker image rm`命令只是删除了该镜像多个标签中的指定标签而已，并不影响镜像文件。因此上述操作相当于只是删除了镜像 `2465309f578e` 的一个标签副本而已：

```shell
smartsi@localhost ~ % docker image ls
REPOSITORY    TAG             IMAGE ID       CREATED       SIZE
ubuntu        22.04           2465309f578e   2 years ago   68.7MB
ubuntu        version-22.04   2465309f578e   2 years ago   68.7MB
ubuntu        latest          d5ca7a445605   2 years ago   65.6MB
hello-world   latest          18e5af790473   2 years ago   9.14kB
centos        latest          e6a0117ec169   2 years ago   272MB
smartsi@localhost ~ %
smartsi@localhost ~ % docker image rm ubuntu:version-22.04
Untagged: ubuntu:version-22.04
smartsi@localhost ~ %
smartsi@localhost ~ % docker image ls
REPOSITORY    TAG       IMAGE ID       CREATED       SIZE
ubuntu        22.04     2465309f578e   2 years ago   68.7MB
ubuntu        latest    d5ca7a445605   2 years ago   65.6MB
hello-world   latest    18e5af790473   2 years ago   9.14kB
centos        latest    e6a0117ec169   2 years ago   272MB
```

但是如果当镜像只有一个标签的时候，此时使用该命令去删除时会彻底删除镜像。如下所示删除 `centos:latest` 镜像时会删除这个镜像文件的所有文件层：

```shell
smartsi@localhost ~ % docker image rm centos:latest
Untagged: centos:latest
Untagged: centos@sha256:a27fd8080b517143cbbbab9dfb7c8571c40d67d534bbdee55bd6c473f432b177
Deleted: sha256:e6a0117ec169eda93dc5ca978c6ac87580e36765a66097a6bfb6639a3bd4038a
Deleted: sha256:d871dadfb37b53ef1ca45be04fc527562b91989991a8f545345ae3be0b93f92a
```

此外`docker image rm` 命令还支持一些可选选项，具体如下所示：

- `-f, -force`：强制删除镜像，即使有容器依赖它

- `-no-prune`：不要清理未带标签的父镜像。



## 8. 清理镜像 image prune

使用 Docker 一段时间后，系统中可能会遗留一些临时的镜像文件，以及一些没有被使用的镜像，可以通过 `docker image prune`命令来进行清理。该命令格式如下所示：

```shell
docker image prune [OPTIONS]
```

此外`docker image prune` 命令还支持一些可选选项，具体如下所示：

- `-a, -all`：删除所有无用镜像，不光是临时镜像；

- `-filter filter`：只清理符合给定过滤器的镜像；

- ` -f, -force`：强制删除镜像，而不进行提示确认



## 9. 构建镜像 image build

可以使用 `docker build` 命令从 Dockerfile 文件中构建镜像。该命令格式如下所示：

```shell
docker image build [OPTIONS] PATH | URL | -
```

Dockerfile 是一个文本文件，利用给定的指令描述基于某个父镜像创建新镜像的过程。下面给出 Dockerfile 的一个简单示例，基于轻量级的 Alpine Linux 作为基础镜像然后输出 "Hello World"：

```shell
# 使用轻量级的Alpine Linux作为基础镜像
FROM alpine
# 设置容器启动时执行的命令
CMD ["echo", "Hello World"]
```

将上述文本内容存储在 Dockerfile 文件中，使用 `docker image build` 命令来构建镜像：

```shell
smartsi@localhost ~ % docker image build -t hello-world:v1 .
[+] Building 20.8s (5/5) FINISHED                                                                                                                                                      docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                                                                                   0.0s
 => => transferring dockerfile: 169B                                                                                                                                                                   0.0s
 => [internal] load metadata for docker.io/library/alpine:latest                                                                                                                                      19.8s
 => [internal] load .dockerignore                                                                                                                                                                      0.0s
 => => transferring context: 2B                                                                                                                                                                        0.0s
 => [1/1] FROM docker.io/library/alpine:latest@sha256:21a3deaa0d32a8057914f36584b5288d2e5ecc984380bc0118285c70fa8c9300                                                                                 1.0s
 => => resolve docker.io/library/alpine:latest@sha256:21a3deaa0d32a8057914f36584b5288d2e5ecc984380bc0118285c70fa8c9300                                                                                 0.0s
 => => sha256:8e1d7573f448dc8d0ca13293b1768959a2528ff04be704f1f3d35fd3dbf6da3d 1.49kB / 1.49kB                                                                                                         0.0s
 => => sha256:9b3977197b4f2147bdd31e1271f811319dcd5c2fc595f14e81f5351ab6275b99 2.72MB / 2.72MB                                                                                                         0.8s
 => => sha256:21a3deaa0d32a8057914f36584b5288d2e5ecc984380bc0118285c70fa8c9300 1.64kB / 1.64kB                                                                                                         0.0s
 => => sha256:c74f1b1166784193ea6c8f9440263b9be6cae07dfe35e32a5df7a31358ac2060 528B / 528B                                                                                                             0.0s
 => => extracting sha256:9b3977197b4f2147bdd31e1271f811319dcd5c2fc595f14e81f5351ab6275b99                                                                                                              0.1s
 => exporting to image                                                                                                                                                                                 0.0s
 => => exporting layers                                                                                                                                                                                0.0s
 => => writing image sha256:492ccfc87a56ae81308c52e938c03e618ba2c6c686f511d359d11e3fd34743ff                                                                                                           0.0s
 => => naming to docker.io/library/hello-world:v1                                                                                                                                                      0.0s

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/u6lj14hmvhhulupbd8p4ychgi
smartsi@localhost ~ %
smartsi@localhost ~ %
smartsi@localhost ~ % docker image ls
REPOSITORY    TAG       IMAGE ID       CREATED       SIZE
ubuntu        22.04     2465309f578e   2 years ago   68.7MB
ubuntu        v22.04    2465309f578e   2 years ago   68.7MB
hello-world   v1        492ccfc87a56   2 years ago   5.33MB
ubuntu        latest    d5ca7a445605   2 years ago   65.6MB
hello-world   latest    18e5af790473   2 years ago   9.14kB
```

此时多了一个 `ubuntu:v1` 的镜像。



## 10. 保存镜像 image save

如果要导出镜像到本地文件，可以使用 `docker [image] save` 命令。该命令支持`-o`、`-output string` 参数，导出镜像到指定的文件中。该命令格式如下所示：

```shell
docker [image] save [OPTIONS] IMAGE [IMAGE...]
```

如下示例将导出 `ubuntu:v22.04` 镜像为 `ubuntu_22.04.tar` 文件：

```shell
smartsi@localhost ~ % docker image save -o ubuntu_22.04.tar ubuntu:v22.04
smartsi@localhost ~ %
smartsi@localhost ~ % ls ubuntu*
ubuntu_22.04.tar
```

可选选项 `-o` 或者 `--output` 用来指定输出的文件。你也可以不使用可选选项，如下所示：

```shell
smartsi@localhost ~ % docker image save ubuntu:v22.04 > ubuntu_22.04.tar
smartsi@localhost ~ %
smartsi@localhost ~ % ls ubuntu*
ubuntu_22.04.tar
```



## 11. 加载镜像 image load

可以使用 `docker [image] load` 命令将导出的 tar 文件再导入到本地镜像库。该命令格式如下：

```shell
docker image load [OPTIONS]
```

`docker [image] load` 命令支持 `-i` 或者 `--input` 可选选项来从指定文件中读取 tar 文件。 如下示例将导出的 `ubuntu_22.04.tar` 文件导入为 `ubuntu:v22.04` 镜像：

```shell
smartsi@localhost ~ % docker image ls
REPOSITORY    TAG       IMAGE ID       CREATED       SIZE
ubuntu        22.04     2465309f578e   2 years ago   68.7MB
ubuntu        latest    d5ca7a445605   2 years ago   65.6MB
hello-world   latest    18e5af790473   2 years ago   9.14kB
smartsi@localhost ~ %
smartsi@localhost ~ % docker image load --input ubuntu_22.04.tar
Loaded image: ubuntu:v22.04
smartsi@localhost ~ %
smartsi@localhost ~ % docker image ls
REPOSITORY    TAG       IMAGE ID       CREATED       SIZE
ubuntu        22.04     2465309f578e   2 years ago   68.7MB
ubuntu        v22.04    2465309f578e   2 years ago   68.7MB
ubuntu        latest    d5ca7a445605   2 years ago   65.6MB
hello-world   latest    18e5af790473   2 years ago   9.14kB
```

你也可以不使用可选选项，如下所示：

```shell
smartsi@localhost ~ % docker image rm ubuntu:v22.04
Untagged: ubuntu:v22.04
smartsi@localhost ~ %
smartsi@localhost ~ % docker image load <  ubuntu_22.04.tar
Loaded image: ubuntu:v22.04
smartsi@localhost ~ %
smartsi@localhost ~ % docker image ls
REPOSITORY    TAG       IMAGE ID       CREATED       SIZE
ubuntu        22.04     2465309f578e   2 years ago   68.7MB
ubuntu        v22.04    2465309f578e   2 years ago   68.7MB
ubuntu        latest    d5ca7a445605   2 years ago   65.6MB
hello-world   latest    18e5af790473   2 years ago   9.14kB
```
