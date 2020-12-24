
### 2. Parquet Files

`Parquet`是一种很多数据处理系统支持的列式存储格式。Spark SQL提供对Parquet文件的读写支持，而且Parquet文件能够自动保存原始数据的模式`schema`。当写Parquet文件的时，为了兼容，所有的字段都会自动转成可为null`nullable`。

#### 2.1 编程方式加载数据

Java版本：
```
Dataset<Row> peopleDF = session.read().json("SparkDemo/src/main/resources/people.json");
// DateFrame保存为parquet文件并保留schema信息
peopleDF.write().parquet("people.parquet");

// 读取上面创建的parquet文件
Dataset<Row> parquetFileDF = session.read().parquet("people.parquet");
parquetFileDF.show();

// Parquet文件也可用于创建临时视图 然后在SQL语句中使用
parquetFileDF.createOrReplaceTempView("parquetFile");
Dataset<Row> namesDF = session.sql("SELECT name FROM parquetFile WHERE age BETWEEN 13 AND 19");
Dataset<String> namesDS = namesDF.map(new MapFunction<Row, String>() {
    public String call(Row row) {
        return "Name: " + row.getString(0);
    }
}, Encoders.STRING());
namesDS.show();
```
输出结果：
```
+----+-------+
| age|   name|
+----+-------+
|null|Michael|
|  30|   Andy|
|  19| Justin|
+----+-------+

+------------+
|       value|
+------------+
|Name: Justin|
+------------+
```
Scala版本：
```
// Encoders for most common types are automatically provided by importing spark.implicits._
import spark.implicits._

val peopleDF = spark.read.json("examples/src/main/resources/people.json")

// DataFrames can be saved as Parquet files, maintaining the schema information
peopleDF.write.parquet("people.parquet")

// Read in the parquet file created above
// Parquet files are self-describing so the schema is preserved
// The result of loading a Parquet file is also a DataFrame
val parquetFileDF = spark.read.parquet("people.parquet")

// Parquet files can also be used to create a temporary view and then used in SQL statements
parquetFileDF.createOrReplaceTempView("parquetFile")
val namesDF = spark.sql("SELECT name FROM parquetFile WHERE age BETWEEN 13 AND 19")
namesDF.map(attributes => "Name: " + attributes(0)).show()
```

Python版本：
```
peopleDF = spark.read.json("examples/src/main/resources/people.json")

# DataFrames can be saved as Parquet files, maintaining the schema information.
peopleDF.write.parquet("people.parquet")

# Read in the Parquet file created above.
# Parquet files are self-describing so the schema is preserved.
# The result of loading a parquet file is also a DataFrame.
parquetFile = spark.read.parquet("people.parquet")

# Parquet files can also be used to create a temporary view and then used in SQL statements.
parquetFile.createOrReplaceTempView("parquetFile")
teenagers = spark.sql("SELECT name FROM parquetFile WHERE age >= 13 AND age <= 19")
teenagers.show()
```

#### 2.2 分区发现

表分区`Table partitioning`是在像Hive这样的系统中使用的常见的优化方法。在分区表中，数据通常存储在不同的目录中，并且将分区列值编码在每个分区目录的路径中(with partitioning column values encoded in the path of each partition directory)。 Parquet数据源现在可以自动发现和推断分区信息。 例如，我们可以使用以下目录结构将以前使用的所有人口数据存储到分区表中，其中包含两个额外的列作为分区列，分别为gender和country：

```
path
└── to
    └── table
        ├── gender=male
        │   ├── ...
        │   │
        │   ├── country=US
        │   │   └── data.parquet
        │   ├── country=CN
        │   │   └── data.parquet
        │   └── ...
        └── gender=female
            ├── ...
            │
            ├── country=US
            │   └── data.parquet
            ├── country=CN
            │   └── data.parquet
            └── ...
```

将`path/to/table`路径传递给`SparkSession.read.parquet`或`SparkSession.read.load`其中任意一个，Spark SQL将自动从路径中提取分区信息。现在返回的DataFrame的模式变成：

