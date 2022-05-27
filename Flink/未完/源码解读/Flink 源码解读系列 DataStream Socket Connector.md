SocketTextStreamFunction

## 1. 如何使用

```java
DataStream<String> text = env.socketTextStream(hostname, port);
```

## 2. 工作原理

### 2.1 入口

```java
public DataStreamSource<String> socketTextStream(String hostname, int port) {
    return socketTextStream(hostname, port, "\n");
}

public DataStreamSource<String> socketTextStream(String hostname, int port, String delimiter) {
    return socketTextStream(hostname, port, delimiter, 0);
}

public DataStreamSource<String> socketTextStream(String hostname, int port, String delimiter, long maxRetry) {
    return addSource(new SocketTextStreamFunction(hostname, port, delimiter, maxRetry), "Socket Stream");
}
```

### 2.2 SocketTextStreamFunction

```java
private final String hostname;
private final int port;
private final String delimiter;
private final long maxNumRetries;
private final long delayBetweenRetries;

public SocketTextStreamFunction(String hostname, int port, String delimiter, long maxNumRetries) {
    this(hostname, port, delimiter, maxNumRetries, DEFAULT_CONNECTION_RETRY_SLEEP);
}

public SocketTextStreamFunction(String hostname, int port, String delimiter, long maxNumRetries, long delayBetweenRetries) {
    checkArgument(isValidClientPort(port), "port is out of range");
    checkArgument(maxNumRetries >= -1,"maxNumRetries must be zero or larger (num retries), or -1 (infinite retries)");
    checkArgument(delayBetweenRetries >= 0, "delayBetweenRetries must be zero or positive");
    this.hostname = checkNotNull(hostname, "hostname must not be null");
    this.port = port;
    this.delimiter = delimiter;
    this.maxNumRetries = maxNumRetries;
    this.delayBetweenRetries = delayBetweenRetries;
}
```


```java
public class SocketTextStreamFunction implements SourceFunction<String> {
    ...
    @Override
    public void run(SourceContext<String> ctx) throws Exception {
      ...
    }
    @Override
    public void cancel() {
      ...
    }
}
```
如果要在 DataStream 中实现一个 DataStreamSource，需要实现 SourceFunction、ParallelSourceFunction、RichSourceFunction 或者 RichParallelSourceFunction 其中一个 Source 接口。SourceFunction 是 Flink 中所有流数据 Source 的基本接口。默认情况下，SourceFunction 不支持并行读取数据，如果想并行读取数据需要实现 ParallelSourceFunction 接口。在 SourceFunction 和 ParallelSourceFunction 的基础上又扩展了 RichSourceFunction 和 RichParallelSourceFunction 抽象实现类，从而可以通过 AbstractRichFunction.getRuntimeContext() 访问上下文信息。详细信息请查阅:[]()

在这 SocketTextStreamFunction 实现的是 SourceFunction 接口，所以需要实现读取数据使用的 run() 方法和取消运行的 cancel() 方法。

#### 2.2.1 run

当 Source 输出元素时，可以在 run 方法中调用 SourceContext 接口的 collect 或者 collectWithTimestamp 方法输出元素。run 方法需要尽可能的一直运行，因此大多数 Source 在 run 方法中都有一个 while 循环。Source 也必须具有响应 cancel 方法调用中断 while 循环的能力。比较通用的模式是添加 volatile 布尔类型变量 isRunning 来表示是否在运行中。在 cancel 方法中设置为 false，并在循环条件中检查该变量是否为 true：

#### 2.2.2 cancel
