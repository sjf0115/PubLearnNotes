Hive支持通常的SQL JOIN语句，但是只支持等值连接。

### 1. Join语法

Hive支持如下语法：
```
join_table:
    table_reference JOIN table_factor [join_condition]
  | table_reference {LEFT|RIGHT|FULL} [OUTER] JOIN table_reference join_condition
  | table_reference LEFT SEMI JOIN table_reference join_condition
  | table_reference CROSS JOIN table_reference [join_condition] (as of Hive 0.10)

table_reference:
    table_factor
  | join_table

table_factor:
    tbl_name [alias]
  | table_subquery alias
  | ( table_references )

join_condition:
    ON equality_expression ( AND equality_expression )*

equality_expression:
    expression = expression
```
#### 1.1 隐式连接

从Hive 0.13.0版本开始支持隐式Join（参见HIVE-5558）。可以允许FROM子句可以连接以逗号分隔的Table列表，省略JOIN关键字。
```
SELECT *
FROM table1 t1, table2 t2, table3 t3
WHERE t1.id = t2.id AND t2.id = t3.id AND t1.zipcode = '02535';
```
#### 1.2 非限定列引用

在连接条件中支持非限定列引用，从Hive 0.13.0版本开始(参见HIVE-6393)。Hive尝试根据Join的输入来解析这些。如果一个非限定列引用解析指向多个表，Hive将它标记为一个模糊引用。
```
CREATE TABLE a (k1 string, v1 string);
CREATE TABLE b (k2 string, v2 string);
SELECT k1, v1, k2, v2
FROM a
JOIN b
ON k1 = k2;
```
#### 1.3 ON子句复杂表达式

从Hive 2.2.0版本开始，ON子句中支持复杂表达式。在此之前，Hive不支持不等于条件的连接条件。
特别地，连接条件的语法限制如下:
```
join_condition:
    ON equality_expression ( AND equality_expression )*

equality_expression:
    expression = expression
```

### 2. Example

#### 2.1 仅支持等值连接
下面两个语句都是有效连接：
```
SELECT a.* FROM a JOIN b ON (a.id = b.id)
SELECT a.* FROM a JOIN b ON (a.id = b.id AND a.department = b.department)
```
但是下面这个语句是不支持的：
```
SELECT a.*
FROM a
JOIN b
ON (a.id <> b.id)
```
**备注**
```
Hive 2.2.0 以后支持，待验证
```

#### 2.2 同一查询连接多个表
```
SELECT a.val, b.val, c.val
FROM a
JOIN b
ON (a.key = b.key1)
JOIN c
ON (c.key = b.key2)
```
#### 2.3 Map/Reducer个数

如果JOIN子句中的每个表都使用同一列进行连接，则多表连接只会生成一个Map/Reducer作业:
```
SELECT a.val, b.val, c.val
FROM a
JOIN b
ON (a.key = b.key1)
JOIN c
ON (c.key = b.key1)
```
上述语句会转换为一个Map/Reducer作业，因为两个JOIN子句中只使用了b表的key1列，a表的key列，c表的key列，相反：
```
SELECT a.val, b.val, c.val
FROM a
JOIN b
ON (a.key = b.key1)
JOIN c
ON (c.key = b.key2)
```
上述语句会转换为两个Map/Reducer作业，因为第一个Join子句使用了b表的key1列，而第二个Join子句使用了b表的key2列。第一个Map/Reducer作业中，表a与表b进行连接，生成的结果在第二个Map/Reducer作业中与表c进行连接。

**备注**

试想一下，如果自己使用Hadoop实现上述语句Join的功能，如何实现呢？三个表三份数据源，针对第一个语句，只需要在一个MapReduce程序中根据a表的key，b表的key1，c表的key在Map端聚合就行．而第二个语句需要完成两个MapReduce程序，第一个根据a表的key和b表的key1进行聚合，再根据生成的结果的key2和c表的key进行聚合．

#### 2.4 表连接顺序优化

在Join的每一个Map/Reducer阶段，Join连接顺序中的最后一个表通过流传输到Reducers，而JOIN前面连接的中间结果数据会缓存在Reducer的内存中（the last table in the sequence is streamed through the reducers where as the others are buffered.）．通过组织这些表，使得最大的表出现在序列的最后，缓存连接键特定值的行，这样，有助于减少reducer中需要的内存．Hive假定查询中最后一个表是最大表，在进行连接操作时，它会尝试将其他表缓存起来，然后扫描最后那个表进行计算。
```
SELECT a.val, b.val, c.val
FROM a
JOIN b
ON (a.key = b.key1)
JOIN c
ON (c.key = b.key1)
```
上面三个表在一个单独的Map/Reducer作业中实现连接。表a和b基于`a.key = b.key1`进行连接，得到的结果会缓存在Reducer的内存中。然后从c表检索每一行，与缓存在内存中的数据进行连接．（在与c进行连接时，从内存中读取Key（根据a.key=b.key1连接的中间结果的特定Key）来与表c的c.key进行连接）。

