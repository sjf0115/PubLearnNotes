
在 open 方法中初始化创建 partitionDiscoverer 分区发现器：
```java
// 分区发现器
this.partitionDiscoverer = createPartitionDiscoverer(
        topicsDescriptor,
        getRuntimeContext().getIndexOfThisSubtask(),
        getRuntimeContext().getNumberOfParallelSubtasks()
);
this.partitionDiscoverer.open();
```
