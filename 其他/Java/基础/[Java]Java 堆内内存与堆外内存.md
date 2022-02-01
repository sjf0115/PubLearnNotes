---
layout: post
author: sjf0115
title: Java 堆内内存与堆外内存
date: 2018-02-04 17:40:01
tags:
  - Java

categories: Java
permalink: java-on-off-heap-memory
---

一般情况下，Java 中分配的非空对象都是由 Java 虚拟机的垃圾收集器管理的，也称为堆内内存（`on-heap memory`）。虚拟机会定期对垃圾内存进行回收，在某些特定的时间点，它会进行一次彻底的回收（`full gc`）。彻底回收时，垃圾收集器会对所有分配的堆内内存进行完整的扫描，这意味着一个重要的事实——这样一次垃圾收集对 Java 应用造成的影响，跟堆的大小是成正比的。过大的堆会影响 Java 应用的性能。

对于这个问题，一种解决方案就是使用堆外内存（`off-heap memory`）。堆外内存意味着把内存对象分配在 Java 虚拟机的堆以外的内存，这些内存直接受操作系统管理（而不是虚拟机）。这样做的结果就是能保持一个较小的堆，以减少垃圾收集对应用的影响。

但是 Java 本身也在不断对堆内内存的实现方式做改进。两者各有什么优缺点？ [Vanilla Java](http://vanillajava.blogspot.com/) 博客作者 Peter Lawrey 撰写了一篇[文章](http://vanillajava.blogspot.com/2014/12/on-heap-vs-off-heap-memory-usage.html)，在文中他对三种方式：用new来分配对象、对象池（object pool）和堆外内存，进行了详细的分析。

用new来分配对象内存是最基本的一种方式，Lawery提到：

在Java 5.0之前，分配对象的代价很大，以至于大家都使用内存池。但是从5.0开始，对象分配和垃圾回收变得快多了，研发人员发现了性能的提升，纷纷简化他们的代码，不再使用内存池，而直接用new来分配对象。从5.0开始，只有一些分配代价较大的对象，比如线程、套接字和数据库链接，用内存池才会有明显的性能提升。

对于内存池，Lawery认为它主要用于两类对象。第一类是生命周期较短，且结构简单的对象，在内存池中重复利用这些对象能增加CPU缓存的命中率，从而提高性能。第二种情况是加载含有大量重复对象的大片数据，此时使用内存池能减少垃圾回收的时间。对此，Lawery还以 [StringInterner](https://github.com/OpenHFT/Java-Lang/blob/master/lang/src/main/java/net/openhft/lang/pool/StringInterner.java) 为例进行了说明。

最后Lawery分析了堆外内存，它和内存池一样，也能缩短垃圾回收时间，但是它适用的对象和内存池完全相反。内存池往往适用于生命期较短的可变对象，而生命期中等或较长的对象，正是堆外内存要解决的。堆外内存有以下特点：
- 对于大内存有良好的伸缩性
- 对垃圾回收停顿的改善可以明显感觉到
- 在进程间可以共享，减少虚拟机间的复制

Lawery还提到堆外内存最重要的还不是它能改进性能，而是它的确定性。

当然堆外内存也有它自己的问题，最大的问题就是你的数据结构变得不那么直观，如果数据结构比较复杂，就要对它进行序列化（serialization），而序列化本身也会影响性能。另一个问题是由于你可以使用更大的内存，你可能开始担心虚拟内存（即硬盘）的速度对你的影响了。

Lawery还介绍了OpenHFT公司提供三个开源库：[Chronicle Queue](http://openhft.net/products/chronicle-queue/)、[Chronicle Map](http://openhft.net/products/chronicle-map/)和 [Thread Affinity](http://openhft.net/products/thread-affinity/)，这些库可以帮助开发人员使用堆外内存来保存数据。采用堆外内存有很多好处，同时也带来挑战，对堆外内存感兴趣的读者可以阅读Lawery的原文来了解更多信息。

转载于： http://www.infoq.com/cn/news/2014/12/external-memory-heap-memory/
