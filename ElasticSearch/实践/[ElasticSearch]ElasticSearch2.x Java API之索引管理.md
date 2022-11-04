---
layout: post
author: sjf0115
title: ElasticSearch2.x Java API之索引管理
date: 2016-07-0８ 23:15:17
tags:
  - ElasticSearch

categories: ElasticSearch
permalink: elasticsearch-java-api-index-administration
---

ElasticSearch　为了便于处理索引管理（Indices administration）请求，提供了　org.elasticsearch.client.IndicesAdminClient　接口。通过如下代码从 Client 对象中获得这个接口的实现：
```java
IndicesAdminClient indicesAdminClient = client.admin().indices();
```
IndicesAdminClient 定义了好几种prepareXXX()方法作为创建请求的入口点。

### 1. 判断索引存在

索引存在API用于检查集群中是否存在由 prepareExists 调用指定的索引。
```java
IndicesAdminClient indicesAdminClient = client.admin().indices();
IndicesExistsResponse response = indicesAdminClient.prepareExists(index).get();
response.isExists();
// 另一种方式
IndicesExistsRequest indicesExistsRequest = new IndicesExistsRequest(index);
IndicesExistsResponse response = client.admin().indices().exists(indicesExistsRequest).actionGet();
response.isExists();
```

prepareExists() 可以同时指定多个索引：
```java
IndicesExistsResponse response = indicesAdminClient.prepareExists(index1, index2 ....).get();
```

### 2. 判断类型存在

类型存在API和索引存在API类似，只是不是用来检查索引是否存在，而是检查指定索引下的指定类型是否存在。为了确保成功返回结果，请确保索引已经存在，否则不会查找到指定的类型。下面代码演示查找索引下的指定类型：
```java
IndicesAdminClient indicesAdminClient = client.admin().indices();
TypesExistsResponse response = indicesAdminClient.prepareTypesExists(index).setTypes(type).get();
response.isExists();
```

### 3. 创建索引API

创建索引API可以用来建立一个新索引。我们可以创建空索引或者给它设置它的映射(mapping)和设置信息(settings)。

#### 3.1 创建空索引

下面代码创建了一个空索引：
```java
IndicesAdminClient indicesAdminClient = client.admin().indices();
CreateIndexResponse response = indicesAdminClient.prepareCreate(index).get();
response.isAcknowledged();
```
查看索引状态信息：
```json
{
    "state": "open",
    "settings": {
        "index": {
            "creation_date": "1476078197394",
            "number_of_shards": "5",
            "number_of_replicas": "1",
            "uuid": "rBATEkx_SBq_oUEIlW8ryQ",
            "version": {
                "created": "2030399"
            }
        }
    },
    "mappings": {

    },
    "aliases": [

    ]
}
```

#### 3.2. 创建复杂索引

下面代码创建复杂索引，给它设置它的映射(mapping)和设置信息(settings)，指定分片个数为3，副本个数为2，同时设置 school 字段不分词。
```java
// settings
Settings settings = Settings.builder().put("index.number_of_shards", 3).put("index.number_of_replicas", 2).build();
// mapping
XContentBuilder mappingBuilder;
mappingBuilder = XContentFactory.jsonBuilder()
        .startObject()
            .startObject(index)
                .startObject("properties")
                    .startObject("name").field("type", "string").field("store", "yes").endObject()
                    .startObject("sex").field("type", "string").field("store", "yes").endObject()
                    .startObject("college").field("type", "string").field("store", "yes").endObject()
                    .startObject("age").field("type", "integer").field("store", "yes").endObject()
                    .startObject("school").field("type", "string").field("store", "yes").field("index", "not_analyzed").endObject()
                .endObject()
            .endObject()
        .endObject();
IndicesAdminClient indicesAdminClient = client.admin().indices();
CreateIndexResponse response = indicesAdminClient.prepareCreate(index)
        .setSettings(settings)
        .addMapping(index, mappingBuilder)
        .get();
response.isAcknowledged();
```

