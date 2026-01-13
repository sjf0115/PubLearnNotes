在大数据生态中，DataX 作为阿里开源的高效数据同步工具，支持多种数据源之间的数据传输。然而，官方版本并未提供 Kafka Writer 插件，这在实时数据同步场景中成为了一个技术缺口。本文将深入探讨如何从零实现一个稳定、高效的 DataX KafkaWriter 插件。

## 1. DataX 插件架构解析

### 1.1 DataX 插件机制核心原理

DataX采用 "Framework + Plugin" 架构，核心框架负责调度、任务切分、错误处理和流量控制，插件则专注于具体的数据读写逻辑。要实现 KafkaWriter，首先插件的入口类必须扩展 Writer 抽象类，并且分别实现 Job 和 Task 两个内部抽象类：
```java
public class KafkaWriter extends Writer {
    public static class Job extends Writer.Job {
        @Override
        public void init() {

        }

        @Override
        public List<Configuration> split(int mandatoryNumber) {
            return Collections.emptyList();
        }

        @Override
        public void destroy() {

        }
    }

    public static class Task extends Writer.Task {
        @Override
        public void init() {

        }

        @Override
        public void startWrite(RecordReceiver lineReceiver) {

        }

        @Override
        public void destroy() {

        }
    }
}
```
> Job 和 Task 的实现必须是内部类的形式。

### 1.2 DataX 任务执行流程

```
Job启动 → 切分多个Task → Task执行 → 结果汇总
    ↓
Reader读取 → Channel传输 → Writer写入
```

## 2. KafkaWriter 插件实现

### 2.1 依赖配置

```xml
<!-- pom.xml关键依赖 -->
<properties>
    <kafka.version>2.5.0</kafka.version>
</properties>

<dependencies>
    <!-- DataX -->
    <dependency>
        <groupId>com.alibaba.datax</groupId>
        <artifactId>datax-common</artifactId>
        <version>${datax-project-version}</version>
        <exclusions>
            <exclusion>
                <artifactId>slf4j-log4j12</artifactId>
                <groupId>org.slf4j</groupId>
            </exclusion>
        </exclusions>
    </dependency>

    <dependency>
        <groupId>org.slf4j</groupId>
        <artifactId>slf4j-api</artifactId>
    </dependency>

    <dependency>
        <groupId>ch.qos.logback</groupId>
        <artifactId>logback-classic</artifactId>
    </dependency>

    <!-- Kafka -->
    <dependency>
        <groupId>org.apache.kafka</groupId>
        <artifactId>kafka-clients</artifactId>
        <version>${kafka.version}</version>
    </dependency>
</dependencies>
```

### 2.2 Maven 插件配置

```xml
<build>
    <plugins>
        <!-- compiler plugin -->
        <plugin>
            <artifactId>maven-compiler-plugin</artifactId>
            <configuration>
                <source>${jdk-version}</source>
                <target>${jdk-version}</target>
                <encoding>${project-sourceEncoding}</encoding>
            </configuration>
        </plugin>
        <!-- assembly plugin -->
        <plugin>
            <artifactId>maven-assembly-plugin</artifactId>
            <configuration>
                <descriptors> <!--描述文件路径-->
                    <descriptor>src/main/assembly/package.xml</descriptor>
                </descriptors>
                <finalName>datax</finalName>
            </configuration>
            <executions>
                <execution>
                    <id>dwzip</id>
                    <phase>package</phase> <!-- 绑定到package生命周期阶段上 -->
                    <goals>
                        <goal>single</goal> <!-- 只运行一次 -->
                    </goals>
                </execution>
            </executions>
        </plugin>
    </plugins>
</build>
```
核心需要引入 Maven-assembly-plugin 插件，目的是要将写的程序和它本身所依赖的 jar 包一起 build 到一个包里，是 Maven 中针对打包任务而提供的标准插件。

### 2.3 package.xml

