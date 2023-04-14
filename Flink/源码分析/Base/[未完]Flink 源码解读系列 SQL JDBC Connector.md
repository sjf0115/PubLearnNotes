
## 1. JDBCTableSourceSinkFactory

```java
public class JDBCTableSourceSinkFactory implements
	StreamTableSourceFactory<Row>,
	StreamTableSinkFactory<Tuple2<Boolean, Row>> {

	@Override
	public Map<String, String> requiredContext() {

	}

	@Override
	public List<String> supportedProperties() {

	}

	@Override
	public StreamTableSource<Row> createStreamTableSource(Map<String, String> properties) {

	}

	@Override
	public StreamTableSink<Tuple2<Boolean, Row>> createStreamTableSink(Map<String, String> properties) {

	}
}
```

### 1.1 requiredContext

```java
Map<String, String> context = new HashMap<>();
context.put(CONNECTOR_TYPE, CONNECTOR_TYPE_VALUE_JDBC); // jdbc
context.put(CONNECTOR_PROPERTY_VERSION, "1"); // backwards compatibility
return context;
```

### 1.2 supportedProperties

```Java
List<String> properties = new ArrayList<>();

// common options
properties.add(CONNECTOR_DRIVER);
properties.add(CONNECTOR_URL);
properties.add(CONNECTOR_TABLE);
properties.add(CONNECTOR_USERNAME);
properties.add(CONNECTOR_PASSWORD);

// scan options
properties.add(CONNECTOR_READ_QUERY);
properties.add(CONNECTOR_READ_PARTITION_COLUMN);
properties.add(CONNECTOR_READ_PARTITION_NUM);
properties.add(CONNECTOR_READ_PARTITION_LOWER_BOUND);
properties.add(CONNECTOR_READ_PARTITION_UPPER_BOUND);
properties.add(CONNECTOR_READ_FETCH_SIZE);

// lookup options
properties.add(CONNECTOR_LOOKUP_CACHE_MAX_ROWS);
properties.add(CONNECTOR_LOOKUP_CACHE_TTL);
properties.add(CONNECTOR_LOOKUP_MAX_RETRIES);

// sink options
properties.add(CONNECTOR_WRITE_FLUSH_MAX_ROWS);
properties.add(CONNECTOR_WRITE_FLUSH_INTERVAL);
properties.add(CONNECTOR_WRITE_MAX_RETRIES);

// schema
properties.add(SCHEMA + ".#." + SCHEMA_DATA_TYPE);
properties.add(SCHEMA + ".#." + SCHEMA_TYPE);
properties.add(SCHEMA + ".#." + SCHEMA_NAME);
// computed column
properties.add(SCHEMA + ".#." + EXPR);

// watermark
properties.add(SCHEMA + "." + WATERMARK + ".#." + WATERMARK_ROWTIME);
properties.add(SCHEMA + "." + WATERMARK + ".#." + WATERMARK_STRATEGY_EXPR);
properties.add(SCHEMA + "." + WATERMARK + ".#." + WATERMARK_STRATEGY_DATA_TYPE);

// table constraint
properties.add(SCHEMA + "." + DescriptorProperties.PRIMARY_KEY_NAME);
properties.add(SCHEMA + "." + DescriptorProperties.PRIMARY_KEY_COLUMNS);

return properties;
```

### 1.3 createStreamTableSource

```java
DescriptorProperties descriptorProperties = getValidatedProperties(properties);
TableSchema schema = TableSchemaUtils.getPhysicalSchema(descriptorProperties.getTableSchema(SCHEMA));

return JdbcTableSource.builder()
        .setOptions(getJdbcOptions(descriptorProperties))
        .setReadOptions(getJdbcReadOptions(descriptorProperties))
        .setLookupOptions(getJdbcLookupOptions(descriptorProperties))
        .setSchema(schema)
        .build();
```


### 1.4 createStreamTableSink

```java
DescriptorProperties descriptorProperties = getValidatedProperties(properties);
TableSchema schema = TableSchemaUtils.getPhysicalSchema(descriptorProperties.getTableSchema(SCHEMA));

final JdbcUpsertTableSink.Builder builder = JdbcUpsertTableSink.builder()
        .setOptions(getJdbcOptions(descriptorProperties))
        .setTableSchema(schema);

descriptorProperties
        .getOptionalInt(CONNECTOR_WRITE_FLUSH_MAX_ROWS)
        .ifPresent(builder::setFlushMaxSize);
descriptorProperties
        .getOptionalDuration(CONNECTOR_WRITE_FLUSH_INTERVAL)
        .ifPresent(s -> builder.setFlushIntervalMills(s.toMillis()));
descriptorProperties
        .getOptionalInt(CONNECTOR_WRITE_MAX_RETRIES)
        .ifPresent(builder::setMaxRetryTimes);

return builder.build();
```

## 2. JdbcTableSource








...
