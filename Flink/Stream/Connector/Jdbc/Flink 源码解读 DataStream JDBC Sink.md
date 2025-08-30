
## 1. JdbcSink

JdbcSink 静态类提供了创建 SinkFunction 的三个途径：
```java
public class JdbcSink {
    public static <T> SinkFunction<T> sink(String sql, JdbcStatementBuilder<T> statementBuilder, JdbcConnectionOptions connectionOptions) {
        return sink(sql, statementBuilder, JdbcExecutionOptions.defaults(), connectionOptions);
    }

    public static <T> SinkFunction<T> sink(
            String sql,
            JdbcStatementBuilder<T> statementBuilder,
            JdbcExecutionOptions executionOptions,
            JdbcConnectionOptions connectionOptions) {
        return new GenericJdbcSinkFunction<>(
                new JdbcBatchingOutputFormat<>(
                        new SimpleJdbcConnectionProvider(connectionOptions),
                        executionOptions,
                        context -> {
                            Preconditions.checkState(
                                    !context.getExecutionConfig().isObjectReuseEnabled(),
                                    "objects can not be reused with JDBC sink function");
                            return JdbcBatchStatementExecutor.simple(
                                    sql, statementBuilder, Function.identity());
                        },
                        JdbcBatchingOutputFormat.RecordExtractor.identity()));
    }

    public static <T> SinkFunction<T> exactlyOnceSink(
            String sql,
            JdbcStatementBuilder<T> statementBuilder,
            JdbcExecutionOptions executionOptions,
            JdbcExactlyOnceOptions exactlyOnceOptions,
            SerializableSupplier<XADataSource> dataSourceSupplier) {
        return new JdbcXaSinkFunction<>(
                sql,
                statementBuilder,
                XaFacade.fromXaDataSourceSupplier(
                        dataSourceSupplier,
                        exactlyOnceOptions.getTimeoutSec(),
                        exactlyOnceOptions.isTransactionPerConnection()),
                executionOptions,
                exactlyOnceOptions);
    }

    private JdbcSink() {}
}
```

```java
public static <T> SinkFunction<T> sink(String sql, JdbcStatementBuilder<T> statementBuilder,
        JdbcExecutionOptions executionOptions, JdbcConnectionOptions connectionOptions) {
    return new GenericJdbcSinkFunction<>(
            new JdbcBatchingOutputFormat<>(
                    new SimpleJdbcConnectionProvider(connectionOptions),
                    executionOptions,
                    context -> {
                        Preconditions.checkState(
                                !context.getExecutionConfig().isObjectReuseEnabled(),
                                "objects can not be reused with JDBC sink function");
                        return JdbcBatchStatementExecutor.simple(
                                sql, statementBuilder, Function.identity());
                    },
                    JdbcBatchingOutputFormat.RecordExtractor.identity())
      );
}
```
通过 GenericJdbcSinkFunction JdbcBatchingOutputFormat







。。。。
