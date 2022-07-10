Flink 支持动态发现新的 Topic 和 Partition，但是默认并未开启，需要手动配置 `flink.partition-discovery.interval-millis` 参数来开启动态感知新 Topic 和 Partition 的时间间隔。如果没有开启，默认时间间隔 discoverIntervalMillis 为 Long.MIN_VALUE，所以 discoverIntervalMillis 要么为默认值 Long.MIN_VALUE，要么是手动设置的大于等于 0 的数。通过下面代码可以看到：
- 默认不开启，会执行 kafkaFetcher.runFetchLoop()
- 如果开启动态发现，即时间间隔大于等于0且不为 Long.MIN_VALUE，会执行 runWithPartitionDiscovery() 方法
```java
if (discoveryIntervalMillis == PARTITION_DISCOVERY_DISABLED) {
    kafkaFetcher.runFetchLoop();
} else {
    runWithPartitionDiscovery();
}
```
在这里，我们主要看启用动态发现机制的情况。启用后最终会调用 createAndStartDiscoveryLoop() 方法，启动一个单独的线程，负责以 discoveryIntervalMillis 时间间隔周期的去发现是否有新的 Topic/Partition，并传递给 KafkaFetcher。
```java
private void runWithPartitionDiscovery() throws Exception {
    final AtomicReference<Exception> discoveryLoopErrorRef = new AtomicReference<>();
    createAndStartDiscoveryLoop(discoveryLoopErrorRef);

    kafkaFetcher.runFetchLoop();

    partitionDiscoverer.wakeup();
    joinDiscoveryLoopThread();

    final Exception discoveryLoopError = discoveryLoopErrorRef.get();
    if (discoveryLoopError != null) {
        throw new RuntimeException(discoveryLoopError);
    }
}
```

通过 createAndStartDiscoveryLoop 方法来启用一个单独的线程 discoveryLoopThread。线程按照 flink.partition-discovery.interval-millis 参数配置的时间间隔周期性运行。每次循环时，总是会优先检查当前任务是否还在运行：
```java
private void createAndStartDiscoveryLoop(AtomicReference<Exception> discoveryLoopErrorRef) {
    discoveryLoopThread =
            new Thread(
                    () -> {
                        try {
                            while (running) {
                                ...
                                // Sleep 一定时间间隔
                                if (running && discoveryIntervalMillis != 0) {
                                    try {
                                        Thread.sleep(discoveryIntervalMillis);
                                    } catch (InterruptedException iex) {
                                        break;
                                    }
                                }
                            }
                        } catch (Exception e) {
                            discoveryLoopErrorRef.set(e);
                        } finally {
                            if (running) {
                                cancel();
                            }
                        }
                    },
                    "Kafka Partition Discovery for " + getRuntimeContext().getTaskNameWithSubtasks()
           );
    discoveryLoopThread.start();
}
```
线程的核心逻辑是通过 KafkaPartitionDiscoverer 的 discoverPartitions() 方法探查是否有新 Topic/Partition，从而实现动态感知新分区：
```java
final List<KafkaTopicPartition> discoveredPartitions;
try {
    // 新分区发现
    discoveredPartitions = partitionDiscoverer.discoverPartitions();
} catch (AbstractPartitionDiscoverer.WakeupException | AbstractPartitionDiscoverer.ClosedException e) {
    break;
}
if (running && !discoveredPartitions.isEmpty()) {
    kafkaFetcher.addDiscoveredPartitions(discoveredPartitions);
}
```

如何通过 discoverPartitions 发现新的 Partition，具体可以参考[]()

总结：
- 单独起一个线程按照 flink.partition-discovery.interval-millis 参数配置的时间间隔周期性探查
- 具体通过 KafkaPartitionDiscoverer 的 discoverPartitions() 方法探查是否有新 Topic/Partition
