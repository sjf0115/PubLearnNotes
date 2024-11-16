在[上一篇文章](https://smartsi.blog.csdn.net/article/details/143661219)中我们实现了一个只支持整数加法运算的计算器。为了得到一个更实用的计算器，除了支持整数运算，也要支持小数运算。这篇文章介绍如何为计算器添加小数加法运算。

## 1. 编写语法文件

你可以使用你喜欢的文本编辑器创建和编辑语法文件。在这我们创建一个 `calculator_v3.jj` 语法文件。在本节的其余部分中，代码示例将是 `calculator_v3.jj` 的文件的一部分内容。这个文件包含了用于解析器和词法分析器的 JavaCC 规范，并被用作 JavaCC 程序的输入。

### 1.1 选项和类声明

文件 `calculator_v3.jj` 的第一部分 还是和以前一样:
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
```
`Calculator` 类中定义的 `previousValue` 变量，用于存储上一行的计算结果，将在下面介绍的 `Start` 方法中使用。`import` 语句说明可以在 `PARSER_BEGIN` 和 `PARSER_END` 之间进行 `import` 声明。这些会被复制到生成的解析器和词法分析器类中。除了 `import` 语句，也可以使用包声明，同样也会将其复制到所有的生成类中。

### 1.2 词法分析器规范

词法分析器的规范稍有一些变化。第一点改动是一行的结束也声明为一个 `TOKEN` 并指定名称为 `EOL`，这样以便将其传递给解析器：
```java
SKIP : { " " }
TOKEN : { < EOL : "\n" | "\r" | "\r\n" > }
TOKEN : { < PLUS : "+" > }
```
第二点改动我们允许在数字中使用小数点。为此需要修改 `NUMBER` 类型的 Token 定义，使得它可以识别数字中的小数点。当数值中允许有小数点时，会出现 4 情况：没有小数点、小数点在中间、小数点在末尾、小数点在开始。在 `NUMBER` Token 定义中使用竖线分割了对应 4 种情况的四个可选选项，如下所示：
```java
TOKEN { < NUMBER : (["0"-"9"])+ | (["0"-"9"])+ "." (["0"-"9"])+ | (["0"-"9"])+ "." | "." (["0"-"9"])+ > }
```
如上面所示同一个表达式出现了多次。为了可读性，最好给这样的表达式起一个符号名称。对于那些只在词法描述文件中使用到，但又不是 Token 的表达式，我们使用一个特殊的标识 `#` 来表示。因此，对于上面的词法规范，可以替换成如下：
```java
TOKEN : { < NUMBER : <DIGITS> | <DIGITS> "." <DIGITS> | <DIGITS> "." | "." <DIGITS> > }
TOKEN : { < #DIGITS : (["0"-"9"])+ > }
```
这种使用特殊标识的名称不会对应一种 Token 类型。可以看到，我们把 `(["0"-"9"])+` 表达式提取了出来，并将其命名为 `DIGITS`。需要注意到是，`DIGITS` 并不是一个 Token，这意味着在后面生成的 `Token` 类中，将不会有 `DIGITS` 对应的属性。

### 1.3 解析器规范

解析器的输入由零行或者多行组成，每行都包含一个表达式。通过使用 `BNF` 符号表达式，解析器可以写成如下形式：
```java
Start --> (Expression EOL) * EOF
```
由此可以得出 `BNF` 产生式如下所示：
```java
void Start() :
{}
{
    (
        Expression()
        <EOL>
    )*
    <EOF>
}
```
我们在上面的 `BNF` 产生式中填充上 Java 代码，使得它具备接收入参、记录并打印每一行的计算结果：
```java
void Start(PrintStream printStream) throws NumberFormatException :
{}
{
    (
        previousValue = Expression()
        <EOL> { printStream.println( previousValue ) ; }
    )*
    <EOF>
}
```
每个表达式由一个或者多个数字组成，这些数字目前用加号隔开。用 `BNF` 符号表达式如下：
```java
Expression −-> Primary (PLUS Primary)∗
```
在这里的 `Primary` 暂时用来表示数字。上面的 `BNF` 符号表达式用 JavaCC 表示出来如下所示：
```java
double Expression() throws NumberFormatException : {
    double i ;
    double value ;
}
{
    value = Primary()
    (
        <PLUS>
        i = Primary()
        { value += i ; }
    )*
    { return value ; }
}
```
这个跟我们[之前例子](https://smartsi.blog.csdn.net/article/details/143661219)中的 Start `BNF` 产生式差不多，我们只是将数值的类型由 `int` 修改成了 `double` 类型而已。`Primary()` 也跟之前的例子非常类似，用 `BNF` 符号表达式如下所示：
```java
Primary --> NUMBER
```
除了现在可以支持计算 double 数字之外，JavaCC 表示与之完全相同：
```java
double Primary() throws NumberFormatException :
{
    Token t ;
}
{
    t = <NUMBER>
    { return Double.parseDouble( t.image ) ; }
}
```
下面我们用 `BNF` 符号表达式将解析器的逻辑表示出来：
```java
Start --> (Expression EOL) * EOF
Expression --> Primary (PLUS Primary)*
Primary --> NUMBER
```

## 2. 生成解析器和词法分析器

至此我们完成了 `calculator_v3.jj` 语法文件的修改：
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
double Expression() throws NumberFormatException : {
    double i ;
    double value ;
}
{
    value = Primary()
    (
        <PLUS>
        i = Primary()
        { value += i ; }
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
生成 `calculator_v3.jj ` 文件后，我们对其调用 JavaCC 命令来生成解析器与词法分析器，JavaCC 的详细安装与运行请查阅[入门示例](https://smartsi.blog.csdn.net/article/details/143640803)。如下所示直接运行 `javacc calculator_v3.jj` 命令来生成：
```java
localhost:v3 wy$ javacc calculator_v3.jj
Java Compiler Compiler Version 7.0.13 (Parser Generator)
(type "javacc" with no arguments for help)
Reading from file calculator_v3.jj . . .
File "TokenMgrError.java" does not exist.  Will create one.
File "ParseException.java" does not exist.  Will create one.
File "Token.java" does not exist.  Will create one.
File "SimpleCharStream.java" does not exist.  Will create one.
Parser generated successfully.
```
执行完之后，同之前一样都会生成 7 个 Java 文件，包括了解析器以及词法分析器，具体说明请查阅[入门示例](https://smartsi.blog.csdn.net/article/details/143640803)。接下来我们对这些 Java 文件进行编译，编译完成之后可得到对应的 class 文件来运行：
```java
localhost:v3 wy$ javac *.java
localhost:v3 wy$ ll
total 200
drwxr-xr-x  17 wy  wheel    544 Nov 16 19:33 ./
drwxr-xr-x  11 wy  wheel    352 Nov 16 19:32 ../
-rw-r--r--   1 wy  wheel   5376 Nov 16 19:33 Calculator.class
-rw-r--r--   1 wy  wheel   6431 Nov 16 19:32 Calculator.java
-rw-r--r--   1 wy  wheel    569 Nov 16 19:33 CalculatorConstants.class
-rw-r--r--   1 wy  wheel    641 Nov 16 19:32 CalculatorConstants.java
-rw-r--r--   1 wy  wheel   6167 Nov 16 19:33 CalculatorTokenManager.class
-rw-r--r--   1 wy  wheel  10368 Nov 16 19:32 CalculatorTokenManager.java
-rw-r--r--   1 wy  wheel   2936 Nov 16 19:33 ParseException.class
-rw-r--r--   1 wy  wheel   6221 Nov 16 19:32 ParseException.java
-rw-r--r--   1 wy  wheel   6586 Nov 16 19:33 SimpleCharStream.class
-rw-r--r--   1 wy  wheel  11826 Nov 16 19:32 SimpleCharStream.java
-rw-r--r--   1 wy  wheel    985 Nov 16 19:33 Token.class
-rw-r--r--   1 wy  wheel   4070 Nov 16 19:32 Token.java
-rw-r--r--   1 wy  wheel   2363 Nov 16 19:33 TokenMgrError.class
-rw-r--r--   1 wy  wheel   4568 Nov 16 19:32 TokenMgrError.java
-rw-r--r--   1 wy  wheel   1138 Nov 16 19:32 calculator_v3.jj
```

## 3. 运行示例

跟[入门示例](https://smartsi.blog.csdn.net/article/details/143640803)一样我们可以通过准备合适的输入文件并执行如下命令来运行程序：
```java
java Calculator <input.txt
```
> 在 input.txt 文件中包含输入序列

当数值中允许有小数点时，会出现 4 情况：没有小数点，小数点在中间，小数点在末尾，小数点在开始。假设输入数字中没有小数点 `123 + 456`，会在控制台看到结果 `579.0`：
```java
localhost:v3 wy$ cat input.txt
123 + 456
localhost:v3 wy$ java Calculator <input.txt
579.0
```
假设输入数字的小数点在中间 `123.2 + 456.7`，会在控制台看到结果 `579.9`：
```java
localhost:v3 wy$ cat input.txt
123.2 + 456.7
localhost:v3 wy$ java Calculator <input.txt
579.9
```
假设输入数字的小数点在末尾 `123. + 456`，会在控制台看到结果 `579.0`：
```java
localhost:v3 wy$ cat input.txt
123. + 456
localhost:v3 wy$ java Calculator <input.txt
579.0
```
假设输入数字的小数点在开始 `.7 + 456.2`，会在控制台看到结果 `456.9`：
```java
localhost:v3 wy$ cat input.txt
.7 + 456.2
localhost:v3 wy$ java Calculator <input.txt
456.9
```
