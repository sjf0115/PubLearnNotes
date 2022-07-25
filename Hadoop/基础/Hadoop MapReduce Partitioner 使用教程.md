---
layout: post
author: sjf0115
title: Hadoop MapReduce Partitioner 使用教程
date: 2017-12-05 20:25:17
tags:
  - Hadoop
  - Hadoop 基础

categories: Hadoop
permalink: hadoop-mapreduce-partitioner-usage
---

`partitioner` 在处理输入数据集时就像条件表达式(condition)一样工作。分区阶段发生在`Map`阶段之后，`Reduce`阶段之前。`partitioner`的个数等于`reducer`的个数(The number of partitioners is equal to the number of reducers)。这就意味着一个`partitioner`将根据`reducer`的个数来划分数据(That means a partitioner will divide the data according to the number of reducers)。因此，从一个单独`partitioner`传递过来的数据将会交由一个单独的`reducer`处理(the data passed from a single partitioner is processed by a single Reducer)。

### 1. Partitioner

`partitioner`对Map中间输出结果的键值对进行分区。使用用户自定义的分区条件来对数据进行分区，它的工作方式类似于hash函数。`partitioner`的总个数与作业的`reducer`任务的个数相同。下面我们以一个例子来说明`partitioner`是如何工作的。

### 2. MapReduce的Partitioner实现

为了方便，假设我们有一个Employee表，数据如下。我们使用下面样例数据作为输入数据集来验证`partitioner`是如何工作的。

Id|Name|Age|Gender|Salary
---|---|---|---|---
1201|gopal|45|Male|50,000
1202|manisha|40|Female|50,000
1203|khalil|34|Male|30,000
1204|prasanth|30|Male|30,000
1205|kiran|20|Male|40,000
1206|laxmi|25|Female|35,000
1207|bhavya|20|Female|15,000
1208|reshma|19|Female|15,000
1209|kranthi|22|Male|22,000
1210|Satish|24|Male|25,000
1211|Krishna|25|Male|25,000
1212|Arshad|28|Male|20,000
1213|lavanya|18|Female|8,000

我们写一个程序来处理输入数据集，对年龄进行分组(例如：小于20，21-30，大于30)，并找到每个分组中的最高工资的员工。

#### 2.1 输入数据

以上数据存储在`/home/xiaosi/tmp/partitionerExample/input/`目录中的`input.txt`文件中，数据存储格式如下：
```
1201	gopal	45	Male	50000
1202	manisha	40	Female	51000
1203	khaleel	34	Male	30000
1204	prasanth	30	Male	31000
1205	kiran	20	Male	40000
1206	laxmi	25	Female	35000
1207	bhavya	20	Female	15000
1208	reshma	19	Female	14000
1209	kranthi	22	Male	22000
1210	Satish	24	Male	25000
1211	Krishna	25	Male	26000
1212	Arshad	28	Male	20000
1213	lavanya	18	Female	8000
```
基于以上输入数据，下面是具体的算法描述。

#### 2.2 Map任务

Map任务以键值对作为输入，我们存储文本数据在text文件中。Map任务输入数据如下：

##### 2.2.1 Input

key以`特殊key+文件名+行号`的模式表示(例如，key = @input1)，value为一行中的数据(例如，value = 1201\tgopal\t45\tMale\t50000)。

##### 2.2.2 Method

读取一行中数据，使用split方法以`\t`进行分割，取出性别存储在变量中
```java
String[] str = value.toString().split("\t", -3);
String gender = str[3];
```
以性别为key，行记录数据为value作为输出键值对，从`Map`任务传递到`Partition`任务：
```java
context.write(new Text(gender), new Text(value));
```
对text文件中的所有记录重复以上所有步骤。

##### 2.2.3 Output

得到性别与记录数据组成的键值对

#### 2.3 Partition任务

`Partition`任务接受来自`Map`任务的键值对作为输入。`Partition`意味着将数据分成几个片段。根据给定分区条件规则，基于年龄标准将输入键值对数据划分为三部分。

#### 2.3.1 Input

键值对集合中的所有数据。key为记录中性别字段值，value为该性别对应的完整记录数据。

#### 2.3.2 Method

从键值对数据中读取年龄字段值
```java
String[] str = value.toString().split("\t");
int age = Integer.parseInt(str[2]);
```

根据如下条件校验age值：
```java
// age 小于等于20
if (age <= 20) {
   return 0;
}
// age 大于20 小于等于30
else if (age > 20 && age <= 30) {
   return 1 % numReduceTask;
}
// age 大于30
else {
   return 2 % numReduceTask;
}
```

#### 2.3.3 Output

键值对所有数据被分割成三个键值对集合。`Reducer`会处理每一个集合。

#### 2.4 Reduce任务

`partitioner`任务的数量等于`reducer`任务的数量。这里我们有三个`partitioner`任务，因此我们有三个`reducer`任务要执行。

