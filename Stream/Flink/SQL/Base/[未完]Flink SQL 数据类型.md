

由于历史原因，在 Flink 1.9 之前，Flink 的 Table & SQL API 数据类型与 Flink 的 TypeInformation 紧密耦合。TypeInformation 用于 DataStream 和 DataSet API，足以描述在分布式设置中序列化和反序列化基于 JVM 的对象所需的所有信息。

但是，TypeInformation 并非旨在表示独立于实际 JVM 类的逻辑类型。很难将 SQL 标准类型映与这种抽象进行映射。此外，某些类型不符合 SQL 标准，并且在没有考虑大局的情况下引入。从 Flink 1.9 开始，Table & SQL API 将获得一个新的类型系统，作为 API 稳定性和标准合规性的长期解决方案。

重新设计类型系统是一项涉及几乎所有面向用户接口的重大工作。因此，它的引入会跨越多个版本，社区目标在 Flink 1.10 完成这项工作。



















原文：[Data Types](https://ci.apache.org/projects/flink/flink-docs-release-1.9/dev/table/types.html)
