---
layout: post
author: sjf0115
title: ElasticSearch 持久化变更
date: 2016-11-08 20:01:23
tags:
  - ElasticSearch
  - ElasticSearch 基础

categories: ElasticSearch
permalink: elasticsearch-base-making-changes-persistent
---

### 1. 持久化变更

如果没有使用 `fsync` 将文件系统缓存中的数据刷（flush）到磁盘上，我们无法保证数据在断电后甚至在正常退出应用程序后仍然存在。为了使 Elasticsearch 具有可靠性，我们需要确保将更改持久化到磁盘上。

在[ElasticSearch 动态更新索引](http://smartsi.club/2016/10/30/elasticsearch-base-dynamically-updatable-indices/)中，我们说过一次完整提交会将段刷到磁盘，并写入到一个包含所有段列表的提交点 `commit point`。Elasticsearch 在启动或重新打开索引时使用此提交点来确定哪些段属于当前分片。

当我们每秒刷新（refresh）一次即可实现近实时搜索，但是我们仍然需要定期进行全面的提交，以确保我们可以从故障中恢复。但发生在两次提交之间文件变化怎么办？ 我们也不想丢失。

Elasticsearch添加了一个 `Translog` 或者叫事务日志，它记录了 Elasticsearch 中的每个操作。使用 `Translog`，处理过程现在如下所示：

(1) 索引文档时，将其添加到内存索引缓冲区中，并追加到 `Translog` 中，如下图所示:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ElasticSearch/elasticsearch-base-making-changes-persistent-1.png?raw=true)

(2) 刷新`refresh`使分片处于下图描述的状态，分片每秒被刷新（refresh）一次：
- 内存缓冲区中的文档写入一个新的段中，而没有 `fsync`。
- 段被打开以使其可以搜索。
- 内存缓冲区被清除。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ElasticSearch/elasticsearch-base-making-changes-persistent-2.png?raw=true)

(3) 该过程继续，将更多的文档添加到内存缓冲区并追加到 `Translog` 中，如下图所示:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ElasticSearch/elasticsearch-base-making-changes-persistent-3.png?raw=true)

(4) 每隔一段时间，例如 `Translog` 变得非常大，索引被刷新 `flush` 到磁盘，一个新的 `Translog` 被创建，并执行一个全量提交：
- 内存缓冲区中的任何文档都将写入新的段。
- 内存缓冲区被清除。
- 一个提交点被写入硬盘。
- 文件系统缓存通过 `fsync` 被刷新 `flush` 到磁盘。
- 老的 `Translog` 被删除。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ElasticSearch/elasticsearch-base-making-changes-persistent-4.png?raw=true)

`Translog` 提供所有尚未刷新 `flush` 到磁盘的操作的一个持久化记录。启动时，Elasticsearch 将使用最后一个提交点从磁盘中恢复已知的段，然后将重新执行 `Translog` 中的所有操作，以添加最后一次提交后发生的更改。

`Translog`也被用来提供实时`CRUD`。当你试着通过ID查询、更新、删除一个文档，在尝试从相应的段中检索文档之前，首先检查 `Translog` 来查看最近的变更。这意味着它总是能够实时地获取到文档的最新版本。

### 2. flush API

在 Elasticsearch 中执行提交和截断 `Translog` 的操作被称作一次 `flush`。分片每30分钟或者当 `Translog` 变得太大时会自动 flush 一次。有关可用于控制这些阈值的设置，请参阅[Translog文档](https://www.elastic.co/guide/en/elasticsearch/reference/current/index-modules-translog.html#_translog_settings)。

flush API 可用于执行手动刷新：
```
POST /blogs/_flush
POST /_flush?wait_for_ongoing
```

> 第一个语句刷新 `blogs` 索引；第二个语句刷新所有索引，等待所有刷新完成后返回。

你很少需要手动 `flush`；通常情况下，自动 `flush` 就足够了。这就是说，在重启节点或关闭索引之前执行 `flush` 有益于你的索引。当 Elasticsearch 尝试恢复或重新打开一个索引，它需要重新执行 `Translog` 中所有的操作，所以如果 `Translog` 中日志越短，恢复越快。

### 3. Translog有多安全？

`Translog` 的目的是确保操作不会丢失。这就提出了一个问题：`Translog`的安全性如何？

在文件被 `fsync` 到磁盘前，被写入的文件在重启之后就会丢失。默认情况下，`Translog` 每5秒进行一次 `fsync` 刷新到磁盘，或者在每次写请求(例如`index`, `delete`, `update`, `bulk`)完成之后执行。这个过程发生在主分片和副本分片上。最终，这意味着在整个请求被`fsync` 到主分片和副本分片上的 `Translog` 之前，你的客户端不会得到一个`200 OK`响应。

在每个请求之后执行 `fsync` 都会带来一些性能消耗，尽管实际上相对较小（特别是对于bulk导入，在单个请求中平摊了许多文档的开销）。

但是对于一些高容量的集群而言，丢失几秒钟的数据并不严重，因此使用异步的 `fsync` 还是比较有好处的。比如，写入的数据被缓存到内存后，再每5秒整体执行一次 `fsync`。

可以通过将 `durability` 参数设置为异步来启用此行为：
```json
PUT /my_index/_settings
{
    "index.translog.durability": "async",
    "index.translog.sync_interval": "5s"
}
```

可以为每个索引单独进行配置，并可以动态更新。如果你决定启用异步 `Translog` 行为，你需要确认如果发生崩溃，丢失掉 `sync_interval` 时间段的数据也没有关系。在决定使用这个参数前请注意这个特征！

如果你不确定此操作的后果，最好使用默认值（`"index.translog.durability"："request"`）以避免数据丢失。

> ElasticSearch版本：2.x

原文：https://www.elastic.co/guide/en/elasticsearch/guide/2.x/translog.html
