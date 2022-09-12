Transformation 表示创建 DataStream 的转换操作，是所有转换操作的抽象类，提供了实现转换操作的基础功能。每一个 DataStream 都有一个与之对应的 Transformation，可以通过转换操作生成新的 DataStream。

诸如 DataStream#map 之类的 API 操作会在底层创建一个 Transformation 树。当要执行流程序时，会使用 StreamGraphGenerator 转换为 StreamGraph。如下所示是一个 Transformation 树：
```
   Source              Source
      +                   +
      |                   |
      v                   v
  Rebalance          HashPartition
      +                   +
      |                   |
      |                   |
      +------>Union<------+
                +
                |
                v
              Split
                +
                |
                v
              Select
                +
                v
               Map
                +
                |
                v
              Sink
```
在运行时会生成如下操作图：
```
 Source              Source
   +                   +
   |                   |
   |                   |
   +------->Map<-------+
             +
             |
             v
            Sink
```
上面的 Partition、Union、Split 以及 Select Transformation 会最终被编码在连接 Source 和 Map 操作的边中。


下面我们具体看一下 Transformation：
```java
public abstract class Transformation<T> {
    public static final int UPPER_BOUND_MAX_PARALLELISM = 1 << 15;

    // 为 Transformation 生成唯一 ID
    protected static Integer idCounter = 0;
    public static int getNewNodeId() {
        idCounter++;
        return idCounter;
    }

    protected final int id;
    protected String name;
    protected TypeInformation<T> outputType;
    private String uid;
    protected long bufferTimeout = -1;
    private String slotSharingGroup;

    protected boolean typeUsed;
    private String userProvidedNodeHash;
    private int parallelism;
    private int maxParallelism = -1;

    private ResourceSpec minResources = ResourceSpec.DEFAULT;
    private ResourceSpec preferredResources = ResourceSpec.DEFAULT;
    private final Map<ManagedMemoryUseCase, Integer> managedMemoryOperatorScopeUseCaseWeights =
            new HashMap<>();
    private final Set<ManagedMemoryUseCase> managedMemorySlotScopeUseCases = new HashSet<>();
    @Nullable private String coLocationGroupKey;


    public Transformation(String name, TypeInformation<T> outputType, int parallelism) {
        this.id = getNewNodeId();
        this.name = Preconditions.checkNotNull(name);
        this.outputType = outputType;
        this.parallelism = parallelism;
        this.slotSharingGroup = null;
    }
}

```
核心属性如下：
- name：Transformation 的名称，这个主要用于可视化的目的
- uid：用户指定的uid，该uid的主要目的是用于在job重启时可以再次分配跟之前相同的uid，应该是用于持久保存状态的目的。
- bufferTimeout：buffer超时时间
- parallelism：并行度
- id：跟属性uid无关，它的生成方式是基于一个静态累加器
- outputType：输出类型
- slotSharingGroup：给当前的transformation设置slot共享组。slot sharing group用于将并行执行的operator“归拢”到相同的TaskManager slot中（slot概念基于资源的划分，因此这里的目的是让不同的subtask共享slot资源）

指定转换 Transformation 的名称 name，输出类型 outType 以及并行度 parallelism 就可以创建一个 Transformation：
```java
public Transformation(String name, TypeInformation<T> outputType, int parallelism) {
    this.id = getNewNodeId();
    this.name = Preconditions.checkNotNull(name);
    this.outputType = outputType;
    this.parallelism = parallelism;
    this.slotSharingGroup = null;
}
```

我们先来看 DataStream 之间的转换操作，Transformation 的实现看起来比较复杂，每种 Transformation 实现都和 DataStream 的接口方法对应。

Transformation 的实现子类涵盖了所有的 DataStream 转换操作。常用到的 StreamMap、StreamFilter 算子封装在 OneInputTransformation 中，也就是单输入类型的转换操作。常见的双输入类型算子有 join、connect 等，对应支持双输入类型转换的 TwoInputTransformation 操作。

## 1. PhysicalTransformation

