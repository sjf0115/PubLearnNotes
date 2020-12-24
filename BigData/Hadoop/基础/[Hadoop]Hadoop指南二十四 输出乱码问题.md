集群上提交的mr任务，发现结果中有的中文正常，有的中文是论码。
分析了一下，应该是集群中hadoop节点的编码配置不一样。可以加上下面的参数：
```
mapred.child.env="LANG=en_US.UTF-8,LC_ALL=en_US.UTF-8" ;
```


hadoop涉及输出文本的默认输出编码统一用没有BOM的UTF-8的形式，但是对于中文的输出window系统默认的是GBK，有些格式文件例如CSV格式的文件用excel打开输出编码为没有BOM的UTF-8文件时，输出的结果为乱码，只能由UE或者记事本打开才能正常显示。因此将hadoop默认输出编码更改为GBK成为非常常见的需求。

默认的情况下MR主程序中，设定输出编码的设置语句为：
```
job.setOutputFormatClass(TextOutputFormat.class);
```



`TextOutputFormat`源码如下:
```java
//
// Source code recreated from a .class file by IntelliJ IDEA
// (powered by Fernflower decompiler)
//

package org.apache.hadoop.mapreduce.lib.output;

import java.io.DataOutputStream;
import java.io.IOException;
import java.io.UnsupportedEncodingException;
import org.apache.hadoop.classification.InterfaceAudience.Public;
import org.apache.hadoop.classification.InterfaceStability.Stable;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FSDataOutputStream;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.compress.CompressionCodec;
import org.apache.hadoop.io.compress.GzipCodec;
import org.apache.hadoop.mapreduce.RecordWriter;
import org.apache.hadoop.mapreduce.TaskAttemptContext;
import org.apache.hadoop.util.ReflectionUtils;

@Public
@Stable
public class TextOutputFormat<K, V> extends FileOutputFormat<K, V> {
    public static String SEPERATOR = "mapreduce.output.textoutputformat.separator";

    public TextOutputFormat() {
    }

    public RecordWriter<K, V> getRecordWriter(TaskAttemptContext job) throws IOException, InterruptedException {
        Configuration conf = job.getConfiguration();
        boolean isCompressed = getCompressOutput(job);
        String keyValueSeparator = conf.get(SEPERATOR, "\t");
        CompressionCodec codec = null;
        String extension = "";
        if (isCompressed) {
            Class<? extends CompressionCodec> codecClass = getOutputCompressorClass(job, GzipCodec.class);
            codec = (CompressionCodec)ReflectionUtils.newInstance(codecClass, conf);
            extension = codec.getDefaultExtension();
        }

        Path file = this.getDefaultWorkFile(job, extension);
        FileSystem fs = file.getFileSystem(conf);
        FSDataOutputStream fileOut;
        if (!isCompressed) {
            fileOut = fs.create(file, false);
            return new TextOutputFormat.LineRecordWriter(fileOut, keyValueSeparator);
        } else {
            fileOut = fs.create(file, false);
            return new TextOutputFormat.LineRecordWriter(new DataOutputStream(codec.createOutputStream(fileOut)), keyValueSeparator);
        }
    }

    protected static class LineRecordWriter<K, V> extends RecordWriter<K, V> {
        private static final String utf8 = "UTF-8";
        private static final byte[] newline;
        protected DataOutputStream out;
        private final byte[] keyValueSeparator;

        public LineRecordWriter(DataOutputStream out, String keyValueSeparator) {
            this.out = out;

            try {
                this.keyValueSeparator = keyValueSeparator.getBytes("UTF-8");
            } catch (UnsupportedEncodingException var4) {
                throw new IllegalArgumentException("can't find UTF-8 encoding");
            }
        }

        public LineRecordWriter(DataOutputStream out) {
            this(out, "\t");
        }

        private void writeObject(Object o) throws IOException {
            if (o instanceof Text) {
                Text to = (Text)o;
                this.out.write(to.getBytes(), 0, to.getLength());
            } else {
                this.out.write(o.toString().getBytes("UTF-8"));
            }

        }

        public synchronized void write(K key, V value) throws IOException {
            boolean nullKey = key == null || key instanceof NullWritable;
            boolean nullValue = value == null || value instanceof NullWritable;
            if (!nullKey || !nullValue) {
                if (!nullKey) {
                    this.writeObject(key);
                }

                if (!nullKey && !nullValue) {
                    this.out.write(this.keyValueSeparator);
                }

                if (!nullValue) {
                    this.writeObject(value);
                }

                this.out.write(newline);
            }
        }

        public synchronized void close(TaskAttemptContext context) throws IOException {
            this.out.close();
        }

        static {
            try {
                newline = "\n".getBytes("UTF-8");
            } catch (UnsupportedEncodingException var1) {
                throw new IllegalArgumentException("can't find UTF-8 encoding");
            }
        }
    }
}

```
从上述代码的第48行可以看出hadoop已经限定此输出格式统一为UTF-8，因此为了改变hadoop的输出代码的文本编码只需定义一个和TextOutputFormat相同的类GbkOutputFormat同样继承FileOutputFormat（注意是org.apache.hadoop.mapreduce.lib.output.FileOutputFormat）即可，如下代码：





Hadoop源代码中涉及编码问题时都是写死的utf-8，但是不少情况下，也会遇到输入文件和输出文件需要GBK编码的情况。

输入文件为GBK，则只需在mapper或reducer程序中读取Text时，使用transformTextToUTF8(text, "GBK");进行一下转码，以确保都是以UTF-8的编码方式在运行。
```java
public static Text transformTextToUTF8(Text text, String encoding) {
    String value = null;
    try {
        value = new String(text.getBytes(), 0, text.getLength(), encoding);
    } catch (UnsupportedEncodingException e) {
        e.printStackTrace();
    }
    return new Text(value);
}
```

输出文件为GBK，则重写TextOutputFormat类，public class GBKFileOutputFormat<K, V> extends FileOutputFormat<K, V>，把TextOutputFormat的源码拷过来，然后把里面写死的utf-8编码改成GBK编码。最后，在run程序中，设置job.setOutputFormatClass(GBKFileOutputFormat.class);
