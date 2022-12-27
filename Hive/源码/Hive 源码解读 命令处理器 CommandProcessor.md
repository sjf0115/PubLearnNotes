

## 1. 创建

命令处理器工厂类 CommandProcessorFactory 根据命令拆分的 tokens 和 Hive 配置文件 conf 来获取命令处理器 CommandProcessor：
```java
CommandProcessor proc = CommandProcessorFactory.get(tokens, (HiveConf) conf);
```
> String[] tokens = cmd.split("\\s+");

## 2. get

```java
public static CommandProcessor get(String[] cmd, HiveConf conf) throws SQLException {
  CommandProcessor result = getForHiveCommand(cmd, conf);
  if (result != null) {
    return result;
  }
  if (isBlank(cmd[0])) {
    return null;
  } else {
    if (conf == null) {
      return new Driver();
    }
    Driver drv = mapDrivers.get(conf);
    if (drv == null) {
      drv = new Driver();
      mapDrivers.put(conf, drv);
    } else {
      drv.resetQueryState();
    }
    drv.init();
    return drv;
  }
}
```

## 3. getForHiveCommand

```java
public static CommandProcessor getForHiveCommand(String[] cmd, HiveConf conf) throws SQLException {
  return getForHiveCommandInternal(cmd, conf, false);
}

public static CommandProcessor getForHiveCommandInternal(String[] cmd, HiveConf conf, boolean testOnly) throws SQLException {
    HiveCommand hiveCommand = HiveCommand.find(cmd, testOnly);
    if (hiveCommand == null || isBlank(cmd[0])) {
      return null;
    }
    if (conf == null) {
      conf = new HiveConf();
    }
    Set<String> availableCommands = new HashSet<String>();
    for (String availableCommand : conf.getVar(HiveConf.ConfVars.HIVE_SECURITY_COMMAND_WHITELIST)
      .split(",")) {
      availableCommands.add(availableCommand.toLowerCase().trim());
    }
    if (!availableCommands.contains(cmd[0].trim().toLowerCase())) {
      throw new SQLException("Insufficient privileges to execute " + cmd[0], "42000");
    }
    if (cmd.length > 1 && "reload".equalsIgnoreCase(cmd[0])
      && "function".equalsIgnoreCase(cmd[1])) {
      // special handling for SQL "reload function"
      return null;
    }
    switch (hiveCommand) {
      case SET:
        return new SetProcessor();
      case RESET:
        return new ResetProcessor();
      case DFS:
        SessionState ss = SessionState.get();
        return new DfsProcessor(ss.getConf());
      case ADD:
        return new AddResourceProcessor();
      case LIST:
        return new ListResourceProcessor();
      case DELETE:
        return new DeleteResourceProcessor();
      case COMPILE:
        return new CompileProcessor();
      case RELOAD:
        return new ReloadProcessor();
      case CRYPTO:
        try {
          return new CryptoProcessor(SessionState.get().getHdfsEncryptionShim(), conf);
        } catch (HiveException e) {
          throw new SQLException("Fail to start the command processor due to the exception: ", e);
        }
      default:
        throw new AssertionError("Unknown HiveCommand " + hiveCommand);
    }
}
```

HiveCommand 是一个命令枚举类，通过 find 方法获取命令对应的枚举命令：
```java
public enum HiveCommand {
    SET(),
    RESET(),
    DFS(),
    CRYPTO(true),
    ADD(),
    LIST(),
    RELOAD(),
    DELETE(),
    COMPILE();
    ...
    public static HiveCommand find(String[] command, boolean findOnlyForTesting) {
        if (null == command){
          return null;
        }
        String cmd = command[0];
        if (cmd != null) {
          cmd = cmd.trim().toUpperCase();
          ...
          else if (COMMANDS.contains(cmd)) {
              // 核心在这
              HiveCommand hiveCommand = HiveCommand.valueOf(cmd);
              if (findOnlyForTesting == hiveCommand.isOnlyForTesting()) {
                return hiveCommand;
              }
              return null;
          }
        }
        return null;
    }
}
```
