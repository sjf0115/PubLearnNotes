---
layout: post
author: sjf0115
title: ElasticSearch 倒排索引
date: 2016-07-06 23:15:17
tags:
  - ElasticSearch

categories: ElasticSearch
permalink: elasticsearch-inverted-index
---

Elasticsearch 使用一种叫做倒排索引的结构来做快速的全文搜索。倒排索引由在文档中出现的单词列表，以及每个单词所在的文档组成。例如，我们有两个文档，每个文档都有一个 content 字段，内容如下：
```
# 文档1
The quick brown fox jumped over the lazy dog
# 文档2
Quick brown foxes leap over lazy dogs in summer
```

为了创建倒排索引，我们首先切分每个文档的 content 字段为单独的单词（可以称为词项（terms）或者词条（tokens）），把所有不重复的词项 terms 放入列表中并排序，并列出每个词项出现在的文档，结果如是所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/ElasticSearch/elasticsearch-inverted-index-1.png?raw=true)

现在，如果我们想搜索 "quick brown"，我们只需要找到每个词在哪个文档中出现即可：

![](https://github.com/sjf0115/ImageBucket/blob/main/ElasticSearch/elasticsearch-inverted-index-2.png?raw=true)

两个文档都匹配，但是第一个比第二个有更多的匹配项。 如果我们使用一个简单的相似度算法(similarity algorithm)，只是计算匹配单词的数目，这样我们就可以说第一个文档比第二个匹配度更高——对于我们的查询具有更多相关性。

但是在我们的倒排索引中还有些问题：
- "Quick" 和 "quick" 被认为是不同的单词，但是用户可能认为它们是相同的。
- "fox" 和 "foxes" 很相似，就像 "dog" 和 "dogs"，它们都是同根词。
- "jumped" 和 "leap" 不是同根词，但意思相似，它们是同义词。

上面的索引中，搜索 "+Quick +fox" 不会匹配任何文档（前缀+表示单词必须匹配到）。"Quick" 和 "fox" 都在同一文档中才可以匹配查询，但是第一个文档中只包含 "fox"，不包含 "Quick"（虽然包含"quick"），而第二个文档中只包含 "Quick"，不包含 "fox"（虽然包含" foxes"）。用户希望两个文档都能匹配查询到。

如果我们将词统一为标准格式，这样就可以找到不是确切匹配的查询，但是足以相似从而可以关联的文档。例如：
- "Quick" 可以转为小写成为 "quick"。
- "foxes" 可以被转为根形式 "fox"。同理 "dogs" 可以被转为 "dog"。
- "jumped" 和 "leap" 同义就可以只索引为单个词 "jump"

现在索引：

![](https://github.com/sjf0115/ImageBucket/blob/main/ElasticSearch/elasticsearch-inverted-index-3.png?raw=true)

但我们做的还不够好。我们的搜索 "+Quick +fox" 依旧失败，因为 "Quick" 的确切值已经不在索引里，不过，如果我们使用相同的标准化规则处理查询字符串的 content 字段，查询将变成 "+quick +fox"，这样就可以匹配到两个文档。

这个标准化的过程叫做分词(analysis)。

参考：https://www.elastic.co/guide/en/elasticsearch/guide/current/inverted-index.html
