Flink 实现操作 OperatorState 的有状态函数，有两种实现方式：
- 第一种是通过实现 CheckpointedFunction 接口
- 第二种是通过实现 ListCheckpointed 接口

## 1. CheckpointedFunction

CheckpointedFunction 是实现有状态转换函数的核心接口，这意味着维护状态的函数可以跨多个流记录进行处理。虽然存在更轻量级的 ListCheckpointed 接口（后面会详细解释），但该接口在管理 KeyedState 和 OperatorState 能提供最大的灵活性。在这我们主要介绍如何通过 CheckpointedFunction 接口实现操作 OperatorState 的有状态函数，实现 CheckpointedFunction 接口需要实现如下两个方法：
```java
public interface CheckpointedFunction {
    void snapshotState(FunctionSnapshotContext context) throws Exception;
    void initializeState(FunctionInitializationContext context) throws Exception;
}
```

### 2.1 initializeState

当第一次初始化函数或者因为故障重启需要从之前 Checkpoint 中恢复状态数据时会调用 `initializeState(FunctionInitializationContext)` 方法：
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

该方法提供了访问 FunctionInitializationContext 的能力，而 FunctionInitializationContext 又提供了访问 OperatorStateStore 和 KeyedStateStore 的能力。此外可以通过 `isRestored()` 来判断状态是否是从上一次执行的 Checkpoint 中恢复(如果是返回 true。对于无状态任务，该方法总是返回 false)：
```java
public interface FunctionInitializationContext extends ManagedInitializationContext {
}

public interface ManagedInitializationContext {
    boolean isRestored();
    OperatorStateStore getOperatorStateStore();
    KeyedStateStore getKeyedStateStore();
}
```
通过 `getOperatorStateStore()` 方法获取允许注册算子状态 OpeartorState 的 OperatorStateStore。通过 `getKeyedStateStore()` 方法获取允许注册键值状态 KeyedState 的 KeyedStateStore。OperatorStateStore 和 KeyedStateStore 则又提供了访问状态 State 存储数据结构的能力，例如 `org.apache.flink.api.common.state.ValueState` 或者 `org.apache.flink.api.common.state.ListState`。

### 2.2 snapshotState

每当触发 Checkpoint 生成转换函数的状态快照时就会调用 `snapshotState(FunctionSnapshotContext)` 方法。该方法提供了访问 FunctionSnapshotContext 的能力，而 FunctionSnapshotContext 又提供了访问检查点元数据的能力：
```java
public interface FunctionSnapshotContext extends ManagedSnapshotContext {}

public interface ManagedSnapshotContext {
    long getCheckpointId();
    long getCheckpointTimestamp();
}
```
通过 `getCheckpointId()` 方法获取生成快照时的检查点 ID，检查点 ID 保证了检查点之间的严格单调递增。对于完成的两个检查点 A 和 B, `ID_B > ID_A` 表示检查点 B 包含检查点 A，即检查点 B 包含的状态晚于检查点 A。通过 `getCheckpointTimestamp()` 方法返回主节点触发检查点生成快照时的时间戳。在 `snapshotState` 方法中，一般需要确保检查点数据结构（在 initialization 方法中获取）是最新的，以便生成快照。此外，函数可以作为一个 hook 与外部系统交互实现刷新/提交/同步。如下所示，通过 FunctionSnapshotContext 上下文获取检查点元数据信息，并将最新数据存储在状态中生成快照：
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

> 完整代码请查阅：[CheckpointedFunctionOSExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/function/stateful/CheckpointedFunctionOSExample.java)

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

转换函数可以在不实现完整 CheckpointedFunction 接口的情况下操作 OperatorState，而是直接通过实现 ListCheckpointed 接口来操作。ListCheckpointed 接口是 CheckpointedFunction 的简化版，可以理解为这个接口自己本身就带了一个 ListState，所以我们不需要像 CheckpointedFunction 一样初始化一个 ListState。虽然这种方式比较快捷，但是只能支持 List 类型的状态(ListState)，相比 CheckpointedFunction 灵活上稍微差一些，例如控制状态对象的序列化、具有多个命名状态等。此外 ListCheckpointed 只支持均匀分布的 ListState，不支持全量广播的 UnionListState。

