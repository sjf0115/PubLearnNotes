> Hive 版本：2.3.4

## 1. 主入口 main

在上篇文章介绍 cli.sh 脚本时，我们了解到 CLI 的主入口类为 `org.apache.hadoop.hive.cli.CliDriver`，其中入口即是 main 方法：
```java
public static void main(String[] args) throws Exception {
  int ret = new CliDriver().run(args);
  System.exit(ret);
}
```
在 main 方法中创建了 CliDriver 对象并进行一些初始化：
```java
public CliDriver() {
  // 创建一个 SessionState 内部保存大量配置信息
  SessionState ss = SessionState.get();
  // 配置对象
  conf = (ss != null) ? ss.getConf() : new Configuration();
  // 初始化 Logger
  Logger LOG = LoggerFactory.getLogger("CliDriver");
  if (LOG.isDebugEnabled()) {
    LOG.debug("CliDriver inited with classpath {}", System.getProperty("java.class.path"));
  }
  console = new LogHelper(LOG);
}
```

## 2. 执行入口 run

在 main 方法调用了 CliDriver 的 run 方法。首先构造了一个参数解析器，来解析用户命令行 CLI 选项，Hive CLI 选项具体用法可查阅 [Hive CLI 命令解读](https://smartsi.blog.csdn.net/article/details/128423760)。在第一阶段 CLI 选项解析 process_stage1 中主要解析 hiveconf、define 以及 hivevar 选项定义的自定义变量和属性：
```java
// 参数解析器
OptionsProcessor oproc = new OptionsProcessor();
if (!oproc.process_stage1(args)) {
  return 1;
}
public boolean process_stage1(String[] argv) {
    try {
      // 调用解析器的 parse 方法解析参数
      commandLine = new GnuParser().parse(options, argv);
      // --hiveconf 属性选项
      Properties confProps = commandLine.getOptionProperties("hiveconf");
      for (String propKey : confProps.stringPropertyNames()) {
        if (propKey.equalsIgnoreCase("hive.root.logger")) {
          CommonCliOptions.splitAndSetLogger(propKey, confProps);
        } else {
          System.setProperty(propKey, confProps.getProperty(propKey));
        }
      }
      // --define 自定义变量选项
      Properties hiveVars = commandLine.getOptionProperties("define");
      for (String propKey : hiveVars.stringPropertyNames()) {
        hiveVariables.put(propKey, hiveVars.getProperty(propKey));
      }
      // --hivevar 自定义变量选项
      Properties hiveVars2 = commandLine.getOptionProperties("hivevar");
      for (String propKey : hiveVars2.stringPropertyNames()) {
        hiveVariables.put(propKey, hiveVars2.getProperty(propKey));
      }
    } catch (ParseException e) {
      System.err.println(e.getMessage());
      printUsage();
      return false;
    }
    return true;
}
```
> OptionsProcessor 如何解析 Hive CLI 选项可查阅 [Apache Common CLI 如何实现命令行解析](https://smartsi.blog.csdn.net/article/details/128438785)

然后定义标准化输入输出和错误输出流保存在 CliSessionState 会话对象中：
```java
CliSessionState ss = new CliSessionState(new HiveConf(SessionState.class));
ss.in = System.in;
try {
  ss.out = new PrintStream(System.out, true, "UTF-8");
  ss.info = new PrintStream(System.err, true, "UTF-8");
  ss.err = new CachingPrintStream(System.err, true, "UTF-8");
} catch (UnsupportedEncodingException e) {
  return 3;
}
```
CliSessionState 使用 HiveConf 进行实例化，继承了 SessionState 类，是专门为 Hive CLI 创建的一个会话对象。用来记录 `-database`、`-e`、`-f`、`-hiveconf` 以及 `-i` 选项指定的值。

在第二阶段 CLI 选项解析 process_stage2 中主要解析 `-H`、`-S`、`--database`、`-e`、`-f`、`-v` 以及`-i` 选项：
```java
if (!oproc.process_stage2(ss)) {
  return 2;
}
public boolean process_stage2(CliSessionState ss) {
    ss.getConf();
    // -H 帮助选项
    if (commandLine.hasOption('H')) {
      printUsage();
      return false;
    }
    // -S 静默选项
    ss.setIsSilent(commandLine.hasOption('S'));
    // --database 数据库选项
    ss.database = commandLine.getOptionValue("database");
    // -e 单 HQL 命令执行选项
    ss.execString = commandLine.getOptionValue('e');
    // -f HQL 文件执行选项
    ss.fileName = commandLine.getOptionValue('f');
    // -v 详细选项
    ss.setIsVerbose(commandLine.hasOption('v'));
    // -i 初始化选项
    String[] initFiles = commandLine.getOptionValues('i');
    if (null != initFiles) {
      ss.initFiles = Arrays.asList(initFiles);
    }
    // -e 和 -f 不能同时指定
    if (ss.execString != null && ss.fileName != null) {
      System.err.println("The '-e' and '-f' options cannot be specified simultaneously");
      printUsage();
      return false;
    }
    //
    if (commandLine.hasOption("hiveconf")) {
      Properties confProps = commandLine.getOptionProperties("hiveconf");
      for (String propKey : confProps.stringPropertyNames()) {
        ss.cmdProperties.setProperty(propKey, confProps.getProperty(propKey));
      }
    }
    return true;
}
```
将解析出的选项内容填充 CliSessionState 会话对象。例如，用户输入了 `-e`，就把 `-e` 对应的字符串赋值给 CliSessionState 的 execString 成员。

然后将用户命令行输入的配置信息和变量等覆盖 HiveConf 的默认值：
```java
HiveConf conf = ss.getConf();
for (Map.Entry<Object, Object> item : ss.cmdProperties.entrySet()) {
  conf.set((String) item.getKey(), (String) item.getValue());
  ss.getOverriddenConfigurations().put((String) item.getKey(), (String) item.getValue());
}
```
读取配置提示和替换变量。用户可以在查询中引用变量，Hive 会先使用变量值替换掉查询中的变量引用，然后才会将查询语句提交给查询处理器：
```java
// 提示符
prompt = conf.getVar(HiveConf.ConfVars.CLIPROMPT);
// 变量替换
prompt = new VariableSubstitution(new HiveVariableSource() {
  @Override
  public Map<String, String> getHiveVariable() {
    return SessionState.get().getHiveVariables();
  }
}).substitute(conf, prompt);
prompt2 = spacesForString(prompt);
```
开启会话状态：
```java
if (HiveConf.getBoolVar(conf, ConfVars.HIVE_CLI_TEZ_SESSION_ASYNC)) {
  SessionState.beginStart(ss, console);
} else {
  SessionState.start(ss);
}
```
最重要的的一步就是执行 CLI 驱动程序：
```java
try {
  return executeDriver(ss, conf, oproc);
} finally {
  ss.resetThreadName();
  ss.close();
}
```

## 3. 执行 CLI 驱动

在上面说到最重要的的一步就是执行 CLI 驱动程序方法 executeDriver。下面具体看一下如何执行的。首先从 OptionsProcessor 解析器中获取解析到的 Hive 变量并存储到 SessionState 的 hiveVariables 变量中：
```java
// oproc 为 OptionsProcessor
cli.setHiveVariables(oproc.getHiveVariables());
// 存储到 SessionState 的 hiveVariables 变量中
public void setHiveVariables(Map<String, String> hiveVariables) {
  SessionState.get().setHiveVariables(hiveVariables);
}
```
如果 Hive CLI 命令行中指定了 `--database` 选项，需要使用指定的数据库，即执行 `use <database>;` HQL 语句：
```java
cli.processSelectDatabase(ss);
// 执行切换数据库HQL语句
public void processSelectDatabase(CliSessionState ss) throws IOException {
  String database = ss.database;
  if (database != null) {
    int rc = processLine("use " + database + ";");
    if (rc != 0) {
      System.exit(rc);
    }
  }
}
```
如果 Hive CLI 命令行中指定了 `-e '<quoted-query-string>'` 选项，需要调用 processLine 来执行 HQL 语句：
```java
if (ss.execString != null) {
  int cmdProcessStatus = cli.processLine(ss.execString);
  return cmdProcessStatus;
}
```
> processLine 如何处理 HQL 语句后续会详细介绍

如果 Hive CLI 命令行中指定了 `-f <query-file>` 选项，需要调用 processFile 来执行文件中的一个或者多个 HQL 语句：
```java
try {
  if (ss.fileName != null) {
    return cli.processFile(ss.fileName);
  }
} catch (FileNotFoundException e) {
  System.err.println("Could not open input file for reading. (" + e.getMessage() + ")");
  return 3;
}
```
> processFile 如何处理文件中的一个或者多个 HQL 语句后续会详细介绍

如果 Hive 的执行引擎选择的是 mr 会打印警告信息 `Hive-on-MR is deprecated in Hive 2 and may not be available in the future versions. Consider using a different execution engine (i.e. spark, tez) or using Hive 1.X releases.`，提示你要切换到 Spark 或者 Tez 执行引擎上：
```java
if ("mr".equals(HiveConf.getVar(conf, ConfVars.HIVE_EXECUTION_ENGINE))) {
  console.printInfo(HiveConf.generateMrDeprecationWarning());
}
```
最后最重要的是从标准化输入中解析出一个个完整 HQL 语句交由 processLine 来执行：
```java
String line;
int ret = 0;
String prefix = "";
String curDB = getFormattedDb(conf, ss);
String curPrompt = prompt + curDB;
String dbSpaces = spacesForString(curDB);

while ((line = reader.readLine(curPrompt + "> ")) != null) {
  // 换行
  if (!prefix.equals("")) {
    prefix += '\n';
  }
  // 遇到注释跳过
  if (line.trim().startsWith("--")) {
    continue;
  }
  // 直到遇到分号结尾 表示一个完整 HQL 语句
  if (line.trim().endsWith(";") && !line.trim().endsWith("\\;")) {
    line = prefix + line;
    // HQL 语句的执行实际上交由 processLine 处理
    ret = cli.processLine(line, true);
    prefix = "";
    curDB = getFormattedDb(conf, ss);
    curPrompt = prompt + curDB;
    dbSpaces = dbSpaces.length() == curDB.length() ? dbSpaces : spacesForString(curDB);
  } else {
    prefix = prefix + line;
    curPrompt = prompt2 + dbSpaces;
    continue;
  }
}
```
