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

### 3.3 历史作业过期配置

每个完成的作业的信息，如状态、计数器和错误日志，都存储在 IMap 对象中。随着运行作业数量的增加，内存会增加，最终内存将溢出。因此，您可以调整 `history-job-expire-minutes` 参数来解决这个问题。此参数的时间单位是分钟。默认值是 1440 分钟，即一天。

```yaml
seatunnel:
  engine:
    history-job-expire-minutes: 1440
```

### 3.4 类加载器缓存模式

此配置主要解决不断创建和尝试销毁类加载器所导致的资源泄漏问题。如果您遇到与 metaspace 空间溢出相关的异常，您可以尝试启用此配置。为了减少创建类加载器的频率，在启用此配置后，SeaTunnel 在作业完成时不会尝试释放相应的类加载器，以便它可以被后续作业使用，也就是说，当运行作业中使用的 Source/Sink 连接器类型不是太多时，它更有效。 默认值是 false。

```yaml
seatunnel:
  engine:
    classloader-cache-mode: true
```

### 3.5 作业调度策略

当资源不足时，作业调度策略可以配置为以下两种模式：
- WAIT：等待资源可用。
- REJECT：拒绝作业，默认值。

```yaml
seatunnel:
  engine:
    job-schedule-strategy: WAIT
```
当 `dynamic-slot: ture` 时，`job-schedule-strategy: WAIT` 配置会失效，将被强制修改为 `job-schedule-strategy: REJECT`，因为动态 Slot时该参数没有意义，可以直接提交。

### 3.6 检查点管理器

> 该参数在Worker节点无效

与 Flink 一样，SeaTunnel Zeta Engine 支持 Chandy–Lamport 算法。因此，可以实现无数据丢失和重复的数据同步。检查点是一种容错恢复机制。这种机制确保程序在运行时，即使突然遇到异常，也能自行恢复。检查点定时触发，每次检查点进行时每个 Task 都会被要求将自身的状态信息（比如读取 kafka 时读取到了哪个offset）上报给检查点线程，由该线程写入一个分布式存储（或共享存储）。当任务失败然后自动容错恢复时，或者通过 `seatunnel.sh -r` 指令恢复之前被暂停的任务时，会从检查点存储中加载对应作业的状态信息，并基于这些状态信息进行作业的恢复。

```yaml
seatunnel:
  engine:
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

`interval` 配置两个检查点之间的间隔，单位是毫秒。`timeout` 配置检查点的超时时间。如果在超时时间内无法完成检查点，则会触发检查点失败，作业失败。如果这两个参数分别在作业的配置文件的 env 中配置了，将以作业配置文件中设置的为准。

如果集群的节点大于1，检查点存储必须是一个分布式存储，或者共享存储，这样才能保证任意节点挂掉后依然可以在另一个节点加载到存储中的任务状态信息。SeaTunnel Zeta Engine 支持 HDFS、OSS 等多种检查点存储类型，检查点存储配置通过 `checkpoint.storage` 配置。

> 检查点配置只有 Master 服务才会读取，Worker 服务不会读取检查点配置。如果 Master 和 Worker 进程在同一个机器上启动，Master 和 Worker 会共用 seatunnel.yaml 配置文件，此时 Worker 节点服务会忽略 checkpoint 配置。





。。。。
