## 1. 概述

在 ClickHouse 中，groupBitmap 函数用于计算两个位图 Bitmap 的交集，常用于高效地进行复杂的位运算。而在 Hive 中没有内置的等效函数，我们可以通过创建一个用户自定义函数（UDF）来实现 bitmapAnd。这里将详细介绍如何在 Hive 中实现一个类似 bitmapAnd 的 UDF `rbm_bitmap_and`，包括 UDF 的定义、编译、注册以及使用步骤。

## 2. 依赖

开发 Hive UDF 需要引入如下依赖：
```xml
<dependency>
    <groupId>org.apache.hive</groupId>
    <artifactId>hive-exec</artifactId>
    <version>2.3.4</version>
 </dependency>
```
里面定义了各种自定义 UDF 函数的类型：UDF、GenericUDF、GenericUDTF。在本文中使用 GenericUDF 实现自定义 UDF。

除了添加 `hive-exec` 依赖，还需要添加 RoaringBitmap 库的依赖，借助 Roaring64NavigableMap 实现位图 Bitmap 的操作：
```xml
<dependency>
    <groupId>org.roaringbitmap</groupId>
    <artifactId>RoaringBitmap</artifactId>
    <version>0.9.49</version>
</dependency>
```

## 3. 定义 UDF

> UDAF 详细实现细节请查阅：[深入理解 Hive UDAF](https://smartsi.blog.csdn.net/article/details/127964198)。

为了实现位图 Bitmap 函数 `rbm_group_bitmap`，需要实现一个 `RbmGroupBitmapUDAF` UDF 类，该 UDF 接收一个整数列的参数生成结果位图的字节序列：
```java
public class RbmGroupBitmapUDAF extends AbstractGenericUDAFResolver {
    private static String functionName = "rbm_group_bitmap";
    @Override
    public GenericUDAFEvaluator getEvaluator(TypeInfo[] arguments) throws SemanticException {
      ...
    }

    public static class MergeEvaluator extends GenericUDAFEvaluator {
        ...
    }
}
```
该 UDAF 需要实现两个部分：
- 第一部分是创建一个 Resolver 类，在 getEvaluator 方法中实现类型检查以及操作符重载(如果需要的话)，并为给定的一组输入参数类型指定正确的 Evaluator 类。
- 第二部分是创建一个 Evaluator 类，用于实现 UDAF 的具体逻辑。一般实现为一个静态内部类。

### 2.1 Resolver

创建 Resolver 类核心是实现 getEvaluator 方法，在方法中实现参数类型、个数的检查以及操作符重载(如果需要的话)，并为给定的一组输入参数类型指定正确的 Evaluator 类。如果传入方法的参数数量、类型不符合要求，可以抛出一个 UDFArgumentException 异常信息。在 RbmGroupBitmapUDAF 接收一个 Long 或者 Int 类型的参数，聚合生成位图并返回结果位图的字节序列。因此方法中包含三部分，第一部分为参数个数校验必须为1个参数，第二部分为参数类型校验必须为原始类型 Long 或者 Int，第三部分为原始类型 Long 或者 Int 指定对应的 Evaluator 类：
```java
public GenericUDAFEvaluator getEvaluator(TypeInfo[] arguments) throws SemanticException {
    // 参数个数校验
    if (arguments.length != 1) {
        throw new UDFArgumentLengthException("The function '" + functionName + "' only accepts 1 argument, but got " + arguments.length);
    }

    // 参数类型校验
    if (arguments[0].getCategory() != ObjectInspector.Category.PRIMITIVE) {
        throw new UDFArgumentTypeException(0, "Only primitive type arguments are accepted but " + arguments[0].getTypeName() + " is passed.");
    }

    // 为输入参数类型指定对应的 Evaluator 类
    PrimitiveObjectInspector.PrimitiveCategory primitiveCategory = ((PrimitiveTypeInfo) arguments[0]).getPrimitiveCategory();
    if (primitiveCategory == PrimitiveObjectInspector.PrimitiveCategory.LONG || primitiveCategory == PrimitiveObjectInspector.PrimitiveCategory.INT) {
        // 支持 Long 或者 Int 类型的聚合
        return new MergeEvaluator();
    } else {
        throw new UDFArgumentTypeException(0, "Only long or int type arguments are accepted but " + arguments[0].getTypeName() + " is passed.");
    }
}
```


### 2.2 Evaluator

创建一个 Evaluator 类用于实现 UDAF 的具体逻辑，一般实现为一个静态内部类：
```java
public static class MergeEvaluator extends GenericUDAFEvaluator {
    @Override
    public ObjectInspector init(Mode mode, ObjectInspector[] parameters) throws HiveException {
        // 初始化输入和输出参数
    }
    @Override
    public AggregationBuffer getNewAggregationBuffer() throws HiveException {
        // 创建中间结果Buffer
    }
    @Override
    public void reset(AggregationBuffer agg) throws HiveException {
        // 重置中间结果Buffer
    }
    @Override
    public void iterate(AggregationBuffer agg, Object[] parameters) throws HiveException {
        // 迭代输入原始数据
    }
    @Override
    public Object terminatePartial(AggregationBuffer agg) throws HiveException {
        // 输出部分聚合结果
    }
    @Override
    public void merge(AggregationBuffer agg, Object partial) throws HiveException {
        // 合并部分聚合结果
    }
    @Override
    public Object terminate(AggregationBuffer agg) throws HiveException {
        // 输出最终聚合结果
    }
}
```

在该 UDAF `MergeEvaluator` 中实现对输入整数列聚合生成一个位图 Bitmap 的功能。下面详细介绍如何将输入整数列聚合生成一个位图 Bitmap。

### 3.1 BitmapAggBuffer

首先定义一个 BitmapAggBuffer 来存储中间聚合结果，里面包含了一个 Rbm64Bitmap 对象(实现了对 Roaring64NavigableMap 的封装)：
```java
static class BitmapAggBuffer implements AggregationBuffer {
    Rbm64Bitmap bitmap;
    public BitmapAggBuffer () {
        bitmap = new Rbm64Bitmap();
    }
}
```

### 3.2 init

`init` 方法用来初始化 Evaluator 实例：
```java
public ObjectInspector init(Mode mode, ObjectInspector[] parameters) throws HiveException {
    if (parameters.length != 1) {
        throw new UDFArgumentLengthException("The function '" + functionName + "' only accepts 1 argument, but got " + parameters.length);
    }
    super.init(mode, parameters);
    if (mode == Mode.PARTIAL1 || mode == Mode.COMPLETE) {
        this.inputOI = (PrimitiveObjectInspector) parameters[0];
    } else {
        this.outputOI = (BinaryObjectInspector) parameters[0];
    }
    return PrimitiveObjectInspectorFactory.javaByteArrayObjectInspector;
}
```

### 3.3 getNewAggregationBuffer

getNewAggregationBuffer：返回一个用于存储临时聚合结果的对象。

```java
public AggregationBuffer getNewAggregationBuffer() {
    BitmapAggBuffer bitmapAggBuffer = new BitmapAggBuffer();
    reset(bitmapAggBuffer);
    return bitmapAggBuffer;
}
```

### 3.4 reset

```java
public void reset(AggregationBuffer agg) {
    BitmapAggBuffer bitmapAggBuffer = (BitmapAggBuffer)agg;
    bitmapAggBuffer.bitmap = new Rbm64Bitmap();
}
```

### 3.5 iterate

iterate：处理一行新数据到 AggregationBuffer 临时聚合结果中。iterate 方法在 Map 阶段开始被调用。

```java
public void iterate(AggregationBuffer agg, Object[] parameters) {
    Object param = parameters[0];
    if (Objects.equal(param, null)) {
        return;
    }
    BitmapAggBuffer bitmapAggBuffer = (BitmapAggBuffer) agg;
    try {
        Long value = PrimitiveObjectInspectorUtils.getLong(param, inputOI);
        bitmapAggBuffer.bitmap.add(value);
    } catch (NumberFormatException e) {
        e.printStackTrace();
    }
}
```
### 3.6 terminatePartial

terminatePartial：以可持久化的方式返回当前聚合结果。可持久化意味着返回值只能通过 Java 原生类型、数组、原生包装器(例如，Double)、Hadoop Writables、Lists 或者 Map 来构建。不能使用我们自定义的类(即使实现了 java.io.Serializable)，否则可能会得到奇怪的错误或(可能更糟)错误的结果。terminatePartial 方法一般在 Map 或者 Combine 阶段结束时调用。

```java
public Object terminatePartial(AggregationBuffer agg) {
    return terminate(agg);
}
```

### 3.7 merge

`merge` 方法将 `terminatePartial` 返回的部分聚合结果 `partial` 合并到当前聚合结果中 `agg`。`terminatePartial` 返回的部分聚合结果 `partial` 是一个 `BytesWritable` 类型的对象。首先将 `partial` 转换为 `BytesWritable` 类型对象后通过 Rbm64Bitmap.fromBytes 转换为一个 Rbm64Bitmap。最终通过 `or` 或操作合并到 `agg` 临时存储中：
```java
public void merge(AggregationBuffer agg, Object partial) throws HiveException {
    if (Objects.equal(partial, null)){
        return;
    }
    BitmapAggBuffer bitmapAggBuffer = (BitmapAggBuffer)agg;
    try {
        BytesWritable bw = (BytesWritable)partial;
        byte[] bytes = bw.getBytes();
        Rbm64Bitmap bitmap = Rbm64Bitmap.fromBytes(bytes);
        bitmapAggBuffer.bitmap.or(bitmap);
    } catch (IOException e) {
        throw new HiveException(e);
    }
}
```

### 3.8 terminate

`terminate` 将最终聚合结果返回给 Hive。将存储在 `BitmapAggBuffer` 临时存储的 Rbm64Bitmap 转换为字节数组并以 BytesWritable 类型返回：
```java
public Object terminate(AggregationBuffer agg) throws HiveException {
    BitmapAggBuffer bitmapAggBuffer = (BitmapAggBuffer) agg;
    try {
        byte[] bytes = bitmapAggBuffer.bitmap.toBytes();
        return new BytesWritable(bytes);
    } catch (IOException e) {
        throw new HiveException(e);
    }
}
```

> 完整代码请详细查阅：[]()

## 4. 注册

开发完成 UDF 类之后编译和打包你的 `RbmBitmapAndUDF` 类。可以使用 Maven 编译和打包成 JAR 文件。需要注意的是确保包含了所有必要的依赖，特别是 `RoaringBitmap` 库。

有了 JAR 文件之后就可以注册 `rbm_bitmap_and` 函数了。在 Hive 会话中，将这个 Jar 文件加入到类路径下：
```shell
add jar /Users/wy/study/code/data-market/hive-market/target/hive-market-1.0.jar;
```
需要注意的是 JAR 文件路径是不需要用引号括起来，并且这个路径需要是当前文件系统的全路径。Hive 不仅仅将这个 JAR 文件加入到 classpath 下，同时还将其加入到分布式缓存中，这样整个集群的机器都是可以获得该 JAR 文件。

然后使用 `CREATE TEMPORARY FUNCTION` 语句定义好使用这个 Java 类的函数：
```
create temporary function rbm_bitmap_and as 'com.data.market.udf.RbmBitmapAndUDF';
```
需要注意的是 `create temporary function` 语句中的 `temporary` 关键字，当前会话中声明的函数只会在当前会话中有效。因此用户需要在每个会话中都需要添加 Jar 文件然后创建函数。不过如果用户需要频繁的使用同一个 Jar 文件或者函数的话，可以将相关语句增加到 `$HOME/.hiverc` 文件中去。

## 5. 使用

创建完函数之后，就可以像内置函数一样使用了：
```sql
SELECT rbm_bitmap_to_str(
  rbm_bitmap_and(
    rbm_bitmap_from_str("1,2,3,4"),
    rbm_bitmap_from_str("1,3,4,6")
  )
);
```
> rbm_bitmap_from_str 和 rbm_bitmap_to_str 也是我们自定义的 Bitmap UDF 方法。rbm_bitmap_from_str 用来实现将逗号的分割的字符串转换为位图 Bitmap，rbm_bitmap_to_str 用来实现将位图 Bitmap转换为逗号的分割的字符串。

实际效果如下所示：
```
hive (default)> SELECT rbm_bitmap_to_str(
              >   rbm_bitmap_and(
              >     rbm_bitmap_from_str("1,2,3,4"),
              >     rbm_bitmap_from_str("1,3,4,6")
              >   )
              > );
OK
1,3,4
Time taken: 1.099 seconds, Fetched: 1 row(s)
```
