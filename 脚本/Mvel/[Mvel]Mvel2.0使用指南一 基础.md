MVEL在很大程度上受到Java语法的启发，作为一个表达式语言，也有一些根本的区别，旨在更高的效率，例如：直接支持集合、数组和字符串匹配等操作以及正则表达式。
MVEL用于执行使用Java语法编写的表达式。

除了表达语言之外，MVEL还可用作配置和字符串构造的模板语言。 

MVEL2.x表达式包含以下部分的内容：
- 属性表达式
- 布尔表达式
- 方法调用
- 变量赋值
- 函数定义


### 1. 基本语法

MVEL 是一种基于Java语法，但又有着显著不同的表达式语言。与Java不同的是，MVEL是动态类型语言（可选类型），意味着源代码中不需要类型限定。MVEL解释器可以作为下载库集成到其他产品中。 它需要从maven网站下载。这些库展现了API。如果一个表达式传递给库的接口，则表达式被计算并提供计算后的结果。

MVEL表达式可以像单个标识符一样简单，或者与使用方法调用和内联集合创建的完整布尔表达式一样复杂。


#### 1.1 简单属性表达式

```
user.name
```
在这个表达式中，我们只需要一个唯一的标识符`user.name`，它们本身就是我们在MVEL中引用的属性表达式，表达式的唯一目的是从一个变量中提取一个属性或者上下文对象。 属性表达式是最常见的用途之一，允许将MVEL用作非常高性能，易于使用的反射优化器。

MVEL甚至可以用于执行布尔表达式：

```
user.name == 'John Doe'
```
像Java一样，MVEL支持全部的运算符优先级规则，包括使用括号来控制执行顺序:
```
(user.name == 'John Doe') && ((x * 2) - 1) > 20
```
#### 1.2 多语句

可以编写具有任意数量语句的脚本，使用分号来表示一个语句的终止。只有一个语句，或在脚本中的最后一个语句的情况下，可以不用使用分号。
```
statement1; statement2; statement3
```
==备注==

第三个语句可以不使用分号，因为是脚本中的最后一个语句；注意的是不能另起新行来表示上一行语句的结束；

#### 1.3 返回值

MVEL表达式使用`最后值输出原则`(a last value out principle)。这意味着虽然MVEL支持return关键字，但可以不使用它。 例如：

```
a = 10;
b = (a = a * 2) + 10;
a;
```
在这个上面的例子中，表达式返回了a的值，因为其是表达式的最后一个值。 它在功能上与以下相同：
```
a = 10;
b = (a = a * 2) + 10;
return a;
```

### 2. 值校验(Value Tests)

MVEL中的所有等式校验均基于值而不是引用。 因此，表达式`foo =='bar'`与Java中的`foo.equals(“bar”)`相当。

#### 2.1 Empty

MVEL提供了一个特殊的字面值，用于校验一个值是否为""或者null，命名为`empty`。

```
a == empty
```
如果a的值满足empty的要求，则示例表达式将为真。

Example:
```
String expression = "a == empty && b == empty";
Map<String, Object> paramMap = Maps.newHashMap();
paramMap.put("a", "");
paramMap.put("b", null);
Object object = MVEL.eval(expression, paramMap);
System.out.println(object); // true
```

#### 2.2 Null

VEL允许使用关键字`null`或`nil`表示一个空值。

```
a == null;
a == nil; // same as null
```
Example:
```
String expression = "a == null && b == nil";
Map<String, Object> paramMap = Maps.newHashMap();
paramMap.put("a", null);
paramMap.put("b", null);
Object object = MVEL.eval(expression, paramMap);
System.out.println(object); // true
```

#### 2.3 值强制类型转换

MVEL的强制类型转换系统适用于如下场景:通过试图将右边的值强制转换为左边值的类型来比较两个无法比较的类型，反之亦然。
```
"123" == 123;
```
上述表达式在MVEL中返回`true`，因为强制类型转换系统将强制将无类型数字123转换为字符串来执行比较。
```
String expression = "a == b";
Map<String, Object> paramMap = Maps.newHashMap();
paramMap.put("a", "123");
paramMap.put("b", 123);
Object object = MVEL.eval(expression, paramMap);
System.out.println(object); // true
```

