考虑到在Elasticsearch中创建，删除和更新的单个文档是原子操作的，因此在相同文档中存储紧密相关的实体是有意义的。 例如，我们可以在一个文档中存储一个订单和其所有的订单线(order lines)，或者我们可以通过传递一组评论来将一篇博客文章及其所有评论存储在一起：
```
PUT /my_index/blogpost/1
{
  "title": "Nest eggs",
  "body":  "Making your money work...",
  "tags":  [ "cash", "shares" ],
  "comments": [ 
    {
      "name":    "John Smith",
      "comment": "Great article",
      "age":     28,
      "stars":   4,
      "date":    "2014-09-01"
    },
    {
      "name":    "Alice White",
      "comment": "More like this please",
      "age":     31,
      "stars":   5,
      "date":    "2014-10-22"
    }
  ]
}
```
如果我们依赖于[动态映射](https://www.elastic.co/guide/en/elasticsearch/guide/current/dynamic-mapping.html)，则`comments`字段将被自动映射为`object`字段。

因为所有的内容都在同一个文档中，所以没有必要在查询时把博客文章和评论进行连接查询，所以搜索效果很好。

问题是前面的文档会匹配一个这样的查询，查询名称为`Alice`年龄28岁：
```
GET /_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "comments.name": "Alice" }},
        { "match": { "comments.age":  28      }} 
      ]
    }
  }
}
```
输出结果:
```
{
    "title": "Nest eggs",
    "body": "Making your money work...",
    "tags": [
        "cash",
        "shares"
    ],
    "comments": [
        {
            "name": "John Smith",
            "comment": "Great article",
            "age": 28,
            "stars": 4,
            "date": "2014-09-01"
        },
        {
            "name": "Alice White",
            "comment": "More like this please",
            "age": 31,
            "stars": 5,
            "date": "2014-10-22"
        }
    ]
}
```
这与我们期望的不太一样，`Alice`31岁，而不是28岁，所以不应该返回上述结果．

如“[内部数组](https://www.elastic.co/guide/en/elasticsearch/guide/current/complex-core-fields.html#object-arrays)”中讨论的，这种跨对象匹配的原因是，我们的JSON文档在索引中被扁平化为简单的键值格式，如下所示：
```
{
  "title":            [ eggs, nest ],
  "body":             [ making, money, work, your ],
  "tags":             [ cash, shares ],
  "comments.name":    [ alice, john, smith, white ],
  "comments.comment": [ article, great, like, more, please, this ],
  "comments.age":     [ 28, 31 ],
  "comments.stars":   [ 4, 5 ],
  "comments.date":    [ 2014-09-01, 2014-10-22 ]
}
```

`Alice`与`31`岁之间的相关性，或`John`与`2014-09-01`之间的相关性已经丢失了。 虽然`object`类型的字段（参见[Multilevel Objects](https://www.elastic.co/guide/en/elasticsearch/guide/current/complex-core-fields.html#inner-objects)）对于存储单个对象很有用，但从搜索的角度来看，它们对于存储对象数组是无用的(While fields of type object are useful for storing a single object, they are useless, from a search point of view, for storing an array of objects)。

嵌套对象`nested objects`被设计来解决上述问题。通过将`comments`字段映射为`nested`而不是`object`，每个嵌套对象都将作为隐藏的单独文档`hidden separate document`进行索引，如下所示：
```
{ 
  "comments.name":    [ john, smith ],
  "comments.comment": [ article, great ],
  "comments.age":     [ 28 ],
  "comments.stars":   [ 4 ],
  "comments.date":    [ 2014-09-01 ]
}
{ 
  "comments.name":    [ alice, white ],
  "comments.comment": [ like, more, please, this ],
  "comments.age":     [ 31 ],
  "comments.stars":   [ 5 ],
  "comments.date":    [ 2014-10-22 ]
}
{ 
  "title":            [ eggs, nest ],
  "body":             [ making, money, work, your ],
  "tags":             [ cash, shares ]
}
```

通过分别索引每个嵌套对象，对象中的字段得以保持相关性。 如果匹配发生在同一个嵌套对象内，我们运行的查询才会匹配。

不仅如此，由于嵌套对象被索引的方式(嵌套文档直接存储在文档内部)，在查询时将嵌套文档与根文档进行联合的速度几乎与查询单个文档一样快。

这些额外的嵌套文档是隐藏的; 我们无法直接访问它们。 要更新，添加或删除嵌套对象，我们必须重新索引整个文档。 请注意，搜索请求返回的结果不是单独的嵌套对象; 这是整个文件。


后面文章中我们会了解如何映射嵌套对象以及如何查询嵌套对象．

原文：https://www.elastic.co/guide/en/elasticsearch/guide/current/nested-objects.html

