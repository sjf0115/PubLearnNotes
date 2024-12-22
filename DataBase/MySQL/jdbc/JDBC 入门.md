## 1. 什么是 JDBC

JDBC(Java 数据库连接) 是 Java DataBase Connectivity 的简写，是一种用于执行 SQL 语句的 Java API，可以为多种关系数据库提供统一访问，它由一组用 Java 语言编写的类和接口组成。JDBC 提供了一种基准，据此可以构建更高级的工具和接口，使数据库开发人员能够编写数据库应用程序。

简单地说，JDBC 可做三件事：与数据库建立连接、发送操作数据库的语句并处理结果。

## 2. 设计原理

JDBC 制定了一套和数据库进行交互的标准，数据库厂商提供这套标准的实现，这样就可以通过统一的 JDBC 接口来连接各种不同的数据库。可以说 JDBC 的作用是屏蔽了底层数据库的差异，使得用户按照 JDBC 写的代码可以在各种不同的数据库上进行执行。那么这是如何实现的呢？如下图所示：

JDBC 定义了 Driver 接口，这个接口就是数据库的驱动程序，所有跟数据库打交道的操作最后都会归结到这里，数据库厂商必须实现该接口，通过这个接口来完成上层应用的调用者和底层具体的数据库进行交互。Driver 是通过 JDBC 提供的 DriverManager 进行注册的，注册的代码写在了 Driver 的静态块中，如 MySQL 的注册代码如下所示：
```java
static {
  try {
    java.sql.DriverManager.registerDriver(new Driver());
  } catch (SQLException E) {
    throw new RuntimeException("Can't register driver!");
  }
}
```
作为驱动定义的规范 Driver，它的主要目的就是和数据库建立连接，所以其接口也很简单，如下所示：
```java
public interface Driver {
    //建立连接
    Connection connect(String url, java.util.Properties info) throws SQLException;
    boolean acceptsURL(String url) throws SQLException;
    DriverPropertyInfo[] getPropertyInfo(String url, java.util.Properties info) throws SQLException;
    int getMajorVersion();
    int getMinorVersion();
    boolean jdbcCompliant();
    public Logger getParentLogger() throws SQLFeatureNotSupportedException;
}
```
作为 Driver 的管理者 DriverManager，它不仅负责 Driver 的注册／注销，还可以直接获取连接。它是怎么做到的呢？观察下面代码发现，实际是通过遍历所有已经注册的 Driver，找到一个能够成功建立连接的 Driver，并且将 Connection 返回，DriverManager 就像代理一样，将真正建立连接的过程还是交给了具体的 Driver。
```java
for(DriverInfo aDriver : registeredDrivers) {
    // If the caller does not have permission to load the driver then
    // skip it.
    if(isDriverAllowed(aDriver.driver, callerCL)) {
        try {
            println("    trying " + aDriver.driver.getClass().getName());
            Connection con = aDriver.driver.connect(url, info);
            if (con != null) {
                // Success!
                println("getConnection returning " + aDriver.driver.getClass().getName());
                return (con);
            }
        } catch (SQLException ex) {
            if (reason == null) {
                reason = ex;
            }
        }

    } else {
        println("    skipping: " + aDriver.getClass().getName());
    }

}
```


> 原文：[JDBC 在性能测试中的应用](https://mp.weixin.qq.com/s/38y1otQLLR0HUmZ1IHHi2Q)
