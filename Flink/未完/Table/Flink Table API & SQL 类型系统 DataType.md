

由于历史原因，在 Flink 1.9 之前，Flink 的 Table API & SQL 数据类型与 Flink 的 TypeInformation 紧密耦合。TypeInformation 主要用于 DataStream 和 DataSet API 中，为系统序列化和反序列化基于 JVM 的对象提供必要的信息。

但是，TypeInformation 原本的设计目的并不能表示不同实际 JVM 类的逻辑类型。因此 SQL 的标准类型很难与这种抽象进行映射。此外，某些类型也不符合 SQL 标准。从 Flink 1.9 开始，Table API & SQL 将获得一个新的类型系统。

重新设计类型系统是一项涉及几乎所有面向用户接口的重大工作。因此，它的引入会跨越多个版本，社区目标在 Flink 1.10 完成这项工作。

由于同时为表 Tbale 程序添加了新的 Planner（参见 FLINK-11439），因此并非支持 Planner 和数据类型的所有组合。此外，Planner 可能不支持具有所需精度或参数的每种数据类型。

## 1. 数据类型

Table API & SQL 中新的数据类型描述表生态系统中值的逻辑类型。它可以用来声明操作的输入和/或输出类型。

Flink 的数据类型与 SQL 标准的数据类型比较相似，同时也支持 NULL/NOT NULL，例如如下所示：
- INT
- INT NOT NULL
- INTERVAL DAY TO SECOND(3)
- ROW<myField ARRAY<BOOLEAN>, myOtherField TIMESTAMP(3)>

### 1.1 Data Types in the Table API

使用基于 JVM API 的用户在编写 Table API 或者在定义 Connector、Catalogs 或者自定义函数中，需要使用 org.apache.flink.table.types.DataType 数据类型的实例。

DataType 实例有两个职责：
- 逻辑类型的声明：并不意味着传输或存储的具体物理表示，但是定义了基于 JVM 的语言和表生态系统之间的边界。
- 物理表示的提示：向 Planner 提供有关数据物理表示的提示。

对于基于 JVM 的语言，所有预定义的数据类型都在 org.apache.flink.table.api.DataTypes 下。

#### 1.1.1 物理提示

在基于 SQL 的类型系统结束并且需要特定于编程的数据类型的表生态系统的边缘需要物理提示。 提示指示实现所期望的数据格式。

例如，数据源可以表示它使用 java.sql.Timestamp 类而不是使用默认的 java.time.LocalDateTime 为逻辑 TIMESTAMP 生成值。 使用此信息，运行时能够将生成的类转换为其内部数据格式。 作为回报，数据接收器可以声明它从运行时使用的数据格式。

以下是一些如何声明桥接转换类的示例：
```java
// tell the runtime to not produce or consume java.time.LocalDateTime instances
// but java.sql.Timestamp
DataType t = DataTypes.TIMESTAMP(3).bridgedTo(java.sql.Timestamp.class);

// tell the runtime to not produce or consume boxed integer arrays
// but primitive int arrays
DataType t = DataTypes.ARRAY(DataTypes.INT().notNull()).bridgedTo(int[].class);
```

## 2. Planner 兼容性

正如介绍中提到的，重做类型系统将跨越多个版本，每种数据类型的支持取决于使用的 Planner。

### 2.1 Old Planner

Flink 的 Old Planner 在 Flink 1.9 版本之前就引入了，主要支持 TypeInformation，对数据类型的支持有限。我们可以声明一个可以转换为类型信息的数据类型，这样以便 Old Planner 能够理解。

下表总结了数据类型和类型信息之间的区别。大多数简单类型以及行类型保持不变。时间类型、数组类型和十进制类型需要特别注意。

| Type Information | 	Java Expression String | Data Type Representation | 备注 |
| :------------- | :------------- | :------------- | :------------- |
| STRING()       | STRING         | STRING()       | |
| BOOLEAN()      | BOOLEAN        | BOOLEAN()      | |
| BYTE()         | BYTE           | TINYINT()      | |
| SHORT()        | SHORT          | SMALLINT()     | |
| INT()          | INT            | INT()          | |
| LONG()         | LONG           | BIGINT()	     | |
| FLOAT()        | FLOAT          | FLOAT()	       | |
| DOUBLE()       | DOUBLE         | DOUBLE()       | |
| ROW(...)       | ROW<...>       | ROW(...)       | |
| BIG_DEC()      | DECIMAL        | [DECIMAL()]    | 不是 1:1 映射，因为精度和比例被忽略，而 Java 的可变精度和比例被使用。|
| SQL_DATE()     | SQL_DATE       | DATE().bridgedTo(java.sql.Date.class)  | |
| SQL_TIME()     | SQL_TIME       | TIME(0).bridgedTo(java.sql.Time.class) | |
| SQL_TIMESTAMP()| SQL_TIMESTAMP  | TIMESTAMP(3).bridgedTo(java.sql.Timestamp.class)  | |
| INTERVAL_MONTHS() | INTERVAL_MONTHS | INTERVAL(MONTH()).bridgedTo(Integer.class) | |
| INTERVAL_MILLIS() | INTERVAL_MILLIS | INTERVAL(DataTypes.SECOND(3)).bridgedTo(Long.class) | |
| PRIMITIVE_ARRAY(...) | PRIMITIVE_ARRAY<...> | ARRAY(DATATYPE.notNull().bridgedTo(PRIMITIVE.class)) | |
| PRIMITIVE_ARRAY(BYTE()) | PRIMITIVE_ARRAY<BYTE> | BYTES() | |
| OBJECT_ARRAY(...) | OBJECT_ARRAY<...> | ARRAY(DATATYPE.bridgedTo(OBJECT.class))	| |
| MULTISET(...) |   | MULTISET(...)	  | |
| MAP(..., ...) | MAP<...,...> | MAP(...)	 | |

