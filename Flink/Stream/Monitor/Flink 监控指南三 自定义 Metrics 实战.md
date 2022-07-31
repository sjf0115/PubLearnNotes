除了使用 Flink 系统自带的监控指标之外，用户也可以自定义监控指标。可以通过在 RichFunction 中调用 getRuntimeContext().getMetricGroup() 获取 MetricGroup 对象，然后将需要监控的指标记录在 MetricGroup 所支持的 Metric 中，然后就可以将自定义指标注册到 Flink 系统中。目前 Flink 支持 Counter、Gauge、Histogram 以及 Meter 四种类型的监控指标的注册和获取。

### 1. 注册 Metrics


#### 1.1 Counter

org.apache.flink.metrics.Counter 是最常用的一种 Metric，主要为了对指标进行计数类型的统计，且仅支持 Int 和 Long 数据类型。你可以通过调用 MetricGroup 对象上的 `counter(String name)` 来创建和注册 Counter。计数值可以通过使用 `inc()`/`inc(long n)` 或 `dec()`/`dec(long n)` 进行加减计算。如下代码所示实现了在 flatMap 方法中对进入到算子中的单词进行计数统计，得到 words-counter 监控指标：
```java
public static class WordsFlatMapFunction extends RichFlatMapFunction<String, String> {
    private transient Counter counter;
    @Override
    public void open(Configuration parameters) throws Exception {
        // 注册 Counter
        this.counter = getRuntimeContext()
                .getMetricGroup()
                .counter("words-counter");
    }
    @Override
    public void flatMap(String value, Collector<String> collector) throws Exception {
        for (String word : value.split("\\s")) {
            // 计数
            counter.inc();
            collector.collect(word);
        }
    }
}
```
或者，你也可以使用自定义 Counter：
```java
this.counter = getRuntimeContext()
      .getMetricGroup()
      .counter("custom-counter", new CustomCounter());
```




#### 1.2 Gauge

org.apache.flink.metrics.Gauge 是最简单的一种 Metric，主要用于单值更新，直接反映了数值变化，可以提供任何你需要的类型值。Gauge 相对于 Counter 指标更加通用，可以支持任何类型的数据记录和统计，且不限制返回的结果类型。为了使用 Gauge，你必须首先创建一个实现 `org.apache.flink.metrics.Gauge` 接口的类，返回值的类型没有限制。然后通过调用 MetricGroup 对象上的 `gauge(String name, Gauge gauge)` 来注册 Gauge。如下代码所示实现了在 flatMap 方法中对进入到算子中的单词进行计数统计，得到 words-gauge 监控指标：
```java
public static class WordsFlatMapFunction extends RichFlatMapFunction<String, String> {
    private transient int valueToExpose = 0;
    @Override
    public void open(Configuration parameters) throws Exception {
        // 注册 Gauge
        getRuntimeContext()
                .getMetricGroup()
                .gauge("words-gauge", new Gauge<Integer>() {
                    @Override
                    public Integer getValue() {
                        return valueToExpose;
                    }
                });
    }

    @Override
    public void flatMap(String value, Collector<String> collector) throws Exception {
        for (String word : value.split("\\s")) {
            // 展示所有单词个数
            valueToExpose++;
            collector.collect(word);
        }
    }
}
```


#### 1.3 Histogram

可以使用直方图表示数值类型数据的分布。Flink 的直方图特别适合用来展示 Long 类型的指标。你可以通过 org.apache.flink.metrics.Histogram 接口来收集数值，获取收集值的数量并为到目前为止收集的值生成统计信息（例如，最小值、最大值、标准差，均值等）。

你可以通过调用 MetricGroup 对象上调用 `histogram(String name, Histogram histogram)` 来注册一个 Histogram。但是 Flink 中没有默认的 Histograms 实现类，但提供了一个封装类 DropwizardHistogramWrapper，然后通过引入 Codahale/DropWizard Histograms 来完成数据分布指标的获取。注意，DropwizardHistogramWrapper 包装类并不在 Flink 默认依赖库中，需要单独引入如下 Maven 依赖：
```xml
<dependency>
      <groupId>org.apache.flink</groupId>
      <artifactId>flink-metrics-dropwizard</artifactId>
      <version>1.13.6</version>
</dependency>
```

如下代码所示，定义 histogramMapper 类实现 RichMapFunction 接口，使用 DropwizardHistogramWrapper 包装类转换 Codahale/DropWizard Histograms，统计 Map 函数中输入数据的分布情况，最终得到 words-histogram 监控指标：
```java
public static class WordsMapFunction extends RichMapFunction<String, Long> {
    private transient Histogram histogram;
    @Override
    public void open(Configuration parameters) throws Exception {
        // 创建 Codahale/DropWizard Histograms
        com.codahale.metrics.Histogram dropwizardHistogram =
                new com.codahale.metrics.Histogram(new SlidingWindowReservoir(500));
        // 使用 DropwizardHistogramWrapper 包装类转换
        this.histogram = getRuntimeContext()
                .getMetricGroup()
                .histogram("words-histogram", new DropwizardHistogramWrapper(dropwizardHistogram));
    }
    @Override
    public Long map(String value) throws Exception {
        Long v = Long.parseLong(value);
        // 更新直方图
        histogram.update(v);
        return v;
    }
}
```

#### 1.4 Meter

可以使用 Meter 来衡量某些事件发生的速率(每秒的事件数)。org.apache.flink.metrics.Meter 接口提供的方法用于标记一个或者多个事件发生、获取每秒事件发生的速率以及获取当前 Meter 标记的事件数目。

你可以通过在 MetricGroup 对象上调用 `meter(String name, Meter meter)` 来注册 Meter。与 Histograms 相同，Flink 中也没有提供默认的 Meter 实现，需要借助 Codahale/DropWizard Meters 实现，并通过 DropwizardMeterWrapper 包装类转换成 Flink 系统内部的 Meter。可以使用 `markEvent()` 方法注册一个事件的发生，如果同时发生多个事件可以使用 `markEvent(long n)` 方法进行注册。

如下代码所示，在实现的 RichFlatMapFunction 中定义 Meter 指标，并在 Meter 中使用 markEvent() 标记进入到函数中的单词，最终得到 words-histogram 监控指标：
```java
public static class WordsFlatMapFunction extends RichFlatMapFunction<String, String> {
    private transient Meter meter;
    @Override
    public void open(Configuration parameters) throws Exception {
        // 创建 Codahale/DropWizard Meter
        com.codahale.metrics.Meter dropwizardMeter = new com.codahale.metrics.Meter();
        // 使用 DropwizardHistogramWrapper 包装类转换
        this.meter = getRuntimeContext()
                .getMetricGroup()
                .meter("words-meter", new DropwizardMeterWrapper(dropwizardMeter));
    }

    @Override
    public void flatMap(String value, Collector<String> collector) throws Exception {
        String[] words = value.split("\\s");
        for (String word : words) {
            // 标记一个单词出现
            this.meter.markEvent();
            collector.collect(word);
        }
    }
}
``

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
