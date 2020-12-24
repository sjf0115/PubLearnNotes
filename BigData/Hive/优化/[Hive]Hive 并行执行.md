

Hadoop可以并行执行 map reduce 作业，并在 Hive 执行几个查询时会自动使用这种并行性。但是，单个复杂的 Hive 查询通常会转换为几个按顺序执行的 map reduce 作业。但是某些查询的 map reduce stage 不是相互依赖的，是可以并行执行的。

可以利用集群上的空闲容量来提高集群的利用率，同时减少总体查询的执行时间。Hive 中用于更改此行为的配置是 `SET hive.exec.parallel = true;`。

![]()

上图中 Hive 并行阶段执行查询的示例，我们可以看到两个子查询是独立的，当我们启用并行执行时，会并行处理。

```sql
EXPLAIN SELECT success.platform, success.channelId, success.md5KeyId, success.price, success.time AS success_time, price.time AS price_time
FROM
(
  SELECT
    get_json_object(line,'$.requestId') AS requestId,
    get_json_object(line,'$.os') AS platform,
    get_json_object(line,'$.channelId') AS channelId,
    get_json_object(line,'$.md5_device_id') AS md5KeyId,
    get_json_object(line,'$.price') AS price,
    time
  FROM adv_push_success
  WHERE dt = '20180728'
) success
JOIN
(
  SELECT get_json_object(line,'$.requestId') AS requestId, time
  FROM adv_push_price
  WHERE dt = '20180728' AND line IS NOT NULL
) price
ON UPPER(success.requestId) = UPPER(price.requestId);


EXPLAIN SELECT success.platform, success.channelId, COUNT(success.md5KeyId)
FROM
(
  SELECT
    get_json_object(line,'$.requestId') AS requestId,
    get_json_object(line,'$.os') AS platform,
    get_json_object(line,'$.channelId') AS channelId,
    get_json_object(line,'$.md5_device_id') AS md5KeyId,
    get_json_object(line,'$.price') AS price,
    time
  FROM adv_push_success
  WHERE dt = '20180728'
) success
JOIN
(
  SELECT get_json_object(line,'$.requestId') AS requestId, time
  FROM adv_push_price
  WHERE dt = '20180728' AND line IS NOT NULL
) price
ON UPPER(success.requestId) = UPPER(price.requestId)
GROUP BY success.platform, success.channelId;
```



hive.exec.parallel
Default Value: false
Added In: Hive 0.5.0
Whether to execute jobs in parallel.  Applies to MapReduce jobs that can run in parallel, for example jobs processing different source tables before a join.  As of Hive 0.14, also applies to move tasks that can run in parallel, for example moving files to insert targets during multi-insert.
hive.exec.parallel.thread.number
Default Value: 8
Added In: Hive 0.6.0
How many jobs at most can be executed in parallel.
