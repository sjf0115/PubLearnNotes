---
layout: post
author: sjf0115
title: Spark SQL DataFrame 与 RDD 交互
date: 2018-07-14 13:31:01
tags:
  - Spark
  - Spark SQL

categories: Spark
permalink: spark-sql-dataframe-interoperating-with-rdds
---

> Spark 版本: 3.1.3

Spark SQL 支持两种不同的方法将现有 RDD 转换为 Datasets。
- 第一种方法使用反射来推断 RDD 的 Schema。当你编写 Spark 应用程序时已经知道了 Schema，这种情况下基于反射的方法会使代码更简洁，并且运行良好。
- 第二种方法是通过编程接口来创建 DataSet，这种方法允许构建一个 schema，并将其应用到现有的 RDD 上。虽然这种方法更详细，但直到运行时才知道列及其类型，才能构造 DataSets。

### 1. 使用反射推导schema

Spark SQL 支持自动将 JavaBeans 的 RDD 转换为 DataFrame。使用反射获取的 BeanInfo 定义了表的 schema。目前为止，Spark SQL 还不支持包含 Map 字段的 JavaBean。但是支持嵌套的 JavaBeans，List 以及 Array 字段。你可以通过创建一个实现 Serializable 的类并为其所有字段设置 getter 和 setter 方法来创建一个 JavaBean。

```java
// 从文本文件中创建 Person 对象的 RDD
JavaRDD<Person> peopleRDD = spark.read()
        .textFile("spark-example-3.1/src/main/resources/data/people.csv")
        .javaRDD()
        .map(line -> {
            String[] parts = line.split(",");
            Person person = new Person();
            person.setName(parts[0]);
            person.setAge(Integer.parseInt(parts[1].trim()));
            return person;
        });

// 在 JavaBean 的 RDD 上应用 schema 生成 DataFrame
Dataset<Row> peopleDF = spark.createDataFrame(peopleRDD, Person.class);
// 注册为临时视图
peopleDF.createOrReplaceTempView("people");

// 运行 SQL 获取 DataFrame
Dataset<Row> teenagersDF = spark.sql("SELECT name FROM people WHERE age BETWEEN 13 AND 19");

// Row 中的列可以通过字段索引获取
Encoder<String> stringEncoder = Encoders.STRING();
Dataset<String> teenagerNamesByIndexDF = teenagersDF.map(
        (MapFunction<Row, String>) row -> "Name: " + row.getString(0),
        stringEncoder);
teenagerNamesByIndexDF.show();
// +------------+
// |       value|
// +------------+
// |Name: Justin|
// +------------+

// Row 中的列可以通过字段名称获取
Dataset<String> teenagerNamesByFieldDF = teenagersDF.map(
        (MapFunction<Row, String>) row -> "Name: " + row.<String>getAs("name"),
        stringEncoder);
teenagerNamesByFieldDF.show();
// +------------+
// |       value|
// +------------+
// |Name: Justin|
// +------------+
```

### 2. 使用编程方式指定 Schema

当 JavaBean 类不能提前定义时（例如，记录的结构以字符串编码，或者解析文本数据集，不同用户字段映射方式不同），可以通过编程方式创建 DataSet<Row>，有如下三个步骤：
- 创建原始 RDD(例如，JavaRDD<String>);
```java
// 原始 RDD
JavaRDD<String> peopleRDD = spark.sparkContext()
        .textFile("spark-example-3.1/src/main/resources/data/people.csv", 1)
        .toJavaRDD();
```
- 将原始 RDD 转化为 Rows 的 RDD
```java
// 将原始 RDD 转化为 Rows 的 RDD
JavaRDD<Row> rowRDD = peopleRDD.map((Function<String, Row>) record -> {
    String[] attributes = record.split(",");
    return RowFactory.create(attributes[0], attributes[1].trim());
});
```
- 创建由 StructType 表示的 schema，与步骤1中创建的 RDD 中的 Rows 结构相匹配，在这有两个字段：name 和 age。
```java
String schemaString = "name age";
List<StructField> fields = new ArrayList<>();
for (String fieldName : schemaString.split(" ")) {
    StructField field = DataTypes.createStructField(fieldName, DataTypes.StringType, true);
    fields.add(field);
}
StructType schema = DataTypes.createStructType(fields);
```
- 通过 SparkSession 提供的 createDataFrame 方法将 schema 应用到 Rows 的 RDD。
```java
Dataset<Row> peopleDataFrame = spark.createDataFrame(rowRDD, schema);
```

完整示例如下所示：
```java
// 1. 原始 RDD
JavaRDD<String> peopleRDD = spark.sparkContext()
        .textFile("spark-example-3.1/src/main/resources/data/people.csv", 1)
        .toJavaRDD();

// 2. 将原始 RDD 转化为 Rows 的 RDD
JavaRDD<Row> rowRDD = peopleRDD.map((Function<String, Row>) record -> {
    String[] attributes = record.split(",");
    return RowFactory.create(attributes[0], attributes[1].trim());
});

// 3. 创建 Schema
String schemaString = "name age";
List<StructField> fields = new ArrayList<>();
for (String fieldName : schemaString.split(" ")) {
    StructField field = DataTypes.createStructField(fieldName, DataTypes.StringType, true);
    fields.add(field);
}
StructType schema = DataTypes.createStructType(fields);

// 4. 将 Schema 应用到 RDD 上创建 DataFrame
Dataset<Row> peopleDataFrame = spark.createDataFrame(rowRDD, schema);

// 在 DataFrame 上创建临时视图
peopleDataFrame.createOrReplaceTempView("people");

// 运行 SQL
Dataset<Row> results = spark.sql("SELECT name FROM people");

// 通过下标获取 name 字段
Dataset<String> namesDS = results.map(
        (MapFunction<Row, String>) row -> "Name: " + row.getString(0),
        Encoders.STRING());
namesDS.show();
// +-------------+
// |        value|
// +-------------+
// |Name: Michael|
// |   Name: Andy|
// | Name: Justin|
// +-------------+
```

原文：[Interoperating with RDDs](https://spark.apache.org/docs/3.1.3/sql-getting-started.html#interoperating-with-rdds)
