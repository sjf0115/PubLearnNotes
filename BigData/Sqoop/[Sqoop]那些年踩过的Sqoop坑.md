#### 1. Unsupported major.minor version 52.0
```
xiaosi@Qunar:/opt/sqoop-1.4.6/bin$ sqoop list-databases --connect jdbc:mysql://localhost:3306 --username root --password root
Warning: /opt/sqoop-1.4.6/../hbase does not exist! HBase imports will fail.
Please set $HBASE_HOME to the root of your HBase installation.
Warning: /opt/sqoop-1.4.6/../hcatalog does not exist! HCatalog jobs will fail.
Please set $HCAT_HOME to the root of your HCatalog installation.
Warning: /opt/sqoop-1.4.6/../accumulo does not exist! Accumulo imports will fail.
Please set $ACCUMULO_HOME to the root of your Accumulo installation.
16/10/08 15:11:44 INFO sqoop.Sqoop: Running Sqoop version: 1.4.6
16/10/08 15:11:44 WARN tool.BaseSqoopTool: Setting your password on the command-line is insecure. Consider using -P instead.
16/10/08 15:11:44 INFO manager.MySQLManager: Preparing to use a MySQL streaming resultset.
Exception in thread "main" java.lang.UnsupportedClassVersionError: com/mysql/jdbc/Driver : Unsupported major.minor version 52.0
	at java.lang.ClassLoader.defineClass1(Native Method)
	at java.lang.ClassLoader.defineClass(ClassLoader.java:792)
	at java.security.SecureClassLoader.defineClass(SecureClassLoader.java:142)
	at java.net.URLClassLoader.defineClass(URLClassLoader.java:449)
	at java.net.URLClassLoader.access$100(URLClassLoader.java:71)
	at java.net.URLClassLoader$1.run(URLClassLoader.java:361)
	at java.net.URLClassLoader$1.run(URLClassLoader.java:355)
	at java.security.AccessController.doPrivileged(Native Method)
	at java.net.URLClassLoader.findClass(URLClassLoader.java:354)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:424)
	at sun.misc.Launcher$AppClassLoader.loadClass(Launcher.java:308)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:357)
	at java.lang.Class.forName0(Native Method)
	at java.lang.Class.forName(Class.java:190)
	at org.apache.sqoop.manager.SqlManager.makeConnection(SqlManager.java:854)
	at org.apache.sqoop.manager.GenericJdbcManager.getConnection(GenericJdbcManager.java:52)
	at org.apache.sqoop.manager.CatalogQueryManager.listDatabases(CatalogQueryManager.java:57)
	at org.apache.sqoop.tool.ListDatabasesTool.run(ListDatabasesTool.java:49)
	at org.apache.sqoop.Sqoop.run(Sqoop.java:143)
	at org.apache.hadoop.util.ToolRunner.run(ToolRunner.java:70)
	at org.apache.sqoop.Sqoop.runSqoop(Sqoop.java:179)
	at org.apache.sqoop.Sqoop.runTool(Sqoop.java:218)
	at org.apache.sqoop.Sqoop.runTool(Sqoop.java:227)
	at org.apache.sqoop.Sqoop.main(Sqoop.java:236)
```	
出现上述问题，可能是因为JDK版本问题，或者是mysql 驱动版本问题，在我这是mysql 驱动版本问题。原先我使用的是当前最先版本mysql-connector-java-6.0.4，转换为mysql-connector-java-5.1.38版本即可。

再次尝试：
```
xiaosi@Qunar:/opt/sqoop-1.4.6/bin$ sqoop list-databases --connect jdbc:mysql://localhost:3306 --username root -password root
Warning: /opt/sqoop-1.4.6/../hbase does not exist! HBase imports will fail.
Please set $HBASE_HOME to the root of your HBase installation.
Warning: /opt/sqoop-1.4.6/../hcatalog does not exist! HCatalog jobs will fail.
Please set $HCAT_HOME to the root of your HCatalog installation.
Warning: /opt/sqoop-1.4.6/../accumulo does not exist! Accumulo imports will fail.
Please set $ACCUMULO_HOME to the root of your Accumulo installation.
16/10/08 15:43:03 INFO sqoop.Sqoop: Running Sqoop version: 1.4.6
16/10/08 15:43:03 WARN tool.BaseSqoopTool: Setting your password on the command-line is insecure. Consider using -P instead.
16/10/08 15:43:03 INFO manager.MySQLManager: Preparing to use a MySQL streaming resultset.
information_schema
hive_db
mysql
performance_schema
phpmyadmin
test
```
#### 2. must contain '$CONDITIONS' in WHERE clause

