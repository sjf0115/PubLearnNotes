### 1. HDFS文件合并到本地

当我们分析Web服务器的Apache日志文件时，由于不同机器在每隔一定时间间隔会生成一个文件，我们想把这些文件合并成一个单独的文件复制到本地进行分析。Hadoop命令行工具中有一个`getMerge`命令，用于把一组HDFS文件复制到本地计算机以前先进行合并。因此我们可以使用这个命令来实现。

语法:
```
hadoop fs -getmerge <src> <localdst> [addnl]
```
说明:
```
接受一个源目录和一个目标文件作为输入，并且将源目录中所有的文件连接成本地目标文件。addnl是可选的，用于指定在每个文件结尾添加一个换行符。
```
Example:
```
# 文件内容
sudo -uwirelessdev hadoop fs -ls ads/click/20170914/
-rw-r--r--   3 xiaosi xiaosi     175441 2017-09-15 00:25 ads/click/20170914/advertisement1.gz
-rw-r--r--   3 xiaosi xiaosi     175650 2017-09-15 00:32 ads/click/20170914/advertisement2.gz
-rw-r--r--   3 xiaosi xiaosi     169371 2017-09-15 00:32 ads/click/20170914/advertisement3.gz
-rw-r--r--   3 xiaosi xiaosi     170835 2017-09-15 00:31 ads/click/20170914/advertisement4.gz
-rw-r--r--   3 xiaosi xiaosi     173836 2017-09-15 00:31 ads/click/20170914/advertisement5.gz
# 合并
sudo -uxiaosi hadoop fs -getmerge  ads/click/20170914/*.gz /home/xiaosi/data/advertisement.gz
```
上述代码将20170914这一天5台机器产生的日志合并为一个文件advertisement.gz

### 2. 本地文件合并到HDFS

当我们分析Web服务器的Apache日志文件时，我们可以把每个日志文件复制到HDFS中，但这样面临的一个问题是，Hadoop处理单个大文件会比处理多个小文件更有效率。一种解决办法是先将所有的文件合并，然后再复制到HDFS中。可是文件合并需要占用本地计算机的大量磁盘空间。如果我们能够在向HDFS复制的过程中合并它们，事情就简单很多。

因此我们需要一个PutMerge类型的操作。Hadoop命令行工具中有一个getMerge命令，用于把一组HDFS文件复制到本地计算机以前先进行合并。但我们想要的截然相反，无法再Hadoop文件管理工具获取，我们用HDFS API来自己编程实现它。

Hadoop文件API的起点是FileSystem类。这是一个与文件系统交互的抽象类，存在不同的具体实现子类用来处理HDFS和本地文件系统。你可以通过调用factory方法`FileSystem.get(Configuration conf)`来得到所需的FileSystem实例。Configuration类是用于保留简直对配置参数的特殊类。它的默认实例化方法是以HDFS系统的资源配置为基础的。我们可以iddio与HDFS接口的FileSystem对象:
```java
Configuration conf = new Configuration();
FileSystem hdfs = FileSystem.get(conf);
```
要得到一个专用于本地文件系统的FileSystem对象，可用factory方法`FileSystem.getLocal(Configuration conf)`:
```java
Configuration conf = new Configuration();
FileSystem local = FileSystem.getLocal(conf);
```
Hadoop文件API使用Path对象来编制文件和目录名，使用FileStatus对象来存储文件和目录的元数据。PutMerge程序将合并一个本地目录中的所有文件。我们使用FileSystem的`listStatus()`方法来得到一个目录中的文件列表:
```java
Path inputPath = new Path(inputPathStr);
FileStatus[] inputFiles = local.listStatus(inputPath);
```
数组inputFiles的长度等于制定目录中的文件个数。在inputFiles中每一个FileStatus对象均有元数据信息，如文件长度，权限，修改时间等。我们通过FSDataInputStream对象访问Path读取文件，通过FSDataOutputStream对象将数据写入HDFS文件:
```java
FSDataInputStream input = local.open(inputFiles[index].getPath());
byte buffer[] = new byte[256];
int bytesRead = 0;
while( (bytesRead = input.read(buffer)) > 0 ){
    output.write(buffer, 0 , bytesRead);
}
input.close();
```
Example:
```java
/**
 * 文件合并
 * @param inputPathStr
 * @param outputPathStr
 * @throws IOException
 */
public static void putMerge(String inputPathStr, String outputPathStr) throws IOException {

    if(StringUtils.isBlank(inputPathStr) || StringUtils.isBlank(outputPathStr)){
        throw new RuntimeException("输入路径或输出路径不能为空");
    }

    // 设定输入输出目录
    Path inputPath = new Path(inputPathStr);
    Path outputPath = new Path(outputPathStr);

    Configuration conf = new Configuration();
    // HDFS文件系统
    FileSystem hdfs = FileSystem.get(conf);
    // 本地文件系统
    FileSystem local = FileSystem.getLocal(conf);

    try{
        // 本地文件列表
        FileStatus[] inputFiles = local.listStatus(inputPath);
        // HDFS输出流
        FSDataOutputStream output = hdfs.create(outputPath);
        for(int index = 0;index < inputFiles.length;index++){
            System.out.println("FileName: " + inputFiles[index].getPath().getName());
            // 打开本地输入流
            FSDataInputStream input = local.open(inputFiles[index].getPath());
            byte buffer[] = new byte[256];
            int bytesRead = 0;
            while( (bytesRead = input.read(buffer)) > 0 ){
                output.write(buffer, 0 , bytesRead);
            }
            input.close();
        }
        output.close();
    }
    catch (Exception e){
        throw new RuntimeException("文件合并失败: " + e.getMessage());
    }
}
```

来源于<<Hadoop实战>>

### 3. HDFS文件合并到HDFS

可以通过如下代码实现:
```
sudo -uxiaosi hadoop fs -cat ads/click/20170914/* |  sudo -uxiaosi hadoop fs -copyFromLocal - ads/total/day=20170914/click_advertisement.gz
```
