---
layout: post
author: sjf0115
title: 深入理解 Hive UDAF
date: 2021-12-12 13:25:01
tags:
  - Hive

categories: Hive
permalink: insights-into-hive-udaf
---

## 1. 概述

用户自定义聚合函数(UDAF)支持用户自行开发聚合函数完成业务逻辑。从实现上来看 Hive 有两种创建 UDAF 的方式，第一种是 Simple 方式，第二种是 Generic 方式。

### 1.1 简单 UDAF

第一种方式是 Simple(简单) 方式，即继承 org.apache.hadoop.hive.ql.exec.UDAF 类，并在派生类中以静态内部类的方式实现 org.apache.hadoop.hive.ql.exec.UDAFEvaluator 接口：

![](img-insights-into-hive-udaf-1.png)

这种方式简单直接，但是在使用过程中需要依赖 Java 反射机制，因此性能相对较低。在 Hive 源码包 org.apache.hadoop.hive.contrib.udaf.example 中包含几个示例，可以直接参阅。但是这种方式已经被标注为 Deprecated，建议不要使用这种方式开发新的 UDAF 函数。

### 1.2 通用 UDAF

简单 UDAF 编写起来比较简单，但是由于使用了 Java 反射机制导致性能下降，并且不允许使用变长参数等特性。通用 UDAF 允许所有这些特性，但编写起来可能不如简单 UDAF 那么直观。通用(Generic) UDAF 是 Hive 社区推荐的新写法，推荐用新的抽象类 org.apache.hadoop.hive.ql.udf.generic.AbstractGenericUDAFResolver 替代老的 UDAF 接口，用新的抽象类 org.apache.hadoop.hive.ql.udf.generic.GenericUDAFEvaluator 替代老的 UDAFEvaluator 接口。

![](img-insights-into-hive-udaf-2.png)

## 2. 结构

> 由于简单（Simple）UDAF 性能相对较低，已经废弃，因此我们后面重点关注通用（Generic）UDAF。

从高层次上来看通用 UDAF 需要实现两个部分：
- 第一部分是创建一个 Resolver 类，用于实现类型检查以及操作符重载(如果需要的话)，并为给定的一组输入参数类型指定正确的 Evaluator 类。
- 第二部分是创建一个 Evaluator 类，用于实现 UDAF 的具体逻辑。一般实现为一个静态内部类。

### 2.1 Resolver

简单 UDAF Resolver 的 UDAF 接口被废弃后，通用 UDAF Resolver 有三种实现方式：
- 实现 GenericUDAFResolver 接口
- 实现 GenericUDAFResolver2 接口
- 继承 AbstractGenericUDAFResolver 类

现在新问题来了：上述三种方式，在开发 UDAF 的时候该用哪一种呢？

![](img-insights-into-hive-udaf-3.png)

#### 2.1.1 GenericUDAFResolver

用户定义聚合函数(GenericUDAF)编译时使用 GenericUDAFResolver 来查找参数类型对应的 GenericUDAFEvaluator：
```java
@Deprecated
public interface GenericUDAFResolver {
  GenericUDAFEvaluator getEvaluator(TypeInfo[] parameters) throws SemanticException;
}
```
getEvaluator 方法返回参数类型对应的 Evaluator。

> GenericUDAFResolver 已经被弃用。

#### 2.1.2 GenericUDAFResolver2

如上图所示，GenericUDAFResolver2 接口继承了 GenericUDAFResolver 接口，此外还提供了另外一个 GenericUDAFParameterInfo 为参数的 getEvaluator 方法：
```java
@Deprecated
@SuppressWarnings("deprecation")
public interface GenericUDAFResolver2 extends GenericUDAFResolver {
  GenericUDAFEvaluator getEvaluator(GenericUDAFParameterInfo info) throws SemanticException;
}
```
相比 GenericUDAFResolver 接口，该接口在参数类型方面提供了更大的灵活性。如下所示 GenericUDAFResolver2 接口提供的 GenericUDAFParameterInfo 参数信息：
```java
public interface GenericUDAFParameterInfo {
  @Deprecated
  TypeInfo[] getParameters();
  ObjectInspector[] getParameterObjectInspectors();
  // 是否使用了 DISTINCT 限定符
  boolean isDistinct();
  // 是否在窗口函数中调用
  boolean isWindowing();
  // 是否使用通配符语法
  boolean isAllColumns();
  boolean respectNulls();
}
```
GenericUDAFResolver2 可以允许 Evaluator 的实现访问关于函数调用的额外信息，比如，是否使用了 DISTINCT 限定符或者使用特殊通配符(function(*))。实现 GenericUDAFResolver 接口的 UDAF 则无法分辨调用 FUNCTION()和 FUNCTION(*) 的区别，因为无法获得有关通配符的信息。类似地，也不能区分 FUNCTION(EXPR) 和 FUNCTION(DISTINCT EXPR) 的区别，因为也无法获取有关 DISTINCT 限定符的信息。

