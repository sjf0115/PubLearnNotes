---
layout: post
author: smartsi
title: ANTLR4 入门项目-计算器
date: 2020-09-12 15:15:01
tags:
  - Antlr

categories: Antlr
permalink: antlr-starter-project-calculator
---


这一篇文章主要通过一个实际的例子来学习 ANTLR 的语法。我们以计算器作为 ANTLR 学习的入门项目，需要实现的功能效果如下：
```
193
1+2*4-5
1+2*3+(3+1)*2
a = 5
b = 6
a+b*2
```
为了简单起见，我们只允许基本的算术操作符（加减乘除）、圆括号、整数以及变量出现。算数表达式限制浮点数的使用，只允许整数的出现。

## 1. 定义 g4 语法文件

计算器应用程序就是一系列语句，每个语句都由换行符终止。一个语句可以是一个表达式、一个赋值语句或者是一个空行。构建这样一个应用程序首先要创建一个能够解析这样语句的 ANTLR 语法。一般将非常大的语法文件拆分为两部分：词法分析器的词法规则文件以及语法分析器的语法规则文件。做这样的拆分主要考虑到，在不同语言的词法规则中，有相当大的一部分是重复的。例如，不同语言的标识符和数字定义通常是相同的。将词法规则重构并抽取出来成为一个模块，这样就可以将它应用于不同的语法分析器中。

### 1.1 定义词法规则文件

下面定义了一个名为 CommonLexerRules 的词法分析器词法规则文件，注意词法规则语法是 `lexer grammar` 前缀：
> CommonLexerRules.g4

```
lexer grammar CommonLexerRules; // 定义一个名为 CommonLexerRules 的词法分析器词法规则语法

ID      : [a-zA-Z]+ ;           // 匹配大小写字母组成的标识符
INT     : [0-9]+ ;              // 匹配整数组成的标识符
NEWLINE : '\r'? '\n' ;          // 新行
WS      : [ \t\r\n]+ -> skip ;  // 忽略空格、Tab、换行以及\r
```

上述词法规则文件中定义了包括 ID（标识符）、INT（整数）、NEWLINE（新行）以及 WS（忽略空格、Tab、换行以及`\r`）这样描述词条的规则，词法规则都以大写字母开头。

此外我们为运算符这样的词条定义一些名字，这样在后面的访问器中就可以将这些词条的名字当做 Java 常量来引用：
```
EQL     :   '=' ;  // 等于
MUL     :   '*' ;  // 乘法
DIV     :   '/' ;  // 除法
ADD     :   '+' ;  // 加法
SUB     :   '-' ;  // 减法
```
例如，`MUL : '*' ;` 将语法中的 `*` 命名为 MUL。

经过上述配置后，最终的词法规则文件如下所示：
> CommonLexerRules.g4
```
lexer grammar CommonLexerRules; // 定义一个名为 CommonLexerRules 的词法分析器语法

ID      :   [a-zA-Z]+ ;           // 匹配大小写字母组成的标识符
INT     :   [0-9]+ ;              // 匹配整数组成的标识符
NEWLINE :   '\r'? '\n' ;          // 新行
WS      :   [ \t\r\n]+ -> skip ;  // 忽略空格、Tab、换行以及\r
EQL     :   '=' ;                 // 等于
MUL     :   '*' ;                 // 乘法
DIV     :   '/' ;                 // 除法
ADD     :   '+' ;                 // 加法
SUB     :   '-' ;                 // 减法
```
> CommonLexerRules.g4 词法文件放在 antlr4 下的 imports 目录中。

现在就可以将原先的语法中的那些词法规则替换为一个 `import` 语句了，具体见下面的语法规则文件。

### 1.2 定义语法规则文件

下面定义了一个名为 Calculator 的语法分析器语法规则文件，注意语法规则语法是 `grammar` 前缀：
> Calculator.g4
```
// 语法文件通常以 grammar 关键词开头 语法名称为 Calculator 所以文件名称也必须为 Calculator
grammar Calculator ;

import CommonLexerRules ; // 引入 CommonLexerRules.g4 文件中的全部词法规则

prog:   stat+ ;

stat:   expr NEWLINE
    |   ID '=' expr NEWLINE
    |   NEWLINE
    ;

expr:   expr op=('*'|'/') expr
    |   expr op=('+'|'-') expr
    |   INT
    |   ID
    |   '(' expr ')'
    ;
```

语法规则文件中定了包括 prog、stat 以及 expr 这样的描述语法结构的规则，语法规则都以小写字母开头；我们使用 `|` 分割同一个规则的不同备份分支，使用圆括号把一些词条组合成子规则。例如，子规则 `('*' | '/')` 匹配一个乘法符或者一个除法符号。

