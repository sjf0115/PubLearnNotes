---
layout: post
author: sjf0115
title: Redis 如何使用HyperLogLog
date: 2019-12-01 14:59:06
tags:
  - Redis

categories: Redis
permalink: how-to-use-hyperloglog-in-redis
---

### 1. 概述

Redis 在 2.8.9 版本添加了 HyperLogLog 数据结构，用来做基数统计，其优点是在输入元素的数量非常大时，计算基数所需的空间比较小并且一般比较恒定。

在 Redis 里面，每个 HyperLogLog 键只需要花费 12 KB 内存就可以计算接近 2^64 个不同元素的基数。这和计算基数时，元素越多耗费内存越多的集合形成鲜明对比。但是，因为 HyperLogLog 只会根据输入元素来计算基数，并不会储存输入元素本身，所以 HyperLogLog 不能像集合那样能返回输入的各个元素。

### 2. 什么是基数?

比如数据集 `{1, 3, 5, 7, 5, 7, 8}`， 那么这个数据集的基数集为 `{1, 3, 5 ,7, 8}`, 基数(不重复元素)为5。基数估计就是在误差可接受的范围内，快速计算基数。

### 3. 命令

HyperLogLog 目前只支持3个命令，`PFADD`、`PFCOUNT`、`PFMERGE`。我们先来逐一介绍一下。

#### 3.1 PFADD

> 最早可用版本：2.8.9。时间复杂度：O(1)。

`PFADD` 命令可以将元素(可以指定多个元素)添加到 HyperLogLog 数据结构中并存储在第一个参数 `key` 指定的键中。如果命令执行之后，基数估计发生变化就返回1，否则返回0。如果指定的 `key` 不存在，那么就创建一个空的 HyperLogLog 数据结构(即，指定字符串长度以及编码的 Redis String)。也可以调用不指定元素参数而只指定键的命令。如果键存在，不执行任何操作并返回0；如果键不存在，则会创建一个新的 HyperLogLog 数据结并且返回1。

(1) 语法格式:
```
PFADD key element [element ...]
```
(2) 返回值:
```
整型，如果至少有个元素被添加返回 1， 否则返回 0。
```
(3) Example:
```
127.0.0.1:6379> PFADD hll a b c d e f g
(integer) 1
127.0.0.1:6379> pfcount hll
(integer) 7
```

#### 3.2 PFCOUNT

> 最早可用版本：2.8.9。时间复杂度：O(1)，对于多个比较大的key的时间复杂度是O(N)。

`PFCOUNT` 命令返回指定 HyperLogLog 的基数估算值。对于单个键，该命令返回的是指定键的基数估算值，如果键不存在，则返回0。对于多个键，返回的是多个 HyperLogLog 并集的基数估算值，通过将多个 HyperLogLog 合并为一个临时的 HyperLogLog 计算基数估算值。可以使用 HyperLogLog 只使用很少且恒定的内存来计算集合的不同元素个数。每个 HyperLogLog 只用 12K 加上键本身的几个字节。

(1) 语法格式:
```
PFCOUNT key [key ...]
```
(2) 返回值:
```
整数，返回指定 HyperLogLog 的基数估算值，如果多个 HyperLogLog 则返回并集的基数估算值。
```
(3) Example:
```
127.0.0.1:6379> PFADD hll foo bar zap
(integer) 1
127.0.0.1:6379> PFADD hll zap zap zap
(integer) 0
127.0.0.1:6379> PFADD hll foo bar
(integer) 0
127.0.0.1:6379> PFCOUNT hll
(integer) 3
127.0.0.1:6379> PFADD some-other-hll 1 2 3
(integer) 1
127.0.0.1:6379> PFCOUNT some-other-hll
(integer) 3
127.0.0.1:6379> PFCOUNT hll some-other-hll
(integer) 6
```
(4) 限制:

HyperLogLog 返回的结果并不精确，错误率大概在 0.81% 左右。

> 该命令会修改 HyperLogLog，会使用8个字节来存储上一次计算的基数。所以，从技术角度来讲，`PFCOUNT` 是一个写命令。

(5) 性能问题

即使理论上处理一个密集型 HyperLogLog 需要花费较长时间，但是当只指定一个键时，`PFCOUNT` 命令仍然具有很高的性能。这是因为 `PFCOUNT` 会缓存上一次计算的基数，并且这个基数并不会一直变动，因为 `PFADD` 命令大多数情况下不会更新寄存器。所以才可以达到每秒上百次请求的效果。

当使用 `PFCOUNT` 命令处理多个键时，会对 HyperLogLog 进行合并操作，这一步非常耗时，更重要的是通过计算出来的并集的基数是不能缓存的。因此当使用多个键时，`PFCOUNT` 可能需要花费一些时间(毫秒数量级)，因此不应过多使用。

> 我们应该记住，该命令的单键和多键执行语义上是不同的并且具有不同的性能。

#### 3.3 PFMERGE

> 最早可用版本：2.8.9。时间复杂度：O(N)，N是要合并的HyperLogLog的数量。

`PFMERGE` 命令将多个 HyperLogLog 合并为一个 HyperLogLog。合并后的 HyperLogLog 的基数估算值是通过对所有给定 HyperLogLog 进行并集计算得出的。计算完的结果保存到指定的键中。

语法格式:
```
PFMERGE destkey sourcekey [sourcekey ...]
```
返回值:
```
返回 OK。
```
Example:
```
127.0.0.1:6379> PFADD hll1 foo bar zap a
(integer) 1
127.0.0.1:6379> PFADD hll2 a b c foo
(integer) 1
127.0.0.1:6379> PFMERGE hll3 hll1 hll2
OK
127.0.0.1:6379> PFCOUNT hll3
(integer) 6
```

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)
