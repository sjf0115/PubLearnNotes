

```java
org.apache.flink.client.program.ProgramInvocationException: The main method caused an error: Unable to instantiate java compiler
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
Caused by: java.lang.IllegalStateException: Unable to instantiate java compiler
	at org.apache.calcite.rel.metadata.JaninoRelMetadataProvider.compile(JaninoRelMetadataProvider.java:428)
	at org.apache.calcite.rel.metadata.JaninoRelMetadataProvider.load3(JaninoRelMetadataProvider.java:374)
	at org.apache.calcite.rel.metadata.JaninoRelMetadataProvider.lambda$static$0(JaninoRelMetadataProvider.java:109)
	at org.apache.flink.calcite.shaded.com.google.common.cache.CacheLoader$FunctionToCacheLoader.load(CacheLoader.java:165)
	at org.apache.flink.calcite.shaded.com.google.common.cache.LocalCache$LoadingValueReference.loadFuture(LocalCache.java:3529)
	...
	at org.apache.flink.table.planner.delegation.PlannerBase.optimize(PlannerBase.scala:279)
	at org.apache.flink.table.planner.delegation.PlannerBase.translate(PlannerBase.scala:163)
	at org.apache.flink.table.api.internal.TableEnvironmentImpl.translate(TableEnvironmentImpl.java:1518)
	at org.apache.flink.table.api.internal.TableEnvironmentImpl.executeInternal(TableEnvironmentImpl.java:740)
	at org.apache.flink.table.api.internal.TableEnvironmentImpl.executeInternal(TableEnvironmentImpl.java:856)
	at org.apache.flink.table.api.internal.TableEnvironmentImpl.executeSql(TableEnvironmentImpl.java:730)
	at com.flink.example.table.function.windows.GroupWindowSQLExample.runProcessTimeExample(GroupWindowSQLExample.java:98)
	at com.flink.example.table.function.windows.GroupWindowSQLExample.main(GroupWindowSQLExample.java:27)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at org.apache.flink.client.program.PackagedProgram.callMainMethod(PackagedProgram.java:355)
	... 11 more
Caused by: java.lang.ClassCastException: org.codehaus.janino.CompilerFactory cannot be cast to org.codehaus.commons.compiler.ICompilerFactory
	at org.codehaus.commons.compiler.CompilerFactoryFactory.getCompilerFactory(CompilerFactoryFactory.java:129)
	at org.codehaus.commons.compiler.CompilerFactoryFactory.getDefaultCompilerFactory(CompilerFactoryFactory.java:79)
	at org.apache.calcite.rel.metadata.JaninoRelMetadataProvider.compile(JaninoRelMetadataProvider.java:426)
	... 63 more
```

https://blog.csdn.net/woloqun/article/details/105657539

http://apache-flink-mailing-list-archive.1008284.n3.nabble.com/Re-TIME-TIMESTAMP-parse-in-Flink-TABLE-SQL-API-td38150.html

有两位用户都遇到了Class冲突的问题，这是因为Flink
1.10把客户端的ClassLoader解析顺序调整为了Child优先，这就导致用户的Jar包不能包含Flink框架的classes，比如常见的Calcite、Flink-Planner依赖、Hive依赖等等。用户需要把有冲突classes的jar放到flink-home/lib下，或者调整策略为Parent优先。


https://blog.csdn.net/weixin_44056920/article/details/118110262

https://www.cnblogs.com/felixzh/p/13448047.html
...
