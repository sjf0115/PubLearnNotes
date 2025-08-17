> Zookeeper 版本：3.8.4

## 1. 问题

在部署 Zookeeper 集群时遇到如下异常：
```java
2025-08-17 20:26:16,261 [myid:3] - WARN  [main:o.a.z.s.q.QuorumPeer@1137] - Problem starting AdminServer
org.apache.zookeeper.server.admin.AdminServer$AdminServerException: Problem starting AdminServer on address 0.0.0.0, port 8080 and command URL /commands
	at org.apache.zookeeper.server.admin.JettyAdminServer.start(JettyAdminServer.java:194)
	at org.apache.zookeeper.server.quorum.QuorumPeer.start(QuorumPeer.java:1135)
	at org.apache.zookeeper.server.quorum.QuorumPeerMain.runFromConfig(QuorumPeerMain.java:229)
	at org.apache.zookeeper.server.quorum.QuorumPeerMain.initializeAndRun(QuorumPeerMain.java:137)
	at org.apache.zookeeper.server.quorum.QuorumPeerMain.main(QuorumPeerMain.java:91)
Caused by: java.io.IOException: Failed to bind to /0.0.0.0:8080
	at org.eclipse.jetty.server.ServerConnector.openAcceptChannel(ServerConnector.java:349)
	at org.eclipse.jetty.server.ServerConnector.open(ServerConnector.java:310)
	at org.eclipse.jetty.server.AbstractNetworkConnector.doStart(AbstractNetworkConnector.java:80)
	at org.eclipse.jetty.server.ServerConnector.doStart(ServerConnector.java:234)
	at org.eclipse.jetty.util.component.AbstractLifeCycle.start(AbstractLifeCycle.java:73)
	at org.eclipse.jetty.server.Server.doStart(Server.java:401)
	at org.eclipse.jetty.util.component.AbstractLifeCycle.start(AbstractLifeCycle.java:73)
	at org.apache.zookeeper.server.admin.JettyAdminServer.start(JettyAdminServer.java:185)
	... 4 common frames omitted
Caused by: java.net.BindException: Address already in use
	at sun.nio.ch.Net.bind0(Native Method)
	at sun.nio.ch.Net.bind(Net.java:440)
	at sun.nio.ch.Net.bind(Net.java:430)
	at sun.nio.ch.ServerSocketChannelImpl.bind(ServerSocketChannelImpl.java:225)
	at sun.nio.ch.ServerSocketAdaptor.bind(ServerSocketAdaptor.java:74)
	at org.eclipse.jetty.server.ServerConnector.openAcceptChannel(ServerConnector.java:344)
	... 11 common frames omitted
```

## 2. 分析

8080 是 Zookeeper 3.5+ 版本 AdminServer 的默认端口。上述异常表明 ZooKeeper 的 AdminServer 无法在 0.0.0.0:8080 端口启动，因为该端口已被其他进程占用。我们是伪分布式部署模式，第一个节点的配置如下：
```bash
tickTime=2000
dataDir=/opt/workspace/zookeeper/data/zk1
clientPort=2181
initLimit=10
syncLimit=5
server.1=127.0.0.1:2888:3888
server.2=127.0.0.1:2889:3889
server.3=127.0.0.1:2890:3890
```
> conf/zoo1.cfg

第二个节点的配置如下：
```bash
tickTime=2000
dataDir=/opt/workspace/zookeeper/data/zk2
clientPort=2182
initLimit=10
syncLimit=5
server.1=127.0.0.1:2888:3888
server.2=127.0.0.1:2889:3889
server.3=127.0.0.1:2890:3890
```
> conf/zoo2.cfg

第三个节点的配置如下：
```bash
tickTime=2000
dataDir=/opt/workspace/zookeeper/data/zk3
clientPort=2183
initLimit=10
syncLimit=5
server.1=127.0.0.1:2888:3888
server.2=127.0.0.1:2889:3889
server.3=127.0.0.1:2890:3890
```
> conf/zoo3.cfg

可以看到我们配置中没有为 AdminServer 明确指定端口号，即三个节点都是用了默认端口号 8080，所以导致了冲突。

## 3. 解决方案

修改配置文件为每个节点添加 `admin.serverPort` 参数来自定义不同的端口号。单机多实例时，每个实例的 `admin.serverPort` 必须唯一：
```
# 第一个节点
admin.serverPort=2081
# 第二个节点
admin.serverPort=2082
# 第三个节点
admin.serverPort=2083
```
