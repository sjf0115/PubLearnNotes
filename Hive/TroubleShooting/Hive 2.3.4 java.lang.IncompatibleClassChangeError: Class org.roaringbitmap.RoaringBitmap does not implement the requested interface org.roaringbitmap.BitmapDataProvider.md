## 1. 问题

> Hive 版本：2.3.4

在使用 RoaringBitmap 实现 UDF 时遇到如下异常：
```sql
hive (default)> SELECT rbm_bitmap_from_str("1,2,3,4");
Exception in thread "main" java.lang.IncompatibleClassChangeError: Class org.roaringbitmap.RoaringBitmap does not implement the requested interface org.roaringbitmap.BitmapDataProvider
	at org.roaringbitmap.longlong.Roaring64NavigableMap.addLong(Roaring64NavigableMap.java:206)
	at com.data.market.market.function.Rbm64Bitmap.add(Rbm64Bitmap.java:80)
	at com.data.market.udf.RbmBitmapFromStringUDF.evaluate(RbmBitmapFromStringUDF.java:55)
	at org.apache.hadoop.hive.ql.udf.generic.GenericUDF.initializeAndFoldConstants(GenericUDF.java:170)
	at org.apache.hadoop.hive.ql.plan.ExprNodeGenericFuncDesc.newInstance(ExprNodeGenericFuncDesc.java:236)
	at org.apache.hadoop.hive.ql.parse.TypeCheckProcFactory$DefaultExprProcessor.getXpathOrFuncExprNodeDesc(TypeCheckProcFactory.java:1104)
	at org.apache.hadoop.hive.ql.parse.TypeCheckProcFactory$DefaultExprProcessor.process(TypeCheckProcFactory.java:1359)
	at org.apache.hadoop.hive.ql.lib.DefaultRuleDispatcher.dispatch(DefaultRuleDispatcher.java:90)
	at org.apache.hadoop.hive.ql.lib.DefaultGraphWalker.dispatchAndReturn(DefaultGraphWalker.java:105)
	at org.apache.hadoop.hive.ql.lib.DefaultGraphWalker.dispatch(DefaultGraphWalker.java:89)
	at org.apache.hadoop.hive.ql.lib.ExpressionWalker.walk(ExpressionWalker.java:76)
	at org.apache.hadoop.hive.ql.lib.DefaultGraphWalker.startWalking(DefaultGraphWalker.java:120)
	at org.apache.hadoop.hive.ql.parse.TypeCheckProcFactory.genExprNode(TypeCheckProcFactory.java:229)
	at org.apache.hadoop.hive.ql.parse.TypeCheckProcFactory.genExprNode(TypeCheckProcFactory.java:176)
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genAllExprNodeDesc(SemanticAnalyzer.java:11613)
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genExprNodeDesc(SemanticAnalyzer.java:11568)
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genSelectPlan(SemanticAnalyzer.java:4394)
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genSelectPlan(SemanticAnalyzer.java:4167)
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genPostGroupByBodyPlan(SemanticAnalyzer.java:9705)
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genBodyPlan(SemanticAnalyzer.java:9644)
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genPlan(SemanticAnalyzer.java:10549)
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genPlan(SemanticAnalyzer.java:10427)
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genOPTree(SemanticAnalyzer.java:11125)
	at org.apache.hadoop.hive.ql.parse.CalcitePlanner.genOPTree(CalcitePlanner.java:481)
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.analyzeInternal(SemanticAnalyzer.java:11138)
	at org.apache.hadoop.hive.ql.parse.CalcitePlanner.analyzeInternal(CalcitePlanner.java:286)
	at org.apache.hadoop.hive.ql.parse.BaseSemanticAnalyzer.analyze(BaseSemanticAnalyzer.java:258)
	at org.apache.hadoop.hive.ql.Driver.compile(Driver.java:512)
	at org.apache.hadoop.hive.ql.Driver.compileInternal(Driver.java:1317)
	at org.apache.hadoop.hive.ql.Driver.runInternal(Driver.java:1457)
	at org.apache.hadoop.hive.ql.Driver.run(Driver.java:1237)
	at org.apache.hadoop.hive.ql.Driver.run(Driver.java:1227)
	at org.apache.hadoop.hive.cli.CliDriver.processLocalCmd(CliDriver.java:233)
	at org.apache.hadoop.hive.cli.CliDriver.processCmd(CliDriver.java:184)
	at org.apache.hadoop.hive.cli.CliDriver.processLine(CliDriver.java:403)
	at org.apache.hadoop.hive.cli.CliDriver.executeDriver(CliDriver.java:821)
	at org.apache.hadoop.hive.cli.CliDriver.run(CliDriver.java:759)
	at org.apache.hadoop.hive.cli.CliDriver.main(CliDriver.java:686)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at org.apache.hadoop.util.RunJar.run(RunJar.java:244)
	at org.apache.hadoop.util.RunJar.main(RunJar.java:158)
```

## 2. 分析

从提示信息中看到 `Class org.roaringbitmap.RoaringBitmap does not implement the requested interface org.roaringbitmap.BitmapDataProvider`。错误信息提示 `org.roaringbitmap.RoaringBitmap` 没有实现所需的 `org.roaringbitmap.BitmapDataProvider` 接口。我们实现 UDF 时的 RoaringBitmap 版本为 `0.9.49` 版本，可以看到 RoaringBitmap 类确实实现了 `org.roaringbitmap.BitmapDataProvider` 接口：
```Java
public class RoaringBitmap implements Cloneable, Serializable, Iterable<Integer>, Externalizable, ImmutableBitmapDataProvider, BitmapDataProvider, AppendableStorage<Container> {
		...
}
```
这种错误通常发生在 Apache Hive 中使用了不兼容版本的 RoaringBitmap 时。猜测是我们环境中可能有多个版本的 RoaringBitmap Jar 包，或者 RoaringBitmap 版本和 Hive 使用的 RoaringBitmap 版本不兼容。检查我们环境下只有一个版本，所以目标聚焦到了 Hive 使用的 RoaringBitmap 版本。查看 Hive lib 目录下发现了一个低版本的 RoaringBitmap：
```shell
(base) localhost:~ wy$ ls -al /opt/hive/lib/RoaringBitmap*
-rw-r--r--@ 1 wy  staff  445294 May 22 07:18 /opt/hive/lib/RoaringBitmap-0.5.18.jar
```
查看 `0.5.18` 版本下 RoaringBitmap 类没有实现 `org.roaringbitmap.BitmapDataProvider` 接口：
```java
public class RoaringBitmap implements Cloneable, Serializable, Iterable<Integer>, Externalizable, ImmutableBitmapDataProvider {
		...
}
```
所以问题定位是 UDF 使用的 RoaringBitmap 版本和 Hive 使用的 RoaringBitmap 版本不兼容。在这我们删除 lib 目录下的 RoaringBitmap 旧 Jar 包，引入新的 `0.9.49` 版本 Jar 包(与 UDF 使用的保持一致)。

在作出修改之后，需要重启 Hive 服务以确保新的配置生效。这样就解决了上述问题。
