
从抽象语法树中获取解析树的过程就是将 AST 树转换为 QueryBlock（QB） 的过程，QB 可以理解为是最小的语法单元，将 AST 树每一个节点单独取出来并封装成一个个 QB，同时在这里替换元数据里的信息。根据语法树生成解析树需要经过如下两步：
```java
boolean needsTransform = needsTransform();
// 1. 位置别名替换为名称
processPositionAlias(ast);
PlannerContext plannerCtx = pcf.create();
// 2. 生成解析树
if (!genResolvedParseTree(ast, plannerCtx)) {
  return;
}
```

## 1. 位置别名替换为名称

将 GROUP BY 和 ORDER BY 中的位置别名替换为名称是生成解析树的前置操作。先看看 GROUP BY 和 ORDER BY 中位置别名具体是怎么回事。在 Hive 中 GROUP BY 和 ORDER BY 语句后面可以写分组/排序字段的位置（而不用写具体的字段名称，默认不开启）：
```sql
SELECT user_id, name
FROM behavior
GROUP BY 1,2
ORDER BY 2
DESC 1;
```
但是在实际生产环境中不建议这么使用，读起来不方便。processPositionAlias 方法的目标就是将字段位置转换为字段名称，具体如下所示：
```java
public void processPositionAlias(ASTNode ast) throws SemanticException {
  // 是否开启了根据字段位置进行分组 GroupBy 和排序 OrderBy
  // 默认不开启
  boolean isBothByPos = HiveConf.getBoolVar(conf, ConfVars.HIVE_GROUPBY_ORDERBY_POSITION_ALIAS);
  boolean isGbyByPos = isBothByPos || HiveConf.getBoolVar(conf, ConfVars.HIVE_GROUPBY_POSITION_ALIAS);
  boolean isObyByPos = isBothByPos || HiveConf.getBoolVar(conf, ConfVars.HIVE_ORDERBY_POSITION_ALIAS);

  Deque<ASTNode> stack = new ArrayDeque<ASTNode>();
  stack.push(ast);

  while (!stack.isEmpty()) {
    ASTNode next = stack.pop();
    if (next.getChildCount()  == 0) {
      continue;
    }
    boolean isAllCol;
    ASTNode selectNode = null;
    ASTNode groupbyNode = null;
    ASTNode orderbyNode = null;

    // 根据节点类型获取 SELECT 节点、GroupBy 节点以及 OrderBy 节点
    int child_count = next.getChildCount();
    for (int child_pos = 0; child_pos < child_count; ++child_pos) {
      ASTNode node = (ASTNode) next.getChild(child_pos);
      int type = node.getToken().getType();
      if (type == HiveParser.TOK_SELECT || type == HiveParser.TOK_SELECTDI) {
        // SELECT 节点
        selectNode = node;
      } else if (type == HiveParser.TOK_GROUPBY) {
        // GroupBy 节点
        groupbyNode = node;
      } else if (type == HiveParser.TOK_ORDERBY) {
        // OrderBy 节点
        orderbyNode = node;
      }
    }

    if (selectNode != null) {
      // SELECT 节点字段个数
      int selectExpCnt = selectNode.getChildCount();
      // 1. 处理 GroupBy 中位置别名 用实际的列名替换
      if (groupbyNode != null) {
        for (int child_pos = 0; child_pos < groupbyNode.getChildCount(); ++child_pos) {
          ASTNode node = (ASTNode) groupbyNode.getChild(child_pos);
          if (node.getToken().getType() == HiveParser.Number) {
            // 是否开启 hive.groupby.position.alias
            if (isGbyByPos) {
              int pos = Integer.parseInt(node.getText());
              if (pos > 0 && pos <= selectExpCnt) {
                groupbyNode.setChild(child_pos, selectNode.getChild(pos - 1).getChild(0));
              } else {
                // 抛异常 位置别名超出范围
              }
            } else {
              // 输出警告 如果使用位置别名进行分组需要开启 hive.groupby.position.alias 参数
            }
          }
        }
      }

      // 2. 处理 OrderBy 中位置别名 用实际的列名替换
      if (!HiveConf.getBoolVar(conf, HiveConf.ConfVars.HIVE_CBO_ENABLED) && orderbyNode != null) {
        isAllCol = false;
        for (int child_pos = 0; child_pos < selectNode.getChildCount(); ++child_pos) {
          ASTNode node = (ASTNode) selectNode.getChild(child_pos).getChild(0);
          if (node != null && node.getToken().getType() == HiveParser.TOK_ALLCOLREF) {
            isAllCol = true;
          }
        }
        for (int child_pos = 0; child_pos < orderbyNode.getChildCount(); ++child_pos) {
          ASTNode colNode = null;
          ASTNode node = null;
          if (orderbyNode.getChildCount() > 0) {
            colNode = (ASTNode) orderbyNode.getChild(child_pos).getChild(0);
            if (colNode.getChildCount() > 0) {
              node = (ASTNode) colNode.getChild(0);
            }
          }
          if (node != null && node.getToken().getType() == HiveParser.Number) {
            // 是否开启 hive.orderby.position.alias
            if (isObyByPos) {
              if (!isAllCol) {
                int pos = Integer.parseInt(node.getText());
                if (pos > 0 && pos <= selectExpCnt && selectNode.getChild(pos - 1).getChildCount() > 0) {
                  colNode.setChild(0, selectNode.getChild(pos - 1).getChild(0));
                } else {
                  // 抛异常 位置别名超出范围
                }
              } else {
                throw new SemanticException(ErrorMsg.NO_SUPPORTED_ORDERBY_ALLCOLREF_POS.getMsg());
              }
            } else {
              // 输出警告 如果使用位置别名进行分组需要开启 hive.orderby.position.alias 参数
            }
          }
        }
      }
    }
    for (int i = next.getChildren().size() - 1; i >= 0; i--) {
      stack.push((ASTNode)next.getChildren().get(i));
    }
  }
}
```

