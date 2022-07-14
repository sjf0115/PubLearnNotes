Flink公开了一个度量指标系统，允许收集和显示度量指标给外部系统。

### 1. 注册Metrics

你可以通过在继承`RichFunction`的用户自定义函数中调用`getRuntimeContext().getMetricGroup()`来访问度量系统。此方法返回一个`MetricGroup`对象，你可以使用它创建并注册新的度量指标。

下面说一下度量指标类型。Flink支持计数器(Counters)，量表(Gauges)，直方图(Histograms)和仪表(Meters)。

#### 1.1 Counter

计数器用来计算一些东西。当前值可以通过使用`inc()`/`inc(long n)`或`dec()`/`dec(long n)`进行加减计算。你可以通过调用`MetricGroup`对象上的`counter(String name)`来创建和注册计数器。

```java
public class MyMapper extends RichMapFunction<String, Integer> {
  private Counter counter;

  @Override
  public void open(Configuration config) {
    this.counter = getRuntimeContext().getMetricGroup().counter("myCounter");
  }

  @Override
  public Integer map(String value) throws Exception {
    this.counter.inc();
  }
}
```

或者，你也可以使用自定义Counter：
```java
public class MyMapper extends RichMapFunction<String, Integer> {
  private Counter counter;

  @Override
  public void open(Configuration config) {
    this.counter = getRuntimeContext().getMetricGroup().counter("myCustomCounter", new CustomCounter());
  }
}
```

#### 1.2 Gauge

