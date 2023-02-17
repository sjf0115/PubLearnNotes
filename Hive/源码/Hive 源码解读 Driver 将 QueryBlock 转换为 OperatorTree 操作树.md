
### 2.2 生成 Operator 树

```java
// 核心点 生成 Operator 树
Operator sinkOp = genOPTree(ast, plannerCtx);

boolean usesMasking = false;
if (!unparseTranslator.isEnabled() &&
    (tableMask.isEnabled() && analyzeRewrite == null)) {
  // Here we rewrite the * and also the masking table
  ASTNode rewrittenAST = rewriteASTWithMaskAndFilter(tableMask, astForMasking, ctx.getTokenRewriteStream(),
      ctx, db, tabNameToTabObject, ignoredTokens);
  if (astForMasking != rewrittenAST) {
    usesMasking = true;
    plannerCtx = pcf.create();
    ctx.setSkipTableMasking(true);
    init(true);
    //change the location of position alias process here
    processPositionAlias(rewrittenAST);
    genResolvedParseTree(rewrittenAST, plannerCtx);
    if (this instanceof CalcitePlanner) {
      ((CalcitePlanner) this).resetCalciteConfiguration();
    }
    sinkOp = genOPTree(rewrittenAST, plannerCtx);
  }
}

// Check query results cache
// In the case that row or column masking/filtering was required, we do not support caching.
// TODO: Enable caching for queries with masking/filtering
if (isCacheEnabled && needsTransform && !usesMasking && queryTypeCanUseCache()) {
  lookupInfo = createLookupInfoForQuery(ast);
  if (checkResultsCache(lookupInfo)) {
    return;
  }
}
```

```java
Operator genOPTree(ASTNode ast, PlannerContext plannerCtx) throws SemanticException {
  return genPlan(qb);
}

public Operator genPlan(QB qb) throws SemanticException {
  return genPlan(qb, false);
}
```

```java
public Operator genPlan(QB qb, boolean skipAmbiguityCheck) throws SemanticException {
  Map<String, Operator> aliasToOpInfo = new LinkedHashMap<String, Operator>();

  // Recurse over the subqueries to fill the subquery part of the plan
  for (String alias : qb.getSubqAliases()) {
    QBExpr qbexpr = qb.getSubqForAlias(alias);
    // 递归
    Operator operator = genPlan(qb, qbexpr);
    aliasToOpInfo.put(alias, operator);
    if (qb.getViewToTabSchema().containsKey(alias)) {
      // we set viewProjectToTableSchema so that we can leverage ColumnPruner.
      if (operator instanceof SelectOperator) {
        if (this.viewProjectToTableSchema == null) {
          this.viewProjectToTableSchema = new LinkedHashMap<>();
        }
        viewProjectToTableSchema.put((SelectOperator) operator, qb.getViewToTabSchema()
            .get(alias));
      } else {
        throw new SemanticException("View " + alias + " is corresponding to "
            + operator.getType().name() + ", rather than a SelectOperator.");
      }
    }
  }

  // Recurse over all the source tables
  for (String alias : qb.getTabAliases()) {
    Operator op = genTablePlan(alias, qb);
    aliasToOpInfo.put(alias, op);
  }

  if (aliasToOpInfo.isEmpty()) {
    qb.getMetaData().setSrcForAlias(DUMMY_TABLE, getDummyTable());
    TableScanOperator op = (TableScanOperator) genTablePlan(DUMMY_TABLE, qb);
    op.getConf().setRowLimit(1);
    qb.addAlias(DUMMY_TABLE);
    qb.setTabAlias(DUMMY_TABLE, DUMMY_TABLE);
    aliasToOpInfo.put(DUMMY_TABLE, op);
  }

  Operator srcOpInfo = null;
  Operator lastPTFOp = null;

  if(queryProperties.hasPTF()){
    HashMap<ASTNode, PTFInvocationSpec> ptfNodeToSpec = qb.getPTFNodeToSpec();
    if ( ptfNodeToSpec != null ) {
      for(Entry<ASTNode, PTFInvocationSpec> entry : ptfNodeToSpec.entrySet()) {
        ASTNode ast = entry.getKey();
        PTFInvocationSpec spec = entry.getValue();
        String inputAlias = spec.getQueryInputName();
        Operator inOp = aliasToOpInfo.get(inputAlias);
        if ( inOp == null ) {
          throw new SemanticException(generateErrorMessage(ast,
              "Cannot resolve input Operator for PTF invocation"));
        }
        lastPTFOp = genPTFPlan(spec, inOp);
        String ptfAlias = spec.getFunction().getAlias();
        if ( ptfAlias != null ) {
          aliasToOpInfo.put(ptfAlias, lastPTFOp);
        }
      }
    }

  }

  // For all the source tables that have a lateral view, attach the
  // appropriate operators to the TS
  genLateralViewPlans(aliasToOpInfo, qb);

  // process join
  if (qb.getParseInfo().getJoinExpr() != null) {
    ASTNode joinExpr = qb.getParseInfo().getJoinExpr();

    if (joinExpr.getToken().getType() == HiveParser.TOK_UNIQUEJOIN) {
      QBJoinTree joinTree = genUniqueJoinTree(qb, joinExpr, aliasToOpInfo);
      qb.setQbJoinTree(joinTree);
    } else {
      QBJoinTree joinTree = genJoinTree(qb, joinExpr, aliasToOpInfo);
      qb.setQbJoinTree(joinTree);
      /*
       * if there is only one destination in Query try to push where predicates
       * as Join conditions
       */
      Set<String> dests = qb.getParseInfo().getClauseNames();
      if ( dests.size() == 1 && joinTree.getNoOuterJoin()) {
        String dest = dests.iterator().next();
        ASTNode whereClause = qb.getParseInfo().getWhrForClause(dest);
        if ( whereClause != null ) {
          extractJoinCondsFromWhereClause(joinTree, qb, dest,
              (ASTNode) whereClause.getChild(0),
              aliasToOpInfo );
        }
      }

      if (!disableJoinMerge) {
        mergeJoinTree(qb);
      }
    }

    // if any filters are present in the join tree, push them on top of the
    // table
    pushJoinFilters(qb, qb.getQbJoinTree(), aliasToOpInfo);
    srcOpInfo = genJoinPlan(qb, aliasToOpInfo);
  } else {
    // Now if there are more than 1 sources then we have a join case
    // later we can extend this to the union all case as well
    srcOpInfo = aliasToOpInfo.values().iterator().next();
    // with ptfs, there maybe more (note for PTFChains:
    // 1 ptf invocation may entail multiple PTF operators)
    srcOpInfo = lastPTFOp != null ? lastPTFOp : srcOpInfo;
  }

  Operator bodyOpInfo = genBodyPlan(qb, srcOpInfo, aliasToOpInfo);

  if (LOG.isDebugEnabled()) {
    LOG.debug("Created Plan for Query Block " + qb.getId());
  }

  if (qb.getAlias() != null) {
    rewriteRRForSubQ(qb.getAlias(), bodyOpInfo, skipAmbiguityCheck);
  }

  setQB(qb);
  return bodyOpInfo;
}
```
