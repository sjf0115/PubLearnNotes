
本文主要介绍如何使用 Druid SQL Parser 来解析 MySQL 的 Select 查询(无论是简单查询还是复杂的子查询、JOIN 查询等)中的表名。

## 1. 生成抽象语法树

使用 Druid SQL Parser 解析 Select 查询中的表名，首先需要创建解析器并解析生成[抽象语法树 AST](https://smartsi.blog.csdn.net/article/details/143134801)，这个过程有多种方法可以实现。你可以创建 `MySqlStatementParser` 对象并调用 `parseStatement` 方法来生成：
```java
MySqlStatementParser parser = new MySqlStatementParser(sql);
SQLStatement statement = parser.parseStatement();
```
或者你直接使用 SQLUtils 工具类中的 `parseSingleMysqlStatement` 方法：
```java
SQLStatement statement = SQLUtils.parseSingleMysqlStatement(sql);
```
由于我们这只是针对 Select 查询语句，所以你也可以直接使用 `MySqlSelectParser` 获取 `SQLSelect`：
```java
MySqlSelectParser parser = new MySqlSelectParser(sql);
SQLSelect select = parser.select();
```
当然不只上面这这几种方法，你也可以选择其他方法。

> 对抽象语法树 AST 不熟悉的同学请先查阅博文[深入理解 Druid SQL Parser 抽象语法树 AST](https://smartsi.blog.csdn.net/article/details/143134801)

## 2. 遍历抽象语法树获取表名

创建好 `SQLStatement` (或者 `SQLSelect`)就已经成功解析成抽象语法树 AST 了，接下来是使用 AST。一般分为两种方案：
- 手工编写代码遍历 AST 节点。灵活性强、适合复杂 SQL 和规范性不强的 SQL 解析。
- 使用 Visitor 遍历 AST 节点。使用简单便捷，适合规范性强的 SQL 解析。

### 2.1 手工编写

手工编写代码直接解析抽象语法树 `SQLStatement` 或者解析更直接的 `SQLSelect`。如下所示直接获取 `SQLSelect` 进行解析：
```java
public static List<String> parseTableNameFromSql(String sql) {
    MySqlSelectParser parser = new MySqlSelectParser(sql);
    SQLSelect select = parser.select();
    SQLSelectQuery selectQuery = select.getQuery();
    return parseTableNameFromQuery(selectQuery);
}
```
上面定义的 `parseTableNameFromQuery` 方法会根据 `SQLSelectQuery` 的不同进行不同的解析：
```java
private static List<String> parseTableNameFromQuery(SQLSelectQuery selectQuery) {
    List<String> tableNames = Lists.newArrayList();
    if (selectQuery == null) {
        return tableNames;
    }
    if (selectQuery instanceof MySqlSelectQueryBlock) {
        // 解析 MySqlSelectQueryBlock 查询
        MySqlSelectQueryBlock queryBlock = (MySqlSelectQueryBlock) selectQuery;
        SQLTableSource tableSource = queryBlock.getFrom();
        List<String> subTableNames = parseTableNameFromTableSource(tableSource);
        tableNames.addAll(subTableNames);
    } else if (selectQuery instanceof SQLUnionQuery) {
        // 解析 SQLUnionQuery Union 查询
        SQLUnionQuery unionQuery = (SQLUnionQuery) selectQuery;
        SQLSelectQuery leftSelectQuery = unionQuery.getLeft();
        // 左子查询表
        List<String> leftSelectTableNames = parseTableNameFromQuery(leftSelectQuery);
        tableNames.addAll(leftSelectTableNames);
        // 右子查询表
        SQLSelectQuery rightSelectQuery = unionQuery.getRight();
        List<String> rightSelectTableNames = parseTableNameFromQuery(rightSelectQuery);
        tableNames.addAll(rightSelectTableNames);
    } else {
        throw new RuntimeException("不支持该 SQLSelectQuery");
    }
    return tableNames;
}
```
在这为了演示我们只支持 `MySqlSelectQueryBlock` 和 `SQLUnionQuery` 两种 `SQLSelectQuery` 查询的解析。`MySqlSelectQueryBlock` 面向的一般是加单查询、LateralView 查询、JOIN 查询等，可以获取 `SQLTableSource` 调用 `parseTableNameFromTableSource` 方法来解析抽象语法树。`SQLUnionQuery` 主要面向的是 Union 查询，本质上会对应多个子查询，通过递归解析子查询最终获取 `SQLTableSource`。然后调用我们定义的 `parseTableNameFromTableSource` 方法，根据 `SQLTableSource` 的不同会进行不同的解析：
```java
private static List<String> parseTableNameFromTableSource(SQLTableSource tableSource) {
    List<String> tableNames = Lists.newArrayList();
    if (tableSource == null) {
        return tableNames;
    }
    if (tableSource instanceof SQLExprTableSource) {
        // 解析简单查询
        SQLExprTableSource exprTableSource = (SQLExprTableSource) tableSource;
        String tableName = exprTableSource.getTableName();
        tableNames.add(tableName);
    } else if (tableSource instanceof SQLJoinTableSource) {
        // 解析 JOIN 查询
        SQLJoinTableSource joinTableSource = (SQLJoinTableSource) tableSource;
        SQLTableSource leftTableSource = joinTableSource.getLeft();
        // 左表
        List<String> leftTableNames = parseTableNameFromTableSource(leftTableSource);
        tableNames.addAll(leftTableNames);
        // 右表
        SQLTableSource rightTableSource = joinTableSource.getRight();
        List<String> rightTableNames = parseTableNameFromTableSource(rightTableSource);
        tableNames.addAll(rightTableNames);
    } else if (tableSource instanceof SQLLateralViewTableSource) {
        // 解析 LateralView 查询
        SQLLateralViewTableSource lateralViewTableSource = (SQLLateralViewTableSource) tableSource;
        SQLTableSource subTableSource = lateralViewTableSource.getTableSource();
        List<String> subTableNames = parseTableNameFromTableSource(subTableSource);
        tableNames.addAll(subTableNames);
    } else if (tableSource instanceof SQLUnionQueryTableSource) {
        // 解析 Union 查询
        SQLUnionQueryTableSource unionQueryTableSource = (SQLUnionQueryTableSource) tableSource;
        SQLUnionQuery unionQuery = unionQueryTableSource.getUnion();
        SQLSelectQuery leftSelectQuery = unionQuery.getLeft();
        // 左子查询表
        List<String> leftSelectTableNames = parseTableNameFromQuery(leftSelectQuery);
        tableNames.addAll(leftSelectTableNames);
        // 右子查询表
        SQLSelectQuery rightSelectQuery = unionQuery.getRight();
        List<String> rightSelectTableNames = parseTableNameFromQuery(rightSelectQuery);
        tableNames.addAll(rightSelectTableNames);
    } else if (tableSource instanceof SQLSubqueryTableSource) {
        // 解析子查询
        SQLSubqueryTableSource subqueryTableSource = (SQLSubqueryTableSource) tableSource;
        SQLSelect subSelect = subqueryTableSource.getSelect();
        SQLSelectQuery selectQuery = subSelect.getQuery();
        List<String> selectTableNames = parseTableNameFromQuery(selectQuery);
        tableNames.addAll(selectTableNames);
    }  else if (tableSource instanceof SQLValuesTableSource) {
        // 无表
    } else {
        throw new RuntimeException("不支持该 TableSource");
    }
    return tableNames;
}
```
上述代码支持 `SQLExprTableSource`、`SQLJoinTableSource`、`SQLLateralViewTableSource`、`SQLUnionQueryTableSource`、`SQLSubqueryTableSource`、`SQLValuesTableSource` 的解析。

解析逻辑完成之后可以针对不同类型的查询语句进行验证：
```java
@Test
public void testExprTableName() {
    String sql = "SELECT id, name, age FROM user AS a";
    List<String> tableNames  = parseTableNameFromSql(sql);
    System.out.println(tableNames); // [user]
}

@Test
public void testJoinTableName() {
    String sql = "SELECT a.id, a.name, a.age, b.department_name\n" +
            "FROM user AS a\n" +
            "LEFT OUTER JOIN department AS b\n" +
            "ON a.id = b.user_id";
    List<String> tableNames  = parseTableNameFromSql(sql);
    System.out.println(tableNames); // [user, department]
}

@Test
public void testLateralViewTableName() {
    String sql = "SELECT sport\n" +
            "FROM user AS a\n" +
            "LATERAL VIEW EXPLODE(like_sports) like_sports AS sport";
    List<String> tableNames  = parseTableNameFromSql(sql);
    System.out.println(tableNames); // [user]
}

@Test
public void testSubqueryTableName() {
    String sql = "SELECT id, name\n" +
            "FROM (\n" +
            "  SELECT id, name FROM user\n" +
            ") AS a";
    List<String> tableNames  = parseTableNameFromSql(sql);
    System.out.println(tableNames); // [user]
}

@Test
public void testUnionTableName() {
    String sql = "SELECT 'user' AS type, id, name\n" +
            "FROM user\n" +
            "UNION ALL\n" +
            "SELECT 'department' AS type, id, name\n" +
            "FROM department\n" +
            "UNION ALL\n" +
            "SELECT 'company' AS type, id, name\n" +
            "FROM company";
    List<String> tableNames  = parseTableNameFromSql(sql);
    System.out.println(tableNames); // [user, department, company]
}

@Test
public void testValuesTableName() {
    String sql = "SELECT id, name\n" +
            "FROM Values ('1', 'Lucy'),('2', 'Lily') t(id, name)";
    List<String> tableNames  = parseTableNameFromSql(sql);
    System.out.println(tableNames); // []
}
```

### 2.2 Visitor 访问者模式

Visitor 需要编写代码实现 SQLASTVisitor 接口（可直接 SQLASTVisitorAdapter 类）重写 visit 方法实现遍历。不过 Druid 已经为我们提供了一些内置的 Visitor，对于我们查询 Select 语句中的表名这种简单需求，可以直接使用内置 Visitor。如下是使用 MySqlSchemaStatVisitor 遍历抽象语法树获取表名：
```java
public List<TableName> parseTableNameFromSql(String sql) {
    // 解析
    MySqlStatementParser parser = new MySqlStatementParser(sql);
    SQLStatement statement = parser.parseStatement();

    // 访问者模式遍历抽象语法树
    MySqlSchemaStatVisitor visitor = new MySqlSchemaStatVisitor();
    statement.accept(visitor);

    // 解析表名
    List<TableName> tableNames = Lists.newArrayList();
    Map<TableStat.Name, TableStat> tables = visitor.getTables();
    for (Map.Entry<TableStat.Name, TableStat> entry : tables.entrySet()) {
        TableName tableName = new TableName();
        // 表名
        tableName.setTableName(entry.getKey().getName());
        // SQL 类型
        tableName.setTableType(entry.getValue().toString());
        tableNames.add(tableName);
    }
    return tableNames;
}
```
这种模式相比自己遍历抽象语法树更简洁，除此之外它不仅仅可以查询 Select 语句中的表名，也可以查询 INSERT 等语句中的表名。例如，可以解析如下所示 SQL 语句中的两个表：
```java
@Test
public void testInsert() {
    String sql = "INSERT INTO result_table SELECT * FROM source_table";
    List<TableName> tableNames = parseTableNameFromSql2(sql);
    for(TableName tableName : tableNames) {
        // 表名：result_table, 类型：Insert
        // 表名：source_table, 类型：Select
        System.out.println("表名：" + tableName.getTableName() + ", 类型：" + tableName.getTableType());
    }
}
```
