HDFS设计之处并不支持给文件追加内容，这样的设计是有其背景的（如果想了解更多关于HDFS的append的曲折实现，可以参考《File Appends in HDFS》：http://blog.cloudera.com/blog/2009/07/file-appends-in-hdfs/
），但从HDFS2.x开始支持给文件追加内容，可以参见 https://issues.apache.org/jira/browse/Hadoop-8230 。可以再看看 http://www.quora.com/HDFS/Is-HDFS-an-append-only-file-system-Then-how-do-people-modify-the-files-stored-on-HDFS 。正如HADOOP-8230所述，只需要将hdfs-site.xml中的以下属性修改为true就行。

## 1. 配置

可以在做如下配置：
```
<property>
    <name>dfs.support.append</name>
    <value>true</value>
</property>
```
## 2. 实现

我们可以通过Hadoop提供的API实现文件内容追加，代码如下：

```
    /**
     * HDFS内容追加
     * @param sourcePath
     * @param targetPath
     * @throws IOException
     */
    public static void append(String sourcePath, String targetPath) throws IOException {
        if(StringUtils.isBlank(sourcePath) || StringUtils.isBlank(targetPath)){
            return;
        }
        Configuration conf = new Configuration();
        conf.set("dfs.support.append", "true");
        // 源文件
        FileSystem sourceFileSystem = FileSystem.get(URI.create(sourcePath), conf);
        InputStream inputStream = sourceFileSystem.open(new Path(sourcePath));
        // 目标文件
        FileSystem targetFileSystem = FileSystem.get(URI.create(targetPath), conf);
        OutputStream outputStream = targetFileSystem.append(new Path(targetPath));
        // 源文件添加到目标文件
        IOUtils.copy(inputStream, outputStream);
    }
```    
## 3. 追加本地文件到HDFS文件

我们先看看原文件内容：
```
xiaosi@yoona:~$ hadoop fs -put a.txt test/
xiaosi@yoona:~$ hadoop fs -text test/a.txt
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
```
我们再来看看要追加文件内容：
```
xiaosi@yoona:~$ cat b.txt
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
```
现在我们把b.txt中的内容追加到HDFS上的a.txt文件中：
```
    @Test
    public void append() throws Exception {
        String sourcePath = "/home/xiaosi/b.txt";
        String targetPath = "hdfs://localhost:9000/user/xiaosi/test/a.txt";
        HDFSUtil.append(sourcePath, targetPath);
    }
```    
再来看一下追加之后a.txt文件的内容：
```
xiaosi@yoona:~$ hadoop fs -text test/a.txt
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
```
## 4. 追加HDFS文件到HDFS文件

我们先看看原文件内容：
```
xiaosi@yoona:~$ hadoop fs -put a.txt test/
xiaosi@yoona:~$ hadoop fs -text test/a.txt
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
```
我们再来看看要追加文件内容：
```
xiaosi@yoona:~$ hadoop fs -put b.txt test/
xiaosi@yoona:~$ hadoop fs -text test/b.txt
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
```
现在我们把b.txt中的内容追加到HDFS上的a.txt文件中：

```
    @Test
    public void append() throws Exception {
        String sourcePath = "hdfs://localhost:9000/user/xiaosi/test/b.txt";
        String targetPath = "hdfs://localhost:9000/user/xiaosi/test/a.txt";
        HDFSUtil.append(sourcePath, targetPath);
    }
```    
再来看一下追加之后a.txt文件的内容：
```
xiaosi@yoona:~$ hadoop fs -text test/a.txt
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
aaaaaaaaa
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
bbbbbbbbb
```