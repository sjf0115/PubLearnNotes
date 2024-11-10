Java Compiler Compiler (JavaCC) 是 Java 应用程序最流行的一种解析器生成器。解析器生成器是一种可以读取语法规范并将其转换为能够识别与匹配语法规范的一段 Java 程序。除了解析器生成器本身，JavaCC 还提供了与解析器生成相关的其他功能，例如树构建(通过 JavaCC 附带的 JJTree 工具)、操作和调试。一旦生成 JavaCC 解析器，运行它只需要 Java 运行时环境(JRE)。

## 1. 特性

- JavaCC 生成的是自顶向下(递归下降)的解析器，而不是像由 YACC 类似工具生成的自底向上的解析器。尽管不允许左递归，但是这样可以使用更通用的语法。自顶向下解析器还有许多其他优点(除了更通用的语法之外)，比如更容易调试，能够解析语法中的任何非终结符，还能够在解析期间在解析树中上下传递值(属性)。
- 默认情况下，JavaCC 生成一个 `LL(1)` 解析器。然而，可能有一部分语法不是 `LL(1)`。JavaCC 提供了语法和语义前瞻性的功能，可以在这些点上解决本地的移位歧义。例如，解析器仅在这些点上是 `LL(k)`，但在其他地方保持 `LL(1)` 以获得更好的性能。对于自顶向下的解析器来说，Shift-reduce 和 reduce-reduce 冲突不是问题。
- JavaCC 生成 100% 纯 Java 的解析器，因此 JavaCC 没有运行时依赖，也不需要在不同的机器平台上运行特殊的移植工作。
- JavaCC 允许在词法和语法规范中使用扩展 BNF 规范，例如 `(A)*`、`(A)+` 等。扩展 BNF 在一定程度上减轻了左递归的需要。实际上，扩展 BNF 通常更容易阅读，例如 `A::= y(x)*` 相比 `A::= Ax|y` 更易阅读。
- 词法规范(如正则表达式、字符串)和语法规范(BNF)可以写在同一个文件中。这样使语法更容易阅读，因为可以在语法规范中使用内联正则表达式，并且也更容易维护。
- JavaCC 的词法分析器可以处理完整的 Unicode 输入，而且词法规范也可以包括任何 Unicode 字符。这有助于描述语言元素，例如 Java 标识符，它允许某些 Unicode 字符(不是 ASCII)，但不允许其他字符。
- JavaCC 提供了类似 Lex 的词法状态和词法操作功能。JavaCC 中优于其他工具的具体方面是它提供的一级类状态，如 TOKEN、MORE、SKIP 和状态更改等概念。这允许更清晰的规范以及来自 JavaCC 的更好的错误和警告消息。
- 在词法规范中定义为特殊 Token 的 Token 在解析期间将被忽略，但这些 Token 可被工具处理。一个比较好的的应用示例是注释的处理。
- 词法规范可以在整个词法规范的全局级别或在单个词法规范上定义不区分大小写的 Token。
- JavaCC 附带了 JJTree，这是一个非常强大的树构建预处理器。
- JavaCC 还包括 JJDoc，这是一种将语法文件转换为文档文件(可选的 HTML 格式)的工具。
- JavaCC 提供了许多选项来定制行为以及为生成的解析器定制行为。这些选项的示例包括在输入流上执行的 Unicode 处理的种类，要执行的歧义检查 Token 的数量等。
- JavaCC 错误报告是解析器生成器中一个比较好的功能。JavaCC 生成的解析器能够通过完整的诊断信息清楚地指出解析错误的位置。
- 通过使用 `DEBUG_PARSER`、`DEBUG_LOOKAHEAD` 和 `DEBUG_TOKEN_MANAGER` 选项，用户可以深入分析解析和 Token 处理步骤。
- JavaCC 版本包含了大量的示例，包括 Java 和 HTML 语法。这些示例及其文档是熟悉 JavaCC 的好方法。

## 2. 安装

你可以通过命令行或者 IDE 来使用 JavaCC。在这我们使用命令行的方式。

### 2.1 下载

