当我们在使用 Docker 容器化应用和服务时，网络成为了一个至关重要的组成部分。Docker 网络不仅允许容器之间的通信，还支持容器与外部世界的连接。本文将详细介绍如何使用 Docker 网络相关的命令，以及分享一些使用 Docker 网络的最佳实践。

## 1. 基本概念

Docker 在默认安装时会创建三种网络类型：`bridge`、`none` 和 `host`。而对于更复杂的场景，比如跨多个 Docker 宿主机的网络通信，你还可以使用 `overlay` 网络：
- `bridge`: 默认网络类型，适用于同一宿主机上的容器间通信。
- `none`: 不配置网络，容器将不会有任何网络接口。
- `host`: 容器将使用宿主机的网络栈，这意味着容器的网络不会隔离。
- `overlay`: 用于 Docker 集群（Swarm）中，实现跨多个宿主机的容器间通信。

## 2. 命令

### 2.1 创建网络

你可以使用 `docker network create` 命令创建一个新的网络，对容器的网络访问进行更细致的控制。在此网络下运行的容器将能够相互发现并通信。命令格式如下所示：
```shell
docker network create [OPTIONS] NETWORK
```
如下所示，创建一个名为 `pub-network` 的网络：
```shell
(base) localhost:docker wy$ docker network create pub-network
846b87d6d3d27219dd9b5f399fc83347fd0d8c80b6682d324a3ea15482dc19cb
```

### 2.2 列出网络

你可以使用 `docker network ls` 命令列出系统中所有 Docker 网络。这可以帮助你快速查看现有的网络配置。命令格式如下所示：
```shell
docker network ls [OPTIONS]
```
> 或者使用 `docker network list`

如下所示列出系统中所有 Docker 网络：
```shell
(base) localhost:docker wy$ docker network ls
NETWORK ID     NAME                          DRIVER    SCOPE
efb26aa5c9bd   bridge                        bridge    local
8bdb7b99ce9d   host                          host      local
dbe4ee4cc122   none                          null      local
846b87d6d3d2   pub-network                   bridge    local
```
这个列表包含如下几个字段：
- NETWORK ID: 网络的唯一标识符。不同网络的 ID 是不同的，这个值在 Docker 主机内是唯一的。
- NAME: 网络的名称。用户可以创建额外的网络并自定义名称。
- DRIVER: 网络使用的驱动类型。Docker 提供了多种网络驱动，最常用的包括 bridge、overlay 和 host。
- SCOPE: 网络的作用域，表示网络是局部的（local）还是跨集群的（swarm）。

可以使用 `--no-trunc` 选项显示完整的网络id：
```shell
(base) localhost:docker wy$ docker network ls --no-trunc
NETWORK ID                                                         NAME                          DRIVER    SCOPE
75da76c9815504f14be998f71a7ac9f768087b9d984fb741ed356e82cb9d3cb9   bridge                        bridge    local
8bdb7b99ce9d14b73ec4ca761b377522ce9bbe8676cfb0a8808c46f0455a2ba6   host                          host      local
dbe4ee4cc12258fe66a367c02edcc02107d94b12d0fd87bc23279950fbb154ac   none                          null      local
846b87d6d3d27219dd9b5f399fc83347fd0d8c80b6682d324a3ea15482dc19cb   pub-network                   bridge    local
```
如果网络比较多，可以使用 `--filter 或 -f` 选项来筛选输出，可以帮助你快速找到特定的网络，有如下几种过滤器可供你选择：
- driver：网络驱动
- id：网络的唯一标识符
- label：网络标签，格式可以是 `label=<key>` 或者 `label=<key>=<value>`
- name：网络名称
- scope：网络作用域，可以是跨集群 `swarm`、全局 `global`、局部 `local`
- type：网络类型，可以是自定义 `custom`、预定义 `builtin`

如果你只想看到使用 bridge 驱动的网络，可以执行如下命令：
```shell
(base) localhost:docker wy$ docker network ls -f driver=bridge
NETWORK ID     NAME                          DRIVER    SCOPE
75da76c98155   bridge                        bridge    local
846b87d6d3d2   pub-network                   bridge    local
```
`type` 过滤器支持两个值：`Builtin` 显示预定义的网络(bridge, none, host)，而 `custom` 显示用户自定义的网络。如果你只想看到自定义的网络，可以执行如下命令：
```shell
(base) localhost:docker wy$ docker network ls --filter type=custom
NETWORK ID     NAME                          DRIVER    SCOPE
846b87d6d3d2   pub-network                   bridge    local
```

此外，还支持格式化选项(`--format`)使用 Go 模板漂亮地打印网络输出。下面列出了 Go 模板的有效占位符：

| Header One     | Header Two     |
| :------------- | :------------- |
| `.ID`       | 网络的唯一标识符 |
| `.Name`     | 网络名称 |
| `.Driver`   | 网络驱动 |
| `.Scope`    | 网络作用域 |
| `.IPv6`     | 网络中是否启用 IPv6 |
| `.Internal`     | 是否为内部网络 |
| `.Labels`     | 分配给网络的所有标签 |
| `.Label`     | 网络的特定标签值 |
| `.CreatedAt`     | 创建网络的时间 |

下面的例子使用一个没有头的模板，输出所有网络的 Name 和 Driver，以冒号(:)分隔：
```shell
(base) localhost:docker wy$ docker network ls --format "{{.Name}}: {{.Driver}}"
bridge: bridge
host: host
none: null
pub-network: bridge
```

### 2.3 查看网络详情

```shell
docker network inspect [OPTIONS] NETWORK [NETWORK...]
```

  示例
   docker network inspect my_bridge
   用于查看 my_bridge 网络的细节，包括哪些容器连接到了这个网络

### 2.4 连接容器到网络



  示例
   docker network connect my_bridge my_container
   这条命令将 my_container 容器连接到 my_bridge 网络。容器连接到网络后，可以跟网络内的其他容器通信。

### 2.5 断开容器与网络的连接
  示例
   docker network disconnect my_bridge my_container
   将 my_container 从 my_bridge 网络中断开。

### 2.6 删除网络

可以使用 `docker network rm` 命令来删除一个或多个网络。命令格式如下所示：
```
docker network rm NETWORK [NETWORK...]
```
> 或者使用 `docker network remove`

使用这个命令时，必须确保没有活动的容器连接到即将删除的网络。如果尝试删除正在使用的网络，命令将会失败，并显示错误信息：
```
(base) localhost:docker wy$ docker network rm mysql_backend-network
Error response from daemon: error while removing network: network mysql_backend-network id 3d1e87c551ec3659b15941b0653f18e3fab022df20d332b3f741265089d5d590 has active endpoints
```
当我们停止连接该网络的容器之后再删除即可正常：
```shell
(base) localhost:docker wy$ docker network rm mysql_backend-network
mysql_backend-network
```
如果需要在一个 `docker network rm` 命令中删除多个网络时，只需要提供多个网络名称或id。如下删除 id 为 3695c422697f，名称为 my-network 的网络：
```shell
(base) localhost:docker wy$ docker network rm mysql_backend-network wordpress_wordpress_network
mysql_backend-network
wordpress_wordpress_network
```
需要注意的是默认网络 bridge、none 和 host 不能被删除。
