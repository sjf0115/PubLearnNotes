`DStream.foreachRDD` 对于开发而言提供了很大的灵活性，但在使用时也要避免很多常见的"坑"。在这篇文章中我们会一步一步的介绍如何使用 `DStream.foreachRDD` 实现与外部存储系统交互(例如，MySQL)。通常，将数据保存到外部系统中的一般是：建立连接、通过连接传输数据到外部存储系统、关闭连接。针对这个流程我们很自然的想到与外部存储系统交互如下所示：
```java
dStream.foreachRDD(new VoidFunction<JavaRDD<String>>() {
    @Override
    public void call(JavaRDD<String> rdd) throws Exception {
        // 1. 通过连接池获取连接
        DruidDataSource dataSource = DruidConfig.getDataSource();
        DruidPooledConnection connection = dataSource.getConnection(); // 在 Driver 上执行
        // 2. 遍历 RDD 通过连接与外部存储系统交互
        rdd.foreach(new VoidFunction<String>() {
            @Override
            public void call(String record) throws Exception {
                String[] params = record.split(",");
                String sql = "INSERT INTO tb_user (id, name, age, email) VALUES (?, ?, ?, ?)";
                PreparedStatement stmt = null;
                try {
                    stmt = connection.prepareStatement(sql); // 在 Worker 上执行
                    // 设置参数并执行插入操作
                    stmt.setInt(1, Integer.parseInt(params[0]));
                    stmt.setString(2, params[1]);
                    stmt.setInt(3, Integer.parseInt(params[2]));
                    stmt.setString(4, params[3]);
                    stmt.executeUpdate();
                } catch (Exception e) {
                    LOG.error("与外部存储系统交互失败：" + e.getMessage());
                } finally {
                    if (stmt != null) {
                        stmt.close();
                    }
                }
            }
        });
        // 3. 关闭连接
        if(connection != null) {
            connection.close();
        }
    }
});
```
我们知道在集群模式下，上述代码中的 connection 需要通过序列化对象的形式从 Driver 发送到 Worker，但是 connection 是无法序列化，无法在机器之间传递的。这样可能会引起 `object not serializable` 的错误：
```java
24/12/21 18:33:50 ERROR JobScheduler: Error running job streaming job 1734777230000 ms.0
org.apache.spark.SparkException: Task not serializable
	at org.apache.spark.util.ClosureCleaner$.ensureSerializable(ClosureCleaner.scala:416)
	...
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
	at java.lang.Thread.run(Thread.java:748)
Caused by: java.io.NotSerializableException: com.alibaba.druid.pool.DruidPooledConnection
Serialization stack:
	- object not serializable (class: com.alibaba.druid.pool.DruidPooledConnection, value: com.mysql.cj.jdbc.ConnectionImpl@4267bcd0)
	- field (class: com.spark.example.streaming.connector.mysql.DataBaseSinkExample$1$1, name: val$connection, type: class com.alibaba.druid.pool.DruidPooledConnection)
	- object (class com.spark.example.streaming.connector.mysql.DataBaseSinkExample$1$1, com.spark.example.streaming.connector.mysql.DataBaseSinkExample$1$1@2b3c85a8)
	- element of array (index: 0)
	- array (class [Ljava.lang.Object;, size 1)
	- field (class: java.lang.invoke.SerializedLambda, name: capturedArgs, type: class [Ljava.lang.Object;)
	- object (class java.lang.invoke.SerializedLambda, SerializedLambda[capturingClass=interface org.apache.spark.api.java.JavaRDDLike, functionalInterfaceMethod=scala/Function1.apply:(Ljava/lang/Object;)Ljava/lang/Object;, implementation=invokeStatic org/apache/spark/api/java/JavaRDDLike.$anonfun$foreach$1$adapted:(Lorg/apache/spark/api/java/function/VoidFunction;Ljava/lang/Object;)Ljava/lang/Object;, instantiatedMethodType=(Ljava/lang/Object;)Ljava/lang/Object;, numCaptured=1])
	- writeReplace data (class: java.lang.invoke.SerializedLambda)
	- object (class org.apache.spark.api.java.JavaRDDLike$$Lambda$1269/1560726547, org.apache.spark.api.java.JavaRDDLike$$Lambda$1269/1560726547@4d1feaa1)
	at org.apache.spark.serializer.SerializationDebugger$.improveException(SerializationDebugger.scala:41)
	at org.apache.spark.serializer.JavaSerializationStream.writeObject(JavaSerializer.scala:47)
	at org.apache.spark.serializer.JavaSerializerInstance.serialize(JavaSerializer.scala:101)
	at org.apache.spark.util.ClosureCleaner$.ensureSerializable(ClosureCleaner.scala:413)
	... 31 more
Exception in thread "main" org.apache.spark.SparkException: Task not serializable
	...
	at java.lang.Thread.run(Thread.java:748)
Caused by: java.io.NotSerializableException: com.alibaba.druid.pool.DruidPooledConnection
Serialization stack:
	- object not serializable (class: com.alibaba.druid.pool.DruidPooledConnection, value: com.mysql.cj.jdbc.ConnectionImpl@4267bcd0)
	- field (class: com.spark.example.streaming.connector.mysql.DataBaseSinkExample$1$1, name: val$connection, type: class com.alibaba.druid.pool.DruidPooledConnection)
	- object (class com.spark.example.streaming.connector.mysql.DataBaseSinkExample$1$1, com.spark.example.streaming.connector.mysql.DataBaseSinkExample$1$1@2b3c85a8)
	- element of array (index: 0)
	- array (class [Ljava.lang.Object;, size 1)
	- field (class: java.lang.invoke.SerializedLambda, name: capturedArgs, type: class [Ljava.lang.Object;)
	- object (class java.lang.invoke.SerializedLambda, SerializedLambda[capturingClass=interface org.apache.spark.api.java.JavaRDDLike, functionalInterfaceMethod=scala/Function1.apply:(Ljava/lang/Object;)Ljava/lang/Object;, implementation=invokeStatic org/apache/spark/api/java/JavaRDDLike.$anonfun$foreach$1$adapted:(Lorg/apache/spark/api/java/function/VoidFunction;Ljava/lang/Object;)Ljava/lang/Object;, instantiatedMethodType=(Ljava/lang/Object;)Ljava/lang/Object;, numCaptured=1])
	- writeReplace data (class: java.lang.invoke.SerializedLambda)
	- object (class org.apache.spark.api.java.JavaRDDLike$$Lambda$1269/1560726547, org.apache.spark.api.java.JavaRDDLike$$Lambda$1269/1560726547@4d1feaa1)
	at org.apache.spark.serializer.SerializationDebugger$.improveException(SerializationDebugger.scala:41)
	at org.apache.spark.serializer.JavaSerializationStream.writeObject(JavaSerializer.scala:47)
	at org.apache.spark.serializer.JavaSerializerInstance.serialize(JavaSerializer.scala:101)
	at org.apache.spark.util.ClosureCleaner$.ensureSerializable(ClosureCleaner.scala:413)
	... 31 more
```

