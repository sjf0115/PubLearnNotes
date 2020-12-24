---
layout: post
author: sjf0115
title: Spark 理解Spark序列化
date: 2018-05-27 13:28:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-understanding-spark-serialization
---

序列化对象意味着将其状态转换为字节流，以便字节流可以恢复为对象的副本。如果 Java 对象或其任何父类实现了 `java.io.Serializable` 接口或其子接口 `java.io.Externalizable`，则该 Java 对象可以序列化。

类不会被序列化，除非类的对象被序列化了。如果对象需要持久化或在网络上传输，则需要序列化对象。

Class Component|Serialization
---|---
instance variable           |yes
Static instance variable    |no
methods                     |no
Static methods              |no
Static inner class          |no
local variables             |no


我们来看一个Spark代码示例，并看一下各种场景：
```Java
public class SparkSample {

  public int instanceVariable                =10 ;
  public static int staticInstanceVariable   =20 ;

  public int run(){

     int localVariable                       =30;

     // create Spark conf
     final SparkConf sparkConf = new SparkConf().setAppName(config.get(JOB_NAME).set("spark.serializer", "org.apache.spark.serializer.KryoSerializer");

     // create spark context
     final JavaSparkContext sparkContext = new JavaSparkContext(sparkConf);

    // read DATA
    JavaRDD<String> lines = spark.read().textFile(args[0]).javaRDD();


    // Anonymous class used for lambda implementation
    JavaRDD<String> words = lines.flatMap(new FlatMapFunction<String, String>() {
            @Override
            public Iterator<String> call(String s) {
            // How will the listed varibles be accessed in RDD across driver and Executors
            System.out.println("Output :" + instanceVariable + " " + staticInstanceVariable + " " + localVariable);
            return Arrays.asList(SPACE.split(s)).iterator();
    });

    // SAVE OUTPUT
    words.saveAsTextFile(OUTPUT_PATH));

  }

   // Inner Static class for the funactional interface which can replace the lambda implementation above
   public static class MapClass extends FlatMapFunction<String, String>() {
            @Override
            public Iterator<String> call(String s) {
            System.out.println("Output :" + instanceVariable + " " + staticInstanceVariable + " " + localVariable);
            return Arrays.asList(SPACE.split(s)).iterator();
    });

    public static void main(String[] args) throws Exception {
        JavaWordCount count = new JavaWordCount();
        count.run();
    }
}
```


























原文：https://stackoverflow.com/questions/40818001/understanding-spark-serialization
