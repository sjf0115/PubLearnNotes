


Handover 是一个实用程序，用于将数据（记录缓冲区）和异常从生产者线程移交给消费者线程。它实际上像一个'大小为一的阻塞队列'，并在不中断线程的情况下提供一些关于异常报告、关闭和唤醒线程的额外功能。该类用于 Flink Kafka Consumer 中，用于在运行 KafkaConsumer 类的线程和主线程之间进行数据和异常的交接。

Handover 具有使用 Handover.WakeupException 而不是线程中断“唤醒”生产者线程的概念。

切换也可以“关闭”，从一个线程向另一个线程发出该线程已终止的信号。


从 producer 那里交出一个元素。如果 Handover 已经有一个尚未被消费者线程拾取的元素，则此调用会阻塞，直到消费者拾取之前的元素。
```java
public void produce(final ConsumerRecords<byte[], byte[]> element) throws InterruptedException, WakeupException, ClosedException {
    synchronized (lock) {
        while (next != null && !wakeupProducer) {
            lock.wait();
        }

        wakeupProducer = false;

        // if there is still an element, we must have been woken up
        if (next != null) {
            throw new WakeupException();
        }
        // if there is no error, then this is open and can accept this element
        else if (error == null) {
            next = element;
            lock.notifyAll();
        }
        // an error marks this as closed for the producer
        else {
            throw new ClosedException();
        }
    }
}
```


```java
public ConsumerRecords<byte[], byte[]> pollNext() throws Exception {
    synchronized (lock) {
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


```java
public void wakeupProducer() {
    synchronized (lock) {
        wakeupProducer = true;
        lock.notifyAll();
    }
}
```
