

## 2. NameNode未启动

#### 2.1 问题原因
```
2016-12-04 14:50:39,879 ERROR org.apache.hadoop.hdfs.server.namenode.NameNode: Failed to start namenode.
org.apache.hadoop.hdfs.server.common.InconsistentFSStateException: Directory /home/xiaosi/tmp/hadoop/dfs/name is in an inconsistent state: storage directory does not exist or is not accessible.
	at org.apache.hadoop.hdfs.server.namenode.FSImage.recoverStorageDirs(FSImage.java:327)
	at org.apache.hadoop.hdfs.server.namenode.FSImage.recoverTransitionRead(FSImage.java:215)
	at org.apache.hadoop.hdfs.server.namenode.FSNamesystem.loadFSImage(FSNamesystem.java:975)
	at org.apache.hadoop.hdfs.server.namenode.FSNamesystem.loadFromDisk(FSNamesystem.java:681)
	at org.apache.hadoop.hdfs.server.namenode.NameNode.loadNamesystem(NameNode.java:585)
	at org.apache.hadoop.hdfs.server.namenode.NameNode.initialize(NameNode.java:645)
	at org.apache.hadoop.hdfs.server.namenode.NameNode.<init>(NameNode.java:812)
	at org.apache.hadoop.hdfs.server.namenode.NameNode.<init>(NameNode.java:796)
	at org.apache.hadoop.hdfs.server.namenode.NameNode.createNameNode(NameNode.java:1493)
	at org.apache.hadoop.hdfs.server.namenode.NameNode.main(NameNode.java:1559)
```

#### 2.2 解决方案``

在配置完成后，运行hadoop前，要初始化HDFS系统，在bin/目录下执行如下命令：
```
./bin/hdfs namenode -format
```

## 3. NodeManager未启动

#### 3.1 问题原因
查看Hadoop log日志：
```
2017-01-23 14:28:53,279 FATAL org.apache.hadoop.yarn.server.nodemanager.containermanager.AuxServices: Failed to initialize mapreduce.shuffle
java.lang.IllegalArgumentException: The ServiceName: mapreduce.shuffle set in yarn.nodemanager.aux-services is invalid.The valid service name should only contain a-zA-Z0-9_ and can not start with numbers
        at com.google.common.base.Preconditions.checkArgument(Preconditions.java:88)
        at org.apache.hadoop.yarn.server.nodemanager.containermanager.AuxServices.serviceInit(AuxServices.java:114)
        at org.apache.hadoop.service.AbstractService.init(AbstractService.java:163)
        at org.apache.hadoop.service.CompositeService.serviceInit(CompositeService.java:107)
        at org.apache.hadoop.yarn.server.nodemanager.containermanager.ContainerManagerImpl.serviceInit(ContainerManagerImpl.java:245)
        at org.apache.hadoop.service.AbstractService.init(AbstractService.java:163)
        at org.apache.hadoop.service.CompositeService.serviceInit(CompositeService.java:107)
        at org.apache.hadoop.yarn.server.nodemanager.NodeManager.serviceInit(NodeManager.java:261)
        at org.apache.hadoop.service.AbstractService.init(AbstractService.java:163)
        at org.apache.hadoop.yarn.server.nodemanager.NodeManager.initAndStartNodeManager(NodeManager.java:495)
        at org.apache.hadoop.yarn.server.nodemanager.NodeManager.main(NodeManager.java:543)

```
从上面异常我们可以知道yarn.nodemanager.aux-services的配置值mapreduce.shuffle有问题。查看原配置：
```
<property>
   <name>yarn.nodemanager.aux-services</name>
   <value>mapreduce.shuffle</value>
</property>
```

#### 3.2 解决方案
修改yarn-site.xml配置文件，做如下修改：
```
<property>
   <name>yarn.nodemanager.aux-services</name>
   <value>mapreduce_shuffle</value>
</property>
```
重启即可



### 5. NameNode启动失败2

```
2017-12-26 20:02:44,017 ERROR org.apache.hadoop.hdfs.server.namenode.NameNode: Failed to start namenode.
org.apache.hadoop.hdfs.server.common.InconsistentFSStateException: Directory /tmp/hadoop-xiaosi/dfs/name is in an inconsistent state: storage directory does not exist or is not accessible.
	at org.apache.hadoop.hdfs.server.namenode.FSImage.recoverStorageDirs(FSImage.java:327)
	at org.apache.hadoop.hdfs.server.namenode.FSImage.recoverTransitionRead(FSImage.java:215)
	at org.apache.hadoop.hdfs.server.namenode.FSNamesystem.loadFSImage(FSNamesystem.java:975)
	at org.apache.hadoop.hdfs.server.namenode.FSNamesystem.loadFromDisk(FSNamesystem.java:681)
	at org.apache.hadoop.hdfs.server.namenode.NameNode.loadNamesystem(NameNode.java:585)
	at org.apache.hadoop.hdfs.server.namenode.NameNode.initialize(NameNode.java:645)
	at org.apache.hadoop.hdfs.server.namenode.NameNode.<init>(NameNode.java:812)
	at org.apache.hadoop.hdfs.server.namenode.NameNode.<init>(NameNode.java:796)
	at org.apache.hadoop.hdfs.server.namenode.NameNode.createNameNode(NameNode.java:1493)
	at org.apache.hadoop.hdfs.server.namenode.NameNode.main(NameNode.java:1559)
```
http://www.linuxidc.com/Linux/2012-03/56348.htm
