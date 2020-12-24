
### 1. 为什么替换已有的Hive CLI

Hive CLI是一个古老的遗留工具，主要有两个的用途。

- 第一个是它在Hadoop上用作SQL的胖客户端`thick client `
- 第二个是Hive Server的命令行工具（原来的Hive服务器，现在通常被称为`HiveServer1`）。 

Hive Server已被弃用，并从Hive1.0.0([HIVE-6977](https://issues.apache.org/jira/browse/HIVE-6977))的Hive代码库中删除，并替换为HiveServer2([HIVE-2935](https://issues.apache.org/jira/browse/HIVE-2935))，因此第二个用例不再适用。 对于第一个用例，Beeline提供了原来的功能或者提供了相同的功能，但与Hive CLI的实现不同。

==备注==

胖客户端(Rich or Thick Client)，是相对于“瘦客户端”(Thin Client)（基于Web的应用程序）而言的，它是在客户机器上安装配置的一个功能丰富的交互式的用户界面，例如Oracle、DB2数据库的客户端管理工具。


理想情况下，`Hive CLI`应该被弃用，因为Hive社区长期以来一直建议使用`Beeline` + `HiveServer2`的配置; 然而，由于`Hive CLI`的使用比较广泛，而是使用在`Beeline`和嵌入式`HiveServer2`（HIVE-10511）之上的新`Hive CLI`来替代旧版`Hive CLI`的实现(保留外壳，本质已变)，因此Hive社区只需要维护一个代码路径。 以这种方式，新的`Hive CLI`只是在shell脚本级别和高代码级别的`Beeline`的别名(an alias to Beeline at both the shell script level and the high code level)。 目标是在使用新`Hive CLI`的情况下对现有用户脚本中尽量不更改或者尽量小的更改。

### 2. Hive CLI支持的功能

我们使用一种新的在`Beeline`之上的`Hive CLI`来实现旧版`Hive CLI`功能。由于在新的`Hive CLI`中不支持一些已有的`Hive CLI`功能，因此我们默认使用旧的Hive客户端实现。 使用以下命令指定新的基于`Beeline`的`Hive CLI`工具：

```
export USE_DEPRECATED_CLI=false
```
请注意，log4j配置文件已更改为`beeline-log4j.properties`。

### 3. Hive CLI支持的选项

可以运行`hive -H`或`hive --help`来获取帮助信息：
```
usage: hive
 -d,--define <key=value>          Variable subsitution to apply to hive
                                  commands. e.g. -d A=B or --define A=B
    --database <databasename>     Specify the database to use
 -e <quoted-query-string>         SQL from command line
 -f <filename>                    SQL from files
 -H,--help                        Print help information
    --hiveconf <property=value>   Use value for given property
    --hivevar <key=value>         Variable subsitution to apply to hive
                                  commands. e.g. --hivevar A=B
 -i <filename>                    Initialization SQL file
 -S,--silent                      Silent mode in interactive shell
 -v,--verbose                     Verbose mode (echo executed SQL to the
                                  console)

```

### 4. Example

从命令行运行查询:
```
hive -e 'select * from tmp_show';
```
设置Hive配置变量:
```
hive -e 'select a.foo from pokes a' --hiveconf hive.exec.scratchdir=/opt/my/hive_scratch --hiveconf mapred.reduce.tasks=1
```
使用无提示模式将数据从查询存储到文件中:
```
hive -S -e 'select a.foo from pokes a' > a.txt
```
以非交互式运行本地磁盘上的脚本:
```
hive -f /home/my/hive-script.sql > a.txt
```
以非交互式运行Hadoop支持的文件系统上的脚本:
```
hive -f hdfs://<namenode>:<port>/hive-script.sql
```
### 5. Hive CLI支持的交互式Shell命令

当使用`$HIVE_HOME/bin/hive`命令运行，并且没有`-e`或`-f`选项时，进入交互式shell模式。
使用`;`（分号）终止命令。可以使用`-`前缀指定脚本中的注释。

命令|描述
---|---
quit或exit|退出交互式Shell
reset|将配置重置为默认值
set <key>=<value>|为指定配置选项设置值
set|打印由用户或Hive覆盖后的配置变量列表
set -v | 打印所有Hadoop和Hive配置变量
add FILE[S] <filepath> <filepath>* 或add JAR[S] <filepath> <filepath>* 或add ARCHIVE[S] <filepath> <filepath>*|将一个或多个文件，jar或归档添加到分布式缓存中的资源列表
list FILE[S]或list JAR[S]或list ARCHIVE[S]|列出已添加到分布式缓存中的资源
delete FILE[S] <filepath>* 或delete JAR[S] <filepath>* 或delete ARCHIVE[S] <filepath>*|从分布式缓存中删除资源
! <command>|Hive shell中执行shell命令
dfs <dfs command>|Hive shell中执行dfs命令
<query string>|执行Hive查询并将结果打印到标准输出
source FILE <filepath>|在CLI客户端中执行脚本文件

Example:

```
hive> source /root/test.sql;
hive> show tables;
test1
test2
hive> exit;
hive> quit;
hive> set;
hive> set hive.cli.print.header=true;
hive> set -v;
hive> reset;
hive> add file /opt/a.txt;
Added resources: [/opt/a.txt]
hive> list files;
/opt/a.txt
hive> delete file /opt/a.txt;
hive> add jar /usr/share/vnc/classes/vncviewer.jar;
Added [/usr/share/vnc/classes/vncviewer.jar]to class path
Added resources:[/usr/share/vnc/classes/vncviewer.jar]
hive> list jars;
/usr/share/vnc/classes/vncviewer.jar
hive> delete jar /usr/share/vnc/classes/vncviewer.jar;
hive> !ls;
bin
conf
hive> dfs -ls / ;
Found 2 items
drwx-wx-wx  - root supergroup  0   2015-08-12 19:06 /tmp
drwxr-xr-x  - root supergroup  0   2015-08-12 19:43 /user
hive> select * from pokes; 
OK
pokes.foo   pokes.bar
238         val_238
86          val_86
311         val_311
hive>source /opt/s.sql;
```

### 6. Hive CLI支持的配置

配置项|新Hive CLI是否支持|描述
---|---|---
hive.cli.print.header|Yes|是否在查询输出中打印列的名称。[HIVE-11624](https://issues.apache.org/jira/browse/HIVE-11624)
hive.cli.errors.ignore|Yes|是否在发生错误时强制执行脚本。[HIVE-11191](https://issues.apache.org/jira/browse/HIVE-11191)
hive.cli.prompt|Yes|命令行提示配置值。 其他hiveconf可用于此配置值。[HIVE-11226](https://issues.apache.org/jira/browse/HIVE-11226)
hive.cli.pretty.output.num.cols|Yes|当时用`DESCRIBE PRETTY table_name`命令格式化输出时使用的列数。[HIVE-11779](https://issues.apache.org/jira/browse/HIVE-11779)
hive.cli.print.current.db|Yes|是否在Hive提示符下显示前数据库。[HIVE-11637](https://issues.apache.org/jira/browse/HIVE-11637)


Example:
```
hive> set hive.cli.print.header;
hive.cli.print.header=false
hive> set hive.cli.print.header = true;
hive> select * from tmp_show;
OK
tmp_show.entrance	tmp_show.show_pv
213	234421
214	8765313
307	897651
325	7653615
408	27651565
122	34343232


hive> set hive.cli.print.current.db;
hive.cli.print.current.db=false
hive> set hive.cli.print.current.db = true;
hive (default)> 
```




原文：https://cwiki.apache.org/confluence/display/Hive/Replacing+the+Implementation+of+Hive+CLI+Using+Beeline