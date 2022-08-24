## 1. 现象

```
2022-08-24 23:06:07
org.apache.flink.util.FlinkRuntimeException: Committing one of transactions failed, logging first encountered failure
	at org.apache.flink.streaming.api.functions.sink.TwoPhaseCommitSinkFunction.notifyCheckpointComplete(TwoPhaseCommitSinkFunction.java:295)
	at org.apache.flink.streaming.api.operators.AbstractUdfStreamOperator.notifyCheckpointComplete(AbstractUdfStreamOperator.java:130)
	at org.apache.flink.streaming.runtime.tasks.StreamOperatorWrapper.notifyCheckpointComplete(StreamOperatorWrapper.java:99)
	at org.apache.flink.streaming.runtime.tasks.SubtaskCheckpointCoordinatorImpl.notifyCheckpointComplete(SubtaskCheckpointCoordinatorImpl.java:334)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.notifyCheckpointComplete(StreamTask.java:1171)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.lambda$notifyCheckpointCompleteAsync$10(StreamTask.java:1136)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.lambda$notifyCheckpointOperation$12(StreamTask.java:1159)
	at org.apache.flink.streaming.runtime.tasks.StreamTaskActionExecutor$1.runThrowing(StreamTaskActionExecutor.java:50)
	at org.apache.flink.streaming.runtime.tasks.mailbox.Mail.run(Mail.java:90)
	at org.apache.flink.streaming.runtime.tasks.mailbox.MailboxProcessor.processMailsWhenDefaultActionUnavailable(MailboxProcessor.java:344)
	at org.apache.flink.streaming.runtime.tasks.mailbox.MailboxProcessor.processMail(MailboxProcessor.java:330)
	at org.apache.flink.streaming.runtime.tasks.mailbox.MailboxProcessor.runMailboxLoop(MailboxProcessor.java:202)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.runMailboxLoop(StreamTask.java:684)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.executeInvoke(StreamTask.java:639)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.runWithCleanUpOnFail(StreamTask.java:650)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.invoke(StreamTask.java:623)
	at org.apache.flink.runtime.taskmanager.Task.doRun(Task.java:779)
	at org.apache.flink.runtime.taskmanager.Task.run(Task.java:566)
	at java.lang.Thread.run(Thread.java:748)
Caused by: org.apache.kafka.common.errors.ProducerFencedException: Producer attempted an operation with an old epoch. Either there is a newer producer with the same transactionalId, or the producer's transaction has been expired by the broker.
```





参考：https://zhuanlan.zhihu.com/p/342046939
