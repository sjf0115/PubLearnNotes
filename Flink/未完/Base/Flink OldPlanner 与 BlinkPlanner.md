

## 1. 发展历程

2019 年的 8 月 22 日 Apache Flink 发布了 1.9.0 版本。在 Flink 1.9 中，Table 模块迎来了核心架构的升级，引入了阿里巴巴 Blink 团队贡献的诸多功能，本文先对 Table 模块的架构进行梳理并介绍如何使用 Blink Planner。

Flink 的 Table 模块 包括 Table API 和 SQL，Table API 是一种类 SQL 的 API，通过 Table API，用户可以像操作表一样操作数据，非常直观和方便；SQL 作为一种声明式语言，有着标准的语法和规范，用户可以不用关心底层实现即可进行数据的处理，非常易于上手，Flink Table API 和 SQL 的实现上有80%左右的代码是公用的。作为一个流批统一的计算引擎，Flink 的 Runtime 层是统一的，但在 Flink 1.9 之前，Flink API 层一直分为 DataStream API 和 DataSet API，Table API & SQL 位于 DataStream API 和 DataSet API 之上。

![]()

在 Flink 1.8 架构里，如果用户需要同时流计算、批处理的场景下，用户需要维护两套业务代码，开发人员也要维护两套技术栈，非常不方便。Flink 社区很早就设想过将批数据看作一个有界流数据，将批处理看作流计算的一个特例，从而实现流批统一，阿里巴巴的 Blink 团队在这方面做了大量的工作，已经实现了 Table API & SQL 层的流批统一。幸运的是，阿里巴巴已经将 Blink 开源回馈给 Flink 社区。为了实现 Flink 整个体系的流批统一，在结合 Blink 团队的一些先行经验的基础上，Flink 社区的开发人员在多轮讨论后，基本敲定了 Flink 未来的技术架构。

在 Flink 的未来架构中，DataSet API 将被废除，面向用户的 API 只有 DataStream API 和 Table API & SQL，在实现层，这两个 API 共享相同的技术栈，使用统一的 DAG 数据结构来描述作业，使用统一的 StreamOperator 来编写算子逻辑，以及使用统一的流式分布式执行引擎，实现彻底的流批统一。这两个 API 都提供流计算和批处理的功能，DataStream API 提供了更底层和更灵活的编程接口，用户可以自行描述和编排算子，引擎不会做过多的干涉和优化；Table API & SQL 则提供了直观的 Table API、标准的 SQL 支持，引擎会根据用户的意图来进行优化，并选择最优的执行计划。




Flink 1.9 到 Flink 1.11 版本中，Flink old Planner和Blink Planner并存，且Flink 1.11将Blink Planner设置为默认Planner。因此开发的时候，需要根据需要引入其一，或两个都引入也可以。


参考：
- [Flink SQL 系列 | 开篇，新架构与 Planner](https://mp.weixin.qq.com/s/zyM-pvV1v4bPcDuNQGju6g)
- [修改代码150万行！Apache Flink 1.9.0做了这些重大修改！](https://mp.weixin.qq.com/s/qcS4FQdSHaZaU52ELEBqBw)
