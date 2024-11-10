在[上一篇文章](https://smartsi.blog.csdn.net/article/details/143661219)中我们实现了一个只支持整数加法运算的运算器，在这里我们再给运算器添加支持小数加法运算的能力。

## 1. 编写语法文件

你可以使用你喜欢的文本编辑器创建和编辑语法文件。在这我们创建一个 `adder_double.jj` 语法文件。在本节的其余部分中，代码示例将是 `adder_double.jj` 的文件的一部分内容。这个文件包含了用于解析器和词法分析器的 JavaCC 规范，并被用作 JavaCC 程序的输入。

### 1.1 选项和类声明

文件 `adder_double.jj` 的第一部分 还是和以前一样:
```java
options {
  STATIC = false ;
}
PARSER_BEGIN(AdderDouble)
  import java.io.PrintStream ;
  class AdderDouble {
      public static void main( String[] args ) throws ParseException, TokenMgrError, NumberFormatException {
          AdderDouble parser = new AdderDouble( System.in ) ;
          parser.Start(System.out) ;
      }
      double previousValue = 0.0 ;
  }
PARSER END(AdderDouble)
```
AdderDouble 类的 `previousValue` 字段用于存储前一行的计算结果，我们将在后续版本中使用它，可以使用美元符号来表示它。`import` 语句说明可以在 `PARSER BEGIN` 和 `PARSER END` 括号之间进行 `import` 声明。这些会被复制到生成的解析器和 Token 管理器类中。也可以使用包声明，并将其复制到所有的生成类中。

### 1.3.2 词法规范

词法分析器的规范稍有变化。首先声明结束行为一个 `TOKEN` 并给定一个符号名称，以便将其传递给解析器。
```java
SKIP : { " " }
TOKEN : { < EOL : "\n" | "\r" | "\r\n" > }
TOKEN : { < PLUS : "+" > }
```
第二，我们允许在数字中使用小数点。我们将 NUMBER 类型的 Token 更改为数字中允许有小数点。我们用竖线分割了四个选项，分别是：没有小数点，小数点在中间，小数点在末尾，小数点在开始。一个完美的规范如下所示：
```java
TOKEN { < NUMBER : (["0"-"9"])+ | (["0"-"9"])+ "." (["0"-"9"])+ | (["0"-"9"])+ "." | "." (["0"-"9"])+ > }
```
如上面所示同一个正则表达式出现了多次。为了可读性，最好给这样的正则表达式起一个符号名称。我们可以为正则表达式起一个名称，只是词法分析器的一个局部名称；这样的名称不表示 Token 类型。
```java
TOKEN : { < NUMBER : <DIGITS> | <DIGITS> "." <DIGITS> | <DIGITS> "." | "." <DIGITS> > }
TOKEN : { < #DIGITS : (["0"-"9"])+ > }
```

### 1.3.3 解析器规范

解析器的输入由零或多行组成的序列组成，每行包含一个表达式。使用 BNF 符号（将在下一章中进一步解释），我们可以写成
```
Start --> (Expression EOL) * EOF
```
这给了我们 Start BNF 的骨架：
```
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
我们用Java操作对这个框架进行扩充，以记录和打印每行的结果。
