---
layout: post
author: sjf0115
title: Flink SourceFunction 初了解
date: 2022-03-06 16:19:17
tags:
  - Flink

categories: Flink
permalink: flink-source-function
---

## 1. SourceFunction

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-source-function-1.png?raw=true)

SourceFunction 是 Flink 中所有流数据 Source 的基本接口。SourceFunction 接口继承了 Function 接口，并在内部定义了数据读取使用的 run() 方法、取消运行的 cancel() 方法以及 SourceContext 内部接口：
```java
public interface SourceFunction<T> extends Function, Serializable {
    void run(SourceContext<T> ctx) throws Exception;
    void cancel();

    interface SourceContext<T> {
        void collect(T element);
        void collectWithTimestamp(T element, long timestamp);
        void emitWatermark(Watermark mark);
        void markAsTemporarilyIdle();
        Object getCheckpointLock();
        void close();
    }
}
```
当 Source 输出元素时，可以在 run 方法中调用 SourceContext 接口的 collect 或者 collectWithTimestamp 方法输出元素。run 方法需要尽可能的一直运行，因此大多数 Source 在 run 方法中都有一个 while 循环。Source 也必须具有响应 cancel 方法调用中断 while 循环的能力。比较通用的模式是添加 volatile 布尔类型变量 isRunning 来表示是否在运行中。在 cancel 方法中设置为 false，并在循环条件中检查该变量是否为 true：
```java
private volatile boolean isRunning = true;
@Override
public void run(SourceContext<T> ctx) throws Exception {
    while (isRunning && otherCondition == true) {
        ctx.collect(xxx);
    }
}

@Override
public void cancel() {
    isRunning = false;
}
```

在默认情况下，SourceFunction 不支持并行读取数据，因此 SourceFunction 被 ParallelSourceFunction 接口继承，以支持对外部数据源中数据的并行读取操作：
```java
public interface ParallelSourceFunction<OUT> extends SourceFunction<OUT> {
}
```
ParallelSourceFunction 是并行 Source 的基本接口。在运行时，Runtime 会执行与 Source 配置的并行度一样多的此函数的并行实例。该接口是一个空接口，仅仅作为一个标记，告诉系统这个 Source 可以并行执行。

在 SourceFunction 的基础上扩展了 RichSourceFunction 和 RichParallelSourceFunction 抽象实现类：
```java
public abstract class RichSourceFunction<OUT> extends AbstractRichFunction
        implements SourceFunction<OUT> {
    private static final long serialVersionUID = 1L;
}

public abstract class RichParallelSourceFunction<OUT> extends AbstractRichFunction
        implements ParallelSourceFunction<OUT> {
    private static final long serialVersionUID = 1L;
}
```

RichParallelSourceFunction 是用于实现并行 Source 的基类。Runtime 会执行与 Source 配置的并行度一样多的此函数的并行实例。Source 还可以通过 AbstractRichFunction.getRuntimeContext() 访问上下文信息，例如通过 getRuntimeContext().getNumberOfParallelSubtasks() 获取并行实例的数量，通过 getRuntimeContext().getIndexOfThisSubtask() 获取当前实例是哪个并行实例。此外还提供了额外的生命周期方法（AbstractRichFunction.open() 和 AbstractRichFunction.close()）。有了这些信息，从而实现更加复杂的操作，例如使用 OperatorState 保存 Kafka 中数据消费的偏移量，从而实现端到端当且仅被处理一次的语义保障。

> 需要注意的是，由于未来社区会基于 DataStream API 实现流批一体，因此 SourceFunction 后期的变化会比较大，要及时关注 Flink 社区的最新动向，并及时跟进相关的设计和实现。

## 2. SourceContext

