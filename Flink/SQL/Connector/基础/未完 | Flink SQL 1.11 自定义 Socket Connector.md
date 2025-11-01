


- [专家带你吃透 Flink 架构：一个新版 Connector 的实现](https://mp.weixin.qq.com/s/azGu5-kFzhG6qCHIeepIMw)

## 1. SocketSourceFunction

```java
public class SocketSourceFunction extends RichSourceFunction<Row> implements ResultTypeQueryable<Row> {
    // RichSourceFunction
    @Override
    public void run(SourceContext<Row> sourceContext) throws Exception {

    }

    @Override
    public void cancel() {

    }

    // ResultTypeQueryable
    @Override
    public TypeInformation<Row> getProducedType() {
        return null;
    }
}
```

### 1.1 构造器

```java
private static final String DEFAULT_DELIMITER = "\n";
private static final long DEFAULT_MAX_NUM_RETRIES = 3;
private static final long DEFAULT_DELAY_BETWEEN_RETRIES = 500;

private final String hostname;
private final int port;
private final String delimiter;
private final long maxNumRetries;
private final long delayBetweenRetries;
private final String[] fieldNames;
private final TypeInformation[] fieldTypes;

private volatile boolean isRunning = true;
private Socket currentSocket;

public SocketSourceFunction(SocketOption option, String[] fieldNames, TypeInformation[] fieldTypes) {
    this.hostname = option.getHostname();
    this.port = option.getPort();
    this.delimiter = option.getDelimiter().orElse(DEFAULT_DELIMITER);
    this.maxNumRetries = option.getMaxNumRetries().orElse(DEFAULT_MAX_NUM_RETRIES);
    this.delayBetweenRetries = option.getDelayBetweenRetries().orElse(DEFAULT_DELAY_BETWEEN_RETRIES);
    this.fieldNames = fieldNames;
    this.fieldTypes = fieldTypes;
}
```

### 1.2 getProducedType

```java
@Override
public TypeInformation<Row> getProducedType() {
    return new RowTypeInfo(fieldTypes, fieldNames);
}
```

### 1.3 cancel

```java
@Override
public void cancel() {
    isRunning = false;
    try {
        currentSocket.close();
    } catch (Throwable t) {
        // ignore
    }
}
```

### 1.4 run

```java
@Override
public void run(SourceContext<Row> sourceContext) throws Exception {
    long attempt = 0;
    final StringBuilder result = new StringBuilder();
    while (isRunning) {
        try (Socket socket = new Socket()) {
            currentSocket = socket;
            socket.connect(new InetSocketAddress(hostname, port), 0);
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream()))) {
                char[] buffer = new char[8012];
                int bytes;
                while ((bytes = reader.read(buffer)) != -1) {
                    result.append(buffer, 0, bytes);
                    int delimiterPos;
                    // 根据指定的分隔符循环切分字符串 buffer
                    while (result.length() >= delimiter.length() && (delimiterPos = result.indexOf(delimiter)) != -1) {
                        // 切分字符串 result
                        String record = result.substring(0, delimiterPos);
                        if (delimiter.equals("\n") && record.endsWith("\r")) {
                            record = record.substring(0, record.length() - 1);
                        }
                        // 输出切分好的字符串
                        sourceContext.collect(Row.of(record));
                        // 切分剩余字符串
                        result.delete(0, delimiterPos + delimiter.length());
                    }
                }
            }
        }

        if (isRunning) {
            // 断链重试 最多重试 maxNumRetries 次(或者一直重试)
            attempt++;
            if (maxNumRetries == -1 || attempt < maxNumRetries) {
                Thread.sleep(delayBetweenRetries);
            } else {
                break;
            }
        }
    }
}
```

## SocketValidator

Connector 是连接外部数据源与 Flink 计算引擎的关键桥梁。然而，Connector 的配置复杂性常常导致各种运行时错误。为了在 SQL 解析阶段就捕获这些配置问题，Flink 提供了 ConnectorDescriptorValidator ——一个强大且可扩展的 Connector 验证框架。
```java
public class SocketValidator extends ConnectorDescriptorValidator {
    public static final String CONNECTOR_TYPE_VALUE = "socket";
    public static final String CONNECTOR_HOST = "host";
    public static final String CONNECTOR_PORT = "port";
    public static final String CONNECTOR_DELIMITER = "delimiter";
    public static final String CONNECTOR_MAX_NUM_RETRIES = "maxNumRetries";
    public static final String CONNECTOR_DELAY_BETWEEN_RETRIES = "delayBetweenRetries";

    @Override
    public void validate(DescriptorProperties properties) {
        super.validate(properties);
        // 必填参数校验
        properties.validateString(CONNECTOR_HOST, false, 1);
        properties.validateInt(CONNECTOR_PORT, false);
        properties.validateString(CONNECTOR_DELIMITER, true, 1);

        // 可选参数校验
        Optional<Long> maxNumRetries = properties.getOptionalLong(CONNECTOR_MAX_NUM_RETRIES);
        maxNumRetries.ifPresent(num -> Preconditions.checkArgument(
                num >= -1,
                "maxNumRetries must be zero or larger (num retries), or -1 (infinite retries)"
        ));
        Optional<Long> delayBetweenRetries = properties.getOptionalLong(CONNECTOR_DELAY_BETWEEN_RETRIES);
        delayBetweenRetries.ifPresent(delay -> Preconditions.checkArgument(delay >= 0, "delayBetweenRetries must be zero or positive"));
    }
}
```
