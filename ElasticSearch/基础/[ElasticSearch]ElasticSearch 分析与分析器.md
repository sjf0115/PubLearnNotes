---
layout: post
author: sjf0115
title: ElasticSearch 分析与分析器
date: 2016-10-19 19:15:17
tags:
  - ElasticSearch
  - ElasticSearch 基础

categories: ElasticSearch
permalink: elasticsearch-how-to-use-analysis-and-analyser
---

### 1. 分析过程

分析(analysis)过程如下：
- 首先，将一个文本块划分为适用于倒排索引的独立的词条(term)
- 然后对这些词进行标准化，提高它们的'可搜索性'或'查全率'
上面的工作就是由分析器(Analyzer)来完成的。

### 2. 分析器组成

分析器（Analyzer） 一般由三部分构成，字符过滤器（Character Filters）、分词器（Tokenizers）、分词过滤器（Token filters）。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ElasticSearch/elasticsearch-how-to-use-analysis-and-analyser-1.png?raw=true)

#### 2.1 字符过滤器

首先字符串要按顺序依次经过几个字符过滤器(Character Filter)。它们的任务就是在分词前对字符串进行一次处理。字符过滤器能够剔除HTML标记，或者转换 `&` 为 `and`。

#### 2.2 分词器

下一步，字符串经过分词器(Tokenizers)被分词成独立的词条(term)。一个简单的分词器可以根据空格或逗号将文本分成词条。

#### 2.3 分词过滤器

最后，每个词条都要按顺序依次经过几个分词过滤器(Token Filters)。这个过程可能会改变词条（例如，将 `Quick` 转为小写），删除词条（例如，删除像 `a`、`and`、`the` 这样的停用词），或者增加词条（例如，像 `jump` 和 `leap` 这样的同义词）。

Elasticsearch提供很多开箱即用的字符过滤器，分词器和分词过滤器。这些可以组合起来创建自定义的分析器以应对不同的需求。

### 3. 内建分析器

不过，Elasticsearch还内置了一些分析器，可以直接使用它们。下面我们列出了几个比较重要的分析器，并演示它们有啥差异。我们看看每个分析器会从下面的字符串得到哪些词条：
```
Set the shape to semi-transparent by calling set_trans(5)
```

#### 3.1  标准分析器（Standard analyzer）