## 2. 生成解析树

将 GROUP BY 和 ORDER BY 中的位置别名替换为名称之后，就可以正式的将 AST 树转换为解析树（转换为 QueryBlock），具体可以分为如下 5 步操作:
```java
boolean genResolvedParseTree(ASTNode ast, PlannerContext plannerCtx) throws SemanticException {
  ASTNode child = ast;
  this.ast = ast;
  viewsExpanded = new ArrayList<String>();
  ctesExpanded = new ArrayList<String>();
  // 1. 分析与处理位置别名
  ...
  // 2. 分析建表命令
  ...
  // 3. 分析建表命令
  ...
  // 4. 分析子树
  ...
  // 5. 生成解析树
}
```

### 2.1 分析与处理位置别名

将 GROUP BY 和 ORDER BY 中的位置别名替换为名称这一步操作移到了 genResolvedParseTree 方法之外，即作为了生成解析树的上述第一大步。

### 2.2 分析建表命令

```java
// 2. analyze create table command
if (ast.getToken().getType() == HiveParser.TOK_CREATETABLE) {
  // 建表语句命令
  if ((child = analyzeCreateTable(ast, qb, plannerCtx)) == null) {
    // 如果不是 CTAS 语句(CREATE TABLE ... AS SELECT ...) 直接返回
    return false;
  }
} else {
  // 查询语句命令
  queryState.setCommandType(HiveOperation.QUERY);
}
```

### 2.3 分析创建视图命令

```java
// 3. 分析创建视图命令
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
```

### 2.4 分析子树

这一步是生成解析树的核心操作，首先由 initPhase1Ctx 方法完成操作之前的初始化，最终交由 doPhase1 方法来完成：
```java
// 4. continue analyzing from the child ASTNode.
// 分析子树
Phase1Ctx ctx_1 = initPhase1Ctx();
if (!doPhase1(child, qb, ctx_1, plannerCtx)) {
  return false;
}
LOG.info("Completed phase 1 of Semantic Analysis");
```

initPhase1Ctx 初始化操作比较简单，只是简单的创建一个包含两个字段（dest 和 nextNum）的 Phase1Ctx 对象：
```java
public Phase1Ctx initPhase1Ctx() {
  Phase1Ctx ctx_1 = new Phase1Ctx();
  ctx_1.nextNum = 0;
  ctx_1.dest = "reduce";
  return ctx_1;
}

static class Phase1Ctx {
  String dest;
  int nextNum;
}
```

