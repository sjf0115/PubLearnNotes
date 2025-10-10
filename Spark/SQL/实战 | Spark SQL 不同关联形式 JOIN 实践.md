数据关联（Join）是数据分析场景中最常见、最重要的操作。毫不夸张地说，几乎在所有的数据应用中，你都能看到数据关联的“身影”。因此，今天这一讲，咱们继续详细说一说 Spark SQL 对于 Join 的支持。众所周知，Join 的种类非常丰富。如果按照关联形式（Join Types）来划分，数据关联分为内关联、外关联、左关联、右关联，等等。对于参与关联计算的两张表，关联形式决定了结果集的数据来源。因此，在开发过程中选择哪种关联形式，是由我们的业务逻辑决定的。

## 1. 数据准备

为了让你更好地掌握新知识，我会通过一个个例子，为你说明 Spark SQL 数据关联的具体用法。在去介绍数据关联之前，咱们先把示例中会用到的数据准备好。
```
import spark.implicits._
import org.apache.spark.sql.DataFrame

// 创建员工信息表
val seq = Seq((1, "Mike", 28, "Male"), (2, "Lily", 30, "Female"), (3, "Raymond", 26, "Male"), (5, "Dave", 36, "Male"))
val employees: DataFrame = seq.toDF("id", "name", "age", "gender")

// 创建薪资表
val seq2 = Seq((1, 26000), (2, 30000), (4, 25000), (3, 20000))
val salaries:DataFrame = seq2.toDF("id", "salary")
```
