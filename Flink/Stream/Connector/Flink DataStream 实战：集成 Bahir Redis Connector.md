
在大数据实时处理场景中，Apache Flink 作为流式计算引擎的标杆，常需要与外部存储系统进行高效交互。Redis 作为高性能的内存键值数据库，常被用于实时缓存、状态存储和低延迟查询。本文将深入探讨如何在 Flink DataStream API 中通过 Redis Connector 实现数据的高效写入，覆盖核心原理、代码实践、调优技巧和常见问题解决方案。

---

## 1. 技术选型与架构设计

### 1.1 为何选择 Redis Connector？

- **低延迟写入**：Redis 内存存储特性与 Flink 的实时处理能力完美契合。
- **丰富数据结构**：支持 String、Hash、List、Set、Sorted Set 等结构，适应不同业务场景。
- **生态兼容性**：通过 Bahir 等扩展库实现与 Flink 的无缝集成。

### 1.2 主流 Connector 对比

| Connector 类型         | 优势                          | 适用场景                     |
|-----------------------|-----------------------------|---------------------------|
| **Bahir Redis**       | 官方推荐，轻量级，支持基础操作       | 简单 Key-Value 或 Hash 写入   |
| **自定义 SinkFunction** | 灵活性高，可深度定制 Redis 交互逻辑 | 复杂数据结构或需要事务支持的场景   |
| **Jedis/Pool 直接调用** | 性能可控，直接利用原生客户端         | 超高频写入或特殊连接池管理需求     |

在这使用 **Apache Bahir** 提供的 Redis Connector。

---

## 2. 环境准备与依赖配置

### 2.1 添加 Maven 依赖

```xml
<dependency>
    <groupId>org.apache.bahir</groupId>
    <artifactId>flink-connector-redis_2.11</artifactId>
    <version>1.1.0</version>
</dependency>
```

### 2.2 Redis 服务准备

确保 Redis 实例已启动并开放访问权限，针对不同的部署模式选择对应的配置类：

| 部署模式 | 特点 | 适用场景 | 配置类 |
| :------------- | :------------- | :------------- | :------------- |
| 单机模式  | 单个 Redis 节点运行，无高可用性，适合开发测试或简单场景 | 本地开发、小规模数据存储 | FlinkJedisPoolConfig |
| 哨兵模式  | 通过 Sentinel 监控主从节点，主节点故障时自动切换从节点为新的主节点，实现高可用 | 对高可用性有要求的线上环境 | FlinkJedisSentinelConfig |
| 集群模式  | 数据分片存储在多个节点，支持水平扩展和高并发，客户端自动路由请求到正确的分片 | 大规模数据、高性能读写、分布式存储需求 | FlinkJedisClusterConfig |

> 单机模式默认端口 `6379`

---

## 3. 核心实现：从数据流到 Redis 写入

### 3.1 定义数据模型

假设处理用户行为事件 `UserBehavior`：
```java
public class SimpleUserBehavior {
    private Long userId;
    private Long timestamp;

    // 必须提供无参构造函数
    public SimpleUserBehavior() {
    }

    public SimpleUserBehavior(Long userId, Long timestamp) {
        this.userId = userId;
        this.timestamp = timestamp;
    }

    // Getter 和 Setter 方法
    public Long getUserId() {
        return userId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public Long getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(Long timestamp) {
        this.timestamp = timestamp;
    }
}
```
---

### 3.2 实现 RedisMapper

通过 `RedisMapper` 接口定义数据到 Redis 命令的转换逻辑：

```java
// 自定义 RedisMapper，定义如何将数据转换为 Redis 命令
public static class UserBehaviorRedisMapper implements RedisMapper<SimpleUserBehavior> {
    @Override
    public RedisCommandDescription getCommandDescription() {
        // 使用 SET 命令（Key-Value 直接存储）
        return new RedisCommandDescription(RedisCommand.SET);
    }

    @Override
    public String getKeyFromData(SimpleUserBehavior behavior) {
        // Redis Key: 用户ID
        return String.valueOf(behavior.getUserId());
    }

    @Override
    public String getValueFromData(SimpleUserBehavior behavior) {
        // Redis Value: 用户操作时间戳
        return String.valueOf(behavior.getTimestamp());
    }
}
```
---

### 3.3 配置连接池配置

单机模式下需要直接连接指定主机和端口的 Redis 实例：
```java
// Redis 连接配置
FlinkJedisPoolConfig redisConfig = new FlinkJedisPoolConfig.Builder()
    .setHost("localhost")    // Redis 主机
    .setPort(6379)          // Redis 端口
    .setDatabase(0) // Redis 数据库
    .setTimeout(3000)
    .setMaxTotal(100) // 连接池最大连接数
    .build();
```
> 单机模式下，若主节点宕机，需手动恢复。

哨兵模式下通过 Sentinel 节点监控主从状态，需要指定 Sentinel 节点列表：
```java
FlinkJedisSentinelConfig config = new FlinkJedisSentinelConfig.Builder()
    .setSentinels(new HashSet<>(Arrays.asList("sentinel1:26379", "sentinel2:26380"))) // Sentinel 节点列表
    .setMasterName("mymaster")      // Sentinel 监控的主节点名称
    .setDatabase(0)                 // 数据库索引
    .setSoTimeout(3000)             // Socket 超时时间（ms）
    .build();
```

