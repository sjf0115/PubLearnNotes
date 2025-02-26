## 1. 问题

使用
```shell
./bin/seatunnel.sh \
    --config /opt/seatunnel/config/v2.batch.config.template \
    -m cluster \
```


如果直接在 `/opt/apache-seatunnel-2.3.8` 路径下执行会出现如下异常：
```java
2025-02-23 17:24:57 2025-02-23 09:24:57,724 INFO  [o.a.s.e.s.m.JobMaster         ] [seatunnel-coordinator-service-22] - Init JobMaster for Job SeaTunnel_Job (945974504738258945)
2025-02-23 17:24:57 2025-02-23 09:24:57,724 INFO  [o.a.s.e.s.m.JobMaster         ] [seatunnel-coordinator-service-22] - Job SeaTunnel_Job (945974504738258945) needed jar urls [file:/opt/apache-seatunnel-2.3.8/connectors/connector-fake-2.3.8.jar, file:/opt/apache-seatunnel-2.3.8/connectors/connector-console-2.3.8.jar]
2025-02-23 17:24:57 2025-02-23 09:24:57,724 INFO  [.c.c.DefaultClassLoaderService] [seatunnel-coordinator-service-22] - Create classloader for job 945974504738258945 with jars [file:/opt/apache-seatunnel-2.3.8/connectors/connector-fake-2.3.8.jar, file:/opt/apache-seatunnel-2.3.8/connectors/connector-console-2.3.8.jar]
2025-02-23 17:24:57 2025-02-23 09:24:57,729 ERROR [o.a.s.e.s.CoordinatorService  ] [seatunnel-coordinator-service-22] - [docker_master]:5801 [seatunnel] [5.1] submit job 945974504738258945 error com.hazelcast.nio.serialization.HazelcastSerializationException: java.lang.ClassNotFoundException: org.apache.seatunnel.connectors.seatunnel.fake.source.FakeSource
...
2025-02-23 17:24:57 Caused by: java.lang.ClassNotFoundException: org.apache.seatunnel.connectors.seatunnel.fake.source.FakeSource
2025-02-23 17:24:57     at java.net.URLClassLoader.findClass(URLClassLoader.java:387)
2025-02-23 17:24:57     at java.lang.ClassLoader.loadClass(ClassLoader.java:418)
2025-02-23 17:24:57     at org.apache.seatunnel.engine.common.loader.SeaTunnelBaseClassLoader.loadClassWithoutExceptionHandling(SeaTunnelBaseClassLoader.java:56)
2025-02-23 17:24:57     at org.apache.seatunnel.engine.common.loader.SeaTunnelChildFirstClassLoader.loadClassWithoutExceptionHandling(SeaTunnelChildFirstClassLoader.java:88)
2025-02-23 17:24:57     at org.apache.seatunnel.engine.common.loader.SeaTunnelBaseClassLoader.loadClass(SeaTunnelBaseClassLoader.java:47)
2025-02-23 17:24:57     at java.lang.ClassLoader.loadClass(ClassLoader.java:351)
2025-02-23 17:24:57     at com.hazelcast.internal.nio.ClassLoaderUtil.tryLoadClass(ClassLoaderUtil.java:301)
2025-02-23 17:24:57     at com.hazelcast.internal.nio.ClassLoaderUtil.loadClass(ClassLoaderUtil.java:259)
2025-02-23 17:24:57     at com.hazelcast.internal.nio.IOUtil$ClassLoaderAwareObjectInputStream.resolveClass(IOUtil.java:867)
2025-02-23 17:24:57     at java.io.ObjectInputStream.readNonProxyDesc(ObjectInputStream.java:1988)
2025-02-23 17:24:57     at java.io.ObjectInputStream.readClassDesc(ObjectInputStream.java:1852)
2025-02-23 17:24:57     at java.io.ObjectInputStream.readOrdinaryObject(ObjectInputStream.java:2186)
2025-02-23 17:24:57     at java.io.ObjectInputStream.readObject0(ObjectInputStream.java:1669)
2025-02-23 17:24:57     at java.io.ObjectInputStream.defaultReadFields(ObjectInputStream.java:2431)
2025-02-23 17:24:57     at java.io.ObjectInputStream.readSerialData(ObjectInputStream.java:2355)
2025-02-23 17:24:57     at java.io.ObjectInputStream.readOrdinaryObject(ObjectInputStream.java:2213)
2025-02-23 17:24:57     at java.io.ObjectInputStream.readObject0(ObjectInputStream.java:1669)
2025-02-23 17:24:57     at java.io.ObjectInputStream.readObject(ObjectInputStream.java:503)
2025-02-23 17:24:57     at java.io.ObjectInputStream.readObject(ObjectInputStream.java:461)
2025-02-23 17:24:57     at com.hazelcast.internal.serialization.impl.defaultserializers.JavaDefaultSerializers$JavaSerializer.read(JavaDefaultSerializers.java:92)
```
修改执行路径为 `/opt/seatunnel` 可以正常运行。
