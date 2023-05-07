对于那些依赖于不支持回滚的状态后端的 Sink，当前检查点机制并不是完全适合。当处理这样的系统时，如果想要保证 Exactly-Once 语义，那么既不能在创建快照时提交数据(如果 Sink 的另一个实例失败了可能会导致对相同数据的重放)，也不能在接收检查点完成通知时提交数据(因为后续失败将使我们不知道数据是否被提交)。

CheckpointCommitter 很好的解决了第二个问题，可以通过保存一个实例是否提交了检查点信息来判断是否提交成功。这些数据必须存储在一个后端 Backend(比如分布式文件或者数据库)，即使在重启期间也是持久化的(这就排除了 Flink 的状态机制)，并且所有机器都可以访问。

## 1. 解读

CheckpointCommitter 是一个抽象类，主要用来保存 Sink 算子实例提交给后端的检查点信息：
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

    public abstract void open() throws Exception;
    public abstract void close() throws Exception;
    public abstract void createResource() throws Exception;
    public abstract void commitCheckpoint(int subtaskIdx, long checkpointID) throws Exception;
    public abstract boolean isCheckpointCommitted(int subtaskIdx, long checkpointID) throws Exception;
}
```
CheckpointCommitter 提供了两个变量，一个是作业 ID（jobId），另一个是算子ID（operatorId），同时提供了两个变量对应的内部使用方法：`setJobId` 和 `setOperatorId`，分别用于实例化后设置作业ID和算子ID。除了这两个方法之外，还提供了与资源相关以及与提交检查点相关的方法：
- 资源相关方法
  - `open()` 方法用于打开或者连接到资源，并可能需要事先创建这个资源。
  - `close()` 方法用于关闭资源或者到它的连接。在此调用之后，资源通常还会存在，并不会删除。
  - `createResource()` 用于创建/打开/连接到存储信息的资源。在实例化后直接调用一次。
- 提交检查点相关的方法
  - `commitCheckpoint()` 方法用于在资源中将给定的检查点标记为已完成。
  - `isCheckpointCommitted()` 用于在资源中检查是否已完全提交给定的检查点。

> 在这的资源 Resource 就是上文提到的用于保存 Sink 算子实例提交检查点信息的后端，比如分布式文件或者数据库

## 2. 实现

在这我们实现一个基于文件资源的 CheckpointCommitter，即将 Sink 算子实例提交的检查点信息保存到文件中：
```java
public class FileCheckpointCommitter extends CheckpointCommitter {
      // 基础目录路径
      private final String basePath;
      // 为不同作业分配的目录路径
      private String jobBasePath;
      public FileCheckpointCommitter(String basePath) {
          this.basePath = basePath;
      }
      ...
}
```
由于在这我们使用的资源是文件，不需要创建或者关闭一个连接，直接创建文件即可，所以 `open()` 和 `close()` 可以不实现：
```java
@Override
public void open() throws Exception {
    LOG.info("open committer");
    // no need to open a connection
}

@Override
public void close() throws Exception {
    LOG.info("close committer");
    // no need to close a connection
}
```
上面提到直接在 `createResource()` 方法中创建用来保存检查点信息的文件即可，需要注意的是我们以当前作业 ID 作为提交文件的目录：
```java
@Override
public void createResource() throws Exception {
    this.jobBasePath = this.basePath + "/" + this.jobId;
    Files.createDirectory(Paths.get(this.jobBasePath));
    LOG.info("create resource {}", this.jobBasePath);
}
```
对于如何共享资源没有强制要求，可以为所有 Flink 作业分配一个资源，也可以为每个作业/算子/实例分别分配一个资源。由于资源不能由系统本身清理，因此应该尽可能的小。

有了资源之后，我们就需要确定如何将检查点信息提交到资源中，在这就是如何写入到文件中：
```java
@Override
public void commitCheckpoint(int subTaskIdx, long checkpointID) throws Exception {
    Path commitPath = Paths.get(this.jobBasePath + "/" + subTaskIdx);
    // 将 CheckpointID 转换为 16 进制字符串
    String hexID = "0x" + StringUtils.leftPad(Long.toHexString(checkpointID), 16, "0");
    // 将 16 进制字符串写进提交文件中
    Files.write(commitPath, hexID.getBytes());
    LOG.info("CheckpointId {} (SubTask = {}) commit, path is {}", checkpointID, subTaskIdx, commitPath);
}
```
从上面可以注意的我们为每个实例单独创建了一个文件，然后将检查点ID的 16 进制字符串写进到以实例 ID 命名的文件中。

最后需要实现在资源中检查指定的检查点是否已经提交：
```java
@Override
public boolean isCheckpointCommitted(int subTaskIdx, long checkpointID) throws Exception {
    boolean isCommitted;
    Path commitPath = Paths.get(this.jobBasePath + "/" + subTaskIdx);
    if (!Files.exists(commitPath)) {
        // 提交文件都没有表示没有提交过
        isCommitted = false;
    } else {
        // 从文件中读取提交的 CheckpointId
        String hexID = Files.readAllLines(commitPath).get(0);
        Long commitCheckpointID = Long.decode(hexID);
        // 判断当前 CheckpointID 是否小于等于已提交的 CheckpointID
        isCommitted = checkpointID <= commitCheckpointID;
    }
    if (isCommitted) {
        LOG.info("CheckpointId {} (SubTask = {}) is committed", checkpointID, subTaskIdx);
    } else {
        LOG.info("CheckpointId {} (SubTask = {}) has not committed", checkpointID, subTaskIdx);
    }
    return isCommitted;
}
```
首先判断以作业ID为目录，实例ID命名的文件是否存在，如果连文件都没有则表示该检查点肯定没有提交过。如果对应的文件存在，则需要判断文件中提交的检查点ID是否大于等于指定的检查点ID，如果大于等于，则表示提交过了。

创建完 FileCheckpointCommitter 之后，简单看一下如何使用：
```java
private static class StdOutWALSink extends GenericWriteAheadSink<Tuple2<String, Long>> {
    public StdOutWALSink() throws Exception {
        super(
                new FileCheckpointCommitter(System.getProperty("java.io.tmpdir")),
                Types.<Tuple2<String, Long>>TUPLE(Types.STRING, Types.LONG).createSerializer(new ExecutionConfig()),
                UUID.randomUUID().toString()
        );
    }
    ...
}
```
从上面可以看到我们在基于 GenericWriteAheadSink 实现的一个 WAL Sink 中使用 FileCheckpointCommitter 来保存 Sink 算子实例提交给后端的检查点信息。使用比较简单，只需要传递一个保存文件的目录即可，在这我们选择的是系统临时目录。

> 详细代码请查阅：[StdOutWriteAheadSinkExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/sink/wal/StdOutWriteAheadSinkExample.java)

除了我们自己实现的 FileCheckpointCommitter 之外，你也可以查看 Flink 的一个内置实现 [CassandraCommitter](https://github.com/apache/flink/blob/release-1.16.1/flink-connectors/flink-connector-cassandra/src/main/java/org/apache/flink/streaming/connectors/cassandra/CassandraCommitter.java)。

> 完整代码请查阅：[FileCheckpointCommitter](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/state/checkpoint/FileCheckpointCommitter.java)
