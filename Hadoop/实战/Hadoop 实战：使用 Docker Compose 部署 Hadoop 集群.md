

首先，您需要创建一个`docker-compose.yml`文件，该文件定义了将要在集群中运行的服务。根据Hadoop的基本组成部分，至少需要定义以下服务：

- **NameNode**: HDFS的核心，管理文件系统的命名空间。
- **DataNode**: 存储实际数据的节点。
- **ResourceManager**: YARN的核心，管理计算资源。
- **NodeManager**: 管理每个节点上的计算资源。
- **SecondaryNameNode**: 用于监视NameNode的状态并执行检查点操作。



```yml
services:
   namenode:
      image: apache/hadoop:3.3.6
      container_name: docker_namenode
      volumes:
        - namenode_data:/hadoop/dfs/name
      command: ["hdfs", "namenode"]
      networks:
        - pub-network
      ports:
        - 9870:9870
      env_file:
        - ./config
      environment:
          ENSURE_NAMENODE_DIR: "/tmp/hadoop-root/dfs/name"
      platform: linux/amd64
   datanode:
      image: apache/hadoop:3.3.6
      container_name: docker_datanode
      volumes:
        - datanode_data:/hadoop/dfs/data
      command: ["hdfs", "datanode"]
      networks:
        - pub-network
      env_file:
        - ./config
      platform: linux/amd64       
   resourcemanager:
      image: apache/hadoop:3.3.6
      container_name: docker_resourcemanager
      depends_on:
         - namenode
      command: ["yarn", "resourcemanager"]
      networks:
        - pub-network
      ports:
         - 8088:8088
      env_file:
        - ./config
      platform: linux/amd64
   nodemanager:
      image: apache/hadoop:3.3.6
      container_name: docker_nodemanager
      depends_on:
         - resourcemanager
      command: ["yarn", "nodemanager"]
      networks:
        - pub-network
      env_file:
        - ./config
      platform: linux/amd64

volumes:
  namenode_data:
  datanode_data:


networks:  # 网络
  pub-network:
      external: true
```



### 2.1 NameNode服务



- `image: apache/hadoop:3.3.6`：从Docker Hub拉取Apache Hadoop的官方镜像，标签为3.3.6。
- `container_name: namenode`：为容器指定一个容易识别的名字，这里是`namenode`。
- `volumes: - namenode_data:/hadoop/dfs/name`：卷挂载，将宿主机上的`namenode_data`卷挂载到容器内的`/hadoop/dfs/name`路径。这用于持久化NameNode的数据。
- `ports: - "9870:9870"`：端口映射，将容器的9870端口映射到宿主机的9870端口。9870是Hadoop 3.x NameNode的Web UI端口。
- `environment: - CLUSTER_NAME=test`：设置环境变量`CLUSTER_NAME`为`test`，该环境变量在后面的命令中被使用。
- `command: ["/bin/bash", "-c", "bin/hdfs namenode -format ${CLUSTER_NAME} && bin/hdfs namenode"]`：容器启动时执行的命令，先格式化NameNode，然后启动NameNode服务。





对于 `command`配置方式，有两种比较常见的配置方式:

- `command: ["/bin/bash", "-c", "bin/hdfs namenode -format ${CLUSTER_NAME} && bin/hdfs namenode"]`

- `command: ["hdfs", "namenode"]`



第一种方案使用了一个批处理命令（通过`/bin/bash -c`运行），并且执行了两个步骤

- Step 1: `bin/hdfs namenode -format ${CLUSTER_NAME}`。这个命令在启动NameNode 服务之前，首先对其进行格式化。格式化是创建新的 HDFS 文件系统所必需的步骤，通常只在第一次或需要重置文件系统时执行。格式化过程会删除HDFS中所有文件的元数据。

- Step 2: `bin/hdfs namenode`。接着启动 NameNode 服务。

>  使用`&&`确保只有在格式化成功完成后才启动NameNode服务。

这种配置方式提供了一种自动化的启动逻辑，格式化（如果必要）并启动 NameNode 服务。对于快速部署、测试或教学实验来说非常方便，尤其是在使用非持久化存储、希望每次启动都是“干净”的环境时。然而，必须小心使用，因为如果已经有重要数据在HDFS上，这种命令则可能导致数据丢失。



第二种方案中的更为直接，唯一执行的操作是启动 NameNode 服务。这里没有进行格式化的步骤。这意味着在使用这个配置之前，用户需要确保 NameNode 已经被正确地格式化。这种方案更适用于生产环境，或者当你预期HDFS的状态需要持久化时。格式化操作需要在不同的步骤手动执行，给予用户更多的控制以避免意外覆盖数据。



没有为各个Hadoop组件（如NameNode、DataNode等）指定具体的`command`指令。这是因为Apache Hadoop的官方Docker镜像通常已经预配置了默认的启动命令，它们在容器启动时自动执行相关组件的启动脚本。对于Apache Hadoop官方镜像，如果没有显式指定`command`或`entrypoint`，它会使用Docker镜像内部定义的默认启动命令。这些默认命令基于镜像的构建文件（如Dockerfile），它们能够确保Hadoop的核心组件（比如NameNode和DataNode）以及YARN的组件（比如ResourceManager和NodeManager）按预期运行。



