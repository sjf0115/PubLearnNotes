这是一个分步教程，展示了如何构建并与 Calcite 进行连接。通过一个简单的适配器既可以使 CSV 文件看起来像是一个包含表的 Schema。Calcite 完成剩下的工作，并提供完整的 SQL 接口。

Calcite-example-CSV 是 Calcite 的全功能适配器，可以读取 CSV（逗号分隔值）格式的文本文件。 值得注意的是，几百行 Java 代码就足以提供完整的 SQL 查询功能。

CSV 还用作构建其他数据格式适配器的模板。 虽然代码行数不多，但涵盖了几个重要的概念：
- 使用 SchemaFactory 和 Schema 接口实现用户定义模式(Schema)；
- 在模型 JSON 文件中声明模式；
- 在模型 JSON 文件中声明视图；
- 使用 Table 接口的用户定义表；
- 确定表的记录类型；
- Table 的简单实现，使用 ScannableTable 接口，直接枚举所有行；
- 更高级的实现FilterableTable，可以根据简单的谓词过滤行；
- Table 的高级实现，使用 TranslatableTable，使用计划器规则转换为关系运算符。