标准分析器是 Elasticsearch 默认使用的分析器。对于文本分析，它对于任何语言都是最佳选择（对于任何一个国家的语言，这个分析器基本够用）。它根据[Unicode Consortium](http://www.unicode.org/reports/tr29/)定义的单词边界(word boundaries)来切分文本，然后去掉大部分标点符号。最后，把所有词条转为小写。

```java
String standardAnalyzer = "standard";
String value = "Set the shape to semi-transparent by calling set_trans(5)";
AnalyzeAPI.analyzeByAnalyzer(client, standardAnalyzer, value);
```
产生的结果为：
```
set, the, shape, to, semi, transparent, by, calling, set_trans, 5
```
> AnalyzeAPI.analyzeByAnalyzer 自定义的一个工具方法，具体实现请看下面介绍。

#### 3.2 简单分析器（Simple analyzer）

简单分析器将根据不是字母的任何字符来切分文本，然后将每个词条转为小写。
```java
String simpleAnalyzer = "simple";
String value = "Set the shape to semi-transparent by calling set_trans(5)";
AnalyzeAPI.analyzeByAnalyzer(client, simpleAnalyzer, value);
```

产生的结果为：
```
set, the, shape, to, semi, transparent, by, calling, set, trans
```
#### 3.3 空格分析器（Whitespace analyzer）

空格分析器根据空格来切分文本。不会转换为小写。
```java
String whitespaceAnalyzer = "whitespace";
String value = "Set the shape to semi-transparent by calling set_trans(5)";
AnalyzeAPI.analyzeByAnalyzer(client, whitespaceAnalyzer, value);
```

产生结果为：
```
Set, the, shape, to, semi-transparent, by, calling, set_trans(5)
```

#### 3.4 语言分析器（Language analyzers）

特定语言分析器适用于很多[语言](https://www.elastic.co/guide/en/elasticsearch/reference/2.4/analysis-lang-analyzer.html)。它们能够考虑到特定语言的特点。例如，`english` 分析器自带一套英语停用词库（像 `and` 或 `the` 这些与语义无关的通用词），分析器将会这些词移除。由于理解英语语法的规则，这个分词器可以提取英语单词的词干。

以英语分析器举例：
```java
String englishAnalyzer = "english";
String value = "Set the shape to semi-transparent by calling set_trans(5)";
AnalyzeAPI.analyzeByAnalyzer(client, englishAnalyzer, value);
```

产生结果为：
```
set, shape, semi, transpar, call, set_tran, 5
```
注意 `transparent`、`calling` 和 `set_trans` 是如何转为词干的。

### 4. 什么时候使用分析器

当我们索引一个文档时，全文字段会被分析为单独的词条来创建倒排索引。不过，当我们在全文字段搜索(search)时，我们要让查询字符串经过同样的分析流程处理，以确保这些词条在索引中存在。理解每个字段是如何定义的，这样才可以让它们做正确的事：
- 当你查询全文(full text)字段，查询将使用相同的分析器来分析查询字符串，以产生正确的词条列表。
- 当你查询一个确切值(exact value)字段，查询将不分析查询字符串，但是你可以自己指定。

### 5. 测试分析器

尤其当你是Elasticsearch新手时，对于如何分词以及存储到索引中理解起来比较困难。为了更好的理解如何进行，你可以使用analyze API来查看文本是如何被分析的。在查询中指定要使用的分析器，以及被分析的文本。

```java
// 使用分词器进行词条分析
public static void analyzeByAnalyzer(Client client, String analyzer, String value){
    IndicesAdminClient indicesAdminClient = client.admin().indices();
    AnalyzeRequestBuilder analyzeRequestBuilder = indicesAdminClient.prepareAnalyze(value);
    analyzeRequestBuilder.setAnalyzer(analyzer);
    AnalyzeResponse response = analyzeRequestBuilder.get();
    // 打印响应信息
    List<AnalyzeResponse.AnalyzeToken> tokenList = response.getTokens();
    for(AnalyzeResponse.AnalyzeToken token : tokenList){
        logger.info("-------- analyzeIndex type {}", token.getType());
        logger.info("-------- analyzeIndex term {}", token.getTerm());
        logger.info("-------- analyzeIndex position {}", token.getPosition());
        logger.info("-------- analyzeIndex startOffSet {}", token.getStartOffset());
        logger.info("-------- analyzeIndex endOffSet {}", token.getEndOffset());
        logger.info("----------------------------------");
    }
}
```
或者使用如下方式：
```json
GET /_analyze
{
  "analyzer": "standard",
  "text": "Text to analyze"
}
```
结果中每个元素代表一个单独的词条：
```json
{
   "tokens": [
      {
         "token":        "text",
         "start_offset": 0,
         "end_offset":   4,
         "type":         "<ALPHANUM>",
         "position":     1
      },
      {
         "token":        "to",
         "start_offset": 5,
         "end_offset":   7,
         "type":         "<ALPHANUM>",
         "position":     2
      },
      {
         "token":        "analyze",
         "start_offset": 8,
         "end_offset":   15,
         "type":         "<ALPHANUM>",
         "position":     3
      }
   ]
}
```
`token` 是实际存储到索引中的词条。 `position` 指明词条在原始文本中出现的位置。 `start_offset` 和 `end_offset` 指明字符在原始字符串中的位置。

### 6. 指定分析器

当Elasticsearch在你的文档中检测到一个新的字符串字段，自动设置它为全文string字段并用 `standard` 分析器分析。

你不希望总是这样。也许你想使用一个更适合这个数据的语言分析器。或者，你只想把字符串字段当作一个普通的字段，不做任何分析，只存储确切值，就像字符串类型的用户ID或者内部状态字段或者标签。为了达到这种效果，必须手动指定这些域的映射。

```java
XContentBuilder mappingBuilder;
try {
    mappingBuilder = XContentFactory.jsonBuilder()
            .startObject()
            .startObject(type)
            .startObject("properties")
            .startObject("club").field("type", "string").field("index", "analyzed").field("analyzer", "english").endObject()
            .endObject()
            .endObject()
            .endObject();
} catch (Exception e) {
    //...
}
```

> ElasticSearch版本：5.4

原文：https://www.elastic.co/guide/en/elasticsearch/guide/2.x/analysis-intro.html#analysis-intro
