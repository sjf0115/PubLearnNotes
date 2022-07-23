

### 3. 

上面两个示例中我们虽然重新定义了文件或者目录，但是总会输出 `part-r-xxx` 形式的默认文件，这些文件并且是空文件：
```
localhost:target wy$ hadoop fs -cat /data/word-count/word-count-output/part-r-00000
localhost:target wy$
```
FileOutputFormat 的子类会产生 `part-r-nnnnn` 格式的输出文件，即使文件是空的也会产生。有时候我们不想要这些空文件，我们可以使用 LazyOutputFormat 进行处理。它是一个封装输出格式，可以指定在分区第一条记录输出时才创建文件。使用 JobConf 和相关输出格式作为参数来调用 `setOutputFormatClass()` 方法即可使用：
```java
Configuration conf = this.getConf();
Job job = Job.getInstance(conf);
LazyOutputFormat.setOutputFormatClass(job, TextOutputFormat.class);
```
再次检查一下我们的输出文件（第一个例子）：
```
localhost:target wy$ hadoop fs -ls /data/word-count/word-count-output/
Found 6 items
-rw-r--r--   1 wy supergroup          0 2022-07-23 17:10 /data/word-count/word-count-output/_SUCCESS
-rw-r--r--   1 wy supergroup          9 2022-07-23 17:10 /data/word-count/word-count-output/a-r-00000
-rw-r--r--   1 wy supergroup          8 2022-07-23 17:10 /data/word-count/word-count-output/f-r-00000
-rw-r--r--   1 wy supergroup          9 2022-07-23 17:10 /data/word-count/word-count-output/h-r-00000
-rw-r--r--   1 wy supergroup          4 2022-07-23 17:10 /data/word-count/word-count-output/i-r-00000
-rw-r--r--   1 wy supergroup         21 2022-07-23 17:10 /data/word-count/word-count-output/s-r-00000
```
此时空文件 part-r-00000 已经不存在了。
