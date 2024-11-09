




### 1.3 第二个例子:计算器

我们把加法器转换成一个只支持简单四则运算的计算器。第一步，为了使计算器更具交互性，每一行都打印出一个值。首先，我们只是把数字相加，然后再考虑其他运算，减法、乘法和除法。

#### 1.3.1 选项和类声明

文件 `calculator0.jj` 的第一部分 还是和以前一样:
```java
/* calculator0.jj An interactive calculator. */
options {
  STATIC = false ;
}
PARSER BEGIN(Calculator)
  import java.io.PrintStream ;
  class Calculator {
      static void main( String[] args )
      throws ParseException, TokenMgrError, NumberFormatException {
          Calculator parser = new Calculator( System.in ) ;
          parser.Start( System.out ) ;
      }
      double previousValue = 0.0 ;
  }
PARSER END(Calculator)
```
Calculator 类的 `previousValue` 字段用于存储前一行的计算结果，我们将在后续版本中使用它，可以使用美元符号来表示它。`import` 语句说明可以在 `PARSER BEGIN` 和 `PARSER END` 括号之间进行 `import` 声明。这些会被复制到生成的解析器和 Token 管理器类中。也可以使用包声明，并将其复制到所有的生成类中。

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



> 原文:[javacc-tutorial](https://www.engr.mun.ca/~theo/JavaCC-Tutorial/javacc-tutorial.pdf)