在 Transformation 的基础上又抽象出了 PhysicalTransformation 类：
```java
public abstract class PhysicalTransformation<T> extends Transformation<T> {
    // 根据指定的名称、输出类型和并行度创建一个新的 Transformation
    PhysicalTransformation(String name, TypeInformation<T> outputType, int parallelism) {
        super(name, outputType, parallelism);
    }
    // 为 Transformation 设置链式策略
    public abstract void setChainingStrategy(ChainingStrategy strategy);
}
```
PhysicalTransformation 在 Transformation 的基础上又提供了 setChainingStrategy 方法，可以将上下游算子按照指定的策略连接。ChainingStrategy 支持如下三种策略：
- ALWAYS：代表该 Transformation 中的算子会和上游算子尽可能地链化，最终将多个 Operator 组合成 OperatorChain。OperatorChain 中的 Operator 会运行在同一个 SubTask 实例中，这样做的目的主要是优化性能，减少 Operator 之间的网络传输。
- NEVER：代表该 Transformation 中的 Operator 永远不会和上下游算子之间链化，因此对应的 Operator 会运行在独立的 SubTask 实例中。
- HEAD：代表该 Transformation 对应的 Operator 为头部算子，不支持上游算子链化，但是可以和下游算子链化，实际上就是 OperatorChain 中的 HeaderOperator。

通过以上策略可以控制算子之间的连接，在生成 JobGraph 时，ALWAYS 类型连接的 Operator 形成 OperatorChain。同一个 OperatorChain 中的 Operator 会运行在同一个 SubTask 线程中，从而尽可能地避免网络数据交换，提高计算性能。当然，用户也可以显性调用 disableChaining() 等方法，设定不同的 ChainingStrategy，实现对 Operator 之间物理连接的控制。

以下是支持设定 ChainingStrategy 的 PhysicalTransformation 操作类型，也就是继承了 PhysicalTransformation 抽象的实现类：
- SourceTransformation：数据集输入操作，调用 DataStream.addSource() 方法时，会创建 SourceTransformation 操作，用于从外部系统中读取数据并转换成DataStream数据集。
- SinkTransformation：数据集输出操作，当用户调用DataStream.addSink()方法时，会同步创建SinkTransformation操作，将DataStream中的数据输出到外部系统中。
- OneInputTransformation：单进单出的数据集转换操作，例如DataStream.map()转换。
- TwoInputTransformation：双进单出的数据集转换操作，例如在DataStream与DataStream之间进行Join操作，且该转换操作中的Operator类型为 TwoInputStreamOperator。

### 1.1 SourceTransformation

SourceTransformation 数据输入操作。调用 DataStream.addSource() 方法时，会创建 SourceTransformation 操作，用于从外部系统中读取数据并转换成 DataStream。在创建 SourceTransformation 的时候，除了指定 Transformation 名称、输出类型以及并行度之外，还需要指定 Watermark 策略 WatermarkStrategy 和真正执行处理的 Source：
```java
public class SourceTransformation<OUT, SplitT extends SourceSplit, EnumChkT>
        extends PhysicalTransformation<OUT> implements WithBoundedness {
    private final Source<OUT, SplitT, EnumChkT> source;
    private final WatermarkStrategy<OUT> watermarkStrategy;
    // 默认为 ALWAYS
    private ChainingStrategy chainingStrategy = ChainingStrategy.DEFAULT_CHAINING_STRATEGY;
    // 创建 SourceTransformation
    public SourceTransformation(
            String name,
            Source<OUT, SplitT, EnumChkT> source,
            WatermarkStrategy<OUT> watermarkStrategy,
            TypeInformation<OUT> outputType,
            int parallelism) {
        super(name, outputType, parallelism);
        this.source = source;
        this.watermarkStrategy = watermarkStrategy;
    }
    @Override
    public void setChainingStrategy(ChainingStrategy chainingStrategy) {
        this.chainingStrategy = checkNotNull(chainingStrategy);
    }
}
```

### 1.2 SinkTransformation

SinkTransformation 为数据输出操作。当用户调用 DataStream.addSink() 方法时，会同步创建 SinkTransformation 操作，将 DataStream 中的数据输出到外部系统中。在创建 SinkTransformation 的时候，除了指定上游 Transformation 以及名称和并行度之外，还需要指定真正执行处理的 Sink：
```java
public class SinkTransformation<InputT, CommT, WriterStateT, GlobalCommT>
        extends PhysicalTransformation<Object> {
    // 输入 Transformation
    private final Transformation<InputT> input;
    // Sink
    private final Sink<InputT, CommT, WriterStateT, GlobalCommT> sink;
    // 链式策略
    private ChainingStrategy chainingStrategy;
    // 创建 SinkTransformation
    public SinkTransformation(
            Transformation<InputT> input,
            Sink<InputT, CommT, WriterStateT, GlobalCommT> sink,
            String name,
            int parallelism) {
        super(name, TypeExtractor.getForClass(Object.class), parallelism);
        this.input = checkNotNull(input);
        this.sink = checkNotNull(sink);
    }
    // 设置链式策略
    @Override
    public void setChainingStrategy(ChainingStrategy strategy) {
        chainingStrategy = checkNotNull(strategy);
    }
    ...
}
```
SinkTransformation 本质上是输入 Transformation 以及将数据写入外部系统 Sink 的封装。

