Flink可以在单台机器上运行，甚至可以在单个Java虚拟机中运行。 这运行机制可以方便用户在本地测试和调试Flink程序。本节概述了Flink的本地执行机制。

本地环境和执行器(executors)允许你可以在本地Java虚拟机上运行Flink程序，或者是在正在运行程序的Java虚拟机上(with within any JVM as part of existing programs)。对于大部分示例程序而言，你只需简单的地点击你IDE上的运行(Run)按钮就可以执行。

Flink支持两种不同的本地运行机制:
(1) `LocalExecutionEnvironment`启动完整的Flink运行环境，包括一个`JobManager`和一个`TaskManager`。这些包含了内存管理以及在集群模式下运行时所运行的所有内部算法。
(2) `CollectionEnvironment`在Java集合上运行Flink程序(executing the Flink program on Java collections)。这种模式不会启动完整的Flink运行环境，因此运行开销比较低以及轻量级。例如，DataSet的map转换操作将map()函数应用于Java列表中的所有元素上。

### 1. 调试

如果你在本地运行Flink程序，还可以像任何其他Java程序一样来调试程序。你可以使用`System.out.println()`来打印一些内部变量，也可以使用调试器。可以在map()，reduce()以及所有其他方法中设置断点。请参阅Java API文档中的[调试部分](https://ci.apache.org/projects/flink/flink-docs-release-1.3/dev/batch/index.html#debugging)，来了解如何使用Java API来测试和本地调试程序。

### 2. Maven

如果你在Maven项目中开发程序，则必须使用下面依赖关系添加`flink-clients`模块：
```
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-clients_2.10</artifactId>
  <version>1.3.2</version>
</dependency>
```

### 3. 本地运行环境

`LocalEnvironment`是本地运行Flink程序的句柄，可以使用它在本地的JVM，独立运行或嵌入其他程序里运行。

本地运行执行环境通过`ExecutionEnvironment.createLocalEnvironment()`方法实例化。默认情况下，Flink将尽可能使用跟你机器CPU核数一样多的本地线程来执行程序。你可以指定程序你想要的并行度。本地运行环境可以通过`enableLogging()/disableLogging()`来配置日志的输出。

在大多数情况下，`ExecutionEnvironment.getExecutionEnvironment()`是一种更好的选择。当程序在本地启动时(不使用命令行接口)，该方法返回`LocalEnvironment`，当程序是通过命令行接口提交时，则该方法会返回为在集群中运行提前配置好的运行环境(pre-configured environment for cluster execution)。

```java
public static void main(String[] args) throws Exception {
    ExecutionEnvironment env = ExecutionEnvironment.createLocalEnvironment();

    DataSet<String> data = env.readTextFile("file:///home/xiaosi/a.txt");

    data.filter(new FilterFunction<String>() {
            public boolean filter(String value) {
                return value.startsWith("http://");
            }
        })
        .writeAsText("file:///home/xiaosi/output");

    JobExecutionResult res = env.execute();
}
```
在程序执行结束时会返回`JobExecutionResult`对象，这个类中包含了程序的运行状态(runtime)和累加器(accumulator)结果。

`LocalEnvironment`也可以向Flink传入用户自定义配置。

```java
Configuration conf = new Configuration();
conf.setFloat(ConfigConstants.TASK_MANAGER_MEMORY_FRACTION_KEY, 0.5f);
final ExecutionEnvironment env = ExecutionEnvironment.createLocalEnvironment(conf);
```

备注:
```
本地运行环境不启动任何Web前端来监控运行。
```

### 4. 集合运行环境

使用`CollectionEnvironment`在Java集合上运行，对于运行Flink程序是一种开销比较低的方法。在这种模式中通常用于自动化测试、调试、代码重用等场景。

用户可以使用用于批处理的算法，或者是用于更具交互性的算法(Users can use algorithms implemented for batch processing also for cases that are more interactive)。Flink程序通过稍微修改就可用于处理请求的Java应用服务器。

下面是集合环境的例子：

```java
public static void main(String[] args) throws Exception {
    // initialize a new Collection-based execution environment
    final ExecutionEnvironment env = new CollectionEnvironment();

    DataSet<User> users = env.fromCollection( /* get elements from a Java Collection */);

    /* Data Set transformations ... */

    // retrieve the resulting Tuple2 elements into a ArrayList.
    Collection<...> result = new ArrayList<...>();
    resultDataSet.output(new LocalCollectionOutputFormat<...>(result));

    // kick off execution.
    env.execute();

    // Do some work with the resulting ArrayList (=Collection).
    for(... t : result) {
        System.err.println("Result = "+t);
    }
}
```
`flink-examples-batch`模块包含一个完整的示例，名称为`CollectionExecutionExample`。

备注:
```
基于集合的Flink程序仅适用于小数据量，这样可以完全放进JVM堆中。在集合上的运行不是多线程的，只使用一个线程。
```

备注:
```
Flink版本为1.3
```

原文:https://ci.apache.org/projects/flink/flink-docs-release-1.3/dev/local_execution.html
