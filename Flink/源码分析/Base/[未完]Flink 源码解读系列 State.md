Flink state从层次上可以分为API层和Backend层，API层可以细分为外部State API和内部State API，Backend层又包括内存存储后端、文件存储后端以及RocksDB存储后端。

API部分：Flink将State API分为两部分：外部api(public state api)和内部api(internal state api)。外部API用于Flink应用程序的编程使用，内部API用于Flink内部使用。
外部State API定义了Flink所支持的各种State类型接口，比如ValueState、MapState等，与各State类型在一起的还有用于创建各state时的描述类，比如ValueStateDescriptor、MapStateDescriptor。外部API代码位于flink-core模块的org.apache.flink.api.common.state目录下面。
内部State API定义了Flink内部使用state的类型接口，比如InternalValueState、InternalMapState，内部api接口和外部api接口一一对应，并且内部api接口都继承了外部api的接口。内部api接口除了继承了外部api的接口方法，还定义了一些用于内部运行的辅助方法。内部API代码位于flink-runtime模块的org.apache.flink.runtime.state.internal目录下面。
Backend部分：Flink在做checkpoint时会将状态持久化到存储后端，来保证Failover后的状态一致性。Flink提供了三种存储后端：内存存储后端(MemoryStateBackend)、文件存储后端(FsStateBackend)和RocksDB存储后端(RocksDBStateBackend)。
MemoryStateBackend会将state数据存储在TaskManager的内存(JVM heap)中，如果没有开启FsStateBackend，则当做checkpoint时会将MemoryStateBackend中的数据同步到JobManager中(这时候JobManager就是存储后端了)。MemoryStateBackend代码位于flink-runtime模块的org.apache.flink.runtime.state.memory目录下面。
FsStateBackend会将state数据存储在TaskManager的内存中(JVM heap)中，当做checkpoint时会将状态数据同步到F是StateBackend所指定的存储目录下。FsStateBackend代码位于flink-runtime模块的org.apache.flink.runtime.state.filesystem目录下面。
RocksDBStateBackend会将state数据存储在RocksDB数据库中，由于RocksDB是单机嵌入式数据库，为了防止机器宕机后数据丢失，一般在做checkpoint时会将RocksDB存储的数据文件(sst文件、meta文件)上传到远程分布式文件系统中。RocksDBStateBackend并没有和MemoryStateBackend、FsStateBackend放在一起，而是在flink-state-backend模块下的flink-statebackend-rocksdb子模块下，位于org.apache.flink.contrib.streaming.state目录下面。

## 1. State API

Flink 中 State 相关的 API 主要分为两大类：
- flink-core 模块 org.apache.flink.api.common.state 包下的对外 API
- flink-runtime 模块 org.apache.flink.runtime.state.internal 包下的开发者 API：Internal API

对外 API 是对外部用户开放的稳定 API，我们需要使用这种 API 来开发应用程序。开发者 API（Internal API）是对内部开发者使用的 API，是不稳定的，可能会随着版本迁移发生变化。开发者 API（Internal API）在形式上继承了对外 API。

### 1.1 State

State 接口是 Keyed State 类型的顶级接口。实现 State 接口的状态只能由 KeyedStream 上的函数访问。状态的 Key 由系统自动提供，所以该类型下各种 State 都是当前 Key 对应的 Value(无论value、map还是list等等)。State 接口只定义了 clear() 方法用于删除当前 Key 对应的 Value 值：
```java
public interface State {
    void clear();
}
```
### 1.2 AppendingState

AppendingState 集成自 State 接口，是 KeyedState 的基础接口。AppendingState 提供了 get 和 add 两个方法：
```java
public interface AppendingState<IN, OUT> extends State {
    OUT get() throws Exception;
    void add(IN value) throws Exception;
}
```
添加进来的数据记录可以缓存在 Buffer (缓存在内存中，类似 List)中，也可以进行聚合。输出的状态类型 Out 不必和输入状态类型 IN 保持一致。

#### 1.2.1 MergingState

