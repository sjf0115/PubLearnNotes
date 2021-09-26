---
layout: post
author: sjf0115
title: 了解HBase与BigTable
date: 2019-10-12 19:07:07
tags:
  - HBase

categories: HBase
permalink: understanding-hbase-and-bigtable
---

在学习HBase（Google BigTable 的开源实现）的时候，我们面临的最为困难的地方就是需要你重构你的思路来理解 BigTable 的概念。

非常不幸的是，在 BigTable 和 HBase 中都出现了 `table` 和 `base` 这两个概念，这很容易让我们与RDBMS（关系型数据库管理系统）产生联想。

本文旨在从概念的角度描述这些分布式数据存储系统。阅读完这篇文章后，我们应该能够更明智的做出决定，即何时使用 HBase 以及何时使用'传统'数据库。

### 1. 术语

幸运的是，Google 的 BigTable Paper 清楚地说明了 BigTable 的真正含义。这是'数据模型'部分的第一句话：
```
Bigtable 是一个稀疏的，分布式的，持久化的多维有序 Map。
```
> A Bigtable is a sparse, distributed, persistent multidimensional sorted map.

论文继续解释到：
```
Map 由行键、列以及时间戳进行索引，在 Map 中的每个值都是无解释的字节数组。
```
> The map is indexed by a row key, column key, and a timestamp; each value in the map is an uninterpreted array of bytes.


在 Hadoop wiki的 HBase Architecture 页面中指出：
```
HBase 使用的数据模型与 Bigtable 非常相似。用户在标记表中存储数据行，数据行中有一个有序的key和任意数量的列。这张表的存储是稀疏的，所以如果用户喜欢的话，甚至可以在同一张表的每行中疯狂的存储差异巨大的列。
```
> HBase uses a data model very similar to that of Bigtable. Users store data rows in labelled tables. A data row has a sortable key and an arbitrary number of columns. The table is stored sparsely, so that rows in the same table can have crazily-varying columns, if the user likes.

上面提到的这些概念似乎很神秘，但其实如果我们把它分解一下就会很好理解。下面我们就按照顺序讨论一下几个主题：Map、持久化、分布式、有序、多维和稀疏。

与其尝试直接描绘一个完整的系统，不如逐渐建立起一个零散的思想框架，以简化它...

### 2. Map

HBase/BigTable 的核心是 Map。根据我们不同编程语言背景，我们可能更熟悉编程语言关联的术语：数组（PHP），字典（Python），哈希（Ruby）或对象（JavaScript）。从维基百科文章来看，Map 是'由一组键和一组值组成的抽象数据类型，其中每个键都与一个值相关联'。

使用 JavaScript 对象表示，这是一个简单的 Map 示例，其中所有值都只是字符串：
```json
{
  "zzzzz" : "woot",
  "xyz" : "hello",
  "aaaab" : "world",
  "1" : "x",
  "aaaaa" : "y"
}
```
### 3. 持久化

持久化仅表示我们创建或访问的程序运行完成后，我们保留在这个特殊 Map 中的数据会'持久化'。概念上与其他类型的持久化存储（例如文件系统上的文件）没有什么不同。

### 4. 分布式

HBase 和 BigTable 建立在分布式文件系统上，因此底层文件存储分布在不同的计算机上。HBase 使用的是 Hadoop 的分布式文件系统（HDFS）或 Amazon 的简单存储服务（S3），而 BigTable 使用的是 Google 文件系统（GFS）。

数据以一种类似于 RAID 系统的方式在多个参与节点中进行复制。在这里，我们并不在乎使用哪种分布式文件系统来实现。重要的是我们需要知道它是分布式的，它提供了一层保护，以防止集群中的某个节点发生故障。

### 5. 有序

与大多数 Map 实现不同，在 HBase/BigTable 中，键/值对严格按照字母顺序排序。也就是说，键 `aaaaa` 的行应紧邻键 `aaaab` 的行，并距离键 `zzzzz` 的行非常远。排序后的版本如下所示：
```json
{
  "1" : "x",
  "aaaaa" : "y",
  "aaaab" : "world",
  "xyz" : "hello",
  "zzzzz" : "woot"
}
```
​由于这些系统常常非常巨大而且是分布式的，有序功能是非常重要的。相似的行（例如键）紧密相邻，这样当你必须对表进行扫描时，你最感兴趣的条目之间彼此相邻。

