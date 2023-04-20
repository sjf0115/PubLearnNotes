
在状态管理中介绍到状态可分为 KeyedState 和 OperateState 两类，Flink 提供多种接口来定义状态函数。

## 1. KeyedState 函数

Keyed State 总是与 key 相对应，即每个 Key 对应一个 State，并且只能在 KeyedStream 上的函数和算子中使用。KeyedStream 可以通过调用 DataStream.keyBy() 来获得。每个 KeyedState 在逻辑上唯一对应一个 `<并行算子实例，key>`，由于每个 key '只属于' 一个 KeyedOperator 的一个并行实例，我们可以简单地认为成 `<operator，key>`。

KeyedState 类似分布式 KV 存储，每个函数实例负责维护状态的一部分。KeyedState 只用于处理 KeyedStream 上的函数，Flink 提供如下 KeyedState 原语：
- ValueState<T>：维护单个值的状态，通过ValueState.value()和ValueState.update(T value)分别获取、更新状态。
- ListState<T>：以链表形式维护多个值的状态，通过ListState.add(T value)、ListState.addAll(List<T> values)添加值，通过ListState.get()获取到所有值的迭代器Iterable<T>，通过ListState.update(List<T> values)更新状态。
- MapState<K, V>：以map形式维护多个值的状态，提供get(K key)、put(K key, V value)、contains(K key)、 remove(K key)方法获取更新值。
- ReducingState<T>：和ListState类似，但没有addAll()和update()方法，通过ReduceFunction计算得到一个聚合结果value，通过get()方法返回只含有value的Iterable。
- AggregatingState<I, O>：和ReducingState类似，使用AggregateFunction计算得到一个结果value，通过get()方法返回只含有value的Iterable。
所有的状态原语通过State.clear()方法清空内容。代码TemperatureAlert.java演示如何使用状态保存上一个温度，并在温度差大于指定值时发出报警。

通过 StateDescriptor 对象获取状态句柄 xxxState，描述符包含状态名称和状态数据类型(Class或者TypeInformation)。状态数据类型必须指定，因为 Flink需要创建合适的序列化器。

通常状态句柄在 RichFunction 的 open() 方法中创建，它仅是状态句柄并不包含状态自身。当函数注册StateDescriptor后，Flink会从状态后端查找是否存在相同名称和类型的状态，如果有的话将状态句柄指向状态，否则返回空。



在访问上，Keyed State 通过 RuntimeContext 来访问，这需要算子是一个 Rich Function。首先我们必须创建状态描述符 StateDescriptor，包含了状态的名字（可以创建多个状态，必须有唯一的名称，以便引用它们），状态值的类型。根据需求我们可以创建一个 ValueStateDescriptor，ListStateDescriptor，ReducingStateDescriptor 或 MapStateDescriptor，下面我们创建一个 ValueStateDescriptor：