UDAF 函数的实现不用对 DISTINCT 限定符或者通配符做特殊处理。DISTINCT 计算实际上是由 Hive 的核心查询处理器完成，不是由 Resolver 或 Evaluator 完成的，只是向 Resolver 提供信息仅用来做验证的。

> 虽然实现 GenericUDAFResolver2 接口的 Resolver 提供了关于 DISTINCT 限定符或者通配符的额外信息，但如果对我们没有任何意义，我们可以选择忽略这些信息。

#### 2.1.3 AbstractGenericUDAFResolver

如上图所示，AbstractGenericUDAFResolver 类是 GenericUDAFResolver2 接口的实现类：
```java
public abstract class AbstractGenericUDAFResolver implements GenericUDAFResolver2 {
  @SuppressWarnings("deprecation")
  @Override
  public GenericUDAFEvaluator getEvaluator(GenericUDAFParameterInfo info) throws SemanticException {
    if (info.isAllColumns()) {
      throw new SemanticException("The specified syntax for UDAF invocation is invalid.");
    }
    return getEvaluator(info.getParameters());
  }

  @Override
  public GenericUDAFEvaluator getEvaluator(TypeInfo[] info) throws SemanticException {
    throw new SemanticException("This UDAF does not support the deprecated getEvaluator() method.");
  }
}
```
AbstractGenericUDAFResolver 提供了一种简单的方法将以前实现 GenericUDAFResolver 接口的 UDAF 迁移到 GenericUDAFResolver2 接口上。这个类提供了新 API 的默认实现，然后通过忽略 GenericUDAFParameterInfo 接口获得的额外参数信息来调用 GenericUDAFResolver#getEvaluator(TypeInfo[]) API。在使用 Resolver 类时，推荐使用 AbstractGenericUDAFResolver 抽象类。

### 2.2 Evaluator

所有 Evaluator 都必须继承基类 org.apache.hadoop.hive.ql.udf.generic.GenericUDAFEvaluator。该类提供了一些必须由扩展类实现的抽象方法。

![](img-insights-into-hive-udaf-4.png)

