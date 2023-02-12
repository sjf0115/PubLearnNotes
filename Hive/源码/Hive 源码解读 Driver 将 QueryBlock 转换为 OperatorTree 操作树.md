
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

### 2.3

```java
// 3. Deduce Resultset Schema
if (createVwDesc != null && !this.ctx.isCboSucceeded()) {
  resultSchema = convertRowSchemaToViewSchema(opParseCtx.get(sinkOp).getRowResolver());
} else {
  // resultSchema will be null if
  // (1) cbo is disabled;
  // (2) or cbo is enabled with AST return path (whether succeeded or not,
  // resultSchema will be re-initialized)
  // It will only be not null if cbo is enabled with new return path and it
  // succeeds.
  if (resultSchema == null) {
    resultSchema = convertRowSchemaToResultSetSchema(opParseCtx.get(sinkOp).getRowResolver(),
        HiveConf.getBoolVar(conf, HiveConf.ConfVars.HIVE_RESULTSET_USE_UNIQUE_COLUMN_NAMES));
  }
}
```

### 2.4

```java
// 4. Generate Parse Context for Optimizer & Physical compiler
copyInfoToQueryProperties(queryProperties);
ParseContext pCtx = new ParseContext(queryState, opToPartPruner, opToPartList, topOps,
    new HashSet<JoinOperator>(joinContext.keySet()),
    new HashSet<SMBMapJoinOperator>(smbMapJoinContext.keySet()),
    loadTableWork, loadFileWork, columnStatsAutoGatherContexts, ctx, idToTableNameMap, destTableId, uCtx,
    listMapJoinOpsNoReducer, prunedPartitions, tabNameToTabObject, opToSamplePruner,
    globalLimitCtx, nameToSplitSample, inputs, rootTasks, opToPartToSkewedPruner,
    viewAliasToInput, reduceSinkOperatorsAddedByEnforceBucketingSorting,
    analyzeRewrite, tableDesc, createVwDesc, materializedViewUpdateDesc,
    queryProperties, viewProjectToTableSchema, acidFileSinks);

// Set the semijoin hints in parse context
pCtx.setSemiJoinHints(parseSemiJoinHint(getQB().getParseInfo().getHintList()));
// Set the mapjoin hint if it needs to be disabled.
pCtx.setDisableMapJoin(disableMapJoinWithHint(getQB().getParseInfo().getHintList()));
```

### 2.5

```java
// 5. Take care of view creation
if (createVwDesc != null) {
  if (ctx.getExplainAnalyze() == AnalyzeState.RUNNING) {
    return;
  }

  if (!ctx.isCboSucceeded()) {
    saveViewDefinition();
  }

  // validate the create view statement at this point, the createVwDesc gets
  // all the information for semanticcheck
  validateCreateView();

  if (createVwDesc.isMaterialized()) {
    createVwDesc.setTablesUsed(getTablesUsed(pCtx));
  } else {
    // Since we're only creating a view (not executing it), we don't need to
    // optimize or translate the plan (and in fact, those procedures can
    // interfere with the view creation). So skip the rest of this method.
    ctx.setResDir(null);
    ctx.setResFile(null);

    try {
      PlanUtils.addInputsForView(pCtx);
    } catch (HiveException e) {
      throw new SemanticException(e);
    }

    // Generate lineage info for create view statements
    // if LineageLogger hook is configured.
    // Add the transformation that computes the lineage information.
    Set<String> postExecHooks = Sets.newHashSet(Splitter.on(",").trimResults()
        .omitEmptyStrings()
        .split(Strings.nullToEmpty(HiveConf.getVar(conf, HiveConf.ConfVars.POSTEXECHOOKS))));
    if (postExecHooks.contains("org.apache.hadoop.hive.ql.hooks.PostExecutePrinter")
        || postExecHooks.contains("org.apache.hadoop.hive.ql.hooks.LineageLogger")
        || postExecHooks.contains("org.apache.atlas.hive.hook.HiveHook")) {
      ArrayList<Transform> transformations = new ArrayList<Transform>();
      transformations.add(new HiveOpConverterPostProc());
      transformations.add(new Generator(postExecHooks));
      for (Transform t : transformations) {
        pCtx = t.transform(pCtx);
      }
      // we just use view name as location.
      queryState.getLineageState()
          .mapDirToOp(new Path(createVwDesc.getViewName()), sinkOp);
    }
    return;
  }
}
```

