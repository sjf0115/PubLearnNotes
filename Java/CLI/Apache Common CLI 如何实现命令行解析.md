
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

命令行处理有三个阶段，分别是定义阶段、解析阶段和查询阶段。下面依次讨论这几个阶段，并讨论如何用 CLI（Apache Common CLI） 实现。

### 2.1 定义阶段

定义阶段的目的就是创建一个 Options 实例以及各种 Option。

#### 2.1.1 Options

每一个命令行都必须定义一组参数，在 CLI 中使用 Options 类来定义和设置，是所有 Option 实例的容器：
```java
Options options = new Options();
```
通过 `addOption` 方法来添加 Option 实例：
```java
// -H 或者 --help
options.addOption(new Option("H", "help", false, "Print help information"));
```

下面具体看一下 Options 的一些常用方法：

| 返回值     | 方法名     | 说明      |
| :------------- | :------------- |
| `Options`  | `addOption(Option opt)` | 添加一个 Option |
| `Options`	 | `addOption(String opt, boolean hasArg, String description)`	| 添加一个只包含短选项名称的 Option（可以指定参数） |
| `Options`	 | `addOption(String opt, String description)` | 添加一个只包含短选项名称的 Option（没有参数）|
| `Options`	 | `addOption(String opt, String longOpt, boolean hasArg, String description)` | 添加一个包含短选项名称和长选项名称的 Option（可以指定参数）|
| `Options`	 | `addOptionGroup(OptionGroup group)`	| 添加一个选项组 |
| `Options`  | `addRequiredOption(String opt, String longOpt, boolean hasArg, String description)` | 添加一个必须的 Option |
| `List<String>` | `getMatchingOptions(String opt)`	| 获取匹配 opt 的长选项名称集合。如果没有直接匹配的，返回匹配 opt 前缀的选项。 |
| `Option` | `getOption(String opt)` | 通过长选项名称或短选项名称获取 Option 实例 |
| `OptionGroup`	| `getOptionGroup(Option opt)` | 获取选项所在的选项组 |
| `Collection<OptionGroup>` | `getOptionGroups()` | 获取所有选项组 |
| `Collection` | `getOptions()` | 获取一个只读的选项集合 |
| `List` | `getRequiredOptions()` | 获取所有必须的选项集合 |
| `boolean` | `hasLongOption(String opt)` | 判断是否存在 opt 指定长选项 |
| `boolean` | `hasShortOption(String opt)` | 判断是否存在 opt 指定的短选项 |
| `boolean` | `hasOption(String opt)` | 判断是否存在 opt 指定长选项或者短选项 |

#### 2.1.2 Option

每一个 Option 实例对应了命令行中的一个参数。目前有两种方式创建 Option，一种是通过构造函数，这是最普通也是最为大家所熟知的一种方式：
```java
// -H 或者 --help
options.addOption(new Option("H", "help", false, "Print help information"));
```
Option 为了应对不同的场景，一共提供了 4 种构造器：
- `public Option(final String option, final String description)`：需要指定短选项名称以及描述信息
- `public Option(final String option, final boolean hasArg, final String description)`：需要指定短选项名称、Option 是否需要额外参数以及描述信息
- `public Option(final String option, final String longOption, final boolean hasArg, final String description)`：需要指定短选项名称、长选项名称、是否需要额外参数以及描述信息

另外一种方式是通过工厂方式来实现：
```java
Options options = new Options();
// 1.3 版本之前
options.addOption(OptionBuilder
    .withValueSeparator()
    .hasArgs(2)
    .withArgName("key=value")
    .withLongOpt("define")
    .withDescription("Variable substitution to apply to Hive commands. e.g. -d A=B or --define A=B")
    .create('d'));
// 1.3 版本及以后版本
options.addOption(Option.builder("d")
    .hasArgs()
    .valueSeparator('=')
    .numberOfArgs(2)
    .longOpt("define")
    .desc("Variable substitution to apply to Hive commands. e.g. -d A=B or --define A=B")
    .build());
```
> 从 1.3 版本开始，OptionBuilder 被 Option#builder 取代

