
## 1. 语法示例

Redis 结果表支持 5 种 Redis 数据结构，其DDL定义如下。

### 1.1 STRING类型

DDL为两列：第1列为key，第2列为value。Redis插入数据的命令为 `set key value`：
```sql
create table resik_output (
  a varchar,
  b varchar,
  primary key(a)
) with (
  type = 'redis',
  mode = 'string',
  host = '${redisHost}', -- 例如，'127.0.0.1'。
  port = '${redisPort}', -- 例如，'6379'。
  dbNum = '${dbNum}', -- 默认值为0。
  ignoreDelete = 'true' -- 收到Retraction时，是否删除已插入的数据，默认值为false。
);
```
### 1.2 LIST类型

DDL为两列：第1列为key，第2列为value。Redis插入数据的命令为 `lpush key value`：
```sql
create table resik_output (
  a varchar,
  b varchar,
  primary key(a)
) with (
  type = 'redis',
  mode = 'list',
  host = '${redisHost}', -- 例如，'127.0.0.1'。
  port = '${redisPort}', -- 例如，'6379'。
  dbNum = '${dbNum}', -- 默认值为0。
  ignoreDelete = 'true' -- 收到Retraction时，是否删除已插入的数据，默认值为false。
);
```
### 1.3 SET类型

DDL为两列：第1列为key，第2列为value。Redis插入数据的命令为 `sadd key value`：
```sql
create table resik_output (
  a varchar,
  b varchar,
  primary key(a)
) with (
  type = 'redis',
  mode = 'set',
  host = '${redisHost}', -- 例如，'127.0.0.1'。
  port = '${redisPort}', -- 例如，'6379'。
  dbNum = '${dbNum}', -- 默认值为0。
  ignoreDelete = 'true' -- 收到Retraction时，是否删除已插入的数据，默认值为false。
);
```
### 1.4 HASHMAP类型

DDL为三列：第1列为key，第2列为hash_key，第3列为hash_key对应的hash_value。Redis插入数据的命令为 `hmset key hash_key hash_value`：
```sql
create table resik_output (
  a varchar,
  b varchar,
  c varchar,
  primary key(a)
) with (
  type = 'redis',
  mode = 'hashmap',
  host = '${redisHost}', -- 例如，'127.0.0.1'。
  port = '${redisPort}', -- 例如，'6379'。
  dbNum = '${dbNum}', -- 默认值为0。
  ignoreDelete = 'true' -- 收到Retraction时，是否删除已插入的数据，默认值为false。
);
```
### 1.5 SORTEDSET类型

DDL为三列：第1列为key，第2列为score，第3列为value。Redis插入数据的命令为 `add key score value`：
```sql
create table resik_output (
  a varchar,
  b double,  --必须为DOUBLE类型。
  c varchar,
  primary key(a)
) with (
  type = 'redis',
  mode = 'sortedset',
  host = '${redisHost}', -- 例如，'127.0.0.1'。
  port = '${redisPort}', -- 例如，'6379'。
  dbNum = '${dbNum}', -- 默认值为0。
  ignoreDelete = 'true' -- 收到Retraction时，是否删除已插入的数据，默认值为false。
);
```
## 2. WITH参数

| 参数 | 参数说明 | 是否必填 | 取值 |
| :------------- | :------------- | :------------- | :------------- |
| type | 结果表类型 | 是 | 固定值为redis。|
| mode	| 对应Redis的数据结构	| 是 | 取值如下：string、list、set、hashmap、sortedset |
| host	| Redis Server对应地址	| 是 | 取值示例：127.0.0.1。|
| port	| Redis Server对应端口	| 否 |	默认值为6379。|
| dbNum	| Redis Server对应数据库序号	| 否 |默认值为0。 |
| ignoreDelete	| 是否忽略Retraction消息	| 否 |默认值为false，可取值为true或false。如果设置为false，收到Retraction时，同时删除数据对应的key及已插入的数据。|
| password	| Redis Server对应的密码	| 否 | 默认值为空，不进行权限验证。|
| clusterMode	| Redis是否为集群模式	| 否 | 取值如下：true：Redis为集群模式。flalse（默认值）：Redis为单机模式。|






。。。
