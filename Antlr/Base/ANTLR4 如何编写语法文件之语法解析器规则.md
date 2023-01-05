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
备选分支可以是一组规则元素的列表，也可以为空。例如，如下有一个空的备选分支的规则，从而使规则成为一条可选规则：
```
superClass
 	: 'extends' ID
 	| // empty means other alternative(s) are optional
 	;
```


> 原文:[Parser Rules](https://github.com/antlr/antlr4/blob/master/doc/parser-rules.md)
