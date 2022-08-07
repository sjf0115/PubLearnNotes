
### 1. 添加内存
```
set mapreduce.map.memory.mb=4096;
set mapreduce.map.java.opts=-Xmx4096m;
set mapreduce.reduce.memory.mb=4096;
set mapreduce.reduce.java.opts=-Xmx4096m;
```
### 2. 压缩中间输出数据
```
set hive.exec.compress.intermediate=true;
set hive.intermediate.compression.codec=org.apache.hadoop.io.compress.SnappyCodec;
set hive.intermediate.compression.type=BLOCK;
```
### 3. 压缩最终输出数据
```
set hive.exec.compress.output=true;
set mapreduce.output.fileoutputformat.compress=true;
set mapreduce.output.fileoutputformat.compress.codec=org.apache.hadoop.io.compress.GzipCodec;
set mapreduce.output.fileoutputformat.compress.type=BLOCK;
```
### 4. 避免本地Task

```
# 禁止启动本地模式运行和禁止启动 FetchTask
set hive.exec.mode.local.auto=false;
set hive.fetch.task.conversion=none;
```