这些方法建立了 UDAF 之后的处理语义。下面是 Evaluator 类的架构：
```java
public static class AverageUDAFEvaluator extends GenericUDAFEvaluator {
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
下面我们对每个函数进行一下说明：
- init：用来初始化 Evaluator 实例。
- getNewAggregationBuffer：返回一个用于存储临时聚合结果的对象。
- iterate：处理一行新数据到 AggregationBuffer 临时聚合结果中。iterate 方法在 Map 阶段开始被调用。
- terminatePartial：以可持久化的方式返回当前聚合结果。可持久化意味着返回值只能通过 Java 原生类型、数组、原生包装器(例如，Double)、Hadoop Writables、Lists 或者 Map 来构建。不能使用我们自定义的类(即使实现了 java.io.Serializable)，否则可能会得到奇怪的错误或(可能更糟)错误的结果。terminatePartial 方法一般在 Map 或者 Combine 阶段结束时调用。
- merge：将 terminatePartial 返回的部分聚合结果合并到当前聚合结果中。merge 方法一般在 Reduce 阶段被调用，用来合并 Map 或者 Combine 输入的数据。
- terminate：将最终聚合结果返回给 Hive。

## 3. 运行流程

抽象类 GenericUDAFEvaluator 中包含一个静态内部枚举类 Mode。这个枚举类表示不同的运行阶段，按照时间先后顺序，分别有：
- PARTIAL1：从原始数据到部分聚合数据的过程，会调用 iterate() 和 terminatePartial() 方法。iterate() 函数负责解析输入数据，terminatePartial() 负责输出当前临时聚合结果。该阶段可以理解为对应 MapReduce 过程中的 Map 阶段。
- PARTIAL2：从部分聚合数据到部分聚合数据的过程（多次聚合），会调用 merge() 和 terminatePartial() 方法。merge() 函数负责聚合 Map 阶段 terminatePartial() 函数输出的部分聚合结果，terminatePartial() 负责输出当前临时聚合结果。阶段可以理解为对应 MapReduce 过程中的 Combine 阶段。
- FINAL: 从部分聚合数据到全部聚合数据的过程，会调用 merge() 和 terminate() 方法。merge() 函数负责聚合 Map 阶段或者 Combine 阶段 terminatePartial() 函数输出的部分聚合结果。terminate() 方法负责输出 Reduce 阶段最终的聚合结果。该阶段可以理解为对应 MapReduce 过程中的 Reduce 阶段。
- COMPLETE: 从原始数据直接到全部聚合数据的过程，会调用 iterate() 和 terminate() 方法。可以理解为 MapReduce 过程中的直接 Map 输出阶段，没有 Reduce 阶段。

> 每个阶段都会执行 Init() 初始化操作。

![](img-insights-into-hive-udaf-5.png)

![](img-insights-into-hive-udaf-6.png)

所以，完整的 UDAF 逻辑是一个 MapReduce 过程，如果有 Mapper 和 Reducer，就会经历 PARTIAL1(对应 Map 阶段)，FINAL(对应 Reduce 阶段)，如果还有 Combiner，那就会经历 PARTIAL1、PARTIAL2(对应 Combine 阶段) 以及 FINAL。此外还有一种情况下只有 Mapper，没有 Reducer，在这种情况下就只有 COMPLETE 阶段。

## 4. 开发

### 4.1 开发 Resolver

Resolver 处理 UDAF 查询的类型检查与运算符重载。类型检查确保用户没有在需要整数的地方传递 Double 表达式，运算符重载允许对不同类型的参数使用不同的 UDAF 逻辑。如上面提到的推荐 Resolver 继承 AbstractGenericUDAFResolver 类：
```java
public class AbstractGenericAverageUDAF extends AbstractGenericUDAFResolver {
  static final Log LOG = LogFactory.getLog(AbstractGenericAverageUDAF.class.getName());
  @Override
  public GenericUDAFEvaluator getEvaluator(GenericUDAFParameterInfo info) throws SemanticException {
    return getEvaluator(info.getParameters());
  }
  public GenericUDAFEvaluator getEvaluator(TypeInfo[] parameters) throws SemanticException {
    // 在这做类型检查以及选择指定的 Evaluator
    return new AverageUDAFEvaluator();
  }
  public static class AverageUDAFEvaluator extends GenericUDAFEvaluator {
    // 在这实现 UDAF 逻辑
  }
}
```
上面的代码展示了 UDAF 的基本框架。第一行设置了一个 Log 对象，可以将 Warn 和 Error 写入到 Hive 日志中。AbstractGenericUDAFResolver 类有两个覆盖方法: getEvaluator，用来接收关于如何调用 UDAF 的信息。info.getParameters() 即 parameters，提供了与调用参数的 SQL 类型相对应的类型信息对象数组。info 除此之外还可以获取关于函数调用的额外信息，比如，是否使用了 DISTINCT 限定符或者使用特殊通配符。

对于平均值 UDAF，我们只需要一个参数：用于计算平均值的数值列。首先要做的是检查我们是否恰好只有一个参数。然后，我们检查第一个参数是否是基本类型，并根据基本类型选择正确的 Evaluator。如果是 BYTE、SHORT、INT、LONG、TIMESTAMP、FLOAT、DOUBLE、STRING、VARCHAR、CHAR 类型，选择 AverageUDAFEvaluator，否则抛出异常：
```java
public GenericUDAFEvaluator getEvaluator(GenericUDAFParameterInfo info) throws SemanticException {
    return getEvaluator(info.getParameters());
}

