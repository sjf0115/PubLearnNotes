从 Hadoop 0.20.0 版本开始，Hadoop 同时提供了新旧两套 MapReduce API。新 API 在旧 API 基础上进行了封装，使得其在扩展性和易用性方面更好。这篇文章是对新旧 API 的主要变更的简要总结。

## 1. 变化

### 1.1 Mapper 和 Reducer 变化

在 Hadoop 0.20.x 之前，一个 Map 类必须扩展一个 MapReduceBase 并像如下实现一个 Mapper：
```java
public static class WordCountMapper extends MapReduceBase implements Mapper<LongWritable, Text, Text, IntWritable> {
    ...
}
```
> MapReduceBase 为 Mapper 和 Reducer 接口的一些方法提供默认的无操作实现。接口要求必须实现接口中的每一个方法，MapReduceBase 为其提供一些默认实现

同样，map 函数必须使用 OutputCollector 和 Reporter 对象来输出 (key,value) 键值对并将进度更新发送到主程序。一个典型的 map 函数如下所示：
```java
public void map(LongWritable key, Text value, OutputCollector<Text, IntWritable> output, Reporter reporter) throws IOException {
    output.collect(key, value);
}
```
使用新版本 API，mapper 或 reducer 必须从包 `org.apache.hadoop.mapreduce.*` 扩展类，并且不再需要实现接口。在新版本 API 中像如下方式来来定义 Map 类：
```java
public static class WordCountMapper extends Mapper<LongWritable, Text, Text, IntWritable> {
    ...
}
```
map 函数使用 Context 对象来输出记录并发送进度更新。一个典型的 map 函数如下所示：
```java
protected void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
    context.write(key, value);
}
```
上述所讲的都是 Mapper 的一些更改，发生在 Reducer 上变更也是类似的，在此不再赘述。

### 1.2 作业配置与提交变化

作业配置与提交的方式也发生一些重大变化。之前，map、reduce 作业通过 JobConf 对象配置，并由 JobClient 的实例来完成作业的提交。驱动程序类的主体过看起来如下所示：
```java
JobConf conf = new JobConf(new Configuration(), WordCountV1.class);
conf.setJobName("WordCountV1");
conf.setMapperClass(WordCountMapper.class);
conf.setReducerClass(WordCountReducer.class);
JobClient.runJob(conf);
```
在新版本 API 中，同样的功能实现如下所示：
```java
Configuration conf = this.getConf();
Job job = Job.getInstance(conf);
job.setJobName("WordCountV2");
job.setJarByClass(WordCountV2.class);
job.setMapperClass(WordCountMapper.class);
job.setReducerClass(WordCountReducer.class);
System.exit(job.waitForCompletion(true) ? 0 : 1);
```
从以上新旧版本 API 可以看出，新版本 API 用 Job 类代替了 JobConf 和 JobClient 两个类，这样仅使用一个类就可以完成作业配置和作业提交相关功能，进一步简化了作业编写方式。

## 2. 总结

通过上述新旧版 MapReduce API 的变化，我们可以总结出如下几方面的区别。

### 2.1 存放位置

旧版本 API 放在 `org.apache.hadoop.mapred` 包中，而新版本 API 则放在 `org.apache.hadoop.mapreduce` 包及其子包中。

### 2.2 接口变为抽象类

接口通常作为一种严格的'协议约束'。只有方法声明而没有方法实现。接口的最大优点是可以允许一个类实现多个接口，进而实现类似 C++ 中的'多重继承'。但是接口要求所有实现类（不包括抽象类）必须实现接口中的每一个方法，这在 API 衍化方面有一定的阻碍，为此 API 中提供了一个 MapReduceBase 基类，为 Mapper 和 Reducer 接口的一些方法提供默认的无操作实现。这样就可以只实现必要的方法即可。

抽象类则是一种较宽松的'约束协议'。为某些方法提供默认实现，而继承类可以选择性的是否重新实现哪些方法。正是因为这一点，抽象类在类衍化方面更有优势，也就是说，抽象类具有良好的向后兼容性，当需要为抽象类添加新的方法时，只要新添加的方法提供了默认实现，用户之前的代码就不必修改了。

考虑到抽象类在 API 衍化方面的优势，新 API 将 InputFormat、OutputFormat、Mapper、Reducer 和 Partitioner 由接口变为抽象类。

### 2.3 上下文封装

新版 API 将变量和函数封装成各种上下文（Context）类，使得 API 具有更好的易用性和扩展性。首先，函数参数列表经封装后变短，使得函数更容易使用；其次，当需要修改或添加某些变量或函数时，只需修改封装后的上下文类即可，用户代码无须修改，这样保证了向后兼容性，具有良好的扩展性。

除了以上三点不同之外，新旧 API 在很多其他细节方面也存在小的差别。

> 由于新版和旧版 API 在类层次结构、编程接口名称及对应的参数列表等方面存在较大差别，所以两种 API 不能兼容。但考虑到应用程序的向后兼容性，短时间内不会将旧 API 从 MapReduce 中去掉。即使在完全采用新 API 的版本中，也仅仅将旧 API 标注为过期（deprecated），用户仍然可以使用。

> [旧版本 API WordCount 实现](https://github.com/sjf0115/data-example/blob/master/hadoop-example/src/main/java/com/hadoop/example/base/WordCountV1.java)
> [新版本 API WordCount 实现](https://github.com/sjf0115/data-example/blob/master/hadoop-example/src/main/java/com/hadoop/example/base/WordCountV2.java)
