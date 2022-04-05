---
layout: post
author: smartsi
title: Flink DataStream 类型系统
date: 2021-10-07 16:35:01
tags:
  - Flink

categories: Flink
permalink: physical-partitioning-in-apache-flink
---

## 1. 数据类型支持

Flink 在其内部构建了一套自己的类型系统，Flink 现阶段支持的类型分类如下图所示，从图中可以看到 Flink 类型可以分为基础类型（Basic）、数组（Arrays）、复合类型（Composite）、辅助类型（Auxiliary）、泛型和其它类型（Generic）。Flink 支持任意的 Java 或是 Scala 类型。不需要像 Hadoop 一样去实现一个特定的接口（org.apache.hadoop.io.Writable），Flink 能够自动识别数据类型。



### 1.1 原始类型

Flink 通过实现 BasicTypeInfo 数据类型，能够支持任意 Java 原生基本类型（装箱）或 String 类型，例如，Integer、String、Double 等，如以下代码所示，通过从给定的元素集中创建 DataStream 数据集。
```
//创建Int类型的数据集
val intStream:DataStream[Int] = env.fromElements(3, 1, 2, 1, 5)
//创建String类型的数据集
val dataStream: DataStream[String] = env.fromElements("hello", "flink")
```

Flink 实现另外一种 TypeInfomation 是 BasicArrayTypeInfo，对应的是 Java 基本类型数组（装箱）或 String 对象的数组，如下代码通过使用 Array 数组和 List 集合创建 DataStream 数据集。
```
//通过从数组中创建数据集
val dataStream: DataStream[Int] = env.fromCollection(Array(3, 1, 2, 1, 5))
//通过List集合创建数据集
val dataStream: DataStream[Int] = env.fromCollection(List(3, 1, 2, 1, 5))
```

### 1.2 Java Tuples 类型

通过定义 TupleTypeInfo 来描述 Tuple 类型数据，Flink 在 Java 接口中定义了元组类（Tuple）供用户使用。Flink Tuples 是固定长度固定类型的 Java Tuple 实现，不支持空值存储。目前支持任意的F link Java Tuple 类型字段数量上限为25，如果字段数量超过上限，可以通过继承 Tuple 类的方式进行拓展。如下代码所示，创建Tuple数据类型数据集。
```
//通过实例化Tuple2创建具有两个元素的数据集
val tupleStream2: DataStream[Tuple2[String, Int]] = env.fromElements(new Tuple2("a",1), new Tuple2("c", 2))
```

### 1.3 Scala Case Class 类型

Flink 通过实现 CaseClassTypeInfo 支持任意的 Scala Case Class，包括 Scala tuples 类型，支持的字段数量上限为 22，支持通过字段名称和位置索引获取指标，不支持存储空值。如下代码实例所示，定义 WordCount Case Class 数据类型，然后通过 fromElements 方法创建 input 数据集，调用 keyBy() 方法对数据集根据 word 字段重新分区。
```
//定义WordCount Case Class数据结构
case class WordCount(word: String, count: Int)
//通过fromElements方法创建数据集
val input = env.fromElements(WordCount("hello", 1), WordCount("world", 2))
val keyStream1 = input.keyBy("word") // 根据word字段为分区字段，
val keyStream2 = input.keyBy(0) //也可以通过指定position分区
```
通过使用Scala Tuple创建DataStream数据集，其他的使用方式和Case Class相似。需要注意的是，如果根据名称获取字段，可以使用Tuple中的默认字段名称。
```
//通过scala Tuple创建具有两个元素的数据集
val tupleStream: DataStream[Tuple2[String, Int]] = env.fromElements(("a", 1),("c", 2))
//使用默认字段名称获取字段，其中_1表示tuple这种第一个字段
tupleStream.keyBy("_1")
```

### 1.4 POJOs类型

