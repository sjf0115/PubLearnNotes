## 1. Jar

Paimon 目前支持 Flink 2.0、1.20、1.19、1.18、1.17、1.16、1.15 版本。我们建议使用最新版本的 Flink 以获得更好的体验。请下载与相应版本匹配的 jar 文件。

目前，Paimon 提供两种类型的 jar 文件：其中一种是 Bundled Jar 用于读写数据，另一种是 Action Jar 用于手动压缩等操作。

| Flink 版本 | 类型 | Jar |
| :------------- | :------------- | :------------- |
| Flink 2.0	  | Bundled Jar	| [paimon-flink-2.0-1.2.0.jar](https://repo.maven.apache.org/maven2/org/apache/paimon/paimon-flink-2.0/1.2.0/paimon-flink-2.0-1.2.0.jar) |
| Flink 1.20	| Bundled Jar	| [paimon-flink-1.20-1.2.0.jar](https://repo.maven.apache.org/maven2/org/apache/paimon/paimon-flink-1.20/1.2.0/paimon-flink-1.20-1.2.0.jar) |
| Flink 1.19	| Bundled Jar	| [paimon-flink-1.19-1.2.0.jar](https://repo.maven.apache.org/maven2/org/apache/paimon/paimon-flink-1.19/1.2.0/paimon-flink-1.19-1.2.0.jar) |
| Flink 1.18	| Bundled Jar	| [paimon-flink-1.18-1.2.0.jar](https://repo.maven.apache.org/maven2/org/apache/paimon/paimon-flink-1.18/1.2.0/paimon-flink-1.18-1.2.0.jar) |
| Flink 1.17	| Bundled Jar	| [paimon-flink-1.17-1.2.0.jar](https://repo.maven.apache.org/maven2/org/apache/paimon/paimon-flink-1.17/1.2.0/paimon-flink-1.17-1.2.0.jar) |
| Flink 1.16	| Bundled Jar	| [paimon-flink-1.16-1.2.0.jar](https://repo.maven.apache.org/maven2/org/apache/paimon/paimon-flink-1.16/1.2.0/paimon-flink-1.16-1.2.0.jar) |
| Flink 1.15	| Bundled Jar	| [paimon-flink-1.15-1.2.0.jar](https://repo.maven.apache.org/maven2/org/apache/paimon/paimon-flink-1.15/1.2.0/paimon-flink-1.15-1.2.0.jar) |
| Flink Action |  Action Jar | [paimon-flink-action-1.2.0.jar](https://repo.maven.apache.org/maven2/org/apache/paimon/paimon-flink-action/1.2.0/paimon-flink-action-1.2.0.jar) |


你也可以从源代码手动构建 Bundled Jar 包。要从源代码构建，先克隆 [Git 仓库](https://github.com/apache/paimon.git)。可以使如下下命令构建 Bundled Jar 包:
```
mvn clean install -DskipTests
```
可以在 `./paimon-flink/paimon-flink-<flink-version>/target/paimon-flink-<flink-version>-1.2.0.jar` 路径下找到 Bundled Jar，在 `./paimon-flink/paimon-flink-action/target/paimon-flink-action-1.2.0.jar` 路径下找到 Action Jar。

## 2. 入门

### 2.1 下载 Flink

如果你还没有下载 Flink，你可以[下载 Flink](https://flink.apache.org/downloads.html)，然后用以下命令解压:
```
tar -xzf flink-*.tgz
```

### 2.2 复制 Paimon Bundled Jar

将 Paimon Bundled Jar 包复制到你的 Flink 安装目录下的 lib 目录中:
```
cp paimon-flink-2.0-1.2.0.jar /opt/workspace/flink-1.20.2/lib/
```
> 在这 Flink 版本为 1.20.0，Paimon 版本为 1.2.0

### 2.3 复制 Hadoop Bundled Jar

> 如果机器处于 Hadoop 环境中，请确保环境变量 `HADOOP_CLASSPATH` 的值包含通用的 Hadoop 库路径，您不需要使用以下预捆绑的 Hadoop jar。

[下载](https://flink.apache.org/downloads.html)预捆绑的 Hadoop jar 并将 jar 文件复制到 Flink 安装目录的 lib 目录中：
```
cp flink-shaded-hadoop-2-uber-*.jar <FLINK_HOME>/lib/
```

### 2.4 启动 Flink 本地集群

为了同时运行多个 Flink 任务，你需要修改 `<FLINK_HOME>/conf/flink-conf.yaml`（Flink 版本 < 1.19）或 `<FLINK_HOME>/conf/config.yaml`（Flink 版本 >= 1.19）中的集群配置:
```
taskmanager.numberOfTaskSlots: 2
```
要启动本地集群，请运行 Flink 自带的 bash 脚本：
```
<FLINK_HOME>/bin/start-cluster.sh
```
访问 `localhost:8081` 来查看 Flink Web UI，可以看到集群正在运行。你现在可以启动 Flink SQL 客户端来执行 SQL 脚本：
```
<FLINK_HOME>/bin/sql-client.sh
```

### 2.5 创建 Catalog 和表

```

```
