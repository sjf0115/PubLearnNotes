---
layout: post
author: sjf0115
title: HBase Java Client API
date: 2020-01-11 20:00:00
tags:
  - HBase

categories: HBase
permalink: hbase-java-client-api
---

### 1. 概述

在这篇文章中，我们看一下 HBase Java 客户端 API 如何使用。HBase 用 Java 编写，并提供 Java API 与之通信。客户端 API 提供了DDL（数据定义语言）和DML（数据操作语言）语义，这与我们在关系数据库中的语义非常相似。因此，我们学习一下如何使用 HBase 的 Java 客户端 API 对 HBase 表进行 CRUD 操作。

### 2. Put

使用 Put 向表中插入数据。需要首先实例化 Connection 类，并通过 Connection 实例来实例化 Table 类：
```java
Table getTable(TableName tableName)
```
插入数据需要实例化 Put 类，创建 Put 实例时用户需要提供一个行键 RowKey：
```java
Put(byte[] row)
Put(byte[] row, long ts)
```
这两个 Put 实例都通过 row 参数指定了要插入的行。创建 Put 实例之后，就可以向该实例添加数据，添加数据方法如下：
```java
Put addColumn(byte[] family, byte[] qualifier, byte[] value)
Put addColumn(byte[] family, byte[] qualifier, long ts, byte[] value)
Put addColumn(byte[] family, ByteBuffer qualifier, long ts, ByteBuffer value)
```
每一次调用 `addColumn()` 方法都可以添加一列数据，如果指定一个时间戳参数，就能形成一个数据单元格。如果不指定时间戳，Put 实例会使用来自构造函数的可选时间戳参数，如果用户在构造 Put 实例时也没有指定时间戳，则由 RegionServer 设定。