POJOs 类可以完成复杂数据结构的定义，Flink 通过实现 PojoTypeInfo 来描述任意的 POJOs，包括 Java 和 Scala类。在 Flink 中使用 POJOs 类可以通过字段名称获取字段，例如 dataStream.join(otherStream).where("name").equalTo("personName")，对于用户做数据处理则非常透明和简单。如果在 Flink 中使用 POJOs 数据类型，需要遵循以下要求：
- POJOs 类必须是 Public 修饰且必须独立定义，不能是内部类；
- POJOs 类中必须包含一个 Public 修饰的无参构造器；
- POJOs 类中所有的字段必须是 Public 或者具有 Public 修饰的 getter 和 setter 方法；
- POJOs 类中的字段类型必须是 Flink 支持的。

```Java
// (1) 必须是 Public 修饰且必须独立定义，不能是内部类
public class Person {
    // (4) 字段类型必须是 Flink 支持的
    private String name;
    private int age;
    // (2) 必须包含一个 Public 修饰的无参构造器
    public Person() {
    }
    public Person(String name, int age) {
        this.name = name;
        this.age = age;
    }
    // (3) 所有的字段必须是 Public 或者具有 Public 修饰的 getter 和 setter 方法
    public String getName() {
        return name;
    }
    public void setName(String name) {
        this.name = name;
    }
    public int getAge() {
        return age;
    }
    public void setAge(int age) {
        this.age = age;
    }
}
```
定义好 POJOs Class 后，就可以在 Flink 环境中使用了，如下代码所示，使用 fromElements 接口构建 Person 类的数据集:
```java
env.fromElements(new Person("Lucy", 18), new Person("Tom", 12))
```
### 1.5 Flink Value 类型

Value 数据类型实现了 org.apache.flink.types.Value，其中包括 read() 和 write() 两个方法完成序列化和反序列化操作，相对于通用的序列化工具会有着比较高效的性能。目前 Flink 提供了內建的 Value 类型有 IntValue、DoubleValue 以及 StringValue 等，用户可以结合原生数据类型和 Value 类型使用。

### 1.6 特殊数据类型

在 Flink 中也支持一些比较特殊的数据数据类型，例如 Scala 中的 List、Map、Either、Option、Try 数据类型，以及 Java 中 Either 数据类型，还有 Hadoop 的 Writable 数据类型。如下代码所示，创建 Map 和 List 类型数据集。这种数据类型使用场景不是特别广泛，主要原因是数据中的操作相对不像 POJOs 类那样方便和透明，用户无法根据字段位置或者名称获取字段信息，同时要借助 Types Hint 帮助 Flink 推断数据类型信息，关于 Tyeps Hmt 介绍可以参考下一小节。

## 2. TypeInformation

在 Flink 中每一个具体的类型都对应了一个具体的 TypeInformation 实现类。例如，BasicTypeInformation 中的 IntegerTypeInformation 对应了 Integer 数据类型。数据类型的描述信息都是由 TypeInformation 定义，比较常用的 TypeInformation 有 BasicTypeInfo、TupleTypeInfo、CaseClassTypeInfo、PojoTypeInfo 类等，如下图所示：

![](2)

TypeInformation 主要作用是为了在 Flink 系统内有效地对数据结构类型进行管理，能够在分布式计算过程中对数据的类型进行管理和推断。同时基于对数据的类型信息管理，Flink 内部对数据存储也进行了相应的性能优化。Flink 能够支持任意的 Java 或 Scala 的数据类型，不用像 Hadoop 中的 org.apache.hadoop.io.Writable 而实现特定的序列化和反序列化接口，从而让用户能够更加容易使用已有的数据结构类型。另外使用 TypeInformation 管理数据类型信息，能够在数据处理之前将数据类型推断出来，而不是真正在触发计算后才识别出，这样能够及时有效地避免用户在使用 Flink 编写应用的过程中的数据类型问题。

要为类型创建 TypeInformation 对象，需要使用特定于语言的方法。因为 Java 会[擦除泛型类型信息]()，所以需要将类型传入 TypeInformation 构造函数。对于非泛型类型，可以传入类型的 Class 对象：
```java
TypeInformation<String> info = TypeInformation.of(String.class);
```
对于泛型类型，你需要通过 TypeHint 来捕获泛型类型信息：
```java
// 方法1
TypeInformation<Tuple2<String, Double>> info = TypeInformation.of(new TypeHint<Tuple2<String, Double>>(){});
// 方法2
TypeHint<Tuple2<String, Double>> hint = new TypeHint<Tuple2<String, Double>>() {};
TypeInformation<Tuple2<String, Double>> info2 = hint.getTypeInfo();
```
在内部，这会创建 TypeHint 的匿名子类，捕获泛型信息并会将其保留到运行时。


