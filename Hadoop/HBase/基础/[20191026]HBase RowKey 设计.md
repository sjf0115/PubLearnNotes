---
layout: post
author: sjf0115
title: HBase RowKey 设计
date: 2019-11-03 15:04:07
tags:
  - HBase

categories: HBase
permalink: introduction-to-hbase-rowkey-design
---

### 1. RowKey作用

#### 1.1 RowKey对查询的影响

HBase中 RowKey 用来唯一标识一行记录。在 HBase 中检索数据有以下三种方式：
- 通过 get 方式，指定 RowKey 获取唯一一条记录。
- 通过 scan 方式，设置 startRow 和 endRow 参数进行范围匹配。
- 全表扫描，即直接扫描整张表中所有行记录。

如果我们 RowKey 设计为 uid+event_type+biz_type，那么这种设计可以很好的支持如下场景:
```sql
uid=10457 AND event_type=click AND biz_type=search
uid=10457 AND event_type=click
uid=10457
uid=10?
```
很难以支持如下场景：
```sql
uid=10457 AND biz_type=search
event_type=click AND biz_type=search
event_type=click
biz_type=search
```

从上面的例子中可以看出，在进行查询的时候，根据 RowKey 从前向后匹配，所以我们在设计 RowKey 的时候选择好字段之后，还应该结合我们的实际的高频的查询场景来组合选择的字段，越高频的查询字段排列越靠左。

#### 1.2 RowKey对Region划分影响

HBase 表的数据是按照 RowKey 来分散到不同 Region，不合理的 RowKey 设计会导致热点问题。热点问题是大量的 Client 直接访问集群的一个或极少数个节点，而集群中的其他节点却处于相对空闲状态。

在 HBase 中，Region 相当于一个数据的分片，每个 Region 都有 StartRowKey 和 EndRowKey，这表示 Region 存储的 RowKey 的范围，HBase 表的数据时按照 RowKey 来分散到不同的 Region 中。不合理的 RowKey 设计会导致热点问题。

> 热点问题是大量的 Client 直接访问集群的一个或极少数个节点，而集群中的其他节点却处于相对空闲状态。

### 2. RowKey设计原则

- 唯一原则：RowKey对应关系型数据库的唯一键，必须保证 RowKey 的唯一性。若向 HBase 同一张表插入相同 RowKey 的数据，则原先存在的数据会被新的数据覆盖。
- 散列原则：设计的 RowKey 应均匀的分布在各个 Region 上。避免递增，否则读写负载都会集中在某个热点 Region，降低性能，甚至引起 RegionServer 过载。
- 长度原则：长度适中，一般从几十字节到几百字节，建议使用定义 RowKey。

### 3. RowKey设计技巧

#### 3.1 热点问题

HBase 中的行是以 RowKey 的字典序排序的，这种设计优化了 Scan 操作，可以将相关的行以及会被一起读取的行存储在临近位置。 但是，糟糕的 RowKey 设计是引起热点的常见原因。热点发生在大量的客户端流量直接访问集群的一个或极少数节点。客户端流量可以是读，写，或者其他操作。大量流量会使负责该 Region 的单台机器不堪重负，引起性能下降甚至是 Region 不可用。这也会对同一个 RegionServer 的其他 Region 产生不利影响，因为主机无法满足请求的负载。设计良好的数据访问模式可以充分，均衡的利用集群。

为了避免写入时出现热点，设计 RowKey 时尽量避免不同行在同一个 Region，但从更大的角度看，数据应该被写入集群中的多个 Region，而不是一次写入一个 Region。下面介绍一些避免热点的常用技术，以及它们的一些优点和缺点。

##### 3.1.1 加盐

这里的加盐不是密码学中的加盐，而是指给 RowKey 添加随机前缀，以使得它和之前排序不同。分配的前缀个数应该和你想使数据分散到的 Region 个数一致。如果你有一些热点 RowKey 反复出现在其他分布均匀的 RowKey 中，加盐是很有用的。
但其弊端也显而易见，会增加读取的成本。现在读操作需要把扫描命令分散到所有 Region 上来查找相应的行，因为它们不再存储在一起。如果需要使用 GET 请求再次获取行数据，我们需要知道添加的随机前缀是什么，所以需要我们在插入时保存原始 RowKey 与随机前缀的映射关系。

下面的例子表明加盐可以将写入负载分散到多个 RegionServer 上，同时也表明了对读取的负面影响。假设我们有如下 RowKey，表中的每一个 Region 对应字母表中的一个字母。前缀 `a` 的 RowKey 对应一个 Region，前缀 `b` 的 RowKey 对应另一个 Region。在表中，所有以 `f` 开头的 RowKey 都在同一个 Region，如下所示：
```
foo0001
foo0002
foo0003
foo0004
```
现在，假设我们想将上面这些 RowKey 分配到 4 个不同的 Region。我们可以用 4 种不同的盐：`a`、`b`、`c`、`d`。在这个情况下，每一个字母前缀都对应不同的 Region。加盐之后，RowKey 变成如下所示：
```
a-foo0003
b-foo0001
c-foo0004
d-foo0002
```
由于我们现在可以写入四个不同的 Region，因此理论上我们现在的写入吞吐量是之前写入相同 Region 时的四倍。现在，我们再增加一行，会随机分配 `a`、`b`、`c`、`d` 中的一个作为前缀，并以一个现有行作为尾部结束：
```
a-foo0003
b-foo0001
c-foo0003
c-foo0004
d-foo0002
```
由于分配是随机的，因此如果我们想要以字典序取回数据，我们需要做更多的工作。加盐增加了写入吞吐量，但会增加读取的成本。

