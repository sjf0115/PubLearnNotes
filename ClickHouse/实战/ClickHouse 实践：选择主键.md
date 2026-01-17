https://clickhouse.com/docs/zh/best-practices/choosing-a-primary-key





对于熟悉 OLTP 数据库（例如 Postgres）中类似术语的读者而言，ClickHouse 中 primary key 的工作方式有很大不同。







选择与排序键不同的主键
可以指定一个与排序键不同的主键（一个表达式，其值会在每个标记的索引文件中写入）。在这种情况下，主键表达式元组必须是排序键表达式元组的前缀。

在使用 SummingMergeTree 和 AggregatingMergeTree 表引擎时，这一特性非常有用。在这些引擎的常见使用场景中，表通常有两类列：维度（dimensions） 和 度量（measures）。典型查询会对度量列的值在任意 GROUP BY 条件下进行聚合，并按维度进行过滤。由于 SummingMergeTree 和 AggregatingMergeTree 会对具有相同排序键值的行进行聚合，因此将所有维度都加入排序键是很自然的做法。结果是，键表达式会由一个很长的列列表组成，并且在新增维度时必须频繁更新该列表。

在这种情况下，更合理的做法是只在主键中保留少数几列，以保证高效的范围扫描，并将其余维度列加入排序键元组中。

对排序键执行 ALTER 是一项轻量级操作，因为当新列同时被添加到表和排序键中时，现有数据部分不需要被修改。由于旧排序键是新排序键的前缀，并且在新添加的列中还没有数据，因此在进行表修改时，数据在逻辑上同时满足按旧排序键和新排序键排序。





https://mp.weixin.qq.com/s/D2aDY17iN4Rn5So_WlCTvA
