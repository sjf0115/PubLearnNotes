当Hive提供的内置函数无法满足你的业务处理需要时，此时就可以考虑使用用户自定义函数

用户自定义函数（user defined function)，针对单条记录。

编写一个UDF，需要继承UDF类，并实现evaluate()函数。在查询执行过程中，查询中对应的每个应用到这个函数的地方都会对这个类进行实例化。对于每行输入都会调用到evaluate()函数。而evaluate()函数处理的值会返回给Hive。同时用户是可以重载evaluate方法的。Hive会像Java的方法重载一样，自动选择匹配的方法。

### 1. 简单UDF

#### 1.1 自定义Java类

下面自定义一个Java类OperationAddUDF，实现了Int，Double，Float以及String类型的加法操作。
```java
package com.sjf.open.hive.udf;
import org.apache.hadoop.hive.ql.exec.UDF;
import org.apache.hadoop.hive.serde2.ByteStream;
import org.apache.hadoop.hive.serde2.io.DoubleWritable;
import org.apache.hadoop.hive.serde2.lazy.LazyInteger;
import org.apache.hadoop.io.FloatWritable;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
/**
 * Created by xiaosi on 16-11-19.
 */
public class OperationAddUDF extends UDF {
    private final ByteStream.Output out = new ByteStream.Output();
    /**
     * IntWritable
     * @param num1
     * @param num2
     * @return
     */
    public IntWritable evaluate(IntWritable num1, IntWritable num2){
        if(num1 == null || num2 == null){
            return null;
        }
        return new IntWritable(num1.get() + num2.get());
    }
    /**
     * DoubleWritable
     * @param num1
     * @param num2
     * @return
     */
    public DoubleWritable evaluate(DoubleWritable num1, DoubleWritable num2){
        if(num1 == null || num2 == null){
            return null;
        }
        return new DoubleWritable(num1.get() + num2.get());
    }
    /**
     * FloatWritable
     * @param num1
     * @param num2
     * @return
     */
    public FloatWritable evaluate(FloatWritable num1, FloatWritable num2){
        if(num1 == null || num2 == null){
            return null;
        }
        return new FloatWritable(num1.get() + num2.get());
    }
    /**
     * Text
     * @param num1
     * @param num2
     * @return
     */
    public Text evaluate(Text num1, Text num2){
        if(num1 == null || num2 == null){
            return null;
        }
        try{
            Integer n1 = Integer.valueOf(num1.toString());
            Integer n2 = Integer.valueOf(num2.toString());
            Integer result = n1 + n2;
            out.reset();
            LazyInteger.writeUTF8NoException(out, result);
            Text text = new Text();
            text.set(out.getData(), 0, out.getLength());
            return text;
        }
        catch (Exception e){
            return null;
        }
    }
}
```
UDF中`evaluate()`函数的参数和返回值类型只能是Hive可以序列化的数据类型。例如，如果用户处理的全是数值，那么UDF的输出参数类型可以是基本数据类型int，Integer封装的对象或者是一个IntWritable对象，也就是Hadoop对整型封装后的对象。用户不需要特别的关心将调用到哪个类型，因为当类型不一致的时候，Hive会自动将数据类型转换成匹配的类型。null值在Hive中对于任何数据类型都是合法的，但是对于Java基本数据类型，不能是对象，也不能是null。

#### 1.2 Hive中使用

如果想在Hive中使用UDF，那么需要将Java代码进行编译，然后将编译后的UDF二进制类文件打包成一个Jar文件。然后，在Hive会话中，将这个Jar文件加入到类路径下，在通过CREATE FUNCTION 语句定义好使用这个Java类的函数：

##### 1.2.1 添加Jar文件到类路径下
```
hive (test)> add jar /home/xiaosi/open-hive-1.0-SNAPSHOT.jar;
Added [/home/xiaosi/open-hive-1.0-SNAPSHOT.jar] to class path
Added resources: [/home/xiaosi/open-hive-1.0-SNAPSHOT.jar]
```
需要注意的是，Jar文件路径是不需要用引号括起来的，同时，到目前为止这个路径需要是当前文件系统的全路径。Hive不仅仅将这个Jar文件加入到classpath下，同时还将其加入到分布式缓存中，这样整个集群的机器都是可以获得该Jar文件的。

##### 1.2.2 创建函数add
```
hive (test)> create temporary function add as 'com.sjf.open.hive.udf.OperationAddUDF';
OK
Time taken: 0.004 seconds
```
注意的是create temporary function语句中的temporary关键字，当前会话中声明的函数只会在当前会话中有效。因此用户需要在每个会话中都增加Jar文件然后创建函数。不过如果用户需要频繁的使用同一个Jar文件和函数的话，那么可以将相关语句增加到$HOME/.hiverc文件中去。

##### 1.2.3 使用

现在这个数值相加函数可以像其他的函数一样使用了。
```
hive (test)> select add(12, 34) from employee_part;
OK
46
Time taken: 0.078 seconds, Fetched: 1 row(s)
hive (test)> select add(12.3, 20.1) from employee_part;
OK
32.400000000000006
Time taken: 0.098 seconds, Fetched: 1 row(s)
hive (test)> select add("12", "45") from employee_part;
OK
57
Time taken: 0.077 seconds, Fetched: 1 row(s)
```
##### 1.2.4 删除UDF

