
### 1. 多路径输入

FileInputFormat是所有使用文件作为其数据源的 InputFormat 实现的基类，它的主要作用是指出作业的输入文件位置。因为作业的输入被设定为一组路径， 这对指定作业输入提供了很强的灵活性。FileInputFormat 提供了四种静态方法来设定 Job 的输入路径：
```java
public static void addInputPath(Job job,Path path);
public static void addInputPaths(Job job,String commaSeparatedPaths);
public static void setInputPaths(Job job,Path... inputPaths);
public static void setInputPaths(Job job,String commaSeparatedPaths);
```

#### 1.1 addInputPath

使用FileInputFormat.addInputPath方法，只能指定一个路径。如果想使用该方法实现多路径输入，需要多次调用来加载不同的路径：
```java
FileInputFormat.addInputPath(job, new Path("result/search/train/pv_log/2016-04-27/"));
FileInputFormat.addInputPath(job, new Path("result/search/train/pv_log/2016-04-28/"));
FileInputFormat.addInputPath(job, new Path("result/search/train/pv_log/2016-04-29/"));
```
#### 1.2 addInputPaths

使用FileInputFormat.addInputPaths方法，可以指定多个路径。如果想使用该方法实现多路径输入，只需调用一次即可，多个路径字符串之间用逗号分隔开：
```java
FileInputFormat.addInputPaths(job, "result/search/train/pv_log/2016-04-27/,result/search/train/pv_log/2016-04-28/,result/search/train/pv_log/2016-04-29/");
```
#### 1.3 setInputPaths

setInputPaths()方法一次设定完整的路径列表，替换前面调用中在 Job 上所设置的所有路径（覆盖）：
```java
FileInputFormat.setInputPaths(job, "result/search/train/pv_log/2016-04-27/,result/search/train/pv_log/2016-04-28/,result/search/train/pv_log/2016-04-29/");
```
### 2. 多个输入

虽然一个MapReduce作业的输入可能包含多个输入文件，但所有的文件都由同一个InputFormat和同一个Mapper来处理，例如上面多路径输入。然而，数据格式往往会随着时间而改变，或者，有些数据源会提供相同的数据，但是格式不同，因此我们必须用不同的mapper来处理不同的数据。

这些问题可以用MultipleInputs类来解决，它允许为每条输入路径指定InputFormat 和 Mapper。MultipleInputs提供了两种用于多个输入的方法：
```java
public static void addInputPath(Job job, Path path,Class<? extends InputFormat> inputFormatClass);
public static void addInputPath(Job job, Path path,Class<? extends InputFormat> inputFormatClass,Class<? extends Mapper> mapperClass);
```
下面两个方法的的区别在于针对不同输入路径文件，是否可以指定不同Mapper进行处理。

前者不需要指定Mapper，所以所有文件都通过一个Mapper进行处理：
```java
MultipleInputs.addInputPath(job, new Path("result/search/train/pv_log/2016-11-29/"), TextInputFormat.class);  
MultipleInputs.addInputPath(job, new Path("result/search/train/pv_log/2016-11-29/"), TextInputFormat.class);  
```
后者可以针对不同输入路径指定不同的Mapper，故可以指定不同Mapper处理不同类型的文件：
```java
MultipleInputs.addInputPath(job, new Path("result/search/train/pv_log/2016-11-29/"), TextInputFormat.class,  TrainOrderMap.class);  
MultipleInputs.addInputPath(job, new Path("result/search/flight/log/day=20161129"), TextInputFormat.class,  FlightOrderMap.class);  
```
这段代码取代了FileInputFormat.addInputPath() 和 job.setMapperClass() 的常规调用。由于火车票和机票订单数据都是文本文件，所以对两者使用TextInputFormat的数据类型。但这两个数据源的行格式不同，所以我们使用两个不一样的Mapper。TrainOrderMapper 读取火车票订单的输入数据并计算订单信息，FlightOrderMapper 读取飞机票订单的输入数据并计算订单信息。重要的是两个Mapper 输出类型一样，因此，reducer看到聚合后的map输出，并不知道这些输入是由不同的Mapper产生的。