下面我们看看可以为 Option 设置哪些属性：

| 属性  | 类型  | 说明 |
| :------------- | :------------- | :------------- |
| `option`  | String | 短选项名称，选项的唯一标识符 |
| `longOption` | String | 长选项名称，段选项的别名或者是更具描述性的标识符 |
| `required` | boolean | 选项是否必须存在 |
| `description` | String | 选项的描述信息 |
| `type` | Object | 选项类型 |
| `optionalArg` | boolean | 选项的参数是否可选 |
| `argName` | String | 参数的名称 |
| `argCount` | int | 选项可以包含的参数个数 |
| `values` | String[] | 参数值列表 |
| `valuesep` | char | 参数值分隔符 |

### 2.2 解析阶段

解析阶段的目的就是创建一个 CommandLine 实例。在解析阶段中，对通过命令行传入应用程序的文本进行处理。CLI 通过 CommandLineParser 的 parse 方法解析命令行参数，用定义阶段产生的 Options 实例和 `String[]` 中的参数作为输入，并返回解析后生成的 CommandLine 对象。

CommandLineParser 有多种实现类，例如 BasicParser、GnuParser、PosixParser、DefaultParser。从 1.3 版本开始推荐使用 DefaultParser，因为除了 DefaultParser，其他的都被打上了 `@Deprecated` 标记：
```java
// 老版本
// CommandLineParser parser = new GnuParser();
// 1.3 新版本
CommandLineParser parser = new DefaultParser();
CommandLine commandLine = parser.parse(options, args);
```

### 2.3 查询阶段

查询阶段的目的是根据命令行和解析器处理的 Options 规则与用户的代码相匹配。应用程序通过查询 CommandLine，并通过其中的布尔参数和提供给应用程序的参数值来决定需要执行哪个程序分支。CommandLine 表示根据 Options 解析的参数列表。如下所示，我们查询 CommandLine 对象来查看是否存在 H 和 d 选项：
```java
if (commandLine.hasOption('H')) {
    printUsage();
    return true;
}
// 例如，-d dt=20221001，选项的第一个参数为dt，第二个参数为20221001
Properties hiveVars = commandLine.getOptionProperties("d");
for (String propKey : hiveVars.stringPropertyNames()) {
    System.out.println("[INFO] -d " + propKey + "=" + hiveVars.getProperty(propKey));
}
```

这个阶段需要在用户的代码中实现，CommandLine 中的访问方法为用户代码提供了 CLI 的交互能力：

| 返回值  | 方法名  | 说明 |
| :------------- | :------------- | :------------- |
| `List` | `getArgList()`	| 获取未识别的选项或者参数列表 |
| `String[]` | `getArgs()` | 获取未识别的选项或者参数数组 |
| `Option[]` | `getOptions()` | 获取选项集合 |
| `Properties` | `getOptionProperties(String opt)` | 获取选项对应参数的键值对；前两个参数作为键值对；|
| `Properties` | `getOptionProperties(Option option)` | 获取选项对应的参数的键值对；前两个参数作为键值对；1.5.0 版本开始；|
| `String` | `getOptionValue(char opt)`	| 获取选项对应的第一个参数 |
| `String` | `getOptionValue(char opt, String defaultValue)` | 获取选项对应的第一个参数；如果没有指定返回 defaultValue |
| `String` | `getOptionValue(String opt)`	| 获取选项对应的第一个参数 |
| `String` | `getOptionValue(String opt, String defaultValue)` | 获取选项对应的第一个参数；如果没有指定返回 defaultValue |
| `String` | `getOptionValue(Option option)` | 获取选项对应的第一个参数 |
| `String` | `getOptionValue(Option option, String defaultValue)` | 获取选项对应的第一个参数；如果没有指定返回 defaultValue；1.5.0 版本开始； |
| `String[]` | `getOptionValues(char opt)` | 获取选项对应所有参数 |
| `String[]` | `getOptionValues(String opt)` | 获取选项对应所有参数 |
| `String[]` | ``getOptionValues(Option option)` | 获取选项对应所有参数；1.5.0 版本开始；|
| `Object` | `getParsedOptionValue(char opt)` | 获取选项对应的第一个参数；转换为 type 指定的类型 |
| `Object` | `getParsedOptionValue(String opt)` | 获取选项对应的第一个参数；转换为 type 指定的类型 |
| `Object` | `getParsedOptionValue(Option option)` |  获取选项对应的第一个参数；转换为 type 指定的类型；1.5.0 版本开始；|
| `boolean` | `hasOption(char opt)`	| 判断是否含有选项 |
| `boolean` | `hasOption(String opt)`	| 判断是否含有选项 |
| `boolean` | `hasOption(Option opt)`	| 判断是否含有选项；1.5.0 版本开始； |

> getOptionValue 获取的是 getOptionValues 中的第一个参数

## 4. 示例

解析 Hive CLI 选项 `-e`、`-d`(`--define`) 以及 `-H`(`--help`)：
```java
public class HiveOptionsProcessor {
    private Gson gson = new GsonBuilder().create();
    private final Options options = new Options();
    private CommandLine commandLine;

