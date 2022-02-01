---
layout: post
author: sjf0115
title: ElasticSearch Term精准匹配中文字符串短语
date: 2016-07-06 23:15:17
tags:
  - ElasticSearch

categories: ElasticSearch
permalink: elasticsearch-term-exact-match-string
---

### 1. 给定数据
```
curl -XPUT 'localhost:9200/test-index/stu/1' -d'
{
    "name":"陈泽鹏",
    "sex":"boy",
    "college":"计算机学院"
}';
curl -XPUT 'localhost:9200/test-index/stu/2' -d'
{
    "name":"廖力生",
    "sex":"boy",
    "college":"通信学院"
}';
curl -XPUT 'localhost:9200/test-index/stu/3' -d'
{
    "name":"李源一",
    "sex":"girl",
    "college":"计算机学院"
}';
curl -XPUT 'localhost:9200/test-index/stu/4' -d'
{
    "name":"陈哲超",
    "sex":"girl",
    "college":"计算机学院"
}';
curl -XPUT 'localhost:9200/test-index/stu/5' -d'
{
    "name":"AA",
    "sex":"girl",
    "college":"计算机学院"
}';
curl -XPUT 'localhost:9200/test-index/stu/6' -d'
{
    "name":"bb",
    "sex":"girll",
    "college":"通信学院"
}';
curl -XPUT 'localhost:9200/test-index/stu/7' -d'
{
    "name":"方镜淇",
    "sex":"boy",
    "college":"电子工程学院"
}';
curl -XPUT 'localhost:9200/test-index/stu/8' -d'
{
    "name":"吴兴涵",
    "sex":"boy",
    "college":"计算机学院"
}';
```

### 2. 需求

我们想精确匹配出来自计算机学院的学生，所以我们就实现如下语句：
```java
// Query
QueryBuilder queryBuilder = QueryBuilders.termQuery("college", "计算机学院");
// Search
SearchRequestBuilder searchRequestBuilder = client.prepareSearch(index);
searchRequestBuilder.setTypes(type);
searchRequestBuilder.setQuery(queryBuilder);
// 执行
SearchResponse searchResponse = searchRequestBuilder.execute().actionGet();
```

返回结果：
```
20:30:46.815 [main] INFO  com.sjf.open.api.TermLevelQuery - ----------termMatch size 0
表示没有找到来自计算机学院的同学，这咋可能。。。。
```

### 3. 解决方案一

把计算机学院拆分成多个汉字，再利用bool查询查找：
```java
// Query
BoolQueryBuilder boolQueryBuilder = QueryBuilders.boolQuery();
boolQueryBuilder.must(QueryBuilders.termQuery("college", "计"));
boolQueryBuilder.must(QueryBuilders.termQuery("college", "算"));
boolQueryBuilder.must(QueryBuilders.termQuery("college", "机"));
boolQueryBuilder.must(QueryBuilders.termQuery("college", "学"));
boolQueryBuilder.must(QueryBuilders.termQuery("college", "院"));
// Search
SearchRequestBuilder searchRequestBuilder = client.prepareSearch(index);
searchRequestBuilder.setTypes(type);
searchRequestBuilder.setQuery(boolQueryBuilder);
// 执行
SearchResponse searchResponse = searchRequestBuilder.execute().actionGet();
```

返回结果：
```
20:34:53.022 [main] INFO  com.sjf.open.api.Search - ----------hit source: id 5 source {college=计算机学院, sex=girll, name=AA}
20:34:53.028 [main] INFO  com.sjf.open.api.Search - ----------hit source: id 8 source {college=计算机学院, sex=boy, name=吴兴涵}
20:34:53.029 [main] INFO  com.sjf.open.api.Search - ----------hit source: id 1 source {college=计算机学院, sex=boy, name=陈泽鹏}
20:34:53.029 [main] INFO  com.sjf.open.api.Search - ----------hit source: id 7 source {college=计算机学院, sex=boy, name=陈哲超}
20:34:53.029 [main] INFO  com.sjf.open.api.Search - ----------hit source: id 3 source {college=计算机学院, sex=girll, name=李源一}
```
### 4. 解决方案二

设置字段属性，设置为 not_analyzed，再插入上面数据：
```json
curl -XPUT 'localhost:9200/test-index' -d'
{
    "mappings":{
            "stu":{
                     "properties":{
                          "name":{
                              "type":"string"
                           },
                          "sex":{
                              "type":"string"
                           },
                          "college":{
                              "type":"string",
                              "index":"not_analyzed"
                          }
                     }
            }
    }
}';
```
具体分析：https://www.elastic.co/guide/en/elasticsearch/reference/2.3/query-dsl-term-query.html

```java
// Query
QueryBuilder queryBuilder = QueryBuilders.termQuery("college", "计算机学院");
// Search
SearchRequestBuilder searchRequestBuilder = client.prepareSearch(index);
searchRequestBuilder.setTypes(type);
searchRequestBuilder.setQuery(queryBuilder);
// 执行
SearchResponse searchResponse = searchRequestBuilder.execute().actionGet();
```

输出结果：
```
20:34:53.022 [main] INFO  com.sjf.open.api.Search - ----------hit source: id 5 source {college=计算机学院, sex=girll, name=AA}
20:34:53.028 [main] INFO  com.sjf.open.api.Search - ----------hit source: id 8 source {college=计算机学院, sex=boy, name=吴兴涵}
20:34:53.029 [main] INFO  com.sjf.open.api.Search - ----------hit source: id 1 source {college=计算机学院, sex=boy, name=陈泽鹏}
20:34:53.029 [main] INFO  com.sjf.open.api.Search - ----------hit source: id 7 source {college=计算机学院, sex=boy, name=陈哲超}
20:34:53.029 [main] INFO  com.sjf.open.api.Search - ----------hit source: id 3 source {college=计算机学院, sex=girll, name=李源一}
```