Flink 将 Source 的运行机制跟发送元素进行了分离。具体如何发送元素，取决于独立内部接口 SourceContext。SourceFunction 以内部接口的方式定义了该上下文接口对象：
```java
public interface SourceFunction<T> extends Function, Serializable {
    ...
    interface SourceContext<T> {
        void collect(T element);
        void collectWithTimestamp(T element, long timestamp);
        void emitWatermark(Watermark mark);
        void markAsTemporarilyIdle();
        Object getCheckpointLock();
        void close();
    }
}
```
SourceContext 定义了数据接入过程用到的上下文信息，包含如下方法：
- collect()：用于收集从外部数据源读取的数据并下发到下游算子中。
- collectWithTimestamp()：用于支持收集数据元素以及 EventTime 时间戳。
- emitWatermark()：用于在 SourceFunction 中生成 Watermark 并发送到下游算子进行处理。
- getCheckpointLock()：用于获取检查点锁（Checkpoint Lock），例如使用 KafkaConsumer 读取数据时，可以使用检查点锁，确保记录发出的原子性和偏移状态更新。

SourceContext 主要有两种类型的实现子类，分别为 NonTimestampContext 和 WatermarkContext：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-source-function-2.png?raw=true)

WatermarkContext 支持事件时间抽取和生成 Watermark，最终用于处理乱序事件。基于 WatermarkContext 抽象类扩展实现了 AutomaticWatermarkContext 和 ManualWatermarkContext，分别对应接入时间和事件时间。由此也可以看出，接入时间对应的 Timestamp 和 Watermark 都是通过 Source 算子自动生成的。事件时间的实现则相对复杂，需要用户自定义 SourceContext.emitWatermark() 方法来实现；NonTimestampContext 不支持基于事件时间的操作，仅实现了从外部数据源中读取数据并处理的逻辑，对应了处理时间。

不同的 SourceContext 实现对应了不同的时间处理语义。根据 TimeCharacteristic 配置的不同，则会创建对应不同类型的 SourceContext：
- TimeCharacteristic.EventTime 时间语义对应创建 ManualWatermarkContext
- TimeCharacteristic.IngestionTime 时间语义对应创建 AutomaticWatermarkContext
- TimeCharacteristic.ProcessingTime 时间语义对应创建 NonTimestampContext

```java
final SourceFunction.SourceContext<OUT> ctx;
switch (timeCharacteristic) {
  // 事件时间
  case EventTime:
      ctx = new ManualWatermarkContext<>(
          output,
          processingTimeService,
          checkpointLock,
          streamStatusMaintainer,
          idleTimeout
      );
      break;
  // 接入时间
  case IngestionTime:
      ctx = new AutomaticWatermarkContext<>(
          output,
          watermarkInterval,
          processingTimeService,
          checkpointLock,
          streamStatusMaintainer,
          idleTimeout
      );
      break;
  // 处理时间
  case ProcessingTime:
      ctx = new NonTimestampContext<>(checkpointLock, output);
      break;
  default:
      throw new IllegalArgumentException(String.valueOf(timeCharacteristic));
}
```

## 3. 常见实现类

SourceFunction 接口的实现类主要通过 run() 方法完成与外部数据源的交互，以实现外部数据的读取，并将读取到的数据通过 SourceContext 提供的 collect() 方法发送给 DataStream 后续的算子进行处理。SourceFunction 常见实现类如下图所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-source-function-3.png?raw=true)

### 3.1 SourceFunction 常见实现类

SourceFunction 是最顶层的 Source 方法，只是实现了 Source 的基本功能，即不支持并行读取数据，也不支持访问 RuntimeContext 获取其他信息。常见的实现有 SocketTextStreamFunction、FromElementsFunction、FromIteratorFunction 等。

SocketTextStreamFunction 是从套接字读取字符串的 Source 函数，根据给定的 hostname 和 port，以 socket 的方式进行通信并读取字符串。该 Source 将从套接字流中读取字节并将它们单独转换为字符。当接收到 delimiter 指定的分隔符时，就会输出当前字符串：
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
DataStream<String> source = env.socketTextStream("localhost", 9000, "\n");
source.print("1");
```
FromElementsFunction 是一个非并行的 Source。该 Source 接收一个元素迭代器或者一组元素，使用 Flink 的类型序列化机制将其序列化为二进制数据，然后在输出元素的循环体中，先进行反序列化为初始类型，再输出数据：
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setParallelism(1);

// 方式1
DataStreamSource<String> source = env.fromElements("a", "b", "c", "d");
source.print("1");

// 方式2
List<String> list = Lists.newArrayList("a", "b", "c", "d");
DataStreamSource<String> source1 = env.fromCollection(list);
source1.print("2");

// 方式3
SourceFunction<String> function = new FromElementsFunction<>("a", "b", "c", "d");
SingleOutputStreamOperator<String> source2 = env.addSource(function, "FromElements")
        .returns(String.class);
source2.print("3");

// 执行
env.execute("FromElementsExample");
```
FromIteratorFunction 也是一个非并行的 Source。该 Source 接收一个迭代器，然后在循环体中依次迭代输出数据：
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setParallelism(1);

