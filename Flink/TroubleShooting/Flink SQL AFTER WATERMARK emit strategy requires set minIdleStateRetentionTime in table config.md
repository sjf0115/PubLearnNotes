
```java
org.apache.flink.client.program.ProgramInvocationException: The main method caused an error: Sql optimization: Cannot generate a valid execution plan for the given query:

FlinkLogicalSink(table=[default_catalog.default_database.user_behavior_cnt], fields=[window_start, window_end, cnt])
+- FlinkLogicalCalc(select=[DATE_FORMAT(CAST(w$start), _UTF-16LE'yyyy-MM-dd HH:mm:ss') AS window_start, DATE_FORMAT(CAST(w$end), _UTF-16LE'yyyy-MM-dd HH:mm:ss') AS window_end, cnt])
   +- FlinkLogicalWindowAggregate(group=[{}], cnt=[COUNT()], window=[TumblingGroupWindow('w$, ts_ltz, 60000)], properties=[w$start, w$end, w$rowtime, w$proctime])
      +- FlinkLogicalCalc(select=[Reinterpret(TO_TIMESTAMP_LTZ(timestamp, 3)) AS ts_ltz])
         +- FlinkLogicalTableSourceScan(table=[[default_catalog, default_database, user_behavior, watermark=[-(TO_TIMESTAMP_LTZ($3, 3), 5000:INTERVAL SECOND)]]], fields=[uid, pid, type, timestamp])

The 'AFTER WATERMARK' emit strategy requires set 'minIdleStateRetentionTime' in table config.
Please check the documentation for the set of currently supported SQL features.
	at org.apache.flink.client.program.PackagedProgram.callMainMethod(PackagedProgram.java:372)
	at org.apache.flink.client.program.PackagedProgram.invokeInteractiveModeForExecution(PackagedProgram.java:222)
	at org.apache.flink.client.ClientUtils.executeProgram(ClientUtils.java:114)
	at org.apache.flink.client.cli.CliFrontend.executeProgram(CliFrontend.java:812)
	at org.apache.flink.client.cli.CliFrontend.run(CliFrontend.java:246)
	at org.apache.flink.client.cli.CliFrontend.parseAndRun(CliFrontend.java:1054)
	at org.apache.flink.client.cli.CliFrontend.lambda$main$10(CliFrontend.java:1132)
	at java.security.AccessController.doPrivileged(Native Method)
	at javax.security.auth.Subject.doAs(Subject.java:422)
	at org.apache.hadoop.security.UserGroupInformation.doAs(UserGroupInformation.java:1762)
	at org.apache.flink.runtime.security.contexts.HadoopSecurityContext.runSecured(HadoopSecurityContext.java:41)
	at org.apache.flink.client.cli.CliFrontend.main(CliFrontend.java:1132)
Caused by: org.apache.flink.table.api.TableException: Sql optimization: Cannot generate a valid execution plan for the given query:

FlinkLogicalSink(table=[default_catalog.default_database.user_behavior_cnt], fields=[window_start, window_end, cnt])
+- FlinkLogicalCalc(select=[DATE_FORMAT(CAST(w$start), _UTF-16LE'yyyy-MM-dd HH:mm:ss') AS window_start, DATE_FORMAT(CAST(w$end), _UTF-16LE'yyyy-MM-dd HH:mm:ss') AS window_end, cnt])
   +- FlinkLogicalWindowAggregate(group=[{}], cnt=[COUNT()], window=[TumblingGroupWindow('w$, ts_ltz, 60000)], properties=[w$start, w$end, w$rowtime, w$proctime])
      +- FlinkLogicalCalc(select=[Reinterpret(TO_TIMESTAMP_LTZ(timestamp, 3)) AS ts_ltz])
         +- FlinkLogicalTableSourceScan(table=[[default_catalog, default_database, user_behavior, watermark=[-(TO_TIMESTAMP_LTZ($3, 3), 5000:INTERVAL SECOND)]]], fields=[uid, pid, type, timestamp])

The 'AFTER WATERMARK' emit strategy requires set 'minIdleStateRetentionTime' in table config.
Please check the documentation for the set of currently supported SQL features.
	at org.apache.flink.table.planner.plan.optimize.program.FlinkVolcanoProgram.optimize(FlinkVolcanoProgram.scala:86)
	at org.apache.flink.table.planner.plan.optimize.program.FlinkChainedProgram$$anonfun$optimize$1.apply(FlinkChainedProgram.scala:62)
	at org.apache.flink.table.planner.plan.optimize.program.FlinkChainedProgram$$anonfun$optimize$1.apply(FlinkChainedProgram.scala:58)
	at scala.collection.TraversableOnce$$anonfun$foldLeft$1.apply(TraversableOnce.scala:157)
	at scala.collection.TraversableOnce$$anonfun$foldLeft$1.apply(TraversableOnce.scala:157)
	at scala.collection.Iterator$class.foreach(Iterator.scala:891)
	at scala.collection.AbstractIterator.foreach(Iterator.scala:1334)
	at scala.collection.IterableLike$class.foreach(IterableLike.scala:72)
	at scala.collection.AbstractIterable.foreach(Iterable.scala:54)
	at scala.collection.TraversableOnce$class.foldLeft(TraversableOnce.scala:157)
	at scala.collection.AbstractTraversable.foldLeft(Traversable.scala:104)
	at org.apache.flink.table.planner.plan.optimize.program.FlinkChainedProgram.optimize(FlinkChainedProgram.scala:57)
	at org.apache.flink.table.planner.plan.optimize.StreamCommonSubGraphBasedOptimizer.optimizeTree(StreamCommonSubGraphBasedOptimizer.scala:163)
	at org.apache.flink.table.planner.plan.optimize.StreamCommonSubGraphBasedOptimizer.doOptimize(StreamCommonSubGraphBasedOptimizer.scala:77)
	at org.apache.flink.table.planner.plan.optimize.CommonSubGraphBasedOptimizer.optimize(CommonSubGraphBasedOptimizer.scala:77)
	at org.apache.flink.table.planner.delegation.PlannerBase.optimize(PlannerBase.scala:279)
	at org.apache.flink.table.planner.delegation.PlannerBase.translate(PlannerBase.scala:163)
	at org.apache.flink.table.api.internal.TableEnvironmentImpl.translate(TableEnvironmentImpl.java:1518)
	at org.apache.flink.table.api.internal.TableEnvironmentImpl.executeInternal(TableEnvironmentImpl.java:740)
	at org.apache.flink.table.api.internal.TableEnvironmentImpl.executeInternal(TableEnvironmentImpl.java:856)
	at org.apache.flink.table.api.internal.TableEnvironmentImpl.executeSql(TableEnvironmentImpl.java:730)
	at com.flink.example.table.function.window.LateFireEventTimeTumbleWindowExample.main(LateFireEventTimeTumbleWindowExample.java:58)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at org.apache.flink.client.program.PackagedProgram.callMainMethod(PackagedProgram.java:355)
	... 11 more
Caused by: org.apache.flink.table.api.TableException: The 'AFTER WATERMARK' emit strategy requires set 'minIdleStateRetentionTime' in table config.
	at org.apache.flink.table.planner.plan.utils.WindowEmitStrategy.checkValidation(WindowEmitStrategy.scala:50)
	at org.apache.flink.table.planner.plan.utils.WindowEmitStrategy.<init>(WindowEmitStrategy.scala:41)
	at org.apache.flink.table.planner.plan.utils.WindowEmitStrategy$.apply(WindowEmitStrategy.scala:163)
	at org.apache.flink.table.planner.plan.rules.physical.stream.StreamPhysicalGroupWindowAggregateRule.convert(StreamPhysicalGroupWindowAggregateRule.scala:75)
	at org.apache.calcite.rel.convert.ConverterRule.onMatch(ConverterRule.java:167)
	at org.apache.calcite.plan.volcano.VolcanoRuleCall.onMatch(VolcanoRuleCall.java:229)
	at org.apache.calcite.plan.volcano.IterativeRuleDriver.drive(IterativeRuleDriver.java:58)
	at org.apache.calcite.plan.volcano.VolcanoPlanner.findBestExp(VolcanoPlanner.java:510)
	at org.apache.calcite.tools.Programs$RuleSetProgram.run(Programs.java:312)
	at org.apache.flink.table.planner.plan.optimize.program.FlinkVolcanoProgram.optimize(FlinkVolcanoProgram.scala:64)
	... 37 more
```
