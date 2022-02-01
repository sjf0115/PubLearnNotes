

在任何给定时间，spout任务可以挂起的最大元组数。此配置适用于单个任务，而不适用于全部Spout或整个拓扑。挂起的元组是从Spout发出但尚未被确认(acked)或失败(failed)的元组。

请注意，此配置参数对于不使用Message ID 标记元组的不可靠Spout无效。

```java
@isInteger
@isPositiveNumber
public static final String TOPOLOGY_MAX_SPOUT_PENDING="topology.max.spout.pending";
```

To make TOPOLOGY_MAX_SPOUT_PENDING you need to enable fault-tolerance mechanism (ie, assigning message IDs in Spouts and anchor and ack in Bolts). Furthermore, if you emit more than one tuple per call to Spout.nextTuple() TOPOLOGY_MAX_SPOUT_PENDING will not work as expected.

It is actually bad practice for some more reasons so emit more than a single tuple per Spout.nextTuple() call (see Why should I not loop or block in Spout.nextTuple() for more details).


Maybe you can set TOPOLOGY_MAX_SPOUT_PENDING to one. This should trigger a single call to nextTuple() and will not issue a second call until all 4096 tuples you emit got processed.

```java
Config conf = new Config();
conf.setMaxSpoutPending(5000);
StormSubmitter.submitTopology("mytopology", conf, topology);
```




http://www.voidcn.com/article/p-kotimlfd-kw.html

https://stackoverflow.com/questions/32547935/why-should-i-not-loop-or-block-in-spout-nexttuple

https://stackoverflow.com/questions/32812448/how-to-set-topology-max-spout-pending-parameter
