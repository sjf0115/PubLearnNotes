Presto 提供了通过 JDBC 访问集群的方式，使用者可以在 Java 程序中通过 Presto 的 JDBC 驱动连接到 Presto 集群，从而进行数据查询和分析。

### 1. Maven

可以在 pom 文件中加入如下配置引入 Presto JDBC driver：
```
<dependency>
    <groupId>com.facebook.presto</groupId>
    <artifactId>presto-jdbc</artifactId>
    <version>0.231.1</version>
</dependency>
```

### 2. 连接字串

可以使用如下格式的连接字串：
```
jdbc:presto://<COORDINATOR>:<PORT>/[CATALOG]/[SCHEMA]
```

例如：
```
# 连接数据库，使用Catalog和Schema
jdbc:presto://localhost:8001
# 连接数据库，使用Catalog(hive)和Schema           
jdbc:presto://localhost:8001/hive
# 连接数据库，使用Catalog(hive)和Schema(default)        
jdbc:presto://localhost:8001/hive/default  
```
### 3. 连接参数

Presto JDBC driver 支持很多参数，这些参数既可以通过 Properties 对象传入，也可以通过 URL 传入参数，这两种方式是等价的。

通过 Properties 对象传入示例：
```java
String url = "jdbc:presto://localhost:8001/hive/default";
Properties properties = new Properties();
properties.setProperty("user", "root");
Connection connection = DriverManager.getConnection(url, properties);
```
通过 URL 传入参数示例：
```java
String url = "jdbc:presto://localhost:8001/hive/default?user=root";
Connection connection = DriverManager.getConnection(url);
```
各参数说明如下：







...
