---
layout: post
author: sjf0115
title: SQL查询并不总是以SELECT开始
date: 2019-11-10 21:58:11
tags:
  - SQL

categories: SQL
permalink: sql-queries-dont-start-with-select
---

很多 SQL 查询确实以 SELECT 开始(本文仅涉及 SELECT 查询，而不涉及 INSERT 或其他内容)。不过，我在网上搜索 '是否可以对窗口函数返回的结果进行过滤' 这个问题，或者说可以在 WHERE、HAVING 或其他中过滤窗口函数的结果吗？最终我得出的结论是：窗口函数必须在 WHERE 和 GROUP BY 发生之后才能运行，所以答案是我们这样做。于是又引出了另一个问题：SQL 查询的执行顺序是什么样的？

直觉上这个问题应该很好回答，毕竟我自己已经至少写了 10000 个 SQL 查询了，其中还有一些是很复杂。但事实是，我仍然很难准确地说出它的执行顺序是什么样的。

### 1. SQL查询按此顺序发生

我研究了一下，执行顺序如下所示。SELECT 并不是第一个执行的，而是第五个。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/SQL/sql-queries-dont-start-with-select-1.jpeg?raw=true)

执行顺序如下：
- FROM/JOIN 以及所有 ON 表达式
- WHERE
- GROUP BY
- HAVING
- SELECT (包括窗口函数)
- ORDER BY
- LIMIT

### 2. 这张图可帮助我们回答以下问题

这张图与 SQL 查询语义相关，让我们可以推理出给定查询返回的内容，并回答如下问题：
- 可以在 GRROUP BY 之后使用 WHERE 吗？（不行，WHERE 是在 GROUP BY 之后使用！）
- 可以对窗口函数返回的结果进行过滤吗？（不行，窗口函数发生在 SELECT 语句中，而 SELECT 发生在 WHERE 和 GROUP BY 之后）
- 可以对 GROUP BY 里的东西进行 ORDER BY 吗？（可以，ORDER BY 基本在最后执行，所以可以对任何东西进行 ORDER BY）
- LIMIT 发生在什么时候？（发生在最后！）

实际上，数据库引擎并不一定按照这个顺序执行查询，因为为了使查询运行更快，实现了一系列优化。所以：
- 当我们只想了解哪些查询是合法的以及如何推理给定查询的返回结果时，可以参考上图。
- 当我们在推断查询性能或者包含索引的任何东西时，上图就不适用了。

### 3. 混合因素：列别名

Twitter上的有人指出，许多 SQL 可以使用如下语法实现：
```sql
SELECT CONCAT(first_name, ' ', last_name) AS full_name, count(*)
FROM table
GROUP BY full_name
```
上面的查询看起来 GROUP BY 发生在 SELECT 之后，因为 GROUP BY 引用了 SELECT 中的一个别名。实际上并不需要让 GROUP BY 发生在 SELECT 之后，因为数据库引擎可以将查询重写为：
```sql
SELECT CONCAT(first_name, ' ', last_name) AS full_name, count(*)
FROM table
GROUP BY CONCAT(first_name, ' ', last_name)
```
这样 GROUP BY 仍然会先执行。

我们的数据库引擎也会进行一系列的检查，以确保在运行查询之前，我们在 SELECT 和 GROUP BY 中输入的内容是合法的，因此在生成执行计划之前必须从整体上检查一下查询。

### 4. 查询可能不会按上述顺序运行

实际上，数据库引擎并不一定会按照 JOIN、WHERE、GROUP BY 的顺序来执行查询，因为它们会进行一系列优化，只要重新排序不会改变查询的结果，它们就会对命令进行重新排序以使查询运行得更快。

下面这个简单的示例说明了为什么需要以不同的顺序运行查询以使其快速运行：
```sql
SELECT *
FROM owners
LEFT JOIN cats
ON owners.id = cats.owner
WHERE cats.name = 'mr darcy'
```
> 按照上图执行顺序我们知道：FROM / LEFT JOIN / ON 会先执行，然后是 WHERE， 最后是 SELECT。

如果只需要查找名为'mr darcy'的猫，那就没必要对两张表的所有行进行左连接，先对猫名为 'mr darcy' 执行过滤会更快。在这种情况下，先执行过滤不会改变查询结果！

在实践中，数据库引擎还会有很多其他优化措施，这些优化措施可能会使它们以不同的顺序执行查询，因为我不是这方面的专家，所以在这不展开介绍。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

原文:[SQL queries don't start with SELECT](https://jvns.ca/blog/2019/10/03/sql-queries-don-t-start-with-select/)
