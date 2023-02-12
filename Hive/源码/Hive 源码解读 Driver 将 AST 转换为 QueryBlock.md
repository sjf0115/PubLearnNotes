- Driver#compile
  - BaseSemanticAnalyzer#analyze
    - BaseSemanticAnalyzer#analyzeInternal
      - CalcitePlanner#analyzeInternal
        - SemanticAnalyzer#analyzeInternal
          - SemanticAnalyzer#processPositionAlias
          - SemanticAnalyzer#genResolvedParseTree
            - SemanticAnalyzer#doPhase1


获取对应的语义分析器并进行语义分析：
> 位置：org.apache.hadoop.hive.ql.Driver#compile
```java
BaseSemanticAnalyzer sem = SemanticAnalyzerFactory.get(queryState, tree);
sem.analyze(tree, ctx);
// org.apache.hadoop.hive.ql.parse.BaseSemanticAnalyzer
public void analyze(ASTNode ast, Context ctx) throws SemanticException {
    // 语义分析初始化
    initCtx(ctx);
    init(true);
    // 实际语义分析
    analyzeInternal(ast);
}
```

## 1. 语义分析初始化

在进行语义分析之前首先进行调用 `initCtx` 和 `init` 进行初始化：
```java
public void initCtx(Context ctx) {
    this.ctx = ctx;
}
// org.apache.hadoop.hive.ql.parse.BaseSemanticAnalyzer
public void init(boolean clearPartsCache) {
    //no-op
}
```
SemanticAnalyzer
```java
// org.apache.hadoop.hive.ql.parse.SemanticAnalyzer
public void init(boolean clearPartsCache) {
  // clear most members
  reset(clearPartsCache);
  // 创建 QueryBlock 对象
  QB qb = new QB(null, null, false);
  this.qb = qb;
}
```
在初始化中最重要的就是创建 QueryBlock 对象 QB：
```java
public class QB {
  private final int numJoins = 0;
  private final int numGbys = 0;
  private int numSels = 0;
  private int numSelDi = 0;
  // 表的别名
  private HashMap<String, String> aliasToTabs;
  // 子查询别名与QBExpr的关系
  private HashMap<String, QBExpr> aliasToSubq;
  // 视图别名与表的关系
  private HashMap<String, Table> viewAliasToViewSchema;
  private HashMap<String, Map<String, String>> aliasToProps;
  // 所有别名
  private List<String> aliases;
  private QBParseInfo qbp;
  private QBMetaData qbm;
  private QBJoinTree qbjoin;
  private String id;
  private boolean isQuery;
  private boolean isAnalyzeRewrite;
  private CreateTableDesc tblDesc = null; // table descriptor of the final
  private CreateTableDesc directoryDesc = null ;
  private List<Path> encryptedTargetTablePaths;
  private boolean insideView;
  private Set<String> aliasInsideView;
  ...
}
```
QueryBlock 是一条 SQL 最基本的组成单元，包括三个部分：输入源，计算过程，输出。简单来讲一个 QueryBlock 就是一个子查询。下面介绍几个 QueryBlock 的重要属性：
- aliasToTabs：保存表的别名。
- aliasToSubq：保存子查询与 QueryBlock 表达式的映射关系。键是子查询的别名。值是 QueryBlock 表达式对象 QBExpr。
- viewAliasToViewSchema：保存视图别名与表的关系。
- aliases：保存所有的别名。
- qbp：QBParseInfo 对象，保存 QueryBlock 相关的解析信息。
- qbm：QBMetaData 对象，保存 QueryBlock 相关的元数据信息。
- qbjoin： Join 树的内部实现。



QueryBlock 表达式：
```java
public class QBExpr {
  public static enum Opcode {
    NULLOP, UNION, INTERSECT, INTERSECTALL, EXCEPT, EXCEPTALL, DIFF
  };
  private Opcode opcode;
  private QBExpr qbexpr1;
  private QBExpr qbexpr2;
  private QB qb;
  private String alias;
  ...
}
```

