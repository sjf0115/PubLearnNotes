> 位置：org.apache.hadoop.hive.ql.Driver#compile
```java
BaseSemanticAnalyzer sem = SemanticAnalyzerFactory.get(queryState, tree);
sem.analyze(tree, ctx);
```
> 位置：org.apache.hadoop.hive.ql.parse.BaseSemanticAnalyzer
```java
public void analyze(ASTNode ast, Context ctx) throws SemanticException {
    initCtx(ctx);
    init(true);
    analyzeInternal(ast);
}
```

## 1. 初始化

```java
public void initCtx(Context ctx) {
    this.ctx = ctx;
}
```

```java
// org.apache.hadoop.hive.ql.parse.BaseSemanticAnalyzer
public void init(boolean clearPartsCache) {
    //no-op
}

// org.apache.hadoop.hive.ql.parse.SemanticAnalyzer
public void init(boolean clearPartsCache) {
  // clear most members
  reset(clearPartsCache);
  // 创建 QueryBlock 对象
  QB qb = new QB(null, null, false);
  this.qb = qb;
}
```
在初始化中最重要的就是创建 QueryBlock 对象 QB，QueryBlock 的一个实现：
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



语义解析就是从ASTTree生成QueryBlock的过程，即从抽象语法树中找出所有的基本单元以及每个单元之间的关系的过程。每个基本单元创建一个QB对象，将每个基本单元的不同操作转化为QB对象的不同属性。


## 3. analyzeInternal

- Driver#compile
  - BaseSemanticAnalyzer#analyze
    - BaseSemanticAnalyzer#analyzeInternal
      - CalcitePlanner#analyzeInternal
        - SemanticAnalyzer#analyzeInternal
          - SemanticAnalyzer#processPositionAlias
          - SemanticAnalyzer#genResolvedParseTree
            - SemanticAnalyzer#doPhase1

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

> org.apache.hadoop.hive.ql.parse.SemanticAnalyzer
```java
public void analyzeInternal(ASTNode ast) throws SemanticException {
    analyzeInternal(ast, new PlannerContext());
}

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

```java
boolean genResolvedParseTree(ASTNode ast, PlannerContext plannerCtx) throws SemanticException {
  ASTNode child = ast;
  this.ast = ast;
  viewsExpanded = new ArrayList<String>();
  ctesExpanded = new ArrayList<String>();

  // 1. analyze and process the position alias
  // step processPositionAlias out of genResolvedParseTree

  // 2. analyze create table command
  if (ast.getToken().getType() == HiveParser.TOK_CREATETABLE) {
    // if it is not CTAS, we don't need to go further and just return
    if ((child = analyzeCreateTable(ast, qb, plannerCtx)) == null) {
      return false;
    }
  } else {
    queryState.setCommandType(HiveOperation.QUERY);
  }

  // 3. analyze create view command
  if (ast.getToken().getType() == HiveParser.TOK_CREATEVIEW ||
      ast.getToken().getType() == HiveParser.TOK_CREATE_MATERIALIZED_VIEW ||
      (ast.getToken().getType() == HiveParser.TOK_ALTERVIEW && ast.getChild(1).getType() == HiveParser.TOK_QUERY)) {
    child = analyzeCreateView(ast, qb, plannerCtx);
    if (child == null) {
      return false;
    }
    viewSelect = child;
    // prevent view from referencing itself
    viewsExpanded.add(createVwDesc.getViewName());
  }

  switch(ast.getToken().getType()) {
  case HiveParser.TOK_SET_AUTOCOMMIT:
    assert ast.getChildCount() == 1;
    if(ast.getChild(0).getType() == HiveParser.TOK_TRUE) {
      setAutoCommitValue(true);
    }
    else if(ast.getChild(0).getType() == HiveParser.TOK_FALSE) {
      setAutoCommitValue(false);
    }
    else {
      assert false : "Unexpected child of TOK_SET_AUTOCOMMIT: " + ast.getChild(0).getType();
    }
    //fall through
  case HiveParser.TOK_START_TRANSACTION:
  case HiveParser.TOK_COMMIT:
  case HiveParser.TOK_ROLLBACK:
    if(!(conf.getBoolVar(ConfVars.HIVE_IN_TEST) || conf.getBoolVar(ConfVars.HIVE_IN_TEZ_TEST))) {
      throw new IllegalStateException(SemanticAnalyzerFactory.getOperation(ast.getToken().getType()) +
          " is not supported yet.");
    }
    queryState.setCommandType(SemanticAnalyzerFactory.getOperation(ast.getToken().getType()));
    return false;
  }

  // masking and filtering should be created here
  // the basic idea is similar to unparseTranslator.
  tableMask = new TableMask(this, conf, ctx.isSkipTableMasking());

  // 4. continue analyzing from the child ASTNode.
  Phase1Ctx ctx_1 = initPhase1Ctx();
  if (!doPhase1(child, qb, ctx_1, plannerCtx)) {
    // if phase1Result false return
    return false;
  }

  // 5. Resolve Parse Tree
  // Materialization is allowed if it is not a view definition
  getMetaData(qb, createVwDesc == null);
  plannerCtx.setParseTreeAttr(child, ctx_1);
  return true;
}
```


doPhase1 主要是递归遍历 AST，进行语义检查，并建立下面的映射关系表：
- 获取所有表/子查询的所有别名，并在aliasToTabs, aliasToSubq中进行适当的映射
- 获取目标的位置并将子句命名为“inclause”+ i
- 创建从聚合树的字符串表示到实际聚合 AST 的映射
- 在destToSelExpr中创建从子句名称到选择表达式AST的映射
- 在 aliasToLateralViews 中创建一个从表别名到横向视图 AST 的映射


```java
public boolean doPhase1(ASTNode ast, QB qb, Phase1Ctx ctx_1, PlannerContext plannerCtx) throws SemanticException {
    boolean phase1Result = true;
    QBParseInfo qbp = qb.getParseInfo();
    boolean skipRecursion = false;
    if (ast.getToken() != null) {
        ...
        // 逻辑处理
        ...
    }
    if (!skipRecursion) {
      // 迭代遍历子树
      int child_count = ast.getChildCount();
      for (int child_pos = 0; child_pos < child_count && phase1Result; ++child_pos) {
        phase1Result = phase1Result && doPhase1((ASTNode)ast.getChild(child_pos), qb, ctx_1, plannerCtx);
      }
    }
    return phase1Result;
```





....
