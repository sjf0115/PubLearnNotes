
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
