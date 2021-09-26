---
layout: post
author: sjf0115
title: HBase Java Admin API
date: 2019-12-29 14:37:11
tags:
  - HBase

categories: HBase
permalink: hbase-java-admin-api
---

HBase 使用 Java 语言开发，因而 HBase 原生提供了一个 Java 语言客户端。这篇文章介绍 HBase Admin API，包括创建、启用、禁用、删除表等。如果项目使用 Maven 进行依赖管理，只需添加如下依赖即可以使用 Java 客户端访问 HBase 集群：
```xml
<dependency>
    <groupId>org.apache.hbase</groupId>
    <artifactId>hbase-client</artifactId>
    <version>2.1.6</version>
</dependency>

<dependency>
    <groupId>org.apache.hbase</groupId>
    <artifactId>hbase-server</artifactId>
    <version>2.1.6</version>
</dependency>
```
> 需要注意的是，客户端版本和 HBase 版本需要保持一致，否则可能会遇到不兼容的问题。

如果要是遇到 Protobuf 等类冲突时，可以使用 HBase 提供的一个非常方便的 Jar：
```xml
<dependency>
  <groupId>org.apache.hbase</groupId>
  <artifactId>hbase-shaded-client</artifactId>
  <version>2.1.6</version>
</dependency>

<dependency>
  <groupId>org.apache.hbase</groupId>
  <artifactId>hbase-shaded-server</artifactId>
  <version>2.1.6</version>
</dependency>
```
> [HBASE-13517](https://issues.apache.org/jira/browse/HBASE-13517)

`hbase-shaded-client` 和 `hbase-shaded-server` 是在无法以其他方式解决依赖冲突的场景下使用的。在没有冲突的情况下，我们应首选：`hbase-client` 和 `hbase-server`。不要在协处理器内部使用 `hbase-shaded-server`或 `hbase-shaded-client`，因为这样可能会发生不好的事情。

### 1. 连接HBase

构建一个 Configuration 示例，该示例包含了一些客户端配置，最重要的必须配置是 HBase 集群的 ZooKeeper 地址与端口。ConnectionFactory 根据 Configuration 示例创建一个 Connection 对象，该 Connection 对象线程安全，封装了连接到 HBase 集群所需要的所有信息，如元数据缓存等。由于 Connection 开销比较大，类似于关系数据库的连接池，因此实际使用中会将该 Connection 缓存起来重复使用：

```java
public class HBaseConn {
    private static final HBaseConn INSTANCE = new HBaseConn();
    private static Configuration config;
    private static Connection conn;

    private HBaseConn() {
        try {
            if (config == null) {
                config = HBaseConfiguration.create();
                config.set("hbase.zookeeper.quorum", "127.0.0.1:2181");
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * 获取连接
     * @return
     */
    private Connection getConnection() {
        if (conn == null || conn.isClosed()) {
            try {
                conn = ConnectionFactory.createConnection(config);
            }
            catch (Exception e) {
                e.printStackTrace();
            }
        }
        return conn;
    }

    /**
     * 关闭连接
     */
    private void closeConnection() {
        if (conn != null) {
            try {
                conn.close();
            }
            catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    /**
     * 获取连接
     * @return
     */
    public static Connection create() {
        return INSTANCE.getConnection();
    }

    /**
     * 关闭连接
     */
    public static void close() {
        INSTANCE.closeConnection();
    }
}
```

### 2. 创建表

可以使用 Admin 类的 `createTable()` 方法在 HBase 中创建表。此类属于 `org.apache.hadoop.hbase.client` 包中。Admin 类需要通过 Connection 对象来获取。使用 `TableDescriptorBuilder` 来构建表名以及列族。然后使用 Admin 类的 `createTable()` 方法创建表：
```java
public static void create(String name, String... columnFamilies) throws IOException {
    Connection connection = HBaseConn.create();
    Admin admin = connection.getAdmin();

    TableName tableName =  TableName.valueOf(name);

    if (admin.tableExists(tableName)) {
        System.out.println("table " + tableName + " already exists");
        return;
    }
    TableDescriptorBuilder builder = TableDescriptorBuilder.newBuilder(tableName);
    for (String cf : columnFamilies) {
        builder.setColumnFamily(ColumnFamilyDescriptorBuilder.of(cf));
    }
    admin.createTable(builder.build());
    System.out.println("create table " + tableName + " success");

}
```
`HTableDescriptor`、`HColumnDescriptor` 在 2.0.0 版本开始废弃，并在 3.0.0 版本中移除：
```java
HBaseAdmin admin = new HBaseAdmin(conf);
HTableDescriptor tableDescriptor = new HTableDescriptor(TableName.valueOf(name));
for (String cf : columnFamilies) {
    tableDescriptor.addFamily(new HColumnDescriptor(cf));
}
admin.createTable(tableDescriptor);
```

### 3. 判断表是否存在

要使用 HBase Shell 验证表是否存在，可以使用 exist 命令。同样，使用 Java API，我们可以调用 Admin 类的 `tableExists()` 方法来验证表是否存在：
```java
public static boolean exists(Admin admin, String name) throws IOException {
    boolean result = admin.tableExists(TableName.valueOf(name));
    return result;
}
```
### 4. 禁用表

如果要禁用表，可以使用 Admin 类的 `disableTable()` 方法。在禁用表之前，我们需要先验证表是否已禁用，可以使用 Admin 类的 `isTableDisabled()` 方法来验证表是否禁用：
```java
public static void disable(String name) throws IOException {
    Connection connection = HBaseConn.create();
    Admin admin = connection.getAdmin();

    TableName tableName = TableName.valueOf(name);

    if (!admin.tableExists(tableName)) {
        System.out.println("table " + tableName + " not exists");
        return;
    }

    boolean isDisabled = admin.isTableDisabled(tableName);
    if (!isDisabled) {
        System.out.println("disable table " + name);
        admin.disableTable(tableName);
    }
}
```
### 5. 启用表

如果要启用表，可以使用 Admin 类的 `enableTable()` 方法。在启用表之前，我们需要先验证表是否已启用，可以使用 Admin 类的 `isTableEnabled()` 方法来验证表是否启用：
```java
public static void enable(String name) throws IOException {
    Connection connection = HBaseConn.create();
    Admin admin = connection.getAdmin();

    TableName tableName = TableName.valueOf(name);

    if (!admin.tableExists(tableName)) {
        System.out.println("table " + tableName + " not exists");
        return;
    }

    boolean isEnabled = admin.isTableEnabled(tableName);
    if (!isEnabled) {
        System.out.println("enable table " + name);
        admin.enableTable(tableName);
    }
}
```
### 6. 删除表

如果要删除表，可以使用 Admin 类中的 `deleteTable()` 方法删除表。在删除表之前，我们需要先验证表是否已被禁用：
```java
public static void delete(String name) throws IOException {
    Connection connection = HBaseConn.create();
    Admin admin = connection.getAdmin();

    TableName tableName = TableName.valueOf(name);

    if (!admin.tableExists(tableName)) {
        System.out.println("table " + tableName + " not exists");
        return;
    }

    // 禁用表
    admin.disableTable(tableName);
    // 删除表
    admin.deleteTable(tableName);
    System.out.println("delete table " + name);
}
```
### 7. 添加列族

如果添加列族，可以使用 Admin 类的 `addColumnFamily()` 方法将列族添加到表中。`addColumnFamily()` 方法需要提供表名以及 `ColumnFamilyDescriptor` 类对象：
```java
public static void addColumnFamily(String name, String cf) throws IOException {
    Connection connection = HBaseConn.create();
    Admin admin = connection.getAdmin();

    TableName tableName =  TableName.valueOf(name);

    if (!admin.tableExists(tableName)) {
        System.out.println("table " + tableName + " not exists");
        return;
    }

    ColumnFamilyDescriptor desc = ColumnFamilyDescriptorBuilder.of(cf);
    admin.addColumnFamily(tableName, desc);
    System.out.println("add column family " + cf);

}
```
### 8. 删除列族

如果要删除列族，可以使用 Admin 类的 `deleteColumnFamily()` 方法将列族从表中删除。`deleteColumnFamily()` 方法需要提供表名以及 `ColumnFamilyDescriptor` 类对象：
```java
public static void deleteColumnFamily(String name, String cf) throws IOException {
    Connection connection = HBaseConn.create();
    Admin admin = connection.getAdmin();

    TableName tableName =  TableName.valueOf(name);

    if (!admin.tableExists(tableName)) {
        System.out.println("table " + tableName + " not exists");
        return;
    }

    admin.deleteColumnFamily(tableName, cf.getBytes());
    System.out.println("delete column family " + cf);
}
```
### 9. 停止

实例化 Admin 类并调用 `shutdown()` 方法来停止 HBase：
```java
public static void shutdown () throws IOException {
    Connection connection = HBaseConn.create();
    Admin admin = connection.getAdmin();
    admin.shutdown();
}
```

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)
