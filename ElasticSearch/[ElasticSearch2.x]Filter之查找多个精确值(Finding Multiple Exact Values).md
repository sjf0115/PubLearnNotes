`term`查询对于查找单个值非常有用，但很多时候我们需要搜索多个值。如果我们想查找价格为20美元或30美元的文件怎么办？

在查找多个值时，可以使用单个`terms`查询（请注意末尾的s）来代替使用多个`term`查询。`terms`查询可以理解为`term`查询的复数形式。

它几乎与`term`的使用方式一样，与指定单个价格不同，现在我们可以指定一组数值：
```
{
    "terms" : {
        "price" : [20, 30]
    }
}
```
与`term`查询一样，我们将它放在一个constant_score查询的filter子句中：
```
curl -XGET 'localhost:9200/my_store/products/_search?pretty' -H 'Content-Type: application/json' -d'
{
    "query" : {
        "constant_score" : {
            "filter" : {
                "terms" : { 
                    "price" : [20, 30]
                }
            }
        }
    }
}
'
```
`terms`查询如前所述，需要将其放置在`constant_score`查询中使用.

该查询将返回如下文档：
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

### 2. 包含但不等价

一定要了解`term`和`terms`是 包含（contains） 操作，而非 等值（equals）。 这是什么意思呢？


### 3. 等价
