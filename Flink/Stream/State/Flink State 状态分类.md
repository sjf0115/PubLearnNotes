---
layout: post
author: smartsi
title: Flink State 状态分类
date: 2020-11-15 15:30:17
tags:
  - Flink

categories: Flink
permalink: flink-stream-working-with-state
---

> Flink版本：1.11

## 1. 什么是状态

### 1.1 无状态计算

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-working-with-state-1.jpg?raw=true)

首先举一个无状态计算的例子：消费延迟计算。假设现在有一个消息队列，消息队列中有一个生产者持续往消费队列写入消息，多个消费者分别从消息队列中读取消息。从图上可以看出，生产者已经写入 16 条消息，Offset 停留在 15 ；有 3 个消费者，有的消费快，而有的消费慢。消费快的已经消费了 13 条数据，消费者慢的才消费了 7、8 条数据。

如何实时统计每个消费者落后多少条数据，如图给出了输入输出的示例。可以了解到输入的时间点有一个时间戳，生产者将消息写到了某个时间点的位置，每个消费者同一时间点分别读到了什么位置。刚才也提到了生产者写入了 15 条，消费者分别读取了 10、7、12 条。那么问题来了，怎么将生产者、消费者的进度转换为右侧示意图信息呢？

consumer 0 落后了 5 条，consumer 1 落后了 8 条，consumer 2 落后了 3 条，根据 Flink 的原理，此处需进行 Map 操作。Map 首先把消息读取进来，然后分别相减，即可知道每个 consumer 分别落后了几条。Map 一直往下发，则会得出最终结果。

大家会发现，在这种模式的计算中，无论这条输入进来多少次，输出的结果都是一样的，因为单条输入中已经包含了所需的所有信息。消费落后等于生产者减去消费者。生产者的消费在单条数据中可以得到，消费者的数据也可以在单条数据中得到，所以相同输入可以得到相同输出，这就是一个无状态的计算。

### 1.2 有状态的计算

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-working-with-state-2.jpg?raw=true)

以访问日志统计量的例子进行说明，比如当前拿到一个 Nginx 访问日志，一条日志表示一个请求，记录该请求从哪里来，访问的哪个地址，需要实时统计每个地址总共被访问了多少次，也即每个 API 被调用了多少次。可以看到下面简化的输入和输出，输入第一条是在某个时间点请求 GET 了 /api/a；第二条日志记录了某个时间点 Post /api/b ;第三条是在某个时间点 GET了一个 /api/a，总共有 3 个 Nginx 日志。从这 3 条 Nginx 日志可以看出，第一条进来输出 /api/a 被访问了一次，第二条进来输出 /api/b 被访问了一次，紧接着又进来一条访问 api/a，所以 api/a 被访问了 2 次。不同的是，两条 /api/a 的 Nginx 日志进来的数据是一样的，但输出的时候结果可能不同，第一次输出 count=1 ，第二次输出 count=2，说明相同输入可能得到不同输出。输出的结果取决于当前请求的 API 地址之前累计被访问过多少次。第一条过来累计是 0 次，count = 1，第二条过来 API 的访问已经有一次了，所以 /api/a 访问累计次数 count=2。单条数据其实仅包含当前这次访问的信息，而不包含所有的信息。要得到这个结果，还需要依赖 API 累计访问的量，即状态。

这个计算模式是将数据输入算子中，用来进行各种复杂的计算并输出数据。这个过程中算子会去访问之前存储在里面的状态。另外一方面，它还会把现在的数据对状态的影响实时更新，如果输入 200 条数据，最后输出就是 200 条结果。

## 2. 使用场景

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-working-with-state-3.jpg?raw=true)

