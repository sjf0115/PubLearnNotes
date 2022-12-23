## 1. Hive 命令行选项

如果想查看 Hive 命令行选项，可以执行 `hive -H` 或 `hive --help` 来获取：
```
localhost:script wy$ hive -H
usage: hive
 -d,--define <key=value>          Variable substitution to apply to Hive
                                  commands. e.g. -d A=B or --define A=B
    --database <databasename>     Specify the database to use
 -e <quoted-query-string>         SQL from command line
 -f <filename>                    SQL from files
 -H,--help                        Print help information
    --hiveconf <property=value>   Use value for given property
    --hivevar <key=value>         Variable substitution to apply to Hive
                                  commands. e.g. --hivevar A=B
 -i <filename>                    Initialization SQL file
 -S,--silent                      Silent mode in interactive shell
 -v,--verbose                     Verbose mode (echo executed SQL to the
                                  console)
```

### 1.1 Hive 批模式命令

当 `$HIVE_HOME/bin/hive` 运行时使用带 `-e` 或 `-f` 选项时，将以批处理方式执行 SQL 命令：
- `hive -e <query-string>` 执行查询字符串。
- `hive -f <filepath>` 执行文件中的一个或多个SQL查询。

例如，使用如下命令以非交互式方式从命令行中运行查询：
```
hive -e 'SHOW TABLES;'
```
例如，使用如下命令以非交互式方式运行本地的 HQL 脚本：
```
hive -f /home/my/hive-script.sql
```
例如，使用如下命令以非交互式方式运行 Hadoop 支持的文件系统上的脚本：
```
hive -f hdfs://<namenode>:<port>/hive-script.sql
```

### 1.2 变量和属性

#### 1.2.1 命名空间

在介绍变量和属性之前，我们先看一下 Hive 中的 4 种内置命名空间：hivevar、hiveconf、system 以及 env。

| 命名空间 | 使用权限 | 说明 |
| :------------- | :------------- | :------------- |
| hivevar | 可读、可写 | 用户自定义变量，Hive 0.8.0 及以后版本有效 |
| hiveconf | 可读、可写 | Hive 相关的配置属性 |
| system | 可读、可写 | Java 定义的配置属性 |
| env | 只可读 | Shell 环境(例如，bash) 定义的环境变量 |

#### 1.2.2 hivevar

可以通过 `--define key=value` 和 `--hivevar key=value` 命令在 hivevar 命名空间自定义变量，两者是等价的，都可以让用户在命令行中自定义用户变量以便在 Hive 脚本中引用。如下所示通过 `--define` 命令定义了一个变量 dt：
```
localhost:~ wy$ hive --define dt=2015-08-01;
...
Logging initialized using configuration in file:/opt/apache-hive-2.3.4-bin/conf/hive-log4j2.properties Async: true
Hive-on-MR is deprecated in Hive 2 and may not be available in the future versions. Consider using a different execution engine (i.e. spark, tez) or using Hive 1.X releases.
hive (default)> set dt;
dt=2015-08-01
hive (default)> set hivevar:dt;
hivevar:dt=2015-08-01
```
通过 SET 查看 dt 的值可以发现变量 dt 是定义在 hivevar 命名空间下的。通过 `hive --hivevar dt=2015-08-01;` 命令也可以达到相同的效果。

Hive 变量内部是以 Java 字符串的方式存储的，用户可以在查询中引用变量。Hive 会先使用变量值替换掉查询中的变量引用，然后才会将查询语句提交给查询处理器。如下两个 SQL 语句是等价的：
```sql
SELECT COUNT(*) FROM behavior
WHERE SUBSTR(time, 1, 10) = '${hivevar:dt}';

SELECT COUNT(*) FROM behavior
WHERE SUBSTR(time, 1, 10) = '2015-08-01';
```

#### 1.2.2 hiveconf

