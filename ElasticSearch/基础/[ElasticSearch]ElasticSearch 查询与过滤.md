---
layout: post
author: sjf0115
title: ElasticSearch 查询与过滤
date: 2016-10-28 14:15:17
tags:
  - ElasticSearch
  - ElasticSearch 基础

categories: ElasticSearch
permalink: elasticsearch-base-queries-and-filters
---

> Elasticsearch版本：2.x

### 1. 查询与过滤

Elasticsearch 使用的查询语言（DSL）拥有一套查询组件(称之为`queries`)，这些组件可以以无限组合的方式进行搭配。这套组件可以在以下两种上下文中使用：过滤上下文（filtering context）和查询上下文（query context）。

#### 1.1 过滤上下文

当在过滤上下文(filtering context)中使用时，该查询被设置成一个'不评分'或者'过滤'的查询。换句话说，这个查询只是简单的问一个问题：这篇文档是否匹配？。回答也是非常的简单，是或者不是。例如，我们举几个例子：
- `created` 时间是否在 `2013` 与 `2014` 这个区间？
- `status` 字段是否包含 `published` 这个词条？
- `lat_lon` 字段表示的位置是否在指定点的 `10km` 范围内？

#### 1.2 查询上下文

当在查询上下文中使用时，查询就变成了一个'评分'的查询。和不评分的查询类似，也要去判断这个文档是否匹配，但同时还需要判断和这个文档匹配度。

此查询的典型用法是用于查找以下文档：
- 查找与 `full text search` 这个词语最佳匹配的文档。
- 包含 `run` 这个词，也能匹配 `runs`，`running`，`jog` 或者 `sprint`。
- 包含 `quick`，`brown` 和 `fox` 这几个词，它们之间距离越近，文档相关性越高。
- 标有 `lucene`，`search` 或者 `java` 标签，含有标签越多，相关性越高。

一个评分查询计算每一个文档与此查询的相关程度，同时将这个相关程度赋值给一个相关性变量 `_score`，然后使用这个变量按照相关性对匹配到的文档进行排序。相关性的概念是非常适合全文搜索的情况，因为全文搜索几乎没有完全'正确'的答案。

> 以前版本中，查询(queries)和过滤(filters)是 Elasticsearch 中两个相互独立的组件。从Elasticsearch2.0版本开始，过滤就已经从技术上被排除了，同时所有查询(queries)都拥有了不评分查询的能力。

> 然而，为了简洁与清晰，我们将使用 `filter` 这个词来表示为不评分，只过滤的查询。你可以将 `filter` 、`filtering query` 和 `non-scoring query` 这几个词视为相同的。

> 类似地，相似的，如果单独地不加任何修饰词地使用 `query` 这个词，我们指的是 `scoring query`。

### 2. 性能差异

过滤查询只是简单的包含/排除检查，这使得它们计算速度非常快。当至少有一个过滤查询的结果是'稀疏'的（匹配到少数文档）时，有很多不同优化方法可以做，不评分查询经常被缓存在内存中，以加快访问速度。

相反，评分查询不仅要找到匹配的文档，还要计算每个文档的相关度，这通常使它们比不评分查询更重，更慢。同时，查询结果不能缓存。

由于倒排索引，一个简单的评分查询在只匹配几个文档时可能会比过滤数百万文档的过滤更好一点。但是，一般情况下，过滤会比评分查询在性能上更优异，并表现的很稳定。

过滤的目标是减少那些需要通过评分查询进行检查的文档。

### 3. 如何选择查询与过滤

通常的规则是，使用查询（query）语句来进行 `全文搜索` 或者其他任何需要影响相关性得分条件的搜索。除此以外的情况都使用过滤（filters)。

原文：https://www.elastic.co/guide/en/elasticsearch/guide/2.x/_queries_and_filters.html#_queries_and_filters
