---
layout: post
author: sjf0115
title: HBase Shell 命令
date: 2019-12-28 20:49:21
tags:
  - HBase

categories: HBase
permalink: hbase-shell-and-commands
---

HBase 提供了一个非常方便的命令行交互工具 HBase Shell。通过 HBase Shell 可以创建表，也可以增删查数据，同时集群的管理、状态查看等也可以通过 HBase shell 实现。

HBase Shell 用法：
- 确保用 HBase Shell 对所有名称使用双引号，例如表名和列名。
- 逗号分隔命令参数。
- 在输入要运行的命令之后，键入<RETURN>。
- 在表的创建和更改中，我们使用配置字典，它们是Ruby哈希。看起来像：`{‘key1’ => ‘value1’, ‘key2’ => ‘value2’, …}`。

### 1. 连接HBase Shell

通过使用以下命令，我们可以通过 Shell 连接到正在运行的 HBase：
```
./bin/hbase shell
```
键入 help 然后回车可以查看 Shell 命令以及参数列表：
```
hbase(main):001:0> help
HBase Shell, version 2.1.6, rba26a3e1fd5bda8a84f99111d9471f62bb29ed1d, Mon Aug 26 20:40:38 CST 2019
Type 'help "COMMAND"', (e.g. 'help "get"' -- the quotes are necessary) for help on a specific command.
Commands are grouped. Type 'help "COMMAND_GROUP"', (e.g. 'help "general"') for help on a command group.

COMMAND GROUPS:
  Group name: general
  Commands: processlist, status, table_help, version, whoami
...
```
如果想退出 Shell，可以通过键入 exit 退出：
```
hbase(main):002:0> exit
```

### 2. 常规命令

在 Hbase 中，有如下常规命令：
- status
- version
- whoami

#### 2.1 status

可以使用 `status` 命令展示 HBase 集群的系统状态的详细，例如服务器数量：
```
hbase(main):001:0> status
1 active master, 0 backup masters, 1 servers, 0 dead, 3.0000 average load
Took 0.3686 seconds
```

我们还可以传递特定参数，具体取决于我们想了解系统的哪些详细状态。参数可以为 `summary`，`simple`，`detailed` 或 `replication`。默认不填为 `summary`。下面我们展示了如何将不同的参数传递给 `status` 命令：
```
hbase> status
hbase> status 'simple'
hbase> status 'summary'
hbase> status 'detailed'
hbase> status 'replication'
hbase> status 'replication', 'source'
hbase> status 'replication', 'sink'
```

#### 2.2 version

可以使用 `version` 命令展示当前使用的 HBase 版本：
```
hbase(main):005:0> version
2.1.6, rba26a3e1fd5bda8a84f99111d9471f62bb29ed1d, Mon Aug 26 20:40:38 CST 2019
```

#### 2.3 whoami

可以使用 `whoami` 命令展示当前 HBase 用户：
```
hbase(main):010:0> whoami
smartsi (auth:SIMPLE)
    groups: staff, everyone, localaccounts, _appserverusr, admin, _appserveradm, _lpadmin, com.apple.sharepoint.group.1, _appstore, _lpoperator, _developer, _analyticsusers, com.apple.access_ftp, com.apple.access_screensharing, com.apple.access_ssh
```

### 3. DDL命令

数据定义语言(Data Definition Language, DDL)，包括数据库表的创建、修改、删除等语句。

在 Hbase 中，有如下数据定义命令：
- Create
- Exists
- Describe
- List
- Disable
- Disable_all
- Is_disabled
- Enable
- Enable_all
- Is_enabled
- Alter
- Drop

#### 3.1 Create

可以使用 `create` 命令创建表，必须指定表名和列族名，以及可选的命名空间参数。列族名可以是一个简单的字符串，也可以是包含 `NAME` 属性的字典：
```
hbase(main):002:0> create 't1', 'f1', 'f2', 'f3'
Created table t1
Took 2.7450 seconds
=> Hbase::Table - t1
```
上述命令也可以通过字典方式创建：
```
create 't1', {NAME => 'f1'}, {NAME => 'f2'}, {NAME => 'f3'}
```
上面命令均没有指定命名空间，默认为 `default`。使用如下命令在 `ns1` 命名空间下创建 `t1` 表：
```
hbase(main):026:0> create 'ns1:t1', 'f1', 'f2', 'f3'
Created table ns1:t1
Took 2.4030 seconds
=> Hbase::Table - ns1:t1
```

