---
layout: post
author: sjf0115
title: Spark SQL 入门
date: 2018-07-14 13:31:01
tags:
  - Spark
  - Spark SQL

categories: Spark
permalink: spark-sql-getting-started
---

### 1. 概述

Spark SQL 是用于结构化数据处理的 Spark 模块。与基本的 Spark RDD API 不同，Spark SQL 提供的接口为 Spark 提供了有关数据和计算的更多结构化信息。在内部，Spark SQL 使用这些额外的信息执行优化。Spark 提供了几种与 Spark SQL 进行交互的方法，包括 `SQL` 和 `DataSet API`。当使用相同的执行引擎计算结果时，与你用来描述计算的API和语言无关。这种统一意味着开发人员可以轻松地在不同API之间来回切换，从而提供了表达给定转换操作最自然的方式．

#### 1.1 SQL

Spark SQL 的一个用途是执行 SQL 查询。Spark SQL 也可以从现有已安装的 Hive 中读取数据。当使用另一种编程语言运行 SQL 时，结果将以 DataSet/DataFrame 形式返回。你还可以使用命令行或 JDBC/ODBC 与 SQL 接口进行交互。

#### 1.2 DataSets 与 DataFrames

DataSet 是分布式数据集合。DataSet 是 Spark 1.6 中新增加的一个接口，既有 RDD 所具有的优势（强类型，可以使用 lambda 函数），也具有 Spark SQL 的优化执行引擎的优点。可以从 JVM 对象构建 DataSet，然后使用转换操作函数（map，flatMap，filter等）进行操作。DataSet API 可以在 Scala 和 Java 语言中使用。

DataFrame 是一个组织成命名列的 DataSet。在概念上等同于关系数据库中的一个表或 R/Python 中的 `data frames`，但是进行了更多优化。DataFrames 可以从各种数据源构建，例如结构化数据文件，Hive 中的表，外部数据库或者现有 RDD。DataFrame API 在 Scala，Java，Python 和 R 中使用。在 Scala 和 Java 中，DataFrame 是 Rows 组成的 DataSet。在 Scala API 中，DataFrame 只是 DataSet[Row] 的一个别名。在 Java API 中，使用 DataSet<Row> 来表示 DataFrame。

### 2. 入门

#### 2.1 SparkSession

Spark 中所有函数的入口点是 SparkSession 类。创建一个 SparkSession，只需使用 `SparkSession.builder（）`即可：

Java版本：
```java
import org.apache.spark.sql.SparkSession;
SparkSession spark = SparkSession
  .builder()
  .master("local[2]")
  .appName("Java Spark SQL basic example")
  .config("spark.some.config.option", "some-value")
  .getOrCreate();
```
Scala版本：
```scala
import org.apache.spark.sql.SparkSession
val spark = SparkSession
  .builder()
  .master("local[2]")
  .appName("Spark SQL basic example")
  .config("spark.some.config.option", "some-value")
  .getOrCreate()

// For implicit conversions like converting RDDs to DataFrames
import spark.implicits._
```
Python版本：
```python
from pyspark.sql import SparkSession
spark = SparkSession \
    .builder \
    .master("local[2]") \
    .appName("Python Spark SQL basic example") \
    .config("spark.some.config.option", "some-value") \
    .getOrCreate()
```
完整示例在 `examples/src/main/java/org/apache/spark/examples/sql/JavaSparkSQLExample.java`。Spark 2.0 中的 SparkSession 为 Hive 功能提供内置支持，包括使用 HiveQL 编写查询，访问 Hive UDF 以及从 Hive 表读取数据的功能。

#### 2.2 创建 DataFrames

