### 1. 使用文件系统缓存

ElasticSearch很大程度上依赖于文件系统缓存，以便快速搜索。 一般来说，你应该确保至少有一半的可用内存用作文件系统缓存，以便ElasticSearch可以将索引中的热区域(hot regions)保留在物理内存中。

### 2. 使用更快的硬件

如果索引受限于 I/O ，应该增加文件系统缓存的内存或者购买更快的驱动设备。我们所知特别是`SSD`硬盘要比普通硬盘性能更好。经常本地存储数据，避免使用 `NFS` 或者 `SMB` 等远程文件系统。还要小心虚拟化存储，像亚马逊的 弹性块存储（Elastic Block Storage）。Elasticsearch 在虚拟存储上也有比较好的性能，具有搜索快，安装便捷的特性；然而相对于本地专用存储，就要慢的多了。如果你在 EBS 上使用 index ，一定要使用 IOPS 否则操作会很快挂掉。

如果搜索受限于 CPU ，更换更快的 CPUs。

### 3. 文档建模

为了尽可能的节省搜索时间，应该为 Documents 创建模版(Documents should be modeled)。特别是要避开联合查询，嵌套查询也会慢好几倍，子查询将会慢好几百倍。同一个问题的结果不加入非规范化 documents 加速效果是可以预期的(So if the same questions can be answered without joins by denormalizing documents, significant speedups can be expected)。

### 4. 预索引数据

您应该利用查询中的模式来优化数据索引的方式(You should leverage patterns in your queries to optimize the way data is indexed)。例如，如果所有的文档都有`price` 字段，并且大多数查询都在一个固定的范围列表中运行范围聚合，那么可以通过将范围预索引到索引中(例如，下面添加了一个price_range字段来预索引范围)以及使用`terms` 聚合来更快地实现聚合。

例如，文档如下所示：
```
curl -XPUT 'localhost:9200/index/type/1?pretty' -d'
{
  "designation": "spoon",
  "price": 13
}
'
```
搜索请求如下所示：
```
curl -XGET 'localhost:9200/index/_search?pretty' -d'
{
  "aggs": {
    "price_ranges": {
      "range": {
        "field": "price",
        "ranges": [
          { "to": 10 },
          { "from": 10, "to": 100 },
          { "from": 100 }
        ]
      }
    }
  }
}
'
```
文档在索引时可以添加一个`price_range`字段，将其映射为`keyword`：
```
curl -XPUT 'localhost:9200/index?pretty' -d'
{
  "mappings": {
    "type": {
      "properties": {
        "price_range": {
          "type": "keyword"
        }
      }
    }
  }
}
'
curl -XPUT 'localhost:9200/index/type/1?pretty' -d'
{
  "designation": "spoon",
  "price": 13,
  "price_range": "10-100"
}
'
```
然后搜索请求可以聚合新字段`price_range`，而不是在`price`字段上运行范围聚合:
```
curl -XGET 'localhost:9200/index/_search?pretty' -d'
{
  "aggs": {
    "price_ranges": {
      "terms": {
        "field": "price_range"
      }
    }
  }
}
'
```

### 5. 映射

一些数据是数字并不意味着它应该被映射为数值型字段。通常情况下，存储标示符(例如ISBN或者标示另一个数据库中记录的数值标示符)的字段，映射为`keyword`要比映射为`integer` 或者 `long` 要好一些( fields storing identifiers such as an ISBN or any number identifying a record from another database, might benefit from being mapped as keyword rather than integer or long.)。


### 6. 避免使用脚本

一般来说，应该避免脚本。 如果必须需要脚本，那你应该首选`painless`　和　`expressions` 的引擎。

### 7. 根据日期查询

日期字段使用`now`的查询通常不可缓存，因为正在匹配的范围一直在更改(since the range that is being matched changes all the time.)。 然而，使用特定范围日期查询，在用户体验方面更佳，并且查询时能够更好地利用高速缓存。

例如，如下查询：
```
curl -XPUT 'localhost:9200/index/type/1?pretty' -d'
{
  "my_date": "2016-05-11T16:30:55.328Z"
}
'
curl -XGET 'localhost:9200/index/_search?pretty' -d'
{
  "query": {
    "constant_score": {
      "filter": {
        "range": {
          "my_date": {
            "gte": "now-1h",
            "lte": "now"
          }
        }
      }
    }
  }
}
'
```
可以使用如下方式替换：
```
curl -XGET 'localhost:9200/index/_search?pretty' -d'
{
  "query": {
    "constant_score": {
      "filter": {
        "range": {
          "my_date": {
            "gte": "now-1h/m",
            "lte": "now/m"
          }
        }
      }
    }
  }
}
'
```
在这种情况下，我们四舍五入到分钟，所以如果当前时间是16:31:29，范围查询将匹配my_date字段在15:31:00到16:31:59之间的所有值。 如果有几个用户在同一分钟内运行包含此范围的查询，查询缓存可以帮助您加快速度。 用于舍入的间隔越长，查询缓存可以帮助越多(The longer the interval that is used for rounding, the more the query cache can help)，但要注意的是，太积极的舍入也可能会伤害用户体验。

==注意==

将范围分为一大部分可以缓存和一小部分不可以缓存，目的是能够有效的利用缓存来查询，如下所示：
```
curl -XGET 'localhost:9200/index/_search?pretty' -d'
{
  "query": {
    "constant_score": {
      "filter": {
        "bool": {
          "should": [
            {
              "range": {
                "my_date": {
                  "gte": "now-1h",
                  "lte": "now-1h/m"
                }
              }
            },
            {
              "range": {
                "my_date": {
                  "gt": "now-1h/m",
                  "lt": "now/m"
                }
              }
            },
            {
              "range": {
                "my_date": {
                  "gte": "now/m",
                  "lte": "now"
                }
              }
            }
          ]
        }
      }
    }
  }
}
'

```

但是，在一些场景下这种做法可能会导致查询运行速度较慢，因为bool查询引入的开销可能会抵消利用查询缓存带来的好处。

### 8. 强制合并只读索引

只读索引合并到只有一个分段会带来一些好处．基于时间的索引就是一个经典例子：只有当前时间范围的索引才会获取新的文档，而旧的索引是只读的。

==重要==

不要强制合并仍在写入的索引 - 将合并放到后台进程中处理( leave merging to the background merge process)。

### 9. 预加载 global ordinals

全局序号`global ordinals` 是用于在 `keyword` 字段上运行 `terms` 聚合的数据结构。它们将会被加载到内存中，因为  ElasticSearch 不知道哪个字段将会用于 `terms` 聚合，哪些字段不会被用到。你可以通过配置映射来告诉ElasticSearch在刷新时加载全局序号：

```
curl -XPUT 'localhost:9200/index?pretty' -d'
{
  "mappings": {
    "type": {
      "properties": {
        "foo": {
          "type": "keyword",
          "eager_global_ordinals": true
        }
      }
    }
  }
}
'
```

### 10. 预加载文件系统缓存

如果运行 elasticsearch 的机器重启了，那么文件系统缓存将会被清空。为了能查询的更快一些，机器启动后 elasticsearch 需要花费一些时间将索引的热区域加载到内存中。可以通过设置 `index.store.preload` 来告诉 elasticsearch  哪些文件扩展名的文件将会被加载到内存中。

==警告==

预加载太多的索引或者文件到文件系统缓存中，如果文件系统缓存不足以容纳所有的数据，将会使搜索变得很慢．请谨慎使用此功能。