## 1. 什么是 AST

AST 是 abstract syntax tree 的缩写，也就是抽象语法树。和所有的 Parser 一样，Druid Parser 也会生成一个抽象语法树。

## 2. AST 节点类型

在 Druid SQL Parser 中，SQLObject 对象是 Druid 体系中的顶层接口，用于描述 AST 节点类型，主要包括 SQLExpr、SQLStatement、SQLDataType、SQLDbTypedObject、SQLHint 等抽象类型。核心是 SQLExpr、SQLStatement 类型：
```java
public interface SQLObject {
  ...
}

public interface SQLExpr extends SQLObject, Cloneable {
  ...
}

public interface SQLStatement extends SQLObject, SQLDbTypedObject {
  ...
}
```

### 2.1 SQLStatemment

SQLStatement 表示一条 SQL 语句，我们知道常见的 SQL 语句有 CRUD 四种操作，所以 SQLStatement 会有四种主要实现类

#### 2.1.1 SQLDDLStatement

```java
public interface SQLDDLStatement extends SQLStatement {
    default DDLObjectType getDDLObjectType() {
        return DDLObjectType.OTHER;
    }

    enum DDLObjectType {
        DATABASE,
        TABLE,
        VIEW,
        MATERIALIZED_VIEW,
        TABLE_SPACE,
        TABLE_GROUP,
        FUNCTION,
        TRIGGER,
        USER,
        ROLE,
        SEQUENCE,
        INDEX,
        PROCEDURE,
        TYPE,
        OTHER
    }
}
```

```java
public interface SQLCreateStatement extends SQLDDLStatement {
    default SQLName getName() {
        return null;
    }
}
```

```java
public interface SQLDropStatement extends SQLDDLStatement {
    default SQLName getName() {
        return null;
    }
}
```

```java
public interface SQLAlterStatement extends SQLDDLStatement {
    default DDLObjectType getDDLObjectType() {
        return DDLObjectType.OTHER;
    }
}
```




#### 2.1.2 SQLStatementImpl

```java
public abstract class SQLStatementImpl extends SQLObjectImpl implements SQLStatement {
  ...
}
```

##### 2.1.2.1 SQLSelectStatement

##### 2.1.2.2 SQLInsertStatement

##### 2.1.2.3 SQLDeleteStatement

##### 2.1.2.4 SQLUpdateStatement





### 2.2 SQLExpr

SQLExpr 是有几个实现类的。

#### 2.2.1 SQLIdentifierExpr

#### 2.2.2 SQLPropertyExpr

#### 2.2.3 SQLVariantRefExpr

#### 2.2.4 SQLIntegerExpr

#### 2.2.5 SQLCharExpr





```java
public interface SQLValuableExpr extends SQLExpr {
    ...
}
```

```java
public abstract class SQLNumericLiteralExpr extends SQLExprImpl implements SQLLiteralExpr {
  ...
}
```

```java
public class SQLBigIntExpr extends SQLNumericLiteralExpr implements SQLValuableExpr {
    private Long value;
    ...
}
```



```java
public final class SQLPropertyExpr extends SQLExprImpl implements SQLName, SQLReplaceable, Comparable<SQLPropertyExpr> {
  ...
}
```






## 3. 怎么产生 AST 节点





https://github.com/alibaba/druid/wiki/Druid_SQL_AST#2-%E5%9C%A8druid-sql-parser%E4%B8%AD%E6%9C%89%E5%93%AA%E4%BA%9Bast%E8%8A%82%E7%82%B9%E7%B1%BB%E5%9E%8B
