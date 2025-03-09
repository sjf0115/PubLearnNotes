本入门部分将指导您使用Docker容器完成Flink集群的本地设置（在一台机器上，但在不同的容器中）。



## 1. 介绍

Docker是一个流行的容器运行时。在Docker Hub上有Apache Flink的官方Docker镜像。您可以使用Docker镜像在Docker上部署Session或Application集群。本页面主要介绍在Docker和Docker Compose上安装Flink。

部署到托管容器化环境（如[独立Kubernetes](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/deployment/resource-providers/standalone/kubernetes/)或[本机Kubernetes](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/deployment/resource-providers/native_kubernetes/)）将在单独的页面上进行描述。

## 2. 在 Docker 上启动 Session 集群

Flink 会话集群可用于运行多个作业。每个作业都需要在集群部署完成后提交给集群。要使用 Docker 部署 Flink Session 集群，你需要启动一个 JobManager 容器。为了使容器之间能够通信，我们首先设置一个必需的 Flink 配置属性并创建一个网络：
```
$ FLINK_PROPERTIES="jobmanager.rpc.address: jobmanager"
$ docker network create flink-network
```
然后我们启动JobManager：
```
$ docker run \
    --rm \
    --name=jobmanager \
    --network flink-network \
    --publish 8081:8081 \
    --env FLINK_PROPERTIES="${FLINK_PROPERTIES}" \
    flink:1.20.1-scala_2.12 jobmanager
```
在启动一个或多个TaskManager容器：
```
$ docker run \
    --rm \
    --name=taskmanager \
    --network flink-network \
    --env FLINK_PROPERTIES="${FLINK_PROPERTIES}" \
    flink:1.20.1-scala_2.12 taskmanager
```
Web 界面现在在 `localhost:8081` 上可用。现在可以像这样提交作业（假设您有Flink可用的本地分发版）：
```
$ ./bin/flink run ./examples/streaming/ topspeedwindow .jar
```
要关闭集群，可以终止（例如按CTRL-C） JobManager和TaskManager进程，或者使用docker ps来识别和docker stop来终止容器。


## 2. 部署模式

Flink 镜像包含一个具有默认配置和标准入口点脚本的常规 Flink 发行包。您可以通过以下方式运行其入口点：
- JobManager for a Session cluster
- JobManager for an Application cluster
- TaskManager for any cluster

这允许您在任何容器化环境中部署独立集群（会话或应用程序模式），例如：
- 手动在本地安装Docker
- 在Kubernetes集群中，
- 使用Docker Compose，

注意本机Kubernetes也默认运行相同的镜像，并按需部署任务管理器，因此您不必手动执行。

接下来的章节描述了如何为各种目的启动单个 Flink Docker 容器。

一旦你在Docker上启动了Flink，你就可以在localhost:8081上访问Flink Web UI，或者像这样提交作业：/bin/ Flink run ./examples/streaming/ topspeedwindow .jar。

我们建议使用Docker Compose在会话模式下部署Flink，以简化系统配置。

### 2.1 Application 模式

要了解应 Application 模式背后的高层次知识，请参考部署模式概述。

Flink Application 集群是运行单个作业的专用集群。在本例中，将使用作业作为一步部署集群，因此不需要提交额外的作业。

作业 artifacts 包含在容器内 Flink 的 JVM 进程的类路径中，由以下部分组成：
- 您的作业jar，通常将其提交到会话集群和
- 所有其他必要的依赖项或资源，不包括在Flink中。

要使用Docker为单个作业部署集群，您需要
- 让作业 artifacts 在/opt/flink/usrlib下的所有容器中本地可用，或者通过——jars参数传递一个jar列表
- 在Application集群模式下启动JobManager容器
- 启动所需数量的TaskManager容器。

要使作业 artifacts 在容器中本地可用，您可以