在上述 assembly plugin 插件的 descriptor 中定义了描述文件路径 `src/main/assembly/package.xml`，那么就需要在 `src/main/assembly/` 路径下创建 `package.xml` 文件：
```xml
<assembly
        xmlns="http://maven.apache.org/plugins/maven-assembly-plugin/assembly/1.1.0"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://maven.apache.org/plugins/maven-assembly-plugin/assembly/1.1.0 http://maven.apache.org/xsd/assembly-1.1.0.xsd">
    <id></id>
    <formats>
        <format>dir</format>
    </formats>
    <includeBaseDirectory>false</includeBaseDirectory>
    <fileSets>
        <fileSet>
            <directory>src/main/resources</directory>
            <includes>
                <include>plugin.json</include>
            </includes>
            <outputDirectory>plugin/writer/kafkawriter</outputDirectory>
        </fileSet>
        <fileSet>
            <directory>target/</directory>
            <includes>
                <include>kafkawriter-0.0.1-SNAPSHOT.jar</include>
            </includes>
            <outputDirectory>plugin/writer/kafkawriter</outputDirectory>
        </fileSet>
    </fileSets>

    <dependencySets>
        <dependencySet>
            <useProjectArtifact>false</useProjectArtifact>
            <outputDirectory>plugin/writer/kafkawriter/libs</outputDirectory>
            <scope>runtime</scope>
        </dependencySet>
    </dependencySets>
</assembly>
```

### 2.4 plugin.json

代码写好了，有没有想过框架是怎么找到插件的入口类的？框架是如何加载插件的呢？在每个插件的项目中，都有一个 `plugin.json` 文件，这个文件定义了插件的相关信息，包括入口类。在 `src/main/resources/` 下创建 `plugin.json` 文件：
```json
{
  "name": "kafkawriter",
  "class": "com.alibaba.datax.plugin.writer.kafkawriter.KafkaWriter",
  "description": "Kafka Writer",
  "developer": "sjf0115"
}
```
- name: 插件名称，大小写敏感。框架根据用户在配置文件中指定的名称来搜寻插件。 十分重要 。
- class: 入口类的全限定名称，框架通过反射插件入口类的实例。十分重要 。
- description: 描述信息。
- developer: 开发人员。

## 3. 插件配置

### 3.1 参数说明

- server
  - 必填参数
  - Kafka 的 server 地址，格式为 ip:port。
- topic
  - 必填参数
  - Kafka 的 topic。每条发布至 Kafka 集群的消息都有一个类别，该类别被称为 topic，一个topic是对一组消息的归纳。
- valueIndex
  - 可选参数
  - Kafka Writer 中作为 Value 的那一列。如果不填写，默认将所有列拼起来作为 Value，分隔符为 fieldDelimiter。
- writeMode
  - 可选参数
  - 如果配置了valueIndex，该配置项无效。
  - 当未配置 valueIndex 时，该配置项决定将源端读取记录的所有列拼接作为写入 Kafka 记录 Value 的格式，可选值为 text 和 JSON，默认值为 text。
    - 配置为 text，将所有列按照 fieldDelimiter 指定分隔符拼接。
    - 配置为 JSON，将所有列按照 column 参数指定字段名称拼接为 JSON 字符串。
  - 例如源端记录有三列，值为 a、b 和 c
    - writeMode 配置为 text、fieldDelimiter 配置为 # 时，写入 Kafka 的记录 Value 为字符串 `a#b#c`；
    - writeMode 配置为 JSON、column 配置为 `[{"name":"col1"},{"name":"col2"},{"name":"col3"}]` 时，写入 Kafka 的记录 Value 为字符串 `{"col1":"a","col2":"b","col3":"c"}`。
- fieldDelimiter
  - 可选参数
  - 当 writeMode 配置为 text，并且未配置 valueIndex 时，将源端读取记录的所有列按照该配置项指定列分隔符拼接作为写入 Kafka 记录的 Value
  - 支持配置单个或者多个字符作为分隔符，支持以 `\u0001` 格式配置 Unicode 字符，支持 `\t`、`\n` 等转义字符。默认值为 `\t`。
  - 如果 writeMode 未配置为 text 或者配置了 valueIndex，该配置项无效。
- column

### 3.2 插件配置示例

#### 3.2.1 基础配置

```json
{
  "job": {
    "content": [{
      "writer": {
        "name": "kafkawriter",
        "parameter": {
          "server": "kafka01:9092,kafka02:9092,kafka03:9092",
          "topic": "datax_topic",
          "format": "json",
          "sync": false,
          "batchSize": 16384,
          "lingerMs": 100,
          "acks": "1",
          "retryTimes": 3,
          "producer.compression.type": "snappy",
          "producer.max.in.flight.requests.per.connection": 5
        }
      }
    }]
  }
}
```

### 3.2 高级配置

```json
{
  "parameter": {
    "bootstrapServers": "kafka-cluster:9092",
    "topic": "user_behavior",
    "keyField": "user_id",
    "partitionStrategy": "hash",
    "format": "json",
    "column": [
      {"name": "user_id", "type": "string"},
      {"name": "action", "type": "string"},
      {"name": "timestamp", "type": "long"}
    ],
    "producer.security.protocol": "SASL_SSL",
    "producer.sasl.mechanism": "PLAIN",
    "producer.ssl.truststore.location": "/path/to/truststore.jks"
  }
}
```



