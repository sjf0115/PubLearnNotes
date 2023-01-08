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

在上面 processCmd 方法中，根据不同的命令获取对应不同的命令处理器 CommandProcessor。在这里，processLocalCmd 方法会根据命令处理器 CommandProcessor 的类型来处理 HQL 命令。根据是否是 Driver 命令处理器分成了两种处理逻辑，一类是 Driver 命令处理器，会调用 Driver 的 run 方法来执行命令并在控制台上输出命令的返回结果；另一类是非 Driver 命令处理器，需要调用各自处理器的 run 方法；

先看一下整体框架，可以看到根据命令处理器 CommandProcessor 的不同会拆分成两种处理逻辑。如果处理过程中出现了异常会一直进行重试：
```java
int processLocalCmd(String cmd, CommandProcessor proc, CliSessionState ss) {
    do {
        try {
          needRetry = false;
          if (proc != null) {
              if (proc instanceof Driver) {
                  // CommandProcessor 为 Driver 的处理逻辑
              } else {
                  // CommandProcessor 为非 Driver 的处理逻辑
              }
          }
        } catch (CommandNeedRetryException e) {
            // 出现异常会进行重试
            console.printInfo("Retry query with a different approach...");
            tryCount++;
            needRetry = true;
        }
    } while (needRetry);
    return ret;
}
```

### Driver 命令处理器

如果命令处理器 CommandProcessor 是 Driver，处理逻辑如下所示。整个处理逻辑可以分成两部分：第一部分通过调用 Driver 的 run 方法来实际执行命令，并计算命令运行的耗时；第二部分输出命令计算的结果：
```java
Driver qp = (Driver) proc;
PrintStream out = ss.out;
// 第一部分
long start = System.currentTimeMillis();
// 如果设置了 -v 选项，打印命令
if (ss.getIsVerbose()) {
  out.println(cmd);
}
// 设置重试次数
qp.setTryCount(tryCount);
// 关键点：通过 Driver 的 run 进行命令处理
ret = qp.run(cmd).getResponseCode();
if (ret != 0) {
  qp.close();
  return ret;
}
long end = System.currentTimeMillis();
// 命令运行耗时
double timeTaken = (end - start) / 1000.0;

// 第二部分
ArrayList<String> res = new ArrayList<String>();
printHeader(qp, out);
int counter = 0;
try {
  if (out instanceof FetchConverter) {
    ((FetchConverter)out).fetchStarted();
  }
  // 输出命令计算结果
  while (qp.getResults(res)) {
    for (String r : res) {
      out.println(r);
    }
    counter += res.size();
    res.clear();
    if (out.checkError()) {
      break;
    }
  }
} catch (IOException e) {
  console.printError("Failed with exception " + e.getClass().getName() + ":"
      + e.getMessage(), "\n"
      + org.apache.hadoop.util.StringUtils.stringifyException(e));
  ret = 1;
}
// 关闭 Driver
int cret = qp.close();
if (ret == 0) {
  ret = cret;
}
if (out instanceof FetchConverter) {
  ((FetchConverter)out).fetchFinished();
}
// 在控制台打印耗时以及结果记录条数
console.printInfo("Time taken: " + timeTaken + " seconds" +
    (counter == 0 ? "" : ", Fetched: " + counter + " row(s)"));

```
### 非 Driver 命令处理器

如果命令处理器 CommandProcessor 是非 Driver 处理器，即 SetProcessor、ResetProcessor、DfsProcessor、AddResourceProcessor、ListResourceProcessor、DeleteResourceProcessor、ReloadProcessor、CryptoProcessor 命令处理器，处理逻辑如下所示。
```java
// 命令 cmd 根据 \\s+ 拆分成词条 获取第一个词条
String firstToken = tokenizeCmd(cmd.trim())[0];
String cmd_1 = getFirstCmd(cmd.trim(), firstToken.length());
// 如果设置了 -v 选项，打印命令
if (ss.getIsVerbose()) {
  ss.out.println(firstToken + " " + cmd_1);
}
// 调用各自命令处理器的 run 方法实际处理命令
CommandProcessorResponse res = proc.run(cmd_1);
if (res.getResponseCode() != 0) {
  ss.out.println("Query returned non-zero code: " + res.getResponseCode() +
      ", cause: " + res.getErrorMessage());
}
// 在控制台打印输出信息
if (res.getConsoleMessages() != null) {
  for (String consoleMsg : res.getConsoleMessages()) {
    console.printInfo(consoleMsg);
  }
}
// 执行结果
ret = res.getResponseCode();
```




...
