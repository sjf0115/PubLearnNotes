
## 1. Common Join

Common Join 是 Hive 中的默认 Join 类型，也称为 Reduce Side Join。在 Join 期间，两个表中的所有行都根据 Join Key 分布到所有节点。这样，有相同 Join Key 的值最终会出现在同一个节点上。

![](1)

工作流程：
- 在 Map 阶段，Mapper 从表中读取数据并以 Join 列值作为 Key 输出到一个中间文件。
- 在 Shuffle 阶段，这些键值对被排序以及合并。有相同 Key 的行都会被发送到同一个 Reducer 实例上。
- 在 Reduce 阶段，Reducer 获取排序后的数据并进行 Join。

Common Join 的优点是可以适用于任何大小的表。但由于 Shuffle 操作代价比较高，因此非常耗费资源。如果一个或多个 Join Key 占据了很大比例的数据，相应的 Reducer 实例负载就会很高，需要运行很长时间。问题是大多数 Reducer 实例已经完成了 Join 操作，只有部分实例仍在运行。查询的总运行时间由运行时间最长的 Reducer 决定。显然，这是一个典型的数据倾斜问题。

如何识别 Common Join：使用 EXPLAIN 命令时，在 Reduce Operator Tree 下方看到 Join Operator。

## 2. Map Join



## 3. Bucket map join

## 4. Sort merge bucket (SMB) join


## 5. Sort merge bucket map (SMBM) join

## 6. Skew join
