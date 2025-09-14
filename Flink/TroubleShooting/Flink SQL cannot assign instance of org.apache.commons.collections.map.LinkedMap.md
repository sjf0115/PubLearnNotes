## 1. 问题

在使用 Flink 消费 Kafka 时，抛出如下异常：
```java
2025-09-14 19:05:12
org.apache.flink.runtime.JobException: Recovery is suppressed by NoRestartBackoffTimeStrategy
	at org.apache.flink.runtime.executiongraph.failover.flip1.ExecutionFailureHandler.handleFailure(ExecutionFailureHandler.java:138)
	at org.apache.flink.runtime.executiongraph.failover.flip1.ExecutionFailureHandler.getFailureHandlingResult(ExecutionFailureHandler.java:82)
	at org.apache.flink.runtime.scheduler.DefaultScheduler.handleTaskFailure(DefaultScheduler.java:216)
	at org.apache.flink.runtime.scheduler.DefaultScheduler.maybeHandleTaskFailure(DefaultScheduler.java:206)
	at org.apache.flink.runtime.scheduler.DefaultScheduler.updateTaskExecutionStateInternal(DefaultScheduler.java:197)
	at org.apache.flink.runtime.scheduler.SchedulerBase.updateTaskExecutionState(SchedulerBase.java:682)
	at org.apache.flink.runtime.scheduler.SchedulerNG.updateTaskExecutionState(SchedulerNG.java:79)
	at org.apache.flink.runtime.jobmaster.JobMaster.updateTaskExecutionState(JobMaster.java:435)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at org.apache.flink.runtime.rpc.akka.AkkaRpcActor.handleRpcInvocation(AkkaRpcActor.java:305)
	at org.apache.flink.runtime.rpc.akka.AkkaRpcActor.handleRpcMessage(AkkaRpcActor.java:212)
	at org.apache.flink.runtime.rpc.akka.FencedAkkaRpcActor.handleRpcMessage(FencedAkkaRpcActor.java:77)
	at org.apache.flink.runtime.rpc.akka.AkkaRpcActor.handleMessage(AkkaRpcActor.java:158)
	at akka.japi.pf.UnitCaseStatement.apply(CaseStatements.scala:26)
	at akka.japi.pf.UnitCaseStatement.apply(CaseStatements.scala:21)
	at scala.PartialFunction.applyOrElse(PartialFunction.scala:123)
	at scala.PartialFunction.applyOrElse$(PartialFunction.scala:122)
	at akka.japi.pf.UnitCaseStatement.applyOrElse(CaseStatements.scala:21)
	at scala.PartialFunction$OrElse.applyOrElse(PartialFunction.scala:171)
	at scala.PartialFunction$OrElse.applyOrElse(PartialFunction.scala:172)
	at scala.PartialFunction$OrElse.applyOrElse(PartialFunction.scala:172)
	at akka.actor.Actor.aroundReceive(Actor.scala:517)
	at akka.actor.Actor.aroundReceive$(Actor.scala:515)
	at akka.actor.AbstractActor.aroundReceive(AbstractActor.scala:225)
	at akka.actor.ActorCell.receiveMessage(ActorCell.scala:592)
	at akka.actor.ActorCell.invoke(ActorCell.scala:561)
	at akka.dispatch.Mailbox.processMailbox(Mailbox.scala:258)
	at akka.dispatch.Mailbox.run(Mailbox.scala:225)
	at akka.dispatch.Mailbox.exec(Mailbox.scala:235)
	at akka.dispatch.forkjoin.ForkJoinTask.doExec(ForkJoinTask.java:260)
	at akka.dispatch.forkjoin.ForkJoinPool$WorkQueue.runTask(ForkJoinPool.java:1339)
	at akka.dispatch.forkjoin.ForkJoinPool.runWorker(ForkJoinPool.java:1979)
	at akka.dispatch.forkjoin.ForkJoinWorkerThread.run(ForkJoinWorkerThread.java:107)
Caused by: org.apache.flink.streaming.runtime.tasks.StreamTaskException: Cannot instantiate user function.
	at org.apache.flink.streaming.api.graph.StreamConfig.getStreamOperatorFactory(StreamConfig.java:338)
	at org.apache.flink.streaming.runtime.tasks.OperatorChain.<init>(OperatorChain.java:159)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.executeRestore(StreamTask.java:551)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.runWithCleanUpOnFail(StreamTask.java:650)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.restore(StreamTask.java:540)
	at org.apache.flink.runtime.taskmanager.Task.doRun(Task.java:759)
	at org.apache.flink.runtime.taskmanager.Task.run(Task.java:566)
	at java.lang.Thread.run(Thread.java:750)
Caused by: java.lang.ClassCastException: cannot assign instance of org.apache.commons.collections.map.LinkedMap to field org.apache.flink.streaming.connectors.kafka.FlinkKafkaConsumerBase.pendingOffsetsToCommit of type org.apache.commons.collections.map.LinkedMap in instance of org.apache.flink.streaming.connectors.kafka.FlinkKafkaConsumer
	at java.io.ObjectStreamClass$FieldReflector.setObjFieldValues(ObjectStreamClass.java:2302)
	at java.io.ObjectStreamClass.setObjFieldValues(ObjectStreamClass.java:1432)
	at java.io.ObjectInputStream.defaultReadFields(ObjectInputStream.java:2478)
	at java.io.ObjectInputStream.readSerialData(ObjectInputStream.java:2396)
	at java.io.ObjectInputStream.readOrdinaryObject(ObjectInputStream.java:2254)
	at java.io.ObjectInputStream.readObject0(ObjectInputStream.java:1710)
	at java.io.ObjectInputStream.defaultReadFields(ObjectInputStream.java:2472)
	at java.io.ObjectInputStream.readSerialData(ObjectInputStream.java:2396)
	at java.io.ObjectInputStream.readOrdinaryObject(ObjectInputStream.java:2254)
	at java.io.ObjectInputStream.readObject0(ObjectInputStream.java:1710)
	at java.io.ObjectInputStream.defaultReadFields(ObjectInputStream.java:2472)
	at java.io.ObjectInputStream.readSerialData(ObjectInputStream.java:2396)
	at java.io.ObjectInputStream.readOrdinaryObject(ObjectInputStream.java:2254)
	at java.io.ObjectInputStream.readObject0(ObjectInputStream.java:1710)
	at java.io.ObjectInputStream.readObject(ObjectInputStream.java:508)
	at java.io.ObjectInputStream.readObject(ObjectInputStream.java:466)
	at org.apache.flink.util.InstantiationUtil.deserializeObject(InstantiationUtil.java:615)
	at org.apache.flink.util.InstantiationUtil.deserializeObject(InstantiationUtil.java:600)
	at org.apache.flink.util.InstantiationUtil.deserializeObject(InstantiationUtil.java:587)
	at org.apache.flink.util.InstantiationUtil.readObjectFromConfig(InstantiationUtil.java:541)
	at org.apache.flink.streaming.api.graph.StreamConfig.getStreamOperatorFactory(StreamConfig.java:322)
	... 7 more
```

## 2. 解决方案

常见的原因是 Kafka 库与 Flink 的反向类加载方法不兼容。可以通过在 conf/flink-conf.yaml 中添加以下配置并重新启动 Flink 来解决此问题：
```
classloader.resolve-order: parent-first
```
