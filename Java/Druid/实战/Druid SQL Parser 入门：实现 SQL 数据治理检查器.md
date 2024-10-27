在数据仓库中我们维护了大量的开发任务，但是随着业务的发展、数据处理逻辑的更迭，以及人员变动等原因，这些开发任务越来越复杂以及越来越难维护。由于不同时期、不同开发同学的开发规范不同会给任务带来一定的风险隐患。这时候就需要通过数据治理来规避其中的风险。可以是事后治理，即通过离线任务筛选出不符合规范的任务，也可以是事前治理，即在任务上线前进行检查操作。无论是事前还是事后都需要一种检查器帮助用户发现问题。

针对数据研发，我们提供了不同的数据治理检查器，下面提供几个示例。

## 1. 禁止使用 SLECT * 检查器

如果任务中存在 SELECT * 用法，未指定查询字段会增加计算资源的消耗。因此这个检查器的用途就是判断任务是否存在 SELECT * 用法。初看这个需求觉得非常简单，首先想到的就是使用正则表达式进行匹配。但是使用正则表达式需要考虑很多特殊情况，实际做下来并没有想象中的那么简单，例如如下 SQL：
```sql
SELECT user_name
FROM user
WHERE user_id = '1' AND desc LIKE '%select *%';
```
上述示例在使用正则表达式匹配时需要考虑单双引号中的 `SLECT *`，这样处理起来就麻烦了。

因此在这我们选择使用 Druid SQL Parser 来将 SQL 解析生成对应的抽象语法树：

![](1)

通过上面的抽象语法树可以看到判断 SQL 是否是 `SELECT *` 只需要判断抽象语法树中是否有 `SQLAllColumnExpr` 表达式即可：

![](2)

先试想一下如果我们想查询一个 SQL 中是否有 `SQLAllColumnExpr` 表达式，我们需要查询所有子查询下的全部字段(因为可能会有嵌套查询、JOIN 查询等)，这就需要我们实现递归遍历一层一层的查询字段。幸运的是，Druid SQL Parser 为我们能提供了不同的 Visitor 实现，只需要继承并在 visit 方法中实现我们自己的逻辑即可快速实现我们想要的遍历：
```java
// 质量规则1：禁止使用 SELECT *
public class SelectAllQualityRuleVisitor extends HiveSchemaStatVisitor {
    // 是否是 SELECT *
    private boolean isSelectAll = false;
    @Override
    public boolean visit(SQLAllColumnExpr expr) {
        // 是否有 SELECT *
        isSelectAll = true;
        return false;
    }
}
```
上面我们实现了一个 `禁止使用 SELECT *` 检查器规则的 Visitor，下面只需要使用 Visitor 解析抽象语法树即可判断 SQL 中是否使用到了 `SELECT *`：
```java
public void parseQualityRule(String sql) {
    // 解析
    HiveStatementParser parser = new HiveStatementParser(sql);
    SQLStatement statement = parser.parseStatement();

    // 规则1：禁止使用 SELECT *
    SelectAllQualityRuleVisitor selectAllVisitor = new SelectAllQualityRuleVisitor();
    statement.accept(selectAllVisitor);
    if (selectAllVisitor.isSelectAll) {
        System.out.println("触发【规则】禁止使用 SELECT *");
    } else {
        System.out.println("未触发【规则】禁止使用 SELECT *");
    }
}
```
这样我们就完成了一个 `禁止使用 SELECT *` 检查器规则，下面来验证一下：
```java
@Test
public void testSelectAll() {
    // 触发【规则】禁止使用 SELECT *
    String sql = "SELECT * FROM user WHERE user_id = '1' AND desc LIKE '%select *%'";
    parseQualityRule(sql);
}

@Test
public void testSelectName() {
    // 未触发【规则】禁止使用 SELECT *
    String sql = "SELECT user_name FROM user WHERE user_id = '1' AND desc LIKE '%select *%'";
    parseQualityRule(sql);
}
```

## 2. 禁止使用 INSERT INTO SELECT 检查器

如果 SQL 任务中存在仅包含使用 INSERT INTO SELECT 往目标表写入数据，当任务重跑时会造成数据重复写入的正确性问题。因此这个检查器的用途就是判断任务是否存在 INSERT INTO SELECT 用法。例如如下 SQL：
```sql
INSERT INTO result_table
SELECT * FROM source_table;
```
跟第一个规则一样在这我们选择使用 Druid SQL Parser 来将 SQL 解析生成对应的抽象语法树：

![](3)

通过上面的抽象语法树可以看到判断 SQL 是否是 `INSERT INTO SELECT` 需要判断抽象语法树中是否有 `SQLSelect` 查询以及 `HiveInsertStatement` 中的 `overwrite` 属性是否为 false：

![](4)

通过第一个规则可以知道只需要继承 `HiveSchemaStatVisitor` 并在 visit 方法中实现判断逻辑：
```java
// 质量规则2：禁止使用 INSERT INTO SELECT
public class InsertIntoSelectQualityRuleVisitor extends HiveSchemaStatVisitor {
    // 是否是 INSERT INTO SELECT
    private boolean isInsertIntoSelect = false;

    @Override
    public boolean visit(HiveInsertStatement insertStatement) {
        boolean overwrite = insertStatement.isOverwrite();
        SQLSelect query = insertStatement.getQuery();
        if (!overwrite && !Objects.equals(query, null)) {
            isInsertIntoSelect = true;
        }
        return false;
    }
}
```
上面我们实现了一个 `禁止使用 INSERT INTO SELECT` 检查器规则的 Visitor，下面只需要使用 Visitor 解析抽象语法树即可判断 SQL 中是否使用到了 `INSERT INTO SELECT` 语法：
```java
// 解析
HiveStatementParser parser = new HiveStatementParser(sql);
SQLStatement statement = parser.parseStatement();
// 访问者模式遍历抽象语法树

// 规则2：禁止使用 SELECT *
InsertIntoSelectQualityRuleVisitor insertIntoVisitor = new InsertIntoSelectQualityRuleVisitor();
statement.accept(insertIntoVisitor);
if (insertIntoVisitor.isInsertIntoSelect) {
    System.out.println("触发【规则】禁止使用 INSERT INTO SELECT");
} else {
    System.out.println("未触发【规则】禁止使用 INSERT INTO SELECT");
}
```
这样我们就完成了一个 `禁止使用 INSERT INTO SELECT` 检查器规则，下面来验证一下：
```java
@Test
public void testInsertSelect() {
    // 触发【规则】禁止使用 INSERT INTO SELECT
    String sql = "INSERT INTO result_table SELECT * FROM source_table";
    parseQualityRule(sql);
}

@Test
public void testInsertValues() {
    // 未触发【规则】禁止使用 INSERT INTO SELECT
    String sql = "INSERT INTO Websites (name, country) VALUES ('百度', 'CN')";
    parseQualityRule(sql);
}

@Test
public void testInsertOverwrite() {
    // 未触发【规则】禁止使用 INSERT INTO SELECT
    String sql = "INSERT OVERWRITE Websites (name, country) VALUES ('百度', 'CN')";
    parseQualityRule(sql);
}
```
## 3. 禁止使用简单查询检查器





。。。
