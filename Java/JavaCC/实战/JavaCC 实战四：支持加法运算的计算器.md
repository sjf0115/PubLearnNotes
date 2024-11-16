[上一篇文章](https://smartsi.blog.csdn.net/article/details/143661219)中介绍了如何使用 Javacc 实现判断输入是否是一个合法的加法运算表达式，但是仅限于检查其输入的合法性，并没有输出表达式计算的结果。从这篇文章开始，我们会一步一步的介绍如何实现一个支持加减乘除运算的计算器。在这篇文章中介绍如何为计算器添加加法运算并输出计算结果。

## 1. 解析器规范优化

在[上一篇文章](https://smartsi.blog.csdn.net/article/details/143658003)中，JavaCC 为 `BNF` 产生式所生成的方法，比如 `Start`，这些方法默认只是简单的检查输入是否匹配 `BNF` 产生式指定的规范，实际上不会计算输入表达式的结果。假设输入文件输入的是 `123 + 456`：
```java
localhost:v1 wy$ cat input.txt
123 + 456
localhost:v1 wy$ java Calculator <input.txt
localhost:v1 wy$
```
从上面可以看到解析器在输入合法时没有任何的输出，不执行任何操作仅限于检查其输入的合法性。但是，我们可以使用 Java 代码来扩展 `BNF` 产生式，使其在输入合法时输出整数加和的结果。只需要完善 JavaCC 为我们提供的框架即可实现我们想要的效果。我们将对上一个示例中的 `calculator_v1.jj` 语法文件做一些修改来扩展 `BNF` 产生式：
```java
/* calculator_v1.jj Adding up numbers */
options {
    STATIC = false ;
}
PARSER_BEGIN(Calculator)
    class Calculator {
        public static void main( String[] args ) throws ParseException, TokenMgrError {
            Calculator parser = new Calculator( System.in ) ;
            parser.Start() ;
        }
    }
PARSER_END(Calculator)

SKIP : { " " }
SKIP : { "\n" | "\r" | "\r\n" }
TOKEN : { < PLUS : "+" > }
TOKEN : { < NUMBER : (["0"-"9"])+ > }

void Start() :
{}
{
    <NUMBER>
    (
        <PLUS>
        <NUMBER>
    )*
    <EOF>
}
```
我们在 `Start` 方法中添加了一些声明和一些 Java 代码：
```java
int Start() throws NumberFormatException :
{
    Token t ;
    int i ;
    int value ;
}
{
    t = <NUMBER>
    { i = Integer.parseInt( t.image ) ; }
    { value = i ; }
    (
        <PLUS>
        t = <NUMBER>
        { i = Integer.parseInt( t.image ) ; }
        { value += i ; }
    )*
    <EOF>
    { return value ; }
}
```

首先第一个改动是 `BNF` 产生式的返回类型，以及由此生成的方法从 `void` 变为 `int`。第二个改动是，声明了可以从生成的方法中抛出 `NumberFormatException` 异常。此外我们还新增声明了三个变量，其中变量 `t` 为 `Token` 类型(`Token` 类型是我们编译 `.jj` 文件之后生成的类)。`Token` 类的 `image` 字段记录匹配的字符串。在声明完变量之后，当 BNF 产生式匹配一个 token 时，我们可以通过为其分配引用来记录 `Token` 对象：
```java
t = <NUMBER>
```
这样我们就可以通过引用来获取 `Token` 的信息，在这可以获取 token 匹配的数字字符串并使用 Java 语法转换为一个 Int 值：
```java
{ i = Integer.parseInt( t.image ) ; }
```

在 `BNF` 产生式的大括号内，我们可以添加任何我们想要的 Java 语句，这些 Java 语句在 JavaCC 编译生成解析器类时，将会被原封不动的复制到解析器类相应方法中。在改动中添加了三块 Java 语句，第一块是获取 token 匹配的数字并使用 `value` 变量存储：
```java
{ i = Integer.parseInt( t.image ) ; }
{ value = i ; }
```
第二块是实现整数加和运算：
```java
{ i = Integer.parseInt( t.image ) ; }
{ value += i ; }
```
最后一块是返回加和之后的数值：
```java
{ return value ; }
```

由于生成的 `Start` 方法现在返回一个数值，因此我们必须修改 `main` 方法，使用 `val` 变量接收返回值并将其输出到控制台：
```java
public static void main( String[] args ) throws ParseException, TokenMgrError, NumberFormatException {
  Calculator parser = new Calculator( System.in ) ;
  int val = parser.Start() ;
  System.out.println(val);
}
```
除了上面的改动之外，还有一个小的优化要做。如下两行在上述语法文件中出现了两次：
```java
t = <NUMBER>
{ i = Integer.parseInt( t.image ) ; }
```
虽然在这个例子中没有太大的影响，因为只涉及到两行代码，但是这种重复可能会导致后期维护问题。因此，我们将把这两行拆解成另一个 `BNF` 产生式，并命名为 `Primary`：
```java
int Start() throws NumberFormatException :
{
    int i ;
    int value ;
}
{
    value = Primary()
    (
        <PLUS>
        i = Primary()
        { value += i ; }
    )*
    <EOF>
    { return value ; }
}

int Primary() throws NumberFormatException :
{
    Token t ;
}
{
    t=<NUMBER>
    { return Integer.parseInt( t.image ) ; }
}
```

## 2. 生成解析器和词法分析器

将前面介绍的修改保存为 `calculator_v2.jj` 语法文件：
```java
options {
    STATIC = false ;
}
PARSER_BEGIN(Calculator)
    class Calculator {
      public static void main( String[] args ) throws ParseException, TokenMgrError, NumberFormatException {
          Calculator parser = new Calculator( System.in ) ;
          int val = parser.Start() ;
          System.out.println(val);
      }
    }
PARSER_END(Calculator)

SKIP : { " " }
SKIP : { "\n" | "\r" | "\r\n" }
TOKEN : { < PLUS : "+" > }
TOKEN : { < NUMBER : (["0"-"9"])+ > }

int Start() throws NumberFormatException :
{
    int i ;
    int value ;
}
{
    value = Primary()
    (
        <PLUS>
        i = Primary()
        { value += i ; }
    )*
    <EOF>
    { return value ; }
}

int Primary() throws NumberFormatException :
{
    Token t ;
}
{
    t=<NUMBER>
    { return Integer.parseInt( t.image ) ; }
}
```

生成 `Calculator_v2.jj ` 文件后，我们对其调用 JavaCC 命令来生成解析器与词法分析器，JavaCC 的详细安装与运行请查阅[入门示例](https://smartsi.blog.csdn.net/article/details/143640803)。如下所示直接运行 `javacc Calculator_v2.jj` 命令来生成：
```java
localhost:v2 wy$ javacc Calculator_v2.jj
Java Compiler Compiler Version 7.0.13 (Parser Generator)
(type "javacc" with no arguments for help)
Reading from file Calculator_v2.jj . . .
File "TokenMgrError.java" does not exist.  Will create one.
File "ParseException.java" does not exist.  Will create one.
File "Token.java" does not exist.  Will create one.
File "SimpleCharStream.java" does not exist.  Will create one.
Parser generated successfully.
```
执行完之后，同之前一样都会生成 7 个 Java 文件，包括了解析器以及词法分析器，具体说明请查阅[入门示例](https://smartsi.blog.csdn.net/article/details/143640803)。接下来我们对这些 Java 文件进行编译，编译完成之后可得到对应的 class 文件来运行：
```java
localhost:v2 wy$ javac *.java
localhost:v2 wy$ ll
total 200
drwxr-xr-x  17 wy  wheel    544 Nov 16 19:17 ./
drwxr-xr-x  10 wy  wheel    320 Nov 16 19:16 ../
-rw-r--r--   1 wy  wheel   5085 Nov 16 19:17 Calculator.class
-rw-r--r--   1 wy  wheel   5961 Nov 16 19:17 Calculator.java
-rw-r--r--   1 wy  wheel    525 Nov 16 19:17 CalculatorConstants.class
-rw-r--r--   1 wy  wheel    565 Nov 16 19:17 CalculatorConstants.java
-rw-r--r--   1 wy  wheel   5707 Nov 16 19:17 CalculatorTokenManager.class
-rw-r--r--   1 wy  wheel   8383 Nov 16 19:17 CalculatorTokenManager.java
-rw-r--r--   1 wy  wheel   2936 Nov 16 19:17 ParseException.class
-rw-r--r--   1 wy  wheel   6221 Nov 16 19:17 ParseException.java
-rw-r--r--   1 wy  wheel   6586 Nov 16 19:17 SimpleCharStream.class
-rw-r--r--   1 wy  wheel  11826 Nov 16 19:17 SimpleCharStream.java
-rw-r--r--   1 wy  wheel    985 Nov 16 19:17 Token.class
-rw-r--r--   1 wy  wheel   4070 Nov 16 19:17 Token.java
-rw-r--r--   1 wy  wheel   2363 Nov 16 19:17 TokenMgrError.class
-rw-r--r--   1 wy  wheel   4568 Nov 16 19:17 TokenMgrError.java
-rw-r--r--   1 wy  wheel    810 Nov 16 19:16 calculator_v2.jj
```

## 3. 运行示例

跟[入门示例](https://smartsi.blog.csdn.net/article/details/143640803)一样我们可以通过准备合适的输入文件并执行如下命令来运行程序：
```java
java Calculator <input.txt
```
> 在 input.txt 文件中包含输入序列

[上一篇文章](https://smartsi.blog.csdn.net/article/details/143658003)已经介绍过可能会遇到的词法错误以及解析错误，在这里我们只关注合法输入时的输出情况，此时不会抛出任何错误异常，程序正常结束时会输出整数加和的结果到控制台。假设输入文件输入的是 `123 + 456`，会在控制台看到结果 `579`：
```java
localhost:v2 wy$ cat input.txt
123 + 456
localhost:v2 wy$ java Calculator <input.txt
579
```