当我们使用完自定义UDF后，我们可以通过如下命令删除此函数：
```
hive (test)> drop temporary function if exists add;
```
### 2. 复杂UDF

#### 2.1 GenericUDF

和UDF相比，GenericUDF（org.apache.hadoop.hive.ql.udf.generic.GenericUDF）支持复杂类型（比如List，struct，map等）的输入和输出。GenericUDF可以让我们通过ObjectInspector来管理方法的参数，检查接收参数的类型和数量。

GenericUDF要求实现一下三个方法：
```
// this is like the evaluate method of the simple API. It takes the actual arguments and returns the result
abstract Object evaluate(GenericUDF.DeferredObject[] arguments);
// Doesn't really matter, we can return anything, but should be a string representation of the function.
abstract String getDisplayString(String[] children);
// called once, before any evaluate() calls. You receive an array of object inspectors that represent the arguments of the function
// this is where you validate that the function is receiving the correct argument types, and the correct number of arguments.
abstract ObjectInspector initialize(ObjectInspector[] arguments);
```
`initialize`方法会被输入的每个参数调用，并最终传入到一个ObjectInspector对象中。这个方法的目标是检查参数类型，个数以及确定参数的返回类型。如果传入方法的类型是不合法的，这时用户同样可以向控制台抛出一个Exception异常信息。

`evaluate`方法的输入是一个DeferredObjec对象数组。在这个方法中实现我们想要的逻辑，返回与initialize方法返回值相符的值。

`getDisplayString`方法用于Hadoop task内部，在使用到这个函数时来展示调试信息（还不太明白）。


#### 2.2 Example

我们想要在Hive实现一个strContain方法，需要两个参数，一个是包含字符串的列表（list<String>），另一个是待寻找的字符串（String）。如果列表中包含我们提供的字符串，返回tue，否则返回false。功能如下所示：
```
strContain(List("a", "b", "c"), "b"); // true
strContain(List("a", "b", "c"), "d"); // false
```
#### 2.3 代码
```java
package com.sjf.open.hive.udf;
import org.apache.hadoop.hive.ql.exec.Description;
import org.apache.hadoop.hive.ql.exec.UDFArgumentException;
import org.apache.hadoop.hive.ql.exec.UDFArgumentLengthException;
import org.apache.hadoop.hive.ql.metadata.HiveException;
import org.apache.hadoop.hive.ql.udf.generic.GenericUDF;
import org.apache.hadoop.hive.serde2.lazy.LazyString;
import org.apache.hadoop.hive.serde2.objectinspector.ListObjectInspector;
import org.apache.hadoop.hive.serde2.objectinspector.ObjectInspector;
import org.apache.hadoop.hive.serde2.objectinspector.primitive.BooleanObjectInspector;
import org.apache.hadoop.hive.serde2.objectinspector.primitive.PrimitiveObjectInspectorFactory;
import org.apache.hadoop.hive.serde2.objectinspector.primitive.StringObjectInspector;
import org.apache.hadoop.io.BooleanWritable;
import com.google.common.base.Objects;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.List;
/**
 * Created by xiaosi on 16-11-21.
 *
 */
@Description(name = "contain", value = "_FUNC_(List<T>, T) ")
public class GenericUDFStrContain extends GenericUDF {
    private static final Logger logger = LoggerFactory.getLogger(GenericUDFStrContain.class);
    private ListObjectInspector listObjectInspector;
    private StringObjectInspector stringObjectInspector;
    @Override
    public ObjectInspector initialize(ObjectInspector[] arguments) throws UDFArgumentException {
        logger.info("--------- GenericUDFStrContain --- initialize");
        // 参数个数校验
        if (arguments.length != 2) {
            throw new UDFArgumentLengthException(
                    "The function 'Contain' only accepts 2 argument : List<T> and T , but got " + arguments.length);
        }
        ObjectInspector argumentOne = arguments[0];
        ObjectInspector argumentTwo = arguments[1];
        // 参数类型校验
        if (!(argumentOne instanceof ListObjectInspector)) {
            throw new UDFArgumentException("The first argument of function must be a list / array");
        }
        if (!(argumentTwo instanceof StringObjectInspector)) {
            throw new UDFArgumentException("The second argument of function must be a string");
        }
        this.listObjectInspector = (ListObjectInspector) argumentOne;
        this.stringObjectInspector = (StringObjectInspector) argumentTwo;
        // 链表元素类型检查
        if (!(listObjectInspector.getListElementObjectInspector() instanceof StringObjectInspector)) {
            throw new UDFArgumentException("The first argument must be a list of strings");
        }
        // 返回值类型
        return PrimitiveObjectInspectorFactory.javaBooleanObjectInspector;
    }
    @Override
    public Object evaluate(DeferredObject[] arguments) throws HiveException {
        logger.info("--------- GenericUDFStrContain --- evaluate");
        // 利用ObjectInspector从DeferredObject[]中获取元素值
        List<LazyString> list = (List<LazyString>) this.listObjectInspector.getList(arguments[0].get());
        String str = this.stringObjectInspector.getPrimitiveJavaObject(arguments[1].get());
        if (Objects.equal(list, null) || Objects.equal(str, null)) {
            return null;
        }
        // 判断是否包含查询元素
        for (LazyString lazyString : list) {
            String s = lazyString.toString();
            if (Objects.equal(str, s)) {
                return new Boolean(true);
            }
        }
        return new Boolean(false);
    }
    @Override
    public String getDisplayString(String[] children) {
        return "arrayContainsExample() strContain(List<T>, T)";
    }
}
```

