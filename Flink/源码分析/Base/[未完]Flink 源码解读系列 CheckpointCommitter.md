
CheckpointCommitter 类用来保存有关哪个 Sink 算子实例已将检查点提交给状态后端的信息。当前的检查点机制不适合一部分 Sink，即依赖不支持回滚的状态后端的。当处理这样的系统时，如果想要保证 Exactly-Once 语义，那么既不能在创建快照时提交数据(可能另一个 Sink 实例失败了，会导致对相同数据的重放)，也不能在接收检查点完成通知时提交数据(因为后续失败将使我们不知道数据是否被提交)。

CheckpointCommitter 可以通过保存一个实例是否提交了属于该检查点的所有数据来解决第二个问题。这些数据必须存储在一个后端 Backend，即使在重启期间也是持久化的(这就排除了 Flink 的状态机制)，并且所有机器都可以访问(例如，数据库或分布式文件)。

对于如何共享资源没有强制要求，可以为所有 Flink 作业分配一个资源，或者为每个作业/算子/实例分别分配一个资源。这意味着资源不能由系统本身清理，因此应该尽可能保持小。

## 1. 基础信息

```java
public abstract class CheckpointCommitter implements Serializable {
    protected static final Logger LOG = LoggerFactory.getLogger(CheckpointCommitter.class);

    protected String jobId;
    protected String operatorId;

    public void setJobId(String id) throws Exception {
        this.jobId = id;
    }

    public void setOperatorId(String id) throws Exception {
        this.operatorId = id;
    }
}
```
CheckpointCommitter 提供了两个变量，一个是作业 ID（jobId）以及算子ID（operatorId），此外还分别对应提供了两个内部使用的方法：`setJobId` 和 `setOperatorId`，用于实例化后设置作业ID和算子ID。

## 2. 资源相关

```java
public abstract void open() throws Exception;
public abstract void close() throws Exception;
public abstract void createResource() throws Exception;
```

`open()` 方法用于打开或者连接到资源，并可能需要事先创建这个资源。`close()` 方法用于关闭资源或者到它的连接。在此调用之后，资源通常还会存在。`createResource()` 用于创建/打开/连接到用于存储信息的资源。在实例化后直接调用一次。


## 3. 检查点相关

```java
public abstract void commitCheckpoint(int subtaskIdx, long checkpointID) throws Exception;
public abstract boolean isCheckpointCommitted(int subtaskIdx, long checkpointID) throws Exception;
```
