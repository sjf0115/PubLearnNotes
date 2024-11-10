
## 1. 解析器规范优化

在[上一个例子](https://smartsi.blog.csdn.net/article/details/143658003)中，JavaCC 为 BNF 生产式所生成的方法，比如 `Start`，这些方法默认只是简单的检查输入是否匹配 BNF 生产式指定的规范，实际上不会把数字加起来。假设输入文件输入的是 `123 + 456`：
```java
localhost:adder wy$ cat input.txt
123 + 456
localhost:adder wy$ java Adder <input.txt
localhost:adder wy$
```
从上面可以看到解析器在输入合法时没有任何的输出，不执行任何操作仅限于检查其输入的合法性。但是，我们可以使用 Java 代码来扩展 BNF 生产式，使其在输入合法时输出整数加和的结果。JavaCC 为我们提供了框架，只需要完善框架即可实现我们想要的效果。我们将对上一个示例中的 `adder.jj` 语法文件做一些修改来扩展 BNF 生产式：
```java
/* adder.jj Adding up numbers */
options {
    STATIC = false ;
}
PARSER_BEGIN(Adder)
    class Adder {
        public static void main( String[] args ) throws ParseException, TokenMgrError {
            Adder parser = new Adder( System.in ) ;
            parser.Start() ;
        }
    }
PARSER_END(Adder)

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
在 `Start` 方法中添加了一些声明和一些 Java 代码：
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

首先第一个改动是 BNF 生产式的返回类型，以及由此生成的方法从 `void` 变为 `int`。第二个改动是，声明了可以从生成的方法中抛出 `NumberFormatException` 异常。此外我们还新增声明了三个变量，变量 `t` 为 `Token` 类型(`Token` 类是我们编译 `.jj` 文件之后生成的类)。`Token` 类的 `image` 字段记录匹配的字符串。在声明完变量之后，当 BNF 生产式匹配一个 token 时，我们可以通过为其分配引用来记录 `Token` 对象：
```java
t = <NUMBER>
```
这样我们就可以通过引用来获取 `Token` 中的信息，在这可以获取 token 匹配的数字字符串并使用 Java 语法转换为一个 Int 值：
```java
{ i = Integer.parseInt( t.image ) ; }
```

在 BNF 生产式的大括号内，我们可以添加任何我们想要的 Java 语句，这些 Java 语句在 javacc 编译生成解析器类时，将会被原封不动的复制到解析器类相应方法中。第一块是获取 token 匹配的数字并使用 `value` 变量存储：
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

由于生成的 `Start` 方法现在返回一个值，因此我们必须修改 `main` 方法，使用 val 变量接收返回值并输出到控制台：
```java
public static void main( String[] args ) throws ParseException, TokenMgrError, NumberFormatException {
  Adder parser = new Adder( System.in ) ;
  int val = parser.Start() ;
  System.out.println(val);
}
```
此外还有一个小的优化要做。如下两行在上述语法文件中出现了两次：
```java
t = <NUMBER>
{ i = Integer.parseInt( t.image ) ; }
```
虽然在这个例子中没有太大的区别，因为只涉及到两行代码，但是这种重复可能会导致后期维护问题。因此，我们将把这两行拆解成另一个 BNF 生产式，并命名为 `Primary`：
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

将前面介绍的修改保存为 `adder_v2.jj` 语法文件：
```java
options {
    STATIC = false ;
}
PARSER_BEGIN(Adder)
    class Adder {
      public static void main( String[] args ) throws ParseException, TokenMgrError, NumberFormatException {
          Adder parser = new Adder( System.in ) ;
          int val = parser.Start() ;
          System.out.println(val);
      }
    }
PARSER_END(Adder)

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

生成 `adder_v2.jj ` 文件后，我们对其调用 JavaCC 命令来生成解析器与词法分析器，详细安装与运行请查阅[JavaCC 实战一：安装与入门示例](https://smartsi.blog.csdn.net/article/details/143640803)。如下所示直接运行 `javacc adder_v2.jj` 命令：
```java
localhost:adder_v2 wy$ javacc adder_v2.jj
Java Compiler Compiler Version 7.0.13 (Parser Generator)
(type "javacc" with no arguments for help)
Reading from file adder_v2.jj . . .
File "TokenMgrError.java" does not exist.  Will create one.
File "ParseException.java" does not exist.  Will create one.
File "Token.java" does not exist.  Will create one.
File "SimpleCharStream.java" does not exist.  Will create one.
Parser generated successfully.
```
执行完之后，同之前一样都会生成 7 个 Java 文件。接下来我们对这些 java 文件进行编译，编译完成之后可得到对应的 class 文件：
```java
localhost:adder_v2 wy$ javac *.java
localhost:adder_v2 wy$
localhost:adder_v2 wy$ ll
total 200
drwxr-xr-x  17 wy  wheel    544 Nov 10 14:08 ./
drwxr-xr-x   5 wy  wheel    160 Nov 10 14:02 ../
-rw-r--r--   1 wy  wheel   5055 Nov 10 14:08 Adder.class
-rw-r--r--   1 wy  wheel   5881 Nov 10 14:07 Adder.java
-rw-r--r--   1 wy  wheel    515 Nov 10 14:08 AdderConstants.class
-rw-r--r--   1 wy  wheel    555 Nov 10 14:07 AdderConstants.java
-rw-r--r--   1 wy  wheel   5692 Nov 10 14:08 AdderTokenManager.class
-rw-r--r--   1 wy  wheel   8353 Nov 10 14:07 AdderTokenManager.java
-rw-r--r--   1 wy  wheel   2936 Nov 10 14:08 ParseException.class
-rw-r--r--   1 wy  wheel   6221 Nov 10 14:07 ParseException.java
-rw-r--r--   1 wy  wheel   6586 Nov 10 14:08 SimpleCharStream.class
-rw-r--r--   1 wy  wheel  11826 Nov 10 14:07 SimpleCharStream.java
-rw-r--r--   1 wy  wheel    985 Nov 10 14:08 Token.class
-rw-r--r--   1 wy  wheel   4070 Nov 10 14:07 Token.java
-rw-r--r--   1 wy  wheel   2363 Nov 10 14:08 TokenMgrError.class
-rw-r--r--   1 wy  wheel   4568 Nov 10 14:07 TokenMgrError.java
-rw-r--r--   1 wy  wheel    785 Nov 10 14:07 adder_v2.jj
```

## 3. 运行示例

跟[上一篇文章](https://smartsi.blog.csdn.net/article/details/143658003)一样我们可以通过准备合适的输入文件并执行如下命令来运行程序：
```java
java Adder <input.txt
```
> 在 input.txt 文件中包含输入序列

[上一篇文章](https://smartsi.blog.csdn.net/article/details/143658003)已经介绍过可能会遇到的词法错误以及解析错误，在这里我们只关注合法输入时的输出情况，此时不会抛出任何错误异常，程序正常结束时会输出整数加和的结果到控制台。假设输入文件输入的是 `123 + 456`：
```java
localhost:adder_v2 wy$ cat input.txt
123 + 456
localhost:adder_v2 wy$ java Adder <input.txt
579
```