QBParseInfo
```java
public class QBParseInfo {
  private boolean isSubQ;
  private String alias;
  private ASTNode joinExpr;
  private ASTNode hints;
  private List<ASTNode> hintList;
  private final HashMap<String, ASTNode> aliasToSrc;
  /**
   * insclause-0 -> TOK_TAB ASTNode
   */
  private final HashMap<String, ASTNode> nameToDest;
  /**
   * For 'insert into FOO(x,y) select ...' this stores the
   * insclause-0 -> x,y mapping
   */
  private final Map<String, List<String>> nameToDestSchema;
  private final HashMap<String, TableSample> nameToSample;
  private final Map<ASTNode, String> exprToColumnAlias;
  private final Map<String, ASTNode> destToSelExpr;
  private final HashMap<String, ASTNode> destToWhereExpr;
  private final HashMap<String, ASTNode> destToGroupby;
  private final Set<String> destRollups;
  private final Set<String> destCubes;
  private final Set<String> destGroupingSets;
  private final Map<String, ASTNode> destToHaving;
  private final Map<String, Boolean> destToOpType;
  // insertIntoTables/insertOverwriteTables map a table's fullName to its ast;
  private final Map<String, ASTNode> insertIntoTables;
  private final Map<String, ASTNode> insertOverwriteTables;
  private ASTNode queryFromExpr;

  private boolean isAnalyzeCommand; // used for the analyze command (statistics)
  private boolean isNoScanAnalyzeCommand; // used for the analyze command (statistics) (noscan)

  private final HashMap<String, TableSpec> tableSpecs; // used for statistics

  private AnalyzeRewriteContext analyzeRewrite;


  /**
   * ClusterBy is a short name for both DistributeBy and SortBy.
   */
  private final HashMap<String, ASTNode> destToClusterby;
  /**
   * DistributeBy controls the hashcode of the row, which determines which
   * reducer the rows will go to.
   */
  private final HashMap<String, ASTNode> destToDistributeby;
  /**
   * SortBy controls the reduce keys, which affects the order of rows that the
   * reducer receives.
   */

  private final HashMap<String, ASTNode> destToSortby;

  /**
   * Maping from table/subquery aliases to all the associated lateral view nodes.
   */
  private final HashMap<String, ArrayList<ASTNode>> aliasToLateralViews;

  private final HashMap<String, ASTNode> destToLateralView;

  /* Order by clause */
  private final HashMap<String, ASTNode> destToOrderby;
  // Use SimpleEntry to save the offset and rowcount of limit clause
  // KEY of SimpleEntry: offset
  // VALUE of SimpleEntry: rowcount
  private final HashMap<String, SimpleEntry<Integer, Integer>> destToLimit;
  private int outerQueryLimit;

  // used by GroupBy
  private final LinkedHashMap<String, LinkedHashMap<String, ASTNode>> destToAggregationExprs;
  private final HashMap<String, List<ASTNode>> destToDistinctFuncExprs;

  // used by Windowing
  private final LinkedHashMap<String, LinkedHashMap<String, ASTNode>> destToWindowingExprs;
  ...
}
```



语义解析就是从ASTTree生成QueryBlock的过程，即从抽象语法树中找出所有的基本单元以及每个单元之间的关系的过程。每个基本单元创建一个QB对象，将每个基本单元的不同操作转化为QB对象的不同属性。


## 2. 语义分析

