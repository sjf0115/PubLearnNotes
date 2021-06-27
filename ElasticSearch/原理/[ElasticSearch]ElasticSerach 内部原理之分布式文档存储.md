---
layout: post
author: sjf0115
title: ElasticSearch 内部原理之分布式文档存储
date: 2016-10-25 20:15:17
tags:
  - ElasticSearch
  - ElasticSearch 内部原理

categories: ElasticSearch
permalink: elasticsearch-internal-distributed-document-store
---

之前的文章中，我们已经知道如何存储数据到索引中以及如何检索它。但是我们掩盖了数据存储到集群中以及从集群中获取数据的具体实现的技术细节。

### 1. 路由文档到分片中

当你索引一篇文档时，它会存储到一个主分片中。但是 ElasticSearch 如何知道文档是属于哪个分片呢？当我们创建一个新的文档，它是怎么知道它是应该存储到分片1上还是分片2上？

数据存储到分片的过程是有一定规则的，并不是随机发生的，因为我们日后还需要从分片中检索出文档。数据存储过程取决于下面的公式：
```
shard = hash(routing) % number_of_primary_shards
```
Routing 值是一个任意字符串，默认为 `文档的id`，也可以设置为一个用户自定义的值。Routing 这个字符串通过一个 hash 函数处理，并返回一个数值，然后再除以索引中主分片的数目 number_of_primary_shards，所得的余数作为主分片的编号，取值一般在 0 到 number_of_primary_shards - 1 之间的余数范围中。通过这种方法计算出该数据是存储到哪个分片中。

这就解释了为什么主分片个数在创建索引之后就不能再更改了：如果主分片个数在创建之后可以修改，那么之前所有通过公式得到的值都会失效，之前存储的文档也可能找不到。

> 有的人可能认为，拥有固定数量的主分片会使以后很难对索引进行扩展。实际上，有一些技术可以让你在需要的时候很轻松的扩展。可以参阅[
Designing for Scale](https://www.elastic.co/guide/en/elasticsearch/guide/2.x/scale.html)。

所有的文档API（get , index , delete , bulk , update , 和 mget）都可以接受一个 routing 参数，来自定义文档与分片之间的映射。一个自定义的路由参数可以用来确保所有相关的文档，例如所有属于同一个用户的文档都被存储到同一个分片中。我们会在[
Designing for Scale](https://www.elastic.co/guide/en/elasticsearch/guide/2.x/scale.html)中详细讨论为什么要这样做。

### 2. 主分片与副本分片如何交互

假设我们有一个三个节点的集群。集群里有一个名称为 blog 的索引，有两个主分片（primary shards）。每个主分片都有两个副本。相同节点的副本不会分配到同一节点，最后如下图展示：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ElasticSearch/elasticsearch-internal-distributed-document-store-1.png?raw=true)

我们可以发送请求到集群中的任何一个节点，每个节点都有能力处理我们的请求。每个节点都知道集群中每个文档的存储位置，所以可以直接将请求转发到对应的节点上。

在下面的例子中，我们将请求都发送到节点 1 上，我们将其称为协调节点(coordinating node)。

#### 2.1 创建，索引和删除文档

创建，索引和删除请求都是写操作，所以必须在主分片上写操作完成之后才能被复制到相关的副本分片上。

交互过程如下图所示：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ElasticSearch/elasticsearch-internal-distributed-document-store-2.png?raw=true)

下面是成功在主分片和副本分片上创建，索引以及删除文档所必须的步骤：
- 客户端发送了一个新建，索引 或者删除文档请求给节点 1；
- 节点 1 通过请求文档的 id 值判断出该文档应该被存储在分片 0 中，并且知道分片 0  的主分片 P0 位于节点 3 上。因此节点 1 会把这个请求转发给节点 3；
- 节点 3 在主分片上执行请求。如果请求执行成功，节点 3 并行将该请求转发给节点 1 和节点 2 上的的副本分片（R0）。一旦所有的副本分片都成功地执行了请求，则向节点 3 报告成功，节点 3 向协调节点 （Node 1 ）报告成功，协调节点向客户端报告成功。

在客户端收到成功响应时，文档变更已经在主分片和所有副本分片执行完成，变更是安全的。

有一些可选的请求参数允许您影响这个过程，可能以数据安全为代价提升性能。这些选项很少使用，因为Elasticsearch已经很快，但是为了完整起见，在这里阐述如下:

##### 2.1.1 一致性

默认情况下，在尝试进行写操作之前，主分片需要规定数量(quorum)或大多数(majority)的分片拷贝 `shard copies` （其中分片副本可以是主分片或副本分片）。这是为了防止将数据写入网络分区的“错误的一边`wrong side`”。 规定数量`quorum`定义如下：
```
int( (primary + number_of_replicas) / 2 ) + 1
```
一致性`consistency`值可以是`one`（只有主分片），`all`（主分片和所有的副本），或者默认值`quorum`，或者大多数的分片副本（The allowed values for consistency are one (just the primary shard), all (the primary and all replicas), or the default quorum, or majority, of shard copies.）。