查看索引状态信息：
```json
{
    "state": "open",
    "settings": {
        "index": {
            "creation_date": "1476078400025",
            "number_of_shards": "3",
            "number_of_replicas": "2",
            "uuid": "ToakRDisSYyX7vjH30HR-g",
            "version": {
                "created": "2030399"
            }
        }
    },
    "mappings": {
        "simple-index": {
            "properties": {
                "college": {
                    "store": true,
                    "type": "string"
                },
                "school": {
                    "index": "not_analyzed",
                    "store": true,
                    "type": "string"
                },
                "sex": {
                    "store": true,
                    "type": "string"
                },
                "name": {
                    "store": true,
                    "type": "string"
                },
                "age": {
                    "store": true,
                    "type": "integer"
                }
            }
        }
    },
    "aliases": [

    ]
}
```
### 4. 删除索引

删除索引API允许我们反向删除一个或者多个索引。

    /**
     * 删除索引
     * @param client
     * @param index
     */
    public static boolean deleteIndex(Client client, String index) {
        IndicesAdminClient indicesAdminClient = client.admin().indices();
        DeleteIndexResponse response = indicesAdminClient.prepareDelete(index).execute().actionGet();
        return response.isAcknowledged();
    }

### 5. 关闭索引

关闭索引API允许我们关闭不使用的索引，进而释放节点和集群的资源，如cpu时钟周期和内存。

    /**
     * 关闭索引
     * @param client
     * @param index
     * @return
     */
    public static boolean closeIndex(Client client, String index){
        IndicesAdminClient indicesAdminClient = client.admin().indices();
        CloseIndexResponse response = indicesAdminClient.prepareClose(index).get();
        return response.isAcknowledged();
    }
测试：

    @Test
    public void closeIndex() throws Exception {
        String index = "suggestion-index";
        if(!IndexAPI.isIndexExists(client, index)){
            logger.info("--------- closeIndex 索引 [{}] 不存在", index);
            return;
        }
        boolean result = IndexAPI.closeIndex(client, index);
        logger.info("--------- closeIndex {}",result);
    }
关闭之前：