## 2. 类型信息

### 2.1 为数据类型创建类型信息

Flink 类型系统的核心类是 TypeInformation。它为系统提供生成序列化器和比较器所需的必要信息。当应用程序提交执行时，Flink 的类型系统会尝试为处理的每种数据类型自动推断 TypeInformation。一个名为类型提取器的组件会分析所有函数的泛型类型以及返回类型，来获取相应的 TypeInformation 对象。但是，有时类型提取器会失灵，或者你可能想定义自己的类型并告诉 Flink 如何有效地处理它们。在这种情况下，你需要为特定数据类型生成 TypeInformation。

Flink 为 Java 和 Scala 提供了两个实用工具类，使用静态方法就可以生成 TypeInformation。对于 Java，工具类是 org.apache.flink.api.common.typeinfo.Types，具体使用如以下示例所示：



### 2.2 显示提供类型信息

大多数情况下，Flink 可以自动推断类型并生成正确的 TypeInformation。Flink 的类型提取器利用反射以及分析函数签名和子类信息，生成用户自定义函数的正确输出类型。但是，有时无法提取必要的信息（例如，Java 擦除泛型类型信息），会抛出类似的如下异常：
```
Exception in thread "main" org.apache.flink.api.common.functions.InvalidTypesException: The return type of function 'main(ReturnsExample.java:21)' could not be determined automatically, due to type erasure. You can give type information hints by using the returns(...) method on the result of the transformation call, or by letting your function implement the 'ResultTypeQueryable' interface.
	at org.apache.flink.api.dag.Transformation.getOutputType(Transformation.java:479)
	at org.apache.flink.streaming.api.datastream.DataStream.addSink(DataStream.java:1236)
	at org.apache.flink.streaming.api.datastream.DataStream.print(DataStream.java:937)
...
Caused by: org.apache.flink.api.common.functions.InvalidTypesException: The generic type parameters of 'Tuple2' are missing. In many cases lambda methods don't provide enough information for automatic type extraction when Java generics are involved. An easy workaround is to use an (anonymous) class instead that implements the 'org.apache.flink.api.common.functions.MapFunction' interface. Otherwise the type has to be specified explicitly using type information.
...
```
此外，在某些情况下，Flink 选择的 TypeInformation 可能无法生成最有效的序列化器和反序列化器的。因此，你可能需要为你使用的数据类型显式地提供 TypeInformation。有两种方法可以提供 TypeInformation，从上面的异常信息中我们也可以知道：
- 实现 ResultTypeQueryable 接口
- 使用 returns 方法给出类型信息提示

#### 2.2.1 ResultTypeQueryable

你可以通过实现 ResultTypeQueryable 接口来扩展函数以显式提供返回类型的 TypeInformation。如下示例是一个显式提供返回类型的 MapFunction：
```java
public static class ResultTypeMapFunction implements MapFunction<String, Stu>, ResultTypeQueryable {
    @Override
    public Stu map(String value) throws Exception {
        String[] params = value.split(",");
        String name = params[0];
        int age = Integer.parseInt(params[1]);
        return new Stu(name, age);
    }

    @Override
    public TypeInformation getProducedType() {
        return Types.POJO(Stu.class);
    }
}
```

#### 2.2.2 returns

在使用 Java DataStream API 定义 Dataflow 时，你还可以使用 returns() 方法显式指定算子的返回类型，如下所示：
```java
DataStream<Tuple2<String, Integer>> result = source
    .map(value -> Tuple2.of(value.split(",")[0], Integer.parseInt(value.split(",")[1])))
    .returns(Types.TUPLE(Types.STRING, Types.INT));
```


