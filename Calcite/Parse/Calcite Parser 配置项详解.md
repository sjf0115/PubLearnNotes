


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
- `DOUBLE_QUOTE("\"")`：在双引号中引用标识符，并使用双引号转义双引号。例如 `"my ""id"""`。
- `DOUBLE_QUOTE_BACKSLASH("\"")`：在双引号中引用标识符，并使用反斜杠转义双引号。
- `SINGLE_QUOTE("`")`：在单引号中引用标识符，并使用单引号转义单引号。
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


### 2.4 Lex

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

- BIG_QUERY：
- ORACLE：
- MYSQL：
- MYSQL_ANSI：
- SQL_SERVER：
- JAVA：