```
SELECT a.val, b.val, c.val
FROM a
JOIN b
ON (a.key = b.key1)
JOIN c
ON (c.key = b.key2)
```
上述语句在计算连接时会产生两个map/reduce作业。在第一个作业中表a和b进行连接，在Reducer中缓存a表的值，同时遍历b表的值进行连接。在第二个作业中，缓存第一个作业连接的中间结果，同时遍历c表的值进行连接。(The first of these joins a with b and buffers the values of a while streaming the values of b in the reducers. The second of one of these jobs buffers the results of the first join while streaming the values of c through the reducers.)

#### 2.5 STREAM TABLE
用户也可以不用将最大的表放置在查询语句的最后面的。这是因为Hive提供了一个"提示"机制来显示的告诉查询优化器哪张表是大表，使用方式如下:
```
SELECT /*+ STREAMTABLE(a) */ a.val, b.val, c.val
FROM a
JOIN b
ON (a.key = b.key1)
JOIN c
ON (c.key = b.key1)
```
上面三个表在一个单独的Map/Reducer作业中实现连接。表b和c进行连接，得到的结果缓存在Reducer的内存中。然后从a表检索每一行，与缓存在内存中的数据进行连接．如果省略了STREAMTABLE提示，Hive会在连接中流遍历最右边的表。

#### 2.6 OUTER JOIN
LEFT，RIGHT和FULL OUTER JOIN，是为没有匹配到数据的ON子句提供更多的控制。例如，如下查询：
```
SELECT a.val, b.val
FROM a LEFT OUTER JOIN b
ON (a.key=b.key)
```
上述语句将返回a表中的每一行数据。当存在一个b.key等于a.key时，输出`a.val,b.val`，当没有对应的b.key时，返回`a.val,NULLL`。没有相应的a.key的b的行将被删除。

语法`FROM a LEFT OUTER JOIN b`必须写在一行上，目的是让你了解它的工作原理:
```
在上述查询中，a是在b的左侧，因此a的所有行将保留；
FROM a RIGHT OUTER JOIN b 将保留b的所有行；
FROM a FULL OUTER JOIN b 将保留a的所有行和b的所有行。
OUTER JOIN语义应符合标准SQL规范。
```
#### 2.7 JOIN发生在WHERE语句之前

JOIN发生在WHERE语句之前，因此，如果要过滤JOIN的输出，则必须在WHERE子句中填写过滤条件，否则就在JOIN ON 子句中填写过滤条件。分区表中应该使用WHERE子句还是JOIN ON子句这一点还是比较容易产生疑惑的：
```
SELECT a.val, b.val
FROM a LEFT OUTER JOIN b
ON (a.key = b.key)
WHERE a.dt = '2009-07-07' AND b.dt = '2009-07-07'
```
上述语句表a与b进行连接，产生a.val和b.val的列表。可以在WHERE子句中引用JOIN输出中表a和b的其他列(reference other columns of a and b that are in the output of the join)，然后进行过滤。 但是，每当JOIN的一行找到一个b和b的键，b的所有列都将为NULL，包括ds列。 也就是说，您将过滤出没有有效b.key的所有连接输出行，因此您已经超出了您的LEFT OUTER要求。 换句话说，如果引用了WHERE子句中的b列，则连接的LEFT OUTER部分是无关紧要的。 相反，当OUTER JOINING时，使用以下语法：
```
SELECT a.val, b.val
FROM a LEFT OUTER JOIN b
ON (a.key = b.key AND b.dt = '2009-07-07' AND a.dt = '2009-07-07')
```
结果是连接的输出被预过滤，并且对于具有有效的a.key但没有匹配的b.key的行，你不会得到后置过滤的麻烦。 同样的逻辑适用于RIGHT和FULL连接。


INSERT OVERWRITE DIRECTORY 'tmp/data_group/test/entrance_click'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LINES TERMINATED BY '\n'
SELECT param['entrance'], param['gid'], param['vid'], param['clickTime'] FROM entrance_order WHERE dt = '20170816';