public GenericUDAFEvaluator getEvaluator(TypeInfo[] parameters) throws SemanticException {
    if (parameters.length != 1) {
        throw new UDFArgumentTypeException(parameters.length - 1,
                "Exactly one argument is expected.");
    }

    if (parameters[0].getCategory() != ObjectInspector.Category.PRIMITIVE) {
        throw new UDFArgumentTypeException(0,
                "Only primitive type arguments are accepted but "
                        + parameters[0].getTypeName() + " is passed.");
    }
    switch (((PrimitiveTypeInfo) parameters[0]).getPrimitiveCategory()) {
        case BYTE:
        case SHORT:
        case INT:
        case LONG:
        case FLOAT:
        case DOUBLE:
        case STRING:
        case VARCHAR:
        case CHAR:
        case TIMESTAMP:
            return new AverageUDAFEvaluator();
        case DECIMAL:
        case BOOLEAN:
        case DATE:
        default:
            throw new UDFArgumentTypeException(0,
                    "Only numeric or string type arguments are accepted but "
                            + parameters[0].getTypeName() + " is passed.");
    }
}
```
从上面可以看出根据不同的类型可以选择不同的 Evaluator 类，我们来分析下 AverageUDAFEvaluator 的实现。

> 在这我们只实现了一个 Evaluator 类：AverageUDAFEvaluator

### 4.2 开发 Evaluator

AverageUDAFEvaluator 是用来对 BYTE、SHORT、INT、LONG、TIMESTAMP、FLOAT、DOUBLE、STRING、VARCHAR、CHAR 类型求平均值的 UDAF，其中有几个变量，inputOI 是输入的数据，partialResult 是部分聚合结果（对应 ObjectInspector 为 StructObjectInspector），result 是最终聚合结果，初始化是对这几个参数的初始化，另外定义了 AverageAggBuffer 来存储中间结果，里面包含了 count 值和 sum 值。

#### 4.2.1 init

首先 init 方法用来初始化 Evaluator 实例：
```java
// Iterate 输入
private PrimitiveObjectInspector inputOI;
// Merge 输入
private StructObjectInspector structOI;
private LongObjectInspector countFieldOI;
private DoubleObjectInspector sumFieldOI;
private StructField countField;
private StructField sumField;

// TerminatePartial 输出
private Object[] partialResult;
// Terminate 输出
private DoubleWritable result;

public ObjectInspector init(Mode mode, ObjectInspector[] parameters) throws HiveException {
    assert (parameters.length == 1);
    super.init(mode, parameters);
    // 初始化输入参数
    if (mode == Mode.PARTIAL1 || mode == Mode.COMPLETE) {
        // 原始数据
        inputOI = (PrimitiveObjectInspector) parameters[0];
    } else {
        // 部分聚合数据
        structOI = (StructObjectInspector) parameters[0];
        countField = structOI.getStructFieldRef("count");
        sumField = structOI.getStructFieldRef("sum");
        countFieldOI = (LongObjectInspector) countField.getFieldObjectInspector();
        sumFieldOI = (DoubleObjectInspector) sumField.getFieldObjectInspector();
    }
    // 初始化输出
    if (mode == Mode.PARTIAL1 || mode == Mode.PARTIAL2) {
        // 最终结果
        partialResult = new Object[2];
        partialResult[0] = new LongWritable(0);
        partialResult[1] = new DoubleWritable(0);
        // 部分聚合结果
        // 字段类型
        ArrayList<ObjectInspector> structFieldOIs = new ArrayList<ObjectInspector>();
        structFieldOIs.add(PrimitiveObjectInspectorFactory.writableLongObjectInspector);
        structFieldOIs.add(PrimitiveObjectInspectorFactory.writableDoubleObjectInspector);
        // 字段名称
        ArrayList<String> structFieldNames = new ArrayList<String>();
        structFieldNames.add("count");
        structFieldNames.add("sum");
        return ObjectInspectorFactory.getStandardStructObjectInspector(structFieldNames, structFieldOIs);
    } else {
        result = new DoubleWritable(0);
        return PrimitiveObjectInspectorFactory.writableDoubleObjectInspector;
    }
}
```
在 PARTIAL1 和 COMPLETE 模式下，输入参数均是原始数据。在 PARTIAL2 和 FINAL 模式中，输入参数是部分聚合结果，部分聚合结果使用 Object 数组(第一个元素为 LongWritable 类型，第二个元素为 DoubleWritable)在不同阶段进行传输，ObjectInspector 为 StructObjectInspector。在 PARTIAL1 和 PARTIAL2 模式下，terminatePartial() 返回值的 ObjectInspector 为 StandardStructObjectInspector。在 FINAL 和 COMPLETE 模式下，terminate() 返回值的 ObjectInspector 为 WritableDoubleObjectInspector。

> ObjectInspector 作用主要是解耦实际数据与数据格式，使得数据流在输入输出端切换不同的输入输出格式，不同的 Operator 上使用不同的格式，可以通过这个抽象类知道上游传递过来的参数类型，从而解耦。一个 ObjectInspector 对象本身并不包含任何数据，它只是提供对数据类型的说明以及对数据对象操作的统一管理或者是代理。

#### 4.2.2 getNewAggregationBuffer

getNewAggregationBuffer 方法返回一个用于存储临时聚合结果的对象 AggregationBuffer，其中 count 字段表示存储聚合的记录个数，sum 字段表示存储聚合的总和：
```java
// 存储临时聚合结果对象
static class AverageAggBuffer implements AggregationBuffer {
    long count;
    double sum;
}

