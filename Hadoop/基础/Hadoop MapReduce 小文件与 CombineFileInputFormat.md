处理小文件是Hadoop中的一个经典问题:在![Stack Overflow](https://stackoverflow.com/questions/14541759/how-can-i-work-with-large-number-of-small-files-in-hadoop)上，建议人们使用CombineFileInputFormat，但是我没有找到一个很好的文章，一步一步的教你如何使用它。所以，我决定自己写一个。

来自于Cloudera博客:
```
小文件是指文件大小明显小于HDFS上块（block）大小（默认64MB）的文件。如果存储小文件，必定会有大量这样的小文件，否则你也不会使用Hadoop，这样的文件给hadoop的扩展性和性能带来严重问题。当一个文件的大小小于HDFS的块大小（默认64MB），就将认定为小文件否则就是大文件。
```

### 1. 基准测试

在我的基准测试中，只需使用自定义的CombineFileInputFormat即可将程序从3小时缩减到23分钟，并在进一步调整之后，可以在6分钟内运行相同的任务！

为了测试不同方法对解决小文件问题的性能，我设置了一个Map，只是做grep并执行二分查找。二分查找部分生成Reduce的key，进一步数据处理的; 它只需要一点点资源（8MB）运行，所以它不会影响基准的结果。

要处理的数据是一些服务器日志数据，总共为53.1 GB。hadoop集群由6个节点组成，使用hadoop 1.1.2版本。在这个基准测试中，实现CombineFileInputFormat类来缩小Map作业; 我还测试了重用JVM的区别，以及不同数量的块大小来组合文件。

### 2. CombineFileInputFormat

这里列出的代码是从![Hadoop示例代码](https://svn.apache.org/repos/asf/hadoop/common/trunk/hadoop-mapreduce-project/hadoop-mapreduce-examples/src/main/java/org/apache/hadoop/examples/MultiFileWordCount.java)中修改而来的。要使用`CombineFileInputFormat`，你需要实现三个类。`CombineFileInputFormat`类是一个没有任何实现的抽象类，所以你必须创建一个子类来实现它; 我们将子类命名为`CFInputFormat`。子类将启动扩展RecordReader的委托CFRecordReader; 这是文件执行逻辑处理的地方。我们还需要一个`FileLineWritable`类，通常替换LongWritable用作文件行的key。

#### 2.1 CFInputFormat

`CFInputFormat`类没有做太多的事情。你需要实现`createRecordReader`方法来传递合并文件逻辑的记录读取器，就是这样。 请注意，你可以在初始化程序中调用setMaxSplitSize来控制每个文件块的大小; 如果你不想将文件分割成一半，请记住在isSplitable方法中返回false，默认为true。
```java
package org.idryman.combinefiles;

import java.io.IOException;

import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.InputSplit;
import org.apache.hadoop.mapreduce.JobContext;
import org.apache.hadoop.mapreduce.RecordReader;
import org.apache.hadoop.mapreduce.TaskAttemptContext;
import org.apache.hadoop.mapreduce.lib.input.CombineFileInputFormat;
import org.apache.hadoop.mapreduce.lib.input.CombineFileRecordReader;
import org.apache.hadoop.mapreduce.lib.input.CombineFileSplit;

import org.idryman.combinefiles.CFRecordReader;
import org.idryman.combinefiles.FileLineWritable;

public class CFInputFormat extends CombineFileInputFormat<FileLineWritable, Text> {
  public CFInputFormat(){
    super();
    setMaxSplitSize(67108864); // 64 MB, default block size on hadoop
  }
  public RecordReader<FileLineWritable, Text> createRecordReader(InputSplit split, TaskAttemptContext context) throws IOException{
    return new CombineFileRecordReader<FileLineWritable, Text>((CombineFileSplit)split, context, CFRecordReader.class);
  }
  @Override
  protected boolean isSplitable(JobContext context, Path file){
    return false;
  }
}
```

#### 2.2 CFRecordReader

`CFRecordReader`是`CombineFileRecordReader`的一个委托类，它是一个内置的类，它将每个拆分（在这个例子中通常是整个文件）传递给我们的`CFRecordReader`类。 当hadoop作业启动时，`CombineFileRecordReader`读取我们希望处理的HDFS中所有文件大小，并根据在`CFInputFormat`中定义的`MaxSplitSize`来决定如何分割。对于每个分割（必须是一个文件，因为我们将`isSplitabe`设置为false），`CombineFileRecordReader`通过自定义构造函数创建一个`CFRecrodReader`实例，并将CombineFileSplit，context和index三个参数传递`CFRecordReader`，以找到要处理的文件。

处理文件时，`CFRecordReader`会创建一个`FileLineWritable`作为hadoop mapper类的key。对于每一行，`FileLineWritable`包含该行的文件名和偏移长度。`FileLineWritable`和通常使用的`LongWritable`在Mapper中的区别是`LongWritable`仅表示文件中行的偏移量，而`FileLineWritable`将文件信息添加到key中。


```java
package com.sjf.open.example;

import org.apache.hadoop.fs.FSDataInputStream;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.InputSplit;
import org.apache.hadoop.mapreduce.RecordReader;
import org.apache.hadoop.mapreduce.TaskAttemptContext;
import org.apache.hadoop.mapreduce.lib.input.CombineFileSplit;
import org.apache.hadoop.util.LineReader;

import java.io.IOException;

/**
 * Created by xiaosi on 17-8-8.
 */
public class CFRecordReader extends RecordReader<FileLineWritable, Text> {

    private long startOffset;
    private long end;
    private long pos;
    private FileSystem fs;
    private Path path;
    private FileLineWritable key;
    private Text value;

    private FSDataInputStream fileIn;
    private LineReader reader;

    public CFRecordReader(CombineFileSplit split, TaskAttemptContext context, Integer index) throws IOException {
        this.path = split.getPath(index);
        fs = this.path.getFileSystem(context.getConfiguration());
        this.startOffset = split.getOffset(index);
        this.end = startOffset + split.getLength(index);

        fileIn = fs.open(path);
        reader = new LineReader(fileIn);
        this.pos = startOffset;
    }

    @Override
    public void initialize(InputSplit arg0, TaskAttemptContext arg1) throws IOException, InterruptedException {
        // Won't be called, use custom Constructor
        // `CFRecordReader(CombineFileSplit split, TaskAttemptContext context, Integer index)`
        // instead
    }

    @Override
    public void close() throws IOException {
    }

    @Override
    public float getProgress() throws IOException {
        if (startOffset == end) {
            return 0;
        }
        return Math.min(1.0f, (pos - startOffset) / (float) (end - startOffset));
    }

    @Override
    public FileLineWritable getCurrentKey() throws IOException, InterruptedException {
        return key;
    }

    @Override
    public Text getCurrentValue() throws IOException, InterruptedException {
        return value;
    }

    @Override
    public boolean nextKeyValue() throws IOException {
        if (key == null) {
            key = new FileLineWritable();
            key.fileName = path.getName();
        }
        key.offset = pos;
        if (value == null) {
            value = new Text();
        }
        int newSize = 0;
        if (pos < end) {
            newSize = reader.readLine(value);
            pos += newSize;
        }
        if (newSize == 0) {
            key = null;
            value = null;
            return false;
        } else {
            return true;
        }
    }
}
```
使用自定义构造函数的原因在hadoop api或document中的任何地方都没有记录。你只能在hadoop源代码中找到它，第40行：
```java
static final Class [] constructorSignature = new Class []
                                       {CombineFileSplit.class,
                                        TaskAttemptContext.class,
                                        Integer.class};
```

#### 2.3 FileLineWritable

此文件非常简单：存储文件名和偏移量，并覆盖compareTo方法实现首先比较文件名，然后再比较偏移量。
```java
package com.sjf.open.example;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.WritableComparable;

import java.io.DataInput;
import java.io.DataOutput;
import java.io.IOException;

/**
 * Created by xiaosi on 17-8-8.
 */
public class FileLineWritable implements WritableComparable<FileLineWritable> {
    public long offset;
    public String fileName;

    public void readFields(DataInput in) throws IOException {
        this.offset = in.readLong();
        this.fileName = Text.readString(in);
    }

    public void write(DataOutput out) throws IOException {
        out.writeLong(offset);
        Text.writeString(out, fileName);
    }

    public int compareTo(FileLineWritable that) {
        int cmp = this.fileName.compareTo(that.fileName);
        if (cmp != 0)
            return cmp;
        return (int) Math.signum((double) (this.offset - that.offset));
    }

    @Override
    public int hashCode() { // generated hashCode()
        final int prime = 31;
        int result = 1;
        result = prime * result + ((fileName == null) ? 0 : fileName.hashCode());
        result = prime * result + (int) (offset ^ (offset >>> 32));
        return result;
    }

    @Override
    public boolean equals(Object obj) { // generated equals()
        if (this == obj)
            return true;
        if (obj == null)
            return false;
        if (getClass() != obj.getClass())
            return false;
        FileLineWritable other = (FileLineWritable) obj;
        if (fileName == null) {
            if (other.fileName != null)
                return false;
        } else if (!fileName.equals(other.fileName))
            return false;
        if (offset != other.offset)
            return false;
        return true;
    }
}
```

### 3. 设置job

最后是hadoop集群运行的作业设置。 我们只需要将类分配给job：

```java
import org.apache.hadoop.mapreduce.Job;
// standard hadoop conf
Job job = new Job(getConf());
FileInputFormat.addInputPath(job, new Path(args[0]));
job.setInputFormatClass(CFInputFormat.class);
job.setMapperClass(MyMapper.class);
job.setNumReduceTasks(0); // map only
FileOutputFormat.setOutputPath(job, new Path(args[1]));
job.submit();
```




```
17/08/09 14:14:59 INFO client.RMProxy: Connecting to ResourceManager at l-hdpm2.data.cn5/10.88.144.88:8032
17/08/09 14:15:22 INFO input.FileInputFormat: Total input paths to process : 120
17/08/09 14:15:22 INFO lzo.GPLNativeCodeLoader: Loaded native gpl library from the embedded binaries
17/08/09 14:15:22 INFO lzo.LzoCodec: Successfully loaded & initialized native-lzo library [hadoop-lzo rev 015e93e6bae89a7ea2ed67c6e3b8e9e23cee299d]
17/08/09 14:15:22 INFO input.CombineFileInputFormat: DEBUG: Terminated node allocation with : CompletedNodes: 285, size left: 77493524
17/08/09 14:15:26 INFO mapreduce.JobSubmitter: number of splits:3
17/08/09 14:15:26 INFO Configuration.deprecation: mapred.job.name is deprecated. Instead, use mapreduce.job.name
17/08/09 14:15:26 INFO Configuration.deprecation: mapred.job.queue.name is deprecated. Instead, use mapreduce.job.queuename
17/08/09 14:15:26 INFO Configuration.deprecation: mapreduce.map.class is deprecated. Instead, use mapreduce.job.map.class
17/08/09 14:15:26 INFO Configuration.deprecation: mapred.input.dir is deprecated. Instead, use mapreduce.input.fileinputformat.inputdir
17/08/09 14:15:26 INFO Configuration.deprecation: mapred.max.split.size is deprecated. Instead, use mapreduce.input.fileinputformat.split.maxsize
17/08/09 14:15:26 INFO Configuration.deprecation: mapreduce.inputformat.class is deprecated. Instead, use mapreduce.job.inputformat.class
17/08/09 14:15:26 INFO Configuration.deprecation: mapred.job.priority is deprecated. Instead, use mapreduce.job.priority
17/08/09 14:15:26 INFO Configuration.deprecation: mapred.jar is deprecated. Instead, use mapreduce.job.jar
17/08/09 14:15:26 INFO Configuration.deprecation: mapred.output.dir is deprecated. Instead, use mapreduce.output.fileoutputformat.outputdir
17/08/09 14:15:26 INFO Configuration.deprecation: mapred.job.reduce.memory.mb is deprecated. Instead, use mapreduce.reduce.memory.mb
17/08/09 14:15:26 INFO Configuration.deprecation: mapred.working.dir is deprecated. Instead, use mapreduce.job.working.dir
17/08/09 14:15:26 INFO Configuration.deprecation: mapred.mapoutput.value.class is deprecated. Instead, use mapreduce.map.output.value.class
17/08/09 14:15:26 INFO Configuration.deprecation: mapred.output.compress is deprecated. Instead, use mapreduce.output.fileoutputformat.compress
17/08/09 14:15:26 INFO Configuration.deprecation: mapred.map.tasks is deprecated. Instead, use mapreduce.job.maps
17/08/09 14:15:26 INFO Configuration.deprecation: mapred.mapoutput.key.class is deprecated. Instead, use mapreduce.map.output.key.class
17/08/09 14:15:26 INFO Configuration.deprecation: mapred.job.map.memory.mb is deprecated. Instead, use mapreduce.map.memory.mb
17/08/09 14:15:26 INFO Configuration.deprecation: user.name is deprecated. Instead, use mapreduce.job.user.name
17/08/09 14:15:26 INFO Configuration.deprecation: mapred.output.compression.codec is deprecated. Instead, use mapreduce.output.fileoutputformat.compress.codec
17/08/09 14:15:26 INFO mapreduce.JobSubmitter: Submitting tokens for job: job_1472052053889_22607057
17/08/09 14:15:26 INFO impl.YarnClientImpl: Submitted application application_1472052053889_22607057 to ResourceManager at l-hdpm2.data.cn5/10.88.144.88:8032
17/08/09 14:15:26 INFO mapreduce.Job: The url to track the job: xxx/proxy/application_1472052053889_22607057/
17/08/09 14:15:26 INFO mapreduce.Job: Running job: job_1472052053889_22607057
17/08/09 14:15:35 INFO mapreduce.Job: Job job_1472052053889_22607057 running in uber mode : false
17/08/09 14:15:35 INFO mapreduce.Job:  map 0% reduce 0%
17/08/09 14:15:47 INFO mapreduce.Job:  map 33% reduce 0%
17/08/09 14:15:49 INFO mapreduce.Job:  map 53% reduce 0%
17/08/09 14:15:50 INFO mapreduce.Job:  map 66% reduce 0%
17/08/09 14:15:52 INFO mapreduce.Job:  map 79% reduce 0%
17/08/09 14:15:53 INFO mapreduce.Job:  map 87% reduce 0%
17/08/09 14:15:56 INFO mapreduce.Job:  map 100% reduce 0%
17/08/09 14:16:01 INFO mapreduce.Job:  map 100% reduce 68%
17/08/09 14:16:04 INFO mapreduce.Job:  map 100% reduce 74%
17/08/09 14:16:07 INFO mapreduce.Job:  map 100% reduce 80%
17/08/09 14:16:10 INFO mapreduce.Job:  map 100% reduce 88%
17/08/09 14:16:13 INFO mapreduce.Job:  map 100% reduce 96%
17/08/09 14:16:16 INFO mapreduce.Job:  map 100% reduce 100%
17/08/09 14:16:16 INFO mapreduce.Job: Job job_1472052053889_22607057 completed successfully
17/08/09 14:16:16 INFO mapreduce.Job: Counters: 43
        File System Counters
                FILE: Number of bytes read=1020492911
                FILE: Number of bytes written=1562447050
                FILE: Number of read operations=0
                FILE: Number of large read operations=0
                FILE: Number of write operations=0
                HDFS: Number of bytes read=77508893
                HDFS: Number of bytes written=78230576
                HDFS: Number of read operations=129
                HDFS: Number of large read operations=0
                HDFS: Number of write operations=2
        Job Counters
                Launched map tasks=3
                Launched reduce tasks=1
                Other local map tasks=3
                Total time spent by all maps in occupied slots (ms)=41289
                Total time spent by all reduces in occupied slots (ms)=210840
        Map-Reduce Framework
                Map input records=1205757
                Map output records=1205757
                Map output bytes=536785769
                Map output materialized bytes=541608175
                Input split bytes=15369
                Combine input records=0
                Combine output records=0
                Reduce input groups=120
                Reduce shuffle bytes=541608175
                Reduce input records=1205757
                Reduce output records=1205757
                Spilled Records=3477544
                Shuffled Maps =3
                Failed Shuffles=0
                Merged Map outputs=3
                GC time elapsed (ms)=1565
                CPU time spent (ms)=52780
                Physical memory (bytes) snapshot=3878338560
                Virtual memory (bytes) snapshot=19011239936
                Total committed heap usage (bytes)=5566365696
        Shuffle Errors
                BAD_ID=0
                CONNECTION=0
                IO_ERROR=0
                WRONG_LENGTH=0
                WRONG_MAP=0
                WRONG_REDUCE=0
        File Input Format Counters
                Bytes Read=0
        File Output Format Counters
                Bytes Written=78230576
```

http://www.idryman.org/blog/2013/09/22/process-small-files-on-hadoop-using-combinefileinputformat-1/