核心操作交最终由 doPhase1 来完成。doPhase1 主要是递归遍历 AST，并进行语义检查，先简单看一下 doPhase1 的运行框架：
```java
public boolean doPhase1(ASTNode ast, QB qb, Phase1Ctx ctx_1, PlannerContext plannerCtx) throws SemanticException {
  boolean phase1Result = true;
  QBParseInfo qbp = qb.getParseInfo();
  boolean skipRecursion = false;
  // 核心逻辑处理
  if (ast.getToken() != null) {
      ...
  }
  // 是否跳过递归
  if (!skipRecursion) {
    // 迭代遍历子节点
    int child_count = ast.getChildCount();
    for (int child_pos = 0; child_pos < child_count && phase1Result; ++child_pos) {
      // 递归遍历子节点
      ASTNode childNode = (ASTNode)ast.getChild(child_pos);
      phase1Result = phase1Result && doPhase1(childNode, qb, ctx_1, plannerCtx);
    }
  }
  return phase1Result;
}
```
核心逻辑处理主要是建立下面的映射关系表：
- 获取所有表/子查询的所有别名，并在aliasToTabs, aliasToSubq中进行适当的映射
- 获取目标的位置并将子句命名为“inclause”+ i
- 创建从聚合树的字符串表示到实际聚合 AST 的映射
- 在destToSelExpr中创建从子句名称到选择表达式AST的映射
- 在 aliasToLateralViews 中创建一个从表别名到横向视图 AST 的映射

```
SELECT COUNT(*) AS num
FROM behavior AS a
WHERE uid LIKE 'a%';
```

```
TOK_QUERY
   TOK_FROM
      TOK_TABREF
         TOK_TABNAME
            behavior
   TOK_INSERT
      TOK_DESTINATION
         TOK_DIR
            TOK_TMP_FILE
      TOK_SELECT
         TOK_SELEXPR
            TOK_FUNCTIONSTAR
               COUNT
            num
      TOK_WHERE
         LIKE
            TOK_TABLE_OR_COL
               uid
            'a%'
```


#### 2.4.1 TOK_SELECT



```java
qb.countSel();
qbp.setSelExprForClause(ctx_1.dest, ast);

int posn = 0;
if (((ASTNode) ast.getChild(0)).getToken().getType() == HiveParser.QUERY_HINT) {
  String queryHintStr = ast.getChild(0).getText();
  ParseDriver pd = new ParseDriver();
  try {
    ASTNode hintNode = pd.parseHint(queryHintStr);
    qbp.setHints(hintNode);
    posn++;
  } catch (ParseException e) {
    throw new SemanticException("failed to parse query hint: "+e.getMessage(), e);
  }
}

if ((ast.getChild(posn).getChild(0).getType() == HiveParser.TOK_TRANSFORM)) {
  queryProperties.setUsesScript(true);
}

LinkedHashMap<String, ASTNode> aggregations = doPhase1GetAggregationsFromSelect(ast, qb, ctx_1.dest);
doPhase1GetColumnAliasesFromSelect(ast, qbp, ctx_1.dest);
qbp.setAggregationExprsForClause(ctx_1.dest, aggregations);
qbp.setDistinctFuncExprsForClause(ctx_1.dest, doPhase1GetDistinctFuncExprs(aggregations));
```




#### 2.4.2 TOK_WHERE

```java
qbp.setWhrExprForClause(ctx_1.dest, ast);
if (!SubQueryUtils.findSubQueries((ASTNode) ast.getChild(0)).isEmpty()) {
  queryProperties.setFilterWithSubQuery(true);
}
```

#### 2.4.3 TOK_INSERT_INTO

```java
String currentDatabase = SessionState.get().getCurrentDatabase();
String tab_name = getUnescapedName((ASTNode) ast.getChild(0).getChild(0), currentDatabase);
qbp.addInsertIntoTable(tab_name, ast);
```

#### 2.4.4 TOK_DESTINATION

