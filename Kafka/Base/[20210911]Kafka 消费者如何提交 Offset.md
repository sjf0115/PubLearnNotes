---
layout: post
author: sjf0115
title: Kafka 消费者如何提交 Offset
date: 2021-09-09 21:52:01
tags:
  - Kafka

categories: Kafka
permalink: kafka-consumer-how-to-commit-offset
---

Kafka Consumer(消费者)每次调用 poll() 方法，它总是返回由生产者写入 Kafka 但还没有被消费者读取过的记录，因此我们可以追踪到哪些记录是被群组里的哪个消费者读取的。Kafka 不会像其他消息队列那样需要得到消费者的确认，相反，Kafka 消费者可以使用 Kafka 来追踪消息在分区里的偏移量(Offset)。我们把更新分区当前位置的操作叫作提交偏移量(Offset)。

因为 Consumer 能够同时消费多个分区的数据，所以 Offset 的提交实际上是在分区粒度上进行的，即 Consumer 需要为分配给它的每个分区提交各自的 Offset。如果 Consumer 一直处于运行状态，那么 Offset 就没有什么用处。如果 Consumer 发生崩溃或者有新的 Consumer 加入群组，就会触发再均衡，完成再均衡之后，每个 Consumer 可能分配到新的分区，而不是之前处理的那个。那 Consumer 应该从新分区的什么位置开始消费呢？这时候 Consumer 就需要读取每个分区最后一次提交的 Offset，然后从 Offset 指定的位置开始消费。当你提交一个 Offset X 时，Kafka 会认为所有 Offset 值小于 X 的消息你都已经成功消费了，所以消费到什么位置由我们来保障。

这一点特别关键。因为位移提交非常灵活，你完全可以提交任何 Offset，但由此产生的后果你也要一并承担。如果提交的 Offset 小于客户端处理的最后一条消息的 Offset，那么处于两个 Offset 之间的消息就会被重复处理。如下图所示，假设最近一次轮询返回的消息是 [7, 11]，在处理完 Offset 10 时 Consumer 发生了崩溃，导致从上一次提交的 Offset 2 开始消费。我们可以看到提交的 Offset 2 小于客户端处理的最后一条消息的 Offset 10，导致 Offset [3, 10] 之间的消息会被重复消费一次：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/kafka-consumer-how-to-commit-offset-1.png?raw=true)

如果提交的 Offset 大于客户端处理的最后一个消息的 Offset，那么处于两个 Offset 之间的消息将会丢失.如下图所示，假设最近一次轮询返回的消息是 [4, 11]，在处理完 Offset 5 时 Consumer 发生了崩溃，导致从上一次提交的 Offset 11 开始消费。我们可以看到提交的 Offset 11 大于客户端处理的最后一条消息的 Offset 5，导致 Offset [6, 11] 之间的消息会丢失：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/kafka-consumer-how-to-commit-offset-2.png?raw=true)

所以，对 Offset 的处理方式对客户端有很大的影响。需要再强调一下，Offset 提交的语义保障是由你来负责，Kafka 只会'无脑'地接受你提交的 Offset。你对 Offset 提交的管理直接影响了你的 Consumer 所能提供的消息语义保障。鉴于 Offset 提交对 Consumer 影响巨大，KafkaConsumer API 提供了多种方式来提交 Offset。从用户的角度来说，Offset 提交分为自动提交和手动提交，从 Consumer 角度来说，Offset 提交分为同步提交和异步提交。

### 1. 自动提交

