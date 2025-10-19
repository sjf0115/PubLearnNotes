Flink 应用端到端的一致性保障取决于 Sink 连接器的属性，正常情况下不做额外的操作是不能提供端到端的 Exactly-Once 语义保障的。例如 Failover 会导致作业重启，然后从最近一次成功的 Checkpoint 记录的 Offset 位点开始消费，这样会导致 Checkpoint 记录的 Offset 位点到实际消费到的 Offset 位点之间记录被重复消费。为了提供端到端的一致性保障，应用的 Sink 连接器要么实现幂等性，要么实现事务支持。如果无法实现幂等性写入，也没有提供内置的事务支持，那只能通过预写日志 WAL 的方式实现。

## 1. 原理

为了简化预写日志 WAL Sink 的实现，Flink DataStream API 提供了一个 GenericWriteAheadSink 模板(抽象类)，可以通过继承这个抽象类更加方便的实现一致性的 Sink。实现 GenericWriteAheadSink 的算子会和 Flink 的检查点机制相结合，目的是将记录以 Exactly-Once 语义写入外部系统。

GenericWriteAheadSink 的工作原理是收集每个 Checkpoint 周期内所有需要写出的记录，并将它们存储到 Sink 任务的算子状态中。最终状态进行 Checkpoint 写入持久化存储中并在故障时用来恢复。由于在发生故障时可以恢复，所以不会导致数据丢失。当一个任务接收到 Checkpoint 完成通知时，会将此 Checkpoint 周期内的所有记录写入到外部系统。根据 Sink 的具体实现，这些记录可以被写入任意一个存储或者消息系统中。当所有记录发送成功时，Sink 需要在内部提交该 Checkpoint。

Checkpoint 的提交分两步：第一步，Sink 需要将 Checkpoint 已提交的信息持久化。第二步，删除 WAL 中相应的数据。Checkpoint 已提交的信息无法存储在 Flink 应用程序状态中，因为状态本身不具有持久性，并且会在故障恢复时重置状态。实际上，GenericWriteAheadSink 依赖一个名为 CheckpointCommitter 的可插拔组件来控制外部持久化系统存储和查找已提交 Checkpoint 信息。

## 2. 注意

需要特别注意的是，基于 WAL 的 Sink 在某些极端情况下可能会将同一条记录重复写出多次。因此 GenericWriteAheadSink 并不能百分之百的提供 Exactly-Once 语义保证，而只能做到 At-Least-Once 语义保证。有两种场景会导致同一条记录重复写出多次：
- 在运行 `sendValues` 方法时发生故障。如果外部系统不支持原子性的写入多个记录(全写或者全不写)，那么就会出现部分数据已经写入而部分数据没能写入成功。由于此时检查点还没有提交，下次恢复时重写全部记录。
- 所有记录都已经成功写入，`sendValues` 返回了 true，但是程序在调用 CheckpointCommitter 前出现故障或者 CheckpointCommitter 未能成功提交检查点。这样，在故障恢复期间，未提交的检查点所对应的全部记录都会被重新消费一次。

## 3. 实现

下面我们自定义实现一个输出标准输出的 StdOutWALSink，如下所示：
```java
private static class StdOutWALSink extends GenericWriteAheadSink<String> {
    // 构造函数
    public StdOutWALSink() throws Exception {
        super(
                // CheckpointCommitter
                new FileCheckpointCommitter(System.getProperty("java.io.tmpdir")),
                // 用于序列化输入记录的 TypeSerializer
                Types.STRING.createSerializer(new ExecutionConfig()),
                // 自定义作业 ID
                UUID.randomUUID().toString()
        );
    }

    @Override
    public void open() throws Exception {
        super.open();
    }

    @Override
    public void close() throws Exception {
        super.close();
    }

    @Override
    protected boolean sendValues(Iterable<String> words, long checkpointId, long timestamp) throws Exception {
        // 输出到外部系统 在这为 StdOut 标准输出
        // 每次 Checkpoint 完成之后通过 notifyCheckpointComplete 调用该方法
        int subtask = getRuntimeContext().getIndexOfThisSubtask();
        for (String word : words) {
            LOG.info("checkpointId {} (subTask = {}) send word: {}", checkpointId, subtask, word);
            System.out.println("StdOut> " + word);
        }
        return true;
    }
}
```
GenericWriteAheadSink 完善的内部逻辑使得我们可以相对容易的实现基于 WAL 的 Sink。继承自 GenericWriteAheadSink 的算子需要在构造方法中提供三个参数：
- 一个 CheckpointCommitter
- 一个用于序列化输入记录的 TypeSerializer
- 一个传递给 CheckpointCommitter，用于应用重启后标识提交信息的作业 ID

