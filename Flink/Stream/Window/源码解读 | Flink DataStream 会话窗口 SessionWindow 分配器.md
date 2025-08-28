

SessionWindow 类型的窗口比较特殊，在 WindowAssigner 的基础上又实现了 MergingWindowAssigner 抽象类。抽象类中提供了一个 mergeWindows 方法，主要用来实现对窗口中的元素进行动态合并。此外还在抽象类中定义了一个 MergeCallback 回调接口，主要原因是 SessionWindow 的窗口长度不固定，而窗口的长度取决于指定时间范围内是否有数据元素接入，然后动态地将接入数据切分成独立的窗口，最后完成窗口计算：
```java
public abstract class MergingWindowAssigner<T, W extends Window> extends WindowAssigner<T, W> {
    // 合并窗口
    public abstract void mergeWindows(Collection<W> windows, MergeCallback<W> callback);
    // 回调
    public interface MergeCallback<W> {
        void merge(Collection<W> toBeMerged, W mergeResult);
    }
}
```
Flink 中提供了 4 种 SessionWindow 的具体实现：
- ProcessingTimeSessionWindows：处理时间会话窗口，使用固定会话间隔时长。
- DynamicProcessingTimeSessionWindows：处理时间会话窗口，使用自定义会话间隔时长。
- EventTimeSessionWindows：事件时间会话窗口，使用固定会话间隔时长。
- DynamicEventTimeSessionWindows：事件时间会话窗口，使用自定义会话间隔时长。

## 1. 窗口分配实现

### 1.1 ProcessingTimeSessionWindows



### 1.2 DynamicProcessingTimeSessionWindows

### 1.3 EventTimeSessionWindows

### 1.4 DynamicEventTimeSessionWindows

## 2. 窗口合并

会话窗口不同于事件窗口，它的切分依赖于事件的行为，而不是时间序列，所以在很多情况下会因为事件乱序使得原本相互独立的窗口因为新事件的到来导致窗口重叠，而必须要进行窗口的合并，如图4-16所示。


在图4-16中，元素8和元素7的时间间隔超过了会话窗口的超时间隔，所以生成了两个会话窗口。

元素4在会话窗口触发计算之前进入了Flink，此时因为元素4的存在，4与8的间隔、4与7的间隔都小于超时间隔，所以此时元素8、4、7应该位于一个会话窗口，那么此时就需要对窗口进行合并，窗口的合并涉及3个要素：
1）窗口对象合并和清理。
2）窗口State的合并和清理。
3）窗口触发器的合并和清理。


（1）窗口合并
对于会话窗口，因为无法事先确定窗口的长度，也不知道该将数据元素放到哪个窗口，所以对于每一个事件分配一个SessionWindow。
然后判断窗口是否需要与已有的窗口进行合并。窗口合并时按照窗口的起始时间进行排序，然后判断窗口之间是否存在时间重叠，重叠的窗口进行合并，将后序窗口合并到前序窗口中，如图4-17所示，延长窗口W1的长度，将W3窗口的结束时间作为W1的结束时间，清理掉W2、W3窗口。

2）State合并
窗口合并的同时，窗口对应的State也需要进行合并，默认复用最早的窗口的状态，本例中是W1窗口的状态，将其他待合并窗口的状态（W2、W3）合并到W1状态中。
创建状态需要跟StateBackend进行交互，成本比较高，对于会话窗口来说合并行为比较频繁，所以尽量复用已有的状态。
（3）触发器合并
Trigger#onMerge方法中用于对触发器进行合并，触发器的常见成本比较低，所以触发器的合并实际上是删除合并的窗口的触发器，本例中会删除W1、W2、W3的触发器，然后为新的W1窗口创建新的触发器，触发时间为W3触发器的触发时间。
