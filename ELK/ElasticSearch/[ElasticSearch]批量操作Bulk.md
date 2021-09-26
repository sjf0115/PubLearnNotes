### 1. Bulk API

批量API(Bulk)允许在单个请求中对多个文档进行索引和删除。 以下是一个示例用法：
```
public static void bulkRequest(String index, String type, String ... sources){

    BulkRequestBuilder bulkRequest = client.prepareBulk();
    for(String source : sources){
        // Index
        IndexRequestBuilder indexRequestBuilder = client.prepareIndex();
        indexRequestBuilder.setIndex(index);
        indexRequestBuilder.setType(type);
        indexRequestBuilder.setSource(source);
        indexRequestBuilder.setTTL(8000);

        bulkRequest.add(indexRequestBuilder);
    }

    BulkResponse bulkResponses = bulkRequest.get();
    if(bulkResponses.hasFailures()){
        logger.error("批量导入失败", bulkResponses.buildFailureMessage());
    }
    else{
        logger.info("批量导入成功");
    }
}

```
测试：

```
String player1 = "{\"country\":\"阿根廷\",\"club\":\"巴萨罗那俱乐部\",\"name\":\"梅西\"}";
String player2 = "{\"country\":\"巴西\",\"club\":\"巴萨罗那俱乐部\",\"name\":\"内马尔\"}";
String player3 = "{\"country\":\"葡萄牙\",\"club\":\"皇家马德里俱乐部\",\"name\":\"C罗\"}";
String player4 = "{\"country\":\"德国\",\"club\":\"拜仁俱乐部\",\"name\":\"诺伊尔\"}";
bulkRequest("football-index", "football-type", player1, player2, player3, player4);
```
### 2. Bulk Processor

BulkProcessor类提供了一个简单的接口，可以根据请求的数量或大小或者在给定的时间段之后自动刷新批量操作(The BulkProcessor class offers a simple interface to flush bulk operations automatically based on the number or size of requests, or after a given period.)。

