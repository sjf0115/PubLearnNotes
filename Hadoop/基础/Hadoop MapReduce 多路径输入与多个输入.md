
### 1. 多路径输入

FileInputFormat 是所有使用文件作为其数据源的 InputFormat 实现的基类，其中一个重要功能就是指定作业的输入文件位置。因为作业的输入被设定为一组路径，这对限定作业输入提供了很强的灵活性。FileInputFormat 类提供了四种静态方法来指定作业的输入路径：
```java
public static void addInputPath(Job job, Path path);
public static void addInputPaths(Job job, String commaSeparatedPaths);
public static void setInputPaths(Job job, Path... inputPaths);
public static void setInputPaths(Job job, String commaSeparatedPaths);
```
这四种静态方法可以分为两大类：
- addXXX：其中包含 addInputPath 和 addInputPaths 方法，这两个方法可以将一个或者多个路径加入到路径列表中
- setXXX：其中包含 setInputPaths 和 setInputPaths 方法，这两个方法一次性将一个或者多个路径设定为完整的路径列表

#### 1.1 addInputPath

使用 FileInputFormat.addInputPath 方法，一次只能指定一个路径。如果想使用该方法实现多路径输入，需要多次调用来加载不同的路径：
```java
FileInputFormat.addInputPath(job, new Path("click/20160427/"));
FileInputFormat.addInputPath(job, new Path("click/20160428/"));
FileInputFormat.addInputPath(job, new Path("click/20160429/"));
```
#### 1.2 addInputPaths

使用 FileInputFormat.addInputPaths 方法，一次可以指定多个路径。如果想使用该方法实现多路径输入，只需调用一次即可，多个路径字符串之间用逗号分隔开：
```java
FileInputFormat.addInputPaths(job, "click/20160427/,click/20160428/,click/20160429/");
```

#### 1.3 setInputPaths

使用 FileInputFormat.setInputPaths 方法，一次性将一个或者多个路径设定为完整的路径列表，覆盖前面调用设置的所有路径：
```java
FileInputFormat.setInputPaths(job, "click/20160427/,click/20160428/,click/20160429/");
```

### 2. 多个输入

虽然一个 MapReduce 作业的输入可能包含多个输入文件，但所有的文件都是由同一个 InputFormat 和同一个 Mapper 来处理，例如上面指定了多个路径输入。然而，有时候不同输入路径的数据虽然提供相同的数据，但是格式不同，所以必须使用不同的 Mapper 来处理不同输入路径的数据。这个问题可以用 MultipleInputs 类来解决，它允许为每条输入路径指定 InputFormat 和 Mapper，即实现了不同输入路径不同的处理方式。

MultipleInputs 提供了两种静态方法来实现不同输入路径不同处理：
```java
public static void addInputPath(Job job, Path path, Class<? extends InputFormat> inputFormatClass);
public static void addInputPath(Job job, Path path, Class<? extends InputFormat> inputFormatClass, Class<? extends Mapper> mapperClass);
```
上述这两个方法取代了 FileInputFormat.addInputPath 和 Job.setMapperClass 的调用。上述这两个方法的的区别在于针对不同输入路径文件，是否指定了不同 Mapper 进行处理。前者不需要指定 Mapper，所有输入路径都通过同一个 Mapper 进行处理：
```java
MultipleInputs.addInputPath(job, new Path("click/20161129/"), TextInputFormat.class);  
MultipleInputs.addInputPath(job, new Path("click/20161130/"), TextInputFormat.class);  
```
后者可以针对不同输入路径指定不同的 Mapper，即可以指定不同 Mapper 处理不同类型的文件：
```java
MultipleInputs.addInputPath(job, new Path("click/20161129/"), TextInputFormat.class,  ClickMapper.class);  
MultipleInputs.addInputPath(job, new Path("page_view/20161129/"), TextInputFormat.class,  PageViewMapper.class);  
```
由于点击和浏览数据都是文本文件，所以对两者均使用 TextInputFormat 数据类型。但这两个数据源的行格式不同，所以我们使用两个不一样的 Mapper 进行处理。ClickMapper 读取点击输入数据，PageViewMapper 读取浏览输入数据。

### 3. 递归处理

一个被指定为输入路径的目录，其内容不会被递归处理。事实上，这些目录下的内容只会被当作文件处理，如果目录下包含了子目录，也会被解释为文件从而产生错误。处理这个问题的方法是：使用一个文件 glob 或者以过滤器根据命名模式限定选择目录中的文件。另一种方法是将 mapreduce.input.fileinputformat.input.dir.recursive 设置为 true 从而强制对输入目录进行递归处理。

> 来源：《Hadoop 权威指南》
