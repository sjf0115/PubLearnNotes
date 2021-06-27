Scala有一个十分强大的模式匹配机制．可以应用在很多场合:switch语句，类型检查等等．此外Scala还提供了样例类，对模式匹配进行了优化．

### 1. 更好的switch

如下是Scala中C风格switch语句的等效代码:
```
var sign = 2
val ch = '+'
ch match {
  case '+' => sign = 1
  case '-' => sign = -1
  case _ => sign = 0
}
println(sign) // 1
```
与default等效的是捕获所有模式(`case _模式`)．有这样一个捕获所有的模式是有好处的．如果没有模式能匹配并且并没有提供`case _`，代码会抛出MatchError．

与C语言的switch不同的是，Scala模式匹配不会像C语言那样必须在每个分支的末尾显示使用break语句防止进行下一分支．

与if类似，match也是表达式，而不是语句．前面代码可以简化为:
```
sign = ch match {
  case '+' => 1
  case '-' => -1
  case _ => 0
}
```
可以在match表达式中使用任何类型，而不仅仅是数字:
```scala
color match{
  case Color.RED => ...
  case Color.BLACK => ...
  ...
}
```
### 2. 守卫

假如说我们想扩展上面第一个代码以匹配所有数字．在C风格switch语句中可以通过简单的添加多个case标签来实现:
```
switch(i){
  case 0:
    ...
    break;
  case 1:
    ...
    break;
  ...
  case 9:
    ...
    break;  
  default:
    ...
}
```
这如果放在Scala中会更简单，给模式添加`守卫`(相当于一个判断条件)即可:
```scala
ch match{
  case '+' => sign = 1
  case '-' => sign = -1
  case _ if Character.isDigit(ch) => digit = Character.digit(ch, 10)
  case _ => sign = 0
}
```
守卫可以是任何Boolean条件．

**备注**
```
模式总是从上往下进行匹配的．如果守卫的这个模式不能匹配，则捕获所有的模式(`case _`)会被用来尝试进行匹配．
```

### 3. 模式中的变量

如果case关键字后面跟着一个变量名，那么匹配的表达式会被赋值给那个变量，进而可以在后面中使用该变量:
```scala
val character = '1'
character match {
  case '+' => println("this is +")
  case '-' => println("this is -")
  case ch => println("this is " + ch) // this is 1
}
```
**备注**
```
上面代码中如果给定字符不是'+'或者'-'，给定字符则会赋值给变量ch
```

也可以在守卫中使用变量:
```scala
val character = '5'
character match {
  case '+' => println("this is +")
  case '-' => println("this is -")
  case ch if Character.isDigit(ch) => println("this is digit") // this is digit
}
```

### 4. 类型模式

可以根据表达式的类型进行匹配:
```
val str:Any = "Hello World"
str match {
  case s: String => println("this is string " + s) // this is string Hello World
  case x: Int => println("this is integer " + x)
  case ch => println("this is other " + ch)
}
```
在Scala中，我们更倾向于使用这种的模式匹配，而不是使用`isInstanceOf`操作符．

**备注**
```
注意模式中的变量名．当你在匹配类型的时候，必须给出一个变量名(例如上例中的s,x)．否则，将会拿对象本身来进行匹配:
case _: BigInt => Int.MaxValue // 匹配任何类型为BigInt的对象
case BigInt => -1 // 匹配类型为Class的BigInt对象
```

### 5. 匹配数组，列表和元组

匹配数组中的内容，可以在模式中使用Array表达式:
```
def arrayMatch(arr:Array[String]) = arr match {
  case Array("Hello") => println("the array only contain 'Hello'")
  case Array(x,y) => println("the array contain two value " + x + " and " + y)
  case Array(x,_*) => println("the array contain many values " + arr.mkString(","))
  case _ => println("the other array")
}

arrayMatch(Array("Hello")) // the array only contain 'Hello'
arrayMatch(Array("Hello", "World")) // the array contain two value Hello and World
arrayMatch(Array("Hello", "World", "Yoona")) // the array contain many values Hello,World,Yoona
```
同样也可以使用List表达式(或者使用`::`操作符)匹配列表:
```
def listMatch(list:List[String]) = list match {
  case "Hello" :: Nil => println("the list only contain 'Hello'")
  case x :: y :: Nil => println("the list contain two value " + x + " and " + y)
  case "Hello" :: tail => println("the list contain many values " + list)
  case _ => println("the other list")
}

listMatch(List("Hello")) // the list only contain 'Hello'
listMatch(List("Hello", "World")) // the list contain two value Hello and World
listMatch(List("Hello", "World", "Yoona")) // the list contain many values List(Hello, World, Yoona)
```
同样也可以使用元组表示法匹配元组:
```
def pairMatch(t:Any) = t match {
  case ("Hello", _) => println("the first value is 'Hello'")
  case (x, "Hello") => println("the first value is " + x + " and the second value is 'Hello'")
  case _ => println("the other tuple")
}

pairMatch(("Hello", "World")) // the first value is 'Hello'
pairMatch(("World", "Hello")) // the first value is World and the second value is 'Hello'
pairMatch(("Hello", "World", "Yoona")) // the other tuple
```
### 6. 提取器

前面我们看到模式是如何匹配数组，列表和元组的，这些功能背后是[提取器](http://blog.csdn.net/sunnyyoona/article/details/77268186)机制，带有从对象中提取值的unapply或unapplySeq方法的对象．unapply方法用于提取固定数量的对象，而unapplySeq提取的是一个序列．
```scala
arr match {
  case Array(0, x) => ...
  ...
}
```
Array伴生对象就是一个提取器，定义了一个unapplySeq方法．该方法被调用时，以被执行匹配动作的表达式作为参数．Array.unapplySeq(arr)产出一个序列的值，即数组中的值．第一个值与零进行比较，二第二个值被赋值给x．

正则表达式是另一个适合使用提取器的场景，如果正则表达式中有分组，可以使用提取器来匹配每个分组:
```scala
val pattern = "([0-9]+ ([a-z]+))".r
val str = "99 bottles"
str match {
  // num = 99 item = bottles
  case pattern(num, item) => ...
  ...
}
```
pattern.unapplySeq("99 bottles")生成一系列匹配分组的字符串，这些字符串分别赋值给变量num和item．

### 7. 变量声明中的模式

之前我们可以看到模式汇总是可以带变量的，同样我们也可以在变量声明中使用这样的模式:
```
// x = 1 y = 2
val (x, y) = (1, 2)
```
这对于使用那些返回对偶的函数是非常有用的:
```
val (q, r) = BigInt(10) /% 3
println("q value is " + q + " and r value is " + r)
// q value is 3 and r value is 1
```
**备注**
```
/%方法返回包含商和余数的对偶，而这两个值分别被变量q和r捕获到.
```

### 8. for表达式中的模式

可以在for推导表达式中使用带变量的模式．对于每一个遍历到的值，使用模式进行变量绑定:
```
import scala.collection.JavaConversions.propertiesAsScalaMap
for( (key, value) <- System.getProperties() ){
  println(key + " = " + value)
}
```
在for表达式中，失败的匹配将被跳过(不会抛出异常)，下面循环打印出所有值为空白的键，跳过所有其他键:
```
import scala.collection.JavaConversions.propertiesAsScalaMap
for( (key, "") <- System.getProperties() ){
  println(key + " = ")
}
```
也可以使用守卫(注意if关键字出现在<-之后):
```
import scala.collection.JavaConversions.propertiesAsScalaMap
for( (key, value) <- System.getProperties() if value == ""){
  println(key + " = " + value)
}
```
