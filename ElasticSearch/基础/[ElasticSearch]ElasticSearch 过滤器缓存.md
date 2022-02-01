---
layout: post
author: sjf0115
title: ElasticSearch 过滤器缓存
date: 2016-10-28 19:15:17
tags:
  - ElasticSearch
  - ElasticSearch 基础

categories: ElasticSearch
permalink: elasticsearch-base-filter-caching
---

过滤器(Filter)的核心实际是采用一个`bitset`记录与过滤器匹配的文档。当Elasticsearch确定一个bitset可能会在将来被重用时，它将被直接缓存在内存中供以后使用。一旦缓存，这些`bitset`可以在使用相同查询的任何地方重复使用，而无需再次重新评估整个查询。

这些缓存的bitset是非常'机智'的：它们是增量更新的。当你在索引新文档时，只需要将那些新文档添加到现有的`bitset`中，而不是对整个缓存一遍又一遍的重复计算。过滤器与系统的其余部分一样都是实时的，不需要担心缓存过期问题。

### 1. 独立的查询缓存

属于一个查询组件的`bitsets`独立于搜索请求的其他部分。这意味着，一旦缓存，可以在多个搜索请求中重复使用查询。 它不依赖于它所存在的查询上下文。 这样使得缓存可以加速查询中经常使用的部分，而不会在较少或易变部分浪费开销。

类似地，如果单个搜索请求重复使用相同的非评分查询，则其缓存的`bitset`可以重用于单个搜索请求内的所有实例。

我们来看看下面这个示例查询，它查找以下任何一个电子邮件：
- 在收件箱中，且没有被读过的
- 不在 收件箱中，但被标注重要的

```json
GET /inbox/emails/_search
{
  "query": {
      "constant_score": {
          "filter": {
              "bool": {
                 "should": [
                    { "bool": {
                          "must": [
                             { "term": { "folder": "inbox" }},
                             { "term": { "read": false }}
                          ]
                    }},
                    { "bool": {
                          "must_not": {
                             "term": { "folder": "inbox" }
                          },
                          "must": {
                             "term": { "important": true }
                          }
                    }}
                 ]
              }
            }
        }
    }
}
```
使用SQL语句描述：
```
SELECT emails
FROM inbox
WHERE (folder='inbox' and read = false) or (folder != 'inbox' and important = true)
```

上面两个查询是相同的，并且将使用相同的`bitset`。

尽管一个inbox子句是一个must子句，另一个是一个must_not子句，但是这两个子句本质上是一样的。如果这个特定`term`查询先前已被缓存过，那么尽管这两个子句使用不同样式的布尔逻辑，也都将受益于缓存表示(If this particular term query was previously cached, both instances would benefit from the cached representation despite being used in different styles of boolean logic)。

这点与查询表达式的组合性很好的相关联。 可以轻松地移动过滤查询，或在搜索请求中的多个位置重复使用相同的查询。 这对开发人员来说不仅方便，而且具有直接的性能优势。

### 2. 自动缓存(Autocaching Behavior)

在旧版本的Elasticsearch中，默认行为是缓存可缓存的所有内容。 这通常意味着系统缓存的`bitset`太冒进，在清理缓存时会给性能带来冲击。 此外，许多过滤器可以非常快速地进行评估，但是缓存（从缓存重用）的速度要慢的多。 这些过滤器没有必要进行缓存，因为再次重新执行过滤器都比从缓存重用快。

检查一个倒排索引是非常快的，但是绝大多数查询组件却很少使用它(Inspecting the inverted index is very fast and most query components are rare.)。例如 在 "user_id"字段上的`term` 过滤 ：如果有上百万的用户，每个具体的用户 ID 出现的概率都很小。那么为这个过滤器缓存`bitsets` 就不是很合算，因为缓存的结果在重用之前很可能就被剔除了。

这种缓存流失(cache churn )可能会对性能造成严重影响。 更糟糕的是，开发人员很难确定哪些组件具有良好的缓存行为，哪些组件的缓存行为没有用处。

为了解决这个问题，Elasticsearch会根据使用频率自动缓存查询。 如果一个非评分查询在最近的256次查询中使用了多次（取决于查询类型），则该查询是被候选缓存。但是，并不是所有段都保证缓存`bitset`。 只有拥有超过10,000个文档的分段（或占文档总数的3％以上）将缓存`bitset`。 因为小段可以快速的搜索和合并，所以在这种情况下缓存`bitset`是没有意义的。

一旦缓存，非评分计算的`bitset`会一直驻留在缓存中直到它被剔除。剔除规则是基于 LRU 的：一旦缓存满了，最近最少使用的过滤器会被剔除。

> Elasticsearch版本：2.x

原文：https://www.elastic.co/guide/en/elasticsearch/guide/2.x/filter-caching.html#_autocaching_behavior
