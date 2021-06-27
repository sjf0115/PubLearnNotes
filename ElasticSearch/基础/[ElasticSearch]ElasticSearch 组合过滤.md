
在[ElascticSearch2.x]精确值查找都是单个过滤器（filter）的使用方式。 在实际应用中，我们很有可能会过滤多个值或字段。比方说，怎样用 Elasticsearch 来表达下面的 SQL ？
```
SELECT product
FROM   products
WHERE  (price = 20 OR productID = "XHDK-A-1293-#fJ3")
  AND  (price != 30)
```
在这些情况下，您需要在`constant_score`查询中使用`bool`查询。 这允许我们构建具有布尔组合（具有多个组件）的过滤器。

### 1. Bool Filter

bool查询由四个部分组成：
```
{
   "bool" : {
      "must" :     [],
      "should" :   [],
      "must_not" : [],
      "filter":    []
   }
}
```

#### 1.1 must

所有的语句都 必须（must） 匹配，与 AND 等价。

#### 1.2 should

至少有一个语句必须匹配，与 OR 等价。

#### 1.3 must_not

所有的语句都 不能（must not） 匹配，与 NOT 等价。

#### 1.4 filter

所有的语句都必须匹配，但是以非评分，过滤模式运行。


在这个二次布尔查询中，我们可以忽略filter子句：查询已经以非评分模式运行，因此额外的filter子句是无用的。


==备注==

布尔过滤器的每个部分都是可选的（例如，您可以只要一个　`must` 语句，而不包含其他语句），并且每个部分都可以包含单个查询或一组查询。

使用ElasticSearch实现前面的SQL示例，我们将使用我们之前使用过的两个`trem`查询，并将它们放在bool查询的should子句中，并添加另一个子句来处理NOT条件：

```
curl -XGET 'localhost:9200/my_store/products/_search?pretty' -d'
{
   "query" : {
      "constant_score" : { #1
         "filter" : {
            "bool" : {
              "should" : [
                 { "term" : {"price" : 20}}, #2
                 { "term" : {"productID" : "XHDK-A-1293-#fJ3"}} #3
              ],
              "must_not" : {
                 "term" : {"price" : 30} #4
              }
           }
         }
      }
   }
}
';
```
==说明==
- #1 请注意，我们仍然需要使用一个constant_score查询来包装其所有过滤子句。目的是进行无评分查询；
- ＃2和#3 这两个`term`查询是bool查询的子查询，因为它们被放置在should子句中，所以至少需要满足一个子句；
- #4 如果产品的价格为30，则会自动排除，因为它满足must_not子句;

返回结果:
```
{
  "took" : 6,
  "timed_out" : false,
  "_shards" : {
    "total" : 5,
    "successful" : 5,
    "failed" : 0
  },
  "hits" : {
    "total" : 2,
    "max_score" : 1.0,
    "hits" : [ {
      "_index" : "my_store",
      "_type" : "products",
      "_id" : "2",
      "_score" : 1.0,
      "_source" : {
        "price" : 20,
        "productID" : "KDKE-B-9947-#kL5"
      }
    }, {
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

第一条结果满足productID =“XHDK-A-1293-＃fJ3”的`term`查询，第二条结果满足price = 20的`term`查询．

### 2. 嵌套 Boolean Queries

您可以看到把布尔查询的嵌套在一起可以产生更复杂的布尔逻辑。 如果需要执行更复杂的操作，可以继续在任意组合中嵌套布尔查询，从而产生任意复杂的布尔逻辑。

例如，如果我们有这个SQL语句：

```
SELECT document
FROM   products
WHERE  productID      = "KDKE-B-9947-#kL5"
  OR (     productID = "JODL-X-1937-#pV7"
       AND price     = 30 )
```

我们可以将其转换成一对嵌套的布尔过滤器：

```
curl -XGET 'localhost:9200/my_store/products/_search?pretty' -d'
{
   "query" : {
      "constant_score" : {
         "filter" : {
            "bool" : {
              "should" : [
                { "term" : {"productID" : "KDKE-B-9947-#kL5"}}, #1
                { "bool" : { #2
                  "must" : [
                    { "term" : {"productID" : "JODL-X-1937-#pV7"}}, #3
                    { "term" : {"price" : 30}} #4
                  ]
                }}
              ]
           }
         }
      }
   }
}
'
```
==说明==

- #1和#2 因为`term`和`bool`是位于Boolean查询should部分下的同级子句，所以这两个子句必须至少满足一个;
- #3和#4 因为两个`term`子句是位于must子句下的同级子句，所以这两个必须都得到满足



结果显示两个文档，它们各匹配 should 语句中的一个条件：
```
{
  "took" : 5,
  "timed_out" : false,
  "_shards" : {
    "total" : 5,
    "successful" : 5,
    "failed" : 0
  },
  "hits" : {
    "total" : 2,
    "max_score" : 1.0,
    "hits" : [ {
      "_index" : "my_store",
      "_type" : "products",
      "_id" : "2",
      "_score" : 1.0,
      "_source" : {
        "price" : 20,
        "productID" : "KDKE-B-9947-#kL5"
      }
    }, {
      "_index" : "my_store",
      "_type" : "products",
      "_id" : "3",
      "_score" : 1.0,
      "_source" : {
        "price" : 30,
        "productID" : "JODL-X-1937-#pV7"
      }
    } ]
  }
}

```
