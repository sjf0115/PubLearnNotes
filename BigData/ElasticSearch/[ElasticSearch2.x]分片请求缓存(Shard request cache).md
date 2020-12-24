当一个搜索请求运行在单个或者多个索引上时，每个涉及的分片在本地执行搜索并将其本地结果返回给协调节点，协调节点将这些分片级结果合并为“全局”结果集。

分片级请求缓存模块将本地结果缓存在每个分片上。 这允许经常使用（或者搜索花费时间长(potentially heavy)）的搜索请求几乎立即返回结果。 请求缓存非常适合日志使用用例(logging use case)，其中只有最新的索引被更新 - 来自旧索引的结果将直接从缓存提供(where only the most recent index is being actively updated — results from older indices will be served directly from the cache.)。

==重要==

默认情况下，请求缓存只会缓存搜索请求size = 0（结果为空）时的请求结果，所以它并不会缓存命中时结果，但是他会缓存`hits.total`, `aggregations`, and `suggestions`.
现在用到的大多数查询都不会缓存 (请参考 “Date Mathedit”章节) .

```
"hits": {
    "total": 0,
    "max_score": null,
    "hits": [ ]
}
```

### 1. 缓存失效

缓存的机制是智能的，它保持与近实时查询一致，即使没有缓存的搜索请求( it keeps the same near real-time promise as uncached search.)。

每当分片刷新，并且只有当分片中的数据确实发生更改时，缓存结果才会自动失效(Cached results are invalidated automatically whenever the shard refreshes, but only if the data in the shard has actually changed)．换句话说，你从缓存中得到的结果与一个没有缓存的搜索请求的结果一样(In other words, you will always get the same results from the cache as you would for an uncached search request)。

刷新时间间隔越长，缓存中条目保持有效的时间越长。 如果缓存已满，最近使用的缓存keys将被驱逐。

缓存可以通过clear-cache API来手动使缓存过期：
```
curl -XPOST 'localhost:9200/kimchy,elasticsearch/_cache/clear?request=true&pretty'
```

### 2. 启用与停用缓存

默认情况下是启用缓存的，但是可以在创建新索引时禁用，如下所示：
```
curl -XPUT 'localhost:9200/my_index?pretty' -d'
{
  "settings": {
    "index.requests.cache.enable": false
  }
}
'
```
也可以使用`update-settings` API在已存在的索引上动态启用或禁用缓存：
```
curl -XPUT 'localhost:9200/my_index/_settings?pretty' -d'
{ "index.requests.cache.enable": true }
'
```

### 3. 启用与停用请求缓存

`request_cache` 查询字符串参数可以设置据每个请求缓存启用或禁用状态。 如果使用此参数进行设置，它将覆盖索引级(index-level)设置：
```
curl -XGET 'localhost:9200/my_index/_search?request_cache=true&pretty' -d'
{
  "size": 0,
  "aggs": {
    "popular_colors": {
      "terms": {
        "field": "colors"
      }
    }
  }
}
'
```

==重要==

如果你的查询中使用了脚本，并且其结果是不确定的（例如，它使用一个随机函数或引用当前的时间）你需要将`request_cache`设置为false，来禁用d对该请求的缓存


当请求size大于0时(Requests size is greater than 0)，即使在索引设置中启用了请求缓存，请求也不会被缓存。 要缓存这些请求，需要使用更详细的查询字符串参数(you will need to use the query-string parameter detailed here.)。

### 4. 缓存key

整个JSON体被用作缓存key。 这意味着如果JSON发生更改 - 例如，如果keys以不同的顺序输出(keys are output in a different order)，则缓存key将不被识别。

==提示==

大多数JSON库都支持规范模式，以确保JSON密钥始终以相同的顺序排列。 该规范模式可以在应用程序中使用，以确保请求始终以相同的方式序列化。


### 5. 缓存设置

缓存在节点级别进行管理，并且默认最大大小为堆的1％。 这可以在config / elasticsearch.yml文件中更改：

```
indices.requests.cache.size: 2%
```

此外，您可以使用`indices.requests.cache.expire`设置为缓存结果指定缓存有效时间TTL，但是没有必要这样做。 记住，当索引被刷新时，陈旧的结果将自动失效。 此设置仅供参考。

### 6. 监控缓存使用

缓存的大小（以字节为单位）和被驱逐次数可以通过索引查看，可以使用`index-stats` API：
```
curl -XGET 'localhost:9200/_stats/request_cache?human&pretty'
```
或节点级别使用`nodes-stats`API：
```
curl -XGET 'localhost:9200/_nodes/stats/indices/request_cache?human&pretty'
```