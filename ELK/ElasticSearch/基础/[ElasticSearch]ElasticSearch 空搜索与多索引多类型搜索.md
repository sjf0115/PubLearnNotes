---
layout: post
author: sjf0115
title: ElasticSearch 空搜索与多索引多类型搜索
date: 2016-10-23 16:15:17
tags:
  - ElasticSearch
  - ElasticSearch 基础

categories: ElasticSearch
permalink: elasticsearch-empty-search-and-multi-index-multi-type-search
---

### 1. 空搜索

测试数据:

https://gist.github.com/clintongormley/8579281

#### 1.1 搜索

最基本的搜索API是空搜索(empty search)，它没有指定任何的查询条件，只返回集群索引中的所有文档：

```
curl -XGET 'localhost:9200/_search?pretty'
```
Java版本:
```java
SearchRequestBuilder searchRequestBuilder = client.prepareSearch();
SearchResponse response = searchRequestBuilder.get();
```
返回的结果如下：
```json
{
    "took": 4,
    "timed_out": false,
    "_shards": {
        "total": 10,
        "successful": 10,
        "failed": 0
    },
    "hits": {
        "total": 13,
        "max_score": 1.0,
        "hits": [
            {
                "_index": "gb",
                "_type": "tweet",
                "_id": "5",
                "_score": 1.0,
                "_source": {
                    "date": "2014-09-15",
                    "name": "Mary Jones",
                    "tweet": "However did I manage before Elasticsearch?",
                    "user_id": 2
                }
            },
            {
                "_index": "gb",
                "_type": "tweet",
                "_id": "13",
                "_score": 1.0,
                "_source": {
                    "date": "2014-09-23",
                    "name": "Mary Jones",
                    "tweet": "So yes, I am an Elasticsearch fanboy",
                    "user_id": 2
                }
            }
            // ...
        ]
    }
}
```

#### 1.2 hits

返回结果中最重要的部分是 `hits`，它包含 `total` 字段来表示匹配到的文档总数，并且有一个 `hits` 数组包含所查询结果的前十个文档。

在 `hits` 数组中每个结果包含文档的 `_index` 、 `_type` 、 `_id` 以及 `_source` 字段。这意味着我们可以直接从返回的搜索结果中获取整个文档。这不像其他的搜索引擎，仅仅返回文档的ID，需要你自己单独去获取文档。

每个结果还有一个 `_score` 字段，这是一个相关性得分，它衡量了文档与查询文本的匹配程度。默认情况下，首先返回相关性最高的文档，就是说，返回文档是按照 `_score` 降序排列的。在这个例子中，我们没有指定任何查询，故所有的文档具有相同的相关性，因此对所有的结果都是中性的 `_score` 为1。

`max_score` 是文档与查询文本匹配度最高的 `_score`。

#### 1.3 Took

`took` 告诉我们整个搜索请求执行多少毫秒数。

#### 1.4 Shards

`_shards` 告诉我们参与查询的分片总数（total），有多少是成功的（successful），有多少的是失败的（failed）。

通常我们不希望分片失败，但是还是有可能发生。如果我们遭受一些重大故障，导致同一分片的主分片和副本分片都丢失，那么这个分片就不会响应搜索请求。这种情况下，Elasticsearch 将报告这个分片failed，但仍将继续返回剩余分片上的结果。

#### 1.5 Timeout

`time_out` 值告诉我们查询是否超时。默认情况下，搜索请求不会超时。如果低响应时间比完整结果更重要，你可以将超时指定为 `10` 或 `10ms`（10毫秒）或 `1s`（1秒）：
```
curl -XGET 'localhost:9200/_search?timeout=10ms'
```
在请求超时之前，ElasticSearch 将返回从每个分片收集到的任何结果。

> 应当注意的是 timeout 不是停止执行查询，仅仅是告知协调节点返回到目前为止收集到的结果并关闭连接。在后台，其他的分片可能仍在执行查询，即使结果已经发送了。

使用超时是因为对你的 SLA(服务等级协议)来说很重要的，而不是因为想去中止长时间运行的查询。

### 2. 多索引和多类型搜索

如果不对我们的搜索做出特定索引或者特定类型的限制，就会搜索集群中的所有文档。Elasticsearch 将搜索请求并行转发到每一个主分片或者副本分片上，收集结果以选择全部中的前10名，并且返回给我们。

但是，通常，我们希望在一个或多个特定索引中搜索，也可能需要在一个或多个特定类型上搜索。我们可以通过在 URL 中指定索引和类型来执行此操作，如下所示：

搜索|描述
---|---
`/_search`|在所有的索引中对所有类型进行搜索
`/gb/_search`|在gb索引中对所有类型进行搜索
`/gb,us/_search`|在gb和us索引中对所有类型进行搜索
`/g*,u*/_search`|在以g或者u开头的索引中对所有类型进行搜索
`/gb/user/_search`|在gb索引中对`user`类型进行搜索
`/gb,us/user,tweet/_search`|在gb和us索引中对user和tweet类型进行搜索
`/_all/user,tweet/_search`|在所有的索引中对user和tweet类型进行搜索

Java版本:
```java
SearchRequestBuilder searchRequestBuilder = client.prepareSearch();
searchRequestBuilder.setIndices("*index");
SearchResponse response = searchRequestBuilder.get();
```
从下面源码中，我们可以知道，设置索引和类型的方法参数是可变参数，因此我们可以设置多个索引或者类型。
```java
public SearchRequestBuilder setIndices(String... indices) {
    request.indices(indices);
    return this;
}
public SearchRequestBuilder setTypes(String... types) {
    request.types(types);
    return this;
}
```

当在单个索引中搜索时，Elasticsearch 将搜索请求转发到该索引中每个分片的主分片或副本分片上，然后从每个分片收集结果。在多个索引中搜索的方式完全相同 - 只是会涉及更多的分片。

> 搜索一个具有五个主分片的索引完全等同于搜索每个具有一个主分片的五个索引。


原文：https://www.elastic.co/guide/en/elasticsearch/guide/2.x/empty-search.html

https://www.elastic.co/guide/en/elasticsearch/guide/2.x/multi-index-multi-type.html