```java
ctx_1.dest = this.ctx.getDestNamePrefix(ast, qb).toString() + ctx_1.nextNum;
ctx_1.nextNum++;
boolean isTmpFileDest = false;
if (ast.getChildCount() > 0 && ast.getChild(0) instanceof ASTNode) {
  ASTNode ch = (ASTNode) ast.getChild(0);
  if (ch.getToken().getType() == HiveParser.TOK_DIR && ch.getChildCount() > 0
      && ch.getChild(0) instanceof ASTNode) {
    ch = (ASTNode) ch.getChild(0);
    isTmpFileDest = ch.getToken().getType() == HiveParser.TOK_TMP_FILE;
  } else {
    if (ast.getToken().getType() == HiveParser.TOK_DESTINATION
        && ast.getChild(0).getType() == HiveParser.TOK_TAB) {
      String fullTableName = getUnescapedName((ASTNode) ast.getChild(0).getChild(0),
          SessionState.get().getCurrentDatabase());
      qbp.getInsertOverwriteTables().put(fullTableName.toLowerCase(), ast);
      qbp.setDestToOpType(ctx_1.dest, true);
    }
  }
}

// is there a insert in the subquery
if (qbp.getIsSubQ() && !isTmpFileDest) {
  throw new SemanticException(ErrorMsg.NO_INSERT_INSUBQUERY.getMsg(ast));
}

qbp.setDestForClause(ctx_1.dest, (ASTNode) ast.getChild(0));
handleInsertStatementSpecPhase1(ast, qbp, ctx_1);

if (qbp.getClauseNamesForDest().size() == 2) {
  // From the moment that we have two destination clauses,
  // we know that this is a multi-insert query.
  // Thus, set property to right value.
  // Using qbp.getClauseNamesForDest().size() >= 2 would be
  // equivalent, but we use == to avoid setting the property
  // multiple times
  queryProperties.setMultiDestQuery(true);
}

if (plannerCtx != null && !queryProperties.hasMultiDestQuery()) {
  plannerCtx.setInsertToken(ast, isTmpFileDest);
} else if (plannerCtx != null && qbp.getClauseNamesForDest().size() == 2) {
  // For multi-insert query, currently we only optimize the FROM clause.
  // Hence, introduce multi-insert token on top of it.
  // However, first we need to reset existing token (insert).
  // Using qbp.getClauseNamesForDest().size() >= 2 would be
  // equivalent, but we use == to avoid setting the property
  // multiple times
  plannerCtx.resetToken();
  plannerCtx.setMultiInsertToken((ASTNode) qbp.getQueryFrom().getChild(0));
}
```

#### 2.4.5 TOK_FROM

```java
int child_count = ast.getChildCount();
if (child_count != 1) {
  throw new SemanticException(generateErrorMessage(ast,
      "Multiple Children " + child_count));
}

if (!qbp.getIsSubQ()) {
  qbp.setQueryFromExpr(ast);
}

// Check if this is a subquery / lateral view
ASTNode frm = (ASTNode) ast.getChild(0);
if (frm.getToken().getType() == HiveParser.TOK_TABREF) {
  processTable(qb, frm);
} else if (frm.getToken().getType() == HiveParser.TOK_SUBQUERY) {
  processSubQuery(qb, frm);
} else if (frm.getToken().getType() == HiveParser.TOK_LATERAL_VIEW ||
    frm.getToken().getType() == HiveParser.TOK_LATERAL_VIEW_OUTER) {
  queryProperties.setHasLateralViews(true);
  processLateralView(qb, frm);
} else if (isJoinToken(frm)) {
  processJoin(qb, frm);
  qbp.setJoinExpr(frm);
}else if(frm.getToken().getType() == HiveParser.TOK_PTBLFUNCTION){
  queryProperties.setHasPTF(true);
  processPTF(qb, frm);
}
```

#### 2.4.6 TOK_CLUSTERBY

```java
// Get the clusterby aliases - these are aliased to the entries in the
// select list
queryProperties.setHasClusterBy(true);
qbp.setClusterByExprForClause(ctx_1.dest, ast);
```

#### 2.4.7 TOK_DISTRIBUTEBY

