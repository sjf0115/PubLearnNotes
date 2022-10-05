
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
