---
layout: post
author: sjf0115
title: Scala 学习笔记之基础语法
date: 2018-02-27 09:35:01
tags:
  - Scala

categories: scala
permalink: scala-notes-basis
---

#### 1. 变量

val定义的值实际上是一个常亮，无法改变其内容
```scala

scala> val num = 0
num: Int = 0

scala> num = 2
<console>:12: error: reassignment to val
       num = 2
           ^

```
如果要声明其值可变的变量，可以使用var
```scala
scala> var number = 0
number: Int = 0

scala> number = 2
number: Int = 2

```

在Scala中，建议使用`val`，除非你真的需要改变它的内容．

> 备注

不需要给出值或者变量的类型，可以从你用来初始化它的表达式推断出来．只声明值或者变量但不做初始化会报错：
```scala
scala> val str: String
<console>:11: error: only classes can have declared but undefined members
       val str: String
           ^

scala> val str: String = "Hello"
str: String = Hello
```
#### 2. 常用类型

常用类型：
- Byte
- Char
- Short
- Int
- Long
- Float
- Double
- Boolean

跟Java不同的是，这些类型是类．Scala并不刻意区分基本类型和引用类型．你可以对数字执行方法：
```scala
scala> 1.toString()
res2: String = 1
```
#### 3. 条件表达式

Scala的 `if/else` 的语法结构和Java的一样．不过，在Scala中 `if/else` 表达式有值，这个值就是跟在 `if` 或 `else` 之后的表达式的值:
```scala
if(x > 0) 1 else -1
```
上述表达式的值是１或者-1，具体是哪一个取决于x的值．你可以将 `if/else` 表达式的值赋值给变量：
```scala
val s = if(x > 0) 1 else -1
```
等同于:
```scala
if(x > 0) s = 1 else s = -1
```
相对于第二种写法，第一种写法更好一些，因为它可以用来初始化一个val，而第二种写法当中，s必须是var．

> 备注

Scala中每个表达式都有一个类型
```scala
scala> val s = if(x > 0) "positive" else -1;
s: Any = positive
```
上述表达式的类型是两个分支类型的公共超类型．在这个例子中，其中一个分支是`java.lang.String`，而另一个分支是`Int`．它们的公共超类型是`Any`．
```scala
if(x > 0) 1
```
那么有可能if语句没有输出值．但是在Scala中，每个表达式都应该有某种值．这个问题的解决方案是引入一个 `Unit` 类，写作 `()`．不带 `else` 的这个 `if` 语句等同于:
```scala
if(x > 0) 1 else ()
```
#### 4. 循环

Scala拥有与Java和C++相同的while和do循环：
```scala
while(n > 2){
  println("num->" + n)
  n = n -1
}
```
但是Scala没有与`for(初始化变量;检查变量是否满足某条件;更新变量)`循环直接对应的结构．如果你需要这样的循环，有两个选择：一是选择while循环，二是使用如下for语句:
```scala
for(i <- 1 to n){
  println("num->" + i)
}
```
上述表达式的目标是让变量i遍历`<-`右边的表达式的所有值．至于如何遍历，则取决于表达式的类型．

遍历字符串或者数组时，你通常需要使用从0到n-1的区间．这个时候你可以使用`util`方法而不是`to`方法．`util`方法返回一个并不包含上限的区间:
```scala
val s = "Hello"
for(i <- 0 until s.length){
  println(i + " = " + s(i))
}
```
或者
```scala
for(ch <- "Hello"){
  println(ch)
}
```
#### 5. 函数

要定义函数，需要给出函数的名称，参数和函数体:
```scala
def abs (x: Double) = if (x >= 0) x else -x
```
必须给出所有参数的类型，只要函数不是递归的，就可以不需要指定返回类型．Scala编译器可以通过`=`符号右侧的表达式的类型推断出返回类型．
如果函数体需要多个表达式完成，可以使用代码块．块中最后一个表达式的值就是函数的返回值:
```scala
def fac(n: Int) = {
  var r = 1
  for(i <- 1 to n){
    r = r * i
  }
  r
}
```
上例中函数返回值为r的值

> 备注