// 返回一个新的聚合对象
public AggregationBuffer getNewAggregationBuffer() throws HiveException {
    AverageAggBuffer buffer = new AverageAggBuffer();
    reset(buffer);
    return buffer;
}
```
#### 4.2.3 reset

reset 方法重置存储临时聚合结果的对象 AggregationBuffer：
```java
public void reset(AggregationBuffer agg) throws HiveException {
    AverageAggBuffer buffer = (AverageAggBuffer) agg;
    buffer.count = 0L;
    buffer.sum = 0.0;
}
```

#### 4.2.4 iterate

iterate() 函数解析出实际的输入数据(一个数字)，然后合并到临时聚合结果 AggregationBuffer 中：
```java
public void iterate(AggregationBuffer agg, Object[] parameters) throws HiveException {
    assert (parameters.length == 1);
    try {
        if (parameters[0] != null) {
            AverageAggBuffer buffer = (AverageAggBuffer) agg;
            buffer.count ++;
            buffer.sum += PrimitiveObjectInspectorUtils.getDouble(parameters[0], inputOI);
        }
    } catch (NumberFormatException e) {
        throw new HiveException("iterate exception", e);
    }
}
```
该方法一般在 Map 阶段调用，用来读取原始数据。

#### 4.2.5 terminatePartial

terminatePartial 以 Object 数组的方式返回当前聚合结果，第一个值存储的是 LongWritable 类型的输入元素个数，第二个值存储的是 DoubleWritable 类型的输入元素总和：
```java
public Object terminatePartial(AggregationBuffer agg) throws HiveException {
    AverageAggBuffer buffer = (AverageAggBuffer) agg;
    ((LongWritable) partialResult[0]).set(buffer.count);
    ((DoubleWritable) partialResult[1]).set(buffer.sum);
    return partialResult;
}
```
terminatePartial 方法一般在 Map 或者 Combine 阶段结束时调用，得到部分数据聚集结果，将数据以持久化方式传输到 Reduce 进行处理。只支持 Java 原始数据类型、数组、原生包装器(例如，Double)、Hadoop Writables、Lists 或者 Map 类型。不能使用我们自己自定义类(即使实现了 java.io.Serializable)，否则可能会得到奇怪的错误或(可能更糟)错误的结果。

#### 4.2.6 merge

merge 方法将 terminatePartial 返回的聚合结果 partial 合并到当前聚合结果 agg 中。一般在 Combine 或者 Reduce 阶段调用，Combiner 合并 Mapper 返回的结果，Reducer 合并 Mapper 或者 Combiner 返回的结果。我们通过 terminatePartial 方法知道传输到 merge 方法的是一个 Object 数组，因此我们需要通过 StructObjectInspector 解析出 partial 数组元素值：
```java
public void merge(AggregationBuffer agg, Object partial) throws HiveException {
    if (partial == null) {
        return;
    }
    AverageAggBuffer buffer = (AverageAggBuffer) agg;
    Object partialCount = structOI.getStructFieldData(partial, countField);
    Object partialSum = structOI.getStructFieldData(partial, sumField);
    buffer.count += countFieldOI.get(partialCount);
    buffer.sum += sumFieldOI.get(partialSum);
}
```

#### 4.2.7 terminate

terminate 方法根据 AggregationBuffer 中临时存储的值计算生成 DoubleWritable 类型的平均值 Object 返回。对应在 Reducer 阶段，输出最终结果：
```java
private DoubleWritable result;
public Object terminate(AggregationBuffer agg) throws HiveException {
    AverageAggBuffer buffer = (AverageAggBuffer) agg;
    if (buffer.count == 0) {
        return null;
    }
    result.set(buffer.sum / buffer.count);
    return result;
}
```

完整代码请参阅：[AbstractGenericAverageUDAF](https://github.com/sjf0115/data-example/blob/master/hive-example/src/main/java/com/hive/example/udf/AbstractGenericAverageUDAF.java)

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg)

参考资料：
- https://blog.csdn.net/lidongmeng0213/article/details/110869457
- https://www.cnblogs.com/itboys/p/13396774.html
- https://cwiki.apache.org/confluence/display/Hive/GenericUDAFCaseStudy