使用 SparkSession，应用程序可以从已存在的 RDD，Hive 表或 Spark 数据源创建 DataFrames。作为示例，以下将基于 JSON 文件的内容创建 DataFrame，Json文件内容如下所示：
```json
{"name":"Michael"}
{"name":"Andy", "age":30}
{"name":"Justin", "age":19}
```
使用如下命令创建 DataFrames：
```java
import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;

// 创建 DataFrame
Dataset<Row> dataFrame = sparkSession.read().json("src/main/resources/person.json");
// 输出 DataFrame 内容
dataFrame.show();

/*+----+-------+
| age|   name|
+----+-------+
|null|Michael|
|  30|   Andy|
|  19| Justin|
+----+-------+*/
```
#### 2.3 无类型 DataSet 操作（DataFrame操作）

DataFrames 为 Scala，Java，Python 和 R 中的结构化数据操作提供了一种特定领域的语言(DSL)。如上所述，在 Spark 2.0 中，DataFrames 只是 Scala 和 Java API 中的 Rows 类型的 DataSet。这些操作也被称为 `无类型转换`，与强类型的 Scala/Java DataSets 中的 `类型转换` 相反。这里我们列举了使用 DataSets 进行结构化数据处理的一些基本示例：
```java
Dataset<Row> dataFrame = sparkSession.read().json("src/main/resources/person.json");

// 选择name这一列
dataFrame.select("name").show();
/**
 * +-------+
 |   name|
 +-------+
 |Michael|
 |   Andy|
 | Justin|
 +-------+
 */

// 选择name age列 age加一
dataFrame.select(col("name"), col("age").plus(1)).show();
/**
 * +-------+---------+
 |   name|(age + 1)|
 +-------+---------+
 |Michael|     null|
 |   Andy|       31|
 | Justin|       20|
 +-------+---------+
 */

// 过滤age大于21岁
dataFrame.filter(col("age").gt(21)).show();
/**
 * +---+----+
 |age|name|
 +---+----+
 | 30|Andy|
 +---+----+
 */

// 按age分组求人数
dataFrame.groupBy("age").count().show();
/**
 * +----+-----+
 | age|count|
 +----+-----+
 |  19|    1|
 |null|    1|
 |  30|    1|
 +----+-----+
 */
```

