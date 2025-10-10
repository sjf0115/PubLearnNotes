## 1. 问题

在 idea 以编程方式运行成功之后，运行日志看到如下 warn 日志:
```java
25/10/09 23:14:00 WARN HiveConf: HiveConf of name hive.vectorized.if.expr.mode does not exist
25/10/09 23:14:00 WARN HiveConf: HiveConf of name hive.exim.test.mode does not exist
25/10/09 23:14:00 WARN HiveConf: HiveConf of name hive.query.results.cache.directory does not exist
25/10/09 23:14:00 WARN HiveConf: HiveConf of name hive.query.results.cache.wait.for.pending.results does not exist
25/10/09 23:14:00 WARN HiveConf: HiveConf of name hive.remove.orderby.in.subquery does not exist
25/10/09 23:14:00 WARN HiveConf: HiveConf of name hive.tez.bmj.use.subcache does not exist
25/10/09 23:14:00 WARN HiveConf: HiveConf of name hive.llap.io.vrb.queue.limit.min does not exist
25/10/09 23:14:00 WARN HiveConf: HiveConf of name hive.server2.wm.pool.metrics does not exist
25/10/09 23:14:00 WARN HiveConf: HiveConf of name hive.repl.add.raw.reserved.namespace does not exist
25/10/09 23:14:00 WARN HiveConf: HiveConf of name hive.resource.use.hdfs.location does not exist
25/10/09 23:14:00 WARN HiveConf: HiveConf of name hive.stats.num.nulls.estimate.percent does not exist
25/10/09 23:14:00 WARN HiveConf: HiveConf of name hive.llap.io.acid does not exist
25/10/09 23:14:00 WARN HiveConf: HiveConf of name hive.llap.zk.sm.session.timeout does not exist
25/10/09 23:14:00 WARN HiveConf: HiveConf of name hive.vectorized.ptf.max.memory.buffering.batch.count does not exist
25/10/09 23:14:00 WARN HiveConf: HiveConf of name hive.llap.task.scheduler.am.registry does not exist
25/10/09 23:14:00 WARN HiveConf: HiveConf of name hive.druid.overlord.address.default does not exist
25/10/09 23:14:00 WARN HiveConf: HiveConf of name hive.optimize.remove.sq_count_check does not exist
25/10/09 23:14:00 WARN HiveConf: HiveConf of name hive.server2.webui.enable.cors does not exist
...
```
这些警告日志是 正常现象，通常不需要担心。核心原因是：
- 配置项过时：`hive-site.xml` 中包含了一些在新版本中已废弃或不存在的配置项
- 特性差异：某些配置是针对 Hive on Tez、LLAP 等特定执行引擎的，而 Spark SQL 不使用这些引擎

这些配置是否需要？大部分不需要，因为：
- Spark SQL 使用自己的执行引擎，不依赖 Hive 的 Tez/LLAP
- 许多配置是 Hive 特定功能的，与 Spark 无关
- 警告不影响功能正常运行

推荐清理 `hive-site.xml` 配置文件。移除不必要的配置，只保留核心元数据配置：
```xml
<!-- 精简版的 hive-site.xml -->
<configuration>
  <!-- 元数据存储连接配置 -->
  <property>
    <name>javax.jdo.option.ConnectionURL</name>
    <value>jdbc:mysql://your-host:3306/hive_metastore</value>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionDriverName</name>
    <value>com.mysql.cj.jdbc.Driver</value>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionUserName</name>
    <value>your_username</value>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionPassword</name>
    <value>your_password</value>
  </property>

  <!-- Hive 数据仓库位置 -->
  <property>
    <name>hive.metastore.warehouse.dir</name>
    <value>/user/hive/warehouse</value>
  </property>

  <!-- 可选：元数据存储相关 -->
  <property>
    <name>hive.metastore.uris</name>
    <value>thrift://your-metastore-host:9083</value>
  </property>
</configuration>
```
