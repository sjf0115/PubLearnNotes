---
layout: post
author: smartsi
title: 深入理解 Kafka Connect Single Message Transforms
date: 2021-12-24 13:55:00
tags:
  - Kafka

categories: Kafka
permalink: kafka-connect-deep-dive-single-message-transforms
---

Kafka Connect 是 Apache Kafka 的一部分，提供了数据存储和 Kafka 之间的流式集成。对于数据开发工程师来说，只需要配置 JSON 文件就可以使用。Kafka 为一些常见数据存储的提供了 Connector，比如，JDBC、Elasticsearch、IBM MQ、S3 和 BigQuery 等等。对于开发人员来说，Kafka Connect 提供了丰富的 API，还可以开发其他的 Connector。除此之外，还提供了用于配置和管理 Connector 的 REST API。

Kafka Connect API 还提供了一个简单的接口来操作从 Source 流经 Sink 的数据记录。这个 API 也被称为 Single Message Transforms(SMT)，顾名思义，当消息通过 Kafka Connect Connector 时，SMT 会对数据管道中的每一条消息进行操作。

Connector 分为 Source Connector 和 Sink Connector，可以从 Kafka 的上游系统拉取数据，也可以将数据推送到 Kafka 下游系统。可以对 Connector 进行配置，充分利用任意一侧的 Transforms。Source Connector 在写入 Kafka Topic 之前通过 Transforms 传递记录，Sink Connector 在写入 Sink 之前通过 Transforms 传递记录。

![](1)

Transforms 的一些常见使用场景如下所示：
- 重命名字段
- 掩蔽值
- 根据值将记录路由到主题
- 将时间戳转换或插入到记录中
- 操作键，比如从字段的值设置键

Kafka 内置了许多 Transforms，但是开发自定义的 Transforms 也非常简单，正如你将在这篇博文中看到的那样。

## 1. 如何配置 SMT

需要给 Transform 指定一个名字，用来配置该 Transform 的其他属性。例如，下面是 JDBC 源端利用 RegexRouter Transform 的配置片段，该 Transform 将固定字符串追加到要写入 Topic 的末尾：
```json
{
  -- Connector 名称
  "name": "jdbcSource",
	"config": {
    "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
    -- Transforms 名称
    "transforms": "routeRecords",
    -- Transforms 类型
    "transforms.routeRecords.type":  "org.apache.kafka.connect.transforms.RegexRouter",
    "transforms.routeRecords.regex": "(.*)",
    "transforms.routeRecords.replacement": "$1-test"
    ...
  }
}
```
在这 Transform 被命名为 routerrecords，该名称在后续的键中用于传递属性。注意，上面的示例显示了 RegexRouter 两个配置属性:正则表达式 regex 和引用匹配组的 replacement。这个配置会从 JDBC Source 中获取表名，并添加 `-test` 后缀。不同的 Transform，转换可能具有不同的配置属性。您可以查看文档了解更多细节。

## 2. 执行多个 Transform

有时需要执行多个 Transform。Kafka Connect 支持在配置中定义多个 Transform 并链接在一起。消息按照在 transforms 属性中定义的顺序一次执行对应的 Transform。

![](2)

### 2.1 Transform 链示例

