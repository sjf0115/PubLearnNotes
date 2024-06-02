



```java
2024-06-01 15:14:31 2024-06-01 07:14:31 WARN  FSNamesystem:810 - Encountered exception loading fsimage
2024-06-01 15:14:31 java.io.IOException: NameNode is not formatted.
2024-06-01 15:14:31     at org.apache.hadoop.hdfs.server.namenode.FSImage.recoverTransitionRead(FSImage.java:253)
2024-06-01 15:14:31     at org.apache.hadoop.hdfs.server.namenode.FSNamesystem.loadFSImage(FSNamesystem.java:1236)
2024-06-01 15:14:31     at org.apache.hadoop.hdfs.server.namenode.FSNamesystem.loadFromDisk(FSNamesystem.java:808)
2024-06-01 15:14:31     at org.apache.hadoop.hdfs.server.namenode.NameNode.loadNamesystem(NameNode.java:694)
2024-06-01 15:14:31     at org.apache.hadoop.hdfs.server.namenode.NameNode.initialize(NameNode.java:781)
2024-06-01 15:14:31     at org.apache.hadoop.hdfs.server.namenode.NameNode.<init>(NameNode.java:1033)
2024-06-01 15:14:31     at org.apache.hadoop.hdfs.server.namenode.NameNode.<init>(NameNode.java:1008)
2024-06-01 15:14:31     at org.apache.hadoop.hdfs.server.namenode.NameNode.createNameNode(NameNode.java:1782)
2024-06-01 15:14:31     at org.apache.hadoop.hdfs.server.namenode.NameNode.main(NameNode.java:1847)
2024-06-01 15:14:31 2024-06-01 07:14:31 INFO  ContextHandler:1159 - Stopped o.e.j.w.WebAppContext@6057aebb{hdfs,/,null,STOPPED}{file:/opt/hadoop/share/hadoop/hdfs/webapps/hdfs}
2024-06-01 15:14:31 2024-06-01 07:14:31 INFO  AbstractConnector:383 - Stopped ServerConnector@2f01783a{HTTP/1.1, (http/1.1)}{0.0.0.0:9870}
2024-06-01 15:14:31 2024-06-01 07:14:31 INFO  session:149 - node0 Stopped scavenging
2024-06-01 15:14:31 2024-06-01 07:14:31 INFO  ContextHandler:1159 - Stopped o.e.j.s.ServletContextHandler@4dc27487{static,/static,file:///opt/hadoop/share/hadoop/hdfs/webapps/static/,STOPPED}
2024-06-01 15:14:31 2024-06-01 07:14:31 INFO  ContextHandler:1159 - Stopped o.e.j.s.ServletContextHandler@71687585{logs,/logs,file:///var/log/hadoop/,STOPPED}
2024-06-01 15:14:31 2024-06-01 07:14:31 INFO  MetricsSystemImpl:210 - Stopping NameNode metrics system...
2024-06-01 15:14:31 2024-06-01 07:14:31 INFO  MetricsSystemImpl:216 - NameNode metrics system stopped.
2024-06-01 15:14:31 2024-06-01 07:14:31 INFO  MetricsSystemImpl:611 - NameNode metrics system shutdown complete.
2024-06-01 15:14:31 2024-06-01 07:14:31 ERROR NameNode:1852 - Failed to start namenode.
```
