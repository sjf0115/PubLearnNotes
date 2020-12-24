---
layout: post
author: sjf0115
title: Scala 学习笔记之数组
date: 2018-02-27 09:36:01
tags:
  - Scala

categories: Scala
permalink: scala-notes-array
---

### 1. 定长数组

如果你需要一个长度不变的数组，可以使用Scala中的 `Array`．
```scala
val nums = new Array[Int](10) // 10个整数的数组　所有元素初始化为0
val strs = new Array[String](10) // 10个字符串的数组　所有元素初始化为null
val s = Array("Hello", "World") // 长度为2的Array[String] 类型是推断出来的　
s(0) = "GoodBye" // Array("GoodBye"，"World")
```

> 备注

- 已提供初始值时不要使用`new`，例如上面的数组s
- 使用`()`而不是`[]`来访问元素
- 在JVM中，Scala的Array以Java数组方式实现．

### 2. 变长数组

对于那种长度按需要变化的数组，Java有 `ArrayList`．Scala中等效数据结构为 `ArrayBuffer`．
```scala
import scala.collection.mutable.ArrayBuffer
val b = ArrayBuffer[Int]() // 或者 new ArrayBuffer[Int]() 创建一个空的数组缓冲来存放整数
b += 1　// ArrayBuffer(1) 用+=在尾端添加元素
b += (1,2,3,5) // ArrayBuffer(1,1,2,3,5) 在尾端添加多个元素
b ++= Array(8, 13, 21) // ArrayBuffer(1,1,2,3,5,8,13,21) 用++=操作追加任何集合
b.trimEnd(5) // ArrayBuffer(1,1,2) 移除最后５个元素
```
可以在任意位置插入或移除元素，但这样的操作不如在尾端添加或移除元素操作那么高效:
```scala
b.insert(2,6) // ArrayBuffer(1,1,6,2) 在下标2之前插入
b.insert(2,7,8,9) // ArrayBuffer(1,1,7,8,9,6,2) 插入任意多的元素
b.remove(2) // ArrayBuffer(1,1,8,9,6,2) 删除下标２的元素
b.remove(2,3) // ArrayBuffer(1,1,2) 第二个参数的含义是要移除多少个元素
```
有时需要构建一个Array，但不知道最终需要装多少元素．这种情况下可以先构建一个数组缓冲，然后调用:
```scala
b.toArray // Array(1,1,2)
```
### 3. 遍历数组和数组缓冲

使用for循环遍历数组和数组缓冲:
```scala
val b = Array(6,5,4,3,2,1)
for(i <- 0 until b.length){
  println(i + "-" + b(i))
}
```
输出结果:
```
0-6
1-5
2-4
3-3
4-2
5-1
```
> 备注

`until` 是 `RichInt` 类的方法，返回所有小于(但不包括)上限的数字

如果想要每两个元素一跳，可以让i这样来进行遍历:
```scala
val b = Array(6,5,4,3,2,1)
for(i <- 0 until (b.length, 2)){
  println(i + "-" + b(i))
}
```
输出结果：
```
0-6
2-4
4-2
```
如果要从数组的尾端开始:
```scala
val b = Array(6,5,4,3,2,1)
for(i <- (0 until b.length).reverse){
  println(i + "-" + b(i))
}
```
如果在循环体中不需要用到数组下标，我们也可以直接访问数组元素:
```scala
for(elem <- b){
  println(elem)
}
```
### 4. 数组转换

从一个数组(数组缓冲)出发，以某种方式对它进行转换是很简单的．这些转换操作不会修改原是数组，而是产生一个全新的数组:
```scala
val a = Array(1,2,3,4)
val result = for(elem <- a) yield 2 * elem // result 是Array(2,4,6,8)
```
`for(...) yield`循环创建了一个类型与原实际和相同的新集合．新元素为yield之后的表达式的值，每次迭代对应一个．

当你遍历一个集合时，如果只想处理满足特定条件的元素．可以通过for中的if来实现:
```scala
val a = Array(1,2,3,4)
val result = for(elem <- a if elem % 2 == 0) yield 2 * elem
```
上面实例中对每个偶数元素翻倍，并丢掉奇数元素．

### 5. 常用操作

#### 5.1 sum
```scala
val a = Array(6,1,7,4)
a.sum // 18
```
要使用sum方法，元素类型必须是数值类型:整型，浮点数或者BigInteger/BigDecimal

#### 5.2 min max
```scala
val a = Array(6,1,7,4)
a.min // 1
a.max // 7
```
min和max输出数组或数组缓冲中最小和最大的元素

#### 5.3 sorted
```scala
val a = Array(6,1,7,4)
val asorted = a.sorted // Array(1, 4, 6, 7)

val a = ArrayBuffer(6,1,7,4)
val asorted = a.sortWith(_ > _) // ArrayBuffer(7, 6, 4, 1)
```
sorted方法将数组或数组缓冲排序并返回经过排序的数组或数组缓冲，不会修改原始数组．可以使用sortWith方法提供一个比较函数．

#### 5.4 mkString

```scala
val a = Array(6,1,7,4)
a.mkString(" and ") // 6 and 1 and 7 and 4
```
如果想要显示数组或者数组缓冲的内容，可以使用`mkString`，允许指定元素之间的分隔符
```scala
val a = Array(6,1,7,4)
a.mkString("<", ",", ">") // <6,1,7,4>
```
该方法的另一个重载版本可以让你指定前缀和后缀

来源于: 快学Scala
