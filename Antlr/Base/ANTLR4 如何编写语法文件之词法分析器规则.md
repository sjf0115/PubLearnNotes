
词法分析器语法由词法分析器规则组成，分为多种模式。词汇模式允许我们将单个词法分析器语法拆分为多个子词法分析器语法。词法分析器只能返回与当前模式中的规则匹配的词法符号。

词法分析器规则指定了词法符号的定义，并与语法解析器规则的语法非常类似，但词法分析器规则不能有参数、返回值以及局部变量。词法分析器规则名称必须以大写字母开头，以区别于语法解析器规则名称：
```
/** 可选的文档注释 */
TokenName : alternative1 | ... | alternativeN ;
```

## 1. fragment 规则

你还可以定义一些不是词法符号 `token` 的规则，但是却可以在识别过程中提供词法符号的功能。这种规则需要规则名称前添加 `fragment` 符号，同时也不会生成语法解析器可见的词法符号：
```
fragment
HelperTokenRule : alternative1 | ... | alternativeN ;
```
例如，如下 `DIGIT` 规则就是一个非常常用的 `fragment` 规则：
```
INT : DIGIT+ ; // 引用 DIGIT 辅助规则
fragment DIGIT : [0-9] ; // 由于添加了 fragment 符号 所以不是一个词法符号
```

## 2. 词法模式

词法模式允许你根据上下文对词法规则进行分组，例如在 XML 标签的内和外。这就像有多个子词法分析器，每个负责一个上下文。词法分析器只能返回在当前模式下输入规则匹配的词法符号。词法分析器以所谓的默认模式开始，除非使用了 `mode` 命令，否则所有规则都被认为是默认模式：
```
rules in default mode
...
mode MODE1;
rules in MODE1
...
mode MODEN;
rules in MODEN
...
```
> 需要注意的是混合语法中不允许使用模式，只允许使用词法分析器语法。

## 3. 词法分析器规则元素

## 4. 递归词法分析器规则

与大多数词法语法工具不同，ANTLR 词法分析器规则是可以递归的。当你想要匹配嵌套的词法符号，例如嵌套的动作块 `{...{...}...}` 时，这非常方便：
```
lexer grammar Recur;

ACTION : '{' ( ACTION | ~[{}] )* '}' ;

WS : [ \r\t\n]+ -> skip ;
```

## 5. 冗余字符串常量

需要注意的是，不要在多个词法分析器规则的右侧指定相同的字符串常量。这样的字符串常量会存在歧义，可以匹配多种词法符号。语法解析器可能无法解析这些字符串常量。这同样也适用于跨模式的规则。例如，下面的词法分析器语法定义了两个具有相同字符常量的词法符号:
> L.g4
```
lexer grammar L;
AND : '&' ;
mode STR;
MASK : '&' ;
```
语法解析器语法不能引用字符串常量 '&'，但它可以引用词法符号的名称：
> P.g4
```
parser grammar P;
options { tokenVocab=L; }
a : '&' // 引发一个错误 找不到词法符号
    AND // no problem
    MASK // no problem
  ;
```

如下所示进行构建和测试：
```
$ antlr4 L.g4 # yields L.tokens file needed by tokenVocab option in P.g4
$ antlr4 P.g4
error(126): P.g4:3:4: cannot create implicit token for string literal '&' in non-combined grammar
```

## 6. 词法分析器规则动作

ANTLR 词法分析器在匹配到一条词法规则后会创建一个 Token 对象。每个词法符号的请求都从 Lexer.nextToken 开始，对每个识别到的词法符号都会调用一次 emit。Emit 从词法分析器的当前状态中收集信息来构建词法符号。它可以访问字段 `_type`，`_text`， `_channel`，`_tokenStartCharIndex`， `_tokenStartLine` 以及 `_tokenStartCharPositionInLine`。你可以使用各种 setter 方法(如setType)设置它们的状态。例如，如果 enumIsKeyword 为 false，下面的规则将 enum 转换为标识符：
```
ENUM : 'enum' {if (!enumIsKeyword) setType(Identifier);} ;
```
一个词法规则无论包含多少个备选分支，但最多只能有一个动作。

## 7. 词法分析器命令

## 8. 词法分析器规则选项


> 原文:[Lexer Rules](https://github.com/antlr/antlr4/blob/master/doc/lexer-rules.md)
