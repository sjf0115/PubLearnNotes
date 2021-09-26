---
layout: post
author: sjf0115
title: Spark SQL DataFrame与RDD交互
date: 2018-07-14 13:31:01
tags:
  - Spark
  - Spark SQL

categories: Spark
permalink: spark-sql-dataframe-interoperating-with-rdds
---

Spark SQL 支持两种不同的方法将现有 RDD 转换为 Datasets。
- 第一种方法使用反射来推断包含特定类型对象的 RDD 的 schema。当你在编写 Spark 应用程序时，你已经知道了 schema，这种基于反射的方法会使代码更简洁，并且运行良好。
- 第二种方法是通过编程接口来创建 DataSet，这种方法允许构建一个 schema，并将其应用到现有的 RDD 上。虽然这种方法更详细，但直到运行时才知道列及其类型，才能构造 DataSets。

### 1. 使用反射推导schema

Spark SQL 支持自动将 JavaBeans 的 RDD 转换为 DataFrame。使用反射获取的 BeanInfo 定义了表的 schema。目前为止，Spark SQL 还不支持包含 Map 字段的 JavaBean。但是支持嵌套的 JavaBeans，List 以及 Array 字段。你可以通过创建一个实现 Serializable 的类并为其所有字段设置 getter 和 setter 方法来创建一个 JavaBean。

Java版本：
```java
import org.apache.spark.api.java.JavaRDD;
import org.apache.spark.api.java.function.Function;
import org.apache.spark.api.java.function.MapFunction;
import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;
import org.apache.spark.sql.Encoder;
import org.apache.spark.sql.Encoders;

// 从文本文件中创建Person对象的RDD
JavaRDD<Person> personRDD = sparkSession.read()
  .textFile("src/main/resources/person.txt")
  .javaRDD()
  .map(line -> {
    String[] parts = line.split(",");
    Person person = new Person();
    person.setName(parts[0]);
    person.setAge(Integer.parseInt(parts[1].trim()));
    return person;
});

// 在 JavaBean 的 RDD 上应用 schema 生成 DataFrame
Dataset<Row> personDataFrame = sparkSession.createDataFrame(personRDD, Person.class);
// 注册为临时视图
personDataFrame.createOrReplaceTempView("people");

// 运行SQl
Dataset<Row> teenagersDataFrame = sparkSession.sql("SELECT name FROM people WHERE age BETWEEN 13 AND 19");

// Row中的列可以通过字段索引获取
Encoder<String> stringEncoder = Encoders.STRING();
Dataset<String> teenagerNamesByIndexDF = teenagersDataFrame.map(
  (MapFunction<Row, String>) row -> "Name: " + row.getString(0),
  stringEncoder
);
teenagerNamesByIndexDF.show();
/**
 +------------+
 |       value|
 +------------+
 |Name: Justin|
 +------------+
 */

// Row中的列可以通过字段名称获取
Dataset<String> teenagerNamesByFieldDF = teenagersDataFrame.map(
  (MapFunction<Row, String>) row -> "Name: " + row.<String>getAs("name"),
  stringEncoder
);
teenagerNamesByFieldDF.show();
/**
 +------------+
 |       value|
 +------------+
 |Name: Justin|
 +------------+
 */
```
Scala版本：
```scala
// For implicit conversions from RDDs to DataFrames
import spark.implicits._

// Create an RDD of Person objects from a text file, convert it to a Dataframe
val peopleDF = spark.sparkContext
  .textFile("src/main/resources/person.txt")
  .map(_.split(","))
  .map(attributes => Person(attributes(0), attributes(1).trim.toInt))
  .toDF()
// Register the DataFrame as a temporary view
peopleDF.createOrReplaceTempView("people")

// SQL statements can be run by using the sql methods provided by Spark
val teenagersDF = spark.sql("SELECT name, age FROM people WHERE age BETWEEN 13 AND 19")

// The columns of a row in the result can be accessed by field index
teenagersDF.map(teenager => "Name: " + teenager(0)).show()
// +------------+
// |       value|
// +------------+
// |Name: Justin|
// +------------+

// or by field name
teenagersDF.map(teenager => "Name: " + teenager.getAs[String]("name")).show()
// +------------+
// |       value|
// +------------+
// |Name: Justin|
// +------------+

// No pre-defined encoders for Dataset[Map[K,V]], define explicitly
implicit val mapEncoder = org.apache.spark.sql.Encoders.kryo[Map[String, Any]]
// Primitive types and case classes can be also defined as
// implicit val stringIntMapEncoder: Encoder[Map[String, Any]] = ExpressionEncoder()

// row.getValuesMap[T] retrieves multiple columns at once into a Map[String, T]
teenagersDF.map(teenager => teenager.getValuesMap[Any](List("name", "age"))).collect()
// Array(Map("name" -> "Justin", "age" -> 19))
```