##### 2.4.1 Input

`Reducer`将使用不同的键值对集合执行三次。key为记录中性别字段值，value为该性别对应的完整记录数据。

##### 2.4.2 Method

读取记录数据中的Salary字段值：
```java
String[] str = value.toString().split("\t", -3);
int salary = Integer.parseInt(str[4]);
```
获取salary最大值:
```java
if (salary > max) {
   max = salary;
}
```
对于每个key集合（Male与Female为两个key集合）中的数据重复以上步骤。执行完这三个步骤之后，我们将会分别从女性集合中得到一个最高工资，从男性集合中得到一个最高工资。
```java
context.write(new Text(key), new IntWritable(max));
```
##### 2.4.3 Output

最后，我们将在不同年龄段的三个集合中获得一组键值对数据。它分别包含每个年龄段的男性集合的最高工资和每个年龄段的女性集合的最高工资。

执行Map，Partition和Reduce任务后，键值对数据的三个集合存储在三个不同的文件中作为输出。

所有这三项任务都被视为MapReduce作业。这些作业的以下要求和规范应在配置中指定：
- 作业名称
- keys和values的输入输出格式
- Map，Reduce和Partitioner任务的类

```java
Configuration conf = getConf();

//Create Job
Job job = new Job(conf, "topsal");
job.setJarByClass(PartitionerExample.class);

// File Input and Output paths
FileInputFormat.setInputPaths(job, new Path(arg[0]));
FileOutputFormat.setOutputPath(job,new Path(arg[1]));

//Set Mapper class and Output format for key-value pair.
job.setMapperClass(MapClass.class);
job.setMapOutputKeyClass(Text.class);
job.setMapOutputValueClass(Text.class);

//set partitioner statement
job.setPartitionerClass(CaderPartitioner.class);

//Set Reducer class and Input/Output format for key-value pair.
job.setReducerClass(ReduceClass.class);

//Number of Reducer tasks.
job.setNumReduceTasks(3);

//Input and Output format for data
job.setInputFormatClass(TextInputFormat.class);
job.setOutputFormatClass(TextOutputFormat.class);
job.setOutputKeyClass(Text.class);
job.setOutputValueClass(Text.class);
```

### 3. Example

```java
package com.sjf.open.test;
import java.io.IOException;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.conf.Configured;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.compress.CompressionCodec;
import org.apache.hadoop.io.compress.GzipCodec;
import org.apache.hadoop.mapred.JobPriority;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Partitioner;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.util.Tool;
import org.apache.hadoop.util.ToolRunner;
import com.sjf.open.utils.FileSystemUtil;
public class PartitionerExample extends Configured implements Tool {

    public static void main(String[] args) throws Exception {
        int status = ToolRunner.run(new PartitionerExample(), args);
        System.exit(status);
    }
    private static class mapper extends Mapper<LongWritable, Text, Text, Text> {
        @Override
        protected void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
            try {
                String[] str = value.toString().split("\t", -3);
                String gender = str[3];
                context.write(new Text(gender), new Text(value));
            } catch (Exception e) {
                System.out.println(e.getMessage());
            }
        }
    }

    private static class reducer extends Reducer<Text, Text, Text, IntWritable> {
        private int max = Integer.MIN_VALUE;
        @Override
        protected void reduce(Text key, Iterable<Text> values, Context context)
                throws IOException, InterruptedException {
            for (Text value : values) {
                String[] str = value.toString().split("\t", -3);
                int salary = Integer.parseInt(str[4]);
                if (salary > max) {
                    max = salary;
                }
            }
            context.write(new Text(key), new IntWritable(max));
        }
    }

    private static class partitioner extends Partitioner<Text, Text> {
        @Override
        public int getPartition(Text key, Text value, int numReduceTask) {
            System.out.println(key.toString() + "------" + value.toString());
            String[] str = value.toString().split("\t");
            int age = Integer.parseInt(str[2]);
            if (numReduceTask == 0) {
                return 0;
            }
            if (age <= 20) {
                return 0;
            }
            else if (age > 20 && age <= 30) {
                return 1 % numReduceTask;
            }
            else {
                return 2 % numReduceTask;
            }
        }
    }
    @Override
    public int run(String[] args) throws Exception {
        if (args.length != 2) {
            System.err.println("./run <input> <output>");
            System.exit(1);
        }
        String inputPath = args[0];
        String outputPath = args[1];
        int numReduceTasks = 3;
        Configuration conf = this.getConf();
        conf.set("mapred.job.queue.name", "test");
        conf.set("mapreduce.map.memory.mb", "1024");
        conf.set("mapreduce.reduce.memory.mb", "1024");
        conf.setBoolean("mapred.output.compress", true);
        conf.setClass("mapred.output.compression.codec", GzipCodec.class, CompressionCodec.class);
        Job job = Job.getInstance(conf);
        job.setJarByClass(PartitionerExample.class);
        job.setPartitionerClass(partitioner.class);
        job.setMapperClass(mapper.class);
        job.setReducerClass(reducer.class);
        job.setMapOutputKeyClass(Text.class);
        job.setMapOutputValueClass(Text.class);
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(IntWritable.class);
        FileSystem fileSystem = FileSystem.get(conf);
        fileSystem.delete(new Path(outputPath), true);
        FileSystemUtil.filterNoExistsFile(conf, job, inputPath);
        FileOutputFormat.setOutputPath(job, new Path(outputPath));
        job.setNumReduceTasks(numReduceTasks);
        boolean success = job.waitForCompletion(true);
        return success ? 0 : 1;
    }
}
```