### 3. Inline List, Maps and Arrays

MVEL允许你使用简单优雅的语法来表示List，Map和Array。 请考虑以下示例：
```
["Bob" : new Person("Bob"), "Michael" : new Person("Michael")]
```
这在功能上等同于以下代码：
```
Map map = new HashMap();
map.put("Bob", new Person("Bob"));
map.put("Michael", new Person("Michael"));
```
这是在MVEL中表达数据结构的非常强大的方法。您可以在任何地方使用这些结构，甚至作为方法的参数：
```
something.someMethod(["foo" : "bar"]);
```
#### 3.1 Lists

Lists可以使用下列格式表示：
```
[item1，item2，...]
```
Example:
```
["Jim", "Bob", "Smith"]
```

#### 3.2 Maps

Maps可以使用下列格式表示：
```
 [key1 : value1, key2: value2, ...]
```
Example:
```
["Foo" : "Bar", "Bar" : "Foo"]
```

#### 3.3 Arrays

Arrays可以使用下列格式表示：
```
{item1, item2, ...}
```
Example:
```
{"Jim", "Bob", "Smith"}
```

#### 3.4 Array Coercion

要了解的内联数组的一个重要方面是它们被强制转换为其他数组类型的特殊能力。 当你声明一个内联数组时，它是无类型的，但是例如说你传递给接受int []的方法。 您只需编写代码如下：
```
foo.someMethod({1,2,3,4});
```
在这种情况下，MVEL会看到目标方法接受一个int[]参数并自动转换数组类型。


### 4. 属性

MVEL属性遵循在其他语言（如Groovy，OGNL，EL等）中的bean属性表达中的完整约定(MVEL property navigation follows well-established conventions found in other bean property expressions found in other languages)。

与需要限定的其他语言不同，MVEL提供了访问属性，静态字段，Map等的单一统一语法。

#### 4.1 Bean Properties

大多数Java开发人员熟悉并使用其Java对象中的`getter`/`setter`方法，以便封装属性访问。 例如，你可以从对象访问属性：
```
user.getManager().getName();
```
为了简化此操作，你可以使用以下表达式访问相同的属性：
```
user.manager.name
```

Example:
```
Fruit fruit = new Fruit();
fruit.setName("苹果");

//String expression = "fruit.getName()";
String expression = "fruit.name";
Map<String, Object> paramMap = Maps.newHashMap();
paramMap.put("fruit", fruit);
Object object = MVEL.eval(expression, paramMap);
System.out.println(object); // 苹果
```

==备注==

当对象中的字段为public的情况下，MVEL仍然希望通过其getter方法访问该属性。

#### 4.2 Null-Safe Bean Navigation

有时候，你可能拥有包含空元素的属性表达式，需要你进行空值检查。你可以使用空安全运算符来简化此操作：

```
user.?manager.name
```
这在功能上等同于：
```
if (user.manager != null) { return user.manager.name; } else { return null; }
```

#### 4.3 Collections

集合的遍历也可以使用缩写语法实现。

##### 4.3.1 List

List的访问与数组相同。 例如：
```
 user[5]
```
相当于Java代码：
```
user.get(5);
```

##### 4.3.2 Map

Map以数组相同的方式访问，除非任意对象可以作为索引值传递。 例如：
```
user["foobar"]
```
相当于Java代码：
```
user.get("foobar");
```
对于使用字符串作为key的Map，你可以使用另一种特殊语法：
```
user.foobar
```
...允许你将Map本身视为虚拟对象。

##### 4.3.3 Strings as Arrays

为了使用属性索引（以及迭代），所有字符串都被视为数组。 在MVEL中，你可以访问String变量中的第一个字符：
```
foo = "My String";
foo[0]; // returns 'M';
```

### 5. 字面值

字面值用于表示特定脚本的源中的固定值(represent a fixed-value in the source of a particular script)。

#### 5.1 字符串字面值

字符串字面值可以用单引号或双引号表示。

```
"This is a string literal"
'This is also string literal'
```
#### 5.2 字符串转义序列

