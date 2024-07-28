
## 1. 简介

Druid SQL Parser 是阿里巴巴开源的一款数据库连接池项目 Druid 的一个重要组成部分，主要用于解析 SQL 语句。Druid Parser 通过词法分析和语法分析技术将接收到的 SQL 文本分解成一系列的 Token，然后构建一个抽象语法树（AST）。这个过程有助于优化 SQL 查询性能，比如支持预编译、统计 SQL 信息、防止 SQL 注入等。Druid 内置使用 SQL Parser 来实现防御 SQL 注入（WallFilter）、合并统计没有参数化的 SQL(StatFilter 的 mergeSql)、SQL 格式化、分库分表等。

## 2. 使用场景

SQL Parser 的使用场景主要如下所示：
- MySql SQL 全量统计
- Hive/ODPS SQL 执行安全审计
- 分库分表 SQL 解析引擎
- 数据库引擎的 SQL Parser

## 3. 语法支持

Druid 的 SQL Parser 是目前支持各种数据语法最完备的 SQL Parser。目前对各种数据库的支持如下：

| 数据库 | DML | DDL |
| :------------- | :------------- | :------------- |
| odps  | 完全支持 | 完全支持 |
| mysql | 完全支持 | 完全支持 |
| postgresql | 完全支持 | 完全支持 |
| oracle | 支持大部分 | 支持大部分 |
| sql server | 支持常用的 | 支持常用的 DDL |
| db2 | 支持常用的 | 支持常用的 DDL |
| hive | 支持常用的 | 支持常用的 DDL |

> druid 还缺省支持 sql-92 标准的语法，所以也部分支持其他数据库的sql语法。

## 4. 代码结构

Druid SQL Parser 分为三个模块：
- Parser
- AST
- Visitor

### 4.1 parser

parser 用来将输入文本转换为 AST（抽象语法树），parser有包括两个部分，Parser 和 Lexer，其中 Lexer 实现词法分析，Parser 实现语法分析

### 4.2 AST

AST 是 Abstract Syntax Tree 的缩写，也就是抽象语法树。AST 是 parser 输出的结果。下面是获得抽象语法树的一个例子：
```java
final String dbType = JdbcConstants.MYSQL; // 可以是ORACLE、POSTGRESQL、SQLSERVER、ODPS等
String sql = "select * from t";
List<SQLStatement> stmtList = SQLUtils.parseStatements(sql, dbType);
```

### 4.3 Visitor

Visitor 是遍历 AST 的手段，是处理 AST 最方便的模式，Visitor 是一个接口，有缺省什么都没做的实现 VistorAdapter。我们可以实现不同的 Visitor 来满足不同的需求，Druid 内置提供了如下 Visitor:
- OutputVisitor 用来把 AST 输出为字符串
- WallVisitor 来分析 SQL 语意来防御 SQL 注入攻击
- ParameterizedOutputVisitor 用来合并未参数化的 SQL 进行统计
- EvalVisitor 用来对 SQL 表达式求值
- ExportParameterVisitor 用来提取 SQL 中的变量参数
- SchemaStatVisitor 用来统计 SQL 中使用的表、字段、过滤条件、排序表达式、分组表达式




...
