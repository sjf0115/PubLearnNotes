
### 1. get
格式：
```
hadoop fs -get [-ignorecrc] [-crc] <src> <localdst>
```
功能：
```
复制文件到本地文件系统。可用-ignorecrc选项复制CRC校验失败的文件。使用-crc选项复制文件以及CRC信息。
```
示例：
```
hadoop fs -get /user/hadoop/file localfile
hadoop fs -get hdfs://host:port/user/hadoop/file localfile
```
返回值：
```
成功返回0，失败返回-1。
```


### 2. put

使用方法：
```
hadoop fs -put <localsrc> ... <dst>
```
功能：
```
从本地文件系统中复制单个或多个源路径到目标文件系统。也支持从标准输入中读取输入写入目标文件系统。
```
示例：
```
hadoop fs -put localfile /user/hadoop/hadoopfile
hadoop fs -put localfile1 localfile2 /user/hadoop/hadoopdir
hadoop fs -put localfile hdfs://host:port/hadoop/hadoopfile
hadoop fs -put - hdfs://host:port/hadoop/hadoopfile  #从标准输入中读取输入
```
返回值：
```
成功返回0，失败返回-1。
```


### 3. mkdir

使用方法：
```
hadoop fs -mkdir <paths>
```
功能：
```
接受路径指定的uri作为参数，创建这些目录。其行为类似于Unix的mkdir -p，它会创建路径中的各级父目录。
```
示例：
```
hadoop fs -mkdir /user/hadoop/dir1 /user/hadoop/dir2
hadoop fs -mkdir hdfs://host1:port1/user/hadoop/dir hdfs://host2:port2/user/hadoop/dir
hadoop fs -mkdir -p user/user_active_new_user
```
返回值：
```
成功返回0，失败返回-1。
```

### 4. getconf


```
xiaosi@yoona:~$ hdfs getconf -confKey fs.trash.interval
0
```
