
开启 MiniBatch 提升吞吐

在 Blink 中存在两种微批处理机制：MicroBatch 和 MiniBatch。它们只是微批的触发机制略有不同。原理同样是缓存一定的数据后再触发处理，以减少对 State 的访问，从而提升吞吐并减少数据的输出量。

MiniBatch 主要依靠在每个 Task 上注册的 Timer 线程来触发微批，需要消耗一定的线程调度性能。MicroBatch 是 MiniBatch 的升级版，主要基于事件消息来触发微批，事件消息会按您指定的时间间隔在源头插入。MicroBatch 在元素序列化效率、反压表现、吞吐和延迟性能上都要优于 MiniBatch。

在 Flink 中只有类似 MicroBatch 机制的微批处理，也叫 MiniBatch。


## 2. 适用场景

微批处理通过增加延迟换取高吞吐，如果您有超低延迟的要求，不建议开启微批处理。通常对于聚合的场景，微批处理可以显著的提升系统性能，建议开启。

## 3. 使用

MiniBatch 默认关闭，开启方式如下：
```java
// 开启 MiniBatch
Configuration configuration = tEnv.getConfig().getConfiguration();
configuration.setString("table.exec.mini-batch.enabled", "true");
configuration.setString("table.exec.mini-batch.allow-latency", "1 s");
configuration.setString("table.exec.mini-batch.size", "5000");
```