在下载目录中下载最新的稳定版本(至少是源代码和二进制文件):
- JavaCC 7.0.13 -([源代码(zip)](https://github.com/javacc/javacc/archive/javacc-7.0.13.zip)，[源代码(tar.gz)](https://github.com/javacc/javacc/archive/javacc-7.0.13.tar.gz)，[二进制文件](https://repo1.maven.org/maven2/net/java/dev/javacc/javacc/7.0.13/javacc-7.0.13.jar)，[Javadocs](https://repo1.maven.org/maven2/net/java/dev/javacc/javacc/7.0.13/javacc-7.0.13-javadoc.jar)，[发行说明](https://javacc.github.io/javacc/release-notes.html#javacc-7.0.13)

所有 JavaCC 版本都可以通过 GitHub 和 Maven 获得，对于所有以前的版本，请参阅[稳定版本]([JavaCC | The most popular parser generator for use with Java applications.](https://javacc.github.io/javacc/downloads.html))。

### 2.2 安装

下载完文件后，导航到下载目录并解压缩源文件到 `/opt` 目录下，这样就创建了一个所谓的 JavaCC 安装目录:
```shell
tar -zxvf javacc-javacc-7.0.13.tar.gz -C /opt
```
创建软连接，便于升级：
```
ln -s javacc-javacc-7.0.13/ javacc
```

然后将下载目录下的二进制文件 `javacc-7.0.13.jar` 移动到安装目录下的新 `target/` 目录下，并将其重命名为 `javacc.jar`。然后将 JavaCC 安装目录中的 `scripts/` 目录添加到 PATH 中：
```
export JAVACC_HOME=/opt/javacc/scripts
export PATH=${JAVACC_HOME}:$PATH
```

在基于 UNIX 的系统上，脚本可能无法立即执行。这可以通过使用 `javacc-7.0.13/` 目录中的命令来解决:
```shell
chmod +x scripts/javacc
```

## 3. 入门示例

我们以识别匹配的大括号为示例进行演示。下面介绍的 JavaCC 语法示例会识别匹配的大括号，后面跟着的零个或多个行结束符，然后是文件结束符。如下所示的几个字符串都是合法字符串:
```
{}, {{{{{}}}}} ...
```

如下所示的几个字符串都是非法字符串:
```
{}{}, }{}}, { }, {x} ...
```

### 3.1 编写语法

你可以使用你喜欢的文本编辑器创建和编辑语法文件。我们创建一个 `brace.jj` 语法文件，具体语法如下：
```java
PARSER_BEGIN(Brace)

  public class Brace {

    public static void main(String args[]) throws ParseException {
      Brace parser = new Brace(System.in);
      parser.Input();
    }

  }

PARSER_END(Brace)

void Input() :
{}
{
  MatchedBraces() ("\n"|"\r")* <EOF>
}

void MatchedBraces() :
{}
{
  "{" [ MatchedBraces() ] "}"
}
```

### 3.2 生成解析器

然后使用 javacc 命令生成解析器：
```
localhost:javacc_jj wy$ javacc brace.jj
Java Compiler Compiler Version 7.0.13 (Parser Generator)
(type "javacc" with no arguments for help)
Reading from file brace.jj . . .
File "TokenMgrError.java" does not exist.  Will create one.
File "ParseException.java" does not exist.  Will create one.
File "Token.java" does not exist.  Will create one.
File "SimpleCharStream.java" does not exist.  Will create one.
Parser generated successfully.
```
执行完之后，会生成 7 个 Java 文件，如下所示：
```
localhost:javacc_jj wy$ ll
total 128
drwxr-xr-x  11 wy  wheel    352 Nov  9 10:03 ./
drwxr-xr-x   4 wy  wheel    128 Nov  9 09:57 ../
-rw-r--r--   1 wy  wheel   7126 Nov  9 10:03 Brace.java
-rw-r--r--   1 wy  wheel    425 Nov  9 10:03 BraceConstants.java
-rw-r--r--   1 wy  wheel   6080 Nov  9 10:03 BraceTokenManager.java
-rw-r--r--   1 wy  wheel   6221 Nov  9 10:03 ParseException.java
-rw-r--r--   1 wy  wheel  12349 Nov  9 10:03 SimpleCharStream.java
-rw-r--r--   1 wy  wheel   4070 Nov  9 10:03 Token.java
-rw-r--r--   1 wy  wheel   4568 Nov  9 10:03 TokenMgrError.java
-rw-r--r--   1 wy  wheel    328 Nov  9 10:02 brace.jj
```
其中：
- `Brace` 是解析器。
- `BraceTokenManager` 是词法分析器。
- `BraceConstants` 是一个接口，里面定义了一些词法分析器和解析器中会用到的常量。
- `TokenMgrError` 是一个简单的错误类，在词法分析器检测到错误时使用，是 Throwable 的子类。
- `ParseException` 是另一个错误类，在解析器检测到的错误时使用，是 Exception 的子类，因此也是 Throwable 的子类。
- `Token` 类是一个用于表示 token 的类。
- `SimpleCharStream` 是一个转接器类，用于把字符传递给词法分析器。

接下来我们对这些 java 文件进行编译，编译完成之后可得到对应的 class 文件：
```
localhost:javacc_jj wy$ javac *.java
localhost:javacc_jj wy$ ll
total 208
drwxr-xr-x  18 wy  wheel    576 Nov  9 10:08 ./
drwxr-xr-x   4 wy  wheel    128 Nov  9 09:57 ../
-rw-r--r--   1 wy  wheel   5258 Nov  9 10:08 Brace.class
-rw-r--r--   1 wy  wheel   7126 Nov  9 10:03 Brace.java
-rw-r--r--   1 wy  wheel    419 Nov  9 10:08 BraceConstants.class
-rw-r--r--   1 wy  wheel    425 Nov  9 10:03 BraceConstants.java
-rw-r--r--   1 wy  wheel   4615 Nov  9 10:08 BraceTokenManager.class
-rw-r--r--   1 wy  wheel   6080 Nov  9 10:03 BraceTokenManager.java
-rw-r--r--   1 wy  wheel   2936 Nov  9 10:08 ParseException.class
-rw-r--r--   1 wy  wheel   6221 Nov  9 10:03 ParseException.java
-rw-r--r--   1 wy  wheel   6608 Nov  9 10:08 SimpleCharStream.class
-rw-r--r--   1 wy  wheel  12349 Nov  9 10:03 SimpleCharStream.java
-rw-r--r--   1 wy  wheel    985 Nov  9 10:08 Token.class
-rw-r--r--   1 wy  wheel   4070 Nov  9 10:03 Token.java
-rw-r--r--   1 wy  wheel   2363 Nov  9 10:08 TokenMgrError.class
-rw-r--r--   1 wy  wheel   4568 Nov  9 10:03 TokenMgrError.java
-rw-r--r--   1 wy  wheel    328 Nov  9 10:02 brace.jj
```

### 3.3 执行程序

`{{}}` 是一个合法字符串，回车执行不会抛出异常：
```java
localhost:javacc_jj wy$ java Brace
{}

```

`{x` 是一个非法字符串，回车执行抛出一个 `TokenMgrError` 词法错误：
```java
localhost:javacc_jj wy$ java Brace
{x
Exception in thread "main" TokenMgrError: Lexical error at line 1, column 2.  Encountered: 'x' (120),
	at BraceTokenManager.getNextToken(BraceTokenManager.java:119)
	at Brace.jj_ntk_f(Brace.java:206)
	at Brace.MatchedBraces(Brace.java:44)
	at Brace.Input(Brace.java:11)
	at Brace.main(Brace.java:7)
```

`{}}` 是一个非法字符串，回车执行抛出一个 `ParseException` 解析异常：
```java
localhost:javacc_jj wy$ java Brace
{}}
Exception in thread "main" ParseException: Encountered " "}" "} "" at line 1, column 3.
Was expecting one of:
    <EOF>
    "\n" ...
    "\r" ...

	at Brace.generateParseException(Brace.java:243)
	at Brace.jj_consume_token(Brace.java:181)
	at Brace.Input(Brace.java:39)
	at Brace.main(Brace.java:7)
```



> 原文:[JavaCC](https://javacc.github.io/javacc/)
