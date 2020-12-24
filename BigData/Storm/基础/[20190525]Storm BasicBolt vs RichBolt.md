---
layout: post
author: sjf0115
title: Storm BasicBolt vs RichBolt
date: 2019-05-25 14:33:01
tags:
  - Storm
  - Storm 基础

categories: Storm
permalink: how-to-choose-basicbolt-and-richbolt-of-storm
---

IComponent 是所有组件的接口，例如 IBasicBolt、IRichBolt、IBatchBolt 都继承自 IComponent，为拓扑中所有组件提供共同的方法。BaseComponent 是 Storm 提供的一个比较方便的抽象类，这个抽象类及其子类都或多或少实现了其接口定义的部分方法。IBolt 接口是 IRichBolt 要继承的接口。还有一些以 Base 开头的 Bolt 类，如 BaseBasicBolt，BaseRichBolt 等，在这些类中所实现的方法都为空，或者返回值为 NULL。从下图中，可以从整体上看到这些类的关系图，从而理清这些类之间的关系及结构。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Storm/how-to-choose-basicbolt-and-richbolt-of-storm.png?raw=true)

### 1. IComponent 与 BaseComponent

IComponent 继承 Serializable 接口，为拓扑中所有组件提供共同的方法，是所有组件的接口：
```java
public interface IComponent extends Serializable {
    void declareOutputFields(OutputFieldsDeclarer declarer);
    Map<String, Object> getComponentConfiguration();
}
```

使用如下方法为拓扑中的流声明输出模式，OutputFieldsDeclarer 用于声明输出流ID，输出字段以及每个输出流是否是直接流：
```java
void declareOutputFields(OutputFieldsDeclarer declarer);
```

使用如下方法声明针对当前组件的配置，只能覆盖 `topology.*` 配置。使用 TopologyBuilder 构建拓扑时，可以进一步覆盖该组件配置：
```java
Map<String, Object> getComponentConfiguration();
```

BaseComponent 是 Storm 提供的一个比较方便的抽象类，这个抽象类及其子类都简单实现了其接口定义的部分方法，所实现的方法返回值为 NULL：
```java
public abstract class BaseComponent implements IComponent {
    @Override
    public Map<String, Object> getComponentConfiguration() {
        return null;
    }    
}
```

### 2. IBolt

IBolt 继承了 Serializable 接口，输入元组经过处理后输出相应的元组，可以执行过滤，连接以及聚合等操作。IBolt 可以不必立即处理接收的元组，而是保留元组在内存中以便稍后处理。

```java
public interface IBolt extends Serializable {
    void prepare(Map stormConf, TopologyContext context, OutputCollector collector);
    void execute(Tuple input);
    void cleanup();
}
```

IBolt 的生命周期如下：在客户端上创建 IBolt 对象。在 Nimbus 上提交 Topology 后，创建出来的 IBolt 在序列化后被发送到具体执行的 Worker 上。在 Worker 上执行时，先调用 prepare 方法传入当前执行的上下文，然后调用 execute 方法，对元组进行处理。如果要参数化 IBolt 对象，需要通过构造函数来设置参数，并将参数保存在实例变量中（然后将其序列化并传送到跨集群执行的每个任务上）。使用传入的 OutputCollector 的 ack 方法或 fail 方法来反馈处理结果。

当初始化 Worker 上该组件的一个任务时会调用如下方法，并提供执行环境。stormConf 为 Bolt 提供配置，并与集群提供的配置进行合并。context 用来获取有关此任务在拓扑中的位置信息，包括此任务的任务ID和组件ID，输入和输出信息等。collector 用来从 Bolt 向下游发送元组，元组可以在任何时间点发送，不必处理完立即发送。collector 是线程安全的，可以保存在一个实例变量：
```java
void prepare(Map stormConf, TopologyContext context, OutputCollector collector);
```
处理单个输入元组时会调用如下方法。Tuple 对象包含有关它来自哪个组件/流/任务的元数据。可以使用 `Tuple.getValue` 访问元组的值。IBolt 不必立即处理元组，而是挂起稍后处理。使用 prepare 方法提供的 OutputCollector 来发送元组。要求所有输入元组使用 OutputCollector 的 ack 或 fail 方法进行反馈。否则，Storm 无法确定从 Spout 发送的元组什么时候完成：
```java
void execute(Tuple input);
```
当停掉 Bolt 实例时会调用如下方法，但是不保证一定会调用该方法：
```java
void cleanup();
```

### 3. RichBolt VS BasicBolt

Storm 提供了两种不同类型的 Bolt，分别是 RichBolt(IRichBolt, BaseRichBolt) 和 BasicBolt(IBasicBolt, BaseBasicBolt)，很多使用 Storm 的人无法分清 BasicBolt 和 RichBolt 之间的区别。我们的建议是尽可能的使用 BasicBolt。