## 4. 核心代码实现

### 4.1 KafkaWriterErrorCode

```java
public enum KafkaWriterErrorCode implements ErrorCode {
    REQUIRED_VALUE("KafkaWriter-00", "Required parameter is not filled .")
    ;

    private final String code;
    private final String description;

    KafkaWriterErrorCode(String code, String description) {
        this.code = code;
        this.description = description;
    }

    @Override
    public String getCode() {
        return this.code;
    }

    @Override
    public String getDescription() {
        return this.description;
    }

    @Override
    public String toString() {
        return String.format("Code:[%s], Description:[%s]. ", this.code, this.description);
    }
}
```

#### 4.2 Job 执行类

#### 4.2.1 init

```java
package com.alibaba.datax.plugin.writer.kafkawriter;

public class KafkaWriter extends Writer {

    public static class Job extends Writer.Job {
        private Configuration originalConfig;
        private KafkaProducerManager producerManager;

        @Override
        public void init() {
            this.originalConfig = super.getPluginJobConf();
            // 验证必填参数
            this.validateParameters();
        }

        private void validateParameters() {
            // 检查bootstrap.servers配置
            originalConfig.getNecessaryValue(
                Key.BOOTSTRAP_SERVERS,
                KafkaWriterErrorCode.REQUIRED_VALUE
            );

            // 检查topic配置
            originalConfig.getNecessaryValue(
                Key.TOPIC,
                KafkaWriterErrorCode.REQUIRED_VALUE
            );
        }

        @Override
        public void prepare() {
            // 初始化Kafka生产者连接池
            this.producerManager = KafkaProducerManager.getInstance(originalConfig);
        }

        @Override
        public List<Configuration> split(int adviceNumber) {
            List<Configuration> taskConfigs = new ArrayList<>();
            for (int i = 0; i < adviceNumber; i++) {
                Configuration taskConfig = originalConfig.clone();
                taskConfig.set(Constant.TASK_ID, i);
                taskConfigs.add(taskConfig);
            }
            return taskConfigs;
        }

        @Override
        public void post() {
            // 任务后置处理
        }

        @Override
        public void destroy() {
            if (producerManager != null) {
                producerManager.close();
            }
        }
    }
}
```

#### 4.3 Task

