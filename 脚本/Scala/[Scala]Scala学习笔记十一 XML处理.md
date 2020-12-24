Scala提供了对XML字面量的内建支持，让我们可以很容易的在程序代码中生成XML片段．

### 1. XML字面量

Scala对XML有内建支持．可以定义XML字面量，直接用XML代码即可:
```
val doc = <html><head><title>测试</title></head><body><p>Hello World</p></body></html>
```
这样`doc`就成了类型为`scala.xml.Elem`的值，表示一个XML元素．
XML字面量也可以是一系列的节点:
```
val items = <li>Fread</li><li>Wilma</li>
```
这样`items`就成了类型为`scala.xml.NodeSeq`的值，表示一个节点．

### 2. XML节点

Node类是所有XML节点类型的祖先．它有两个最重要的子类`Text`和`Elem`．
Elem类描述的是XML元素:
```
val elem = <a href="http://xxx">This is a <em>beautiful</em> girl</a>
```
label属性产出标签名称(例如这里是`a`)，而child属性对应的是后代的序列(在上例中是两个Text节点和一个Elem节点)．\

节点序列的类型为NodeSeq，它是Seq[Node]的子类型，加入了对XPath操作的支持:如果要遍历节点序列，只需要简单的使用for循环即可，例如:
```
for(n <- elem.child) 处理 n
```
如果你通过编程的方式构建节点序列，则可以使用`NodeBuffer`，它是`ArrayBuffer[Node]`的子类:
```
val items = new scala.xml.NodeBuffer
items += <li>苹果</li>
items += <li>香蕉</li>
val nodes: scala.xml.NodeSeq = items
```

**备注**
```
Node类扩展自NodeSeq．单个节点等同于长度为1的序列．这样的设计本意是更加方便的处理那些既能返回单个节点也能返回一系列节点的函数．(这样会带来其他问题，不建议使用)

NodeBuffer是一个Seq[Node]，它可以被隐式转化为NodeSeq．一旦完成这个转换，需要小心别再继续修改它，因为XML节点序列应该是不可变的．
```

### 3. 元素属性

要处理某个元素的属性键和值，可以用`attributes`属性．将生成一个类型为`MetaData`的对象，该对象几乎就是但又不完全等同于一个从属性键对属性值的映射．可以使用()操作符来访问给定键的值:
```
val elem = <a href="http://xxx">This is a <em>beautiful</em> girl</a>
elem.attributes("href")
res13: Seq[scala.xml.Node] = http://xxx
```
但是使用这种方法调用产生的是一个节点序列，而不是字符串，因为XML的属性可以包含实体引用．如果你很肯定在你的属性当中不存在未被解析的实体，则可以　简单的调用text方法来将节点序列转成字符串:
```
scala> val elem = <a href="http://xxx">This is a <em>beautiful</em> girl</a>
elem: scala.xml.Elem = <a href="http://xxx">This is a <em>beautiful</em> girl</a>

scala> elem.attributes("href").text
res2: String = http://xxx
```
如果这样的一个属性不存，()操作符将返回null．如果你不喜欢处理null，可以用get方法，返回的是一个Option[Seq[Node]]．可惜MetaData类并没有getOrElse方法，不过你可以对get方法返回的Option应用getOrElse:
```
scala> elem.attributes.get("href2").getOrElse("")
res7: Object = ""

scala> elem.attributes.get("href").getOrElse("")
res8: Object = http://xxx
```
如果要遍历所有属性，使用如下方式:
```
for(attr <- elem.attributes){
  // 处理attr.key 和 attr.value.text
}
```
或者使用`asAttrMap`方法:
```
scala> val img = <img src="https://xxx.jpg" alt="这里写图片描述" title=""/>
img: scala.xml.Elem = <img src="https://xxx.jpg" alt="这里写图片描述" title=""/>

scala> val map = img.attributes.asAttrMap
map: Map[String,String] = Map(src -> https://xxx.jpg, alt -> 这里写图片描述, title -> "")
```
