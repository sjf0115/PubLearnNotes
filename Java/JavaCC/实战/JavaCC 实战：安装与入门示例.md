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

## 2. 示例

下面的 JavaCC 语法示例识别匹配的大括号，后面跟着零个或多个行结束符，然后是文件结束符。该语法中合法字符串的示例如下:
```
{}, {{{{{}}}}} // … etc
```

如下所示是一个非法字符串的示例:
```
{}{}, }{}}, { }, {x} // … etc
```

### 2.1 语法

具体语法如下：
```java
PARSER_BEGIN(Example)

/** Simple brace matcher. */
public class Example {

  /** Main entry point. */
  public static void main(String args[]) throws ParseException {
    Example parser = new Example(System.in);
    parser.Input();
  }

}

PARSER_END(Example)

/** Root production. */
void Input() :
{}
{
  MatchedBraces() ("\n"|"\r")* <EOF>
}

/** Brace matching production. */
void MatchedBraces() :
{}
{
  "{" [ MatchedBraces() ] "}"
}
```

### 2.2 执行与输出

【1】`{{}}` 执行不会抛出异常：
```java
$ java Example
{{}}<return>
```

【2】`{x` 抛出一个词法错误：
```java
$ java Example
{x<return>
Lexical error at line 1, column 2.  Encountered: "x"
TokenMgrError: Lexical error at line 1, column 2.  Encountered: "x" (120), after : ""
        at ExampleTokenManager.getNextToken(ExampleTokenManager.java:146)
        at Example.getToken(Example.java:140)
        at Example.MatchedBraces(Example.java:51)
        at Example.Input(Example.java:10)
        at Example.main(Example.java:6)
```

【3】`{}}` 抛出一个 ParseException 异常：
```java
$ java Example
{}}<return>
ParseException: Encountered "}" at line 1, column 3.
Was expecting one of:
    <EOF>
    "\n" ...
    "\r" ...
        at Example.generateParseException(Example.java:184)
        at Example.jj_consume_token(Example.java:126)
        at Example.Input(Example.java:32)
        at Example.main(Example.java:6)
```

## 3. 入门

你可以通过命令行或者 IDE 来使用 JavaCC。

### 3.1 使用命令行

#### 3.1.1 下载

在下载目录中下载最新的稳定版本(至少是源代码和二进制文件):
- JavaCC 7.0.13 -([源代码(zip)](https://github.com/javacc/javacc/archive/javacc-7.0.13.zip)，[源代码(tar.gz)](https://github.com/javacc/javacc/archive/javacc-7.0.13.tar.gz)，[二进制文件](https://repo1.maven.org/maven2/net/java/dev/javacc/javacc/7.0.13/javacc-7.0.13.jar)，[Javadocs](https://repo1.maven.org/maven2/net/java/dev/javacc/javacc/7.0.13/javacc-7.0.13-javadoc.jar)，[发行说明](https://javacc.github.io/javacc/release-notes.html#javacc-7.0.13)

所有 JavaCC 版本都可以通过 GitHub 和 Maven 获得，对于所有以前的版本，请参阅[稳定版本]([JavaCC | The most popular parser generator for use with Java applications.](https://javacc.github.io/javacc/downloads.html))。

#### 3.1.2 安装

下载完文件后，导航到下载目录并解压缩源文件到 `/opt` 目录下，这样就创建了一个所谓的 JavaCC 安装目录:
```shell
tar -zxvf javacc-javacc-7.0.13.tar.gz -C /opt
```

```
ln -s javacc-javacc-7.0.13/ javacc
```

然后将下载目录下的二进制文件 `javacc-7.0.14.jar` 移动到安装目录下的新 `target/` 目录下，并将其重命名为 `javacc.jar`。然后将 JavaCC 安装目录中的 `scripts/` 目录添加到 PATH 中：
```
export JAVACC_HOME=/opt/javacc/scripts
export PATH=${JAVACC_HOME}/javacc:$PATH
```
> JavaCC、JJTree 和 JJDoc 调用脚本/可执行文件均位于此目录中。

在基于 UNIX 的系统上，脚本可能无法立即执行。这可以通过使用 `javacc-7.0.14/` 目录中的命令来解决:
```shell
chmod +x scripts/javacc
```

#### 3.1.3 编写语法并生成解析器

你可以使用你喜欢的文本编辑器创建和编辑语法文件。然后使用适当的脚本从语法生成解析器。

### 3.2 在 IDE 中使用 JavaCC

将以下依赖项添加到 pom.xml 文件中：
```xml
<dependency>
    <groupId>net.java.dev.javacc</groupId>
    <artifactId>javacc</artifactId>
    <version>7.0.14</version>
</dependency>
```





> 原文:[JavaCC](https://javacc.github.io/javacc/)
