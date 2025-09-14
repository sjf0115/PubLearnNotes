## 1. 问题

提交作业运行如下 SQL 语句：
```sql
INSERT INTO shop_category_max_price
SELECT
    product_id, category, price, DATE_FORMAT(`timestamp`, 'yyyy-MM-dd HH:mm:ss') AS `time`,
    MAX(price) OVER (PARTITION BY category ORDER BY `timestamp` ROWS BETWEEN 2 preceding AND CURRENT ROW) AS max_price
FROM shop_sales
```
出现如下异常：
```
Exception in thread "main" org.apache.flink.table.api.TableException: OVER windows' ordering in stream mode must be defined on a time attribute.
	at org.apache.flink.table.planner.plan.nodes.exec.stream.StreamExecOverAggregate.translateToPlanInternal(StreamExecOverAggregate.java:156)
	at org.apache.flink.table.planner.plan.nodes.exec.ExecNodeBase.translateToPlan(ExecNodeBase.java:134)
	at org.apache.flink.table.planner.plan.nodes.exec.ExecEdge.translateToPlan(ExecEdge.java:247)
	at org.apache.flink.table.planner.plan.nodes.exec.common.CommonExecCalc.translateToPlanInternal(CommonExecCalc.java:88)
	at org.apache.flink.table.planner.plan.nodes.exec.ExecNodeBase.translateToPlan(ExecNodeBase.java:134)
	at org.apache.flink.table.planner.plan.nodes.exec.ExecEdge.translateToPlan(ExecEdge.java:247)
	at org.apache.flink.table.planner.plan.nodes.exec.stream.StreamExecSink.translateToPlanInternal(StreamExecSink.java:114)
	at org.apache.flink.table.planner.plan.nodes.exec.ExecNodeBase.translateToPlan(ExecNodeBase.java:134)
	at org.apache.flink.table.planner.delegation.StreamPlanner.$anonfun$translateToPlan$1(StreamPlanner.scala:70)
	at scala.collection.TraversableLike.$anonfun$map$1(TraversableLike.scala:233)
	at scala.collection.Iterator.foreach(Iterator.scala:937)
	at scala.collection.Iterator.foreach$(Iterator.scala:937)
	at scala.collection.AbstractIterator.foreach(Iterator.scala:1425)
	at scala.collection.IterableLike.foreach(IterableLike.scala:70)
	at scala.collection.IterableLike.foreach$(IterableLike.scala:69)
	at scala.collection.AbstractIterable.foreach(Iterable.scala:54)
	at scala.collection.TraversableLike.map(TraversableLike.scala:233)
	at scala.collection.TraversableLike.map$(TraversableLike.scala:226)
	at scala.collection.AbstractTraversable.map(Traversable.scala:104)
	at org.apache.flink.table.planner.delegation.StreamPlanner.translateToPlan(StreamPlanner.scala:69)
	at org.apache.flink.table.planner.delegation.PlannerBase.translate(PlannerBase.scala:165)
	at org.apache.flink.table.api.internal.TableEnvironmentImpl.translate(TableEnvironmentImpl.java:1518)
	at org.apache.flink.table.api.internal.TableEnvironmentImpl.executeInternal(TableEnvironmentImpl.java:740)
	at org.apache.flink.table.api.internal.TableEnvironmentImpl.executeInternal(TableEnvironmentImpl.java:856)
	at org.apache.flink.table.api.internal.TableEnvironmentImpl.executeSql(TableEnvironmentImpl.java:730)
	at com.flink.example.sql.funciton.over.RowsOverWindowExample.main(RowsOverWindowExample.java:60)
```

## 2. 解决方案

Over Window 必须基于时间属性，如事件时间或处理时间。所以需要首先查看表 DDL 查看是否是时间属性字段：
```sql
CREATE TABLE shop_sales (
    product_id BIGINT COMMENT '商品Id',
    category STRING COMMENT '商品类目',
    price BIGINT COMMENT '商品价格',
    `timestamp` BIGINT COMMENT '商品上架时间'
) WITH (
    'connector' = 'kafka',
    'topic' = 'shop_sales',
    'properties.bootstrap.servers' = 'localhost:9092',
    'properties.group.id' = 'shop_sales',
    'scan.startup.mode' = 'latest-offset',
    'format' = 'json',
    'json.ignore-parse-errors' = 'false',
    'json.fail-on-missing-field' = 'true'
));
```
需要注意的是在 Flink SQL 中，字段类型为 TIMESTAMP/BIGINT 并不等同于时间属性，时间属性需要显式声明（事件时间或处理时间）才能用于 Over Window 操作。需通过以下方式显式声明：
- 事件时间：通过 WATERMARK 定义（如 WATERMARK FOR ts_ltz AS ts_ltz - INTERVAL '5' SECOND）。
- 处理时间：通过 `PROCTIME()` 生成（如 proc_time AS PROCTIME()）。

若字段未按上述方式声明，即使类型为 TIMESTAMP/BIGINT，也会被视作普通字段而非时间属性。在这是基于事件时间，修改如下所示：
```sql
CREATE TABLE shop_sales (
    product_id BIGINT COMMENT '商品Id',
    category STRING COMMENT '商品类目',
    price BIGINT COMMENT '商品价格',
    `timestamp` BIGINT COMMENT '商品上架时间',
    ts_ltz AS TO_TIMESTAMP_LTZ(`timestamp`, 3), -- 事件时间
    WATERMARK FOR ts_ltz AS ts_ltz - INTERVAL '5' SECOND -- 在 ts_ltz 上定义watermark，ts_ltz 成为事件时间列
) WITH (
  'connector' = 'kafka',
  'topic' = 'shop_sales',
  'properties.bootstrap.servers' = 'localhost:9092',
  'properties.group.id' = 'shop_sales',
  'scan.startup.mode' = 'latest-offset',
  'format' = 'json',
  'json.ignore-parse-errors' = 'false',
  'json.fail-on-missing-field' = 'true'
));
```
