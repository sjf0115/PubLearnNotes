---
layout: post
author: sjf0115
title: ElasticSearch 近实时搜索
date: 2016-11-11 19:30:23
tags:
  - ElasticSearch
  - ElasticSearch 基础

categories: ElasticSearch
permalink: elasticsearch-base-near-real-time-search
---

### 1. 按段搜索

随着 `按段搜索` 的发展，索引文档与文档可被搜索的延迟显着下降。新文档可以在数分钟内可被搜索，但仍然不够快。

在这里磁盘是瓶颈。提交一个新的段到磁盘需要 `fsync` 来确保段被物理性地写入磁盘，这样在断电的时候也不会丢失数据。但是 `fsync` 代价很大; 如果每次索引一个文档都去执行一次的话会造成很大的性能问题。

我们需要的是一个更轻量的方式来使文档可被搜索，这意味着要从整个过程中移除 `fsync`。

在 Elasticsearch 和磁盘之间的是文件系统缓存。如前所述，内存中索引缓冲区中的文档(如下第一图)被写入新的段(如下第二图)．但是新的段首先被写入到文件系统缓存中 - 成本较低 - 只是稍后会被刷到磁盘 - 成本较高。但一旦文件在缓存中，它就可以像任何其他文件一样打开和读取。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ElasticSearch/elasticsearch-base-near-real-time-search-1.png?raw=true)

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ElasticSearch/elasticsearch-base-near-real-time-search-2.png?raw=true)

Lucene 允许新段被写入和打开，使其包含的文档在没有进行一次完整提交之前便对搜索可见。这是一种比提交更轻量级的过程，并在不影响性能的前提下可以被频繁地执行。

### 2. Refresh API

在 ElasticSearch 中，这种轻量级写入和打开新片段的过程称为刷新`refresh`。默认情况下，每个分片每秒会自动刷新一次。这就是为什么我们说 Elasticsearch 是近实时搜索：文档更改不会立即对搜索可见，但会在1秒之内对搜索可见。

这可能会让新用户感到困惑：他们索引文档后并尝试搜索它，但是没有搜索到。这个问题的解决办法是使用 Refresh API 手动刷新一下：
```
POST /_refresh
POST /blogs/_refresh
```

> 第一个语句刷新所有索引，第二个语句只是刷新`blogs`索引

虽然刷新比提交(一次完整提交会将段刷到磁盘)更轻量级，但是仍然具有性能成本。编写测试时手动刷新可能很有用，但在生产环境中不要每次索引文档就去手动刷新。它会增大性能开销。相反，你的应用需要意识到 Elasticsearch 的近实时的性质，并做相应的补偿措施。

并非所有场景都需要每秒刷新一次。也许你正在使用 Elasticsearch 来索引数百万个日志文件，而你更希望优化索引速度，而不是近实时搜索。你可以通过设置 `refresh_interval` 来降低每个索引的刷新频率：
```json
PUT /my_logs
{
  "settings": {
    "refresh_interval": "30s"
  }
}
```

> 每30秒刷新一次`my_logs`索引。

`refresh_interval` 可以在现有索引上动态更新。你可以在构建大型新索引时关闭自动刷新，然后在生产环境中开始使用索引时将其重新打开：
```
PUT /my_logs/_settings
{ "refresh_interval": -1 }

PUT /my_logs/_settings
{ "refresh_interval": "1s" }
```

> 第一个语句禁用自动刷新,第二个语句每秒自动刷新一次;

`refresh_interval` 需要一个持续时间值， 例如 1s （1 秒） 或 2m （2 分钟）。 一个绝对值 1 表示的是 1毫秒 --无疑会使你的集群陷入瘫痪(每一毫秒刷新一次)。

> ElasticSearch版本：2.x

原文：https://www.elastic.co/guide/en/elasticsearch/guide/2.x/near-real-time.html
