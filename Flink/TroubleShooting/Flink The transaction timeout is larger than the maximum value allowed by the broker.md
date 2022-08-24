## 1. 现象

```java
2022-08-24 08:57:01
org.apache.kafka.common.KafkaException: org.apache.kafka.common.KafkaException: Unexpected error in InitProducerIdResponse; The transaction timeout is larger than the maximum value allowed by the broker (as configured by transaction.max.timeout.ms).
	at sun.reflect.NativeConstructorAccessorImpl.newInstance0(Native Method)
	at sun.reflect.NativeConstructorAccessorImpl.newInstance(NativeConstructorAccessorImpl.java:62)
	at sun.reflect.DelegatingConstructorAccessorImpl.newInstance(DelegatingConstructorAccessorImpl.java:45)
	at java.lang.reflect.Constructor.newInstance(Constructor.java:423)
	at java.util.concurrent.ForkJoinTask.getThrowableException(ForkJoinTask.java:593)
	at java.util.concurrent.ForkJoinTask.reportException(ForkJoinTask.java:677)
	at java.util.concurrent.ForkJoinTask.invoke(ForkJoinTask.java:735)
	at java.util.stream.ForEachOps$ForEachOp.evaluateParallel(ForEachOps.java:160)
	at java.util.stream.ForEachOps$ForEachOp$OfRef.evaluateParallel(ForEachOps.java:174)
	at java.util.stream.AbstractPipeline.evaluate(AbstractPipeline.java:233)
	at java.util.stream.ReferencePipeline.forEach(ReferencePipeline.java:418)
	at java.util.stream.ReferencePipeline$Head.forEach(ReferencePipeline.java:583)
	at org.apache.flink.streaming.connectors.kafka.FlinkKafkaProducer.abortTransactions(FlinkKafkaProducer.java:1263)
	at org.apache.flink.streaming.connectors.kafka.FlinkKafkaProducer.initializeState(FlinkKafkaProducer.java:1189)
	at org.apache.flink.streaming.util.functions.StreamingFunctionUtils.tryRestoreFunction(StreamingFunctionUtils.java:189)
	at org.apache.flink.streaming.util.functions.StreamingFunctionUtils.restoreFunctionState(StreamingFunctionUtils.java:171)
	at org.apache.flink.streaming.api.operators.AbstractUdfStreamOperator.initializeState(AbstractUdfStreamOperator.java:96)
	at org.apache.flink.streaming.api.operators.StreamOperatorStateHandler.initializeOperatorState(StreamOperatorStateHandler.java:118)
	at org.apache.flink.streaming.api.operators.AbstractStreamOperator.initializeState(AbstractStreamOperator.java:290)
	at org.apache.flink.streaming.runtime.tasks.OperatorChain.initializeStateAndOpenOperators(OperatorChain.java:441)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.restoreGates(StreamTask.java:585)
	at org.apache.flink.streaming.runtime.tasks.StreamTaskActionExecutor$1.call(StreamTaskActionExecutor.java:55)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.executeRestore(StreamTask.java:565)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.runWithCleanUpOnFail(StreamTask.java:650)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.restore(StreamTask.java:540)
	at org.apache.flink.runtime.taskmanager.Task.doRun(Task.java:759)
	at org.apache.flink.runtime.taskmanager.Task.run(Task.java:566)
	at java.lang.Thread.run(Thread.java:748)
Caused by: org.apache.kafka.common.KafkaException: Unexpected error in InitProducerIdResponse; The transaction timeout is larger than the maximum value allowed by the broker (as configured by transaction.max.timeout.ms).
	at org.apache.kafka.clients.producer.internals.TransactionManager$InitProducerIdHandler.handleResponse(TransactionManager.java:1352)
	at org.apache.kafka.clients.producer.internals.TransactionManager$TxnRequestHandler.onComplete(TransactionManager.java:1260)
	at org.apache.kafka.clients.ClientResponse.onComplete(ClientResponse.java:109)
	at org.apache.kafka.clients.NetworkClient.completeResponses(NetworkClient.java:571)
	at org.apache.kafka.clients.NetworkClient.poll(NetworkClient.java:563)
	at org.apache.kafka.clients.producer.internals.Sender.maybeSendAndPollTransactionalRequest(Sender.java:414)
	at org.apache.kafka.clients.producer.internals.Sender.runOnce(Sender.java:312)
	at org.apache.kafka.clients.producer.internals.Sender.run(Sender.java:239)
	... 1 more
```

## 2. 解决方案

```
producerProps.put("transaction.timeout.ms", "5000");
```

https://nightlies.apache.org/flink/flink-docs-release-1.13/docs/connectors/datastream/kafka/#kafka-producers-and-fault-tolerance
