Flink程序可以分布在许多机器的群集上。有两种方式可以将程序发送到集群上运行：
(1) 命令行接口
(2) 远程环境

### 1. 命令行接口

命令行接口允许你将打包程序(JAR)提交到集群(或单机配置)。

详细请参阅[[Flink]Flink1.3 指南四 命令行接口](http://blog.csdn.net/sunnyyoona/article/details/78316406)。

### 2. 远程环境

远程环境允许你直接在集群上运行Flink Java程序。远程环境指的是你要在上面运行程序的集群。

#### 2.1 Maven依赖

使用下面依赖关系添加`flink-clients`模块：
```
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-clients_2.10</artifactId>
  <version>1.3.2</version>
</dependency>
```
#### 2.2 Example

下面说明了如何使用RemoteEnvironment：
```Java
public static void main(String[] args) throws Exception {
    ExecutionEnvironment env = ExecutionEnvironment.createRemoteEnvironment("flink-master", 6123, "/home/user/udfs.jar");

    DataSet<String> data = env.readTextFile("hdfs://path/to/file");

    data.filter(new FilterFunction<String>() {
            public boolean filter(String value) {
                return value.startsWith("http://");
            }
        })
        .writeAsText("hdfs://path/to/result");

    env.execute();
}
```
备注:
```
该程序包含了用户自定义代码，因此需要一个包含代码类的JAR文件。远程环境的构造函数需要指定路径来指向JAR文件。
```


备注:
```
Flink版本:1.3
```

原文:https://ci.apache.org/projects/flink/flink-docs-release-1.3/dev/cluster_execution.html