INSERT OVERWRITE DIRECTORY 'tmp/data_group/test/entrance_order'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LINES TERMINATED BY '\n'
SELECT param['entrance'], param['gid'], param['vid'], param['actionTime'] FROM entrance_order WHERE dt = '20170816';

CREATE EXTERNAL TABLE IF NOT EXISTS tmp_entrance_order (
  entrance string,
  gid string,
  vid string,
  actionTime string
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LINES TERMINATED BY '\n'
LOCATION '/user/wirelessdev/tmp/data_group/test/entrance_order';


#### 2.8 LEFT SEMI JOIN

左半开连接（LEFT SEMI JOIN）会返回左边表的记录，前提是其记录对于右边表满足ON 语句中的判定条件。对于常见的内连接（INNER JOIN）来说，这是一个特殊的，优化了的情况。大多数的SQL 方言会通过IN ... EXISTS 结构来处理这种情况，不过在Hive 0.13版本之前这种查询是不支持的。

从Hive 0.13开始，子查询中支持IN / NOT IN / EXISTS / NOT EXISTS运算符，因此大多数JOIN不必手动执行LEFT SEMI JOIN。

使用LEFT SEMI JOIN的限制是其记录对于右边表满足ON 语句中的判定条件，同时不能在WHERE或SELECT子句中引用右边表中的字段。

```
Hive 不支持右半连接（RIGHT SEMI JOIN）
```
SEMI JOIN 比通常的INNER JOIN 要高效，原因是，对于左边中一条指定的记录，在右边表中一旦找到匹配的记录，Hive就会停止扫描。

```

SELECT a.key, a.value
FROM a
WHERE a.key in
 (SELECT b.key
  FROM B);
```
可以用LEFT SEMI JOIN代替：
```
SELECT a.key, a.val
FROM a LEFT SEMI JOIN b ON (a.key = b.key)
```

#### 2.9 Map-SIDE JOIN

如果所有表中只有一张表是小表，那么可以在最大表通过mapper的时候将小表完全放到内存中。Hive可以在map端执行连接过程（成为map-side join），这是因为Hive可以和在内存中的小表进行逐一匹配，从而省略掉常规连接操作所需要的 reduce 过程。即使对于很小的数据集，这个优化也明显的要快于常规的连接操作。不仅减少了 reduce 过程，而且还可以同时减少 map 过程的步骤。

在Hive 0.7 版本之前，如果使用这个优化，需要在查询语句中添加一个标记来进行触发：
```
SELECT /*+ MAPJOIN(b) */ a.key, a.value
FROM a JOIN b ON a.key = b.key
```
备注：
```
Hive 对于右外连接（RIGHT OUTER JOIN）和全外连接（FULL OUTER JOIN）不支持Map-side JOIN优化
```

从Hive 0.7版本开始，就废弃了这种标记的方式，不过如果增加了这个标记同样还是有效的。如果不添加上这个标记，那么这时用户需要设置属性 **hive.auto.convert.JOIN** 的值为true，这样Hive 才会在必要的时候启动这个优化。默认情况下这个属性的值是false。
```
hive> set hive.auto.convert.JOIN = true
```
用户还可以配置能够是用这个优化的小表的大小。如下是这个属性的默认值（单位：字节）：
```
hive.mapjoin.smalltable.filesize=25000000
```
如果所有表中的数据是分桶的，那么对于大表，在特定的情况下同样可以使用这个优化。简单的说，表中的数据必须是按照 ON 语句中的键进行分桶的，而且其中一张表的分桶的个数是另一张表分桶个数的若干倍。当满足这些条件时，那么Hive可以在map阶段按照分桶数据进行连接。因此这种情况下，不需要先获取到表中所有内容，之后才去和另一张表中每个分桶进行匹配连接。

不过这个优化同样默认是没有开启的，需要配置参数**set hive.optimize.bucketmapjoin**为true才可以开启这个优化：
```
set hive.optimize.bucketmapjoin = true
```
如果所涉及的分桶表都具有相同的分桶数，而且数据是按照连接键或桶的键进行排序的，那么这时Hive可以执行一个更快的分类-合并连接（sort-merge JOIN）。同样的，这个优化需要设置如下属性才能开启：
```
set hive.input.format=org.apache.hadoop.hive.ql.io.BucketizedHiveInputFormat;
set hive.optimize.bucketmapjoin = true;
set hive.optimize.bucketmapjoin.sortedmerge = true;
```
