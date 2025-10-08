## 1. 问题

执行如下语句时遇到了 `unexpected block data` 异常：
```sql
Flink SQL> INSERT INTO enriched_orders
>  SELECT o.*, p.name, p.description, s.shipment_id, s.origin, s.destination, s.is_arrived
>  FROM orders AS o
>  LEFT JOIN products AS p ON o.product_id = p.id
>  LEFT JOIN shipments AS s ON o.order_id = s.order_id;
[ERROR] Could not execute SQL statement. Reason:
java.io.StreamCorruptedException: unexpected block data
```

## 2. 解决方案

类加载顺序问题，flink 默认是 child-first，在 flink 的 flink-conf.yaml 文件中将 `classloader.resolve-order: child-first` 改成 `parent-first`，重启集群即可。
