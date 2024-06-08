

## 1.

在 ClickHouse 中，bitmapAnd 函数用于计算两个位图 Bitmap 的交集，常用于高效地进行复杂的位运算。而在 Hive 中，有内建的等效函数，我们可以通过创建一个用户自定义函数（UDF）来实现 bitmapAnd。

这里将详细介绍如何在 Hive 中实现一个类似 bitmapAnd 的UDF，包括UDF的定义、编写、注册以及使用步骤。

Apache Hive是一个数据仓库系统，用于存储、查询和分析存储在Hadoop中的大数据。对于复杂的数据处理，Hive提供了用户定义函数（UDF）的功能。本文将指导你如何在Hive中实现一个类似于ClickHouse中bitmap_and函数的UDF，用于对两个位图(bitmap)执行逻辑与(AND)操作。

ClickHouse的bitmap_and函数主要用于处理位图索引，返回两个位图的交集，这在进行复杂查询时非常有用。在Hive中，虽然没有内置的位图处理函数，但我们可以通过创建自定义函数来实现类似的功能。





initialize(ObjectInspector[] arguments)
在我们实现的bitmap_and函数中，该方法首先检查确保UDF接收了两个参数。然后，返回值类型被设定为PrimitiveObjectInspectorFactory.writableBinaryObjectInspector，说明此UDF返回的是一个二进制的Writable对象。

evaluate(DeferredObject[] arguments)
这是UDF逻辑执行的核心。在bitmap_and的实现中，它首先从arguments数组中获取两个参数。
使用RoaringBitmap库，反序列化得到两个MutableRoaringBitmap对象。
调用and方法来计算两个位图的交集。
将计算结果序列化回字节数组，并包装成BytesWritable对象返回。



## 2. 定义 UDF

BitmapAndGenericUDF类实现解析
接下来，具体解析BitmapAndGenericUDF类实现细节：

### 2.1 RbmBitmapAndUDF

