---
layout: post
author: sjf0115
title: Scala 学习笔记之Map与Tuple
date: 2018-02-27 09:40:01
tags:
  - Scala

categories: Scala
permalink: scala-notes-map-and-tuple
---

### 1. 构造映射

可以使用如下命令构造一个映射:
```scala
scala> val scores = Map("Alice" -> 90, "Kim" -> 89, "Bob"-> 98)
scores: scala.collection.immutable.Map[String,Int] = Map(Alice -> 90, Kim -> 89, Bob -> 98)
```
上面构造了一个不可变的Map[String, Int]，其值也不能被改变．如果想要一个可变映射，使用如下命令创建:
```scala
scala> val scores = scala.collection.mutable.Map("Alice" -> 90, "Kim" -> 89, "Bob"-> 98)
scores: scala.collection.mutable.Map[String,Int] = Map(Bob -> 98, Alice -> 90, Kim -> 89)
```
如果只想创建一个空的映射:
```scala
scala> val scores = new scala.collection.mutable.HashMap[String, Int]
scores: scala.collection.mutable.HashMap[String,Int] = Map()
```
从上面我们可以知道使用`->`操作符来创建映射的键值对元素
```
"Alice" -> 90
```
我们也可以使用下面的方式定义映射:
```scala
scala> val scores = Map(("Alice",90), ("Kim",89), ("Bob",98))
scores: scala.collection.immutable.Map[String,Int] = Map(Alice -> 90, Kim -> 89, Bob -> 98)
```
### 2. 获取映射中的值

可以使用`()`来查找某个键对应的值:
```scala
scala> val bobscores = scores("Bob")
bobscores: Int = 98
```
如果映射中并不包含对应键的值，则会抛出异常，这与Java返回`null`不同:
```scala
scala> val tomScores = scores("Tom")
java.util.NoSuchElementException: key not found: Tom
  at scala.collection.MapLike$class.default(MapLike.scala:228)
  at scala.collection.AbstractMap.default(Map.scala:59)
  at scala.collection.MapLike$class.apply(MapLike.scala:141)
  at scala.collection.AbstractMap.apply(Map.scala:59)
  ... 32 elided
```
所以在获取某个键对应的值之前，要先检查映射中是否存在指定的键:
```scala
scala> val tomScores = if(scores.contains("Tom")) scores("Tom") else 0
tomScores: Int = 0
```
以下是一个快捷写法:
```scala
scala> val tomScores = scores.getOrElse("Tom", 0)
tomScores: Int = 0
```
### 3. 更新映射中的值

在可变映射中，可以更新某个映射的值，也可以添加一个新的键值对:
```scala
scala> val scores = scala.collection.mutable.Map("Alice" -> 90, "Kim" -> 89, "Bob"-> 98)
scores: scala.collection.mutable.Map[String,Int] = Map(Bob -> 98, Alice -> 90, Kim -> 89)
scala> scores("Alice")=100 // 更新键值对
scala> scores("Tom")=67 // 添加键值对
scala> println(scores)
Map(Bob -> 98, Tom -> 67, Alice -> 100, Kim -> 89)
```
还可以使用`+=`操作符来添加多个关系:
```scala
scala> scores += ("Bob" -> 78, "Fred" -> 89)
res3: scores.type = Map(Bob -> 78, Fred -> 89, Tom -> 67, Alice -> 100, Kim -> 89)
```
还可以使用`-=`操作符移除某个键对应的值:
```scala
scala> scores -= "Tom"
res4: scores.type = Map(Bob -> 78, Fred -> 89, Alice -> 100, Kim -> 89)
```
虽然不可以更新一个不可变的映射，但是我们利用一些操作产生一个新的映射，并可以对原映射中的键值对进行修改或者添加新的键值对:
```scala
scala> val scores = Map("Alice" -> 90, "Kim" -> 89, "Bob"-> 98)
scores: scala.collection.immutable.Map[String,Int] = Map(Alice -> 90, Kim -> 89, Bob -> 98)

scala> val newScores = scores + ("Kim" -> 78, "Tom" -> 54)
newScores: scala.collection.immutable.Map[String,Int] = Map(Alice -> 90, Kim -> 78, Bob -> 98, Tom -> 54)
```
上例中scores是不可变映射，我们在它基础上对"Kim"进行了修改，添加了"Tom"，产生了一个新的映射newScores

