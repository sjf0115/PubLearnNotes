---
layout: post
author: sjf0115
title: ElasticSearch 倒排索引
date: 2016-07-06 23:15:17
tags:
  - ElasticSearch

categories: ElasticSearch
permalink: elasticsearch-inverted-index
---

Elasticsearch使用一种叫做倒排索引(inverted index)的结构来做快速的全文搜索。倒排索引由在文档中出现的唯一的单词列表，以及对于每个单词在文档中的位置组成（ An inverted index consists of a list of all the unique words that appear in any document, and for each word, a list of the documents in which it appears）。

例如，我们有两个文档，每个文档都有一个content字段，内容如下：
```
The quick brown fox jumped over the lazy dog
Quick brown foxes leap over lazy dogs in summer
```

为了创建倒排索引，我们首先切分每个文档的content字段为单独的单词（我们把它们叫做词项（terms）或者词条（tokens）），把所有的唯一词项terms放入列表中并排序，并列出每个词项出现在哪些文档中，结果是这个样子的：
