作为数据处理和分析的核心抽象，DataFrame 是 Spark SQL 中最常用的数据结构。本文将详细介绍 Spark SQL 中创建 DataFrame 的各种方式，并提供实际示例和最佳实践。

## 1. 从现有 RDD 创建 DataFrame

### 1.1 使用反射推断 Schema

```scala
import org.apache.spark.sql.SparkSession

// 创建 SparkSession
val spark = SparkSession.builder()
  .appName("DataFrameCreation")
  .master("local[*]")
  .getOrCreate()

import spark.implicits._

// 样例类定义
case class Person(name: String, age: Int, city: String)

// 创建 RDD 并转换为 DataFrame
val personRDD = spark.sparkContext.parallelize(Seq(
  Person("Alice", 25, "New York"),
  Person("Bob", 30, "San Francisco"),
  Person("Charlie", 35, "Chicago")
))

val personDF = personRDD.toDF()
personDF.show()
personDF.printSchema()
```

## 2. 从数据源读取创建 DataFrame

### 2.1 从 JSON 文件读取

```scala
// 读取 JSON 文件
val jsonDF = spark.read
  .format("json")
  .option("multiline", "true")
  .load("path/to/people.json")

// 或者使用简写方式
val jsonDF2 = spark.read.json("path/to/people.json")

jsonDF.show()
```

### 2.2 从 CSV 文件读取

```scala
val csvDF = spark.read
  .format("csv")
  .option("header", "true")
  .option("inferSchema", "true")
  .option("delimiter", ",")
  .load("path/to/people.csv")

// 使用简写方式并指定更多选项
val csvDF2 = spark.read
  .option("header", "true")
  .option("inferSchema", "true")
  .csv("path/to/people.csv")

csvDF.show()
```

### 2.3 从 Parquet 文件读取

```scala
val parquetDF = spark.read
  .format("parquet")
  .load("path/to/people.parquet")

// 简写方式
val parquetDF2 = spark.read.parquet("path/to/people.parquet")
```

### 2.4 从 JDBC 数据源读取

```scala
val jdbcDF = spark.read
  .format("jdbc")
  .option("url", "jdbc:mysql://localhost:3306/test")
  .option("dbtable", "people")
  .option("user", "username")
  .option("password", "password")
  .load()
```

## 3. 从集合创建 DataFrame

### 3.1 使用 toDF() 方法

> 已验证

```scala
object SeqToDataFrameScalaExample {

  case class Employees(id: Int, name: String, age: Int, sex: String)

  def main( args: Array[String] ): Unit = {
    val sparkSession = SparkSession.builder()
      .appName("SeqToDataFrameScalaExample")
      .enableHiveSupport()
      .master("local[*]")
      .getOrCreate()

    // 注意：使用 toDF 需要引入 SparkSession示例的隐式转换
    import sparkSession.implicits._

    // 1. 从元组序列创建薪资表
    val salariesSeq = Seq((1, 26000), (2, 30000), (4, 25000), (3, 20000))
    val salariesDF: DataFrame = salariesSeq.toDF("id", "salary")
    salariesDF.show()
    /*+---+------+
    | id|salary|
    +---+------+
    |  1| 26000|
    |  2| 30000|
    |  4| 25000|
    |  3| 20000|
    +---+------+*/

    // 2. 从样例类序列创建员工信息表
    val employeesSeq = Seq(
      Employees(1, "Mike", 28, "Male"),
      Employees(2, "Lily", 30, "Female"),
      Employees(3, "Raymond", 26, "Male"),
      Employees(5, "Dave", 36, "Male")
    )
    val employeesDF: DataFrame = employeesSeq.toDF()
    employeesDF.show()
    /*+---+-------+---+------+
    | id|   name|age|   sex|
    +---+-------+---+------+
    |  1|   Mike| 28|  Male|
    |  2|   Lily| 30|Female|
    |  3|Raymond| 26|  Male|
    |  5|   Dave| 36|  Male|
    +---+-------+---+------+*/
  }
}
```
注意的是使用 toDF 需要引入 SparkSession 示例的隐式转换：
```
import sparkSession.implicits._
```

### 3.2 使用 createDataFrame 方法

> 已验证

这一种方法比较繁琐，通过 row+schema 创建 DataFrame：
```scala
object SeqToDFByCreateDataFrameScalaExample {

  def main( args: Array[String] ): Unit = {
    val sparkSession = SparkSession.builder()
      .appName("SeqToDFByCreateDataFrameScalaExample")
      .master("local[*]")
      .getOrCreate()

    // Seq
    val seq = Seq(Row(1, 26000), Row(2, 30000), Row(4, 25000), Row(3, 20000))
    // 转换为 RDD
    val rdd = sparkSession.sparkContext.parallelize(seq)
    // Schema
    val schema = StructType(List(
      StructField("id", IntegerType, nullable = false),
      StructField("salary", IntegerType, nullable = false)
    ))

    val salariesDF = sparkSession.createDataFrame(rdd, schema)
    salariesDF.show()
    /*+---+------+
    | id|salary|
    +---+------+
    |  1| 26000|
    |  2| 30000|
    |  4| 25000|
    |  3| 20000|
    +---+------+*/
  }
}
```

