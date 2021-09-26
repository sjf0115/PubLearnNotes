---
layout: post
author: sjf0115
title: ElasticSearch 精确值与全文文本
date: 2016-10-06 20:15:17
tags:
  - ElasticSearch
  - ElasticSearch 基础

categories: ElasticSearch
permalink: elasticsearch-exact-values-vs-full-text
---

Elasticsearch中的数据可以大致分为两种类型：精确值和全文文本。

### 1. 精确值

精确值（Exact Values）是确切的，正如它的名字一样。比如一个日期或一个用户ID，也可以包含确切的字符串，比如用户姓名或邮件地址。精确值"Foo"不同于和精确值"foo"。同样，精确值2014和精确值2014-09-15也不相同。

### 2. 全文文本

全文文本（Full text），换句话说，是文本化的数据(常常以人类的语言书写)，比如一篇Twitter文章或邮件正文等。

全文文本常常被称为非结构化数据，其实是一种用词不当的称谓，实际上自然语言是高度结构化的。问题是自然语言的语法规则是如此的复杂，以至于计算机难以正确解析。例如这个句子：
```
May is fun but June bores me.
```
到底是说的月份还是人呢？

### 3. 对比

精确值是比较容易查询的。因为就两个结果，要么匹配，要么不匹配。这类的查询很容易用SQL表达：
```
WHERE name = "John Smith"
  AND user_id = 2
  AND date > "2014-09-15"
```
而对于查询全文文本数据来说，却有些微妙。我们不只会去询问这篇文档是否满足查询要求，我们还会询问这篇文档与查询的匹配程度如何。换句话说，这篇文档与查询条件的相关度有多高？

我们很少精确的匹配整个全文文本。相反，我们会在全文文本中查询包含查询文本的部分。不仅如此，我们还期望搜索引擎能理解我们的意图：
- 如果查询"UK"，同时也希望能够返回涉及"United Kingdom"的文档。
- 如果查询"jump"，同时也希望能够返回匹配"jumped"， "jumps"， "jumping"甚至"leap"的文档。
- 如果查询"johnny walker"，同时也希望能够返回匹配"Johnnie Walker"的文档。
- 如果查询"fox news hunting"，同时也希望能够返回有关hunting on Fox News的故事，查询"fox hunting news"，也能返回关于fox hunting的新闻故事。

为了方便在全文文本字段中进行这些类型的查询，Elasticsearch首先对文本分析(analyzes)，然后使用结果建立一个倒排索引。

> Elasticsearch版本：5.4

参考：https://www.elastic.co/guide/en/elasticsearch/guide/2.x/_exact_values_versus_full_text.html