![image](http://img.blog.csdn.net/20170512111817468?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

关闭之后：

![image](http://img.blog.csdn.net/20170512111801952?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

### 6. 打开索引

打开索引API允许我们打开我们之前使用关闭索引API

    /**
     * 关闭索引
     * @param client
     * @param index
     * @return
     */
    public static boolean openIndex(Client client, String index){
        IndicesAdminClient indicesAdminClient = client.admin().indices();
        OpenIndexResponse response = indicesAdminClient.prepareOpen(index).get();
        return response.isAcknowledged();
    }

### 7. 设置映射API

设置映射API允许我们在指定索引上一次性创建或修改一到多个索引的映射。如果设置映射必须确保指定的索引必须存在，否则会报错。

    /**
     * 设置映射
     * @param client
     * @param index
     * @param type
     * @return
     */
    public static boolean putIndexMapping(Client client, String index, String type){
        // mapping
        XContentBuilder mappingBuilder;
        try {
            mappingBuilder = XContentFactory.jsonBuilder()
                    .startObject()
                        .startObject(type)
                            .startObject("properties")
                                .startObject("name").field("type", "string").field("store", "yes").endObject()
                                .startObject("sex").field("type", "string").field("store", "yes").endObject()
                                .startObject("college").field("type", "string").field("store", "yes").endObject()
                                .startObject("age").field("type", "long").field("store", "yes").endObject()
                                .startObject("school").field("type", "string").field("store", "yes").field("index", "not_analyzed").endObject()
                            .endObject()
                        .endObject()
                    .endObject();
        } catch (Exception e) {
            logger.error("--------- createIndex 创建 mapping 失败：", e);
            return false;
        }
        IndicesAdminClient indicesAdminClient = client.admin().indices();
        PutMappingResponse response = indicesAdminClient.preparePutMapping(index).setType(type).setSource(mappingBuilder).get();
        return response.isAcknowledged();
    }
先创建一个空索引，这样该索引上不会有映射，再使用下面代码添加映射：

    @Test
    public void putIndexMapping() throws Exception {
        String index = "simple-index";
        String type = "simple-type";
        if(!IndexAPI.isIndexExists(client, index)){
            logger.info("--------- putIndexMapping 索引 [{}] 不存在", index);
            return;
        }
        boolean result = IndexAPI.putIndexMapping(client, index, type);
        logger.info("--------- putIndexMapping {}",result);
    }
添加映射之后的索引信息：
```
{
    "state": "open",
    "settings": {
        "index": {
            "creation_date": "1476108496237",
            "number_of_shards": "5",
            "number_of_replicas": "1",
            "uuid": "9SR5OQJ-QLSARFjmimvs1A",
            "version": {
                "created": "2030399"
            }
        }
    },
    "mappings": {
        "simple-type": {
            "properties": {
                "college": {
                    "store": true,
                    "type": "string"
                },
                "school": {
                    "index": "not_analyzed",
                    "store": true,
                    "type": "string"
                },
                "sex": {
                    "store": true,
                    "type": "string"
                },
                "name": {
                    "store": true,
                    "type": "string"
                },
                "age": {
                    "store": true,
                    "type": "long"
                }
            }
        }
    },
    "aliases": [

    ]
}
```

### 8. 别名API

别名API允许我们可以为已经存在的索引创建别名

    /**
     * 为索引创建别名
     * @param client
     * @param index
     * @param alias
     * @return
     */
    public static boolean addAliasIndex(Client client, String index , String alias){
        IndicesAdminClient indicesAdminClient = client.admin().indices();
        IndicesAliasesResponse response = indicesAdminClient.prepareAliases().addAlias(index, alias).get();
        return response.isAcknowledged();
    }
测试：下面代码为simple-index索引创建一个别名为simple：

    @Test
    public void addAliasIndex() throws Exception {
        String index = "simple-index";
        String aliasName = "simple";
        boolean result = IndexAPI.addAliasIndex(client, index, aliasName);
        logger.info("--------- addAliasIndex {}", result);
    }
结果图：

![image](http://img.blog.csdn.net/20170512111746670?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)



### 9.  别名存在API

别名存在API允许我们检查是否存在至少一个我们列举出的的别名，注意是判断的索引别名，不是索引。我们可以在别名中使用星号通配符。

    /**
     * 判断别名是否存在
     * @param client
     * @param aliases
     * @return
     */
    public static boolean isAliasExist(Client client, String... aliases){
        IndicesAdminClient indicesAdminClient = client.admin().indices();
        AliasesExistResponse response = indicesAdminClient.prepareAliasesExist(aliases).get();
        return response.isExists();
    }
测试，下面代码检查以sim开头的索引别名和test索引别名是否存在，我们列举的索引别名只要有一个存在就会返回true。

    @Test
    public void isAliasExist() throws Exception {
        String aliasName = "simp*";
        String aliasName2 = "test";
        boolean result = IndexAPI.isAliasExist(client, aliasName, aliasName2);
        logger.info("--------- isAliasExist {}", result); // true
    }


### 10. 获取别名API

获取别名API可以列举出当前已经定义的的别名

    /**
     * 获取别名
     * @param client
     * @param aliases
     */
    public static void getAliasIndex(Client client, String... aliases){
        IndicesAdminClient indicesAdminClient = client.admin().indices();
        GetAliasesResponse response = indicesAdminClient.prepareGetAliases(aliases).get();
        ImmutableOpenMap<String, List<AliasMetaData>> aliasesMap = response.getAliases();
        UnmodifiableIterator<String> iterator = aliasesMap.keysIt();
        while(iterator.hasNext()){
            String key = iterator.next();
            List<AliasMetaData> aliasMetaDataList = aliasesMap.get(key);
            for(AliasMetaData aliasMetaData : aliasMetaDataList){
                logger.info("--------- getAliasIndex {}", aliasMetaData.getAlias());
            }
        }
    }
测试，下面代码展示以sim开头的别名和test别名：

    @Test
    public void getAliasIndex() throws Exception {
        String aliasName = "simp*";
        String aliasName2 = "test";
        IndexAPI.getAliasIndex(client, aliasName, aliasName2); // simple test
    }


### 11. 删除别名API

删除别名API允许我们删除指定索引的别名，如果索引没有该别名，则会报错

    /**
     * 删除别名
     * @param client
     * @param index
     * @param aliases
     * @return
     */
    public static boolean deleteAliasIndex(Client client, String index, String... aliases){
        IndicesAdminClient indicesAdminClient = client.admin().indices();
        IndicesAliasesResponse response = indicesAdminClient.prepareAliases().removeAlias(index, aliases).get();
        return response.isAcknowledged();
    }
测试，下面代码删除test-index索引的别名test：

    @Test
    public void deleteAliasIndex() throws Exception {
        String index = "test-index";
        String aliasName = "test";
        boolean result = IndexAPI.deleteAliasIndex(client, index, aliasName);
        logger.info("--------- deleteAliasIndex {}", result); // true
    }


### 12. 更新设置API

更新设置API允许我们更新特定索引或全部索引的设置。

    /**
     * 更新设置
     * @param client
     * @param index
     * @param settings
     * @return
     */
    public static boolean updateSettingsIndex(Client client, String index, Settings settings){
        IndicesAdminClient indicesAdminClient = client.admin().indices();
        UpdateSettingsResponse response = indicesAdminClient.prepareUpdateSettings(index).setSettings(settings).get();
        return response.isAcknowledged();
    }
测试，下面代码更改副本数为2，修改分片个数会报错：

    @Test
    public void updateSettingsIndex() throws Exception {
        String index = "test-index";
        Settings settings = Settings.builder().put("index.number_of_replicas", 2).build();
        if(!IndexAPI.isIndexExists(client, index)){
            logger.info("--------- updateSettingsIndex 索引 [{}] 不存在", index);
            return;
        }
        boolean result = IndexAPI.updateSettingsIndex(client, index, settings);
        logger.info("--------- updateSettingsIndex {}", result); // true
    }


### 13. 索引统计API

索引统计API可以提供关于索引，文档，存储以及操作的信息，如获取，查询，索引等。这些信息按类别进行了划分，如果需要输出特定信息需要在请求时指定。下面代码演示了获取指定索引的全部信息：

    /**
     * 索引统计
     * @param client
     * @param index
     */
    public static void indexStats(Client client, String index) {
        IndicesAdminClient indicesAdminClient = client.admin().indices();
        IndicesStatsResponse response = indicesAdminClient.prepareStats(index).all().get();
        ShardStats[] shardStatsArray = response.getShards();
        for(ShardStats shardStats : shardStatsArray){
            logger.info("shardStats {}",shardStats.toString());
        }
        Map<String, IndexStats> indexStatsMap = response.getIndices();
        for(String key : indexStatsMap.keySet()){
            logger.info("indexStats {}", indexStatsMap.get(key));
        }
        CommonStats commonStats = response.getTotal();
        logger.info("total commonStats {}",commonStats.toString());
        commonStats = response.getPrimaries();
        logger.info("primaries commonStats {}", commonStats.toString());
    }




完成代码与演示地址：

https://github.com/sjf0115/OpenDiary/blob/master/ElasticSearchDemo/src/main/java/com/sjf/open/api/IndexAPI.java

https://github.com/sjf0115/OpenDiary/blob/master/ElasticSearchDemo/src/test/java/com/sjf/open/api/IndexAPITest.java

> ElascticSearch版本：2.x
> ElacticSearch Java 版本：6.2

参考: https://www.elastic.co/guide/en/elasticsearch/client/java-api/6.2/java-admin-indices.html#java-admin-indices-create-index
