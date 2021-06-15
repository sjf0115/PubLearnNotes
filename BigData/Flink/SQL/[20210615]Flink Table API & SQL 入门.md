

Apache Flink 提供了两种关系型API，分别为 Table API 和 SQL，通过 Table API 和 SQL 实现了流批的统一。其中 Table API 是用于 Scala、Java 以及 Python 的语言集成查询 API，它允许以非常直观的方式组合关系运算符（例如，select，where和join）的查询。Flink SQL 基于 Apache Calcite 实现了标准的 SQL，用户可以使用标准的SQL处理数据集。Table API和SQL与Flink的DataStream和DataSet API紧密集成在一起，用户可以实现相互转化，比如可以将DataStream或者DataSet注册为table进行操作数据。值得注意的是，Table API and SQL目前尚未完全完善，还在积极的开发中，所以并不是所有的算子操作都可以通过其实现。
