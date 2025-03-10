## 1. 问题

在使用 spark-submit 以 cluster 模式向 Yarn 提交作业之后还没等作业执行完成就退出：
```java
25/03/10 14:46:18 INFO ClientEndpoint: Driver successfully submitted as driver-20250310144617-0000
25/03/10 14:46:22 INFO ClientEndpoint: State of driver-20250310144617-0000 is RUNNING
25/03/10 14:46:22 INFO ClientEndpoint: Driver running on 172.21.0.3:41839 (worker-20250310143614-172.21.0.3-41839)
25/03/10 14:46:22 INFO ClientEndpoint: spark-submit not configured to wait for completion, exiting spark-submit JVM.
25/03/10 14:46:22 INFO ShutdownHookManager: Shutdown hook called
25/03/10 14:46:22 INFO ShutdownHookManager: Deleting directory /tmp/spark-c81ee881-8a11-4fab-bfdc-68121490d7d5
```

## 2. 解决方案

方法很简单，可以通过在使用spark-submit时设置--conf spark.yarn.submit.waitAppCompletion = false来实现。 这样，客户端将在成功提交spark程序申请后将会自动退出。

https://blog.csdn.net/yolohohohoho/article/details/89977897
