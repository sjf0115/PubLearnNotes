


```
I have no name!@spark-master:/opt/bitnami/spark$ bin/spark-submit \
    --master yarn \
    --deploy-mode cluster \
    --class org.apache.spark.examples.SparkPi \
    /opt/bitnami/spark/examples/jars/spark-examples_2.12-3.5.0.jar \
    1000
25/03/10 14:59:18 WARN NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
25/03/10 14:59:18 INFO DefaultNoHARMFailoverProxyProvider: Connecting to ResourceManager at resourcemanager/172.21.0.6:8032
25/03/10 14:59:18 INFO AHSProxy: Connecting to Application History server at historyserver/172.21.0.8:10200
25/03/10 14:59:19 INFO Configuration: resource-types.xml not found
25/03/10 14:59:19 INFO ResourceUtils: Unable to find 'resource-types.xml'.
25/03/10 14:59:19 INFO Client: Verifying our application has not requested more than the maximum memory capability of the cluster (8192 MB per container)
25/03/10 14:59:19 INFO Client: Will allocate AM container, with 1408 MB memory including 384 MB overhead
25/03/10 14:59:19 INFO Client: Setting up container launch context for our AM
25/03/10 14:59:19 INFO Client: Setting up the launch environment for our AM container
25/03/10 14:59:19 INFO Client: Preparing resources for our AM container
25/03/10 14:59:19 WARN Client: Neither spark.yarn.jars nor spark.yarn.archive is set, falling back to uploading libraries under SPARK_HOME.
25/03/10 14:59:29 INFO Client: Uploading resource file:/tmp/spark-e585cb79-fb57-4636-a1b8-55312284bc60/__spark_libs__1823642903416740548.zip -> hdfs://namenode:9000/user/spark/.sparkStaging/application_1741617430753_0004/__spark_libs__1823642903416740548.zip
25/03/10 14:59:35 INFO Client: Uploading resource file:/opt/bitnami/spark/examples/jars/spark-examples_2.12-3.5.0.jar -> hdfs://namenode:9000/user/spark/.sparkStaging/application_1741617430753_0004/spark-examples_2.12-3.5.0.jar
25/03/10 14:59:36 INFO Client: Uploading resource file:/tmp/spark-e585cb79-fb57-4636-a1b8-55312284bc60/__spark_conf__16880872893869355967.zip -> hdfs://namenode:9000/user/spark/.sparkStaging/application_1741617430753_0004/__spark_conf__.zip
25/03/10 14:59:36 INFO SecurityManager: Changing view acls to: spark
25/03/10 14:59:36 INFO SecurityManager: Changing modify acls to: spark
25/03/10 14:59:36 INFO SecurityManager: Changing view acls groups to:
25/03/10 14:59:36 INFO SecurityManager: Changing modify acls groups to:
25/03/10 14:59:36 INFO SecurityManager: SecurityManager: authentication disabled; ui acls disabled; users with view permissions: spark; groups with view permissions: EMPTY; users with modify permissions: spark; groups with modify permissions: EMPTY
25/03/10 14:59:36 INFO Client: Submitting application application_1741617430753_0004 to ResourceManager
25/03/10 14:59:38 INFO YarnClientImpl: Submitted application application_1741617430753_0004
25/03/10 14:59:39 INFO Client: Application report for application_1741617430753_0004 (state: ACCEPTED)
25/03/10 14:59:39 INFO Client:
	 client token: N/A
	 diagnostics: AM container is launched, waiting for AM container to Register with RM
	 ApplicationMaster host: N/A
	 ApplicationMaster RPC port: -1
	 queue: default
	 start time: 1741618777016
	 final status: UNDEFINED
	 tracking URL: http://resourcemanager:8088/proxy/application_1741617430753_0004/
	 user: spark
25/03/10 14:59:52 INFO Client: Application report for application_1741617430753_0004 (state: FAILED)
25/03/10 14:59:52 INFO Client:
	 client token: N/A
	 diagnostics: Application application_1741617430753_0004 failed 2 times due to AM Container for appattempt_1741617430753_0004_000002 exited with  exitCode: 1
Failing this attempt.Diagnostics: [2025-03-10 14:59:50.804]Exception from container-launch.
Container id: container_e09_1741617430753_0004_02_000001
Exit code: 1

[2025-03-10 14:59:50.816]Container exited with a non-zero exit code 1. Error file: prelaunch.err.
Last 4096 bytes of prelaunch.err :
Last 4096 bytes of stderr :
Error: Could not find or load main class java.base.sun.nio.ch=ALL-UNNAMED


[2025-03-10 14:59:50.816]Container exited with a non-zero exit code 1. Error file: prelaunch.err.
Last 4096 bytes of prelaunch.err :
Last 4096 bytes of stderr :
Error: Could not find or load main class java.base.sun.nio.ch=ALL-UNNAMED


For more detailed output, check the application tracking page: http://historyserver:8188/applicationhistory/app/application_1741617430753_0004 Then click on links to logs of each attempt.
. Failing the application.
	 ApplicationMaster host: N/A
	 ApplicationMaster RPC port: -1
	 queue: default
	 start time: 1741618777016
	 final status: FAILED
	 tracking URL: http://historyserver:8188/applicationhistory/app/application_1741617430753_0004
	 user: spark
25/03/10 14:59:52 INFO Client: Deleted staging directory hdfs://namenode:9000/user/spark/.sparkStaging/application_1741617430753_0004
25/03/10 14:59:52 ERROR Client: Application diagnostics message: Application application_1741617430753_0004 failed 2 times due to AM Container for appattempt_1741617430753_0004_000002 exited with  exitCode: 1
Failing this attempt.Diagnostics: [2025-03-10 14:59:50.804]Exception from container-launch.
Container id: container_e09_1741617430753_0004_02_000001
Exit code: 1

[2025-03-10 14:59:50.816]Container exited with a non-zero exit code 1. Error file: prelaunch.err.
Last 4096 bytes of prelaunch.err :
Last 4096 bytes of stderr :
Error: Could not find or load main class java.base.sun.nio.ch=ALL-UNNAMED


[2025-03-10 14:59:50.816]Container exited with a non-zero exit code 1. Error file: prelaunch.err.
Last 4096 bytes of prelaunch.err :
Last 4096 bytes of stderr :
Error: Could not find or load main class java.base.sun.nio.ch=ALL-UNNAMED


For more detailed output, check the application tracking page: http://historyserver:8188/applicationhistory/app/application_1741617430753_0004 Then click on links to logs of each attempt.
. Failing the application.
Exception in thread "main" org.apache.spark.SparkException: Application application_1741617430753_0004 finished with failed status
	at org.apache.spark.deploy.yarn.Client.run(Client.scala:1309)
	at org.apache.spark.deploy.yarn.YarnClusterApplication.start(Client.scala:1742)
	at org.apache.spark.deploy.SparkSubmit.org$apache$spark$deploy$SparkSubmit$$runMain(SparkSubmit.scala:1029)
	at org.apache.spark.deploy.SparkSubmit.doRunMain$1(SparkSubmit.scala:194)
	at org.apache.spark.deploy.SparkSubmit.submit(SparkSubmit.scala:217)
	at org.apache.spark.deploy.SparkSubmit.doSubmit(SparkSubmit.scala:91)
	at org.apache.spark.deploy.SparkSubmit$$anon$2.doSubmit(SparkSubmit.scala:1120)
	at org.apache.spark.deploy.SparkSubmit$.main(SparkSubmit.scala:1129)
	at org.apache.spark.deploy.SparkSubmit.main(SparkSubmit.scala)
25/03/10 14:59:52 INFO ShutdownHookManager: Shutdown hook called
25/03/10 14:59:52 INFO ShutdownHookManager: Deleting directory /tmp/spark-88e61db7-3ac5-4c4e-afa1-29cb91784897
25/03/10 14:59:52 INFO ShutdownHookManager: Deleting directory /tmp/spark-e585cb79-fb57-4636-a1b8-55312284bc60
```




