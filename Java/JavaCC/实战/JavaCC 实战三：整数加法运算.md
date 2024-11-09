
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
PARSER BEGIN(Adder)
    class Adder {
        static void main( String[] args ) throws ParseException, TokenMgrError {
            Adder parser = new Adder( System.in ) ;
            parser.Start() ;
    }
}
PARSER END(Adder)
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
```
123 + 456\n
```
生成的词法分析器会包含七个 Token：一个 NUMBER、一个空格、一个 PLUS、另一个空格、另一个 NUMBER、一个换行符以及一个 EOF。其中，正则表达式实例指定为 SKIP 的 Token 不会传递给解析器，因此解析器只能看到如下序列：

```
NUMBER, PLUS, NUMBER, EOF
```

假设不是一个合法的输入文件，而是一个包含意外字符的文件，如下所示：

```
123 - 456\n
```

找到第一个空格后，词法分析器会遇到一个负号。由于指定的 Token 不能以减号开头，因此词法分析器将抛出 TokenMgrError 类异常。现在，如果输入包含字符序列呢？

```
123 ++ 456\n
```

这一次，序列词法分析器仍然可以传递一个 Token 序列：

```
NUMBER, PLUS, PLUS, NUMBER, EOF
```

词法分析器不能决定 Token 序列是否合理，这通常是由解析器决定的。在词法分析器交付第二个 `PLUS` Token 之后，我们指定的解析器会检测错误，并且在此之后不再从词法分析器请求任何 Token。因此，传递给解析器的 Token 实际序列为：

```
NUMBER, PLUS, PLUS
```

跳过一个字符或字符序列并不等同于忽略它。考虑如下一个输入序列：

```
123 456\n
```

针对上述序列，词法分析器会识别出三个 Token：两个 `NUMBER` Token 以及中间的对应空格字符的 Token，同样解析器也会检测出错误（缺少了 `PLUS` Token）。



### 1.3 指定解析器

解析器的规范由所谓的 BNF 定义，这看起来有点像 Java 方法定义：

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

## 2. 生成解析器和词法分析器

构造 `adder.jj ` 文件后，我们对其调用 JavaCC。具体怎么做这取决于操作系统。在 Windows NT、2000和
XP 中具体如何操作如下所示。首先使用'命令提示符'程序(CMD.EXE)运行 JavaCC：
```
D:\home\JavaCC-Book\adder>javacc adder.jj
Java Compiler Compiler Version 2.1 (Parser Generator)
Copyright (c) 1996-2001 Sun Microsystems, Inc.
Copyright (c) 1997-2001 WebGain, Inc.
(type "javacc" with no arguments for help)
Reading from file adder.jj . . .
File "TokenMgrError.java" does not exist. Will create one.
File "ParseException.java" does not exist. Will create one.
File "Token.java" does not exist. Will create one.
File "SimpleCharStream.java" does not exist. Will create one.
Parser generated successfully
```
这将生成七个 Java 类，每个类都在自己的文件中：
- TokenMgrError 是一个简单的错误类，在词法分析器检测到错误时使用，是 Throwable 的子类。
- ParseException 是另一个错误类，在解析器检测到的错误时使用，是 Exception 的子类，因此也是 Throwable 的子类。
- Token 是一个表示 Token 的类。每个 Token 对象都有一个整数字段 kind 表示 Token 的类型(`PLUS`、`NUMBER` 或 `EOF`)以及一个字符串字段
image 用来表示 Token 对应输入文件中的字符序列。
- SimpleCharStream 是一个适配器类，将字符传递给词法分析器。
- AdderConstants 是一个接口，定义了在词法分析器和解析器使用到的类个数。
- AdderTokenManager 是词法分析器。
- Adder 是解析器。

现在我们可以用 Java 编译器编译这些类：
```
D:\home\JavaCC-Book\adder> javac *.java
```

### 1.2.5 运行示例

现在让我们再看一下 Adder 类中的主方法：
```java
static void main( String[] args ) throws ParseException, TokenMgrError {
  Adder parser = new Adder( System.in ) ;
  parser.Start() ;
}
```
首先注意到 main 方法可能会抛出 Throwable 任意两个生成子类。这样抛出异常的风格不是很好，因为应该捕捉这些异常，但是，这样写可以让第一个例子保持简短和整洁。主体的第一个语句是创建一个新的解析器对象。所使用的构造函数是自动生成并接受一个 InputStream 对象。此外还有一个接收 Reader 对象的构造函数。构造函数依次构造生成 SimpleCharacterStream 类的实例和 AdderTokenManager 类的词法分析器对象。因此，结果是解析器从词法分析器获取 Token(通过一个 SimpleCharacterStream 对象从 System.in 读取字符)。第二个语句调用一个名为 Start 的生成方法。对于在规范中的每个 BNF 实例，JavaCC 都会在解析器类中生成相应的方法。这个方法尝试在输入流中查找与输入描述匹配的内容。在本例中，调用 Start 方法会让解析器尝试在输入中查找 Token 序列来与如下规范匹配：
```
<NUMBER> (<PLUS> <NUMBER>)* <EOF>
```
我们可以通过准备合适的输入文件并执行如下命令来运行程序：
```
D:\home\JavaCC-Book\adder>java Adder <input.txt
```
当我们给定的输入文件并运行主程序时，可能会发生以下三种情况。

