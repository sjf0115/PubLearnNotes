


### 2. 自动背压机制

[Storm 1.0.0](http://storm.apache.org/2016/04/12/storm100-released.html)
版本引入了自动背压(automatic back pressure)。在该版本之前，对 Spout 限流的唯一方法是开启 Ack 以及设置 `topology.max.spout.pending` 参数。不建议使用这个参数进行限流的原因是这个参数比较难调整，具体取决于 Bolt 的数量。另一方面使用这个参数必须要开启 ACK ，对于不需要 At-Least-Once 处理语义的用户，这种方法也会显着降低性能。因此，非常需要自动背压机制。

Storm 1.0 版本引入了一个新的自动背压机制，该机制不再依赖于 ACK 和 `topology.max.spout.pending`，而是基于可配置的高/低水位(watermarks)进行节流，高低水位由 Task 缓冲区大小的百分比表示。如果达到高水位线，Storm 会对 Spout 进行节流，在达到低水位线时解除节流。

Storm 的背压机制独立于 Spout API 实现，因此支持现在所有的 Spout。

### 3. 工作原理

第一步我们需要了解一下背压机制的实现原理。背压机制依赖于消息缓冲区来确定 Bolt 何时负载过大。一个 Bolt 由一个执行程序线程运行，该线程有2个消息缓冲区来分发和发送消息给应用程序代码：
- `executor.receive.buffer.size(1024)`:对于一个Bolt最多能等待的消息个数。
- `executor.send.buffer.size(1024)`:最多可以缓冲多少条消息用于发送。

为了更好地理解 Storm 内部消息缓冲区以及消息如何流转，我强烈建议您阅读该[博客文章](http://www.michael-noll.com/blog/2013/06/21/understanding-storm-internal-message-buffers/)，详细介绍了不同类型的缓冲区。

背压系统依赖于 Bolt 的接收缓冲区大小。这就是为什么有水位(watermark)的概念。高低水位线定义了缓冲区多满时对 Spout 进行节流以及多空闲时解除节流：
- `backpressure.disruptor.high.watermark`:默认值为0.9，当一个 Bolt 的接收缓冲区达到90%时发送`满`的信号，对 Spout 进行节流。
- `backpressure.disruptor.low.watermark`:默认值为0.4，当一个 Bolt 的接收缓冲区降低40%时发送`不满`的信号，Spout 重新发送消息。

下图很好描述了背压机制:
![](https://jobs.one2team.com/us/wp-content/uploads/2016/04/apache-750x566.png)

### 4. 如何使用

背压机制没有使用默认参数的原因是假如我们有一个处理时间比较长的的 Bolt，一条消息通常需要处理0.1秒。在事件高峰期，Spout 很快就会填充满这些处理速度比较慢的 Bolt 的缓冲区。当我们使用默认大小1024时，一个 Bolt 不得不处理1000多条消息，每条消息花费0.1秒，在最后一条消息处理完成时已经花费100多秒。如果拓扑中的设置的元组超时时间为30秒时，会导致许多消息失败(处理超时)。

我们必须调整缓冲区的大小。如果我们不希望出现太多的超时失败，同时我们对延迟不是很敏感，我们同意元组在 Executor 接收缓冲区中不应等待超过10秒的限制。这意味着缓冲区中不得超过100条消息，我们可以设置缓冲区大小为64或128。根据经验，我们需要将 `topology.executor.send.buffer.size` 与 `topology.executor.receive.buffer.size` 保持一致。对我们来说，将缓冲区调整到适当的大小以使背压正常工作。当 Bolt 无法跟上节奏时，它会对 Spout 进行节流。

我们几乎没有提及水位线，这些似乎只有在特定场景下才有意义：
- 当 Spout 在0.9处进行节流时，这已经太晚了，一些元组仍在填充缓冲区，让高水位降低到0.8。
- 当 Spout 被节流，并且低于0.4时，Spout 会有一些延迟来获取到新数据，这会导致一些 Bolt 在一小段时间内空闲，让我们将低水位增加到0.5。

### 5. 问题

[Backpressure can cause spout to stop emitting and stall topology](https://issues.apache.org/jira/browse/STORM-1949)





参考：[HOW TO TUNE APACHE STORM’S AUTOMATIC BACK PRESSURE](https://jobs.one2team.com/us/apache-storms/)

https://blog.csdn.net/u013063153/article/details/73928150