通常情况下 Flink 都能正常进行数据类型推断，并选择合适的 serializers 以及 comparators。但在某些情况下却无法直接做到，例如，定义函数时如果使用到了泛型，JVM 就会出现类型擦除的问题，使得 Flink 并不能很容易地获取到数据集中的数据类型信息。同时在 Scala API 和 Java API 中，Flink 分别使用了不同的方式重构了数据类型信息。

### 3.1 Scala API 类型信息

Scala API 通过使用 Manifest 和类标签，在编译器运行时获取类型信息，即使是在函数定义中使用了泛型，也不会像 Java API 出现类型擦除的问题，这使得 Scala API 具有非常精密的类型管理机制。同时在 Flink 中使用到 Scala Macros 框架，在编译代码的过程中推断函数输入参数和返回值的类型信息，同时在 Flink 中注册成 TypeInformation 以支持上层计算算子使用。

当使用 Scala API 开发 Flink 应用，如果使用到 Flink 已经通过 TypeInformation 定义的数据类型，TypeInformation 类不会自动创建，而是使用隐式参数的方式引入，代码不会直接抛出编码异常，但是当启动 Flink 应用程序时就会报 'could not find implicit value for evidence parameter of type TypeInformation' 的错误。这时需要将 TypeInformation 类隐式参数引入到当前程序环境中，代码实例如下：
```scala
import org.apache.flink.api.scala._
```

### 3.2 Java API 类型信息

由于 Java 的泛型会出现类型擦除问题，Flink 通过 Java 反射机制尽可能重构类型信息，例如，使用函数签名以及子类的信息等。对于函数的返回类型取决于输入类型的情况时，会包含一些简单的类型推断：
```java
public class AppendOne<T> implements MapFunction<T, Tuple2<T, Long>> {
    public Tuple2<T, Long> map(T value) {
        return new Tuple2<T, Long>(value, 1L);
    }
}
```
存在 Flink 无法重构所有泛型类型信息的情况。在这种情况下，用户必须通过类型提示（Type Hints）提供帮助。

但是如果函数的输出类型不依赖于输入参数的类型信息，这个时候就需要借助于类型提示来告诉系统函数中传入的参数类型信息和输出参数信息。

(1) Java API 中的 Type Hints

在 Flink 无法重建擦除的泛型类型信息的情况下，Java API 提供了类型提示。类型提示告诉系统函数产生的数据流或数据集的类型：
```java
DataStream<SomeType> result = stream
    .map(new MyGenericNonInferrableFunction<Long, SomeType>())
      .returns(SomeType.class);
```
returns 语句指定生成的类型，在本例中通过类。 提示通过以下方式支持类型定义

类，用于非参数化类型（无泛型）
返回形式的 TypeHints(new TypeHint<Tuple2<Integer, SomeType>>(){})。 TypeHint 类可以捕获泛型类型信息并为运行时保留它（通过匿名子类）。







如下代码所示，通过在 returns 方法中传入 TypeHint 实例指定输出参数类型，帮助 Flink 系统对输出类型进行数据类型参数的推断和收集。
```java
// stream Tuple3<String, Long, Long>
DataStream<Tuple2<String, Long>> result = stream
  // 格式转换
  .map(tuple -> Tuple2.of(tuple.f0, tuple.f1)).returns(Types.TUPLE(Types.STRING, Types.LONG));
```
在使用 Java API 定义 POJOs 类型数据时，PojoTypeInformation 为 POJOs 类中的所有字段创建序列化器，对于标准的类型，例如，Integer、String、Long 等类型是通过 Flink 自带的序列化器进行数据序列化，对于其他类型数据都是直接调用 Kryo 序列化工具来进行序列化。通常情况下，如果 Kryo 序列化工具无法对 POJOs 类序列化时，可以使用 Avro 对 POJOs 类进行序列化。


### 2.3 returns

SingleOutputStreamOperator#returns

```java
public SingleOutputStreamOperator<T> returns(Class<T> typeClass) {
    requireNonNull(typeClass, "type class must not be null.");
    try {
        return returns(TypeInformation.of(typeClass));
    } catch (InvalidTypesException e) {
        ...
    }
}
```

