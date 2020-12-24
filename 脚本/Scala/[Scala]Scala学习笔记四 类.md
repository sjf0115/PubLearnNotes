---
layout: post
author: sjf0115
title: Scala 学习笔记之类
date: 2018-02-27 09:45:01
tags:
  - Scala

categories: Scala
permalink: scala-notes-class
---

### 1. 简单类与无参方法

```scala
class Person {
  var age = 0 // 必须初始化字段
  def getAge() = age // 方法默认为公有的
}
```
> 备注

在Scala中，类并不声明为public． Scala源文件可以包含多个类，所有这些类都具有公有可见性．属性不声明默认为public．

使用类:
```scala
val p = new Person // 或者new Person()
p.age = 23
println(p.getAge()) // 23
```
调用无参方法时，可以写上圆括号，也可以不写:
```scala
p.getAge() // 23
p.getAge   // 23
```
### 2. 带getter和setter的属性

#### 2.1 Java getter和setter

在Java类中，我们并不喜欢使用公有字段:
```java
public class Person{
  public int age; // Java中不推荐使用这种方式
}
```
更倾向于使用getter和setter方法:
```java
public class Person{
  private int age;
  public int getAge() {return age;}
  public void setAge(int age) {this.age = age;}
}
```
像这样的一对getter/setter通常被称为属性．我们会说Person类有一个age属性．

#### 2.２ Scala getter和setter

在Scala中对每个字段都提供了getter和setter方法:
```scala
class Person{
  var age = 0
}
```
scala生成面向JVM的类，会生成一个私有的age字段以及相应的getter和setter方法．这两个方法都是公有的，因为我们没有将age声明为private．(对于私有字段而言,getter和setter方法也是私有的)　

在scala中getter和setter方法分别叫`age`和`age_=`．使用的时候如下:
```scala
val p = new Person
p.age = 21 // 调用p.age_=(21)
println(p.age) // 调用p.age()方法
```

> 备注

在scala中，getter和setter方法并非被命名为getXXX和setXXX，不过用意相同．

任何时候我们都可以自己重新定义getter和setter方法:
```scala
class Person {
  private var privateAge = 0
  def age = privateAge
  def age_= (newAge : Int): Unit = {
    if(newAge > 150){
      privateAge = 150
    }
    else if(newAge < 0){
      privateAge = 0
    }
  }
}
```
使用:
```
val p = new Person
p.age = -1;
println(p.age) // 0
p.age = 189
println(p.age) // 150
```

> 备注

Scala对每个字段生成getter和setter方法听上去有些恐怖，不过你可以控制这个过程:
- 如果字段是私有的，则getter和setter方法也是私有的
- 如果字段是val，则只有getter方法被生成
- 如果你不需要任何的getter和setter方法，可以将字段声明为`private[this]`

#### 2.3 Example

(1) 对于公有字段,getter和setter方法是公有的:
```scala
class Student {
  var age = 22
}

val stu = new Student
stu.age = 23
println(stu.age) // 23
```
(2) 对于私有字段,getter和setter方法是私有的:
```scala
class Student {
  private var age = 22
}

val stu = new Student
//stu.age = 23 // symbol age is inaccessible from this place
//println(stu.age) // symbol age is inaccessible from this place
```

(3) 如果字段是val，则只有getter方法被生成:
```scala
class Student {
  val age = 22
}

val stu = new Student
// stu.age = 23 // reassignment to val
println(stu.age) // 22
```

### 3. 只带getter的属性

如果只想需要一个只读的属性，有getter但没有setter，属性的值在对象构建完成之后就不再改变了，可以使用val字段:
```scala
class Student {
  val age = 22
}
```
Scala会生成一个私有的final字段和一个getter方法，但没有setter方法

### 4. 对象私有字段

在Scala中，方法可以访问该类的`所有对象`的私有字段:
```scala
class Counter {
  private var value = 0
  def increment(): Unit = {
    value += 1
  }
  // 对象可以访问另一个对象的私有字段
  def isLess (other : Counter) = value < other.value
}
```
之所以访问 `other.value` 是合法的，是因为 `other` 也是Counter对象，这与Java的private权限不一样.

