
## 1. JavaCC 介绍

### 1.1 JavaCC 和解析器生成

JavaCC 是一个解析器生成器和词法分析器生成器。解析器和词法分析器是处理字符序列输入的软件组件。编译器(Compilers)和解释器(Interpreters)结合词法分析器和解析器来解密包含程序的文件，然而，词法分析器和解析器可以用于各种各样的其他应用程序，正如我希望本书中的示例将说明的那样。那么什么是解析器和词法分析器呢?词法分析器可以将字符序列分解成成为 Token 的字符子序列，同时还会对 Token 进行分类。如下是一个用C语言编写的短程序：
```c
int main() {
  return 0 ;
}
```
C 语言编译器的词法分析器会将其分解为如下 Token：
```
"int", " ", "main", "(", ")",
" ", "{", "\n", "\t", "return"
" ", "0", " ", ";", "\n",
"}", "\n", ""
```
词法分析器还会识别每个 Token 的类型。上面示例中的 Token 对应的种类分别如下所示：
```
KWINT, SPACE, ID, OPAR, CPAR,
SPACE, OBRACE, SPACE, SPACE, KWRETURN,
SPACE, OCTALCONST, SPACE, SEMICOLON, SPACE,
CBRACE, SPACE, EOF
```
EOF 类型的 Token 表示原始文件的结束。词法分析器分解出的 Token 序列会传递给解析器。在 C 语言中，解析器不需要所有的 Token。在我们的示例中，那些被分类为 SPACE 的不会传递给解析器。解析器然后分析 Token 序列来确定程序的结构。通常在编译器，解析器输出一个表示程序结构的树。然后这棵树作为编译器(负责分析和代码生成)组件的输入。如下是程序中的一条简单语句：
```
fahrenheit = 32.0 + 9.0 * celcius / 5.0 ;
```
解析器根据语言规则分析语句，并生成一个树。

> DIAGRAM TBD

词法分析器和解析器还负责在输入不符合语言的词法或句法规则时生成错误消息。

JavaCC 本身不是解析器或词法分析器，而是生成器。这意味着它根据从文件中读取的规范输出词法分析器和解析器。JavaCC 生成用 Java 编写的词法分析器和解析器。

> 见图TBD

解析器和词法分析器往往是代码非常长而且非常复杂的组件。直接用 Java 编写一个高效的词法分析器或解析器必须谨慎考虑规则之间的交互。例如，在C语言的词法分析器中，处理整数常量和浮点常量的代码不能分割，因为整数常量开始时与浮点常量相同。如果使用像 JavaCC 这样的解析器生成器，整数常量和浮点常量的规则分别编写，并在生成过程中提取它们之间的通用性。与手工编写的 Java 程序相比，这种增加的模块化意味着规范文件更容易编写、读取和修改。通过使用像 JavaCC 这样的解析器生成器，软件工程师可以节省大量的时间，聚焦软件组件本身的质量。

## 1.2 A first example — adding integers

### 1.2.4 生成解析器和词法分析器

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
Exception in thread ”main” ParseException: Encountered "+" at
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

### 1.3 第二个例子:计算器

我们将把加法器转换成一个简单的四则运算计算器。第一步，我们将使计算器更具交互性，每一行都打印出一个值。首先，我们只是把数字相加，然后再考虑其他运算，减法、乘法和除法。

#### 1.3.1 选项和类声明

文件 `calculator0.jj` 的第一部分 还是和以前一样:

> 原文:[javacc-tutorial](https://www.engr.mun.ca/~theo/JavaCC-Tutorial/javacc-tutorial.pdf)
