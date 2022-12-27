## processLine

## processFile

## 2. processCmd

processCmd 方法用来执行 cmd 命令：
```java
public int processCmd(String cmd) {
    CliSessionState ss = (CliSessionState) SessionState.get();
    // 将当前命令作为最后一个命令保存
    ss.setLastCommand(cmd);
    ss.updateThreadName();
    // 刷新打印流 确保不会包含上一个命令的输出
    ss.err.flush();
    String cmd_trimmed = cmd.trim();
    // 将 cmd 命令根据 \\s+ 拆分成不同的 Token
    String[] tokens = tokenizeCmd(cmd_trimmed);
    int ret = 0;
    // 有4种类型场景
    if (cmd_trimmed.toLowerCase().equals("quit") || cmd_trimmed.toLowerCase().equals("exit")) {
        // 处理退出命令
    } else if (tokens[0].equalsIgnoreCase("source")) {
        // 处理 HQL 文件
    } else if (cmd_trimmed.startsWith("!")) {
        // 处理 Shell 命令
    }  else {
        // 处理 HQL 命令
    }
}
```

### 2.1 处理退出命令

命令 cmd 处理的第一种场景是通过 `quit` 或者 `exit` 命令退出 Hive CLI 交互式模式：
```java
if (cmd_trimmed.toLowerCase().equals("quit") || cmd_trimmed.toLowerCase().equals("exit")) {
    // 关闭 SessionState
    ss.close();
    // 正常退出
    System.exit(0);
}
```

### 2.2 处理 HQL 文件

命令 cmd 处理的第二种场景是在 Hive CLI 交互式模式中通过 `source` 命令执行 HQL 文件，例如 `hive > source /opt/data/sql/show_table.sql;`：
```java
if (tokens[0].equalsIgnoreCase("source")) {
    // source 后的文件路径，例如上述命令的 /opt/data/sql/show_table.sql
    String cmd_1 = getFirstCmd(cmd_trimmed, tokens[0].length());
    // 变量替换
    cmd_1 = new VariableSubstitution(new HiveVariableSource() {
      @Override
      public Map<String, String> getHiveVariable() {
        return SessionState.get().getHiveVariables();
      }
    }).substitute(ss.getConf(), cmd_1);
    // 根据路径创建 File 对象
    File sourceFile = new File(cmd_1);
    if (! sourceFile.isFile()){
      // 指定的路径不是一个文件
      console.printError("File: "+ cmd_1 + " is not a file.");
      ret = 1;
    } else {
      try {
        // 处理 HQL 文件
        ret = processFile(cmd_1);
      } catch (IOException e) {
        console.printError("Failed processing file "+ cmd_1 +" "+ e.getLocalizedMessage(),
          stringifyException(e));
        ret = 1;
      }
    }
}
```

### 2.3 处理 Shell 命令

命令 cmd 处理的第三种场景是在 Hive CLI 交互式模式中通过 `!` 命令执行 Shell 命令，例如 `hive > !pwd;`：
```java
if (cmd_trimmed.startsWith("!")) {
    // ! 命令后的 Shell 命令
    String shell_cmd = cmd_trimmed.substring(1);
    // 变量替换
    shell_cmd = new VariableSubstitution(new HiveVariableSource() {
        @Override
        public Map<String, String> getHiveVariable() {
          return SessionState.get().getHiveVariables();
        }
    }).substitute(ss.getConf(), shell_cmd);
    // Shell 命令执行
    try {
        // 通过 ShellCmdExecutor 处理 Shell 命令
        ShellCmdExecutor executor = new ShellCmdExecutor(shell_cmd, ss.out, ss.err);
        ret = executor.execute();
        // 执行失败
        if (ret != 0) {
          console.printError("Command failed with exit code = " + ret);
        }
    } catch (Exception e) {
        console.printError("Exception raised from Shell command " + e.getLocalizedMessage(), stringifyException(e));
        ret = 1;
    }
}
```
### 2.4 处理 HQL 命令

命令 cmd 处理的最后一种场景是在 Hive CLI 交互式模式中执行 HQL 命令，例如 `hive > SHOW TABLES;`：
```java
try {
    // 通过 cmd 获取对应的 CommandProcessor 来处理
    CommandProcessor proc = CommandProcessorFactory.get(tokens, (HiveConf) conf);
    // 通过 processLocalCmd 来真正处理 HQL 命令
    ret = processLocalCmd(cmd, proc, ss);
} catch (SQLException e) {
    console.printError("Failed processing command " + tokens[0] + " " + e.getLocalizedMessage(),
      org.apache.hadoop.util.StringUtils.stringifyException(e));
    ret = 1;
}
```
> 后续会详细介绍 CommandProcessor。

## processLocalCmd





...
