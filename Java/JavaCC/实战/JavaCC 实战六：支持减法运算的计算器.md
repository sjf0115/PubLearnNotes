为了得到一个更实用的计算器，我们需要更多的运算符，例如减法、乘法和除法。我们从减法开始。这篇文章介绍如何为计算器添加减法运算。

## 1. 编写语法文件

你可以使用你喜欢的文本编辑器创建和编辑语法文件。在这我们创建一个 `calculator_minus.jj` 语法文件。在本节的其余部分中，代码示例将是 `calculator_minus.jj` 的文件的一部分内容。这个文件包含了用于解析器和词法分析器的 JavaCC 规范，并被用作 JavaCC 程序的输入。

词法分析器的规范稍有一些变化，我们增加了一个新的生产式：
```java
TOKEN : { < MINUS : "-" > }
```

在 `EOL` 和 `NUMBER` 的表达式生产式中，我们使用竖线来分隔不同的选项；我们可以在定义解析器的 BNF 结果中执行相同的操作。在这种情况下，我们需要在 `PLUS` 和 `MINUS` 两个 Token 之间进行选择。使用 BNF 表示法可以将 Expression 的修改为：
```java
Expression --> Primary ((PLUS | MINUS) Primary) *
```
但是我们更建议使用如下的等价表示：
```java
Expression --> Primary (PLUS Primary | MINUS Primary)*
```
这种方式使得生成的 Java 代码简单些(思考一下如果是第一种方式，对应的生产式是什么)，在 JavaCC 描述文件中，其对应的生产式如下所示：
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

至此我们完成了 `calculator_minus.jj` 语法文件的修改：
```java
options {
  STATIC = false ;
}
PARSER_BEGIN(CalculatorMinus)
  import java.io.PrintStream ;
  class CalculatorMinus {
      public static void main( String[] args ) throws ParseException, TokenMgrError, NumberFormatException {
          CalculatorMinus parser = new CalculatorMinus( System.in ) ;
          parser.Start(System.out) ;
      }
      double previousValue = 0.0 ;
  }
PARSER_END(CalculatorMinus)


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
生成 `calculator_minus.jj ` 文件后，我们对其调用 JavaCC 命令来生成解析器与词法分析器，JavaCC 的详细安装与运行请查阅[JavaCC 实战一：安装与入门示例](https://smartsi.blog.csdn.net/article/details/143640803)。如下所示直接运行 `javacc calculator_minus.jj` 命令来生成：
```java
localhost:calculator_minus wy$ javacc calculator_minus.jj
Java Compiler Compiler Version 7.0.13 (Parser Generator)
(type "javacc" with no arguments for help)
Reading from file calculator_minus.jj . . .
File "TokenMgrError.java" does not exist.  Will create one.
File "ParseException.java" does not exist.  Will create one.
File "Token.java" does not exist.  Will create one.
File "SimpleCharStream.java" does not exist.  Will create one.
Parser generated successfully.
```
执行完之后，同之前一样都会生成 7 个 Java 文件，包括了解析器以及词法分析器。接下来我们对这些 java 文件进行编译，编译完成之后可得到对应的 class 文件来运行：
```java
localhost:calculator_minus wy$ javac *.java
localhost:calculator_minus wy$ ll
total 200
drwxr-xr-x  17 wy  wheel    544 Nov 10 20:08 ./
drwxr-xr-x   7 wy  wheel    224 Nov 10 20:07 ../
-rw-r--r--   1 wy  wheel   5552 Nov 10 20:08 CalculatorMinus.class
-rw-r--r--   1 wy  wheel   6860 Nov 10 20:08 CalculatorMinus.java
-rw-r--r--   1 wy  wheel    623 Nov 10 20:08 CalculatorMinusConstants.class
-rw-r--r--   1 wy  wheel    712 Nov 10 20:08 CalculatorMinusConstants.java
-rw-r--r--   1 wy  wheel   6220 Nov 10 20:08 CalculatorMinusTokenManager.class
-rw-r--r--   1 wy  wheel  10459 Nov 10 20:08 CalculatorMinusTokenManager.java
-rw-r--r--   1 wy  wheel   2936 Nov 10 20:08 ParseException.class
-rw-r--r--   1 wy  wheel   6221 Nov 10 20:08 ParseException.java
-rw-r--r--   1 wy  wheel   6586 Nov 10 20:08 SimpleCharStream.class
-rw-r--r--   1 wy  wheel  11826 Nov 10 20:08 SimpleCharStream.java
-rw-r--r--   1 wy  wheel    985 Nov 10 20:08 Token.class
-rw-r--r--   1 wy  wheel   4070 Nov 10 20:08 Token.java
-rw-r--r--   1 wy  wheel   2363 Nov 10 20:08 TokenMgrError.class
-rw-r--r--   1 wy  wheel   4568 Nov 10 20:08 TokenMgrError.java
-rw-r--r--   1 wy  wheel   1262 Nov 10 20:07 calculator_minus.jj
```

## 3. 运行示例

跟[上一篇文章](https://smartsi.blog.csdn.net/article/details/143661219)一样我们可以通过准备合适的输入文件并执行如下命令来运行程序：
```java
java CalculatorMinus <input.txt
```
> 在 input.txt 文件中包含输入序列

假设输入是 `123 + 456`，会在控制台看到结果 `579.0`：
```java
localhost:calculator_minus wy$ cat input.txt
123 + 456
localhost:calculator_minus wy$ java CalculatorMinus <input.txt
579.0
localhost:calculator_minus wy$
```
假设输入是 `456 - 123`，会在控制台看到结果 `333.0`：
```java
localhost:calculator_minus wy$ cat input.txt
456 - 123
localhost:calculator_minus wy$ java CalculatorMinus <input.txt
333.0
localhost:calculator_minus wy$
```
