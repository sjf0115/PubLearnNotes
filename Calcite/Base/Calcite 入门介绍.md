

什么是Calcite

Apache Calcite是一个动态数据管理框架，它具备很多典型数据库管理系统的功能，比如SQL解析、SQL校验、SQL查询优化、SQL生成以及数据连接查询等，但是又省略了一些关键的功能，比如Calcite并不存储相关的元数据和基本数据，不完全包含相关处理数据的算法等。


Apache Calcite 是一个基础软件框架，能够为许多流行的开源数据处理系统提供查询处理、查询优化以及查询语言的支持，例如 Apache Hive、Apache Storm、Apache Flink、Druid 以及 MapD 等等。



也正是因为Calcite本身与数据存储和处理的逻辑无关，所以这让它成为与多个数据存储位置（数据源）和多种数据处理引擎之间进行调解的绝佳选择。

Calcite所做的工作就是将各种SQL语句解析成抽象语法树（AST Abstract Syntax Tree），并根据一定的规则或成本对AST的算法与关系进行优化，最后推给各个数据处理引擎进行执行。

目前，使用Calcite作为SQL解析与优化引擎的又Hive、Drill、Flink、Phoenix和Storm，Calcite凭借其优秀的解析优化能力，会有越来越多的数据处理引擎采用Calcite作为SQL解析工具。

Calcite 主要功能

Calcite的主要功能我们上面其实已经提到了，主要有以下功能：

SQL解析：通过JavaCC将SQL解析成未经校验的AST语法树

SQL校验：校验分两部分，一种为无状态的校验，即验证SQL语句是否符合规范；一种为有状态的即通过与元数据结合验证SQL中的Schema、Field、Function是否存在。

SQL查询优化：对上个步骤的输出（RelNode）进行优化，得到优化后的物理执行计划

SQL生成：将物理执行计划生成为在特定平台/引擎的可执行程序，如生成符合Mysql or Oracle等不同平台规则的SQL查询语句等

数据连接与执行：通过各个执行平台执行查询，得到输出结果。
