在之前讨论轮询时就说过，不需要担心消费者会在一个无限循环里一直轮询消息，我们会告诉消费者如何优雅地退出循环。如果确定要退出循环，需要通过另一个线程调用 consumer.wakeup() 方法。如果循环运行在主线程里，可以在 ShutdownHook 里调用该方法。要记住，consumer.wakeup() 是消费者唯一一个可以从其他线程里安全调用的方法。调用 consumer.wakeup() 可以退出 poll()，并抛出 WakeupException 异常，或者如果调用 consumer.wakeup() 时线程没有等待轮询，那么异常将在下一轮调用 poll() 时抛出。我们不需要处理 WakeupException，因为它只是用于跳出循环的一种方式。不过，在退出线程之前调用 consumer.close() 是很有必要的，它会提交任何还没有提交的东西，并向群组协调器发送消息，告知自己要离开群组，接下来就会触发再均衡，而不需要等待会话超时。

下面是运行在主线程上的消费者退出线程的代码：
```java
// 创建消费者
Properties props = new Properties();
props.setProperty("bootstrap.servers", "localhost:9092");
props.setProperty("group.id", "wakeup-consumer-example");
props.setProperty("enable.auto.commit", "true");
props.setProperty("auto.commit.interval.ms", "1000");
props.setProperty("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
props.setProperty("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
consumer.subscribe(Arrays.asList("user_behavior"));

// Shutdown 钩子 优雅退出轮询
final Thread mainThread = Thread.currentThread();
Runtime.getRuntime().addShutdownHook(new Thread(){
    @Override
    public void run() {
        System.out.println("start exit .....");
        // 中断轮询
        consumer.wakeup();
        try {
            // 等待主线程完成提交偏移量、关闭消费者等操作
            mainThread.join();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }
});

// 消费者无限轮询消息
while (true) {
    try {
        ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
        for (ConsumerRecord<String, String> record : records) {
            System.out.printf("offset = %d, key = %s, value = %s%n", record.offset(), record.key(), record.value());
        }
    } catch (WakeupException e) {
        // 忽略异常
        System.out.println("throw wakeup exception....");
    } finally {
        consumer.close();
        System.out.println("close consumer....");
    }
}
```
ShutdownHook 运行在单独的线程里，所以退出循环最安全的方式只能是调用 wakeup() 方法。在另一个线程里调用 wakeup() 方法，会导致 poll() 抛出 WakeupException。你可能想捕获异常以确保应用不会意外终止，但实际上这不是必需的。此外在退出之前，需要调用 close 方法确保彻底关闭了消费者。

> ShutdownHook 说明：
当程序正常退出,系统调用 System.exit 方法或虚拟机被关闭时才会执行添加的 shutdownHook 线程。其中 shutdownHook 是一个已初始化但并不有启动的线程，当 jvm 关闭的时候，会执行系统中已经设置的所有通过方法 addShutdownHook 添加的钩子，当系统执行完这些钩子后，jvm 才会关闭。所以可通过这些钩子在 jvm 关闭的时候进行内存清理、资源回收等工作。
