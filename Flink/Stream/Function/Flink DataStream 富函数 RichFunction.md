## 1. 什么是富函数

很多时候，我们需要在函数处理第一条记录之前进行一些初始化的工作或者获得函数执行上下文的一些信息，以及在处理完数据后做一些清理工作。而 DataStream API 就提供了这样的机制：富函数 RichFunction。DataStream API 提供了一类富函数，和普通函数相比可对外提供跟多的功能。

DataStream API 中所有的转换函数都有对应的富函数，例如 MapFunction 和 RichMapFunction、SourceFunction 和 RichSourceFunction、SinkFunction 和 RichSinkFunction。可以看出，只需要在普通函数的前面加上 Rich 前缀就是富函数了。富函数可以像普通函数一样接收参数，并且富函数的使用位置也和普通函数相同，即在使用普通函数的地方都可以使用对应的富函数来代替。

富函数有一个生命周期的概念，当我们使用富函数时，可以实现两个额外的方法：
- open：是富函数的初始化方法。在每个任务首次调用转换方法(map 或者 filter 等)之前会被调用一次。通常用来做一些只需要做一次即可的初始化工作。
- close：是富函数的终止方法。在每个任务最后一次调用转换方法(map 或者 filter 等)之后会被调用一次。通常用来做一些清理和释放资源的工作。

另外可以利用 `getRuntimeContext()` 方法访问函数的 RuntimeContext。可以从 RuntimeContext 中的获取一些信息，例如函数的并行度，函数所在子任务的编号，当函数的子任务名字。同时还它还包含了访问分区状态的方法。

## 2. 层次关系

我们以 RichMapFunction 为例具体看一下函数的层次关系：

![]()

Function 接口是所有用户自定义函数的基础接口，RichFunction 和 MapFunction 都是继承 Function 的接口。可以看到，SinkFunction和RichFunction接口中有各有不同的方法，而后者的方法更丰富一些，功能也就越多，所以称为“富函数”。


```java
public interface MapFunction<T, O> extends Function, Serializable {
    O map(T value) throws Exception;
}
```







```java
public abstract class AbstractRichFunction implements RichFunction, Serializable {

    private static final long serialVersionUID = 1L;
    private transient RuntimeContext runtimeContext;

    @Override
    public void setRuntimeContext(RuntimeContext t) {
        this.runtimeContext = t;
    }

    @Override
    public RuntimeContext getRuntimeContext() {
        if (this.runtimeContext != null) {
            return this.runtimeContext;
        } else {
            throw new IllegalStateException("The runtime context has not been initialized.");
        }
    }

    @Override
    public IterationRuntimeContext getIterationRuntimeContext() {
        if (this.runtimeContext == null) {
            throw new IllegalStateException("The runtime context has not been initialized.");
        } else if (this.runtimeContext instanceof IterationRuntimeContext) {
            return (IterationRuntimeContext) this.runtimeContext;
        } else {
            throw new IllegalStateException("This stub is not part of an iteration step function.");
        }
    }

    @Override
    public void open(Configuration parameters) throws Exception {}

    @Override
    public void close() throws Exception {}
}
```

https://docherish.com/post/flink-richfunction/

int subTask = getRuntimeContext().getIndexOfThisSubtask();
