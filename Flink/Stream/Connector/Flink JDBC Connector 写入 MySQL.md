
JDBC Connector 连接器提供一个 Sink 接收器来将数据写入 JDBC 数据库。在这使用 JDBC Connector 连接器实现将数据写入 MySQL 数据库。

## 1. 依赖

要使用 JDBC Connector 连接器，需要将如下依赖项添加到项目中：
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-connector-jdbc_2.11</artifactId>
    <version>1.13.6</version>
</dependency>
```
除此之外还需要添加 MySQL 的 JDBC 驱动程序：
```xml
<dependency>
    <groupId>mysql</groupId>
    <artifactId>mysql-connector-java</artifactId>
    <version>8.0.22</version>
</dependency>
```
如果不添加上述 MySQL 驱动程序会抛出如下异常信息：
```java
Caused by: java.io.IOException: unable to open JDBC writer
	at org.apache.flink.connector.jdbc.internal.AbstractJdbcOutputFormat.open(AbstractJdbcOutputFormat.java:56)
	at org.apache.flink.connector.jdbc.internal.JdbcBatchingOutputFormat.open(JdbcBatchingOutputFormat.java:115)
	at org.apache.flink.connector.jdbc.internal.GenericJdbcSinkFunction.open(GenericJdbcSinkFunction.java:49)
	at org.apache.flink.api.common.functions.util.FunctionUtils.openFunction(FunctionUtils.java:34)
	at org.apache.flink.streaming.api.operators.AbstractUdfStreamOperator.open(AbstractUdfStreamOperator.java:102)
	at org.apache.flink.streaming.api.operators.StreamSink.open(StreamSink.java:46)
	at org.apache.flink.streaming.runtime.tasks.OperatorChain.initializeStateAndOpenOperators(OperatorChain.java:442)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.restoreGates(StreamTask.java:585)
	at org.apache.flink.streaming.runtime.tasks.StreamTaskActionExecutor$1.call(StreamTaskActionExecutor.java:55)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.executeRestore(StreamTask.java:565)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.runWithCleanUpOnFail(StreamTask.java:650)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.restore(StreamTask.java:540)
	at org.apache.flink.runtime.taskmanager.Task.doRun(Task.java:759)
	at org.apache.flink.runtime.taskmanager.Task.run(Task.java:566)
	at java.lang.Thread.run(Thread.java:748)
Caused by: java.lang.ClassNotFoundException: com.mysql.cj.jdbc.Driver
	at java.net.URLClassLoader.findClass(URLClassLoader.java:381)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:424)
	at org.apache.flink.util.FlinkUserCodeClassLoader.loadClassWithoutExceptionHandling(FlinkUserCodeClassLoader.java:64)
	at org.apache.flink.util.ChildFirstClassLoader.loadClassWithoutExceptionHandling(ChildFirstClassLoader.java:74)
	at org.apache.flink.util.FlinkUserCodeClassLoader.loadClass(FlinkUserCodeClassLoader.java:48)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:357)
	at org.apache.flink.runtime.execution.librarycache.FlinkUserCodeClassLoaders$SafetyNetWrapperClassLoader.loadClass(FlinkUserCodeClassLoaders.java:172)
	at java.lang.Class.forName0(Native Method)
	at java.lang.Class.forName(Class.java:348)
	at org.apache.flink.connector.jdbc.internal.connection.SimpleJdbcConnectionProvider.loadDriver(SimpleJdbcConnectionProvider.java:90)
	at org.apache.flink.connector.jdbc.internal.connection.SimpleJdbcConnectionProvider.getLoadedDriver(SimpleJdbcConnectionProvider.java:100)
	at org.apache.flink.connector.jdbc.internal.connection.SimpleJdbcConnectionProvider.getOrEstablishConnection(SimpleJdbcConnectionProvider.java:117)
	at org.apache.flink.connector.jdbc.internal.AbstractJdbcOutputFormat.open(AbstractJdbcOutputFormat.java:54)
	... 14 more