### 1.3 OneInputTransformation

OneInputTransformation 为只接收一个输入的操作。创建 OneInputTransformation 跟上面的 SinkTransformation 类似，需要指定输入 Transformation 以及真正处理的 OneInputStreamOperator：
```java
public class OneInputTransformation<IN, OUT> extends PhysicalTransformation<OUT> {
    private final Transformation<IN> input;
    private final StreamOperatorFactory<OUT> operatorFactory;
    private KeySelector<IN, ?> stateKeySelector;
    private TypeInformation<?> stateKeyType;

    public OneInputTransformation(
            Transformation<IN> input,
            String name,
            OneInputStreamOperator<IN, OUT> operator,
            TypeInformation<OUT> outputType,
            int parallelism) {
        this(input, name, SimpleOperatorFactory.of(operator), outputType, parallelism);
    }

    public OneInputTransformation(
            Transformation<IN> input,
            String name,
            StreamOperatorFactory<OUT> operatorFactory,
            TypeInformation<OUT> outputType,
            int parallelism) {
        super(name, outputType, parallelism);
        this.input = input;
        this.operatorFactory = operatorFactory;
    }

    @Override
    public final void setChainingStrategy(ChainingStrategy strategy) {
        operatorFactory.setChainingStrategy(strategy);
    }
    ...
}
```

### 1.4 TwoInputTransformation

TwoInputTransformation 为接收两个输入的操作。创建 TwoInputTransformation 跟上面的 OneInputTransformation 类似，不过需要指定两个输入 Transformation，OneInputStreamOperator 变成了 TwoInputStreamOperator：
```java
public class TwoInputTransformation<IN1, IN2, OUT> extends PhysicalTransformation<OUT> {
    private final Transformation<IN1> input1;
    private final Transformation<IN2> input2;
    private final StreamOperatorFactory<OUT> operatorFactory;
    private KeySelector<IN1, ?> stateKeySelector1;
    private KeySelector<IN2, ?> stateKeySelector2;
    private TypeInformation<?> stateKeyType;
    // 需要指定两个输入 Transformation 以及 TwoInputStreamOperator
    public TwoInputTransformation(
            Transformation<IN1> input1,
            Transformation<IN2> input2,
            String name,
            TwoInputStreamOperator<IN1, IN2, OUT> operator,
            TypeInformation<OUT> outputType,
            int parallelism) {
        this(input1, input2, name, SimpleOperatorFactory.of(operator), outputType, parallelism);
    }

    public TwoInputTransformation(
            Transformation<IN1> input1,
            Transformation<IN2> input2,
            String name,
            StreamOperatorFactory<OUT> operatorFactory,
            TypeInformation<OUT> outputType,
            int parallelism) {
        super(name, outputType, parallelism);
        this.input1 = input1;
        this.input2 = input2;
        this.operatorFactory = operatorFactory;
    }
    @Override
    public final void setChainingStrategy(ChainingStrategy strategy) {
        operatorFactory.setChainingStrategy(strategy);
    }
    ...
}
```

### 1.5 TimestampsAndWatermarksTransformation

```java
public class TimestampsAndWatermarksTransformation<IN> extends PhysicalTransformation<IN> {

    private final Transformation<IN> input;
    private final WatermarkStrategy<IN> watermarkStrategy;

    private ChainingStrategy chainingStrategy = ChainingStrategy.DEFAULT_CHAINING_STRATEGY;

    public TimestampsAndWatermarksTransformation(
            String name,
            int parallelism,
            Transformation<IN> input,
            WatermarkStrategy<IN> watermarkStrategy) {
        super(name, input.getOutputType(), parallelism);
        this.input = input;
        this.watermarkStrategy = watermarkStrategy;
    }
    @Override
    public void setChainingStrategy(ChainingStrategy chainingStrategy) {
        this.chainingStrategy = checkNotNull(chainingStrategy);
    }
}
```

## 2. 非PhysicalTransformation

Transformation 不一定。有些转换操作只是逻辑概念，这方面的示例是联合、拆分/选择数据流、分区。

除了 PhysicalTransformation 之外，还有一部分转换操作直接继承自 Transformation 抽象类，这些 Transformation 只是一个逻辑概念，不会对应运行时的一个物理操作，不涉及具体的数据处理过程，仅描述上下游算子之间的数据分区。这种 Transformation 不支持链化操作，因此不能继承自 PhysicalTransformation。