什么场景会用到状态呢？下面列举了常见的 4 种场景：
- 去重：比如上游的系统数据可能会有重复，落到下游系统时希望把重复的数据都去掉。去重需要先了解哪些数据来过，哪些数据还没有来，也就是把所有的主键都记录下来，当一条数据到来后，能够看到在主键当中是否存在。
- 窗口计算：比如统计每分钟 Nginx 日志 API 被访问了多少次。窗口是一分钟计算一次，在窗口触发前，如 08:00 ~ 08:01 这个窗口，前59秒的数据来了需要先放入内存，即需要把这个窗口之内的数据先保留下来，等到 8:01 时一分钟后，再将整个窗口内触发的数据输出。未触发的窗口数据也是一种状态。
- 机器学习/深度学习：如训练的模型以及当前模型的参数也是一种状态，机器学习可能每次都用有一个数据集，需要在数据集上进行学习，对模型进行一个反馈。
- 访问历史数据：比如与昨天的数据进行对比，需要访问一些历史数据。如果每次从外部去读，对资源的消耗可能比较大，所以也希望把这些历史数据也放入状态中做对比。

## 3. 为什么要管理状态

管理状态最直接的方式就是将数据都放到内存中，这也是很常见的做法。比如在做 WordCount 时，Word 作为输入，Count 作为输出。在计算的过程中把输入不断累加到 Count。

但对于流式作业有以下要求：
- 7*24小时运行，高可靠；
- 数据不丢不重，恰好计算一次；
- 数据实时产出，不延迟；

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-working-with-state-4.jpg?raw=true)

基于以上要求，内存的管理就会出现一些问题。由于内存的容量是有限制的。如果要做 24 小时的窗口计算，将 24 小时的数据都放到内存，可能会出现内存不足；另外，作业是 7*24，需要保障高可用，机器若出现故障或者宕机，需要考虑如何备份及从备份中去恢复，保证运行的作业不受影响；此外，考虑横向扩展，假如网站的访问量不高，统计每个 API 访问次数的程序可以用单线程去运行，但如果网站访问量突然增加，单节点无法处理全部访问数据，此时需要增加几个节点进行横向扩展，这时数据的状态如何平均分配到新增加的节点也问题之一。因此，将数据都放到内存中，并不是最合适的一种状态管理方式。

## 4. 理想的状态管理

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-working-with-state-5.jpg?raw=true)

最理想的状态管理需要满足易用、高效、可靠三点需求：
- 易用：Flink 提供了丰富的数据结构、多样的状态组织形式以及简洁的扩展接口，让状态管理更加易用；
- 高效：实时作业一般需要更低的延迟，一旦出现故障，恢复速度也需要更快；当处理能力不够时，可以横向扩展，同时在处理备份时，不影响作业本身处理性能；
- 可靠：Flink 提供了状态持久化，包括不丢不重的语义以及具备自动的容错能力，比如 HA，当节点挂掉后会自动拉起，不需要人工介入。

## 5. 状态的类型

### 5.1 Raw State 与 Managed State

Flink 有两种基本类型的状态：托管状态（Managed State）和原生状态（Raw State）。从名称中也能读出两者的区别：Managed State 是由 Flink 管理的，而 Raw State 是需要开发者自己管理的。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-working-with-state-6.jpg?raw=true)

- 从状态管理的方式上来说，Managed State 由 Flink Runtime 托管，状态可以自动存储、自动恢复的。可以在并行度发生变化时自动重新分配状态，并且还可以更好地进行内存管理；Raw State 需要用户自己管理，需要自己序列化，Flink 不知道 State 中存入的数据是什么结构，只有用户自己知道，需要最终序列化为可存储的数据结构。
- 从状态的数据结构上来说，Managed State 支持了一系列常见的数据结构，如 ValueState、ListState、MapState 等；Raw State只支持字节数组，所有状态都要转换为二进制字节数组才可以。
- 从使用场景来说，Managed State 适用于大部分场景；Raw State 只有当 Managed State 不满足使用需求时才推荐使用，比如需要自定义算子场景。

### 5.2 Keyed State 与 Operator State

Managed State 又分为两种：Keyed State 与 Operator State。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-working-with-state-7.jpg?raw=true)

#### 5.2.1 Keyed State