#### 2.4 测试

Java测试：
```
package com.sjf.open.hive.udf;
import org.apache.hadoop.hive.ql.metadata.HiveException;
import org.apache.hadoop.hive.ql.udf.generic.GenericUDF;
import org.apache.hadoop.hive.serde2.objectinspector.ObjectInspector;
import org.apache.hadoop.hive.serde2.objectinspector.ObjectInspectorFactory;
import org.apache.hadoop.hive.serde2.objectinspector.primitive.BooleanObjectInspector;
import org.apache.hadoop.hive.serde2.objectinspector.primitive.PrimitiveObjectInspectorFactory;
import java.util.ArrayList;
import java.util.List;
/**
 * Created by xiaosi on 16-11-22.
 */
public class GenericUDFStrContainTest {
    public static void test() throws HiveException {
        GenericUDFStrContain genericUDFStrContain = new GenericUDFStrContain();
        ObjectInspector stringOI = PrimitiveObjectInspectorFactory.javaStringObjectInspector;
        ObjectInspector listOI = ObjectInspectorFactory.getStandardListObjectInspector(stringOI);
        BooleanObjectInspector resultInspector = (BooleanObjectInspector) genericUDFStrContain.initialize(new ObjectInspector[]{listOI, stringOI});
        // create the actual UDF arguments
        List<String> list = new ArrayList<String>();
        list.add("a");
        list.add("b");
        list.add("c");
        // test our results
        // the value exists
        Object result = genericUDFStrContain.evaluate(new GenericUDF.DeferredObject[]{new GenericUDF.DeferredJavaObject(list), new GenericUDF.DeferredJavaObject("a")});
        System.out.println("-----------" + result);
        // the value doesn't exist
        Object result2 = genericUDFStrContain.evaluate(new GenericUDF.DeferredObject[]{new GenericUDF.DeferredJavaObject(list), new GenericUDF.DeferredJavaObject("d")});
        System.out.println("-----------" + result2);
        // arguments are null
        Object result3 = genericUDFStrContain.evaluate(new GenericUDF.DeferredObject[]{new GenericUDF.DeferredJavaObject(null), new GenericUDF.DeferredJavaObject(null)});
        System.out.println("-----------" + result3);
    }
    public static void main(String[] args) throws HiveException {
        test();
    }
}
```
Hive测试：

在Hive中使用跟简单UDF一样，需要将Java代码进行编译，然后将编译后的UDF二进制类文件打包成一个Jar文件。然后，在Hive会话中，将这个Jar文件加入到类路径下，在通过CREATE FUNCTION 语句定义好使用这个Java类的函数：
```
hive (test)> add jar /home/xiaosi/code/openDiary/HiveCode/target/open-hive-1.0-SNAPSHOT.jar;
Added [/home/xiaosi/code/openDiary/HiveCode/target/open-hive-1.0-SNAPSHOT.jar] to class path
Added resources: [/home/xiaosi/code/openDiary/HiveCode/target/open-hive-1.0-SNAPSHOT.jar]
hive (test)> create temporary function strContain as 'com.sjf.open.hive.udf.GenericUDFStrContain';
OK
Time taken: 0.021 seconds
```
使用：
```
hive (test)> select subordinates, strContain(subordinates, "tom") from employee2;
OK
["lily","lucy","tom"]	true
["lucy2","tom2"]	false
["lily","lucy","tom"]	true
["lily","yoona","lucy"]	false
Time taken: 1.147 seconds, Fetched: 4 row(s)
hive (test)> select subordinates, strContain(subordinates, 1) from employee2;
FAILED: SemanticException [Error 10014]: Line 1:21 Wrong arguments '1': The second argument of function must be a string
hive (test)> select subordinates, strContain("yoona", 1) from employee2;
FAILED: SemanticException [Error 10014]: Line 1:21 Wrong arguments '1': The first argument of function must be a list / array
hive (test)> select subordinates, strContain("yoona", 1, 3) from employee2;
FAILED: SemanticException [Error 10015]: Line 1:21 Arguments length mismatch '3': The function 'Contain' only accepts 2 argument : List<T> and T , but got 3
```
==备注==

subordinates是一个array<string>类型集合。



资料：http://blog.matthewrathbone.com/2013/08/10/guide-to-writing-hive-udfs.html#the-complex-api