最简单的提交方式就是让 Consumer 自动提交 Offset。所谓自动提交，就是指 Consumer 在后台默默地为你提交 Offset，作为用户的你完全不必操心这些事。开启自动提交 Offset 也很简单：只需要设置 enable.auto.commit 为 true 即可（或者不设置，默认就为 true），那么每过 5s，Consumer 会自动把从 poll() 方法接收到的最大 Offset 提交上去。提交时间间隔由 auto.commit.interval.ms 控制，默认值是 5s。与 Consumer 里的其他东西一样，自动提交也是在轮询(poll())里进行的。Consumer 每次在进行轮询时会检查是否该提交偏移量了，如果是，那么就会提交从上一次轮询返回的 Offset：
```java
Properties props = new Properties();
props.setProperty("bootstrap.servers", "localhost:9092");
props.setProperty("group.id", "auto-commit-offset-example");
props.setProperty("enable.auto.commit", "true");
props.setProperty("auto.commit.interval.ms", "1000");
props.setProperty("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
props.setProperty("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
consumer.subscribe(Arrays.asList("behavior"));
while (true) {
    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
    for (ConsumerRecord<String, String> record : records) {
        System.out.printf("offset = %d, key = %s, value = %s%n", record.offset(), record.key(), record.value());
    }
}
```
虽然这种方式简单，但也有一些问题。假设我们仍然使用默认的 5s 提交时间间隔，在最近一次提交之后的 3s 发生了崩溃，再均衡之后，Consumer 从最后一次提交的 Offset 开始读取消息。这个时候 Offset 已经落后 了 3s，所以在这 3s 内消息会被重复处理。可以通过修改提交时间间隔来更频繁地提交 Offset，减小可能出现重复消息的时间窗，不过这种情况是无法完全避免的。

在使用自动提交时，每次调用轮询方法都会把上一次调用返回的 Offset 提交上去，它并不知道具体哪些消息已经被处理了，所以在再次调用之前最好确保所有当前调用返回的消息都已经处理完毕(在调用 close() 方法之前也会进行自动提交)。自动提交会保证在开始调用 poll 方法时，提交上次 poll 返回的所有消息。从顺序上来说，poll 方法的逻辑是先提交上一批消息的 Offset，再处理下一批消息，因此它能保证不出现消费丢失的情况。一般情况下不会有什么问题，不过在处理异常或提前退出轮询时要格外小心 。

### 2. 手动提交

和自动提交相反的，就是手动提交了，这样我们就可以在必要的时候提交 Offet，而不是基于时间间隔。开启手动提交 Offset 的方法就是设置 enable.auto.commit 为 false。但是，仅仅设置它为 false 还不够，因为你只是告诉 Consumer 不要自动提交 Offset 而已，你还需要调用相应的 API 手动提交 Offset。

#### 2.1 同步提交

使用 commitSync() 提交 Offset 最简单也最可靠。这个 API会提交由 poll() 方法返回的最新 Offset。该方法是一个同步操作，所以会一直等待，直到 Offset 被成功提交才会返回。如果提交过程中出现异常，该方法会将异常信息抛出。下面是我们在处理完最近一批消息后使用 commitSync() 方法提交 Offset 的例子：
```java
Properties props = new Properties();
props.setProperty("bootstrap.servers", "localhost:9092");
props.setProperty("group.id", "sync-commit-offset-example");
props.setProperty("enable.auto.commit", "false");
props.setProperty("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
props.setProperty("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
consumer.subscribe(Arrays.asList("behavior"));
while (true) {
    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
    for (ConsumerRecord<String, String> record : records) {
        System.out.printf("offset = %d, key = %s, value = %s%n", record.offset(), record.key(), record.value());
    }
    try {
        // 同步提交 Offset
        consumer.commitSync();
    } catch (CommitFailedException e) {
        e.printStackTrace();
    }
}
```
处理完当前批次中的所有消息，在我们轮询其他消息之前调用 commitSync 方法来提交当前批次中的最后一个 Offset。可见，调用 commitSync() 方法的时机，是在你处理完了 poll() 方法返回的所有消息之后。如果你莽撞地过早提交了位移，就可能会出现消费数据丢失的情况。另外，只要没有发生不可恢复的错误，commitSync 方法就会一直重试直至提交成功。如果提交失败，我们也只能把异常记录到错误日志里。

#### 2.2 异步提交

