---
layout: post
author: sjf0115
title: Hadoop 多文件输出 MultipleOutputFormat
date: 2017-03-15 19:01:01
tags:
  - Hadoop
  - Hadoop 基础

categories: Hadoop
permalink: hadoop-base-multiple-output-format
---

FileOutputFormat 及其子类产生的文件放在输出目录下。每个 reducer 一个文件并且文件由分区号命名：part-r-00000，part-r-00001，等等。有时可能要对输出的文件名进行控制或让每个 reducer 输出多个文件。MapReduce 为此提供了 MultipleOutputFormat 类。

MultipleOutputFormat 类可以将数据写到多个文件，这些文件的名称源于输出的键和值或者任意字符串。这允许每个 reducer（或者只有 map 作业的 mapper）创建多个文件。采用 name-r-nnnnn 形式的文件名用于 reduce 输出，其中 name 是由程序设定的任意名字，nnnnn 是一个指名块号的整数（从0开始）。块号保证从不同块（mapper 或者 reducer）写的输出在相同名字情况下不会冲突。

### 1. 重定义输出文件名

我们可以对输出的文件名进行控制。考虑这样一个需求：按男女性别来区分度假订单数据。这需要运行一个作业，作业的输出是男女各一个文件，此文件包含男女性别的所有数据记录。

这个需求可以使用 MultipleOutputs 来实现：

```java
package com.sjf.open.test;
import java.io.IOException;
import org.apache.commons.lang3.StringUtils;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.conf.Configured;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.compress.CompressionCodec;
import org.apache.hadoop.io.compress.GzipCodec;
import org.apache.hadoop.mapred.JobPriority;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.input.FileSplit;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.mapreduce.lib.output.MultipleOutputs;
import org.apache.hadoop.util.Tool;
import org.apache.hadoop.util.ToolRunner;
import com.sjf.open.utils.ConfigUtil;
/**
 * Created by xiaosi on 16-11-7.
 */
public class VacationOrderBySex extends Configured implements Tool {
    public static void main(String[] args) throws Exception {
        int status = ToolRunner.run(new VacationOrderBySex(), args);
        System.exit(status);
    }
    public static class VacationOrderBySexMapper extends Mapper<LongWritable, Text, Text, Text> {
        public String fInputPath = "";
        @Override
        protected void setup(Context context) throws IOException, InterruptedException {
            super.setup(context);
            fInputPath = ((FileSplit) context.getInputSplit()).getPath().toString();
        }
        @Override
        protected void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
            String line = value.toString();
            if(fInputPath.contains("vacation_hot_order")){
                String[] params = line.split("\t");
                String sex = params[2];
                if(StringUtils.isBlank(sex)){
                    return;
                }
                context.write(new Text(sex.toLowerCase()), value);
            }
        }
    }
    public static class VacationOrderBySexReducer extends Reducer<Text, Text, NullWritable, Text> {
        private MultipleOutputs<NullWritable, Text> multipleOutputs;
        @Override
        protected void setup(Context context) throws IOException, InterruptedException {
            multipleOutputs = new MultipleOutputs<NullWritable, Text>(context);
        }
        @Override
        protected void reduce(Text key, Iterable<Text> values, Context context)
                throws IOException, InterruptedException {
            for (Text value : values) {
                multipleOutputs.write(NullWritable.get(), value, key.toString());
            }
        }
        @Override
        protected void cleanup(Context context) throws IOException, InterruptedException {
            multipleOutputs.close();
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
        int numReduceTasks = 16;
        Configuration conf = this.getConf();
        conf.setBoolean("mapred.output.compress", true);
        conf.setClass("mapred.output.compression.codec", GzipCodec.class, CompressionCodec.class);
        Job job = Job.getInstance(conf);
        job.setJobName("vacation_order");
        job.setJarByClass(VacationOrderBySex.class);
        job.setMapperClass(VacationOrderBySexMapper.class);
        job.setReducerClass(VacationOrderBySexReducer.class);
        job.setMapOutputKeyClass(Text.class);
        job.setMapOutputValueClass(Text.class);
        job.setOutputKeyClass(NullWritable.class);
        job.setOutputValueClass(Text.class);
        FileInputFormat.setInputPaths(job, inputPath);
        FileOutputFormat.setOutputPath(job, new Path(outputPath));
        job.setNumReduceTasks(numReduceTasks);
        boolean success = job.waitForCompletion(true);
        return success ? 0 : 1;
    }
}
```
在生成输出的 reduce 中，在 setup() 方法中构造一个 MultipleOutputs 的实例并将它赋予一个实例变量。在 reduce() 方法中使用 MultipleOutputs 实例来写输出，而不是 context。write() 方法作用于键，值和名字。这里使用的是性别作为名字，因此最后产生的输出名称的形式为 sex-r-nnnnn：
```
-rw-r--r--   3 xiaosi xiaosi          0 2016-12-06 10:41 tmp/order_by_sex/_SUCCESS
-rw-r--r--   3 xiaosi xiaosi      88574 2016-12-06 10:41 tmp/order_by_sex/f-r-00005.gz
-rw-r--r--   3 xiaosi xiaosi      60965 2016-12-06 10:41 tmp/order_by_sex/m-r-00012.gz
-rw-r--r--   3 xiaosi xiaosi         20 2016-12-06 10:41 tmp/order_by_sex/part-r-00000.gz
-rw-r--r--   3 xiaosi xiaosi         20 2016-12-06 10:41 tmp/order_by_sex/part-r-00001.gz
-rw-r--r--   3 xiaosi xiaosi         20 2016-12-06 10:41 tmp/order_by_sex/part-r-00002.gz
-rw-r--r--   3 xiaosi xiaosi         20 2016-12-06 10:41 tmp/order_by_sex/part-r-00003.gz
-rw-r--r--   3 xiaosi xiaosi         20 2016-12-06 10:41 tmp/order_by_sex/part-r-00004.gz
-rw-r--r--   3 xiaosi xiaosi         20 2016-12-06 10:41 tmp/order_by_sex/part-r-00005.gz
-rw-r--r--   3 xiaosi xiaosi         20 2016-12-06 10:41 tmp/order_by_sex/part-r-00006.gz
-rw-r--r--   3 xiaosi xiaosi         20 2016-12-06 10:41 tmp/order_by_sex/part-r-00007.gz
-rw-r--r--   3 xiaosi xiaosi         20 2016-12-06 10:41 tmp/order_by_sex/part-r-00008.gz
```
我们可以看到在输出文件中不仅有我们想要的输出文件类型，还有part-r-nnnnn形式的文件，但是文件内没有信息，这是程序默认的输出文件。所以我们在指定输出文件名称时（name-r-nnnnn），不要指定name为part，因为它已经被使用为默认值了。

