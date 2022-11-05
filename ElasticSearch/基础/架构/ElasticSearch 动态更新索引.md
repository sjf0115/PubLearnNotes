---
layout: post
author: sjf0115
title: ElasticSearch 动态更新索引
date: 2016-11-04 09:15:17
tags:
  - ElasticSearch
  - ElasticSearch 基础

categories: ElasticSearch
permalink: elasticsearch-base-dynamically-updatable-indices
---

> Elasticsearch版本：2.x

### 1. 不变性

倒排索引被写入磁盘后是 `不可改变`(immutable)：永远不会被修改。不变性有如下几个重要的优势：
- 不需要锁。如果你没有必要更新索引，你就没有必要担心多进程会同时修改数据。
- 一旦索引被读入内核的文件系统缓存中，由于其不会改变，便会留在那里。只要文件系统缓存中还有足够的空间，那么大部分读请求会直接请求内存，而不会命中磁盘。这提供了很大的性能提升。
- 其它缓存(例如filter缓存)，在索引的生命周期内始终保持有效。因为数据不会改变，不需要在每次数据改变时被重建。
- 写入一个大的倒排索引中允许数据被压缩，减少磁盘 I/O 和 缓存索引所需的RAM量。

当然，一个不变的索引也有缺点。主要是它是不可变的! 你不能修改它。如果你需要让一个新的文档可被搜索，你需要重建整个索引。这对索引可以包含的数据量或可以更新索引的频率造成很大的限制。

### 2. 动态更新索引

下一个需要解决的问题是如何更新倒排索引，而不会失去其不变性的好处？ 答案是：`使用多个索引`。

通过增加一个新的补充索引来反映最近的修改，而不是直接重写整个倒排索引。每一个倒排索引都会被轮流查询--从最旧的开始--再对各个索引的查询结果进行合并。

Lucene 是 Elasticsearch 所基于的Java库，引入了 `按段搜索` 的概念。 每一个段本身就是一个倒排索引， 但 Lucene 中的 `index` 除表示段 `segments` 的集合外，还增加了提交点 `commit point` 的概念，一个列出了所有已知段的文件，如下图所示展示了带有一个提交点和三个分段的 Lucene 索引:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ElasticSearch/elasticsearch-base-dynamically-updatable-indices-1.png?raw=true)

新文档首先被添加到内存中的索引缓冲区中，如下图所示展示了一个在内存缓存中包含新文档准备提交的Lucene索引:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ElasticSearch/elasticsearch-base-dynamically-updatable-indices-2.png?raw=true)

然后写入到一个基于磁盘的段，如下图所示展示了在一次提交后一个新的段添加到提交点而且缓存被清空:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ElasticSearch/elasticsearch-base-dynamically-updatable-indices-3.png?raw=true)

#### 2.1 索引与分片

一个 Lucene 索引就是我们 Elasticsearch 中的分片`shard`，而 Elasticsearch 中的一个索引是分片的集合。当 Elasticsearch 搜索索引时，它将查询发送到属于该索引的每个分片(Lucene索引)的副本(主分片，副本分片)上，然后将每个分片的结果聚合成全局结果集，如[ElasticSearch 内部原理之分布式文档搜索](http://smartsi.club/2016/10/26/elasticsearch-internal-distributed-document-search/)中描述。

#### 2.2 按段搜索过程

(1) 新文档被收集到内存索引缓冲区中，如上第一图；

(2) 每隔一段时间，缓冲区就被提交：
- 一个新的段(补充的倒排索引)被写入磁盘。
- 一个新的提交点`commit point`被写入磁盘，其中包括新的段的名称。
- 磁盘进行`同步` — 所有在文件系统缓冲区中等待写入的都 `flush` 到磁盘，以确保它们被写入物理文件。

(3) 新分段被开启，使其包含的文档可以被搜索。

(4) 内存缓冲区被清除，并准备好接受新的文档。

当一个查询被触发，所有已知的段按顺序被查询。词项统计会对所有段的结果进行聚合，以保证每个词和每个文档的关联都被准确计算。 这种方式可以用相对较低的成本将新文档添加到索引。

### 3. 删除与更新

段是不可变的，因此无法从旧的段中删除文档，也不能更新旧的段来反映文档的更新。相反，每个提交点 `commit point` 都包括一个 `.del` 文件，文件列出了哪个文档在哪个段中已经被删除了。

当文档被'删除'时，它实际上只是在 `.del` 文件中被标记为已删除。标记为已删除的文档仍然可以匹配查询，但在最终查询结果返回之前，它将从结果列表中删除。

文档更新也以类似的方式工作：当文档更新时，旧版本文档被标记为已删除，新版本文档被索引到新的段中。也许文档的两个版本都可以匹配查询，但是在查询结果返回之前旧的标记删除版本的文档会被移除。

在[ElasticSearch 段合并](http://smartsi.club/2016/11/05/elasticsearch-base-sgement-merge/)中，我们将展示如何从文件系统中清除已删除的文档。

原文：https://www.elastic.co/guide/en/elasticsearch/guide/2.x/dynamic-indices.html
