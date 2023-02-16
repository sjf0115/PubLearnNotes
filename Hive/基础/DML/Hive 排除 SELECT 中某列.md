---
layout: post
author: sjf0115
title: Hive 排除 SELECT 中某列
date: 2019-08-27 21:48:09
tags:
  - Hive

categories: Hive
permalink: exclude-columns-from-select-query-in-hive
---

### 1. 简介

在 Hive 表中可能存在很多列，也有可能就存在几列。如果我们想要表中所有列，毫无疑问我们可以使用 `SELECT *`。但在某些情况下，我们可能拥有 100 多列，并且我们只不需要其中几列。在这种情况下，之前都是手动的添加 `SELECT` 查询中的所有列名。由于列数很多，比较啰嗦。因此，我们希望能在 Hive 中从 SELECT 查询中排除某些列。

### 2. 方案

我们可以使用正则表达式来排除某些列。如果要使用正则表达式，需要将属性 `hive.support.quoted.identifiers` 设置为 `none`。

下面是我们的样本数据。此表中一共有100多列，如下图所示(只展示了8列):

![](https://github.com/sjf0115/ImageBucket/blob/main/Hive/exclude-columns-from-select-query-in-hive.png?raw=true)

如果我们不想要 `event_ts` 这一列。我们会使用如下查询来排除这一列:
```sql
SELECT `(event_ts)?+.+` FROM <table>;
```
上面语句等价于:
```sql
SELECT user_id, event_tm, os, os_version, app_version, ..., prov, city
FROM <table>;
```
如果我们不想要 `event_ts` 和 `event_tm` 两列。我们会使用如下查询来排除这两列:
```sql
SELECT `(event_ts|event_tm)?+.+` FROM <table>;
```
如果我们要排除多列，使用 `|` 分割。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)
