---
layout: post
author: sjf0115
title: Hadoop 第一个应用程序 WordCount
date: 2021-07-03 11:01:01
tags:
  - Hadoop

categories: Hadoop
permalink: hadoop-word-count
---

## 1. 实现

使用 Java 语言编写 MapReduce 非常方便，因为 Hadoop 的 API 提供了 Mapper 和 Reducer 的抽象类，只需要继承这两个抽象类，然后实现抽象类里面的方法就可以了。

### 1.1 Mapper

首先创建一个 WordCountMapper 类，该类需要继承 `Mapper＜LongWritable, Text, Text, IntWritable＞` 抽象类，并且实现如下方法：
```java
protected void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
}
```
这个方法是 Mapper 抽象类的核心方法，有如下三个参数：
- LongWritable key：每行文件的偏移量。
- Text value：每行文件的内容。
- Context context：Map 端的上下文，与 OutputCollector 和 Reporter 的功能类似。

> 注意 OutputCollector 和 Reporter 是 Hadoop-0.19 以前版本里面的 API，在 Hadoop-0.20.2 以后就换成 Context，Context 的功能包含了 OutputCollector 和 Reporter 的功能，此外还添加了一些别的功能。

具体 WordCountMapper 类代码如下所示：
```java
public static class WordCountMapper extends Mapper<LongWritable, Text, Text, IntWritable> {
    private final static IntWritable one = new IntWritable(1);
    private Text word = new Text();
    @Override
    protected void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
        String line = value.toString();
        StringTokenizer itr = new StringTokenizer(line);
        while (itr.hasMoreTokens()) {
            word.set(itr.nextToken());
            context.write(word, one);
        }
    }
}
```

### 1.2 Reducer

在创建 WordCountMapper 类之后，我们再创建一个 WordCountReducer 类，该类要继承 `Reducer＜Text, IntWritable, Text, IntWritable＞` 抽象类，并且实现如下方法：
```java
protected void reduce(Text key, Iterable<IntWritable> values, Context context) throws IOException, InterruptedException {
}
```
这个方法是 Reducer 抽象类的核心方法，有如下三个参数：
- Text key：Map 端输出的 Key 值。
- Iterable＜IntWritable＞ values：Map 端输出的 Value 集合（相同Key的集合）。
- Context context：Reduce 端的上下文，与 OutputCollector 和 Reporter 的功能类似。

具体 WordCountReducer 类代码如下所示：
```java
public static class WordCountReducer extends Reducer<Text, IntWritable, Text, IntWritable> {
    @Override
    protected void reduce(Text key, Iterable<IntWritable> values, Context context) throws IOException, InterruptedException {
        int sum = 0;
        for(IntWritable intWritable : values){
            sum += intWritable.get();
        }
        context.write(key, new IntWritable(sum));
    }
}
```

### 1.3 ToolRunner

为了简化命令行运行作业，Hadoop 自带了一些辅助类。GenericOptionsParser 是一个类，用来解释常用的 Hadoop 命令行选项。一般情况下，不会直接使用 GenericOptionsParser，而是使用更方便的方式：实现 Tool 接口，通过 ToolRunner 来运行应用程序：
```java
public static void main(String[] args) throws Exception {
    int result = ToolRunner.run(new Configuration(), new WordCountV2(), args);
    System.exit(result);
}
```
并且需要实现 Tool 接口的 run 方法：
```java
public int run(String[] args) throws Exception {
    if (args.length != 2) {
        System.err.println("./xxxx <input> <output>");
        System.exit(1);
    }
    String inputPaths = args[0];
    String outputPath = args[1];

    Configuration conf = this.getConf();
    Job job = Job.getInstance(conf);
    job.setJobName("WordCountV2");
    job.setJarByClass(WordCountV2.class);
    // Map 输出 Key 格式
    job.setMapOutputKeyClass(Text.class);
    // Map 输出 Value 格式
    job.setMapOutputValueClass(IntWritable.class);
    // Reduce 输出 Key 格式
    job.setOutputKeyClass(Text.class);
    // Reduce 输出 Value 格式
    job.setOutputValueClass(IntWritable.class);
    // Mapper 类
    job.setMapperClass(WordCountMapper.class);
    // Combiner 类
    job.setCombinerClass(WordCountReducer.class);
    // Reducer 类
    job.setReducerClass(WordCountReducer.class);
    // 输入路径
    FileInputFormat.setInputPaths(job, inputPaths);
    // 输出路径
    FileOutputFormat.setOutputPath(job, new Path(outputPath));
    boolean success = job.waitForCompletion(true);
    return success ? 0 : 1;
}
```
Configuration 类用来读取 Hadoop 的配置文件，如 site-core.xml、mapred-site.xml、hdfs-site.xml 等。也可以使用 set 方法进行重新设置，如 `conf.set("fs.default.name","hdfs：//xxxxx：9000")`。set 方法设置的值会覆盖配置文件里面配置的值。通过 Job 类来创建一个 MapReduce 任务，可以通过调用不同的方法来设置输入输出格式、输入输出路径等信息。