analyzeInternal 本身是一个抽象类，不同的语义分析器有不同的语义分析实现，在这我们以 CalcitePlanner 语义分析器为例进行分析。
```java
public void analyzeInternal(ASTNode ast) throws SemanticException {
  if (runCBO) {
    super.analyzeInternal(ast, new PlannerContextFactory() {
      @Override
      public PlannerContext create() {
        return new PreCboCtx();
      }
    });
  } else {
    super.analyzeInternal(ast);
  }
}
```
根据是否开启了 CBO 优化，传递 analyzeInternal 方法的参数也不一样：
> org.apache.hadoop.hive.ql.parse.SemanticAnalyzer
```java
// 不开启 CBO 优化
public void analyzeInternal(ASTNode ast) throws SemanticException {
    analyzeInternal(ast, new PlannerContext());
}
// 开启 CBO 优化
void analyzeInternal(ASTNode ast, PlannerContextFactory pcf) throws SemanticException {
    LOG.info("Starting Semantic Analysis");
    // 1. Generate Resolved Parse tree from syntax tree
    boolean needsTransform = needsTransform();
    //change the location of position alias process here
    processPositionAlias(ast);
    PlannerContext plannerCtx = pcf.create();
    if (!genResolvedParseTree(ast, plannerCtx)) {
      return;
    }
    ...
}
```
从上面可以知道如果开启了 CBO 优化会使用 PreCboCtx（继承自 PlannerContext）。下面重点分析一下如何进行语义分析。

### 2.1 生成解析树

首先第一步就是根据抽象语法树 AST 生成 ResolvedParseTree 解析树：
```java
boolean needsTransform = needsTransform();
// 将 GroupBy 和 OrderBy 中的位置别名替换为名称
processPositionAlias(ast);
PlannerContext plannerCtx = pcf.create();
// 生成解析树 本质上就是把 AST 解析成 QB
if (!genResolvedParseTree(ast, plannerCtx)) {
  return;
}
// 如果子查询或者视图中 Order/SortBy 没有 LIMIT 将被移除
if (HiveConf.getBoolVar(conf, ConfVars.HIVE_REMOVE_ORDERBY_IN_SUBQUERY)) {
  for (String alias : qb.getSubqAliases()) {
    removeOBInSubQuery(qb.getSubqForAlias(alias));
  }
}
// 检查查询结果是否缓存 如果先前执行的查询的结果会被缓存，那么再次执行相同的查询时会复用缓存的查询结果
boolean isCacheEnabled = isResultsCacheEnabled();
QueryResultsCache.LookupInfo lookupInfo = null;
if (isCacheEnabled && !needsTransform && queryTypeCanUseCache()) {
  lookupInfo = createLookupInfoForQuery(ast);
  if (checkResultsCache(lookupInfo)) {
    return;
  }
}

ASTNode astForMasking;
if (isCBOExecuted() && needsTransform && (qb.isCTAS() || qb.isView() || qb.isMaterializedView() || qb.isMultiDestQuery())) {
  astForMasking = (ASTNode) ParseDriver.adaptor.dupTree(ast);
} else {
  astForMasking = ast;
}
```
在生成解析树之前先通过 processPositionAlias 方法将 GroupBy 和 OrderBy 中的位置别名替换为名称。实际生成解析树的过程是通过 genResolvedParseTree 方法来完成的，本质上是把 AST 解析成 QB 对象，在 []() 会详细介绍是如何生成解析树的。

在 Hive 3.0.0 版本之后，如果子查询或者视图中 Order/SortBy 没有 LIMIT 将被移除：
```java
if (HiveConf.getBoolVar(conf, ConfVars.HIVE_REMOVE_ORDERBY_IN_SUBQUERY)) {
  for (String alias : qb.getSubqAliases()) {
    removeOBInSubQuery(qb.getSubqForAlias(alias));
  }
}
```
> hive.remove.orderby.in.subquery 参数默认为 true，即子查询或者视图中 Order/SortBy 没有 LIMIT 将会被移除，具体参阅[配置](https://cwiki.apache.org/confluence/display/Hive/Configuration+Properties#ConfigurationProperties-hive.remove.orderby.in.subquery)

如果开启 CBO 优化并应用 Masking/Filtering 屏蔽过滤策略，则需要创建一个 AST 的副本。原因是生成 Operator 树的过程中可能会修改原始的 AST，但如果需要第二次解析，则需要解析未修改的 AST：
```java
ASTNode astForMasking;
if (isCBOExecuted() && needsTransform && (qb.isCTAS() || qb.isView() || qb.isMaterializedView() || qb.isMultiDestQuery())) {
  astForMasking = (ASTNode) ParseDriver.adaptor.dupTree(ast);
} else {
  astForMasking = ast;
}
```




....
