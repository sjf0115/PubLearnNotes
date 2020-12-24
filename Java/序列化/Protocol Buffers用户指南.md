
### 1. 定义一个消息类型

先来看一个非常简单的例子。假设你想定义一个搜索请求的消息格式，每一个请求都包含一个查询字符串、你感兴趣的查询结果所在的页数，以及每一页有多少条查询结果。可以采用如下方式来定义消息类型的`.proto`文件：
```
message SearchRequest {
  required string query = 1;
  optional int32 page_number = 2;
  optional int32 result_per_page = 3;
}
```