Gauge提供了任何你需要类型的值(A Gauge provides a value of any type on demand)。为了使用Gauge，你必须首先创建一个实现`org.apache.flink.metrics.Gauge`接口的类。返回值的类型没有限制。你可以通过调用`MetricGroup`对象上的gauge(String name, Gauge gauge）来注册Gauge。

Java版本:
```java
public class MyMapper extends RichMapFunction<String, Integer> {
  private int valueToExpose;
  @Override
  public void open(Configuration config) {
    getRuntimeContext().getMetricGroup()
      .gauge("MyGauge", new Gauge<Integer>() {
        @Override
        public Integer getValue() {
          return valueToExpose;
        }
      });
  }
}
```

Scala版本:
```
public class MyMapper extends RichMapFunction[String,Int] {
  val valueToExpose = 5

  override def open(parameters: Configuration): Unit = {
    getRuntimeContext()
      .getMetricGroup()
      .gauge("MyGauge", ScalaGauge[Int]( () => valueToExpose ) )
  }
  ...
}
```
备注:
```
请注意，reporter会将对象转换成一个字符串，这意味着必需实现一个有意义的toString()方法。
```

#### 1.3 Histogram

Histogram测量Long类型值的分布。你可以通过在`MetricGroup`对象上调用`histogram(String name, Histogram histogram)`来注册一个。

```java
public class MyMapper extends RichMapFunction<Long, Integer> {
  private Histogram histogram;

  @Override
  public void open(Configuration config) {
    this.histogram = getRuntimeContext().getMetricGroup()
      .histogram("myHistogram", new MyHistogram());
  }

  @Override
  public Integer map(Long value) throws Exception {
    this.histogram.update(value);
  }
}
```

Flink不提供Histogram的默认实现，但提供了一个封装，允许使用`Codahale`/`DropWizard`的Histogram。要使用这个封装，需要在你的pom.xml中添加下面的依赖项：
```
<dependency>
      <groupId>org.apache.flink</groupId>
      <artifactId>flink-metrics-dropwizard</artifactId>
      <version>1.3.2</version>
</dependency>
```
然后你可以像这样注册一个`Codahale`/`DropWizard` Histogram：
```java
public class MyMapper extends RichMapFunction<Long, Integer> {
  private Histogram histogram;

  @Override
  public void open(Configuration config) {
    com.codahale.metrics.Histogram histogram =
      new com.codahale.metrics.Histogram(new SlidingWindowReservoir(500));

    this.histogram = getRuntimeContext()
      .getMetricGroup()
      .histogram("myHistogram", new DropwizardHistogramWrapper(histogram));
  }
}

```

#### 1.4 Meter

Meter测量平均吞吐量。可以使用`markEvent()`方法注册事件的发生。同时发生多个事件可以使用`markEvent(long n)`方法进行注册。你可以通过在`MetricGroup`对象上调用`meter(String name, Meter meter)`来注册Meter。

```java
public class MyMapper extends RichMapFunction<Long, Integer> {
  private Meter meter;

  @Override
  public void open(Configuration config) {
    this.meter = getRuntimeContext()
      .getMetricGroup()
      .meter("myMeter", new MyMeter());
  }

  @Override
  public Integer map(Long value) throws Exception {
    this.meter.markEvent();
  }
}
```

Flink提供了一个封装，允许使用`Codahale`/`DropWizard` Meter。 要使用这个封装，在你的pom.xml中添加下面的依赖项：
```
<dependency>
      <groupId>org.apache.flink</groupId>
      <artifactId>flink-metrics-dropwizard</artifactId>
      <version>1.3.2</version>
</dependency>
```
然后你可以像这样注册一个`Codahale`/`DropWizard` Meter：
```java
public class MyMapper extends RichMapFunction<Long, Integer> {
  private Meter meter;

  @Override
  public void open(Configuration config) {
    com.codahale.metrics.Meter meter = new com.codahale.metrics.Meter();

    this.meter = getRuntimeContext()
      .getMetricGroup()
      .meter("myMeter", new DropwizardMeterWrapper(meter));
  }
}
```

### 2. 范围

每个度量指标都被分配一个标识符，并以这个标识符进行报告，它基于3个组件(Every metric is assigned an identifier under which it will be reported that is based on 3 components)：注册度量指标时用户提供的名称，可选的用户定义的作用域和系统提供的作用域。例如，如果`A.B`是系统作用域，`C.D`是用户作用域，`E`是名称，则度量指标的标识符是`A.B.C.D.E`.

你可以通过在`conf/flink-conf.yaml`中设置`metrics.scope.delimiter`配置项来配置标识符使用哪个分隔符(默认为:`.`)。

#### 2.1 用户作用域

你可以通过调用`MetricGroup.addGroup(String name)`或`MetricGroup.addGroup(int name)`来定义用户作用域。

```java
counter = getRuntimeContext()
  .getMetricGroup()
  .addGroup("MyMetrics")
  .counter("myCounter");
```

#### 2.2 系统作用域

系统作用域包含有关度量指标的上下文信息，例如，它在哪个任务中注册或该任务属于哪个作业等。

应该包含哪些上下文信息可以通过在`conf/flink-conf.yaml`中通过设置以下键进行配置。这些键中的每一个都应该是格式化字符串，可能包含常量(例如`taskmanager`)以及在运行时可以被替换的变量(例如`<task_id>`)的。

配置项|默认值|描述
---|---|---
metrics.scope.jm|`<host>.jobmanager`|适用于作业管理器范围内的所有度量指标
metrics.scope.jm.job|`<host>.jobmanager.<job_name>`|适用于作业管理器和作业的所有度量指标
metrics.scope.tm| `<host>.taskmanager.<tm_id>`|适用于指定任务管理器的所有度量指标
metrics.scope.tm.job|`<host>.taskmanager.<tm_id>.<job_name>`|适用于指定任务管理器和作业的所有度量指标
metrics.scope.task|`<host>.taskmanager.<tm_id>.<job_name>.<task_name>.<subtask_index>`|适用于指定任务的所有度量指标
metrics.scope.operator|`<host>.taskmanager.<tm_id>.<job_name>.<operator_name>.<subtask_index>`|适用于指定算子的所有度量指标

变量的数量或顺序没有限制。变量是区分大小写的。

算子指标的默认作用域将产生一个类似于下面的标识符:
```
localhost.taskmanager.1234.MyJob.MyOperator.0.MyMetric
```
如果你只想包含任务名称，省略任务管理器信息，则可以指定以下格式：
```
metrics.scope.operator: <host>.<job_name>.<task_name>.<operator_name>.<subtask_index>
```
```
This could create the identifier localhost.MyJob.MySource_->_MyOperator.MyOperator.0.MyMetric.
localhost.MyJob.MySource_->_MyOperator.MyOperator.0.MyMetric.
```

### 3. Reporter

### 4. 系统Metrics





原文:https://ci.apache.org/projects/flink/flink-docs-release-1.3/monitoring/metrics.html
