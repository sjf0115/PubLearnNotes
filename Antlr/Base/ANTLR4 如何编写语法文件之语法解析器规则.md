---
layout: post
author: smartsi
title: ANTLR4 如何编写语法文件之语法解析器规则
date: 2023-01-04 23:15:01
tags:
  - Antlr

categories: Antlr
permalink: antlr-parser-rules
---

语法解析器由位于语法解析器规则语法或者混合语法中的一组解析器规则组成。Java 应用程序通过调用由 ANTLR 自动生成的、与所需的启动规则相对应的规则函数来启动语法解析器。规则最基本的形式包含规则名称，以及后跟一个以分号结尾的备选分支名称：
```
/** Javadoc comment can precede rule */
retstat : 'return' expr ';' ;
```
规则中还可以包含以 `|` 分隔的备选分支：
```
operator:
 	stat: retstat
 	| 'break' ';'
 	| 'continue' ';'
 	;
```
备选分支是一组规则元素的列表，也可以为空。例如，如下有一个空的备选分支的规则，从而使规则成为一条可选规则：
```
superClass
 	: 'extends' ID
 	| // empty means other alternative(s) are optional
 	;
```

## 1. 备选分支标签

为了获得更加精确的语法解析器监听器事件，可以通过使用 `#` 标记规则的最外层备选分支。如果备选分支上没有标签，ANTLR 为规则只生成一个方法。通过标签，可以使每个备选分支都有不同的访问器方法，从而对每种输入都获得一个不同的事件。一条规则中的备选分支要么全带上标签，要么全部不带标签：
```
grammar A;
stat: 'return' e ';' # Return
 	| 'break' ';' # Break
 	;

e   : e '*' e # Mult
    | e '+' e # Add
    | INT # Int
    ;
```
备选分支标签不必一定在行尾，`#` 符号后的空格也不是必须得。ANTLR 会为每个标签生成一个规则上下文类。下面是 ANTLR 为上面语法 `A` 生成的监听器：
```java
public interface AListener extends ParseTreeListener {
 	void enterReturn(AParser.ReturnContext ctx);
 	void exitReturn(AParser.ReturnContext ctx);
 	void enterBreak(AParser.BreakContext ctx);
 	void exitBreak(AParser.BreakContext ctx);
 	void enterMult(AParser.MultContext ctx);
 	void exitMult(AParser.MultContext ctx);
 	void enterAdd(AParser.AddContext ctx);
 	void exitAdd(AParser.AddContext ctx);
 	void enterInt(AParser.IntContext ctx);
 	void exitInt(AParser.IntContext ctx);
}
```
> 为每个标签生成了一个规则上下文类，例如 Return 标签的 AParser.ReturnContext 类

为每个带标签的备选分支生成一个进入和退出方法，例如 Return 标签的 `enterReturn` 和 `exitReturn`。这些方法的参数类型取决于备选分支本身，即备选分支标签的规则上下文类，例如 AParser.ReturnContext。

可以在多个备选分支上使用相同的标签，从而指示解析树遍历器为这些备选分支触发相同的事件。例如，下面是上面语法 `A` 中规则 `e` 的变体，复用了 BinaryOp 标签：
```
e : e '*' e # BinaryOp
 	| e '+' e # BinaryOp
 	| INT # Int
 	;
```
ANTLR会为 `e` 生成以下监听器方法:
```java
void enterBinaryOp(AParser.BinaryOpContext ctx);
void exitBinaryOp(AParser.BinaryOpContext ctx);
void enterInt(AParser.IntContext ctx);
void exitInt(AParser.IntContext ctx);
```
如果备选分支标签名称与规则名称冲突，ANTLR 会报错 `rule alt label xxx conflicts with rule xxx`。下面是规则 `e` 的另一个重写，其中两个备选分支标签名称与规则名称冲突：
```
e : e '*' e # e
| e '+' e # Stat
| INT # Int
;
```
规则上下文类是通过规则名称或者备选分支标签名称生成的，因此标签 Stat 与规则 Stat 发生冲突：
```
$ antlr4 A.g4
 	error(124): A.g4:5:23: rule alt label e conflicts with rule e
 	error(124): A.g4:6:23: rule alt label Stat conflicts with rule stat
 	warning(125): A.g4:2:13: implicit definition of token INT in parser
```

