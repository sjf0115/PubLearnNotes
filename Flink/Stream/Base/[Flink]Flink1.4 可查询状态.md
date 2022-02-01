---
layout: post
author: sjf0115
title: Flink1.4 可查询状态
date: 2018-01-26 19:11:17
tags:
  - Flink
  - Flink 容错

categories: Flink
permalink: flink-stream-queryable-state
---

备注:
```
可查询状态的客户端API目前处于迭代状态，对提供的接口的稳定性没有任何保证。在即将到来的Flink版本中，API很可能会在客户端方面发生较大更改。
```

简而言之，该功能向外界公开了`Flink`的`Managed State`（分区）状态（请参见[使用状态](https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/stream/state/state.html)），并允许用户从`Flink`外部查询作业的状态。在某些情况下，可查询状态消除了与外部系统（例如在实践中常常是瓶颈的键值存储）的分布式操作/事务的需要(queryable state eliminates the need for distributed operations/transactions with external systems such as key-value stores which are often the bottleneck in practice)。另外，这个功能对于调试帮助很大。

当查询状态对象时，可以使用没有同步或复制的并发线程访问该对象。因为上述任何都会导致作业延迟增加，这是我们想避免的。由于任何使用`Java`堆空间的状态后端，例如 `MemoryStateBackend` 或 `FsStateBackend` 在检索值时不能使用副本，而是直接引用存储的值，`读取-修改-写入`模式并不安全，并且可能导致可查询状态服务器由于并发修改而产生故障。`RocksDBStateBackend`是不会存在上述问题。


### 1. 架构

在展示如何使用可查询状态之前，简要描述一下它的组成部分。可查询状态功能由三个主要实体组成：
- `QueryableStateClient`在`Flink`集群之外运行并提交用户查询
- `QueryableStateClientProxy`，运行在每个`TaskManager`上（即在`Flink`集群内部运行），负责接收客户端的查询，从负责的`TaskManager`上获取请求的状态，并将其返回给客户端
- `QueryableStateServer`运行在每个`TaskManager`上，负责提供本地存储的状态。

简而言之，客户端将连接到其中一个代理服务器，并发送与特定键相关联的状态请求。正如在[使用状态]()中所述，`Keyed State`是在`Key Groups`中组织的，并且每个`TaskManager`都被分配了一些`Key Groups`。要发现哪个`TaskManager`负责的`Key Groups`持有`k`，代理将询问所在的`JobManager`。根据答复，代理将查询在该`TaskManager`上运行的`QueryableStateServer`以查找与`k`相关联的状态，并将响应转发回客户端。

### 2. 启用可查询状态

要在你的`Flink`集群上启用可查询状态，你只需将`Flink`发行版的`opt/`文件夹下的的`flink-queryable-state-runtime_2.11-1.4.0.jar`复制到`lib/`文件夹即可。否则，可查询状态功能不会启用。

要验证群集是否在启用了可查询状态的情况下运行，请检查任何任务管理器的日志是否有："Started the Queryable State Proxy Server @ ..."。

### 3. 使状态可查询

现在你已经在你的集群上启动了可查询状态，现在该看看如何使用它了。为了使状态对外部可见，需要通过使用以下内容明确地进行查询：
- 或者使用`QueryableStateStream`，作为一个接收器，并可以将传入值(incoming values)作为可查询状态的便利对象
- 或者使用`stateDescriptor.setQueryable（String queryableStateName）`方法，它使状态描述符表示的`Keyed State`成为可查询的。
以下部分解释了这两种方法的用法。

#### 3.1 可查询状态Stream

在`KeyedStream上`调用`.asQueryableState（stateName，stateDescriptor）`将返回一个`QueryableStateStream`，它提供了可查询状态的值。根据状态的类型，`asQueryableState（）`方法有以下几种变体：
```
// ValueState
QueryableStateStream asQueryableState(String queryableStateName, ValueStateDescriptor stateDescriptor)

// Shortcut for explicit ValueStateDescriptor variant
QueryableStateStream asQueryableState(String queryableStateName)

// FoldingState
QueryableStateStream asQueryableState(String queryableStateName, FoldingStateDescriptor stateDescriptor)

// ReducingState
QueryableStateStream asQueryableState(String queryableStateName, ReducingStateDescriptor stateDescriptor)
```

