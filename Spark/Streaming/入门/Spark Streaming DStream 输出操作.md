> Spark 版本：3.1.3

输出操作允许将 DStream 的数据推送到外部系统，例如数据库或者文件系统。由于输出操作实际上让外部系统消费转换操作后的数据，所以它们会触发 DStream 所有转换操作的实际执行（类似于 RDD 的动作操作）。 目前，定义了以下输出操作：

函数 | 描述
---|---
print() | 在运行流应用程序的 Driver 节点上打印 DStream 每个批次中的前十个元素。这对开发和调试很有帮助。在 Python API 中为 `pprint()`
saveAsTextFiles(prefix, [suffix]) | 将此 DStream 的内容另存为文本文件。每个批处理间隔的文件名是根据前缀和后缀`prefix-TIME_IN_MS [.suffix]`生成的
saveAsObjectFiles(prefix, [suffix])|将此DStream的内容保存为Java对象序列化后的SequenceFiles。每个批处理间隔的文件名是根据前缀和后缀`prefix-TIME_IN_MS [.suffix]`生成的．这在Python API中是不可用的
saveAsHadoopFiles(prefix, [suffix])|将此DStream的内容另存为Hadoop文件。每个批处理间隔的文件名是根据前缀和后缀`prefix-TIME_IN_MS [.suffix]`生成的
foreachRDD(func)|这是最常用的输出操作，接收一个函数`func`，`func`应用到从流生成的每个RDD上。该函数将每个RDD中的数据推送到外部系统，例如将RDD保存到文件，或将其通过网络写入数据库。请注意，函数`func`在运行流应用程序的驱动程序进程中执行，通常会在其中包含RDD动作操作，强制流式RDD计算。


输出操作指定了流数据经转换操作得到的数据所要执行的操作．与RDD中的惰性求值类似，如果一个DStream以及派生的DStream都没有被执行输出操作，那么这些DStream就都不会被求值．如果StreamingContext中没有设定输出操作，整个context就都不会启动．

## 1. print

print 输出操作在运行流应用程序的 Driver 节点上打印 DStream 每个批次中的前十个元素。

## 2. saveAsTextFiles



## 3. saveAsObjectFiles

## 4. saveAsHadoopFiles

## 5. foreachRDD


### 使用foreachRDD的设计模式

`DStream.foreachRDD`是一个非常强大的原生工具函数，允许将数据推送到外部系统中。不过重要的是用户需要了解如何正确而高效地使用这个函数。以下列举了一些常见的错误。

通常，对外部系统写入数据需要一些连接对象（如：连接远程服务器的TCP连接），使用它发送数据给远程系统。因此，开发人员可能会不经意地在Spark驱动器程序中创建一个连接对象，然后又试图在Spark工作节点上使用这个连接。如下例所示：

Java版：
```
dstream.foreachRDD(new VoidFunction<JavaRDD<String>>() {
  @Override
  public void call(JavaRDD<String> rdd) {
    final Connection connection = createNewConnection(); // executed at the driver
    rdd.foreach(new VoidFunction<String>() {
      @Override
      public void call(String record) {
        connection.send(record); // executed at the worker
      }
    });
  }
});
```
Scala版：
```
dstream.foreachRDD { rdd =>
  val connection = createNewConnection()  // executed at the driver
  rdd.foreach { record =>
    connection.send(record) // executed at the worker
  }
}
```
Python版:
```
def sendRecord(rdd):
    connection = createNewConnection()  # executed at the driver
    rdd.foreach(lambda record: connection.send(record))
    connection.close()

dstream.foreachRDD(sendRecord)
```

上述代码是错误的，因为需要将连接对象序列化，并从驱动器节点发送到工作节点。而这些连接对象通常都是不能跨节点传递的。比如，此错误可能为序列化错误(连接对象通常不能序列化)，或者初始化错误(连接对象通常需要在工作接节点上初始化)等等．解决此类错误的办法就是在工作节点上创建连接对象。

