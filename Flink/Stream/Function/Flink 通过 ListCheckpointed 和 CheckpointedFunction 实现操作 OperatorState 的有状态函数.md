## 1. CheckpointedFunction

这是有状态转换函数的核心接口，这意味着维护状态的函数可以跨多个流记录进行处理。虽然存在更轻量级的接口，但该接口在管理 Keyed State 和 Operator State 能提供最大的灵活性。

OperatorStateStore 和 KeyedStateStore提供了对数据结构的访问，Flink应该在其中存储状态，以便透明地管理和检查它，例如org.apache.flink.api.common.state.ValueState或org.apache.flink.api.common.state.ListState。
注意:KeyedStateStore只能在转换支持键控状态时使用，也就是说，当它应用在键控流上时(在keyBy(…)之后)。


```java
public interface CheckpointedFunction {
    void snapshotState(FunctionSnapshotContext context) throws Exception;
    void initializeState(FunctionInitializationContext context) throws Exception;
}
```

### 2.1 initializeState

在分布式执行期间，当创建转换函数的并行实例时，将会调用 `initializeState(FunctionInitializationContext)` 方法。该方法提供了访问 FunctionInitializationContext 的能力，而 FunctionInitializationContext 又提供了访问 OperatorStateStore 和 KeyedStateStore 的能力：
```java
public interface FunctionInitializationContext extends ManagedInitializationContext {
}

public interface ManagedInitializationContext {
    boolean isRestored();
    OperatorStateStore getOperatorStateStore();
    KeyedStateStore getKeyedStateStore();
}
```
通过 `isRestored()` 可以判断状态是否是从上一次执行的快照中恢复，如果是返回 true。需要注意的是对于无状态任务，该方法总是返回 false。通过 `getOperatorStateStore()` 方法获取允许注册算子状态 OpeartorState 的 OperatorStateStore。通过 `getKeyedStateStore()` 方法获取允许注册键值状态 KeyedState 的 KeyedStateStore。

OperatorStateStore 和 KeyedStateStore 则又提供了访问状态 State 存储数据结构的能力，例如 `org.apache.flink.api.common.state.ValueState` 或者 `org.apache.flink.api.common.state.ListState`：
```java
public void initializeState(FunctionInitializationContext context) throws Exception {
    ListStateDescriptor<String> descriptor = new ListStateDescriptor<>(
            "buffered-words", TypeInformation.of(new TypeHint<String>() {}));
    statePerPartition = context.getOperatorStateStore().getListState(descriptor);
    int subTask = getRuntimeContext().getIndexOfThisSubtask();
    // 从状态中恢复
    if (context.isRestored()) {
        for (String word : statePerPartition.get()) {
            bufferedWords.add(word);
        }
        LOG.info("initializeState subTask: {}, words: {}", subTask, bufferedWords.toString());
    } else {
        // 首次运行时执行逻辑
    }
}
```

### 2.2 snapshotState

每当触发 Checkpoint 生成转换函数的状态快照时就会调用 `snapshotState(FunctionSnapshotContext)` 方法。该方法提供了访问 FunctionSnapshotContext 的能力，而 FunctionSnapshotContext 又提供了访问检查点元数据的能力：
```java
public interface FunctionSnapshotContext extends ManagedSnapshotContext {}

public interface ManagedSnapshotContext {
    long getCheckpointId();
    long getCheckpointTimestamp();
}
```
通过 `getCheckpointId()` 方法获取生成快照时的检查点 ID，检查点 ID 保证了检查点之间的严格单调递增。对于完成的两个检查点 A 和 B, `ID_B > ID_A` 表示检查点 B 包含检查点 A，即检查点 B 包含的状态晚于检查点 A。通过 `getCheckpointTimestamp()` 方法返回主节点触发检查点生成快照时的时间戳。

在 `snapshotState` 方法中，一般需要确保检查点数据结构（在 initialization 方法中获取）是最新的，以便生成快照。此外，函数可以作为一个 hook 与外部系统交互实现刷新/提交/同步。如下所示，通过 FunctionSnapshotContext 上下文获取检查点元数据信息，并将最新数据存储在状态中生成快照：
```java
public void snapshotState(FunctionSnapshotContext context) throws Exception {
    long checkpointId = context.getCheckpointId();
    int subTask = getRuntimeContext().getIndexOfThisSubtask();
    // 清空上一次快照的状态
    statePerPartition.clear();
    // 生成新快照的状态
    for (String word : bufferedWords) {
        statePerPartition.add(word);
    }
    LOG.info("snapshotState subTask: {}, checkpointId: {}, words: {}", subTask, checkpointId, bufferedWords.toString());
}
```
从代码中可以看出，在 `snapshotState` 中首先清理掉上一次 Checkpoint 触发存储的 OperatorState 的数据，然后再添加并更新本次 Checkpoint 需要的状态数据。

### 2.3 示例

