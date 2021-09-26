当进行精确值查找时， 我们会使用非评分的过滤器查询．过滤器(Filters)很重要，因为它们执行速度非常快．不会计算相关度（避免了整个评分阶段）而且很容易被缓存．我们会在[过滤器缓存](https://www.elastic.co/guide/en/elasticsearch/guide/current/filter-caching.html) 中讨论过滤器的性能优势，不过现在你需要记住：`请尽可能多的使用过滤器查询`。

### 1. term 查询数字

我们首先看一下 `term`查询,因为我们会经常使用它．`term`查询可以处理数字，布尔值，日期和文本等数据。

让我们以下面的例子进行说明，创建并索引一些表示产品的文档，每个文档都有 `price`字段 和 `productID`字段 （ `价格` 和 `产品ID` ）：

```
curl -XPUT  'localhost:9200/my_store/products/1' -d '{
"price" : 10, 
"productID" : "XHDK-A-1293-#fJ3"
}';

curl -XPUT  'localhost:9200/my_store/products/2' -d '{
"price" : 20, 
"productID" : "KDKE-B-9947-#kL5"
}';

curl -XPUT  'localhost:9200/my_store/products/3' -d '{
"price" : 30, 
"productID" : "JODL-X-1937-#pV7"
}';

curl -XPUT  'localhost:9200/my_store/products/4' -d '{
"price" : 40, 
"productID" : "QQPX-R-3956-#aD8"
}';
```

我们的目的是查找指定价格的所有产品，如果你有关系数据库背景，则肯定熟悉 SQL，如果我们将其用 SQL 形式表达，会是下面这样：

```
SELECT product
FROM   products
WHERE  price = 20
```

在Elasticsearch查询DSL中，我们可以使用`term`查询来完成同样的事情。 `term`查询将查找我们指定的精确值。term 查询本身很简单。 它接受一个字段名称和我们希望找到的值：
```
{
    "term" : {
        "price" : 20
    }
}
```

通常，当查找精确值时，我们不想对查询进行评分。 我们只希望对文档进行包括或排除的计算，所以我们将使用一个`constant_score`查询，以非评分模式执行`term`查询，并应用一个统一的分数。
最终组合将是一个包含`term`查询的`constant_score`查询：
```
curl -XGET 'localhost:9200/my_store/products/_search?pretty' -d'
{
    "query" : {
        "constant_score" : { #1
            "filter" : {
                "term" : { #2
                    "price" : 20
                }
            }
        }
    }
}
'
```
- 1 我们用 constant_score 将 term 查询转化成为过滤器
- 2 我们之前看到过的 term 查询

返回结果：
```
{
  "took" : 7,
  "timed_out" : false,
  "_shards" : {
    "total" : 5,
    "successful" : 5,
    "failed" : 0
  },
  "hits" : {
    "total" : 1,
    "max_score" : 1.0,
    "hits" : [ {
      "_index" : "my_store",
      "_type" : "products",
      "_id" : "2",
      "_score" : 1.0, # 1
      "_source" : {
        "price" : 20,
        "productID" : "KDKE-B-9947-#kL5"
      }
    } ]
  }
}
```
- 1. 放置在过滤器子句内的查询不执行评分或相关性计算，因此所有结果都将获得分值为1的中立分数。

执行后，这个查询所搜索到的结果与我们期望的一致：只有文档 2 命中并作为返回结果（因为只有文档2 的价格是 20 ）:


### 2. term 查询文本

就像我们刚开始提到过的一样 ，使用 `term` 查询匹配字符串与匹配数字一样容易。这次我们不查询价格，而是查询指定 UPC ID 的产品，使用 SQL 表达式会是如下这样：
```
SELECT product
FROM   products
WHERE  productID = "XHDK-A-1293-#fJ3"
```
转换成查询DSL，我们可以使用`term`过滤器执行类似的查询，如下所示：
```
curl -XGET 'localhost:9200/my_store/products/_search?pretty' -d'
{
    "query" : {
        "constant_score" : { 
            "filter" : {
                "term" : { 
                    "productID" : "XHDK-A-1293-#fJ3"
                }
            }
        }
    }
}
';
```
返回结果:
```
{
  "took" : 2,
  "timed_out" : false,
  "_shards" : {
    "total" : 5,
    "successful" : 5,
    "failed" : 0
  },
  "hits" : {
    "total" : 0,
    "max_score" : null,
    "hits" : [ ]
  }
}
```
我们没有得到我们想要的结果！ 这是为什么？ 问题不在于`term`查询; 而在于索引数据的方式。 如果我们使用分析API（测试分析器），我们可以看到我们的UPC已经被标记为较小的token：
```
curl -XGET 'localhost:9200/my_store/_analyze?pretty' -d'
{
  "field": "productID",
  "text": "XHDK-A-1293-#fJ3"
}
';
```
返回结果：
```
{
  "tokens" : [ {
    "token" : "xhdk",
    "start_offset" : 0,
    "end_offset" : 4,
    "type" : "<ALPHANUM>",
    "position" : 0
  }, {
    "token" : "a",
    "start_offset" : 5,
    "end_offset" : 6,
    "type" : "<ALPHANUM>",
    "position" : 1
  }, {
    "token" : "1293",
    "start_offset" : 7,
    "end_offset" : 11,
    "type" : "<NUM>",
    "position" : 2
  }, {
    "token" : "fj3",
    "start_offset" : 13,
    "end_offset" : 16,
    "type" : "<ALPHANUM>",
    "position" : 3
  } ]
}
```
我们需要注意一下几点：

- Elasticsearch 用 4 个不同的 token 而不是一个 token 来表示这个 UPC 。
- 所有字母都是小写的。
- 丢失了连字符(-)和哈希符(#)。

所以当我们用 `term` 查询查找精确值 `XHDK-A-1293-#fJ3` 的时候，找不到任何文档，因为它并不在我们的倒排索引中，相反，索引里有四个token（我们之前列出的４个） 。

显然，这不是我们在处理识别码或任何一种精确值时想要发生的事情。

为了防止这种情况发生，我们需要告诉Elasticsearch，通过将字段设置为not_analyzed来包含一个确切值。 我们可以在自定义字段映射中看到了这一点。 为此，我们需要先删除旧索引（因为它的映射是不正确的），并创建一个具有正确映射的新索引：
```
curl -XDELETE 'localhost:9200/my_store?pretty';
curl -XPUT 'localhost:9200/my_store?pretty' -d'
{
    "mappings" : {
        "products" : {
            "properties" : {
                "productID" : {
                    "type" : "string",
                    "index" : "not_analyzed" 
                }
            }
        }
    }
';
```
现在我们可以重新索引我们的文件：
```
curl -XPUT  'localhost:9200/my_store/products/1' -d '{
"price" : 10, 
"productID" : "XHDK-A-1293-#fJ3"
}';

curl -XPUT  'localhost:9200/my_store/products/2' -d '{
"price" : 20, 
"productID" : "KDKE-B-9947-#kL5"
}';

curl -XPUT  'localhost:9200/my_store/products/3' -d '{
"price" : 30, 
"productID" : "JODL-X-1937-#pV7"
}';

curl -XPUT  'localhost:9200/my_store/products/4' -d '{
"price" : 40, 
"productID" : "QQPX-R-3956-#aD8"
}';
```
此时， `term` 查询就能搜索到我们想要的结果，让我们再次搜索新索引过的数据（注意，查询和过滤并没有发生任何改变，改变的是数据映射的方式）
```
curl -XGET 'localhost:9200/my_store/products/_search?pretty' -d'
{
    "query" : {
        "constant_score" : { 
            "filter" : {
                "term" : { 
                    "productID" : "XHDK-A-1293-#fJ3"
                }
            }
        }
    }
}
'
```
因为 productID 字段是未分析过的， `term` 查询不会对其做任何分析，查询会进行精确查找并返回文档 1 。
```
{
  "took" : 7,
  "timed_out" : false,
  "_shards" : {
    "total" : 5,
    "successful" : 5,
    "failed" : 0
  },
  "hits" : {
    "total" : 1,
    "max_score" : 1.0,
    "hits" : [ {
      "_index" : "my_store",
      "_type" : "products",
      "_id" : "1",
      "_score" : 1.0,
      "_source" : {
        "price" : 10,
        "productID" : "XHDK-A-1293-#fJ3"
      }
    } ]
  }
}
```