手动提交 Offset 的好处就在于更加灵活，你完全能够把控 Offset 提交的时机和频率。但是，它的问题就是在调用 commitSync() 时，在 broke 对提交请求作出回应之前，应用程序会一直阻塞，这样会限制应用程序的吞吐量。我们可以通过降低提交频率来提升吞吐量，但如果发生了崩溃，会增加重复消息的数量。鉴于这个问题，Kafka 社区为手动提交 Offset 提供了一个异步提交 API：KafkaConsumer#commitAsync()。我们只管发送提交请求，无需等待 broker 的响应。调用 commitAsync() 之后，它会立即返回，不会阻塞，因此不会影响应用程序的吞吐量。由于它是异步的，Kafka 提供了回调函数（callback），供你实现提交之后的逻辑，比如记录日志或处理异常等。下面是我们在处理完最近一批消息后使用 commitAsync() 方法提交 Offset 的例子：
```java
Properties props = new Properties();
props.setProperty("bootstrap.servers", "localhost:9092");
props.setProperty("group.id", "async-commit-offset-example");
props.setProperty("enable.auto.commit", "false");
props.setProperty("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
props.setProperty("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
consumer.subscribe(Arrays.asList("behavior"));
while (true) {
    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
    for (ConsumerRecord<String, String> record : records) {
        System.out.printf("offset = %d, key = %s, value = %s%n", record.offset(), record.key(), record.value());
    }
    // 异步提交 Offset
    consumer.commitAsync(new OffsetCommitCallback() {
        @Override
        public void onComplete(Map<TopicPartition, OffsetAndMetadata> offsets, Exception e) {
            if (e != null) {
                LOG.error("Commit failed for offsets {}", offsets, e);
            }
        }
    });
}
```
在成功提交或碰到无怯恢复的错误之前，commitSync() 会一直重试(应用程序也一直阻塞)，但是 commitAsync() 不会，这也是 commitAsync() 不好的 一个地方。它之所以不进行重试，是因为在它收到服务器响应的时候，可能有一个更大的 Offset 已经提交成功。假设我们发出一个请求用于提交 Offset 2000，这个时候发生了短暂的通信问题，服务器收不到请求，自然也不会作出任何响应。与此同时，我们处理了另外一批消息，并成功提交了 Offset 3000。如果 commitAsync() 重新尝试提交 Offset 2000，它有可能在 Offset 3000 之后提交成功。这个时候如果发生再均衡，就会出现重复消息(2000-3000之间的消息又会被重新消费一次)。

此外，commitAsync() 方法也支持回调，在 broker 作出响应时会执行回调。回调经常被用于记录提交错误或生成度量指标，不过如果你要用它来进行重试， 一定要注意提交的顺序。

#### 2.3 同步异步组合提交

一般情况下，针对偶尔出现的提交失败，不进行重试不会有太大问题，因为如果提交失败是因为临时问题导致的，那么后续的提交总会有成功的。但如果这是发生在关闭 Consumer 或再均衡前的最后一次提交，就要确保能够提交成功。因此，在 Consumer 关闭前一般会组合使用 commitAsync() 和 commitSync()，这样才能发挥两者的最大优势：
- 在 Consumer 正常消费中，可以利用 commitSync 的自动重试来规避那些瞬时错误，比如网络的瞬时抖动，Broker 端 GC 等。因为这些问题都是短暂的，自动重试通常都会成功。此外，我们不希望程序总处于阻塞状态，影响吞吐量。
- 在 Consumer 要关闭前，可以利用 commitSync() 方法执行同步阻塞式的 Offset 提交。commitSync() 方法会一直重试，直到提交成功或者发生无法恢复的错误。
将两者结合后，我们既实现了异步无阻塞式的 Offset 提交，也确保了 Offset 最终的正确性，所以，如果你需要自行编写代码开发一套 Kafka Consumer 应用，那么我推荐使用下面的代码范例来实现手动 Offset 提交：
```java
Properties props = new Properties();
props.setProperty("bootstrap.servers", "localhost:9092");
props.setProperty("group.id", "sync-async-commit-offset-example");
props.setProperty("enable.auto.commit", "false");
props.setProperty("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
props.setProperty("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
consumer.subscribe(Arrays.asList("behavior"));
try {
    while (true) {
        ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(200));
        for (ConsumerRecord<String, String> record : records) {
            System.out.printf("offset = %d, key = %s, value = %s%n", record.offset(), record.key(), record.value());
        }
        // 异步提交
        consumer.commitAsync(new OffsetCommitCallback() {
            @Override
            public void onComplete(Map<TopicPartition, OffsetAndMetadata> offsets, Exception e) {
                if (e != null) {
                    LOG.error("Commit failed for offsets {}", offsets, e);
                }
            }
        });
    }
} catch (Exception e) {
    LOG.error("consumer error", e);
} finally {
    try {
        // 同步提交
        consumer.commitSync();
    } finally {
        consumer.close();
    }
}
```

