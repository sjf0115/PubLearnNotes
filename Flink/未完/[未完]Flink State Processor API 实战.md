

```

```

## 2. 读取状态

读取状态首先指定有效的 Savepoint 或者 Checkpoint 的路径以及用于恢复数据的 StateBackend。恢复状态的兼容性保证与恢复 DataStream 应用程序时的兼容性保证相同。
```java
ExecutionEnvironment bEnv   = ExecutionEnvironment.getExecutionEnvironment();
ExistingSavepoint savepoint = Savepoint.load(bEnv, "hdfs://path/", new MemoryStateBackend());
```

### 2.1 Operator State

Operator State 是 Flink 中的任何非键控状态。这包括但不限于在应用程序中对 CheckpointedFunction 或 BroadcastState 的任何使用。读取 Operator State 时，用户指定算子 uid、状态名称和类型信息。

#### 2.1.1 Operator List State

使用 getListState 存储在 CheckpointedFunction 中的 Operator State 可以使用 ExistingSavepoint#readListState 读取。状态名称和类型信息需要与声明此状态的 ListStateDescriptor 中定义的信息相匹配。

```java
DataSet<Integer> listState  = savepoint.readListState("my-uid", "list-state", Types.INT);
```

#### 2.1.2 Operator Union List State

使用 getUnionListState 存储在 CheckpointedFunction 中的 Operator State 可以使用 ExistingSavepoint#readUnionState 读取。状态名称和类型信息需要与声明此状态的 ListStateDescriptor 中定义的信息相匹配。框架会返回该状态的一个副本，相当于用并行度 1 来恢复一个 DataStream。
```java
DataSet<Integer> listState  = savepoint.readUnionState("my-uid", "union-state", Types.INT);
```

#### 2.1.3 Broadcast State

可以使用 ExistingSavepoint#readBroadcastState 读取 BroadcastState。状态名和类型信息需要与声明该状态的 MapStateDescriptor 中定义的信息相匹配。框架会返回状态的一个副本，相当于用并行度 1 来恢复一个 DataStream。
```java
DataSet<Tuple2<Integer, Integer>> broadcastState = savepoint.readBroadcastState("my-uid", "broadcast-state", Types.INT, Types.INT);
```

#### 2.1.4 使用自定义序列化器

每个 Operator State 读取器都支持使用自定义的 Typeserializer 来定义状态描述符。
```java
DataSet<Integer> listState = savepoint.readListState("uid", "list-state", Types.INT, new MyCustomIntSerializer());
```

### 2.2 Keyed State



### 2.3 Window State

## 3. 写入新的 Savepoint

### 3.1 Operator State

### 3.2 Keyed State

### 3.3 Window State

### 3.4 Broadcast State

## 4. 修改 Savepoint
