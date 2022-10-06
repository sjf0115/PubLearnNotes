

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

### 1.1 GroupBy



### 1.2 Cumulate Window



## 2. Flink DataStream






参考：
- [快手基于 Flink 构建实时数仓场景化实践](https://smartsi.blog.csdn.net/article/details/127164637)
