


### 1. 分散同一个Reducer上的不同Key

#### 1.1 增加Reducer个数

MapReduce 在做Shuffle时，默认使用HashPartitioner对数据进行分区。如果Reducer个数设置的不合理，可能造成大量不相同的Key对应的数据被分配到了同一个Reducer上，造成该Reducer所处理的数据远大于其它Reducer，从而造成数据倾斜。

这时我们可以增加Reducer的个数来提高并行度，使得原本分配到同一Reducer处理的不同Key现在发配到不同Reducer上处理，这样就可以降低原Reducer所需处理的数据量，从而缓解数据倾斜问题。

这种方式实现简单，通过调整 `mapreduce.job.reduces` 参数即可。

#### 1.2 自定义Partitioner

使用自定义的Partitioner（默认为HashPartitioner），将原本被分配到同一个Reducer的不同Key分配到不同Reducer。关于Partitioner的具体信息可以参考[Hadoop Partitioner使用教程](http://smartsi.club/2017/12/05/hadoop-mapreduce-partitioner-usage/)

上述两种方式虽然比较简单，但是适用场景少，只能将分配到同一Reducer上的不同Key分开，但是对于同一Key倾斜严重的情况该方法并不适用。该方法一般只能缓解数据倾斜，并没有彻底消除问题。从实践经验来看，其效果一般。

### 2. 分散同一个Reducer上的相同Key

如果没有聚合操作（例如，计算key对应的pv,uv），为数据量特别大的Key增加随机前/后缀，使得原来Key相同的数据变为Key不相同的数据，从而使倾斜的数据分散到不同的Reducer中，彻底解决数据倾斜问题。如果涉及聚合操作，可以使用Combiner在Map端先进行聚合再传输到Reducer中。

### 3. Join












https://www.cnblogs.com/datacloud/p/3601624.html
