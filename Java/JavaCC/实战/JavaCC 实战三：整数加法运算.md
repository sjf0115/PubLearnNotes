
前两篇文章我们主要介绍了 JavaCC [安装](https://smartsi.blog.csdn.net/article/details/143640803)以及[入门介绍](https://smartsi.blog.csdn.net/article/details/143647560)。在这篇文章中介绍如何使用 Javacc 实现判断输入是否是一个合法的加法运算。在如下这个例子中，我们需要实现对如下数字进行加和：
```
99 + 42 + 0 + 15
```
并且在输入中可以允许在数字之间的任意位置出现空格或者换行符。除此之外，输入中唯一允许的字符必须是0-9之间的10个数字以及加号符号。

## 1. 编写语法文件

你可以使用你喜欢的文本编辑器创建和编辑语法文件。在这我们创建一个 `adder.jj` 语法文件。在本节的其余部分中，代码示例将是 `adder.jj` 的文件的一部分内容。这个文件包含了用于解析器和词法分析器的 JavaCC 规范，并被用作 JavaCC 程序的输入。

### 1.1 选项和类声明

`adder.jj` 文件的第一部分是选项 `options` 和类 `class` 声明，如下所示：
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
```
上面的代码可以分为两个部分，第一部分是选项 `options`，第二部分是 `PARSER_BEGIN(XXX)…… PARSER_END(XXX)` 类声明。

在第一行初始注释之后是选项 `options` 部分。除了 `STATIC` 选项，`options` 中几乎所有选项的默认值都可以适用本例子，`STATIC` 默认只为 `true`，这里需要将其修改为 `false`，使得生成的函数不是 `static` 的。接下来是一个名为 `Adder` 的 Java 类代码片段。可以看到，在这里的不是一个完整的 `Adder` 类。JavaCC 只提供类声明，其它信息 JavaCC 会根据 `.jj` 描述文件来生成。此外在该类的 main 方法声明中，抛出了两个异常类 `ParseException` 和 `TokenMgrError`，这些类也将由 JavaCC 生成。

### 1.2 词法分析器规范

稍后我们再介绍 main 方法，现在先让我们看一下词法分析器的规范。在我们这个简单的示例中只需要四行就可以指定词法分析器：
```java
SKIP : { " " }
SKIP : { "\n" | "\r" | "\r\n" }
TOKEN : { < PLUS : "+" > }
TOKEN : { < NUMBER : (["0"-"9"])+ > }
```
第一行是 `SKIP`，即告诉 JavaCC 跳过空格符(表示词法分析器会忽略空格)，也就是说它们不会传递给解析器。第二行告诉 JavaCC 要跳过换行符，并用竖线分割不同的字符序列。之所以会有几个，是因为在不同的系统中，换行符有不同的表示方式：在 Unix/Linux 系统中，换行符是 "\n"；在 Windows 系统中，换行符是 "\r"；在 Mac 系统中，换行符则是 "\r\n"。这几个换行符用一个竖线分隔，表示或的意思。第三行定义了一个名为 `PLUS` 的 Token，用它来表示加号 "+"。第四行定义了一个名为 `NUMBET` 的 Token，用它来表示正整数。如果您熟悉 Perl 或 Java 的正则表达式包下的正则表达式，那么 `NUMBER` 这个 Token 的规范就比较好理解了。我们详细看一下 `(["0"-"9"])+` 这个正则表达式，正则表达式 `["0" - "9"]` 部分可以匹配任意一个数字，即 Unicode 编码在 0 到 9 之间的任意字符。正则表达式 `(x)+` 部分可以匹配一个或多个字符串的任意字符序列，每个字符串都由正则表达式 x 匹配。因此正则表达式 `(["0" - "9"])+` 可以匹配任意一个或多个数字的序列。

> 上面四行中的每一行都称为表达生产式(`regular expression production`)。

还有一种由词法分析器生成的 Token，符号名称为 `EOF`，表示输入序列的结束。但是没有必要显式定义这个 EOF Token，因为 JavaCC 会自动处理文件的结尾。

考虑一个包含如下字符的输入：
```java
123 + 456\n
```
生成的词法分析器会包含七个 Token：一个 `NUMBER`、一个空格、一个 `PLUS`、另一个空格、另一个 `NUMBER`、一个换行符以及一个 `EOF`。其中，Token 为 `SKIP` 的不会传递给解析器，因此解析器只能看到如下序列：
```java
NUMBER, PLUS, NUMBER, EOF
```
假设不是一个合法的输入，包含了其它特殊字符，如下所示：
```java
123 - 456\n
```
找到第一个空格后，词法分析器会遇到一个负号。由于指定的 Token 没有以减号开头的，因此词法分析器将抛出 `TokenMgrError` 类异常。

如果输入包含如下字符序列呢？
```java
123 ++ 456\n
```
虽然上面的输入有问题，但是词法分析器仍然可以传递给解析器一个 Token 序列，如下所示：
```java
NUMBER, PLUS, PLUS, NUMBER, EOF
```
词法分析器无法判断 Token 序列是否合理，这通常是由解析器决定的。在词法分析器传递第二个 `PLUS` Token 给解析器之后，解析器会检测出错误(出现了连续两个 `PLUS`)。一旦检测到错误就不再从词法分析器请求任何 Token。因此，实际传递给解析器的 Token 序列为：
```java
NUMBER, PLUS, PLUS
```

跳过一个字符或字符序列并不等同于忽略它。考虑如下一个输入序列：
```java
123 456\n
```
针对上述序列，词法分析器会识别出三个 Token：两个 `NUMBER` Token 以及中间对应空格字符的 Token，同样解析器也会检测出错误（缺少了 `PLUS` Token）。

### 1.3 解析器规范

解析器的规范由 `BNF` 定义。可以看到，解析器的描述看起来有点像 Java 方法定义：
```java
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
上述 BNF 生产式指定了无错误输入时合法 Token 类型的序列。这个生产式告诉我们序列必须以 `NUMBER` Token 开头，以 `EOF` Token 结束。在 `NUMBER` 和 `EOF` Token 中间，可以是零个或者多个由 `PLUS` 和 `NUMBER` Token 组成的子序列，而且必须是 `NUMBER` 紧跟在 `PLUS` 后面。

上面的解析器规范只能让解析器检测输入序列是否无错误，实际上不会把数字加起来。后面我们会修改解析器描述文件以修正此问题，但是首先，让我们生成 Java 组件来运行检测输入序列是否有错误。

## 2. 生成解析器和词法分析器

将前面介绍的几部分合并起来保存为 `adder.jj` 语法文件：
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

生成 `adder.jj ` 文件后，我们对其调用 JavaCC 命令来生成解析器与词法分析器，详细安装与运行请查阅[JavaCC 实战一：安装与入门示例](https://smartsi.blog.csdn.net/article/details/143640803)。如下所示直接运行 `javacc adder.jj` 命令：
```java
localhost:adder wy$ javacc adder.jj
Java Compiler Compiler Version 7.0.13 (Parser Generator)
(type "javacc" with no arguments for help)
Reading from file adder.jj . . .
File "TokenMgrError.java" does not exist.  Will create one.
File "ParseException.java" does not exist.  Will create one.
File "Token.java" does not exist.  Will create one.
File "SimpleCharStream.java" does not exist.  Will create one.
Parser generated successfully.
```
执行完之后，会生成 7 个 Java 文件，如下所示：
```java
localhost:adder wy$ ll
total 120
drwxr-xr-x  10 wy  wheel    320 Nov 10 10:21 ./
drwxr-xr-x   4 wy  wheel    128 Nov 10 10:18 ../
-rw-r--r--   1 wy  wheel   5434 Nov 10 10:21 Adder.java
-rw-r--r--   1 wy  wheel    555 Nov 10 10:21 AdderConstants.java
-rw-r--r--   1 wy  wheel   8353 Nov 10 10:21 AdderTokenManager.java
-rw-r--r--   1 wy  wheel   6221 Nov 10 10:21 ParseException.java
-rw-r--r--   1 wy  wheel  11826 Nov 10 10:21 SimpleCharStream.java
-rw-r--r--   1 wy  wheel   4070 Nov 10 10:21 Token.java
-rw-r--r--   1 wy  wheel   4568 Nov 10 10:21 TokenMgrError.java
-rw-r--r--   1 wy  wheel    496 Nov 10 10:21 adder.jj
```
其中：
- `Adder` 是解析器。
- `AdderTokenManager` 是词法分析器。
- `AdderConstants` 是一个接口，里面定义了一些词法分析器和解析器中会用到的常量。
- `TokenMgrError` 是一个简单的错误类，在词法分析器检测到错误时使用，是 Throwable 的子类。
- `ParseException` 是另一个错误类，在解析器检测到的错误时使用，是 Exception 的子类，因此也是 Throwable 的子类。
- `Token` 类是一个用于表示 token 的类。每个 Token 对象都有一个整数字段 kind 表示 Token 的类型(`PLUS`、`NUMBER` 或 `EOF`)以及一个字符串字段
image 用来表示 Token 对应输入文件中的字符序列。
- `SimpleCharStream` 是一个转接器类，用于把字符传递给词法分析器。

接下来我们对这些 java 文件进行编译，编译完成之后可得到对应的 class 文件：
```java
localhost:adder wy$ javac *.java
localhost:adder wy$ ll
total 200
drwxr-xr-x  17 wy  wheel    544 Nov 10 10:31 ./
drwxr-xr-x   4 wy  wheel    128 Nov 10 10:18 ../
-rw-r--r--   1 wy  wheel   4547 Nov 10 10:31 Adder.class
-rw-r--r--   1 wy  wheel   5434 Nov 10 10:21 Adder.java
-rw-r--r--   1 wy  wheel    515 Nov 10 10:31 AdderConstants.class
-rw-r--r--   1 wy  wheel    555 Nov 10 10:21 AdderConstants.java
-rw-r--r--   1 wy  wheel   5692 Nov 10 10:31 AdderTokenManager.class
-rw-r--r--   1 wy  wheel   8353 Nov 10 10:21 AdderTokenManager.java
-rw-r--r--   1 wy  wheel   2936 Nov 10 10:31 ParseException.class
-rw-r--r--   1 wy  wheel   6221 Nov 10 10:21 ParseException.java
-rw-r--r--   1 wy  wheel   6586 Nov 10 10:31 SimpleCharStream.class
-rw-r--r--   1 wy  wheel  11826 Nov 10 10:21 SimpleCharStream.java
-rw-r--r--   1 wy  wheel    985 Nov 10 10:31 Token.class
-rw-r--r--   1 wy  wheel   4070 Nov 10 10:21 Token.java
-rw-r--r--   1 wy  wheel   2363 Nov 10 10:31 TokenMgrError.class
-rw-r--r--   1 wy  wheel   4568 Nov 10 10:21 TokenMgrError.java
-rw-r--r--   1 wy  wheel    496 Nov 10 10:21 adder.jj
```

## 3. 运行示例

现在让我们再看一下 Adder 类中的主方法：
```java
static void main( String[] args ) throws ParseException, TokenMgrError {
  Adder parser = new Adder( System.in ) ;
  parser.Start() ;
}
```
首先注意到 `main` 方法可能会抛出 `ParseException` 和 `TokenMgrError` 两个异常。这样抛出异常的风格并不是很好，更好的是应该捕捉这些异常，但是这样写可以让第本例子保持简短和整洁。

`main` 方法第一行语句创建了一个解析器 parser 对象。使用的是 Adder 类的默认构造器，接收一个 InputStream 类型对象作为输入。此外还有一个接收 Reader 对象的构造器。构造器依次创建生成 `SimpleCharacterStream` 类的实例和 `AdderTokenManager` 类的词法分析器对象。因此，结果是词法分析器通过 `SimpleCharacterStream` 实例对象从 `System.in` 中读取字符，解析器则是从词法分析器中读取 Token。

第二行语句调用词法分析器中一个名为 `Start` 的生成方法。对于在规范中的每个 BNF 生产式，JavaCC 都会在解析器类中生成相应的方法。这个方法会尝试在输入流中查找与输入描述匹配的内容。在本例中，调用 `Start` 方法会让解析器尝试在输入中查找 Token 序列来与如下规范匹配：
```java
<NUMBER> (<PLUS> <NUMBER>)* <EOF>
```

我们可以通过准备合适的输入文件并执行如下命令来运行程序：
```
java Adder <input.txt
```
> 在 input.txt 文件中包含输入序列

当我们给定输入文件并运行主程序时，可能会发生以下三种情况。

### 3.1 词法错误

第一种是出现一个词法错误。在本例中，只有在输入中出现意外字符时才会发生词法错误。假设输入文件是 `123 - 456` 输入时就会产生词法错误。在这种情况下，程序将抛出 `TokenMgrError` 错误：
```java
localhost:adder wy$ cat input.txt
123 - 456
localhost:adder wy$ java Adder <input.txt
Exception in thread "main" TokenMgrError: Lexical error at line 1, column 5.  Encountered: '-' (45),
	at AdderTokenManager.getNextToken(AdderTokenManager.java:219)
	at Adder.jj_ntk_f(Adder.java:156)
	at Adder.Start(Adder.java:13)
	at Adder.main(Adder.java:6)
```

### 3.2 解析错误

第二种是出现有一个解析错误。当 Token 序列与 `Start` 的规范不匹配时，就会发生这种情况。例如 `123 ++ 456` 或者 `123 456`。在这种情况下，程序将抛出一个 `ParseException`。假设输入文件输入的是 `123 ++ 456`：
```java
localhost:adder wy$ cat input.txt
123 ++ 456
localhost:adder wy$ java Adder <input.txt
Exception in thread "main" ParseException: Encountered " "+" "+ "" at line 1, column 6.
Was expecting:
    <NUMBER> ...

	at Adder.generateParseException(Adder.java:193)
	at Adder.jj_consume_token(Adder.java:131)
	at Adder.Start(Adder.java:23)
	at Adder.main(Adder.java:6)
```
假设输入文件输入的是 `123 456`：
```java
localhost:adder wy$ cat input.txt
123 456
localhost:adder wy$ java Adder <input.txt
Exception in thread "main" ParseException: Encountered " <NUMBER> "456 "" at line 1, column 5.
Was expecting one of:
    <EOF>
    "+" ...

	at Adder.generateParseException(Adder.java:193)
	at Adder.jj_consume_token(Adder.java:131)
	at Adder.Start(Adder.java:25)
	at Adder.main(Adder.java:6)
```

### 3.3 正常运行

第三种情况是输入包含一系列与 `Start` 规范匹配的 Token。在这种情况下，不会抛出任何错误异常，程序正常结束。假设输入文件输入的是 `123 + 456`：
```java
localhost:adder wy$ cat input.txt
123 + 456
localhost:adder wy$ java Adder <input.txt
localhost:adder wy$
```
在这由于该解析器在输入合法时不执行任何操作，因此它的用途仅限于检查其输入的合法性。在后面内容中，我们将进行一些修改，使解析器更有用。

## 4. 生成代码

要了解 JavaCC 是如何生成解析器的，那么有必要查看一些生成的代码：
```java
final public void Start() throws ParseException {
  jj_consume_token(NUMBER);
  label_1:
  while (true) {
    switch ((jj_ntk==-1)?jj_ntk_f():jj_ntk) {
    case PLUS:{
      ;
      break;
      }
    default:
      jj_la1[0] = jj_gen;
      break label_1;
    }
    jj_consume_token(PLUS);
    jj_consume_token(NUMBER);
  }
  jj_consume_token(0);
}
```
`jj_consume_token` 方法将 Token 类型作为参数，并尝试从词法分析器获取该类型的 Token。如果下一个 Token 具有不同的类型，则抛出异常。表达式`(jj_ntk == -1) ? jj_ntk_f() : jj_ntk` 计算下一个未读取 Token 的类型。最后一行尝试获取类型为 0 的 Token，因为 JavaCC 总是使用 0 来编码 `EOF` Token 的类型。
