
不再推荐使用 Group Window Aggregation。现在推荐使用功能更加强大以及更有效的 Window TVF Aggregation。与 Group Window Aggregation 相比，Window TVF Aggregation 有很多优势，包括：
- 具有性能调优中提到的所有性能优化。
- 支持标准的 GROUPING SETS 语法。
- 可以在窗口聚合结果后应用 Window TopN。

Group Window Aggregation 通过 SQL 查询的 GROUP BY 子句来定义。就像使用常规 GROUP BY 子句一样查询，但是 GROUP BY 子句会包含一个分组窗口函数。批处理表和流表上的 SQL 支持以下组窗口函数。

对于流处理，分组窗口函数的 time_attr 参数必须使用一个有效的时间属性，可以是处理时间属性，也可以是事件时间属性。对于批处理，分组窗口函数的 time_attr 参数必须是 TIMESTAMP 类型的属性。


Group Window 是和 GroupBy 语句绑定使用的窗口，和Table API一样，Flink SQL也支持三种窗口类型，分别为Tumble Windows、HOP Windows 和 Session Windows，其中 HOP Windows 对应 Table API 中的 Sliding Window，同时每种窗口分别有相应的使用场景和方法。

## 1. Tumble Windows

滚动窗口的窗口长度是固定的，且窗口和窗口之间的数据不会重合。SQL 中通过 TUMBLE(time_attr, interval) 窗口函数来定义滚动窗口，其中参数 time_attr 用于指定时间属性，参数 interval 用于指定窗口的固定长度。

滚动窗口可以应用在基于 EventTime 的批量计算和流式计算场景中，和基于 ProcessTime 的流式计算场景中。窗口元数据信息可以通过在 Select 语句中使用相关的函数获取，且窗口元数据信息可用于后续的 SQL 操作，例如可以通过 TUMBLE_START 获取窗口起始时间，TUMBLE_END 获取窗口结束时间，TUMBLE_ROWTIME 获取窗口事件时间，TUMBLE_PROCTIME 获取窗口数据中的 ProcessTime。如以下实例所示，分别创建基于不同时间属性的 Tumble 窗口：
```java

```

## 2. HOP Windows

滑动窗口的窗口长度固定，且窗口和窗口之间的数据可以重合。在Flink SQL中通过HOP(time_attr, interval1, interval2)关键字来定义HOP Windows，其中参数time_attr用于指定使用的时间属性，参数interval1用于指定窗口滑动的时间间隔，参数interval2用于指定窗口的固定大小。其中如果interval1小于interval2，窗口就会发生重叠。HOP Windows可以应用在基于EventTime的批量计算场景和流式计算场景中，以及基于ProcessTime的流式计算场景中。HOP窗口的元数据信息获取的方法和Tumble的相似，例如可以通过HOP_START获取窗口起始时间，通过HOP_END获取窗口结束时间，通过HOP_ROWTIME获取窗口事件时间，通过HOP_PROCTIME获取窗口数据中的ProcessTime。
如以下代码所示，分别创建基于不同时间概念的HOP窗口，并通过相应方法获取窗口云数据。
val env = StreamExecutionEnvironment.getExecutionEnvironment
val tableEnv = TableEnvironment.getTableEnvironment(env)
// 创建数据集
val ds: DataStream[(Long, String, Int)] = ...
// 注册表名信息并定义字段proctime为ProcessTime,定义字段rowtime为rowtime,
tableEnv.registerDataStream("Sensors", ds, 'id, 'type, 'var1, 'proctime.proctime, 'rowtime.rowtime)

## 3. Session Windows

Session窗口没有固定的窗口长度，而是根据指定时间间隔内数据的活跃性来切分窗口，例如当10min内数据不接入Flink系统则切分窗口并触发计算。在SQL中通过SESSION(time_attr, interval)关键字来定义会话窗口，其中参数time_attr用于指定时间属性，参数interval用于指定Session Gap。Session Windows可以应用在基于EventTime的批量计算场景和流式计算场景中，以及基于ProcessTime的流式计算场景中。
Session窗口的元数据信息获取与Tumble窗口和HOP窗口相似，通过SESSION_START获取窗口起始时间，SESSION_END获取窗口结束时间，SESSION_ROWTIME获取窗口数据元素事件时间，SESSION_PROCTIME获取窗口数据元素处理时间。















参考：https://nightlies.apache.org/flink/flink-docs-release-1.13/docs/dev/table/sql/queries/window-agg/#group-window-aggregation
