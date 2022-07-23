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

FileOutputFormat 及其子类产生的文件放在输出目录下。一个 reducer 就会输出一个文件，文件名称的输出格式为 `name-r-nnnnn`，例如 `part-r-00000`：
- name 是由程序设定的任意名字，默认为 part
- nnnnn 是一个指名块号的整数（从0开始）。块号保证从不同块（mapper 或者 reducer）写的输出在相同名字情况下不会冲突。

有时可能要对输出的文件名进行控制或让每个 reducer 输出多个文件。MapReduce 为此提供了 MultipleOutputFormat 类。MultipleOutputFormat 类可以将数据写到多个文件，可以根据输出键和值或者任意字符串来重命名这些文件或者目录。

### 1. 重定义输出文件

我们可以对输出的文件名进行控制。考虑这样一个需求：我们需要按照单词首字母输出来区分 WordCount 程序的输出。这个需求可以使用 MultipleOutputs 来实现：
```java
public class MultipleOutputsExample  extends Configured implements Tool {
    // Mapper
    public static class MultipleOutputsMapper extends Mapper<LongWritable, Text, Text, IntWritable> {
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
    // Reducer
    public static class MultipleOutputsReducer extends Reducer<Text, IntWritable, Text, IntWritable> {
        private MultipleOutputs<Text, IntWritable> multipleOutputs;
        @Override
        protected void setup(Context context) throws IOException, InterruptedException {
            // 初始化 MultipleOutputs
            multipleOutputs = new MultipleOutputs<Text, IntWritable>(context);
        }
        @Override
        protected void reduce(Text key, Iterable<IntWritable> values, Context context) throws IOException, InterruptedException {
            int sum = 0;
            for(IntWritable intWritable : values){
                sum += intWritable.get();
            }
            // key 首字母作为基础输出路径
            String baseOutput = StringUtils.substring(key.toString(), 0, 1);
            // 使用 multipleOutputs
            multipleOutputs.write(key, new IntWritable(sum), StringUtils.lowerCase(baseOutput));
        }
        @Override
        protected void cleanup(Context context) throws IOException, InterruptedException {
            // 关闭 MultipleOutputs
            multipleOutputs.close();
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
        job.setJobName("MultipleOutputsExample");
        job.setJarByClass(MultipleOutputsExample.class);
        // Map 输出 Key 格式
        job.setMapOutputKeyClass(Text.class);
        // Map 输出 Value 格式
        job.setMapOutputValueClass(IntWritable.class);
        // Reduce 输出 Key 格式
        job.setOutputKeyClass(Text.class);
        // Reduce 输出 Value 格式
        job.setOutputValueClass(IntWritable.class);
        // Mapper 类
        job.setMapperClass(MultipleOutputsMapper.class);
        // Reducer 类
        job.setReducerClass(MultipleOutputsReducer.class);
        // 输入路径
        FileInputFormat.setInputPaths(job, inputPaths);
        // 输出路径
        FileOutputFormat.setOutputPath(job, new Path(outputPath));
        boolean success = job.waitForCompletion(true);
        return success ? 0 : 1;
    }
    public static void main(String[] args) throws Exception {
        int result = ToolRunner.run(new Configuration(), new MultipleOutputsExample(), args);
        System.exit(result);
    }
}
```

首先在 setup() 方法中构造一个 MultipleOutputs 的实例。在 reduce() 方法中使用 MultipleOutputs 实例的 `write(KEYOUT key, VALUEOUT value, String baseOutputPath)` 方法代替 context.write() 方法输出。与 context.write 方法输出的最大不同就是提供了一个重写输出路径的参数 baseOutputPath，默认为 part，在这我们使用输出单词的首字母：
```
localhost:target wy$ hadoop fs -ls /data/word-count/word-count-output/
Found 7 items
-rw-r--r--   1 wy supergroup          0 2022-07-23 15:31 /data/word-count/word-count-output/_SUCCESS
-rw-r--r--   1 wy supergroup          9 2022-07-23 15:31 /data/word-count/word-count-output/a-r-00000
-rw-r--r--   1 wy supergroup          8 2022-07-23 15:31 /data/word-count/word-count-output/f-r-00000
-rw-r--r--   1 wy supergroup          9 2022-07-23 15:31 /data/word-count/word-count-output/h-r-00000
-rw-r--r--   1 wy supergroup          4 2022-07-23 15:31 /data/word-count/word-count-output/i-r-00000
-rw-r--r--   1 wy supergroup          0 2022-07-23 15:31 /data/word-count/word-count-output/part-r-00000
-rw-r--r--   1 wy supergroup         21 2022-07-23 15:31 /data/word-count/word-count-output/s-r-00000
```
我们可以看到在输出文件中不仅有我们想要的输出文件类型，还有 `part-r-nnnnn` 形式的文件，但是文件内没有信息，这是程序默认的输出文件。所以我们在指定输出文件名称时，最好不要指定 name 为part，因为它已经被使用为默认值了。

### 2. 多目录输出

在 MultipleOutputs 的 write() 方法中指定的基本路径 baseOutputPath 可以包含文件路径分隔符（`/`），这样就可以创建任意深度的子目录。例如，我们改动上面的需求：按单词的首字母来区分数据，不同首字母的数据位于不同子目录（例如：`a/part-r-00000`）:
```java
protected void reduce(Text key, Iterable<IntWritable> values, Context context) throws IOException, InterruptedException {
    int sum = 0;
    for(IntWritable intWritable : values){
        sum += intWritable.get();
    }
    // key 首字母作为基础输出路径
    String baseOutput = StringUtils.substring(key.toString(), 0, 1);
    // 使用 multipleOutputs
    // String basePath = StringUtils.lowerCase(baseOutput);
    // 只需要修改此处 包含文件分隔符
    String basePath = String.format("%s/part", StringUtils.lowerCase(baseOutput));
    multipleOutputs.write(key, new IntWritable(sum), basePath);
}
```
上述代码文件输出名称的形式为 `{单词首字母}/part-r-nnnnn`：
```
localhost:target wy$ hadoop fs -ls /data/word-count/word-count-output/
Found 7 items
-rw-r--r--   1 wy supergroup          0 2022-07-23 17:42 /data/word-count/word-count-output/_SUCCESS
drwxr-xr-x   - wy supergroup          0 2022-07-23 17:42 /data/word-count/word-count-output/a
drwxr-xr-x   - wy supergroup          0 2022-07-23 17:42 /data/word-count/word-count-output/f
drwxr-xr-x   - wy supergroup          0 2022-07-23 17:42 /data/word-count/word-count-output/h
drwxr-xr-x   - wy supergroup          0 2022-07-23 17:42 /data/word-count/word-count-output/i
-rw-r--r--   1 wy supergroup          0 2022-07-23 17:42 /data/word-count/word-count-output/part-r-00000
drwxr-xr-x   - wy supergroup          0 2022-07-23 17:42 /data/word-count/word-count-output/s
```
