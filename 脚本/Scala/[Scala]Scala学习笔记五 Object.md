---
layout: post
author: sjf0115
title: Scala 学习笔记之Object
date: 2018-02-27 09:50:01
tags:
  - Scala

categories: Scala
permalink: scala-notes-object
---

### 1. 单例对象

Scala没有静态方法或静态字段，可以使用 `object` 来达到这个目的，对象定义了某个类的单个实例:
```scala
object Account{
  private var lastNumber = 0
  def newUniqueNumber () = {lastNumber += 1; lastNumber}
}
```
当你在应用程序中需要一个新的唯一账号时，调用 `Account.newUniqueNumber()` 即可．对象的构造器在该对象第一次被使用时调用．在本例中，`Account` 的构造器在 `Account.newUniqueNumber` 的首次调用时执行．如果一个对象从未被使用，那么构造器也不会被执行．

对象本质上可以拥有类的所有特性，但是不能提供构造器参数．

在Scala中可以用对象来实现:
- 作为存放工具函数或常量的地方
- 高效的共享单个不可变实例
- 需要用单个实例来协调某个服务时(参考单例模式)

### 2. 伴生对象

在Java中，通常会用到既有实例方法又有静态方法的类，在Scala中，可以通过类和类同名的 `伴生对象` 来达到同样的目的:
```scala
class Account{
  val id = Account.newUniqueNumber()
  private var balance = 0.0
  def deposit(amount : Double) { balance += amount }
  ...
}

// 伴生对象
object Account{
  private var lastNumber = 0
  def newUniqueNumber () = {lastNumber += 1; lastNumber}  
}
```
类和它的伴生对象可以相互访问私有特性．它们必须在同一个源文件中．

### 3. apply方法

我们通常会定义和使用对象的 `apply` 方法．当遇到如下形式的表达式时，`apply` 方法就会被调用:
```scala
Object(参数1，参数2，...，参数N)
```
通常，这样一个 `apply` 方法返回的是伴生类的对象．举例来说，Array对象定义了 `apply` 方法，让我们可以用下面这样的表达式来创建数组:
```scala
Array("Mary", "had", "a", "little", "lamb")
```
不使用构造器，而是使用apply方法，对于使用嵌套表达式而言，省去new关键字会方便很多:
```scala
Array(Array(1,7), Array(2,9))
```
下面有一个定义apply方法的示例:
```scala
class Account private (val id :Int, initialBalance: Double){
  private var balance = initialBalance
  ...
}

// 伴生对象
object Account{
  def apply(initialBalance : Double){
    new Account(newUniqueNumber(), initialBalance)
  }
  ...
}
```
这样我们就可以使用如下方式创建账号了:
```scala
val acct = Account(1000.0)
```

### 4. 应用程序对象

每个Scala程序都必须从一个对象的main方法开始，这个方法的类型为 `Array[String]=>Unit`:
```scala
object Hello{
  def main(args: Array[String]){
    println("Hello world!")
  }
}
```
除了每次都提供自己main方法外，你可以扩展App特质，然后将程序代码放入构造器方法体内:
```scala
object Hello extends App{
  println("Hello world!")
}
```
如果需要命令行参数，则可以通过args属性得到:
```scala
object Hello extends App{
  if(args.length > 0){
    println("Hello, " + args(0))
  }
  else{
    println("Hello world!")
  }
}
```
### 5. 枚举

不同于Java，Scala中没有枚举类型，需要我们通过标准库类 `Enumeration` 来实现:
```scala
object BusinessType extends Enumeration{
  var FLIGHT, HOTEL, TRAIN, COACH = Value
}
```
继承 `Enumeration` 类，实现一个 `BusinessType` 对象，并以 `Value` 方法调用初始化枚举中的所有可选值．在这里我们定义了４个业务线类型，然后用Value调用它们初始化．

每次调用Value方法都返回内部类的新实例，该内部类也叫做Value．或者，可以向Value方法传入ID，名称:
```scala
val FLIGHT = Value(0, "FLIGHT")
val HOTEL = Value(10) // 名称为"HOTEL"
val TRAIN = Value("TRAIN") // ID为11
```
如果不指定ID，ID为上一个枚举值上加一，如果不指定名称，名称默认为字段名．定义完成后，可以使用 `BusinessType.FLIGHT`，`BusinessType.HOTEL`，`BusinessType.TRAIN` 等来引用:
```scala
def businessHandle(business: BusinessType.Value): Unit ={
  if(business == BusinessType.FLIGHT){
    println("this is a flight behavior")
  }
  else if(business == BusinessType.HOTEL){
    println("this ia a hotel behavior")
  }
}

def main(args: Array[String]): Unit = {
  val business = BusinessType.FLIGHT
  businessHandle(business) // this is a flight behavior
}
```
如果觉的BusinessType.FLIGHT比较冗长繁琐，可以使用如下方式引入枚举值:
```scala
import BusinessType._
```
使用时直接使用枚举值名称即可:
```scala
def businessHandle(business: BusinessType.Value): Unit ={
  if(business == FLIGHT){
    println("this is a flight behavior")
  }
  else if(business == HOTEL){
    println("this ia a hotel behavior")
  }
}
```
记住枚举值的类型是BusinessType.Value而不是BusinessType，后者是拥有这些值的对象，可以增加一个类型别名:
```scala
object BusinessType extends Enumeration{
  type BusinessType = Value
  var FLIGHT, HOTEL, TRAIN, COACH = Value
}
```
如下使用:
```scala
def businessHandle(business: BusinessType): Unit ={
  if(business == FLIGHT){
    println("this is a flight behavior")
  }
  else if(business == HOTEL){
    println("this ia a hotel behavior")
  }
}
```

枚举值的ID可以通过id方法返回，名称通过toString方法返回:
```scala
val business = FLIGHT
println("ID:" + business.id + "   name:" + business.toString) // ID:0   name:FLIGHT
```

可以通过如下方式输出所有的枚举值:
```scala
for(business <- BusinessType.values){
  println("ID:" + business.id + "   name:" + business.toString)
}

ID:0   name:FLIGHT
ID:1   name:HOTEL
ID:2   name:TRAIN
ID:3   name:COACH
```

你也可以通过枚举的ID或名称来进行查找定位:
```scala
val FLIGHT1 = BusinessType(0)
println("ID:" + FLIGHT1.id + "   name:" + FLIGHT1.toString)
val FLIGHT2 = BusinessType.withName("FLIGHT")
println("ID:" + FLIGHT2.id + "   name:" + FLIGHT2.toString)

ID:0   name:FLIGHT
ID:0   name:FLIGHT    
```

来源于： 快学Scala