在开始使用之前，我们可以先对语法做少量的修改。首先给备选分支添加上标签，可以是任意标识符，只要他们不与规则名冲突即可。如果备选分支上面没有标签，ANTLR 就只为每条规则生成一个方法。在这个例子中，希望每个备选分支都有不同的访问器方法，这样就可以对每种输入都获得一个不同的事件。标签以 `#` 开头，并放置在备选分支的右侧，如下为 stat 和 expr 规则的每个备选分支添加标签：
```
stat:   expr NEWLINE                # printExpr // 标签以 # 开头
    |   ID '=' expr NEWLINE         # assign
    |   NEWLINE                     # blank
    ;

expr:   expr op=('*'|'/') expr      # MulDiv
    |   expr op=('+'|'-') expr      # AddSub
    |   INT                         # int
    |   ID                          # id
    |   '(' expr ')'                # parens
    ;
```
经过上述配置后，最终的语法规则文件如下所示：
> Calculator.g4
```
// 语法文件通常以 grammar 关键词开头 语法名称为 Calculator 所以文件名称也必须为 Calculator
grammar Calculator;

import CommonLexerRules ; // 引入 CommonLexerRules.g4 文件中的全部词法规则

prog:   stat+ ;

stat:   expr NEWLINE                # printExpr // 标签以 # 开头
    |   ID '=' expr NEWLINE         # assign
    |   NEWLINE                     # blank
    ;

expr:   expr op=('*'|'/') expr      # MulDiv
    |   expr op=('+'|'-') expr      # AddSub
    |   INT                         # int
    |   ID                          # id
    |   '(' expr ')'                # parens
    ;
```

最终语法文件布局如下所示：

![](1)

## 2. 测试语法文件

上面定义了语法文件并简单进行了解释。如果使用命令行，测试语法最简单的方式就是使用内置的 TestRig 命令；如果是在 IDEA 中，只需要在语法规则 `prog` 处选中 `prog` 并右击鼠标后，点击 `Test Rule r` 即可，如下图所示：

![](2)

然后在左下方框输入文本信息，在右下方框中便会显示对应的语法分析树：

![](3)

## 3. 与 Java 程序集成

使用测试组件开发和测试语法是一种不错的方法，不过最终，我们还是需要 ANTLR 为我们自动生成词法分析器和语法分析器，并集成到 Java 程序中。

### 3.1 自动生成 Java 文件

