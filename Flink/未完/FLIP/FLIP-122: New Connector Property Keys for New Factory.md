
## 1. 目标

表 DDL 中的 WITH 选项定义了 Connector 创建 Source/ Sink 所需的属性。Connector 属性结构是很久以前为 SQL CLI config YAML 设计的。这就是为什么我们会用 `connector.*` 和 `format.*` 前缀定义层次结构的原因。但是，从 DDL 的角度来看，`connector.*` 这种格式显的就比较冗长，因为 WITH 中所有选项都是针对特定 Connector 的，包括格式。此外，我们可能希望引入更多针对于 Connector 的属性，以允许指定哪些字段应该在 FLIP-107 中记录的哪些部分结束，例如 'key.fields'、'timestamp.field'。前缀 `connector.` 会使属性选型变得冗长，但是没有 `connector.` 前缀又会出现不一致。

FLIP-122 重新整理了 Table/SQL Connector 的”With”配置项。由于历史原因，With 配置项有一些冗余或不一致的地方，例如所有的配置项都以 connector. 开头以及不同的配置项名称模式等。修改后的配置项解决了这些冗余和不一致的问题。（需要强调的是，现有的配置项仍然可以正常使用）。

以 Kafka 为例，在 1.11 版本之前用户的 DDL 需要声明成如下方式：
```sql
CREATE TABLE user_behavior (
  ...
) WITH (
  'connector.type'='kafka',
  'connector.version'='universal',
  'connector.topic'='user_behavior',
  'connector.startup-mode'='earliest-offset',
  'connector.properties.zookeeper.connect'='localhost:2181',
  'connector.properties.bootstrap.servers'='localhost:9092',
  'format.type'='json'
);
```
而在 Flink SQL 1.11 中则简化为：
```sql
CREATE TABLE user_behavior (
  ...
) WITH (
  'connector'='kafka',
  'topic'='user_behavior',
  'scan.startup.mode'='earliest-offset',
  'properties.zookeeper.connect'='localhost:2181',
  'properties.bootstrap.servers'='localhost:9092',
  'format'='json'
);
```
DDL 表达的信息量丝毫未少，但是看起来清爽许多。

本次 FLIP 希望进一步简化 Connector 属性，以使属性更加简洁、更易读，并与 FLIP-107 更好地配合。随着新 TableSource/TableSink/Factory 接口的引入，这为重构 Connector 属性提供了好机会。

## 2. 优化

在新的属性中，主要有 4 点变化：
- 'connector.type' 修改为 'connector'，'format.type' 修改为 'format'。
- 将 'connector.version' 放入 'connector' 中作为标识符，并使用 '-' 作为 Connector 名称与版本的分隔符。我们建议对现有 Connector 使用如下标识符：
  - kafka：kafka 0.11+ 版本。不加 '-universal'后缀，是因为 'universal' 不好理解。
  - kafka-0.11：kafka 0.11 版本。
  - kafka-0.10：kafka 0.10 版本。
  - elasticsearch-6：Elasticsearch 6.x 版本。
  - elasticsearch-7：Elasticsearch 7.x 版本。
  - hbase-1.4：Hbase 1.4.x 版本。
  - jdbc
  - filesystem
- 其他所有的 'connector.' 前缀都会被删除，但是 'format.' 前缀会继续被保留。
- 使用 'scan'、'lookup' 以及 'sink' 前缀重构一些属性键。这样可以将 Source 和 Sink 的选项区分开。这些术语是与 FLIP-95 中的接口、ScanTableSource、LookupTableSource 和 DynamicTableSink 对齐。

我们之所以仍然保持 'format.' 前缀是用来构建属性的层次结构。我们可以通过框架提供的工具轻松提取所有以 'format' 为前缀的属性。然后使用提取的属性来发现、验证以及实例化格式。'connector' 属性键是框架级的，不会被 Connector 重命名为其他键。这就意味着所有 Connector 都会具有这个属性键。

## 3.删除 Factory#factoryVersion() 方法

如上所述，我们希望使用唯一标识符来发现 Factory。所以不再需要 Factory#factoryVersion() 方法。我们应该删除这个在 FLIP-95 中引入的方法。

## 4. 新的属性 Key

我将一些命名更改涂成红色，不是简单地删除 'connector.' 前缀或者是重构 'scan'、'lookup'、'sink' 前缀。

### 4.1 Kafka

| 旧属性 Key                              | 新属性 Key                                            | 备注            |
| :-------------------------------------  :---------------------------------------------------- | :------------- |
| connector.type                         | connector                                            | |
| connector.version	                     | 废弃不在使用                                           | 合并到 'connector' Key 中 |
| connector.topic	                       | topic                                                | |
| connector.properties.zookeeper.connect | properties.zookeeper.connect                         | |
| connector.properties.bootstrap.servers | properties.bootstrap.servers                         | |
| connector.properties.group.id	         | properties.group.id                                  | |
| connector.startup-mode	               | <font color=red>scan.startup.mode</font>             | |
| connector.specific-offsets	           | <font color=red>scan.startup.specific-offsets</font> | |
| connector.startup-timestamp-millis	   | <font color=red>scan.startup.timestamp-millis</font> | |
| connector.sink-partitioner	           | <font color=red>sink.partitioner</font>              | fixed、round-robin 或者自定义类名 |
| connector.sink-partitioner-class	     | 废弃不在使用	                                          | 合并到 sink.partitioner' Key 中 |
| format.type	                           | format                                               | |

### 4.2 Elasticsearch

