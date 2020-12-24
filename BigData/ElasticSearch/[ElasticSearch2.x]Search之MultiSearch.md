---
layout: post
author: sjf0115
title: ElasticSearch Search之MultiSearch
date: 2016-07-0８ 23:15:17
tags:
  - ElasticSearch

categories: ElasticSearch
permalink: elasticsearch-search-multi-search
---

多搜索API允许在同一个 API 中执行多个搜索请求。它的端点是　`_msearch`。

```
curl -XGET 'localhost:9200/twitter/_msearch?pretty' -H 'Content-Type: application/json' -d'
{}
{"query" : {"match_all" : {}}, "from" : 0, "size" : 10}
{}
{"query" : {"match_all" : {}}}
{"index" : "twitter2"}
{"query" : {"match_all" : {}}}
'
```



















```java
SearchRequestBuilder srb1 = client.prepareSearch().setQuery(QueryBuilders.queryStringQuery("elasticsearch")).setSize(1);
SearchRequestBuilder srb2 = client.prepareSearch().setQuery(QueryBuilders.matchQuery("name", "kimchy")).setSize(1);

MultiSearchResponse multiSearchResponse = client.prepareMultiSearch().add(srb1).add(srb2).get();

MultiSearchResponse.Item[] responseItem = multiSearchResponse.getResponses();
long nbHits = 0;
for (MultiSearchResponse.Item item : responseItem) {
    SearchResponse response = item.getResponse();
    SearchHit[] searchHits = searchResponse.getHits().getHits();
    // 一次搜索的多个结果
    for(SearchHit searchHit : searchHits){
      xxx = searchHit.getSource();
    }
}
```



















原文：　https://www.elastic.co/guide/en/elasticsearch/reference/6.2/search-multi-search.html
