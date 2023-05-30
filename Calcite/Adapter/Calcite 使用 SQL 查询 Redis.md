Redis 是一个开源的内存数据结构存储，一般用作数据库、缓存和消息代理。它支持的数据结构包括字符串、哈希、列表、集合、带范围查询的排序集合、位图、HyperLogLogs、带半径查询的地理空间索引和流。

Calcite 的 Redis 适配器可以让你使用 SQL 来查询 Redis 中的数据，并可以与 Calcite 下其他 Schema 中的数据相结合使用。Redis 适配器允许查询存储在 Redis 中的实时数据。每个 Redis 键值对以单行表示，可以使用表定义文件将行分解为列。Redis 适配器支持 `string`、`hash`、`sets`、`zsets`、`list` 数据类型;

首先，我们需要定义一个模型 model，为 Calcite 提供了创建 Redis 适配器实例所需的参数。下面给出了一个模型文件的示例：
```json
{
  "version": "1.0",
  "defaultSchema": "test",
  "schemas": [
    {
      "type": "custom",
      "name": "test",
      "factory": "org.apache.calcite.adapter.redis.RedisSchemaFactory",
      "operand": {
        "host": "localhost",
        "port": 6379,
        "database": 0,
        "password": ""
      },
      "tables": [
        {
          "name": "students_json",
          "factory": "com.calcite.example.adapter.redis.RedisTableFactory",
          "operand": {
            "dataFormat": "json",
            "fields": [
              {
                "name": "id",
                "type": "varchar",
                "mapping": "id"
              },
              {
                "name": "name",
                "type": "varchar",
                "mapping": "name"
              }
            ]
          }
        },
        {
          "name": "raw_01",
          "factory": "org.apache.calcite.adapter.redis.RedisTableFactory",
          "operand": {
            "dataFormat": "raw",
            "fields": [
              {
                "name": "id",
                "type": "varchar",
                "mapping": "id"
              },
              {
                "name": "city",
                "type": "varchar",
                "mapping": "city"
              },
              {
                "name": "pop",
                "type": "int",
                "mapping": "pop"
              }
            ]
          }
        },
        {
          "name": "csv_01",
          "factory": "org.apache.calcite.adapter.redis.RedisTableFactory",
          "operand": {
            "dataFormat": "csv",
            "keyDelimiter": ":",
            "fields": [
              {
                "name": "EMPNO",
                "type": "varchar",
                "mapping": 0
              },
              {
                "name": "NAME",
                "type": "varchar",
                "mapping": 1
              }
            ]
          }
        }
      ]
    }
  ]
}
```
目前 Redis 适配器支持三种格式：`csv`、`json` 以及 `raw`，可以通过 `format` 参数来指定。

format 参数用于指定 Redis 中数据的格式。目前支持 `csv`、`json` 以及 `raw` 三种格式。

映射的功能是将 Redis 的列映射到底层数据。由于 Redis 中没有列的概念，具体的映射方法根据格式不同而不同。例如，对于 `csv` 格式，我们知道经过解析后将形成 CSV 数据。相应的列映射使用底层数组的索引(下标)。在上面的示例中，EMPNO 被映射到索引 0 ,NAME 被映射到索引 1，以此类推。

### Json

JSON 格式解析一个 Redis 字符串值，并使用映射将字段转换为多个列：
```
127.0.0.1:6379> LPUSH students_json '{"id":"1001","name":"Lucy"}'
127.0.0.1:6379> LPUSH students_json
```

```
127.0.0.1:6379> LPUSH students_json_2 '{"id":"1001","name":"Lucy"}'
127.0.0.1:6379> LPUSH students_json_2 '{"id":"1002","name":"Tom"}'
```

```json
{
  "name": "students_json",
  "factory": "com.calcite.example.adapter.redis.RedisTableFactory",
  "operand": {
    "dataFormat": "json",
    "fields": [
      {
        "name": "id",
        "type": "varchar",
        "mapping": "id"
      },
      {
        "name": "name",
        "type": "varchar",
        "mapping": "name"
      }
    ]
  }
}
```

### raw

`raw` 格式保持原始 Redis 键和值不变，查询中只使用一个字段键。

```json
{
  "name": "raw_01",
  "factory": "org.apache.calcite.adapter.redis.RedisTableFactory",
  "operand": {
    "dataFormat": "raw",
    "fields": [
      {
        "name": "id",
        "type": "varchar",
        "mapping": "id"
      },
      {
        "name": "city",
        "type": "varchar",
        "mapping": "city"
      },
      {
        "name": "pop",
        "type": "int",
        "mapping": "pop"
      }
    ]
  }
}
```

### csv

```
127.0.0.1:6379> LPUSH students_csv "1001:Lucy"
127.0.0.1:6379> LPUSH students_csv "1002:Tom"
```

```json
{
  "name": "students_csv",
  "factory": "com.calcite.example.adapter.redis.RedisTableFactory",
  "operand": {
    "dataFormat": "csv",
    "keyDelimiter": ":",
    "fields": [
      {
        "name": "id",
        "type": "varchar",
        "mapping": 0
      },
      {
        "name": "name",
        "type": "varchar",
        "mapping": 1
      }
    ]
  }
}
```

keyDelimiter 用于分割值，默认值是冒号，分割值用于映射字段列。这只适用于CSV格式。







> 参考：[Redis adapter](https://calcite.apache.org/docs/redis_adapter.html)
