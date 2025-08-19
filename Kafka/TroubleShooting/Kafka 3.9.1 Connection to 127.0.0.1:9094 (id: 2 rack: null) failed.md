
```
[2025-08-19 23:29:32,346] INFO [Controller id=0] New broker startup callback for 1 (kafka.controller.KafkaController)
[2025-08-19 23:29:32,347] WARN [RequestSendThread controllerId=0] Controller 0's connection to broker 127.0.0.1:9093 (id: 1 rack: null) was unsuccessful (kafka.controller.RequestSendThread)
java.io.IOException: Connection to 127.0.0.1:9093 (id: 1 rack: null) failed.
        at org.apache.kafka.clients.NetworkClientUtils.awaitReady(NetworkClientUtils.java:71)
        at kafka.controller.RequestSendThread.brokerReady(ControllerChannelManager.scala:299)
        at kafka.controller.RequestSendThread.doWork(ControllerChannelManager.scala:252)
        at org.apache.kafka.server.util.ShutdownableThread.run(ShutdownableThread.java:136)
[2025-08-19 23:29:32,348] DEBUG [Controller id=0] Register BrokerModifications handler for Vector(1) (kafka.controller.KafkaController)
[2025-08-19 23:29:32,349] INFO [Controller id=0] Updated broker epochs cache: Map(1 -> 21474836589, 0 -> 21474836569) (kafka.controller.KafkaController)
[2025-08-19 23:29:32,365] INFO [ControllerEventThread controllerId=1] Starting (kafka.controller.ControllerEventManager$ControllerEventThread)
[2025-08-19 23:29:32,371] DEBUG [Controller id=1] Broker 0 has been elected as the controller, so stopping the election process. (kafka.controller.KafkaController)
[2025-08-19 23:29:32,453] INFO [RequestSendThread controllerId=0] Controller 0 connected to 127.0.0.1:9093 (id: 1 rack: null) for sending state change requests (kafka.controller.RequestSendThread)
[2025-08-19 23:29:34,690] INFO [Controller id=0] Newly added brokers: 2, deleted brokers: , bounced brokers: , all live brokers: 0,1,2 (kafka.controller.KafkaController)
[2025-08-19 23:29:34,690] DEBUG [Channel manager on controller 0]: Controller 0 trying to connect to broker 2 (kafka.controller.ControllerChannelManager)
[2025-08-19 23:29:34,692] INFO [RequestSendThread controllerId=0] Starting (kafka.controller.RequestSendThread)
[2025-08-19 23:29:34,692] INFO [Controller id=0] New broker startup callback for 2 (kafka.controller.KafkaController)
[2025-08-19 23:29:34,692] DEBUG [Controller id=0] Register BrokerModifications handler for Vector(2) (kafka.controller.KafkaController)
[2025-08-19 23:29:34,693] WARN [RequestSendThread controllerId=0] Controller 0's connection to broker 127.0.0.1:9094 (id: 2 rack: null) was unsuccessful (kafka.controller.RequestSendThread)
java.io.IOException: Connection to 127.0.0.1:9094 (id: 2 rack: null) failed.
        at org.apache.kafka.clients.NetworkClientUtils.awaitReady(NetworkClientUtils.java:71)
        at kafka.controller.RequestSendThread.brokerReady(ControllerChannelManager.scala:299)
        at kafka.controller.RequestSendThread.doWork(ControllerChannelManager.scala:252)
        at org.apache.kafka.server.util.ShutdownableThread.run(ShutdownableThread.java:136)
```