```java
// Get the distribute by aliases - these are aliased to the entries in
// the
// select list
queryProperties.setHasDistributeBy(true);
qbp.setDistributeByExprForClause(ctx_1.dest, ast);
if (qbp.getClusterByForClause(ctx_1.dest) != null) {
  throw new SemanticException(generateErrorMessage(ast,
      ErrorMsg.CLUSTERBY_DISTRIBUTEBY_CONFLICT.getMsg()));
} else if (qbp.getOrderByForClause(ctx_1.dest) != null) {
  throw new SemanticException(generateErrorMessage(ast,
      ErrorMsg.ORDERBY_DISTRIBUTEBY_CONFLICT.getMsg()));
}
```

#### 2.4.8 TOK_SORTBY

```java
// Get the sort by aliases - these are aliased to the entries in the
// select list
queryProperties.setHasSortBy(true);
qbp.setSortByExprForClause(ctx_1.dest, ast);
if (qbp.getClusterByForClause(ctx_1.dest) != null) {
  throw new SemanticException(generateErrorMessage(ast,
      ErrorMsg.CLUSTERBY_SORTBY_CONFLICT.getMsg()));
} else if (qbp.getOrderByForClause(ctx_1.dest) != null) {
  throw new SemanticException(generateErrorMessage(ast,
      ErrorMsg.ORDERBY_SORTBY_CONFLICT.getMsg()));
}
```

#### 2.4.9 TOK_ORDERBY

```java
// Get the order by aliases - these are aliased to the entries in the
// select list
queryProperties.setHasOrderBy(true);
qbp.setOrderByExprForClause(ctx_1.dest, ast);
if (qbp.getClusterByForClause(ctx_1.dest) != null) {
  throw new SemanticException(generateErrorMessage(ast,
      ErrorMsg.CLUSTERBY_ORDERBY_CONFLICT.getMsg()));
}
// If there are aggregations in order by, we need to remember them in qb.
qbp.addAggregationExprsForClause(ctx_1.dest,
    doPhase1GetAggregationsFromSelect(ast, qb, ctx_1.dest));
```

#### 2.4.10 TOK_GROUPBY

- TOK_GROUPBY:
- TOK_ROLLUP_GROUPBY:
- TOK_CUBE_GROUPBY:
- TOK_GROUPING_SETS:

```java
// Get the groupby aliases - these are aliased to the entries in the
// select list
queryProperties.setHasGroupBy(true);
if (qbp.getJoinExpr() != null) {
  queryProperties.setHasJoinFollowedByGroupBy(true);
}
if (qbp.getSelForClause(ctx_1.dest).getToken().getType() == HiveParser.TOK_SELECTDI) {
  throw new SemanticException(generateErrorMessage(ast,
      ErrorMsg.SELECT_DISTINCT_WITH_GROUPBY.getMsg()));
}
qbp.setGroupByExprForClause(ctx_1.dest, ast);
skipRecursion = true;

// Rollup and Cubes are syntactic sugar on top of grouping sets
if (ast.getToken().getType() == HiveParser.TOK_ROLLUP_GROUPBY) {
  qbp.getDestRollups().add(ctx_1.dest);
} else if (ast.getToken().getType() == HiveParser.TOK_CUBE_GROUPBY) {
  qbp.getDestCubes().add(ctx_1.dest);
} else if (ast.getToken().getType() == HiveParser.TOK_GROUPING_SETS) {
  qbp.getDestGroupingSets().add(ctx_1.dest);
}
```

#### 2.4.11 TOK_HAVING

```java
qbp.setHavingExprForClause(ctx_1.dest, ast);
qbp.addAggregationExprsForClause(ctx_1.dest,doPhase1GetAggregationsFromSelect(ast, qb, ctx_1.dest));
```

#### 2.4.12 KW_WINDOW

```java
if (!qb.hasWindowingSpec(ctx_1.dest) ) {
  throw new SemanticException(generateErrorMessage(ast,
      "Query has no Cluster/Distribute By; but has a Window definition"));
}
handleQueryWindowClauses(qb, ctx_1, ast);
```

#### 2.4.13 TOK_LIMIT

