---
layout: post
author: sjf0115
title: Spark 第一个Spark程序WordCount
date: 2018-03-11 15:03:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-first-application-word-count
---

### 1 Maven 依赖
```
<spark.version>2.1.0</spark.version>

<!-- spark -->
<dependency>
    <groupId>org.apache.spark</groupId>
    <artifactId>spark-core_2.11</artifactId>
    <version>${spark.version}</version>
</dependency>

<dependency>
    <groupId>org.apache.spark</groupId>
    <artifactId>spark-sql_2.11</artifactId>
    <version>${spark.version}</version>
</dependency>
```

### 2. JavaWordCount

```java
package com.sjf.open.spark;

import org.apache.spark.api.java.JavaPairRDD;
import org.apache.spark.api.java.JavaRDD;
import org.apache.spark.api.java.function.FlatMapFunction;
import org.apache.spark.api.java.function.Function2;
import org.apache.spark.api.java.function.PairFunction;
import org.apache.spark.sql.SparkSession;
import scala.Tuple2;

import java.util.Arrays;
import java.util.Iterator;
import java.util.List;
import java.util.regex.Pattern;

/**
 * Created by xiaosi on 17-2-13.
 *
 * Spark 测试程序 WordCount
 *
 */

public final class JavaWordCount {

    private static final Pattern SPACE = Pattern.compile(" ");

    public static void main(String[] args) throws Exception {

        if (args.length < 1) {
            System.err.println("Usage: JavaWordCount <file>");
            System.exit(1);
        }

        SparkSession spark = SparkSession.builder().appName("JavaWordCount").getOrCreate();

        JavaRDD<String> lines = spark.read().textFile(args[0]).javaRDD();

        JavaRDD<String> words = lines.flatMap(new FlatMapFunction<String, String>() {
            @Override
            public Iterator<String> call(String s) {
                return Arrays.asList(SPACE.split(s)).iterator();
            }
        });

        JavaPairRDD<String, Integer> ones = words.mapToPair(new PairFunction<String, String, Integer>() {
            @Override
            public Tuple2<String, Integer> call(String s) {
                return new Tuple2<String, Integer>(s, 1);
            }
        });

        JavaPairRDD<String, Integer> counts = ones.reduceByKey(new Function2<Integer, Integer, Integer>() {
            @Override
            public Integer call(Integer i1, Integer i2) {
                return i1 + i2;
            }
        });

        List<Tuple2<String, Integer>> output = counts.collect();
        for (Tuple2<?, ?> tuple : output) {
            System.out.println(tuple._1() + ": " + tuple._2());
        }
        spark.stop();
    }
}
```

### 3. 命令行执行
使用Maven 进行打包：
```
mvn clean
mvn package
```
使用上述命令打包后，会在项目根目录下的target目录生成jar包。打完jar包后，我们可以使用spark-submit提交任务：
```
bin/spark-submit --class com.sjf.open.spark.JavaWordCount --master local /home/xiaosi/code/Common-Tool/target/common-tool-jar-with-dependencies.jar /home/xiaosi/a.txt

ee: 1
aa: 3
dd: 2
vvv: 1
ff: 2
bb: 3
cc: 1

```

### 4. Idea本地调试

运行配置

![image](http://img.blog.csdn.net/20170223113917294?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)