下面我们以一个缓冲 4 个元素才输出的 Sink 为例，具体看一下 CheckpointedFunction 是如何操作 OperatorState：
```java
public class CheckpointedFunctionOSExample {
    private static final Logger LOG = LoggerFactory.getLogger(CheckpointedFunctionOSExample.class);

    public static void main(String[] args) throws Exception {
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.setParallelism(2);

        // 每10s一次Checkpoint
        env.enableCheckpointing(30 * 1000);
        // 重启策略
        env.setRestartStrategy(RestartStrategies.fixedDelayRestart(
                3, // 重启最大次数
                Time.of(10, TimeUnit.SECONDS) // 重启时间间隔
        ));

        // Socket 输入
        DataStream<String> stream = env.socketTextStream("localhost", 9100, "\n");

        // 单词流
        DataStream<String> wordStream = stream.flatMap(new FlatMapFunction<String, String>() {
            @Override
            public void flatMap(String value, Collector out) {
                for (String word : value.split("\\s")) {
                    LOG.info("word: {}", word);
                    if (Objects.equals(word, "ERROR")) {
                        throw new RuntimeException("error dirty data");
                    }
                    out.collect(word);
                }
            }
        }).keyBy(new KeySelector<String, String>() {
            @Override
            public String getKey(String word) throws Exception {
                return word;
            }
        });

        // 每个并行实例缓冲4个单词输出一次
        wordStream.addSink(new BufferingSink(4));

        env.execute("CheckpointedFunctionOperatorStateExample");
    }

    public static class BufferingSink extends RichSinkFunction<String> implements CheckpointedFunction {

        private static final Logger LOG = LoggerFactory.getLogger(CheckpointedFunctionOSExample.class);

        private final int threshold;
        private transient ListState<String> statePerPartition;
        private List<String> bufferedWords;

        public BufferingSink(int threshold) {
            this.threshold = threshold;
            this.bufferedWords = new ArrayList<>();
        }

        @Override
        public void invoke(String word, Context context) {
            int subTask = getRuntimeContext().getIndexOfThisSubtask();
            bufferedWords.add(word);
            LOG.info("invoke buffer subTask: {}, words: {}", subTask, bufferedWords.toString());
            // 缓冲达到阈值输出
            if (bufferedWords.size() == threshold) {
                for (String bufferedWord: bufferedWords) {
                    // 输出
                    LOG.info("invoke sink subTask: {}, word: {}", subTask, bufferedWord);
                }
                bufferedWords.clear();
            }
        }

        @Override
        public void snapshotState(FunctionSnapshotContext context) throws Exception {
            long checkpointId = context.getCheckpointId();
            int subTask = getRuntimeContext().getIndexOfThisSubtask();
            // 清空上一次快照的状态
            statePerPartition.clear();
            // 生成新快照的状态
            for (String word : bufferedWords) {
                statePerPartition.add(word);
            }
            LOG.info("snapshotState subTask: {}, checkpointId: {}, words: {}", subTask, checkpointId, bufferedWords.toString());
        }

        @Override
        public void initializeState(FunctionInitializationContext context) throws Exception {
            ListStateDescriptor<String> descriptor = new ListStateDescriptor<>(
                    "buffered-words", TypeInformation.of(new TypeHint<String>() {}));
            statePerPartition = context.getOperatorStateStore().getListState(descriptor);
            int subTask = getRuntimeContext().getIndexOfThisSubtask();
            // 从状态中恢复
            if (context.isRestored()) {
                for (String word : statePerPartition.get()) {
                    bufferedWords.add(word);
                }
                LOG.info("initializeState subTask: {}, words: {}", subTask, bufferedWords.toString());
            }
        }
    }
}
```
为了模拟脏数据异常 Failover，在 flatMap 处理中判断出现的单词是否是 `ERROR`，如果是则抛出一个运行时异常导致作业 Failover 异常重启。在这我们实现了一个 BufferingSink，每个并发任务缓冲 4 个元素才能输出。BufferingSink 继承 RichSinkFunction 而不是 SinkFunction 的原因是想通过 RuntimeContext 获取当前执行的任务编号，从而更好的了解任务运行情况。此外还实现了 CheckpointedFunction 接口，也是本文的重点。通过实现该接口，重写 `initializeState` 方法实现作业状态的初始化以及重启时的状态恢复逻辑，重写 `snapshotState` 方法实现 Checkpoint 触发时的状态快照生成逻辑。如下所示是输入不同单词之后的具体运行信息(经过裁剪)：
```
07:59:46,713 INFO  [] - word: a
07:59:46,715 INFO  [] - invoke buffer subTask: 1, words: [a]
07:59:48,784 INFO  [] - word: b
07:59:48,869 INFO  [] - invoke buffer subTask: 0, words: [b]
07:59:50,933 INFO  [] - word: c
07:59:51,037 INFO  [] - invoke buffer subTask: 0, words: [b, c]
07:59:53,615 INFO  [] - word: d
07:59:53,708 INFO  [] - invoke buffer subTask: 1, words: [a, d]
07:59:58,254 INFO  [] - word: e
07:59:58,349 INFO  [] - invoke buffer subTask: 0, words: [b, c, e]
08:00:00,199 INFO  [] - word: f
08:00:00,284 INFO  [] - invoke buffer subTask: 0, words: [b, c, e, f]
08:00:00,285 INFO  [] - invoke sink subTask: 0, word: b
08:00:00,285 INFO  [] - invoke sink subTask: 0, word: c
08:00:00,285 INFO  [] - invoke sink subTask: 0, word: e
08:00:00,285 INFO  [] - invoke sink subTask: 0, word: f
08:00:04,698 INFO  [] - Triggering checkpoint 1
08:00:04,705 INFO  [] - snapshotState subTask: 0, checkpointId: 1, words: []
08:00:04,705 INFO  [] - snapshotState subTask: 1, checkpointId: 1, words: [a, d]
08:00:04,735 INFO  [] - Completed checkpoint 1
08:00:21,357 INFO  [] - word: g
08:00:21,457 INFO  [] - invoke buffer subTask: 0, words: [g]
08:00:34,685 INFO  [] - Triggering checkpoint 2
08:00:34,687 INFO  [] - snapshotState subTask: 0, checkpointId: 2, words: [g]
08:00:34,687 INFO  [] - snapshotState subTask: 1, checkpointId: 2, words: [a, d]
08:00:34,689 INFO  [] - Completed checkpoint 2
08:00:40,474 INFO  [] - word: ERROR
08:00:40,481 WARN  [] - Flat Map (1/2)#0 (c52dc9cc7a6e078811f67ad615fb455f) switched from RUNNING to FAILED with failure cause: java.lang.RuntimeException: error dirty data
08:00:50,571 INFO  [] - initializeState subTask: 1, words: [a, d]
08:00:50,571 INFO  [] - initializeState subTask: 0, words: [g]
08:01:03,425 INFO  [] - Triggering checkpoint 3
08:01:03,427 INFO  [] - snapshotState subTask: 0, checkpointId: 3, words: [g]
08:01:03,427 INFO  [] - snapshotState subTask: 1, checkpointId: 3, words: [a, d]
08:01:03,428 INFO  [] - Completed checkpoint 3
08:01:06,351 INFO  [] - word: h
08:01:06,421 INFO  [] - invoke buffer subTask: 0, words: [g, h]
08:01:20,985 INFO  [] - word: i
08:01:21,083 INFO  [] - invoke buffer subTask: 0, words: [g, h, i]
08:01:27,470 INFO  [] - word: j
08:01:27,575 INFO  [] - invoke buffer subTask: 1, words: [a, d, j]
08:01:33,425 INFO  [] - Triggering checkpoint 4
08:01:33,427 INFO  [] - snapshotState subTask: 0, checkpointId: 4, words: [g, h, i]
08:01:33,427 INFO  [] - snapshotState subTask: 1, checkpointId: 4, words: [a, d, j]
08:01:33,428 INFO  [] - Completed checkpoint 4
08:01:41,651 INFO  [] - word: k
08:01:41,739 INFO  [] - invoke buffer subTask: 0, words: [g, h, i, k]
08:01:41,739 INFO  [] - invoke sink subTask: 0, word: g
08:01:41,739 INFO  [] - invoke sink subTask: 0, word: h
08:01:41,739 INFO  [] - invoke sink subTask: 0, word: i
08:01:41,739 INFO  [] - invoke sink subTask: 0, word: k
08:02:03,425 INFO  [] - Triggering checkpoint 5
08:02:03,427 INFO  [] - snapshotState subTask: 0, checkpointId: 5, words: []
08:02:03,427 INFO  [] - snapshotState subTask: 1, checkpointId: 5, words: [a, d, j]
08:02:03,428 INFO  [] - Completed checkpoint 5
```
从上面可以看到 Task 0 缓冲 4 个单词 `b, c, e, f` 后就直接输出，再新单词到来之前 Checkpoint 触发快照状态中不包含任何单词。在 Task 0 缓缓了一个单词 `g`，Task 1 缓冲了 2 个单词 `a, d`，作业遇到脏数据出现异常导致作业 Failover 重启。重启之后，Task 需要初始化，Task 0 从状态中恢复一个单词 `g`，Task 1 恢复了 2 个单词 `a, d`。

