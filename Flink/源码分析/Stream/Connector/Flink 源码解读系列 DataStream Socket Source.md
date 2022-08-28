
## 1. 如何使用

DataStream API 支持从 Socket 套接字读取数据。我们只需要调用 socketTextStream 方法，并指定要读取的主机和端口号即可：
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
DataStream<String> text = env.socketTextStream(hostname, port);
```

## 2. 工作原理

### 2.1 入口

Flink 提供了如下几种快捷创建 Socket DataStreamSource 的方法，用户需要指定主机名和端口号，此外也可以指定分割从 Socket 中读取字符串的分隔符以及最大重试次数（默认为 500 毫秒）：
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
我们看到 socketTextStream 方法最终实际上是创建 SocketTextStreamFunction 方法。

### 2.2 SocketTextStreamFunction

从上面代码中可以看到可以指定主机名、端口号、分隔符以及最大重试次数来创建 SocketTextStreamFunction。最大重试次数必须大于等于 0 或者为 -1，指定为 0 表示不会重试，立即终止；指定为 -1 表示无限重试。如果重试时间间隔不指定，默认为 500 毫秒：
```java
private final String hostname;
private final int port;
private final String delimiter;
private final long maxNumRetries;
private final long delayBetweenRetries;
private static final int DEFAULT_CONNECTION_RETRY_SLEEP = 500;

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
下面具体看一下 SocketTextStreamFunction 的整体结构：
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

在这 SocketTextStreamFunction 实现的是 SourceFunction 接口，所以需要实现读取数据使用的 run() 方法和取消运行的 cancel() 方法。因为默认情况下，SourceFunction 不支持并行读取数据，所以 SocketTextStreamFunction 也不支持并行读取数据。下面具体看一下需要重写的两个方法，即核心处理逻辑的地方。

#### 2.2.1 run

当 Source 输出元素时，可以在 run 方法中调用 SourceContext 接口的 collect 或者 collectWithTimestamp 方法输出元素。run 方法需要尽可能的一直运行，因此在 run 方法中会有一个 while 循环。为了响应 cancel 方法中断 while 循环的能力，通用方案是添加 volatile 布尔类型变量 isRunning 来表示是否在运行中。在 cancel 方法中设置为 false，并在循环条件中检查该变量是否为 true：
```java
private volatile boolean isRunning = true;
final StringBuilder buffer = new StringBuilder();
long attempt = 0;
while (isRunning) {
    // 连接 Socket，读取数据；按照指定的分隔符切分字符串并输出
    ...
    // 是否重试 如果非运行状态则不必重试
    if (isRunning) {
        attempt++;
        // 最大重试次数不超过 maxNumRetries 次
        if (maxNumRetries == -1 || attempt < maxNumRetries) {
            // 每次重试间隔 delayBetweenRetries 毫秒
            Thread.sleep(delayBetweenRetries);
        } else {
            break;
        }
    }
}
// 输出剩余字符串
if (buffer.length() > 0) {
    ctx.collect(buffer.toString());
}
```
While 循环中是从 Socket 中读取数据，并按照指定的分隔符切分字符串输出的逻辑。此外，还增加了重试能力，如果处于运行状态并且重试的次数没有超过最大重试次数，间隔 delayBetweenRetries 毫秒之后再次重试连接 Socket 读取数据。下面详细看一下如何连接 Socket 分割读取数据：
```java
try (Socket socket = new Socket()) {
    currentSocket = socket;
    // 连接 Socket
    socket.connect(new InetSocketAddress(hostname, port), CONNECTION_TIMEOUT_TIME);
    try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream()))) {
        char[] cbuf = new char[8192];
        int bytesRead;
        while (isRunning && (bytesRead = reader.read(cbuf)) != -1) {
            buffer.append(cbuf, 0, bytesRead);
            int delimPos;
            // 根据指定的分隔符循环切分字符串 buffer
            while (buffer.length() >= delimiter.length() && (delimPos = buffer.indexOf(delimiter)) != -1) {
                // 切分字符串 result
                String record = buffer.substring(0, delimPos);
                if (delimiter.equals("\n") && record.endsWith("\r")) {
                    record = record.substring(0, record.length() - 1);
                }
                // 输出切分好的字符串 record
                ctx.collect(record);
                // 待切分的剩余部分字符串
                buffer.delete(0, delimPos + delimiter.length());
            }
        }
    }
}
```
首先创建 Socket 对象，根据指定的主机和端口号进行连接。使用 BufferedReader 的 read 方法循环从 Socket 中读取数据，每次都读取一个字节数组大小的数据，在碰到输入流结尾时返回 -1 结束循环读取。从 Socket 中读取数据的临时缓存在 buffer 字符串中，后续根据指定的分隔符循环切分 buffer 字符串，并输出每次切分好的字符串。

#### 2.2.2 cancel

在 cancel 方法实现中断 while 循环的能力，同时关闭 Socket 对象释放资源：
```java
public void cancel() {
    isRunning = false;
    Socket theSocket = this.currentSocket;
    if (theSocket != null) {
        IOUtils.closeSocket(theSocket);
    }
}
```
