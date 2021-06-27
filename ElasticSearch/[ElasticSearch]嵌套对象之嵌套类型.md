`nested`类型是一种特殊的对象`object`数据类型(specialised version of the object datatype )，允许对象数组彼此独立地进行索引和查询。


### 1. 对象数组如何扁平化

内部对象`object`字段的数组不能像我们所期望的那样工作。 Lucene没有内部对象的概念，所以Elasticsearch将对象层次结构扁平化为一个字段名称和值的简单列表。 例如，以下文件：

```
curl -XPUT 'localhost:9200/my_index/my_type/1?pretty' -H 'Content-Type: application/json' -d'
{
  "group" : "fans",
  "user" : [ 
    {
      "first" : "John",
      "last" :  "Smith"
    },
    {
      "first" : "Alice",
      "last" :  "White"
    }
  ]
}
'
```

==说明==

`user`字段被动态的添加为`object`类型的字段。

在内部其转换成一个看起来像下面这样的文档：
```
{
  "group" :        "fans",
  "user.first" : [ "alice", "john" ],
  "user.last" :  [ "smith", "white" ]
}
```

`user.first`和`user.last`字段被扁平化为多值字段，并且`alice`和`white`之间的关联已经丢失。 本文档将错误地匹配`user.first`为`alice`和`user.last`为`smith`的查询：

```
curl -XGET 'localhost:9200/my_index/_search?pretty' -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        { "match": { "user.first": "Alice" }},
        { "match": { "user.last":  "Smith" }}
      ]
    }
  }
}
'
```

### 2. 对对象数组使用嵌套字段

如果需要索引对象数组并维护数组中每个对象的独立性，则应使用`nested`数据类型而不是`object`数据类型。 在内部，嵌套对象将数组中的每个对象作为单独的隐藏文档进行索引，这意味着每个嵌套对象都可以使用嵌套查询`nested query`独立于其他对象进行查询：
```
curl -XPUT 'localhost:9200/my_index?pretty' -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "my_type": {
      "properties": {
        "user": {
          "type": "nested" 
        }
      }
    }
  }
}
'

curl -XPUT 'localhost:9200/my_index/my_type/1?pretty' -H 'Content-Type: application/json' -d'
{
  "group" : "fans",
  "user" : [
    {
      "first" : "John",
      "last" :  "Smith"
    },
    {
      "first" : "Alice",
      "last" :  "White"
    }
  ]
}
'
```
==说明==

`user`字段映射为`nested`类型，而不是默认的`object`类型


```
curl -XGET 'localhost:9200/my_index/_search?pretty' -H 'Content-Type: application/json' -d'
{
  "query": {
    "nested": {
      "path": "user",
      "query": {
        "bool": {
          "must": [
            { "match": { "user.first": "Alice" }},
            { "match": { "user.last":  "Smith" }} 
          ]
        }
      }
    }
  }
}
'
```
==说明==

此查询得不到匹配，是因为`Alice`和`Smith`不在同一个嵌套对象中。

```
curl -XGET 'localhost:9200/my_index/_search?pretty' -H 'Content-Type: application/json' -d'
{
  "query": {
    "nested": {
      "path": "user",
      "query": {
        "bool": {
          "must": [
            { "match": { "user.first": "Alice" }},
            { "match": { "user.last":  "White" }} 
          ]
        }
      },
      "inner_hits": { 
        "highlight": {
          "fields": {
            "user.first": {}
          }
        }
      }
    }
  }
}
'
```
==说明==

此查询得到匹配，是因为`Alice`和`White`位于同一个嵌套对象中。

`inner_hits`允许我们突出显示匹配的嵌套文档。

==输出==

```
{
    "took": 6,
    "timed_out": false,
    "_shards": {
        "total": 5,
        "successful": 5,
        "failed": 0
    },
    "hits": {
        "total": 1,
        "max_score": 1.987628,
        "hits": [
            {
                "_index": "my_index",
                "_type": "my_type",
                "_id": "1",
                "_score": 1.987628,
                "_source": {
                    "group": "fans",
                    "user": [
                        {
                            "first": "John",
                            "last": "Smith"
                        },
                        {
                            "first": "Alice",
                            "last": "White"
                        }
                    ]
                },
                "inner_hits": {
                    "user": {
                        "hits": {
                            "total": 1,
                            "max_score": 1.987628,
                            "hits": [
                                {
                                    "_index": "my_index",
                                    "_type": "my_type",
                                    "_id": "1",
                                    "_nested": {
                                        "field": "user",
                                        "offset": 1
                                    },
                                    "_score": 1.987628,
                                    "_source": {
                                        "first": "Alice",
                                        "last": "White"
                                    },
                                    "highlight": {
                                        "user.first": [
                                            "<em>Alice</em>"
                                        ]
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
```

嵌套文档可以：
- 使用[nested](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-nested-query.html)查询进行查询
- 使用[nested](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-nested-aggregation.html)和[reverse_nested](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-reverse-nested-aggregation.html)聚合进行分析
- 使用[nested](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-request-sort.html#nested-sorting)排序进行排序
- 使用[nested inner hits](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-request-inner-hits.html#nested-inner-hits)进行检索与突出显示

### 3. 嵌套字段参数

嵌套字段接受以下参数：

参数 | 描述
---|---
[dynamic](https://www.elastic.co/guide/en/elasticsearch/reference/current/dynamic.html) | 是否将新属性动态添加到现有的嵌套对象。共有`true`（默认），`false`和`strict`三种参数。
[include_in_all](https://www.elastic.co/guide/en/elasticsearch/reference/current/include-in-all.html) | Sets the default include_in_all value for all the properties within the nested object. Nested documents do not have their own _all field. Instead, values are added to the _all field of the main “root” document.
[properties](https://www.elastic.co/guide/en/elasticsearch/reference/current/properties.html) | 嵌套对象中的字段，可以是任何数据类型，包括嵌套。新的属性可能会添加到现有的嵌套对象。

==备注==

类型映射(`type mapping`)、对象字段和嵌套字段包含的子字段，称之为属性`properties`。这些属性可以为任意数据类型，包括`object`和 `nested`。属性可以通过以下方式加入:
- 当在创建索引时显式定义他们。
- 当使用`PUT mapping API`添加或更新映射类型时显式地定义他们。
- 当索引包含新字段的文档时动态的加入。



==重要==

由于嵌套文档作为单独的文档进行索引，因此只能在`nested`查询，`nested`/`reverse_nested`聚合或者 [nested inner hits](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-request-inner-hits.html#nested-inner-hits) 的范围内进行访问。

For instance, if a string field within a nested document has index_options set to offsets to allow use of the postings highlighter, these offsets will not be available during the main highlighting phase. Instead, highlighting needs to be performed via nested inner hits.

### 4. 限制嵌套字段的个数

索引一个拥有100个嵌套字段的文档，相当于索引了101个文档，因为每一个嵌套文档都被索引为一个独立的文档．为了防止不明确的映射，每个索引可以定义的嵌套字段的数量已被限制为50个。
具体请参阅 [Settings to prevent mappings explosion](https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html#mapping-limit-settings)


原文：https://www.elastic.co/guide/en/elasticsearch/reference/current/nested.html#nested-params


