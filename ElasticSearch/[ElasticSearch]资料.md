

＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝

假设您使用过滤器，您可以禁用的唯一真正相关的过滤器是过滤器缓存（将index.cache.filter.type设置为none）。 通常使用的主要其他缓存是文件系统缓存，这是操作系统级别。

```
- Per-index: 
curl -XGET "http://localhost:9200//_stats" 

- Per-node: 
curl -XGET "http://localhost:9200/_nodes/stats" 

- Entire Cluster (this is actually pretty new, introduced in 0.90.8): 
curl -XGET "http://localhost:9200/_cluster/stats" 
```


资料：

[how-to-monitor-for-filter-cache-churn](https://discuss.elastic.co/t/how-to-monitor-for-filter-cache-churn/15439/4)


[Shard request cache](https://www.elastic.co/guide/en/elasticsearch/reference/current/shard-request-cache.html)

[Node Query Cache](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-cache.html)


[Clear Cache](https://www.elastic.co/guide/en/elasticsearch/reference/current/indices-clearcache.html)


[Get index setting](https://www.elastic.co/guide/en/elasticsearch/reference/current/indices-get-settings.html)

老版本:

[Shard query cache](https://www.elastic.co/guide/en/elasticsearch/reference/1.7/index-modules-shard-query-cache.html#_cache_invalidation)