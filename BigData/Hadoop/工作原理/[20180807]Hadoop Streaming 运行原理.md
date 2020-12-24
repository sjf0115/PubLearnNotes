---
layout: post
author: sjf0115
title: Hadoop Streaming 运行机制
date: 2018-08-07 20:29:01
tags:
  - Hadoop
  - Hadoop 内部原理

categories: Hadoop
permalink: hadoop-internal-anatomy-of-hadoop-streaming
---

Hadoop 提供了 MapReduce 的 API，允许你使用非 Java 的其他语言来写自己的 Map 和 Reduce 函数。Hadoop Streaming 使用 Unix 标准流作为 Hadoop 和应用程序之间的接口，所以我们可以使用任何编程语言通过标准输入/输出来写 MapReduce 程序。允许用户将任何可执行文件或者脚本作为 Map 和 Reduce 函数，这大大提高了程序员的开发效率。

Streaming 天生适合用于文本处理。Map 的输入数据通过标准输入流传递给 Map 函数，并且是一行一行的传输，最后将结果行写入到标准输出中。Map 输出的键值对是一个制表符分割的行，Reduce 函数的输入格式与之相同（通过制表符分割的键值对）并通过标准输入流进行传输。Reduce 函数从标准输入流中读取输入行，该输入已由 Hadoop 框架根据键排过序，最后将结果写入标准输出。

### 1. Example

```python
#! /usr/bin/env python

import re
import sys

for line in sys.stdin:
    params = line.strip().split(" ")
    for word in params:
        value = 1
        print( "%s\t%d" % (word, value) )
```
程序通过程序块读取 STDIN 中的每一行来迭代执行标准输入中的每一行。该程序块将输入的每一行根据空格拆分为多个单词。将单词以及`1`以制表符隔开标准输出。

> 值得一提的是 Streaming 和 Java MapReduce API 之间的设计差异。Java MapReduce API 控制的 Map 函数一次只处理一条记录。针对输入数据中的每一条记录，该框架需要调用 Mapper 的 Map 方法来处理。然而在 Streaming 中，Map 程序可以自己决定如何处理输入数据，例如，它可以轻松读取并同时处理若干行，因为它受读操作的控制。

这个脚本只能在标准输入和输出上运行，所以最简单的方式是通过 Unix 管道进行测试，而不使用 Hadoop：
```
[sjf0115@ying ~]$ cat word_count.txt | /home/sjf0115/tools/word_count_map.py
I       1
am      1
a       1
boy     1
I       1
come    1
from    1
China   1
China   1
is      1
a       1
very    1
good    1
country 1
Welcome 1
to      1
China   1
```
下面看一下 Reduce 函数:
```python
#! /usr/bin/env python

import re
import sys

result = 0
last_key=None
for line in sys.stdin:
    (key, value) = line.strip().split("\t", 1)
    count = int(value)
    if last_key and last_key == key:
        result += count
    else:
        if last_key:
            print( "%s\t%d" % (last_key, result) )
        result = count
        last_key = key
if last_key == key:
    print( "%s\t%d" % (last_key, result) )
```
同样，程序遍历标准输入中的行，但在我们处理每个键值对时，我们要存储几个状态 （`result`, `last_key`），记录每个单词对应的出现次数。

Hadoop 命令不支持 Streaming，因此，我们需要在指定 Streaming JAR 文件流与 jar 选项时指定。Streaming 程序的选项指定了输入和输出路径以及 Map 和 Reduce 脚本，如下所示：
```
sudo -usjf0115 hadoop jar hadoop-streaming-2.2.0.jar \
  -Dmapred.job.queue.name=sjf0115 \
  -files word_count_map.py,word_count_reduce.py \
  -input tmp/data_group/example/input/word_count \
  -output tmp/data_group/example/output/word_count \
  -mapper word_count_map.py \
  -reducer word_count_reduce.py
```
输出结果如下：
```
China   3
I       2
Welcome 1
a       2
am      1
boy     1
come    1
country 1
from    1
good    1
is      1
to      1
very    1
```


### 2. 运行机制

Streaming 运行特殊的 Map 任务和 Reduce 任务，目的是运行用户提供的可执行程序，并与之通信，如下图所示：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hadoop/hadoop-internal-anatomy-of-hadoop-streaming-1.png?raw=true)

Streaming 任务使用标准输入和输出流与进程（可以使用任何语言编写）进行通信。在任务执行过程中，Java 进程都会把输入键值对传递给外部的进程，后者通过用户定义的 Map 函数和 Reduce 函数来执行它并把输出键值对传回 Java 进程。从节点管理器的角度看，就像其子进程自己在运行 Map 或 Reduce 代码一样。

原文：Hadoop权威指南

http://www.glennklockwood.com/data-intensive/hadoop/streaming.html
