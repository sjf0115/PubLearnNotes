这篇文章介绍了HiveServer2支持的不同客户端。

==版本==

从Hive 0.11版本引入

### 1. Beeline 命令行Shell

### 2. JDBC

HiveServer2具有JDBC驱动程序。 它支持嵌入式和远程两种方式来访问HiveServer2。实际生产环境中建议使用远程HiveServer2模式，因为它更安全，直接访问HDFS/metastore不需要授予用户权限(doesn't require direct HDFS/metastore access to be granted for users.)。

#### 2.1 连接URL

##### 2.1.1 连接URL格式

HiveServer2 URL是一个具有以下语法的字符串：

```
jdbc:hive2://<host1>:<port1>,<host2>:<port2>/dbName;initFile=<file>;sess_var_list?hive_conf_list#hive_var_list
```
==说明==

- `<host1>:<port1>,<host2>:<port2>`是要连接的服务器实例或者以逗号分隔的服务器实例列表(如果启用了动态服务发现)。如果为空，则将使用嵌入式服务器。
- `dbName`是初始数据库的名称。
- `file`是初始化脚本文件的路径(Hive 2.2.0及更高版本)。这个脚本文件是用SQL语句编写的，它将在连接后自动执行。此选项可以为空。
- `sess_var_list`是以分号分隔的会话变量`key=value`键值对列表（例如，user = foo; password = bar）。
- `hive_conf_list`是本次会话以分号分割的Hive配置变量的`key=value`键值对列表
- `hive_var_list`是本次会话以分号分割的Hive变量的`key=value`键值对列表。

##### 2.1.2 远程或嵌入式模式的连接URL

JDBC连接URL格式具有`jdbc：hive2：//`前缀，Driver类为`org.apache.hive.jdbc.HiveDriver`。 请注意，这与旧的[HiveServer](https://cwiki.apache.org/confluence/display/Hive/HiveServer)不同。

(1) 对于远程服务器，URL格式为
```
jdbc:hive2://<host>:<port>/<db>;initFile=<file>
```
HiveServer2的默认端口为10000

(2) 对于嵌入式服务器，URL格式为
```
jdbc:hive2:///;initFile=<file>
```
无主机或端口

Hive 2.2.0及更高版本中提供了initFile选项。

##### 2.1.3 Http模式下的连接URL

JDBC连接URL:
```
jdbc:hive2://<host>:<port>/<db>;transportMode=http;httpPath=<http_endpoint>
```
==说明==

- `http_endpoint`是在hive-site.xml中配置的相应HTTP端点。默认值是cliservice。HTTP传输模式的默认端口为10001。

==备注==

在0.14之前的版本中，这些参数分别被称为`hive.server2.transport.mode`和`hive.server2.thrift.http.path`，并且是`hive_conf_list`的一部分。这些版本已被弃用，有利于新版本（它们是sess_var_list的一部分），但是现在仍然继续工作。

##### 2.1.4 启用SSL时的连接URL

JDBC连接URL:
```
jdbc:hive2://<host>:<port>/<db>;ssl=true;sslTrustStore=<trust_store_path>;trustStorePassword=<trust_store_password>
```

==说明==

- `trust_store_path`是客户端的信任库(truststore)文件所在的路径。
- `trust_store_password`是访问信任库的密码。

在HTTP模式下:
```
jdbc:hive2://<host>:<port>/<db>;ssl=true;sslTrustStore=<trust_store_path>;trustStorePassword=<trust_store_password>;transportMode=http;httpPath=<http_endpoint>
```

##### 2.1.5 启动ZooKeeper服务发现时的连接URL

在Hive 0.14.0版本引入的基于ZooKeeper的服务发现可实现HiveServer2的高可用性和滚动升级`rolling upgrade`。为了充分利用这些特性，JDBC URL需要指定`zookeeper quorum`。

##### 2.1.6 Named Connection URLs

##### 2.1.7  Reconnecting

##### 2.1.8 使用hive-site.xml自动连接到HiveServer2

从Hive 2.2.0 开始，BeeLine增加支持如果classpath中存在`hive-site.xml`会自动生成基于`hive-site.xml`中的配置属性的连接url和另外一个用户配置文件。并非所有的url属性都可以从`hive-site.xml`派生，因此为了使用此功能，用户必须创建一个名为`beeline-hs2-connection.xml`的配置文件，该配置文件是Hadoop xml格式文件。此文件用于为连接URL提供用户特定的连接属性。BeeLine在`${user.home}/.beeline/`（基于Unix的操作系统）或`${user.home}\beeline\`目录（在Windows的情况下）查找此配置文件。如果在以上位置找不到该文件，BeeLine将在`${HIVE_CONF_DIR}`位置和`/etc/hive/conf`（在Hive 2.2.0中修改为`/etc/conf/hive`）中查找。一旦找到该文件，BeeLine将使用`beeline-hs2-connection.xml`与classpath中的`hive-site.xml`一起确定连接URL。

在`beeline-hs2-connection.xml`中的url连接属性必须具有`beeline.hs2.connection`前缀，后跟url属性名称。 例如，为了提供属性ssl，`beeline-hs2-connection.xml`中的属性键应为`beeline.hs2.connection.ssl`。以下示例`beeline.hs2.connection.xml`为BeeLine连接url提供了用户和密码。在这种情况下，其他属性如HS2主机名和端口信息，kerberos配置属性，SSL属性，传输模式等使用classpath中的`hive-site.xml`来获取。如果密码为空，请删除`beeline.hs2.connection.password`属性。在大多数情况下，`beeline-hs2-connection.xml`中的以下配置值和classpath中正确的`hive-site.xml`足以连接到HiveServer2。

```xml
<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
<property>
  <name>beeline.hs2.connection.user</name>
  <value>hive</value>
</property>
<property>
  <name>beeline.hs2.connection.password</name>
  <value>hive</value>
</property>
</configuration>
```
如果属性在`beeline-hs2-connection.xml`和`hive-site.xml`中存在的情况下，从`beeline-hs2-connection.xml`派生的属性值优先。例如在下面的`beeline-hs2-connection.xml`文件中，为在Kerberos启用的环境中，需要为BeeLine连接提供principal属性值。在这种情况下，就连接URL而言,`beeline.hs2.connection.principal`的属性值将覆盖从`hive-site.xml`配置文件的`HiveConf.ConfVars.HIVE_SERVER2_KERBEROS_PRINCIPAL`的值。

```xml
<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
<property>
  <name>beeline.hs2.connection.hosts</name>
  <value>localhost:10000</value>
</property>
<property>
  <name>beeline.hs2.connection.principal</name>
  <value>hive/dummy-hostname@domain.com</value>
</property>
</configuration>
```

在属性`beeline.hs2.connection.hosts`,`beeline.hs2.connection.hiveconf`和`beeline.hs2.connection.hivevar`的属性值为以逗号分隔的列表的情况下，例如，以下`beeline-hs2-connection.xml`以逗号分隔格式提供hiveconf和hivevar值。
```xml
<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
<property>
  <name>beeline.hs2.connection.user</name>
  <value>hive</value>
</property>
<property>
  <name>beeline.hs2.connection.hiveconf</name>
  <value>hive.cli.print.current.db=true, hive.cli.print.header=true</value>
</property>
<property>
  <name>beeline.hs2.connection.hivevar</name>
  <value>testVarName1=value1, testVarName2=value2</value>
</property>
</configuration>
```
当`beeline-hs2-connection.xml`存在，以及没有其他参数提供时，BeeLine自动连接到使用配置文件生成的URL。当提供连接参数（-u，-n或-p）时，BeeLine使用这些参数，不使用`beeline-hs2-connection.xml`p配置文件自动连接。删除或重命名`beeline-hs2-connection.xml`禁用此功能。

##### 2.1.9 使用JDBC

加载HiveServer2 JDBC驱动程序。 从1.2.0开始，应用程序不再需要使用`Class.forName()`显式加载JDBC驱动程序:
```java
Class.forName("org.apache.hive.jdbc.HiveDriver");
```
通过使用JDBC驱动程序创建一个Connection对象来连接到数据库:
```java
Connection cnct = DriverManager.getConnection("jdbc:hive2://<host>:<port>", "<user>", "<password>");
```
默认的端口号为10000.在非安全配置中，为运行查询指定一个`<user>`。 在非安全模式下，`<password>`字段值被忽略:
```java
Connection cnct = DriverManager.getConnection("jdbc:hive2://<host>:<port>", "<user>", "");
```
通过创建Statement对象并使用其executeQuery（）方法将SQL提交到数据库:
```java
Statement stmt = cnct.createStatement();
ResultSet rset = stmt.executeQuery("SELECT foo FROM bar");
```
如果有必要，可以结果集进行处理。

Example:
```java
import java.sql.SQLException;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import java.sql.DriverManager;

public class HiveJdbcClient {
  private static String driverName = "org.apache.hive.jdbc.HiveDriver";

  /**
   * @param args
   * @throws SQLException
   */
  public static void main(String[] args) throws SQLException {
      try {
      Class.forName(driverName);
    } catch (ClassNotFoundException e) {
      // TODO Auto-generated catch block
      e.printStackTrace();
      System.exit(1);
    }
    //replace "hive" here with the name of the user the queries should run as
    Connection con = DriverManager.getConnection("jdbc:hive2://localhost:10000/default", "hive", "");
    Statement stmt = con.createStatement();
    String tableName = "testHiveDriverTable";
    stmt.execute("drop table if exists " + tableName);
    stmt.execute("create table " + tableName + " (key int, value string)");
    // show tables
    String sql = "show tables '" + tableName + "'";
    System.out.println("Running: " + sql);
    ResultSet res = stmt.executeQuery(sql);
    if (res.next()) {
      System.out.println(res.getString(1));
    }
       // describe table
    sql = "describe " + tableName;
    System.out.println("Running: " + sql);
    res = stmt.executeQuery(sql);
    while (res.next()) {
      System.out.println(res.getString(1) + "\t" + res.getString(2));
    }

    // load data into table
    // NOTE: filepath has to be local to the hive server
    // NOTE: /tmp/a.txt is a ctrl-A separated file with two fields per line
    String filepath = "/tmp/a.txt";
    sql = "load data local inpath '" + filepath + "' into table " + tableName;
    System.out.println("Running: " + sql);
    stmt.execute(sql);

    // select * query
    sql = "select * from " + tableName;
    System.out.println("Running: " + sql);
    res = stmt.executeQuery(sql);
    while (res.next()) {
      System.out.println(String.valueOf(res.getInt(1)) + "\t" + res.getString(2));
    }

    // regular hive query
    sql = "select count(1) from " + tableName;
    System.out.println("Running: " + sql);
    res = stmt.executeQuery(sql);
    while (res.next()) {
      System.out.println(res.getString(1));
    }
  }
}
```
运行：
```
# Then on the command-line
$ javac HiveJdbcClient.java

# To run the program using remote hiveserver in non-kerberos mode, we need the following jars in the classpath
# from hive/build/dist/lib
#     hive-jdbc*.jar
#     hive-service*.jar
#     libfb303-0.9.0.jar
#     libthrift-0.9.0.jar
#     log4j-1.2.16.jar
#     slf4j-api-1.6.1.jar
#     slf4j-log4j12-1.6.1.jar
#     commons-logging-1.0.4.jar
#
#
# To run the program using kerberos secure mode, we need the following jars in the classpath
#     hive-exec*.jar
#     commons-configuration-1.6.jar (This is not needed with Hadoop 2.6.x and later).
#  and from hadoop
#     hadoop-core*.jar (use hadoop-common*.jar for Hadoop 2.x)
#
# To run the program in embedded mode, we need the following additional jars in the classpath
# from hive/build/dist/lib
#     hive-exec*.jar
#     hive-metastore*.jar
#     antlr-runtime-3.0.1.jar
#     derby.jar
#     jdo2-api-2.1.jar
#     jpox-core-1.2.2.jar
#     jpox-rdbms-1.2.2.jar
# and from hadoop/build
#     hadoop-core*.jar
# as well as hive/build/dist/conf, any HIVE_AUX_JARS_PATH set,
# and hadoop jars necessary to run MR jobs (eg lzo codec)

$ java -cp $CLASSPATH HiveJdbcClient
```
或者，可以运行以下bash脚本，这将在调用客户端之前发送数据文件并构建类路径。该脚本还添加了在嵌入式模式下使用HiveServer2所需的所有其他jar:
```Shell
#!/bin/bash
HADOOP_HOME=/your/path/to/hadoop
HIVE_HOME=/your/path/to/hive

echo -e '1\x01foo' > /tmp/a.txt
echo -e '2\x01bar' >> /tmp/a.txt

HADOOP_CORE=$(ls $HADOOP_HOME/hadoop-core*.jar)
CLASSPATH=.:$HIVE_HOME/conf:$(hadoop classpath)

for i in ${HIVE_HOME}/lib/*.jar ; do
    CLASSPATH=$CLASSPATH:$i
done

java -cp $CLASSPATH HiveJdbcClient
```

#### 2.2 JDBC Data Types

#### 2.3 DBC Client Setup for a Secure Cluster


### 3. Python Client

### 4. Ruby Client