> 对于 Type Information 列，该表省略了前缀 org.apache.flink.table.api.Types。
> 对于 Data Type Representation 列，该表省略了前缀 org.apache.flink.table.api.DataTypes。


### 2.2 New Blink Planner

| Data Type | 备注 |
| :------------- | :------------- |
|	CHAR	|		|
|	VARCHAR	|		|
|	STRING	|		|
|	BOOLEAN	|		|
|	BYTES	|	BINARY and VARBINARY are not supported yet.	|
|	DECIMAL	|	Supports fixed precision and scale.	|
|	TINYINT	|		|
|	SMALLINT	|		|
|	INTEGER	|		|
|	BIGINT	|		|
|	FLOAT	|		|
|	DOUBLE	|		|
|	DATE	|		|
|	TIME	|	Supports only a precision of 0.	|
|	TIMESTAMP	|		|
|	TIMESTAMP_LTZ	|		|
|	INTERVAL	|	Supports only interval of MONTH and SECOND(3).	|
|	ARRAY	|		|
|	MULTISET	|		|
|	MAP	|		|
|	ROW	|		|
|	RAW	|		|
|	structured types	|	Only exposed in user-defined functions yet.	|

## 3. Limitations

## 4. List of Data Types

下面我们详细看一下所有预定义的数据类型。

> 对于基于 JVM 的 Table API，这些类型也可以在 org.apache.flink.table.api.DataTypes 中使用。

### 4.1 Character Strings

(1) CHAR：具有固定长度字符串的数据类型
```sql
CHAR
CHAR(n)
```
其中 n 表示字符数量。n 的值必须在 [1, 2147483647] 之间。如果未指定长度，n 默认为 1。

(2) VARCHAR / STRING：可变长度字符串的数据类型
```sql
VARCHAR
VARCHAR(n)
STRING
```
其中 n 表示字符的最大数量。n 的值必须在 [1, 2147483647] 之间。如果未指定长度，n 默认为 1。STRING 等价于 VARCHAR(2147483647)。

### 4.2 Binary Strings

(1) BINARY：具有固定长度的二进制字符串数据类型（字节序列）
```sql
BINARY
BINARY(n)
```
其中 n 是字节数量。n 的值必须在 [1, 2147483647] 之间。如果未指定长度，n 默认为 1。

(2) VARBINARY / BYTES：可变长度的二进制字符串数据类型（字节序列）
```sql
VARBINARY
VARBINARY(n)
BYTES
```
其中 n 是字节的最大数量。n 的值必须在 [1, 2147483647] 之间。如果未指定长度，n 默认为 1。BYTES 等价于 VARBINARY(2147483647)。

### 4.3 Exact Numerics

(1) DECIMAL：具有固定精度和小数位数的十进制数数据类型
```sql
DECIMAL
DECIMAL(p)
DECIMAL(p, s)

DEC
DEC(p)
DEC(p, s)

NUMERIC
NUMERIC(p)
NUMERIC(p, s)
```
其中 p 是数字的位数（精度），s 是数字小数点右边的位数（尾数）。p 的值必须在 [1, 38] 之间。s 的值必须在 [0, p]。如果不指定 p，默认为是 10，同样 s 默认值为 0。

NUMERIC 和 DEC 都等价于这个类型。

(2) TINYINT：1 字节有符号整数的数据类型，取值范围 [-128, 127]：
```sql
TINYINT
```

(3) SMALLINT：2 字节有符号整数的数据类型，取值范围 [-32768, 32767]：
```sql
SMALLINT
```

(4) INT：4 字节有符号整数的数据类型，取值范围 [-2147483648, 2147483647]：
```sql
INT
INTEGER
```

INTEGER 与 INT 数据类型等价。

(5) BIGINT：8 字节有符号整数的数据类型，取值范围 [-9223372036854775808, 9223372036854775807]：
```sql
BIGINT
```

