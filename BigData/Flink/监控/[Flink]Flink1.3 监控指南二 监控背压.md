
### 1. 背压

如果发现某项任务出现背压警告(例如"HIGH")，那就意味着当前算子产生数据的速度要比下游算子消耗的速度要快。作业中的数据流向下游(例如从sources到sinks)，而背压流向相反的方向，流上上游。

以一个简单的`Source -> Sink`为例。如果你在Source上看的警告，这意味着Sink消耗数据的速度比Source正在生成数据的速度要慢。Sink反向向上游施压(Sink is back pressuring the upstream operator Source.)。

### 2. Sampling Threads

背压监控通过反复对运行任务抽样进行堆栈跟踪而实现。JobManager触发重复调用作业中Task的`Thread.getStackTrace()`方法(The JobManager triggers repeated calls to Thread.getStackTrace() for the tasks of your job.)。

![](http://img.blog.csdn.net/20171117193104380?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

如果样本显示某个任务线程停留在某个内部方法调用上(从网络堆栈中请求缓冲区)，则表明该任务存在背压(If the samples show that a task Thread is stuck in a certain internal method call (requesting buffers from the network stack), this indicates that there is back pressure for the task.)。

默认情况下，为了确定背压,作业管理器每50毫秒触发100个堆栈跟踪。在Web界面中看到的比率会告诉你有多少这些堆栈跟踪卡在内部方法调用上，例如，0.01表示100个只有一个卡在该方法上。

```
OK: 0 <= Ratio <= 0.10
LOW: 0.10 < Ratio <= 0.5
HIGH: 0.5 < Ratio <= 1
```
为了不使堆栈跟踪样本过载任务管理器，Web界面仅在60秒后刷新样本(In order to not overload the task managers with stack trace samples, the web interface refreshes samples only after 60 seconds.)。

### 3. 配置

你可以使用以下配置键配置作业管理器的样本数量：

配置键|默认值|说明
---|---|---
jobmanager.web.backpressure.refresh-interval|1min|刷新时间间隔.可用状态被弃用,需要重新刷新
jobmanager.web.backpressure.num-samples|100|确定背压需要使用到的堆栈抽样个数
jobmanager.web.backpressure.delay-between-samples|50ms|确定背压堆栈抽样之间的延迟

### 4. Example

可以在作业概览旁边找到背压选项卡。

#### 4.1 正在抽样

这意味着JobManager触发了正在运行任务的堆栈跟踪抽样。使用默认配置，大约需要5秒钟才能完成。

请注意，单击该行，你将触发此算子的所有子任务的抽样。

![](http://img.blog.csdn.net/20171117194658443?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

#### 4.2 背压状态

如果看到任务的状态`OK`，则不存在背压。相反，`HIGN`表示任务存在背压。

![](http://img.blog.csdn.net/20171117194728623?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

![](http://img.blog.csdn.net/20171117194739697?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)


原文:https://ci.apache.org/projects/flink/flink-docs-release-1.3/monitoring/back_pressure.html