从查询结果中导入数据，使用如下命令时，会报错：

```
sqoop import --connect jdbc:mysql://localhost:3306/test -target-dir /user/xiaosi/data/ -query "select * from order_info where business = 'flight'" -m 1 --username root -P
```
报错信息：
```
16/11/14 10:43:45 INFO sqoop.Sqoop: Running Sqoop version: 1.4.6
Enter password: 
16/11/14 10:43:47 INFO manager.MySQLManager: Preparing to use a MySQL streaming resultset.
16/11/14 10:43:47 INFO tool.CodeGenTool: Beginning code generation
16/11/14 10:43:47 ERROR tool.ImportTool: Encountered IOException running import job: java.io.IOException: Query [select * from order_info where business = 'flight'] must contain '$CONDITIONS' in WHERE clause.
	at org.apache.sqoop.manager.ConnManager.getColumnTypes(ConnManager.java:300)
	at org.apache.sqoop.orm.ClassWriter.getColumnTypes(ClassWriter.java:1833)
	at org.apache.sqoop.orm.ClassWriter.generate(ClassWriter.java:1645)
	at org.apache.sqoop.tool.CodeGenTool.generateORM(CodeGenTool.java:107)
	at org.apache.sqoop.tool.ImportTool.importTable(ImportTool.java:478)
	at org.apache.sqoop.tool.ImportTool.run(ImportTool.java:605)
	at org.apache.sqoop.Sqoop.run(Sqoop.java:143)
	at org.apache.hadoop.util.ToolRunner.run(ToolRunner.java:70)
	at org.apache.sqoop.Sqoop.runSqoop(Sqoop.java:179)
	at org.apache.sqoop.Sqoop.runTool(Sqoop.java:218)
	at org.apache.sqoop.Sqoop.runTool(Sqoop.java:227)
	at org.apache.sqoop.Sqoop.main(Sqoop.java:236)
```	
报错原因：

从查询结果中导入数据，使用-query参数时必须指定-target-dir，同时在查询语句中一定要有where条件且在where条件中需要包含$CONDITIONS

修改之后：
```
sqoop import --connect jdbc:mysql://localhost:3306/test --target-dir /user/xiaosi/data/ --query "select * from order_info where $CONDITIONS" -m 1 --username root -P
```
报错信息：
```
16/11/14 12:03:56 INFO manager.MySQLManager: Preparing to use a MySQL streaming resultset.
16/11/14 12:03:56 INFO tool.CodeGenTool: Beginning code generation
16/11/14 12:03:56 ERROR tool.ImportTool: Encountered IOException running import job: java.io.IOException: Query [select * from order_info where ] must contain '$CONDITIONS' in WHERE clause.
	at org.apache.sqoop.manager.ConnManager.getColumnTypes(ConnManager.java:300)
	at org.apache.sqoop.orm.ClassWriter.getColumnTypes(ClassWriter.java:1833)
	at org.apache.sqoop.orm.ClassWriter.generate(ClassWriter.java:1645)
	at org.apache.sqoop.tool.CodeGenTool.generateORM(CodeGenTool.java:107)
	at org.apache.sqoop.tool.ImportTool.importTable(ImportTool.java:478)
	at org.apache.sqoop.tool.ImportTool.run(ImportTool.java:605)
	at org.apache.sqoop.Sqoop.run(Sqoop.java:143)
	at org.apache.hadoop.util.ToolRunner.run(ToolRunner.java:70)
	at org.apache.sqoop.Sqoop.runSqoop(Sqoop.java:179)
	at org.apache.sqoop.Sqoop.runTool(Sqoop.java:218)
	at org.apache.sqoop.Sqoop.runTool(Sqoop.java:227)
	at org.apache.sqoop.Sqoop.main(Sqoop.java:236)
```	
报错原因：

使用双引号会导致如上的报错信息，使用单引号就可以

最后修改：
```
sqoop import --connect jdbc:mysql://localhost:3306/test --target-dir /user/xiaosi/data/ --query 'select * from order_info where $CONDITIONS' -m 1 --username root -P
```



