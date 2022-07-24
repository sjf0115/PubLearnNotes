
### 1. InputFormat API 变化

在旧版 API 中，InputFormat 是一个接口，包含两种方法:
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
新版 API 的 InputFormat 与旧版相比，在形式上发生了较大变化，但是仅仅是对之前的一些类进行了封装。通过封装，使接口的易用性和扩展性得以增强：
```java
package org.apache.hadoop.mapreduce;
...
public abstract class InputFormat<K, V> {
    public InputFormat() {
    }
    public abstract List<InputSplit> getSplits(JobContext var1) throws IOException, InterruptedException;
    public abstract RecordReader<K, V> createRecordReader(InputSplit var1, TaskAttemptContext var2) throws IOException, InterruptedException;
}
```
> 详细请参考 [Hadoop MapReduce 新旧 mapred 与 mapreduce API](https://smartsi.blog.csdn.net/article/details/125954508)

## 2. 功能

InputFormat 主要描述了输入数据的格式，并提供如下功能:
- 将输入文件逻辑上拆分为 InputSplits，然后将每个 InputSplit 分配给一个 Mapper(一个 InputSplit 交由一个 MapperTask 处理)
- 为 Mapper 提供输入数据：提供 RecordReader 实现，给定某个 InputSplit，能将起解析为一个个 key/value 对。

### 2.1 getSplits

getSplits 方法主要完成数据切分的功能，将输入数据切分为多个 InputSplit。InputSplit 有一下两个特点:
- 逻辑分片: 它只是在逻辑上对输入数据进行分片，并不会在磁盘上将其切分成分片进行存储。InputSplit 只记录了分片的元数据信息，比如起始位置，长度以及所在的节点列表等。
- 可序列化: 在 Hadoop 中，对象序列化主要有两个作用，分别是进程间通信和永久存储。此处，InputSplit 支持序列化操作主要是为了进程间通信。Client 会调用作业 InputFormat 中的 getSplits 函数，并将得到的 InputSplit 序列化到文件中。

### 2.2 createRecordReader

createRecordReader 方法返回一个 RecordReader 对象，该对象可将输入的 InputSplit 解析成若干个 key/value 键值对。MapReduce 框架在 MapTask 执行过程中，会不断调用 RecordReader 对象中的方法, 迭代获取 key/value 键值对并交给 map() 函数处理。

基于文件的 InputFormat（通常是 FileInputFormat 的子类）的默认行为是根据输入文件的总大小（以字节为单位）将输入拆分为逻辑 InputSplit。但是，输入文件的 FileSystem 块大小被视为 InputSplit 的上限。而下限可以通过 `mapreduce.input.fileinputformat.split.minsize` 配置参数进行修改。基于输入大小的逻辑分割对于许多应用显然是不够的，因为要遵守记录边界。在这种情况下，应用程序还必须实现一个 RecordReader，它负责尊重记录边界，并向单个任务提供逻辑 InputSplit 的面向记录的视图。

### 3. InputFormat 实现

系统自带了各种 InputFormat 实现。为了方便用户编写 MapReduce 程序，Hadoop 自带了一些针对数据库和文件的 InputFormat 实现，具体如下图所示。通常而言，用户需要处理的数据均以文件形式存储到 HDFS 上，所以我们重点针对文件的 InputFormat 实现进行讨论。

![image](http://img.blog.csdn.net/20170929151601227?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

所有基于文件的 InputFormat 实现的基类是 FileInputFormat，并由此派生出针对文本文件格式的 TextInputFormat、KeyValueTextInputFormat 和 NLineInputFormat，针对二进制文件格式的 SequenceFileInputFormat 等。整个基于文件的 InputFormat 体系的设计思路是由公共基类 FileInputFormat 采用统一的方法对各种输入文件进行切分，比如按照某个固定大小等分，而由各个派生 InputFormat 自己提供机制将进一步解析 InputSplit。对应到具体的实现是，基类 FileInputFormat 提供 getSplits 实现，而派生类提供 getRecordReader 实现。