##### 3.1.2 哈希

除了加盐，你也可以使用哈希。哈希会使同一行始终有相同的前缀加盐，使用确定性哈希可以使客户端重新构造完整的 RowKey，并使用 Get 操作正常检索该行。哈希的原理是计算 RowKey 的哈希值，然后取哈希值的部分字符串和原来的 RowKey 进行拼接或者完全替代。这里说的哈希包含 MD5、sha1、sha256或sha512等算法。

对于上面的例子，我们可以使用哈希来代替加盐，这样会使得 RowKey 始终有可预测前缀(对于每一个 RowKey 都有确定性的前缀)。通过哈希我们可以知道前缀进而检索该行数据。我们还可以做一些优化，例如使某些键始终位于同一 Region。比如我们有如下的 RowKey：
```
foo0001
foo0002
foo0003
foo0004
```
我们使用 md5 算法计算这些 RowKey 的哈希值，然后取前 6 位和原来的 RowKey 拼接得到新的 RowKey：
```
95f18c-foo0001
6ccc20-foo0002
b61d00-foo0003
1a7475-foo0004
```

##### 3.1.3 翻转RowKey

如果初步设计出的 RowKey 在数据分布上不均匀，但 RowKey 尾部的数据却呈现出了良好的随机性，此时可以考虑将 RowKey 翻转，或者直接将尾部部分放到 RowKey 的前面，这样就可以把最频繁发生变化的部分放在前面。翻转可以有效的使 RowKey 随机分布，但是牺牲了 RowKey 的有序性特性。

翻转是避免热点问题的常用的方法，用户Id一般是关系型数据库的自增主键，通常会将用户Id翻转后在末尾加0补齐。类似的，如果我们使用时间戳作为 RowKey 的一部分，可以使用 `Long.MAX_VALUE - 时间戳` 进行替换。

#### 3.2 单调递增问题

