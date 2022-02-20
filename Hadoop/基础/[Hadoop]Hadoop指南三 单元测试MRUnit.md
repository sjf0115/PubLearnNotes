在MapReduce中，map函数和reduce函数的独立测试是非常方便的，这是由函数风格决定的 。MRUnit是一个测试库，它便于将已知的输入传递给mapper或者检查reducer的输出是否符合预期。MRUnit与标准的执行框架（JUnit）一起使用。
### 1. 设置开发环境

从（https://repository.apache.org/content/repositories/releases/org/apache/mrunit/mrunit/ ）下载最新版本的MRUnit jar，例如如果你使用的hadoop版本为1.0.3，则需要下载

mrunit-x.x.x-incubating-hadoop2.jar。同时还需要下载JUnit最新版本jar。

如果使用Maven方式则使用如下方式：
```
<junit.version>4.12</junit.version>
<mrunit.version>1.1.0</mrunit.version>
<!-- junit -->
<dependency>
    <groupId>junit</groupId>
    <artifactId>junit</artifactId>
    <version>${junit.version}</version>
    <scope>test</scope>
</dependency>
<!-- mrunit -->
<dependency>
   <groupId>org.apache.mrunit</groupId>
   <artifactId>mrunit</artifactId>
   <version>${mrunit.version}</version>
   <classifier>hadoop2</classifier>
   <scope>test</scope>
</dependency>
```
**备注**：

如果你使用的是hadoop 2.x版本，classifier设置为hadoop2

### 2. MRUnit 测试用例

MRUnit测试框架基于Junit，可以测试hadoop版本为0.20，0.23.x，1.0.x，2.x的map reduce程序。

下面是一个使用MRUnit对统计一年最高气温的Map Reduce程序进行单元测试。

测试数据如下：

```
0096007026999992016062218244+00000+000000FM-15+702699999V0209999C000019999999N999999999+03401+01801999999ADDMA1101731999999REMMET069MOBOB0 METAR 7026 //008 000000 221824Z AUTO 00000KT //// 34/18 A3004=
```
这只有一天的数据，气温是340，Mapper输出为该天气温340

下面是相应的Mapper和Reducer：

MaxTemperatureMapper：