```java
if (ast.getChildCount() == 2) {
  qbp.setDestLimit(ctx_1.dest,
      new Integer(ast.getChild(0).getText()),
      new Integer(ast.getChild(1).getText()));
} else {
  qbp.setDestLimit(ctx_1.dest, new Integer(0),
      new Integer(ast.getChild(0).getText()));
}
```

#### 2.4.14 TOK_ANALYZE

```java
// Case of analyze command

String table_name = getUnescapedName((ASTNode) ast.getChild(0).getChild(0)).toLowerCase();


qb.setTabAlias(table_name, table_name);
qb.addAlias(table_name);
qb.getParseInfo().setIsAnalyzeCommand(true);
qb.getParseInfo().setNoScanAnalyzeCommand(this.noscan);
// Allow analyze the whole table and dynamic partitions
HiveConf.setVar(conf, HiveConf.ConfVars.DYNAMICPARTITIONINGMODE, "nonstrict");
HiveConf.setVar(conf, HiveConf.ConfVars.HIVEMAPREDMODE, "nonstrict");
```

#### 2.4.15 TOK_UNIONALL

```java
if (!qbp.getIsSubQ()) {
  // this shouldn't happen. The parser should have converted the union to be
  // contained in a subquery. Just in case, we keep the error as a fallback.
  throw new SemanticException(generateErrorMessage(ast,
      ErrorMsg.UNION_NOTIN_SUBQ.getMsg()));
}
skipRecursion = false;
```

#### 2.4.16 TOK_INSERT

```java
ASTNode destination = (ASTNode) ast.getChild(0);
Tree tab = destination.getChild(0);

// Proceed if AST contains partition & If Not Exists
if (destination.getChildCount() == 2 &&
    tab.getChildCount() == 2 &&
    destination.getChild(1).getType() == HiveParser.TOK_IFNOTEXISTS) {
  String tableName = tab.getChild(0).getChild(0).getText();

  Tree partitions = tab.getChild(1);
  int childCount = partitions.getChildCount();
  HashMap<String, String> partition = new HashMap<String, String>();
  for (int i = 0; i < childCount; i++) {
    String partitionName = partitions.getChild(i).getChild(0).getText();
    // Convert to lowercase for the comparison
    partitionName = partitionName.toLowerCase();
    Tree pvalue = partitions.getChild(i).getChild(1);
    if (pvalue == null) {
      break;
    }
    String partitionVal = stripQuotes(pvalue.getText());
    partition.put(partitionName, partitionVal);
  }
  // if it is a dynamic partition throw the exception
  if (childCount != partition.size()) {
    throw new SemanticException(ErrorMsg.INSERT_INTO_DYNAMICPARTITION_IFNOTEXISTS
        .getMsg(partition.toString()));
  }
  Table table = null;
  try {
    table = this.getTableObjectByName(tableName);
  } catch (HiveException ex) {
    throw new SemanticException(ex);
  }
  try {
    Partition parMetaData = db.getPartition(table, partition, false);
    // Check partition exists if it exists skip the overwrite
    if (parMetaData != null) {
      phase1Result = false;
      skipRecursion = true;
      LOG.info("Partition already exists so insert into overwrite " +
          "skipped for partition : " + parMetaData.toString());
      break;
    }
  } catch (HiveException e) {
    LOG.info("Error while getting metadata : ", e);
  }
  validatePartSpec(table, partition, (ASTNode)tab, conf, false);
}
skipRecursion = false;
```

#### 2.4.17 TOK_LATERAL_VIEW

```java
case HiveParser.TOK_LATERAL_VIEW:
case HiveParser.TOK_LATERAL_VIEW_OUTER:
  // todo: nested LV
  assert ast.getChildCount() == 1;
  qb.getParseInfo().getDestToLateralView().put(ctx_1.dest, ast);
  break;
```

#### 2.4.18 TOK_CTE

```java
processCTE(qb, ast);
```


### 2.5

```java
// 5. Resolve Parse Tree
getMetaData(qb, createVwDesc == null);
LOG.info("Completed getting MetaData in Semantic Analysis");
plannerCtx.setParseTreeAttr(child, ctx_1);
```