Robin Moffatt 写了一篇[博客](https://www.confluent.io/blog/simplest-useful-kafka-connect-data-pipeline-world-thereabouts-part-3/)文章，介绍了一个 Transform 链，使用 ValueToKey Transform 将一个值转换为一个键，同时使用 ExtractField Transform 只使用ID整数作为键:
```
"transforms":"createKey,extractInt",
"transforms.createKey.type":"org.apache.kafka.connect.transforms.ValueToKey",
"transforms.createKey.fields":"c1",
"transforms.extractInt.type":"org.apache.kafka.connect.transforms.ExtractField$Key",
"transforms.extractInt.field":"c1"
```
需要注意的是上面的 $Key 符号，我们指定了在记录的 Key 上执行这个 Transform。如果要对记录的值进行操作，我们需要使用 $Value 符号。因此，一个 ConnectRecord 看起来像这样:
```
key        value
------------------------------
null       {"c1":{"int":100},"c2":{"string":"bar"}}
```
最后看起来是这样的:
```
key        value
------------------------------
100       {"c1":{"int":100},"c2":{"string":"bar"}}
```

## 3. Transform 使用场景

Transform 应该只在简单、不太变化的数据上使用。不推荐在 Transform 中调用外部 API 或存储状态，更不要尝试在 Transform 中进行复杂的处理。更重的 Transform 和数据集成应该在 Connector 之间的流处理层处理，可以使用 Kafka Streams 或 KSQL 等流处理解决方案。Transform 不能将一个消息拆分成多个消息、不能 Join 其他流进行信息补充，也不能进行任何类型的聚合。这些都应该留给流处理器处理。

如果你想了解更多，我强烈建议你看看这个相关的Kafka峰会的谈话:[Single Message Transformations Are Not the Transformations You’re Looking For](https://www.confluent.io/kafka-summit-nyc17/single-message-transformations-not-transformations-youre-looking/)。

## 4. 深入了解 SMT

下面我们深入看一下 Connector 是如何处理数据的。如果您想开发自己的 Single Message Transform，或者只是对使用 Transform 时所发生的事情感兴趣，否则可以跳过这一节。Transform 被编译成 jar，并通过 Connect worker 的属性文件中 plugin.path 来指定。安装之后，可以在 Connector 属性中配置 Transform。

配置和部署后，Source Connector 接收来自上游系统的记录，将其转换为 ConnectRecord，然后通过已配置 Transform 的 apply() 函数传递该记录，并返回期望记录。Sink Connector 也会发生相同的过程，但顺序相反。读取并反序列化来自 Kafka topic 的消息，然后调用 Transform 的 apply() 函数，并将生成的记录发送到目标系统。

## 5. 如何开发 SMT

要开发一个将 UUID 插入到每个记录中的 SMT，需要按照如下所示步骤进行操作。Apply() 函数是 Transform 的核心。该 Transform 既可以支持有 Schema 模式，也可以支持没有 Schema 的数据，因此各自对应一个 Transform。Apply() 方法适当地路由数据:
```java
@Override
public R apply(R record) {
  if (operatingSchema(record) == null) {
    return applySchemaless(record);
  } else {
    return applyWithSchema(record);
  }
}

private R applySchemaless(R record) {
  final Map<String, Object> value = requireMap(operatingValue(record), PURPOSE);
  final Map<String, Object> updatedValue = new HashMap<>(value);
  updatedValue.put(fieldName, getRandomUuid());
  return newRecord(record, null, updatedValue);
}

private R applyWithSchema(R record) {
  final Struct value = requireStruct(operatingValue(record), PURPOSE);
  Schema updatedSchema = schemaUpdateCache.get(value.schema());
  if(updatedSchema == null) {
    updatedSchema = makeUpdatedSchema(value.schema());
    schemaUpdateCache.put(value.schema(), updatedSchema);
  }
  final Struct updatedValue = new Struct(updatedSchema);
  for (Field field : value.schema().fields()) {
    updatedValue.put(field.name(), value.get(field));
  }
  updatedValue.put(fieldName, getRandomUuid());
  return newRecord(record, updatedSchema, updatedValue);
}
```
Transform 可以作用于记录键上，也可以作用在值上，所以我们需要实现键和值的子类来扩展主 InsertUuid 类，并实现 apply() 函数用到的 newRecord 函数:
```java
public static class Key<R extends ConnectRecord<R>> extends InsertUuid<R> {
  @Override
  protected Schema operatingSchema(R record) {
    return record.keySchema();
  }

  @Override
  protected Object operatingValue(R record) {
    return record.key();
  }

  @Override
  protected R newRecord(R record, Schema updatedSchema, Object updatedValue) {
    return record.newRecord(record.topic(), record.kafkaPartition(), updatedSchema, updatedValue, record.valueSchema(), record.value(), record.timestamp());
  }

}

public static class Value<R extends ConnectRecord<R>> extends InsertUuid<R> {
  @Override
  protected Schema operatingSchema(R record) {
    return record.valueSchema();
  }

  @Override
  protected Object operatingValue(R record) {
    return record.value();
  }

  @Override
  protected R newRecord(R record, Schema updatedSchema, Object updatedValue) {
    return record.newRecord(record.topic(), record.kafkaPartition(), record.keySchema(), record.key(), updatedSchema, updatedValue, record.timestamp());
  }
}
```
该 Transform 只更改 Schema 和值，但需要注意的是，我们可以操作 ConnectRecord 的所有部分：键、值、键和值的 Schema、目标 Topic、目标分区以及时间戳。此外还有可选的参数，这些参数在运行时设置，并通过 Transform 类中被重写的 configure() 函数来访问:
```java
@Override
public void configure(Map<String, ?> props) {
  final SimpleConfig config = new SimpleConfig(CONFIG_DEF, props);
  fieldName = config.getString(ConfigName.UUID_FIELD_NAME);

  schemaUpdateCache = new SynchronizedCache<>(new LRUCache<Schema, Schema>(16));
}
```
如上所述，Transform 接口非常简单，实现一个 apply()函数，接收 ConnectRecord 并返回新的 ConnectRecord。此外还可以通过 configure() 函数提供参数。接下来，编译这个 JAR，并把它放到 Connect worker 配置参数 plugin.path 指定的路径下。请记住，您需要将 Transform 依赖的所有依赖项与它一起打包，要么打包在路径中，要么编译为 fat JAR。在你的 Connector 配置中调用，如下所示(注意$Value内部类约定表示这个转换应该作用于记录的Value):
```
transforms=insertuuid
transforms.insertuuid.type=com.github.cjmatta.kafka.connect.smt.InsertUuid$Value
transforms.insertuuid.uuid.field.name="uuid"
```

## 6. 结论

SMT 是一个扩展 Kafka Connect 实现数据集成目的的很好的方法。你可以使用内置 Transform，或者如上所示轻松地创建一个自定义 Transform。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

参考：
- [Kafka Connect Transformations](https://docs.confluent.io/platform/current/connect/transforms/overview.html)
- [How to Use Single Message Transforms in Kafka Connect](https://www.confluent.io/blog/kafka-connect-single-message-transformation-tutorial-with-examples/?_ga=2.72252507.979685385.1632409679-31410519.1631805246)