### 2.6

```java
// 6. Generate table access stats if required
if (HiveConf.getBoolVar(this.conf, HiveConf.ConfVars.HIVE_STATS_COLLECT_TABLEKEYS)) {
  TableAccessAnalyzer tableAccessAnalyzer = new TableAccessAnalyzer(pCtx);
  setTableAccessInfo(tableAccessAnalyzer.analyzeTableAccess());
}
```

### 2.7

```java
// 7. Perform Logical optimization
if (LOG.isDebugEnabled()) {
  LOG.debug("Before logical optimization\n" + Operator.toString(pCtx.getTopOps().values()));
}
Optimizer optm = new Optimizer();
optm.setPctx(pCtx);
optm.initialize(conf);
pCtx = optm.optimize();
if (pCtx.getColumnAccessInfo() != null) {
  // set ColumnAccessInfo for view column authorization
  setColumnAccessInfo(pCtx.getColumnAccessInfo());
}
if (LOG.isDebugEnabled()) {
  LOG.debug("After logical optimization\n" + Operator.toString(pCtx.getTopOps().values()));
}
```

### 2.8

```java
// 8. Generate column access stats if required - wait until column pruning
// takes place during optimization
boolean isColumnInfoNeedForAuth = SessionState.get().isAuthorizationModeV2()
    && HiveConf.getBoolVar(conf, HiveConf.ConfVars.HIVE_AUTHORIZATION_ENABLED);
if (isColumnInfoNeedForAuth
    || HiveConf.getBoolVar(this.conf, HiveConf.ConfVars.HIVE_STATS_COLLECT_SCANCOLS)) {
  ColumnAccessAnalyzer columnAccessAnalyzer = new ColumnAccessAnalyzer(pCtx);
  // view column access info is carried by this.getColumnAccessInfo().
  setColumnAccessInfo(columnAccessAnalyzer.analyzeColumnAccess(this.getColumnAccessInfo()));
}
```

### 2.9

```java
// 9. Optimize Physical op tree & Translate to target execution engine (MR,
// TEZ..)
if (!ctx.getExplainLogical()) {
  TaskCompiler compiler = TaskCompilerFactory.getCompiler(conf, pCtx);
  compiler.init(queryState, console, db);
  compiler.compile(pCtx, rootTasks, inputs, outputs);
  fetchTask = pCtx.getFetchTask();
}
//find all Acid FileSinkOperatorS
QueryPlanPostProcessor qp = new QueryPlanPostProcessor(rootTasks, acidFileSinks, ctx.getExecutionId());
```

### 2.10

```java
// 10. Attach CTAS/Insert-Commit-hooks for Storage Handlers
final Optional<TezTask> optionalTezTask =
    rootTasks.stream().filter(task -> task instanceof TezTask).map(task -> (TezTask) task)
        .findFirst();
if (optionalTezTask.isPresent()) {
  final TezTask tezTask = optionalTezTask.get();
  rootTasks.stream()
      .filter(task -> task.getWork() instanceof DDLWork)
      .map(task -> (DDLWork) task.getWork())
      .filter(ddlWork -> ddlWork.getPreInsertTableDesc() != null)
      .map(ddlWork -> ddlWork.getPreInsertTableDesc())
      .map(ddlPreInsertTask -> new InsertCommitHookDesc(ddlPreInsertTask.getTable(),
          ddlPreInsertTask.isOverwrite()))
      .forEach(insertCommitHookDesc -> tezTask.addDependentTask(
          TaskFactory.get(new DDLWork(getInputs(), getOutputs(), insertCommitHookDesc), conf)));
}
```
### 2.11

```java
// 11. put accessed columns to readEntity
if (HiveConf.getBoolVar(this.conf, HiveConf.ConfVars.HIVE_STATS_COLLECT_SCANCOLS)) {
  putAccessedColumnsToReadEntity(inputs, columnAccessInfo);
}

if (isCacheEnabled && lookupInfo != null) {
  if (queryCanBeCached()) {
    QueryResultsCache.QueryInfo queryInfo = createCacheQueryInfoForQuery(lookupInfo);

    // Specify that the results of this query can be cached.
    setCacheUsage(new CacheUsage(
        CacheUsage.CacheStatus.CAN_CACHE_QUERY_RESULTS, queryInfo));
  }
}
```
