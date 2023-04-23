## 1. RuntimeContext

可以通过 RuntimeContext 方法访问 KeyedState：
```java
public static class TemperatureAlertFlatMapFunction extends RichFlatMapFunction<Tuple2<String, Double>, Tuple3<String, Double, Double>> {
    private double threshold;
    private ValueState<Double> lastTemperatureState;
    public TemperatureAlertFlatMapFunction(double threshold) {
        this.threshold = threshold;
    }

    @Override
    public void open(Configuration parameters) throws Exception {
        ValueStateDescriptor<Double> stateDescriptor = new ValueStateDescriptor<>("lastTemperature", Double.class);
        lastTemperatureState = getRuntimeContext().getState(stateDescriptor);
    }

    @Override
    public void flatMap(Tuple2<String, Double> sensor, Collector<Tuple3<String, Double, Double>> out) throws Exception {
        double temperature = sensor.f1;
        Double lastTemperature = this.lastTemperatureState.value();
        lastTemperatureState.update(temperature);
        ...
    }
}
```

如果有状态函数正在从某 Checkpoint 恢复或者从某保存点重启，那么当函数注册状态描述符 StateDescriptor 时，Flink 会检查状态后端是否存储存储了函数相关的数据以及与给定名称、类型匹配的状态。无论上述哪种原因，Flink 都会将新注册的状态引用对象与已有的状态建立关联。如果状态后端没有包含给定状态描述的对应状态，那么系统会将状态引用对象所关联的状态初始化为空。


## 1.2 示例

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
从上面可以看到传感器 1 连续上传了两次温度，并且温度变化超过了10°，所以会发出报警。当传感器 2 上传温度后出现了脏数据，导致作业重启并进行作业状态的恢复。此时，传感器 1 上传了一次温度，与上次温度相比变化也超过了 10°，也会发出报警。从侧面证明了传感器 1 保留在状态中的上一次温度在作业重启之后进行了恢复(重新恢复到 20.8°)。当传感器 2 再次上传温度时，被认作是首次上传不做温度变化阈值判断，这是为什么吗呢？细致看一下输出日志，可以发现出现脏数据后作业重启并将作业状态恢复到最近一次 Checkpoint（ID 为 2）生成的快照状态。传感器 2 的第一次温度上传是发生在 Checkpoint 2 和出现脏数据之间，导致这一次的上传温度丢失，所以传感器 2 再次上传温度 37.2 时，被认做了是第一次上传。

## 2. CheckpointedFunction









。。。
