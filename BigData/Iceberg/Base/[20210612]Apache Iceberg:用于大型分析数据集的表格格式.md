

Apache Iceberg 是一种用于跟踪超大规模表的新格式，是专门为对象存储（如S3）而设计的。本文将介绍为什么 Netflix 需要构建 Iceberg，Apache Iceberg 的高层次设计，并会介绍那些能够更好地解决查询性能问题的细节。本文由 Ryan Blue 分享，他在 Netflix 从事开源数据项目，是 Apache Iceberg 的最初创建者之一，也是 Apache Spark, Parquet, 以及 Avro 贡献者。

Apache Iceberg 是由 Netflix 开发开源的，其于 2018年11月16日进入 Apache 孵化器，是 Netflix 公司数据仓库基础。在功能上和我们熟悉的 Delta Lake 或者 Apache Hudi 类似，但各有优缺点。任何东西的诞生都是有其背后的原因，那么为什么 Netflix 需要开发 Apache Iceberg？

![](1)

在 Netflix，他们希望有更智能的处理引擎，比如有 CBO 优化，更好的 Join 实现，缓存结果集以及物化视图等功能。同时，他们也希望减少人工维护数据。

![](2)

Netflix 面临的问题包括：1、不安全的操作随处可见：写多分区、重命名列等；2、和对象存储交互有时候会出现很大的问题；3、无休止的可扩展性挑战。为了解决这些问题，Iceberg 诞生了。那么 Iceberg 是什么？

![](3)

Iceberg 是一种可伸缩的表存储格式，内置了许多最佳实践。

![](4)

什么？是一种存储格式？可是我们已经有 Parquet，Avro 以及 ORC 这些格式了，为什么还要设计一种新格式？

![](5)

![](6)
