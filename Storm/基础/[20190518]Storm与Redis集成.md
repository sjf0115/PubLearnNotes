---
layout: post
author: sjf0115
title: Storm与Redis集成
date: 2019-05-27 11:05:34
tags:
  - Storm
  - Storm 基础

categories: Storm
permalink: how-to-use-redis-in-storm
---

Storm-redis 使用 Jedis 作为 Redis 客户端。

### 1. 如何使用

添加Maven依赖：
```xml
<dependency>
    <groupId>org.apache.storm</groupId>
    <artifactId>storm-redis</artifactId>
    <version>${storm.version}</version>
    <type>jar</type>
</dependency>
```

### 2. 常用Bolt

Storm-redis 提供了基本的 Bolt 实现：RedisLookupBolt，RedisStoreBolt 以及 RedisFilterBolt。

根据名字我们就可以知道其功能，RedisLookupBolt 从 Redis 中检索指定键的值，RedisStoreBolt 将键/值存储到 Redis 上。RedisFilterBolt 过滤键或字段不在 Redis 上的元组。

一个元组匹配一个键/值对，你可以在 TupleMapper 中定义匹配模式。你还可以从 RedisDataTypeDescription 中选择你需要的数据类型。通过  RedisDataTypeDescription.RedisDataType 来查看支持哪些数据类型。一些数据类型，例如散列，有序集，还需要指定额外的键来将元组转换为元素：
```java
public RedisDataTypeDescription(RedisDataType dataType, String additionalKey) {
    this.dataType = dataType;
    this.additionalKey = additionalKey;
    if (dataType == RedisDataType.HASH ||
            dataType == RedisDataType.SORTED_SET || dataType == RedisDataType.GEO) {
        if (additionalKey == null) {
            throw new IllegalArgumentException("Hash, Sorted Set and GEO should have additional key");
        }
    }
}
```

这些接口与 RedisLookupMapper，RedisStoreMapper 以及 RedisFilterMapper 组合使用，分别适用于 RedisLookupBolt，RedisStoreBolt 以及 RedisFilterBolt。当你实现 RedisFilterMapper 时，请确保在 declareOutputFields() 中声明与输入流相同的字段，因为 FilterBolt 只是转发存在 Redis 上输入元组。

#### 2.1 RedisLookupBolt

实现RedisLookupMapper：
```java
class WordCountRedisLookupMapper implements RedisLookupMapper {
    private RedisDataTypeDescription description;
    private final String hashKey = "wordCount";

    public WordCountRedisLookupMapper() {
        description = new RedisDataTypeDescription(
                RedisDataTypeDescription.RedisDataType.HASH, hashKey);
    }

    @Override
    public List<Values> toTuple(ITuple input, Object value) {
        String member = getKeyFromTuple(input);
        List<Values> values = Lists.newArrayList();
        values.add(new Values(member, value));
        return values;
    }

    @Override
    public void declareOutputFields(OutputFieldsDeclarer declarer) {
        declarer.declare(new Fields("wordName", "count"));
    }

    @Override
    public RedisDataTypeDescription getDataTypeDescription() {
        return description;
    }

    @Override
    public String getKeyFromTuple(ITuple tuple) {
        return tuple.getStringByField("word");
    }

    @Override
    public String getValueFromTuple(ITuple tuple) {
        return null;
    }
}
```

根据如下方式使用：
```java
JedisPoolConfig poolConfig = new JedisPoolConfig.Builder()
        .setHost(host).setPort(port).build();
RedisLookupMapper lookupMapper = new WordCountRedisLookupMapper();
RedisLookupBolt lookupBolt = new RedisLookupBolt(poolConfig, lookupMapper);
```

#### 2.2 RedisStoreBolt

实现RedisStoreMapper：
```java
class WordCountStoreMapper implements RedisStoreMapper {
    private RedisDataTypeDescription description;
    private final String hashKey = "wordCount";

    public WordCountStoreMapper() {
        description = new RedisDataTypeDescription(
            RedisDataTypeDescription.RedisDataType.HASH, hashKey);
    }

    @Override
    public RedisDataTypeDescription getDataTypeDescription() {
        return description;
    }

    @Override
    public String getKeyFromTuple(ITuple tuple) {
        return tuple.getStringByField("word");
    }

    @Override
    public String getValueFromTuple(ITuple tuple) {
        return tuple.getStringByField("count");
    }
}
```
根据如下方式使用：
```java
JedisPoolConfig poolConfig = new JedisPoolConfig.Builder()
                .setHost(host).setPort(port).build();
RedisStoreMapper storeMapper = new WordCountStoreMapper();
RedisStoreBolt storeBolt = new RedisStoreBolt(poolConfig, storeMapper);
```

#### 2.3 RedisFilterBolt