### 4. 集群上执行

运行结果:
```
17/01/03 20:22:02 INFO mapreduce.Job: Running job: job_1472052053889_7059198
17/01/03 20:22:21 INFO mapreduce.Job: Job job_1472052053889_7059198 running in uber mode : false
17/01/03 20:22:21 INFO mapreduce.Job:  map 0% reduce 0%
17/01/03 20:22:37 INFO mapreduce.Job:  map 100% reduce 0%
17/01/03 20:22:55 INFO mapreduce.Job:  map 100% reduce 100%
17/01/03 20:22:55 INFO mapreduce.Job: Job job_1472052053889_7059198 completed successfully
17/01/03 20:22:56 INFO mapreduce.Job: Counters: 43
        File System Counters
                FILE: Number of bytes read=470
                FILE: Number of bytes written=346003
                FILE: Number of read operations=0
                FILE: Number of large read operations=0
                FILE: Number of write operations=0
                HDFS: Number of bytes read=485
                HDFS: Number of bytes written=109
                HDFS: Number of read operations=12
                HDFS: Number of large read operations=0
                HDFS: Number of write operations=6
        Job Counters
                Launched map tasks=1
                Launched reduce tasks=3
                Rack-local map tasks=1
                Total time spent by all maps in occupied slots (ms)=5559
                Total time spent by all reduces in occupied slots (ms)=164768
        Map-Reduce Framework
                Map input records=13
                Map output records=13
                Map output bytes=426
                Map output materialized bytes=470
                Input split bytes=134
                Combine input records=0
                Combine output records=0
                Reduce input groups=6
                Reduce shuffle bytes=470
                Reduce input records=13
                Reduce output records=6
                Spilled Records=26
                Shuffled Maps =3
                Failed Shuffles=0
                Merged Map outputs=3
                GC time elapsed (ms)=31
                CPU time spent (ms)=2740
                Physical memory (bytes) snapshot=1349193728
                Virtual memory (bytes) snapshot=29673148416
                Total committed heap usage (bytes)=6888620032
        Shuffle Errors
                BAD_ID=0
                CONNECTION=0
                IO_ERROR=0
                WRONG_LENGTH=0
                WRONG_MAP=0
                WRONG_REDUCE=0
        File Input Format Counters
                Bytes Read=351
        File Output Format Counters
                Bytes Written=109

```



```
17/12/06 16:36:15 INFO mapreduce.Job: Counters: 43
        File System Counters
                FILE: Number of bytes read=476
                FILE: Number of bytes written=435296
                FILE: Number of read operations=0
                FILE: Number of large read operations=0
                FILE: Number of write operations=0
                HDFS: Number of bytes read=501
                HDFS: Number of bytes written=129
                HDFS: Number of read operations=15
                HDFS: Number of large read operations=0
                HDFS: Number of write operations=8
        Job Counters
                Launched map tasks=1
                Launched reduce tasks=4
                Rack-local map tasks=1
                Total time spent by all maps in occupied slots (ms)=5965
                Total time spent by all reduces in occupied slots (ms)=229264
        Map-Reduce Framework
                Map input records=13
                Map output records=13
                Map output bytes=426
                Map output materialized bytes=476
                Input split bytes=150
                Combine input records=0
                Combine output records=0
                Reduce input groups=6
                Reduce shuffle bytes=476
                Reduce input records=13
                Reduce output records=6
                Spilled Records=26
                Shuffled Maps =4
                Failed Shuffles=0
                Merged Map outputs=4
                GC time elapsed (ms)=488
                CPU time spent (ms)=6410
                Physical memory (bytes) snapshot=2026946560
                Virtual memory (bytes) snapshot=45281419264
                Total committed heap usage (bytes)=6688342016
        Shuffle Errors
                BAD_ID=0
                CONNECTION=0
                IO_ERROR=0
                WRONG_LENGTH=0
                WRONG_MAP=0
                WRONG_REDUCE=0
        File Input Format Counters
                Bytes Read=351
        File Output Format Counters
                Bytes Written=129
```

原文:https://www.tutorialspoint.com/map_reduce/map_reduce_partitioner.htm
