问题：
- 如何判断哪些是可合并窗口
- 可合并窗口中的状态如何存储，以什么样的格式存储
- 窗口合并时如何合并状态
- 窗口合并时如何合并触发器

合并的主要过程如下：
1）找出合并之前的窗口集合和合并之后的窗口；
2）找出合并之后的窗口对应的状态窗口（方式是从合并窗口集合中挑选第一个窗口的状态窗口）；
3）执行merge方法（合并窗口需要做的工作，也就是执行MergingWindowSet的addWindow方法）。
这里不好理解的是合并结果的窗口和结果对应的状态窗口（用来获取合并之后的数据），我们来看图2-6。
[插图]
图2-6 合并窗口
MergingWindowSet（窗口合并的工具类）中有个map，用来保存窗口和状态窗口的对应关系，那么怎么理解这个状态窗口呢？如果我们在得到TimeWindow(1,4)时基于TimeWindow(1,4)在状态中保存了数据（数据A），也就是说状态的命名空间是TimeWindow(1,4)，在得到TimeWindow(5,8)时基于TimeWindow(5,8)在状态中保存了数据（数据B），当第三个数据（数据C）来的时候，又经过合并窗口得到了TimeWindow(1,8)，那么怎么获取合并窗口的数据集AB呢？显然我们还需要原来的TimeWindow(1,4)或者TimeWindow(5,8)，原来的TimeWindow(1,4)在这里就是状态窗口。
这里窗口合并的同时会把窗口对应的状态所保存的数据合并到结果窗口对应的状态窗口对应的状态中。这里有点绕，还是看图2-6，最终合并窗口的结果窗口是TimeWindow(1,8)。我们怎么获取TimeWindow(1,8)对应的数据集ABC呢？这个时候可以通过MergingWindowSet中保存的TimeWindow(1,8)对应的状态窗口TimeWindow(1,4)来获取合并后的状态，即数据集ABC。
会话窗口的其他过程与滑动窗口及滚动窗口没有什么区别。

```java
MergingWindowSet<W> mergingWindows = getMergingWindowSet();
W actualWindow = mergingWindows.addWindow(window, new MergingWindowSet.MergeFunction<W>() {
          @Override
          public void merge(W mergeResult, Collection<W> mergedWindows,
                  W stateWindowResult, Collection<W> mergedStateWindows) throws Exception {
                    // 合并逻辑
          }
      });
```

```java
if ((windowAssigner.isEventTime() &&
      mergeResult.maxTimestamp() + allowedLateness <= internalTimerService .currentWatermark())) {
    throw new UnsupportedOperationException(xxx);
} else if (!windowAssigner.isEventTime()) {
    long currentProcessingTime = internalTimerService.currentProcessingTime();
    if (mergeResult.maxTimestamp() <= currentProcessingTime) {
        throw new UnsupportedOperationException(xxx);
    }
}

triggerContext.key = key;
triggerContext.window = mergeResult;
triggerContext.onMerge(mergedWindows);

for (W m : mergedWindows) {
    triggerContext.window = m;
    triggerContext.clear();
    deleteCleanupTimer(m);
}

// merge the merged state windows into the newly resulting
// state window
windowMergingState.mergeNamespaces(stateWindowResult, mergedStateWindows);
```


## 1. MergingWindowAssigner

## 窗口对象合并

判断窗口是否需要与已有的窗口进行合并。窗口合并时按照窗口的起始时间进行排序，然后判断窗口之间是否存在时间重叠，重叠的窗口进行合并，将后序窗口合并到前序窗口中，如图4-17所示，延长窗口W1的长度，将W3窗口的结束时间作为W1的结束时间，清理掉 W2、W3 窗口。