```
package com.sjf.open.maxTemperature;
import java.io.IOException;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;
import com.google.common.base.Objects;
/**
 * Created by xiaosi on 16-7-27.
 */
public class MaxTemperatureMapper extends Mapper<LongWritable, Text, Text, IntWritable> {
    private static final int MISSING = 9999;
    public void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
        String line = value.toString();
        // 年份
        String year = line.substring(15, 19);
        // 温度
        int airTemperature;
        if(Objects.equal(line.charAt(87),"+")){
            airTemperature = Integer.parseInt(line.substring(88,92));
        }
        else{
            airTemperature = Integer.parseInt(line.substring(87,92));
        }
        // 空气质量
        String quality = line.substring(92, 93);
        if(!Objects.equal(airTemperature, MISSING) && quality.matches("[01459]")){
            context.write(new Text(year), new IntWritable(airTemperature));
        }
    }
}
```
MaxTemperatureReducer：
```
package com.sjf.open.maxTemperature;
import java.io.IOException;
import java.util.Iterator;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Reducer;
/**
 * Created by xiaosi on 16-7-27.
 */
public class MaxTemperatureReducer extends Reducer<Text, IntWritable, Text, IntWritable> {
    @Override
    protected void reduce(Text key, Iterable<IntWritable> values, Context context) throws IOException, InterruptedException {
        // 一年最高气温
        int maxValue = Integer.MIN_VALUE;
        for(IntWritable value : values){
            maxValue = Math.max(maxValue, value.get());
        }//for
        // 输出
        context.write(key, new IntWritable(maxValue));
    }
}
```
下面是MRUnit测试类：
```
package com.sjf.open.maxTemperature;
import com.google.common.collect.Lists;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mrunit.mapreduce.MapDriver;
import org.apache.hadoop.mrunit.mapreduce.MapReduceDriver;
import org.apache.hadoop.mrunit.mapreduce.ReduceDriver;
import org.apache.hadoop.mrunit.types.Pair;
import org.junit.Before;
import org.junit.Test;
import java.io.IOException;
import java.util.List;
/**
 * Created by xiaosi on 16-12-8.
 */
public class MaxTemperatureTest {
    private MapDriver mapDriver;
    private ReduceDriver reduceDriver;
    private MapReduceDriver mapReduceDriver;
    @Before
    public void setUp(){
        MaxTemperatureMapper mapper = new MaxTemperatureMapper();
        mapDriver = MapDriver.newMapDriver(mapper);
        MaxTemperatureReducer reducer = new MaxTemperatureReducer();
        reduceDriver = ReduceDriver.newReduceDriver();
        reduceDriver.withReducer(reducer);
        mapReduceDriver = MapReduceDriver.newMapReduceDriver(mapper, reducer);
    }
    @Test
    public void testMapper() throws IOException {
        Text text = new Text("0096007026999992016062218244+00000+000000FM-15+702699999V0209999C000019999999N999999999+03401+01801999999ADDMA1101731999999REMMET069MOBOB0 METAR 7026 //008 000000 221824Z AUTO 00000KT //// 34/18 A3004=");
        mapDriver.withInput(new LongWritable(), text);
        mapDriver.withOutput(new Text("2016"), new IntWritable(340));
        mapDriver.runTest();
        // 输出
        List<Pair> expectedOutputList = mapDriver.getExpectedOutputs();
        for(Pair pair : expectedOutputList){
            System.out.println(pair.getFirst() + " --- " + pair.getSecond()); // 2016 --- 340
        }
    }
    @Test
    public void testReducer() throws IOException {
        List<IntWritable> IntWritableList = Lists.newArrayList();
        IntWritableList.add(new IntWritable(340));
        IntWritableList.add(new IntWritable(240));
        IntWritableList.add(new IntWritable(320));
        IntWritableList.add(new IntWritable(330));
        IntWritableList.add(new IntWritable(310));
        reduceDriver.withInput(new Text("2016"), IntWritableList);
        reduceDriver.withOutput(new Text("2016"), new IntWritable(340));
        reduceDriver.runTest();
        // 输出
        List<Pair> expectedOutputList = reduceDriver.getExpectedOutputs();
        for(Pair pair : expectedOutputList){
            System.out.println(pair.getFirst() + " --- " + pair.getSecond());
        }
    }
    @Test
    public void testMapperAndReducer() throws IOException {
        Text text = new Text("0089010010999992014010114004+70933-008667FM-12+000999999V0201201N006019999999N999999999+00121-00361100681ADDMA1999990100561MD1810171+9990REMSYN04801001 46/// /1206 10012 21036 30056 40068 58017=");
        mapReduceDriver.withInput(new LongWritable(), text);
        mapReduceDriver.withOutput(new Text("2014"), new IntWritable(12));
        mapReduceDriver.runTest();
        // 输出
        List<Pair> expectedOutputList = mapReduceDriver.getExpectedOutputs();
        for(Pair pair : expectedOutputList){
            System.out.println(pair.getFirst() + " --- " + pair.getSecond()); // 2014 --- 12
        }
    }
}
```
如果测试的是Mapper，使用MRUnit的MapDiver，如果测试Reducer，使用ReduceDriver，如果测试整个MapReduce程序，则需要使用MapReduceDriver。在调用runTest()方法之前，需要配置mapper（或者Reducer），输入值，期望的输出key，期望的输出值等。如果与期望的输出值不匹配，MRUnit测试失败。根据withOutput()被调用的次数，MapDiver（ReduceDriver，MapReduceDriver）能来检查0，1,或者多个输出记录。

**备注**：

注意 MapDriver，ReduceDriver，MapReduceDriver 引入的jar包版本：

```
import org.apache.hadoop.mrunit.mapreduce.MapDriver;
import org.apache.hadoop.mrunit.mapreduce.MapReduceDriver;
import org.apache.hadoop.mrunit.mapreduce.ReduceDriver;
```
而不是：
```
import org.apache.hadoop.mrunit.MapDriver;
import org.apache.hadoop.mrunit.MapReduceDriver;
import org.apache.hadoop.mrunit.ReduceDriver;
```
这分别对应Hadoop新老版本API，第一类对应新版本的Mapper和Reducer：
```
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
```
第二类对应老版本的Mapper和Reducer：

```
import org.apache.hadoop.mapred.Mapper;
import org.apache.hadoop.mapred.Reducer;
```

参考：https://cwiki.apache.org/confluence/display/MRUNIT/MRUnit+Tutorial

数据来源：ftp://ftp.ncdc.noaa.gov/pub/data/noaa





