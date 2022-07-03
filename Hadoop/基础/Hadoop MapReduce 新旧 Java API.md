从 0.20.0 版本开始，Hadoop 同时提供了新旧两套 MapReduce API。新 API 在旧 API 基础上进行了封装，使得其在扩展性和易用性方面更好。

## 1. 主要区别

新旧版 MapReduce API 的主要区别如下：

### 1.1 存放位置

旧版 API 放在 org.apache.hadoop.mapred 包中，而新版 API 则放在 org.apache.hadoop.mapreduce 包及其子包中。

### 1.2 接口变为抽象类

接口通常作为一种严格的'协议约束'。只有方法声明而没有方法实现，且要求所有实现类（不包括抽象类）必须实现接口中的每一个方法。接口的最大优点是允许一个类实现多个接口，进而实现类似 C++ 中的'多重继承'。

```java
public static class WordCountMapper extends MapReduceBase implements Mapper<LongWritable, Text, Text, IntWritable> {
    ...
}
```
> MapReduceBase 提供了 Mapper 接口的默认实现

抽象类则是一种较宽松的'约束协议'。为某些方法提供默认实现，而继承类可以选择性的是否重新实现哪些方法。正是因为这一点，抽象类在类衍化方面更有优势，也就是说，抽象类具有良好的向后兼容性，当需要为抽象类添加新的方法时，只要新添加的方法提供了默认实现，用户之前的代码就不必修改了。

```java
public static class WordCountMapper extends Mapper<LongWritable, Text, Text, IntWritable> {
    ...
}
```

考虑到抽象类在 API 衍化方面的优势，新 API 将 InputFormat、OutputFormat、Mapper、Reducer 和 Partitioner 由接口变为抽象类。

### 1.3 上下文封装

新版 API 将变量和函数封装成各种上下文（Context）类，使得 API 具有更好的易用性和扩展性。首先，函数参数列表经封装后变短，使得函数更容易使用；其次，当需要修改或添加某些变量或函数时，只需修改封装后的上下文类即可，用户代码无须修改，这样保证了向后兼容性，具有良好的扩展性。

![]()

上图展示了新版 API 中树形的 Context 类继承关系。这些 Context 各自封装了一种实体的基本信息及对应的操作（setter和getter函数），如 JobContext、TaskAttemptContext 分别封装了 Job 和 Task 的基本信息，TaskInputOutputContext 封装了 Task 的各种输入输出操作，MapContext 和 ReduceContext 分别封装了 Mapper 和 Reducer 对外的公共接口。

除了以上三点不同之外，新旧 API 在很多其他细节方面也存在小的差别。

> 由于新版和旧版 API 在类层次结构、编程接口名称及对应的参数列表等方面存在较大差别，所以两种 API 不能兼容。但考虑到应用程序的向后兼容性，短时间内不会将旧 API 从 MapReduce 中去掉。即使在完全采用新 API 的版本中，也仅仅将旧 API 标注为过期（deprecated），用户仍然可以使用。
