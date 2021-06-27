### 1. Unsupported major.minor version 52.0

启动ZooKeeper报如下错误：

```java
ZooKeeper JMX enabled by default
Using config: /opt/zookeeper/bin/../conf/zoo.cfg
Exception in thread "main" java.lang.UnsupportedClassVersionError: org/apache/zookeeper/server/quorum/QuorumPeerMain : Unsupported major.minor version 52.0
	at java.lang.ClassLoader.defineClass1(Native Method)
	at java.lang.ClassLoader.defineClass(ClassLoader.java:808)
	at java.security.SecureClassLoader.defineClass(SecureClassLoader.java:142)
	at java.net.URLClassLoader.defineClass(URLClassLoader.java:443)
	at java.net.URLClassLoader.access$100(URLClassLoader.java:65)
	at java.net.URLClassLoader$1.run(URLClassLoader.java:355)
	at java.net.URLClassLoader$1.run(URLClassLoader.java:349)
	at java.security.AccessController.doPrivileged(Native Method)
	at java.net.URLClassLoader.findClass(URLClassLoader.java:348)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:430)
	at sun.misc.Launcher$AppClassLoader.loadClass(Launcher.java:326)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:363)
	at sun.launcher.LauncherHelper.checkAndLoadMain(LauncherHelper.java:482)
```

### 2. Address unresolved: 127.0.0.1:3888

在启动 ZooKeeper 节点1时报如下错误：
```
wy:zookeeper wy$ zkServer.sh start /opt/zookeeper/conf/zoo1.cfg
ZooKeeper JMX enabled by default
Using config: /opt/zookeeper/conf/zoo1.cfg
Starting zookeeper ... FAILED TO START
```
查看 ZooKeeper 具体日志如下：
```java
2020-10-11 22:24:04,463 [myid:] - INFO  [main:QuorumPeerConfig@135] - Reading configuration from: /opt/zookeeper/conf/zoo1.cfg
2020-10-11 22:24:04,478 [myid:] - INFO  [main:QuorumPeerConfig@387] - clientPortAddress is 0.0.0.0:2181
2020-10-11 22:24:04,478 [myid:] - INFO  [main:QuorumPeerConfig@391] - secureClientPort is not set
2020-10-11 22:24:04,482 [myid:] - ERROR [main:QuorumPeerMain@89] - Invalid config, exiting abnormally
org.apache.zookeeper.server.quorum.QuorumPeerConfig$ConfigException: Address unresolved: 127.0.0.1:3888
        at org.apache.zookeeper.server.quorum.QuorumPeer$QuorumServer.<init>(QuorumPeer.java:261)
        at org.apache.zookeeper.server.quorum.flexible.QuorumMaj.<init>(QuorumMaj.java:89)
        at org.apache.zookeeper.server.quorum.QuorumPeerConfig.createQuorumVerifier(QuorumPeerConfig.java:597)
        at org.apache.zookeeper.server.quorum.QuorumPeerConfig.parseDynamicConfig(QuorumPeerConfig.java:630)
        at org.apache.zookeeper.server.quorum.QuorumPeerConfig.setupQuorumPeerConfig(QuorumPeerConfig.java:603)
        at org.apache.zookeeper.server.quorum.QuorumPeerConfig.parseProperties(QuorumPeerConfig.java:422)
        at org.apache.zookeeper.server.quorum.QuorumPeerConfig.parse(QuorumPeerConfig.java:152)
        at org.apache.zookeeper.server.quorum.QuorumPeerMain.initializeAndRun(QuorumPeerMain.java:113)
        at org.apache.zookeeper.server.quorum.QuorumPeerMain.main(QuorumPeerMain.java:82)
Invalid config, exiting abnormally
```
错误原因是在配置zoo1.cfg文件时候，端口号后面还有空格：
```
server.1=127.0.0.1:2888:3888(此处有空格)
server.2=127.0.0.1:2889:3889
server.3=127.0.0.1:2890:3890
```
### 3.