## 4. 从 Hive 表创建 DataFrame

```scala
// 启用 Hive 支持
val spark = SparkSession.builder()
  .appName("HiveExample")
  .config("spark.sql.warehouse.dir", "/user/hive/warehouse")
  .enableHiveSupport()
  .getOrCreate()

// 从 Hive 表读取
val hiveDF = spark.sql("SELECT * FROM people")

// 或者使用 table 方法
val hiveDF2 = spark.table("people")
```

## 5. 通过转换操作创建新的 DataFrame

```scala
// 从现有 DataFrame 转换创建新的 DataFrame
val originalDF = spark.read.option("header", "true").csv("path/to/data.csv")

// 通过筛选创建新 DataFrame
val filteredDF = originalDF.filter($"age" > 25)

// 通过选择列创建新 DataFrame
val selectedDF = originalDF.select("name", "city")

// 通过聚合创建新 DataFrame
val aggregatedDF = originalDF
  .groupBy("city")
  .agg(avg("age").as("avg_age"), count("*").as("count"))
```

## 6. 从 Pandas DataFrame 创建（PySpark）

```python
from pyspark.sql import SparkSession
import pandas as pd

# 创建 SparkSession
spark = SparkSession.builder \
    .appName("PandasIntegration") \
    .getOrCreate()

# 创建 Pandas DataFrame
pandas_df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'city': ['New York', 'San Francisco', 'Chicago']
})

# 转换为 Spark DataFrame
spark_df = spark.createDataFrame(pandas_df)
spark_df.show()
```

## 7. 最佳实践和性能考虑

### 7.1 Schema 推断 vs 显式定义

```scala
// 不推荐：自动推断 Schema（性能较差）
val inferredDF = spark.read
  .option("inferSchema", "true")
  .csv("large_dataset.csv")

// 推荐：显式定义 Schema
val customSchema = StructType(Array(
  StructField("id", IntegerType, true),
  StructField("name", StringType, true),
  StructField("timestamp", TimestampType, true)
))

val definedDF = spark.read
  .schema(customSchema)
  .csv("large_dataset.csv")
```

### 7.2 分区数据读取

```scala
// 读取分区数据
val partitionedDF = spark.read
  .option("basePath", "hdfs://path/to/partitioned_data")
  .parquet("hdfs://path/to/partitioned_data/year=2023/month=*/day=*")

// 使用分区发现
val discoveredDF = spark.read
  .option("partitionDiscovery.enabled", "true")
  .parquet("hdfs://path/to/partitioned_data")
```

## 8. 完整示例：综合使用多种方式

```scala
import org.apache.spark.sql.{SparkSession, DataFrame}
import org.apache.spark.sql.types._

object DataFrameCreationDemo {
  def main(args: Array[String]): Unit = {
    val spark = SparkSession.builder()
      .appName("DataFrameCreationDemo")
      .master("local[*]")
      .getOrCreate()

    import spark.implicits._

    // 方式1：从集合创建
    val fromCollection = createFromCollection(spark)

    // 方式2：从文件创建
    val fromFile = createFromFile(spark, "path/to/data.csv")

    // 方式3：从 RDD 创建
    val fromRDD = createFromRDD(spark)

    // 显示结果
    fromCollection.show()
    fromFile.show()
    fromRDD.show()

    spark.stop()
  }

  def createFromCollection(spark: SparkSession): DataFrame = {
    import spark.implicits._
    Seq(
      ("Alice", 25, "Engineer"),
      ("Bob", 30, "Manager")
    ).toDF("name", "age", "job")
  }

  def createFromFile(spark: SparkSession, path: String): DataFrame = {
    spark.read
      .option("header", "true")
      .option("inferSchema", "true")
      .csv(path)
  }

  def createFromRDD(spark: SparkSession): DataFrame = {
    case class Product(name: String, price: Double, category: String)

    val rdd = spark.sparkContext.parallelize(Seq(
      Product("Laptop", 999.99, "Electronics"),
      Product("Book", 19.99, "Education")
    ))

    rdd.toDF()
  }
}
```

## 总结

Spark SQL 提供了多种灵活的方式来创建 DataFrame，每种方法都有其适用的场景：

- **从集合创建**：适合小规模测试数据和原型开发
- **从文件创建**：适合处理各种格式的数据文件
- **从 RDD 创建**：适合与现有的 RDD 代码集成
- **从数据源创建**：适合连接外部数据系统

选择合适的方法取决于数据源、数据规模、性能要求和开发便利性。在实际项目中，通常需要根据具体需求组合使用多种方法来构建完整的数据处理管道。
