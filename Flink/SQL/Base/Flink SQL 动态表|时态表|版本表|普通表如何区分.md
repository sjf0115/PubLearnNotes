根据 [ 官方文档 ] 所述，在 Flink 中，时态表和动态表是一个概念，只是强调的侧重点不同。Flink 流上的表都是动态的，也就是一直在变化，所以被称为动态表，因为动态表都会随时间发生变化，所以也被叫作了 “时态表”。而根据能否 trace (追踪) 一张时态表的变化历史，时态表会细分成：版本表 和 普通表 两种，区别就是：版本表可以追溯历史，而普通表只保存当前最新状态的数据。


时态表（Temporal Table）是一张随时间变化的表 – 在 Flink 中称为动态表，时态表中的每条记录都关联了一个或多个时间段，所有的 Flink 表都是时态的（动态的）。

时态表包含表的一个或多个有版本的表快照，时态表可以是一张跟踪所有变更记录的表（例如数据库表的 changelog，包含多个表快照），也可以是物化所有变更之后的表（例如数据库表，只有最新表快照）。

版本: 时态表可以划分成一系列带版本的表快照集合，表快照中的版本代表了快照中所有记录的有效区间，有效区间的开始时间和结束时间可以通过用户指定，根据时态表是否可以追踪自身的历史版本与否，时态表可以分为 版本表 和 普通表。

版本表: 如果时态表中的记录可以追踪和并访问它的历史版本，这种表我们称之为版本表，来自数据库的 changelog 可以定义成版本表。

普通表: 如果时态表中的记录仅仅可以追踪并和它的最新版本，这种表我们称之为普通表，来自数据库 或 HBase 的表可以定义成普通表。





Flink 官方文档中说：定义了主键约束和事件时间属性（通过 WATERMARK 关键字标识）的表就是版本表，并且举例说：数据库的 changelog 数据（CDC数据）就可以定义成版本表。这里不要产生错误的理解，不是说只有数据库的 changelog 数据才支持定义成版本表，而是说数据库的 changelog 型数据是版本表的一种典型数据，因为它必定包含记录的主键和一个标记操作执行的时间戳，即使不是 changelog 型的数据，只要数据本身含有一个主键和一个时间戳，就可以被定义为一张版本表，表的历史版本是由 Flink 负责维护的 (参考 此处 )，并能通过 Temporal Join 或 Temporal Table Function 获取到指定时刻的版本。

```
-- 定义一张版本表
-- 只有同时定义了主键和事件时间字段的表才是一张版本表
-- 通过 CDC 技术从数据库采集的 changelog 数据是构成版本表的数据“典型”数据
-- 但并不是说：版本表的数据一定是 changelog 型的数据，只要满足有主键和事件时间字段数据，就可以定义为版本表
CREATE TABLE product_changelog (
  product_id STRING,
  product_name STRING,
  product_price DECIMAL(10, 4),
  update_time TIMESTAMP(3) METADATA FROM 'value.source.timestamp' VIRTUAL,
  PRIMARY KEY(product_id) NOT ENFORCED,      -- 版本表特征(1) 定义主键
  WATERMARK FOR update_time AS update_time   -- 版本表特征(2) 定义事件时间字段（通过 watermark 定义事件时间）              
) WITH (
  'connector' = 'kafka',
  'topic' = 'products',
  'scan.startup.mode' = 'earliest-offset',
  'properties.bootstrap.servers' = 'localhost:9092',
  'value.format' = 'debezium-json'
);
```
实际上，Flink 的版本表条件和定义一张 Hudi 表所必须指定的两项配置：hoodie.datasource.write.recordkey.field 和 precombine.field 在性质上是一样的：如果你想区别同一条记录的不同版本，就得需要同时指定记录的唯一标识（即主键）和当出现相同主键记录时的版本号（即记录的时间戳），本质上，这是保证记录版本可回溯的两个必要条件，所以才会有 Flink 版本表与 Hudi 表之间的这种“神似”状况。

以下是对四个概念的梳理：

时态表 <=> 动态表
	├── 版本表：可追溯历史版本，只有定义了：主键和事件时间属性（通过 watermark 定义） 的表才可以成为一张版本表，
	│          反过来说：数据本身必须包含主键字段和一个标记记录生成或更新的时间戳字段才能被定义成 Flink 上的版本表。
	│          由于版本表有这两项约束条件，能构成版本表的数据往往是 changelog 型数据，典型代表是数据库的 CDC 数据；
	└── 普通表：只保存当前最新状态数据，就是只能拿到当前最新快照


普通表并不会特别拿来强调，只是用于和版本表这个概念做对比的，真正被特别拿来强调的是版本表，而经常与版本表放在一起提及的就是“Temporal Join“，“Temporal Join“ 其实特指与版本表的 Join。目前在官方文档的多处描述中可以判断的是：但凡提及 时态表 / Temporal Table 或 Temporal 这个关键词时，通常谈论的是都是 版本表，所以，我们可以在沟通和描述中使用“时态表”这个称谓指代“版本表”这个概念，但要清楚两者之间的关系，以及在必要的时候能区分对方想要表达的具体是哪一种就可以了。应该是 Flink 在历史上似乎没有对这些概念进行明确的区分，或者中途引入的概念有一些冲突，各种混用导致了概念上的一些轻微的混淆。


https://nightlies.apache.org/flink/flink-docs-release-1.18/zh/docs/dev/table/concepts/versioned_tables/
https://blog.csdn.net/bluishglc/article/details/136392632
