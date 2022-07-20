---
layout: post
author: sjf0115
title: Spark 第一个程序 WordCount
date: 2018-03-11 15:03:01
tags:
  - Spark

categories: Spark
permalink: spark-first-application-word-count
---

### 1 Maven 依赖

```xml
<spark.version>3.1.3</spark.version>

<!-- spark -->
<dependency>
    <groupId>org.apache.spark</groupId>
    <artifactId>spark-core_2.11</artifactId>
    <version>${spark.version}</version>
</dependency>
```

### 2. JavaWordCount

```java
public class WordCount {
    private static final Pattern SPACE = Pattern.compile(" ");

    public static void main(String[] args) throws Exception {

        if (args.length < 1) {
            System.err.println("Usage: JavaWordCount <file>");
            System.exit(1);
        }

        SparkSession spark = SparkSession
                .builder()
                .appName("JavaWordCount")
                .getOrCreate();

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
                return new Tuple2<>(s, 1);
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

使用 Maven 进行打包：
```
mvn clean
mvn package
```
使用上述命令打包后，会在项目根目录下的 target 目录生成 jar 包。打完 jar 包后，我们可以使用 spark-submit 脚本提交任务：
```
bin/spark-submit \
  --class com.spark.example.core.base.WordCount \
  --master local[2] \
  /Users/wy/study/code/data-example/spark-example-3.1/target/spark-example-3.1-1.0.jar \
  /data/word-count/word-count-input
```
上述任务输出如下结果：
```
Flink: 1
a: 1
am: 3
studying: 2
I: 3
student: 1
Hadoop: 1
```

> 对 spark-submit 不熟悉的用户，可以参阅[Spark 应用程序部署工具spark-submit](https://smartsi.blog.csdn.net/article/details/55271395)


### 4. Idea 本地调试

运行配置

![image](http://img.blog.csdn.net/20170223113917294?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)