MergingState 是 AppendingState 的扩展接口，可以实现 State 的合并。目前只是一个标识接口，未定义任何实现：
```java
public interface MergingState<IN, OUT> extends AppendingState<IN, OUT> {}
```
可以允许两个 MergingState 实例进行合并，合并后的实例会包含被合并实例的所有状态信息。

#### 1.2.2 ListState

ListState 是 MergingState 的扩展接口，数据类型是一个 List。其中 MergingState 的 OUT 类型为 Iterable，即可以实现多个 State 的合并：
```java
public interface ListState<T> extends MergingState<T, Iterable<T>> {
    void update(List<T> var1) throws Exception;
    void addAll(List<T> var1) throws Exception;
}
```
ListState 提供了两个方法：update 和 addAll：
- update 会进行全量更新，如果传入 List 是 null 或者为空，则 ListState 会被清空。
- addAll 则是对现有列表状态进行更新，如果传入的是 null 或者为空，则不会对现有状态进行更新。

需要注意的是 ListState 相较其它 Keyed State 比较特殊，ListState 既可以是 Keyed ListState，也可以是 Operator ListState：
- 当它是 Keyed ListState 时，状态只能由 KeyedStream 上的函数访问。状态的 Key 由系统自动提供，所以该类型下各种 State 都是当前 Key 对应的 Value。
- 当它是 Operator ListState 时，该 List 是状态项的集合，这些状态项彼此独立，并且在算子并行度发生变化时可以跨算子实例重新分配。

#### 1.2.3 AggregatingState

AggregatingState 是 MergingState 的扩展接口，会对所有添加的元素通过 AggregateFunction 进行聚合。目前只是一个标识接口，未定义任何实现：
```java
public interface AggregatingState<IN, OUT> extends MergingState<IN, OUT> {}
```
通过 AggregateFunction 聚合后可以生成与输入数据不一样的数据类型，IN 表示聚合前 State 的数据类型，OUT 表示聚合后 State 的数据类型。

#### 1.2.4 ReducingState

ReducingState 是 MergingState 的扩展接口，会对添加的元素通过 ReduceFunction 进行聚合，最后合并到一个单一的状态值：
```java
public interface ReducingState<T> extends MergingState<T, T> {}
```
与 AggregatingState 通过 AggregateFunction 聚合不同的是，通过 ReduceFunction 聚合前后的数据类型 IN 和 OUT 是相同的。

### 1.3 ValueState

ValueState 是 State 的扩展接口，是类型为 T 的单值状态：
```java
public interface ValueState<T> extends State {
    T value() throws IOException;
    void update(T var1) throws IOException;
}
```
ValueState 定义了 value 和 update 两个方法。可以通过 update 方法更新状态值，通过 value 方法获取状态值。

### 1.4 MapState

MapState 是 State 的扩展接口，使用 Map 存储 Key-Value 对：
```java
public interface MapState<UK, UV> extends State {
    UV get(UK key) throws Exception;
    void put(UK key, UV value) throws Exception;
    void putAll(Map<UK, UV> map) throws Exception;
    void remove(UK key) throws Exception;
    boolean contains(UK key) throws Exception;
    Iterable<Map.Entry<UK, UV>> entries() throws Exception;
    Iterable<UK> keys() throws Exception;
    Iterable<UV> values() throws Exception;
    Iterator<Map.Entry<UK, UV>> iterator() throws Exception;
    boolean isEmpty() throws Exception;
}
```
通过 put(UK,UV) 或者 putAll(Map<UK,UV>) 来添加，使用 get(UK) 来获取。

### 1.5 BroadcastState

ReadOnlyBroadcastState 是一个只读定义接口。ReadOnlyBroadcastState定了三个方法：get、contains和immutableEntries。对于get和immutableEntries返回的结果，用户不应该对其修改，否则会引发状态的不一致性(之所以没有直接返回副本，主要考虑性能原因)。

```java
public interface ReadOnlyBroadcastState<K, V> extends State {
    V get(K key) throws Exception;
    boolean contains(K key) throws Exception;
    Iterable<Map.Entry<K, V>> immutableEntries() throws Exception;
}
```
BroadcastState使用依赖于BroadcastStream广播流，当需要广播规则、配置等低吞吐的事件流到下游所有task时，下游task使用BroadcastState存储这里规则、配置等。BroadcastState假设上游广播的元素会发送给当前operator的所有实例上。