| 旧属性 Key                                 | 新属性 Key                                                | 备注                     |
| :---------------------------------------- | :------------------------------------------------------- | :------------------------|
| connector.type                            | connector                                                | |
| connector.version	                        | 废弃不在使用                                               | 合并到 'connector' Key 中 |
| connector.hosts                           |	hosts                                                    | |
| connector.index                           |	index                                                    | |
| connector.document-type	                  | document-type                                            | |
| connector.failure-handler	                | failure-handler                                          | |
| connector.connection-max-retry-timeout	  | <font color=red>connection.max-retry-timeout</font>      | |
| connector.connection-path-prefix	        | <font color=red>connection.path-prefix</font>            | |
| connector.key-delimiter	                  | <font color=red>document-id.key-delimiter</font>	       | |
| connector.key-null-literal	              | <font color=red>document-id.key-null-literal</font>      | |
| connector.flush-on-checkpoint	            | sink.flush-on-checkpoint                                 | |
| connector.bulk-flush.max-actions          |	sink.bulk-flush.max-actions	                             | |
| connector.bulk-flush.max-size	            | sink.bulk-flush.max-size                                 | |
| connector.bulk-flush.interval	            | sink.bulk-flush.interval                                 | |
| connector.bulk-flush.back-off.type	      | <font color=red>sink.bulk-flush.back-off.strategy</font> | |
| connector.bulk-flush.back-off.max-retries	| sink.bulk-flush.back-off.max-retries                     | |
| connector.bulk-flush.back-off.delay	      | sink.bulk-flush.back-off.delay                           | |

### 4.3 HBase

| 旧属性 Key                             | 新属性 Key                                     | 备注                     |
| :------------------------------------ | :-------------------------------------------- | :------------------------|
| connector.type                        | connector                                     | |
| connector.version	                    | 废弃不在使用                                    | 合并到 'connector' Key 中 |
| connector.table-name	                | table-name                                    | |
| connector.zookeeper.quorum	          | zookeeper.quorum                              | |
| connector.zookeeper.znode.parent	    | <font color=red>zookeeper.znode-parent</font> | |
| connector.write.buffer-flush.max-size	| sink.buffer-flush.max-size                    | |
| connector.write.buffer-flush.max-rows	| sink.buffer-flush.max-rows                    | |
| connector.write.buffer-flush.interval	| sink.buffer-flush.interval                    | |

### 4.4 JDBC

| 旧属性 Key                             | 新属性 Key                                        | 备注     |
| :------------------------------------ | :----------------------------------------------- | :------ |
| connector.type                       | connector                                         | |
| connector.url	                       | url                                               | |
| connector.table	                     | <font color=red>table-name</font>                 | |
| connector.driver	                   | driver                                            | |
| connector.username	                 | username                                          | |
| connector.password	                 | password                                          | |
| connector.read.partition.column	     | scan.partition.column                             | |
| connector.read.partition.num	       | scan.partition.num                                | |
| connector.read.partition.lower-bound | scan.partition.lower-bound                        | |
| connector.read.partition.upper-bound | scan.partition.upper-bound                        | |
| connector.read.fetch-size	           | scan.fetch-size                                   | |
| connector.lookup.cache.max-rows	     | lookup.cache.max-rows                             | |
| connector.lookup.cache.ttl	         | lookup.cache.ttl                                  | |
| connector.lookup.max-retries	       | lookup.max-retries                                | |
| connector.write.flush.max-rows	     | <font color=red>sink.buffer-flush.max-rows</font> | |
| connector.write.flush.interval	     | <font color=red>sink.buffer-flush.interval</font> | |
| connector.write.max-retries	         | sink.max-retries                                  | |

### 4.5 Filesystem

| 旧属性 Key      | 新属性 Key | 备注     |
| :------------- | :-------- | :------ |
| connector.type | connector | |
| connector.path | path      | |
| format.type	   | format    | |


### 4.6 Csv Format

| 旧属性 Key                      | 新属性 Key                   | 备注     |
| :----------------------------- | :-------------------------- | :------ |
| format.type	                   | format                      | |
| format.field-delimiter         | csv.field-delimiter         | |
| format.disable-quote-character | csv.disable-quote-character | |
| format.quote-character	       | csv.quote-character         | |
| format.allow-comments	         | csv.allow-comments          | |
| format.ignore-parse-errors	   | csv.ignore-parse-errors     | |
| format.array-element-delimiter | csv.array-element-delimiter | |
| format.escape-character        | csv.escape-character        | |
| format.null-literal	           | csv.null-literal            | |

### 4.7 Json Format

| 旧属性 Key                      | 新属性 Key                   | 备注     |
| :----------------------------- | :-------------------------- | :------ |
| format.type	                   | format                      | |
| format.fail-on-missing-field	 | json.fail-on-missing-field  | |
| format.ignore-parse-errors	   | json.ignore-parse-errors    | |


因为我们为新 Factory 引入了一组新的 Connector 属性 Key。我们建议不要使用旧的 Factory，因为这个版本改动部分比较多，可能会影响用户的稳定性。所以为了兼容性，最终 kafka Connector jar 会包含两个 Factory。如果 Connector 属性使用 'connector' 属性 Key，那么框架会使用新的 Factory 实例；如果使用 'connector.type' 属性 Key，那么框架会使用旧的 Factory 实例。为了未来的发展，我们建议在处理 DDL 时向属性隐式添加 'property-version=1'。


原文:[FLIP-122: New Connector Property Keys for New Factory](https://cwiki.apache.org/confluence/display/FLINK/FLIP-122%3A+New+Connector+Property+Keys+for+New+Factory)
