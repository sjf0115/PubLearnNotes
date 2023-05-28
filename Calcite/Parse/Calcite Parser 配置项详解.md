


## 1. 解析

Calcite 针对 SQL 的解析提供了很多的配置项，可以针对不同的 SQL 方言进行解析。相关的配置项都存储在SqlParser.Config这个结构中，常见的用法如下所示：
```java
// 1. 配置
SqlParser.Config config = SqlParser.config();

// 2. 解析器
String sql = "SELECT id, name FROM t_user WHERE id > 10";
SqlParser sqlParser = SqlParser.create(sql, config);

// 3. 解析
SqlNode sqlNode = sqlParser.parseStmt();
System.out.println(sqlNode);
```
根据上面代码我们可以将一个字符串的 SQL 解析为一个 SqlNode 对象。而这个 `config()` 就是 Calcite 默认提供的一个配置集合，如下所示：
```

```

## 2. 配置项

### 2.1 Quoting 引用标识符

指定了 SQL 语句如何引用标识符：
```java
public enum Quoting {
  DOUBLE_QUOTE("\""),
  DOUBLE_QUOTE_BACKSLASH("\""),
  SINGLE_QUOTE("`"),
  SINGLE_QUOTE_BACKSLASH("`"),
  BACK_TICK("`"),
  BACK_TICK_BACKSLASH("`"),
  BRACKET("[");

  public String string;
  Quoting(String string) {
    this.string = string;
  }
}
```
Quoting 为我们提供了如下几种选择：
- `DOUBLE_QUOTE("\"")`：使用双引号引用标识符，并使用双引号转义双引号。
  ```sql
  -- 双引号引用标识符
  SELECT "id", "name" FROM "t_user" WHERE "id" > 10;
  -- 常量 双引号转义双引号
  SELECT "I am a ""SQL Boy""";
  ```
- `DOUBLE_QUOTE_BACKSLASH("\"")`：使用双引号引用标识符，并使用反斜杠转义双引号。
  ```sql
  -- 常量
  SELECT "I am a \"SQL Boy\"";
  ```
- `SINGLE_QUOTE("`")`：使用单引号引用标识符，并使用单引号转义单引号。
  ```sql
  -- 常量
  SELECT 'I am a ''SQL Boy''';
  ```
- `SINGLE_QUOTE_BACKSLASH("`")`：在单引号中引用标识符，并使用反斜杠转义单引号。
- `BACK_TICK("`")`：用反引号引用标识符，并使用反引号转义反引号。
- `BACK_TICK_BACKSLASH("`")`：在反引号中引用标识符，并使用反斜杠转义反引号。
- `BRACKET("[")`：在括号中引用标识符。例如，`[my id]`。





## 2.2 Casing 标识符大小写转换

```java
public enum Casing {
  UNCHANGED,
  TO_UPPER,
  TO_LOWER
}
```
使用 Casing 可以设置标识符是否进行大小写转换，可以通过 `SqlParser.Config` 的两个方法可以进行设置，如下所示：
```java
// 对使用了引用标识符包围的列、表名等，进行大小写转换
Config withQuotedCasing(Casing casing);
// 对没有引用标识符包围的列、表名等，进行大小写转换
Config withUnquotedCasing(Casing casing);
```

## 2.3 CharLiteralStyle 字符常量值样式

```java
public enum CharLiteralStyle {
  STANDARD,
  BQ_SINGLE,
  BQ_DOUBLE
}
```
字符常量值样式可以如下几种形式：
- `STANDARD`：标准字符字面量。用单引号括起来，用单引号转义。
- `BQ_SINGLE`：用单引号括起来，并使用反斜杠进行转义。只在 BigQuery 方言中使用。
- `BQ_DOUBLE`：用双引号括起来，并使用反斜杠进行转义。只在 BigQuery 方言中使用。

而 BQ_SINGLE 和 BQ_DOUBLE 分别表示使用单引号和双引号来包围字符串，转义符号用的则是反斜杠，这两种格式是 BigQuery 的语法。


### 2.4 Lex 词法策略

Calcite 针对当前主流的方言内置了一些词法策略。词法策略描述了如何引用标识符、读取时是否转换为大小写，以及是否匹配区分大小写：
- BIG_QUERY：
  - 词法策略类似于 BigQuery
  - 不会改变标识符的大小写(无论它们是否被引用)
  - 在匹配标识符时不区分大小写
  - 反引号允许标识符可以包含非字母数字字符，使用反斜杠转义反引号
  - 字符字面量可以用单引号或双引号括起来
- ORACLE：
  - 词法策略类似于 Oracle
  - 如果使用双引号引用标识符，那么不会改变标识符的大小写
  - 未加引号的标识符被转换为大写
  - 匹配标识符时区分大小写
- MYSQL：
  - 词法策略类似于 MySQL。准确地说 Windows 和 Linux 上的 MySQL 匹配标识符区分大小写
  - 不会改变标识符的大小写(无论它们是否被引用)
  - 在匹配标识符时不区分大小写
  - 反引号允许标识符可以包含非字母数字字符，使用反引号转义反引号
- MYSQL_ANSI：
  - 词法策略类似于启用了ANSI_QUOTES选项的MySQL
  - 标识符的大小写被保留，无论它们是否被引用;
  - 不区分大小写地匹配标识符
  - 双引号允许标识符包含非字母数字字符。
- SQL_SERVER：
  - 词法策略类似于 Microsoft SQL Server
  - 不会改变标识符的大小写(无论它们是否被引用)
  - 在匹配标识符时不区分大小写
  - 括号 `[]` 允许标识符包含非字母数字字符
- JAVA：
  - 词法策略类似于 Java
  - 不会改变标识符的大小写(无论它们是否被引用)
  - 大小写敏感：在匹配标识符时区分大小写
  - 与 Java 不同，反引号允许标识符包含非字母数字字符，使用反引号转义反引号


```java
public enum Lex {
  BIG_QUERY(Quoting.BACK_TICK_BACKSLASH, Casing.UNCHANGED, Casing.UNCHANGED,
      false, CharLiteralStyle.BQ_SINGLE, CharLiteralStyle.BQ_DOUBLE),
  ORACLE(Quoting.DOUBLE_QUOTE, Casing.TO_UPPER, Casing.UNCHANGED, true,
      CharLiteralStyle.STANDARD),
  MYSQL(Quoting.BACK_TICK, Casing.UNCHANGED, Casing.UNCHANGED, false,
      CharLiteralStyle.STANDARD),
  MYSQL_ANSI(Quoting.DOUBLE_QUOTE, Casing.UNCHANGED, Casing.UNCHANGED, false,
      CharLiteralStyle.STANDARD),
  SQL_SERVER(Quoting.BRACKET, Casing.UNCHANGED, Casing.UNCHANGED, false,
      CharLiteralStyle.STANDARD),
  JAVA(Quoting.BACK_TICK, Casing.UNCHANGED, Casing.UNCHANGED, true,
      CharLiteralStyle.STANDARD);

