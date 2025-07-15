
随着流计算的发展，挑战不再仅限于数据量和计算量，业务变得越来越复杂，开发者可能是资深的大数据从业者、初学 Java 的爱好者，或是不懂代码的数据分析者。如何提高开发者的效率，降低流计算的门槛，对推广实时计算非常重要。

SQL 是数据处理中使用最广泛的语言，允许用户简明扼要地展示其业务逻辑。Flink 作为流批一体的计算引擎，致力于提供一套 SQL 支持全部应用场景，Flink SQL 的实现也完全遵循 ANSI SQL 标准。之前，用户可能需要编写上百行业务代码，使用 SQL 后，可能只需要几行 SQL 就可以轻松搞定。

Flink SQL 的发展大概经历了以下阶段：
- Flink 1.1.0：第一次引入 SQL 模块，并且提供 TableAPI，当然，这时候的功能还非常有限。
- Flink 1.3.0：在 Streaming SQL 上支持了 Retractions，显著提高了 Streaming SQL 的易用性，使得 Flink SQL 支持了复杂的 Unbounded 聚合连接。
- Flink 1.5.0：SQL Client 的引入，标志着 Flink SQL 开始提供纯 SQL 文本。
- Flink 1.9.0：抽象了 Table 的 Planner 接口，引入了单独的 Blink Table 模块。Blink Table 模块是阿里巴巴内部的 SQL 层版本，不仅在结构上有重大变更，在功能特性上也更加强大和完善。
- Flink 1.10.0：作为第一个 Blink 基本完成 merge 的版本，修复了大量遗留的问题，并给 DDL 带来了 Watermark 的语法，也给 Batch SQL 带来了完整的 TPC-DS 支持和高效的性能。
