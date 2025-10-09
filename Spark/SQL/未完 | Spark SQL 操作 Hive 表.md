
> Spark版本: 3.5.3

Spark SQL 支持读取和写入存储在 Apache Hive 中的数据。但是，由于 Hive 具有大量依赖项，这些依赖项不包含在默认 Spark 发行版中。如果在类路径 classpath 中可以找到 Hive 依赖项，Spark 会自动加载。需要注意的是这些 Hive 依赖项也必须存在于所有 Worker 节点上，因为需要访问 Hive 序列化和反序列化库 (SerDes)才可以访问存储在 Hive 中的数据。

通过将 hive-site.xml 文件放在 `conf/` 中来完成 Hive 配置，此外如果还需要访问 HDFS，也需要将 core-site.xml和 hdfs-site.xml 放在 `conf/` 中。

当使用 Hive 时，必须实例化支持 Hive 的 SparkSession，包括连接到持久化的 Hive 元数据，支持 Hive serdes 以及 Hive 用户自定义的函数。没有部署 Hive 的用户仍然可以启用 Hive 支持。当 hive-site.xml 未配置时，上下文会自动在当前目录中创建 `metastore_db`，并创建由 `spark.sql.warehouse.dir` 配置的目录，该目录默指向 Spark 应用程序启动时当前目录中的 spark-warehouse 目录。注意的是从 Spark 2.0.0 开始，`hive-site.xml` 中的 `hive.metastore.warehouse.dir` 属性已被弃用，使用 `spark.sql.warehouse.dir` 来指定 warehouse 中数据库的默认位置。你可能需要向启动 Spark 应用程序的用户授予写权限。

```

```

### 2. 指定 Hive 表的存储格式

创建 Hive 表时，需要定义如何 从/向 文件系统 read/write 数据，即 “输入格式” 和 “输出格式”。 您还需要定义该表如何将数据反序列化为行，或将行序列化为数据，即 “serde”。 以下选项可用于指定存储格式 (“serde”, “input format”, “output format”)，例如，CREATE TABLE src(id int) USING hive OPTIONS(fileFormat 'parquet')。 默认情况下，我们将以纯文本形式读取表格文件。 请注意，Hive 存储处理程序在创建表时不受支持，您可以使用 Hive 端的存储处理程序创建一个表，并使用 Spark SQL 来读取它。


### 3. 与不同版本的 Hive Metastore 进行交互

Spark SQL 的 Hive 支持的最重要的部分之一是与 Hive metastore 进行交互，这使得 Spark SQL 能够访问 Hive 表的元数据。从 Spark 1.4.0 开始，使用 Spark SQL 的单一二进制构建可以使用下面所述的配置来查询不同版本的 Hive 元数据。请注意，独立于用于与转移点通信的 Hive 版本，内部 Spark SQL 将针对 Hive 1.2.1 进行编译，并使用这些类进行内部执行（serdes，UDF，UDAF等）。



## 编程方式读写 Hive

### 1.1 配置

将 Hive 的配置文件 `$HIVE_HOME/conf/hive-site.xml` 拷贝到 `resources` 目录下：

![]()

### 1.2 添加依赖

添加 Hive 依赖：
```xml
<!-- Spark Hive -->
<dependency>
    <groupId>org.apache.spark</groupId>
    <artifactId>spark-hive_${scala.binary.version}</artifactId>
    <version>${spark.version}</version>
</dependency>
```
Spark 使用 Hive 元数据存储时，需要连接到 MySQL 数据库来存储元数据信息，因此需要添加如下 MySQL 驱动依赖：
```xml
<dependency>
    <groupId>mysql</groupId>
    <artifactId>mysql-connector-java</artifactId>
    <version>8.0.33</version>
</dependency>
```

### 1.3 读取 Hive

> 与 Hive 交互需要开启 enableHiveSupport()

```java
SparkSession spark = SparkSession
        .builder()
        .master("local[*]")
        .appName("Java Spark Hive Example")
        .enableHiveSupport()
        .getOrCreate();

// 读取
spark.sql("show databases").show();
// +---------+
// |namespace|
// +---------+
// |  default|
// +---------+
spark.sql("show tables").show();
// +--------+--------------------+-----------+
// |database|           tableName|isTemporary|
// +--------+--------------------+-----------+
// | default|   dim_user_behavior|      false|
// | default|  dws_mt_qs_order_dd|      false|
// | default|            tb_order|      false|
// | default|     tb_order_bucket|      false|
// | default|tb_order_sorted_b...|      false|
// | default|          tb_payment|      false|
// | default|   tb_payment_bucket|      false|
// | default|tb_payment_sorted...|      false|
// | default|          tb_product|      false|
// | default|         tb_province|      false|
// | default|tmp_hive_managed_...|      false|
// | default|       user_behavior|      false|
// +--------+--------------------+-----------+
spark.sql("SELECT COUNT(*) FROM tb_order").show();
// +--------+
// |count(1)|
// +--------+
// |20000000|
// +--------+
```

### 1.4 写入 Hive

```java
SparkSession spark = SparkSession
        .builder()
        .master("local[*]")
        .appName("HiveWriteExample")
        .enableHiveSupport()
        .getOrCreate();

// 创建 Hive 表
spark.sql("CREATE TABLE IF NOT EXISTS src (key INT, value STRING) USING hive");
// 导入数据
spark.sql("LOAD DATA LOCAL INPATH 'spark-example-3.5/src/main/resources/data/kv.txt' INTO TABLE src");

// 查询
spark.sql("SELECT * FROM src").show();
// +---+-------+
// |key|  value|
// +---+-------+
// |238|val_238|
// | 86| val_86|
// |311|val_311|
// ...

// 聚合
spark.sql("SELECT COUNT(*) FROM src").show();
// +--------+
// |count(1)|
// +--------+
// |    500 |
// +--------+
```

### 1.5 与DataSet/DataFrame交互

```java
SparkSession spark = SparkSession
        .builder()
        .master("local[*]")
        .appName("HiveDataSetExample")
        .enableHiveSupport()
        .getOrCreate();

// DataFrame
// SQL 查询的结果本身就是 dataframe，并支持所有正常功能。
Dataset<Row> dataFrame = spark.sql("SELECT key, value FROM src WHERE key < 10 ORDER BY key");
dataFrame.show();
/*+---+-----+
|key|value|
+---+-----+
|  0|val_0|
|  0|val_0|
|  0|val_0|
|  2|val_2|
|  4|val_4|
|  5|val_5|
|  5|val_5|
|  5|val_5|
|  8|val_8|
|  9|val_9|
+---+-----+*/

// DataSet
Dataset<String> dataset = dataFrame.map(
        (MapFunction<Row, String>) row -> "Key: " + row.get(0) + ", Value: " + row.get(1),
        Encoders.STRING());
dataset.show();

/*+--------------------+
|               value|
+--------------------+
|Key: 0, Value: val_0|
|Key: 0, Value: val_0|
|Key: 0, Value: val_0|
|Key: 2, Value: val_2|
|Key: 4, Value: val_4|
|Key: 5, Value: val_5|
|Key: 5, Value: val_5|
|Key: 5, Value: val_5|
|Key: 8, Value: val_8|
|Key: 9, Value: val_9|
+--------------------+*/
```



原文：https://spark.apache.org/docs/3.5.3/sql-data-sources-hive-tables.html#specifying-storage-format-for-hive-tables
https://cloud.tencent.com/developer/article/1733891
