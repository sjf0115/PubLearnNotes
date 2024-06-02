2024-05-31 17:15:17 2024-05-31 09:15:17 WARN  Storage:420 - Failed to add storage directory [DISK]file:/tmp/hadoop-hadoop/dfs/data
2024-05-31 17:15:17 java.io.IOException: Incompatible clusterIDs in /tmp/hadoop-hadoop/dfs/data: namenode clusterID = CID-e9120058-e531-422c-a1c1-4f6a2ac94ad3; datanode clusterID = CID-01ee3611-8e40-4001-9a3b-009a5987db7f
2024-05-31 17:15:17     at org.apache.hadoop.hdfs.server.datanode.DataStorage.doTransition(DataStorage.java:746)
2024-05-31 17:15:17     at org.apache.hadoop.hdfs.server.datanode.DataStorage.loadStorageDirectory(DataStorage.java:296)
2024-05-31 17:15:17     at org.apache.hadoop.hdfs.server.datanode.DataStorage.loadDataStorage(DataStorage.java:409)
2024-05-31 17:15:17     at org.apache.hadoop.hdfs.server.datanode.DataStorage.addStorageLocations(DataStorage.java:389)
2024-05-31 17:15:17     at org.apache.hadoop.hdfs.server.datanode.DataStorage.recoverTransitionRead(DataStorage.java:561)
2024-05-31 17:15:17     at org.apache.hadoop.hdfs.server.datanode.DataNode.initStorage(DataNode.java:2059)
2024-05-31 17:15:17     at org.apache.hadoop.hdfs.server.datanode.DataNode.initBlockPool(DataNode.java:1995)
2024-05-31 17:15:17     at org.apache.hadoop.hdfs.server.datanode.BPOfferService.verifyAndSetNamespaceInfo(BPOfferService.java:394)
2024-05-31 17:15:17     at org.apache.hadoop.hdfs.server.datanode.BPServiceActor.connectToNNAndHandshake(BPServiceActor.java:312)
2024-05-31 17:15:17     at org.apache.hadoop.hdfs.server.datanode.BPServiceActor.run(BPServiceActor.java:891)
2024-05-31 17:15:17     at java.lang.Thread.run(Thread.java:748)
2024-05-31 17:15:17 2024-05-31 09:15:17 ERROR DataNode:903 - Initialization failed for Block pool <registering> (Datanode Uuid 345644fd-eafe-42a6-a71c-8d26ed721aa5) service to namenode/172.21.0.2:8020. Exiting.
2024-05-31 17:15:17 java.io.IOException: All specified directories have failed to load.
2024-05-31 17:15:17     at org.apache.hadoop.hdfs.server.datanode.DataStorage.recoverTransitionRead(DataStorage.java:562)
2024-05-31 17:15:17     at org.apache.hadoop.hdfs.server.datanode.DataNode.initStorage(DataNode.java:2059)
2024-05-31 17:15:17     at org.apache.hadoop.hdfs.server.datanode.DataNode.initBlockPool(DataNode.java:1995)
2024-05-31 17:15:17     at org.apache.hadoop.hdfs.server.datanode.BPOfferService.verifyAndSetNamespaceInfo(BPOfferService.java:394)
2024-05-31 17:15:17     at org.apache.hadoop.hdfs.server.datanode.BPServiceActor.connectToNNAndHandshake(BPServiceActor.java:312)
2024-05-31 17:15:17     at org.apache.hadoop.hdfs.server.datanode.BPServiceActor.run(BPServiceActor.java:891)
2024-05-31 17:15:17     at java.lang.Thread.run(Thread.java:748)
2024-05-31 17:15:17 2024-05-31 09:15:17 WARN  DataNode:931 - Ending block pool service for: Block pool <registering> (Datanode Uuid 345644fd-eafe-42a6-a71c-8d26ed721aa5) service to namenode/172.21.0.2:8020
2024-05-31 17:15:17 2024-05-31 09:15:17 INFO  DataNode:102 - Removed Block pool <registering> (Datanode Uuid 345644fd-eafe-42a6-a71c-8d26ed721aa5)
2024-05-31 17:15:19 2024-05-31 09:15:19 WARN  DataNode:3256 - Exiting Datanode