至此，WordCount 就开发完成了，接下来就是把 WordCount 放在 Hadoop 上运行。

## 2. 运行

假设我们要统计单词个数的内容如下所示：
```
I am a student
I am studying Hadoop
I am studying Flink
```
首先将我们要统计单词个数的内容上传到 HDFS 系统，如下所示：
```
hadoop fs -put word-count-input.txt /data/word-count/word-count-input
```
然后我们的开发的 MapReduce 程序打包成 JAR 文件，使用如下命令运行 WordCount 程序：
```
hadoop jar hadoop-example-1.0.jar com.hadoop.example.base.WordCountV2 /data/word-count/word-count-input /data/word-count/word-count-output-v2
```
> 统计结果输出到 /data/word-count/word-count-output-v2 HDFS 目录下

运行输出如下日志：
```
localhost:target wy$ hadoop jar hadoop-example-1.0.jar com.hadoop.example.base.WordCountV2 /data/word-count/word-count-input /data/word-count/word-count-output-v2
22/07/03 09:40:40 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
22/07/03 09:40:40 INFO client.RMProxy: Connecting to ResourceManager at /0.0.0.0:8032
22/07/03 09:40:41 INFO input.FileInputFormat: Total input paths to process : 1
22/07/03 09:40:41 INFO mapreduce.JobSubmitter: number of splits:1
22/07/03 09:40:41 INFO mapreduce.JobSubmitter: Submitting tokens for job: job_1656752978387_0005
22/07/03 09:40:41 INFO impl.YarnClientImpl: Submitted application application_1656752978387_0005
22/07/03 09:40:41 INFO mapreduce.Job: The url to track the job: http://localhost:8088/proxy/application_1656752978387_0005/
22/07/03 09:40:41 INFO mapreduce.Job: Running job: job_1656752978387_0005
22/07/03 09:40:47 INFO mapreduce.Job: Job job_1656752978387_0005 running in uber mode : false
22/07/03 09:40:47 INFO mapreduce.Job:  map 0% reduce 0%
22/07/03 09:40:51 INFO mapreduce.Job:  map 100% reduce 0%
22/07/03 09:40:56 INFO mapreduce.Job:  map 100% reduce 100%
22/07/03 09:40:56 INFO mapreduce.Job: Job job_1656752978387_0005 completed successfully
22/07/03 09:40:56 INFO mapreduce.Job: Counters: 49
        File System Counters
                FILE: Number of bytes read=85
                FILE: Number of bytes written=247207
                FILE: Number of read operations=0
                FILE: Number of large read operations=0
                FILE: Number of write operations=0
                HDFS: Number of bytes read=175
                HDFS: Number of bytes written=51
                HDFS: Number of read operations=6
                HDFS: Number of large read operations=0
                HDFS: Number of write operations=2
        Job Counters
                Launched map tasks=1
                Launched reduce tasks=1
                Data-local map tasks=1
                Total time spent by all maps in occupied slots (ms)=2169
                Total time spent by all reduces in occupied slots (ms)=2171
                Total time spent by all map tasks (ms)=2169
                Total time spent by all reduce tasks (ms)=2171
                Total vcore-milliseconds taken by all map tasks=2169
                Total vcore-milliseconds taken by all reduce tasks=2171
                Total megabyte-milliseconds taken by all map tasks=2221056
                Total megabyte-milliseconds taken by all reduce tasks=2223104
        Map-Reduce Framework
                Map input records=3
                Map output records=12
                Map output bytes=104
                Map output materialized bytes=85
                Input split bytes=119
                Combine input records=12
                Combine output records=7
                Reduce input groups=7
                Reduce shuffle bytes=85
                Reduce input records=7
                Reduce output records=7
                Spilled Records=14
                Shuffled Maps =1
                Failed Shuffles=0
                Merged Map outputs=1
                GC time elapsed (ms)=98
                CPU time spent (ms)=0
                Physical memory (bytes) snapshot=0
                Virtual memory (bytes) snapshot=0
                Total committed heap usage (bytes)=328204288
        Shuffle Errors
                BAD_ID=0
                CONNECTION=0
                IO_ERROR=0
                WRONG_LENGTH=0
                WRONG_MAP=0
                WRONG_REDUCE=0
        File Input Format Counters
                Bytes Read=56
        File Output Format Counters
                Bytes Written=51

```
现在我们通过 HDFS 命令查看统计的最终结果：
```
localhost:data wy$ hadoop fs -cat  hdfs://localhost:9000/data/word-count/word-count-output-v2/*
Flink	1
Hadoop	1
I	3
a	1
am	3
student	1
studying	2
```

