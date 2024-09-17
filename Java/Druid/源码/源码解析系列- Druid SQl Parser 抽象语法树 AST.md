## 1. 什么是 AST

AST 是 abstract syntax tree 的缩写，也就是抽象语法树。和所有的 Parser 一样，Druid Parser 也会生成一个抽象语法树。

## 2. AST 节点类型

在 Druid SQL Parser 中，SQLObject 对象是 Druid 体系中的顶层接口，用于描述 AST 节点类型，主要包括 SQLStatement、SQLExpr、SQLDataType、SQLTableSource、SQLHint 等抽象类型。核心是 SQLExpr、SQLStatement、SQLDataType、SQLTableSource 类型：
```java
public interface SQLObject {
    ...
}

public interface SQLExpr extends SQLObject, Cloneable {
    ...
}

public interface SQLDbTypedObject extends SQLObject {
    ...
}

public interface SQLStatement extends SQLObject, SQLDbTypedObject {
    ...
}

public interface SQLTableSource extends SQLObject {
    ...
}

public interface SQLDataType extends SQLObject {
    ...
}
```

### 2.1 SQLStatemment

SQLStatement 表示一条 SQL 语句，SQL 按其功能可以分为 4 类：
- DDL：数据定义语言，用来操作数据库、表、列等。主要语句有 CREATE、ALTER 和 DROP。
- DML：数据操作语言，用来操作数据库中表里的数据。主要语句有 INSERT、UPDATE 和 DELETE。
- DQL：数据查询语言，用来查询数据。核心语句为 SELECT。
- DCL：数据控制语言，用来操作访问权限和安全级别。主要语句有 GRANT、DENY 等。

#### 2.1.1 DDL 数据定义语言语句

DDL 数据定义语言语句通过 SQLDDLStatement 接口进行抽象：
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
DDL 语句主要有 CREATE、ALTER 和 DROP 三类，因此 SQLDDLStatement 分别对应细分 SQLCreateStatement、SQLAlterStatement、SQLDropStatement 三类：
```java
public interface SQLCreateStatement extends SQLDDLStatement {
    default SQLName getName() {
        return null;
    }
}

public interface SQLAlterStatement extends SQLDDLStatement {
    default DDLObjectType getDDLObjectType() {
        return DDLObjectType.OTHER;
    }
}

public interface SQLDropStatement extends SQLDDLStatement {
    default SQLName getName() {
        return null;
    }
}
```
根据 DDL 对象类型 DDLObjectType 的不同，又分为不同类型的 Statement，以 SQLCreateStatement 为例：

![](img-druid-sql-parser-ast-1.png)

#### 2.1.2 DML 数据操作语言语句

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
