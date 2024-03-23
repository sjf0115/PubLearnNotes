---
layout: post
author: 酷壳陈皓
title: Cache 缓存更新策略
date: 2018-02-03 10:40:01
tags:
  - CaChe

categories: other
permalink: cache-update-policy
---

看到好些人在写更新缓存数据代码时，`先删除缓存，然后再更新数据库，而后续的操作会把数据再装载的缓存中`。然而，这个是逻辑是 `错误` 的。试想，两个并发操作，一个是更新操作，另一个是查询操作，更新操作删除缓存后，查询操作没有命中缓存，先把老数据读出来后放到缓存中，然后更新操作更新了数据库。于是，在缓存中的数据还是老的数据，导致缓存中的数据是脏的，而且还一直这样脏下去了。

我不知道为什么这么多人用的都是这个逻辑，当我在微博上发了这个贴以后，我发现好些人给了好多非常复杂和诡异的方案，所以，我想写这篇文章说一下几个缓存更新策略。

这里，我们先不讨论更新缓存和更新数据这两个事是一个事务的事，或是会有失败的可能，我们先假设更新数据库和更新缓存都可以成功的情况（我们先把成功的代码逻辑先写对）。

更新缓存的的策略有四种：

- `Cache aside`
- `Read through`
- `Write through`
- `Write behind caching`

我们下面一一来看一下这四种策略。

### 1. Cache aside

这是最常用最常用的策略了。其具体逻辑如下：

- 失效：应用程序先从 `cache` 取数据，没有得到，则从数据库中取数据，成功后，放到缓存中。
- 命中：应用程序从 `cache` 中取数据，取到后返回。
- 更新：先把数据存到数据库中，成功后，再让缓存失效。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/cache-update-policy-1.png?raw=true)

注意，我们的更新是先更新数据库，成功后，让缓存失效。那么，这种方式是否可以没有文章前面提到过的那个问题呢？我们可以脑补一下。

一个是查询操作，一个是更新操作的并发，首先，没有了删除cache数据的操作了，而是先更新了数据库中的数据，此时，缓存依然有效，所以，并发的查询操作拿的是没有更新的数据，但是，更新操作马上让缓存的失效了，后续的查询操作再把数据从数据库中拉出来。而不会像文章开头的那个逻辑产生的问题，后续的查询操作一直都在取老的数据。

这是标准的策略，包括Facebook的论文[《Scaling Memcache at Facebook》](https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf)也使用了这个策略。为什么不是写完数据库后更新缓存？你可以看一下Quora上的这个问答[《Why does Facebook use delete to remove the key-value pair in Memcached instead of updating the Memcached during write request to the backend?》](https://www.quora.com/Why-does-Facebook-use-delete-to-remove-the-key-value-pair-in-Memcached-instead-of-updating-the-Memcached-during-write-request-to-the-backend)，主要是怕两个并发的写操作导致脏数据。

那么，是不是 `Cache Aside` 这个就不会有并发问题了？不是的，比如，一个是读操作，但是没有命中缓存，然后就到数据库中取数据，此时来了一个写操作，写完数据库后，让缓存失效，然后，之前的那个读操作再把老的数据放进去，所以，会造成脏数据。

但，这个case理论上会出现，不过，实际上出现的概率可能非常低，因为这个条件需要发生在读缓存时缓存失效，而且并发着有一个写操作。而实际上数据库的写操作会比读操作慢得多，而且还要锁表，而读操作必需在写操作前进入数据库操作，而又要晚于写操作更新缓存，所有的这些条件都具备的概率基本并不大。

所以，这也就是Quora上的那个答案里说的，要么通过2PC或是Paxos协议保证一致性，要么就是拼命的降低并发时脏数据的概率，而Facebook使用了这个降低概率的玩法，因为2PC太慢，而Paxos太复杂。当然，最好还是为缓存设置上过期时间。

### 2. Read/Write Through

我们可以看到，在上面的 `Cache Aside` 套路中，我们的应用代码需要维护两个数据存储，一个是缓存（`Cache`），一个是数据库（`Repository`）。所以，应用程序比较啰嗦。而 `Read/Write Through` 套路是把更新数据库（`Repository`）的操作由缓存自己代理了，所以，对于应用层来说，就简单很多了。可以理解为，应用认为后端就是一个单一的存储，而存储自己维护自己的 `Cache`。

#### 2.1 Read Through

`Read Through` 套路就是在查询操作中更新缓存，也就是说，当缓存失效的时候（过期或LRU换出），`Cache Aside` 是由调用方负责把数据加载入缓存，而 `Read Through` 则用缓存服务自己来加载，从而对应用方是透明的。

#### 2.2 Write Through

`Write Through` 套路和 `Read Through` 相仿，不过是在更新数据时发生。当有数据更新的时候，如果没有命中缓存，直接更新数据库，然后返回。如果命中了缓存，则更新缓存，然后再由 `Cache` 自己更新数据库（这是一个同步操作）

下图自来 Wikipedia 的 [Cache](https://en.wikipedia.org/wiki/Cache_(computing)) 词条。其中的 `Memory` 你可以理解为就是我们例子里的数据库。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/cache-update-policy-2.png?raw=true)

### 3. Write Behind Caching

`Write Behind` 又叫 `Write Back`。一些了解 `Linux` 操作系统内核的同学对 `write back` 应该非常熟悉，这不就是 `Linux` 文件系统的 `Page Cache` 的算法吗？ 是的，你看基础这玩意全都是相通的。所以，基础很重要，我已经不是一次说过基础很重要这事了。

`Write Back` 套路，一句说就是，在更新数据的时候，只更新缓存，不更新数据库，而我们的缓存会异步地批量更新数据库。这个设计的好处就是让数据的I/O操作飞快无比（因为直接操作内存嘛 ），因为异步，`write back` 还可以合并对同一个数据的多次操作，所以性能的提高是相当可观的。

但是，其带来的问题是，数据不是强一致性的，而且可能会丢失（我们知道 `Unix/Linux` 非正常关机会导致数据丢失，就是因为这个事）。在软件设计上，我们基本上不可能做出一个没有缺陷的设计，就像算法设计中的时间换空间，空间换时间一个道理，有时候，强一致性和高性能，高可用和高性性是有冲突的。软件设计从来都是取舍 `Trade-Off`。

另外，`Write Back` 实现逻辑比较复杂，因为他需要track有哪数据是被更新了的，需要刷到持久层上。操作系统的 `write back` 会在仅当这个 `cache` 需要失效的时候，才会被真正持久起来，比如，内存不够了，或是进程退出了等情况，这又叫 `lazy write`。

在 wikipedia 上有一张 `write back` 的流程图，基本逻辑如下：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/cache-update-policy-3.png?raw=true)

转载于： https://coolshell.cn/articles/17416.html