    @SuppressWarnings("static-access")
    public HiveOptionsProcessor() {
        // 1. 定义阶段
        // -e 'quoted-query-string'
        options.addOption(Option.builder("e")
                .hasArg()
                .argName("quoted-query-string")
                .desc("SQL from command line")
                .build());

        // 自定义变量 -d, --define
        options.addOption(Option.builder()
                .hasArgs()
                .numberOfArgs(2)
                .argName("key=value")
                .valueSeparator('=')
                .longOpt("define")
                .option("d")
                .desc("Variable substitution to apply to Hive commands. e.g. -d A=B or --define A=B")
                .build());

        // [-H|--help]
        options.addOption(new Option("H", "help", false, "Print help information"));
    }

    public boolean process(String[] args) {
        try {
            // 2. 解析阶段
            // CommandLineParser parser = new GnuParser(); // 老版本
            CommandLineParser parser = new DefaultParser();
            commandLine = parser.parse( options, args);

            // 3. 查询阶段
            // -H 或者 --help
            if (commandLine.hasOption('H')) {
                printUsage();
                return true;
            }
            // -d 或者 --define
            Properties hiveVars = commandLine.getOptionProperties("d");
            for (String propKey : hiveVars.stringPropertyNames()) {
                System.out.println("[INFO] -d " + propKey + "=" + hiveVars.getProperty(propKey));
            }
            // -e
            if (commandLine.hasOption('e')) {
                String execString = commandLine.getOptionValue('e');
                System.out.println("[INFO] -e " + execString);
            }

            // 其他测试
            for (String arg : commandLine.getArgList()) {
                System.out.println("ArgList: " + arg);
            }
            System.out.println("Args: " + gson.toJson(commandLine.getArgs()));
            for (Option o : commandLine.getOptions()) {
                System.out.println("Option: " + o.toString());
            }
            System.out.println("OptionProperties: " + gson.toJson(commandLine.getOptionProperties("d")));
            System.out.println("OptionValue: " + gson.toJson(commandLine.getOptionValue("d")));
            System.out.println("OptionValues: " + gson.toJson(commandLine.getOptionValues("d")));
            System.out.println("ParsedOptionValue: " + gson.toJson(commandLine.getParsedOptionValue("d")));

        } catch (ParseException e) {
            System.err.println(e.getMessage());
            printUsage();
            return false;
        }
        return true;
    }

    // 打印帮助信息
    private void printUsage() {
        new HelpFormatter().printHelp("hive", options);
    }

    public static void main(String[] args) {
        HiveOptionsProcessor processor = new HiveOptionsProcessor();
        String[] params = {"-e", "SHOW DATABASES", "-d", "dt=20221001", "--define", "hh=10"};
        processor.process(params);
    }
}
```

> 完整代码：[HiveOptionsProcessor](https://github.com/sjf0115/data-example/blob/master/common-example/src/main/java/com/common/example/cli/HiveOptionsProcessor.java)