I have no name!@spark-master:/opt/bitnami/spark$ bin/spark-submit \
    --master yarn \
    --deploy-mode client \
    --class org.apache.spark.examples.SparkPi \
    /opt/bitnami/spark/examples/jars/spark-examples_2.12-3.5.0.jar \
    1000
25/03/10 15:14:57 INFO SparkContext: Running Spark version 3.5.0
25/03/10 15:14:57 INFO SparkContext: OS info Linux, 6.6.22-linuxkit, amd64
25/03/10 15:14:57 INFO SparkContext: Java version 17.0.10
25/03/10 15:14:57 INFO ResourceUtils: ==============================================================
25/03/10 15:14:57 INFO ResourceUtils: No custom resources configured for spark.driver.
25/03/10 15:14:57 INFO ResourceUtils: ==============================================================
25/03/10 15:14:57 INFO SparkContext: Submitted application: Spark Pi
25/03/10 15:14:57 INFO ResourceProfile: Default ResourceProfile created, executor resources: Map(cores -> name: cores, amount: 1, script: , vendor: , memory -> name: memory, amount: 1024, script: , vendor: , offHeap -> name: offHeap, amount: 0, script: , vendor: ), task resources: Map(cpus -> name: cpus, amount: 1.0)
25/03/10 15:14:57 INFO ResourceProfile: Limiting resource is cpus at 1 tasks per executor
25/03/10 15:14:57 INFO ResourceProfileManager: Added ResourceProfile id: 0
25/03/10 15:14:57 INFO SecurityManager: Changing view acls to: spark
25/03/10 15:14:57 INFO SecurityManager: Changing modify acls to: spark
25/03/10 15:14:57 INFO SecurityManager: Changing view acls groups to:
25/03/10 15:14:57 INFO SecurityManager: Changing modify acls groups to:
25/03/10 15:14:57 INFO SecurityManager: SecurityManager: authentication disabled; ui acls disabled; users with view permissions: spark; groups with view permissions: EMPTY; users with modify permissions: spark; groups with modify permissions: EMPTY
25/03/10 15:14:58 WARN NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
25/03/10 15:14:58 INFO Utils: Successfully started service 'sparkDriver' on port 44465.
25/03/10 15:14:58 INFO SparkEnv: Registering MapOutputTracker
25/03/10 15:14:58 INFO SparkEnv: Registering BlockManagerMaster
25/03/10 15:14:58 INFO BlockManagerMasterEndpoint: Using org.apache.spark.storage.DefaultTopologyMapper for getting topology information
25/03/10 15:14:58 INFO BlockManagerMasterEndpoint: BlockManagerMasterEndpoint up
25/03/10 15:14:58 INFO SparkEnv: Registering BlockManagerMasterHeartbeat
25/03/10 15:14:58 INFO DiskBlockManager: Created local directory at /tmp/blockmgr-2ade03d7-5608-4e84-9b73-e2aa3d20bf67
25/03/10 15:14:58 INFO MemoryStore: MemoryStore started with capacity 434.4 MiB
25/03/10 15:14:58 INFO SparkEnv: Registering OutputCommitCoordinator
25/03/10 15:14:59 INFO JettyUtils: Start Jetty 0.0.0.0:4040 for SparkUI
25/03/10 15:14:59 INFO Utils: Successfully started service 'SparkUI' on port 4040.
25/03/10 15:14:59 INFO SparkContext: Added JAR file:/opt/bitnami/spark/examples/jars/spark-examples_2.12-3.5.0.jar at spark://spark-master:44465/jars/spark-examples_2.12-3.5.0.jar with timestamp 1741619697661
25/03/10 15:14:59 INFO DefaultNoHARMFailoverProxyProvider: Connecting to ResourceManager at resourcemanager/172.21.0.6:8032
25/03/10 15:15:00 INFO AHSProxy: Connecting to Application History server at historyserver/172.21.0.8:10200
25/03/10 15:15:00 INFO Configuration: resource-types.xml not found
25/03/10 15:15:00 INFO ResourceUtils: Unable to find 'resource-types.xml'.
25/03/10 15:15:00 INFO Client: Verifying our application has not requested more than the maximum memory capability of the cluster (8192 MB per container)
25/03/10 15:15:00 INFO Client: Will allocate AM container, with 896 MB memory including 384 MB overhead
25/03/10 15:15:00 INFO Client: Setting up container launch context for our AM
25/03/10 15:15:00 INFO Client: Setting up the launch environment for our AM container
25/03/10 15:15:00 INFO Client: Preparing resources for our AM container
25/03/10 15:15:00 WARN Client: Neither spark.yarn.jars nor spark.yarn.archive is set, falling back to uploading libraries under SPARK_HOME.
25/03/10 15:15:19 INFO Client: Uploading resource file:/tmp/spark-f4460c90-cd8c-4520-b35a-fc1380562bfe/__spark_libs__13777774246483308415.zip -> hdfs://namenode:9000/user/spark/.sparkStaging/application_1741617430753_0005/__spark_libs__13777774246483308415.zip