- `\\` 双重转义允许在字符串中出现单个反斜杠。
- `\n` 新行
- `\r` 回车
- `\u####` Unicode字符（示例：\ uAE00）
- `\###` 八进制字符（示例：\ 73）

#### 5.3 数值型字面值

整数可以十进制（10位），八进制（8位）或十六进制（16位）表示。

十进制整数可以表示为不以零开始的任何数字。

```
125 // 十进制
```
八进制表示为带有`0`前缀的数字，后跟数字范围从0到7。

```
0353 // 八进制
```
十六进制表示为带有`0x`前缀的数字，后跟数字范围为0-9..A-F。

```
0xAFF0 // 十六进制
```
#### 5.4 浮点型字面值

浮点数由整数部分和由点/周期字符表示的小数部分组成，并具有可选的类型后缀。
```
10.503 // a double
94.92d // a double
14.5f // a float
```
#### 5.5 BigInteger和BigDecimal字面值

你可以使用后缀`B`和`I`来表示`BigInteger`和`BigDecimal`字面值（大写字母是必填字段）。

```
104.39484B // BigDecimal
8.4I // BigInteger
```
#### 5.6 Boolean 字面值

布尔字面值由保留关键字`true`和`false`表示。

#### 5.7 Null 字面值

Null字面值由保留的关键字`null`或`nil`表示。

### 6. 类型字面值

类型文字与Java中的类似，具有以下格式：
```
<PackageName>．<ClassName>
```
所以一个类可能是被限定为如下：
```
java.util.HashMap
```
或者如果类是通过内联或外部配置引入的，那么可以使用其非限定名称引用它：
```
HashMap
```
#### 6.1 嵌套类

MVEL 2.0中的标准点符号`.`（如Java中）无法访问嵌套类。 相反，你必须使用`$`符号限定这些类。

```
org.proctor.Person$BodyPart 
```

### 7. 流控制

#### 7.1 If-Then-Else

MVEL支持完整的C/Java风格的if-then-else块。 例如：
```
if (var > 0) {
   System.out.println("Greater than zero!");
}
else if (var == -1) { 
   System.out.println("Minus one!");
}
else { 
   System.out.println("Something else!");
}
```
Example:
```
String expression = "if (param > 0) {return \"Greater than zero!\"; } else if (param == -1) { return \"Minus one!\"; } else { return \"Something else!\"; }";
Map<String, Object> paramMap = Maps.newHashMap();
paramMap.put("param", 2);
Object object = MVEL.eval(expression, paramMap);
System.out.println(object); // Greater than zero!
```


#### 7.2 三元声明

就像Java一样,支持三元声明语句：
```
num > 0 ? "Yes" : "No";
```
和嵌套三元语句：
```
num > 0 ? "Yes" : (num == -1 ? "Minus One!" : "No")
```

Example:
```
String expression = "num > 0  ? \"Yes\" : \"No\";";
Map<String, Object> paramMap = Maps.newHashMap();
paramMap.put("num", new Integer(1));
Object object = eval(expression, paramMap);
System.out.println(object); // Yes
```

#### 7.3 Foreach

MVEL中最强大的功能之一就是`foreach`操作。 它与Java 1.5中的`foreach`运算符的语法和功能类似。它接受由冒号分隔的两个参数，第一个是当前元素的局部变量，第二个是要迭代的集合或数组。
```
count = 0;
foreach (name : people) {
   count++;
   System.out.println("Person #" + count + ":" + name);
}
    
System.out.println("Total people: " + count);
```
由于MVEL将字符串视为可迭代对象，你可以使用`foreach`块来迭代字符串（逐字符）：
```
str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

foreach (el : str) {
   System.out.print("["+ el + "]"); 
}
```
上面输出为: 
```
[A][B][C][D][E][F][G][H][I][J][K][L][M][N][O][P][Q][R][S][T][U][V][W][X][Y][Z]
```
你还可以使用MVEL计数到一个整数值（从1）：
```
foreach (x : 9) { 
   System.out.print(x);
} 
```
上面输出为:
```
123456789
```
==语法注意==

