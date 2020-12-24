---
layout: post
author: smartsi
title: Java 实现 Kafka Producer
date: 2020-10-10 18:16:01
tags:
  - Kafka

categories: Kafka
permalink: kafka-producer-in-java
---

> kafka 版本：2.5.0

在本文章中，我们创建一个简单的 Java 生产者示例。我们会创建一个名为 my-topic Kafka 主题（Topic），然后创建一个使用该主题发送记录的 Kafka 生产者。Kafka 发送记录可以使用同步方式，也可以使用异步方式。

在创建 Kafka 生产者之前，我们必须安装 Kafka 以及启动集群。具体可以查阅博文：[Kafka 安装与启动](http://smartsi.club/kafka-setup-and-run.html)。

### 1. Maven依赖

要使用 Java 创建 Kafka 生产者，需要添加以下 Maven 依赖项：
```xml
<!-- https://mvnrepository.com/artifact/org.apache.kafka/kafka-clients -->
<dependency>
    <groupId>org.apache.kafka</groupId>
    <artifactId>kafka-clients</artifactId>
    <version>2.5.0</version>
</dependency>
```
> 具体版本需要根据安装的Kafka版本制定，在此我们使用 2.5.0 版本。

### 2. 创建Kafka生产者

如果要往 Kafka 中写入数据，需要首先创建一个生产者对象，并设置一些属性。Kafka 生产者有3个必选的属性：
- `bootstrap.servers`：该属性指定 broker 的地址清单，地址的格式为 host:port。清单里不需要包含所有的 broker 地址，生产者会从给定的 broker 里查找到其他 broker 的信息。不过建议至少要提供两个 broker 的信息，一旦其中一个宕机，生产者仍然能够连接到集群上。
- `key.serializer`：broker 希望接收到的消息的键和值都是字节数组。生产者接口允许使用参数化类型，因此可以把 Java 对象作为键和值发送给 broker。这样的代码具有良好的可读性，不过生产者需要知道如何把这些 Java 对象转换成字节数组。`key.serializer` 必须被设置为一个实现了 org.apache.kafka.common.serialization.Serializer 接口的类，生产者会使用这个类把键对象序列化成字节数组。Kafka 客户端默认提供了 ByteArraySerializer(这个只做很少的事情)、 StringSerializer 以及 IntegerSerializer，因此，如果你只使用常见的几种 Java 对象类型，那么就没必要实现自己的序列化器。要注意，key.serializer 是必须设置的，就算你打算只发送值内容。
- `value.serializer`：与 `key.serializer` 一样，`value.serializer` 指定的类会将值序列化。如果键和值都是字符串，可以使用与 key.serializer 一样的序列化器。如果键是整数类型而值是字符串，那么需要使用不同的序列化器。

如下代码创建了一个生产者，并指定了必须要设置的属性，其他使用默认设置即可：
```java
Properties props = new Properties();
props.put("bootstrap.servers", "localhost:9092");
props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
Producer<String, String> producer = new KafkaProducer<>(props);
```
因为我们的键值都是字符串类型的，所以键值序列化器使用的是内置的 StringSerializer。

生产者由一个缓冲池和一个单独后台线程组成。缓冲池保存尚未传输到服务器的记录；单独线程负责将这些记录转换为请求并将它们发送到集群。如果没有关闭生产者，会导致资源泄漏。

实例化生产者对象后，接下来就可以发送消息了。发送消息主要有以下3种方式：
- 简单发送消息
- 同步发送消息
- 异步发送消息

下面我们详细介绍上述几种发送消息的方式。

### 3. 简单发送消息

对于简单发送消息方式，我们只是把消息发送给服务器，但并不关心消息是否正常到达服务器。大多数情况下，消息会正常到达服务器，因为 Kafka 是高可用的，而且生产者会自动尝试重发。不过，使用这种方式有时候也会丢失一些消息。

简单发送消息方式如下代码所示：
```java
Producer<String, String> producer = new KafkaProducer<>(props);
String topic = "my-topic";
String key = "key-1";
String value = "value-1";
ProducerRecord<String, String> record = new ProducerRecord<>(topic, key, value);
try {
    producer.send(record);
} catch (Exception e) {
    e.printStackTrace();
} finally {
    if (producer != null) {
        producer.close();
    }
}
```

生产者的 send() 方法将 ProducerRecord 对象作为参数，所以我们要先创建一个 ProducerRecord 对象。ProducerRecord 需要发送消息的主题以及要发送的键和值对象。键值对象都必须是字符串类型的，因为必须与序列化器相匹配。

我们使用生产者的 send() 方法发送 ProducerRecord 对象。消息先是被放进缓冲区，然后使用单独的线程发送到服务器端。send() 方法会返回一个包含 RecordMetadata 的 Future 对象，不过因为我们忽略返回值，所以无法知道消息是否发送成功。如果不关心发送结果，那么可以使用这种发送方式。

### 4. 同步发送消息

对于同步发送方式，我们使用 send() 方法发送消息，它会返回一个 Future 对象，调用 Future 对象的 get() 方法进行等待，就可以知道悄息是否发送成功。

同步发送消息方式如下代码所示：
```java
Producer<String, String> producer = new KafkaProducer<>(props);
String topic = "my-topic";
String key = "key-2";
String value = "value-2";
ProducerRecord<String, String> record = new ProducerRecord<>(topic, key, value);
try {
    Future<RecordMetadata> metadataFuture = producer.send(record);
    RecordMetadata metadata = metadataFuture.get();
    System.out.println("返回结果: topic->" + metadata.topic() + ", partition->" + metadata.partition() +  ", offset->" + metadata.offset());
} catch (Exception e) {
    e.printStackTrace();
} finally {
    if (producer != null) {
        producer.close();
    }
}
```

producer.send() 方法先返回一个 Future 对象，然后调用 Future 对象的 get() 方法等待 Kafka 的响应(阻塞)。如果服务器返回错误，get() 方法会抛出异常。如果没有发生错误，我们会得到一个 RecordMetadata 对象，可以用它获取消息的主题、分区以及偏移量。

如果在发送数据之前或者在发送过程中发生了任何错误，比如 broker 返回了一个不允许重发消息的异常或者已经超过了重发的次数，那么就会抛出异常。

KafkaProducer 一般会发生两类错误。其中一类是可重试错误，这类错误可以通过重发消息来解决。比如对于连接错误，可以通过再次建立连接来解决，`无主(noleader)` 错误则可以通过重新为分区选举首领来解决。KafkaProducer 可以被配置成自动重试，如果在多次重试后仍无法解决问题，应用程序会收到一个重试异常。另一类错误无法通过重试解决，比如消息太大异常。对于这类错误，KafkaProducer 不会进行任何重试，直接抛出异常。

### 5. 异步发送消息

假设消息在应用程序和 Kafka 集群之间一个来回需要 10ms。如果在发送完每个消息后都等待回应，那么发送 100 个消息需要 1秒。但如果只发送消息而不等待响应，那么发送 100个消息所需要的时间会少很多。大多数时候，我们并不需要等待响应，尽管 Kafka 会把主题、分区以及消息的偏移量发送回来，但对于发送端的应用程序来说不是必需的。不过在遇到消息发送失败时，我们需要抛出异常、记录错误日志，或者把消息写入错误消息文件以便日后分析。

为了在异步发送消息的同时能够对异常情况进行处理，生产者提供了回调支持。异步发送消息方式如下代码所示：
```java
Properties props = new Properties();
props.put("bootstrap.servers", "localhost:9092");
props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

Producer<String, String> producer = new KafkaProducer<>(props);
String topic = "my-topic";
String key = "key-3";
String value = "value-3";
ProducerRecord<String, String> record = new ProducerRecord<>(topic, key, value);
producer.send(record, new AsyncSendCallback());
producer.close();
```
为了使用回调，需要一个实现了 org.apache.kafka.clients.producer.Callback 接口的类，这个接口只有一个 onCompletion 方法：
```java
public class AsyncSendCallback implements Callback {
    @Override
    public void onCompletion(RecordMetadata recordMetadata, Exception e) {
        if (e != null) {
            e.printStackTrace();
        }
        if (recordMetadata != null) {
            System.out.println("返回结果: topic->" + recordMetadata.topic() + ", partition->" + recordMetadata.partition() +  ", offset->" + recordMetadata.offset());
        }
    }
}
```
如果 kafka 返回一个错误，onCompletion 方法会抛出一个非空异常。正常情况下，我们可以通过 RecordMetadata 对象获取主题、分区以及消息的偏移量。

> 注意：调用send方法之后（消息只是保存在缓冲池中），需要调用close方法（有一个单独的线程把、缓冲池中的消息发送的服务器）。

具体代码可以参阅：[KafkaProducerExample](https://github.com/sjf0115/data-example/blob/master/kafka-example/src/main/java/com/kafka/example/KafkaProducerExample.java)

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

参考：《Kafka权威指南》