```java
public static class Task extends Writer.Task {

    private Configuration taskConfig;
    private KafkaProducer<String, String> producer;
    private String topic;
    private String keyField;
    private boolean syncSend;
    private int retryTimes;

    @Override
    public void init() {
        this.taskConfig = super.getPluginJobConf();

        // 解析配置参数
        this.topic = taskConfig.getString(Key.TOPIC);
        this.keyField = taskConfig.getString(Key.KEY_FIELD, "");
        this.syncSend = taskConfig.getBool(Key.SYNC_SEND, false);
        this.retryTimes = taskConfig.getInt(Key.RETRY_TIMES, 3);

        // 创建Kafka生产者
        Properties props = buildKafkaProperties(taskConfig);
        this.producer = new KafkaProducer<>(props);
    }

    private Properties buildKafkaProperties(Configuration config) {
        Properties props = new Properties();

        // 必填参数
        props.put("bootstrap.servers",
                 config.getString(Key.BOOTSTRAP_SERVERS));
        props.put("key.serializer",
                 "org.apache.kafka.common.serialization.StringSerializer");
        props.put("value.serializer",
                 "org.apache.kafka.common.serialization.StringSerializer");

        // 可选参数
        config.getKeys().forEach(key -> {
            if (key.startsWith("producer.")) {
                String kafkaKey = key.substring(9);
                props.put(kafkaKey, config.getString(key));
            }
        });

        // 设置生产者的关键配置
        props.putIfAbsent("acks", config.getString(Key.ACKS, "1"));
        props.putIfAbsent("retries", config.getInt(Key.RETRIES, 3));
        props.putIfAbsent("batch.size",
                         config.getInt(Key.BATCH_SIZE, 16384));
        props.putIfAbsent("linger.ms",
                         config.getInt(Key.LINGER_MS, 1));
        props.putIfAbsent("buffer.memory",
                         config.getLong(Key.BUFFER_MEMORY, 33554432L));

        return props;
    }

    @Override
    public void startWrite(RecordReceiver recordReceiver) {
        Record record;
        int recordCount = 0;
        List<Future<RecordMetadata>> futures = new ArrayList<>();

        try {
            while ((record = recordReceiver.getFromReader()) != null) {
                // 数据转换
                String message = convertRecordToMessage(record);
                String key = extractKey(record);

                // 发送消息
                Future<RecordMetadata> future = producer.send(
                    new ProducerRecord<>(topic, key, message)
                );

                if (syncSend) {
                    // 同步发送模式
                    future.get();
                } else {
                    futures.add(future);
                }

                recordCount++;

                // 批量确认
                if (recordCount % 1000 == 0) {
                    waitForFutures(futures);
                    futures.clear();
                }
            }

            // 等待剩余的消息发送完成
            waitForFutures(futures);

        } catch (Exception e) {
            throw DataXException.asDataXException(
                KafkaWriterErrorCode.WRITE_ERROR, e
            );
        }
    }

    private String convertRecordToMessage(Record record) {
        // 支持多种输出格式
        int columnNumber = record.getColumnNumber();
        Map<String, Object> messageMap = new LinkedHashMap<>();

        for (int i = 0; i < columnNumber; i++) {
            Column column = record.getColumn(i);
            String columnName = "col_" + i; // 实际使用中应从配置获取列名
            messageMap.put(columnName, column.asString());
        }

        // 支持JSON、CSV等格式
        String format = taskConfig.getString(Key.FORMAT, "json");
        switch (format.toLowerCase()) {
            case "json":
                return new Gson().toJson(messageMap);
            case "csv":
                return messageMap.values().stream()
                    .map(Object::toString)
                    .collect(Collectors.joining(","));
            default:
                return messageMap.toString();
        }
    }

    private String extractKey(Record record) {
        if (StringUtils.isNotBlank(keyField)) {
            // 从记录中提取指定字段作为Key
            // 这里需要根据实际列名映射实现
        }
        return null; // 使用Kafka默认分区策略
    }

    private void waitForFutures(List<Future<RecordMetadata>> futures)
        throws Exception {
        for (Future<RecordMetadata> future : futures) {
            future.get();
        }
    }

    @Override
    public void destroy() {
        if (producer != null) {
            producer.close();
        }
    }
}
```

## 5. 插件安装

### 5.1 生成插件

DataX 使用 assembly 打包，打包命令如下：
```
mvn -U clean package assembly:assembly -Dmaven.test.skip=true -pl :kafkawriter -am -Dautoconfig.skip
```
当你看到如下类似信息时表示生成打包成功：
```
...
[INFO] ------------------------------------------------------------------------
[INFO] Reactor Summary:
[INFO]
[INFO] datax-all 0.0.1-SNAPSHOT ........................... SUCCESS [01:39 min]
[INFO] datax-common ....................................... SUCCESS [  1.178 s]
[INFO] kafkawriter 1.0 .................................... SUCCESS [  2.219 s]
[INFO] ------------------------------------------------------------------------
[INFO] BUILD SUCCESS
[INFO] ------------------------------------------------------------------------
[INFO] Total time: 01:44 min
[INFO] Finished at: 2026-01-11T18:05:47+08:00
[INFO] ------------------------------------------------------------------------
```
打包生成的插件在目录 `DataX/kafkawriter/target/datax/plugin` 下：
```
smarsi:datax smartsi$ tree -L 4
.
└── plugin
    └── writer
        └── kafkawriter
            ├── kafkawriter-1.0.jar
            ├── libs
            └── plugin.json
```
- libs: 插件的依赖库。
- plugin.json: 插件描述文件。

> 插件的目录名字必须和plugin.json中定义的插件名称一致

### 5.2 安装 Datax

[]()

### 5.3 上传自定义插件

DataX 集群 Writer 插件均存放在 `${DATAX_HOME}/plugin/writer` 目录下：
```
smarsi:writer smartsi$ ls -al
total 0
drwxr-xr-x@ 41 smartsi  wheel  1312  8 23 21:03 .
drwxr-xr-x@  4 smartsi  wheel   128  8 23 21:03 ..
drwxr-xr-x@  6 smartsi  wheel   192  8 23 21:03 adbpgwriter
drwxr-xr-x@  6 smartsi  wheel   192  8 23 21:03 adswriter
drwxr-xr-x@  6 smartsi  wheel   192  8 23 21:03 cassandrawriter
drwxr-xr-x@  6 smartsi  wheel   192  8 23 21:03 clickhousewriter
...
```
我们自定义的 KafkaWriter 插件也需要上传到该目录下。将自己开发的 plugin 目录下所有文件上传到 DataX 插件目录下：
```

```