## 2. ListCheckpointed

转换函数可以在不实现完整 CheckpointedFunction 接口的情况下使用 State。可以直接通过实现 ListCheckpointed 接口来访问 OperatorState。ListCheckpointed 接口是 CheckpointedFunction 的简化版，可以理解为这个接口自己本身就带了一个 ListState，所以我们不需要像 CheckpointedFunction 一样初始化一个 ListState。实现 ListCheckpointed 接口与实现 CheckpointedFunction 接口类似，同样需要实现两个方法：
```java
public interface ListCheckpointed<T extends Serializable> {
    List<T> snapshotState(long checkpointId, long timestamp) throws Exception;
    void restoreState(List<T> state) throws Exception;
}
```
`snapshotState()` 需要返回一个将写入到 checkpoint 的对象列表 List。如果 OpeartorState 中没有状态时，返回的列表会为空。如果状态不可切分，
则可以在 `snapshotState()` 中返回 `Collections.singletonList(xxx)`：
```java
public List snapshotState(long checkpointId, long timestamp) throws Exception {
    // localCount 本地 Long 型计数器
    return Collections.singletonList(localCount);
}
```
`restoreState()` 则需要处理恢复回来的对象列表，将函数或者算子的状态恢复到前一个 Checkpoint 的状态。如果函数的并行实例不恢复任何状态，则状态列表可能为空：
```java
public void restoreState(List<Long> state) throws Exception {
    for (Long count : state) {
        localCount += count;
    }
}
```
> 重要提示：当与RichFunction一起实现此接口时，在RichFunction.open(Configuration)之前调用restoreState()方法。

ListCheckpointed 只支持均匀分布的ListState，不支持全量广播的 UnionListState。实现这个接口是从 OperatorStateStore 中获取默认 ListState 的一种更快捷的方式。但是直接使用 OperatorStateStore 为使用 OperatorState 提供了更灵活的选项，例如控制状态对象的序列化，或具有多个命名状态等。

