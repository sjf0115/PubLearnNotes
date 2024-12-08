我们在入门示例[Spark Streaming 第一个应用程序 WordCount](https://smartsi.blog.csdn.net/article/details/127231676)中使用 `ssc.socketTextStream()` 通过 TCP 套接字连接接收文本数据。除了套接字，StreamingContext API 还提供了从文件创建 DStreams 作为输入源的方法。





对于从任何与 HDFS API 兼容的文件系统（即HDFS、S3、NFS等）上的文件读取数据，可以通过 StreamingContext 创建 DStream.fileStream[KeyClass, ValueClass, InputFormatClass]。



文件流不需要运行接收器 Recevier，因此不需要为接收文件数据分配任何内核。对于简单的文本文件，最简单的方法是 StreamingContext.textFileStream(dataDirectory)。