备注:
```
没有可查询的ListState接收器，因为它会导致不断增长的列表，这些列表可能不会被清理，因此最终会消耗太多的内存。
```

返回的`QueryableStateStream`可以看作是一个接收器，不能进一步转换。在内部，`QueryableStateStream`被转换为一个算子，该算子使用所有传入记录来更新可查询状态实例。更新逻辑由`asQueryableState`中`StateDescriptor`的类型所表示。在类似下面的程序中，`Keyed State`的所有记录将被用来通过`ValueState.update（value）`更新状态实例：
```
stream.keyBy(0).asQueryableState("query-name")
```

#### 3.2 Managed Keyed State

通过使用`StateDescriptor.setQueryable（String queryableStateName）`使状态描述符可以查询，从而使一个算子的`Managed Keyed State`可查询（请参阅使用[Managed Keyed State](https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/stream/state/state.html#using-managed-keyed-state)），如下例所示：
```
ValueStateDescriptor<Tuple2<Long, Long>> descriptor =
        new ValueStateDescriptor<>(
                "average", // the state name
                TypeInformation.of(new TypeHint<Tuple2<Long, Long>>() {}), // type information
                Tuple2.of(0L, 0L)); // default value of the state, if nothing was set
descriptor.setQueryable("query-name"); // queryable state name
```

备注:
```
queryableStateName参数名称可以任意选择，仅是为了查询使用。它不必与状态的名字相同。
```

这个变体对于可以查询哪种类型的状态没有限制。这意味着，这可以用于任何`ValueState`， `ReduceState`， `ListState`， `MapState`， `AggregatingState` 和当前弃用的 `FoldingState`。

### 4 . 查询状态

到目前为止，你已经将你的集群配置为以可查询状态运行，并且已声明（某些）你的状态为可查询状态。现在该看看如何查询这个状态了。

为此，你可以使用`QueryableStateClient`辅助类。这可以在`flink-queryable-state-client jar`中获取，你必须在项目的`pom.xml`中明确地包含一个依赖项，如下所示：
```
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-queryable-state-client-java__2.11</artifactId>
  <version>1.4.0</version>
</dependency>
```
`QueryableStateClient`会将你的查询提交给内部代理，然后内部代理将处理你的查询并返回最终结果。初始化客户端的唯一要求是提供有效的`TaskManager`主机名（请记住，每个`TaskManager`上都有一个可查询的状态代理）以及代理监听的端口。更多关于如何配置代理和状态服务器端口的信息可以在[配置部分](https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/stream/state/queryable_state.html#Configuration)查阅。
```
QueryableStateClient client = new QueryableStateClient(tmHostname, proxyPort);
```
在客户端准备就绪的情况下，要查询一个键（类型为`K`）相关联的的状态（类型为`V`），可以使用以下方法：
```
CompletableFuture<S> getKvState(
    final JobID jobId,
    final String queryableStateName,
    final K key,
    final TypeInformation<K> keyTypeInfo,
    final StateDescriptor<S, V> stateDescriptor)
```
上面的方法返回一个`CompletableFuture`，保存了由作业ID为`jobID`的`queryableStateName`标识的可查询状态实例的状态值。`key`是你感兴趣状态的`key`，`keyTypeInfo`会告诉`Flink`如何序列化/反序列化它。最后，`stateDescriptor`包含有关请求状态的必要信息，即其类型（Value，Reduce等）以及有关如何序列化/反序列化的必要信息。

仔细的读者将会注意到，返回的`future`将包含一个`S`类型的值，即一个包含实际值的`State`对象。这可以是`Flink`支持的任何状态类型：`ValueState`， `ReduceState`， `ListState`， `MapState`， `AggregatingState`和当前不推荐使用的`FoldingState`。

这些状态对象不允许修改包含的状态。你可以使用它们来获取状态的实际值，例如 使用 `valueState.get（）` 或迭代其包含的 `<K，V>` 条目，例如使用`mapState.entries（）`，就是不能修改它们。例如，在返回的列表状态中调用`add（）`方法将引发`UnsupportedOperationException`异常。

客户端是异步的，可以被多个线程共享。 它需要通过`QueryableStateClient.shutdown（）`在未使用时关闭以释放资源。

#### 4.1 Example

以下示例通过使`CountWindowAverage`示例演示可查询并显示如何查询值：
```java
public class CountWindowAverage extends RichFlatMapFunction<Tuple2<Long, Long>, Tuple2<Long, Long>> {

    private transient ValueState<Tuple2<Long, Long>> sum; // a tuple containing the count and the sum

    @Override
    public void flatMap(Tuple2<Long, Long> input, Collector<Tuple2<Long, Long>> out) throws Exception {
        Tuple2<Long, Long> currentSum = sum.value();
        currentSum.f0 += 1;
        currentSum.f1 += input.f1;
        sum.update(currentSum);

        if (currentSum.f0 >= 2) {
            out.collect(new Tuple2<>(input.f0, currentSum.f1 / currentSum.f0));
            sum.clear();
        }
    }

    @Override
    public void open(Configuration config) {
        ValueStateDescriptor<Tuple2<Long, Long>> descriptor =
                new ValueStateDescriptor<>(
                        "average", // the state name
                        TypeInformation.of(new TypeHint<Tuple2<Long, Long>>() {}), // type information
                        Tuple2.of(0L, 0L)); // default value of the state, if nothing was set
        descriptor.setQueryable("query-name");
        sum = getRuntimeContext().getState(descriptor);
    }
}
```
一旦在作业中使用，你可以检索作业ID，然后从该算子中查询出任何键的当前状态：
```java
QueryableStateClient client = new QueryableStateClient(tmHostname, proxyPort);

// the state descriptor of the state to be fetched.
ValueStateDescriptor<Tuple2<Long, Long>> descriptor =
        new ValueStateDescriptor<>(
          "average",
          TypeInformation.of(new TypeHint<Tuple2<Long, Long>>() {}),
          Tuple2.of(0L, 0L));

CompletableFuture<ValueState<Tuple2<Long, Long>>> resultFuture =
        client.getKvState(jobId, "query-name", key, BasicTypeInfo.LONG_TYPE_INFO, descriptor);

// now handle the returned value
resultFuture.thenAccept(response -> {
        try {
            Tuple2<Long, Long> res = response.get();
        } catch (Exception e) {
            e.printStackTrace();
        }
});
```

### 5. 配置

以下配置参数影响可查询状态服务器和客户端的行为。它们在`QueryableStateOptions`中定义。

(1) State Server
- `query.server.ports`：可查询状态服务器的服务器端口范围。如果多个`TaskManager`在同一台机器上运行，这对于避免端口冲突非常有用。指定的范围可以是：(a) 端口：`9123`， (c) 端口范围：`50100-50200`，(c) 端口范围或具体端口的列表：`50100-50200,50300-50400,51234`。默认端口是`9067`。
- `query.server.network-threads`：接收传入状态服务器请求的网络（事件循环）线程数（0 => #slots）
- `query.server.query-threads`：处理/服务传入状态服务器请求的线程数（0 => #slots）。

(2) Proxy
- `query.proxy.ports`：可查询状态代理的服务器端口范围。如果多个`TaskManager`在同一台机器上运行，这对于避免端口冲突非常有用。指定的范围可以是：(a) 端口：`9123`， (b) 端口范围：`50100-50200`， (c) 端口范围或具体端口的列表：`50100-50200,50300-50400,51234`。默认端口是`9069`。
- `query.proxy.network-threads`：接收传入客户端代理的请求的网络（事件循环）线程数（0 => #slots）
- `query.proxy.query-threads`：处理/服务传入客户端代理的请求的线程数（0 => #slots）。

(3) 使用限制
- 可查询的状态生命周期必然与作业的生命周期有关。例如，任务在启动时注册可查询状态，并在清除时取消注册。在将来的版本中，为了在任务完成之后允许查询并且通过状态副本来加速恢复，希望解耦这个。
- 关于可用的`KvState`的通知通过简单的告诉你发生。在未来，这应该被改进。
- 服务器和客户端跟踪查询的统计信息。这些目前默认是禁用的，因为它们不会暴露在任何地方。只要通过指标系统对发布指标有更好的支持，我们应该启用统计信息。

备注：
```
Flink版本:1.4
```

原文:https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/stream/state/queryable_state.html