hiveconf 选项是 Hive 0.7.0 版本才开始支持的功能，用于配置 Hive 行为的所有属性。例如，我们可以使用该选项指定 hive.cli.print.header 属性来打印表头（默认为 false）：
```
localhost:~ wy$ hive --hiveconf hive.cli.print.header=true;
...
Logging initialized using configuration in file:/opt/apache-hive-2.3.4-bin/conf/hive-log4j2.properties Async: true
Hive-on-MR is deprecated in Hive 2 and may not be available in the future versions. Consider using a different execution engine (i.e. spark, tez) or using Hive 1.X releases.
hive (default)> set hive.cli.print.header;
hive.cli.print.header=true
hive (default)> set hiveconf:hive.cli.print.header;
hiveconf:hive.cli.print.header=true
hive (default)>
```
此外，我们还可以增加新的 hiveconf 属性，这个功能只有 Hive 0.8.0 版本才开始支持：
```
localhost:~ wy$ hive --hiveconf dt=2022-10-01;
...
Logging initialized using configuration in file:/opt/apache-hive-2.3.4-bin/conf/hive-log4j2.properties Async: true
Hive-on-MR is deprecated in Hive 2 and may not be available in the future versions. Consider using a different execution engine (i.e. spark, tez) or using Hive 1.X releases.
hive (default)> set dt;
dt=2022-10-01
hive (default)> set hivevar:dt;
hivevar:dt is undefined as a hive variable
Query returned non-zero code: 1, cause: null
hive (default)> set hiveconf:dt;
hiveconf:dt=2022-10-01
hive (default)>
```
通过上面语句可以发现 dt 属性是定义在 hiveconf 命名空间下的，而不是定义在 hivevar 命名空间下。

> dt 认为是变量也没有问题，只是定义在不同命名空间下而已。变量和属性是在不同的上下文中使用的术语，但是在大多数情况下它们的功能是相同的

#### 1.2.3 system

可以通过如下命令查看 system 命名空间下 Java 定义的配置属性：
```
hive (default)> set system:user.name;
system:user.name=wy
```
> 和 hivevar 和 hiveconf 不同，用户必须使用 `sytem:` 前缀来指定系统属性。

#### 1.2.4 env

可以通过如下命令查看 env 命名空间下 Shell 环境(例如，bash) 定义的环境变量：
```
hive (default)> set env:HIVE_HOME;
env:HIVE_HOME=/opt/hive
```
> 和 hivevar 和 hiveconf 不同，用户必须使用 `env:` 前缀来指定环境变量。

### 1.3 静默模式

使用 `-S` 命令进入 hive 的静默模式，只显示查询结果，不显示执行过程；如下所示使用静默模式执行 HQL 语句：
```
hive -S -e 'SELECT COUNT(*) FROM behavior';
```
这样可以在输出中去掉 'OK'、'Time taken' 等无关的输出。

### 1.4 hiverc 文件

CLI 选项有一个 `-i` 选项，允许用户指定一个文件，当 CLI 启动时，在提示符出现前会先执行这个文件。Hive 会自动在 HOME 目录下寻找名为 `.hiverc` 的文件，而且会自动执行这个文件中的命令（如果文件有的话）。对于用户使用比较频繁的命令，使用这个文件是非常方便的。下面的例子展示了一个典型的 `$HOME/.hiverc` 文件中的内容：
```
set hive.cli.print.current.db=true;
set hive.exec.mode.local.auto=true;
```
我们也可以为 `-i` 选项手动指定配置文件：
```
hive -i /opt/conf/hive-init.conf;
```
其中 hive-init.conf 的内容如下：
```
set hive.cli.print.header=true;
```
> 如果通过 -i 选项手动指定了配置文件，那么就不会再执行 $HOME/.hiverc 文件中的命令了。

## 2. Hive 交互式 Shell 命令

当使用 `$HIVE_HOME/bin/hive` 命令运行，并且没有 `-e` 或 `-f` 选项时，会进入到交互式 Shell 模式：

命令|描述
---|---
`quit` 或 `exit` | 退出交互式 Shell 模式
`reset` | 将配置重置为默认值
`set <key>=<value>` | 为指定配置选项设置值
`set` | 打印由用户或 Hive 覆盖后的配置变量列表
`set -v` | 打印所有 Hadoop 和 Hive 配置变量
`add FILE[S] <filepath> <filepath>*` 或 `add JAR[S] <filepath> <filepath>*` 或 `add ARCHIVE[S] <filepath> <filepath>*` | 将一个或多个文件，jar或归档添加到分布式缓存中的资源列表
`list FILE[S]` 或 `list JAR[S]` 或 `list ARCHIVE[S]` | 列出已添加到分布式缓存中的资源
`delete FILE[S] <filepath>*` 或 `delete JAR[S] <filepath>*` 或 `delete ARCHIVE[S] <filepath>*` ` | 从分布式缓存中删除资源
`! <command>` | Hive shell 中执行 shell命令
`dfs <dfs command>` | Hive shell 中执行 dfs 命令
`<query string>` | 执行 Hive 查询并将结果打印到标准输出
`source FILE <filepath>` | 在 CLI 客户端中执行脚本文件
