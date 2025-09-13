## 1. 现象

在使用如下命令消费 test 主题下的消息，提示 LEADER_NOT_AVAILABLE
```
localhost:kafka wy$ bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic test --group test-group --from-beginning
[2022-08-23 23:51:27,173] WARN [Consumer clientId=consumer-test-group-1, groupId=test-group] Error while fetching metadata with correlation id 2 : {test=LEADER_NOT_AVAILABLE} (org.apache.kafka.clients.NetworkClient)
```

## 2. 分析

出现上述问题可能与 server.properties 中的 adverted.host.name 设置有关。可能发生的情况是您的消费者试图找出谁是给定分区的领导者，计算出它的 adverted.host.name 和 adverted.port 并尝试连接。如果这些设置没有正确配置，那么它可能会认为领导者不可用。

Socket 服务器侦听的地址。如果未配置，将会从 java.net.InetAddress.getCanonicalHostName() 获取：
```
listeners=PLAINTEXT://127.0.0.1:9092
```

Broker 向生产者和消费者通告主机名和端口。如果未设置，则使用 'listeners' 的值（如果已配置）。否则，将从 java.net.InetAddress.getCanonicalHostName() 获取：
```
advertised.listeners=PLAINTEXT://127.0.0.1:9092
```

listeners 这个参数必须开启，否则绝对报异常 LEADER_NOT_AVAILABLE 异常。

## 3. 解决方案

添加 advertised.listeners 参数：
```
advertised.listeners=PLAINTEXT://127.0.0.1:9092
```

参考:[Leader Not Available Kafka in Console Producer](https://stackoverflow.com/questions/35788697/leader-not-available-kafka-in-console-producer)