### 4. 迭代映射

可以使用如下命令迭代映射:
```scala
scala> for( key <- scores.keySet ) println(key + "---" + scores(key))
Alice---90
Kim---89
Bob---98
```
或者
```scala
scala> for( value <- scores.values ) println(value)
90
89
98
```
### 5. 排序映射

在操作映射时，我们需要选定一个映射(哈希表还是平衡树)．默认情况下，scala给的是哈希表．有时候我们想对键进行一个排序，顺序访问键，这就需要一个树形映射:
```scala
scala> val scores = scala.collection.immutable.SortedMap("Alice" -> 90, "Kim" -> 89, "Bob"-> 98)
scores: scala.collection.immutable.SortedMap[String,Int] = Map(Alice -> 90, Bob -> 98, Kim -> 89)
```

### 6. 与Java互操作

如果你有一个Java映射，想要转换为Scala映射，以便便捷的使用Scala映射的方法，只需要增加如下语句:
```scala
import scala.collection.JavaConversions.mapAsScalaMap
```
然后指定Scala映射类型来触发转换:
```scala
scala> val scores : scala.collection.mutable.Map[String,Int] = new java.util.TreeMap[String, Int]
scores: scala.collection.mutable.Map[String,Int] = Map()
```
还可以将java.util.Properties到Map[String, String]的转换:
```scala
scala> import scala.collection.JavaConversions.propertiesAsScalaMap
import scala.collection.JavaConversions.propertiesAsScalaMap

scala> val props : scala.collection.Map[String, String] = System.getProperties()
props: scala.collection.Map[String,String] =
Map(env.emacs -> "", java.runtime.name -> Java(TM) SE Runtime Environment, sun.boot.library.path -> /home/xiaosi/opt/jdk-1.8.0/jre/lib/amd64, java.vm.version -> 25.91-b14, java.vm.vendor -> Oracle Corporation, ...
```
相反，如果想要把Scal映射转换为Java映射，只需要提供相反的隐式转换即可:
```scala
scala> import scala.collection.JavaConversions.mapAsJavaMap
import scala.collection.JavaConversions.mapAsJavaMap

scala> import java.awt.font.TextAttribute._ // 引入下面的映射会用到的键
import java.awt.font.TextAttribute._

scala> val attrs = Map(FAMILY -> "Serif", SIZE -> 12) // Scala映射
attrs: scala.collection.immutable.Map[java.awt.font.TextAttribute,Any] = Map(java.awt.font.TextAttribute(family) -> Serif, java.awt.font.TextAttribute(size) -> 12)

scala> val font = new java.awt.Font(attrs) // Java映射
font: java.awt.Font = java.awt.Font[family=Serif,name=Serif,style=plain,size=12]
```

### 7. 元组Tuple

元组是不同类型的值的聚合，元组的值通过将单个的值包含在圆括号中构成的：
```scala
scala> val bobScore = (1, 98.5, "Bob")
bobScore: (Int, Double, String) = (1,98.5,Bob)
```
可以使用方法`_1`，`_2`，`_3`访问其组员:
```scala
scala> val bobScore = (1, 98.5, "Bob")
bobScore: (Int, Double, String) = (1,98.5,Bob)

scala> bobScore._1
res10: Int = 1

scala> bobScore._3
res11: String = Bob
```
通常，使用模式匹配的方式来获取元组的组元:
```scala
scala> val (id, score, name) = bobScore // 将变量id赋值为1，变量score赋值为98.5，变量name赋值为Bob
   val bobScore: (Int, Double, String)

scala> val (id, score, name) = bobScore
id: Int = 1
score: Double = 98.5
name: String = Bob

scala> println("name = " + name + ", score = " + score + ", name = " + name)
name = Bob, score = 98.5, name = Bob
```

来源于： 快学Scala
