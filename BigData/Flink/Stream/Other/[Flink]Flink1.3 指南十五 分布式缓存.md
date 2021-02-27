Flink提供了类似于Apache Hadoop的分布式缓存，可以使用户函数的并行实例访问本地文件(make files locally accessible to parallel instances of user functions)。此功能可用于共享包含静态外部数据的文件(如字典或机器学习回归模型)。

缓存的工作原理如下。程序在`ExecutionEnvironment`中将本地或远程文件系统(如HDFS或S3)的文件或目录以指定的名称注册为缓存文件(A program registers a file or directory of a local or remote filesystem such as HDFS or S3 under a specific name in its ExecutionEnvironment as a cached file)。执行程序时，Flink会自动将文件或目录复制到所有worker节点的本地文件系统上。用户函数(user function)可以从worker节点的本地文件系统上查找指定名称下的文件或目录，并可以访问。

分布式缓存如下使用：

在ExecutionEnvironment中注册文件或目录。

Java版本:
```java
ExecutionEnvironment env = ExecutionEnvironment.getExecutionEnvironment();

// 从HDFS上注册文件
env.registerCachedFile("hdfs:///path/to/your/file", "hdfsFile")

// 注册本地可执行文件 (script, executable, ...)
env.registerCachedFile("file:///path/to/exec/file", "localExecFile", true)

// define your program and execute
...
DataSet<String> input = ...
DataSet<Integer> result = input.map(new MyMapper());
...
env.execute();
```

Scala版本:
```
val env = ExecutionEnvironment.getExecutionEnvironment

// register a file from HDFS
env.registerCachedFile("hdfs:///path/to/your/file", "hdfsFile")

// register a local executable file (script, executable, ...)
env.registerCachedFile("file:///path/to/exec/file", "localExecFile", true)

// define your program and execute
...
val input: DataSet[String] = ...
val result: DataSet[Integer] = input.map(new MyMapper())
...
env.execute()
```

在用户定义的函数中访问缓存文件(这里是MyMapper函数)。该函数必须继承一个`RichFunction`类，因为它需要访问`RuntimeContext`。

Java版本:
```java
// extend a RichFunction to have access to the RuntimeContext
public final class MyMapper extends RichMapFunction<String, Integer> {

    @Override
    public void open(Configuration config) {

      // 通过RuntimeContext and DistributedCache 访问缓存文件
      File myFile = getRuntimeContext().getDistributedCache().getFile("hdfsFile");
      // 读文件挥着遍历目录
      ...
    }

    @Override
    public Integer map(String value) throws Exception {
      // 使用缓存文件中内容
      ...
    }
}
```

Scala版本:
```
// extend a RichFunction to have access to the RuntimeContext
class MyMapper extends RichMapFunction[String, Int] {

  override def open(config: Configuration): Unit = {

    // 通过RuntimeContext and DistributedCache 访问缓存文件
    val myFile: File = getRuntimeContext.getDistributedCache.getFile("hdfsFile")
    // 读文件挥着遍历目录
    ...
  }

  override def map(value: String): Int = {
    // 使用缓存文件中内容
    ...
  }
}
```

我们看一下注册文件的方法`registerCachedFile`:
```java
public void registerCachedFile(String filePath, String name, boolean executable){
		this.cacheFile.add(new Tuple2<>(name, new DistributedCacheEntry(filePath, executable)));
}
```
该方法接受三个参数:
(1) filePath: 文件路径URI (例如，本地文件路径`file:///some/path`，HDFS文件路径`hdfs://host:port/and/path`)
(2) name : 路径下需要注册的文件名称
(3) executable : 表示文件是否可执行的标志



备注:
```
Flink版本:1.3
```

原文:https://ci.apache.org/projects/flink/flink-docs-release-1.3/dev/batch/index.html#distributed-cache