> 命名空间是表的逻辑分组，类似于关系数据库系统中的数据库。这种抽象为多租户相关功能奠定了基础。具体使用可以查阅[HBase 命名空间 Namespace](http://smartsi.club/hbase-namespace-commands-examples)

#### 3.2 Exists

可以使用 `exists` 命令判断表是否存在：
```
hbase> exists 't1'
hbase> exists 'ns1:t1'
```
例如，使用如下命令查看表 `t1` 是否存在：
```
hbase(main):003:0> exists 't1'
Table t1 does exist
Took 0.0914 seconds
=> true
hbase(main):029:0> exists 'ns1:t1'
Table ns1:t1 does exist
Took 0.1863 seconds
=> true
```

#### 3.3 Describe

可以使用 `describe` 命令查看表信息：
```
hbase> describe 't1'
hbase> describe 'ns1:t1'
```
或者简写为：
```
hbase> desc 't1'
hbase> desc 'ns1:t1'
```
例如，使用如下命令查看表 `t1` 的具体信息：
```
hbase(main):043:0> describe 't1'
Table t1 is ENABLED
t1
COLUMN FAMILIES DESCRIPTION
{NAME => 'f1', VERSIONS => '1', EVICT_BLOCKS_ON_CLOSE => 'false', NEW_VERSION_BEHAVIOR => 'false', KEEP_DELETED_CELLS => 'FALSE', CACHE_DATA_ON_WRITE => 'false', DATA_BLOCK_ENCODING => 'NONE', TTL => 'FOREVER', MIN_VERS
IONS => '0', REPLICATION_SCOPE => '0', BLOOMFILTER => 'ROW', CACHE_INDEX_ON_WRITE => 'false', IN_MEMORY => 'false', CACHE_BLOOMS_ON_WRITE => 'false', PREFETCH_BLOCKS_ON_OPEN => 'false', COMPRESSION => 'NONE', BLOCKCACHE
 => 'true', BLOCKSIZE => '65536'}
...
Took 0.0319 seconds
```
可以看到在建表的时候没有指定任何属性，但是 HBase 默认会给表设置一些属性：
- `VERSIONS`：HBase 对表的数据行可以保留多个数据版本，以时间戳来区分。`VERSIONS` 表示对该表应该保留多少个数据版本。
- `KEEP_DELETED_CELLS`：保留删除的数据。这意味着可以通过 Get 或 Scan 操作获取已经被删除的数据（如果数据删除后经过了一次主压缩，那么这些删除的数据也会被清理）。需要注意的是，如果开启了集群间复制，则这个属性必须设置为 true，否则可能导致数据复制失败。
- `DATA_BLOCK_ENCODING`：数据块编码。用类似压缩算法的编码形式来节省存储空间，主要是针对行键。默认情况下不启用数据块编码。
- `TTL`：数据有效时长。超过有效时长的数据在主压缩的时候会被删除。
- `BLOOMFILTER`：布隆过滤器。数据查询 Scan 操作的时候用来排除待扫描的 StoreFile 文件。
- `REPLICATION_SCOPE`：集群间数据复制开关。当集群间数据复制配置好之后 `REPLICATION_SCOPE` = 1 的表会开启复制。默认为 0，表示不开启复制。
- `COMPRESSION`：压缩方式。HBase 提供了多种压缩方式来在数据存储到磁盘之前压缩以减少存储空间。
- `BLOCKSIZE`：HBase 读取数据的最小单元。设置过大会导致读取很多不需要的数据，过小则会产生过多的索引文件，默认为 64 KB。

#### 3.4 List

可以使用 `list` 命令查看 HBase 中用户自定义的表，也可以使用正则表达式查询：
```
hbase> list
hbase> list 'abc.*'
hbase> list 'ns:abc.*'
hbase> list 'ns:.*'
```
例如，使用如下命令查看所有的表：
```
hbase(main):045:0> list
TABLE
ns1:t1
ns1:test
t1
test
4 row(s)
Took 0.0075 seconds
=> ["ns1:t1", "ns1:test", "t1", "test"]
```
#### 3.5 Disable

可以使用 `disable` 命令禁用表：
```
hbase(main):050:0> disable 'test'
Took 0.7409 seconds
hbase(main):051:0> disable 'ns1:test'
Took 0.4331 seconds
```

#### 3.6 Disable_all

可以使用 `disable_all` 命令禁用满足正则表达式条件的表：
```
hbase> disable_all 't.*'
hbase> disable_all 'ns:t.*'
hbase> disable_all 'ns:.*'
```

#### 3.7 Is_disabled

可以使用 `is_disabled` 命令查看表是否被禁用：
```
hbase> is_disabled 't1'
hbase> is_disabled 'ns1:t1'
```
例如，使用如下命令查看表 `t1` 是否被禁用：
```
hbase(main):009:0> is_disabled 't1'
true
Took 0.0269 seconds
=> 1
```
#### 3.8 Enable

可以使用 `enable` 命令启用表：
```
hbase> enable 't1'
hbase> enable 'ns1:t1'
```

#### 3.9 Enable_all

可以使用 `enable_all` 命令启用满足正则表达式条件的表：
```
hbase> enable_all 't.*'
hbase> enable_all 'ns:t.*'
hbase> enable_all 'ns:.*'
```

#### 3.10 Is_enabled

可以使用 `is_enabled` 命令查看表是否启用：
```
hbase> is_enabled 't1'
hbase> is_enabled 'ns1:t1'
```
例如，使用如下命令查看表 `t1` 是否启用：
```
hbase(main):004:0> is_enabled 't1'
false
Took 0.0242 seconds
=> false
```

#### 3.11 Alter

可以使用 `alter` 命令对 Hbase 的表以及列族进行修改，如新增一个列族、修改表属性，增加协处理器等等。修改表的模式之前需要先将表下线（禁用），然后执行修改命令，再上线（启用）。例如，使用如下命令修改表列族 `f1` 可以最多保留5个版本的数据：
```
hbase(main):012:0> alter 't1', NAME => 'f1', VERSIONS => 5
Updating all regions with the new schema...
All regions updated.
Done.
Took 1.3834 seconds
```
我们也可以同时操作多个列族：
```
hbase> alter 't1', 'f1', {NAME => 'f2', IN_MEMORY => true}, {NAME => 'f3', VERSIONS => 5}
```
我们可以使用如下方法删除表 `ns1:t1` 中的 `f3` 列族：
```
hbase> alter 'ns1:t1', NAME => 'f3', METHOD => 'delete'
hbase> alter 'ns1:t1', 'delete' => 'f3'
```

#### 3.12 drop

可以使用 `drop` 命令删除表，但是表必须首先要禁用表：
```
hbase(main):052:0> drop 't1'
Took 0.2300 seconds
hbase(main):053:0> drop 'ns1:t1'
Took 0.2357 seconds
```

### 4. DML命令

数据操纵语言(Data Manipulation Language, DML)，包括数据的修改、查询、删除等语句。

在 Hbase 中，有如下数据操纵命令：
- Put
- Get
- Scan
- Count
- Append
- Delete
- Deleteall
- Truncate

#### 4.1 Put

可以使用 `put` 命令将一行数据插入到 HBase 表中：
```
put <table>, <rowkey>, <列族:列标示符>, <值>
```
例如，使用如下命令分别在表 `t1`、`ns1:t1` 插入一行数据：
```
put 't1', 'r1', 'f1:c1', 'this is first value'
put 'ns1:t1', 'r1', 'f1:c1', 'this is first value of ns1'
```

#### 4.2 Get

可以使用 `get` 命令获取 HBase 表的一行或者一个单元的内容：
```
hbase> get 'ns1:t1', 'r1'
hbase> get 't1', 'r1'
hbase> get 't1', 'r1', {TIMERANGE => [ts1, ts2]}
hbase> get 't1', 'r1', {COLUMN => 'c1'}
hbase> get 't1', 'r1', {COLUMN => ['c1', 'c2', 'c3']}
hbase> get 't1', 'r1', {COLUMN => 'c1', TIMESTAMP => ts1}
hbase> get 't1', 'r1', {COLUMN => 'c1', TIMERANGE => [ts1, ts2], VERSIONS => 4}
hbase> get 't1', 'r1', {COLUMN => 'c1', TIMESTAMP => ts1, VERSIONS => 4}
hbase> get 't1', 'r1', {FILTER => "ValueFilter(=, 'binary:abc')"}
hbase> get 't1', 'r1', 'c1'
hbase> get 't1', 'r1', 'c1', 'c2'
hbase> get 't1', 'r1', ['c1', 'c2']
hbase> get 't1', 'r1', {COLUMN => 'c1', ATTRIBUTES => {'mykey'=>'myvalue'}}
hbase> get 't1', 'r1', {COLUMN => 'c1', AUTHORIZATIONS => ['PRIVATE','SECRET']}
hbase> get 't1', 'r1', {CONSISTENCY => 'TIMELINE'}
hbase> get 't1', 'r1', {CONSISTENCY => 'TIMELINE', REGION_REPLICA_ID => 1}
```
例如，使用如下命令可以获取表 `t1` 的一条记录：
```
hbase(main):028:0> get 'ns1:t1', 'r1'
COLUMN                                              CELL
 f1:c1                                              timestamp=1573986505024, value=this is third value of ns1
1 row(s)
Took 0.0299 seconds
```
`Get` 也可以支持获取多个版本的数据，但是需要修改表的 `VERSIONS` 属性以支持多版本：
```
hbase(main):019:0> alter 'ns1:t1', NAME => 'f1', VERSIONS => 3
Updating all regions with the new schema...
1/1 regions updated.
Done.
Took 1.8057 seconds

hbase(main):027:0> get 'ns1:t1', 'r1', {COLUMN => 'f1:c1', VERSIONS => 3}
COLUMN                                              CELL
 f1:c1                                              timestamp=1573986505024, value=this is third value of ns1
 f1:c1                                              timestamp=1573986499590, value=this is second value of ns1
 f1:c1                                              timestamp=1573986493844, value=this is first value of ns1
1 row(s)
Took 0.0070 seconds
```

#### 4.3 Scan

可以使用 `scan` 命令来扫描表的数据。该命令是 HBase 数据查询命令中最复杂的命令，需要特别注意查询的数据量，以免由于扫描数据过大导致 HBase 集群出现响应延迟：
```
hbase(main):042:0> scan 'ns1:t1'
ROW                                                 COLUMN+CELL
 r1                                                 column=f1:c1, timestamp=1573994164276, value=this is first value of r1
 r2                                                 column=f1:c1, timestamp=1573994095092, value=this is first value of r2
 r3                                                 column=f1:c1, timestamp=1573994102776, value=this is first value of r3
 r4                                                 column=f1:c1, timestamp=1573994109851, value=this is first value of r4
 r5                                                 column=f1:c1, timestamp=1573994116959, value=this is first value of r5
 r6                                                 column=f1:c1, timestamp=1573994123621, value=this is first value of r6
 r7                                                 column=f1:c1, timestamp=1573994130600, value=this is first value of r7
 r8                                                 column=f1:c1, timestamp=1573994138110, value=this is first value of r8
8 row(s)
Took 0.0137 seconds
```
我们也可以通过指定时间区间获取某个时刻的数据：
```
hbase(main):043:0> scan 'ns1:t1', {TIMERANGE => [1573994102776, 1573994130600]}
ROW                                                 COLUMN+CELL
 r3                                                 column=f1:c1, timestamp=1573994102776, value=this is first value of r3
 r4                                                 column=f1:c1, timestamp=1573994109851, value=this is first value of r4
 r5                                                 column=f1:c1, timestamp=1573994116959, value=this is first value of r5
 r6                                                 column=f1:c1, timestamp=1573994123621, value=this is first value of r6
4 row(s)
Took 0.0786 seconds
```
我们也可以从 `r6` 行键开始获取 2 条记录：
```
hbase(main):002:0> scan 'ns1:t1', {COLUMNS => 'f1:c1', LIMIT => 2, STARTROW => 'r6'}
ROW                                                 COLUMN+CELL
 r6                                                 column=f1:c1, timestamp=1573994123621, value=this is first value of r6
 r7                                                 column=f1:c1, timestamp=1573994130600, value=this is first value of r7
2 row(s)
Took 0.4751 seconds
```

#### 4.4 Count

可以使用 `count` 命令统计表的行数：
```
hbase(main):005:0> count 'ns1:t1'
8 row(s)
Took 0.0726 seconds
=> 8
```
> 此操作可能需要花费很长的时间，因为会使用 `$HADOOP_HOME/bin/hadoop/jarhbase.jar rowcount` 命令来运行计数 MapReduce 作业。

默认情况下每 1000 行展示当前统计的计数，也可以通过 `INTERVAL` 属性重新指定计数间隔，如下每 2 行展示一次计数：
```
hbase(main):007:0> count 'ns1:t1', INTERVAL => 2
Current count: 2, row: r2
Current count: 4, row: r4
Current count: 6, row: r6
Current count: 8, row: r8
8 row(s)
Took 0.0200 seconds
=> 8
```

#### 4.5 Append

可以使用 `append` 命令向指定的单元上在原先值上追加新值：
```
hbase> append 't1', 'r1', 'c1', 'value'
```
例如，使用如下命令在原先的值后面追加`, append a new value`：
```
hbase(main):047:0> get 'ns1:t1', 'r1'
COLUMN                                              CELL
 f1:c1                                              timestamp=1573994164276, value=this is first value of r1
1 row(s)
Took 0.0475 seconds
hbase(main):049:0> append 'ns1:t1', 'r1', 'f1:c1', ', append a new value'
CURRENT VALUE = this is first value of r1, append a new value
Took 0.0119 seconds
hbase(main):050:0> get 'ns1:t1', 'r1'
COLUMN                                              CELL
 f1:c1                                              timestamp=1573996248316, value=this is first value of r1, append a new value
1 row(s)
Took 0.0171 seconds
```

#### 4.6 Delete

可以使用 `delete` 命令删除某列数据。如果我们指定了时间戳，那么我们只会删除对应版本的单元数据：
```
hbase(main):027:0> put 't1', 'r1', 'f1:c1', 'f1:c1:value1'
Took 0.0029 seconds
hbase(main):028:0> put 't1', 'r1', 'f1:c2', 'f1:c2:value1'
Took 0.0032 seconds
hbase(main):029:0> delete 't1', 'r1', 'f1:c1'
Took 0.0040 seconds
hbase(main):030:0> scan 't1'
ROW                                         COLUMN+CELL
 r1                                         column=f1:c2, timestamp=1577537013630, value=f1:c2:value1
1 row(s)
Took 0.0097 seconds
hbase(main):031:0> delete 't1', 'r1', 'f1:c2'
Took 0.0056 seconds
hbase(main):032:0> scan 't1'
ROW                                         COLUMN+CELL
0 row(s)
Took 0.0035 seconds
```

#### 4.7 Deleteall

可以使用 `deleteall` 命令删除整行数据：
```
hbase(main):033:0> put 't1', 'r1', 'f1:c1', 'f1:c1:value1'
Took 0.0030 seconds
hbase(main):034:0> put 't1', 'r1', 'f1:c2', 'f1:c2:value1'
Took 0.0044 seconds
hbase(main):035:0> deleteall 't1', 'r1'
Took 0.0038 seconds
hbase(main):036:0> scan 't1'
ROW                                         COLUMN+CELL
0 row(s)
Took 0.0036 seconds
```

#### 4.8 Truncate

可以使用 `truncate` 命令清空整个表的数据：
```
hbase(main):037:0> put 't1', 'r1', 'f1:c1', 'f1:c1:value1'
Took 0.0053 seconds
hbase(main):038:0> put 't1', 'r2', 'f1:c1', 'f1:c1:value2'
Took 0.0031 seconds
hbase(main):039:0> put 't1', 'r3', 'f1:c1', 'f1:c1:value3'
Took 0.0037 seconds
hbase(main):040:0> scan 't1'
ROW                                         COLUMN+CELL
 r1                                         column=f1:c1, timestamp=1577537153001, value=f1:c1:value1
 r2                                         column=f1:c1, timestamp=1577537167747, value=f1:c1:value2
 r3                                         column=f1:c1, timestamp=1577537173985, value=f1:c1:value3
3 row(s)
Took 0.0072 seconds
hbase(main):041:0> truncate 't1'
Truncating 't1' table (it may take a while):
Disabling table...
Truncating table...
Took 2.6141 seconds
hbase(main):042:0> scan 't1'
ROW                                         COLUMN+CELL
0 row(s)
Took 0.7199 seconds
```

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

原文:[HBase Shell & Commands – Usage & Starting HBase Shell](https://data-flair.training/blogs/hbase-shell-commands/)