继承 MergingWindowAssigner 抽象的实现类都可以通过 mergeWindows 方法合并窗口：
```java
public void mergeWindows(Collection<TimeWindow> windows, MergeCallback<TimeWindow> c) {
    TimeWindow.mergeWindows(windows, c);
}
```
从上面我们可以看到合并窗口的能力是借助 TimeWindow 实现的：
```java
// TimeWindow#mergeWindows
public static void mergeWindows(Collection<TimeWindow> windows, MergingWindowAssigner.MergeCallback<TimeWindow> c) {
    // 按照窗口的起始时间进行排序
    List<TimeWindow> sortedWindows = new ArrayList<>(windows);
    Collections.sort(sortedWindows,
            new Comparator<TimeWindow>() {
                @Override
                public int compare(TimeWindow o1, TimeWindow o2) {
                    return Long.compare(o1.getStart(), o2.getStart());
                }
            });
    // 窗口你对象合并
    // 合并完成的窗口  Set<TimeWindow> 中的窗口合并为 TimeWindow
    List<Tuple2<TimeWindow, Set<TimeWindow>>> merged = new ArrayList<>();
    // 当前正在合并的窗口
    Tuple2<TimeWindow, Set<TimeWindow>> currentMerge = null;
    for (TimeWindow candidate : sortedWindows) {
        if (currentMerge == null) {
            // 第一个窗口
            currentMerge = new Tuple2<>();
            currentMerge.f0 = candidate;
            currentMerge.f1 = new HashSet<>();
            currentMerge.f1.add(candidate);
        } else if (currentMerge.f0.intersects(candidate)) {
            // 两个窗口重叠进行合并
            currentMerge.f0 = currentMerge.f0.cover(candidate);
            currentMerge.f1.add(candidate);
        } else {
            // 不重叠
            merged.add(currentMerge);
            currentMerge = new Tuple2<>();
            currentMerge.f0 = candidate;
            currentMerge.f1 = new HashSet<>();
            currentMerge.f1.add(candidate);
        }
    }

    if (currentMerge != null) {
        merged.add(currentMerge);
    }

    for (Tuple2<TimeWindow, Set<TimeWindow>> m : merged) {
        if (m.f1.size() > 1) {
            // 需要合并的窗口
            c.merge(m.f1, m.f0);
        }
    }
}
```

通过 MergingWindowAssigner 的 MergeCallback 回调函数确定哪些窗口需要合并：
```java
// 窗口合并结果
final Map<W, Collection<W>> mergeResults = new HashMap<>();
windowAssigner.mergeWindows(windows,
      new MergingWindowAssigner.MergeCallback<W>() {
          @Override
          public void merge(Collection<W> toBeMerged, W mergeResult) {
              if (LOG.isDebugEnabled()) {
                  LOG.debug("Merging {} into {}", toBeMerged, mergeResult);
              }
              // mergeResult 窗口对象合并的结果
              // toBeMerged 中窗口对象合并成 mergeResult 窗口对象
              mergeResults.put(mergeResult, toBeMerged);
          }
      });
```
> MergingWindowSet#addWindow
> 通过 mergeWindows 只是完成了窗口对象的合并，也就是逻辑意义上的合并。本质上是时间区间的合并，底层存储的数据并没有合并。

## 窗口状态合并

创建状态需要跟 StateBackend 进行交互，成本比较高，对于会话窗口来说合并行为比较频繁，所以尽量复用已有的状态。

窗口合并的同时，窗口对应的 State 也需要进行合并，默认复用最早的窗口的状态，本例中是W1窗口的状态，将其他待合并窗口的状态（W2、W3）合并到W1状态中。


```java
for (Map.Entry<W, Collection<W>> c : mergeResults.entrySet()) {
    // 窗口合并结果
    W mergeResult = c.getKey();
    // 合并的各个窗口
    Collection<W> mergedWindows = c.getValue();

    // if our new window is in the merged windows make the merge result the
    // result window
    if (mergedWindows.remove(newWindow)) {
        mergedNewWindow = true;
        resultWindow = mergeResult;
    }

    // pick any of the merged windows and choose that window's state window
    // as the state window for the merge result
    W mergedStateWindow = this.mapping.get(mergedWindows.iterator().next());

    // figure out the state windows that we are merging
    List<W> mergedStateWindows = new ArrayList<>();
    for (W mergedWindow : mergedWindows) {
        W res = this.mapping.remove(mergedWindow);
        if (res != null) {
            mergedStateWindows.add(res);
        }
    }

    this.mapping.put(mergeResult, mergedStateWindow);

    // don't put the target state window into the merged windows
    mergedStateWindows.remove(mergedStateWindow);

    // don't merge the new window itself, it never had any state associated with it
    // i.e. if we are only merging one pre-existing window into itself
    // without extending the pre-existing window
    if (!(mergedWindows.contains(mergeResult) && mergedWindows.size() == 1)) {
        mergeFunction.merge(
                mergeResult,
                mergedWindows,
                this.mapping.get(mergeResult),
                mergedStateWindows);
    }
}
```

## 窗口触发器合并

Trigger 也需要能支持对合并窗口后的响应，所以 Trigger 添加了一个新的接口 onMerge(W window, OnMergeContext ctx)，用来响应发生窗口合并之后对 trigger 的相关动作，比如根据合并后的窗口注册新的 event time 定时器。

Trigger#onMerge方法中用于对触发器进行合并，触发器的常见成本比较低，所以触发器的合并实际上是删除合并的窗口的触发器，本例中会删除W1、W2、W3的触发器，然后为新的W1窗口创建新的触发器，触发时间为W3触发器的触发时间。


