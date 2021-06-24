

SqlSelect 是解析树的一个节点，代表了一个 SELECT 语句。

SqlNodeList 是一个 SqlNode 列表。它同样也是一个 SqlNode，所以也可能会出现在解析树中：
```java
public class SqlNodeList extends SqlNode implements List<SqlNode>, RandomAccess {
}
```

SqlIdentifier 表示一个标识符，可能是复合的。
