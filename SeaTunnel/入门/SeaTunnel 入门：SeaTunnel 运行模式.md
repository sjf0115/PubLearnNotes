SeaTunnel 支持两种运行模式：
- 本地模式（Local Mode）：任务在单机上运行，无需启动集群。
- 集群模式（Cluster Mode）：任务在分布式集群上运行，需要启动 SeaTunnel 集群。

## 1. 本地模式

### 1.1 特点

任务在单机上运行，适合小规模数据同步任务。无需额外资源，启动速度快。

### 1.2 适用场景

数据量较小（如百万级以下）的开发和测试环境。

### 1.3 运行方式

直接运行 seatunnel.sh 脚本，无需启动集群，如下所示：
```shell
bin/seatunnel.sh --config config/mysql_to_console.conf
```

## 2. 集群模式

### 2.1 特点

任务在分布式集群上运行，适合大规模数据同步任务。需要启动 SeaTunnel 集群（如基于 Flink 或 Spark 的集群）。

### 2.2 适用场景

数据量较大（如千万级或以上）的生产环境。

### 2.3 运行方式

需要先启动 SeaTunnel 集群，然后提交任务到集群。

第一步是启动 SeaTunnel 集群。假设使用 Flink 作为集群引擎：
```
# 启动 Flink 集群
./bin/start-cluster.sh
```

第二步是修改配置文件。在 mysql_to_console.conf 配置文件中指定集群模式：
```yaml
env {
  execution.parallelism = 4  # 设置并行度
  job.mode = "CLUSTER"       # 集群模式
}
```

第三步提交任务到集群。运行以下命令提交任务：
```
bin/seatunnel.sh --config config/mysql_to_console.conf --cluster
```