集群模式下数据分片存储在多个节点，需要指定集群节点列表：
```java
FlinkJedisClusterConfig config = new FlinkJedisClusterConfig.Builder()
    .setNodes(new HashSet<>(Arrays.asList("redis-node1:6379", "redis-node2:6380"))) // 集群节点列表
    .setMaxRedirects(3)            // 最大重定向次数（应对集群拓扑变化）
    .build();
```

---

### 3.4 构建 Redis Sink

```java
// 创建 Sink
RedisSink<SimpleUserBehavior> redisSink = new RedisSink<>(
    redisConfig,
    new UserBehaviorRedisMapper()
);

// 将数据流接入 Sink
DataStream<UserBehavior> source = ... // 来自 Kafka 或其他 Source
source.addSink(redisSink); // 将数据写入 Redis
```
---

### 3.5 示例

下面示例中使用 DataGeneratorSource 随机构造用户ID以及时间戳生成随机用户写入 Redis 中存储每个用户的最新操作时间：
```java
public class BahirRedisConnectorExample {
    private static final Logger LOG = LoggerFactory.getLogger(BahirRedisConnectorExample.class);

    public static void main(String[] args) throws Exception {
        // 1. 创建 Flink 流执行环境
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        // 2. DataGeneratorSource
        RandomGenerator<SimpleUserBehavior> randomGenerator = new RandomGenerator<SimpleUserBehavior>() {
            @Override
            public SimpleUserBehavior next() {
                SimpleUserBehavior userBehavior = new SimpleUserBehavior(
                        random.nextLong(10000001, 90000001),
                        System.currentTimeMillis()
                );
                LOG.info("Source UserId: " + userBehavior.getUserId() + ", Timestamp: " + userBehavior.getTimestamp());
                return userBehavior;
            }
        };
        DataGeneratorSource<SimpleUserBehavior> generatorSource = new DataGeneratorSource<>(randomGenerator, 1L, 10L);
        DataStream<SimpleUserBehavior> source = env.addSource(generatorSource, "DataGeneratorSource")
                .returns(Types.POJO(SimpleUserBehavior.class));

        // 3. 配置 Redis 连接
        FlinkJedisPoolConfig redisConfig = new FlinkJedisPoolConfig.Builder()
                .setHost("localhost")    // Redis 主机
                .setPort(6379)          // Redis 端口
                .setDatabase(0) // Redis 数据库
                .setTimeout(3000)
                .setMaxTotal(100) // 连接池最大连接数
                .build();

        // 4. 创建 RedisSink
        RedisSink<SimpleUserBehavior> redisSink = new RedisSink<>(
                redisConfig,
                new UserBehaviorRedisMapper()
        );

        // 5. 将数据写入 Redis
        source.addSink(redisSink);

        // 6. 执行任务
        env.execute("BahirRedisConnectorExample");
    }

    // 自定义 RedisMapper，定义如何将数据转换为 Redis 命令
    public static class UserBehaviorRedisMapper implements RedisMapper<SimpleUserBehavior> {
        @Override
        public RedisCommandDescription getCommandDescription() {
            // 使用 SET 命令（Key-Value 直接存储）
            return new RedisCommandDescription(RedisCommand.SET);
        }

        @Override
        public String getKeyFromData(SimpleUserBehavior behavior) {
            // Redis Key: 用户ID
            return String.valueOf(behavior.getUserId());
        }

        @Override
        public String getValueFromData(SimpleUserBehavior behavior) {
            // Redis Value: 用户操作时间戳
            return String.valueOf(behavior.getTimestamp());
        }
    }
}
```
运行上述程序随机生成了如下 10 个用户：
```java
16:37:52,215 INFO  BahirRedisConnectorExample [] - Source UserId: 39429175, Timestamp: 1746952672215
16:37:52,215 INFO  BahirRedisConnectorExample [] - Source UserId: 82172014, Timestamp: 1746952672215
16:37:52,215 INFO  BahirRedisConnectorExample [] - Source UserId: 16610178, Timestamp: 1746952672215
16:37:52,215 INFO  BahirRedisConnectorExample [] - Source UserId: 75186643, Timestamp: 1746952672215
16:37:53,210 INFO  BahirRedisConnectorExample [] - Source UserId: 39159513, Timestamp: 1746952673210
16:37:53,210 INFO  BahirRedisConnectorExample [] - Source UserId: 73432909, Timestamp: 1746952673210
16:37:53,210 INFO  BahirRedisConnectorExample [] - Source UserId: 16058372, Timestamp: 1746952673210
16:37:53,210 INFO  BahirRedisConnectorExample [] - Source UserId: 69252173, Timestamp: 1746952673210
16:37:54,212 INFO  BahirRedisConnectorExample [] - Source UserId: 86405133, Timestamp: 1746952674212
16:37:54,212 INFO  BahirRedisConnectorExample [] - Source UserId: 65315201, Timestamp: 1746952674212
```
可以通过 Redis Cli 来验证写入是否成功:
```
127.0.0.1:6379> keys *
 1) "16058372"
 2) "75186643"
 3) "69252173"
 4) "86405133"
 5) "73432909"
 6) "39429175"
 7) "65315201"
 8) "16610178"
 9) "39159513"
10) "82172014"
127.0.0.1:6379> get 16058372
"1746952673210"
127.0.0.1:6379>
```
通过上述可以看到通过 Flink DataStream 写入 Redis 成功。

---

- 参考:[Flink Redis Connector](https://bahir.apache.org/docs/flink/current/flink-streaming-redis/)
