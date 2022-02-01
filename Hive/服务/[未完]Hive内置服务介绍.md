
### 1. Hive服务

> Hive 2.3.7 版本

Hive CLI 是我们经常用到的一个 Hive 服务，也是 Hive 命令默认的服务。例如，我们直接运行 `hive` 命令：
![](1)

除了 Hive CLI 之外，Hive 还内置了很多的服务，如果你不知道 Hive 内部有多少服务，可以用如下命令来查看：
```shell
hive --service help
```
![](2)

我们可以看到 Service List 展示了 Hive 目前支持的服务列表：
- beeline
- cli
- hiveserver2
- jar
- metastore
- schemaTool
- lineage
- version
- hplsql
- hbaseimport
- hbaseschematool
- help
- hiveburninclient  
- cleardanglingscratchdir
- llap
- llapdump
- llapstatus
- metatool
- orcfiledump
- rcfilecat  

下面我们介绍一些最有用的服务：
- CLI：Hive的命令行接口。这是默认的服务。
- HiveServer2：让 Hive 以提供 Thrift 服务的服务器形式来运行，可以用不同语言编写的客户端进行访问。HiveServer2 在支持认证和多用户并发方面比原始的 HiveServer 有很大的改进。使用 Thrift、JDBC 和 ODBC 连接器的客户端需要运行 Hive 服务器来和 Hive 进行通信。通过设置 `hive.server2.thrift.port` 配置属性来指明服务器监听的端口号（默认呢为1000）。
- Beeline：以嵌入方式工作的 Hive 命令行接口（类似于常规的 CLI），或者使用 JDBC 连接到一个 HiveServer2 进程。
- HWI：Hive 的 Web 接口。在没有安装任何客户端软件的情况下，这个简单的 Web 接口可以代替 CLI。另外，HUE 是一个功能更全面d的 Hadoop Web 接口，其中包括运行 Hive 查询和浏览 Hive metastore 的应用程序。
- Jar：与 Hadoop jar 等价。这是运行类路径中同时包含 Hadoop 和 Hive 类 Java 应用程序的简便方法。
- MetaSote：默认情况下，metaStore 和 Hive 服务运行在同一个进程里。使用这个服务，可以让 metaStore 作为一个单独(远程)进程运行。通过设置 MEATASTORE_PORT 环境变量（或者使用-p命令行选项）可以指定服务器监听的端口号（默认为9083）。

### 2. HiveServer2

### 3. MetaStore





#### 3.3 远程MetaStore









参考：
- [Hive的几种内置服务](https://www.iteblog.com/archives/957.html)
- [HiveServer2(Spark ThriftServer)自定义权限认证](https://www.iteblog.com/archives/2318.html)
- [Hive CLI和Beeline的区别](https://mp.weixin.qq.com/s/49nLaa3eaSgyjRul0Usq7Q)