#### 2.4 指定Offset提交

提交 Offset 的频率与处理消息批次的频率是一样的。上面 Offset 提交方式都是提交 poll 方法返回的最新消息的 Offset，比如 poll 方法一次返回了 500 条消息，当你处理完这 500 条消息之后，会将最新一条消息的 Offset 提交。但如果想要更频繁地提交出怎么办？设想这样一个场景：你的 poll 方法返回的不是 500 条消息，而是 5000 条。那么，你肯定不想把这 5000 条消息都处理完之后再提交 Offset，因为一旦中间出现差错，之前处理的全部都要重来一遍。这类似于我们数据库中的事务处理。很多时候，我们希望将一个大事务分割成若干个小事务分别提交，这能够有效减少错误恢复的时间。

这种情况无法通过调用 commitSync() 或 commitAsync() 来实现，因为它们只会提交最后一个 Offset，而此时该批次里的消息还没有处理完。幸运的是，Consumer API 允许在调用 commitSync() 和 commitAsync() 方法时传进去希望提交的分区和 Offset 的 map，如下所示：
```java
public void commitSync(Map<TopicPartition, OffsetAndMetadata> offsets) {
}
public void commitAsync(Map<TopicPartition, OffsetAndMetadata> offsets) {
}
public void commitAsync(Map<TopicPartition, OffsetAndMetadata> offsets, OffsetCommitCallback callback) {
}
```
它们的参数是一个 Map 对象，Key 就是 TopicPartition，即消费的分区，而值是一个 OffsetAndMetadata 对象，保存的主要是 Offset 数据。

我们如何每处理 1000 条消息就提交一次 Offset 呢？在这里，我以 commitAsync 为例(commitSync 的调用方法也是一样的)：
```java
Map<TopicPartition, OffsetAndMetadata> offsets = new HashMap<>();
int count = 0;

Properties props = new Properties();
props.setProperty("bootstrap.servers", "localhost:9092");
props.setProperty("group.id", "commit-offset-map-example");
props.setProperty("enable.auto.commit", "false");
props.setProperty("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
props.setProperty("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
consumer.subscribe(Arrays.asList("behavior"));
while (true) {
    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
    for (ConsumerRecord<String, String> record : records) {
        System.out.printf("topic = %s, partition = %s, offset = %d, key = %s, value = %s\n",
                record.topic(), record.partition(), record.offset(), record.key(), record.value()
        );
        offsets.put(
                new TopicPartition(record.topic(), record.partition()),
                new OffsetAndMetadata(record.offset() + 1, "no metadata")
        );
        // 每处理100条消息提交一次Offset
        if (count % 1000 == 0) {
            consumer.commitAsync(offsets, new OffsetCommitCallback(){
                @Override
                public void onComplete(Map<TopicPartition, OffsetAndMetadata> map, Exception e) {
                    if (e != null) {
                        LOG.error("Commit failed for offsets {}", offsets, e);
                    }
                }
            });
        }
        count ++;
    }
}
```
简单解释一下这段代码。程序先是创建了一个 Map 对象，用于保存 Consumer 消费处理过程中要提交的分区，之后开始逐条处理消息，并构造要提交的 Offset 值(当前消息 Offset 加 1)。代码的最后部分是做 Offset 的提交。我在这里设置了一个计数器，每累计 1000 条消息就统一提交一次 Offset。与调用无参的 commitAsync 不同，这里调用了带 Map 对象参数的 commitAsync 进行细粒度的 Offset 提交。这样，这段代码就能够实现每处理 1000 条消息就提交一次 Offset，不用再受 poll 方法返回的消息总数的限制了。



参考:
- Kafka权威指南
- 极客学习 Kafka核心技术与实战
