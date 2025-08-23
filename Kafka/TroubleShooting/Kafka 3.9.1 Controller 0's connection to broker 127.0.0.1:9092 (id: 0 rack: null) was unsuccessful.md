

```
[2025-08-20 23:10:31,678] INFO [ReplicaStateMachine controllerId=0] Triggering online replica state changes (kafka.controller.ZkReplicaStateMachine)
[2025-08-20 23:10:31,682] WARN [RequestSendThread controllerId=0] Controller 0's connection to broker 127.0.0.1:9092 (id: 0 rack: null) was unsuccessful (kafka.controller.RequestSendThread)
java.io.IOException: Connection to 127.0.0.1:9092 (id: 0 rack: null) failed.
        at org.apache.kafka.clients.NetworkClientUtils.awaitReady(NetworkClientUtils.java:71)
        at kafka.controller.RequestSendThread.brokerReady(ControllerChannelManager.scala:299)
        at kafka.controller.RequestSendThread.doWork(ControllerChannelManager.scala:252)
        at org.apache.kafka.server.util.ShutdownableThread.run(ShutdownableThread.java:136)
[2025-08-20 23:10:31,687] INFO [ReplicaStateMachine controllerId=0] Triggering offline replica state changes (kafka.controller.ZkReplicaStateMachine)
```
