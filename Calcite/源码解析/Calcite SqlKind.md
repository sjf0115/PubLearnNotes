
SqlKind 表示 SqlNode 的类型。这些值是不可变的规范常量，因此可以使用types快速查找特定类型的表达式。要识别对'='等通用操作符的调用，请使用SqlNode.isA:
exp.isA (=)
只有常用的节点才有自己的类型;其他节点为other类型。有些值，比如SET_QUERY，表示聚合。
要在多个选项之间快速选择，请使用switch语句:
```java
switch (exp.getKind()) {
    case EQUALS:
       ...;
    case NOT_EQUALS:
       ...;
    default:
    throw new AssertionError("unexpected");
}
```

注意，我们甚至不必检查SqlNode是否为SqlCall。
要识别表达式类别，请使用SqlNode。具有聚合SqlKind的isA。下面的表达式对于调用'='和'>='将返回true，但是对于常量'5'或调用'+'将返回false:
exp.isA (SqlKind.COMPARISON)
RexNode也有一个getKind方法;在适用的情况下，在从SqlNode到RexNode的转换过程中保留SqlKind值。
“普通”并没有无懈可击的定义，但没关系。总会有没有自己类型的操作符，对于这些操作符，我们使用sqlooperator。但是对于真正常见的，例如，我们正在寻找AND, OR和EQUALS的许多地方，enum有帮助。
(如果我们使用Scala, sqlooperator将是case类，我们不需要SqlKind。但我们不是。)