您可以引用这个文件，而不是直接在服务定义内部列出这些环境变量。这种方式可以使配置更加整洁，并且方便在多个服务之间共享相同的环境变量设置。首先，创建一个文本文件来保存`HADOOP_HOME`和`CLUSTER_NAME`的定义。通常，这类文件命名为`config`，但您可以根据需要命名。例如，创建一个名为`config`的文件。在`config`文件中，添加以下内容：

```shell
HADOOP_HOME=/opt/hadoop
CLUSTER_NAME=hadoop_cluster
```



> 确保`HADOOP_HOME`的值反映了您Docker镜像中Hadoop的实际安装路径。



### 2.2 DataNode服务

- `depends_on: - namenode`：表明`datanode1`服务在`namenode`服务启动后才会启动。
- `volumes: - datanode1_data:/hadoop/dfs/data`：卷挂载，用于持久化DataNode的数据。
- `command: ["/bin/bash", "-c", "bin/hdfs datanode"]`：容器启动时执行的命令，启动DataNode服务。









```xml
HADOOP_HOME=/opt/hadoop
CLUSTER_NAME=docker_hadoop_cluster
CORE-SITE.XML_fs.default.name=hdfs://namenode
CORE-SITE.XML_fs.defaultFS=hdfs://namenode
HDFS-SITE.XML_dfs.namenode.rpc-address=namenode:8020
HDFS-SITE.XML_dfs.replication=1
MAPRED-SITE.XML_mapreduce.framework.name=yarn
MAPRED-SITE.XML_yarn.app.mapreduce.am.env=HADOOP_MAPRED_HOME=$HADOOP_HOME
MAPRED-SITE.XML_mapreduce.map.env=HADOOP_MAPRED_HOME=$HADOOP_HOME
MAPRED-SITE.XML_mapreduce.reduce.env=HADOOP_MAPRED_HOME=$HADOOP_HOME
YARN-SITE.XML_yarn.resourcemanager.hostname=resourcemanager
YARN-SITE.XML_yarn.nodemanager.pmem-check-enabled=false
YARN-SITE.XML_yarn.nodemanager.delete.debug-delay-sec=600
YARN-SITE.XML_yarn.nodemanager.vmem-check-enabled=false
YARN-SITE.XML_yarn.nodemanager.aux-services=mapreduce_shuffle
CAPACITY-SCHEDULER.XML_yarn.scheduler.capacity.maximum-applications=10000
CAPACITY-SCHEDULER.XML_yarn.scheduler.capacity.maximum-am-resource-percent=0.1
CAPACITY-SCHEDULER.XML_yarn.scheduler.capacity.resource-calculator=org.apache.hadoop.yarn.util.resource.DefaultResourceCalculator
CAPACITY-SCHEDULER.XML_yarn.scheduler.capacity.root.queues=default
CAPACITY-SCHEDULER.XML_yarn.scheduler.capacity.root.default.capacity=100
CAPACITY-SCHEDULER.XML_yarn.scheduler.capacity.root.default.user-limit-factor=1
CAPACITY-SCHEDULER.XML_yarn.scheduler.capacity.root.default.maximum-capacity=100
CAPACITY-SCHEDULER.XML_yarn.scheduler.capacity.root.default.state=RUNNING
CAPACITY-SCHEDULER.XML_yarn.scheduler.capacity.root.default.acl_submit_applications=*
CAPACITY-SCHEDULER.XML_yarn.scheduler.capacity.root.default.acl_administer_queue=*
CAPACITY-SCHEDULER.XML_yarn.scheduler.capacity.node-locality-delay=40
CAPACITY-SCHEDULER.XML_yarn.scheduler.capacity.queue-mappings=
CAPACITY-SCHEDULER.XML_yarn.scheduler.capacity.queue-mappings-override.enable=false
```



## 3. 启动集群

按照以下步骤部署和初始化集群:

1. **启动集群服务**: 使用`docker-compose up -d`命令启动所有定义的服务。

2. **格式化NameNode**: 在首次启动集群前需要格式化HDFS。通过执行命令 `docker exec docker_namenode hdfs namenode -format` 完成格式化。



## 4. 访问集群

### 4.1 登录节点

可以通过指定容器登录到任何节点，如:

```shell
docker exec -it docker_namenode /bin/bash
```

运行示例作业(Pi Job):

```shell
yarn jar share/hadoop/mapreduce/hadoop-mapreduce-examples-3.3.6.jar pi 10 15
```

上面的命令将运行一个 Pi Job，类似地，任何hadoop相关的命令都可以运行。



### 4.2 访问UI

Namenode 的访问地址为  `http://localhost:9870/` 来查看NameNode的Web界面，此界面提供了有关HDFS状态和集群健康信息的详细视图， ResourceManager 的访问地址为`http://localhost:8088/`。