首先我们创建一个名为 RbmBitmapAndUDF 的 UDF，其功能是计算两个位图 Bitmap 的交集，返回一个新的位图 Bitmap。UDF 详细实现细节请查阅：[Hive 如何实现自定义函数 UDF](https://smartsi.blog.csdn.net/article/details/126211216)。在这继承一个 GenericUDF 实现位图 Bitmap 交集的 RbmBitmapAndUDF：
```java
public class RbmBitmapAndUDF extends GenericUDF {
    private static String functionName = "rbm_bitmap_and";
    private transient BinaryObjectInspector inspector0;
    private transient BinaryObjectInspector inspector1;

    public ObjectInspector initialize(ObjectInspector[] arguments) throws UDFArgumentException {
        ...
    }

    public Object evaluate(DeferredObject[] deferredObjects) throws HiveException {
        ...
    }

    public String getDisplayString(String[] children) {
        // 这里返回函数及其参数的描述
        return functionName + "(bitmap, bitmap)";
    }
}
```

核心是实现三个方法 `initialize`、`evaluate` 以及 `getDisplayString` 方法。`getDisplayString` 方法比较简单，用于返回函数及其参数的描述，当需要在 Hive 的日志或错误消息中显示关于此 UDF 的信息时，此方法提供了一个字符串表示。通常，该字符串会包含 UDF 名称和其接收的参数。下面详细说一下 `initialize` 和 `evaluate` 方法的实现细节。

### 2.1 initialize

`initialize` 方法的目标是检查参数类型，个数以及确定参数的返回类型。如果传入方法的参数数量、类型不符合要求，可以抛出一个 UDFArgumentException 异常信息。在 RbmBitmapAndUDF 接收两个 BytesWritable 类型的参数——代表两个位图 Bitmap 的字节序列，执行逻辑与操作后，返回结果位图的字节序列。因此方法中包含三部分，第一部分为参数个数校验必须为两个参数，第二部分为参数类型校验必须为 Binary 类型，第三部分返回正确的 ObjectInspector 实例：
```java
public ObjectInspector initialize(ObjectInspector[] arguments) throws UDFArgumentException {
    // 参数个数校验
    if (arguments.length != 2) {
        throw new UDFArgumentLengthException("The function '" + functionName + "' only accepts 2 argument, but got " + arguments.length);
    }

    // 参数类型校验
    ObjectInspector arg0 = arguments[0];
    ObjectInspector arg1 = arguments[1];
    if (!(arg0 instanceof BinaryObjectInspector) || !(arg1 instanceof BinaryObjectInspector)) {
        throw new UDFArgumentException("Argument of '" + functionName + "' should be binary type");
    }
    this.inspector0 = (BinaryObjectInspector) arg0;
    this.inspector1 = (BinaryObjectInspector) arg1;

    // 返回值类型
    return PrimitiveObjectInspectorFactory.javaByteArrayObjectInspector;
}
```
下面详细说一下 UDF 返回值类型，在 Hive UDF 中，函数目的是处理或生成 Bitmap 数据（通常以字节流形式存在），那么返回类型应该是与二进制数据处理相关的 ObjectInspector。对于处理 Bitmap 这类二进制数据，建议你使用 `WritableBinaryObjectInspector` 作为输出的 ObjectInspector，因为 Hive 在内部处理数据时倾向于使用 Hadoop 的 Writable 接口来提高序列化和反序列化的效率，尤其是当数据需要跨网络传输或写入文件时。`javaByteArrayObjectInspector` 是与 Java 原生的 `byte[]` 数组类型对应的 ObjectInspector。尽管在某些场景下也能用作二进制数据的处理，但它不如 `WritableBinaryObjectInspector` 高效，尤其是在需要进行序列化操作时。考虑到 Bitmap 数据处理的效率和 Hive 的内部机制，推荐使用 WritableBinaryObjectInspector 作为返回类型。

### 2.2 evaluate

`evaluate` 方法包含了 UDF 的核心逻辑，在这个方法中实现我们想要的逻辑，并每次调用 UDF 时都会执行此方法。使用 `DeferredObject.get()` 方法获取实际参数值。并根据 initialize 方法中定义的参数类型进行相应的类型转换。需要注意的是返回的对象类型应与 `initialize` 方法中定义的返回类型一致。在 RbmBitmapAndUDF 中接收两个 BytesWritable 类型的参数——代表两个位图 Bitmap 的字节序列，执行逻辑与操作后，返回结果位图的字节序列。下面代码中通过 Rbm64Bitmap 类将字节数组转换为 Rbm64Bitmap，再借助 and 方法实现逻辑与操作，最终返回一个 BytesWritable 类型位图：
```java
public Object evaluate(DeferredObject[] deferredObjects) throws HiveException {
    if (deferredObjects[0].get() == null || deferredObjects[1].get() == null) {
        return null;
    }

    byte[] bytes0 = PrimitiveObjectInspectorUtils.getBinary(deferredObjects[0].get(), this.inspector0).getBytes();
    byte[] bytes1 = PrimitiveObjectInspectorUtils.getBinary(deferredObjects[1].get(), this.inspector1).getBytes();

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

上面 initialize 方法选择 `WritableBinaryObjectInspector` 作为返回类型，所以在这需要确保 evaluate 方法返回的是一个 BytesWritable 对象，因为这是与 `WritableBinaryObjectInspector` 配套使用的 Hadoop Writable 类型，适合存储和传输二进制数据。
```java
@Override
public Object evaluate(DeferredObject[] arguments) throws HiveException {
    // 计算逻辑
    byte[] bitmapData = ...; // 假设这是你的Bitmap数据
    return new BytesWritable(bitmapData);
}
```

### 2.2 RbmGroupBitmapUDAF


```java
public class RbmGroupBitmapUDAF extends AbstractGenericUDAFResolver {
    private static String functionName = "rbm_group_bitmap";
    @Override
    public GenericUDAFEvaluator getEvaluator(TypeInfo[] arguments) throws SemanticException {
        // 参数个数校验
        if (arguments.length != 1) {
            throw new UDFArgumentLengthException("The function '" + functionName + "' only accepts 1 argument, but got " + arguments.length);
        }

        // 参数类型校验
        if (arguments[0].getCategory() != ObjectInspector.Category.PRIMITIVE) {
            throw new UDFArgumentTypeException(0, "Only primitive type arguments are accepted but " + arguments[0].getTypeName() + " is passed.");
        }
        PrimitiveObjectInspector.PrimitiveCategory primitiveCategory = ((PrimitiveTypeInfo) arguments[0]).getPrimitiveCategory();
        if (primitiveCategory == PrimitiveObjectInspector.PrimitiveCategory.LONG || primitiveCategory == PrimitiveObjectInspector.PrimitiveCategory.INT) {
            // 支持 Long 或者 Int 类型的聚合
            return new MergeEvaluator();
        } else {
            throw new UDFArgumentTypeException(0, "Only long or int type arguments are accepted but " + arguments[0].getTypeName() + " is passed.");
        }
    }

    public static class MergeEvaluator extends GenericUDAFEvaluator {
        private PrimitiveObjectInspector inputOI;
        private BinaryObjectInspector outputOI;

        static class BitmapAggBuffer implements AggregationBuffer {
            boolean empty;
            Rbm64Bitmap bitmap;
            public BitmapAggBuffer () {
                bitmap = new Rbm64Bitmap();
            }
        }

        // 返回类型。这里定义返回类型为 Binary
        @Override
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

        // 创建新的聚合计算需要的内存，用来存储 Mapper, Combiner, Reducer 运算过程中的聚合。
        @Override
        public AggregationBuffer getNewAggregationBuffer() {
            BitmapAggBuffer bitmapAggBuffer = new BitmapAggBuffer();
            reset(bitmapAggBuffer);
            return bitmapAggBuffer;
        }

        @Override
        public void reset(AggregationBuffer agg) {
            BitmapAggBuffer bitmapAggBuffer = (BitmapAggBuffer)agg;
            bitmapAggBuffer.bitmap = new Rbm64Bitmap();
        }

        // Map阶段：遍历输入参数
        @Override
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

        // Mapper,Combiner 结束要返回的结果
        @Override
        public Object terminatePartial(AggregationBuffer agg) {
            return terminate(agg);
        }

        // 合并: Combiner 合并 Mapper 返回的结果, Reducer 合并 Mapper 或 Combiner 返回的结果
        @Override
        public void merge(AggregationBuffer agg, Object partial) {
            if (Objects.equal(partial, null)){
                return;
            }
            BitmapAggBuffer bitmapAggBuffer = (BitmapAggBuffer)agg;
            try {
                byte[] bytes = PrimitiveObjectInspectorUtils.getBinary(partial, outputOI).getBytes();
                Rbm64Bitmap bitmap = Rbm64Bitmap.fromBytes(bytes);
                bitmapAggBuffer.bitmap.or(bitmap);
            } catch (IOException e) {
                e.printStackTrace();
            }
        }

        // 输出最终聚合结果
        @Override
        public Object terminate(AggregationBuffer agg) {
            BitmapAggBuffer bitmapAggBuffer = (BitmapAggBuffer) agg;
            byte[] bytes = null;
            try {
                bytes = bitmapAggBuffer.bitmap.toBytes();
            } catch (IOException e) {
                e.printStackTrace();
            }
            return bytes;
        }
    }
}
```

### 2.3 编译

第二步：编译和打包你的GenericUDF类
将上面的Java代码保存，并使用Maven或你选择的任何Java构建工具编译和打包成JAR文件。确保你包含了所有必要的依赖，特别是RoaringBitmap库。

### 2.4 注册

第三步：在Hive中注册和使用GenericUDF
将编译的JAR文件上传到你的Hadoop集群中可以被Hive访问的路径。
在Hive会话中添加你的JAR，并创建一个函数指向你的GenericUDF:
ADD JAR path_to_your_jar_file.jar;
CREATE TEMPORARY FUNCTION bitmap_and AS 'your.package.BitmapAndGenericUDF';
使用UDF进行查询：
SELECT bitmap_and(bitmap_column1, bitmap_column2) FROM your_table;
这将对指定表中的两个位图列执行逻辑与操作，并返回它们的交集。



```sql
hive --service metastore -p 9083 &

add jar /Users/wy/study/code/data-market/hive-market/target/hive-market-1.0.jar;

create temporary function rbm_bitmap_from_str as 'com.data.market.udf.RbmBitmapFromStringUDF';
create temporary function rbm_bitmap_from_str as 'com.data.market.udf.RbmBitmapFromStringUDF';
create temporary function rbm_bitmap_from_str as 'com.data.market.udf.RbmBitmapFromStringUDF';
create temporary function rbm_bitmap_from_str as 'com.data.market.udf.RbmBitmapFromStringUDF';



SELECT rbm_bitmap_from_str("1,2,3,4");


SELECT rbm_bitmap_contains(rbm_bitmap_from_str("1,2,3,4"), 4L);
```