有关可在数据集上执行的操作类型的完整列表，请参阅[API文档](http://spark.apache.org/docs/latest/api/java/org/apache/spark/sql/Dataset.html)。

除了简单的列引用和表达式，DataSets还具有丰富的函数库，包括字符串操作，日期算术，常用的数学运算等。 完整列表可参阅在[DataFrame函数参考](http://spark.apache.org/docs/latest/api/scala/index.html#org.apache.spark.sql.functions$)。

#### 2.4 编程方式运行 SQL 查询

SparkSession 上的 sql 函数能使应用程序以编程的方式运行 SQL 查询，并将结果以 DataSet<Row> 形式返回。

Java版本：
```java
// 创建DataFrame
Dataset<Row> dataFrame = sparkSession.read().json("src/main/resources/person.json");
// 注册 DataFrame 为 SQL 临时视图
dataFrame.createOrReplaceTempView("people");
// 运行
Dataset<Row> result = sparkSession.sql("SELECT * FROM people");
// 输出
result.show();
/**
 * +----+-------+
 | age|   name|
 +----+-------+
 |null|Michael|
 |  30|   Andy|
 |  19| Justin|
 +----+-------+
 */
```
Scala版本：
```scala
dataFrame.createOrReplaceTempView("people")
val result = sparkSession.sql("SELECT * FROM people")
result.show()
```

#### 2.5 全局临时视图

Spark SQL 中的临时视图是 Session 级别的，如果创建它的 Session 终止，临时视图也将会消失。如果要在所有 Session 之间共享临时视图，并保持活动状态保持到 Spark 应用程序终止，可以创建一个全局临时视图。全局临时视图与系统预留数据库 global_temp 相关联，我们必须使用该限定名称来引用它。例如，`SELECT * FROM global_temp.view1`。

Java版本：
```java
// 创建DataFrame
Dataset<Row> dataFrame = sparkSession.read().json("src/main/resources/person.json");
// 将DataFrame注册为全局临时视图
dataFrame.createGlobalTempView("people");

// 全局临时视图与系统保留的数据库global_temp关联
Dataset<Row> sqlDataFrame = sparkSession.sql("SELECT * FROM global_temp.people");
// 输出结果
sqlDataFrame.show();
/**
 +----+-------+
 | age|   name|
 +----+-------+
 |null|Michael|
 |  30|   Andy|
 |  19| Justin|
 +----+-------+
 */

// 全局临时视图是跨会话的
Dataset<Row> sqlDataFrame2 = sparkSession.newSession().sql("SELECT * FROM global_temp.people");
sqlDataFrame2.show();
/**
 +----+-------+
 | age|   name|
 +----+-------+
 |null|Michael|
 |  30|   Andy|
 |  19| Justin|
 +----+-------+
 */
```
Scala版本：
```scala
dataFrame.createGlobalTempView("people")
sparkSession.sql("SELECT * FROM global_temp.people").show()
sparkSession.newSession().sql("SELECT * FROM global_temp.people").show()
```

#### 2.6 创建DataSet

DataSet 与 RDD 类似，但是，不是使用 Java 或 Kryo 序列化，而是使用专门的 Encoder 来序列化对象以进行处理或网络传输。虽然 Encoder 和标准序列化都可以将对象转换成字节，但是 Encoder 是动态生成的代码，并使用一种让 Spark 可以执行多种操作（如过滤，排序和散列），而无需将字节反序列化成对象的格式。

Java版本：
```java
import java.io.Serializable;
import java.util.Arrays;
import java.util.Collections;
import org.apache.spark.api.java.function.MapFunction;
import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;
import org.apache.spark.sql.Encoder;
import org.apache.spark.sql.Encoders;

public class Person implements Serializable{
    private String name;
    private int age;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public int getAge() {
        return age;
    }

    public void setAge(int age) {
        this.age = age;
    }
}

// 创建Person对象
Person person = new Person();
person.setName("Andy");
person.setAge(32);

// 根据Java Bean创建Encoders
Encoder<Person> personEncoder = Encoders.bean(Person.class);
Dataset<Person> dataSet = sparkSession.createDataset(
        Collections.singletonList(person),
        personEncoder
);
dataSet.show();
/**
 +---+----+
 |age|name|
 +---+----+
 | 32|Andy|
 +---+----+
 */

// 大多数常见类型的编码器都在Encoders中提供
Encoder<Integer> integerEncoder = Encoders.INT();
Dataset<Integer> primitiveDS = sparkSession.createDataset(Arrays.asList(1, 2, 3), integerEncoder);
Dataset<Integer> transformedDS = primitiveDS.map(new MapFunction<Integer, Integer>() {
    @Override
    public Integer call(Integer value) throws Exception {
        return value + 1;
    }
}, integerEncoder);
transformedDS.show();
/**
 +-----+
 |value|
 +-----+
 |    2|
 |    3|
 |    4|
 +-----+
 */

// DataFrames可以通过提供的类来转换为DataSet 基于名称映射
// 创建DataFrame
Dataset<Row> dataFrame = sparkSession.read().json("src/main/resources/person.json");
// DataFrame转换为DataSet
Dataset<Person> peopleDS = dataFrame.as(personEncoder);
peopleDS.show();
/**
 +----+-------+
 | age|   name|
 +----+-------+
 |null|Michael|
 |  30|   Andy|
 |  19| Justin|
 +----+-------+
 */
```
Scala版本：
```scala
case class Person(name: String, age: Long)

// Encoders are created for case classes
val caseClassDS = Seq(Person("Andy", 32)).toDS()
caseClassDS.show()

// Encoders for most common types are automatically provided by importing spark.implicits._
val primitiveDS = Seq(1, 2, 3).toDS()
primitiveDS.map(_ + 1).collect() // Returns: Array(2, 3, 4)

// DataFrames can be converted to a Dataset by providing a class. Mapping will be done by name
val path = "src/main/resources/person.json"
val peopleDS = spark.read.json(path).as[Person]
peopleDS.show()
```

> Spark 版本：2.3.1

原文：http://spark.apache.org/docs/2.3.1/sql-programming-guide.html#overview