```
root
|-- name: string (nullable = true)
|-- age: long (nullable = true)
|-- gender: string (nullable = true)
|-- country: string (nullable = true)
```
请注意，分区列的数据类型是自动推断出来的。目前，可以支持数字数据类型和字符串类型。有些时候，用户可能不想自动推断分区列的数据类型。对于这些用例，类型自动推断可以由`spark.sql.sources.partitionColumnTypeInference.enabled`配置，默认为true。当禁用类型推断时，分区列将使用字符串类型。

从Spark 1.6.0开始，默认情况下，分区发现只能找到给定路径下的分区。 对于上述示例，如果用户将`path/to/table/gender=male`传递给`SparkSession.read.parquet`或`SparkSession.read.load`，那么`gender`不会被视为分区列。如果用户需要指定分区发现应该开始的基本路径，则可以在数据源选项中设置`basePath`。 例如，当`path/to/table/gender=male`是数据的路径，用户只有将`basePath`设置为`path/to/table/`时，`gender`才是一个分区列。


#### 2.3 Schema 合并

像ProtocolBuffer，Avro和Thrift一样，Parquet也支持`schema`演进。用户可以从一个简单的`schema`开始，并根据需要逐渐向`schema`中添加更多的列。以这种方式，用户最终会得到多个`schema`不同但相互兼容的Parquet文件。Parquet数据源现在能够自动检测这种情况并合并这些文件的模式。

由于`schema`合并是一个成本相对较高的操作，并且在大多数情况下不是必需的，所以从1.5.0开始默认情况下是关闭的。你可以通过如下方式启用它：

- 在读取`Parquet`文件时，将数据源选项`mergeSchema`设置为true（如下面的示例所示）或
- 将全局SQL选项`spark.sql.parquet.mergeSchema`设置为true。

```
List<Square> squares = new ArrayList<>();
for (int value = 1; value <= 5; value++) {
    Square square = new Square();
    square.setValue(value);
    square.setSquare(value * value);
    squares.add(square);
}

// Create a simple DataFrame, store into a partition directory
Dataset<Row> squaresDF = session.createDataFrame(squares, Square.class);
squaresDF.write().parquet("data/test_table/key=1");

List<Cube> cubes = new ArrayList<>();
for (int value = 6; value <= 10; value++) {
    Cube cube = new Cube();
    cube.setValue(value);
    cube.setCube(value * value * value);
    cubes.add(cube);
}

// Create another DataFrame in a new partition directory,
// adding a new column and dropping an existing column
Dataset<Row> cubesDF = session.createDataFrame(cubes, Cube.class);
cubesDF.write().parquet("data/test_table/key=2");

// Read the partitioned table
Dataset<Row> mergedDF = session.read().option("mergeSchema", true).parquet("data/test_table");
mergedDF.printSchema();
```


#### 2.4 Hive metastore Parquet table conversion

##### 2.4.1 Hive/Parquet Schema Reconciliation

##### 2.4.2 Metadata Refreshing

#### 2.5 Configuration

可以使用SparkSession上的`setConf`方法或使用SQL运行`SET key = value`命令来完成Parquet的配置。

配置项|默认值|描述
---|---|---
spark.sql.parquet.binaryAsString	|false|一些其他Parquet-producing生产系统，特别是Impala，Hive和旧版本的Spark SQL，在写出Parquet模式时，不区分二进制数据和字符串。 该标志告诉Spark SQL将二进制数据解释为字符串以提供与这些系统的兼容性。






#### 3. JSON Datasets

Spark SQL可以自动推断JSON数据集的模式，并加载json文件返回`DataSet<Row>`。可以使用`SparkSession.read().json()`，在一个字符串RDD上或一个JSON文件上完成上述转换。

