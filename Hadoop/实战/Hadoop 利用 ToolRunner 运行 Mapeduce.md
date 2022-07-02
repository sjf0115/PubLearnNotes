---
layout: post
author: sjf0115
title: Hadoop 利用 ToolRunner 运行 MapReduce
date: 2018-06-01 17:01:01
tags:
  - Hadoop
  - Hadoop 基础

categories: Hadoop
permalink: hadoop-base-implementing-the-tool-interface-for-mapreduce
---

大多数人通常使用通过静态 main 方法执行驱动程序代码创建他们的 MapReduce 作业。这种实现的缺点是大多数特定的配置（如果有的话）通常都是硬编码的(例如：设置 Reducer 的个数)。如果需要随时修改一些配置属性（例如：修改 Reducer 数量），就必须修改代码，然后重新构建你的 jar 文件并重新部署应用程序。这种方式很浪费时间。这可以通过在 MapReduce 驱动程序代码中实现 Tool 接口来避免。

### 1. Hadoop 配置

通过实现 Tool 接口并扩展 Configured 类，你可以通过 GenericOptionsParser 轻松的在命令行界面设置 Hadoop 配置对象。这使得你的代码更加具有可移植性（并且更加简洁），因为你不需要再对任何特定配置进行硬编码。让我们举几个例子，使用和不使用Tool接口。

#### 1.1 不使用 Tool 接口

```java
package com.sjf.open.example;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.conf.Configured;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.util.Tool;
import org.apache.hadoop.util.ToolRunner;

import java.io.IOException;


/**
 * WordCount示例
 * @author sjf0115
 * @Date Created in 上午10:01 18-6-1
 */
public class WordCountNoTool{

    public int run(String[] args) throws Exception {
        if (args.length != 2) {
            System.err.println("./xxxx <input> <output> but got " + args.length + ":");
            for(String argument : args){
                System.out.println("Output: " + argument);
            }
            System.exit(1);
        }
        String inputPaths = args[0];
        String outputPath = args[1];

        Configuration conf = new Configuration();
        conf.set("mapred.job.queue.name", "xxx");

        Job job = Job.getInstance(conf);
        job.setJobName("word_count_example");
        job.setJarByClass(WordCountNoTool.class);

        // mapper
        job.setMapperClass(mapper.class);

        // reducer
        job.setReducerClass(reducer.class);
        job.setNumReduceTasks(2);

        // input
        FileInputFormat.setInputPaths(job, inputPaths);
        job.setMapOutputKeyClass(Text.class);
        job.setMapOutputValueClass(IntWritable.class);

        // output
        FileOutputFormat.setOutputPath(job, new Path(outputPath));
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(IntWritable.class);

        boolean success = job.waitForCompletion(true);
        return success ? 0 : 1;
    }

    public static class mapper extends Mapper<LongWritable, Text, Text, IntWritable> {
        @Override
        protected void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
            String line = value.toString();
            String[] words = line.split("\\s+");
            Text text = new Text();
            IntWritable intWritable = new IntWritable();
            for(String word : words){
                text.set(word);
                intWritable.set(1);
                // <word, 1>
                context.write(text, intWritable);
            }
        }
    }

    public static class reducer extends Reducer<Text, IntWritable, Text, IntWritable> {
        @Override
        protected void reduce(Text key, Iterable<IntWritable> values, Context context) throws IOException, InterruptedException {
            int count = 0;
            for(IntWritable intWritable : values){
                count += intWritable.get();
            }
            context.write(key, new IntWritable(count));
        }
    }

    public static void main(String[] args) throws Exception {
        WordCountNoTool wordCountNoTool = new WordCountNoTool();
        int result = wordCountNoTool.run(args);
        System.exit(result);
    }
}
```
如下方式执行 MapReduce 作业。你期望在这里只有2个参数 inputPath 和 outputPath，可以通过 main 方法 String 数组上的索引 [0] 和 [1] 获取：
```
hadoop jar common-tool-jar-with-dependencies.jar com.sjf.open.example.WordCountNoTool ${inputPath} ${outputPath}
```
在这种情况下，reducer 的个数硬编码在代码中（`job.setNumReduceTasks(2)`），因此无法根据需要进行修改。

