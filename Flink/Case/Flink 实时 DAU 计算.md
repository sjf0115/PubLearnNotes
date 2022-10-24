数据分析的开发者经常会遇到这样的需求，绘制一条曲线，每个点的含义是当天 0 点到当前时间点的累计指标，横坐标表示时间，纵坐标是表示累计的指标。对这样的需求可以有两个解决方案：

第一个方案是使用无限流聚合，把时间归一到分钟粒度以后作为 group key 的一列，但是业务上要求输出到屏幕上的曲线不再变化，而无限流聚合的输出结果是一个更新流，所以不符合要求；

第二个方案是使用一天的滚动窗口函数。为了提前输出结果，还是要设置提前触发，时间点选用当前机器的时间或者是历史输入数据里最大的时间戳。这个方案的缺点，首先是每个点的纵坐标的值并不是这个时间点上的累计值。这会导致几个异常现象，比如作业失败重启或者是业务主动回溯历史的时候，不能完全还原当时的历史曲线。而且各个点上分维度的累计值加起来也不等于总维度的值。还有一个缺点，统计 UV 的时候，我们经常会使用两阶段的聚合来避免 distinct key 的倾斜，但是使用这个方案的时候，原本自身的曲线上可能会出现凹坑。

方案二导致的一些异常曲线：
- 第一个曲线是进行历史回溯， lag 消除以后曲线才开始正常，在没有完全消除 lag 的时候，曲线是不平滑的，而且不能还原历史曲线；
- 第二个曲线是自增曲线上出现凹坑。

因为第一级聚合的输出流是一个更新流，Flink 目前的更新机制是发送撤回和更新两条独立的消息，而不是一个原子消息，所以第二个聚合可能会先收到上游多个并发上发下来的撤回消息，这就会导致累计值先下降再上升，所以形成了凹坑。

CUMULATE 窗口的优点：
- 第一个优点是使用窗口的结束时间作为每个点的横坐标，曲线上每个点的纵坐标就是在横坐标对应时间点上的累计值，所以无论在回溯历史或者是作业发生 failover 的情况下，曲线都可以完全还原，而且各个时间点上分维度的值加起来总是等于总维度的值。
- 第二个优点是使用两阶段聚合，能够防止 distinct key 倾斜。由于数据是在窗口结束的时候才发送，所以不存在撤回，输出的是 append 流，因此自增曲线上也不会有凹坑。

## 1. Flink SQL

我感觉这种场景可以有两种方式，
1. 可以直接用group by + mini batch
2. window聚合 + fast emit

对于#1，group by的字段里面可以有一个日期的字段，例如你上面提到的DATE_FORMAT(rowtm, 'yyyy-MM-dd')。
这种情况下的状态清理，需要配置state retention时间，配置方法可以参考[1] 。同时，mini batch的开启也需要
用参数[2] 来打开。

对于#2，这种直接开一个天级别的tumble窗口就行。然后状态清理不用特殊配置，默认就可以清理。
fast emit这个配置现在还是一个experimental的feature，所以没有在文档中列出来，我把配置贴到这里，你可以参考一下：
table.exec.emit.early-fire.enabled = true
table.exec.emit.early-fire.delay = 60 s

[1]
https://ci.apache.org/projects/flink/flink-docs-release-1.10/dev/table/streaming/query_configuration.html
[2]
https://ci.apache.org/projects/flink/flink-docs-release-1.10/dev/table/config.html

本超提的两个方案也是阿里内部解决这个问题最常用的方式，但是 1.10 会有 primary key 的限制，要等到 1.11 才行。
另外这两个方案在追数据时，都可能会有毛刺现象（有几分钟没有值，因为数据追太快，跳过了）。

在 Flink 1.11 中，你可以尝试这样：

CREATE TABLE mysql (
   time_str STRING,
   uv BIGINT,
   PRIMARY KEY (ts) NOT ENFORCED
) WITH (
   'connector' = 'jdbc',
   'url' = 'jdbc:mysql://localhost:3306/mydatabase',
   'table-name' = 'myuv'
);

INSERT INTO mysql
SELECT MAX(DATE_FORMAT(ts, 'yyyy-MM-dd HH:mm:00')), COUNT(DISTINCT  user_id)
FROM user_behavior;


如果是1.10的话，我通过表转流,再转表的方式实现了，您看合理吗?
val resTmpTab: Table = tabEnv.sqlQuery(
  """
    SELECT MAX(DATE_FORMAT(ts, 'yyyy-MM-dd HH:mm:00')) time_str,COUNT(DISTINCT userkey) uv
    FROM user_behavior    GROUP BY DATE_FORMAT(ts, 'yyyy-MM-dd')    """)

val resTmpStream=tabEnv.toRetractStream[(String,Long)](resTmpTab)
  .filter(line=&gt;line._1==true).map(line=&gt;line._2)

val res= tabEnv.fromDataStream(resTmpStream)
tabEnv.sqlUpdate(
  s"""
    INSERT INTO rt_totaluv
    SELECT _1,MAX(_2)
    FROM $res
    GROUP BY _1
    """)

    您好，我程序运行一段时间后，发现checkpoint文件总在增长，应该是状态没有过期，
    我配置了tableConfig.setIdleStateRetentionTime(Time.minutes(2),Time.minutes(7)),按理说，日期是前一天的key对应的状态会在第二天过期的。

### 1.1 GroupBy + MiniBatch



### 1.2 Cumulate Window



## 2. Flink DataStream






参考：
- [快手基于 Flink 构建实时数仓场景化实践](https://smartsi.blog.csdn.net/article/details/127164637)
- [Flink计算pv和uv的通用方法](https://www.cnblogs.com/data-magnifier/p/15493159.html) https://github.com/Get-up-And-Lean/20percent/blob/3a40106bef6cbd6d2666a477a8f9417e8f6094fc/%E5%A4%A7%E6%95%B0%E6%8D%AE%E5%AE%9E%E6%97%B6%E8%AE%A1%E7%AE%97%E5%BC%95%E6%93%8EFlink%E5%AE%9E%E6%88%98%E4%B8%8E%E6%80%A7%E8%83%BD%E4%BC%98%E5%8C%96/4349%E5%A6%82%E4%BD%95%E7%BB%9F%E8%AE%A1%E7%BD%91%E7%AB%99%E5%90%84%E9%A1%B5%E9%9D%A2%E4%B8%80%E5%A4%A9%E5%86%85%E7%9A%84%20PV%20%E5%92%8C%20UV%EF%BC%9F.md
- https://github.com/chenpengcong/flink-uv/blob/master/src/main/java/UVWindowFunction.java
- https://github.com/yindahuisme/flink_learn/blob/da8af005b2f4baa63bd52ada6bc3c6fc160d78af/flink-learning-monitor/flink-learning-monitor-pvuv/src/main/java/com/zhisheng/monitor/pvuv/MapStateUvExample.java
- https://github.com/MrWhiteSike/learning-experience/blob/d7526130104f01a17e205c51398c5473c2e2ae82/flink/UserBehaviorAnalysis/NetworkFlowAnalysis/src/main/java/com/bsk/flink/pvuv/UvWithBloomFilter.java