BroadcastState在方法定义上和MapState非常类似，定了put、putAll、remove、iterator和entries方法。

BroadcastState继承了ReadOnlyBroadcastState接口。

```java
public interface BroadcastState<K, V> extends ReadOnlyBroadcastState<K, V> {
    void put(K var1, V var2) throws Exception;
    void putAll(Map<K, V> var1) throws Exception;
    void remove(K var1) throws Exception;
    Iterator<Map.Entry<K, V>> iterator() throws Exception;
    Iterable<Map.Entry<K, V>> entries() throws Exception;
}
```

## 2. Internal API

用于runtime内部的Internal api位于flink-runtime的org.apache.flink.runtime.state.internal包下面。每种类型的internal api都实现了对应的public api，比如InternalValueState -> ValueState、InternalMapSate -> MapSate、InternalListState -> ListState。

我们通过上面的依赖图可以看到Internal api除了继承对应的public api，还都继承了InternalKvState。InternalKvState是Internal api的root接口，类似Public api的State接口。


### 2.1 InternalKvState

InternalKvState 提供了 Internal state 要实现的方法，主要是getKeySerializer、getValueSerializer、getNamespaceSerializer、setCurrentNamespace和getSerializedValue。其中getSerializedValue会被多线程访问，所以需要保证线程安全。除此之外，还定义了子接口StateIncrementalVisitor，StateIncrementalVisitor提供了操作一组StateEntry的方法。

```java
public interface InternalKvState<K, N, V> extends State {
    TypeSerializer<K> getKeySerializer();
    TypeSerializer<N> getNamespaceSerializer();
    TypeSerializer<V> getValueSerializer();
    void setCurrentNamespace(N var1);
    byte[] getSerializedValue(byte[] var1, TypeSerializer<K> var2, TypeSerializer<N> var3, TypeSerializer<V> var4) throws Exception;
    StateIncrementalVisitor<K, N, V> getStateIncrementalVisitor(int var1);
    public interface StateIncrementalVisitor<K, N, V> {
        boolean hasNext();
        Collection<StateEntry<K, N, V>> nextEntries();
        void remove(StateEntry<K, N, V> var1);
        void update(StateEntry<K, N, V> var1, V var2);
    }
}
```

### 2.2 InternalAppendingState

InternalAppendingState 继承了 InternalKvState 和 AppendingState。

K：KVState中的key类型
N：namespace的数据类型
IN：输入元素的数据类型
SV：KVState中的value类型，SV是state value的缩写，也就是代表状态数据在state内的数据类型
OUT：输出元素的数据类型

```java
public interface InternalAppendingState<K, N, IN, SV, OUT> extends InternalKvState<K, N, SV>, AppendingState<IN, OUT> {
    SV getInternal() throws Exception;
    void updateInternal(SV var1) throws Exception;
}
```

#### 2.2.1 InternalMergeingState

InternalMergeingState 继承了 InternalAppendingState 和 MergingState 接口：
```java
public interface InternalMergingState<K, N, IN, SV, OUT> extends InternalAppendingState<K, N, IN, SV, OUT>, MergingState<IN, OUT> {
    void mergeNamespaces(N var1, Collection<N> var2) throws Exception;
}
```
InternalMergingState 定义了一个 mergeNamespaces 方法，用于将给定 namespace 的 state 合并到目标 namespace 里。

#### 2.2.2 InternalAggregatingState

InternalAggregatingState 继承了 InternalMergingState 和 AggregatingState 接口:
```java
public interface InternalAggregatingState<K, N, IN, SV, OUT> extends InternalMergingState<K, N, IN, SV, OUT>, AggregatingState<IN, OUT> {
}
```
#### 2.2.3 InternalListState

InternalListState 继承了 InternalMergingState 和 ListState 接口：
```java
public interface InternalListState<K, N, T> extends InternalMergingState<K, N, T, List<T>, Iterable<T>>, ListState<T> {
    void update(List<T> var1) throws Exception;
    void addAll(List<T> var1) throws Exception;
}
```
InternalListState 定义了 update 和 addAll 方法。个人感觉这里没必要定义，因为和 ListState 定义一样(包括方法描述)。