## 6. 实践

```sql
CREATE TABLE `datax_user` (
  `id` bigint NOT NULL COMMENT '主键ID',
  `name` varchar(30) DEFAULT NULL COMMENT '姓名',
  `age` int DEFAULT NULL COMMENT '年龄',
  `email` varchar(50) DEFAULT NULL COMMENT '邮箱',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

INSERT INTO datax_user (id, name, age, email) VALUES
  ('1', 'Jone', 18, 'jone@163.com'),
  ('2', 'Jack', 20, 'jack@163.com'),
  ('3', 'Tom', 28, 'tom@163.com'),
  ('4', 'Sandy', 21, 'sandy@163.com'),
  ('5', 'Billie', 24, 'billie@163.com'),
  ('6', null, 24, null)
;
```

### 6.1 作业配置

创建 DataX 同步作业配置文件 mysql2kafka.json 文件，实现从 MySQL 读取数据发送到 Kafka：
```json
{
    "job": {
        "setting": {
            "speed": {
                 "channel": 3
            },
            "errorLimit": {
                "record": 0,
                "percentage": 0.02
            }
        },
        "content": [
            {
                "reader": {
                    "name": "mysqlreader",
                    "parameter": {
                        "username": "root",
                        "password": "root",
                        "column": [
                            "id",
                            "name",
                            "age",
                            "email"
                        ],
                        "splitPk": "id",
                        "connection": [
                            {
                                "table": [
                                    "datax_user"
                                ],
                                "jdbcUrl": [
                                    "jdbc:mysql://127.0.0.1:3306/test"
                                ]
                            }
                        ]
                    }
                },
               "writer": {
                    "name": "kafkawriter",
                    "parameter": {
                        "server": "127.0.0.1:9092",
                        "keyIndex": 1,
                        "valueIndex": 1,
                        "topic": "user",
                        "":"",
                        "batchSize": 1024
                    }
                }
            }
        ]
    }
}
```

```json
"writer": {
     "name": "kafkawriter",
     "parameter": {
         "server": "127.0.0.1:9092",
         "topic": "user",
         "keyIndex": 1,
         "nullKeyFormat":"default",
         "writeMode": "text",
         "fieldDelimiter":",",
         "nullValueFormat":"null",
         "batchSize": 1024
     }
}
```

```json
"writer": {
     "name": "kafkawriter",
     "parameter": {
         "server": "127.0.0.1:9092",
         "topic": "user",
         "keyIndex": 1,
         "nullKeyFormat":"default",
         "writeMode": "json",
         "nullValueFormat":"-",
         "column": [
            {"name": "id", "type": "JSON_NUMBER"},
            {"name": "name", "type": "JSON_STRING"},
            {"name": "age", "type": "JSON_NUMBER"},
            {"name": "email", "type": "JSON_STRING"},
            {"name": "gender", "type": "JSON_STRING"}
         ],
         "batchSize": 1024
     }
}
```

### 6.2 运行

```
python3 bin/datax.py job/kafka/mysql2kafka_json.json
```

> 可能报错：

> 2022-12-09 15:18:30.412 [main] WARN ConfigParser - 插件[txtfilereader,kafkawriter]加载失败，1s后重试... Exception:Code:[Common-00], Describe:[您提供的配置文件存在错误信息，请检查您的作业配置 .] - 配置信息错误，您提供的配置文件[/home/hadoop/datax/plugin/writer/.DS_Store/plugin.json]不存在. 请检查您的配置文件.

> 原因，Mac电脑打包自己默认将.DS_Store打进去了，需要删除，不然DataX会解析失败

执行结果：
```java
2026-01-11 22:52:59.351 [job-0] INFO  JobContainer - PerfTrace not enable!
2026-01-11 22:52:59.352 [job-0] INFO  StandAloneJobContainerCommunicator - Total 6 records, 102 bytes | Speed 10B/s, 0 records/s | Error 0 records, 0 bytes |  All Task WaitWriterTime 0.000s |  All Task WaitReaderTime 0.000s | Percentage 100.00%
2026-01-11 22:52:59.355 [job-0] INFO  JobContainer -
任务启动时刻                    : 2026-01-11 22:52:48
任务结束时刻                    : 2026-01-11 22:52:59
任务总计耗时                    :                 10s
任务平均流量                    :               10B/s
记录写入速度                    :              0rec/s
读出记录总数                    :                   6
读写失败总数                    :                   0
```

> [异源数据同步 → DataX 为什么要支持 kafka？](https://cloud.tencent.com/developer/article/2447802)
