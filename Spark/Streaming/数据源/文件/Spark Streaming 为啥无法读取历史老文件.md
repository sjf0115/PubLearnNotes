在 [Spark Streaming Connector 从文件读取数据](https://smartsi.blog.csdn.net/article/details/144489186) 文章中我们介绍了如何使用 Spark Streaming 从 HDFS 中读取文件。

## 1. 为什么读取不到历史老文件

但是我们发现使用 `textFileStream` 方法只能读取到新添加的文件，无法读取程序启动之前就存在的历史老文件：
```java
SparkConf conf = new SparkConf().setAppName("text-file-stream").setMaster("local[2]");
JavaSparkContext sparkContext = new JavaSparkContext(conf);
JavaStreamingContext ssc = new JavaStreamingContext(sparkContext, Durations.seconds(10));

String path = "hdfs://localhost:9000/user/hive/warehouse/tag_user";
JavaDStream<String> dStream = ssc.textFileStream(path);
dStream.print();
```
开启 Debug 日志可以看到历史文件都被过滤了：
```java
24/12/21 15:38:50 DEBUG FileInputDStream: Getting new files for time 1734766730000, ignoring files older than 1734766728620
...
24/12/21 15:38:50 DEBUG FileInputDStream: hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0 ignored as mod time 1717940766472 <= ignore time 1734766728620
24/12/21 15:38:50 DEBUG FileInputDStream: hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_1 ignored as mod time
...
24/12/21 15:38:50 DEBUG FileInputDStream: hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_8 ignored as mod time 1734183339919 <= ignore time 1734766728620
```
通过源码可以知道这些文件是因为文件的修改时间小于忽略阈值 `modTimeIgnoreThreshold` (`1734766728620`) 而被过滤掉：
```java
private def isNewFile(fileStatus: FileStatus, currentTime: Long, modTimeIgnoreThreshold: Long): Boolean = {
  ...
  val modTime = fileStatus.getModificationTime()
  if (modTime <= modTimeIgnoreThreshold) {
    logDebug(s"$pathStr ignored as mod time $modTime <= ignore time $modTimeIgnoreThreshold")
    return false
  }
  ...
  return true
}
```
忽略阈值 `modTimeIgnoreThreshold` 是如何设置的呢？具体取决于一个叫 `newFilesOnly` 的配置：
- 如果 `newFilesOnly` 为 `true` 表示只处理新文件，阈值为当前系统时钟
- 如果 `newFilesOnly` 为 `false` 表示还需要处理已有文件，阈值为当前时间往前倒退记忆窗口时长

> 具体详细逻辑在这不再详细介绍，可以参考[Spark Streaming fileStream 实现原理](https://smartsi.blog.csdn.net/article/details/144631839)

由于在上述示例中我们使用的是 `ssc.textFileStream(directory)` 方法：
```
def textFileStream(directory: String): DStream[String] = withNamedScope("text file stream") {
  fileStream[LongWritable, Text, TextInputFormat](directory).map(_._2.toString)
}

def fileStream[K: ClassTag, V: ClassTag, F <: NewInputFormat[K, V]: ClassTag] (directory: String): InputDStream[(K, V)] = {
  new FileInputDStream[K, V, F](this, directory)
}

private[streaming] class FileInputDStream[K, V, F <: NewInputFormat[K, V]](_ssc: StreamingContext, directory: String,
    filter: Path => Boolean = FileInputDStream.defaultFilter,
    newFilesOnly: Boolean = true, conf: Option[Configuration] = None)
    (implicit km: ClassTag[K], vm: ClassTag[V], fm: ClassTag[F])
  extends InputDStream[(K, V)](_ssc) {

    ...

}
```
从上述代码中可以看到 `newFilesOnly` 参数使用的默认值 `true`，这也就是忽略阈值为当前系统时钟，即 Spark Streaming 只能处理新文件。所以程序启动之前的历史老文件被过滤就不足为奇了。

## 2. 如何读取历史文件

`newFilesOnly` 为 `true` 表示只处理新文件，那我们是不是改成 false 就可以解决问题了？如果设置 `newFilesOnly` 参数需要调用如下 `fileStream` 的重载方法：
```java
def fileStream[K, V, F <: NewInputFormat[K, V]](directory: String, kClass: Class[K], vClass: Class[V], fClass: Class[F], filter: JFunction[Path, JBoolean], newFilesOnly: Boolean): JavaPairInputDStream[K, V] = {
    implicit val cmk: ClassTag[K] = ClassTag(kClass)
    implicit val cmv: ClassTag[V] = ClassTag(vClass)
    implicit val cmf: ClassTag[F] = ClassTag(fClass)
    def fn: (Path) => Boolean = (x: Path) => filter.call(x).booleanValue()
    ssc.fileStream[K, V, F](directory, fn, newFilesOnly)
}
```
下面我们以如下示例为例来验证是否可行，核心是设置 `newFilesOnly` 为 `false` 来处理历史已有文件：
```java
SparkConf conf = new SparkConf().setAppName("file-stream").setMaster("local[2]");
// 序列化
conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer");

JavaSparkContext sparkContext = new JavaSparkContext(conf);
JavaStreamingContext ssc = new JavaStreamingContext(sparkContext, Durations.seconds(10));

String path = "hdfs://localhost:9000/user/hive/warehouse/tag_user";

// 过滤临时文件
Function<Path, Boolean> filter = new Function<Path, Boolean>() {
    @Override
    public Boolean call(Path path) throws Exception {
        return !path.getName().startsWith(".");
    }
};

// 读取文件
// newFilesOnly 设置为 false 表示要处理历史已有文件
JavaPairInputDStream<LongWritable, Text> dStream = ssc.fileStream(
        path,
        LongWritable.class,
        Text.class,
        TextInputFormat.class,
        filter,
        false
);
dStream.map(text -> text._2.toString()).print();
```
> 完整代码：[FileStreamSourceExample](https://github.com/sjf0115/data-example/blob/master/spark-example-3.1/src/main/java/com/spark/example/streaming/connector/file/FileStreamSourceExample.java)

通过下面的 Debug 日志可以看到只有 `tag_user/000000_0_copy_9` 文件被检测为新文件：
```java
24/12/21 16:25:31 DEBUG FileInputDStream: hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0 ignored as mod time 1717940766472 <= ignore time 1734769470000
24/12/21 16:25:31 DEBUG FileInputDStream: hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_1 ignored as mod time 1733643640342 <= ignore time 1734769470000
...
24/12/21 16:25:31 DEBUG FileInputDStream: hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_8 ignored as mod time 1734768842384 <= ignore time 1734769470000
24/12/21 16:25:31 DEBUG FileInputDStream: hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_9 accepted with mod time 1734769511658
```
最终输出 `tag_user/000000_0_copy_9` 文件中的数据：
```
-------------------------------------------
Time: 1734769530000 ms
-------------------------------------------
tag3	9
```
虽然 `newFilesOnly` 设置为 `false` 表示我们可以处理历史已有文件，但是不是全部的历史文件都可以被处理。通过[Spark Streaming fileStream 实现原理](https://smartsi.blog.csdn.net/article/details/144631839) 文章分析可以知道处理的历史文件范围取决于忽略阈值 `modTimeIgnoreThreshold`。在 `newFilesOnly` 设置为 `false` 的情况下，忽略阈值等于当前时间减去记忆窗口时长：
```java
modTimeIgnoreThreshold = currentTime - durationToRemember.milliseconds
```
而记忆窗口时长 `durationToRemember` 等于 `slideDuration * math.ceil(minRememberDurationS.milliseconds.toDouble / slideDuration.milliseconds).toInt`。

> slideDuration 为批次时间间隔，在我们示例中设置的为 10s

在批次时间间隔一定的情况下，我们只能修改 `minRememberDurationS` 的值，这个值可以通过 `spark.streaming.fileStream.minRememberDuration` 属性参数来配置。

## 3. 示例

假设我们要读取的目录下有如下 10 个文件：
```shell
(base) localhost:~ wy$ hadoop fs -ls hdfs://localhost:9000/user/hive/warehouse/tag_user
Found 10 items
-rwxr-xr-x   1 wy supergroup         70 2024-06-09 21:46 hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0
-rwxr-xr-x   1 wy supergroup         14 2024-12-08 15:40 hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_1
-rwxr-xr-x   1 wy supergroup         14 2024-12-14 09:59 hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_2
-rwxr-xr-x   1 wy supergroup         14 2024-12-14 12:51 hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_3
-rwxr-xr-x   1 wy supergroup         14 2024-12-14 17:30 hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_4
-rwxr-xr-x   1 wy supergroup          7 2024-12-14 17:32 hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_5
-rwxr-xr-x   1 wy supergroup          7 2024-12-14 21:35 hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_6
-rwxr-xr-x   1 wy supergroup          7 2024-12-21 16:12 hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_7
-rwxr-xr-x   1 wy supergroup          7 2024-12-21 16:14 hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_8
-rwxr-xr-x   1 wy supergroup          7 2024-12-21 16:25 hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_9
```
我们只想读取 2024-12-14 日期(包含)之后的8个文件：
```shell
-rwxr-xr-x   1 wy supergroup         14 2024-12-14 09:59 hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_2
-rwxr-xr-x   1 wy supergroup         14 2024-12-14 12:51 hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_3
-rwxr-xr-x   1 wy supergroup         14 2024-12-14 17:30 hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_4
-rwxr-xr-x   1 wy supergroup          7 2024-12-14 17:32 hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_5
-rwxr-xr-x   1 wy supergroup          7 2024-12-14 21:35 hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_6
-rwxr-xr-x   1 wy supergroup          7 2024-12-21 16:12 hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_7
-rwxr-xr-x   1 wy supergroup          7 2024-12-21 16:14 hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_8
-rwxr-xr-x   1 wy supergroup          7 2024-12-21 16:25 hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_9
```
我们可以通过 `spark.streaming.fileStream.minRememberDuration` 属性参数来配置读取最近8天的文件(当前日期为 2024-12-21)，如下所示：
```java
SparkConf conf = new SparkConf()
        .setAppName("text-file-stream")
        .setMaster("local[2]");

// 序列化
conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer");

// 设置记忆窗口为8*24*60*60 即文件修改时间戳在最近8天内就可以被处理
conf.set("spark.streaming.minRememberDuration", "891200");

JavaSparkContext sparkContext = new JavaSparkContext(conf);
JavaStreamingContext ssc = new JavaStreamingContext(sparkContext, Durations.seconds(10));

String path = "hdfs://localhost:9000/user/hive/warehouse/tag_user";

// 过滤临时文件
Function<Path, Boolean> filter = new Function<Path, Boolean>() {
    @Override
    public Boolean call(Path path) throws Exception {
        return !path.getName().startsWith(".");
    }
};

// 读取文件
JavaPairInputDStream<LongWritable, Text> dStream = ssc.fileStream(
        path,
        LongWritable.class,
        Text.class,
        TextInputFormat.class,
        filter,
        false
);
dStream.map(text -> text._2.toString()).print();
```
> 完整代码：[MinRememberDurationExample](https://github.com/sjf0115/data-example/blob/master/spark-example-3.1/src/main/java/com/spark/example/streaming/connector/file/MinRememberDurationExample.java)

通过 Debug 日志可以看到 2024-12-14 之前的文件都被过滤，只读取了 2024-12-14 之后的 8 个文件：
```java
24/12/21 17:27:51 DEBUG FileInputDStream: hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0 ignored as mod time 1717940766472 <= ignore time 1733882070000
24/12/21 17:27:51 DEBUG FileInputDStream: hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_1 ignored as mod time 1733643640342 <= ignore time 1733882070000
24/12/21 17:27:51 DEBUG FileInputDStream: hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_2 accepted with mod time 1734141565194
24/12/21 17:27:51 DEBUG FileInputDStream: hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_3 accepted with mod time 1734151864835
24/12/21 17:27:51 DEBUG FileInputDStream: hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_4 accepted with mod time 1734168659003
24/12/21 17:27:51 DEBUG FileInputDStream: hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_5 accepted with mod time 1734168734333
24/12/21 17:27:51 DEBUG FileInputDStream: hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_6 accepted with mod time 1734183339919
24/12/21 17:27:51 DEBUG FileInputDStream: hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_7 accepted with mod time 1734768720331
24/12/21 17:27:51 DEBUG FileInputDStream: hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_8 accepted with mod time 1734768842384
24/12/21 17:27:51 DEBUG FileInputDStream: hdfs://localhost:9000/user/hive/warehouse/tag_user/000000_0_copy_9 accepted with mod time 1734769511658
```
程序输出结果也符合我们的预期，读取到了程序启动之前的历史老文件：
```
-------------------------------------------
Time: 1734773270000 ms
-------------------------------------------
tag3	1
tag3	2
tag3	1
tag3	2
tag3	3
tag3	4
tag3	5
tag3	6
tag3	7
tag3	8
```
