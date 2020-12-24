---
layout: post
author: sjf0115
title: HBase 命名空间 Namespace
date: 2019-11-16 13:55:01
tags:
  - HBase

categories: HBase
permalink: hbase-namespace-commands-examples
---

### 1. 简介

命名空间是表的逻辑分组，类似于关系数据库系统中的数据库。这种抽象为多租户相关功能奠定了基础：
- 配额管理([HBASE-8410](https://issues.apache.org/jira/browse/HBASE-8410)）：限制一个命名空间可以使用的资源(Region或者Table等)。
- 命名空间安全管理([HBASE-9206](https://issues.apache.org/jira/browse/HBASE-9206))：为多租户提供另一级别的安全管理。
- RegionServer组([HBASE-6721](https://issues.apache.org/jira/browse/HBASE-6721))：一个命名空间或一张表，可以被固定到一组 RegionServer 上，从而保证了数据隔离性。

### 2. 命名空间管理

可以创建，删除或修改命名空间。命名空间成员是在表创建期间通过指定完全限定表名来确定：
```
<table namespace>:<table qualifier>
```

有如下常用的命名空间命令：
- `create_namespace`
- `describe_namespace`
- `list_namespace`
- `alter_namespace`
- `list_namespace_tables`
- `drop_namespace`

#### 2.1 创建命名空间

可以使用 `create_namespace` 命令创建命名空间：
```
hbase> create_namespace 'ns1'
```
也可以通过可选的配置字典来创建命名空间：
```
hbase> create_namespace 'ns1', {'PROPERTY_NAME'=>'PROPERTY_VALUE'}
```
#### 2.2 查看命名空间

可以使用 `describe_namespace` 命令查看命名空间：
```
hbase(main):017:0> describe_namespace 'ns1'
DESCRIPTION
{NAME => 'ns1'}
Took 0.0033 seconds
=> 1
```

#### 2.3 查看所有命名空间

可以使用 `list_namespace` 命令列出所有可用的名称空间：
```
hbase(main):019:0> list_namespace
NAMESPACE
default
hbase
ns1
3 row(s)
hbase(main):022:0> list_namespace 'ns*'
NAMESPACE
ns1
1 row(s)
```
> 支持正则表达式

#### 2.4 修改命名空间

可以使用 `alter_namespace` 命令修改已经创建的命名空间。

(1) 添加或者修改命名空间属性：
```
alter_namespace 'ns1', {METHOD => 'set', 'PROPERTY_NAME' => 'PROPERTY_VALUE'}
```
(2) 删除命名空间属性：
```
alter_namespace 'ns1', {METHOD => 'unset', NAME=>'PROPERTY_NAME'}
```

#### 2.5 在命名空间中创建表

创建命名空间后，我们可以在该命名空间上创建表。就像任何其他 RDBMS Scheme 一样，我们必须在命名空间名称后附加表名称。如果不指定命名空间，默认在 `default` 命名空间下创建表。

如下示例在 `ns1` 命名空间中创建表 `test`：
```
hbase(main):008:0> create 'ns1:test', 'f1', 'f2'
Created table ns1:test
Took 0.9023 seconds
=> Hbase::Table - ns1:test
```

#### 2.6 查看给定命名空间所有可用的表

可以使用 `list_namespace_tables` 命令列出给定命名空间下所有可用的表：
```
hbase(main):011:0> list_namespace_tables 'ns1'
TABLE
test
1 row(s)
Took 0.0078 seconds
=> ["test"]
```

#### 2.7 删除命名空间

可以使用 `drop_namespace` 命令删除表中存在的命名空间。我们只能删除空的命名空间。如果删除包含表的命名空间，必须先把该命名空间下创建的表删除。

如下所示删除包含表的命名空间：
```java
hbase(main):013:0> drop_namespace 'ns1'

ERROR: org.apache.hadoop.hbase.constraint.ConstraintException: Only empty namespaces can be removed. Namespace ns1 has 1 tables
	at org.apache.hadoop.hbase.master.procedure.DeleteNamespaceProcedure.prepareDelete(DeleteNamespaceProcedure.java:217)
	at org.apache.hadoop.hbase.master.procedure.DeleteNamespaceProcedure.executeFromState(DeleteNamespaceProcedure.java:78)
	at org.apache.hadoop.hbase.master.procedure.DeleteNamespaceProcedure.executeFromState(DeleteNamespaceProcedure.java:45)
	at org.apache.hadoop.hbase.procedure2.StateMachineProcedure.execute(StateMachineProcedure.java:189)
	at org.apache.hadoop.hbase.procedure2.Procedure.doExecute(Procedure.java:965)
	at org.apache.hadoop.hbase.procedure2.ProcedureExecutor.execProcedure(ProcedureExecutor.java:1723)
	at org.apache.hadoop.hbase.procedure2.ProcedureExecutor.executeProcedure(ProcedureExecutor.java:1462)
	at org.apache.hadoop.hbase.procedure2.ProcedureExecutor.access$1200(ProcedureExecutor.java:78)
	at org.apache.hadoop.hbase.procedure2.ProcedureExecutor$WorkerThread.run(ProcedureExecutor.java:2039)
```
如下所示删除一个空的命名空间：
```
hbase(main):014:0> create_namespace 'ns2'
Took 0.2518 seconds
hbase(main):015:0> drop_namespace 'ns2'
Took 0.2303 second
```

### 3. 内置命名空间

HBase 中有两个内置的特殊命名空间：
- `hbase`：系统命名空间，包含 HBase 内部表。
- `default`：如果在创建表时没有显式指定命名空间，默认会在此命名空间创建表。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

参考:[Hbase Namespace Commands and Examples](http://dwgeek.com/hbase-namespace-commands-examples.html/)