```java
public SingleOutputStreamOperator<T> returns(TypeHint<T> typeHint) {
    requireNonNull(typeHint, "TypeHint must not be null");
    try {
        return returns(TypeInformation.of(typeHint));
    } catch (InvalidTypesException e) {
        ...
    }
}
```

```java
public SingleOutputStreamOperator<T> returns(TypeInformation<T> typeInfo) {
    requireNonNull(typeInfo, "TypeInformation must not be null");
    transformation.setOutputType(typeInfo);
    return this;
}
```




### 2.2 自定义 TypeInformation

除了使用已有的 TypeInformation 所定义的数据格式类型之外，用户也可以自定义实现 TypeInformation，来满足的不同的数据类型定义需求。Flink 提供了可插拔的 Type Information Factory 让用户将自定义的 TypeInformation 注册到 Flink 类型系统中。如下代码所示只需要通过实现 org.apache.flink.api.common.typeinfo.TypeInfoFactory 接口，返回相应的类型信息。

通过 @TypeInfo 注解创建数据类型，定义CustomTuple数据类型。


然后定义 CustomTypeInfoFactory 类继承于 TypeInfoFactory，参数类型指定 CustomTuple。最后重写 createTypeInfo 方法，创建的 CustomTupleTypeInfo 就是 CustomTuple 数据类型 TypeInformation。

### 2.3 序列化器

除了对类型地描述之外，TypeInformation 还提供了序列化的支撑。在 Flink 中每一个具体的类型都对应了一个具体的 TypeInformation 实现类，每一个 TypeInformation 都会为对应的具体数据类型提供一个专属的序列化器。TypeInformation 会提供一个 createSerialize() 方法，通过这个方法就可以得到该类型进行数据序列化操作与反序列化操作的序列化器 TypeSerializer：
```java  
public TypeSerializer<T> createSerializer(ExecutionConfig executionConfig) {
    return this.serializer;
}
```

对于大多数数据类型 Flink 可以自动生成对应的序列化器，能非常高效地对数据集进行序列化和反序列化，比如，BasicTypeInfo、WritableTypeIno 等，但针对 GenericTypeInfo 类型，Flink 会使用 Kyro 进行序列化和反序列化。其中，Tuple、Pojo 和 CaseClass 类型是复合类型，它们可能嵌套一个或者多个数据类型。在这种情况下，它们的序列化器同样是复合的。它们会将内嵌类型的序列化委托给对应类型的序列化器。


除了对类型地描述之外，TypeInformation 还提供了序列化的支撑。在 TypeInformation 中有一个方法：createSerializer：

用来创建序列化器，序列化器中定义了一系列的方法。可以通过 serialize 和 deserialize 方法将指定类型进行序列化。Flink 中也提供了非常丰富的序列化器。

## 3. TypeExtractror

## 4. TypeHint

TypeHint 是用于描述泛型类型的工具类。通过 TypeInformation.of() 方法，可以简单地创建类型信息对象。

(1) 对于非泛型的类，直接传入 Class 对象即可：
```java
TypeInformation.of(Person.class);
```
(2) 对于泛型类，需要借助 TypeHint 获取类型信息：
```java
// 方法1
TypeInformation<Tuple2<String, Long>> info = TypeInformation.of(new TypeHint<Tuple2<String, Long>>(){
});
// 方法2
TypeHint<Tuple2<String, Long>> tupleTypeHint = new TypeHint<Tuple2<String, Long>>() {
};
TypeInformation<Tuple2<String, Long>> tupleTypeInfo2 = tupleTypeHint.getTypeInfo();
```
(3) 预定义的快捷方式

BasicTypeInfo 类定义了一系列常用类型的快捷方式，对于 String、Boolean、Byte、Short、Integer、Long、Float、Double、Char 等基本类型的类型声明，可以直接使用：

![]()

当然，如果觉得 BasicTypeInfo 还是太长，Flink 还提供了完全等价的 Types 类（org.apache.flink.api.common.typeinfo.Types）：









原文：
- [Apache Flink 进阶（五）：数据类型和序列化](https://mp.weixin.qq.com/s/FziI1YyaccuRLQAURWLnUw)
