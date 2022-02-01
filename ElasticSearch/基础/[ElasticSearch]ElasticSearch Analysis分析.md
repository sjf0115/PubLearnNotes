---
layout: post
author: sjf0115
title: ElasticSearch Analysis分析
date: 2016-10-20 19:15:17
tags:
  - ElasticSearch
  - ElasticSearch 基础

categories: ElasticSearch
permalink: elasticsearch-how-to-use-analysis
---

分析(analysis)是将文本（如任何电子邮件的正文）转换为添加到倒排索引中进行搜索的`tokens`或`terms`的过程。分析由 `analyzer` 分析器执行，分析器可以是内置分析器或者每个索引定制的自定义分析器。

### 1. 索引时分析(Index time analysis)

例如，在索引时，内置的英文分析器将会对下面句子进行转换：
```
"The QUICK brown foxes jumped over the lazy dog!"
```
转换为添加到倒排索引中的词条如下：
```
[ quick, brown, fox, jump, over, lazi, dog ]
```

#### 1.1 指定索引时分析器

映射中的每个`text`字段都可以指定自己的分析器：
```json
curl -XPUT 'localhost:9200/my_index?pretty' -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "my_type": {
      "properties": {
        "title": {
          "type":     "text",
          "analyzer": "standard"
        }
      }
    }
  }
}
'
```
在索引时，如果没有指定分析器，则会在索引设置中查找一个叫做`default`的分析器。如果没有找到，默认使用标准分析器　`standard analyzer`。

### 2. 搜索时分析(Search time analysis)

同样的分析过程也可以应用于进行全文检索搜索(例如 `match query` 匹配查询)时，将查询字符串的文本转换为与存储在倒排索引中相同形式的词条。

例如，用户可能搜索：
```
"a quick fox"
```
这将由相同的英语分析器分析为以下词条(上面索引时举例使用的是英语分析器，如果不使用相同的分析器，有可能搜不到正确的结果)：
```
[ quick, fox ]
```

即使在查询字符串中使用的确切单词不会出现在原始存储文本（`quick` vs `QUICK`，`fox` vs `foxes`）中，查询字符串中的词条也能够完全匹配到倒排索引中的词条，因为我们已将相同的分析器应用于文本和查询字符串上，这意味着此查询将与我们的示例文档匹配。

#### 2.1 指定搜索时分析器

通常情况下，在索引时和搜索时应该使用相同的分析器，全文查询(例如匹配查询 `match query`)将根据映射来查找用于每个字段的分析器。

用于搜索特定字段的分析器由一下流程决定：
- 在查询中指定的分析器。
- `search_analyzer` 映射参数。
- `analyzer` 映射参数。
- 索引设置中的`default_search`分析器。
- 索引设置中的`default`分析器。
- `standard` 标准分析器。


> ElasticSearch版本 5.4

原文：https://www.elastic.co/guide/en/elasticsearch/reference/5.4/analysis.html