从MVEL 2.0开始，可以通过使用`for`关键字简单地简化foreach，就像在Java 5.0中一样。 例如：
```
for (item : collection) { ... }
```
#### 7.4 For循环

MVEL 2.0实现标准C `for`循环：
```
for (int i =0; i < 100; i++) { 
   System.out.println(i);
}
```
#### 7.5 Do While, Do Until

在MVEL中实现了`do while`和`do until`，遵循与Java相同的约定，带有`until`的与`while `相反。

```
do { 
   x = something();
} 
while (x != null);
```
...在语义上相当于...

```
do {
   x = something();
}
until (x == null);
```
#### 7.5 While, Until

MVEL 2.0实现标准的`while`，以及相反的`until`。

```
while (isTrue()) {
   doSomething();
}
```
或者
```
until (isFalse()) {
   doSomething();
}
```

### 8. 投影与折叠

简单地说，投影是表示集合的一种方式。可以使用非常简单的语法，检查集合中非常复杂的对象模型。

想像你有一个User对象的集合。 这些对象中的每一个都有一个`Parent`。 现在，你想要在用户层次结构中获取父目录的所有名称（假设Parent类有一个`name`字段），你将会写下如下内容：
```
parentNames = (parent.name in users);
```
甚至可以执行嵌套操作。想象一下，User对象有一个名为`familyMembers`的成员集合，我们想要一个所有家庭成员名称的列表：
```
familyMembers = (name in (familyMembers in users));
```

### 9. 变量赋值

MVEL允许你可以在表达式中赋值变量，运行时可以提取使用，或在表达式中直接使用。

由于MVEL是一种动态类型的语言，你不需要指定一个类型来声明一个新的变量。 但是，你可以选择这样做。

```
str = "My String"; // valid
String str = "My String"; // valid
```
然而，与Java不同，MVEL在为类型变量赋值时提供了自动类型转换（如果可能的话）。 例如：

```
String num = 1;
assert num instanceof String && num == "1";
```
对于动态类型变量，如果你只想执行类型转换，你可以简单地将该值转换为所需的类型：
```
num = (String) 1;
assert num instanceof String && num == "1";
```

### 10. 方法定义

MVEL允许使用`def`或`function`关键字定义native函数。

函数按声明的顺序定义，不能前言引用。 唯一的例外是在函数本身中，可以直接引用另一个函数。

#### 10.1 简单示例

定义一个简单的函数:
```
def hello() { System.out.println("Hello!"); }
```
这定义了一个名为“hello”的简单函数，它不接受任何参数。调用该函数时打印`你好！`到控制台．MVEL定义的函数像任何常规方法调用一样工作。
```
hello(); // calls function
```
Example:
```
String expression = "def hello() { return \"Hello!\"; } hello();";
Map<String, Object> paramMap = Maps.newHashMap();
Object object = MVEL.eval(expression, paramMap);
System.out.println(object); // Hello!
```

#### 10.2 接受参数并返回值

函数可以被声明为接受参数，并且可以返回单个值。如下示例：
```
def addTwo(a, b) { 
   a + b;
}
```
该函数将接受两个参数（a和b），然后将两个变量相加。 由于MVEL使用最终值退出原则，所以返回最终结果值。因此，你可以使用以下功能：
```
val = addTwo(5, 2);
assert val == 10;
```
`return`关键字也可用于强制从函数的内部程序流程中返回值。

Example:
```
String expression = "def addTwo(num1, num2) { num1 + num2; } val = addTwo(a, b);";
Map<String, Object> paramMap = Maps.newHashMap();
paramMap.put("a", 2);
paramMap.put("b", 4);
Object object = MVEL.eval(expression, paramMap);
System.out.println(object); // 6
```

#### 10.3 Closures

MVEL允许Closures。 但是，该功能不能与本地Java方法互操作。
```
// define a function that accepts a parameter    
def someFunction(f_ptr) { f_ptr(); }

// define a var
var a = 10;

// pass the function a closure
someFunction(def { a * 10 }); 
```




原文：https://en.wikibooks.org/wiki/Transwiki:MVEL_Language_Guide#Language_Guide_for_2.0

