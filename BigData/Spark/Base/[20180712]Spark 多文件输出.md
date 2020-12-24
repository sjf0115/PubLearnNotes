---
layout: post
author: sjf0115
title: Spark 多文件输出
date: 2018-07-12 19:01:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-multiple-output-format
---

### 1. 自定义MultipleOutputFormat

在[Hadoop 多文件输出MultipleOutputFormat](http://smartsi.club/2017/03/15/hadoop-base-multiple-output-format/)中介绍了如何在Hadoop中根据Key或者Value的值将属于不同的类型的记录写到不同的文件中。在这里面用到了MultipleOutputFormat这个类。

因为Spark内部写文件方式其实调用的是Hadoop相关API，所以我们也可以通过Spark实现多文件输出。不过遗憾的是，Spark内部没有多文件输出的函数供我们直接使用。我们可以通过调用saveAsHadoopFile函数并自定义MultipleOutputFormat类来实现多文件输出，如下所示：
```java
public class RDDMultipleTextOutputFormat<K, V> extends MultipleTextOutputFormat<K, V> {
    @Override
    protected String generateFileNameForKeyValue(K key, V value, String name) {
        return key.toString();
    }
}
```
RDDMultipleTextOutputFormat类中的 `generateFileNameForKeyValue` 函数有三个参数，key和value是RDD对应的Key和Value，而name参数是每个Reduce的编号。上面例子中没有使用该参数，而是直接将同一个Key的数据输出到同一个文件中。我们来看看如何使用这个自定义的类：
```java
String appName = "MultipleTextOutputExample";
SparkConf conf = new SparkConf().setAppName(appName);
JavaSparkContext sc = new JavaSparkContext(conf);

JavaRDD<String> source = sc.textFile(inputPath);
// 以platform为key
JavaPairRDD<String, String> result = source.mapToPair(new PairFunction<String, String, String>() {
    @Override
    public Tuple2<String, String> call(String str) throws Exception {
        String[] params = str.split("\t");
        String platform = "other";
        if(params.length > 1 && StringUtils.isNotBlank(params[1])){
            platform = params[1];
        }
        return new Tuple2<>(platform, str);
    }
});
// 保存
result.saveAsHadoopFile(outputPath, String.class, String.class, RDDMultipleTextOutputFormat.class);
```
上面示例中通过调用 `saveAsHadoopFile` 函数并自定义 `MultipleOutputFormat` 类来实现多文件输出，如下所示输出：
```
[xiaosi@ying ~]$  sudo -uxiaosi hadoop fs -ls tmp/data_group/example/output/price
Found 3 items
-rw-r--r--   3 xiaosi xiaosi          0 2018-07-12 16:24 tmp/data_group/example/output/price/_SUCCESS
-rw-r--r--   3 xiaosi xiaosi     723754 2018-07-12 16:23 tmp/data_group/example/output/price/adr
-rw-r--r--   3 xiaosi xiaosi     799216 2018-07-12 16:23 tmp/data_group/example/output/price/ios
```
我们可以看到输出已经根据RDD的key将属于不同类型的记录写到不同的文件中，每个key对应一个文件，如果想每个key对应多个文件输出，需要修改一下我们自定义的RDDMultipleTextOutputFormat，如下代码所示：
```java
public class RDDMultipleTextOutputFormat<K, V> extends MultipleTextOutputFormat<K, V> {
    @Override
    protected String generateFileNameForKeyValue(K key, V value, String name) {
        return key.toString() + "/" + name;
    }
}
```
输出如下所示:
```
[xiaosi@ying ~]$  sudo -uxiaosi hadoop fs -ls tmp/data_group/example/output/price/
Found 3 items
-rw-r--r--   3 xiaosi xiaosi          0 2018-07-16 10:00 tmp/data_group/example/output/price/_SUCCESS
drwxr-xr-x   - xiaosi xiaosi          0 2018-07-16 10:00 tmp/data_group/example/output/price/adr
drwxr-xr-x   - xiaosi xiaosi          0 2018-07-16 10:00 tmp/data_group/example/output/price/ios
[xiaosi@ying ~]$
[xiaosi@ying ~]$  sudo -uxiaosi hadoop fs -ls tmp/data_group/example/output/price/adr/
Found 2 items
-rw-r--r--   3 xiaosi xiaosi 23835 2018-07-16 10:00 tmp/data_group/example/output/price/adr/part-00000
-rw-r--r--   3 xiaosi xiaosi      22972 2018-07-16 10:00 tmp/data_group/example/output/price/adr/part-00001
```

### 2. DataFrame 方式

如果你使用的是Spark 1.4+，借助DataFrame API会变得更加容易。（DataFrames是在Spark 1.3中引入的，但我们需要的partitionBy（）是在1.4中引入的。）

如果你使用的是RDD，首先需要将其转换为DataFrame。拥有DataFrame后，基于特定 key 输出到多个文件中就很简单了。
```java
SparkSession sparkSession = SparkSession
  .builder()
  .appName("MultipleTextOutputExample")
  .config("spark.some.config.option", "some-value")
  .getOrCreate();

JavaRDD<Price> priceRDD = sparkSession.read().textFile(inputPath).javaRDD().map(new Function<String, Price>() {
  @Override
  public Price call(String str) throws Exception {
    String[] params = str.split("\t");
    Price price = new Price();
    price.setDate(params[0]);
    price.setPlatform(params[1]);
    price.setAdType(params[2]);
    price.setChannelId(params[3]);
    price.setUid(params[4]);
    price.setPrice(params[5]);
    return price;
  }
});
Dataset<Row> priceDataFrame = sparkSession.createDataFrame(priceRDD, Price.class);
priceDataFrame.write().partitionBy("platform").json(outputPath);
```
在这个示例中，Spark将为我们在DataFrame上分区的每个 key 创建一个子目录：
```
[xiaosi@ying ~]$  sudo -uxiaosi hadoop fs -ls tmp/data_group/example/output/price/
Found 3 items
-rw-r--r--   3 xiaosi xiaosi  0 2018-07-16 15:41 tmp/data_group/example/output/price/_SUCCESS
drwxr-xr-x   - xiaosi xiaosi  0 2018-07-16 15:41 tmp/data_group/example/output/price/platform=adr
drwxr-xr-x   - xiaosi xiaosi  0 2018-07-16 15:41 tmp/data_group/example/output/price/platform=ios
```

参考：　https://www.iteblog.com/archives/1281.html

https://stackoverflow.com/questions/23995040/write-to-multiple-outputs-by-key-spark-one-spark-job
