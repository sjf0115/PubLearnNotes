MapReduce作业运行时，任务可能会失败，报out of memory错误。这个时候可以采用以下几个过程调优

简单粗暴： 加大内存

哪个阶段报错就增加那个阶段的内存。以reduce阶段为例，map阶段的类似
```
mapreduce.reduce.memory.mb=5120   //设置reduce container的内存大小
mapreduce.reduce.java.opts=-Xms2000m -Xmx4600m; //设置reduce任务的JVM参数
```

https://blog.csdn.net/dxl342/article/details/53079155
https://blog.csdn.net/jiewuyou/article/details/50592233

https://stackoverflow.com/questions/24070557/what-is-the-relation-between-mapreduce-map-memory-mb-and-mapred-map-child-jav



```
18/04/26 14:48:30 INFO mapreduce.Job: Task Id : attempt_1504162679223_22379281_r_000024_0, Status : FAILED
Container [pid=38228,containerID=container_1504162679223_22379281_01_000455] is running beyond physical memory limits. Current usage: 4.1 GB of 4 GB physical memory used; 5.9 GB of 80 GB virtual memory used. Killing container.
Dump of the process-tree for container_1504162679223_22379281_01_000455 :
        |- PID PPID PGRPID SESSID CMD_NAME USER_MODE_TIME(MILLIS) SYSTEM_TIME(MILLIS) VMEM_USAGE(BYTES) RSSMEM_USAGE(PAGES) FULL_CMD_LINE
        |- 38233 38228 38228 38228 (java) 3589 746 6257569792 1080177 /home/q/java/jdk1.8.0_25/bin/java -Djava.net.preferIPv4Stack=true -Dhadoop.metrics.log.level=WARN -Xmx4096m -XX:+UseParallelGC -XX:ParallelGCThreads=2 -Djava.io.tmpdir=/data12/hadoop2x/nm-local-dir/usercache/wirelessdev/appcache/application_1504162679223_22379281/container_1504162679223_22379281_01_000455/tmp -Dlog4j.configuration=container-log4j.properties -Dyarn.app.container.log.dir=/data9/hadoop2x/userlogs/application_1504162679223_22379281/container_1504162679223_22379281_01_000455 -Dyarn.app.container.log.filesize=0 -Dhadoop.root.logger=INFO,CLA org.apache.hadoop.mapred.YarnChild 10.95.40.218 42292 attempt_1504162679223_22379281_r_000024_0 455
        |- 38228 39993 38228 38228 (bash) 0 2 108650496 296 /bin/bash -c /home/q/java/jdk1.8.0_25/bin/java -Djava.net.preferIPv4Stack=true -Dhadoop.metrics.log.level=WARN  -Xmx4096m -XX:+UseParallelGC -XX:ParallelGCThreads=2 -Djava.io.tmpdir=/data12/hadoop2x/nm-local-dir/usercache/wirelessdev/appcache/application_1504162679223_22379281/container_1504162679223_22379281_01_000455/tmp -Dlog4j.configuration=container-log4j.properties -Dyarn.app.container.log.dir=/data9/hadoop2x/userlogs/application_1504162679223_22379281/container_1504162679223_22379281_01_000455 -Dyarn.app.container.log.filesize=0 -Dhadoop.root.logger=INFO,CLA org.apache.hadoop.mapred.YarnChild 10.95.40.218 42292 attempt_1504162679223_22379281_r_000024_0 455 1>/data9/hadoop2x/userlogs/application_1504162679223_22379281/container_1504162679223_22379281_01_000455/stdout 2>/data9/hadoop2x/userlogs/application_1504162679223_22379281/container_1504162679223_22379281_01_000455/stderr  

Container killed on request. Exit code is 143
```



```
2018-04-26 16:39:39,269 FATAL [main] org.apache.hadoop.mapred.YarnChild: Error running child : java.lang.OutOfMemoryError: GC overhead limit exceeded
	at org.apache.hadoop.mapred.IFile$Reader.nextRawValue(IFile.java:441)
	at org.apache.hadoop.mapred.Merger$Segment.nextRawValue(Merger.java:327)
	at org.apache.hadoop.mapred.Merger$Segment.getValue(Merger.java:309)
	at org.apache.hadoop.mapred.Merger$MergeQueue.next(Merger.java:533)
	at org.apache.hadoop.mapred.ReduceTask$4.next(ReduceTask.java:619)
	at org.apache.hadoop.mapreduce.task.ReduceContextImpl.nextKeyValue(ReduceContextImpl.java:154)
	at org.apache.hadoop.mapreduce.task.ReduceContextImpl$ValueIterator.next(ReduceContextImpl.java:237)
	at com.qunar.search.promote.AdvPushPromoteOrderFeature$AdvPushPromoteOverallReducer.reduce(AdvPushPromoteOrderFeature.java:126)
	at com.qunar.search.promote.AdvPushPromoteOrderFeature$AdvPushPromoteOverallReducer.reduce(AdvPushPromoteOrderFeature.java:98)
	at org.apache.hadoop.mapreduce.Reducer.run(Reducer.java:171)
	at org.apache.hadoop.mapred.ReduceTask.runNewReducer(ReduceTask.java:645)
	at org.apache.hadoop.mapred.ReduceTask.run(ReduceTask.java:405)
	at org.apache.hadoop.mapred.YarnChild$2.run(YarnChild.java:162)
	at java.security.AccessController.doPrivileged(Native Method)
	at javax.security.auth.Subject.doAs(Subject.java:422)
	at org.apache.hadoop.security.UserGroupInformation.doAs(UserGroupInformation.java:1491)
	at org.apache.hadoop.mapred.YarnChild.main(YarnChild.java:157)
```
