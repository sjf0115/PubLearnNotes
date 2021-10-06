

## 1. 数据类型支持

Flink 支持非常完善的数据类型，数据类型的描述信息都是由 TypeInformation 定义，比较常用的 TypeInformation 有 BasicTypeInfo、TupleTypeInfo、CaseClassTypeInfo、PojoTypeInfo 类等。TypeInformation 主要作用是为了在 Flink 系统内有效地对数据结构类型进行管理，能够在分布式计算过程中对数据的类型进行管理和推断。同时基于对数据的类型信息管理，Flink 内部对数据存储也进行了相应的性能优化。Flink 能够支持任意的 Java 或 Scala 的数据类型，不用像 Hadoop 中的 org.apache.hadoop.io.Writable 而实现特定的序列化和反序列化接口，从而让用户能够更加容易使用已有的数据结构类型。另外使用 TypeInformation 管理数据类型信息，能够在数据处理之前将数据类型推断出来，而不是真正在触发计算后才识别出，这样能够及时有效地避免用户在使用 Flink 编写应用的过程中的数据类型问题。

### 1.1 原生数据类型

Flink 通过实现 BasicTypeInfo 数据类型，能够支持任意 Java 原生基本类型（装箱）或 String 类型，例如，Integer、String、Double 等，如以下代码所示，通过从给定的元素集中创建DataStream数据集。
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
### 1.5 Flink Value类型

Value 数据类型实现了 org.apache.flink.types.Value，其中包括 read() 和 write() 两个方法完成序列化和反序列化操作，相对于通用的序列化工具会有着比较高效的性能。目前 Flink 提供了內建的 Value 类型有 IntValue、DoubleValue 以及 StringValue 等，用户可以结合原生数据类型和 Value 类型使用。

### 1.6 特殊数据类型

在 Flink 中也支持一些比较特殊的数据数据类型，例如 Scala 中的 List、Map、Either、Option、Try 数据类型，以及 Java 中 Either 数据类型，还有 Hadoop 的 Writable 数据类型。如下代码所示，创建 Map 和 List 类型数据集。这种数据类型使用场景不是特别广泛，主要原因是数据中的操作相对不像 POJOs 类那样方便和透明，用户无法根据字段位置或者名称获取字段信息，同时要借助 Types Hint 帮助 Flink 推断数据类型信息，关于 Tyeps Hmt 介绍可以参考下一小节。

## 2. TypeInformation

通常情况下 Flink 都能正常进行数据类型推断，并选择合适的 serializers 以及 comparators。但在某些情况下却无法直接做到，例如，定义函数时如果使用到了泛型，JVM 就会出现类型擦除的问题，使得 Flink 并不能很容易地获取到数据集中的数据类型信息。同时在 Scala API 和 Java API 中，Flink 分别使用了不同的方式重构了数据类型信息。

### 2.1 Scala API 类型信息

Scala API 通过使用 Manifest 和类标签，在编译器运行时获取类型信息，即使是在函数定义中使用了泛型，也不会像 Java API 出现类型擦除的问题，这使得 Scala API 具有非常精密的类型管理机制。同时在 Flink 中使用到 Scala Macros 框架，在编译代码的过程中推断函数输入参数和返回值的类型信息，同时在 Flink 中注册成 TypeInformation 以支持上层计算算子使用。

当使用 Scala API 开发 Flink 应用，如果使用到 Flink 已经通过 TypeInformation 定义的数据类型，TypeInformation 类不会自动创建，而是使用隐式参数的方式引入，代码不会直接抛出编码异常，但是当启动 Flink 应用程序时就会报 'could not find implicit value for evidence parameter of type TypeInformation' 的错误。这时需要将 TypeInformation 类隐式参数引入到当前程序环境中，代码实例如下：
```scala
import org.apache.flink.api.scala._
```

### 2.2 Java API 类型信息

由于 Java 的泛型会出现类型擦除问题，Flink 通过 Java 反射机制尽可能重构类型信息，例如，使用函数签名以及子类的信息等。同时类型推断在当输出类型依赖于输入参数类型时相对比较容易做到，但是如果函数的输出类型不依赖于输入参数的类型信息，这个时候就需要借助于类型提示（Ctype Himts）来告诉系统函数中传入的参数类型信息和输出参数信息。如下代码所示，通过在 returns 方法中传入 TypeHint<Integer> 实例指定输出参数类型，帮助 Flink 系统对输出类型进行数据类型参数的推断和收集。
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




### 3. 自定义 TypeInformation

除了使用已有的 TypeInformation 所定义的数据格式类型之外，用户也可以自定义实现 TypeInformation，来满足的不同的数据类型定义需求。Flink 提供了可插拔的 Type Information Factory 让用户将自定义的 TypeInformation 注册到 Flink 类型系统中。如下代码所示只需要通过实现 org.apache.flink.api.common.typeinfo.TypeInfoFactory 接口，返回相应的类型信息。

通过 @TypeInfo 注解创建数据类型，定义CustomTuple数据类型。


然后定义 CustomTypeInfoFactory 类继承于 TypeInfoFactory，参数类型指定 CustomTuple。最后重写 createTypeInfo 方法，创建的 CustomTupleTypeInfo 就是 CustomTuple 数据类型 TypeInformation。

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
