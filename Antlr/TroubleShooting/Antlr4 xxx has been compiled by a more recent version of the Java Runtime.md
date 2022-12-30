> Antlr 版本 4.11.1

## 1. 问题

在安装完 Antlr 后检查是否正确安装时，抛出如下异常信息：
```java
localhost:opt wy$ java -jar /opt/antlr/antlr-4.11.1-complete.jar
Error: A JNI error has occurred, please check your installation and try again
Exception in thread "main" java.lang.UnsupportedClassVersionError: org/antlr/v4/Tool has been compiled by a more recent version of the Java Runtime (class file version 55.0), this version of the Java Runtime only recognizes class file versions up to 52.0
	at java.lang.ClassLoader.defineClass1(Native Method)
	at java.lang.ClassLoader.defineClass(ClassLoader.java:763)
	at java.security.SecureClassLoader.defineClass(SecureClassLoader.java:142)
	at java.net.URLClassLoader.defineClass(URLClassLoader.java:467)
	at java.net.URLClassLoader.access$100(URLClassLoader.java:73)
	at java.net.URLClassLoader$1.run(URLClassLoader.java:368)
	at java.net.URLClassLoader$1.run(URLClassLoader.java:362)
	at java.security.AccessController.doPrivileged(Native Method)
	at java.net.URLClassLoader.findClass(URLClassLoader.java:361)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:424)
	at sun.misc.Launcher$AppClassLoader.loadClass(Launcher.java:338)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:357)
	at sun.launcher.LauncherHelper.checkAndLoadMain(LauncherHelper.java:495)
```

## 2. 解决方案

通过错误信息可以看到 `org/antlr/v4/Tool` 类是通过更高版本的 Java 进行编译的，我们本地安装的版本比较低，所以才导致了这个错误。也就是如果低版本的 Java 却安装高版本的 Antlr4 就会报错。`class` 文件的 version 与 Java 的对应关系如下所示：
```
49 = Java 5
50 = Java 6
51 = Java 7
52 = Java 8
53 = Java 9
54 = Java 10
55 = Java 11
56 = Java 12
57 = Java 13
58 = Java 14
59 = Java 15
60 = Java 16
61 = Java 17
62 = Java 18
63 = Java 19
```
通过这个对应关系，我们可以知道 4.11.1 版本（55.0）的 Antlr 需要的 Java 11，但是我们本地却是 Java 8。所以解决方案有两种：
- 将本地的 Java 版本提升到 11
- 使用 Java 8 的 Antlr 版本

在这为了方便，采用第二种方案，将 Antlr 版本下降到 4.9.3 版本。
