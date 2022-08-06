



## 1. 概述

当 Hive 提供的内置函数无法满足你的业务处理需要时，此时可以考虑使用用户自定义函数 UDF 来满足不同的计算需求。UDF 在使用上与普通的内建函数类似。

编写一个UDF，需要继承UDF类，并实现evaluate()函数。在查询执行过程中，查询中对应的每个应用到这个函数的地方都会对这个类进行实例化。对于每行输入都会调用到evaluate()函数。而evaluate()函数处理的值会返回给Hive。同时用户是可以重载evaluate方法的。Hive会像Java的方法重载一样，自动选择匹配的方法。

## 2. 依赖

开发 Hive UDF 之前，我们需要引入一个 jar，这个 jar 就是 hive-exec，里面定义了各种我们自定义的 UDF 函数的类型：UDF、GenericUDF、GenericUDTF 等。

```xml
<dependency>
    <groupId>org.apache.hive</groupId>
    <artifactId>hive-exec</artifactId>
    <version>2.3.4</version>
 </dependency>
```

## 3. 开发

从实现上来看 Hive 有两种创建 UDF 的方式，第一种是 Simple 方式，第二种是 Generic 方式。

### 3.1 简单 UDF

第一种方式是 Simple(简单) 方式，只需要继承 org.apache.hadoop.hive.ql.exec.UDF 类即可。如下所示自定义一个 AddUDF 类，实现了 Int、Double 类型的加法操作：
```java
public class AddUDF extends UDF {
    // Int 加和
    public IntWritable evaluate(IntWritable num1, IntWritable num2){
        if(num1 == null || num2 == null){
            return null;
        }
        return new IntWritable(num1.get() + num2.get());
    }
    // Double 加和
    public DoubleWritable evaluate(DoubleWritable num1, DoubleWritable num2){
        if(num1 == null || num2 == null){
            return null;
        }
        return new DoubleWritable(num1.get() + num2.get());
    }
}
```
UDF中`evaluate()`函数的参数和返回值类型只能是Hive可以序列化的数据类型。例如，如果用户处理的全是数值，那么UDF的输出参数类型可以是基本数据类型int，Integer封装的对象或者是一个IntWritable对象，也就是Hadoop对整型封装后的对象。用户不需要特别的关心将调用到哪个类型，因为当类型不一致的时候，Hive会自动将数据类型转换成匹配的类型。null值在Hive中对于任何数据类型都是合法的，但是对于Java基本数据类型，不能是对象，也不能是null。

这种方式简单直接，但是在使用过程中需要依赖 Java 反射机制，因此性能相对较低。在 Hive 源码包 org.apache.hadoop.hive.contrib.udf.example 中包含几个示例，可以直接参阅。但是这种方式已经被标注为 Deprecated，建议不要使用这种方式开发新的 UDAF 函数。

### 3.2 通用 UDAF

简单 UDF 编写起来比较简单，但是由于使用了 Java 反射机制导致性能下降，并且不允许使用变长参数等特性。通用(Generic) UDF 可以支持复杂类型（比如List，struct，map等）的输入和输出，还可以让我们通过 ObjectInspector 来管理方法的参数，检查接收参数的类型和数量。通用 UDF 允许所有这些特性，但编写起来可能不如简单 UDF 那么直观。

通用 UDF 是 Hive 社区推荐的新写法，推荐用新的抽象类 org.apache.hadoop.hive.ql.udf.generic.GenericUDF 替代老的 UDF 抽象类，同时需要实现如下方法：
```java
@Override
public ObjectInspector initialize(ObjectInspector[] objectInspectors) throws UDFArgumentException {
    return null;
}
@Override
public Object evaluate(DeferredObject[] deferredObjects) throws HiveException {
    return null;
}
@Override
public String getDisplayString(String[] strings) {
    return null;
}
```
- initialize 方法会被输入的每个参数调用，并最终传入到一个 ObjectInspector 对象中。这个方法的目标是检查参数类型，个数以及确定参数的返回类型。如果传入方法的类型是不合法的，这时用户同样可以向控制台抛出一个 Exception 异常信息。
- evaluate 方法的输入是一个 DeferredObjec 对象数组。在这个方法中实现我们想要的逻辑，返回与 initialize 方法返回值相符的值。
- getDisplayString 方法用于 Hadoop task 内部，在使用到这个函数时来展示调试信息（还不太明白）。