Keyed State 总是与 key 相对应，即每个 Key 对应一个 State，并且只能在与 KeyedStream 相关的函数和算子中使用。KeyedStream 可以通过调用 DataStream.keyBy() 来获得。而在 KeyedStream 上进行任何 Transformation 都将转变回 DataStream。

每个 Keyed State 在逻辑上只对应一个 `<并行算子实例，key>`，并且由于每个 key "只属于" 一个 Keyed Operator 的一个并行实例，我们可以简单地认为成 `<operator，key>`。

Keyed State 有很多种，如图为几种 Keyed State 之间的关系。首先 State 的子类中一级子类有 ValueState、MapState、AppendingState。AppendingState 又有一个子类 MergingState。MergingState 又分为 3 个子类分别是ListState、ReducingState、AggregatingState。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-working-with-state-8.jpg?raw=true)

这个继承关系使它们的访问方式、数据结构也存在差异：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-working-with-state-9.jpg?raw=true)

> FoldingState和FoldingStateDescriptor已经在Flink 1.4中被弃用，将来会被彻底删除。请改用AggregatingState和AggregatingStateDescriptor。

几种 Keyed State 的差异具体体现在：
- ValueState 存储单个值，比如 Wordcount，用 Word 当 Key，State 就是它的 Count。这里面的单个值可能是数值或者字符串，作为单个值，访问接口可能有两种，get 和 set。在 State 上体现的是 update(T) / T value()。
- MapState 的状态数据类型是 Map，在 State 上有 put、remove等。需要注意的是在 MapState 中的 key 和 Keyed state 中的 key 不是同一个。
- ListState 状态数据类型是 List，访问接口如 add、update 等。
- ReducingState 和 AggregatingState 与 ListState 都是同一个父类，但状态数据类型上是单个值，原因在于其中的 add 方法不是把当前的元素追加到列表中，而是把当前元素直接更新进了 Reducing 的结果中。
- AggregatingState 的区别是在访问接口，ReducingState 中 add（T）和 T get() 进去和出来的元素都是同一个类型，但在 AggregatingState 输入的类型可以与输出的的类型不同。

#### 5.2.2 Operator State

每一个并行算子实例都对应一个 Operator State。Operator State 需要支持重新分布，例如，并行度发生变化时。Operator State 并不常用，主要用于 Source 和 Sink 节点。Kafka Connector 是 Flink 中使用 Operator State 的一个很好的例子。Kafka 消费者的每个并行实例都要维护一个 topic 分区和偏移量的 map 作为其 Operator State。在并行度发生变化时，Operator State 接口支持在并行算子实例之间进行重新分配状态。可以有不同的方案来处理这个重新分配。Operator State 支持的数据结构相对较少，有 ListState、UnionListState 以及 BroadcastState。

## 6. 使用示例

> 下面我们介绍的都是 Managed State。

### 6.1 Keyed State 使用示例

在访问上，Keyed State 通过 RuntimeContext 来访问，这需要算子是一个 Rich Function。首先我们必须创建状态描述符 `StateDescriptor`，包含了状态的名字（可以创建多个状态，必须有唯一的名称，以便引用它们），状态值的类型。根据需求我们可以创建一个 ValueStateDescriptor，ListStateDescriptor，ReducingStateDescriptor 或 MapStateDescriptor，下面我们创建一个 ValueStateDescriptor：
```java
ValueStateDescriptor<Long> stateDescriptor = new ValueStateDescriptor<>("counter", Long.class);
```

第二步是注册状态：
```java
private ValueState<Long> counterState;
@Override
public void open(Configuration parameters) throws Exception {
    super.open(parameters);
    // 声明状态描述符
    ValueStateDescriptor<Long> stateDescriptor = new ValueStateDescriptor<>("counter", Long.class);
    // 注册状态
    counterState = getRuntimeContext().getState(stateDescriptor);
}
```
注册状态之后，我们就可以读取状态中的值，也可以更新状态中的值，下面实现了一个简单的计数器功能：
```java
@Override
public Long map(WeiboBehavior behavior) throws Exception {
    Long count = counterState.value();
    if (Objects.equals(count, null)) {
        count = 0L;
    }
    Long newCount = count + 1;
    counterState.update(newCount);
    System.out.println(behavior.getUid() + ":" + newCount);
    return newCount;
}
```

