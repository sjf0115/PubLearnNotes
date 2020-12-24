



启动 Metastore:
```
bin/hive--service metastore
```
后台启动:
```
bin/hive --service metastore 2>&1 >> /var/log.log &
bin/hive --service metastore 2>&1 >> /dev/null &
```

对于 hive 1.2 及以上的版本，hive不再使用，而直接使用 hiveserver2 命令；
```
hiveserver2 &
```


How to connect to a Hive metastore programmatically in SparkSQL?

Spark 1.x:
```java
final SparkConf conf = new SparkConf();
SparkContext sc = new SparkContext(conf);
HiveContext hiveContext = new HiveContext(sc);
hiveContext.setConf("hive.metastore.uris", "thrift://METASTORE:PORT");
```
Spark 2.x:
```java
SparkSession sparkSession = SparkSession
  .builder()
  .appName("Java Spark Hive Example")
  .config("spark.sql.warehouse.dir", "/user/hive/warehouse")
  .config("hive.metastore.uris", "thrift://METASTORE:PORT")
  .enableHiveSupport()
  .getOrCreate();
```











资料：https://www.cnblogs.com/juncaoit/p/6545092.html
