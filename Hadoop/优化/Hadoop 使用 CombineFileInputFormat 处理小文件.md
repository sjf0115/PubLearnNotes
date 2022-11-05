---
layout: post
author: sjf0115
title: Hadoop 使用 CombineFileInputFormat 处理小文件
date: 2018-08-02 09:32:17
tags:
  - Hadoop
  - Hadoop 优化

categories: Hadoop
permalink: hadoop-use-combinefileinputformat-merge-small-files
---

### 1. 背景需求

在这里我们有广告投放的激活数据一共有 1349 个文件：
```
[smartsi@ying ~]$  sudo -usmartsi hadoop fs -ls adv_push_activate/ | grep ".gz" | wc -l
1349
```
每个文件都只有几 KB 大小，正常写一个 MapReduce 程序，如下输出我们发现一共产生了 1349 个 InputSplit，也就是每个小文件就会产生了一个 InputSplit。文件很小（比HDFS的块要小很多），并且文件数量很多，那么每次 Map 任务只处理很少的输入数据，每次 Map 操作都会造成额外的开销：
```
...
18/08/01 12:40:38 INFO input.FileInputFormat: Total input paths to process : 1349
...
18/08/01 12:40:38 INFO mapreduce.JobSubmitter: number of splits:1349
...
18/08/01 12:40:51 INFO mapreduce.Job:  map 0% reduce 0%
...
18/08/01 12:42:34 INFO mapreduce.Job:  map 100% reduce 100%
18/08/01 12:42:34 INFO mapreduce.Job: Job job_1504162679223_32340234 completed successfully
```
相对于大批量的小文件，Hadoop 更合适处理少量的大文件。一个原因是 `FileInputFormat` 生成的分块是一个文件或该文件的一部分。如果文件很小（小意味着比 HDFS 的块要小很多），并且文件数量很多，那么每次 Map 任务只处理很少的输入数据，（一个文件）就会有很多 Map 任务，每次 Map 操作都会造成额外的开销。比较一下把 1G 的文件分割成 8 个 128MB 与分成 10000 个左右的 100KB 的文件。10000 个文件每个都需要使用一个 Map 任务，作业时间比一个输入文件上用 8 个 Map 任务慢几十倍甚至几百倍。

### 2. CombineFileInputFormat

`CombineFileInputFormat` 可以缓解上述问题，它是针对小文件而设计的。`FileInputFormat` 为每个文件产生一个分片，而 `CombineFileInputFormat` 把多个文件打包到一个分片中以便每个 Map 可以处理更多的数据。决定哪些块放入同一个分片中时， `CombineFileInputFormat` 会考虑到节点和机架的因素，所以在 MapReduce 作业中处理输入的速度并不会下降。

> 当然，如果可能的话，应该尽可能的避免产生许多小文件。因为 MapReduce 处理数据的最佳速度最好与数据在集群中的传输速度相同，而处理小文件将增加运行作业而必需的寻址时间。还有，在 HDFS 集群中存储大量的小文件会浪费 NameNode 的内存。但，如果 HDFS 中已经有大量的小文件，可以试试 `CombineFileInputFormat`。

`CombineFileInputFormat` 不仅可以很好的处理小文件，在处理大文件的时候也有好处。这是因为，它在为每个节点生成一个分片，分片可能由多个块组成。本质上，`CombineFileInputFormat` 使 Map 操作中处理的数据量与 HDFS 中文件的块大小之间的耦合度降低了。

`CombineFileInputFormat` 类继承自 `FileInputFormat`，主要重写了 `List getSplits(JobContext job)` 方法。这个方法会根据数据的分布，`mapreduce.input.fileinputformat.split.minsize.per.node`、`mapreduce.input.fileinputformat.split.minsize.per.rack` 以及 `mapreduce.input.fileinputformat.split.maxsize` 参数的设置来合并小文件，并生成 List。其中 `mapreduce.input.fileinputformat.split.maxsize` 参数至关重要：
- 如果用户没有设置这个参数（默认就是没设置），那么同一个机架上的所有小文件将组成一个 InputSplit，最终由一个 Map Task 来处理；
- 如果用户设置了这个参数，那么同一个节点（node）上的文件将会组成一个 InputSplit。

`CombineFileInputFormat` 是抽象类，如果我们要使用它，需要实现 `createRecordReader` 方法，告诉 MapReduce 程序如何读取组合的 `InputSplit`。内置实现了两种用于解析组合 InputSplit 的类：
- `org.apache.hadoop.mapreduce.lib.input.CombineTextInputFormat`
- `org.apache.hadoop.mapreduce.lib.input.CombineSequenceFileInputFormat`

### 3. Example

```java
package com.sjf.example.mapreduce;

import com.sjf.example.utils.Constant;
import com.sjf.example.utils.HDFSUtil;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.conf.Configured;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.lib.input.CombineTextInputFormat;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.util.Tool;
import org.apache.hadoop.util.ToolRunner;

import java.io.IOException;

/**
 * CombineFileInputFormat处理小文件
 * Created by xiaosi on 16-11-7.
 */
public class CombineInputExample extends Configured implements Tool {

    public static void main(String[] args) throws Exception {
        int status = ToolRunner.run(new CombineInputExample(), args);
        System.exit(status);
    }
    private static class ParserMapper extends Mapper<LongWritable, Text, NullWritable, Text> {
        @Override
        protected void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
            context.write(NullWritable.get(), value);
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
        Configuration conf = this.getConf();
        HDFSUtil.checkAndDel(outputPath, conf);
        conf.set("mapreduce.input.fileinputformat.split.maxsize", String.valueOf(Constant.ONE_MB * 32));
        conf.set("mapreduce.job.queuename", "wirelessdev");
        Job job = Job.getInstance(conf);
        job.setJobName("CombineTextInputFormatExample");
        job.setJarByClass(CombineInputExample.class);
        // map
        job.setInputFormatClass(CombineTextInputFormat.class);
        job.setMapperClass(ParserMapper.class);
        job.setMapOutputKeyClass(NullWritable.class);
        job.setMapOutputValueClass(Text.class);
        // 输入输出路径
        FileInputFormat.addInputPaths(job, inputPath);
        FileOutputFormat.setOutputPath(job, new Path(outputPath));
        boolean success = job.waitForCompletion(true);
        return success ? 0 : 1;
    }
}
```
上面的程序很简单，其实就是将 HDFS 上多个小文件合并到大文件中。运行上述程序，如下输出我们发现 1349 个小文件只产生了 1 个 InputSplit，程序运行时间也会减少：
```
...
18/08/01 12:32:40 INFO input.FileInputFormat: Total input paths to process : 1349
...
18/08/01 12:32:40 INFO input.CombineFileInputFormat: DEBUG: Terminated node allocation with : CompletedNodes: 780, size left: 568937
18/08/01 12:32:40 INFO mapreduce.JobSubmitter: number of splits:1
...
18/08/01 12:32:59 INFO mapreduce.Job:  map 0% reduce 0%
...
18/08/01 12:34:17 INFO mapreduce.Job:  map 100% reduce 100%
18/08/01 12:34:19 INFO mapreduce.Job: Job job_1504162679223_32339255 completed successfully
```

> 注意体会 `mapreduce.input.fileinputformat.split.maxsize` 参数的设置，大家可以不设置这个参数和设置这个参数运行情况对比，观察 Map Task 的个数变化。

参考：[使用CombineFileInputFormat来优化Hadoop小文件](https://www.iteblog.com/archives/2139.html)