### 2. 多目录输出

在 MultipleOutputs 的 write() 方法中指定的基本路径相对于输出路径进行解释，因为它可以包含文件路径分隔符（`/`），创建任意深度的子目录。例如，我们改动上面的需求：按男女性别来区分度假订单数据，不同性别数据位于不同子目录（例如：`sex=f/part-r-00000`）。
```java
    public static class VacationOrderBySexReducer extends Reducer<Text, Text, NullWritable, Text> {
        private MultipleOutputs<NullWritable, Text> multipleOutputs;
        @Override
        protected void setup(Context context) throws IOException, InterruptedException {
            multipleOutputs = new MultipleOutputs<NullWritable, Text>(context);
        }
        @Override
        protected void reduce(Text key, Iterable<Text> values, Context context)
                throws IOException, InterruptedException {
            for (Text value : values) {
                String basePath = String.format("sex=%s/part", key.toString());
                multipleOutputs.write(NullWritable.get(), value, basePath);
            }
        }
        @Override
        protected void cleanup(Context context) throws IOException, InterruptedException {
            multipleOutputs.close();
        }
    }
```
后产生的输出名称的形式为 `sex=f/part-r-nnnnn` 或者 `sex=m/part-r-nnnnn`：
```
-rw-r--r--   3 xiaosi xiaosi          0 2016-12-06 12:26 tmp/order_by_sex/_SUCCESS
-rw-r--r--   3 xiaosi xiaosi         20 2016-12-06 12:26 tmp/order_by_sex/part-r-00000.gz
-rw-r--r--   3 xiaosi xiaosi         20 2016-12-06 12:26 tmp/order_by_sex/part-r-00001.gz
-rw-r--r--   3 xiaosi xiaosi         20 2016-12-06 12:26 tmp/order_by_sex/part-r-00002.gz
-rw-r--r--   3 xiaosi xiaosi         20 2016-12-06 12:26 tmp/order_by_sex/part-r-00003.gz
-rw-r--r--   3 xiaosi xiaosi         20 2016-12-06 12:26 tmp/order_by_sex/part-r-00004.gz
-rw-r--r--   3 xiaosi xiaosi         20 2016-12-06 12:26 tmp/order_by_sex/part-r-00005.gz
-rw-r--r--   3 xiaosi xiaosi         20 2016-12-06 12:26 tmp/order_by_sex/part-r-00006.gz
-rw-r--r--   3 xiaosi xiaosi         20 2016-12-06 12:26 tmp/order_by_sex/part-r-00007.gz
drwxr-xr-x   - xiaosi xiaosi          0 2016-12-06 12:26 tmp/order_by_sex/sex=f
drwxr-xr-x   - xiaosi xiaosi          0 2016-12-06 12:26 tmp/order_by_sex/sex=m
```

### 3. 延迟输出

FileOutputFormat 的子类会产生输出文件(part-r-nnnnn)，即使文件是空的，也会产生。我们有时候不想要这些空的文件，我们可以使用 LazyOutputFormat 进行处理。它是一个封装输出格式，可以指定分区第一条记录输出时才真正创建文件。要使用它，使用 JobConf 和相关输出格式作为参数来调用 `setOutputFormatClass()` 方法即可：
```java
Configuration conf = this.getConf();
Job job = Job.getInstance(conf);
LazyOutputFormat.setOutputFormatClass(job, TextOutputFormat.class);
```
再次检查一下我们的输出文件（第一个例子）：
```
sudo -uxiaosi hadoop fs -ls tmp/order_by_sex/
Found 3 items
-rw-r--r--   3 xiaosi xiaosi          0 2016-12-06 13:36 tmp/order_by_sex/_SUCCESS
-rw-r--r--   3 xiaosi xiaosi      88574 2016-12-06 13:36 tmp/order_by_sex/f-r-00005.gz
-rw-r--r--   3 xiaosi xiaosi      60965 2016-12-06 13:36 tmp/order_by_sex/m-r-00012.gz
```
