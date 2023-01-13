语义解析主要是把 AST Tree 转化为 QueryBlock，那为什么要转成 QueryBlock 呢？从之前的分析，我们可以看到 AST Tree 还是很抽象，并且也不携带表、字段相关的信息，进行语义解析可以将AST Tree分模块存入QueryBlock 并携带对应的元数据信息，为生成逻辑执行计划做准备

## 1. 入口

通过 QueryState 和语法树 ASTNode 以工厂设计模式获取处理不同语义的语义分析器：
```java
BaseSemanticAnalyzer sem = SemanticAnalyzerFactory.get(queryState, tree);
```
获取具体语义分析器的工作实际是交由 getInternal 方法处理，除此之外就是判断在 getInternal 方法中通过语法树 Token 获取的 Hive 操作类型是否支持：
```java
public static BaseSemanticAnalyzer get(QueryState queryState, ASTNode tree) throws SemanticException {
  BaseSemanticAnalyzer sem = getInternal(queryState, tree);
  if(queryState.getHiveOperation() == null) {
    String query = queryState.getQueryString();
    if(query != null && query.length() > 30) {
      query = query.substring(0, 30);
    }
    String msg = "Unknown HiveOperation for query='" + query + "' queryId=" + queryState.getQueryId();
  }
  return sem;
}
```

## 2. 获取语义分析器

获取语义分析器的框架如下所示：
```java
private static BaseSemanticAnalyzer getInternal(QueryState queryState, ASTNode tree) throws SemanticException {
  if (tree.getToken() == null) {
    throw new RuntimeException("Empty Syntax Tree");
  } else {
    // 通过词法符号获取对应的 Hive 操作
    HiveOperation opType = commandType.get(tree.getType());
    queryState.setCommandType(opType);
    // 通过词法符号获取对应的语义分析器
    switch (tree.getType()) {
      ...
    }
  }
}
```
核心是通过词法符号获取对应的语义分析器。不同的词法符号对应的语义分析器不同，例如 `explain` 命令解析后的抽象语法树的 Token 为 `TOK_EXPLAIN`，需要通过 `ExplainSemanticAnalyzer` 语义分析器进行分析：
```java
switch (tree.getType()) {
    case HiveParser.TOK_EXPLAIN:
      return new ExplainSemanticAnalyzer(queryState);
    case HiveParser.TOK_EXPLAIN_SQ_REWRITE:
      return new ExplainSQRewriteSemanticAnalyzer(queryState);
    case HiveParser.TOK_LOAD:
      return new LoadSemanticAnalyzer(queryState);
    ...
    case HiveParser.TOK_CREATEDATABASE:
    case HiveParser.TOK_DROPDATABASE:
    case HiveParser.TOK_DROPTABLE:
    case HiveParser.TOK_SHOWDATABASES:
    case HiveParser.TOK_SHOWTABLES:
    case HiveParser.TOK_SHOWCOLUMNS:
    ...
    case HiveParser.TOK_SHOW_CREATEDATABASE:
    case HiveParser.TOK_SHOW_CREATETABLE:
    case HiveParser.TOK_SHOWFUNCTIONS:
    case HiveParser.TOK_SHOWPARTITIONS:
      return new DDLSemanticAnalyzer(queryState);
    ...
    case HiveParser.TOK_START_TRANSACTION:
    case HiveParser.TOK_COMMIT:
    case HiveParser.TOK_ROLLBACK:
    case HiveParser.TOK_SET_AUTOCOMMIT:
    default: {
      SemanticAnalyzer semAnalyzer = HiveConf.getBoolVar(
            queryState.getConf(), HiveConf.ConfVars.HIVE_CBO_ENABLED
      ) ? new CalcitePlanner(queryState) : new SemanticAnalyzer(queryState);
      return semAnalyzer;
    }
}
```
我们日常打交道更多的是用户查询 Query，因此会走 default 选项，根据是否开启了 CBO 优化 选择的语义分析器也不一样：如果开启了则使用 CalcitePlanner 语义分析器，否则走 SemanticAnalyzer 语义分析器。

> CBO，全称是 Cost Based Optimization，即基于代价的优化器。其优化目标是：在编译阶段，根据查询语句中涉及到的表和查询条件，计算出产生中间结果少的高效 JOIN 顺序，从而减少查询时间和资源消耗。Hive 使用开源组件 Apache Calcite 实现 CBO 优化。

| 语义分析器 | 词法符号 |
| :------------- | :------------- |
| ExplainSemanticAnalyzer | TOK_EXPLAIN |
| ExplainSQRewriteSemanticAnalyzer | TOK_EXPLAIN_SQ_REWRITE |
| LoadSemanticAnalyzer | TOK_LOAD |
| ExportSemanticAnalyzer | TOK_EXPORT |
| ImportSemanticAnalyzer | TOK_IMPORT |
| ReplicationSemanticAnalyzer | TOK_REPL_DUMP、TOK_REPL_LOAD、TOK_REPL_STATUS |
| DDLSemanticAnalyzer | TOK_ALTERTABLE、TOK_CREATEDATABASE、TOK_DROPDATABASE、TOK_DROPTABLE 等 |
| FunctionSemanticAnalyzer | TOK_CREATEFUNCTION、TOK_DROPFUNCTION、TOK_RELOADFUNCTION|
| ColumnStatsSemanticAnalyzer | TOK_ANALYZE、TOK_ALTERVIEW |
| MacroSemanticAnalyzer | TOK_CREATEMACRO、TOK_DROPMACRO |
| UpdateDeleteSemanticAnalyzer | TOK_EXPORT、TOK_UPDATE_TABLE、TOK_DELETE_FROM、TOK_MERGE |
| CalcitePlanner | 默认。开启 CBO 优化的情况下 |
| SemanticAnalyzer | 默认。不开启 CBO 优化的情况下 |



https://cloud.tencent.com/developer/article/1616684
