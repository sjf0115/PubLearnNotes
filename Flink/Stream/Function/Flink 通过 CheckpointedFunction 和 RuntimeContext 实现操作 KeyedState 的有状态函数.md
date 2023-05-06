上一篇文章 [Flink 通过 ListCheckpointed 和 CheckpointedFunction 实现操作 OperatorState 的有状态函数](https://smartsi.blog.csdn.net/article/details/130298767) 中介绍了如何使用 ListCheckpointed 和 CheckpointedFunction 实现操作 OperatorState 的有状态函数，在这篇文章中我们来介绍如何通过 RuntimeContext 和 CheckpointedFunction 实现操作 KeyedState 的有状态函数。

用户函数可以通过 KeyedState 来存储和访问当前 Key 上下文中的状态。对于每一个 Key，Flink 都会维护一个状态实例。函数的 KeyedState 实例会分布在函数所在算子的所有并行任务上。这意味着每个函数的并行实例都会负责一部分 Key 域并维护相应的状态实例。有关 KeyedState 的详细描述可以参阅 [Flink 状态分类](https://smartsi.blog.csdn.net/article/details/123296073)。

## 1. RuntimeContext

### 1.1 RuntimeContext 操作 KeyedState

首先介绍一下如何通过 RuntimeContext 来操作 KeyedState 从而实现一个有状态函数。要想获取 RuntimeContext，首先继承一个富函数 RichFunction 获取用于访问执行函数的上下文的 getRuntimeContext 方法。通过 getRuntimeContext 方法获取的 RuntimeContext 在 Flink 运行时中注册一个状态描述符 StateDescriptor。每个状态原语都有自己特定的状态描述符 StateDescriptor，它里面包含了状态名称和类型。状态名称的作用域是整个算子，可以通过在函数内注册多个状态描述符来创建多个状态对象。状态处理的数据类型可以通过 Class 或者 TypeInformation 对象指定。通常情况状态对象需要在 RichFunction 的 `open()` 方法中进行初始化。该方法会在任意处理方法之前调用。我们一般会将状态对象声明为函数类的普通成员变量。需要注意的是状态对象(或者叫状态引用对象，只提供状态访问的接口而不会存储状态本身，具体保存需要由状态后端来完成)。如下所示声明一个 ValueState 状态对象：
```java
// 声明为函数类的普通成员变量
private ValueState<Double> lastTemperatureState;
@Override
public void open(Configuration parameters) throws Exception {
    // 在 RichFunction 的 `open()` 方法中进行初始化
    ValueStateDescriptor<Double> stateDescriptor = new ValueStateDescriptor<>("lastTemperature", Double.class);
    lastTemperatureState = getRuntimeContext().getState(stateDescriptor);
}
```

> 关于富函数 RichFunction 的详细信息可以参阅[Flink DataStream 富函数 RichFunction](https://smartsi.blog.csdn.net/article/details/130191889)

需要注意的是，如果有状态函数正在从某 Checkpoint 恢复或者从某保存点重启，那么当函数注册状态描述符 StateDescriptor 时，Flink 会检查状态后端是否存储存储了函数相关的数据以及与给定名称、类型匹配的状态。无论上述哪种原因，Flink 都会将新注册的状态引用对象与已有的状态建立关联。如果状态后端没有包含给定状态描述的对应状态，那么系统会将状态引用对象所关联的状态初始化为空。

## 1.2 示例

我们通过一个具体的示例来看看如何通过 RuntimeContext 来操作 KeyedState 从而实现一个有状态函数。如下所示示例，在检测到相邻的两个传感器上报温度值变化超过给定阈值时就发出报警信息：
```java
public class RuntimeContextExample {
    private static final Logger LOG = LoggerFactory.getLogger(RuntimeContextExample.class);

    public static void main(String[] args) throws Exception {
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.setParallelism(2);

        // 每10s一次Checkpoint
        env.enableCheckpointing(30 * 1000);

        // Socket 输入
        DataStream<String> stream = env.socketTextStream("localhost", 9100, "\n");

        // 传感器温度流
        DataStream<Tuple3<String, Double, Double>> alertStream = stream.map(new MapFunction<String, Tuple2<String, Double>>() {
            @Override
            public Tuple2<String, Double> map(String value) throws Exception {
                if(Objects.equals(value, "ERROR")) {
                    throw new RuntimeException("error dirty data");
                }
                String[] params = value.split(",");
                LOG.info("sensor input, id: {}, temperature: {}", params[0], params[1]);
                return new Tuple2<>(params[0], Double.parseDouble(params[1]));
            }
        }).keyBy(new KeySelector<Tuple2<String, Double>, String>() {
            @Override
            public String getKey(Tuple2<String, Double> sensor) throws Exception {
                return sensor.f0;
            }
        }).flatMap(new TemperatureAlertFlatMapFunction(10));// 温度变化超过10度则报警
        alertStream.print();

        env.execute("RuntimeContextExample");
    }

    // FlatMap 的好处是在温度变化不超过阈值的时候不进行输出
    public static class TemperatureAlertFlatMapFunction extends RichFlatMapFunction<Tuple2<String, Double>, Tuple3<String, Double, Double>> {
        // 温度差报警阈值
        private double threshold;
        // 上一次温度
        private ValueState<Double> lastTemperatureState;
        public TemperatureAlertFlatMapFunction(double threshold) {
            this.threshold = threshold;
        }

        @Override
        public void open(Configuration parameters) throws Exception {
            // 初始化
            ValueStateDescriptor<Double> stateDescriptor = new ValueStateDescriptor<>("lastTemperature", Double.class);
            lastTemperatureState = getRuntimeContext().getState(stateDescriptor);
        }

        @Override
        public void flatMap(Tuple2<String, Double> sensor, Collector<Tuple3<String, Double, Double>> out) throws Exception {
            String sensorId = sensor.f0;
            // 当前温度
            double temperature = sensor.f1;

            // 上一次温度
            Double lastTemperature = this.lastTemperatureState.value();
            // 获取新的温度之后更新上一次的温度
            lastTemperatureState.update(temperature);
            if (Objects.equals(lastTemperature, null)) {
                LOG.info("sensor first temperature, id: {}, temperature: {}", sensorId, temperature);
                return;
            }

            double diff = Math.abs(temperature - lastTemperature);
            if (diff > threshold) {
                // 温度变化超过阈值
                LOG.info("sensor alert, id: {}, temperature: {}, lastTemperature: {}, diff: {}", sensorId, temperature, lastTemperature, diff);
                out.collect(Tuple3.of(sensorId, temperature, diff));
            } else {
                LOG.info("sensor no alert, id: {}, temperature: {}, lastTemperature: {}, diff: {}", sensorId, temperature, lastTemperature, diff);
            }
        }
    }
}
```
为了模拟脏数据异常 Failover，在 flatMap 处理中判断出现的单词是否是 `ERROR`，如果是则抛出一个运行时异常导致作业 Failover 异常重启。在这我们实现了一个 TemperatureAlertFlatMapFunction，每个传感器上报的相邻温度值变化如果超过了阈值10度则输出报警信息。TemperatureAlertFlatMapFunction 继承 RichFlatMapFunction 的目的是获取 RuntimeContext 来注册状态描述符来创建状态对象 lastTemperatureState，来保存该传感器上一个温度值。如下所示是传感器上报温度之后的具体运行信息(经过裁剪)：
```java
07:54:56,105 INFO  [] - sensor input, id: 1, temperature: 35.4
07:54:56,206 INFO  [] - sensor first temperature, id: 1, temperature: 35.4
07:54:59,092 INFO  [] - Triggering checkpoint 1
07:54:59,150 INFO  [] - Completed checkpoint 1
07:55:03,639 INFO  [] - sensor input, id: 1, temperature: 20.8
07:55:03,730 INFO  [] - sensor alert, id: 1, temperature: 20.8, lastTemperature: 35.4, diff: 14.599999999999998
1> (1,20.8,14.599999999999998)
07:55:29,074 INFO  [] - Triggering checkpoint 2
07:55:29,084 INFO  [] - Completed checkpoint 2
07:55:32,041 INFO  [] - sensor input, id: 2, temperature: 23.5
07:55:32,099 INFO  [] - sensor first temperature, id: 2, temperature: 23.5
07:55:37,014 WARN  org.apache.flink.runtime.taskmanager.Task                    [] - Map (2/2)#0 (82706eeb5bc7d5ec76c01876b7022662) switched from RUNNING to FAILED with failure cause: java.lang.RuntimeException: error dirty data
...
07:55:49,211 INFO  [] - sensor input, id: 1, temperature: 31.6
07:55:49,316 INFO  [] - sensor alert, id: 1, temperature: 31.6, lastTemperature: 20.8, diff: 10.8
1> (1,31.6,10.8)
07:55:57,285 INFO  [] - Triggering checkpoint 3
07:55:57,292 INFO  [] - Completed checkpoint 3
07:56:02,110 INFO  [] - sensor input, id: 2, temperature: 37.2
07:56:02,214 INFO  [] - sensor first temperature, id: 2, temperature: 37.2
07:56:27,286 INFO  [] - Triggering checkpoint 4
07:56:27,290 INFO  [] - Completed checkpoint 4
```
从上面可以看到传感器 1 连续上传了两次温度，并且温度变化超过了10°，所以会输出报警信息。当传感器 2 上传温度后出现了脏数据，导致作业重启并进行作业状态的恢复。状态会恢复之后，传感器 1 又上传了一次温度，与上次温度相比变化也超过了 10°，也输出报警信息。从侧面证明了传感器 1 保留在状态中的上一次温度在作业重启之后进行了恢复(重新恢复到 20.8°)。当传感器 2 再次上传温度时，被认作是首次上传不做温度变化阈值判断，这是为什么吗呢？细致看一下输出日志，可以发现出现脏数据后作业重启并将作业状态恢复到最近一次 Checkpoint（ID 为 2）生成的快照状态。传感器 2 的第一次温度上传是发生在 Checkpoint 2 和出现脏数据之间，导致这一次的上传温度丢失，所以传感器 2 再次上传温度 37.2 时，被认做了是第一次上传。

> 完整代码请查阅：[RuntimeContextExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/function/stateful/RuntimeContextExample.java)

## 2. CheckpointedFunction

上一篇文章 [Flink 通过 ListCheckpointed 和 CheckpointedFunction 实现操作 OperatorState 的有状态函数](https://smartsi.blog.csdn.net/article/details/130298767) 中介绍了如何使用 CheckpointedFunction 实现操作 OperatorState 的有状态函数。CheckpointedFunction 是实现有状态转换函数的核心接口，不仅可以管理 OperatorState 也可以管理 KeyedState。在这我们主要介绍如何通过 CheckpointedFunction 接口实现操作 KeyedState 的有状态函数。同实现操作 OperatorState 的有状态函数一样，实现操作 KeyedState 的有状态函数也需要实现如下两个方法：
```java
public interface CheckpointedFunction {
    void snapshotState(FunctionSnapshotContext context) throws Exception;
    void initializeState(FunctionInitializationContext context) throws Exception;
}
```

### 2.1 initializeState

当第一次初始化函数或者因为故障重启需要从之前 Checkpoint 中恢复状态数据时会调用 `initializeState(FunctionInitializationContext)` 方法：
```java
public void initializeState(FunctionInitializationContext context) throws Exception {
    // 初始化
    ValueStateDescriptor<Double> stateDescriptor = new ValueStateDescriptor<>("lastTemperature", Double.class);
    lastTemperatureState = context.getKeyedStateStore().getState(stateDescriptor);
    if (context.isRestored()) {
        lastTemperature = lastTemperatureState.value();
    }
}
```
该方法通过 FunctionInitializationContext 提供了访问 KeyedStateStore 的能力。通过 context 的 `getKeyedStateStore()` 方法获取允许注册键值状态 KeyedState 的 KeyedStateStore。KeyedStateStore 则又提供了访问状态 State 存储数据结构的能力，例如 `org.apache.flink.api.common.state.ValueState` 或者 `org.apache.flink.api.common.state.ListState`。此外可以通过 `isRestored()` 来判断状态是否是从上一次执行的 Checkpoint 中恢复(如果是返回 true。对于无状态任务，该方法总是返回 false)。

### 2.2 snapshotState

每当触发 Checkpoint 生成转换函数的状态快照时就会调用 `snapshotState(FunctionSnapshotContext)` 方法。该方法通过 FunctionSnapshotContext 提供了访问检查点元数据的能力。此外需要确保检查点数据结构（在 initialization 方法中获取）是最新的，以便生成快照。如下所示，将最新数据存储在状态中生成快照：
```java
public void snapshotState(FunctionSnapshotContext context) throws Exception {
    // 获取最新的温度之后更新保存上一次温度的状态
    lastTemperatureState.update(lastTemperature);
}
```

### 2.3 示例

我们还是以在检测到相邻的两个传感器上报温度值变化超过给定阈值时就发出报警信息为例，看看如何通过 CheckpointedFunction 来操作 KeyedState 从而实现一个有状态函数：
```java
public class CheckpointedFunctionKSExample {
    private static final Logger LOG = LoggerFactory.getLogger(CheckpointedFunctionKSExample.class);

    public static void main(String[] args) throws Exception {
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.setParallelism(2);

        // 每10s一次Checkpoint
        env.enableCheckpointing(30 * 1000);

        // Socket 输入
        DataStream<String> stream = env.socketTextStream("localhost", 9100, "\n");

        // 传感器温度流
        DataStream<Tuple3<String, Double, Double>> alertStream = stream.map(new MapFunction<String, Tuple2<String, Double>>() {
            @Override
            public Tuple2<String, Double> map(String value) throws Exception {
                if(Objects.equals(value, "ERROR")) {
                    throw new RuntimeException("error dirty data");
                }
                String[] params = value.split(",");
                LOG.info("sensor input, id: {}, temperature: {}", params[0], params[1]);
                return new Tuple2<>(params[0], Double.parseDouble(params[1]));
            }
        }).keyBy(new KeySelector<Tuple2<String, Double>, String>() {
            @Override
            public String getKey(Tuple2<String, Double> sensor) throws Exception {
                return sensor.f0;
            }
        }).flatMap(new TemperatureAlertFlatMapFunction(10));// 温度变化超过10度则报警
        alertStream.print();

        env.execute("CheckpointedFunctionKSExample");
    }

    // FlatMap 的好处是在温度变化不超过阈值的时候不进行输出
    public static class TemperatureAlertFlatMapFunction implements CheckpointedFunction, FlatMapFunction<Tuple2<String, Double>, Tuple3<String, Double, Double>> {
        // 温度差报警阈值
        private double threshold;
        // 上一次温度
        private ValueState<Double> lastTemperatureState;
        private Double lastTemperature;
        public TemperatureAlertFlatMapFunction(double threshold) {
            this.threshold = threshold;
        }

        @Override
        public void flatMap(Tuple2<String, Double> sensor, Collector<Tuple3<String, Double, Double>> out) throws Exception {
            String sensorId = sensor.f0;
            // 当前温度
            double temperature = sensor.f1;
            // 是否有保存上一次的温度
            if (Objects.equals(lastTemperature, null)) {
                LOG.info("sensor first temperature, id: {}, temperature: {}", sensorId, temperature);
                return;
            }
            double diff = Math.abs(temperature - lastTemperature);
            if (diff > threshold) {
                // 温度变化超过阈值
                LOG.info("sensor alert, id: {}, temperature: {}, lastTemperature: {}, diff: {}", sensorId, temperature, lastTemperature, diff);
                out.collect(Tuple3.of(sensorId, temperature, diff));
            } else {
                LOG.info("sensor no alert, id: {}, temperature: {}, lastTemperature: {}, diff: {}", sensorId, temperature, lastTemperature, diff);
            }
            lastTemperature = temperature;
        }

        @Override
        public void snapshotState(FunctionSnapshotContext context) throws Exception {
            // 获取最新的温度之后更新保存上一次温度的状态
            lastTemperatureState.update(lastTemperature);
            LOG.info("sensor snapshotState, temperature: {}", lastTemperature);
        }

        @Override
        public void initializeState(FunctionInitializationContext context) throws Exception {
            // 初始化
            ValueStateDescriptor<Double> stateDescriptor = new ValueStateDescriptor<>("lastTemperature", Double.class);
            lastTemperatureState = context.getKeyedStateStore().getState(stateDescriptor);
            if (context.isRestored()) {
                lastTemperature = lastTemperatureState.value();
                LOG.info("sensor initializeState, lastTemperature: {}", lastTemperature);
            }
        }
    }
}
```
跟上面的示例一样，为了模拟脏数据异常 Failover，在 flatMap 处理中判断出现的单词是否是 `ERROR`，如果是则抛出一个运行时异常导致作业 Failover 异常重启。在这 TemperatureAlertFlatMapFunction 不再继承 RichFlatMapFunction 而是实现 FlatMapFunction 和 CheckpointedFunction 接口。核心是通过实现 FlatMapFunction 接口的 flatMap 方法完成连续两个温度值变化的判断，通过实现 CheckpointedFunction 接口的 `initializeState` 和 `snapshotState` 方法完成
状态的初始化以及保存。如下所示是传感器上报温度之后的具体运行信息(经过裁剪)：
```java
23:27:55,548 [] - sensor input, id: 1, temperature: 35.4
23:27:55,562 [] - sensor first temperature, subTask: 0, id: 1, temperature: 35.4
23:27:59,941 [] - Triggering checkpoint 1
23:27:59,960 [] - sensor snapshotState, subTask: 1, checkpointId: 1, temperature: null
23:27:59,961 [] - sensor snapshotState, subTask: 0, checkpointId: 1, temperature: 35.4
23:28:00,008 [] - Completed checkpoint 1
23:28:05,199 [] - sensor input, id: 1, temperature: 20.8
23:28:05,298 [] - sensor alert, subTask: 0, id: 1, temperature: 20.8, lastTemperature: 35.4, diff: 14.599999999999998
23:28:29,922 [] - Triggering checkpoint 2
23:28:29,925 [] - sensor snapshotState, subTask: 1, checkpointId: 2, temperature: null
23:28:29,925 [] - sensor snapshotState, subTask: 0, checkpointId: 2, temperature: 20.8
23:28:29,939 [] - Completed checkpoint 2
23:28:39,426 [] - sensor input, id: 2, temperature: 23.5
23:28:39,485 [] - sensor no alert, subTask: 0, id: 2, temperature: 23.5, lastTemperature: 20.8, diff: 2.6999999999999993
23:28:59,917 [] - Triggering checkpoint 3
23:28:59,920 [] - sensor snapshotState, subTask: 0, checkpointId: 3, temperature: 23.5
23:28:59,920 [] - sensor snapshotState, subTask: 1, checkpointId: 3, temperature: null
23:28:59,928 [] - Completed checkpoint 3
```




...
