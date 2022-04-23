Flink 1.9 实现了一个 新的数据类型系统，以便从 Table API 中移除对 Flink TypeInformation 的依赖，并提高其对 SQL 标准的遵从性，不过还在进行中，预计将在下一版本完工，并且在 Flink 1.9 中，UDF 尚未移植到新的类型系统上。

目前，Table API & SQL 在代码中依赖了 Flink 的 TypeInformation。API 使用它在 DataSet/DataStream API、转换和表模式表示之间进行转换。 运行时运算符的代码生成和序列化规划。

过去表明，TypeInformation 在 DataSet/DataStream API 之间转换时很有用，但是它不能很好地与 SQL 类型系统集成，并且所使用的编程语言不同而不同。

例如，如果用户实现了一个 TableFunction：
```scala
case class SimpleUser(name: String, age: Int)
class TableFunc0 extends TableFunction[SimpleUser] {
  def eval(user: String): Unit = {
      if (user.contains("#")) {
        val splits = user.split("#")
        collect(SimpleUser(splits(0), splits(1).toInt))
      }
  }
}
```
上述表函数的返回类型不仅取决于函数类本身，还取决于所使用的表环境：
```java
org.apache.flink.table.api.java.StreamTableEnvironment#registerFunction
```
使用 Java 类型提取堆栈并通过使用基于反射的 TypeExtractor 提取 TypeInformation。
```scala
org.apache.flink.table.api.scala.StreamTableEnvironment#registerFunction
```
使用 Scala 类型提取堆栈并使用 Scala 宏提取 TypeInformation。

根据表环境，上面的示例可能使用 Case Class 序列化程序或 Kryo 序列化程序进行序列化（我假设 case 类不被识别为 POJO）。

优步等其他大贡献者也提到了不灵活和不一致。 看：

当前的类型系统有许多不同的缺点。
- 它与 SQL 不一致。
- 例如，不能为 DECIMAL 定义精度和比例。
- 不支持 CHAR/VARCHAR 之间的区别（FLINK-10257、FLINK-9559）。
- 物理类型和逻辑类型是紧密耦合的。
- 物理类型是类型信息而不是类型序列化器。




[FLIP-37: Rework of the Table API Type System](https://cwiki.apache.org/confluence/display/FLINK/FLIP-37%3A+Rework+of+the+Table+API+Type+System)
