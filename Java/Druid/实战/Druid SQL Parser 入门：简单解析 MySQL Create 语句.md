今天来介绍一下如何使用 Druid SQL Parser 来解析 MySQL Create 语句。

## 1. 添加依赖

如果要使用 Druid SQL Parser 需要在 pom 文件中添加如下依赖：
```xml
<dependency>
    <groupId>com.alibaba</groupId>
    <artifactId>druid</artifactId>
    <version>1.2.20</version>
</dependency>
```
> 在这使用的是 1.2.20 版本，根据你的需求选择合适的版本。

## 2. 生成抽象语法树

使用 Druid SQL Parser 来解析 MySQL Create 语句首先需要将 SQL 语句解析成抽象语法树。下面介绍几种生成抽象语法树的方法。

### 2.1 MySqlCreateTableParser

你可以使用 `MySqlCreateTableParser` 创建解析器解析 SQL 语句来生成 `MySqlCreateTableStatement` 抽象语法树：
```java
MySqlCreateTableParser parser = new MySqlCreateTableParser(sql);
MySqlCreateTableStatement stmt = (MySqlCreateTableStatement) parser.parseCreateTable();
```
`MySqlCreateTableParser` 创建的 `Statement` 实际上是 `MySqlCreateTableStatement`：
```java
public SQLCreateTableStatement parseCreateTable() {
    return parseCreateTable(true);
}

public MySqlCreateTableStatement parseCreateTable(boolean acceptCreate) {
    MySqlCreateTableStatement stmt = new MySqlCreateTableStatement();
    ...
    return stmt;
}
```

### 2.2 MySqlStatementParser

你也可以使用 `MySqlStatementParser` 创建解析器来生成 `MySqlCreateTableStatement` 抽象语法树：
```java
MySqlStatementParser parser = new MySqlStatementParser(sql);
MySqlCreateTableStatement createTableStatement = (MySqlCreateTableStatement) parser.parseCreateTable();
```
可以看到 `MySqlStatementParser` 实际上是对 `MySqlCreateTableParser` 的封装，最终还是使用的 `MySqlCreateTableParser` 来创建抽象语法树：
```java
public SQLCreateTableStatement parseCreateTable() {
    MySqlCreateTableParser parser = new MySqlCreateTableParser(this.exprParser);
    return parser.parseCreateTable();
}
```

### 2.3 SQLUtils

你也可以使用 `SQLUtils` 工具类直接生成 `MySqlCreateTableStatement` 抽象语法树：
```java
SQLStatement statement = SQLUtils.parseSingleMysqlStatement(sql);
MySqlCreateTableStatement createTableStatement = (MySqlCreateTableStatement) statement;
```
`SQLUtils` 工具类提供的 `parseSingleMysqlStatement` 方法是对不同数据库解析器的封装，可以看到对于 MySQL 来说是通过 `MySqlStatementParser` 来实现解析的，即最终还是通过 `MySqlCreateTableParser` 来创建抽象语法树：
```java
public static SQLStatement parseSingleMysqlStatement(String sql) {
    return parseSingleStatement(sql, DbType.mysql, false);
}

public static SQLStatement parseSingleStatement(String sql, DbType dbType, boolean keepComments) {
    SQLStatementParser parser = SQLParserUtils.createSQLStatementParser(sql, dbType, keepComments);
    List<SQLStatement> stmtList = parser.parseStatementList();
    ...
    return stmtList.get(0);
}

public static SQLStatementParser createSQLStatementParser(String sql, DbType dbType, boolean keepComments) {
    SQLParserFeature[] features;
    ...
    return createSQLStatementParser(sql, dbType, features);
}

public static SQLStatementParser createSQLStatementParser(String sql, DbType dbType, SQLParserFeature... features) {
    ...
    switch (dbType) {
        ...
        case mysql: {
            return new MySqlStatementParser(sql, features);
        }
        ...
        default:
            return new SQLStatementParser(sql, dbType);
    }
}
```

## 3. 解析 Create 语句信息

下面通过一个简单的小需求来了解一下如何通过 Druid SQL Parser 来实现简单解析 Create 语句。我们的需求是将 Create 语句中的字段信息转换为一个 Markdown 表格。例如如下 Create 语句：
```sql
CREATE TABLE ads_app_pub_user_group_label_distd_1d (
    dt VARCHAR(20) COMMENT '日期',
    user_group VARCHAR(100) COMMENT '人群类型',
    label_name VARCHAR(100) COMMENT '标签名称',
    label_value VARCHAR(100) COMMENT '标签值',
    uv BIGINT COMMENT '用户量',
    PRIMARY KEY (dt, user_group, label_name, label_value),
    INDEX idx(dt, user_group, label_name)
) ENGINE= InnoDB DEFAULT CHARSET= utf8 COMMENT ='人群标签分布';
```
转换为 Markdown 表格效果应该如下所示：
```
| 序号 | 标签字段 | 标签类型 | 标签说明 |
| -------- | -------- | -------- | -------- |
|1|dt|VARCHAR(20)|日期|
|2|user_group|VARCHAR(100)|人群类型|
|3|label_name|VARCHAR(100)|标签名称|
|4|label_value|VARCHAR(100)|标签值|
|5|uv|BIGINT|用户量|
```

下面详细看一下是如何转换的。第一步是获取解析器(在这直接使用 `MySqlCreateTableParser` 创建解析器)；第二步通过解析器的 `parseCreateTable` 方法解析 SQL 生成抽象语法树；第三步遍历抽象语法树中列字段转换为 Markdown 表格：
```java
public static String createSqlToMarkdown(String sql) {
    // 解析器
    MySqlCreateTableParser parser = new MySqlCreateTableParser(sql);
    // 生成抽象语法树
    MySqlCreateTableStatement createTableStatement = (MySqlCreateTableStatement) parser.parseCreateTable();
    // 遍历字段生成 Markdown 表格
    List<SQLColumnDefinition> columnDefinitions = createTableStatement.getColumnDefinitions();
    int index = 1;
    StringBuilder result = new StringBuilder("| 序号 | 标签字段 | 标签类型 | 标签说明 |\n")
            .append("| -------- | -------- | -------- | -------- |\n");
    for (SQLColumnDefinition definition : columnDefinitions) {
        String columnName = definition.getColumnName();
        SQLExpr columnComment = definition.getComment();
        SQLDataType dataType = definition.getDataType();
        result.append("|").append(index)
                .append("|").append(columnName)
                .append("|").append(dataType)
                .append("|").append(StringUtils.replace(columnComment.toString(), "'", ""))
                .append("|")
                .append("\n");
        index++;
    }
    return result.toString();
}
```