```

## 2. JdbcSink

可以通过如下语句创建一个 JDBC Sink：
```java
JdbcSink.sink(
    dmlSQL,                            // 必填
    statementBuilder,                  // 必填   	
    executionOptions,                  // 可选
    connectionOptions                  // 必填
);
```
executionOptions 参数是可选的，你也可以选择不填此参数来创建一个默认 JdbcExecutionOptions 实例的 JDBC Sink：
```java
JdbcSink.sink(String dmlSQL, JdbcStatementBuilder<T> statementBuilder, JdbcConnectionOptions connectionOptions)
```

### 2.1 SQL DML 语句

JdbcSink 的第一个参数便是如何将数据写入 MySQL 的 DML 语句：
```sql
insert into word_count_append (word, count) values (?, ?)
```

需要注意的是 JDBC 接收器只提供了 `At-Least-Once` 语义保证。但是，可以通过编写 upsert SQL 语句或幂等 SQL 更新，可以有效地实现 `Exactly-Once`。如下是一个 upsert SQL 语句：
```sql
INSERT INTO word_count_upsert (word, count) VALUES (?, ?) ON DUPLICATE KEY UPDATE count = ?
```

### 2.2 JDBC 语句构建器

第二步是使用 JdbcStatementBuilder 来构造 JDBC Statement 构建器。用流的每个元素来更新 PreparedStatement，例如如下所示使用计算出来的单词以及出现次数来更新 statement：
```java
JdbcStatementBuilder<Tuple2<String, Integer>> statementBuilder = new JdbcStatementBuilder<Tuple2<String, Integer>>() {
    @Override
    public void accept(PreparedStatement statement, Tuple2<String, Integer> wordCount) throws SQLException {
        String word = wordCount.f0;
        Integer count = wordCount.f1;
        statement.setString(1, word);
        statement.setInt(2, count);
        statement.setInt(3, count);
    }
};
```
你也可以选择 Lambda 表达式的方式来创建 JdbcStatementBuilder：
```java
JdbcStatementBuilder<Tuple2<String, Integer>> statementBuilder = (statement, tuple2) -> {
    statement.setString(1, tuple2.f0);
    statement.setLong(2, tuple2.f1);
    statement.setLong(3, tuple2.f1);
};
```

### 2.3 JDBC 执行参数构建器

第一步配置的 SQL DML 语句是分批次执行的，例如攒够多少条记录或者等待多长时间之后触发批次的写入。可以选择使用以下示例进行配置：
```java
JdbcExecutionOptions.Builder executionOptionsBuilder = JdbcExecutionOptions.builder();
JdbcExecutionOptions executionOptions = executionOptionsBuilder
        .withBatchSize(100)
        .withBatchIntervalMs(200)
        .withMaxRetries(5)
        .build();
```
JdbcExecutionOptions 构建器支持三个参数：
- size：批次大小，即缓存多少条记录之后才会触发写出操作；默认值是 5000；即需要攒够 5000 条记录才会触发写出动作；通过 `withBathSize` 方法设置自定义的批次大小。
- intervalMs：批次间隔时间，即缓存多久之后才会触发写出操作；默认值为 0，即没有时间限制，一直等到 buffer 满了或者作业结束才能触发写出动作；可以通过 `withBatchIntervalMs` 方法设置自定义的批次间隔。
- maxRetries：最大重试次数，默认值为 3；可以通过 `withMaxRetries` 方法来设置。

```java
public class JdbcExecutionOptions implements Serializable {
    public static final int DEFAULT_MAX_RETRY_TIMES = 3;
    private static final int DEFAULT_INTERVAL_MILLIS = 0;
    public static final int DEFAULT_SIZE = 5000;

    ...

    public static final class Builder {
        private long intervalMs = DEFAULT_INTERVAL_MILLIS;
        private int size = DEFAULT_SIZE;
        private int maxRetries = DEFAULT_MAX_RETRY_TIMES;

        public Builder withBatchSize(int size) {
            this.size = size;
            return this;
        }

        public Builder withBatchIntervalMs(long intervalMs) {
            this.intervalMs = intervalMs;
            return this;
        }

        public Builder withMaxRetries(int maxRetries) {
            this.maxRetries = maxRetries;
            return this;
        }

        public JdbcExecutionOptions build() {
            return new JdbcExecutionOptions(intervalMs, size, maxRetries);
        }
    }
}
```
SQL DML 语句什么时候执行，取决于如下条件。只要满足以下条件之一，JDBC 批次处理就会执行：
- 批次间隔时间到达配置的间隔时间
- 批次大小到达配置的记录条数
- Flink Checkpoint 启动

### 2.4 JDBC 连接参数构建器

使用 JdbcConnectionOptions 实例配置到数据库的连接：
```java
JdbcConnectionOptions.JdbcConnectionOptionsBuilder connectionOptionsBuilder = new JdbcConnectionOptions.JdbcConnectionOptionsBuilder();
JdbcConnectionOptions connectionOptions = connectionOptionsBuilder
        .withUrl("jdbc:mysql://localhost:3308/flink")
        .withDriverName("com.mysql.cj.jdbc.Driver")
        .withUsername("root")
        .withPassword("root")
        .build();
