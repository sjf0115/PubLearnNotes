SeaTunnel Zeta 引擎支持三种不同的部署模式：本地模式、混合集群模式和分离集群模式。每种部署模式都有不同的使用场景和优缺点。在选择部署模式时，您应该根据您的需求和环境来选择。在这将详细介绍分离集群模式。

分离集群模式是将 SeaTunnel Zeta 引擎的 Master 服务和 Worker 服务分离，每个服务单独一个进程。Master 节点只负责作业调度、RESTful API、任务提交、Imap 数据存储等。Worker 节点只负责任务的执行，不参与选举成为 Master，也不存储 Imap 数据。

在所有 Master 节点中，同一时间只有一个 Master 节点工作，其他 Master 节点处于 Standby 状态。当当前 Master 节点宕机或心跳超时，会从其它 Master 节点中选举出一个新的 Master Active 节点。

分离集群模式是最推荐的一种使用方式，在该模式下 Master 的负载会很小，Master 有更多的资源用来进行作业的调度，任务的容错指标监控以及提供 RESTful API 服务等，会有更高的稳定性。同时 Worker 节点不存储 Imap 的数据，所有的 Imap 数据都存储在 Master 节点中，即使 Worker 节点负载高或者挂掉，也不会导致 Imap 数据重新分布。

## 1. 下载

下载和制作SeaTunnel安装包请参考[]()。

## 2. 配置 Master 节点 JVM 选项

Master节点的JVM参数在 $SEATUNNEL_HOME/config/jvm_master_options 文件中配置。
```
# JVM Heap
-Xms2g
-Xmx2g

# JVM Dump
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/tmp/seatunnel/dump/zeta-server

# Metaspace
-XX:MaxMetaspaceSize=2g

# G1GC
-XX:+UseG1GC
```
Worker节点的JVM参数在$SEATUNNEL_HOME/config/jvm_worker_options文件中配置。
```
# JVM Heap
-Xms2g
-Xmx2g

# JVM Dump
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/tmp/seatunnel/dump/zeta-server

# Metaspace
-XX:MaxMetaspaceSize=2g

# G1GC
-XX:+UseG1GC
```
## 3. 配置 SeaTunnel Engine

SeaTunnel Engine 提供许多功能，需要在 seatunnel.yaml 中进行配置。
```yaml
seatunnel:
  engine:
    history-job-expire-minutes: 1440
    backup-count: 1
    queue-type: blockingqueue
    print-execution-info-interval: 60
    print-job-metrics-info-interval: 60
    slot-service:
      dynamic-slot: true
    checkpoint:
      interval: 10000
      timeout: 60000
      storage:
        type: hdfs
        max-retained: 3
        plugin-config:
          namespace: /tmp/seatunnel/checkpoint_snapshot
          storage.type: hdfs
          fs.defaultFS: file:///tmp/ # Ensure that the directory has written permission
```

### 3.1 Imap中数据的备份数设置

> 该参数在Worker节点无效

```yaml
seatunnel:
    engine:
        backup-count: 1
        # 其他配置
```
SeaTunnel Engine 是基于 Hazelcast IMDG 实现集群管理。集群的状态数据（作业运行状态、资源状态）存储在 Hazelcast IMap。存储在 Hazelcast IMap 中的数据将在集群的所有节点上分布和存储。Hazelcast 会分区存储在 Imap 中的数据。每个分区可以指定备份数量。 因此，SeaTunnel Engine 可以实现集群 HA，无需使用其他服务（例如 zookeeper）。

`backup-count` 是定义同步备份数量的参数。例如，如果设置为 1，则分区的备份将放置在一个其他成员上。如果设置为 2，则将放置在两个其他成员上。我们建议 `backup-count` 的值为 max(1, min(5, N/2))。

> N 是集群节点的数量。

由于在分离集群模式下，Worker节点不存储Imap数据，因此Worker节点的backup-count配置无效。如果Master和Worker进程在同一个机器上启动，Master和Worker会共用seatunnel.yaml配置文件，此时Worker节点服务会忽略backup-count配置。

### 3.2 Slot配置

> 该参数在Worker节点无效

Slot数量决定了集群节点可以并行运行的任务组数量。一个任务需要的Slot的个数公式为 N = 2 + P(任务配置的并行度)。 默认情况下SeaTunnel Engine的slot个数为动态，即不限制个数。我们建议slot的个数设置为节点CPU核心数的2倍。

动态slot个数（默认）配置如下：
```yaml
seatunnel:
    engine:
        slot-service:
            dynamic-slot: true
        # 其他配置
```
静态slot个数配置如下：
```yaml
seatunnel:
    engine:
        slot-service:
            dynamic-slot: false
            slot-num: 20
```


。。。。