Scala允许我们定义更加严格的访问限制，通过private[this]这个修饰符来实现:
```scala
private[this] var value = 0
```
这样 `other.value` 是不被允许访问的，这样以来Counter类只能访问当前对象的value字段，而不能访问同样是Counter类型的其他对象的字段．

Scala允许你将访问权限赋予指定得类，private[类名]可以定义仅有指定类的方法可以访问给定的字段．这里的类名必须是当前定义的类，或者是包含该类的外部类．

> 备注

对于类私有的字段(private)，Scala会生成私有的getter和setter方法，但是对于对象私有的字段，不会生成getter和setter方法．

### 5. Bean属性

Scala对于你定义的字段提供了getter和setter方法，但是并不是Java工具所期望的．JavaBeans规范把Java属性定义为一对getXXX/setXXX方法．很多Java工具都依赖这样的命令习惯．

Scala给我们提供了@BeanProperty注解，这样就会字段生成我们期望的getXXX和setXXX方法:
```scala
class Student {
  @BeanProperty
  var age = 22
}

val stu = new Student
stu.setAge(25)
println(stu.getAge()) // 25
```

> 总结

scala字段|生成的方法|何时使用
---|---|---
val/var name|公有的`name` `name_=`(仅限var)|实现一个可以被公开访问并且背后是以字段形式保存的属性
@BeanProperty val/var name | 公有的`name` `getName()` `name_=`(仅限var) `setName()` (仅限var) | 与JavaBeans互操作
private val/var name|私有的`name` `name_=`(仅限var)|用于将字段访问限制在本类的方法．尽量使用private，除非真的需要一个公有属性
private[this] val/var name | 无 | 用于将字段访问限制在同一个对象上调用的方法．不经常用
private[类名] val/var name | 依赖于具体实现 | 将访问权限赋予外部类．不经常使用

### 6. 辅助构造器

Scala可以有任意多的构造器，不过，Scala有一个构造器比其他所有构造器都重要，就是主构造器，除了主构造器之外，类还有任意多的辅助构造器．其同Java中的构造器十分相似，只有两处不同:
- 辅助构造器的名称为`this`
- 每一个辅助构造器都必须以一个先前已定义的其他辅助构造器或主构造器的调用开始

```scala
class Person {
  private var name = ""
  private var age = 0

  def this (name : String){
    this() // 调用主构造器
    this.name = name
  }

  def this (name : String, age : Int){
    this(name) // 调用前一个辅助构造器
    this.age = age
  }
}
```
可以使用如下三种方式构造对象:
```scala
val p1 = new Person // 调用主构造器
val p2 = new Person("Bob") // 调用第一个辅助构造器
val p3 = new Person("Bob", 25) // 调用第二个辅助构造器
```
### 7. 主构造器

在Scala中，每个类都有主构造器．主构造器并不以this方法定义，而是与类定义交织在一起．

(1) 主构造器的参数直接放在类名之后
```scala
class Person(val name:String) {
  private var age = 0
  def this (name : String, age : Int){
    this(name) // 调用主构造器
    this.age = age
  }
}
```
主构造器的参数被编译成字段，其值被初始化成构造时传入的参数．上述示例中name和age为Person类的字段．

(2) 主构造器会执行类定义中的所有语句
```scala
class Person(val name:String) {
  println("constructed a person ...")
  private var age = 0

  def this (name : String, age : Int){
    this(name) // 调用主构造器
    this.age = age
  }
}
```
println语句是主构造器的一部分．每当有对象被构造出来时．上述代码就会被执行

(3) 通常可以在主构造器中使用默认参数来避免使用过多的辅助构造器
```scala
class Person(val name:String = "", val age: Int = 0) {
}
```


> 备注

如果类名之后没有参数，则该类具备一个无参主构造器.


来源于： 快学Scala
