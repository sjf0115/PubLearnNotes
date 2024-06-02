

## 1.

在 ClickHouse 中，bitmapAnd 函数用于计算两个位图 Bitmap 的交集，常用于高效地进行复杂的位运算。而在 Hive 中，有内建的等效函数，我们可以通过创建一个用户自定义函数（UDF）来实现 bitmapAnd。

这里将详细介绍如何在 Hive 中实现一个类似 bitmapAnd 的UDF，包括UDF的定义、编写、注册以及使用步骤。

## 2. 定义 UDF

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


核心是实现三个方法 `initialize`、`evaluate` 以及 `getDisplayString` 方法。`getDisplayString` 方法比较简单，用于返回函数及其参数的描述。下面详细说一下 `initialize` 和 `evaluate` 方法的实现细节。

### 2.1 initialize

`initialize` 方法的目标是检查参数类型，个数以及确定参数的返回类型。如果传入方法的类型是不合法的，这时用户同样可以向控制台抛出一个 Exception 异常信息。在 RbmBitmapAndUDF 中需要传入两个位图 Bitmap 参数，并最终返回交集的位图 Bitmap。因此方法中包含三部分，第一部分为参数个数校验必须为两个参数，第二部分为参数类型校验必须为 Binary 类型

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

### 2.2 evaluate

evaluate 方法的输入是一个 DeferredObjec 对象数组。在这个方法中实现我们想要的逻辑，返回与 initialize 方法返回值相符的值。



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
        return bitmap0.toBytes();
    } catch (IOException e) {
        throw new HiveException(e);
    }
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

### 2.3

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
