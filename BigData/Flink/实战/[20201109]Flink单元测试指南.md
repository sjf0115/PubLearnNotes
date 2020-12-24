---
layout: post
author: smartsi
title: Flink单元测试指南
date: 2020-11-09 22:09:01
tags:
  - Flink

categories: Flink
permalink: a-guide-for-unit-testing-in-apache-flink
---

> Flink版本：1.11.2

编写单元测试是设计生产应用程序的基本任务之一。如果不进行测试，那么一个很小的代码变更都会导致生产任务的失败。因此，无论是清理数据、模型训练的简单作业，还是复杂的多租户实时数据处理系统，我们都应该为所有类型的应用程序编写单元测试。下面我们将提供有关 Apache Flink 应用程序的单元测试指南。Apache Flink 提供了一个强大的单元测试框架，以确保我们的应用程序在上线后符合我们的预期。

### 1. Maven依赖

如果我们要使用 Apache Flink 提供的单元测试框架，我们需要引入如下依赖：
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-streaming-java_${scala.binary.version}</artifactId>
    <version>${flink.version}</version>
    <scope>test</scope>
    <classifier>tests</classifier>
</dependency>

<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-test-utils_${scala.binary.version}</artifactId>
    <version>${flink.version}</version>
    <scope>test</scope>
</dependency>

<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-runtime_${scala.binary.version}</artifactId>
    <version>${flink.version}</version>
    <scope>test</scope>
    <classifier>tests</classifier>
</dependency>
```
> flink.version：1.11.2，scala.binary.version：2.11

注意：由于需要测试 JAR 包：org.apache.flink:flink-runtime_2.11:tests:1.11.2 和 org.apache.flink:flink-streaming-java_2.11:tests:1.11.2，所以依赖需要制定 classifier 为 tests。

对于不同的算子，单元测试的编写也不一样。我们可以分为如下三种：
- 无状态算子
- 有状态算子
- 定时处理算子（ProcessFunction）

### 2. 无状态算子

> 只有在使用 Test Harnesses 时，我们才需要上述 Maven 依赖，所以在编写无状态算子的单元测试时，可以不添加上述 Maven 依赖。

无状态算子的单元测试编写比较简单。我们只需要遵循编写测试用例的基本规范，即创建函数类的实例并测试适当的方法。我们以一个简单的 Map 算子为例：
```java
public class MyStatelessMap implements MapFunction<String, String> {
    @Override
    public String map(String s) throws Exception {
        String out = "hello " + s;
        return out;
    }
}
```
上述算子的单元测试用例如下所示：
```java
@Test
public void MyStatelessMap() throws Exception {
    MyStatelessMap statelessMap = new MyStatelessMap();
    String out = statelessMap.map("world");
    Assert.assertEquals("hello world", out);
}
```
下面让我们来看一下 FlatMap 算子：
```java
public class MyStatelessFlatMap implements FlatMapFunction<String, String> {
    @Override
    public void flatMap(String s, Collector<String> collector) throws Exception {
        String out = "hello " + s;
        collector.collect(out);
    }
}
```
FlatMap 算子需要一个 Collector 对象以及一个输入参数。编写测试用例，我们有如下两种方式：
- 使用 Mockito 模拟 Collector 对象
- 使用 Flink 提供的 ListCollector

我更喜欢第二种方法，因为只需要很少的代码即可，并且适合大多数情况：
```java
@Test
public void MyStatelessFlatMap() throws Exception {
    MyStatelessFlatMap statelessFlatMap = new MyStatelessFlatMap();
    List<String> out = new ArrayList<>();
    ListCollector<String> listCollector = new ListCollector<>(out);
    statelessFlatMap.flatMap("world", listCollector);
    Assert.assertEquals(Lists.newArrayList("hello world"), out);
}
```

### 3. 有状态算子

测试有状态算子（使用状态或者定时器）会比较困难。因为用户代码需要与 Flink Runtime 进行交互。为此，Flink 提供了一组 TestHarness，可用于测试用户定义的函数以及自定义算子：
- OneInputStreamOperatorTestHarness：适用于 DataStreams 上的算子
- KeyedOneInputStreamOperatorTestHarness：适用于 KeyedStreams 上的算子
- TwoInputStreamOperatorTestHarness：用于两个数据流的 ConnectedStream 的算子
- KeyedTwoInputStreamOperatorTestHarness：用于两个 KeyedStream 的 ConnectedStream 上的算子

我们以有状态的 FlatMap 函数为例：
```java
public class MyStatefulFlatMap extends RichFlatMapFunction<String, Long> {
    ValueState<Long> counterState;

