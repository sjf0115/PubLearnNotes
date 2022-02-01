---
layout: post
author: sjf0115
title: ElasticSearch2.x Java API之索引文档
date: 2016-07-07 23:15:17
tags:
  - ElasticSearch

categories: ElasticSearch
permalink: elasticsearch-java-api-index-doc
---

Index API 允许我们存储一个JSON格式的文档，使数据可以被搜索。文档通过index、type、id唯一确定。我们可以自己提供一个id，或者也使用Index API 为我们自动生成一个。

这里有几种不同的方式来产生JSON格式的文档(document)：
- 手动方式，使用原生的byte[]或者String
- 使用Map方式，会自动转换成与之等价的JSON
- 使用第三方库来序列化beans，如Jackson
- 使用内置的帮助类 XContentFactory.jsonBuilder()

### 1. 手动方式

```java
// Index
IndexRequestBuilder indexRequestBuilder = client.prepareIndex();
indexRequestBuilder.setIndex(index);
indexRequestBuilder.setType(type);
indexRequestBuilder.setId(id);
indexRequestBuilder.setSource(json);
indexRequestBuilder.setTTL(8000);
// 执行
IndexResponse indexResponse = indexRequestBuilder.get();
```
测试，下面代码存储梅西信息到索引为football-index，类型为football-type，id为1的文档中：
```java
String index = "football-index";
String type = "football-type";
String id = "1";
String json = "{" +
        "\"club\":\"巴萨罗那\"," +
        "\"country\":\"阿根廷\"," +
        "\"name\":\"梅西\"" +
        "}";
```

### 2. Map方式

```java
// Index
IndexRequestBuilder indexRequestBuilder = client.prepareIndex();
indexRequestBuilder.setIndex(index);
indexRequestBuilder.setType(type);
indexRequestBuilder.setId(id);
indexRequestBuilder.setSource(map);
indexRequestBuilder.setTTL(8000);
// 执行
IndexResponse indexResponse = indexRequestBuilder.get();
```
测试，下面代码存储穆勒信息到索引为football-index，类型为football-type，id为2的文档中：
```java
String index = "football-index";
String type = "football-type";
String id = "2";
Map<String, Object> map = Maps.newHashMap();
map.put("name", "穆勒");
map.put("club", "拜仁慕尼黑俱乐部");
map.put("country", "德国");
```

### 3.  序列化方式

```java
// Bean转换为字节
ObjectMapper mapper = new ObjectMapper();
byte[] json;
try {
    json = mapper.writeValueAsBytes(bean);
} catch (JsonProcessingException e) {
    logger.error("---------- json 转换失败 Bean:{}", bean.toString());
    return false;
}
// Index
IndexRequestBuilder indexRequestBuilder = client.prepareIndex();
indexRequestBuilder.setIndex(index);
indexRequestBuilder.setType(type);
indexRequestBuilder.setId(id);
indexRequestBuilder.setSource(json);
indexRequestBuilder.setTTL(8000);
// 执行
IndexResponse response = indexRequestBuilder.get();
```

测试，下面代码存储卡卡信息到索引为football-index，类型为football-type，id为3的文档中：
```java
String index = "football-index";
String type = "football-type";
String id = "3";
FootballPlayer footballPlayer = new FootballPlayer();
footballPlayer.setName("卡卡");
footballPlayer.setClub("奥兰多城俱乐部");
footballPlayer.setCountry("巴西");
```

### 4.  XContentBuilder帮助类方式

ElasticSearch提供了一个内置的帮助类XContentBuilder来产生JSON文档
```java
// Index
IndexRequestBuilder indexRequestBuilder = client.prepareIndex();
indexRequestBuilder.setIndex(index);
indexRequestBuilder.setType(type);
indexRequestBuilder.setId(id);
indexRequestBuilder.setSource(xContentBuilder);
indexRequestBuilder.setTTL(8000);
// 执行
IndexResponse response = indexRequestBuilder.get();
```

测试，下面代码存储托雷斯信息到索引为football-index，类型为football-type，id为4的文档中：
```java
String index = "football-index";
String type = "football-type";
String id = "4";
XContentBuilder xContentBuilder;
try {
    xContentBuilder = XContentFactory.jsonBuilder();
    xContentBuilder
            .startObject()
                .field("name", "托雷斯")
                .field("club", "马德里竞技俱乐部")
                .field("country", "西班牙")
            .endObject();
} catch (IOException e) {
    logger.error("----------indexDocByXContentBuilder create xContentBuilder failed", e);
    return;
}
```
备注:
```
你还可以通过startArray(string)和endArray()方法添加数组。.field()方法可以接受多种对象类型。你可以给它传递数字、日期、甚至其他XContentBuilder对象。
```

> ElasticSearch版本:2.x


参考：https://www.elastic.co/guide/en/elasticsearch/client/java-api/2.x/java-docs-index.html#java-docs-index-generate