实现 ListCheckpointed 接口与实现 CheckpointedFunction 接口类似，同样需要实现两个方法：
```java
public interface ListCheckpointed<T extends Serializable> {
    List<T> snapshotState(long checkpointId, long timestamp) throws Exception;
    void restoreState(List<T> state) throws Exception;
}
```

> 特别需要注意的是，在 Flink 1.11 版本 ListCheckpointed 接口已经标注为 `@Deprecated`，即表示已经废弃，推荐使用 CheckpointedFunction 接口来代替。具体详情请查阅 [FLINK-6258](https://issues.apache.org/jira/browse/FLINK-6258)

### 2.1 restoreState

`restoreState()` 定义了将函数或者算子的状态恢复到上一个成功的 Checkpoint 的状态，即如下所示需要处理恢复回来的对象列表：
```java
public void restoreState(List<Long> state) throws Exception {
    for (Long count : state) {
        localCount += count;
    }
}
```
> 从 CheckpointedFunction 和 ListCheckpointed 恢复状态方法的名字也能看出一些事情，CheckpointedFunction 下的 initializeState 不仅需要实现作业重启的状态恢复还需要实现状态的初始化，而 ListCheckpointed 下的 restoreState 仅需要实现状态恢复逻辑。

### 2.2 snapshotState

`snapshotState()` 需要返回一个将写入到 Checkpoint 的对象列表 List：
```java
public List snapshotState(long checkpointId, long timestamp) throws Exception {
    // 无需清空上一次快照的状态 直接返回 List 即可
    return bufferedWords; // List<String> bufferedWords;
}
```
如果 OpeartorState 中没有状态时，返回的列表会为空。如果状态不可切分，则可以在 `snapshotState()` 中返回 `Collections.singletonList(xxx)`：
```java
public List snapshotState(long checkpointId, long timestamp) throws Exception {
    return Collections.singletonList(count); // Long count
}
```

### 2.3 示例

下面我们还是以缓冲 4 个元素才输出的 Sink 为例，具体看一下 ListCheckpointed 是如何操作 OperatorState：
```java
public class ListCheckpointedExample {
    private static final Logger LOG = LoggerFactory.getLogger(ListCheckpointedExample.class);

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

        env.execute("ListCheckpointedExample");
    }

    // 自定义实现 ListCheckpointed
    public static class BufferingSink extends RichSinkFunction<String> implements ListCheckpointed<String> {
        private List<String> bufferedWords;
        private final int threshold;

        public BufferingSink(int threshold) {
            this.threshold = threshold;
            this.bufferedWords = new ArrayList<>();
        }

        @Override
        public void invoke(String word, Context context) throws Exception {
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
        public List snapshotState(long checkpointId, long timestamp) throws Exception {
            int subTask = getRuntimeContext().getIndexOfThisSubtask();
            LOG.info("snapshotState subTask: {}, checkpointId: {}, words: {}", subTask, checkpointId, bufferedWords.toString());
            // 无需清空上一次快照的状态 直接返回 List 即可
            return bufferedWords;
        }

        @Override
        public void restoreState(List<String> state) throws Exception {
            int subTask = getRuntimeContext().getIndexOfThisSubtask();
            // 不需要初始化 ListState
            // 从状态中恢复
            for (String word : state) {
                bufferedWords.add(word);
            }
            LOG.info("initializeState subTask: {}, words: {}", subTask, bufferedWords.toString());
        }
    }
}
```
> 完整代码请查阅： [ListCheckpointedExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/function/stateful/ListCheckpointedExample.java)

为了模拟脏数据异常 Failover，在 flatMap 处理中判断出现的单词是否是 `ERROR`，如果是则抛出一个运行时异常导致作业 Failover 异常重启。跟实现 CheckpointedFunction 接口比较类似，在这重写 `restoreState` 方法实现作业重启时的状态恢复逻辑，重写 `snapshotState` 方法实现 Checkpoint 触发时的状态快照生成逻辑。如下所示是输入不同单词之后的具体运行信息(经过裁剪)：
```
08:55:23,992 INFO  [] - word: a
08:55:24,083 INFO  [] - invoke buffer subTask: 1, words: [a]
08:55:24,817 INFO  [] - word: b
08:55:24,893 INFO  [] - invoke buffer subTask: 0, words: [b]
08:55:25,743 INFO  [] - word: c
08:55:25,836 INFO  [] - invoke buffer subTask: 0, words: [b, c]
08:55:26,969 INFO  [] - word: d
08:55:27,055 INFO  [] - invoke buffer subTask: 1, words: [a, d]
08:55:29,650 INFO  [] - word: e
08:55:29,655 INFO  [] - invoke buffer subTask: 0, words: [b, c, e]
08:55:30,574 INFO  [] - word: f
08:55:30,630 INFO  [] - invoke buffer subTask: 0, words: [b, c, e, f]
08:55:30,630 INFO  [] - invoke sink subTask: 0, word: b
08:55:30,630 INFO  [] - invoke sink subTask: 0, word: c
08:55:30,630 INFO  [] - invoke sink subTask: 0, word: e
08:55:30,630 INFO  [] - invoke sink subTask: 0, word: f
08:55:45,960 INFO  [] - Triggering checkpoint 1
08:55:45,970 INFO  [] - snapshotState subTask: 1, checkpointId: 1, words: [a, d]
08:55:45,971 INFO  [] - snapshotState subTask: 0, checkpointId: 1, words: []
08:55:46,002 INFO  [] - Completed checkpoint 1
08:55:51,869 INFO  [] - word: g
08:55:51,880 INFO  [] - invoke buffer subTask: 0, words: [g]
08:56:15,942 INFO  [] - Triggering checkpoint 2
08:56:15,943 INFO  [] - snapshotState subTask: 1, checkpointId: 2, words: [a, d]
08:56:15,944 INFO  [] - snapshotState subTask: 0, checkpointId: 2, words: [g]
08:56:15,946 INFO  [] - Completed checkpoint 2
08:56:22,247 INFO  [] - word: ERROR
08:56:22,255 WARN  [] - Flat Map (2/2)#0 (c92d839a41f6cc8a2427cd537b5c1a0e) switched from RUNNING to FAILED with failure cause: java.lang.RuntimeException: error dirty data
08:56:32,348 INFO  [] - initializeState subTask: 1, words: [a, d]
08:56:32,348 INFO  [] - initializeState subTask: 0, words: [g]
08:56:47,794 INFO  [] - Triggering checkpoint 3
08:56:47,795 INFO  [] - snapshotState subTask: 0, checkpointId: 3, words: [g]
08:56:47,795 INFO  [] - snapshotState subTask: 1, checkpointId: 3, words: [a, d]
08:56:47,797 INFO  [] - Completed checkpoint 3
08:56:53,878 INFO  [] - word: h
08:56:53,897 INFO  [] - invoke buffer subTask: 0, words: [g, h]
08:56:55,930 INFO  [] - word: i
08:56:55,954 INFO  [] - invoke buffer subTask: 0, words: [g, h, i]
08:56:57,469 INFO  [] - word: j
08:56:57,477 INFO  [] - invoke buffer subTask: 1, words: [a, d, j]
08:57:17,793 INFO  [] - Triggering checkpoint 4
08:57:17,794 INFO  [] - snapshotState subTask: 0, checkpointId: 4, words: [g, h, i]
08:57:17,794 INFO  [] - snapshotState subTask: 1, checkpointId: 4, words: [a, d, j]
08:57:17,795 INFO  [] - Completed checkpoint 4
08:57:24,066 INFO  [] - word: k
08:57:24,093 INFO  [] - invoke buffer subTask: 0, words: [g, h, i, k]
08:57:24,093 INFO  [] - invoke sink subTask: 0, word: g
08:57:24,093 INFO  [] - invoke sink subTask: 0, word: h
08:57:24,093 INFO  [] - invoke sink subTask: 0, word: i
08:57:24,093 INFO  [] - invoke sink subTask: 0, word: k
08:57:47,793 INFO  [] - Triggering checkpoint 5
08:57:47,794 INFO  [] - snapshotState subTask: 0, checkpointId: 5, words: []
08:57:47,794 INFO  [] - snapshotState subTask: 1, checkpointId: 5, words: [a, d, j]
08:57:47,795 INFO  [] - Completed checkpoint 5
```
输出信息跟 CheckpointedFunction 的基本一致。
