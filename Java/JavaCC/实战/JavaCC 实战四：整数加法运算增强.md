## 5. 扩展解析器

JavaCC 为 BNF 生产式生成的方法(例如 `Start`)在默认情况下只是检查输入是否与规范匹配。但是，我们可以用 Java 代码来扩展 BNF 生产式，使其包含在生成的方法中。JavaCC 为我们提供了框架，只需要完善框架即可。我们将对上面的 `adder.jj` 语法文件做一些修改来扩展 BNF 生产式，保存为 `adder1.jj` 语法文件。在 `Start` 方法中添加了一些声明和一些 Java 代码：
```
int Start() throws NumberFormatException :
{
Token t ;
int i ;
int value ;
}
{
t = <NUMBER>
{ i = Integer.parseInt( t.image ) ; }
{ value = i ; }
(
<PLUS>
t = <NUMBER>
{ i = Integer.parseInt( t.image ) ; }
{ value += i ; }
)*
<EOF>
{ return value ; }
}
```

首先，BNF 生成的返回类型，以及由此生成的方法，从 void 变为 int。我们已经声明了可以从生成的方法中抛出 NumberFormatException。我们声明了三个变量。变量 `t` 为类 Token 的类型，它是一个表示 Token 的生成类。Token 类的 image 字段记录匹配的字符串。当在 BNF 实例中匹配一个 Token 时，我们可以通过为其分配引用来记录 Token 对象，如下所示：
```
t = <NUMBER>
```
在 BNF 实例的大括号内，我们可以添加任何我们想要的 Java 语句，这些语句基本上逐字复制到生成的方法中。由于生成的 Start 方法现在返回一个值，我们必须修改 main 方法：
```java
static void main( String[] args ) throws ParseException, TokenMgrError, NumberFormatException {
  Adder parser = new Adder( System.in ) ;
  int val = parser.Start() ;
  System.out.println(val);
}
```
还有一个小的优化要做。如下两行：
```
t = <NUMBER>
{ i = Integer.parseInt( t.image ) ; }
```
出现过两次。虽然在这种情况下没有太大的区别，因为只涉及到两行代码，但这种重复可能会导致维护问题。因此，我们将把这两行拆解成另一个 BNF 实例，并命名为 Primary：
```

```
查看生成的方法可以看到JavaCC如何将Java声明和语句集成到生成方法的框架中。
```
```

稍后我们将看到将参数传递到 BNF 实例中也是可以的。
