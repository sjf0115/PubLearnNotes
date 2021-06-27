---
layout: post
author: sjf0115
title: ElasticSearch 索引
date: 2016-10-18 19:15:17
tags:
  - ElasticSearch
  - ElasticSearch 基础

categories: ElasticSearch
permalink: elasticsearch-how-to-indexing
---

### 1. 背景

假设我们刚好在一家工作，这时人力资源部门出于某种目的需要让我们创建一个员工目录，它有以下不同的需求：
- 数据能够包含多个值的标签、数字和纯文本。
- 检索任何员工的所有信息。
- 支持结构化搜索，例如查找30岁以上的员工。
- 支持简单的全文搜索和更复杂的短语(phrase)搜索。
- 高亮搜索结果中的关键字。
- 能够利用图表管理分析这些数据。

### 2. 索引员工文档

我们首先要做的是存储员工数据，每个文档代表一个员工。在Elasticsearch中存储数据的行为就叫做索引(indexing)，不过在索引之前，我们需要明确数据应该存储在哪里。

在Elasticsearch中，文档归属于一种 type (类型)，而这些 type 存在于 index (索引)中，我们可以画一个简单的对比图来类比传统关系型数据库：
```
Relational DB -> Databases -> Tables -> Rows -> Columns
Elasticsearch -> Indices   -> Types  -> Documents -> Fields
```
Elasticsearch集群可以包含多个 index （数据库），每一个 index 可以包含多个 types （表），每一个 type 又可以包含多个文档（行），然后每个文档包含多个字段（列）。


你可能已经注意到索引(index)这个词在Elasticsearch中有着不同的含义，所以有必要在此做一下区分:
- 索引（名词）：如上文所述，一个索引(index)就像是传统关系数据库中的数据库，它是相关文档存储的地方，index的复数是indices 或indexes。
- 索引（动词）：索引一个文档，表示把一个文档存储到索引（名词）里，以便它可以被检索或者查询。这很像SQL中的INSERT关键字，差别是，如果文档已经存在，新的文档将覆盖旧的文档。
- 倒排索引：传统数据库为特定列增加一个索引，例如B-Tree索引来加速检索。Elasticsearch和Lucene使用一种叫做倒排索引(inverted index)的数据结构来达到相同目的。

默认情况下，文档中的所有字段都会被索引（拥有一个倒排索引），只有这样他们才是可被搜索的。

### 3. 创建

创建员工目录，我们将进行如下操作：
- 为每个员工的文档建立索引，每个文档包含了相应员工的所有信息（每个员工一个文档）。
- 每个文档的 type 为 employee。
- employee 归属的索引为 company。
- company 存储在Elasticsearch集群中。

实际上这些都是很容易的（尽管看起来有许多步骤）。我们能通过一个命令执行完成的操作：
```json
curl -XPUT 'localhost:9200/company/employee/1'  -d '
{
    "first_name" : "John",
    "last_name" :  "Smith",
    "age" :        25,
    "about" :      "I love to go rock climbing",
    "interests": [ "sports", "music" ]
}'
```
输出信息：
```json
{
  "_index": "company",
  "_type": "employee",
  "_id": "1",
  "_version": 1,
  "_shards": {
    "total": 2,
    "successful": 1,
    "failed": 0
  },
  "created": true
}
```
我们看到路径: `/company/employee/1` 包含三部分信息：

名字|说明
---|---
company|索引名
employee|类型名
1|员工的ID

请求JSON实体（文档），包含了这个员工的所有信息。他的名字叫“John Smith”，25岁，喜欢攀岩。

让我们比较舒服的是它不需要你做额外的管理操作，比如创建索引或者定义每个字段的数据类型。我们能够直接索引文档，Elasticsearch已经内置所有的缺省设置，所有管理操作都是透明的。

接下来，让我们在目录中加入更多员工信息：
```json
curl -XPUT 'localhost:9200/company/employee/2'  -d '
{
    "first_name" : "li",
    "last_name" :  "chen",
    "age" :        29,
    "about" :      "I love to sing",
    "interests": [ "eat", "music" ]
}';
curl -XPUT 'localhost:9200/company/employee/3'  -d '
{
    "first_name" : "gao",
    "last_name" :  "lin",
    "age" :        22,
    "about" :      "no no no ",
    "interests": [ "eat", "footbal" ]
}';
curl -XPUT 'localhost:9200/company/employee/4'  -d '
{
    "first_name" : "li",
    "last_name" :  "yuan",
    "age" :        19,
    "about" :      "no haha",
    "interests": [ "basketball", "music" ]
}';
curl -XPUT 'localhost:9200/company/employee/5'  -d '
{
    "first_name" : "li",
    "last_name" :  "yuan",
    "age" :        19,
    "about" :      "I like playing basketball ",
    "interests": [ "basketball", "music" ]
}';
curl -XPUT 'localhost:9200/company/employee/6'  -d '
{
    "first_name" : "li",
    "last_name" :  "yuan",
    "age" :        19,
    "about" :      "I like playing football ",
    "interests": [ "football", "music" ]
}';
```
