---
layout: post
author: sjf0115
title: ElasticSearch 内置分析器
date: 2016-10-21 20:15:17
tags:
  - ElasticSearch
  - ElasticSearch 基础

categories: ElasticSearch
permalink: elasticsearch-built-in-analyzer
---

### 1. 配置内置分析器

内置分析器可以直接使用，不需任何配置。然而，其中一些分析器支持可选配置来改变其行为。例如，标准分析器可以配置为支持停止词列表：
```json
curl -XPUT 'localhost:9200/my_index?pretty' -H 'Content-Type: application/json' -d'
{
  "settings": {
    "analysis": {
      "analyzer": {
        "std_english": {
          "type":      "standard",
          "stopwords": "_english_"
        }
      }
    }
  },
  "mappings": {
    "my_type": {
      "properties": {
        "my_text": {
          "type":     "text",
          "analyzer": "standard",
          "fields": {
            "english": {
              "type":     "text",
              "analyzer": "std_english"
            }
          }
        }
      }
    }
  }
}
'
curl -XPOST 'localhost:9200/my_index/_analyze?pretty' -H 'Content-Type: application/json' -d'
{
  "field": "my_text",
  "text": "The old brown cow"
}
'
curl -XPOST 'localhost:9200/my_index/_analyze?pretty' -H 'Content-Type: application/json' -d'
{
  "field": "my_text.english",
  "text": "The old brown cow"
}
'
```

我们基于标准分析器定义一个`std_english`分析器，同时配置删除预定义的英文词汇表:
```json
"analyzer": {
    "std_english": {
        "type":"standard",
        "stopwords": "_english_"
    }
}
```
`my_text` 字段直接使用标准分析器，没有任何配置：
```json
"my_text": {
    "type": "text",
    "analyzer": "standard"
}
```
因此，这个字段不会删除停用词。所得的词条为：
```
[ the, old, brown, cow ]
```

`my_text.english` 字段使用`std_english`分析器：
```json
"my_text": {
    "type": "text",
    "analyzer": "standard",
    "fields": {
        "english": {
            "type":"text",
            "analyzer": "std_english"
        }
    }
}
```
因此会删除停用词。得出的结果是:
```
[ old, brown, cow ]
```

### 2. 标准分析器(Standard Analyzer)

如果没有指定分析器，默认使用 `standard` 分析器。对于文本分析，它对于任何语言都是最佳选择（对于任何一个国家的语言，这个分析器基本够用）。它根据[Unicode Consortium](http://www.unicode.org/reports/tr29/)定义的单词边界(word boundaries)来切分文本，然后去掉大部分标点符号。最后，把所有词转为小写。

#### 2.1 定义

`standard` 分析器包含一下内容：

(1) 分词器(Tokenizer) ：`Standard Tokenizer`

(2) 分词过滤器(Token Filters) ：
- `Standard Token Filter`
- `Lower Case Token Filter`
- `top Token Filter (默认情况下禁用)`

#### 2.2 输出Example

```json
curl -XPOST 'localhost:9200/_analyze?pretty' -H 'Content-Type: application/json' -d'
{
  "analyzer": "standard",
  "text": "The 2 QUICK Brown-Foxes jumped over the lazy dog's bone."
}
'
```

Java版本:
```java
String text = "The 2 QUICK Brown-Foxes jumped over the lazy dog's bone.";
String analyzer = "standard";
IndicesAdminClient indicesAdminClient = client.admin().indices();
AnalyzeRequestBuilder analyzeRequestBuilder = indicesAdminClient.prepareAnalyze(text);
analyzeRequestBuilder.setAnalyzer(analyzer);
AnalyzeResponse response = analyzeRequestBuilder.get();
```
上述句子将产生以下词条：
```
[ the, 2, quick, brown, foxes, jumped, over, the, lazy, dog's, bone ]
```

#### 2.3 配置

`standard` 分析器接受以下参数：

参数 | 说明
---|---
max_token_length | 最大token长度。如果一个token超过此长度，则以`max_token_length`进行分割。默认为255。
stopwords | 预定义的停用词列表，如`_english_`或包含一组停用词的数组。 默认为`\ _none_`。
stopwords_path |包含停用词文件的路径。

有关停用词配置的更多信息，请参阅[Stop Token Filter](https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-stop-tokenfilter.html)。

#### 2.4 配置Example

在此示例中，我们将 `standard` 分析器配置`max_token_length`为5（用于演示目的），并使用预定义的英文停用词列表：
```json
curl -XPUT 'localhost:9200/my_index?pretty' -H 'Content-Type: application/json' -d'
{
  "settings": {
    "analysis": {
      "analyzer": {
        "my_english_analyzer": {
          "type": "standard",
          "max_token_length": 5,
          "stopwords": "_english_"
        }
      }
    }
  }
}
'
curl -XPOST 'localhost:9200/my_index/_analyze?pretty' -H 'Content-Type: application/json' -d'
{
  "analyzer": "my_english_analyzer",
  "text": "The 2 QUICK Brown-Foxes jumped over the lazy dog's bone."
}
'
```
上述示例产生以下词条：
```
[ 2, quick, brown, foxes, jumpe, d, over, lazy, dog's, bone ]
```

### 3. 简单分析器(Simple Analyzer)

只要遇到不是字母的字符，简单的分析器将文本进行切割分解为`terms`。 所有`terms`都是小写。

#### 3.1 定义

分词器(Tokenizer) : `Lower Case Tokenizer`

#### 3.2 输出Example

```json
curl -XPOST 'localhost:9200/_analyze?pretty' -H 'Content-Type: application/json' -d'
{
  "analyzer": "simple",
  "text": "The 2 QUICK Brown-Foxes jumped over the lazy dog's bone."
}
'
```
以上示例产生如下词条：
```
[ the, quick, brown, foxes, jumped, over, the, lazy, dog, s, bone ]
```
#### 3.3 配置

无

### 4. 空格分析器（Whitespace analyzer）

空白分析器在遇到空格字符时将文本切分成词条。

#### 4.1 定义

分析器(Tokenizer) : `Whitespace Tokenizer`

#### 4.2 输出Example

```json
curl -XPOST 'localhost:9200/_analyze?pretty' -H 'Content-Type: application/json' -d'
{
  "analyzer": "whitespace",
  "text": "The 2 QUICK Brown-Foxes jumped over the lazy dog's bone."
}
'
```
以上示例产生如下词条：
```
[ The, 2, QUICK, Brown-Foxes, jumped, over, the, lazy, dog's, bone. ]
```
#### 4.3 配置

无

> Elasticsearch 版本：5.4

原文: https://www.elastic.co/guide/en/elasticsearch/reference/5.4/configuring-analyzers.html

https://www.elastic.co/guide/en/elasticsearch/reference/5.4/analysis-standard-analyzer.html

https://www.elastic.co/guide/en/elasticsearch/reference/5.4/analysis-simple-analyzer.html

https://www.elastic.co/guide/en/elasticsearch/reference/5.4/analysis-whitespace-analyzer.html