```
JdbcConnectionOptions 连接参数构建器支持 5 个参数：
- url：JDBC 连接URL，通过 `withUrl` 方法配置；
- driverName：驱动程序，通过 `withDriverName` 方法配置；在这为 MySQL 选择的是 `com.mysql.cj.jdbc.Driver`；
- username：用户名，通过 `withUsername` 方法配置；
- password：密码，通过 `withPassword` 方法配置；
- connectionCheckTimeoutSeconds：设置重试之间的最大超时时间，默认为60秒。通过 `withConnectionCheckTimeoutSeconds` 方法配置；

```java
public class JdbcConnectionOptions implements Serializable {
    public static class JdbcConnectionOptionsBuilder {
        private String url;
        private String driverName;
        private String username;
        private String password;
        private int connectionCheckTimeoutSeconds = 60;

        public JdbcConnectionOptionsBuilder withUrl(String url) {
            this.url = url;
            return this;
        }

        public JdbcConnectionOptionsBuilder withDriverName(String driverName) {
            this.driverName = driverName;
            return this;
        }

        public JdbcConnectionOptionsBuilder withUsername(String username) {
            this.username = username;
            return this;
        }

        public JdbcConnectionOptionsBuilder withPassword(String password) {
            this.password = password;
            return this;
        }

        public JdbcConnectionOptionsBuilder withConnectionCheckTimeoutSeconds(
                int connectionCheckTimeoutSeconds) {
            this.connectionCheckTimeoutSeconds = connectionCheckTimeoutSeconds;
            return this;
        }

        public JdbcConnectionOptions build() {
            return new JdbcConnectionOptions(
                    url, driverName, username, password, connectionCheckTimeoutSeconds);
        }
    }
}
```

## 3. 实战

```java
String hostname = "localhost";
int port = 9100;
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

// 单词流
DataStream<String> text = env.socketTextStream(hostname, port, "\n");
DataStream<Tuple2<String, Integer>> words = text.flatMap(new FlatMapFunction<String, Tuple2<String, Integer>>() {
    @Override
    public void flatMap(String line, Collector<Tuple2<String, Integer>> collector) throws Exception {
        String[] words = line.split("\\s+");
        for (String word : words) {
            collector.collect(Tuple2.of(word, 1));
        }
    }
});

// 单词计数
DataStream<Tuple2<String, Integer>> wordsCount = words.keyBy(new KeySelector<Tuple2<String, Integer>, String>() {
    @Override
    public String getKey(Tuple2<String, Integer> tuple) throws Exception {
        return tuple.f0;
    }
}).reduce(new ReduceFunction<Tuple2<String, Integer>>() {
    @Override
    public Tuple2<String, Integer> reduce(Tuple2<String, Integer> a, Tuple2<String, Integer> b) throws Exception {
        return new Tuple2(a.f0, a.f1 + b.f1);
    }
});

//String dmlSQL = "insert into word_count_append (word, count) values (?, ?)";
String dmlSQL = "INSERT INTO word_count_upsert (word, count) VALUES (?, ?) ON DUPLICATE KEY UPDATE count = ?";

JdbcStatementBuilder<Tuple2<String, Integer>> statementBuilder = new JdbcStatementBuilder<Tuple2<String, Integer>>() {
    @Override
    public void accept(PreparedStatement statement, Tuple2<String, Integer> wordCount) throws SQLException {
        String word = wordCount.f0;
        Integer count = wordCount.f1;
        statement.setString(1, word);
        statement.setInt(2, count);
        statement.setInt(3, count);
    }
};

JdbcExecutionOptions.Builder executionOptionsBuilder = JdbcExecutionOptions.builder();
JdbcExecutionOptions executionOptions = executionOptionsBuilder
        .withBatchSize(1)
        .withBatchIntervalMs(200)
        .withMaxRetries(5)
        .build();

JdbcConnectionOptions.JdbcConnectionOptionsBuilder connectionOptionsBuilder = new JdbcConnectionOptions.JdbcConnectionOptionsBuilder();
JdbcConnectionOptions connectionOptions = connectionOptionsBuilder.withUrl("jdbc:mysql://localhost:3308/flink")
        .withDriverName("com.mysql.cj.jdbc.Driver")
        .withUsername("root")
        .withPassword("root")
        .build();

wordsCount.addSink(
        JdbcSink.sink(dmlSQL, statementBuilder, executionOptions, connectionOptions)
);
```