### 2.3 InternalValueState

InternalValueState 直接继承了 InternalKvState 和 ValueState 接口：
```java
public interface InternalValueState<K, N, T> extends InternalKvState<K, N, T>, ValueState<T> {
}
```
### 2.4 InternalMapState

InternalMapState 直接继承了 InternalKvState 和 MapState 接口:
```java
public interface InternalMapState<K, N, UK, UV> extends InternalKvState<K, N, Map<UK, UV>>, MapState<UK, UV> {
}
```
其中UK、UV代表Map的KV数据类型。

## 3. Descriptor

对于可供flink application直接使用的state，在获取对应state时需要使用对应的Descriptor来描述State，比如ValueStateDescriptor、MapStateDescriptor。下面我们首先看下Descriptor的抽象基类 StateDescriptor:
```java
public abstract class StateDescriptor<S extends State, T> implements Serializable {
    // 所支持的 State 类型
    public enum Type {
        @Deprecated
        UNKNOWN,
        VALUE,
        LIST,
        REDUCING,
        FOLDING,
        AGGREGATING,
        MAP
    }
}
```
S 是 StateDescriptor 所支持的 State 类型，必须是 State 的子类，T 是 value 的类型。

### 3.1 ValueStateDescriptor

ValueStateDescriptor 是 ValueState 所对应的 StateDescriptor。ValueStateDescriptor 只是指定了构造方法以及对应的 State 类型，其它默认都继承自 StateDescriptor：

```java
public class ValueStateDescriptor<T> extends StateDescriptor<ValueState<T>, T> {
    public ValueStateDescriptor(String name, Class<T> typeClass) {
        super(name, typeClass, null);
    }

    public ValueStateDescriptor(String name, TypeInformation<T> typeInfo) {
        super(name, typeInfo, null);
    }

    public ValueStateDescriptor(String name, TypeSerializer<T> typeSerializer) {
        super(name, typeSerializer, null);
    }

    @Override
    public Type getType() {
        // 对应 ValueState
        return Type.VALUE;
    }
}
```

### 3.2 AggregatingStateDescriptor

AggregatingStateDescriptor 是 AggregatingState 所对应的 StateDescriptor。对于 AggregatingState、FoldingState 这类聚合类 State，需要指定聚合的 Function 给对应的 Descriptor。
```java
public class AggregatingStateDescriptor<IN, ACC, OUT> extends StateDescriptor<AggregatingState<IN, OUT>, ACC> {

    private final AggregateFunction<IN, ACC, OUT> aggFunction;

    public AggregatingStateDescriptor(
            String name, AggregateFunction<IN, ACC, OUT> aggFunction, Class<ACC> stateType) {

        super(name, stateType, null);
        this.aggFunction = checkNotNull(aggFunction);
    }

    public AggregatingStateDescriptor(
            String name,
            AggregateFunction<IN, ACC, OUT> aggFunction,
            TypeInformation<ACC> stateType) {

        super(name, stateType, null);
        this.aggFunction = checkNotNull(aggFunction);
    }

    public AggregatingStateDescriptor(
            String name,
            AggregateFunction<IN, ACC, OUT> aggFunction,
            TypeSerializer<ACC> typeSerializer) {

        super(name, typeSerializer, null);
        this.aggFunction = checkNotNull(aggFunction);
    }

    public AggregateFunction<IN, ACC, OUT> getAggregateFunction() {
        return aggFunction;
    }

    @Override
    public Type getType() {
        //
        return Type.AGGREGATING;
    }
}
```
IN 代表输入到AggregatingState的数据类型。

OUT代表从AggregatingState中获取的数据类型。

ACC代表中间的聚合状态类型。

### 3.3

## 4. Operator State

我们知道Flink将state分为Keyed state和Operator state，而Operator state相较KeyedState简单很多。通过OperatorStateStore定义Operator state所支持的state类型，Operator state目前只提供了BroadcastState和ListState。

...