虽然在函数中使用 `return` 并没有什么不对，我们还是最好适应没有 `return` 的日子．之后，我们会使用大量的匿名函数，这些函数中 `return` 并不返回值给调用者．它跳出到包含它的函数中．我们可以把 `return` 当做是函数版的 `break` 语句，仅在需要时使用．

对于递归函数，我们必须指定返回类型：
```scala
def fac(n: Int) : Int = if(n < 0) 1 else n * fac(n-1)
```
#### 6. 默认参数和带名参数

我们在调用某些函数时并不显示的给出所有参数值，对于这些函数我们可以使用默认参数：
```scala
def decorate (str : String, left : String = "[" , right : String = "]") {
  left + str + right
}
```
这个函数带有两个参数，left 和 right，带有默认值 `[` 和 `]`:
```scala
decorate("Hello") // [Hello]
decorate("Hello", "<", ">") // <Hello>
```
你可以在提供参数值的时候指定参数名(带名参数)：
```scala
decorate(left = "<<", str = "Hello", right = ">>") // <<Hello>>
```
你可以混用未命名参数和带名参数，只要那些未命名的参数是排在前面即可:
```scala
decorate("Hello", right = "]###") // 实际调用 decorate("Hello", "[", "]###")
```

> 备注

带名参数并不需要跟参数列表的顺序完全一致

#### 7. 变长参数

可以实现一个接受可变长度参数列表的函数:
```scala
def sum(args : Int *) = {
  var result = 0
  for(arg <- args){
    result += arg
  }
  result
}
```
可以使用任意多的参数来调用该函数:
```scala
val result = sum(4, 5, 1) // 10
```
#### 8. 过程

Scala对于不返回值的函数有特殊的表示法．如果函数体包含在花括号当中但没有前面的`=`符号，那么返回类型就是Unit，这样的函数被称为过程:
```scala
def welcome(str : String) {
  println("welcome " + str)
}
```
或者显示声明Unit返回类型:
```scala
def welcome(str : String) : Unit = {
  println("welcome " + str)
}
```
#### 9. 懒值

当val被声明为lazy时，它的初始化将被推迟，直到我们首次对它取值:
```scala
lazy val words = scala.io.Source.fromFile("/usr/share/dict/words").mkString
```
如果程序从不访问words，那么文件也不会被打开．

懒值对于开销较大的初始化语句而言十分有用．

> 备注

懒值并不是没有额外的开销．我们每次访问懒值，都会有一个方法被调用，而这个方法将会以线程安全的方式检查该值是否已被初始化．

#### 10. 异常

Scala的异常工作机制跟Java一样．当你抛出异常时:
```scala
throw new IllegalArgumentException("x should not be negative")
```
当前的运算被终止，运行时系统查找可以接受 `IllegalArgumentException` 的异常处理器．控制权将在离抛出点最近的处理器中恢复．如果没有找到符合要求的异常处理器，则程序退出．

和Java一样，抛出的对象必须是 `java.lang.Throwable` 的子类．不过，与Java不同的是，Scala没有"受检"异常，你不需要声明函数或者方法可能会抛出某种异常．

`throw` 表达式有特殊的类型`Nothing`．这在if/else表达式中很有用．如果一个分支的类型是`Nothing`，那么 `if/else` 表达式的类型就是另一个分支的类型:
```scala
if (x > 0) {
  sqrt(x)
}
else{
  throw new IllegalArgumentException("x should not be negative")
}
```
第一个分支的类型是`Double`，第二个分支的类型是`Nothing`，因此if/else表达式的类型是`Double`

捕获异常的语法采用的是模式匹配的语法:
```scala
try{
  process(new URL("Http://hortsman.com/fred-tiny.gif"))
}
catch {
  case _: MalformedURLException => println ("Bad URL:" + url)
  case ex: IOException => ex.printStackTrace()
}
```
与Java一样，更通用的异常应该排在更具体的异常之后．

`try/finally` 语句可以释放资源，不论有没有异常发生:
```scala
var in = new URL("").openStream()
try{
  process (in)
}
finally {
  in.close()
}
```


来源于： 快学Scala