完整代码示例：
```java
public class WordCountV2 extends Configured implements Tool {
    public static class WordCountMapper extends Mapper<LongWritable, Text, Text, IntWritable> {
        private final static IntWritable one = new IntWritable(1);
        private Text word = new Text();
        @Override
        protected void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
            String line = value.toString();
            StringTokenizer itr = new StringTokenizer(line);
            while (itr.hasMoreTokens()) {
                word.set(itr.nextToken());
                context.write(word, one);
            }
        }
    }
    public static class WordCountReducer extends Reducer<Text, IntWritable, Text, IntWritable> {
        @Override
        protected void reduce(Text key, Iterable<IntWritable> values, Context context) throws IOException, InterruptedException {
            int sum = 0;
            for(IntWritable intWritable : values){
                sum += intWritable.get();
            }
            context.write(key, new IntWritable(sum));
        }
    }
    public int run(String[] args) throws Exception {
        if (args.length != 2) {
            System.err.println("./xxxx <input> <output>");
            System.exit(1);
        }
        String inputPaths = args[0];
        String outputPath = args[1];

        Configuration conf = this.getConf();
        Job job = Job.getInstance(conf);
        job.setJobName("WordCountV2");
        job.setJarByClass(WordCountV2.class);
        // Map 输出 Key 格式
        job.setMapOutputKeyClass(Text.class);
        // Map 输出 Value 格式
        job.setMapOutputValueClass(IntWritable.class);
        // Reduce 输出 Key 格式
        job.setOutputKeyClass(Text.class);
        // Reduce 输出 Value 格式
        job.setOutputValueClass(IntWritable.class);
        // Mapper 类
        job.setMapperClass(WordCountMapper.class);
        // Combiner 类
        job.setCombinerClass(WordCountReducer.class);
        // Reducer 类
        job.setReducerClass(WordCountReducer.class);
        // 输入路径
        FileInputFormat.setInputPaths(job, inputPaths);
        // 输出路径
        FileOutputFormat.setOutputPath(job, new Path(outputPath));
        boolean success = job.waitForCompletion(true);
        return success ? 0 : 1;
    }
    public static void main(String[] args) throws Exception {
        int result = ToolRunner.run(new Configuration(), new WordCountV2(), args);
        System.exit(result);
    }
}
```
> Github地址：[WordCountV2](https://github.com/sjf0115/data-example/blob/master/hadoop-example/src/main/java/com/hadoop/example/base/WordCountV2.java)