    @Override
    public void open(Configuration parameters) throws Exception {
        ValueStateDescriptor<Long> descriptor = new ValueStateDescriptor<>(
                "Counter",
                Types.LONG
        );
        this.counterState = getRuntimeContext().getState(descriptor);
    }

    @Override
    public void flatMap(String s, Collector<Long> collector) throws Exception {
        Long count = 0L;
        if (this.counterState.value() != null) {
            count = this.counterState.value();
        }
        count ++;
        this.counterState.update(count);
        collector.collect(count);
    }
}
```
编写上述类的单元测试最复杂部分是模拟应用程序的配置以及运行时上下文。我们使用 Flink 提供的 TestHarness 类，这样我们就不必自己创建模拟对象。使用 KeyedOperatorHarness 类进行单元测试如下所示：
```java
public class MyStatefullFlatMapUnitTest {

    private KeyedOneInputStreamOperatorTestHarness<String, String, Long>  testHarness;
    private MyStatefulFlatMap statefulFlatMap;

    @Before
    public void setupTestHarness() throws Exception {
        statefulFlatMap = new MyStatefulFlatMap();
        // KeyedOneInputStreamOperatorTestHarness 需要三个参数：算子对象、键 Selector、键类型
        testHarness = new KeyedOneInputStreamOperatorTestHarness<>(
                new StreamFlatMap<>(statefulFlatMap),
                x -> "1",
                Types.STRING
        );
        testHarness.open();
    }

    @Test
    public void MyStatefulFlatMap() throws Exception{
        // test first record
        testHarness.processElement("a", 10);
        //
        Assert.assertEquals(
                Lists.newArrayList(new StreamRecord<>(1L, 10)),
                this.testHarness.extractOutputStreamRecords()
        );

        // test second record
        testHarness.processElement("b", 20);
        Assert.assertEquals(
                Lists.newArrayList(
                        new StreamRecord<>(1L, 10),
                        new StreamRecord<>(2L, 20)
                ),
                testHarness.extractOutputStreamRecords()
        );

        // test other record
        testHarness.processElement("c", 30);
        testHarness.processElement("d", 40);
        testHarness.processElement("e", 50);
        Assert.assertEquals(
                Lists.newArrayList(
                        new StreamRecord<>(1L, 10),
                        new StreamRecord<>(2L, 20),
                        new StreamRecord<>(3L, 30),
                        new StreamRecord<>(4L, 40),
                        new StreamRecord<>(5L, 50)
                ),
                testHarness.extractOutputStreamRecords()
        );
    }
}
```
TestHarness 提供了许多辅助方法，上述代码使用了其中三种：
- open：使用相关参数调用 FlatMap 函数的 open 方法，同时还会对上下文进行初始化。
- processElement：允许用户传入输入元素以及与该元素关联的时间戳。
- extractOutputStreamRecords：从 Collector 获取输出记录以及时间戳。

TestHarness 极大地简化了有状态算子的单元测试。

### 4. 定时处理算子

为与时间有关的 Process Function 编写单元测试与为有状态算子编写单元测试非常相似，我们都需要使用 TestHarness。但是，在这我们还需要考虑另一个方面，即为事件提供时间戳并控制应用程序的当前时间。通过设置当前（处理时间或事件时间）时间，我们可以触发注册的计时器，并调用该函数的 onTimer 方法：
```java
public class TimerProcessFunction extends KeyedProcessFunction<String, String, String> {
    @Override
    public void processElement(String s, Context context, Collector<String> collector) throws Exception {
        context.timerService().registerProcessingTimeTimer(50);
        String out = "hello " + s;
        collector.collect(out);
    }

    @Override
    public void onTimer(long timestamp, OnTimerContext ctx, Collector<String> out) throws Exception {
        // 到达时间点触发事件操作
        out.collect(String.format("Timer triggered at timestamp %d", timestamp));
    }
}
```
我们需要测试 KeyedProcessFunction 中的两个方法，即 processElement 和 onTimer 方法。使用 TestHarness，我们可以控制函数的当前时间。因此，我们可以随意触发计时器，而不必等待特定的时间：
```java
public class TimerProcessFunctionUnitTest {

    private OneInputStreamOperatorTestHarness<String, String> testHarness;
    private TimerProcessFunction processFunction;

    @Before
    public void setupTestHarness() throws Exception {
        processFunction = new TimerProcessFunction();

        // KeyedOneInputStreamOperatorTestHarness 需要三个参数：算子对象、键 Selector、键类型
        testHarness = new KeyedOneInputStreamOperatorTestHarness<>(
                new KeyedProcessOperator<>(processFunction),
                x -> "1",
                Types.STRING
        );
        // Function time is initialized to 0
        testHarness.open();
    }