我们使用 Maven 提供的 `antlr4-maven-plugin`（详细请参阅 [ANTLR4 在 IDEA 中使用 ANTLR 与 Java 程序集成](https://smartsi.blog.csdn.net/article/details/128521224)）插件来自动解析 ANTLR4 语法文件(`.g4`)并将它们转换为 Java 源文件。使用如下的 pom 插件配置：
```xml
<plugin>
    <groupId>org.antlr</groupId>
    <artifactId>antlr4-maven-plugin</artifactId>
    <executions>
        <execution>
            <id>antlr</id>
            <goals>
                <goal>antlr4</goal>
            </goals>
            <phase>generate-sources</phase>
        </execution>
    </executions>
    <configuration>
        <!-- ANTLR 导入文件所在目录 -->
        <libDirectory>${basedir}/src/main/antlr4/imports</libDirectory>
        <!-- ANTLR 语法文件(*.g4)所在目录 -->
        <sourceDirectory>${basedir}/src/main/antlr4</sourceDirectory>
        <!-- 指定生成 Java 文件的输出目录 -->
        <!-- Java 文件输出测试目录 -->
         <outputDirectory>${basedir}/src/main/generated-sources/antlr4</outputDirectory>
        <!-- 生成语分析法树监听器代码 -->
        <listener>true</listener>
        <!-- 生成语法分析树访问器代码 -->
        <visitor>true</visitor>
        <!-- 将 Warning 视为 Error -->
        <treatWarningsAsErrors>true</treatWarningsAsErrors>
    </configuration>
</plugin>
```

当 mvn 命令执行时，`${basedir}/src/main/antlr4` 下的 `Calculator.g4` 语法文件将被分析并转换为输出目录 `${basedir}/src/main/generated-sources/antlr4` 下的 Java 源码：

![](4)

ANTLR 自动生成了很多文件，下面简单介绍一下生成的文件。

ANTLR 能够自动识别出我们语法文件中的词法规则和语法规则。`CalculatorLexer.java` 文件包含的是词法分析器类的定义，它是由 ANTLR 通过分析词法规则 ID、INT、WS、NEWLINE 等，以及语法中的字面值 '='、'+'，和 '-' 等生成的。词法分析器的作用是将输入字符序列分解成词条。CalculatorLexer 类如下所示：
```java
public class CalculatorLexer extends Lexer {
    ...
}
```

`CalculatorParser.java` 文件包含一个语法分析器类的定义，这个语法分析器专门用来识别我们的 `prog`、`stat` 以及 `expr` 语法。在该类中，每条规则都有对应的方法，除此之外，还有一些其他的辅助代码。CalculatorParser 类如下所示：
```java
public class CalculatorParser extends Parser {
    ...
    public final ProgContext prog() throws RecognitionException {
        ...
    }
    public final StatContext stat() throws RecognitionException {
        ...
    }
    public final ExprContext expr() throws RecognitionException {
       ...
    }
    ...
}
```

ANTLR 会给每个我们定义的词条指定一个数字形式的类型，然后将它们的对应关系存储于 `Calculator.tokens` 文件中：
```
MUL=4
DIV=5
ADD=6
SUB=7
ID=8
INT=9
NEWLINE=10
WS=11
'='=1
'('=2
')'=3
'*'=4
'/'=5
'+'=6
'-'=7
```
有时，我们需要将一个大型语法切分为多个更小的语法，在这种情况下，这个文件就非常有用了。通过它，ANTLR 可以在多个小型语法间同步全部的词条的类型。

默认情况下，ANTLR 生成的语法分析器能将输入文本转换为一棵语法分析树。在遍历语法分析树时，遍历器能够触发一系列'事件'（回调），并通知我们提供的监听器对象。`CalculatorListener` 接口给出了这些回调方法的定义，我们可以实现它来完成自定义的功能。`CalculatorBaseListener` 是该接口的默认实现类，为其中的每个方法提供了一个空实现，使得我们只需要覆盖那些我们感兴趣的回调方法。

### 3.2 利用访问器构造计算器功能

现在需要一个能够遍历语法分析树、计算并返回结果的访问器。ANTLR 为我们自动生成了一个访问器接口 CalculatorVisitor，并为规则中每个带标签的备选分支生成了一个方法：
```java
public interface CalculatorVisitor<T> extends ParseTreeVisitor<T> {
	T visitProg(CalculatorParser.ProgContext ctx);
	T visitPrintExpr(CalculatorParser.PrintExprContext ctx);
	T visitAssign(CalculatorParser.AssignContext ctx);
	T visitBlank(CalculatorParser.BlankContext ctx);
	T visitParens(CalculatorParser.ParensContext ctx);
	T visitMulDiv(CalculatorParser.MulDivContext ctx);
	T visitAddSub(CalculatorParser.AddSubContext ctx);
	T visitId(CalculatorParser.IdContext ctx);
	T visitInt(CalculatorParser.IntContext ctx);
}
```
该接口使用了 Java 的泛型定义，参数化的类型是 visit 方法的返回值。

ANTLR 也生成了一个该访问器的默认实现类 CalculatorBaseVisitor：
```java
public class CalculatorBaseVisitor<T> extends AbstractParseTreeVisitor<T> implements CalculatorVisitor<T> {
	@Override public T visitProg(CalculatorParser.ProgContext ctx) { return visitChildren(ctx); }
	@Override public T visitPrintExpr(CalculatorParser.PrintExprContext ctx) { return visitChildren(ctx); }
	@Override public T visitAssign(CalculatorParser.AssignContext ctx) { return visitChildren(ctx); }
	@Override public T visitBlank(CalculatorParser.BlankContext ctx) { return visitChildren(ctx); }
	@Override public T visitParens(CalculatorParser.ParensContext ctx) { return visitChildren(ctx); }
	@Override public T visitMulDiv(CalculatorParser.MulDivContext ctx) { return visitChildren(ctx); }
	@Override public T visitAddSub(CalculatorParser.AddSubContext ctx) { return visitChildren(ctx); }
	@Override public T visitId(CalculatorParser.IdContext ctx) { return visitChildren(ctx); }
	@Override public T visitInt(CalculatorParser.IntContext ctx) { return visitChildren(ctx); }
}
```
由于我们的计算器只提供整数的计算，因此我们自定义的 CalcVisitor 类应该继承 `CalculatorBaseVisitor<Integer>` 类，为完成计算器的功能，我们覆盖了访问器中表达式和赋值语句规则对应的方法：
```java
public class CalcVisitor extends CalculatorBaseVisitor<Integer> {
    // 计数器内存 存放变量名和变量值的关系
    private HashMap<String, Integer> memory = new HashMap<>();

    // expr NEWLINE 备选分支 printExpr 标签
    @Override
    public Integer visitPrintExpr(CalculatorParser.PrintExprContext ctx) {
        // 表达式
        String text = ctx.expr().getText();
        // 计算表达式的值
        Integer value = visit(ctx.expr());
        System.out.println(text + "=" + value);
        // 返回值无所谓
        return value;
    }

    // ID '=' expr NEWLINE 备选分支 assign 标签
    @Override
    public Integer visitAssign(CalculatorParser.AssignContext ctx) {
        // 获取 ID 值
        String id = ctx.ID().getText();
        // 计算右侧表达式的值
        Integer value = visit(ctx.expr());
        // 由于是赋值语句 将映射关系存入 memory 变量中
        memory.put(id, value);
        return value;
    }

    // NEWLINE 备选分支 blank 标签
    @Override
    public Integer visitBlank(CalculatorParser.BlankContext ctx) {
        return 0;
    }

    // expr op=('*'|'/') expr 备选分支 MulDiv
    @Override
    public Integer visitMulDiv(CalculatorParser.MulDivContext ctx) {
        // 左侧的数
        Integer left = visit(ctx.expr(0));
        // 右侧的数
        Integer right = visit(ctx.expr(1));
        // 运算
        if (ctx.op.getType() == CalculatorParser.MUL) {
            return left * right;
        } else {
            return left / right;
        }
    }

    // expr op=('+'|'-') expr 备选分支 AddSub
    @Override
    public Integer visitAddSub(CalculatorParser.AddSubContext ctx) {
        // 左侧的数
        Integer left = visit(ctx.expr(0));
        // 右侧的数
        Integer right = visit(ctx.expr(1));
        // 运算
        if (ctx.op.getType() == CalculatorParser.ADD) {
            return left + right;
        } else {
            return left - right;
        }
    }

    // INT 备选分支 int
    @Override
    public Integer visitInt(CalculatorParser.IntContext ctx) {
        // 计算 INT 的值
        String value = ctx.INT().getText();
        return Integer.parseInt(value);
    }

    // ID 备选分支 id
    @Override
    public Integer visitId(CalculatorParser.IdContext ctx) {
        // 获取 ID 变量
        String id = ctx.ID().getText();
        // 获取 ID 变量对应的值
        if (memory.containsKey(id)) {
            // 是否是赋值语句
            return memory.get(id);
        }
        return 0;
    }

    // '(' expr ')' 备选分支 parens
    @Override
    public Integer visitParens(CalculatorParser.ParensContext ctx) {
        return visit(ctx.expr());
    }
}
```
### 3.3 驱动类

Main 函数打印输出结果类：
```java
public class Calc {
    public static void main(String[] args) {
        String input = "a = 2\nb = 3\n1 + a * b + (3 + 1) * 2\n";

        // 1. 新建一个 CharStream 从字符串中读取数据
        CharStream charStream = CharStreams.fromString(input);
        // 新建一个 CharStream 从标准输入中读取数据
        // CharStream charStream = CharStreams.fromStream(System.in);

        // 2. 创建词法分析器
        CalculatorLexer lexer = new CalculatorLexer(charStream);

        // 3. 创建词法符号缓冲区对象
        CommonTokenStream tokens = new CommonTokenStream(lexer);

        // 4. 创建语法分析器
        CalculatorParser parser = new CalculatorParser(tokens);

        // 5. 针对 prog 语法规则 开始语法分析
        CalculatorParser.ProgContext tree = parser.prog();

        //5. 打印 语法分析树
        System.out.println(tree.toStringTree(parser));

        // 6. 访问器模式执行
        CalcVisitor visitor = new CalcVisitor();
        visitor.visit(tree);
    }
}
```
首先为词法分析器新建了一个处理字符的字符流 CharStream，从字符串中读取数据。然后创建词法分析器 lexer、语法分析器 parser 以及两者之间的词条流 tokens。有了语法分析器之后，针对 prog 语法规则开始真正的语法分析。最后两部分是输出：一是以文本形式的将规则 prog 返回的语法分析树打印出来，二是自定义一个访问器，调用 visit 方法，开始遍历 prog 方法返回语法分析树。

输出如下结果：
```
(prog (stat a = (expr 2) \n) (stat b = (expr 3) \n) (stat (expr (expr (expr 1) + (expr (expr a) * (expr b))) + (expr (expr ( (expr (expr 3) + (expr 1)) )) * (expr 2))) \n))
1+a*b+(3+1)*2=15
```







。。。