但是，这可能会导致另一个常见的错误 - 为每个记录创建一个新的连接。 例如：
Java版：
```
dstream.foreachRDD(new VoidFunction<JavaRDD<String>>() {
  @Override
  public void call(JavaRDD<String> rdd) {
    rdd.foreach(new VoidFunction<String>() {
      @Override
      public void call(String record) {
        Connection connection = createNewConnection();
        connection.send(record);
        connection.close();
      }
    });
  }
});
```
Scala版:
```
dstream.foreachRDD { rdd =>
  rdd.foreach { record =>
    val connection = createNewConnection()
    connection.send(record)
    connection.close()
  }
}
```
Python版：
```
def sendRecord(record):
    connection = createNewConnection()
    connection.send(record)
    connection.close()

dstream.foreachRDD(lambda rdd: rdd.foreach(sendRecord))
```
通常，创建连接对象具有时间和资源开销。因此，创建和销毁每个记录的连接对象可能会引起不必要的高开销，并可能显著降低系统的总体吞吐量。一个更好的解决方案是使用`rdd.foreachPartition` - 创建一个连接对象，并使用该连接在一个RDD分区中发送所有记录：

Java版：
```
dstream.foreachRDD(new VoidFunction<JavaRDD<String>>() {
  @Override
  public void call(JavaRDD<String> rdd) {
    rdd.foreachPartition(new VoidFunction<Iterator<String>>() {
      @Override
      public void call(Iterator<String> partitionOfRecords) {
        Connection connection = createNewConnection();
        while (partitionOfRecords.hasNext()) {
          connection.send(partitionOfRecords.next());
        }
        connection.close();
      }
    });
  }
});
```
Scala版：
```
dstream.foreachRDD { rdd =>
  rdd.foreachPartition { partitionOfRecords =>
    val connection = createNewConnection()
    partitionOfRecords.foreach(record => connection.send(record))
    connection.close()
  }
}
```
Python版：
```
def sendPartition(iter):
    connection = createNewConnection()
    for record in iter:
        connection.send(record)
    connection.close()

dstream.foreachRDD(lambda rdd: rdd.foreachPartition(sendPartition))
```
这样可以在多个记录上分摊连接的创建开销。

最后，可以通过在多个RDD /批次之间重复使用连接对象来进一步优化。可以维护连接对象的静态池(连接池)，这样多个批次的RDD推送到外部系统时可以重复使用，从而进一步减少开销：
Java版：
```
dstream.foreachRDD(new VoidFunction<JavaRDD<String>>() {
  @Override
  public void call(JavaRDD<String> rdd) {
    rdd.foreachPartition(new VoidFunction<Iterator<String>>() {
      @Override
      public void call(Iterator<String> partitionOfRecords) {
        // ConnectionPool is a static, lazily initialized pool of connections
        Connection connection = ConnectionPool.getConnection();
        while (partitionOfRecords.hasNext()) {
          connection.send(partitionOfRecords.next());
        }
        ConnectionPool.returnConnection(connection); // return to the pool for future reuse
      }
    });
  }
});
```
Scala版：
```
dstream.foreachRDD { rdd =>
  rdd.foreachPartition { partitionOfRecords =>
    // ConnectionPool is a static, lazily initialized pool of connections
    val connection = ConnectionPool.getConnection()
    partitionOfRecords.foreach(record => connection.send(record))
    ConnectionPool.returnConnection(connection)  // return to the pool for future reuse
  }
}
```
Pyton版：
```
def sendPartition(iter):
    # ConnectionPool is a static, lazily initialized pool of connections
    connection = ConnectionPool.getConnection()
    for record in iter:
        connection.send(record)
    # return to the pool for future reuse
    ConnectionPool.returnConnection(connection)

dstream.foreachRDD(lambda rdd: rdd.foreachPartition(sendPartition))
```
注意，连接池中的连接应该是根据需要惰性创建的，如果长时间段不使用，则会失效(timed out if not used for a while. )。这个是目前发送数据到外部系统最有效的方式。

==其他注意点==

- DStreams通过输出操作惰性执行的，就像RDD由RDD动作操作惰性的执行。具体来说，DStream输出操作中的RDD动作操作强制处理接收到的数据。因此，如果你的应用程序没有任何输出操作，或者有类似`dstream.foreachRDD()`的输出操作，而在其中没有任何RDD动作操作，则不会执行任何操作。系统将简单地接收数据，然后丢弃。
- 默认情况下，输出操作是一次执行一个的。它们按照它们在应用程序中定义的顺序执行。


原文：[Output Operations on DStreams](https://archive.apache.org/dist/spark/docs/3.1.3/streaming-programming-guide.html#output-operations-on-dstreams)