5/03/10 15:15:37 INFO SecurityManager: SecurityManager: authentication disabled; ui acls disabled; users with view permissions: spark; groups with view permissions: EMPTY; users with modify permissions: spark; groups with modify permissions: EMPTY
25/03/10 15:15:38 INFO Client: Submitting application application_1741617430753_0005 to ResourceManager
25/03/10 15:15:38 INFO YarnClientImpl: Submitted application application_1741617430753_0005
25/03/10 15:15:39 INFO Client: Application report for application_1741617430753_0005 (state: ACCEPTED)
25/03/10 15:15:39 INFO Client:
	 client token: N/A
	 diagnostics: [Mon Mar 10 15:15:39 +0000 2025] Scheduler has assigned a container for AM, waiting for AM container to be launched
	 ApplicationMaster host: N/A
	 ApplicationMaster RPC port: -1
	 queue: default
	 start time: 1741619738140
	 final status: UNDEFINED
	 tracking URL: http://resourcemanager:8088/proxy/application_1741617430753_0005/
	 user: spark
25/03/10 15:16:03 INFO Client: Application report for application_1741617430753_0005 (state: RUNNING)
25/03/10 15:16:03 INFO Client:
	 client token: N/A
	 diagnostics: N/A
	 ApplicationMaster host: 172.21.0.5
	 ApplicationMaster RPC port: -1
	 queue: default
	 start time: 1741619738140
	 final status: UNDEFINED
	 tracking URL: http://resourcemanager:8088/proxy/application_1741617430753_0005/
	 user: spark
