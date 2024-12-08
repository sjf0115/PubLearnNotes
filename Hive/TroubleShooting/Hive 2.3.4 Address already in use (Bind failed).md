## 1. 问题

在使用如下命令：
```
hive --service metastore -p 9083 &
```
启动 MetaStore 服务时抛出如下异常：
```java
2024-12-08T15:16:44,282 ERROR [main] metastore.HiveMetaStore: Metastore Thrift Server threw an exception...
org.apache.thrift.transport.TTransportException: Could not create ServerSocket on address 0.0.0.0/0.0.0.0:9083.
	at org.apache.thrift.transport.TServerSocket.<init>(TServerSocket.java:109) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.thrift.transport.TServerSocket.<init>(TServerSocket.java:91) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.thrift.transport.TServerSocket.<init>(TServerSocket.java:87) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.common.auth.HiveAuthUtils.getServerSocket(HiveAuthUtils.java:87) ~[hive-common-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.metastore.HiveMetaStore.startMetaStore(HiveMetaStore.java:7184) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.metastore.HiveMetaStore.main(HiveMetaStore.java:7065) [hive-exec-2.3.4.jar:2.3.4]
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method) ~[?:1.8.0_161]
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62) ~[?:1.8.0_161]
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43) ~[?:1.8.0_161]
	at java.lang.reflect.Method.invoke(Method.java:498) ~[?:1.8.0_161]
	at org.apache.hadoop.util.RunJar.run(RunJar.java:244) [hadoop-common-2.10.1.jar:?]
	at org.apache.hadoop.util.RunJar.main(RunJar.java:158) [hadoop-common-2.10.1.jar:?]
Caused by: java.net.BindException: Address already in use (Bind failed)
	at java.net.PlainSocketImpl.socketBind(Native Method) ~[?:1.8.0_161]
	at java.net.AbstractPlainSocketImpl.bind(AbstractPlainSocketImpl.java:387) ~[?:1.8.0_161]
	at java.net.ServerSocket.bind(ServerSocket.java:375) ~[?:1.8.0_161]
	at org.apache.thrift.transport.TServerSocket.<init>(TServerSocket.java:106) ~[hive-exec-2.3.4.jar:2.3.4]
	... 11 more
```

## 2. 分析

`Address already in use` 错误通常表示我们启动的服务想要绑定的端口已经被其他进程占用。在 Hive 的上下文中，这通常意味着 Hive 服务尝试绑定的端口 9083 已经被其他应用程序使用。我们可以查找并停止占用端口的进程，在 Linux 系统中，可以使用 `lsof -i:端口号` 或 `netstat -tulnp | grep 端口号` 来查找占用端口的进程：
```
localhost:script wy$ lsof -i:9083
COMMAND   PID USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
java    33638   wy  518u  IPv4 0x5ac58382a98ccd75      0t0  TCP *:9083 (LISTEN)
```
可以看到进程ID 为 `33638`，可以使用 `kill 进程ID` 命令来停止它：
```
localhost:script wy$ sudo kill 33638
```
