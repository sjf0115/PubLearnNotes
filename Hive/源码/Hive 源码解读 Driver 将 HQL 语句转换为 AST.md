
## 1. 前言-ANTLR

Hive 使用 ANTLR3 实现 HQL 的词法和语法解析。ANTLR 是一种语言识别的工具，可以用来构造领域语言。 这里不详细介绍 ANTLR，具体可以查阅 [ANTLR4 初识语法分析器生成工具 ANTLR](https://smartsi.blog.csdn.net/article/details/128500910)。在这只需要了解使用 ANTLR 构造特定的语言只需要编写一个语法文件，定义词法和语法规则即可。ANTLR 通过词法分析器 (Lexer)、语法分析器 (Parser) 以及树分析器 (Tree Parser)等实现了词法分析、语法分析、语义分析、中间代码生成的过程。

Hive 中语法规则的定义文件在 0.10 版本以前只有一个 `Hive.g` 文件，随着语法规则越来越复杂，由语法规则生成的 Java 解析类可能超过 Java 类文件的最大上限，因此 0.11 版本将 `Hive.g` 拆成了 5 个文件，词法规则 `HiveLexer.g` 和语法规则的 4 个文件 `SelectClauseParser.g`、`FromClauseParser.g`，`IdentifiersParser.g` 以及 `HiveParser.g`：
- `HiveLexer.g` 文件定义了 Hive 关键字以及组成词法符号的合法字符
- `SelectClauseParser.g` 文件定义 select 语句的语法规则
- `FromClauseParser.g` 文件定义 FROM 语句的语法规则
- `IdentifiersParser.g` 文件定义了函数、GROUP 等的语法规则
- `HiveParser.g` 定义语法规则文件，引入了其他语法规则文件

> 这几个文件均存放在 org.apache.hadoop.hive.ql.parse 目录下。

## 2. 入口

上面也说过 Hive 是使用 ANTLR3 来实现 HQL 的词法和语法解析，并最终转换为一棵语法树 ASTNode。我们通过 debug 模式一步一步的前进，可以发现 Hive 是通过调用 ParseUtils 中的 parse 方法来将 HQL 命令转换为语法树 ASTNode：
```java
ASTNode tree = ParseUtils.parse(command, ctx);
```
ParseUtils 实际上是一个解析工具类，实际是将 HQL 命令转换为语法树 ASTNode 的工作交给了 ParseDriver：
```java
public static ASTNode parse(String command, Context ctx) throws ParseException {
  return parse(command, ctx, null);
}
public static ASTNode parse(String command, Context ctx, String viewFullyQualifiedName) throws ParseException {
  ParseDriver pd = new ParseDriver();
  ASTNode tree = pd.parse(command, ctx, viewFullyQualifiedName);
  tree = findRootNonNullToken(tree);
  handleSetColRefs(tree);
  return tree;
}
```

## 3. 转换语法树

ParseDriver 再将 HQL 命令转换为语法树 ASTNode 的工作可以分为 4 步：
- 创建 ANTLRNoCaseStringStream
- 创建词法解析器 lexer
- 生成词法符号流 tokens
- 创建语法分析器 parser
- 转化为抽象语法树 tree

```java
public ASTNode parse(String command, Context ctx, String viewFullyQualifiedName) throws ParseException {
  // 词法解析器
  HiveLexerX lexer = new HiveLexerX(new ANTLRNoCaseStringStream(command));
  // 词法符号流
  TokenRewriteStream tokens = new TokenRewriteStream(lexer);
  ...
  // 语法分析器
  HiveParser parser = new HiveParser(tokens);
  parser.setTreeAdaptor(adaptor);
  ...
  // 转换为语法树
  HiveParser.statement_return r = parser.statement();
  ASTNode tree = (ASTNode) r.getTree();
  return tree;
}
```

首先创建 `ANTLRNoCaseStringStream`，继承了 ANTLR 内部类 `ANTLRStringStream`，主要用于从字符串中读取 HQL 命令：
```java
public class ANTLRNoCaseStringStream extends ANTLRStringStream {
    public ANTLRNoCaseStringStream(String input) {
      super(input);
    }

    @Override
    public int LA(int i) {
      int returnChar = super.LA(i);
      if (returnChar == CharStream.EOF) {
        return returnChar;
      } else if (returnChar == 0) {
        return returnChar;
      }
      return Character.toUpperCase((char) returnChar);
    }
  }
```
Hive 使用自定义类 `ANTLRNoCaseStringStream`，而不是原始基类 `ANTLRStringStream` 的目的是在词法解析器使用其 LA 方法从流中查看字符时，将字符转换成大写字符，从而实现大小写不敏感的词法解析器。这样在 `.g` 语法文件定义的语法中，只要识别大写字母就可以了。

下一步是创建词法解析器 HiveLexerX，其继承了 ANTLR 自动生成的 `HiveLexer` 类：
```java
public class HiveLexerX extends HiveLexer {
  private final ArrayList<ParseError> errors;
  public HiveLexerX() {
    super();
    errors = new ArrayList<ParseError>();
  }

  public HiveLexerX(CharStream input) {
    super(input);
    errors = new ArrayList<ParseError>();
  }

  @Override
  public void displayRecognitionError(String[] tokenNames, RecognitionException e) {
    errors.add(new ParseError(this, e, tokenNames));
  }

  @Override
  public String getErrorMessage(RecognitionException e, String[] tokenNames) {
    String msg = null;
    if (e instanceof NoViableAltException) {
      @SuppressWarnings("unused")
      NoViableAltException nvae = (NoViableAltException) e;
      msg = "character " + getCharErrorDisplay(e.c) + " not supported here";
    } else {
      msg = super.getErrorMessage(e, tokenNames);
    }
    return msg;
  }

  public ArrayList<ParseError> getErrors() {
    return errors;
  }
}
```
Hive 使用 `HiveLexerX` 自定义词法解析器类的目的是显示、记录分析过程中的错误信息。有了词法分析器 lexer 通过 TokenRewriteStream 创建词法分析器与语法解析器之间的管道-词法符号流 tokens。接着使用 ANTLR 自动生成的 HiveParser 创建语法解析器。

正常情况下 ANTLR3 的语法解析器返回的是一个 CommonTree 对象。Hive 为了让语法解析器返回自定义的 ASTNode（而不是 CommonTree），需要为语法解析器设置 TreeAdapter：
```java
parser.setTreeAdaptor(adaptor);
```
TreeAdapter 实际上是 CommonTreeAdapter 对象，目的就是让语法解析器可以构建不同类型的节点。在 Hive 中重写了 CommonTreeAdaptor 类的 `create`、`errorNode`、`dupNode` 以及 `dupTree` 方法以返回 ASTNode：
```java
public static final TreeAdaptor adaptor = new CommonTreeAdaptor() {
    // 为 Toekn 创建 ASTNode
    @Override
    public Object create(Token payload) {
      return new ASTNode(payload);
    }

    @Override
    public Object dupNode(Object t) {
      return create(((CommonTree)t).token);
    };

    @Override
    public Object dupTree(Object t, Object parent) {
      ASTNode astNode = (ASTNode) t;
      ASTNode astNodeCopy = (ASTNode) super.dupTree(t, parent);
      astNodeCopy.setTokenStartIndex(astNode.getTokenStartIndex());
      astNodeCopy.setTokenStopIndex(astNode.getTokenStopIndex());
      return astNodeCopy;
    }

    @Override
    public Object errorNode(TokenStream input, Token start, Token stop, RecognitionException e) {
      return new ASTErrorNode(input, start, stop, e);
    };
};
```
ASTNode 是 Hive 自己定义的一个树节点对象，是对 ANTLR 的 CommonTree 类的一个包装，主要实现了 Node 和 Serializable 接口：
```java
public class ASTNode extends CommonTree implements Node,Serializable {
    ...
}
```
Hive 之所以要这样做，主要是可以实现 Node 接口，以便可以使用 Hive 自己的遍历框架对语法树进行遍历；此外还实现 Serializable 接口，以便可以将语法树序列化。

创建完语法解析器并设置 TreeAdapter 后，就可以进行真正的语法分析，并转换为 ASTNode。假设我们有如下 SQL：
```sql
SELECT COUNT(*) AS num FROM behavior WHERE uid LIKE 'a%';
```
有两种方式可以查看 ASTNode 具体长的什么样：一种方式是通过 debug 模式下的计算表达式(`tree.dump()`)查看语法树 ASTNode 的树形形式，另一种方式是直接调用 Hive 的 ParseDriver 解析器类获取：
```java
String command = "SELECT COUNT(*) AS num FROM behavior WHERE uid LIKE 'a%'";
ParseDriver pd = new ParseDriver();
ASTNode tree = pd.parse(command);
System.out.println(tree.dump());
```
经过词法分析器、语义解析器分析之后得到的语法树 ASTNode 打印之后树形形式如下所示：
```
nil
   TOK_QUERY
      TOK_FROM
         TOK_TABREF
            TOK_TABNAME
               behavior
      TOK_INSERT
         TOK_DESTINATION
            TOK_DIR
               TOK_TMP_FILE
         TOK_SELECT
            TOK_SELEXPR
               TOK_FUNCTIONSTAR
                  COUNT
               num
         TOK_WHERE
            LIKE
               TOK_TABLE_OR_COL
                  uid
               'a%'
   <EOF>
```
整个 `TOK_QUERY` 语法树根节点是 `nil`，下面跟着 SQL 语法树主体和结束标志符 `<EOF>`。`TOK_QUERY` 主要由 `TOK_FROM` 和 `TOK_INSERT` 两部分组成。`TOK_FROM` 代表了 FROM 子句的语法树；`TOK_INSERT` 则表示查询的主体部分，包含了查询结果目的数据源 `TOK_DESTINATION`（Hive 的查询数据会临时存在 HDFS 的临时文件中）、查询条件 `TOK_SELECT`、过滤条件 `TOK_WHERE` 等。详细对比 HQL 语句和语法树来看，解析过程对每个表生成一个 `TOK_TABREF` 节点，表名对应 `TOK_TABNAME` 节点；对查询的每个字段生成一个 `TOK_SELEXPR` 节点，每个使用到的属性列生成一个 `TOK_TABLE_OR_COL` 节点，其他节点类似可以一一对应到 HQL 语句上。