    @Test
    public void testProcessElement() throws Exception{

        testHarness.processElement("world", 10);
        Assert.assertEquals(
                Lists.newArrayList(
                        new StreamRecord<>("hello world", 10)
                ),
                testHarness.extractOutputStreamRecords()
        );
    }

    @Test
    public void testOnTimer() throws Exception {
        // test first record
        testHarness.processElement("world", 10);
        Assert.assertEquals(1, testHarness.numProcessingTimeTimers());

        // Function time 设置为 50
        testHarness.setProcessingTime(50);
        Assert.assertEquals(
                Lists.newArrayList(
                        new StreamRecord<>("hello world", 10),
                        new StreamRecord<>("Timer triggered at timestamp 50")
                ),
                testHarness.extractOutputStreamRecords()
        );
    }
}
```

考虑到 ProcessFunction 的重要性，除了上面可以直接用于测试 ProcessFunction 的 TestHarness 之外，Flink 还提供了一个名为 ProcessFunctionTestHarnesses 的 TestHarness 工厂，可以大大简化 TestHarness 的实例化。如下所示：
```java
public class MyProcessFunction extends ProcessFunction<Integer, Integer> {
    @Override
    public void processElement(Integer integer, Context context, Collector<Integer> collector) throws Exception {
        collector.collect(integer);
    }
}
```
通过传递适当的参数并验证输出，使用 ProcessFunctionTestHarnesses 进行单元测试会更加容易：
```java
public class ProcessFunctionUnitTest {
    @Test
    public void testPassThrough() throws Exception {

        MyProcessFunction processFunction = new MyProcessFunction();

        OneInputStreamOperatorTestHarness<Integer, Integer> testHarness = ProcessFunctionTestHarnesses
                .forProcessFunction(processFunction);

        testHarness.processElement(1, 10);
        Assert.assertEquals(
                Lists.newArrayList(
                        new StreamRecord<>(1, 10)
                ),
                testHarness.extractOutputStreamRecords()
        );
    }
}
```
有关如何使用 ProcessFunctionTestHarnesses 测试 ProcessFunction 不同风味（例如 KeyedProcessFunction，KeyedCoProcessFunction，BroadcastProcessFunction等）的更多示例，，可以参阅 [ProcessFunctionTestHarnessesTest](https://github.com/apache/flink/blob/d31bd5af28def3de4e353bb1e667eb7f2973ab6a/flink-streaming-java/src/test/java/org/apache/flink/streaming/util/ProcessFunctionTestHarnessesTest.java)：
```java
public static <IN, OUT> OneInputStreamOperatorTestHarness<IN, OUT> forProcessFunction(ProcessFunction<IN, OUT> function) throws Exception {
}

public static <K, IN, OUT> KeyedOneInputStreamOperatorTestHarness<K, IN, OUT> forKeyedProcessFunction(KeyedProcessFunction<K, IN, OUT> function, KeySelector<IN, K> keySelector, TypeInformation<K> keyType) throws Exception {
}

public static <IN1, IN2, OUT> TwoInputStreamOperatorTestHarness<IN1, IN2, OUT> forCoProcessFunction(CoProcessFunction<IN1, IN2, OUT> function) throws Exception {
}

public static <K, IN1, IN2, OUT> KeyedTwoInputStreamOperatorTestHarness<K, IN1, IN2, OUT> forKeyedCoProcessFunction(KeyedCoProcessFunction<K, IN1, IN2, OUT> function, KeySelector<IN1, K> keySelector1, KeySelector<IN2, K> keySelector2, TypeInformation<K> keyType) throws Exception {
}

public static <IN1, IN2, OUT> BroadcastOperatorTestHarness<IN1, IN2, OUT> forBroadcastProcessFunction(BroadcastProcessFunction<IN1, IN2, OUT> function, MapStateDescriptor... descriptors) throws Exception {
}

public static <K, IN1, IN2, OUT> KeyedBroadcastOperatorTestHarness<K, IN1, IN2, OUT> forKeyedBroadcastProcessFunction(KeyedBroadcastProcessFunction<K, IN1, IN2, OUT> function, KeySelector<IN1, K> keySelector, TypeInformation<K> keyType, MapStateDescriptor... descriptors) throws Exception {
}
```


> 上述示例代码[点此查看](https://github.com/sjf0115/data-example/tree/master/flink-example/src/test/java/com/flink/example/test)

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

参考：
- [Testing](https://ci.apache.org/projects/flink/flink-docs-release-1.11/dev/stream/testing.html)
-  [A Guide for Unit Testing in Apache Flink](https://flink.apache.org/news/2020/02/07/a-guide-for-unit-testing-in-apache-flink.html)
