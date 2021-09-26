
### 1. 嵌套对象映射

设置一个嵌套字段很简单 - 通常你会指定`object`类型，现在改为`nested`类型：
```
PUT /blogpost
{
  "mappings": {
    "blogpost": {
      "properties": {
        "comments": {
          "type": "nested", 
          "properties": {
            "name":    { "type": "string"  },
            "comment": { "type": "string"  },
            "age":     { "type": "short"   },
            "stars":   { "type": "short"   },
            "date":    { "type": "date"    }
          }
        }
      }
    }
  }
}
```
Java版本:
```
XContentBuilder mappingBuilder;
try {
    mappingBuilder = XContentFactory.jsonBuilder()
        .startObject()
        .startObject(type)
        .startObject("properties")
            .startObject("comments").field("type", "nested").endObject()
        .endObject()
        .endObject()
        .endObject();
} catch (Exception e) {
    logger.error("--------- 创建 mapping 失败：", e);
    return;
}

IndicesAdminClient indicesAdminClient = client.admin().indices();
CreateIndexRequestBuilder createIndexRequestBuilder = indicesAdminClient.prepareCreate("blogpost");

createIndexRequestBuilder.addMapping("blogpost", mappingBuilder);
CreateIndexResponse response = createIndexRequestBuilder.get();
return response.isAcknowledged();
```

嵌套字段接受与`object`类型的字段相同的参数。

查看映射:
```
{
    "blogpost": {
        "properties": {
            "comments": {
                "type": "nested",
                "properties": {
                    "date": {
                        "format": "strict_date_optional_time||epoch_millis",
                        "type": "date"
                    },
                    "name": {
                        "type": "string"
                    },
                    "comment": {
                        "type": "string"
                    },
                    "stars": {
                        "type": "long"
                    },
                    "age": {
                        "type": "long"
                    }
                }
            },
            "body": {
                "type": "string"
            },
            "title": {
                "type": "string"
            },
            "tags": {
                "type": "string"
            }
        }
    }
}
```

这就是嵌套对象映射所需要的。 任何`comments`对象现在都将作为单独的嵌套文档被索引。 有关详细信息，请参阅[嵌套类型](https://www.elastic.co/guide/en/elasticsearch/reference/current/nested.html)。

### 2. 嵌套对象查询

因为嵌套对象被索引为单独的隐藏文档，所以我们不能直接查询它们。 相反，我们必须使用嵌套查询来访问它们．

#### 2.1 嵌套查询

嵌套查询允许查询嵌套对象/文档。 对嵌套对象/文档查询，就像将它们作为单独的文档进行索引一样，并生成根父文档`root parent doc`（或父嵌套映射`parent nested mapping`）。 以下是我们将使用的示例映射：

```
curl -XPUT 'localhost:9200/my_index?pretty' -H 'Content-Type: application/json' -d'
{
    "mappings": {
        "type1" : {
            "properties" : {
                "obj1" : {
                    "type" : "nested"
                }
            }
        }
    }
}
'
```
这里是一个示例嵌套查询用法：
```
curl -XGET 'localhost:9200/_search?pretty' -H 'Content-Type: application/json' -d'
{
    "query": {
        "nested" : {
            "path" : "obj1",
            "score_mode" : "avg",
            "query" : {
                "bool" : {
                    "must" : [
                    { "match" : {"obj1.name" : "blue"} },
                    { "range" : {"obj1.count" : {"gt" : 5}} }
                    ]
                }
            }
        }
    }
}
'
```

查询中`path`指向嵌套对象路径，`query`包括运行在与直接路径匹配的嵌套文档上的的查询，以及与根文档进行连接(the query includes the query that will run on the nested docs matching the direct path, and joining with the root parent docs.)。请注意，查询中引用的任何字段必须使用完整路径（例如：`obj1.name`）。

`score_mode`允许设置内部子嵌套匹配如何影响父嵌套的评分(set how inner children matching affects scoring of parent)。 它默认为`avg`，但可以是`sum`，`min`，`max`和`none`。


还有一个`ignore_unmapped`选项，当设置为true时，将忽略未映射的路径，并且将不匹配此查询的任何文档。 当查询可能具有不同映射的多个索引时，这可能很有用。 当设置为false（默认值）时，如果路径未映射，则查询将抛出异常。


#### 2.2 嵌套对象查询

```
GET /my_index/blogpost/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "match": {
            "title": "eggs" 
          }
        },
        {
          "nested": {
            "path": "comments", 
            "query": {
              "bool": {
                "must": [ 
                  {
                    "match": {
                      "comments.name": "john"
                    }
                  },
                  {
                    "match": {
                      "comments.age": 28
                    }
                  }
                ]
              }
            }
          }
        }
      ]
}}}
```
==说明==

- `title` 子句是查询根文档的。
- `nested` 子句"下移"作用于嵌套字段 `comments` 。在此查询中，既不能访问根文档字段，也不能访问其他嵌套文档。
- `comments.name` 和 `comments.age` 子句对相同的嵌套文档进行操作。

==提示==

`nested` 字段可以包含其他的 `nested` 字段。同样地，`nested` 查询也可以包含其他的 `nested` 查询。而嵌套的层次会按照你所期待的被应用。


当然，`nested`查询可以匹配多个嵌套文档。每个匹配的嵌套文档都具有自己的相关性分数，但是这些多个分数需要聚合成单个分数来应用于根文档(these multiple scores need to be reduced to a single score that can be applied to the root document.)。聚合方式可以使用`score_mode`参数设置.

默认情况下，它会聚合所有匹配到的嵌套文档的分数。 这可以通过将`score_mode`参数设置为`avg`，`max`，`sum`或甚至`none`（在这种情况下，根文档获得1.0的常量）来控制。


```
GET /my_index/blogpost/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "match": {
            "title": "eggs"
          }
        },
        {
          "nested": {
            "path": "comments",
            "score_mode": "max", 
            "query": {
              "bool": {
                "must": [
                  {
                    "match": {
                      "comments.name": "john"
                    }
                  },
                  {
                    "match": {
                      "comments.age": 28
                    }
                  }
                ]
              }
            }
          }
        }
      ]
    }
  }
}
```
==说明==

最佳匹配嵌套文档的`_score`返回给根文档。

==注意==

如果`nested`查询放在一个布尔查询的`filter`子句中，其表现就像一个`nested`查询，只是不在使用`score_mode`参数(except that it doesn’t accept the score_mode parameter. )。因为它被用于非评分的查询中，只是包含或不包含条件，不进行打分．　那么`score_mode`就没有任何意义，因为根本就没有得分(there is nothing to score.)。




原文：https://www.elastic.co/guide/en/elasticsearch/reference/5.4/query-dsl-nested-query.html

https://www.elastic.co/guide/en/elasticsearch/guide/current/nested-query.html