```java
// 构造函数
public StdOutWALSink() throws Exception {
    super(
            // CheckpointCommitter
            new FileCheckpointCommitter(System.getProperty("java.io.tmpdir")),
            // 用于序列化输入记录的 TypeSerializer
            Types.STRING.createSerializer(new ExecutionConfig()),
            // 自定义作业 ID
            UUID.randomUUID().toString()
    );
}
```
> 从上面可以看到内部使用一个名为 FileCheckpointCommitter 的 CheckpointCommitter，其目的是将 Sink 算子实例提交的检查点信息保存到文件中，具体实现可以查阅[源码解读 | Flink CheckpointCommitter](https://smartsi.blog.csdn.net/article/details/130550211)。

此外，最重要的是需要实现 `sendValues` 方法：
```java
@Override
protected boolean sendValues(Iterable<Tuple2<String, Long>> words, long checkpointId, long timestamp) throws Exception {
    // 输出到外部系统 在这为 StdOut 标准输出
    // 每次 Checkpoint 完成之后通过 notifyCheckpointComplete 调用该方法
    int subtask = getRuntimeContext().getIndexOfThisSubtask();
    for (Tuple2<String, Long> word : words) {
        LOG.info("checkpointId {} (subTask = {}) send word: {}", checkpointId, subtask, word);
        System.out.println("StdOut> " + word);
    }
    return true;
}
```
GenericWriteAheadSink 会调用 `sendValues` 方法将已完成检查点 `checkpointId` 对应的全部记录写入外部存储系统。该方法第一个参数是检查点 `checkpointId` 对应全部记录的 Iterable 对象 `words`、检查点ID `checkpointId` 以及检查点的生成时间 `timestamp`。在这我们简单实现了一个写标准输出的 WAL Sink，输出该检查点对应的全部记录。在全部记录写出成功时返回 true，如果失败则返回 false。

> 你可以简单理解 GenericWriteAheadSink 实现了一个缓存，在收到上游的记录时，先将消息存储在状态中，再收到 Checkpoint 完成通知后，调用 `sendValues` 方法向外部系统输出缓冲的全部记录。GenericWriteAheadSink 相当于缓存了一个 Checkpoint 间隔的记录。


## 4. 示例

```java
// 每隔 30s 进行一次 Checkpoint 如果不设置 Checkpoint 自定义 WAL Sink 不会输出数据
env.enableCheckpointing(30 * 1000);
// 重启策略
env.setRestartStrategy(RestartStrategies.fixedDelayRestart(
        1, // 重启最大次数
        Time.of(10, TimeUnit.SECONDS) // 重启时间间隔
));

...

// 单词流
DataStreamSource<String> source = env.addSource(consumer);
// 单词计数
DataStream<String> wordCountStream = source.map(new MapFunction<String, WordCount>() {
            @Override
            public WordCount map(String word) throws Exception {
                WordCount wc = gson.fromJson(word, WordCount.class);
                LOG.info("word: {}", wc.getWord());
                // 模拟程序 Failover 遇到 error 抛出异常
                if (Objects.equals(wc.getWord(), "ERROR")) {
                    throw new RuntimeException("模拟程序 Failover");
                }
                return wc;
            }
        })
        .keyBy(wc -> wc.getWord())
        .sum("frequency")
        .map(new MapFunction<WordCount, String>() {
            @Override
            public String map(WordCount wordCount) throws Exception {
                return gson.toJson(wordCount);
            }
        });

wordCountStream.transform(
        "StdOutWriteAheadSink",
        Types.STRING,
        new StdOutWALSink()
);
```

>完整代码请查阅：[StdOutWriteAheadSinkExample](https://github.com/sjf0115/flink-example/blob/main/flink-example-1.13/src/main/java/com/flink/example/stream/sink/wal/StdOutWriteAheadSinkExample.java)

需要注意的是，GenericWriteAheadSink 没有实现 SinkFunction 接口。因此我们无法使用 `DataStream.addSink()` 方法添加一个继承自 GenericWriteAheadSink 的 Sink，而是要使用 `DataStream.transform()` 方法：
```java
result.transform(
    "StdOutWriteAheadSink",
    Types.TUPLE(Types.STRING, Types.LONG),
    new StdOutWALSink()
);
```

实际输出效果如下所示：
```
22:51:41,269 INFO  org.apache.kafka.clients.consumer.KafkaConsumer              [] - [Consumer clientId=consumer-word-count-2, groupId=word-count] Subscribed to partition(s): word-0
22:51:41,271 INFO  org.apache.kafka.clients.consumer.internals.SubscriptionState [] - [Consumer clientId=consumer-word-count-2, groupId=word-count] Seeking to LATEST offset of partition word-0
22:51:41,277 INFO  org.apache.kafka.clients.Metadata                            [] - [Consumer clientId=consumer-word-count-2, groupId=word-count] Cluster ID: 08_cspBUQ76ihA2JXXIV9w
22:51:41,283 INFO  org.apache.kafka.clients.consumer.internals.SubscriptionState [] - [Consumer clientId=consumer-word-count-2, groupId=word-count] Resetting offset for partition word-0 to offset 17.
22:51:48,719 INFO  com.flink.example.stream.sink.wal.StdOutWriteAheadSinkExample [] - word: a
22:51:48,721 INFO  com.flink.example.stream.sink.wal.StdOutWriteAheadSinkExample [] - word: c
22:51:53,615 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - Triggering checkpoint 1 (type=CHECKPOINT) @ 1756651913599 for job 83b9fd3bc8bc1e8dbefda77be9c7ad0b.
22:51:53,740 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - Completed checkpoint 1 for job 83b9fd3bc8bc1e8dbefda77be9c7ad0b (3754 bytes in 139 ms).
22:51:53,740 INFO  com.flink.example.stream.sink.wal.FileCheckpointCommitter    [] - CheckpointId 1 (SubTask = 0) has not committed
22:51:53,741 INFO  org.apache.flink.streaming.runtime.operators.GenericWriteAheadSink [] - checkpointId 1 (subTask = 0) send word: {"word":"a","frequency":1}
StdOut> {"word":"a","frequency":1}
22:51:53,741 INFO  org.apache.flink.streaming.runtime.operators.GenericWriteAheadSink [] - checkpointId 1 (subTask = 0) send word: {"word":"c","frequency":1}
StdOut> {"word":"c","frequency":1}
22:51:53,799 INFO  org.apache.kafka.clients.consumer.internals.AbstractCoordinator [] - [Consumer clientId=consumer-word-count-2, groupId=word-count] Discovered group coordinator 127.0.0.1:9092 (id: 2147483647 rack: null)
22:51:53,799 INFO  com.flink.example.stream.sink.wal.FileCheckpointCommitter    [] - CheckpointId 1 (SubTask = 0) commit, path is /var/folders/hg/hmth4y_n0rb5rnh0jyv43r7h0000gn/T/b450956c-03dc-443e-ac89-87f821050816/0
22:52:02,283 INFO  com.flink.example.stream.sink.wal.StdOutWriteAheadSinkExample [] - word: a
22:52:02,284 INFO  com.flink.example.stream.sink.wal.StdOutWriteAheadSinkExample [] - word: c
22:52:23,598 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - Triggering checkpoint 2 (type=CHECKPOINT) @ 1756651943597 for job 83b9fd3bc8bc1e8dbefda77be9c7ad0b.
22:52:23,611 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - Completed checkpoint 2 for job 83b9fd3bc8bc1e8dbefda77be9c7ad0b (3754 bytes in 12 ms).
22:52:23,615 INFO  com.flink.example.stream.sink.wal.FileCheckpointCommitter    [] - CheckpointId 2 (SubTask = 0) has not committed
22:52:23,615 INFO  org.apache.flink.streaming.runtime.operators.GenericWriteAheadSink [] - checkpointId 2 (subTask = 0) send word: {"word":"a","frequency":2}
StdOut> {"word":"a","frequency":2}
22:52:23,615 INFO  org.apache.flink.streaming.runtime.operators.GenericWriteAheadSink [] - checkpointId 2 (subTask = 0) send word: {"word":"c","frequency":2}
StdOut> {"word":"c","frequency":2}
22:52:23,616 INFO  com.flink.example.stream.sink.wal.FileCheckpointCommitter    [] - CheckpointId 2 (SubTask = 0) commit, path is /var/folders/hg/hmth4y_n0rb5rnh0jyv43r7h0000gn/T/b450956c-03dc-443e-ac89-87f821050816/0
22:52:31,904 INFO  com.flink.example.stream.sink.wal.StdOutWriteAheadSinkExample [] - word: a
22:52:31,905 INFO  com.flink.example.stream.sink.wal.StdOutWriteAheadSinkExample [] - word: c
22:52:38,670 INFO  com.flink.example.stream.sink.wal.StdOutWriteAheadSinkExample [] - word: ERROR
22:52:38,679 WARN  org.apache.flink.runtime.taskmanager.Task                    [] - Source: Custom Source -> Map (1/1)#0 (affccf641708ddecc467009d8b6eca0f) switched from RUNNING to FAILED with failure cause: java.lang.RuntimeException: 模拟程序 Failover

...

22:52:48,764 INFO  org.apache.kafka.clients.consumer.KafkaConsumer              [] - [Consumer clientId=consumer-word-count-4, groupId=word-count] Subscribed to partition(s): word-0
22:52:48,764 INFO  org.apache.kafka.clients.consumer.KafkaConsumer              [] - [Consumer clientId=consumer-word-count-4, groupId=word-count] Seeking to offset 21 for partition word-0
22:52:48,768 INFO  org.apache.kafka.clients.Metadata                            [] - [Consumer clientId=consumer-word-count-4, groupId=word-count] Cluster ID: 08_cspBUQ76ihA2JXXIV9w
22:52:48,772 INFO  com.flink.example.stream.sink.wal.StdOutWriteAheadSinkExample [] - word: a
22:52:48,772 INFO  com.flink.example.stream.sink.wal.StdOutWriteAheadSinkExample [] - word: c
22:52:48,772 INFO  com.flink.example.stream.sink.wal.StdOutWriteAheadSinkExample [] - word: ERROR
22:52:48,774 WARN  org.apache.flink.runtime.taskmanager.Task                    [] - Source: Custom Source -> Map (1/1)#1 (e3a3ee0f4258f54f1d71a1503283ef70) switched from RUNNING to FAILED with failure cause: java.lang.RuntimeException: 模拟程序 Failover
...
```
