InputFormat主要描述了输入数据的格式，并提供一下功能:
- 校验作业的输入是否符合规范（或者格式）
- 将输入文件逻辑上拆分为 InputSplits，然后将每个 InputSplit 分配给一个Mapper(一个InputSplit交由一个MapperTask处理)
- 为Mapper提供输入数据:提供RecordReader的实现，给定某个InputSplit，能将起解析为一个个key/value对。

### 1. 旧版 API InputFormat

在旧版API中，InputFormat是一个接口，它包含两种方法:
```java
package org.apache.hadoop.mapred;
...
@InterfaceAudience.Public
@InterfaceStability.Stable
public interface InputFormat<K, V> {
  InputSplit[] getSplits(JobConf job, int numSplits) throws IOException;
  RecordReader<K, V> getRecordReader(InputSplit split, JobConf job, Reporter reporter) throws IOException;
}
```

(1) getSplits方法主要完成数据切分的功能，将输入数据切分为多个InputSplit。InputSplit有一下两个特点:
- 逻辑分片: 它只是在逻辑上对输入数据进行分片，并不会在磁盘上将其切分成分片进行存储。InputSplit只记录了分片的元数据信息，比如起始位置，长度以及所在的节点列表等。
- 可序列化: 在Hadoop中，对象序列化主要有两个作用:进程间通信和永久存储。此处，InputSplit支持序列化操作主要是为了进程间通信。作业被提交到JobTracker之前，Client会调用作业InputFormat中的getSplits函数，并将得到的InputSplit序列化到文件中。

(2) createRecordReader方法返回一个RecordReader对象,该对象可将输入的InputSplit解析成若干个key/value对。MapReduce框架在MapTask执行过程中, 会不断调用RecordReader对象中的方法, 迭代获取key/value对并交给map()函数处理。

基于文件的InputFormat（通常是FileInputFormat的子类）的默认行为是根据输入文件的总大小（以字节为单位）将输入拆分为逻辑InputSplit。 但是，输入文件的 FileSystem 块大小被视为 InputSplit 的上限。而下限可以通过 **mapreduce.input.fileinputformat.split.minsize** 配置参数进行修改。基于输入大小的逻辑分割对于许多应用显然是不够的，因为要遵守记录边界。 在这种情况下，应用程序还必须实现一个RecordReader，它负责尊重记录边界，并向单个任务提供逻辑InputSplit的面向记录的视图。


### 2. 新版 API InputFormat

新版的API的InputFormat与旧版相比较，在形式上发生了较大变化，但是仅仅是对之前的一些类进行了封装。通过封装，使接口的易用性和扩展性得以增强。

```java
package org.apache.hadoop.mapreduce;
...
public abstract class InputFormat<K, V> {
  public abstract List<InputSplit> getSplits(JobContext context) throws IOException,InterruptedException;  
  public abstract RecordReader<K,V> createRecordReader(InputSplit split,TaskAttemptContext context) throws IOException,  InterruptedException;  
}  
```

### 3. InputFormat实现

系统自带了各种InputFormat实现 。为了方便用户编写 MapReduce 程序 , Hadoop 自带了一些针对数据库和文件的 InputFormat实现 , 具体如下图所示。 通常而言,用户需要处理的数据均以文件形式存储到HDFS上, 所以我们重点针对文件的InputFormat实现进行讨论 。

![image](http://img.blog.csdn.net/20170929151601227?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

所有基于文件的 InputFormat 实现的基类是 **FileInputFormat**, 并由此派生出针对文本文件格式的 **TextInputFormat** 、 **KeyValueTextInputFormat** 和 **NLineInputFormat** ,
针对二进制文件格式的 **SequenceFileInputFormat** 等 。整个基于文件的InputFormat体系的设计思路是由公共基类FileInputFormat采用统一的方法对各种输入文件进行切分，比如按照某个固定大小等分, 而由各个派生InputFormat自己提供机制将进一步解析InputSplit。对应到具体的实现是，基类FileInputFormat提供getSplits实现，而派生类提供getRecordReader实现。