在启动 JobManager 和 taskmanager 时，将带有 artifacts 的卷（或多个卷）挂载到 /opt/flink/usrlib：
```
$ FLINK_PROPERTIES="jobmanager.rpc.address: jobmanager"
$ docker network create flink-network

$ docker run \
    --mount type=bind,src=/host/path/to/job/artifacts1,target=/opt/flink/usrlib/artifacts1 \
    --mount type=bind,src=/host/path/to/job/artifacts2,target=/opt/flink/usrlib/artifacts2 \
    --rm \
    --env FLINK_PROPERTIES="${FLINK_PROPERTIES}" \
    --name=jobmanager \
    --network flink-network \
    flink:1.20.1-scala_2.12 standalone-job \
    --job-classname com.job.ClassName \
    [--job-id <job id>] \
    [--fromSavepoint /path/to/savepoint [--allowNonRestoredState]] \
    [job arguments]

$ docker run \
    --mount type=bind,src=/host/path/to/job/artifacts1,target=/opt/flink/usrlib/artifacts1 \
    --mount type=bind,src=/host/path/to/job/artifacts2,target=/opt/flink/usrlib/artifacts2 \
    --env FLINK_PROPERTIES="${FLINK_PROPERTIES}" \
    flink:1.20.1-scala_2.12 taskmanager
```
或者通过编写一个自定义 Dockerfile 来扩展 Flink 镜像，构建它并使用它来启动 JobManager 和 taskmanager：
```
FROM flink
ADD /host/path/to/job/artifacts/1 /opt/flink/usrlib/artifacts/1
ADD /host/path/to/job/artifacts/2 /opt/flink/usrlib/artifacts/2
```

```
docker build --tag flink_with_job_artifacts .
$ docker run \
    flink_with_job_artifacts standalone-job \
    --job-classname com.job.ClassName \
    [--job-id <job id>] \
    [--fromSavepoint /path/to/savepoint [--allowNonRestoredState]] \
    [job arguments]

$ docker run flink_with_job_artifacts taskmanager
```

或者在启动JobManager时通过jar参数传递jar path：
```
$ FLINK_PROPERTIES="jobmanager.rpc.address: jobmanager"
$ docker network create flink-network

$ docker run \
    --env FLINK_PROPERTIES="${FLINK_PROPERTIES}" \
    --env ENABLE_BUILT_IN_PLUGINS=flink-s3-fs-hadoop-1.20.1.jar \
    --name=jobmanager \
    --network flink-network \
    flink:1.20.1-scala_2.12 standalone-job \
    --job-classname com.job.ClassName \
    --jars s3://my-bucket/my-flink-job.jar,s3://my-bucket/my-flink-udf.jar \
    [--job-id <job id>] \
    [--fromSavepoint /path/to/savepoint [--allowNonRestoredState]] \
    [job arguments]
```
standalone-job参数在应用模式下启动JobManager容器。

#### JobManager附加命令行参数

你可以为集群入口点提供以下额外的命令行参数：

- `--job-classname <job class name>`：要运行的作业的类名。
  - 默认情况下，Flink 会扫描它的类路径，寻找带有 Main-Class 或 program-class 清单条目的JAR，并选择它作为作业类。使用此命令行参数手动设置作业类。
  - 如果在类路径上没有或有多个具有此类清单条目的JAR可用，则需要此参数。
- `--job-id <job id> `：手动为作业设置 Flink 作业id（默认：00000000000000000000000000000000）
- `--fromSavepoint /path/to/savepoint`：从保存点恢复
  - 为了从保存点恢复，还需要传递保存点路径。注意/path/to/savepoint需要在集群的所有Docker容器中都可以访问（例如，将其存储在DFS上或从挂载的卷中或将其添加到镜像中）。
- `--allowNonRestoredState`：跳过损坏的保存点状态
  - 此外，您可以指定此参数以允许跳过无法恢复的保存点状态。
- `--jars`：作业jar和任何额外工件的路径，以逗号分隔
  - 您可以指定此参数来指向存储在flink文件系统或通过HTTP(S)下载的作业工件。Flink将在作业部署期间获取这些文件。（例如——jars s3://my-bucket/my- flint -job.jar，——jars s3://my-bucket/my- flint -job.jar,s3://my-bucket/my- flint -udf.jar）。

如果用户作业main类的main函数接受参数，您也可以在docker run命令的末尾传递它们。

### 2.2 Session 模式

在上面的入门部分中已经介绍了会话模式下的本地部署。

## 3. Flink Docker Images

### 3.1 Image Hosting

Flink Docker 镜像有两个发行渠道：
- Docker Hub 上的官方 flink 镜像(由 Docker 审查和构建)
- 在 Docker Hub apache/flink 下的 flink 镜像(由Flink开发人员管理)

我们建议使用 Docker Hub 上的官方镜像，因为它们是由 Docker 审查的。`apache/flink` 上的镜像以防在 Docker 审查过程中出现延迟。

启动名为 `flink:latest` 的镜像将从 Docker Hub 中提取最新的镜像。如果想使用 `apache/flink` 中托管的镜像，请将 flink 替换为 apache/flink。任何镜像标记（从Flink 1.11.3开始）也可以在 apache/flink 上使用。

