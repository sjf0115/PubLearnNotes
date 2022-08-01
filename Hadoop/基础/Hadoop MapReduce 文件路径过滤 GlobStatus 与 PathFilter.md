## 1. 丢失文件路径过滤

应用场景：我们想查询一个月以来度假的订单数据，但是HDFS中可能因为业务故障，导致某一天的订单数据不存在：
```java
FileInputFormat.setInputPaths(job, inputPath);
```
上述代码在遇到路径不存在的时候会报错。

所以在设置路径之前需要进行一次判断，判断这个路径在HDFS上是否存在，如果存在，使用addInputPath方法添加：
```java
FileSystem fileSystem = FileSystem.get(conf);
String[] params = inputPath.split(",");
for(String path : params){
   boolean isExists = fileSystem.exists(new Path(path));
   if(isExists){
      FileInputFormat.addInputPath(job, new Path(path));
   }
}
```

## 2. GlobStatus 文件模式过滤

在一步操作中批量处理文件，这个要求很常见。举例来说，处理日志的 MapReduce 作业可能会分析一个月的文件，这些文件可能会包含在很多目录中。针对这样的需求，可以在一个表达式使用通配符来匹配多个文件，从而不需要列举每个文件和目录来指定输入。Hadoop 提供了两个 FileSystem 方法来使用通配符来匹配：
```java
public FileStatus[] globStatus(Path pathPattern) throws IOException
public FileStatus[] globStatus(Path pathPattern, PathFilter filter) throws IOException
```

globStatus() 返回了路径格式指定模式与相匹配的所有 FileStatus 对象组成的数组，并按路径排序。可选的 PathFilter 命令可以进一步对匹配结果进行限制。

### 2.1 通配符过滤

Hadoop 支持的通配符与 Unix bash 支持的相同：

通配符|名称|匹配
---|---|---
`*`|星号|匹配0或多个字符
`?`|问号|匹配单一字符
`[ab]`|字符类别|匹配{a,b}中的一个字符
`[^ab]`|非字符类别|匹配不是{a,b}中的一个字符
`[a-b]`|字符范围|匹配一个在{a,b}范围内的字符(包括ab)，a在字典顺序上要小于或等于b
`[^a-b]`|非字符范围|匹配一个不在{a,b}范围内的字符(包括ab)，a在字典顺序上要小于或等于b
`{a,b}`|或选择|匹配包含a或b中的一个的语句
`\c`|转义字符|匹配元字符c

假设有日志文件存储在按日期分层组织的目录结构中。如此一来，便可以假设 2007 年最后一天的日志文件就会以 `/2007/12/31` 的命名存入目录。假设整个文件列表如下：
```
/2007/12/30  
/2007/12/31  
/2008/01/01  
/2008/01/02
```
以下是一些文件通配符及其扩展：

通配符|扩展
---|---
`/*`|/2007、/2008
`/*/*`|/2007/12、/2008/01
`/*/12/*`|/2007/12/30、/2007/12/31
`/200?`|/2007、/2008
`/200[78]`|/2007、/2008
`/200[7-8]`|/2007、/2008
`/200[^01234569]`|/2007、/2008
`/*/*/{31,01}`|/2007/12/31、/2008/01/01
`/*/*/3{0,1}`|/2007/12/30、/2007/12/31
`/*/{12/31,01/01}`|/2007/12/31、/2008/01/01

### 2.2 示例

通过 put 命令上传数据到 HDFS 中，作为下面 word-count 示例的输入数据源：
```
hadoop fs -put /opt/data/word-count/a.txt /data/word-count/input/2007/12/30/a.txt
hadoop fs -put /opt/data/word-count/b.txt /data/word-count/input/2007/12/31/b.txt
hadoop fs -put /opt/data/word-count/c.txt /data/word-count/input/2008/01/01/c.txt
hadoop fs -put /opt/data/word-count/d.txt /data/word-count/input/2008/01/02/d.txt
```
通过如下 MapReduce 作业输出每年12月31和1月1号文件对应的单词：
```java
public class GlobStatusExample extends Configured implements Tool {
    public static class WordCountMapper extends org.apache.hadoop.mapreduce.Mapper<LongWritable, Text, Text, Text> {
        private Text word = new Text();
        private Text path = new Text();
        @Override
        protected void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
            // 路径
            FileSplit fileSplit = (FileSplit)context.getInputSplit();
            String pathName = fileSplit.getPath().getName();
            path.set(pathName);
            // 单词
            String line = value.toString();
            StringTokenizer itr = new StringTokenizer(line);
            while (itr.hasMoreTokens()) {
                word.set(itr.nextToken());
                context.write(path, word);
            }
        }
    }
    public int run(String[] args) throws Exception {
        String inputPath = "/data/word-count/input/*/{12/31,01/01}";
        String outputPath = "/data/word-count/output/v1";

        Configuration conf = this.getConf();
        Job job = Job.getInstance(conf);

        job.setJobName("GlobStatusExample");
        job.setJarByClass(GlobStatusExample.class);
        // Map 输出 Key 格式
        job.setMapOutputKeyClass(Text.class);
        // Map 输出 Value 格式
        job.setMapOutputValueClass(Text.class);
        // Mapper 类
        job.setMapperClass(WordCountMapper.class);
        // 输入路径 使用文件模式 GlobStatus 过滤
        FileSystem fileSystem = FileSystem.get(conf);
        FileStatus[] fileStatuses = fileSystem.globStatus(new Path(inputPath));
        for (FileStatus status : fileStatuses) {
            Path path = status.getPath();
            FileInputFormat.addInputPath(job, path);
        }
        // 输出路径
        FileOutputFormat.setOutputPath(job, new Path(outputPath));
        boolean success = job.waitForCompletion(true);
        return success ? 0 : 1;
    }

    public static void main(String[] args) throws Exception {
        int result = ToolRunner.run(new Configuration(), new GlobStatusExample(), args);
        System.exit(result);
    }
}
```
具体输出如下结果：
```
b.txt	flink
b.txt	like
b.txt	I
c.txt	spark
c.txt	and
c.txt	hadoop
c.txt	like
c.txt	I
```
> 12月31和1月1号正好对应了 b.txt 和 c.txt 文件

