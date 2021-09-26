### 1. Maven依赖

```
<dependency>
    <groupId>org.apache.hadoop</groupId>
    <artifactId>hadoop-client</artifactId>
    <version>2.7.2</version>
</dependency>

<dependency>
    <groupId>junit</groupId>
    <artifactId>junit</artifactId>
    <version>4.12</version>
</dependency>
```
### 2. 调试设置

本地调试需要设置两点：
```
conf.set("fs.default.name", "file:///");
conf.set("mapred.job.tracker", "local");
```
这样MapReduce程序就不会读取HDFS目录上的文件，而是读取本地文件，如果不设置，就会找不到对应的文件而报错：
```
org.apache.hadoop.mapreduce.lib.input.InvalidInputException: Input path does not exist: hdfs://localhost:9000/home/xiaosi/test/input/maxTemperature

	at org.apache.hadoop.mapreduce.lib.input.FileInputFormat.singleThreadedListStatus(FileInputFormat.java:323)
	at org.apache.hadoop.mapreduce.lib.input.FileInputFormat.listStatus(FileInputFormat.java:265)
	at org.apache.hadoop.mapreduce.lib.input.FileInputFormat.getSplits(FileInputFormat.java:387)
	...
	at com.intellij.junit4.JUnit4IdeaTestRunner.startRunnerWithArgs(JUnit4IdeaTestRunner.java:119)
	at com.intellij.junit4.JUnit4IdeaTestRunner.startRunnerWithArgs(JUnit4IdeaTestRunner.java:42)
	at com.intellij.rt.execution.junit.JUnitStarter.prepareStreamsAndStart(JUnitStarter.java:234)
	at com.intellij.rt.execution.junit.JUnitStarter.main(JUnitStarter.java:74)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at com.intellij.rt.execution.application.AppMain.main(AppMain.java:144)
```
### 3. 程序设置

我们在调试代码中对配置文件进行更改，传给MapReduce程序：
```
maxTemperature.setConf(conf);
```
创建Job作业时必须使用如下方式指定我们设置的配置文件，否则读取不到我们更改的设置：
```
Configuration conf = this.getConf();
Job job = Job.getInstance(conf);
```
而不能使用：
```
Job job = Job.getInstance();
```
这样是不会读取我们更改的配置，只是读取默认配置，程序会去HDFS目录上找我们的输入文件而找不到报错．


### 4. 示例

#### 4.1 本地调试代码
```
package com.sjf.open;

import com.sjf.open.maxTemperature.MaxTemperature;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;

import java.io.IOException;

import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.MatcherAssert.assertThat;

import org.junit.Before;
import org.junit.Test;

/**
 * Created by xiaosi on 17-6-8.
 */
public class MapReduceTest {
    private Configuration conf = new Configuration();
    private Path inputPath;
    private Path outputPath;

    private String baseInputStr = "/home/xiaosi/test/input";
    private String outputStr = "/home/xiaosi/test/output";


    @Before
    public void setUp() throws IOException {
        conf.set("fs.default.name", "file:///");
        conf.set("mapred.job.tracker", "local");

        outputPath = new Path(outputStr);

        FileSystem fileSystem = FileSystem.getLocal(conf);
        fileSystem.delete(outputPath, true);
    }

    @Test
    public void MapReduceTest() throws Exception {

        String path = baseInputStr + "/maxTemperature";
        inputPath = new Path(path);
        outputPath = new Path(outputStr);

        MaxTemperature maxTemperature = new MaxTemperature();
        maxTemperature.setConf(conf);

        int exitCode = maxTemperature.run(new String[] {inputPath.toString(), outputPath.toString()});
        assertThat(exitCode, is(0));
    }
}

```

#### 4.2 程序Main代码

```
package com.sjf.open.maxTemperature;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.conf.Configured;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.compress.CompressionCodec;
import org.apache.hadoop.io.compress.GzipCodec;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.util.Tool;
import org.apache.hadoop.util.ToolRunner;

import java.io.IOException;

/**
 * Created by xiaosi on 16-7-27.
 */
public class MaxTemperature extends Configured implements Tool{

    public static void main(String[] args) throws Exception {
        int status = ToolRunner.run(new MaxTemperature(), args);
        System.exit(status);
    }

    @Override
    public int run(String[] args) throws Exception {
        if(args.length != 2){
            System.err.println("Usage: MaxTemperature <input path> <output path>");
            System.exit(-1);
        }

        String inputPath = args[0];
        String outputPath = args[1];

        Configuration conf = this.getConf();
        conf.setBoolean("mapred.output.compress", true);
        conf.setClass("mapred.output.compression.codec", GzipCodec.class, CompressionCodec.class);

        Job job = Job.getInstance(conf);

        job.setJarByClass(MaxTemperature.class);
        job.setMapperClass(MaxTemperatureMapper.class);
        job.setReducerClass(MaxTemperatureReducer.class);

        job.setMapOutputKeyClass(Text.class);
        job.setMapOutputValueClass(IntWritable.class);
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(IntWritable.class);

        FileInputFormat.addInputPath(job, new Path(inputPath));
        FileOutputFormat.setOutputPath(job, new Path(outputPath));

        boolean success = job.waitForCompletion(true);
        return success ? 0 : 1;
    }
}

```