
## 1. 简介

Apache Commons CLI 提供了一个解析传递给程序的命令行选项的 API 类库。此外它还能够打印帮助消息，详细说明命令行工具的可用选项。

Commons CLI支持不同类型的选项:
- POSIX 类选项，例如 `tar -zxvf foo.tar.gz`
- GNU 类长选项，例如 `du --human-readable --max-depth=1`
- Java 类属性，例如 `java -Djava.awt.headless=true -Djava.net.useSystemProxies=true Foo`
- 带有参数值的短选项，例如 `gcc -O2 foo.c`
- 带有单个连字符的长选项，例如 `ant -projecthelp`

> 短选项（Short Options）：短选项用一个单独的字母作为标志，通常也是一个选项英语的缩写。例如：`-f` 表示文件（file）。多个短选项可以连写，如 `ls -a -l`，可以写成`ls -al`；
> 长选项（Long Options）：单独字母的数量毕竟有限，会不够用，而且表达的意思不够明确，于是就有了长选项 `--`，后面可以跟一串单词，如 `--version`。

## 2. 命令行处理阶段

命令行处理有三个阶段，分别是定义阶段、解析阶段和交互阶段。下面依次讨论这几个阶段，并讨论如何用 CLI（Apache Common CLI） 实现。

### 2.1 定义阶段

每一个命令行都必须定义一组参数，来定义应用程序的接口。CLI 使用 Options 类来定义和设置参数，是所有 Option 实例的容器。目前有两种方式创建 Option，一种是通过构造函数，这是最普通也是最为大家所熟知的一种方式：
```java
Options options = new Options();
// -H 或者 --help
options.addOption(new Option("H", "help", false, "Print help information"));
```
Option 对象有4个参数，分别为短选项、长选项、是否需要额外参数以及描述信息。我们也可以 `options.addOption("H", "help", false, "Print help information")` 来执行。

另外一种方式是通过 Options 中定义的工厂方式来实现：
```java
Options options = new Options();
// -d 或者 --define
options.addOption(OptionBuilder
    .withValueSeparator()
    .hasArgs(2)
    .withArgName("key=value")
    .withLongOpt("define")
    .withDescription("Variable substitution to apply to Hive commands. e.g. -d A=B or --define A=B")
    .create('d'));
```

> 定义阶段的目的就是创建一个 Options 实例以及各种 Option。

### 2.2 解析阶段

在解析阶段中，对通过命令行传入应用程序的文本进行处理。CLI 通过 CommandLineParser 的 parse 方法解析命令行参数，用定义阶段产生的 Options 实例和 `String[]` 中的参数作为输入，并返回解析后生成的 CommandLine 对象。

CommandLineParser 有多种实现类，例如 BasicParser、GnuParser、PosixParser、DefaultParser。从 1.3 版本开始推荐使用 DefaultParser，因为除了 DefaultParser，其他的都被打上了 `@Deprecated` 标记：
```java
// 老版本
// CommandLineParser parser = new GnuParser();
CommandLineParser parser = new DefaultParser();
CommandLine commandLine = parser.parse(options, args);
```

> 解析阶段的目的就是创建一个 CommandLine 实例。

### 2.3 查询阶段

在查询阶段中，应用程序通过查询 CommandLine，并通过其中的布尔参数和提供给应用程序的参数值来决定需要执行哪个程序分支。这个阶段在用户的代码中实现，CommandLine 中的访问方法为用户代码提供了 CLI 的交互能力。如下所示，我们需要查询 CommandLine 对象来查看是否存在 H 选项：
```java
if (commandLine.hasOption('H')) {
    printUsage();
    return true;
}
```
hasOption 方法接受一个 String 参数，如果 String 表示的选项存在，则返回 true，否则返回 false。

> 查询阶段的目的是根据命令行和解析器处理的 Options 规则与用户的代码相匹配。

## 3. Option 选项

| 选项  | 类  | 说明 |
| :------------- | :------------- | :------------- |
| Item One       | Item Two       |

## 4. 示例


> 参考：[]()