请注意，文件由`json file`提供而不是典型的JSON文件(the file that is offered as a json file is not a typical JSON file.)。 每行必须包含一个单独的，独立的有效的JSON对象。 有关更多信息，请参阅[JSON Lines文本格式，也称为换行符分隔的JSON](http://jsonlines.org/)。 因此，常规的多行JSON文件通常会失败。

```
// JSON数据集由给定路径指定
// 该路径可以是单个文本文件或存储文本文件的目录
Dataset<Row> people = session.read().json("SparkDemo/src/main/resources/people.json");
// 推断模式
people.printSchema();

// 使用DataFrame创建临时视图
people.createOrReplaceTempView("people");

// 可以使用由spark提供的sql方法来运行SQL语句
Dataset<Row> namesDF = session.sql("SELECT name FROM people WHERE age BETWEEN 13 AND 19");
namesDF.show();

// DataFrame可以由一个RDD[String](每个字符串一个JSON对象)表示的JSON数据集创建
List<String> jsonData = Arrays.asList(
        "{\"name\":\"Yin\",\"address\":{\"city\":\"Columbus\",\"state\":\"Ohio\"}}");
JavaRDD<String> anotherPeopleRDD =
        new JavaSparkContext(session.sparkContext()).parallelize(jsonData);
Dataset anotherPeople = session.read().json(anotherPeopleRDD);
anotherPeople.show();
```
结果输出：
```
root
 |-- age: long (nullable = true)
 |-- name: string (nullable = true)

+------+
|  name|
+------+
|Justin|
+------+

+---------------+----+
|        address|name|
+---------------+----+
|[Columbus,Ohio]| Yin|
+---------------+----+
```

#### 4. Hive 表

Spark SQL还支持读取和写入存储在Apache Hive中的数据。 但是，由于Hive具有大量依赖关系，因此这些依赖关系不包含在默认的Spark发布包里。 如果在classpath中找到Hive依赖项，Spark将自动加载它们。请注意，这些Hive依赖关系也必须存在于所有工作节点上，因为它们将需要访问Hive序列化和反序列化库（SerDes），以访问存储在Hive中的数据。

Hive的配置是通过conf文件下的`hive-site.xml`，`core-site.xml`（用于安全配置）和`hdfs-site.xml`（用于HDFS配置）完成的。

当使用Hive时，必须在Hive支持下实例化`SparkSession`，包括与持久化的Hive`metastore`连接，支持Hive 序列化和Hive用户定义的功能。 没有部署Hive的用户仍然可以启用Hive支持。当hive-site.xml未配置时，上下文会自动在当前目录中创建`metastore_db`，并创建由`spark.sql.warehouse.dir`配置的目录，该目录默认为Spark应用程序启动的当前目录下的`spark-warehouse`目录(which defaults to the directory spark-warehouse in the current directory that the Spark application is started. )．请注意，自Spark 2.0.0以来，hive-site.xml中的`hive.metastore.warehouse.dir`属性已被弃用。 而是使用`spark.sql.warehouse.dir`来指定仓库中数据库的默认位置。你可能需要向启动Spark应用程序的用户授予写权限。

```
// warehouseLocation指向数据库和表的默认位置
String warehouseLocation = "/home/xiaosi/code/OpenDiary/SparkDemo/spark-warehouse";
SparkSession session = SparkSession.builder()
        .appName("Java Spark Hive Example")
        .config("spark.sql.warehouse.dir", warehouseLocation)
        .config("spark.master", "local")
        .enableHiveSupport()
        .getOrCreate();

session.sql("CREATE TABLE IF NOT EXISTS src (key INT, value STRING)");
session.sql("LOAD DATA LOCAL INPATH 'SparkDemo/src/main/resources/kv1.txt' INTO TABLE src");

// 使用HiveQL进行查询
session.sql("SELECT * FROM src").show();

// 支持聚合查询
session.sql("SELECT COUNT(*) FROM src").show();

// SQL查询的结果本身就是DataFrames 并支持所有基本的功能
Dataset<Row> sqlDF = session.sql("SELECT key, value FROM src WHERE key < 10 ORDER BY key");

// DataFrame中的条目数据类型是Row 它允许你按顺序访问每一列
Dataset<String> stringsDS = sqlDF.map(new MapFunction<Row, String>() {
    @Override
    public String call(Row row) throws Exception {
        return "Key: " + row.get(0) + ", Value: " + row.get(1);
    }
}, Encoders.STRING());
stringsDS.show();

// 使用DataFrame在SparkSession中创建临时视图
List<Record> records = new ArrayList<>();
for (int key = 1; key < 100; key++) {
    Record record = new Record();
    record.setKey(key);
    record.setValue("val_" + key);
    records.add(record);
}
Dataset<Row> recordsDF = session.createDataFrame(records, Record.class);
recordsDF.createOrReplaceTempView("records");
// 可以使用Hive中存储的数据与DataFrames数据进行Join操作
session.sql("SELECT * FROM records r JOIN src s ON r.key = s.key").show();
```
输出结果：
```
+----+-------+
| key|  value|
+----+-------+
|null|   null|
| 238|val_238|
|  86| val_86|
| 311|val_311|
|  27| val_27|
| 165|val_165|
| 409|val_409|
| 255|val_255|
| 278|val_278|
|  98| val_98|
| 484|val_484|
| 265|val_265|
| 193|val_193|
| 401|val_401|
| 150|val_150|
| 273|val_273|
| 224|val_224|
| 369|val_369|
|  66| val_66|
| 128|val_128|
+----+-------+
only showing top 20 rows

+--------+
|count(1)|
+--------+
|     501|
+--------+

+--------------------+
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
+--------------------+

+---+------+---+------+
|key| value|key| value|
+---+------+---+------+
|  2| val_2|  2| val_2|
|  4| val_4|  4| val_4|
|  5| val_5|  5| val_5|
|  5| val_5|  5| val_5|
|  5| val_5|  5| val_5|
|  8| val_8|  8| val_8|
|  9| val_9|  9| val_9|
| 10|val_10| 10|val_10|
| 11|val_11| 11|val_11|
| 12|val_12| 12|val_12|
| 12|val_12| 12|val_12|
| 15|val_15| 15|val_15|
| 15|val_15| 15|val_15|
| 17|val_17| 17|val_17|
| 18|val_18| 18|val_18|
| 18|val_18| 18|val_18|
| 19|val_19| 19|val_19|
| 20|val_20| 20|val_20|
| 24|val_24| 24|val_24|
| 24|val_24| 24|val_24|
+---+------+---+------+
only showing top 20 rows


```


#### 4.1 Interacting with Different Versions of Hive Metastore

### 5. JDBC To Other Databases

Spark SQL还包括可以使用JDBC从其他数据库读取数据的数据源。相比于使用JdbcRDD，应该将JDBC数据源的方式作为首选，因为JDBC数据源能够将结果作为DataFrame对象返回，直接用Spark SQL处理或与其他数据源连接。JDBC数据源也更容易在Java或Python中使用，因为它不需要用户提供ClassTag。

==注意==

这不同于Spark SQL JDBC服务器，可以允许其他应用程序使用`Spark SQL`运行查询。

要使用`JDBC`数据源，你需要在Spark classpath 中包含指定数据库的JDBC驱动程序。 例如，要从Spark Shell连接到postgres，你将运行以下命令：

```
bin/spark-shell --driver-class-path postgresql-9.4.1207.jar --jars postgresql-9.4.1207.jar
```
可以使用Data Sources API将来自远程数据库的表加载为`DataFrame`或Spark SQL临时视图。用户可以在数据源选项中指定JDBC连接属性。 用户和密码通常作为登录数据源的连接属性提供。 除了连接属性外，Spark还支持以下不区分大小写的选项：

属性 | 说明
---|---
url | 要连接的JDBC URL。特定数据源的连接属性可以在URL中指定。例如`jdbc:mysql://localhost:3306/test`
dbtable | 要读取的JDBC表。 请注意，在SQL查询FROM子句中任何有效的内容都可以使用。 例如，你可以使用括号中的子查询代替完整表
driver | 用于连接到此URL的JDBC驱动程序的类名。
partitionColumn, lowerBound, upperBound, numPartitions | 这几个选项，如果指定其中一个，则必须全部指定。他们描述了多个worker如何并行的读入数据，并将表分区。partitionColumn必须是所查询的表中的一个数值字段。注意，lowerBound和upperBound只是用于决定分区跨度的，而不是过滤表中的行。因此，表中所有的行都会被分区然后返回．
fetchsize | JDBC fetch size，决定每次获取多少行数据。 该选项可以帮助JDBC驱动程序提高性能，默认具有较低的提取大小（例如，Oracle每次提取10行数据）． 此选项仅适用于读操作．
batchsize | JDBC batch size，决定每次插入多少行数据。 该选项可以帮助JDBC驱动程序提高性能。 此选项仅适用于写操作。默认大小为1000．
isolationLevel | 事务隔离级别，适用于当前连接．它可以是`NONE`，`READ_COMMITTED`，`READ_UNCOMMITTED`，`REPEATABLE_READ`或`SERIALIZABLE`之一，对应于JDBC连接对象定义的标准事务隔离级别，默认为`READ_UNCOMMITTED`。 此选项仅适用于写操作。 请参考java.sql.Connection中的文档。
truncate | 这是一个与JDBC writer相关的选项。 启用`SaveMode.Overwrite`时，此选项会导致Spark截断现有表，而不是删除并重新创建。 这可以更有效，并且防止表元数据（例如，索引）被移除。 但是，在某些情况下，例如当新数据具有不同的模式时，它将无法工作。 它默认为false。 此选项仅适用于写操作．
createTableOptions | 这是一个与JDBC writer相关的选项。 如果指定，此选项允许在创建表时设置特定数据库表和分区的选项（例如，CREATE TABLE t（name string）ENGINE = InnoDB。）。 此选项仅适用于写操作。
```
// JDBC加载和保存可以通过load / save或jdbc方法来实现

// 使用load方法加载或保存JDBC
String url = "jdbc:mysql://localhost:3306/test";
String personsTable = "Persons";
String personsCopyTable = "PersonsCopy";

Dataset<Row> jdbcDF = session.read()
        .format("jdbc")
        .option("url", url)
        .option("dbtable", personsTable)
        .option("user", "root")
        .option("password", "root")
        .load();

jdbcDF.write()
        .format("jdbc")
        .option("url", url)
        .option("dbtable", personsCopyTable)
        .option("user", "root")
        .option("password", "root")
        .save();

// 使用jdbc方法加载或保存JDBC
Properties connectionProperties = new Properties();
connectionProperties.put("user", "root");
connectionProperties.put("password", "root");
Dataset<Row> jdbcDF2 = session.read().jdbc(url, personsTable, connectionProperties);

jdbcDF2.write().jdbc(url, personsCopyTable, connectionProperties);
```

Scala版本：
```
// Note: JDBC loading and saving can be achieved via either the load/save or jdbc methods
// Loading data from a JDBC source
val jdbcDF = spark.read
  .format("jdbc")
  .option("url", "jdbc:postgresql:dbserver")
  .option("dbtable", "schema.tablename")
  .option("user", "username")
  .option("password", "password")
  .load()

val connectionProperties = new Properties()
connectionProperties.put("user", "username")
connectionProperties.put("password", "password")
val jdbcDF2 = spark.read
  .jdbc("jdbc:postgresql:dbserver", "schema.tablename", connectionProperties)

// Saving data to a JDBC source
jdbcDF.write
  .format("jdbc")
  .option("url", "jdbc:postgresql:dbserver")
  .option("dbtable", "schema.tablename")
  .option("user", "username")
  .option("password", "password")
  .save()

jdbcDF2.write
  .jdbc("jdbc:postgresql:dbserver", "schema.tablename", connectionProperties)
```

Python版本：
```
# Note: JDBC loading and saving can be achieved via either the load/save or jdbc methods
# Loading data from a JDBC source
jdbcDF = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:postgresql:dbserver") \
    .option("dbtable", "schema.tablename") \
    .option("user", "username") \
    .option("password", "password") \
    .load()

jdbcDF2 = spark.read \
    .jdbc("jdbc:postgresql:dbserver", "schema.tablename",
          properties={"user": "username", "password": "password"})

# Saving data to a JDBC source
jdbcDF.write \
    .format("jdbc") \
    .option("url", "jdbc:postgresql:dbserver") \
    .option("dbtable", "schema.tablename") \
    .option("user", "username") \
    .option("password", "password") \
    .save()

jdbcDF2.write \
    .jdbc("jdbc:postgresql:dbserver", "schema.tablename",
          properties={"user": "username", "password": "password"})
```


#### 5.1 故障排除

- JDBC driver class必须在所有client session或者executor上，对Java的原生classloader可见。这是因为Java的`DriverManager`在打开一个连接之前，会做安全检查，并忽略所有对原声classloader不可见的driver。最简单的一种方法，就是在所有worker节点上修改`compute_classpath.sh`，并包含你所需的driver jar包。
- 一些数据库，如H2，会把所有的名字转大写。对于这些数据库，在Spark SQL中必须也使用大写。



==当前版本==

2.1.1

原文：http://spark.apache.org/docs/latest/sql-programming-guide.html#data-sources
