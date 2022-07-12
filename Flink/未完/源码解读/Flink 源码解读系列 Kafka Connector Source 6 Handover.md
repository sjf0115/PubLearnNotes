


Handover 是一个实用程序，用于将数据（记录缓冲区）和异常从生产者线程移交给消费者线程。它实际上像一个'大小为一的阻塞队列'，并在不中断线程的情况下提供一些关于异常报告、关闭和唤醒线程的额外功能。该类用于 Flink Kafka Consumer 中，用于在运行 KafkaConsumer 类的线程和主线程之间进行数据和异常的交接。

Handover 底层封装的是一个 ConsumerRecords 对象。

## 1. 生产元素

从 producer 那里取出一个元素。如果 Handover 目前还有一个尚未被消费者线程取走的元素，那么调用此方法会被阻塞，直到消费者取走这个元素。因为 Handover 看着像一个'大小为1的阻塞队列'，即只能存储一个元素。如果 Handover 中没有元素，才能调用 produce 方法存储一个元素：
```java
public void produce(final ConsumerRecords<byte[], byte[]> element) {
    synchronized (lock) {
        // 直到 next 为 null，即 Handover 中没有元素，否则一直阻塞
        while (next != null && !wakeupProducer) {
            lock.wait();
        }
        wakeupProducer = false;
        // 如果 next 不为 null 抛出异常
        if (next != null) {
            throw new WakeupException();
        }
        // 存储该 element
        else if (error == null) {
            next = element;
            lock.notifyAll();
        }
        // 如果有异常爬抛出 ClosedException
        else {
            throw new ClosedException();
        }
    }
}
```

## 2. 消费元素

从 Handover 中消费下一个元素。如果没有可用的元素可能会一直处于阻塞状态。此方法类似于从阻塞队列中轮询：
```java
public ConsumerRecords<byte[], byte[]> pollNext() throws Exception {
    synchronized (lock) {
        // 直到有一个可用的元素 否则一直阻塞
        while (next == null && error == null) {
            lock.wait();
        }
        ConsumerRecords<byte[], byte[]> n = next;
        if (n != null) {
            next = null;
            lock.notifyAll();
            return n;
        } else {
            ExceptionUtils.rethrowException(error, error.getMessage());
            return ConsumerRecords.empty();
        }
    }
}
```
## 3. 关闭生产者线程

close 用来关闭生产者线程，清空所有变量。如果 produce(ConsumerRecords) 和 pollNext() 方法当前还在阻塞中或者下一次调用时会抛出 ClosedException：
```java
public void close() {
    synchronized (lock) {
        next = null;
        wakeupProducer = false;
        if (error == null) {
            error = new ClosedException();
        }
        lock.notifyAll();
    }
}
```
## 4. 中断生产者线程

wakeupProducer 用来中断生产者线程，不再往 Handover 中存储元素了。如果生产者线程当前在阻塞在 produce(ConsumerRecords) 方法中，那么调用如下方法之后它将退出 produce 方法并抛出 WakeupException：
```java
public void wakeupProducer() {
    synchronized (lock) {
        wakeupProducer = true;
        lock.notifyAll();
    }
}
```