实现RedisFilterMapper：
```java
class BlacklistWordFilterMapper implements RedisFilterMapper {
    private RedisDataTypeDescription description;
    private final String setKey = "blacklist";

    public BlacklistWordFilterMapper() {
        description = new RedisDataTypeDescription(
                RedisDataTypeDescription.RedisDataType.SET, setKey);
    }

    @Override
    public void declareOutputFields(OutputFieldsDeclarer declarer) {
        declarer.declare(new Fields("word", "count"));
    }

    @Override
    public RedisDataTypeDescription getDataTypeDescription() {
        return description;
    }

    @Override
    public String getKeyFromTuple(ITuple tuple) {
        return tuple.getStringByField("word");
    }

    @Override
    public String getValueFromTuple(ITuple tuple) {
        return null;
    }
}
```
根据如下方式使用：
```java
JedisPoolConfig poolConfig = new JedisPoolConfig.Builder()
        .setHost(host).setPort(port).build();
RedisFilterMapper filterMapper = new BlacklistWordFilterMapper();
RedisFilterBolt filterBolt = new RedisFilterBolt(poolConfig, filterMapper);
```
### 3. 自定义Bolt

如果你的场景不适合 RedisStoreBolt，RedisLookupBolt 以及 RedisFilterBolt，那么 storm-redis 还提供了 AbstractRedisBolt，你可以自定义自己的业务逻辑。
```java
public static class LookupWordTotalCountBolt extends AbstractRedisBolt {
    private static final Logger LOG = LoggerFactory.getLogger(LookupWordTotalCountBolt.class);
    private static final Random RANDOM = new Random();

    public LookupWordTotalCountBolt(JedisPoolConfig config) {
        super(config);
    }

    public LookupWordTotalCountBolt(JedisClusterConfig config) {
        super(config);
    }

    @Override
    public void execute(Tuple input) {
        JedisCommands jedisCommands = null;
        try {
            jedisCommands = getInstance();
            String wordName = input.getStringByField("word");
            String countStr = jedisCommands.get(wordName);
            if (countStr != null) {
                int count = Integer.parseInt(countStr);
                this.collector.emit(new Values(wordName, count));

                // print lookup result with low probability
                if(RANDOM.nextInt(1000) > 995) {
                    LOG.info("Lookup result - word : " + wordName + " / count : " + count);
                }
            } else {
                // skip
                LOG.warn("Word not found in Redis - word : " + wordName);
            }
        } finally {
            if (jedisCommands != null) {
                returnInstance(jedisCommands);
            }
            this.collector.ack(input);
        }
    }

    @Override
    public void declareOutputFields(OutputFieldsDeclarer declarer) {
        // wordName, count
        declarer.declare(new Fields("wordName", "count"));
    }
}
```
### 4. Trident State 用法

- RedisState 和 RedisMapState，为单机 Redis 模式提供了 Jedis 接口。
- RedisClusterState 和 RedisClusterMapState，为 Redis 集群模式提供了 JedisCluster 接口。

RedisState:
```java
JedisPoolConfig poolConfig = new JedisPoolConfig.Builder()
    .setHost(redisHost).setPort(redisPort)
    .build();
RedisStoreMapper storeMapper = new WordCountStoreMapper();
RedisLookupMapper lookupMapper = new WordCountLookupMapper();
RedisState.Factory factory = new RedisState.Factory(poolConfig);

TridentTopology topology = new TridentTopology();
Stream stream = topology.newStream("spout1", spout);

stream.partitionPersist(factory,
    fields,
    new RedisStateUpdater(storeMapper).withExpire(86400000),
    new Fields()
);

TridentState state = topology.newStaticState(factory);
stream = stream.stateQuery(state, new Fields("word"),
    new RedisStateQuerier(lookupMapper),
    new Fields("columnName","columnValue")
);
```

RedisClusterState:
```java
Set<InetSocketAddress> nodes = new HashSet<InetSocketAddress>();
for (String hostPort : redisHostPort.split(",")) {
    String[] host_port = hostPort.split(":");
    nodes.add(new InetSocketAddress(host_port[0], Integer.valueOf(host_port[1])));
}
JedisClusterConfig clusterConfig = new JedisClusterConfig.Builder().setNodes(nodes).build();
RedisStoreMapper storeMapper = new WordCountStoreMapper();
RedisLookupMapper lookupMapper = new WordCountLookupMapper();
RedisClusterState.Factory factory = new RedisClusterState.Factory(clusterConfig);

TridentTopology topology = new TridentTopology();
Stream stream = topology.newStream("spout1", spout);

stream.partitionPersist(factory, fields,
    new RedisClusterStateUpdater(storeMapper).withExpire(86400000,
    new Fields()
);

TridentState state = topology.newStaticState(factory);
stream = stream.stateQuery(state, new Fields("word"),
    new RedisClusterStateQuerier(lookupMapper),
    new Fields("columnName","columnValue")
);
```

> storm版本:2.0.0-SNAPSHOT

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

原文：[Storm Redis Integration](https://storm.apache.org/releases/2.0.0-SNAPSHOT/storm-redis.html)
