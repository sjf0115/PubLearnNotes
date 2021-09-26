---
layout: post
author: sjf0115
title: Flink 如何管理 RocksDB 内存大小
date: 2021-07-13 18:08:21
tags:
  - Flink

categories: Flink
permalink: manage-rocksdb-memory-size-apache-flink
---

这篇文章描述了一些配置选项，这些选项可以帮助我们有效地管理 Apache Flink 中 RocksDB 状态后端的内存大小。在前面的[文章](http://smartsi.club/stateful-stream-processing-apache-flink-state-backends.html)中，我们讲述了 Flink 中可支持的状态后端，本文将介绍跟 Flink 相关的一些 RocksDB 操作，并讨论一些提高资源利用率的重要配置。

> 从 Flink 1.10 开始，Flink 就开始自动管理 RocksDB 的内存，详细介绍请查阅 [Memory Management](https://ci.apache.org/projects/flink/flink-docs-release-1.10/ops/state/state_backends.html#memory-management)

### 1. RocksDB 状态后端

在深入了解配置参数之前，我们先回顾一下在 Apache Flink 中如何使用 RocksDB 来进行状态管理。当我们选择 RocksDB 作为状态后端时，状态将作为序列化字节串存在于堆外内存或本地磁盘中。RocksDB 是以日志合并树(LSM 树）进行组织的 KV 存储。当用于存储 Keyed 状态时，Key 由 <Keygroup，Key，Namespace> 的序列化字节组成，而 Value 由状态的序列化字节组成。每次注册 Keyed 状态时，它都可以映射到列族（类似于传统数据库中的表），并将键值对以序列化字节存储在 RocksDB 中。这意味着每次读写操作都必须对数据进行反序列化或者序列化，与 Flink 内置的内存状态后端相比，会有一些性能开销。

使用 RocksDB 作为状态后端有许多优点：
- 不受 Java 垃圾回收的影响，与堆对象相比，它的内存开销更低，并且是目前唯一支持增量检查点的状态后端。
- 此外使用 RocksDB，状态大小仅受限于本地可用磁盘空间的大小，非常适合状态特别大的 Flink 应用程序。

下面的图表将进一步阐明 RocksDB 的基本读写操作：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/manage-rocksdb-memory-size-apache-flink-1.png?raw=true)

RocksDB 的 WRITE 操作将把数据存储到当前活跃的 MemTable 中。当 MemTable 写满时，它将成为 READ ONLY MemTable，并被一个新的空的 MemTable 替换。READ ONLY MemTable 被后台线程周期性地刷新到磁盘上，生成按键排序的只读文件，这便是所谓的 SSTables。这些 SSTable 是不可变的，通过后台的多路归并实现进一步的整合。如前所述，对于 RocksDB，每个注册状态都对应一个列族，这意味着每个状态都包含一组 MemTables 和 SSTables。

RocksDB 中的 READ 操作首先访问活跃的 MemTable 来反馈查询。如果找到待查询的 key，那么 READ 操作将从最新 READ ONLY MemTables 到最旧依次访问，直到找到待查询的 key 为止。如果在任何 MemTable 中都找不到该 key，那么 READ 操作将访问 SSTables，再次从最新的开始。SSTables 文件可以：
- 优先去 RocksDB 的 BlockCache 读取；
- 如果 BlockCache 没有的话，就去读操作系统的文件，这些文件块又可能被操作系统缓存了；
- 最差的情况就是去本地磁盘读取；
- SST 级别的布隆过滤器策略可以避免大量的磁盘访问。

### 2. 管理 RocksDB 内存的 3 种配置

现在，我们已经理解了 Flink 中 Rocksdb 功能，接下来看看一些配置选项以更有效地管理 RocksDB 内存大小。请注意，下面的选项并不详尽，因为您可以使用 Apache Flink 1.6 中引入的 state TTL（Time To Live）功能来管理 Flink 应用程序的状态大小。

以下三个配置是一个很好的起点，可以有效帮助您管理 Rocksdb 的内存开销：

#### 2.1 block_cache_size

此配置最终将控制内存中缓存的最大未压缩块数。随着块数的不断增加，内存大小也会增加。因此，通过预先配置，您可以保持固定内存消耗级别。

#### 2.2 write_buffer_size

此配置本质上是控制 RocksDB 中 MemTable 的最大大小。活跃 MemTables 和 READ ONLY MemTables 最终会影响 RocksDB 中的内存大小，所以提前调整可能会为以后避免一些麻烦。

#### 2.3 max_write_buffer_number

在 RocksDB 将 MemTables 刷新到磁盘上的 SSTable 之前，此配置控制着内存中保留的 MemTables 的最大数量。这实际上是内存中 READ ONLY MemTables 的最大数量。

除了上面提到的资源之外，您还可以选择配置索引和布隆过滤器，但它们会消耗额外的内存空间， Table 级别的 Cache 也是一样。在这里，Table 缓存不仅会额外占用 RocksDB 的内存，还会占用 SST 文件的打开文件描述符，(在默认情况下设置的大小是不受限制的)，如果配置不正确，可能会影响操作系统的设置。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

原文：[How to manage your RocksDB memory size in Apache Flink](https://www.ververica.com/blog/manage-rocksdb-memory-size-apache-flink)
