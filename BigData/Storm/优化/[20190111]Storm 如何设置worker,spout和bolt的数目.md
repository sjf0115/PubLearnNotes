
worker 的数量最好是服务器数量的倍数；topology 的总并发度(parallelism)最好是 worker 数量的倍数；Kafka 的分区数(partitions)最好是 Spout（特指 KafkaSpout）并发度的倍数。

worker 的完整数量是由 supervisor 配置的。每个 supervisor 会分配到一定数量的 JVM slot，你在拓扑中设置的 worker 数量就是以这个 slot 为依据进行分配的。

不建议为每个拓扑在每台机器上分配超过一个 worker。

假如有一个运行于三台 8 核服务器节点的拓扑，它的并行度为24，每个 bolt 在每台机器上分配有 8 个 executor（即每个 CPU 核心分配一个）。这种场景下，使用三个 worker （每个 worker 分配 8 个executor）相对于使用更多的 worker （比如使用 24 个 worker，为每个 executor 分别分配一个）有三点好处：

首先，在 worker 内部将数据流重新分区到不同的 executor 的操作（比如 shuffle 或者 group-by）就不会产生触发到传输 buffer 缓冲区，tuple 会直接从发送端转储到接收端的 buffer 区。这一点有很大的优势。相反，如果目标 executor 是在同一台机器的不同 worker 进程内，tuple 就需要经历“发送 -> worker 传输队列 -> 本地 socket 端口 -> 接收端 worker -> 接收端 executor”这样一个漫长的过程。虽然这个过程并不会产生网络级传输，但是在同一台机器的不同进程间的传输损耗也是很可观的。

其次，三个大的聚合器带来的大的缓存空间比 24 个小聚合器带来的小缓存空间要有用得多。因为这回降低数据倾斜造成的影响，同时提高 LRU 的性能。

最后，更少的 worker 可以有效地降低控制流的频繁变动。