请注意，`number_of_replicas`是索引设置中指定的副本数，而不是当前活跃的副本数。 如果指定索引有三个副本，则`quorum`将如下定义：
```
int( (primary + 3 replicas) / 2 ) + 1 = 3
```
但是，如果仅启动两个节点，则活跃的分片副本不满足规定数量，您将无法对任何文档进行索引或删除。

##### 2.1.2 超时

如果没有足够的副本分片会发生什么？ Elasticsearch会等待，希望更多的分片出现。默认情况下，它最多等待1分钟。 如果你需要，你可以使用 timeout 参数 使它更早终止： 100 100毫秒，30s 是30秒。

> 新索引默认有 1 个副本分片，这意味着为满足 规定数量 应该 需要两个活动的分片副本。 但是，这些默认的设置会阻止我们在单一节点上做任何事情。为了避免这个问题，要求只有当 number_of_replicas 大于1的时候，规定数量才会执行。


#### 2.2 检索文档

我们可以从一个主分片（primary shard）或者它们任一副本中检索文档，流程如下图：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ElasticSearch/elasticsearch-internal-distributed-document-store-3.png?raw=true)


下面是从主分片或者副本分片上检索文档所需要的一系列步骤：
- 客户端发送了一个 Get 请求给节点 1；
- 节点 1 通过请求文档的 id 值判断出该文档被存储在分片 0 中。三个节点上都存有分片 0 的复制（节点1上R0，节点2上R0，节点3上P0）。这一次，它将请求转发给节点 2 。
- 节点 2 返回文档给节点 1 ，节点 1 在返回文档给客户端。


对于读请求，对于每一次请求，请求节点都会选择一个不同的副本分本，达到负载均衡。通过轮询所有的副本分片。

在文档被检索时，已经被索引的文档可能已经存在于主分片上但是还没有复制到副本分片。 在这种情况下，副本分片可能会报告文档不存在，但是主分片可能成功返回文档。 一旦索引请求成功返回给用户，文档在主分片和副本分片都是可用的。

#### 2.3 局部更新文档

更新 API （Update API）融合了上面解释的两种读写模式，如下图所示：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ElasticSearch/elasticsearch-internal-distributed-document-store-4.png?raw=true)


下面是部分更新一篇文档所需要的一系列步骤：
- 客户端发送了一个 Update 请求给节点 1；
- 节点1通过请求文档的 id 值判断出该文档被存储在分片0中。并且知道分片0的主分片P0位于节点3上。因此节点1会把这个请求转发给节点 3；
- 节点3从主分片（P0）上检索出指定文档，并更改 `_source` 字段中的JSON，修改完毕之后试着重新索引文档到主分片（P0）上。如果有人已经修改了该文档，那么会重复步骤3，如果尝试 `retry_on_conflict` 次还没有成功则放弃。
- 如果节点3更新文档成功，节点3会把文档新版本并行发给节点1和节点2上的副本分片，重新索引文档。一旦所有的副本分片返回成功，节点3向协调节点返回成功，协调节点向客户端返回成功。


> 基于文档的复制：当主分片把更改转发到副本分片时， 它不会转发更新请求。 相反，它转发完整文档的新版本。请记住，这些更改将会异步转发到副本分片，并且不能保证它们以发送它们相同的顺序到达。 如果Elasticsearch仅转发更改请求，则可能以错误的顺序应用更改，导致得到损坏的文档。

#### 2.4 多文档模式

mget 和 bulk API的模式类似于单文档模式。 不同的是，协调节点知道每个文档存储在哪个分片中。 它将多文档请求分解成对每个分片的多文档请求，并将请求并行转发到每个参与节点。

一旦从每个节点接收到应答，将每个节点的响应整合到单个响应中，并返回给客户端

##### 2.4.1 mget

如下图所示：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ElasticSearch/elasticsearch-internal-distributed-document-store-5.png?raw=true)

以下是使用单个 mget 请求取回多个文档所需的步骤顺序：

- 客户端向节点 1 发送 mget 请求。
- 节点 1 为每个分片构建多文档获取请求，然后并行转发这些请求到托管在每个所需的主分片或者副本分片的节点上。一旦收到所有应答， 节点 1 构建响应并将其返回给客户端。

##### 2.4.2 bulk

bulk API，允许在单个批量请求中执行多个创建、索引、删除和更新请求，如下图所示：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ElasticSearch/elasticsearch-internal-distributed-document-store-6.png?raw=true)

bulk API 按如下步骤顺序执行：
- 客户端向 节点 1 发送 bulk 请求。
- 节点 1 为每个节点创建一个批量请求，并将这些请求并行转发到每个包含主分片的节点主机。
- 主分片一个接一个按顺序执行每个操作。当每个操作成功时，主分片并行转发新文档（或删除）到副本分片，然后执行下一个操作。 一旦所有的副本分片报告所有操作成功，该节点将向协调节点报告成功，协调节点将这些响应收集整理并返回给客户端。

bulk API 还可以在整个批量请求的最顶层使用 consistency 参数，以及在每个请求中的元数据中使用 routing 参数。


> ElasticSearch版本: 2.x

原文： https://www.elastic.co/guide/en/elasticsearch/guide/2.x/distributed-docs.html
