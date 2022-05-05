---
layout: post
author: sjf0115
title: GC overhead limit exceeded
date: 2019-01-25 20:40:01
tags:
  - Java
  - JVM

categories: Java
permalink: jvm-gc-overhead-limit-exceeded
---

Java 运行时环境内置了 [垃圾收集(GC)](https://plumbr.io/handbook/what-is-garbage-collection) 进程。在很多编程语言中程序员需要手动分配和释放内存来重复利用释放的内存。

相反，在Java应用程序中我们只需要关心内存的分配。当内存中某块区域不再使用时，垃圾回收进程就会自动进行清理。GC的详细原理请参考 [GC性能优化](https://plumbr.io/java-garbage-collection-handbook) 系列文章, 一般来说, JVM内置的垃圾收集算法就能够应对绝大多数的业务场景。

当你的应用程序几乎耗尽所有可用内存并且GC无法清除时，会发生：java.lang.OutOfMemoryError: GC overhead limit exceeded 这种情况。

### 1. 发生的原因

抛出 `java.lang.OutOfMemoryError: GC overhead limit exceeded` 错误时表示你的应用程序花费太多的时间进行垃圾回收，但是效果比较差。默认情况下, 如果JVM花费的时间超过了GC执行总时间的98%，并且在GC之后，只有不到2％的堆被回收，JVM就会抛出这个错误。
















原文：https://plumbr.io/outofmemoryerror/gc-overhead-limit-exceeded