这两个类继承的父类如第一个图所示，它们的共同之处是父类中都有 BaseComponent 和 ICompont。不同之处是 BaseRichBolt 实现有 IBolt 和 IRichBolt 接口，而 BaseBasicBolt 只有 IBasicBolt 接口。其实本质的区别在于 IBolt 和 IBasicBolt 的区别：
```java
public interface IBasicBolt extends IComponent {
    void prepare(Map stormConf, TopologyContext context);
    void execute(Tuple input, BasicOutputCollector collector);
    void cleanup();
}

public interface IBolt extends Serializable {
    void prepare(Map stormConf, TopologyContext context, OutputCollector collector);
    void execute(Tuple input);
    void cleanup();
}
```
RichBolt 继承 IBolt 接口，使用 OutputCollector 的如下方法来发送元组:
```java
// 向指定数据流发送锚定的元组, 需要向 Acker 发送 ack 确认, 可靠传递
List<Integer> emit(String streamId, Tuple anchor, List<Object> tuple);
// 向指定数据流发送未锚定的元组, 不需要向 Acker 发送 ack 确认, 是不可靠传递
List<Integer> emit(String streamId, List<Object> tuple);
// 向默认数据流发送锚定的元组, 需要向 Acker 发送 ack 确认, 可靠传递
List<Integer> emit(Tuple anchor, List<Object> tuple);
// 向默认数据流发送未锚定的元组, 不需要向 Acker 发送 ack 确认, 是不可靠传递
List<Integer> emit(List<Object> tuple);
```
BasicBolt 使用 BasicOutputCollector 的如下方法来发送元组:
```java
// 向指定数据流发送锚定的元组, 需要向 Acker 发送 ack 确认, 可靠传递
List<Integer> emit(String streamId, List<Object> tuple);
// 向默认数据流发送锚定的元组, 需要向 Acker 发送 ack 确认, 可靠传递
List<Integer> emit(List<Object> tuple);
```
两个 Bolt 都可以实现可靠性消息传递，不过 RichBolt 需要自己做很多周边的事情（例如，建立 Anchor 树，以及手动 ACK/FAIL 通知 Acker），而 BasicBolt 则由 Storm 帮忙实现了很多周边的事情，实现起来方便简单。

### 4. 实现(不)可靠性消息传递

下面我们看一下如何使用上面的 Bolt 来实现(不)可靠性消息传递。

(1) 使用 BaseRichBolt 实现不可靠的Bolt
```java
public class SplitSentence extends BaseRichBolt {
    private OutputCollector collector;
    public void prepare(Map conf, TopologyContext context, OutputCollector collector) {
        this.collector = collector;
    }

    public void execute(Tuple tuple) {
        String sentence = tuple.getString(0);
        for(String word: sentence.split(" ")) {
            collector.emit(new Values(word));
        }
        // 在这即使Ack也是没有用处的
        // collector.ack(tuple);
    }

    public void declareOutputFields(OutputFieldsDeclarer declarer) {
        declarer.declare(new Fields("word"));
    }      
}
```
这种方式我们没有手动建立 Anchor 树以及手动 Ack 或者 Fail，所以这是一种不可靠的消息传递方式。

(2) 使用 BaseRichBolt 实现可靠的Bolt
```java
public class SplitSentence extends BaseRichBolt {
    private OutputCollector collector;
    public void prepare(Map conf, TopologyContext context, OutputCollector collector) {
        this.collector = collector;
    }

    public void execute(Tuple tuple) {
        String sentence = tuple.getString(0);
        for(String word: sentence.split(" ")) {
            collector.emit(tuple, new Values(word));
        }
        collector.ack(tuple);
    }

    public void declareOutputFields(OutputFieldsDeclarer declarer) {
        declarer.declare(new Fields("word"));
    }      
}
```
这种方式需要我们手动的建立 Anchor 树以及手动的 Ack 或者 Fail，所以这是一种可靠的消息传递方式。

(3) 使用 BaseBasicBolt 实现可靠的Bolt
```java
public class SplitSentence extends BaseBasicBolt {
    public void execute(Tuple tuple, BasicOutputCollector collector) {
        String sentence = tuple.getString(0);
        for(String word: sentence.split(" ")) {
            collector.emit(new Values(word));
        }
    }

    public void declareOutputFields(OutputFieldsDeclarer declarer) {
        declarer.declare(new Fields("word"));
    }      
}
```
这种方式由 Storm 自动帮助我们建立 Anchor 树以及发送 Ack 或者 Fail。这是一种可靠的消息传递方式。我们只需要关心业务逻辑即可。


英译对照:
- 直接流: direct stream

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)


参考：
- [Storm 的可靠性保证测试](https://zhuanlan.zhihu.com/p/23127603)
- [IBasicBolt vs IRichBolt](https://github.com/alibaba/jstorm/wiki/IBasicBolt-vs-IRichBolt)
