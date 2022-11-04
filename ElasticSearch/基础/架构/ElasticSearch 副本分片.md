---
layout: post
author: sjf0115
title: ElasticSearch 副本分片
date: 2016-11-02 16:45:17
tags:
  - ElasticSearch
  - ElasticSearch 基础

categories: ElasticSearch
permalink: elasticsearch-base-replica-shard
---

> ElasticSearch版本：2.x

### 1. 副本分片

到目前为止，我们只讨论了主分片，但是我们还有另一个工具：副本分片。副本分片的主要目的是为了故障转移（failover），如[深入集群生命周期](https://www.elastic.co/guide/en/elasticsearch/guide/2.x/distributed-cluster.html)所述：如果持有主分片的节点挂掉了，则一个副本分片会提升为主分片的角色。

在索引写入时，副本分片做着与主分片相同的工作。新文档首先被索引进主分片然后再同步到其它所有的副本分片。增加副本数并不会增加索引容量。

但是，副本分片可以为读取请求提供帮助。如果通常情况下，你的索引搜索占很大比重（偏向于查询使用），则可以通过增加副本数量来增加搜索性能，但这样你也会为此付出占用额外的硬件资源的代价。

让我们回到那个具有两个主分片的索引示例中。我们通过添加第二个节点来增加索引的容量。添加更多节点不会帮助我们提升索引写入能力，但是我们可以在搜索时通过增加副本分片的的个数来充分利用额外硬件资源：
```json
PUT /my_index/_settings
{
  "number_of_replicas": 1
}
```

拥有两个主分片，另外加上每个主分片的一个副本，我们总共拥有四个分片：每个节点一个，如下图所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/ElasticSearch/elasticsearch-base-replica-shard-1.png?raw=true)

### 2. 通过副本进行负载均衡

搜索性能取决于最慢节点的响应时间，所以尝试均衡所有节点的负载是一个好想法。如果我们只是增加一个节点，最终我们会有三个节点，其中两个节点只拥有一个分片，另一个节点有两个分片做着两倍的工作。

我们可以通过调整分片副本数量来平衡这些。通过分配两个副本，最终我们会拥有六个分片，刚好可以平均分给三个节点
```json
PUT /my_index/_settings
{
  "number_of_replicas": 2
}
```
作为奖励，我们同时提升了我们的可用性。我们可以容忍丢失两个节点而仍然保持一份完整数据的拷贝。

如下图所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/ElasticSearch/elasticsearch-base-replica-shard-2.png?raw=true)

事实上节点 3 拥有两个副本分片，没有主分片并不重要。副本分片与主分片做着相同的工作。它们只是扮演着略微不同的角色。没有必要确保主分片均匀地分布在所有节点中。

原文：[Replica Shards](https://www.elastic.co/guide/cn/elasticsearch/guide/2.x/replica-shards.html)
