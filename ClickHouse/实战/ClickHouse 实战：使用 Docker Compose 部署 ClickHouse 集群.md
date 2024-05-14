
在今天的这篇文章中，我们将详细介绍如何使用 Docker Compose 来部署 ClickHouse 数据库。ClickHouse 是一个用于在线分析处理（OLAP）的列式数据库管理系统（DBMS），以其高速查询性能而闻名。使用 Docker Compose，我们可以方便地定义和运行多容器 Docker 应用程序，使部署 ClickHouse 变得更为简单和高效。

## 1. ClickHouse 简介

ClickHouse 是战斗民族俄罗斯搜索巨头 Yandex 公司开源的一个极具"战斗力"的实时数据分析数据库，是面向 OLAP 的分布式列式 DBMS，圈内人戏称为“喀秋莎数据库”。ClickHouse 有一个简称 CK，与 Hadoop、Spark 这些巨无霸组件相比，ClickHouse 很轻量级。最初是作为一个内部工具于2016年开源。ClickHouse 特别适用于实时生成分析数据报告的应用场景。作为一个高性能的列式数据库，ClickHouse 以其出色的查询速度、扩展性和灵活性，在海量数据处理和实时分析领域占有一席之地。关于 ClickHouse 详细介绍请查阅[实时数据分析数据库 ClickHouse 介绍](https://smartsi.blog.csdn.net/article/details/138887132)。


## 2. Docker Compose 简介

Docker Compose 是一个用于定义和运行多容器 Docker 应用程序的工具。通过 Compose，您可以通过一个 YAML 文件来配置您的应用的服务。然后，使用一个简单的命令，就可以创建并启动所有配置中的服务。这让组织和管理容器变成了一件轻而易举的事情。

在开始之前，首先需要确保已经安装了 Docker Compose，如果没有安装或者不熟悉 Compose 的具体查阅 [Docker 实战：使用 Docker Compose 实现高效的多容器部署](https://smartsi.blog.csdn.net/article/details/138414972)。

## 3. Docker Compose 部署 ClickHouse

接下来，我们将一步步通过 Docker Compose 来部署 ClickHouse 集群。

### 3.1 创建项目目录

首先为项目创建一个目录。在这里，在我们的工作目录 `/opt/workspace/docker` 下创建一个名为 `clickhouse` 的项目 ：
```
smartsi@localhost docker % mkdir clickhouse
smartsi@localhost docker % cd clickhouse
```
> 该目录是应用程序镜像的上下文。该目录应该只包含用于构建该镜像的资源。


### 3.2 创建配置文件

服务端的配置文件核心包括全局配置文件 `config.xml` 和用户配置文件 `users.xml` 等，不建议你直接修改这两个配置文件。ClickHouse 为我们提供了一种扩展方式，可以灵活的扩展和修改全局配置文件和用户配置文件。ClickHouse 提供了 `config.d` 和 `users.d` 目录，你可以通过添加额外的 `.xml` 文件来引入新的配置设置或修改现有设置，使得配置管理更加模块化和容易维护。这种方式尤其适用于在 Docker 容器中部署，因为你可以通过 Docker 数据卷挂载机制轻松地将自定义的配置文件添加到 `config.d` 和 `users.d` 目录而无需修改容器镜像。当你以这种方式配置时，ClickHouse 会加载目录中的所有 `.xml` 文件并将这些文件中的配置合并到主配置中，这样可以实现添加新的配置项或覆盖现有配置。

在这里，我们在工作目录 `/opt/workspace/docker` 下创建一个名为 `conf` 目录，并分别创建 `config.d` 和 `users.d` 目录来放置自定义配置文件。假设我们想要扩展 `config.xml` 来覆盖已有的配置项，可以在 `config.d` 目录下创建一个名为 `base_config.xml` 的文件：
```xml
<clickhouse>
    <!-- 日志配置 -->
    <logger>
        <level>trace</level>
        <log>/var/log/clickhouse-server/clickhouse-server.log</log>
        <errorlog>/var/log/clickhouse-server/clickhouse-server.err.log</errorlog>
        <size>1000M</size>
        <count>10</count>
    </logger>

    <!-- 端口号 -->
    <http_port>8123</http_port>
    <tcp_port>9000</tcp_port>
    <mysql_port>9004</mysql_port>
    <postgresql_port>9005</postgresql_port>
    <interserver_http_port>9009</interserver_http_port>

    <!-- ZooKeeper 配置 -->
    <zookeeper>
        <node>
            <host>zk1</host>
            <port>2181</port>
        </node>
        <node>
            <host>zk2</host>
            <port>2181</port>
        </node>
        <node>
            <host>zk3</host>
            <port>2181</port>
        </node>
        <!-- ZooKeeper 会话的超时时间 -->
        <session_timeout_ms>12000</session_timeout_ms>
    </zookeeper>

    <!-- 分布式表的默认配置 -->
    <distributed_ddl>
        <path>/clickhouse/task_queue/ddl</path>
    </distributed_ddl>

    <!-- 存储路径 -->
    <path>/var/lib/clickhouse/</path>
    <tmp_path>/var/lib/clickhouse/tmp/</tmp_path>

    <format_schema_path>/var/lib/clickhouse/format_schemas/</format_schema_path>
    <user_files_path>/var/lib/clickhouse/user_files/</user_files_path>
</clickhouse>
```
> 这里列出来 config.xml 的一些核心配置，可以根据业务自行决定自定义配置

假如你想要添加一个新用户，你可以在 `users.d` 目录下创建一个名为 `new_user.xml` 的文件：
```xml
<clickhouse>
    <!-- 添加新用户 -->
    <users>
        <test>
            <password>test</password>
            <networks>
                <ip>::/0</ip>
            </networks>
            <profile>default</profile>
            <quota>default</quota>
        </test>
    </users>
</clickhouse>
```
> 在这我们创建了一个 test 用户

### 3.3 构建 Compose 文件

Docker Compose 简化了对整个应用程序堆栈的控制，使得在一个易于理解的 YAML 配置文件中轻松管理服务、网络和数据卷。要使用 Docker Compose 部署，首先需创建一个 docker-compose.yml 文件，如下所示：
```yml
services:
  ck1:
      image: clickhouse/clickhouse-server:23.3.13.6
      container_name: docker_ck1
      restart: always
      networks:
        - pub-network
      volumes:
        - ck1_data:/var/lib/clickhouse
        - ck1_log:/var/log/clickhouse-server/
        - ./conf/config.d:/etc/clickhouse-server/config.d
        - ./conf/users.d:/etc/clickhouse-server/users.d

  ck2:  
      image: clickhouse/clickhouse-server:23.3.13.6
      container_name: docker_ck2
      restart: always
      networks:
        - pub-network
      volumes:
        - ck2_data:/var/lib/clickhouse
        - ck2_log:/var/log/clickhouse-server/
        - ./conf/config.d:/etc/clickhouse-server/config.d
        - ./conf/users.d:/etc/clickhouse-server/users.d

volumes:
  ck1_data:
  ck1_log:
  ck2_data:
  ck2_log:

networks:  # 网络
  pub-network:
      external: true
```
这个文件定义了一个 ClickHouse 集群，其中包含两个服务：`ck1` 和 `ck2`。每个服务都使用 ClickHouse 的官方 Docker 镜像，同时映射了容器的 8123 端口（HTTP接口）和 9000 端口（原生客户端接口）到宿主机相同的端口上，这样我们就可以从宿主机访问 ClickHouse 服务了。下面详细介绍具体配置。

#### 3.3.1 顶级配置

`services` 配置用于定义不同的应用服务。上边的例子定义了两个服务：`ck1` 和 `ck2`，分别作为集群的两个节点。Docker Compose 会将每个服务部署在各自的容器中。在这里我们使用自定义容器名称，分别为 `docker_ck1` 以及 `docker_ck2`。

`networks` 配置用于声明服务要连接的网络 `pub-network`。`external: true` 表示网络是在 Docker Compose 配置文件之外定义的，即它已经存在了，Docker Compose 不需要尝试创建它。只要加入这个网络的服务就能够实现项目容器间以及跨项目通信。具体可以查阅 [Docker 实战：使用 Docker Compose 部署实现跨项目网络访问](https://smartsi.blog.csdn.net/article/details/138734487)。

`volumes` 配置用于声明 Docker Compose 创建新的数据卷 `ck1_data`、`ck2_data`。我们只负责声明，不需要手动创建，Docker Compose 会自动管理。默认情况下，在容器删除之后数据会丢失。为了解决这个问题，我们需要三个服务分别使用声明中的数据卷来将数据保存在宿主机上。

3.2.2 service元素配置
`services` 配置定义了三个服务，我们以 minio1 服务为例，详细介绍服务的配置。

`image` 配置指定了要使用的 Docker 镜像及其版本。三个服务均使用 minio/minio:RELEASE.2024-05-10T01-41-38Z 镜像确保所有节点运行同一版本的 MinIO，保持集群的一致性。这里的版本 RELEASE.2024-05-10T01-41-38Z 可以根据需求替换为最新或特定版本，其中日期时间戳代表了该版本的构建时间。当然你也可以选择 minio/minio:latest 的镜像，这会确保每次拉取都是最新的稳定版，但在生产环境中可能带来不确定性，因为“最新版”会随新版本发布而变化。选择特定版本的标签可以提供更多的控制和预测性，减少意外的更新可能造成的问题。



```shell
(base) localhost:clickhouse wy$ docker compose up -d
[+] Running 6/6
 ✔ Volume "clickhouse_ck2_data"  Created                                        0.0s
 ✔ Volume "clickhouse_ck2_log"   Created                                        0.0s
 ✔ Volume "clickhouse_ck1_data"  Created                                        0.0s
 ✔ Volume "clickhouse_ck1_log"   Created                                        0.0s
 ✔ Container docker_ck2          Started                                        0.2s
 ✔ Container docker_ck1          Started                                        0.2s
```


上述方式中只有 `zoo1` 配置了端口映射，这一般是为了在宿主机上提供一个方便的访问点，供管理员使用 CLI 工具或者其他服务连接到 ZooKeeper 集群进行维护或检查。通常，在 Docker Compose 中，同一网络内的服务（containers）可以使用服务名直接互相访问，无需端口映射到宿主机。

ClickHouse 集群内的节点会使用内部服务名称（如 `zoo1`、`zoo2`、`zoo3`）来访问整个 ZooKeeper 集群，因为所有的服务都在 `clickhouse_net` 这一自定义网络下。这意味着，尽管只有 `zoo1` 对外映射了端口，节点 `clickhouse01` 和 `clickhouse02` 仍能够通过 Docker 的内部网络连接到 `zoo1`、`zoo2` 和 `zoo3`。

如果您希望能够从外部网络访问所有 ZooKeeper 节点（例如，对于跨主机的 Docker 集群或特定的监控需求），则应对每一个 ZooKeeper 服务配置端口映射，并且使用不同的宿主机端口来避免冲突。例如：



在大多数情况下，在生产环境中为了安全考虑，不建议将 ZooKeeper 的端口映射到宿主机上，除非是临时的需要。而在 Docker 内部网络间进行的服务通讯已经足够满足 ClickHouse 集群和 ZooKeeper 集群间的交互。



hostname：



在 Docker Compose 方案中配置 `hostname` 的目的主要是为了在容器内部设置容器的主机名。具体到 ClickHouse 集群和 ZooKeeper 实例，设置 `hostname` 会有以下用途：

1. **服务发现**: 在 Docker 网络中，服务可以通过主机名相互发现和通信。尽管 Docker Compose 默认使用服务名称（service name）作为可解析的网络标识来实现服务之间的互联互通，`hostname` 设置可以确保在容器内部网络解析和服务发现方面与外部定义一致，特别是当服务需要通过它们的主机名而不是服务名称来参考对方时。

2. **配置一致性**: 在设置分布式系统配置时，如 ClickHouse 集群配置，通常需要指定各个节点名称。通过 `hostname` 明确设置主机名，使配置文件中的节点名与容器内的主机名保持一致，进而保证各个 ClickHouse 节点之间可以通过设置的名字互相识别和通信。

3. **日志和监控**: 设置 `hostname` 对日志记录和监控工具也非常有用。容器内的应用程序（包括 ClickHouse 服务器）通常会在日志消息中包含主机名。定制 `hostname` 使你能够更容易地辨识日志来源于哪个节点或容器。

4. **复制和分布式设置**: 对于 ClickHouse 的 `Replicated*` 表引擎和其它分布式特性来说，指定恰当的 `hostname` 有助于正确构建复制和分布式数据结构，因为这些设置可能依赖于节点的主机名来定义副本和分片规则。

5. **兼容性和迁移**: 如果您之前有过 ClickHouse 或其他服务的物理部署，并且要迁移到容器化部署，已有的配置文件可能包含物理主机名。通过在 Docker 中设置相同的 `hostname`，您可以无缝迁移现有配置文件到容器环境。

在实践中，设置 `hostname` 提供了额外的明确性和灵活性，使得各种服务和工具可以如预期般运行。在复杂的生产环境和集群设置下，这有助于减少混淆并简化管理过程。





在上述 Docker Compose 方案中的 `environment` 部分包含了设定环境变量的条目，这是用于容器启动时设置特定参数的方法。`CLICKHOUSE_DB`, `CLICKHOUSE_USER` 和 `CLICKHOUSE_PASSWORD` 是按照 ClickHouse 官方 Docker 镜像设定的环境变量，用于在容器启动时创建初始用户、密码和数据库。

### `CLICKHOUSE_DB`

- **用途**: `CLICKHOUSE_DB` 环境变量用于指定在启动 ClickHouse 服务器时应该创建的数据库名���。如果设置了此环境变量，ClickHouse 服务器将在启动后自动创建数据库。

### `CLICKHOUSE_USER`

- **用途**: `CLICKHOUSE_USER` 环境变量用于指定在启动 ClickHouse 服务器时应该创建的用户名。

### `CLICKHOUSE_PASSWORD`

- **用途**: `CLICKHOUSE_PASSWORD` 环境变量与 `CLICKHOUSE_USER` 一起使用，用于指定相应用户的密码。

### 是否必须设置

这些环境变量不是强制性的。对于某些 ClickHouse 的 Docker 镜像，在没有设置这些变量的情况下，它会默认创建一个名为 `default` 的用户，没有密码，同时还会创建一个默认的数据库。如果您接受这些默认值，可以省略这些环境变量。

然而，出于安全和管理的考虑，在生产环境中建议采取以下措施：

1. **创建非默认用户**: 使用 `CLICKHOUSE_USER` 创建特定用户，并为其分配权限，以防止使用默认用户和默认权限。

2. **设置密码**: 使用 `CLICKHOUSE_PASSWORD` 为用户创建密码，加强数据库实例的安全性。

3. **定制数据库**: 通过 `CLICKHOUSE_DB` 创建业务相关的数据库，便于管理和区分不同的数据集。

创建初始用户和数据库的环境变量可以帮助自动化容器启动过程中的初始设置，并通过避免使用默认配置来增强系统的安全性。在实际应用中，您还应该根据实际需要评估和实现更精细的安全策略。





在上述 Docker Compose 方案中的 `environment` 部分所提到的 `CLICKHOUSE_DB` 和 `CLICKHOUSE_USER` 环境变量是指 ClickHouse 自身的数据库和用户，而不是外部的如 MySQL 数据库。这些环境变量用于在 ClickHouse 实例启动时，在 ClickHouse 中创建一个用户账户和数据库。





确实，在早期的 ClickHouse 版本中，配置文件使用的是 <yandex> 根元素，但在较新的版本中，根元素已被更改为 <clickhouse>。如果您使用的是 ClickHouse 的最新 Docker 镜像，您应该使用 <clickhouse> 作为根元素。不过，旧版 ClickHouse 配置文件中的 <yandex> 根元素仍然是兼容的，新版本保持了向后兼容性以支持旧配置文件。
