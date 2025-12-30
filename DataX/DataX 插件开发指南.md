本文面向DataX插件开发人员，尝试尽可能全面地阐述开发一个DataX插件所经过的历程，力求消除开发者的困惑，让插件开发变得简单。

一、开发之前
路走对了，就不怕远。✓ 路走远了，就不管对不对。✕

当你打开这篇文档，想必已经不用在此解释什么是DataX了。那下一个问题便是：

DataX为什么要使用插件机制？
从设计之初，DataX就把异构数据源同步作为自身的使命，为了应对不同数据源的差异、同时提供一致的同步原语和扩展能力，DataX自然而然地采用了框架 + 插件 的模式：

插件只需关心数据的读取或者写入本身。
而同步的共性问题，比如：类型转换、性能、统计，则交由框架来处理。
作为插件开发人员，则需要关注两个问题：

数据源本身的读写数据正确性。
如何与框架沟通、合理正确地使用框架。
开工前需要想明白的问题
就插件本身而言，希望在您动手coding之前，能够回答我们列举的这些问题，不然路走远了发现没走对，就尴尬了。

## 2. 插件视角看框架

### 2.1 逻辑执行模型

插件开发者不用关心太多，基本只需要关注特定系统读和写，以及自己的代码在逻辑上是怎样被执行的，哪一个方法是在什么时候被调用的。在此之前，需要明确以下概念：
- `Job`: Job是DataX用以描述从一个源头到一个目的端的同步作业，是DataX数据同步的最小业务单元。比如：从一张mysql的表同步到odps的一个表的特定分区。
- `Task`: Task是为最大化而把Job拆分得到的最小执行单元。比如：读一张有1024个分表的mysql分库分表的Job，拆分成1024个读Task，用若干个并发执行。
- `TaskGroup`: 描述的是一组Task集合。在同一个TaskGroupContainer执行下的Task集合称之为TaskGroup
- `JobContainer`: Job执行器，负责Job全局拆分、调度、前置语句和后置语句等工作的工作单元。类似Yarn中的JobTracker
- `TaskGroupContainer`: TaskGroup执行器，负责执行一组Task的工作单元，类似Yarn中的TaskTracker。

简而言之， Job 拆分成 Task，在分别在框架提供的容器中执行，插件只需要实现 Job 和 Task 两部分逻辑。

### 2.2 物理执行模型

框架为插件提供物理上的执行能力（线程）。DataX 框架有三种运行模式：
- Standalone: 单进程运行，没有外部依赖。
- Local: 单进程运行，统计信息、错误信息汇报到集中存储。
- Distrubuted: 分布式多进程运行，依赖 DataX Service 服务。

当然，上述三种模式对插件的编写而言没有什么区别，你只需要避开一些小错误，插件就能够在单机/分布式之间无缝切换了。当 JobContainer 和 TaskGroupContainer 运行在同一个进程内时，就是单机模式（Standalone和Local）；当它们分布在不同的进程中执行时，就是分布式（Distributed）模式。

### 2.3 编程接口

那么，Job 和 Task 的逻辑应是怎么对应到具体的代码中的？首先，插件的入口类必须扩展 Reader 或 Writer 抽象类，并且实现分别实现 Job 和 Task 两个内部抽象类，Job 和 Task 的实现必须是内部类的形式，原因见加载原理一节。以Reader为例：
```java
public class SomeReader extends Reader {

    public static class Job extends Reader.Job {
        @Override
        public void init() {
        }

    		@Override
    		public void prepare() {
        }

        @Override
        public List<Configuration> split(int adviceNumber) {
            return null;
        }

        @Override
        public void post() {
        }

        @Override
        public void destroy() {
        }
    }

    public static class Task extends Reader.Task {

        @Override
        public void init() {
        }

    		@Override
    		public void prepare() {
        }

        @Override
        public void startRead(RecordSender recordSender) {
        }

        @Override
        public void post() {
        }

        @Override
        public void destroy() {
        }
    }
}
```

Job 接口功能如下：
- `init`: Job 对象初始化工作，此时可以通过 `super.getPluginJobConf()` 获取与本插件相关的配置。读插件获得配置中 reader 部分，写插件获得 writer 部分。
- `prepare`: 全局准备工作，比如odpswriter清空目标表。
- `split`: 拆分Task。参数adviceNumber框架建议的拆分数，一般是运行时所配置的并发度。值返回的是Task的配置列表。
- `post`: 全局的后置工作，比如mysqlwriter同步完影子表后的rename操作。
- `destroy`: Job对象自身的销毁工作。

Task接口功能如下：
- `init`：Task对象的初始化。此时可以通过super.getPluginJobConf()获取与本Task相关的配置。这里的配置是Job的split方法返回的配置列表中的其中一个。
- `prepare`：局部的准备工作。
- `startRead`: 从数据源读数据，写入到 RecordSender 中。RecordSender会把数据写入连接Reader和Writer的缓存队列。
- `startWrite`：从 RecordReceiver 中读取数据，写入目标数据源。RecordReceiver中的数据来自Reader和Writer之间的缓存队列。
- `post`: 局部的后置工作。
- `destroy`: Task象自身的销毁工作。

需要注意的是：
- Job 和 Task 之间一定不能有共享变量，因为分布式运行时不能保证共享变量会被正确初始化。两者之间只能通过配置文件进行依赖。
- prepare 和 post 在 Job 和 Task 中都存在，插件需要根据实际情况确定在什么地方执行操作。

框架按照如下的顺序执行 Job 和 Task 的接口：

![](https://github.com/alibaba/DataX/blob/master/images/plugin_dev_guide_1.png)

上图中，黄色表示 Job 部分的执行阶段，蓝色表示 Task 部分的执行阶段，绿色表示框架执行阶段。

![](https://github.com/alibaba/DataX/blob/master/images/plugin_dev_guide_2.png)

## 3. 插件定义

代码写好了，有没有想过框架是怎么找到插件的入口类的？框架是如何加载插件的呢？在每个插件的项目中，都有一个 plugin.json 文件，这个文件定义了插件的相关信息，包括入口类。例如：
```json
{
    "name": "mysqlwriter",
    "class": "com.alibaba.datax.plugin.writer.mysqlwriter.MysqlWriter",
    "description": "Use Jdbc connect to database, execute insert sql.",
    "developer": "alibaba"
}
```
- name: 插件名称，大小写敏感。框架根据用户在配置文件中指定的名称来搜寻插件。 十分重要 。
- class: 入口类的全限定名称，框架通过反射插件入口类的实例。十分重要 。
- description: 描述信息。
- developer: 开发人员。
