

### 1. ElasticSearch 2.0 变动
#### 1.1 Queries与filters合并

查询(Queries)和过滤器(filters)进行合并 - 所有过滤器子句现在都是查询子句( all filter clauses are now query clauses.)。 相反，查询子句现在可以在查询上下文或过滤器上下文中使用：

Query context

在查询上下文中使用的查询将计算相关性分数，不会被缓存。 只要过滤器上下文不适用，就使用查询上下文。

Filter context

在过滤器上下文中使用的查询将不会计算相关性分数，并且可以缓存。 过滤器上下文由以下引入：

- `constant_score`查询
- `bool`查询中的`must_not`和（新添加）`filter`参数
- `function_score`查询中的`filter`和`filters`参数
- 任何叫`filter`的API，例如post_filter搜索参数,或者在聚合和索引别名中(any API called filter, such as the post_filter search parameter, or in aggregations or index aliases)

#### 1.2 or 和 and通过bool实现

以前`or`和`and`过滤器与`bool`过滤器有不同的执行模式。 (It used to be important to use and/or with certain filter clauses, and bool with others.)。

现在这个区别已被删除：现在`bool`查询足够智能，可以很好地处理这两种情况。 由于这种变化，现在`or`和`and`过滤器是bool查询内部执行语法。 这些过滤器将来会被删除。

#### 1.3 `filtered`查询 与 `query`过滤器 废弃

`query`过滤器已经废弃不再需要 - 所有查询都可以在查询或过滤器上下文中使用。

`filtered`查询已被弃用。 `filtered`查询如下：
```
GET _search
{
  "query": {
    "filtered": {
      "query": {
        "match": {
          "text": "quick brown fox"
        }
      },
      "filter": {
        "term": {
          "status": "published"
        }
      }
    }
  }
}
```
将查询和过滤器转换为`bool`查询中的`must`和`filter`参数：
```
GET _search
{
  "query": {
    "bool": {
      "must": {
        "match": {
          "text": "quick brown fox"
        }
      },
      "filter": {
        "term": {
          "status": "published"
        }
      }
    }
  }
}
```
#### 1.4 Filter自动缓存

以前可以通过`_cache`选项来控制哪些过滤器被缓存，并提供一个自定义的`_cache_key`。 这些选项已被弃用，如果存在，将被忽略。

过滤器上下文中使用的查询子句现在可以自动缓存。该算法考虑到使用频率，查询执行成本以及构建过滤器的成本。

`terms`过滤器查找机制不在缓存文档内容．现在依赖于文件系统缓存．如果查找索引不是太大，建议通过设置`index.auto_expand_replicas：0-all`将其复制到所有节点，以消除网络开销。

### 


#### 1.5 Java API Query和Filter重构

org.elasticsearch.index.queries.FilterBuilders从ElasticSearch2.0开始已被删除，作为查询和过滤器组合的一部分。 这些过滤器现在可以在QueryBuilders中使用具有相同名称的方法。所有可以接受FilterBuilder的方法现在也可以接受QueryBuilder。

以前使用方式：
```
FilterBuilders.boolFilter()  
    .must(FilterBuilders.termFilter("name", "张三"))  
    .mustNot(FilterBuilders.rangeFilter("age").from(28).to(30))  
    .should(FilterBuilders.termFilter("city", "北京"));  
```
现在可以使用如下方式：
```
BoolQueryBuilder boolQueryBuilder = QueryBuilders.boolQuery();
boolQueryBuilder.must(QueryBuilders.termQuery("name", "张三"));
boolQueryBuilder.must(QueryBuilders.rangeQuery("age").from(28).to(30));
boolQueryBuilder.must(QueryBuilders.termQuery("city", "北京");
ConstantScoreQueryBuilder queryBuilder = QueryBuilders.constantScoreQuery(boolQueryBuilder);
```

### 2. 深入理解Filter

在执行非评分查询时，Elasticsearch内部会执行多个操作．以下面查询为例：
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
例如我们想要查询产品ID为`XHDK-A-1293-#fJ3`的产品：
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

#### 2.1 查找匹配文档

`term`查询在倒排索引中查找词条`XHDK-A-1293-＃fJ3`，并检索包含该词条的所有文档。 在本例中，只有文件1具有我们正在寻找的词条。然后获取包含该 term 的所有文档。


#### 2.2 构建bitset

然后，过滤器构建一个bitset - 一个包含1和0的数组，描述了哪些文档包含查找词条。 匹配文档的标志位是 1 。 在我们的例子中，bitset将是[1,0,0,0]（只有文档１具有我们要查找的词条）。在内部，它表示成一个 "roaring bitmap"，可以同时对稀疏或密集的集合进行高效编码。

#### 2.3 迭代bitset(s)

一旦为每个查询生成了bitsets，Elasticsearch会遍历该bitsets，以找到满足所有过滤条件的匹配文档集合。 执行顺序是启发式的(The order of execution is decided heuristically)，但通常最稀疏的bitsets是首先被迭代的（因为它排除了最大数量的文档）。

#### 2.4 增加使用计数器

Elasticsearch 可以缓存非评分查询从而达到更快的访问，但是有一点不合理的地方是它也会缓存一些使用极少的东西。由于倒排索引的原因，非评分计算已经相当快了，所以我们只想缓存那些我们知道在后面会被再次使用的查询，以避免资源的浪费。

为了实现上面的目标，Elasticsearch 会跟踪每个索引查询使用的历史。如果查询在最近的 256 次查询中会被多次用到，那么就会被缓存到内存中。而当bitset被缓存时，对于具有少于10,000个文档（或小于总索引大小的3％）的段，会省略缓存。这些小的段即将会消失，所以为它们缓存是一种浪费。



实际情况并非如此（执行有点复杂，这取决于查询计划是如何重新规划的，有些启发式是基于查询代价的）（execution is a bit more complicated based on how the query planner re-arranges things, and some heuristics based on query cost），你可以在理论上认为非评分查询 先于 评分查询执行。非评分查询的目的是降低那些将高成本评分查询计算的文档数量，从而达到快速搜索的目的。

从概念上记住非评分计算是首先执行的，这将有助于写出高效又快速的搜索请求。

原文：https://www.elastic.co/guide/en/elasticsearch/guide/current/_finding_exact_values.html#_internal_filter_operation

https://www.elastic.co/guide/en/elasticsearch/reference/2.0/breaking_20_query_dsl_changes.html  

https://www.elastic.co/guide/en/elasticsearch/reference/2.0/breaking_20_java_api_changes.html