25/03/10 15:16:03 INFO YarnClientSchedulerBackend: Application application_1741617430753_0005 has started running.
25/03/10 15:16:03 INFO Utils: Successfully started service 'org.apache.spark.network.netty.NettyBlockTransferService' on port 38317.
25/03/10 15:16:03 INFO NettyBlockTransferService: Server created on spark-master:38317
25/03/10 15:16:03 INFO BlockManager: Using org.apache.spark.storage.RandomBlockReplicationPolicy for block replication policy
25/03/10 15:16:03 INFO BlockManagerMaster: Registering BlockManager BlockManagerId(driver, spark-master, 38317, None)
25/03/10 15:16:03 INFO BlockManagerMasterEndpoint: Registering block manager spark-master:38317 with 434.4 MiB RAM, BlockManagerId(driver, spark-master, 38317, None)
25/03/10 15:16:03 INFO BlockManagerMaster: Registered BlockManager BlockManagerId(driver, spark-master, 38317, None)
25/03/10 15:16:03 INFO BlockManager: Initialized BlockManager: BlockManagerId(driver, spark-master, 38317, None)
25/03/10 15:16:04 INFO YarnClientSchedulerBackend: Add WebUI Filter. org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter, Map(PROXY_HOSTS -> resourcemanager, PROXY_URI_BASES -> http://resourcemanager:8088/proxy/application_1741617430753_0005), /proxy/application_1741617430753_0005
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /jobs: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /jobs/json: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /jobs/job: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /jobs/job/json: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /stages: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /stages/json: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /stages/stage: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /stages/stage/json: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /stages/pool: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /stages/pool/json: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /storage: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /storage/json: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /storage/rdd: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /storage/rdd/json: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /environment: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /environment/json: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /executors: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /executors/json: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /executors/threadDump: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /executors/threadDump/json: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /executors/heapHistogram: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /executors/heapHistogram/json: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:04 INFO ServerInfo: Adding filter to /static: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:05 INFO ServerInfo: Adding filter to /: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:05 INFO ServerInfo: Adding filter to /api: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:05 INFO ServerInfo: Adding filter to /jobs/job/kill: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:05 INFO ServerInfo: Adding filter to /stages/stage/kill: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:05 INFO ServerInfo: Adding filter to /metrics/json: org.apache.hadoop.yarn.server.webproxy.amfilter.AmIpFilter
25/03/10 15:16:05 INFO YarnClientSchedulerBackend: SchedulerBackend is ready for scheduling beginning after waiting maxRegisteredResourcesWaitingTime: 30000000000(ns)
25/03/10 15:16:05 INFO YarnSchedulerBackend$YarnSchedulerEndpoint: ApplicationMaster registered as NettyRpcEndpointRef(spark-client://YarnAM)
25/03/10 15:16:08 INFO SparkContext: Starting job: reduce at SparkPi.scala:38
25/03/10 15:16:08 INFO DAGScheduler: Got job 0 (reduce at SparkPi.scala:38) with 1000 output partitions
25/03/10 15:16:08 INFO DAGScheduler: Final stage: ResultStage 0 (reduce at SparkPi.scala:38)
25/03/10 15:16:08 INFO DAGScheduler: Parents of final stage: List()
25/03/10 15:16:08 INFO DAGScheduler: Missing parents: List()
25/03/10 15:16:08 INFO DAGScheduler: Submitting ResultStage 0 (MapPartitionsRDD[1] at map at SparkPi.scala:34), which has no missing parents
25/03/10 15:16:09 INFO MemoryStore: Block broadcast_0 stored as values in memory (estimated size 4.0 KiB, free 434.4 MiB)
25/03/10 15:16:09 INFO MemoryStore: Block broadcast_0_piece0 stored as bytes in memory (estimated size 2.3 KiB, free 434.4 MiB)
25/03/10 15:16:09 INFO BlockManagerInfo: Added broadcast_0_piece0 in memory on spark-master:38317 (size: 2.3 KiB, free: 434.4 MiB)
25/03/10 15:16:09 INFO SparkContext: Created broadcast 0 from broadcast at DAGScheduler.scala:1580
25/03/10 15:16:10 INFO DAGScheduler: Submitting 1000 missing tasks from ResultStage 0 (MapPartitionsRDD[1] at map at SparkPi.scala:34) (first 15 tasks are for partitions Vector(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14))
25/03/10 15:16:10 INFO YarnScheduler: Adding task set 0.0 with 1000 tasks resource profile 0