在汤姆·怀特（Tom White）的《 Hadoop：权威指南》的 HBase 一章中，有一个优化注意事项：所有客户端一段时间内一致写入某一个 Region，然后再接着一起写入下一个 Region，依此类推。使用单调递增的 RowKey（例如，使用时间戳），就会发生这种情况。可以参阅 IKai Lan 的漫画 [monotonically increasing values are bad](http://ikaisays.com/2011/01/25/app-engine-datastore-tip-monotonically-increasing-values-are-bad/)，该漫画解释了为什么在像 BigTable 这样的数据存储中使用单调递增的 RowKey 会出现问题。可以通过将输入记录随机化来缓解单调递增键在单个 Region 上堆积所带来的压力，最好避免使用时间戳或序列（例如1、2、3）作为 RowKey。

如果确实需要将时间序列数据上传到 HBase，可以学习 [OpenTSDB](http://smartsi.club/how-hbase-RowKey-is-designed-of-opentsdb.html) 是怎么做的。具体细节可以参阅 [scheme](http://opentsdb.net/docs/build/html/user_guide/backends/hbase.html)。OpenTSDB 中的 RowKey 格式为 `[metric_type] [event_timestamp]`，乍一看这似乎违反了不使用时间戳作为 RowKey 的原则。但是，不同之处在于时间戳不在 RowKey 的关键位置，而这个设计假设存在数十个或数百个（或更多）不同的度量标准类型。

#### 3.3 尽量减小行和列的大小

在 HBase 中，RowKey、列名、时间戳总是跟值一起发送。如果 RowKey 和列名比较大，尤其是与单元格值大小相比差异不大时，可能会遇到一些问题。Marc Limotte 在 [HBASE-3551](https://issues.apache.org/jira/browse/HBASE-3551?page=com.atlassian.jira.plugin.system.issuetabpanels:comment-tabpanel&focusedCommentId=13005272#comment-13005272) 描述了这种情况（推荐看一下！）。

##### 3.3.1 列族

尽量使列族名尽可能的短，最好是一个字符（例如，`d` 表示数据/默认值）。

##### 3.3.2 属性

虽然详细的属性名称（例如，`myVeryImportantAttribute`）有更好的可读性，但是最好在 HBase 中存储较短的属性名称（例如 `via`）。

##### 3.3.3 RowKey长度

RowKey 尽可能的短，但仍可用于必需的数据访问（例如，Get 与 Scan）。如果 RowKey 短的对于数据访问没有用处，那么还不如使用一个长的 RowKey。设计 RowKey 时需要权衡取舍。

##### 3.3.4 字节模式

长整型8个字节，我们可以使用这八个字节存储一个最大为18,446,744,073,709,551,615的无符号整数。如果将此数字存储为字符串（假定每个字符一个字节），则需要将近3倍的字节：
```java
// long
//
long l = 1234567890L;
byte[] lb = Bytes.toBytes(l);
System.out.println("long bytes length: " + lb.length);   // returns 8

String s = String.valueOf(l);
byte[] sb = Bytes.toBytes(s);
System.out.println("long as string length: " + sb.length);    // returns 10

// hash
//
MessageDigest md = MessageDigest.getInstance("MD5");
byte[] digest = md.digest(Bytes.toBytes(s));
System.out.println("md5 digest bytes length: " + digest.length);    // returns 16

String sDigest = new String(digest);
byte[] sbDigest = Bytes.toBytes(sDigest);
System.out.println("md5 digest as string length: " + sbDigest.length);    // returns 26
```
不幸的是，用二进制类型会使你的数据在代码之外很难以阅读。例如，下面是我们在shell 中增加一个值后看到的：
```shell
hbase(main):001:0> incr 't', 'r', 'f:q', 1
COUNTER VALUE = 1

hbase(main):002:0> get 't', 'r'
COLUMN                                        CELL
 f:q                                          timestamp=1369163040570, value=\x00\x00\x00\x00\x00\x00\x00\x01
1 row(s) in 0.0310 seconds
```
Shell 会尽力打印字符串，但是这种情况下，它只能打印16进制。这也会在你的 RowKey 中发生。如果你知道存的是什么那当然没什么，但是如果任意数据存放在具体的值中，那将难以阅读。这也需要权衡。

### 4. RowKey Example

假设我们正在收集以下数据元素：
- 主机名(Hostname)
- 时间戳(Timestamp)
- 日志事件(Log event)
- 值(Value)

我们可以将它们存储在名为 LOG_DATA 的 HBase 表中，但是 RowKey 是什么呢？从这些属性中看，RowKey 将是主机名、时间戳以及日志事件的某种组合，但是具体是什么？

#### 4.1 时间戳在RowKey的主要位置

RowKey `[timestamp][hostname][log-event]` 这种设计出现了我们上面说的 RowKey 单调递增问题。

有一个经常提到的'分桶'时间戳方法，通过对时间戳取模来实现。如果面向时间的 Scan 很重要，那么这可能是一种有用的方法。必须注意分桶的数量，因为这需要相同数量的 Scan 才能返回结果。
```java
long bucket = timestamp % numBuckets;
```
现在 RowKey 设计如下：
```
[bucket][timestamp][hostname][log-event]
```
如上所述，要选择特定时间范围的数据，需要在每个分桶上执行一次 Scan。例如，100个分桶，我们需要执行100次 Scan 才能获取特定时间戳的数据，因此需要做一些权衡取舍。

#### 4.2 主机名在RowKey的主要位置

如果需要读写大量主机名，那么 RowKey `[hostname][log-event][timestamp]` 是一个不错的备选方案。

#### 4.3 时间戳还是反向时间戳？

如果我们经常访问最新事件，那么将时间戳存储为反向时间戳（例如，`Long.MAX_VALUE – timestamp`），我们就能通过对 `[hostname][log-event]` 进行 Scan 操作获取最新的事件。

时间戳还是反向时间戳都没有错，具体取决于我们的需求。

#### 4.4 可变长度还是固定长度的RowKey？

我们都知道 RowKey 存储在 HBase 的每一列上。如果主机名是 `a` 并且事件类型是 `e1`，那么 RowKey 会非常小。但是，如果主机名是 `myserver1.mycompany.com`，事件类型是 `com.package1.subpackage2.subsubpackage3.ImportantService`，那怎么办？

在 RowKey 中使用某些替换是一个不错的方法。我们至少有两种方法：哈希和数字。上面主机名在 RowKey 的主要位置的示例如下所示。

(1) 哈希

使用哈希的复合 RowKey：
- [MD5 hash of hostname] = 16 bytes
- [MD5 hash of event-type] = 16 bytes
- [timestamp] = 8 bytes

(2) 使用数字的复合 RowKey：
对于这种方法，除了LOG_DATA外，还需要另一个查询表，称为LOG_TYPES。 LOG_TYPES的行键为：
- [type] 表明是主机名还是日志事件
- [bytes] 主机名或事件类型的原始字节

此 RowKey 的列可以是带有指定数字的长整数，可以通过使用 HBase 计数器获得该数字，因此生成的复合 RowKey 为：
- [hostname 对应的长整形] = 8 bytes
- [event-type 对应的长整形] = 8 bytes
- [timestamp] = 8 bytes

无论是哈希还是数字替换方法，主机名和事件类型的原始值可以存储为列值中。


欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

参考：[RowKey Design](https://hbase.apache.org/book.html#RowKey.design)