### 4.4 Approximate Numerics

(1) FLOAT：4 字节单精度浮点数的数据类型。与标准 SQL 相比，该类型不带参数：
```sql
FLOAT
```

(2) DOUBLE：8 字节双精度浮点数的数据类型：
```sql
DOUBLE

DOUBLE PRECISION
```
DOUBLE PRECISION 与 DOUBLE 等价。

### 4.4 Date and Time

#### 4.4.1 DATE

日期数据类型，格式为 '年-月-日'，取值范围 [0000-01-01, 9999-12-31]。与标准 SQL 相比，年的范围从 0000 开始：
```sql
DATE
```

#### 4.4.2 TIME

不带时区的时间数据类型，格式为 '小时:分钟:秒[.小数]'，精度可达纳秒，取值范围为 [00:00:00.000000000, 23:59:59.999999999]。与标准 SQL 相比，不支持闰秒（23:59:60 和 23:59:61），在语义上更接近于 java.time.LocalTime：
```sql
TIME
TIME(p)
```
其中 p 是秒的小数部分的位数（精度）。p 的值必须在 [0, 9] 之间。如果未指定精度，p 默认为 0。

#### 4.4.3 TIMESTAMP

不带时区的时间戳数据类型，格式为 '年-月-日 小时:分钟:秒[.小数]'，精度达到纳秒，取值范围为 [0000-01-01 00:00:00.000000000, 9999-12-31 23:59:59.999999999]。与标准 SQL 相比，不支持闰秒（23:59:60 和 23:59:61），语义上更接近于 java.time.LocalDateTime。此类型不支持和 BIGINT（JVM long 类型）互相转换，此类型是无时区的：
```sql
TIMESTAMP
TIMESTAMP(p)

TIMESTAMP WITHOUT TIME ZONE
TIMESTAMP(p) WITHOUT TIME ZONE
```
其中 p 是秒的小数部分的位数（精度）。p 的值必须在 [0, 9] 之间。如果未指定精度，p 默认为 6。TIMESTAMP(p) WITHOUT TIME ZONE 与 TIMESTAMP 等价。

#### 4.4.4 TIMESTAMP WITH TIME ZONE

带时区的时间戳数据类型，格式为 '年-月-日 小时:分钟:秒[.小数] 时区'，精度达到纳秒，取值范围为 [0000-01-01 00:00:00.000000000 +14:59, 9999-12-31 23:59:59.999999999 -14:59]。与 TIMESTAMP_LTZ 相比，时区偏移信息物理存储在每个数据中。
```sql
TIMESTAMP WITH TIME ZONE
TIMESTAMP(p) WITH TIME ZONE
```

#### 4.4.5 TIMESTAMP_LTZ

带本地时区的时间戳数据类型，'年-月-日 小时:分钟:秒[.小数] 时区'，精度可达纳秒，取值范围为 [0000-01-01 00:00:00.000000000 +14:59, 9999-12-31 23:59:59.999999999 -14:59]。与标准 SQL 相比，不支持闰秒（23:59:60 和 23:59:61），在语义上更接近于 java.time.OffsetDateTime。

与 TIMESTAMP WITH TIME ZONE 相比，时区偏移信息并非物理存储在每个数据中。相反，此类型在 Table 编程环境的 UTC 时区中采用 java.time.Instant 语义。每个数据都在当前会话中配置的本地时区中进行解释，以便用于计算和可视化。此类型允许根据配置的会话时区来解释 UTC 时间戳，可以区分时区无关和时区相关的时间戳类型。

```sql
TIMESTAMP_LTZ
TIMESTAMP_LTZ(p)

TIMESTAMP WITH LOCAL TIME ZONE
TIMESTAMP(p) WITH LOCAL TIME ZONE
```
其中 p 是秒的小数部分的位数（精度）。p 的值必须在 [0, 9] 之间。如果未指定精度，那么 p 默认为 6。TIMESTAMP(p) WITH LOCAL TIME ZONE 与 TIMESTAMP_LTZ(p) 等价。

#### 4.4.6 INTERVAL YEAR TO MONTH

一组由 Year-Month Interval 组成的数据类型，其范围从 -9999-11 到 +9999-11，可以表达：

```sql
INTERVAL YEAR
INTERVAL YEAR(p)
INTERVAL YEAR(p) TO MONTH
INTERVAL MONTH
```
其中 p 是年数（年精度）的位数。p 的值必须在 [1, 4] 之间。如果未指定年精度，p 默认等于 2。

#### 4.4.7 NTERVAL DAY TO SECOND

### 4.5 Constructured Data Types

### 4.6 User-Defined Data Types

### 4.7 Other Data Types



参考：https://mp.weixin.qq.com/s/aqDRWgr3Kim7lblx10JvtA









原文：[Data Types](https://ci.apache.org/projects/flink/flink-docs-release-1.9/dev/table/types.html)
