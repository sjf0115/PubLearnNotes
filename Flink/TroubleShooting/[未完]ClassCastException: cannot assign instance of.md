
```java
Caused by: org.apache.flink.streaming.runtime.tasks.StreamTaskException: Cannot instantiate user function.
	at org.apache.flink.streaming.api.graph.StreamConfig.getStreamOperatorFactory(StreamConfig.java:338)
	at org.apache.flink.streaming.runtime.tasks.OperatorChain.<init>(OperatorChain.java:159)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.executeRestore(StreamTask.java:551)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.runWithCleanUpOnFail(StreamTask.java:650)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.restore(StreamTask.java:540)
	at org.apache.flink.runtime.taskmanager.Task.doRun(Task.java:759)
	at org.apache.flink.runtime.taskmanager.Task.run(Task.java:566)
	at java.lang.Thread.run(Thread.java:748)
Caused by: java.lang.ClassCastException: cannot assign instance of org.apache.commons.collections.map.LinkedMap to field org.apache.flink.streaming.connectors.kafka.FlinkKafkaConsumerBase.pendingOffsetsToCommit of type org.apache.commons.collections.map.LinkedMap in instance of org.apache.flink.streaming.connectors.kafka.FlinkKafkaConsumer
	at java.io.ObjectStreamClass$FieldReflector.setObjFieldValues(ObjectStreamClass.java:2233)
	at java.io.ObjectStreamClass.setObjFieldValues(ObjectStreamClass.java:1405)
	at java.io.ObjectInputStream.defaultReadFields(ObjectInputStream.java:2284)
	at java.io.ObjectInputStream.readSerialData(ObjectInputStream.java:2202)
	at java.io.ObjectInputStream.readOrdinaryObject(ObjectInputStream.java:2060)
	at java.io.ObjectInputStream.readObject0(ObjectInputStream.java:1567)
	at java.io.ObjectInputStream.defaultReadFields(ObjectInputStream.java:2278)
	at java.io.ObjectInputStream.readSerialData(ObjectInputStream.java:2202)
	at java.io.ObjectInputStream.readOrdinaryObject(ObjectInputStream.java:2060)
	at java.io.ObjectInputStream.readObject0(ObjectInputStream.java:1567)
	at java.io.ObjectInputStream.defaultReadFields(ObjectInputStream.java:2278)
	at java.io.ObjectInputStream.readSerialData(ObjectInputStream.java:2202)
	at java.io.ObjectInputStream.readOrdinaryObject(ObjectInputStream.java:2060)
	at java.io.ObjectInputStream.readObject0(ObjectInputStream.java:1567)
	at java.io.ObjectInputStream.readObject(ObjectInputStream.java:427)
	at org.apache.flink.util.InstantiationUtil.deserializeObject(InstantiationUtil.java:615)
	at org.apache.flink.util.InstantiationUtil.deserializeObject(InstantiationUtil.java:600)
	at org.apache.flink.util.InstantiationUtil.deserializeObject(InstantiationUtil.java:587)
	at org.apache.flink.util.InstantiationUtil.readObjectFromConfig(InstantiationUtil.java:541)
	at org.apache.flink.streaming.api.graph.StreamConfig.getStreamOperatorFactory(StreamConfig.java:322)
	... 7 more
```

解决办法：在 conf/flink-conf.yaml 配置文件中添加如下内容并重启 Flink：
```
classloader.resolve-order: parent-first
```


2.1 ClassCastException: cannot assign instance
使用bin/flink run -m yarn-cluster ...方式提交flink作业时，报错如下：

Caused by: java.lang.ClassCastException: cannot assign instance of org.apache.commons.collections.map.LinkedMap to field org.apache.flink.streaming.connectors.kafka.FlinkKafkaConsumerBase.pendingOffsetsToCommit of type org.apache.commons.collections.map.LinkedMap in instance of org.apache.flink.streaming.connectors.kafka.FlinkKafkaConsumer010
1
经查，是因为
。我们提交的Flink作业，相关的class被动态加载。

可参考X cannot be cast to X exceptions

是因为多个不同版本的org.apache.commons.collections.map.LinkedMap被不同的CalssLoader加载，而这些类被尝试转换为对方。

解决方法是编辑conf/flink-conf.yaml，设置classloader.resolve-order: parent-first（flink默认逆置了ClassLoader，使用ChildClassLoader即user code ClassLoader来动态加载类。这个选项就关闭了逆置，即优先使用ParentClassLoader Java Application ClassLoader动态加载）来关闭逆置或设置classloader.parent-first-patterns-additional来单独设置使用parent-first的package。