第一种是出现一个词法错误。在本例中，只有在输入中出现意外字符时才会发生词法错误。例如通过在输入文件中包含 `123 - 456\n` 输入时，可以产生词法错误。在这种情况下，程序将抛出 `TokenMgrError`。异常的 `message` 信息是 `Exception in thread "main" TokenMgrError: Lexical error at line 1,
column 5. Encountered: "-" (45), after : ""`

第二种是出现有一个解析错误。当 Token 序列与 Start 的规范不匹配时，就会发生这种情况。例如 `123 ++ 456\n` 或者 `123 456\n` 或者 `\n`。在这种情况下，程序将抛出一个 ParseException。第一个示例的异常 `message` 信息是：
```
Exception in thread "main" ParseException: Encountered "+" at
line 1, column 6.
Was expecting:
<NUMBER> ...
```

第三种情况是输入包含一系列符合 Start 规范的 Token。在这种情况下，不会抛出异常，程序只是终止。

在这由于该解析器在输入合法时不执行任何操作，因此它的用途仅限于检查其输入的合法性。在下一节中，我们将进行一些修改，使解析器更有用。

### 1.2.6 The generated code

要了解 JavaCC 是如何生成解析器的，那么有必要查看一些生成的代码：
```
final public void Start() throws ParseException {
jj consume token(NUMBER);
label 1:
while (true) {
jj consume token(PLUS);
jj consume token(NUMBER);
switch ((jj ntk == -1) ? jj ntk() : jj ntk) {
case PLUS:
;
break;
default:
jj la1[0] = jj gen;
break label 1; } }
jj consume token(0);
}
```
`jj_consume_token` 方法将 Token 类型作为参数，并尝试从词法分析器获取该类型的 Token。如果下一个 Token 具有不同的类型，则抛出异常。表达式`(jj_ntk == -1) ? jj_ntk() : jj_ntk` 计算下一个未读取 Token 的类型。最后一行尝试获取类型为 0 的 Token，因为 JavaCC 总是使用 0 来编码EOF令牌的类型


### 1.2.7 扩展解析器

JavaCC为 BNF 实例(如 `Start` 的)生成的方法在默认情况下只是检查输入是否与规范匹配。但是，我们可以用 Java 代码来扩展 BNF 实例，使其包含在生成的方法中。JavaCC 提供了框架。只需要我们来完善框架即可。我们将对规范文件做一些修改来获得 `adder1.jj`。我们在 BNF 实例 `Start` 中添加了一些声明和一些 Java 代码。

```
```

首先，BNF 生成的返回类型，以及由此生成的方法，从 void 变为 int。我们已经声明了可以从生成的方法中抛出 NumberFormatException。我们声明了三个变量。变量 `t` 为类 Token 的类型，它是一个表示 Token 的生成类。Token 类的 image 字段记录匹配的字符串。当在 BNF 实例中匹配一个 Token 时，我们可以通过为其分配引用来记录 Token 对象，如下所示：
```
t = <NUMBER>
```
在 BNF 实例的大括号内，我们可以添加任何我们想要的 Java 语句，这些语句基本上逐字复制到生成的方法中。由于生成的 Start 方法现在返回一个值，我们必须修改 main 方法：
```java
static void main( String[] args ) throws ParseException, TokenMgrError, NumberFormatException {
  Adder parser = new Adder( System.in ) ;
  int val = parser.Start() ;
  System.out.println(val);
}
```
还有一个小的优化要做。如下两行：
```
t = <NUMBER>
{ i = Integer.parseInt( t.image ) ; }
```
出现过两次。虽然在这种情况下没有太大的区别，因为只涉及到两行代码，但这种重复可能会导致维护问题。因此，我们将把这两行拆解成另一个 BNF 实例，并命名为 Primary：
```

```
查看生成的方法可以看到JavaCC如何将Java声明和语句集成到生成方法的框架中。
```
```

稍后我们将看到将参数传递到 BNF 实例中也是可以的。
