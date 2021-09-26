## 1. DataNode未启动

#### 1.1 问题原因

这个问题一般是由于两次或两次以上的格式化NameNode造成的。jps命令发现没有datanode启动，所以去Hadoop的日志文件下查看日志（/opt/hadoop-2.7.2/logs/hadoop-xiaosi-datanode-Qunar.log），每个人的日志文件都是不一样的：
```
2016-06-12 20:01:31,374 WARN org.apache.hadoop.hdfs.server.common.Storage: java.io.IOException: Incompatible clusterIDs in /home/xiaosi/config/hadoop/tmp/dfs/data: namenode clusterID = CID-67134f3c-0dcd-4e29-a629-a823d6c04732; datanode clusterID = CID-cf2f0387-3b3b-4bd8-8b10-6f5baecccdcf
2016-06-12 20:01:31,375 FATAL org.apache.hadoop.hdfs.server.datanode.DataNode: Initialization failed for Block pool <registering> (Datanode Uuid unassigned) service to localhost/127.0.0.1:9000. Exiting.
java.io.IOException: All specified directories are failed to load.
	at org.apache.hadoop.hdfs.server.datanode.DataStorage.recoverTransitionRead(DataStorage.java:478)
	at org.apache.hadoop.hdfs.server.datanode.DataNode.initStorage(DataNode.java:1358)
	at org.apache.hadoop.hdfs.server.datanode.DataNode.initBlockPool(DataNode.java:1323)
	at org.apache.hadoop.hdfs.server.datanode.BPOfferService.verifyAndSetNamespaceInfo(BPOfferService.java:317)
	at org.apache.hadoop.hdfs.server.datanode.BPServiceActor.connectToNNAndHandshake(BPServiceActor.java:223)
	at org.apache.hadoop.hdfs.server.datanode.BPServiceActor.run(BPServiceActor.java:802)
	at java.lang.Thread.run(Thread.java:724)
2016-06-12 20:01:31,377 WARN org.apache.hadoop.hdfs.server.datanode.DataNode: Ending block pool service for: Block pool <registering> (Datanode Uuid unassigned) service to localhost/127.0.0.1:9000
2016-06-12 20:01:31,388 INFO org.apache.hadoop.hdfs.server.datanode.DataNode: Removed Block pool <registering> (Datanode Uuid unassigned)
2016-06-12 20:01:33,389 WARN org.apache.hadoop.hdfs.server.datanode.DataNode: Exiting Datanode
2016-06-12 20:01:33,391 INFO org.apache.hadoop.util.ExitUtil: Exiting with status 0
2016-06-12 20:01:33,392 INFO org.apache.hadoop.hdfs.server.datanode.DataNode: SHUTDOWN_MSG:
/************************************************************
SHUTDOWN_MSG: Shutting down DataNode at Qunar/127.0.0.1
************************************************************/
2016-06-13 12:56:00,753 INFO org.apache.hadoop.hdfs.server.datanode.DataNode: STARTUP_MSG:
/************************************************************
```

从日志文件中我们捕捉到Incompatible这个单词，意思是“不相容的”，所以我们可以看出是datanode的clusterID出错了，最后导致shutDown。

#### 1.2 解决方案

查看hadoop路径下的配置文件hdfs-site.xml（/opt/hadoop-2.7.2/etc/hadoop/hdfs-site.xml）：
```
<configuration>
   <property>
      <name>dfs.replication</name>
      <value>1</value>
   </property>
   <property>
      <name>dfs.namenode.name.dir</name>
      <value>file:/home/xiaosi/config/hadoop/tmp/dfs/name</value>
   </property>
   <property>
      <name>dfs.datanode.data.dir</name>
　　　<value>file:/home/xiaosi/config/hadoop/tmp/dfs/data</value>
   </property>
</configuration>
```
我们可以看到datanode和namenode不再默认路径，而是自己设置过的路径。根据设置的路径，进入datanode的dfs.datanode.data.dir的current目录，修改其中的VERSION文件：
```
#Wed May 25 11:19:08 CST 2016
storageID=DS-92ce5ab0-115f-45ef-b7f1-cf6540cc8bfa
#clusterID=CID-cf2f0387-3b3b-4bd8-8b10-6f5baecccdcf
clusterID=CID-67134f3c-0dcd-4e29-a629-a823d6c04732
cTime=0
datanodeUuid=261d557d-4f5b-4006-9a64-39c544b6b962
storageType=DATA_NODE
layoutVersion=-56
```
修改clusterID与/opt/hadoop-2.7.2/logs/hadoop-xiaosi-datanode-Qunar.log中namenode的clusterID一致。

最后重新启动Hadoop：
```
xiaosi@Qunar:/opt/hadoop-2.7.2/sbin$ ./start-all.sh
This script is Deprecated. Instead use start-dfs.sh and start-yarn.sh
Starting namenodes on [localhost]
localhost: namenode running as process 3689. Stop it first.
localhost: starting datanode, logging to /opt/hadoop-2.7.2/logs/hadoop-xiaosi-datanode-Qunar.out
Starting secondary namenodes [0.0.0.0]
0.0.0.0: secondarynamenode running as process 4131. Stop it first.
starting yarn daemons
resourcemanager running as process 7192. Stop it first.
localhost: nodemanager running as process 7331. Stop it first.
```
看最后的运行结果：
```
xiaosi@Qunar:/opt/hadoop-2.7.2/sbin$ jps
4131 SecondaryNameNode
7192 ResourceManager
7331 NodeManager
3689 NameNode
9409 Jps
8989 DataNode
7818 RunJar
```
从上面可以看到我们的dataNode已经跑起来了。


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

#### 2.2 解决方案

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

## 4. Unhealthy Node local-dirs are bad

#### 4.1 问题原因
在运行作业时，作业一直卡在下面语句不能运行：
```
17/01/23 21:43:21 INFO mapreduce.Job: Running job: job_1485165672363_0004
```
在访问 http://localhost:8088/cluster/ 时，发现节点为不健康节点。NodeHealthReport报告如下：
```
1/1 local-dirs are bad: /tmp/hadoop-hduser/nm-local-dir;
1/1 log-dirs are bad: /usr/local/hadoop/logs/userlogs
```
#### 4.2 解决方案
引起local-dirs are bad的最常见原因是由于节点上的磁盘使用率超出了**max-disk-utilization-per-disk-percentage**（默认值90.0%）。

清理不健康节点上的磁盘空间或者降低参数设置的阈值：
```
<property>
        <name>yarn.nodemanager.disk-health-checker.max-disk-utilization-per-disk-percentage</name>
        <value>98.5</value>
</property>
```

因为当没有磁盘空间，或因为权限问题，会导致作业失败，所以不要禁用磁盘检查。更详细的信息可以： https://hadoop.apache.org/docs/current/hadoop-yarn/hadoop-yarn-site/NodeManager.html#Disk_Checker

参考：http://stackoverflow.com/questions/29131449/hadoop-unhealthy-node-local-dirs-are-bad-tmp-hadoop-hduser-nm-local-dir

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
