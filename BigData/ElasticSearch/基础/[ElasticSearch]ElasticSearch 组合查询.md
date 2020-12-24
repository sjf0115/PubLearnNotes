---
layout: post
author: sjf0115
title: ElasticSearch 组合查询
date: 2016-10-28 14:15:17
tags:
  - ElasticSearch
  - ElasticSearch 基础

categories: ElasticSearch
permalink: elasticsearch-base-compound-queries
---

现实世界的搜索需求从来都没有那么简单：它们需要在不同文本上查询多个字段，并且根据一系列的标准进行过滤。为了构建复杂的查询，你需要有一种能够将多个查询组合成一个搜索请求的方法。

### 1. 布尔查询

你可以使用 `bool` 查询来实现这个需求。这种查询将多个查询组合在一起，形成用户自定义的布尔查询组合。这个查询接受以下参数：
- `must`：文档`必须`匹配这些条件才能被包含进来。
- `must_not`：文档`必须不`匹配这些条件才能被包含进来。
- `should`：如果满足这些语句中的任意语句，将增加 `_score` 的值，否则，没有任何影响。它们主要用于修正每个文档的相关性得分。
- `filter`：必须 `匹配`，但它以不评分、过滤模式来运行。这些语句对评分没有贡献，只是根据过滤标准来排除或包含文档。

由于这是我们看到的第一个包含其他查询的查询，所以有必要讨论一下相关性得分是如何组合的。每一个子查询都独立地计算文档的相关性得分。一旦它们的得分被计算出来， `bool` 查询就将这些得分进行合并并且返回一个得分来代表布尔操作的总分。

下面的查询用于查找 `title` 字段能够匹配 `how to make millions` 查询字符串并且没有被标识为 `spam` 的文档。那些被标识为 `starred` 或时间在 2014 之后的文档，将比另外那些文档拥有更高的排名。如果两者都满足，那么它排名将更高：
```json
{
    "bool": {
        "must":     { "match": { "title": "how to make millions" }},
        "must_not": { "match": { "tag":   "spam" }},
        "should": [
            { "match": { "tag": "starred" }},
            { "range": { "date": { "gte": "2014-01-01" }}}
        ]
    }
}
```
> 如果没有 must 语句，那么至少需要能够匹配其中的一条 should 语句。但，如果存在至少一条 must 语句，则对 should 语句的匹配没有要求。

### 2. 增加带过滤器的查询

如果我们不想文档的时间影响得分，可以用 `filter` 语句来重写前面的例子：
```json
{
    "bool": {
        "must":     { "match": { "title": "how to make millions" }},
        "must_not": { "match": { "tag":   "spam" }},
        "should": [
            { "match": { "tag": "starred" }}
        ],
        "filter": {
          "range": { "date": { "gte": "2014-01-01" }}
        }
    }
}
```
> range 查询已经从 should 语句中转移到 filter 语句。

通过将 `range` 查询转移到 `filter` 语句中，我们将这个查询转换成一个不评分查询，不会再为文档相关性排名贡献得分。由于它现在是一个不评分的查询，可以使用各种对 `filters` 查询的优化手段来提升性能。

所有查询都可以借鉴这种方式。简单的将查询转移到 `bool` 查询的 `filter` 语句中，这样它会自动转换成一个不评分的 `filter`。

如果你需要通过多个不同的标准来进行过滤，`bool` 查询本身也可以被用做一个不评分查询。简单地将它放到 `filter` 语句中并在内部构建布尔逻辑：
```json
{
    "bool": {
        "must":     { "match": { "title": "how to make millions" }},
        "must_not": { "match": { "tag":   "spam" }},
        "should": [
            { "match": { "tag": "starred" }}
        ],
        "filter": {
          "bool": {
              "must": [
                  { "range": { "date": { "gte": "2014-01-01" }}},
                  { "range": { "price": { "lte": 29.99 }}}
              ],
              "must_not": [
                  { "term": { "category": "ebooks" }}
              ]
          }
        }
    }
}
```
> 将 bool 查询放在在 filter 语句中，我们可以在过滤标准中增加布尔逻辑。

通过混合布尔查询，我们可以在我们的查询请求中灵活地编写 `scoring` 和 `filtering` 查询逻辑。

### 3. constant_score 查询

尽管没有 `bool` 查询使用这么频繁，但是 `constant_score` 查询对我们也非常有用。将一个不变的常量评分应用于所有匹配的文档。经常用来只需要执行一个 `filter` 而没有其它查询（例如，评分查询）的情况下。

可以使用它来取代只有 `filter` 语句的 `bool` 查询。在性能上是完全相同的，但对于提高查询简洁性和清晰度有很大帮助：
```json
{
    "constant_score":   {
        "filter": {
            "term": { "category": "ebooks" }
        }
    }
}
```
> term 查询放在 constant_score 语句中的 filter 子句中，转成一个不评分的 filter。这种方式可以用来取代只有 filter 语句的 bool 查询。


> ElasticSearch版本:2.x

原文：https://www.elastic.co/guide/en/elasticsearch/guide/2.x/combining-queries-together.html