## WindowOperator

在一些情况下，窗口的边界不是固定的，可能会随着数据记录的到达不断进行调整，例如会话窗口就会随着数据记录的到达可能发生窗口的合并。

可以合并的窗口相比于不可以合并的窗口，在 WindowOperator.open 方法中除了初始化窗口状态之外，还会初始化一个新的 mergingSetsState 用于保存窗口合并状态：
```java
if (windowAssigner instanceof MergingWindowAssigner) {
    // 窗口状态必须是可以合并的
    if (windowState instanceof InternalMergingState) {
        windowMergingState = (InternalMergingState<K, W, IN, ACC, ACC>) windowState;
    }
    // 窗口合并状态描述符
    final Class<Tuple2<W, W>> typedTuple = (Class<Tuple2<W, W>>) (Class<?>) Tuple2.class;
    final TupleSerializer<Tuple2<W, W>> tupleSerializer =
            new TupleSerializer<>(typedTuple, new TypeSerializer[] {windowSerializer, windowSerializer});
    final ListStateDescriptor<Tuple2<W, W>> mergingSetsStateDescriptor =
            new ListStateDescriptor<>("merging-window-set", tupleSerializer);
    // 获取窗口合并状态 mergingSetsState
    mergingSetsState = (InternalListState<K, VoidNamespace, Tuple2<W, W>>)getOrCreateKeyedState(
        VoidNamespaceSerializer.INSTANCE, mergingSetsStateDescriptor
    );
    mergingSetsState.setCurrentNamespace(VoidNamespace.INSTANCE);
}
```
> InternalListState<K, VoidNamespace, Tuple2<W, W>> mergingSetsState

相比于不可合并的窗口，可以合并的窗口实现上的一个难点就在于窗口合并时状态的处理，这需要依赖于 mergingSetsState 和 MergingWindowSet。我们先来梳理下窗口合并时窗口状态的处理，然后再详细地看具体的实现。

首先，窗口合并的前提条件是窗口状态必须可以合并，只有这样当两个窗口进行合并时其状态才可以正确地保存。ListState，ReducingState和 AggregatingState 都继承了 MergingState 接口。InternalMergingState 接口提供了将多个 namespace 关联的状态合并到目标 namespace 的功能：
```java
public interface InternalMergingState<K, N, IN, SV, OUT> extends InternalAppendingState<K, N, IN, SV, OUT>, MergingState<IN, OUT> {
    void mergeNamespaces(N var1, Collection<N> var2) throws Exception;
}
```

## MergingWindowSet

作用是什么？MergingWindowSet 是一个用来跟踪窗口合并的类。比如我们有 A、B、C 三个窗口需要合并，合并后的窗口为 D 窗口。这三个窗口在底层都有对应的状态，为了避免代价高昂的状态替换（创建新状态是很昂贵的），我们选择其中一个窗口作为状态窗口，其他几个窗口的数据合并到该状态窗口中。比如随机选择 A 作为状态窗口，那么 B 和 C 窗口中的数据需要合并到 A 窗口中去。这样就没有新状态产生了，但是我们需要额外维护窗口与状态窗口之间的映射关系（D->A），这就是 MergingWindowSet 负责的工作。这个映射关系需要在失败重启后能够恢复，所以 MergingWindowSet 内部也是对该映射关系做了容错。

状态合并的工作示意图如下所示：

https://smartsi.blog.csdn.net/article/details/126614957

先要明白几个概念：
- StateWindow：状态窗口



变量：
- MergingWindowAssigner<?, W> windowAssigner：合并窗口分配器
- ListState<Tuple2<W, W>> state：合并窗口状态
- Map<W, W> initialMapping：原始映射关系
- Map<W, W> mapping：合并窗口的映射关系，key 为合并的目标窗口，value 为需要合并的窗口
  - 合并后的窗口与保存合并窗口状态的窗口映射

```java
public MergingWindowSet(MergingWindowAssigner<?, W> windowAssigner, ListState<Tuple2<W, W>> state) throws Exception {
    this.windowAssigner = windowAssigner;
    // 合并后的映射关系
    mapping = new HashMap<>();
    Iterable<Tuple2<W, W>> windowState = state.get();
    if (windowState != null) {
        for (Tuple2<W, W> window : windowState) {
            mapping.put(window.f0, window.f1);
        }
    }
    this.state = state;
    // 初始化映射关系
    initialMapping = new HashMap<>();
    initialMapping.putAll(mapping);
}
```
追踪窗口变化：
```java

```






...