最后使用 Table 的 `put()` 方法向 HBase 中存储数据，使用如下方法进行调用：
```java
void put(Put put) throws IOException
```
如下代码所示向 HBase 表中插入单行数据：
```java
Connection connection = HBaseConn.create();
Table table = connection.getTable(TableName.valueOf("user"));
Put put = new Put(Bytes.toBytes("Lucy"));
put.addColumn(Bytes.toBytes("info"), Bytes.toBytes("age"), Bytes.toBytes("28"));
table.put(put);
table.close();
```
> [HBaseConn](https://github.com/sjf0115/hbase-example/blob/master/src/main/java/com/hbase/example/utils/HBaseConn.java) 类是自定义的工具类，可以返回 Connection 类。

客户端 API 可以插入单个 Put 实例，同时也有批量处理操作的高级特性。调用形式如下：
```java
void put(List<Put> puts) throws IOException
```
用户需要建立一个 Put 实例的列表，然后调用以列表为参数的 `put()` 方法。如下代码所示向 HBase 表中插入多行数据：
```java
Connection connection = HBaseConn.create();
Table table = connection.getTable(TableName.valueOf("user"));

List<String> rowKeyList = Lists.newArrayList("Tom", "Kary", "Ford");
List<String> ageList = Lists.newArrayList("15", "43", "21");
List<Put> putList = Lists.newArrayList();
for (int index = 0;index < rowKeyList.size();index ++) {
    String rowKey = rowKeyList.get(index);
    String age = ageList.get(index);
    Put put = new Put(Bytes.toBytes(rowKey));
    put.addColumn(Bytes.toBytes("info"), Bytes.toBytes("age"), Bytes.toBytes(age));
    putList.add(put);
}
table.put(putList);
table.close();
```

### 3. Get

下面我们介绍根据客户端 API 查询已存储在 HBase 表中的数据。Table 类的 `get()` 方法可以从 HBase 表中读取数据。`get()` 方法需要 Get 类的实例。与 Put 类似，需要首先实例化 Connection 类，通过 Connection 实例来实例化 Table 类。

查询数据需要实例化 Get 类，创建 Get 实例时用户需要提供一个行键 RowKey：
```java
Get(byte[] row)
Get(byte[] row, int rowOffset, int rowLength)
```
这两个 Get 实例都通过 row 参数指定了要查询的行。与 Put 操作一样，可以用多种标准筛选目标数据，也可以指定精确的坐标获取单元格的数据：
```java
Get addFamily(byte[] family)
Get addColumn(byte[] family, byte[] qualifier)
Get setTimestamp(long timestamp)
Get setTimeRange(long minStamp, long maxStamp)
Get setFilter(Filter filter)
Get readVersions(int versions)
Get readAllVersions()
```
`addFamily()` 方法限制 `get()` 方法只能获取一个指定的列族，要获取多个列族需要多次调用。`addColumn()` 方法可以指定 `get()` 方法获取哪一列的数据。`setTimestamp()` 方法可以设定要获取的数据的时间戳，或者可以通过 `setTimeRange()` 方法设定一个时间段来获取某个时间戳段内的数据。如果用户没有设定时间戳，默认返回最新的匹配版本。

当用户使用 `get()` 方法获取数据时，HBase 返回的结果包含所有匹配的单元格数据，这些数据被封装在一个 Result 实例中返回给用户。用他提供的方法，可以从服务端获取匹配指定行的特定返回值，包括列族、列限定符以及时间戳等。如下代码所示从 HBase 表中查询单行数据：
```java
Connection connection = HBaseConn.create();
Table table = connection.getTable(TableName.valueOf("user"));
Get get = new Get(Bytes.toBytes("Lucy"));
Result result = table.get(get);
byte[] value = result.getValue(Bytes.toBytes("info"), Bytes.toBytes("age"));
System.out.println(Bytes.toString(value));
```
客户端 API 可以一次查询一行数据，同时也有批量处理操作的高级特性，用户可以一次请求获取多行数据。调用形式如下：
```java
Result[] get(List<Get> gets) throws IOException
```
> 实际上，请求有可能被发往多个不同的服务器，但这部分逻辑已经被封装起来，因此对于客户端代码来说，还是表现为一次请求。

用户需要建立一个 Get 实例的列表，然后调用以列表为参数的 `get()` 方法，并返回一个 Result 数组。如下代码所示向 HBase 表中查询多行数据：
```java
Connection connection = HBaseConn.create();
Table table = connection.getTable(TableName.valueOf("user"));
List<String> rowKeyList = Lists.newArrayList("Lucy", "Lily");
List<Get> getList = Lists.newArrayList();
for (int index = 0;index < rowKeyList.size();index ++) {
    String rowKey = rowKeyList.get(index);
    Get get = new Get(Bytes.toBytes(rowKey));
    getList.add(get);
}
Result[] results = table.get(getList);
for (Result result : results) {
    byte[] ageValue = result.getValue(Bytes.toBytes("info"), Bytes.toBytes("age"));
    System.out.println(Bytes.toString(ageValue));
}
table.close();
```

### 4. Delete

下面我们介绍使用客户端 API 删除已存储数据的方法。Table 类的 `delete()` 方法可以从 HBase 表中删除数据。`delete()` 方法需要 Delete 类的实例。与 Put、Get 类似，都需要首先实例化 Connection 类，通过 Connection 实例来实例化 Table 类。

与前面讲的 `get()` 方法和 `put()` 方法一样，删除数据用户必须先创建一个 Delete 实例，并需要提供要删除行的行键 RowKey：
```java
Delete(byte[] row)
Delete(byte[] row, long timestamp)
Delete(byte[] row, int rowOffset, int rowLength)
Delete(byte[] row, int rowOffset, int rowLength, long timestamp)
```
这几个 Delete 实例都通过 row 参数指定了要删除的行。我们最好缩小要删除的给定行中涉及的数据范围，可以使用下列方法：
```java
Delete addFamily(byte[] family)
Delete addFamily(byte[] family, long timestamp)
Delete addFamilyVersion(byte [] family, long timestamp)
Delete addColumns(byte[] family, byte[] qualifier)
Delete addColumns(byte[] family, byte[] qualifier, long timestamp)
Delete addColumn(byte[] family, byte[] qualifier)
Delete addColumn(byte[] family, byte[] qualifier, long timestamp)
```
`addFamily()` 方法可以删除指定列族下所有的列(包括所有版本)，我们也可以指定一个时间戳，触发针对单元格数据版本的过滤。从给定列族下的所有列中删除与给定时间戳相匹配的版本以及更旧版本的列。`addFamilyVersion()` 与 `addFamily()` 方法不同的是，只会删除与时间戳相匹配的版本的所有列。
`addColumns()` 方法只作用于特定的一列，如果用户没有指定时间戳，这个方法会删除给定列的所有版本，如果指定了时间戳，从给定列中删除与给定时间戳相匹配的版本以及更旧的版本。`addColumn()` 跟 `addColumns()` 方法一样，也操作一个具体的列，但是只删除最新版本，保留旧版本。如果指定了时间戳，从给定列中删除与给定时间戳相匹配的版本。如下代码所示从 HBase 表中删除单行或者单列数据：
```java
// 删除指定行数据
Connection connection = HBaseConn.create();
Table table = connection.getTable(TableName.valueOf("user"));
Delete delete = new Delete(Bytes.toBytes("Lucy"));
table.delete(delete);

// 删除指定列数据
Connection connection = HBaseConn.create();
Table table = connection.getTable(TableName.valueOf("user"));
Delete delete = new Delete(Bytes.toBytes("Lucy"));
delete.addColumn(Bytes.toBytes("info"), Bytes.toBytes("age"));
table.delete(delete);
```
客户端 API 可以一次删除一行数据，同时也有批量处理操作的高级特性，用户可以一次请求删除多行数据。调用形式如下：
```java
void delete(List<Delete> deletes) throws IOException
```
用户需要建立一个 Delete 实例的列表，然后调用以列表为参数的 `delete()` 方法。如下代码所示向 HBase 表中删除多行数据：
```java
Connection connection = HBaseConn.create();
Table table = connection.getTable(TableName.valueOf("user"));

List<String> rowKeyList = Lists.newArrayList("Lucy", "Lily");
List<Delete> deleteList = Lists.newArrayList();
for (int index = 0;index < rowKeyList.size();index ++) {
    String rowKey = rowKeyList.get(index);
    Delete delete = new Delete(Bytes.toBytes(rowKey));
    deleteList.add(delete);
}
table.delete(deleteList);
table.close();
```

### 5. Scan

在介绍基本的 CRUD 类型操作之后，现在来看一下 Scan 操作，类似于数据库系统中的游标，并利用到了 HBase 提供的底层顺序存储的数据结构。Scan 的工作类似于迭代器，所以用户无需调用 `scan()` 方法创建实例，只需要调用 Table 的 `getScanner()` 方法，这个方法在返回真正的扫描器实例的同时，用户可以使用它迭代获取数据。与 Put、Get、Delete 类似，需要首先实例化 Connection 类，通过 Connection 实例来实例化 Table 类。与前面讲过的 `get()`、`put()` 以及 `delete()` 方法一样，用户必须先创建一个 Scan 实例：
```java
Scan()
Scan(Get get)
```
创建 Scan 实例之后，用户可能还要给它增加很多限制条件。这种情况下，用户仍然可以使用空白参数的扫描，读取整个表格，包括所有的列族以及它们的所有列。可以使用多种方法限制所要读取的数据：
```java
Scan addFamily(byte[] family)
Scan addColumn(byte[] family, byte[] qualifier)
Scan setTimestamp(long timestamp)
Scan setTimeRange(long minStamp, long maxStamp)
Scan withStartRow(byte[] startRow)
Scan withStopRow(byte[] stopRow)
Scan setFilter(Filter filter)
```
上述有几个方法于 Get 类相似的功能：可以使用 `addFamily` 方法限制返回数据的列族，或者通过 `addColumn` 方法限制返回的列。另外用户可以通过 `setTimestamp` 方法设置时间戳或者通过 `setTimeRange` 设置时间范围，进一步对结果进行限制。还可以使用 `withStartRow`、`withStopRow`、`setFilter` 进一步限定返回的数据。一旦设置好了 Scan 实例，就可以调用 Table 的 `getScanner()` 方法获取用于检索数据的 ResultScanner 实例。

Scan 操作不会通过一次 RPC 请求返回所有匹配的行，而是一行为单位进行返回。ResultScanner 把扫描操作转换为类似的 get 操作，它将每一行数据封装成一个 Result 实例，并将所有的 Result 实例放入一个迭代器中：
```java
Connection connection = HBaseConn.create();
Table table = connection.getTable(TableName.valueOf("user"));
Scan scan = new Scan();
ResultScanner scanner = table.getScanner(scan);
for (Result result = scanner.next(); result != null; result = scanner.next()) {
    byte[] rowBytes = result.getRow();
    byte[] sexBytes = result.getValue(Bytes.toBytes("info"), Bytes.toBytes("sex"));
    byte[] ageBytes = result.getValue(Bytes.toBytes("info"), Bytes.toBytes("age"));
    byte[] addressBytes = result.getValue(Bytes.toBytes("info"), Bytes.toBytes("address"));
    String rowKey = Bytes.toString(rowBytes);
    String sex = Bytes.toString(sexBytes);
    String age = Bytes.toString(ageBytes);
    String address = Bytes.toString(addressBytes);
    System.out.println("rowKey: " + rowKey + ", cf: " + cf + ", sex: " + sex + ", age: " + age + ", address: " + address);
}
scanner.close();
```

欢迎关注我的公众号和博客：

![](https://mmbiz.qpic.cn/mmbiz_jpg/nKovjAe6LrqPP36RWGmwXAHAUPcg48ibQzRb82UubkaEj0K8CANwdefia4cJZK3B0jiavicU35I08Z8lbgeFzibJofw/0?wx_fmt=jpeg)
