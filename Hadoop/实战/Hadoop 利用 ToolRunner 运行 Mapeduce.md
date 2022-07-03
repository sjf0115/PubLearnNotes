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

大多数人通常使用通过静态 main 方法执行驱动程序代码创建他们的 MapReduce 作业。这种实现的缺点是大多数特定的配置（如果有的话）通常都是硬编码的(例如：设置 Reducer 的个数)。如果需要随时修改一些配置属性（例如：修改 Reducer 数量），就必须修改代码，然后重新构建你的 JAR 文件并重新部署应用程序。这种方式很浪费时间。这可以通过在 MapReduce 驱动程序代码中实现 Tool 接口来避免。

通过实现 Tool 接口并扩展 Configured 类，你可以通过 GenericOptionsParser 轻松的在命令行界面设置 Hadoop 配置对象。这使得你的代码更加具有可移植性（并且更加简洁），因为你不需要再对任何特定配置进行硬编码或者从传入的参数中解析。下面具体看一下使用和不使用 Tool 接口的区别。

## 1. 使用 Tool 接口

为了简化命令行运行作业，Hadoop 自带了一些辅助类。GenericOptionsParser 是一个类，用来解释常用的 Hadoop 命令行选项。一般情况下，不会直接使用 GenericOptionsParser，而是使用更方便的方式：实现 Tool 接口，通过 ToolRunner 来运行应用程序。
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
ToolsRunner 通过其静态 run 方法执行 MapReduce 作业。在这个例子中，我们不需要对 reducer 的个数做额外的处理或者在代码里硬编码，因为可以直接可以在命令行中指定（使用 `-D` 选项）：
```
hadoop jar hadoop-example-1.0.jar com.hadoop.example.base.WordCountV2 -D mapred.reduce.tasks=2 /data/word-count/word-count-input /data/word-count/word-count-output-v2
```
你仍然需要提供输入路径和输出路径两个参数。GenericOptionParser 可以把通用 Tools 选项与实际作业的参数分开。无论你提供多少个通用选项，输入路径和输出路径都会位于下标 0 和 1 处。需要注意的是，是位于 run 方法 String 数组的下标 0 和 1 处，不是在 main 方法 String 数组。

## 2. 不使用 Tool 接口

如果不实现 Tool 接口，对 Mapper 和 Reducer 的实现没有任何影响。核心在于如何解释 Hadoop 命令行选项，没有 GenericOptionsParser 帮助我们解析 Hadoop 命令行选项，只能我们自己实现解析或者在代码里硬编码：
```java
public class WordCountNoTool {
    public static class WordCountMapper extends Mapper<LongWritable, Text, Text, IntWritable> {
        ...
    }
    public static class WordCountReducer extends Reducer<Text, IntWritable, Text, IntWritable> {
        ...
    }
    // 启动 MapReduce 作业
    public boolean run(String[] args) throws Exception {
        // 参数解析
        int reduceTask = 0;
        List<String> other_args = new ArrayList<String>();
        for(int i=0; i < args.length; ++i) {
            try {
                if ("-r".equals(args[i])) {
                    reduceTask = Integer.parseInt(args[++i]);
                } else {
                    other_args.add(args[i]);
                }
            } catch (NumberFormatException except) {
                System.out.println("ERROR: Integer expected instead of " + args[i]);
            } catch (ArrayIndexOutOfBoundsException except) {
                System.out.println("ERROR: Required parameter missing from " + args[i-1]);
            }
        }
        if (other_args.size() != 2) {
            System.err.println("./xxxx [-r reduceTaskNum] <input> <output>");
            System.exit(1);
        }
        String inputPaths = other_args.get(0);
        String outputPath = other_args.get(1);
        // 作业配置
        Configuration conf = new Configuration();
        Job job = Job.getInstance(conf);
        job.setJobName("WordCountNoTool");
        ...
        // 设置 Reduce Task 个数
        if (reduceTask > 0) {
            job.setNumReduceTasks(reduceTask);
        }
        ...
        boolean success = job.waitForCompletion(true);
        return success;
    }

    public static void main(String[] args) throws Exception {
        WordCountNoTool wordCountNoTool = new WordCountNoTool();
        boolean success = wordCountNoTool.run(args);
        System.exit(success ? 0 : 1);
    }
}
```
如果不实现 Tool 接口使用如下命令运行 MapReduce 作业:
```
hadoop jar hadoop-example-1.0.jar com.hadoop.example.base.WordCountNoTool -D mapred.reduce.tasks=2 /data/word-count/word-count-input /data/word-count/word-count-output-v2
```
`-D mapred.reduce.tasks=1` 选项会被 main 方法认为是与输入路径和输出路径一样的参数，位于 run 方法 String 数组的下标 0 处，输入路径和输出路径位于下标 1 和 2 处。

参考:
- [Implementing the Tool interface for MapReduce driver](https://hadoopi.wordpress.com/2013/06/05/hadoop-implementing-the-tool-interface-for-mapreduce-driver/)