在 Flink 1.11 版本 ListCheckpointed 接口已经标注为 `@Deprecated`，即表示已经废弃，推荐使用 CheckpointedFunction 接口来代替。具体详情请查阅 [FLINK-6258](https://issues.apache.org/jira/browse/FLINK-6258)

### 示例

```
08:55:23,992 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - word: a
08:55:24,083 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - invoke buffer subTask: 1, words: [a]
08:55:24,817 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - word: b
08:55:24,893 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - invoke buffer subTask: 0, words: [b]
08:55:25,743 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - word: c
08:55:25,836 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - invoke buffer subTask: 0, words: [b, c]
08:55:26,969 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - word: d
08:55:27,055 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - invoke buffer subTask: 1, words: [a, d]
08:55:29,650 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - word: e
08:55:29,655 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - invoke buffer subTask: 0, words: [b, c, e]
08:55:30,574 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - word: f
08:55:30,630 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - invoke buffer subTask: 0, words: [b, c, e, f]
08:55:30,630 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - invoke sink subTask: 0, word: b
08:55:30,630 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - invoke sink subTask: 0, word: c
08:55:30,630 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - invoke sink subTask: 0, word: e
08:55:30,630 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - invoke sink subTask: 0, word: f
08:55:45,960 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - Triggering checkpoint 1 (type=CHECKPOINT) @ 1681952145946 for job 5a09018a62b24958656d354f31556d5d.
08:55:45,970 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - snapshotState subTask: 1, checkpointId: 1, words: [a, d]
08:55:45,971 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - snapshotState subTask: 0, checkpointId: 1, words: []
08:55:46,002 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - Completed checkpoint 1 for job 5a09018a62b24958656d354f31556d5d (374 bytes in 53 ms).
08:55:51,869 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - word: g
08:55:51,880 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - invoke buffer subTask: 0, words: [g]
08:56:15,942 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - Triggering checkpoint 2 (type=CHECKPOINT) @ 1681952175941 for job 5a09018a62b24958656d354f31556d5d.
08:56:15,943 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - snapshotState subTask: 1, checkpointId: 2, words: [a, d]
08:56:15,944 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - snapshotState subTask: 0, checkpointId: 2, words: [g]
08:56:15,946 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - Completed checkpoint 2 for job 5a09018a62b24958656d354f31556d5d (382 bytes in 3 ms).
08:56:22,247 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - word: ERROR
08:56:22,255 WARN  org.apache.flink.runtime.taskmanager.Task                    [] - Flat Map (2/2)#0 (c92d839a41f6cc8a2427cd537b5c1a0e) switched from RUNNING to FAILED with failure cause: java.lang.RuntimeException: error dirty data
	at com.flink.example.stream.function.stateful.ListCheckpointedExample$2.flatMap(ListCheckpointedExample.java:53)
	at com.flink.example.stream.function.stateful.ListCheckpointedExample$2.flatMap(ListCheckpointedExample.java:47)
	at org.apache.flink.streaming.api.operators.StreamFlatMap.processElement(StreamFlatMap.java:47)
	at org.apache.flink.streaming.runtime.tasks.OneInputStreamTask$StreamTaskNetworkOutput.emitRecord(OneInputStreamTask.java:205)
	at org.apache.flink.streaming.runtime.io.AbstractStreamTaskNetworkInput.processElement(AbstractStreamTaskNetworkInput.java:134)
	at org.apache.flink.streaming.runtime.io.AbstractStreamTaskNetworkInput.emitNext(AbstractStreamTaskNetworkInput.java:105)
	at org.apache.flink.streaming.runtime.io.StreamOneInputProcessor.processInput(StreamOneInputProcessor.java:66)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.processInput(StreamTask.java:423)
	at org.apache.flink.streaming.runtime.tasks.mailbox.MailboxProcessor.runMailboxLoop(MailboxProcessor.java:204)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.runMailboxLoop(StreamTask.java:684)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.executeInvoke(StreamTask.java:639)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.runWithCleanUpOnFail(StreamTask.java:650)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.invoke(StreamTask.java:623)
	at org.apache.flink.runtime.taskmanager.Task.doRun(Task.java:779)
	at org.apache.flink.runtime.taskmanager.Task.run(Task.java:566)
	at java.lang.Thread.run(Thread.java:748)

08:56:22,256 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Freeing task resources for Flat Map (2/2)#0 (c92d839a41f6cc8a2427cd537b5c1a0e).
08:56:22,260 INFO  org.apache.flink.runtime.taskexecutor.TaskExecutor           [] - Un-registering task and sending final execution state FAILED to JobManager for task Flat Map (2/2)#0 c92d839a41f6cc8a2427cd537b5c1a0e.
08:56:22,262 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Flat Map (2/2) (c92d839a41f6cc8a2427cd537b5c1a0e) switched from RUNNING to FAILED on 97fcaaca-6449-4c4c-896e-a57a8f923deb @ localhost (dataPort=-1).
java.lang.RuntimeException: error dirty data
	at com.flink.example.stream.function.stateful.ListCheckpointedExample$2.flatMap(ListCheckpointedExample.java:53) ~[classes/:?]
	at com.flink.example.stream.function.stateful.ListCheckpointedExample$2.flatMap(ListCheckpointedExample.java:47) ~[classes/:?]
	at org.apache.flink.streaming.api.operators.StreamFlatMap.processElement(StreamFlatMap.java:47) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.OneInputStreamTask$StreamTaskNetworkOutput.emitRecord(OneInputStreamTask.java:205) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.io.AbstractStreamTaskNetworkInput.processElement(AbstractStreamTaskNetworkInput.java:134) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.io.AbstractStreamTaskNetworkInput.emitNext(AbstractStreamTaskNetworkInput.java:105) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.io.StreamOneInputProcessor.processInput(StreamOneInputProcessor.java:66) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.StreamTask.processInput(StreamTask.java:423) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.mailbox.MailboxProcessor.runMailboxLoop(MailboxProcessor.java:204) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.StreamTask.runMailboxLoop(StreamTask.java:684) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.StreamTask.executeInvoke(StreamTask.java:639) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.StreamTask.runWithCleanUpOnFail(StreamTask.java:650) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.StreamTask.invoke(StreamTask.java:623) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.taskmanager.Task.doRun(Task.java:779) ~[flink-runtime_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.taskmanager.Task.run(Task.java:566) ~[flink-runtime_2.11-1.13.5.jar:1.13.5]
	at java.lang.Thread.run(Thread.java:748) ~[?:1.8.0_161]
08:56:22,275 INFO  org.apache.flink.runtime.executiongraph.failover.flip1.RestartPipelinedRegionFailoverStrategy [] - Calculating tasks to restart to recover the failed task 0a448493b4782967b150582570326227_1.
08:56:22,275 INFO  org.apache.flink.runtime.executiongraph.failover.flip1.RestartPipelinedRegionFailoverStrategy [] - 5 tasks should be restarted to recover the failed task 0a448493b4782967b150582570326227_1.
08:56:22,277 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Job ListCheckpointedExample (5a09018a62b24958656d354f31556d5d) switched from state RUNNING to RESTARTING.
08:56:22,277 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Source: Socket Stream (1/1) (a4329d9e22d878b816ac0db058a39a85) switched from RUNNING to CANCELING.
08:56:22,278 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Attempting to cancel task Source: Socket Stream (1/1)#0 (a4329d9e22d878b816ac0db058a39a85).
08:56:22,278 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Source: Socket Stream (1/1)#0 (a4329d9e22d878b816ac0db058a39a85) switched from RUNNING to CANCELING.
08:56:22,278 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Triggering cancellation of task code Source: Socket Stream (1/1)#0 (a4329d9e22d878b816ac0db058a39a85).
08:56:22,279 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Sink: Unnamed (2/2) (4067f93bf1b2c0ebe914c983123a5cf2) switched from RUNNING to CANCELING.
08:56:22,279 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Sink: Unnamed (1/2) (a81c8e08a66111a3881d828220c0206b) switched from RUNNING to CANCELING.
08:56:22,280 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Flat Map (1/2) (e41ef26050154db8fbe292fddea88371) switched from RUNNING to CANCELING.
08:56:22,281 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Attempting to cancel task Sink: Unnamed (2/2)#0 (4067f93bf1b2c0ebe914c983123a5cf2).
08:56:22,281 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Sink: Unnamed (2/2)#0 (4067f93bf1b2c0ebe914c983123a5cf2) switched from RUNNING to CANCELING.
08:56:22,281 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Triggering cancellation of task code Sink: Unnamed (2/2)#0 (4067f93bf1b2c0ebe914c983123a5cf2).
08:56:22,282 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Attempting to cancel task Sink: Unnamed (1/2)#0 (a81c8e08a66111a3881d828220c0206b).
08:56:22,282 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Sink: Unnamed (1/2)#0 (a81c8e08a66111a3881d828220c0206b) switched from RUNNING to CANCELING.
08:56:22,283 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Triggering cancellation of task code Sink: Unnamed (1/2)#0 (a81c8e08a66111a3881d828220c0206b).
08:56:22,284 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Attempting to cancel task Flat Map (1/2)#0 (e41ef26050154db8fbe292fddea88371).
08:56:22,285 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Flat Map (1/2)#0 (e41ef26050154db8fbe292fddea88371) switched from RUNNING to CANCELING.
08:56:22,285 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Triggering cancellation of task code Flat Map (1/2)#0 (e41ef26050154db8fbe292fddea88371).
08:56:22,286 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Sink: Unnamed (2/2)#0 (4067f93bf1b2c0ebe914c983123a5cf2) switched from CANCELING to CANCELED.
08:56:22,286 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Sink: Unnamed (1/2)#0 (a81c8e08a66111a3881d828220c0206b) switched from CANCELING to CANCELED.
08:56:22,286 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Flat Map (1/2)#0 (e41ef26050154db8fbe292fddea88371) switched from CANCELING to CANCELED.
08:56:22,286 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Freeing task resources for Sink: Unnamed (1/2)#0 (a81c8e08a66111a3881d828220c0206b).
08:56:22,286 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Freeing task resources for Flat Map (1/2)#0 (e41ef26050154db8fbe292fddea88371).
08:56:22,286 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Freeing task resources for Sink: Unnamed (2/2)#0 (4067f93bf1b2c0ebe914c983123a5cf2).
08:56:22,286 INFO  org.apache.flink.runtime.taskexecutor.TaskExecutor           [] - Un-registering task and sending final execution state CANCELED to JobManager for task Sink: Unnamed (1/2)#0 a81c8e08a66111a3881d828220c0206b.
08:56:22,286 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Source: Socket Stream (1/1)#0 (a4329d9e22d878b816ac0db058a39a85) switched from CANCELING to CANCELED.
08:56:22,286 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Freeing task resources for Source: Socket Stream (1/1)#0 (a4329d9e22d878b816ac0db058a39a85).
08:56:22,287 INFO  org.apache.flink.runtime.taskexecutor.TaskExecutor           [] - Un-registering task and sending final execution state CANCELED to JobManager for task Flat Map (1/2)#0 e41ef26050154db8fbe292fddea88371.
08:56:22,287 INFO  org.apache.flink.runtime.taskexecutor.TaskExecutor           [] - Un-registering task and sending final execution state CANCELED to JobManager for task Sink: Unnamed (2/2)#0 4067f93bf1b2c0ebe914c983123a5cf2.
08:56:22,287 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Sink: Unnamed (1/2) (a81c8e08a66111a3881d828220c0206b) switched from CANCELING to CANCELED.
08:56:22,287 INFO  org.apache.flink.runtime.taskexecutor.TaskExecutor           [] - Un-registering task and sending final execution state CANCELED to JobManager for task Source: Socket Stream (1/1)#0 a4329d9e22d878b816ac0db058a39a85.
08:56:22,288 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Flat Map (1/2) (e41ef26050154db8fbe292fddea88371) switched from CANCELING to CANCELED.
08:56:22,288 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Sink: Unnamed (2/2) (4067f93bf1b2c0ebe914c983123a5cf2) switched from CANCELING to CANCELED.
08:56:22,293 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Source: Socket Stream (1/1) (a4329d9e22d878b816ac0db058a39a85) switched from CANCELING to CANCELED.
08:56:22,293 INFO  org.apache.flink.runtime.resourcemanager.slotmanager.DeclarativeSlotManager [] - Received resource requirements from job 5a09018a62b24958656d354f31556d5d: [ResourceRequirement{resourceProfile=ResourceProfile{UNKNOWN}, numberOfRequiredSlots=1}]
08:56:22,295 INFO  org.apache.flink.runtime.resourcemanager.slotmanager.DeclarativeSlotManager [] - Clearing resource requirements of job 5a09018a62b24958656d354f31556d5d
08:56:32,290 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Job ListCheckpointedExample (5a09018a62b24958656d354f31556d5d) switched from state RESTARTING to RUNNING.
08:56:32,293 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - Restoring job 5a09018a62b24958656d354f31556d5d from Checkpoint 2 @ 1681952175941 for 5a09018a62b24958656d354f31556d5d located at <checkpoint-not-externally-addressable>.
08:56:32,306 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - No master state to restore
08:56:32,308 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Source: Socket Stream (1/1) (665c2cc5e4fdbca579e498eeb9b9d33a) switched from CREATED to SCHEDULED.
08:56:32,308 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Flat Map (1/2) (8de28abbc65de4380214211b0b065018) switched from CREATED to SCHEDULED.
08:56:32,308 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Flat Map (2/2) (9a932025b27720a918c66c20b358607c) switched from CREATED to SCHEDULED.
08:56:32,308 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Sink: Unnamed (1/2) (211611586605683dc0a8c08a3762a144) switched from CREATED to SCHEDULED.
08:56:32,308 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Sink: Unnamed (2/2) (5dd575082fda3b4c24d98d7a13081fa7) switched from CREATED to SCHEDULED.
08:56:32,309 INFO  org.apache.flink.runtime.resourcemanager.slotmanager.DeclarativeSlotManager [] - Received resource requirements from job 5a09018a62b24958656d354f31556d5d: [ResourceRequirement{resourceProfile=ResourceProfile{UNKNOWN}, numberOfRequiredSlots=1}]
08:56:32,310 INFO  org.apache.flink.runtime.resourcemanager.slotmanager.DeclarativeSlotManager [] - Received resource requirements from job 5a09018a62b24958656d354f31556d5d: [ResourceRequirement{resourceProfile=ResourceProfile{UNKNOWN}, numberOfRequiredSlots=2}]
08:56:32,311 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Source: Socket Stream (1/1) (665c2cc5e4fdbca579e498eeb9b9d33a) switched from SCHEDULED to DEPLOYING.
08:56:32,311 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Deploying Source: Socket Stream (1/1) (attempt #1) with attempt id 665c2cc5e4fdbca579e498eeb9b9d33a to 97fcaaca-6449-4c4c-896e-a57a8f923deb @ localhost (dataPort=-1) with allocation id e124f3f3bd7c97eccd994ac456046729
08:56:32,311 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Flat Map (1/2) (8de28abbc65de4380214211b0b065018) switched from SCHEDULED to DEPLOYING.
08:56:32,311 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Deploying Flat Map (1/2) (attempt #1) with attempt id 8de28abbc65de4380214211b0b065018 to 97fcaaca-6449-4c4c-896e-a57a8f923deb @ localhost (dataPort=-1) with allocation id e124f3f3bd7c97eccd994ac456046729
08:56:32,311 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Flat Map (2/2) (9a932025b27720a918c66c20b358607c) switched from SCHEDULED to DEPLOYING.
08:56:32,311 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Deploying Flat Map (2/2) (attempt #1) with attempt id 9a932025b27720a918c66c20b358607c to 97fcaaca-6449-4c4c-896e-a57a8f923deb @ localhost (dataPort=-1) with allocation id d52dc94322cde20daf53a89ad14dbf88
08:56:32,311 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Sink: Unnamed (1/2) (211611586605683dc0a8c08a3762a144) switched from SCHEDULED to DEPLOYING.
08:56:32,311 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Deploying Sink: Unnamed (1/2) (attempt #1) with attempt id 211611586605683dc0a8c08a3762a144 to 97fcaaca-6449-4c4c-896e-a57a8f923deb @ localhost (dataPort=-1) with allocation id e124f3f3bd7c97eccd994ac456046729
08:56:32,311 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Sink: Unnamed (2/2) (5dd575082fda3b4c24d98d7a13081fa7) switched from SCHEDULED to DEPLOYING.
08:56:32,311 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Deploying Sink: Unnamed (2/2) (attempt #1) with attempt id 5dd575082fda3b4c24d98d7a13081fa7 to 97fcaaca-6449-4c4c-896e-a57a8f923deb @ localhost (dataPort=-1) with allocation id d52dc94322cde20daf53a89ad14dbf88
08:56:32,316 INFO  org.apache.flink.runtime.taskexecutor.slot.TaskSlotTableImpl [] - Activate slot e124f3f3bd7c97eccd994ac456046729.
08:56:32,319 INFO  org.apache.flink.runtime.taskexecutor.TaskExecutor           [] - Received task Source: Socket Stream (1/1)#1 (665c2cc5e4fdbca579e498eeb9b9d33a), deploy into slot with allocation id e124f3f3bd7c97eccd994ac456046729.
08:56:32,320 INFO  org.apache.flink.runtime.taskexecutor.slot.TaskSlotTableImpl [] - Activate slot e124f3f3bd7c97eccd994ac456046729.
08:56:32,320 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Source: Socket Stream (1/1)#1 (665c2cc5e4fdbca579e498eeb9b9d33a) switched from CREATED to DEPLOYING.
08:56:32,320 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Loading JAR files for task Source: Socket Stream (1/1)#1 (665c2cc5e4fdbca579e498eeb9b9d33a) [DEPLOYING].
08:56:32,322 INFO  org.apache.flink.streaming.runtime.tasks.StreamTask          [] - No state backend has been configured, using default (HashMap) org.apache.flink.runtime.state.hashmap.HashMapStateBackend@61fe4b0c
08:56:32,322 INFO  org.apache.flink.streaming.runtime.tasks.StreamTask          [] - Checkpoint storage is set to 'jobmanager'
08:56:32,323 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Source: Socket Stream (1/1)#1 (665c2cc5e4fdbca579e498eeb9b9d33a) switched from DEPLOYING to INITIALIZING.
08:56:32,326 INFO  org.apache.flink.runtime.taskexecutor.TaskExecutor           [] - Received task Flat Map (1/2)#1 (8de28abbc65de4380214211b0b065018), deploy into slot with allocation id e124f3f3bd7c97eccd994ac456046729.
08:56:32,326 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Source: Socket Stream (1/1) (665c2cc5e4fdbca579e498eeb9b9d33a) switched from DEPLOYING to INITIALIZING.
08:56:32,327 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Flat Map (1/2)#1 (8de28abbc65de4380214211b0b065018) switched from CREATED to DEPLOYING.
08:56:32,327 INFO  org.apache.flink.runtime.taskexecutor.slot.TaskSlotTableImpl [] - Activate slot d52dc94322cde20daf53a89ad14dbf88.
08:56:32,328 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Loading JAR files for task Flat Map (1/2)#1 (8de28abbc65de4380214211b0b065018) [DEPLOYING].
08:56:32,329 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Source: Socket Stream (1/1)#1 (665c2cc5e4fdbca579e498eeb9b9d33a) switched from INITIALIZING to RUNNING.
08:56:32,329 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Source: Socket Stream (1/1) (665c2cc5e4fdbca579e498eeb9b9d33a) switched from INITIALIZING to RUNNING.
08:56:32,329 INFO  org.apache.flink.streaming.runtime.tasks.StreamTask          [] - No state backend has been configured, using default (HashMap) org.apache.flink.runtime.state.hashmap.HashMapStateBackend@53e17f63
08:56:32,330 INFO  org.apache.flink.streaming.runtime.tasks.StreamTask          [] - Checkpoint storage is set to 'jobmanager'
08:56:32,330 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Flat Map (1/2)#1 (8de28abbc65de4380214211b0b065018) switched from DEPLOYING to INITIALIZING.
08:56:32,330 INFO  org.apache.flink.streaming.api.functions.source.SocketTextStreamFunction [] - Connecting to server socket localhost:9100
08:56:32,330 INFO  org.apache.flink.runtime.taskexecutor.TaskExecutor           [] - Received task Flat Map (2/2)#1 (9a932025b27720a918c66c20b358607c), deploy into slot with allocation id d52dc94322cde20daf53a89ad14dbf88.
08:56:32,330 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Flat Map (1/2) (8de28abbc65de4380214211b0b065018) switched from DEPLOYING to INITIALIZING.
08:56:32,330 INFO  org.apache.flink.runtime.taskexecutor.slot.TaskSlotTableImpl [] - Activate slot e124f3f3bd7c97eccd994ac456046729.
08:56:32,331 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Flat Map (2/2)#1 (9a932025b27720a918c66c20b358607c) switched from CREATED to DEPLOYING.
08:56:32,331 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Loading JAR files for task Flat Map (2/2)#1 (9a932025b27720a918c66c20b358607c) [DEPLOYING].
08:56:32,332 INFO  org.apache.flink.runtime.taskexecutor.TaskExecutor           [] - Received task Sink: Unnamed (1/2)#1 (211611586605683dc0a8c08a3762a144), deploy into slot with allocation id e124f3f3bd7c97eccd994ac456046729.
08:56:32,332 INFO  org.apache.flink.runtime.taskexecutor.slot.TaskSlotTableImpl [] - Activate slot d52dc94322cde20daf53a89ad14dbf88.
08:56:32,332 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Sink: Unnamed (1/2)#1 (211611586605683dc0a8c08a3762a144) switched from CREATED to DEPLOYING.
08:56:32,333 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Loading JAR files for task Sink: Unnamed (1/2)#1 (211611586605683dc0a8c08a3762a144) [DEPLOYING].
08:56:32,334 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Flat Map (1/2)#1 (8de28abbc65de4380214211b0b065018) switched from INITIALIZING to RUNNING.
08:56:32,335 INFO  org.apache.flink.streaming.runtime.tasks.StreamTask          [] - No state backend has been configured, using default (HashMap) org.apache.flink.runtime.state.hashmap.HashMapStateBackend@6b4d1460
08:56:32,335 INFO  org.apache.flink.streaming.runtime.tasks.StreamTask          [] - Checkpoint storage is set to 'jobmanager'
08:56:32,334 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Flat Map (1/2) (8de28abbc65de4380214211b0b065018) switched from INITIALIZING to RUNNING.
08:56:32,335 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Sink: Unnamed (1/2)#1 (211611586605683dc0a8c08a3762a144) switched from DEPLOYING to INITIALIZING.
08:56:32,335 INFO  org.apache.flink.streaming.runtime.tasks.StreamTask          [] - No state backend has been configured, using default (HashMap) org.apache.flink.runtime.state.hashmap.HashMapStateBackend@4a337b2b
08:56:32,335 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Sink: Unnamed (1/2) (211611586605683dc0a8c08a3762a144) switched from DEPLOYING to INITIALIZING.
08:56:32,335 INFO  org.apache.flink.streaming.runtime.tasks.StreamTask          [] - Checkpoint storage is set to 'jobmanager'
08:56:32,336 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Flat Map (2/2)#1 (9a932025b27720a918c66c20b358607c) switched from DEPLOYING to INITIALIZING.
08:56:32,336 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Flat Map (2/2) (9a932025b27720a918c66c20b358607c) switched from DEPLOYING to INITIALIZING.
08:56:32,340 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Flat Map (2/2)#1 (9a932025b27720a918c66c20b358607c) switched from INITIALIZING to RUNNING.
08:56:32,341 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Flat Map (2/2) (9a932025b27720a918c66c20b358607c) switched from INITIALIZING to RUNNING.
08:56:32,341 INFO  org.apache.flink.runtime.state.heap.HeapKeyedStateBackendBuilder [] - Finished to build heap keyed state-backend.
08:56:32,341 INFO  org.apache.flink.runtime.taskexecutor.TaskExecutor           [] - Received task Sink: Unnamed (2/2)#1 (5dd575082fda3b4c24d98d7a13081fa7), deploy into slot with allocation id d52dc94322cde20daf53a89ad14dbf88.
08:56:32,341 INFO  org.apache.flink.runtime.state.heap.HeapKeyedStateBackend    [] - Initializing heap keyed state backend with stream factory.
08:56:32,342 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Sink: Unnamed (2/2)#1 (5dd575082fda3b4c24d98d7a13081fa7) switched from CREATED to DEPLOYING.
08:56:32,342 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Loading JAR files for task Sink: Unnamed (2/2)#1 (5dd575082fda3b4c24d98d7a13081fa7) [DEPLOYING].
08:56:32,343 INFO  org.apache.flink.streaming.runtime.tasks.StreamTask          [] - No state backend has been configured, using default (HashMap) org.apache.flink.runtime.state.hashmap.HashMapStateBackend@1cfcc0fd
08:56:32,343 INFO  org.apache.flink.streaming.runtime.tasks.StreamTask          [] - Checkpoint storage is set to 'jobmanager'
08:56:32,343 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Sink: Unnamed (2/2)#1 (5dd575082fda3b4c24d98d7a13081fa7) switched from DEPLOYING to INITIALIZING.
08:56:32,344 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Sink: Unnamed (2/2) (5dd575082fda3b4c24d98d7a13081fa7) switched from DEPLOYING to INITIALIZING.
08:56:32,345 INFO  org.apache.flink.runtime.state.heap.HeapKeyedStateBackendBuilder [] - Finished to build heap keyed state-backend.
08:56:32,346 INFO  org.apache.flink.runtime.state.heap.HeapKeyedStateBackend    [] - Initializing heap keyed state backend with stream factory.
08:56:32,348 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - initializeState subTask: 1, words: [a, d]
08:56:32,348 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - initializeState subTask: 0, words: [g]
08:56:32,349 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Sink: Unnamed (2/2)#1 (5dd575082fda3b4c24d98d7a13081fa7) switched from INITIALIZING to RUNNING.
08:56:32,349 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Sink: Unnamed (1/2)#1 (211611586605683dc0a8c08a3762a144) switched from INITIALIZING to RUNNING.
08:56:32,350 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Sink: Unnamed (2/2) (5dd575082fda3b4c24d98d7a13081fa7) switched from INITIALIZING to RUNNING.
08:56:32,351 INFO  org.apache.flink.runtime.executiongraph.ExecutionGraph       [] - Sink: Unnamed (1/2) (211611586605683dc0a8c08a3762a144) switched from INITIALIZING to RUNNING.
08:56:47,794 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - Triggering checkpoint 3 (type=CHECKPOINT) @ 1681952207793 for job 5a09018a62b24958656d354f31556d5d.
08:56:47,795 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - snapshotState subTask: 0, checkpointId: 3, words: [g]
08:56:47,795 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - snapshotState subTask: 1, checkpointId: 3, words: [a, d]
08:56:47,797 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - Completed checkpoint 3 for job 5a09018a62b24958656d354f31556d5d (382 bytes in 3 ms).
08:56:53,878 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - word: h
08:56:53,897 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - invoke buffer subTask: 0, words: [g, h]
08:56:55,930 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - word: i
08:56:55,954 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - invoke buffer subTask: 0, words: [g, h, i]
08:56:57,469 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - word: j
08:56:57,477 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - invoke buffer subTask: 1, words: [a, d, j]
08:57:17,793 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - Triggering checkpoint 4 (type=CHECKPOINT) @ 1681952237793 for job 5a09018a62b24958656d354f31556d5d.
08:57:17,794 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - snapshotState subTask: 0, checkpointId: 4, words: [g, h, i]
08:57:17,794 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - snapshotState subTask: 1, checkpointId: 4, words: [a, d, j]
08:57:17,795 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - Completed checkpoint 4 for job 5a09018a62b24958656d354f31556d5d (406 bytes in 2 ms).
08:57:24,066 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - word: k
08:57:24,093 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - invoke buffer subTask: 0, words: [g, h, i, k]
08:57:24,093 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - invoke sink subTask: 0, word: g
08:57:24,093 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - invoke sink subTask: 0, word: h
08:57:24,093 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - invoke sink subTask: 0, word: i
08:57:24,093 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - invoke sink subTask: 0, word: k
08:57:47,793 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - Triggering checkpoint 5 (type=CHECKPOINT) @ 1681952267792 for job 5a09018a62b24958656d354f31556d5d.
08:57:47,794 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - snapshotState subTask: 0, checkpointId: 5, words: []
08:57:47,794 INFO  com.flink.example.stream.function.stateful.ListCheckpointedExample [] - snapshotState subTask: 1, checkpointId: 5, words: [a, d, j]
08:57:47,795 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - Completed checkpoint 5 for job 5a09018a62b24958656d354f31556d5d (382 bytes in 3 ms).
```
