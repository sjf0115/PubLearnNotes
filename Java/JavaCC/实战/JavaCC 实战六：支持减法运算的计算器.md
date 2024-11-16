在[上一篇文章](https://smartsi.blog.csdn.net/article/details/143821999)中我们实现了一个支持整数、小数加法运算的计算器。为了得到一个更实用的计算器，我们需要更多的运算符，例如减法、乘法和除法。这篇文章介绍如何为计算器添加减法运算。

## 1. 编写语法文件

你可以使用你喜欢的文本编辑器创建和编辑语法文件。在这我们创建一个 `calculator_v4.jj` 语法文件。在本节的其余部分中，代码示例将是 `calculator_v4.jj` 的文件的一部分内容。这个文件包含了用于解析器和词法分析器的 JavaCC 规范，并被用作 JavaCC 程序的输入。

词法分析器的规范稍有一些变化，我们增加了一个新的产生式：
```java
TOKEN : { < MINUS : "-" > }
```

在 `EOL` 和 `NUMBER` 的表达式产生式中，我们使用竖线来分隔不同的选项；我们可以在定义解析器的 `BNF` 结果中执行相同的操作。在这种情况下，我们需要在 `PLUS` 和 `MINUS` 两个 Token 之间进行选择。使用 BNF 表示法可以将 Expression 的修改为：
```java
Expression --> Primary ((PLUS | MINUS) Primary) *
```
但是我们更建议使用如下的等价表示：
```java
Expression --> Primary (PLUS Primary | MINUS Primary)*
```
这种方式使得生成的 Java 代码简单些(思考一下如果是第一种方式，对应的产生式是什么)，在 JavaCC 描述文件中，其对应的产生式如下所示：
```java
double Expression() throws NumberFormatException :
{
    double i ;
    double value ;
}
{
    value = Primary()
    (
        <PLUS>
        i = Primary()
        { value += i ; }
    |
        <MINUS>
        i = Primary()
        { value -= i ; }
    )*
    { return value ; }
}
```

## 2. 生成解析器和词法分析器

至此我们完成了 `calculator_v4.jj` 语法文件的修改：
```java
options {
  STATIC = false ;
}
PARSER_BEGIN(Calculator)
  import java.io.PrintStream ;
  class Calculator {
      public static void main( String[] args ) throws ParseException, TokenMgrError, NumberFormatException {
          Calculator parser = new Calculator( System.in ) ;
          parser.Start(System.out) ;
      }
      double previousValue = 0.0 ;
  }
PARSER_END(Calculator)


SKIP : { " " }
TOKEN : { < EOL : "\n" | "\r" | "\r\n" > }
TOKEN : { < PLUS : "+" > }
TOKEN : { < MINUS : "-" > }
TOKEN : { < NUMBER : <DIGITS> | <DIGITS> "." <DIGITS> | <DIGITS> "." | "." <DIGITS> > }
TOKEN : { < #DIGITS : (["0"-"9"])+ > }


void Start(PrintStream printStream) throws NumberFormatException :
{}
{
    (
        previousValue = Expression()
        <EOL> { printStream.println( previousValue ) ; }
    )*
    <EOF>
}

double Expression() throws NumberFormatException :
{
    double i ;
    double value ;
}
{
    value = Primary()
    (
        <PLUS>
        i = Primary()
        { value += i ; }
    |
        <MINUS>
        i = Primary()
        { value -= i ; }
    )*
    { return value ; }
}

double Primary() throws NumberFormatException :
{
    Token t ;
}
{
    t = <NUMBER>
    { return Double.parseDouble( t.image ) ; }
}
```
生成 `calculator_v4.jj ` 文件后，我们对其调用 JavaCC 命令来生成解析器与词法分析器，JavaCC 的详细安装与运行请查阅[入门示例](https://smartsi.blog.csdn.net/article/details/143640803)。如下所示直接运行 `javacc calculator_v4.jj` 命令来生成：
```java
localhost:v4 wy$ javacc calculator_v4.jj
Java Compiler Compiler Version 7.0.13 (Parser Generator)
(type "javacc" with no arguments for help)
Reading from file calculator_v4.jj . . .
File "TokenMgrError.java" does not exist.  Will create one.
File "ParseException.java" does not exist.  Will create one.
File "Token.java" does not exist.  Will create one.
File "SimpleCharStream.java" does not exist.  Will create one.
Parser generated successfully.
```
执行完之后，同之前一样都会生成 7 个 Java 文件，包括了解析器以及词法分析器，具体说明请查阅[入门示例](https://smartsi.blog.csdn.net/article/details/143640803)。接下来我们对这些 Java 文件进行编译，编译完成之后可得到对应的 class 文件来运行：
```java
localhost:v4 wy$ javac *.java
localhost:v4 wy$ ll
total 200
drwxr-xr-x  17 wy  wheel    544 Nov 16 19:49 ./
drwxr-xr-x   9 wy  wheel    288 Nov 16 19:48 ../
-rw-r--r--   1 wy  wheel   5522 Nov 16 19:49 Calculator.class
-rw-r--r--   1 wy  wheel   6780 Nov 16 19:49 Calculator.java
-rw-r--r--   1 wy  wheel    613 Nov 16 19:49 CalculatorConstants.class
-rw-r--r--   1 wy  wheel    702 Nov 16 19:49 CalculatorConstants.java
-rw-r--r--   1 wy  wheel   6205 Nov 16 19:49 CalculatorTokenManager.class
-rw-r--r--   1 wy  wheel  10429 Nov 16 19:49 CalculatorTokenManager.java
-rw-r--r--   1 wy  wheel   2936 Nov 16 19:49 ParseException.class
-rw-r--r--   1 wy  wheel   6221 Nov 16 19:49 ParseException.java
-rw-r--r--   1 wy  wheel   6586 Nov 16 19:49 SimpleCharStream.class
-rw-r--r--   1 wy  wheel  11826 Nov 16 19:49 SimpleCharStream.java
-rw-r--r--   1 wy  wheel    985 Nov 16 19:49 Token.class
-rw-r--r--   1 wy  wheel   4070 Nov 16 19:49 Token.java
-rw-r--r--   1 wy  wheel   2363 Nov 16 19:49 TokenMgrError.class
-rw-r--r--   1 wy  wheel   4568 Nov 16 19:49 TokenMgrError.java
-rw-r--r--   1 wy  wheel   1237 Nov 16 19:49 calculator_v4.jj
```

## 3. 运行示例

跟[入门示例](https://smartsi.blog.csdn.net/article/details/143640803)一样我们可以通过准备合适的输入文件并执行如下命令来运行程序：
```java
java Calculator <input.txt
```
> 在 input.txt 文件中包含输入序列

假设输入是 `123 + 456`，会在控制台看到结果 `579.0`：
```java
localhost:v4 wy$ cat input.txt
123 + 456
localhost:v4 wy$ java Calculator <input.txt
579.0
```
假设输入是 `456 - 123`，会在控制台看到结果 `333.0`：
```java
localhost:v4 wy$ cat input.txt
456 - 123
localhost:v4 wy$ java Calculator <input.txt
333.0
```
假设输入是 `456 - 123 + 17 - 5`，会在控制台看到结果 `345.0`：
```java
localhost:v4 wy$ cat input.txt
456 - 123 + 17 - 5
localhost:v4 wy$ java Calculator <input.txt
345.0
```
