
```java
public interface SQLASTVisitor {
    default void endVisit(SQLAllColumnExpr x) {
    }

    default void endVisit(SQLBetweenExpr x) {
    }

    default void endVisit(SQLBinaryOpExpr x) {
    }

    ...

    default boolean visit(SQLCreateTableStatement x) {
        return true;
    }

    default void endVisit(SQLCreateTableStatement x) {
    }

    ...

}
```


```java
public interface MySqlASTVisitor extends SQLASTVisitor {
    default boolean visit(MySqlTableIndex x) {
        return true;
    }

    default void endVisit(MySqlTableIndex x) {
    }

    default boolean visit(MySqlKey x) {
        return true;
    }

    default void endVisit(MySqlKey x) {
    }

    default boolean visit(MySqlPrimaryKey x) {
        return true;
    }

    default void endVisit(MySqlPrimaryKey x) {
    }

    ...

}
```
