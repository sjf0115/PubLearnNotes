
## 1. 执行

```java
HiveDriverRunHookContext hookContext = new HiveDriverRunHookContextImpl(conf, alreadyCompiled ? ctx.getCmd() : command);
List<HiveDriverRunHook> driverRunHooks;
try {
    // 获取全部的 driverRunHook
    driverRunHooks = getHooks(HiveConf.ConfVars.HIVE_DRIVER_RUN_HOOKS, HiveDriverRunHook.class);
    for (HiveDriverRunHook driverRunHook : driverRunHooks) {
        // 执行 hook 的 preDriverRun 方法
        driverRunHook.preDriverRun(hookContext);
    }
} catch (Exception e) {
    ...
}

...

try {
    for (HiveDriverRunHook driverRunHook : driverRunHooks) {
        // 执行 hook 的 postDriverRun 方法
        driverRunHook.postDriverRun(hookContext);
    }
} catch (Exception e) {
    ...
}
```

## 2. 获取 Hook

根据配置变量 hookConfVar 返回指定的 Hook 列表：
```java
private <T extends Hook> List<T> getHooks(ConfVars hookConfVar, Class<T> clazz) throws Exception {
    try {
      return HookUtils.getHooks(conf, hookConfVar, clazz);
    } catch (ClassNotFoundException e) {
      console.printError(hookConfVar.varname + " Class not found:" + e.getMessage());
      throw e;
    }
}
```

```java
public static <T extends Hook> List<T> getHooks(HiveConf conf, ConfVars hookConfVar, Class<T> clazz) throws InstantiationException, IllegalAccessException, ClassNotFoundException  {
    String csHooks = conf.getVar(hookConfVar);
    List<T> hooks = new ArrayList<T>();
    if (csHooks == null) {
      return hooks;
    }
    csHooks = csHooks.trim();
    if (csHooks.equals("")) {
      return hooks;
    }
    String[] hookClasses = csHooks.split(",");
    for (String hookClass : hookClasses) {
        // 通过反射获取 Hook 类
        T hook = (T) Class.forName(hookClass.trim(), true, Utilities.getSessionSpecifiedClassLoader())
              .newInstance();
        hooks.add(hook);
    }
    return hooks;
}
```

## 3. 执行时机

### 3.1 Driver 执行 Hook



### 3.2 生命周期 Hook

> 位置：org.apache.hadoop.hive.ql.Driver#compile

```java
// 获取所有生命周期 Hook
queryHooks = loadQueryHooks();

if (queryHooks != null && !queryHooks.isEmpty()) {
    // 设置生命周期 Hook 上下文
    QueryLifeTimeHookContext qhc = new QueryLifeTimeHookContextImpl();
    qhc.setHiveConf(conf);
    qhc.setCommand(command);
    // 在编译之前
    for (QueryLifeTimeHook hook : queryHooks) {
      hook.beforeCompile(qhc);
    }
}

...

if (queryHooks != null && !queryHooks.isEmpty()) {
    // 设置生命周期 Hook 上下文
    QueryLifeTimeHookContext qhc = new QueryLifeTimeHookContextImpl();
    qhc.setHiveConf(conf);
    qhc.setCommand(command);
    // 在编译之后
    for (QueryLifeTimeHook hook : queryHooks) {
      hook.afterCompile(qhc, compileError);
    }
}
```
单独构建 loadQueryHooks 的目的就是额外添加了一个 HiveServer2 指标 Hook：
```java
private List<QueryLifeTimeHook> loadQueryHooks() throws Exception {
    List<QueryLifeTimeHook> hooks = new ArrayList<>();
    if (conf.getBoolVar(ConfVars.HIVE_SERVER2_METRICS_ENABLED)) {
      hooks.add(new MetricsQueryLifeTimeHook());
    }
    List<QueryLifeTimeHook> propertyDefinedHoooks = getHooks(ConfVars.HIVE_QUERY_LIFETIME_HOOKS, QueryLifeTimeHook.class);
    if (propertyDefinedHoooks != null) {
      Iterables.addAll(hooks, propertyDefinedHoooks);
    }
    return hooks;
}
```


### 3.2 语义分析 Hook

> 位置：org.apache.hadoop.hive.ql.Driver#compile

```java
// 获取所有语义分析 Hook
List<HiveSemanticAnalyzerHook> saHooks = getHooks(
    HiveConf.ConfVars.SEMANTIC_ANALYZER_HOOK, HiveSemanticAnalyzerHook.class
);
// 设置语义分析 Hook 上下文
HiveSemanticAnalyzerHookContext hookCtx = new HiveSemanticAnalyzerHookContextImpl();
hookCtx.setConf(conf);
hookCtx.setUserName(userName);
hookCtx.setIpAddress(SessionState.get().getUserIpAddress());
hookCtx.setCommand(command);
hookCtx.setHiveOperation(queryState.getHiveOperation());
// 语义分析之前
for (HiveSemanticAnalyzerHook hook : saHooks) {
  tree = hook.preAnalyze(hookCtx, tree);
}
sem.analyze(tree, ctx);
hookCtx.update(sem);
// 语义分析之后
for (HiveSemanticAnalyzerHook hook : saHooks) {
  hook.postAnalyze(hookCtx, sem.getAllRootTasks());
}
```

## 4. HookRunner

```java
hookRunner.runBeforeParseHook(command);
...
// 解析逻辑
...
hookRunner.runAfterParseHook(command, parseError);
...

hookRunner.runBeforeCompileHook(command);
boolean executeHooks = hookRunner.hasPreAnalyzeHooks();
HiveSemanticAnalyzerHookContext hookCtx = new HiveSemanticAnalyzerHookContextImpl();
if (executeHooks) {
  ...
  tree =  hookRunner.runPreAnalyzeHooks(hookCtx, tree);
}
...
// 语义分析逻辑
...
if (executeHooks) {
  hookRunner.runPostAnalyzeHooks(hookCtx, sem.getAllRootTasks());
}
...

hookRunner.runAfterCompilationHook(command, compileError);

```



https://blog.csdn.net/houzhizhen/article/details/121036390


。。。。