> [GlobStatusExample]()

### 2.2 PathFilter 过滤

通配格式并不是总能够精确地描述我们想要访问的文件集合。比如，使用通配格式排除一个特定的文件就不太可能。FileSystem 中的 listStatus() 和 globStatus() 方法提供了可选的 PathFilter 对象，使我们能够通过编程方式控制通配符：
```java
package org.apache.hadoop.fs;  
public interface PathFilter {  
   boolean accept(Path path);
}
```
PathFilter 与 java.io.FileFilter 一样，是 Path 对象而不是 File 对象。如下展示了一个 PathFilter，用于排除匹配正则表达式的路径：
```java
public class RegexExcludePathFilter implements PathFilter {  
  private final String regex;  
  public RegexExcludePathFilter(String regex) {  
    this.regex = regex;  
  }  
  public boolean accept(Path path) {  
    return !path.toString().matches(regex);  
  }  
}
```
这个过滤器只留下与正则表达式不同的文件。在通配符选出一组要包含的初始文件之后，RegexExcludePathFilter 过滤器再进行一次结果的优化，排除匹配正则表达式的路径。

通过如下 MapReduce 作业输出 2007 年所有文件对应的单词，但是不包含12月31号的单词：
```java
public class PathFilterExample extends Configured implements Tool {
    public static class WordCountMapper extends org.apache.hadoop.mapreduce.Mapper<LongWritable, Text, Text, Text> {
        private Text word = new Text();
        private Text path = new Text();
        @Override
        protected void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
            // 路径
            FileSplit fileSplit = (FileSplit)context.getInputSplit();
            String pathName = fileSplit.getPath().getName();
            path.set(pathName);
            // 单词
            String line = value.toString();
            StringTokenizer itr = new StringTokenizer(line);
            while (itr.hasMoreTokens()) {
                word.set(itr.nextToken());
                context.write(path, word);
            }
        }
    }

    public int run(String[] args) throws Exception {
        String inputPath = "/data/word-count/input/2007/*/*";
        String excludePathRegex = "^.*/2007/12/31$";
        String outputPath = "/data/word-count/output/v1";

        Configuration conf = this.getConf();
        Job job = Job.getInstance(conf);

        job.setJobName("PathFilterExample");
        job.setJarByClass(PathFilterExample.class);
        // Map 输出 Key 格式
        job.setMapOutputKeyClass(Text.class);
        // Map 输出 Value 格式
        job.setMapOutputValueClass(Text.class);
        // Mapper 类
        job.setMapperClass(WordCountMapper.class);
        // 输入路径 使用 PathFilter 过滤
        FileSystem fileSystem = FileSystem.get(conf);
        FileStatus[] fileStatuses = fileSystem.globStatus(
                // 初始路径
                new Path(inputPath),
                // 过滤路径
                new RegexExcludePathFilter(excludePathRegex)
        );
        for (FileStatus status : fileStatuses) {
            Path path = status.getPath();
            FileInputFormat.addInputPath(job, path);
        }
        // 输出路径
        FileOutputFormat.setOutputPath(job, new Path(outputPath));
        boolean success = job.waitForCompletion(true);
        return success ? 0 : 1;
    }

    public static void main(String[] args) throws Exception {
        int result = ToolRunner.run(new Configuration(), new PathFilterExample(), args);
        System.exit(result);
    }

    // 排除满足正则表达式路径过滤器
    private static class RegexExcludePathFilter implements PathFilter {
        private final String regex;
        public RegexExcludePathFilter(String regex) {
            this.regex = regex;
        }
        @Override
        public boolean accept(Path path) {
            return !path.toString().matches(regex);
        }
    }
}
```
核心点在于 globStatus 获取初始化文件后通过 RegexExcludeFilter 过滤器过滤指定的路径：
```java
fs.globStatus(
  new Path("/2007/*/*"),   
  new RegexExcludeFilter("^.*/2007/12/31$")
)
```
