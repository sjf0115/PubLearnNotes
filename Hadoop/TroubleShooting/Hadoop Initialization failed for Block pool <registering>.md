## 1. 问题

在启动 HDFS 时遇到如下异常：
```java
2023-08-22 07:47:47,609 WARN org.apache.hadoop.hdfs.server.common.Storage: Failed to add storage directory [DISK]file:/Users/wy/tmp/hadoop/dfs/data/
java.io.IOException: Incompatible clusterIDs in /Users/wy/tmp/hadoop/dfs/data: namenode clusterID = CID-099a5efb-80ac-4fa4-96d5-7f44d8512e2d; datanode clusterID = CID-365e3e12-8892-4abb-a0c2-68efd55cc59b
        at org.apache.hadoop.hdfs.server.datanode.DataStorage.doTransition(DataStorage.java:768)
        at org.apache.hadoop.hdfs.server.datanode.DataStorage.loadStorageDirectory(DataStorage.java:293)
        at org.apache.hadoop.hdfs.server.datanode.DataStorage.loadDataStorage(DataStorage.java:409)
        at org.apache.hadoop.hdfs.server.datanode.DataStorage.addStorageLocations(DataStorage.java:388)
        at org.apache.hadoop.hdfs.server.datanode.DataStorage.recoverTransitionRead(DataStorage.java:564)
        at org.apache.hadoop.hdfs.server.datanode.DataNode.initStorage(DataNode.java:1659)
        at org.apache.hadoop.hdfs.server.datanode.DataNode.initBlockPool(DataNode.java:1620)
        at org.apache.hadoop.hdfs.server.datanode.BPOfferService.verifyAndSetNamespaceInfo(BPOfferService.java:388)
        at org.apache.hadoop.hdfs.server.datanode.BPServiceActor.connectToNNAndHandshake(BPServiceActor.java:282)
        at org.apache.hadoop.hdfs.server.datanode.BPServiceActor.run(BPServiceActor.java:826)
        at java.base/java.lang.Thread.run(Thread.java:834)
2023-08-22 07:47:47,612 ERROR org.apache.hadoop.hdfs.server.datanode.DataNode: Initialization failed for Block pool <registering> (Datanode Uuid 553ed9a7-a2f4-40e1-ab50-f6625ede6952) service to localhost/127.0.0.1:9000. Exiting.
java.io.IOException: All specified directories have failed to load.
        at org.apache.hadoop.hdfs.server.datanode.DataStorage.recoverTransitionRead(DataStorage.java:565)
        at org.apache.hadoop.hdfs.server.datanode.DataNode.initStorage(DataNode.java:1659)
        at org.apache.hadoop.hdfs.server.datanode.DataNode.initBlockPool(DataNode.java:1620)
        at org.apache.hadoop.hdfs.server.datanode.BPOfferService.verifyAndSetNamespaceInfo(BPOfferService.java:388)
        at org.apache.hadoop.hdfs.server.datanode.BPServiceActor.connectToNNAndHandshake(BPServiceActor.java:282)
        at org.apache.hadoop.hdfs.server.datanode.BPServiceActor.run(BPServiceActor.java:826)
        at java.base/java.lang.Thread.run(Thread.java:834)
2023-08-22 07:47:47,612 WARN org.apache.hadoop.hdfs.server.datanode.DataNode: Ending block pool service for: Block pool <registering> (Datanode Uuid 553ed9a7-a2f4-40e1-ab50-f6625ede6952) service to localhost/127.0.0.1:9000
2023-08-22 07:47:47,625 INFO org.apache.hadoop.hdfs.server.datanode.DataNode: Removed Block pool <registering> (Datanode Uuid 553ed9a7-a2f4-40e1-ab50-f6625ede6952)
2023-08-22 07:47:49,627 WARN org.apache.hadoop.hdfs.server.datanode.DataNode: Exiting Datanode
2023-08-22 07:47:49,630 INFO org.apache.hadoop.hdfs.server.datanode.DataNode: SHUTDOWN_MSG:
/************************************************************
SHUTDOWN_MSG: Shutting down DataNode at localhost/127.0.0.1
************************************************************/
```
从上面异常中可以发现 namenode 的 clusterID 为 `CID-099a5efb-80ac-4fa4-96d5-7f44d8512e2d`，而 datanode 的 clusterID 为 `CID-365e3e12-8892-4abb-a0c2-68efd55cc59b`，两者的 clusterID 不一致导致最终 datanode 没有启动。这个问题一般是由于两次或两次以上的格式化 NameNode 造成的。

## 2. 解决方案

进入到 `/Users/wy/tmp/hadoop/dfs/data/current` 目录，查看 VERSION 文件，可以发现 datanode 的 clusterID 为 `CID-365e3e12-8892-4abb-a0c2-68efd55cc59b`：
```
localhost:current wy$ cat VERSION
#Wed Aug 16 07:29:12 CST 2023
storageID=DS-d974b748-bad1-4417-8206-6291bbf7b3c3
clusterID=CID-365e3e12-8892-4abb-a0c2-68efd55cc59b
cTime=0
datanodeUuid=553ed9a7-a2f4-40e1-ab50-f6625ede6952
storageType=DATA_NODE
layoutVersion=-56
```
现在只需要将 datanode 的 VERTSION 文件中的 clusterID 更改成和 namenode 的 clusterID 一致即可：
```
#Wed Aug 16 07:29:12 CST 2023
storageID=DS-d974b748-bad1-4417-8206-6291bbf7b3c3
clusterID=CID-099a5efb-80ac-4fa4-96d5-7f44d8512e2d
cTime=0
datanodeUuid=553ed9a7-a2f4-40e1-ab50-f6625ede6952
storageType=DATA_NODE
layoutVersion=-56
```
修改完之后通过 `start-all.sh` 重启 Hadoop 即可。看最后的运行结果：
```
localhost:hadoop wy$ jps
6352 SecondaryNameNode
6152 NameNode
6237 DataNode
6478 Jps
```
从上面可以看到我们的 dataNode 已经跑起来了。
