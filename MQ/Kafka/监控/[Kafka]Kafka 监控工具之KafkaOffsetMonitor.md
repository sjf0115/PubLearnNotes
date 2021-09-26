
### 1. 概述

KafkaOffsetMonitor是用来实时监控Kafka集群的consumers以及它们在partition中的offset(偏移量)的一个应用程序。

你可以查看当前的消费者 Groups，每个 Group 消费的 Topic 以及每个 Topic 所有 Partition 的消费情况。这有助于你了解从队列中消费的速度以及队列消息增长的速度。这可以允许对kafka生产者和消费者进行调试，或者只是想知道系统将会发生什么。

该应用程序保存了消费者排队位置和滞后的历史记录，因此你可以清楚的了解过去几天发生的事情。

### 2. 使用

这是一个小型webapp，只要你有权限访问控制kafka的ZooKeeper节点，你就可以在本地或服务器上运行：
```
java -cp KafkaOffsetMonitor-assembly-0.2.1.jar \
     com.quantifind.kafka.offsetapp.OffsetGetterWeb \
     --offsetStorage kafka
     --zk zk-server1,zk-server2 \
     --port 8080 \
     --refresh 10.seconds \
     --retain 2.days
```

参数|描述
---|---
offsetStorage|可以选择zookeeper，kafka或storm。其他的都属于zookeeper
zk|ZooKeeper的hosts
port|应用程序端口
refresh|应用程序在数据库中刷新和存储点的频率
retain|在数据库中保留多长时间
dbName|存储历史记录的数据库，默认为offsetapp
kafkaOffsetForceFromStart|仅适用于offsetStorage为kafka的格式。强制KafkaOffsetMonitor从开始扫描提交消息
stormZKOffsetBase|仅适用于offsetStorage为storm的格式。更改zookeeper中的偏移量存储基数，默认为'/stormconsumers'
pluginsArgs|扩展使用的其他参数
















参考：https://github.com/quantifind/KafkaOffsetMonitor

https://www.iteblog.com/archives/1083.html

http://www.2bowl.info/kafka%E7%9B%91%E6%8E%A7%E5%B7%A5%E5%85%B7-kafkaoffsetmonitor/
