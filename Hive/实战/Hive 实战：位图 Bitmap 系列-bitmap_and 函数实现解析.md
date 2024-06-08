## 1. 概述

在 ClickHouse 中，bitmapAnd 函数用于计算两个位图 Bitmap 的交集，常用于高效地进行复杂的位运算。而在 Hive 中没有内置的等效函数，我们可以通过创建一个用户自定义函数（UDF）来实现 bitmapAnd。这里将详细介绍如何在 Hive 中实现一个类似 bitmapAnd 的 UDF `rbm_bitmap_and`，包括 UDF 的定义、编译、注册以及使用步骤。

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

> UDF 详细实现细节请查阅：[Hive 如何实现自定义函数 UDF](https://smartsi.blog.csdn.net/article/details/126211216)。

为了实现位图 Bitmap 函数 `rbm_bitmap_and`，需要实现一个 `RbmBitmapAndUDF` UDF 类，该 UDF 接收两个 BytesWritable 类型的参数——代表两个位图 Bitmap 的字节序列，执行逻辑与操作后，返回结果位图的字节序列：
```java
@Description(name = "rbm_bitmap_and", value = "_FUNC_(bitmap1, bitmap2) - Returns the and of two bitmaps")
public class RbmBitmapAndUDF extends GenericUDF {
    private static String functionName = "rbm_bitmap_and";

    public ObjectInspector initialize(ObjectInspector[] arguments) throws UDFArgumentException {
        ...
    }

    public Object evaluate(DeferredObject[] deferredObjects) throws HiveException {
        ...
    }

    public String getDisplayString(String[] children) {
        ...
    }
}
```
该 UDF 核心是实现 `initialize`、`evaluate` 以及 `getDisplayString` 三个方法。接下来，详细介绍三个方法的实现细节。

### 3.1 getDisplayString

`getDisplayString` 方法比较简单，用于返回函数及其参数的描述，当需要在 Hive 的日志或错误消息中显示关于此 UDF 的信息时，此方法提供了一个字符串表示。通常，该字符串会包含 UDF 名称和其接收的参数：
```java
public String getDisplayString(String[] children) {
    // 这里返回函数及其参数的描述
    return functionName + "(bitmap, bitmap)";
}
```

### 3.2 initialize

`initialize` 方法的目标是检查参数类型，个数以及确定参数的返回类型。如果传入方法的参数数量、类型不符合要求，可以抛出一个 UDFArgumentException 异常信息。RbmBitmapAndUDF 接收两个 BytesWritable 类型的参数——代表两个位图 Bitmap 的字节序列，执行逻辑与操作后，返回结果位图的字节序列。因此方法中包含三部分，第一部分为参数个数校验必须为两个参数，第二部分为参数类型校验必须为 Binary 类型，第三部分返回正确的 ObjectInspector 实例 `writableBinaryObjectInspector`：
```java
public ObjectInspector initialize(ObjectInspector[] arguments) throws UDFArgumentException {
    // 参数个数校验
    if (arguments.length != 2) {
        throw new UDFArgumentLengthException("The function '" + functionName + "' only accepts 2 argument, but got " + arguments.length);
    }

    // 参数类型校验
    for (int i = 0; i < arguments.length; i++) {
        if (!(arguments[i] instanceof WritableBinaryObjectInspector)) {
            throw new UDFArgumentException(functionName + " expects binary type for argument " + (i + 1));
        }
    }

    // 返回值类型
    return PrimitiveObjectInspectorFactory.writableBinaryObjectInspector;
}
```
下面详细说一下 UDF 返回值类型，在 Hive UDF 中，函数目的是处理或生成 Bitmap 数据（通常以字节流形式存在），那么返回类型应该是与二进制数据处理相关的 ObjectInspector。对于处理 Bitmap 这类二进制数据，建议你使用 `WritableBinaryObjectInspector` 作为输出的 ObjectInspector，因为 Hive 在内部处理数据时倾向于使用 Hadoop 的 Writable 接口来提高序列化和反序列化的效率，尤其是当数据需要跨网络传输或写入文件时。`javaByteArrayObjectInspector` 是与 Java 原生的 `byte[]` 数组类型对应的 ObjectInspector。尽管在某些场景下也能用作二进制数据的处理，但它不如 `WritableBinaryObjectInspector` 高效，尤其是在需要进行序列化操作时。考虑到 Bitmap 数据处理的效率和 Hive 的内部机制，推荐使用 `WritableBinaryObjectInspector` 作为返回类型。

### 3.3 evaluate

`evaluate` 方法包含了 UDF 的核心逻辑，在这个方法中实现我们想要的逻辑，并每次调用 UDF 时都会执行此方法。使用 `DeferredObject.get()` 方法获取实际参数值，并根据 initialize 方法中定义的参数类型进行相应的类型转换。需要注意的是返回的对象类型应与 `initialize` 方法中定义的返回类型一致。下面代码中通过 Rbm64Bitmap 类将字节数组转换为 Rbm64Bitmap，再借助 and 方法实现逻辑与操作，最终返回一个 BytesWritable 类型位图：
```java
public Object evaluate(DeferredObject[] deferredObjects) throws HiveException {
    if (deferredObjects[0].get() == null || deferredObjects[1].get() == null) {
        return null;
    }

    BytesWritable bw0 = (BytesWritable)(deferredObjects[0].get());
    BytesWritable bw1 = (BytesWritable)(deferredObjects[1].get());
    byte[] bytes0 = bw0.getBytes();
    byte[] bytes1 = bw1.getBytes();

    try {
        Rbm64Bitmap bitmap0 = Rbm64Bitmap.fromBytes(bytes0);
        Rbm64Bitmap bitmap1 = Rbm64Bitmap.fromBytes(bytes1);
        bitmap0.and(bitmap1);
        return new BytesWritable(bitmap0.toBytes());
    } catch (IOException e) {
        throw new HiveException(e);
    }
}
```

> Rbm64Bitmap 是一个对 Roaring64NavigableMap 封装的工具类，详细请查阅源代码[Rbm64Bitmap](https://github.com/sjf0115/data-market/blob/main/common-market/src/main/java/com/data/market/market/function/Rbm64Bitmap.java)

上面 `initialize` 方法选择 `WritableBinaryObjectInspector` 作为返回类型，所以在这需要确保 `evaluate` 方法返回的是一个 `BytesWritable` 对象，因为这是与 `WritableBinaryObjectInspector` 配套使用的 Hadoop Writable 类型，适合存储和传输二进制数据。
```java
@Override
public Object evaluate(DeferredObject[] arguments) throws HiveException {
    // 计算逻辑
    byte[] bitmapData = ...; // 假设这是你的Bitmap数据
    return new BytesWritable(bitmapData);
}
```

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
