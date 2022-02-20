
## 1. 问题

在使用 RocksDBStateBackend 启动程序时，抛出如下异常：
```java
java.lang.Exception: Exception while creating StreamOperatorStateContext.
	at org.apache.flink.streaming.api.operators.StreamTaskStateInitializerImpl.streamOperatorStateContext(StreamTaskStateInitializerImpl.java:254)
	at org.apache.flink.streaming.api.operators.AbstractStreamOperator.initializeState(AbstractStreamOperator.java:272)
	at org.apache.flink.streaming.runtime.tasks.OperatorChain.initializeStateAndOpenOperators(OperatorChain.java:427)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.lambda$beforeInvoke$2(StreamTask.java:545)
	at org.apache.flink.streaming.runtime.tasks.StreamTaskActionExecutor$1.runThrowing(StreamTaskActionExecutor.java:50)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.beforeInvoke(StreamTask.java:535)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.invoke(StreamTask.java:575)
	at org.apache.flink.runtime.taskmanager.Task.doRun(Task.java:758)
	at org.apache.flink.runtime.taskmanager.Task.run(Task.java:573)
	at java.lang.Thread.run(Thread.java:748)
Caused by: org.apache.flink.util.FlinkException: Could not restore keyed state backend for StreamMap_20ba6b65f97481d5570070de90e4e791_(1/1) from any of the 1 provided restore options.
	at org.apache.flink.streaming.api.operators.BackendRestorerProcedure.createAndRestore(BackendRestorerProcedure.java:160)
	at org.apache.flink.streaming.api.operators.StreamTaskStateInitializerImpl.keyedStatedBackend(StreamTaskStateInitializerImpl.java:345)
	at org.apache.flink.streaming.api.operators.StreamTaskStateInitializerImpl.streamOperatorStateContext(StreamTaskStateInitializerImpl.java:163)
	... 9 more
Caused by: java.io.IOException: Could not load the native RocksDB library
	at org.apache.flink.contrib.streaming.state.RocksDBStateBackend.ensureRocksDBIsLoaded(RocksDBStateBackend.java:1022)
	at org.apache.flink.contrib.streaming.state.RocksDBStateBackend.createKeyedStateBackend(RocksDBStateBackend.java:531)
	at org.apache.flink.contrib.streaming.state.RocksDBStateBackend.createKeyedStateBackend(RocksDBStateBackend.java:93)
	at org.apache.flink.streaming.api.operators.StreamTaskStateInitializerImpl.lambda$keyedStatedBackend$1(StreamTaskStateInitializerImpl.java:328)
	at org.apache.flink.streaming.api.operators.BackendRestorerProcedure.attemptCreateAndRestore(BackendRestorerProcedure.java:168)
	at org.apache.flink.streaming.api.operators.BackendRestorerProcedure.createAndRestore(BackendRestorerProcedure.java:135)
	... 11 more
Caused by: java.lang.UnsatisfiedLinkError: /private/var/folders/54/crgqfp1n52s6560cqcjp7y9h0000gn/T/rocksdb-lib-d3f651ccf8d3d8d2866ed459b33cef4a/librocksdbjni-osx.jnilib: dlopen(/private/var/folders/54/crgqfp1n52s6560cqcjp7y9h0000gn/T/rocksdb-lib-d3f651ccf8d3d8d2866ed459b33cef4a/librocksdbjni-osx.jnilib, 1): Symbol not found: __ZdlPvSt11align_val_t
  Referenced from: /private/var/folders/54/crgqfp1n52s6560cqcjp7y9h0000gn/T/rocksdb-lib-d3f651ccf8d3d8d2866ed459b33cef4a/librocksdbjni-osx.jnilib
  Expected in: /usr/lib/libc++.1.dylib
 in /private/var/folders/54/crgqfp1n52s6560cqcjp7y9h0000gn/T/rocksdb-lib-d3f651ccf8d3d8d2866ed459b33cef4a/librocksdbjni-osx.jnilib
	at java.lang.ClassLoader$NativeLibrary.load(Native Method)
	at java.lang.ClassLoader.loadLibrary0(ClassLoader.java:1941)
	at java.lang.ClassLoader.loadLibrary(ClassLoader.java:1824)
	at java.lang.Runtime.load0(Runtime.java:809)
	at java.lang.System.load(System.java:1086)
	at org.rocksdb.NativeLibraryLoader.loadLibraryFromJar(NativeLibraryLoader.java:78)
	at org.rocksdb.NativeLibraryLoader.loadLibrary(NativeLibraryLoader.java:56)
	at org.apache.flink.contrib.streaming.state.RocksDBStateBackend.ensureRocksDBIsLoaded(RocksDBStateBackend.java:996)
	... 16 more
```