详细代码可以参阅:[KeyedStateExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/state/state/KeyedStateExample.java)

### 6.2 Operator State 使用示例

Operator State 需要自己实现 CheckpointedFunction 或 ListCheckpointed 接口。

> ListCheckpointed 已经废弃，不建议使用。

CheckpointedFunction 接口提供了如下两个方法：
```java
void snapshotState(FunctionSnapshotContext context) throws Exception;
void initializeState(FunctionInitializationContext context) throws Exception;
```

每当执行 checkpoint 时，会调用 snapshotState 方法。每当用户自定义函数被初始化时，或者当函数从之前的检查点恢复时，initializeState 方法被调用。因此，initializeState 方法不仅是初始化不同类型状态的地方，而且还是状态恢复的地方。

下面是一个有状态的 SinkFunction 的例子，在元素输出到外部之前先缓冲一定数据量再输出：
```java
public static class BehaviorBufferingSink implements SinkFunction<Tuple2<String, String>>, CheckpointedFunction {

    private final int threshold;
    private transient ListState<Tuple2<String, String>> statePerPartition;
    private List<Tuple2<String, String>> bufferedElements;

    public BehaviorBufferingSink(int threshold) {
        this.threshold = threshold;
        this.bufferedElements = new ArrayList<>();
    }

    @Override
    public void invoke(Tuple2<String, String> behavior, Context context) throws Exception {
        bufferedElements.add(behavior);
        // 缓冲达到阈值输出
        if (bufferedElements.size() == threshold) {
            int index = 0;
            for (Tuple2<String, String> element: bufferedElements) {
                // 输出 send it to the sink
                LOG.info(index + ": " + element.toString());
                index ++;
            }
            bufferedElements.clear();
        }
    }

    @Override
    public void snapshotState(FunctionSnapshotContext context) throws Exception {
        LOG.info("snapshotState........");
        statePerPartition.clear();
        for (Tuple2<String, String> element : bufferedElements) {
            statePerPartition.add(element);
        }
    }

    @Override
    public void initializeState(FunctionInitializationContext context) throws Exception {
        LOG.info("initializeState........");
        ListStateDescriptor<Tuple2<String, String>> descriptor = new ListStateDescriptor<>(
                "buffered-elements",
                TypeInformation.of(new TypeHint<Tuple2<String, String>>() {})
        );

        statePerPartition = context.getOperatorStateStore().getListState(descriptor);

        // 状态恢复
        if (context.isRestored()) {
            for (Tuple2<String, String> element : statePerPartition.get()) {
                bufferedElements.add(element);
            }
        }
    }
}
```

Operator State 初始化类似于 Keyed State 状态的初始化，都是使用包含状态名称和状态值类型相关信息的 StateDescriptor：
```Java
ListStateDescriptor<Tuple2<String, String>> descriptor = new ListStateDescriptor<>(
        "buffered-elements",
        TypeInformation.of(new TypeHint<Tuple2<String, String>>() {})
);

statePerPartition = context.getOperatorStateStore().getListState(descriptor);
```
初始化状态后，我们使用上下文的 isRestored 方法检查失败后是否要对状态进行恢复：
```java
if (context.isRestored()) {
    for (Tuple2<String, String> element : statePerPartition.get()) {
        bufferedElements.add(element);
    }
}
```

详细代码可以参阅:[OperatorStateExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/state/state/OperatorStateExample.java)

参考：
- [Working with State](https://ci.apache.org/projects/flink/flink-docs-release-1.11/dev/stream/state/state.html)
- [Apache Flink 零基础入门（七）：状态管理及容错机制
](https://ververica.cn/developers/state-management/)