行键的设计非常重要。例如，我们有一个表，行键为域名。我们最好以域名的倒序形式作为行键（使用 `com.jimbojw.www` 而不是 `www.jimbojw.com`），这样相关子域名的行就会位于父域名行的附近。这样域名 `mail.jimbojw.com` 的行会紧邻 `www.jimbojw.com` 的行，而不会是 `mail.xyz.com`。

需要注意的是，术语'sorted'在 HBase/BigTable 中并不意味着值是有序的。除了行键之外，没有其他任何自动索引。

### 6. 多维

到现在为止，我们还没有提到 `column` 的任何概念，而是将 `table` 视为概念上的常规 Hash/Map。`column` 这个词也跟 `table` 和`base` 的概念一样，承载了太多的 RDBMS 的情感在内。我们可以把它理解为一个多维 Map，即 Map 中嵌套 Map。在 JSON 示例中增加一维：
```json
{
  "1" : {
    "A" : "x",
    "B" : "z"
  },
  "aaaaa" : {
    "A" : "y",
    "B" : "w"
  },
  "aaaab" : {
    "A" : "world",
    "B" : "ocean"
  },
  "xyz" : {
    "A" : "hello",
    "B" : "there"
  },
  "zzzzz" : {
    "A" : "woot",
    "B" : "1337"
  }
}
```
在上面的示例中，我们会注意到，每个键都指向具有两个键的 Map：`A`和 `B`。从这里开始，我们将顶级键/Map对称为行(`Row`)。同样，在 BigTable/HBase 命名中，`A`和 `B` 映射称为列族。表的列族是在创建表时指定的，以后很难或无法修改。添加新的列族代价可能也很昂贵，因此最好预先指定所有需要的列族。

幸运的是，列族可以具有任意数量的列，用限定符(`Qualifier`)或标签(`Label`)列表示。下面是我们的 JSON 示例的子集，这次是添加列限定符维度：
```json
{
  // ...
  "aaaaa" : {
    "A" : {
      "foo" : "y",
      "bar" : "d"
    },
    "B" : {
      "" : "w"
    }
  },
  "aaaab" : {
    "A" : {
      "foo" : "world",
      "bar" : "domination"
    },
    "B" : {
      "" : "ocean"
    }
  },
  // ...
}
```
> 在上面两行中，`A` 列族有两列：`foo` 和 `bar`，而 `B` 列族只有一列，其限定符为空字符串。

向 HBase/BigTable 查询数据时，我们必须以 `<family>:<qualifier>` 的形式提供完整的列名。因此，上例中的三列为：`A:foo`，`A:bar` 和`B:`。

尽管列族是静态的，但列不是。考虑以下扩展行：
```json
{
  // ...
  "zzzzz" : {
    "A" : {
      "catch_phrase" : "woot",
    }
  }
}
```
在这个示例下，`zzzzz` 行只有一列 `A:catch_phrase`。由于每一行都可以有任意数量的不同列，因此没有内置的方法来查询所有行中所有列。要获取该信息，我们必须进行全表扫描。但是，我们可以查询所有列族，因为它们是不变的。

HBase/BigTable 中最后一个维度是时间。我们可以使用整数时间戳（自纪元以来的秒数）或我们选择自定义整数来对数据进行版本控制。客户端可以在插入数据时指定时间戳。

使用任意整数时间戳示例：
```json
{
  // ...
  "aaaaa" : {
    "A" : {
      "foo" : {
        15 : "y",
        4 : "m"
      },
      "bar" : {
        15 : "d",
      }
    },
    "B" : {
      "" : {
        6 : "w"
        3 : "o"
        1 : "w"
      }
    }
  },
  // ...
}
```
每个列族在保存给定单元格的版本数量方面都有其自己的规则（一个单元格通过其行键/列对来标识）。在大多数情况下，应用程序只是简单地查询给定单元格的数据，无需指定时间戳。在这种常见情况下，HBase/BigTable 将返回最新版本（时间戳最高的版本）的数据。如果应用程序查询给定时间戳版本的数据，HBase 将返回时间戳小于或等于我们提供的时间戳的单元格数据。

例如，查询 `aaaaa/A:foo` (行/列)单元格数据将返回 `y`，而查询 `aaaaa/A:foo/10` (行/列/时间戳)单元格数据将返回 `m`。查询 `aaaaa/A:foo/2` (行/列/时间戳)单元格数据将返回空。

### 7. 稀疏

最后一个关键字是稀疏。如前所述，给定的行在每个列族中可以有任意数量的列，或者根本没有列。稀疏的另一种类型是基于行的间隙，这仅意味着键之间可能存在间隙。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

原文：[Understanding HBase and BigTable](https://dzone.com/articles/understanding-HBase-and-bigtab)