## 2. 规则上下文对象

ANTLR 自动生成方法来访问与每个规则引用所关联的规则上下文对象(解析树节点)。对于只包含一个规则引用的规则，ANTLR 生成一个不带参数的方法。如下规则所示：
```
inc : e '++' ;
```
ANTLR 生成这个上下文类：
```java
public static class IncContext extends ParserRuleContext {
 	public EContext e() { ... } // return context object associated with e
 	...
}
```
当一个规则有多个引用时，ANTLR 也支持对上下文对象的访问：
```
field : e '.' e ;
```
ANTLR 生成一个带索引值的方法来访问第 i 个元素（参数是访问第 i 个规则元素的索引值），另外还生成一个方法返回该规则所有的上下文对象：
```java
public static class FieldContext extends ParserRuleContext {
 	public EContext e(int i) { ... } // get ith e context
 	public List<EContext> e() { ... } // return ALL e contexts
 	...
}
```
如果我们有另一个引用 `field` 的规则 `s`，可以通过一个内嵌动作 `action` 来访问由 `field` 规则所有上下文对象列表（调用 `e` 方法）:
```
s : field
 	{
 	List<EContext> x = $field.ctx.e();
 	...
 	}
;
```
监听器或者访问器都可以做同样的事情。给定一个指向 FieldContext 对象的指针 `f`, `f.e()` 将返回规则所有上下文对象列表。

## 3. 规则元素标签

可以使用 `=` 符号为规则元素添加标签，以此将字段添加到规则上下文对象中：
```
stat: 'return' value=e ';' # Return
 	| 'break' ';' # Break
 	;
```
这里的 value 是规则 `e` 返回值的标签，规则 `e` 是在其他地方定义的。标签会成为语法解析树节点类中的字段。在上面例子中，由于 Return 备选分支签的原因，标签 value 成为 ReturnContext 中的一个字段：
```java
public static class ReturnContext extends StatContext {
 	public EContext value;
 	...
}
```
可以使用 `+=` 列表标签符方便的获取一组词条 `token`。例如，下面的规则创建了一个 `token` 对象列表来匹配一个简单的数组结构：
```
array : '{' el+=INT (',' el+=INT)* '}' ;
```
ANTLR 在相应的规则上下文类中生成一个 List 字段：
```java
public static class ArrayContext extends ParserRuleContext {
 	public List<Token> el = new ArrayList<Token>();
 	...
}
```
`+=` 列表标签符适用于规则引用：
```
elist : exprs+=e (',' exprs+=e)* ;
```
ANTLR 生成一个包含上下文对象列表的字段：
```java
public static class ElistContext extends ParserRuleContext {
 	public List<EContext> exprs = new ArrayList<EContext>();
 	...
 }
```

## 4. 规则元素

规则元素指定了解析器在给定时刻应该做什么，就像编程语言中的语句一样。元素可以是规则 `rule`、词条 `token`、字符串文字常量，例如表达式、ID 或者 'return'。下面是规则元素的完整列表：

| 用法  | 说明 |
| :------------- | :------------- |
| `T` | 在当前输入位置匹配词条 `T`。词条总是以大写字母开头。 |
| `'literal'` | 在当前输入位置匹配字符串文本常量。字符串文本常量就是一个由固定字符串组成的词条。|
| `r` | 在当前输入位置匹配规则 `r`，这相当于像调用函数一样调用规则。语法解析器规则名称总是以小写字母开头。|
| `r [«args»]` | 在当前输入位置匹配规则 `r`，像函数调用一样传入一组参数。方括号内的参数满足目标语言的语法，通常是逗号分隔的表达式列表。|
| `{«action»}` | 在前一个的备选分支元素之后，后一个备选分支元素之前立即执行一个动作 `action`。动作中的代码满足目标语言的语法。ANTLR 将动作中的代码逐字复制到生成的类中，除了替换属性和 `token` 引用，例如 `$x` 和 `$x.y`。|
| `{«p»}?` | |
| `.` | |


## 5. 子规则


## 6. 捕获异常


## 7. 规则属性定义


## 8. 起始规则和文件结束符











> 原文:[Parser Rules](https://github.com/antlr/antlr4/blob/master/doc/parser-rules.md)
