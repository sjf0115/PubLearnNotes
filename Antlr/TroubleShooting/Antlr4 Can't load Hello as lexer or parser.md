
## 1. 问题

在使用 `antlr4-test Hello r -tokens` 命令测试语法文件时，抛出如下异常：
```
Can't load Hello as lexer or parser
```
> antlr4-test 是我们对 `java org.antlr.v4.gui.TestRig` 定义的一个别名。

## 2. 解决方案

如果出现此问题需要检查如下几项是否正确，如果都配置正确应该不会看到上述错误：
- 确保生成了 `*.java` 文件
- 确保生成了 `*.class` 文件
- 正确设置了 CLASSPATH：CLASSPATH 中的 '.' 非常关键，代表当前目录。如果没有它，Java 编译器和 Java 虚拟机就无法加载当前目录的 class 文件。

检查发现我们没有运行 `javac *.java` 来编译 Antlr 生成的 Java 代码。我们通过在语法文件上运行 Antlr 命令来生成 Java 源文件，但是 TestRig 需要已编译好的 `.class` 文件。在使用 TestRig 之前，需要在源文件上运行 Java 编译器生成 `*.class` 文件：
```
localhost:antlr wy$ javac *.java
localhost:antlr wy$ ll
total 6976
drwxr-xr-x  18 wy   staff      612 12 30 20:23 ./
drwxrwxrwx  56 667  staff     1904 12 30 10:31 ../
-rw-r--r--   1 wy   staff      250 12 30 20:22 Hello.g4
-rw-r--r--   1 wy   staff      308 12 30 20:22 Hello.interp
-rw-r--r--   1 wy   staff       27 12 30 20:22 Hello.tokens
-rw-r--r--   1 wy   staff      794 12 30 20:23 HelloBaseListener.class
-rw-r--r--   1 wy   staff     1304 12 30 20:22 HelloBaseListener.java
-rw-r--r--   1 wy   staff     3722 12 30 20:23 HelloLexer.class
-rw-r--r--   1 wy   staff     1055 12 30 20:22 HelloLexer.interp
-rw-r--r--   1 wy   staff     3562 12 30 20:22 HelloLexer.java
-rw-r--r--   1 wy   staff       27 12 30 20:22 HelloLexer.tokens
-rw-r--r--   1 wy   staff      304 12 30 20:23 HelloListener.class
-rw-r--r--   1 wy   staff      536 12 30 20:22 HelloListener.java
-rw-r--r--   1 wy   staff      869 12 30 20:23 HelloParser$RContext.class
-rw-r--r--   1 wy   staff     4377 12 30 20:23 HelloParser.class
-rw-r--r--   1 wy   staff     3854 12 30 20:22 HelloParser.java
-rw-r--r--@  1 wy   staff  3508089 12 30 11:11 antlr-4.9.3-complete.jar
```

参考：https://stackoverflow.com/questions/23315302/antlr4-cant-load-hello-as-lexer-or-parser
