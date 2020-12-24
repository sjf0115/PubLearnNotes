---
layout: post
author: sjf0115
title: ElasticSearch 分页搜索
date: 2016-10-25 12:45:17
tags:
  - ElasticSearch
  - ElasticSearch 基础

categories: ElasticSearch
permalink: elasticsearch-pagination-search
---

### 1. 分页

之前的文章[ElasticSearch 空搜索与多索引多类型搜索](http://smartsi.club/2016/10/23/elasticsearch-empty-search-and-multi-index-multi-type-search/)我们知道，我们的空搜索匹配到集群中的13个文档。 但是，命中数组中只有10个文档（文章只显示了2条数据，故意省略掉）。 我们如何查看其他文档呢？

与SQL使用`LIMIT`关键字返回一个'页面'的结果数据相同，Elasticsearch 接受 from 和 size 参数：
- size　表示应返回的结果数，默认为10
- from　表示应跳过的初始结果数，默认为0

如果想每页显示五个条数据，那么第1到3页的结果请求如下所示：
```
curl -XGET 'localhost:9200/_search?size=5&pretty'
curl -XGET 'localhost:9200/_search?size=5&from=5&pretty'
curl -XGET 'localhost:9200/_search?size=5&from=10&pretty'
```
Java版本:
```java
SearchRequestBuilder searchRequestBuilder = client.prepareSearch();
searchRequestBuilder.setIndices(index);
searchRequestBuilder.setTypes(type);
searchRequestBuilder.setFrom(from);
searchRequestBuilder.setSize(size);
SearchResponse response = searchRequestBuilder.get();
```

要避免分页太深或者一次请求太多的结果。结果在返回前要进行排序。请记住，搜索请求通常跨越多个分片。每个分片都会生成自己的排序结果，然后在协调节点集中排序，以确保整体顺序正确。

### 2. 深度分页

为了理解深度分页为什么是有问题的，我们假设在一个有5个主分片的索引中搜索。当我们请求结果的第一页（结果从1到10），每个分片产生自己的前10个结果，并且返回给协调节点 ，协调节点对所有50个结果进行排序，最终返回全部结果的前10个。

现在假设我们请求第1000页的数据--结果从10001到10010。除了每个分片不得不产生前10010个数据以外，其他的都跟上面查询第一页一样。协调节点对全部5个分片的50050个数据进行排序，最后丢弃掉这其中的50040个(只要10个)。

你可以看到，在分布式系统中，排序结果的成本以指数级增长。好消息是，网页搜索引擎一般不会为任何查询返回超过1,000个结果。

> Elasticsearch版本:2.x

原文：https://www.elastic.co/guide/en/elasticsearch/guide/2.x/pagination.html
