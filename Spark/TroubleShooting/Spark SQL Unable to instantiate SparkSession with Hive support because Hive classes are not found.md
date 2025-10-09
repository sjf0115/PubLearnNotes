
## 1. 问题描述

在使用 Spark SQL 实现查询 Hive 时：
```java
String warehouseLocation = "spark-warehouse";
SparkSession session = SparkSession.builder()
        .appName("Java Spark Hive Example")
        .config("spark.sql.warehouse.dir", warehouseLocation)
        .enableHiveSupport()
        .getOrCreate();
session.sql("CREATE TABLE IF NOT EXISTS src (key INT, value STRING)");
session.sql("LOAD DATA LOCAL INPATH 'SparkDemo/src/main/resources/kv1.txt' INTO TABLE src");

session.sql("SELECT * FROM src").show();
```
出现如下异常：
```java
Exception in thread "main" java.lang.IllegalArgumentException: Unable to instantiate SparkSession with Hive support because Hive classes are not found.
	at org.apache.spark.sql.SparkSession$Builder.enableHiveSupport(SparkSession.scala:815)
	at com.sjf.open.sql.DataSourceDemo.hiveTable(DataSourceDemo.java:104)
	at com.sjf.open.sql.DataSourceDemo.main(DataSourceDemo.java:114)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at com.intellij.rt.execution.application.AppMain.main(AppMain.java:144)
```
## 2. 解决方案

添加如下依赖：
```xml
<dependency>
    <groupId>org.apache.spark</groupId>
    <artifactId>spark-hive_2.11</artifactId>
    <version>3.5.3</version>
    <scope>provided</scope>
</dependency>
```