### 3.2 Image Tags

Flink Docker 存储库托管在 Docker Hub 上，提供 Flink 1.2.1 及更高版本的镜像。这些镜像的源代码可以在 [Apache flink-docker](https://github.com/apache/flink-docker) 存储库中找到。

每个支持的 Flink 和 Scala 版本组合的镜像都是可用的，并且为方便起见提供了 Tag 别名。

例如，您可以使用以下别名：
```
flink:latest → flink:<latest-flink>-scala_<latest-scala>
flink:1.11 → flink:1.11.<latest-flink-1.11>-scala_2.12
```

注意：建议始终使用 docker 镜像的显式版本标签来指定所需的 Flink 和 Scala 版本（例如Flink:1.11-scala_2.12）。这将避免在应用程序中使用的 Flink 和/或Scala版本与 docker 镜像提供的版本不同时可能发生的一些类冲突。

注意：在Flink 1.5版本之前，Hadoop依赖项总是与Flink捆绑在一起。你可以看到某些标签包含Hadoop的版本，例如（例如-hadoop28）。从Flink 1.5开始，省略Hadoop版本的图像标签对应于不包含捆绑Hadoop发行版的Flink的无Hadoop版本。

## 4. Flink with Docker Compose

Docker Compose 是一种在本地运行一组 Docker 容器的方法。下一节将展示运行 Flink 的配置文件示例。

### 4.1 General

创建 docker-compose.yaml 文件。请查看以下章节中的示例：
- Application Mode
- Session Mode
- Session Mode with SQL Client

在前台启动集群（使用 `-d` 作为后台）
```
$ docker-compose up
```
将集群扩展或缩小到 N 个 taskmanager：
```
$ docker-compose scale taskmanager=<N>
```
访问 JobManager 容器
```
$ docker exec -it $(docker ps——filter name=jobmanager——format={{.ID}}) /bin/sh
```
终止集群
```
$ docker-compose down
```
访问Web界面
- 当集群运行时，可以访问web UI: http://localhost:8081。

### 4.2 Application Mode

在应用程序模式下，启动Flink集群，该集群专用于仅运行与映像捆绑在一起的Flink作业。因此，您需要为每个应用程序构建一个专用的Flink Image。详情请点击这里。另请参阅如何在命令中为JobManager服务指定JobManager参数。

`docker-compose.yml` 用于应用模式：
```yaml
version: "2.2"
services:
  jobmanager:
    image: flink:1.20.1-scala_2.12
    ports:
      - "8081:8081"
    command: standalone-job --job-classname com.job.ClassName [--job-id <job id>] [--jars /path/to/artifact1,/path/to/artifact2] [--fromSavepoint /path/to/savepoint] [--allowNonRestoredState] [job arguments]
    volumes:
      - /host/path/to/job/artifacts:/opt/flink/usrlib
    environment:
      - |
        FLINK_PROPERTIES=
        jobmanager.rpc.address: jobmanager
        parallelism.default: 2        

  taskmanager:
    image: flink:1.20.1-scala_2.12
    depends_on:
      - jobmanager
    command: taskmanager
    scale: 1
    volumes:
      - /host/path/to/job/artifacts:/opt/flink/usrlib
    environment:
      - |
        FLINK_PROPERTIES=
        jobmanager.rpc.address: jobmanager
        taskmanager.numberOfTaskSlots: 2
        parallelism.default: 2     
```
### 4.3 Session Mode

在会话模式下，您可以使用 docker-compose 启动一个长时间运行的 Flink 集群，然后向该集群提交作业。

docker-compose.yml for Session Mode：
```yaml
version: "2.2"
services:
  jobmanager:
    image: flink:1.20.1-scala_2.12
    ports:
      - "8081:8081"
    command: jobmanager
    environment:
      - |
        FLINK_PROPERTIES=
        jobmanager.rpc.address: jobmanager        

  taskmanager:
    image: flink:1.20.1-scala_2.12
    depends_on:
      - jobmanager
    command: taskmanager
    scale: 1
    environment:
      - |
        FLINK_PROPERTIES=
        jobmanager.rpc.address: jobmanager
        taskmanager.numberOfTaskSlots: 2    
```
### 4.4 Flink SQL Client with Session Cluster

在本例中，启动了一个长时间运行的会话集群和一个Flink SQL CLI，后者使用该集群向其提交作业。



docker-compose。Flink SQL Client with Session Cluster

```yaml

```



。。。
