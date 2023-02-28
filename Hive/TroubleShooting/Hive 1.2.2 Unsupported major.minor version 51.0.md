
> Hive 1.2.2 版本

## 1. 问题

在 Hive 1.2.2 版本运行 HQL 语句时，报如下异常：
```java
Exception in thread "main" java.lang.UnsupportedClassVersionError: org/apache/hadoop/hive/cli/CliDriver : Unsupported major.minor version 51.0
        at java.lang.ClassLoader.defineClass1(Native Method)
        at java.lang.ClassLoader.defineClassCond(ClassLoader.java:632)
        at java.lang.ClassLoader.defineClass(ClassLoader.java:616)
        at java.security.SecureClassLoader.defineClass(SecureClassLoader.java:141)
        at java.net.URLClassLoader.defineClass(URLClassLoader.java:283)
        at java.net.URLClassLoader.access$000(URLClassLoader.java:58)
        at java.net.URLClassLoader$1.run(URLClassLoader.java:197)
        at java.security.AccessController.doPrivileged(Native Method)
        at java.net.URLClassLoader.findClass(URLClassLoader.java:190)
        at java.lang.ClassLoader.loadClass(ClassLoader.java:307)
        at sun.misc.Launcher$AppClassLoader.loadClass(Launcher.java:301)
        at java.lang.ClassLoader.loadClass(ClassLoader.java:296)
        at java.lang.ClassLoader.loadClass(ClassLoader.java:248)
        at java.lang.Class.forName0(Native Method)
        at java.lang.Class.forName(Class.java:247)
        at org.apache.hadoop.util.RunJar.main(RunJar.java:205)
```

> 当前 JDK 版本比较低为 1.6。

## 2. 问题分析

这是因为依赖的Hadoop 'jar' 是使用 JDK 1.7 编译，但是我们在运行时却在 JDK 1.6 环境下运行。所以主要原因是 JDK 版本过低导致。

版本对照关系可以参考：https://en.wikipedia.org/wiki/Java_class_file
```
Java SE 9 = 53 (0x35 hex)
Java SE 8 = 52 (0x34 hex)
Java SE 7 = 51 (0x33 hex)
Java SE 6.0 = 50 (0x32 hex)
Java SE 5.0 = 49 (0x31 hex)
JDK 1.4 = 48 (0x30 hex)
JDK 1.3 = 47 (0x2F hex)
JDK 1.2 = 46 (0x2E hex)
JDK 1.1 = 45 (0x2D hex)
```

## 3. 解决方案

根据上面的分析把 JDK 版本提升到 JDK 1.7 即可。