如下所示自定义一个 GenericAddUDF 类，实现了 Int 类型的加法操作：
```java
public class GenericAddUDF extends GenericUDF {
    private IntObjectInspector intOI;
    @Override
    public ObjectInspector initialize(ObjectInspector[] arguments) throws UDFArgumentException {
        // 参数个数校验
        if (arguments.length != 2) {
            throw new UDFArgumentLengthException("The function 'Add' only accepts 2 argument, but got " + arguments.length);
        }
        ObjectInspector a1 = arguments[0];
        ObjectInspector a2 = arguments[1];
        // 参数类型校验
        if (!(a1 instanceof IntObjectInspector)) {
            throw new UDFArgumentException("The first argument of function must be a int");
        }
        if (!(a2 instanceof IntObjectInspector)) {
            throw new UDFArgumentException("The second argument of function must be a int");
        }
        this.intOI = (IntObjectInspector) a1;
        this.intOI = (IntObjectInspector) a2;
        // 返回值类型
        return PrimitiveObjectInspectorFactory.javaIntObjectInspector;
    }

    @Override
    public Object evaluate(DeferredObject[] deferredObjects) throws HiveException {
        Object o1 = deferredObjects[0].get();
        Object o2 = deferredObjects[1].get();
        // 利用 ObjectInspector 从 DeferredObject[] 中获取元素值
        int a1 = (int) this.intOI.getPrimitiveJavaObject(o1);
        int a2 = (int) this.intOI.getPrimitiveJavaObject(o2);
        return new Integer(a1 + a2);
    }

    @Override
    public String getDisplayString(String[] strings) {
        return "custom_add(T, T)";
    }
}
```

## 4. 注册

如果想在 Hive 中使用 UDF，那么需要将 Java 代码进行编译，然后将编译后的 UDF 二进制类文件打包成一个 Jar 文件。然后，在 Hive 会话中，将这个 Jar 文件加入到类路径下，再通过 CREATE FUNCTION 语句定义好使用这个 Java 类的函数。

### 4.1 添加 Jar 文件到类路径下
```
hive (test)> add jar /opt/jar/hive-example-1.0.jar;
Added [/home/xiaosi/open-hive-1.0-SNAPSHOT.jar] to class path
Added resources: [/home/xiaosi/open-hive-1.0-SNAPSHOT.jar]
```
需要注意的是，Jar 文件路径是不需要用引号括起来的，同时，到目前为止这个路径需要是当前文件系统的全路径。Hive不仅仅将这个Jar文件加入到classpath下，同时还将其加入到分布式缓存中，这样整个集群的机器都是可以获得该Jar文件的。


add jar /Users/wy/study/code/data-example/hive-example/target/hive-example-1.0.jar;

### 4.2 创建函数 add
```
hive (test)> create temporary function custom_add as 'com.hive.example.udf.GenericAddUDF';
OK
Time taken: 0.004 seconds
```
注意的是create temporary function语句中的temporary关键字，当前会话中声明的函数只会在当前会话中有效。因此用户需要在每个会话中都增加Jar文件然后创建函数。不过如果用户需要频繁的使用同一个Jar文件和函数的话，那么可以将相关语句增加到$HOME/.hiverc文件中去。

## 5. 使用

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

当我们使用完自定义UDF后，我们可以通过如下命令删除此函数：
```
hive (test)> drop temporary function if exists add;
```

## 6. 测试

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