- PartitionTransformation：支持对上游 DataStream 中的数据进行分区，分区策略通过指定的 StreamPartitioner 决定。例如在调用 DataStream.keyBy() 方法时，就会实例化此类的对象，并返回一个 KeyedStream 类型的对象
- UnionTransformation：用于对多个输入 Transformation 进行合并，最终将上游 DataStream 数据集中的数据合并为一个 DataStream。在调用 DataStream.union() 方法时会实例化此类的对象
- SideOutputTransformation：根据 OutputTag 筛选上游 DataStream 中的数据并下发到下游的算子中继续处理
- FeedbackTransformation	用于迭代计算中单输入反馈数据流节点的转换操作，表示 Flink DAG 中的一个反馈点
- CoFeedbackTransformation	用于迭代计算中双输入反馈数据流节点的转换操作。与 FeedbackTransformation 类似，也是 Flink DAG 中的一个反馈点。两者的不同之处在于，CoFeedBackTransformation 反馈给上游的数据流与上游 Transformation 的输入类型不同，所以要求上游的 Transformation 必须是 TwoInputTransformation

### UnionTransformation

UnionTransformation 为合并转换操作，主要用来将多个输入 Transformation 进行合并，在内部名称为 Union。通过指定一个 Transformation 列表来创建 UnionTransformation：
```java
public class UnionTransformation<T> extends Transformation<T> {
    // 可以指定多个输入
    private final List<Transformation<T>> inputs;
    // 根据指定的输入创建 UnionTransformation
    public UnionTransformation(List<Transformation<T>> inputs) {
        super("Union", inputs.get(0).getOutputType(), inputs.get(0).getParallelism());
        // 多个输入 Transformation 的输出类型必须一致
        for (Transformation<T> input : inputs) {
            if (!input.getOutputType().equals(getOutputType())) {
                throw new UnsupportedOperationException("Type mismatch in input " + input);
            }
        }
        this.inputs = Lists.newArrayList(inputs);
    }
    ...
}
```
UnionTransformation 不会创建物理操作，只会影响上游操作与下游操作的连接方式。本质上是接收的多个 Transformation 的封装。需要注意的是输入的多个 Transformation 的输出类型 OutputType 必须一致。

### PartitionTransformation

PartitionTransformation 为分区转换操作，主要用来改变输入元素的分区，在内部名称为 Partition。因此，除了提供一个 Transformation 作为输入，还需要提供一个 StreamPartitioner 来进行分区：
```java
public class PartitionTransformation<T> extends Transformation<T> {
    // 输入 Transformation
    private final Transformation<T> input;
    // 分区器
    private final StreamPartitioner<T> partitioner;
    // Shuffle 模式
    private final ShuffleMode shuffleMode;
    // 指定 Transformation 和 StreamPartitioner 创建 PartitionTransformation
    public PartitionTransformation(Transformation<T> input, StreamPartitioner<T> partitioner) {
        this(input, partitioner, ShuffleMode.UNDEFINED);
    }
    public PartitionTransformation(Transformation<T> input, StreamPartitioner<T> partitioner, ShuffleMode shuffleMode) {
        super("Partition", input.getOutputType(), input.getParallelism());
        this.input = input;
        this.partitioner = partitioner;
        this.shuffleMode = checkNotNull(shuffleMode);
    }
    ...
}
```
PartitionTransformation 不会创建物理操作，只会影响上游操作与下游操作的连接方式。本质上是一个 Transformation 和 StreamPartitioner 的封装。

### SideOutputTransformation

SideOutputTransformation 为侧输出操作，主要用来根据 OutputTag 筛选上游 DataStream 中的数据并分发到下游的算子中继续处理。SideOutputTransformation 内部名称为 SideOutput。因此，除了提供一个 Transformation 作为输入，还需要提供一个 OutputTag：
```java
public class SideOutputTransformation<T> extends Transformation<T> {
    // 输入 Transformation
    private final Transformation<?> input;
    // 输出标记 OutputTag
    private final OutputTag<T> tag;
    // 指定 Transformation 和 OutputTag 创建 SideOutputTransformation
    public SideOutputTransformation(Transformation<?> input, final OutputTag<T> tag) {
        super("SideOutput", tag.getTypeInfo(), requireNonNull(input).getParallelism());
        this.input = input;
        this.tag = requireNonNull(tag);
    }
    ...
}
```
SideOutputTransformation 不会创建物理操作，只会影响上游操作与下游操作的连接方式。本质上是一个 Transformation 和 OutputTag 的封装。