#### 1.2 使用 Tool 接口

```java
package com.sjf.open.example;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.conf.Configured;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.util.Tool;
import org.apache.hadoop.util.ToolRunner;

import java.io.IOException;


/**
 * WordCount示例
 * @author sjf0115
 * @Date Created in 上午10:01 18-6-1
 */
public class WordCountWithTool extends Configured implements Tool {
    @Override
    public int run(String[] args) throws Exception {
        if (args.length != 2) {
            System.err.println("./xxxx <input> <output>");
            System.exit(1);
        }
        String inputPaths = args[0];
        String outputPath = args[1];

        Configuration conf = this.getConf();
        conf.set("mapred.job.queue.name", "xxxx");

        Job job = Job.getInstance(conf);
        job.setJobName("word_count_example");
        job.setJarByClass(WordCountWithTool.class);

        // mapper
        job.setMapperClass(mapper.class);

        // reducer
        job.setReducerClass(reducer.class);

        // input
        FileInputFormat.setInputPaths(job, inputPaths);
        job.setMapOutputKeyClass(Text.class);
        job.setMapOutputValueClass(IntWritable.class);

        // output
        FileOutputFormat.setOutputPath(job, new Path(outputPath));
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(IntWritable.class);

        boolean success = job.waitForCompletion(true);
        return success ? 0 : 1;
    }

    public static class mapper extends Mapper<LongWritable, Text, Text, IntWritable> {
        @Override
        protected void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
            String line = value.toString();
            String[] words = line.split("\\s+");
            Text text = new Text();
            IntWritable intWritable = new IntWritable();
            for(String word : words){
                text.set(word);
                intWritable.set(1);
                // <word, 1>
                context.write(text, intWritable);
            }
        }
    }

    public static class reducer extends Reducer<Text, IntWritable, Text, IntWritable> {
        @Override
        protected void reduce(Text key, Iterable<IntWritable> values, Context context) throws IOException, InterruptedException {
            int count = 0;
            for(IntWritable intWritable : values){
                count += intWritable.get();
            }
            context.write(key, new IntWritable(count));
        }
    }

    public static void main(String[] args) throws Exception {
        int result = ToolRunner.run(new Configuration(), new WordCountWithTool(), args);
        System.exit(result);
    }
}
```
ToolsRunner 通过其静态 run 方法执行 MapReduce 作业。在这个例子中，我们不需要对 reducer 的个数进行硬编码，因为它可以直接可以在命令行中指定（使用`-D`选项）：
```
hadoop jar common-tool-jar-with-dependencies.jar com.sjf.open.example.WordCountWithTool -D mapred.reduce.tasks=1 ${inputPath} ${outputPath}
```
请注意，你仍然需要提供 inputPath 和 outputPath 两个参数。GenericOptionParser 可以把通用 Tools 选项与实际作业的参数分开。无论你提供多少个通用选项，inputPath 和 outputPath 变量仍位于索引[0]和[1]处，但位于 run 方法String数组中（不是在 main 方法String数组中）。

> 如果不实现 Tool 接口运行 MapReduce 作业:
```
hadoop jar common-tool-jar-with-dependencies.jar com.sjf.open.example.WordCountNoTool -D mapred.reduce.tasks=1 ${inputPath} ${outputPath}
```
> `-D mapred.reduce.tasks=1` 也会被 main 方法认为是一个参数，位于索引[0]处，inputPath 和 outputPath 则分别位于索引[1]和[2]处。

### 2. 支持通用选项

可以从CLI提供一些其他有用的选项。
```
-conf 指定应用程序配置文件
-D 给指定属性设置值
-fs 指定 namenode
-files 指定复制到集群上的文件，以逗号分隔
-libjars 指定包含在类路径中的jar文件，以逗号分隔
```



参考:
- [Implementing the Tool interface for MapReduce driver](https://hadoopi.wordpress.com/2013/06/05/hadoop-implementing-the-tool-interface-for-mapreduce-driver/)
