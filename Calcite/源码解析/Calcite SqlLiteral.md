SqlLiteral 用来封装输入的常量(字面量)，它和它的子类一般用来封装具体的变量值，也可以通过 getValue 返回需要的值。

```java
public class SqlLiteral extends SqlNode {
  private final SqlTypeName typeName;
  protected final @Nullable Object value;
}
```