  public final Quoting quoting;
  public final Casing unquotedCasing;
  public final Casing quotedCasing;
  public final boolean caseSensitive;
  @SuppressWarnings("ImmutableEnumChecker")
  public final Set<CharLiteralStyle> charLiteralStyles;

  Lex(Quoting quoting,
      Casing unquotedCasing,
      Casing quotedCasing,
      boolean caseSensitive,
      CharLiteralStyle... charLiteralStyles) {
    this.quoting = Objects.requireNonNull(quoting, "quoting");
    this.unquotedCasing = Objects.requireNonNull(unquotedCasing, "unquotedCasing");
    this.quotedCasing = Objects.requireNonNull(quotedCasing, "quotedCasing");
    this.caseSensitive = caseSensitive;
    this.charLiteralStyles = ImmutableSet.copyOf(charLiteralStyles);
  }
}
```


### 2.5 SqlConformance

除了上面提到的 Lex，还有一个与之搭配使用的变量就是 SqlConformanceEnum：
```java
public enum SqlConformanceEnum implements SqlConformance {
    DEFAULT,
    LENIENT,
    BABEL,
    STRICT_92,
    STRICT_99,
    PRAGMATIC_99,
    BIG_QUERY,
    MYSQL_5,
    ORACLE_10,
    ORACLE_12,
    STRICT_2003,
    PRAGMATIC_2003,
    SQL_SERVER_2008;
}
```
这个枚举里面定义了一系列的 SQL 行为模式，例如是否支持 Group By Alias 等，如下所示：
```java
public boolean isGroupByAlias() {
    switch(this) {
    case BABEL:
    case LENIENT:
    case BIG_QUERY:
    case MYSQL_5:
        return true;
    default:
        return false;
    }
}
```



https://cloud.tencent.com/developer/article/2169871
