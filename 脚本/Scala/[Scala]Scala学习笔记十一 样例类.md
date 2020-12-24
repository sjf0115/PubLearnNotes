### 1. 样例类

样例类是一种特殊的类，它们经过优化以被用于模式匹配．下面有两个扩展自常规(非样例)类的样例类:
```
abstract ckass Amount
case class Dollar(value: Double) extends Amount
case class Currency(value : Double, unit: String) extends Amount
```
我们也可以针对的单例的样例对象:
```
case object Nothing extends Amount
```
当我们有一个类型为Amount的对象时，我们可以用模式匹配来匹配到它的类型，并将属性值绑定到变量:
```
amt match {
  case Dollar(v) => "$" + v
  case Currency(_, u) => "On nose, I got " + u
  case Nothing => ""
}
```
当你使用样例类时，有如下几件事会自动发生:
(1) 构造器中的每一个参数都成为val(除非它被显示的声明为var，但是不建议这样做)
(2) 在伴生对象中提供apply方法让你不用new关键字就能构造出相应的对象
(3) 提供unapply方法让模式匹配可以工作
(4) 将生成toString，equals，hashCode和copy方法，除非显示的给出这些方法的定义

### 2. copy方法和带名参数
样例类的copy方法创建一个与现有对象值相同的新对象:
```
val amt = Currency(29,95, "EUR")
val price = amt.copy()
```
这个方法本身并不是很有用，Currency对象是不可变的，我们完全可以共享这个对象引用．我们可以使用带名参数来修改某些属性:
```
val price = amt.copy(value = 19.24)
val price2 = amt.copy(unit = "CHF")
```
### 3.
