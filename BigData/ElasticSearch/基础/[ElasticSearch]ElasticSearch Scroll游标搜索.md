---
layout: post
author: sjf0115
title: ElasticSearch Scroll游标搜索
date: 2016-10-28 19:20:17
tags:
  - ElasticSearch
  - ElasticSearch 基础

categories: ElasticSearch
permalink: elasticsearch-base-scroll-search
---

### 1. 深分页

在[ElasticSearch 分页搜索](http://smartsi.club/2016/10/25/elasticsearch-pagination-search/)一文中，我们了解到分布式系统中深度分页。在这里我们再具体的了解一下深度分页，可能带来的问题，以及 ElasticSearch 给出的解决方案。

在 [ElasticSearch 内部原理之分布式文档搜索](http://smartsi.club/2016/10/26/elasticsearch-internal-distributed-document-search/) 一文中我们了解到分布式搜索的工作原理，分布式搜索这种先查后取的过程支持用 `from` 和 `size` 参数分页，但是这是有限制的。请记住，每个分片必须构建一个长度为 `from+size` 的优先级队列，所有这些队列都需要传递回协调节点。协调节点需要对 `number_of_shards *（from + size）` 个文档进行排序，以便正确找到 `size` 个文档。

取决于你的文档的大小，分片的数量和你使用的硬件，给 10,000 到 50,000 的结果文档深分页（ 1,000 到 5,000 页）是完全可行的。但是使用足够大的 `from` 值，排序过程可能会变得非常沉重，使用大量的CPU、内存和带宽。因为这个原因，我们强烈建议你不要使用深分页。

实际上，'深分页'很少符合我们的行为。当2到3页过去以后，我们会停止翻页，并且改变搜索条件。不知疲倦地一页一页的获取网页直到你的服务崩溃的罪魁祸首一般是机器人或者网络爬虫。

如果你确实需要从集群里取回大量的文档，你可以通过使用`scroll`查询（禁用排序）来更有效率的取回文档，具体我们会在下面进行讨论。

### 2. 游标Scroll

`Scroll` 查询用于从 Elasticsearch 中有效地检索大量文档，而又不需付出深度分页那种代价。

`Scroll` 允许我们先进行初始化搜索，然后再不断地从 Elasticsearch 中取回批量结果，直到取回所有结果。这有点像传统数据库中的 `cursor`。

`Scroll` 会搜索在某个时间上生成快照。在搜索初始化完成后，搜索不会看到之后发生在索引上的更改。通过保留旧的数据文件来实现这一点，以便可以保留其在开始搜索时索引的`视图`。

深分页的代价主要花费在结果数据全局排序上，如果我们禁用排序，那么我们可以花费较少的代价就能返回所有的文档。为此，我们按 `_doc` 排序。这样 Elasticsearch 只是从仍然还有结果数据需要返回的每个分片返回下一批结果。

启用游标查询，我们执行一个搜索请求，并将 `scroll` 值设置为游标查询窗口打开的时间长度（即我们期望的游标查询的过期时间）。每次运行游标查询时都会刷新游标查询的过期时间，所以这个时间只需要足够处理当前批的结果就可以了，而不是处理所有与查询匹配的文档。超时设置是非常重要的，因为保持游标查询窗口打开需要消耗资源，我们希望在不再需要时释放它们。设置这个超时能够让 Elasticsearch 在稍后空闲的时候自动释放这部分资源。

```json
GET /old_index/_search?scroll=1m
{
    "query": { "match_all": {}},
    "sort" : ["_doc"],
    "size":  1000
}
```

> 上面语句保持游标查询窗口一分钟。并且根据`_doc`进行排序；

这个查询的返回结果包括一个 `_scroll_id` 字段，它是一个Base-64编码的长字符串。现在我们可以将 `_scroll_id` 传递给 `_search/scroll` 接口来检索下一批结果：
```json
GET /_search/scroll
{
    "scroll": "1m",
    "scroll_id" : "cXVlcnlUaGVuRmV0Y2g7NTsxMDk5NDpkUmpiR2FjOFNhNnlCM1ZDMWpWYnRROzEwOTk1OmRSamJHYWM4U2E2eUIzVkMxalZidFE7MTA5OTM6ZFJqYkdhYzhTYTZ5QjNWQzFqVmJ0UTsxMTE5MDpBVUtwN2lxc1FLZV8yRGVjWlI2QUVBOzEwOTk2OmRSamJHYWM4U2E2eUIzVkMxalZidFE7MDs="
}
```

> 再次设置游标查询过期时间为一分钟。

这个游标查询返回的下一批结果。虽然我们指定了请求大小为 1000，但是我们可能会得到更多的文件。当查询的时候，size 作用于每个分片，所以每个批次实际返回的文档数量最大为 `size * number_of_primary_shards` 。

游标查询每次都返回一个新的 `_scroll_id`。每次我们进行下一个游标查询时，我们必须传递上一个游标查询返回的 `_scroll_id`。

当没有更多的命中返回时，我们已经处理了所有匹配的文档。

### 3. Java中使用游标

```java
import static org.elasticsearch.index.query.QueryBuilders.*;

QueryBuilder qb = termQuery("multi", "test");

SearchResponse scrollResp = client.prepareSearch(test)
  .addSort(FieldSortBuilder.DOC_FIELD_NAME, SortOrder.ASC)
  .setScroll(new TimeValue(60000))
  .setQuery(qb)
  .setSize(100)
  .get();

// 直到没有命中时返回
do {
    for (SearchHit hit : scrollResp.getHits().getHits()) {
        // 处理hit...
    }
    scrollResp = client.prepareSearchScroll(scrollResp.getScrollId()).setScroll(new TimeValue(60000)).execute().actionGet();
} while(scrollResp.getHits().getHits().length != 0);
```

> ElasticSearch版本：2.x

原文：https://www.elastic.co/guide/en/elasticsearch/guide/2.x/scroll.html
