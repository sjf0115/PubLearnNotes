> Hive 版本：2.3.4

## 1. HQL 文件拆分

### 1.1 入口

从上一篇文章 [Hive 源码解读 CliDriver HQL 读取与参数解析](https://smartsi.blog.csdn.net/article/details/128462596) 中了解到，如果 Hive CLI 命令行中指定了 `-f <query-file>` 选项，需要调用 processFile 来执行文件中的一个或者多个 HQL 语句：
```java
try {
  if (ss.fileName != null) {
    return cli.processFile(ss.fileName);
  }
} catch (FileNotFoundException e) {
  ...
}
```
除了 `-f <query-file>` 选项需要调用 processFile 处理 HQL 文件之外，`-i <filename>` 选项也需要：
```java
public void processInitFiles(CliSessionState ss) throws IOException {
    ...
    // 调用 processFile 处理初始文件
    for (String initFile : ss.initFiles) {
      int rc = processFile(initFile);
      ...
    }
    ...
}
```

### 1.2 文件处理 processFile

现在具体看一下 Hive 是如何通过 `processFile` 处理一个 HQL 文件中的语句。`processFile` 函数根据输入的文件路径名读取文件，实际处理逻辑交由 `processReader` 函数处理：
```java
public int processFile(String fileName) throws IOException {
    Path path = new Path(fileName);
    FileSystem fs;
    // 绝对路径
    if (!path.toUri().isAbsolute()) {
      fs = FileSystem.getLocal(conf);
      path = fs.makeQualified(path);
    } else {
      fs = FileSystem.get(path.toUri(), conf);
    }
    BufferedReader bufferReader = null;
    int rc = 0;
    try {
      bufferReader = new BufferedReader(new InputStreamReader(fs.open(path)));
      rc = processReader(bufferReader);
    } finally {
      IOUtils.closeStream(bufferReader);
    }
    return rc;
}
```
我们可以看到 processReader 处理逻辑比较简单，只是去掉注释行，其他的调用 `processLine` 方法处理：
```java
public int processReader(BufferedReader r) throws IOException {
    String line;
    StringBuilder qsb = new StringBuilder();
    // 一行一行的处理
    while ((line = r.readLine()) != null) {
      // 跳过注释
      if (! line.startsWith("--")) {
        qsb.append(line + "\n");
      }
    }
    return (processLine(qsb.toString()));
}
```

## 2. HQL 语句拆分

### 2.1 入口

除了上述 `processFile` 最终会调用 `processLine` 处理之外，`hive -e <query-string>` 执行查询字符串时也会调用：
> CliDriver#executeDriver
```java
if (ss.execString != null) {
    int cmdProcessStatus = cli.processLine(ss.execString);
    return cmdProcessStatus;
}
```
除此之外，在交互式模式下从标准化输入中解析出 HQL 语句也会交由 `processLine` 来执行：
> CliDriver#executeDriver
```java
while ((line = reader.readLine(curPrompt + "> ")) != null) {
  ...
  // 直到遇到分号结尾才确定一个一条 HQL 语句的终结
  if (line.trim().endsWith(";") && !line.trim().endsWith("\\;")) {
    line = prefix + line;
    // HQL 语句的执行实际上交由 processLine 处理
    ret = cli.processLine(line, true);
    ...
  } else {
    ...
  }
}
```

### 2.2 行处理 processLine

现在具体看一下 Hive 是如何通过 `processLine` 处理一个 HQL 语句。

首先第一部分的逻辑是对中断信号的处理。当调用的是 `processLine(line, true)` 方法时，表示当前作业可以被允许打断。当第一次用户输入 Ctrl+C 时，在交互式界面中输出 `Interrupting... Be patient, this might take some time.` 表示正在中断中，CLI 线程会中断并杀死正在进行的 MR 作业。当第一次用户输入 Ctrl+C 时，则会退出 JVM：
```java
SignalHandler oldSignal = null;
Signal interruptSignal = null;
if (allowInterrupting) {
  interruptSignal = new Signal("INT");
  oldSignal = Signal.handle(interruptSignal, new SignalHandler() {
    private boolean interruptRequested;
    @Override
    public void handle(Signal signal) {
      boolean initialRequest = !interruptRequested;
      interruptRequested = true;
      if (!initialRequest) {
        // 第二次 ctrl+c 退出 JVM
        console.printInfo("Exiting the JVM");
        System.exit(127);
      }
      // 第一次 Ctrl+C 中断 CLI 线程、停止当前语句并杀死正在进行的 MR 作业
      console.printInfo("Interrupting... Be patient, this might take some time.");
      console.printInfo("Press Ctrl+C again to kill JVM");
      HadoopJobExecHelper.killRunningJobs();
      TezJobExecHelper.killRunningJobs();
      HiveInterruptUtils.interrupt();
    }
  });
}
```

第二部分逻辑是对 HQL 语句进行拆分：
```java
// 拆分为不同的 HQL 命令
List<String> commands = splitSemiColon(line);
String command = "";
for (String oneCmd : commands) {
  if (StringUtils.endsWith(oneCmd, "\\")) {
    command += StringUtils.chop(oneCmd) + ";";
    continue;
  } else {
    command += oneCmd;
  }
  if (StringUtils.isBlank(command)) {
    continue;
  }
  // 交由 processCmd 处理命令
  ret = processCmd(command);
  command = "";
  lastRet = ret;
  boolean ignoreErrors = HiveConf.getBoolVar(conf, HiveConf.ConfVars.CLIIGNOREERRORS);
  if (ret != 0 && !ignoreErrors) {
    CommandProcessorFactory.clean((HiveConf) conf);
    return ret;
  }
}
```
上游处理时只是针对每行末尾是分号 `;` 时才调用 `processLine` 进行处理，所以一行中可能存在多条 HQL 命令，如下所示一行中就存在两条 HQL 命令：
```sql
hive > USE default;SELECT concat(uid, ";") FROM behavior LIMIT 1;
```
首先第一步就是将 HQL 语句拆分为不同的 HQL 命令，需要注意的是不能使用 `split` 函数直接根据 `;` 进行拆分，因为 HQL 语句中可能存在 `;`，例如上述语句中的第二个命令，所以需要单独调用 `splitSemiColon` 方法进行处理。最后将拆分后的 HQL 命令交由 `processCmd` 方法执行。
