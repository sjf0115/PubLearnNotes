DStream.foreachRDD对于开发而言提供了很大的灵活性，但在使用时也要避免很多常见的“坑”。通常，将数据保存到外部系统中的流程是：建立远程连接→通过连接传输数据到远程系统→关闭连接。针对这个流程我们想到了下面的程序代码：

        dstream.foreachRDD { rdd =>
          val connection = createNewConnection()            // 在Driver执行
          rdd.foreach { record =>
            connection.send(record)                            // 在Worker执行
          }
        }
在2.2节中对Spark的Worker和Driver进行了详细的介绍，我们知道在集群模式下，上述代码中的connection需要通过序列化对象的形式从Driver发送到Worker，但是connection是无法在机器之间传递的，即connection是无法序列化的，这样可能会引起_serialization errors (connection object not serializable)_的错误。为了避免这种错误，我们在Worker当中建立conenction，代码如下：

        dstream.foreachRDD { rdd =>
          rdd.foreach { record =>
            // 建立连接
            val connection = createNewConnection()
            // 发送记录
        connection.send(record)
            // 关闭连接
        connection.close()
          }
        }
上面的程序在运行时是没有问题的，但是这里我们忽略了一个严重的性能问题：在RDD的每条记录进行外部存储操作时，都需要建立和关闭连接，这个开销在大规模数据集中是很夸张的，会降低系统的吞吐量。
所以这里需要用到前面介绍的foreachPartition，即按照RDD的不同分区（partition）来遍历RDD，再在每个分区遍历每条记录。由于每个partition是运行在同一Worker之上的，不存在跨机器的网络传输，我们便可以将外部连接的建立和关闭操作在每个分区只建立一次，代码如下：

        dstream.foreachRDD { rdd =>
          rdd.foreachPartition { partitionOfRecords =>
            // partition内建立连接
        val connection = createNewConnection()
        // 发送记录
        partitionOfRecords.foreach(record => connection.send(record))
        // 关闭连接
            connection.close()
          }
        }
这样就降低了频繁建立连接的负载，通常在连接数据库时会使用连接池，把连接池的概念引入，代码优化如下：
dstream.foreachRDD { rdd =>

          rdd.foreachPartition { partitionOfRecords =>
            // 连接池是静态，惰性初始化的连接池
            al connection = ConnectionPool.getConnection()
            partitionOfRecords.foreach(record => connection.send(record))
            ConnectionPool.returnConnection(connection)
                                                      // 将连接返回连接池，以供继续使用
          }
        }
通过建立静态惰性初始化的连接池，我们可以循环获取连接，更进一步减少建立、关闭连接的开销。同数据库的连接池类似，我们这里所说的连接池同样应该是lazy的按需建立连接，并且及时地收回超时的连接。
另外值得注意的是：
● 程序中如果存在多个foreachRDD，其会顺序执行，不会同步进行。
● 因为DStream对于输出操作是惰性策略（lazy），所以假设在foreachRDD中不添加任何RDD的action操作，Spark Streaming仅仅会接收数据然后将数据丢弃。