### 2. 使用编程方式指定Schema

当 JavaBean 类不能提前定义时（例如，记录的结构以字符串编码，或者解析文本数据集，不同用户字段映射方式不同），可以通过编程方式创建 DataSet<Row>，有如下三个步骤：
- 从原始 RDD(例如，JavaRDD<String>)创建 Rows 的 RDD(JavaRDD<Row>);
- 创建由 StructType 表示的 schema，与步骤1中创建的 RDD 中的 Rows 结构相匹配。
- 通过SparkSession提供的 createDataFrame 方法将 schema 应用到 Rows 的 RDD。

Java版本：
```java
import java.util.ArrayList;
import java.util.List;

import org.apache.spark.api.java.JavaRDD;
import org.apache.spark.api.java.function.Function;

import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;

import org.apache.spark.sql.types.DataTypes;
import org.apache.spark.sql.types.StructField;
import org.apache.spark.sql.types.StructType;

// JavaRDD<String>
JavaRDD<String> peopleRDD = sparkSession.sparkContext()
  .textFile("src/main/resources/person.txt", 1)
  .toJavaRDD();

// JavaRDD<Row>
JavaRDD<Row> rowRDD = peopleRDD.map((Function<String, Row>) record -> {
    String[] attributes = record.split(",");
    return RowFactory.create(attributes[0], attributes[1].trim());
});

// 字符串 schema
String schemaString = "name age";
// 根据字符串 schema 产生 schema
List<StructField> fields = new ArrayList<>();
for (String fieldName : schemaString.split(" ")) {
    StructField field = DataTypes.createStructField(fieldName, DataTypes.StringType, true);
    fields.add(field);
}
StructType schema = DataTypes.createStructType(fields);

// Dataset<Row>
Dataset<Row> peopleDataFrame = sparkSession.createDataFrame(rowRDD, schema);

// 临时视图
peopleDataFrame.createOrReplaceTempView("people");

// 运行SQL
Dataset<Row> results = sparkSession.sql("SELECT name FROM people");

Dataset<String> namesDS = results.map(
        (MapFunction<Row, String>) row -> "Name: " + row.getString(0),
        Encoders.STRING());
namesDS.show();
/**
 +-------------+
 |        value|
 +-------------+
 |Name: Michael|
 |   Name: Andy|
 | Name: Justin|
 +-------------+
 */
```
Scala版本：
```scala
import org.apache.spark.sql.types._

// Create an RDD
val peopleRDD = spark.sparkContext.textFile("src/main/resources/person.txt")

// The schema is encoded in a string
val schemaString = "name age"

// Generate the schema based on the string of schema
val fields = schemaString.split(" ")
  .map(fieldName => StructField(fieldName, StringType, nullable = true))
val schema = StructType(fields)

// Convert records of the RDD (people) to Rows
val rowRDD = peopleRDD
  .map(_.split(","))
  .map(attributes => Row(attributes(0), attributes(1).trim))

// Apply the schema to the RDD
val peopleDF = spark.createDataFrame(rowRDD, schema)

// Creates a temporary view using the DataFrame
peopleDF.createOrReplaceTempView("people")

// SQL can be run over a temporary view created using DataFrames
val results = spark.sql("SELECT name FROM people")

// The results of SQL queries are DataFrames and support all the normal RDD operations
// The columns of a row in the result can be accessed by field index or by field name
results.map(attributes => "Name: " + attributes(0)).show()
/**
 +-------------+
 |        value|
 +-------------+
 |Name: Michael|
 |   Name: Andy|
 | Name: Justin|
 +-------------+
 */
```

> Spark 版本: 2.3.1

原文：http://spark.apache.org/docs/2.3.1/sql-programming-guide.html#interoperating-with-rdds