// 方式1
DataStreamSource<Long> source = env.fromCollection(new NumberSequenceIterator(1L, 20L), Long.class);
source.print("1");

// 方式2
SourceFunction<Long> function = new FromIteratorFunction<>(new NumberSequenceIterator(1L, 20L));
SingleOutputStreamOperator<Long> source1 = env.addSource(function, "FromIterator")
        .returns(Long.class);
source1.print("2");

// 执行
env.execute("FromIteratorExample");
```

### 3.2 RichSourceFunction 常见实现类

RichSourceFunction 在 SourceFunction 基础之上继承了 AbstractRichFunction，这使得 RichSourceFunction 可以在数据接入的过程中获取 RuntimeContext 信息，从而实现更加复杂的操作。常见的实现有 ContinuousFileMonitoringFunction、MessageAcknowledgingSourceBase 等。

ContinuousFileMonitoringFunction 是一个非并行的 Source。该 Source 用来监控给定路径下文件的变化：
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setParallelism(1);

String path = "/Users/wy/test.txt";

// 方式1
DataStreamSource<String> source = env.readTextFile(path);
source.print("1");

// 方式2
TextInputFormat inputFormat = new TextInputFormat(new Path(path));
inputFormat.setFilesFilter(FilePathFilter.createDefaultFilter());
inputFormat.setCharsetName("UTF-8");
inputFormat.setFilePath(path);
FileProcessingMode monitoringMode = FileProcessingMode.PROCESS_ONCE;

ContinuousFileMonitoringFunction<String> function = new ContinuousFileMonitoringFunction<>(
        inputFormat,
        monitoringMode,
        env.getParallelism(),
        -1
);

ContinuousFileReaderOperatorFactory<String, TimestampedFileInputSplit> factory =
        new ContinuousFileReaderOperatorFactory<>(inputFormat);
String sourceName = "FileMonitoring";
TypeInformation<String> typeInfo = BasicTypeInfo.STRING_TYPE_INFO;

SingleOutputStreamOperator<String> source1 = env.addSource(function, sourceName)
        .transform("Split Reader: " + sourceName, typeInfo, factory);
source1.print("2");

// 执行
env.execute("FileMonitoringExample");
```
MessageAcknowledgingSourceBase 针对数据源是消息队列的场景并提供了基于 ID 的应答机制，而 MultipleIdsMessageAcknowledgingSourceBase 是在 MessageAcknowledgingSourceBase 的基础上针对 ID 应答机制进行了更为细分的处理，支持两种 ID 应答模型：session id 和 unique message id。

### 3.3 RichParallelSourceFunction  常见实现类

RichParallelSourceFunction 实现了 ParallelSourceFunction 接口，从而可以支持对外部数据源中数据的并行读取。常见的实现有 DataGeneratorSource、 InputFormatSourceFunction、FromSplittableIteratorFunction、StatefulSequenceSource 等。

DataGeneratorSource 是一个并行 Source。主要是用于生成一些随机数或者递增序列，用于在没有数据源的时候，进行流任务的测试以及性能测试：
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setParallelism(2);

// 复杂随机生成器 自己实现Next逻辑
RandomGenerator<Order> randomGenerator = new RandomGenerator<Order>() {
    @Override
    public Order next() {
        return new Order(
                StringUtils.upperCase(random.nextSecureHexString(8)),
                random.nextInt(10001, 99999),
                random.nextUniform(1, 1000),
                System.currentTimeMillis()
        );
    }
};
DataGeneratorSource<Order> generatorSource = new DataGeneratorSource<>(randomGenerator, 1L, 5L);

// 执行
SingleOutputStreamOperator<Order> source = env.addSource(generatorSource, "DataGeneratorSource")
        .returns(Types.POJO(Order.class));
// 输出
source.print("task");
env.execute("RandomGeneratorExample");
```
