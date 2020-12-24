

如下使用Java访问Hive表：
```java
Class.forName("org.apache.hive.jdbc.HiveDriver");
Connection conn = DriverManager.getConnection("jdbc:hive://xxx", user, password);
```
出现如下错误：
```java
java.sql.SQLException: No suitable driver found for jdbc:hive:xxx
        at java.sql.DriverManager.getConnection(DriverManager.java:689)
        at java.sql.DriverManager.getConnection(DriverManager.java:247)
        at com.sjf.example.hive.HiveServer2Example.getConn(HiveServer2Example.java:31)
        at com.sjf.example.hive.HiveServer2Example.main(HiveServer2Example.java:170)
```
解决如下：
```
hive 版本为 2.1.1 所以需要 jdbc:hive2://xxx 替换 jdbc:hive://xxx
```