为了避免这种错误，我们可以考虑在 Worker 中建立连接，如下所示：
```java
dStream.foreachRDD(new VoidFunction<JavaRDD<String>>() {
    @Override
    public void call(JavaRDD<String> rdd) throws Exception {
        rdd.foreach(new VoidFunction<String>() {
            @Override
            public void call(String record) throws Exception {
                LOG.info("[INFO] 输入记录：" + record);
                // 1. 通过连接池获取连接
                DruidDataSource dataSource = DruidConfig.getDataSource();
                DruidPooledConnection connection = dataSource.getConnection();

                // 2. 遍历 RDD 通过连接与外部存储系统交互
                String[] params = record.split(",");
                String sql = "INSERT INTO tb_user (id, name, age, email) VALUES (?, ?, ?, ?)";
                PreparedStatement stmt = null;
                try {
                    stmt = connection.prepareStatement(sql);
                    // 设置参数并执行插入操作
                    stmt.setInt(1, Integer.parseInt(params[0]));
                    stmt.setString(2, params[1]);
                    stmt.setInt(3, Integer.parseInt(params[2]));
                    stmt.setString(4, params[3]);
                    stmt.executeUpdate();
                    LOG.info("[INFO] 通过连接与外部存储系统交互");
                } catch (Exception e) {
                    LOG.error("[ERROR] 与外部存储系统交互失败：" + e.getMessage());
                } finally {
                    // 3. 关闭连接
                    if (stmt != null) {
                        stmt.close();
                    }
                    if(connection != null) {
                        connection.close();
                        LOG.info("[INFO] 关闭连接");
                    }
                }
            }
        });

    }
});
```
上面的程序在运行时是没有问题的，但是这里我们忽略了一个严重的性能问题：在 RDD 的每条记录进行外部存储操作时，都需要建立和关闭连接，这个开销在大规模数据集中是很夸张的，会降低系统的吞吐量：
```java
24/12/22 10:29:20 INFO DataBaseSinkRddWorkerExample: [INFO] 输入记录：1,lily,12,lily@qq.com
24/12/22 10:29:20 INFO DruidConfig: [INFO] 创建 DruidDataSource
24/12/22 10:29:20 INFO DruidDataSource: {dataSource-1} inited
24/12/22 10:29:20 INFO DataBaseSinkRddWorkerExample: [INFO] 通过连接与外部存储系统交互
24/12/22 10:29:20 INFO DataBaseSinkRddWorkerExample: [INFO] 关闭连接
24/12/22 10:29:20 INFO DataBaseSinkRddWorkerExample: [INFO] 输入记录：2,lucy,21,lucy@qq.com
24/12/22 10:29:20 INFO DruidConfig: [INFO] 创建 DruidDataSource
24/12/22 10:29:20 INFO DruidDataSource: {dataSource-2} inited
24/12/22 10:29:20 INFO DataBaseSinkRddWorkerExample: [INFO] 通过连接与外部存储系统交互
24/12/22 10:29:20 INFO DataBaseSinkRddWorkerExample: [INFO] 关闭连接
24/12/22 10:29:20 INFO DataBaseSinkRddWorkerExample: [INFO] 输入记录：3,jark,18,jark@qq.com
24/12/22 10:29:20 INFO DruidConfig: [INFO] 创建 DruidDataSource
24/12/22 10:29:20 INFO DruidDataSource: {dataSource-3} inited
24/12/22 10:29:20 INFO DataBaseSinkRddWorkerExample: [INFO] 通过连接与外部存储系统交互
24/12/22 10:29:20 INFO DataBaseSinkRddWorkerExample: [INFO] 关闭连接
24/12/22 10:29:20 INFO DataBaseSinkRddWorkerExample: [INFO] 输入记录：4,tom,35,tom@qq.com
24/12/22 10:29:20 INFO DruidConfig: [INFO] 创建 DruidDataSource
24/12/22 10:29:20 INFO DruidDataSource: {dataSource-4} inited
24/12/22 10:29:20 INFO DataBaseSinkRddWorkerExample: [INFO] 通过连接与外部存储系统交互
24/12/22 10:29:20 INFO DataBaseSinkRddWorkerExample: [INFO] 关闭连接
```
针对上述 RDD 的每条记录进行外部存储操作时都需要建立和关闭连接的瓶颈使用 `foreachPartition` 优化，即按照 RDD 的不同分区（partition）来遍历 RDD，再在每个分区遍历每条记录。由于每个 partition 是运行在同一 Worker 之上的，不存在跨机器的网络传输，我们便可以在每个分区上实现只建立和关闭连接一次：
```java
dStream.foreachRDD(new VoidFunction<JavaRDD<String>>() {
    @Override
    public void call(JavaRDD<String> rdd) throws Exception {
        rdd.foreachPartition(new VoidFunction<Iterator<String>>() {
            @Override
            public void call(Iterator<String> iterator) throws Exception {
                // 1. 通过连接池获取连接
                DruidDataSource dataSource = DruidConfig.getDataSource();
                DruidPooledConnection connection = dataSource.getConnection();
                while (iterator.hasNext()) {
                    String record = iterator.next();
                    LOG.info("[INFO] 输入记录：" + record);
                    // 2. 通过连接与外部存储系统交互
                    String[] params = record.split(",");
                    String sql = "INSERT INTO tb_user (id, name, age, email) VALUES (?, ?, ?, ?)";
                    PreparedStatement stmt = null;
                    try {
                        stmt = connection.prepareStatement(sql);
                        // 设置参数并执行插入操作
                        stmt.setInt(1, Integer.parseInt(params[0]));
                        stmt.setString(2, params[1]);
                        stmt.setInt(3, Integer.parseInt(params[2]));
                        stmt.setString(4, params[3]);
                        stmt.executeUpdate();
                        LOG.info("[INFO] 通过连接与外部存储系统交互");
                    } catch (Exception e) {
                        LOG.error("[ERROR] 与外部存储系统交互失败：" + e.getMessage());
                    } finally {
                        if (stmt != null) {
                            stmt.close();
                        }
                    }
                }
                // 3. 关闭连接
                if(connection != null) {
                    connection.close();
                    LOG.info("[INFO] 关闭连接");
                }
            }
        });
    }
});
```
这样就降低了频繁建立连接的负载。如下所示，相对比上一方案建立和关闭连接的次数大大减少：
```java
24/12/22 10:35:50 INFO DruidConfig: [INFO] 创建 DruidDataSource
24/12/22 10:35:51 INFO DruidDataSource: {dataSource-1} inited
24/12/22 10:35:51 INFO DataBaseSinkPartitionExample: [INFO] 输入记录：1,lily,12,lily@qq.com
24/12/22 10:35:51 INFO DataBaseSinkPartitionExample: [INFO] 通过连接与外部存储系统交互
24/12/22 10:35:51 INFO DataBaseSinkPartitionExample: [INFO] 输入记录：2,lucy,21,lucy@qq.com
24/12/22 10:35:51 INFO DataBaseSinkPartitionExample: [INFO] 通过连接与外部存储系统交互
24/12/22 10:35:51 INFO DataBaseSinkPartitionExample: [INFO] 输入记录：3,jark,18,jark@qq.com
24/12/22 10:35:51 INFO DataBaseSinkPartitionExample: [INFO] 通过连接与外部存储系统交互
24/12/22 10:35:51 INFO DataBaseSinkPartitionExample: [INFO] 输入记录：4,tom,35,tom@qq.com
24/12/22 10:35:51 INFO DataBaseSinkPartitionExample: [INFO] 通过连接与外部存储系统交互
24/12/22 10:35:51 INFO DataBaseSinkPartitionExample: [INFO] 关闭连接
```
