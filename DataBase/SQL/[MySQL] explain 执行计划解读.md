### 1. 概述
如果在select语句前放上关键词explain，mysql将解释它如何处理select，提供有关表如何联接和联接的次序。

### 2. 语法
```
explain <sql>
```

### 3. 样例
```
mysql> explain select * from stu where id = 1;
+----+-------------+-------+-------+---------------+---------+---------+-------+------+-------+
| id | select_type | table | type  | possible_keys | key     | key_len | ref   | rows | Extra |
+----+-------------+-------+-------+---------------+---------+---------+-------+------+-------+
|  1 | SIMPLE      | stu   | const | PRIMARY       | PRIMARY | 4       | const |    1 | NULL  |
+----+-------------+-------+-------+---------------+---------+---------+-------+------+-------+
1 row in set (0.00 sec)

```

### 4. EXPLAIN 输出列

#### 4.1 id
select 的标识符。在查询中每个 select都有一个顺序的数值。
```
mysql> explain select * from (select * from stu where id = 1) a;
+----+-------------+------------+--------+---------------+---------+---------+-------+------+-------+
| id | select_type | table      | type   | possible_keys | key     | key_len | ref   | rows | Extra |
+----+-------------+------------+--------+---------------+---------+---------+-------+------+-------+
|  1 | PRIMARY     | <derived2> | system | NULL          | NULL    | NULL    | NULL  |    1 | NULL  |
|  2 | DERIVED     | stu        | const  | PRIMARY       | PRIMARY | 4       | const |    1 | NULL  |
+----+-------------+------------+--------+---------------+---------+---------+-------+------+-------+
2 rows in set (0.00 sec)

```
#### 4.2 select_type
就是select类型,可以有以下几种：
##### 4.2.1 SIMPLE
简单SELECT查询(不使用UNION或子查询等) 例如:

```
mysql> explain select * from stu where id = 1;
+----+-------------+-------+-------+---------------+---------+---------+-------+------+-------+
| id | select_type | table | type  | possible_keys | key     | key_len | ref   | rows | Extra |
+----+-------------+-------+-------+---------------+---------+---------+-------+------+-------+
|  1 | SIMPLE      | stu   | const | PRIMARY       | PRIMARY | 4       | const |    1 | NULL  |
+----+-------------+-------+-------+---------------+---------+---------+-------+------+-------+
1 row in set (0.00 sec)
```
##### 4.2.2 PRIMARY
最外层的 select：
```
mysql> explain select * from (select * from stu where id = 1) a;
+----+-------------+------------+--------+---------------+---------+---------+-------+------+-------+
| id | select_type | table      | type   | possible_keys | key     | key_len | ref   | rows | Extra |
+----+-------------+------------+--------+---------------+---------+---------+-------+------+-------+
|  1 | PRIMARY     | <derived2> | system | NULL          | NULL    | NULL    | NULL  |    1 | NULL  |
|  2 | DERIVED     | stu        | const  | PRIMARY       | PRIMARY | 4       | const |    1 | NULL  |
+----+-------------+------------+--------+---------------+---------+---------+-------+------+-------+
2 rows in set (0.00 sec)
```
##### 4.2.3 DERIVED
派生表的SELECT(FROM子句的子查询)：
```
mysql> explain select * from (select * from stu where id = 1) a;
+----+-------------+------------+--------+---------------+---------+---------+-------+------+-------+
| id | select_type | table      | type   | possible_keys | key     | key_len | ref   | rows | Extra |
+----+-------------+------------+--------+---------------+---------+---------+-------+------+-------+
|  1 | PRIMARY     | <derived2> | system | NULL          | NULL    | NULL    | NULL  |    1 | NULL  |
|  2 | DERIVED     | stu        | const  | PRIMARY       | PRIMARY | 4       | const |    1 | NULL  |
+----+-------------+------------+--------+---------------+---------+---------+-------+------+-------+
2 rows in set (0.00 sec)
```

##### 4.2.4 UNION和UNION RESULT
UNION是指UNION语句中第二个或后面的SELECT语句；UNION RESULT指union的结果；
```
mysql> explain select * from stu union select * from stu2;
+----+--------------+------------+------+---------------+------+---------+------+------+-----------------+
| id | select_type  | table      | type | possible_keys | key  | key_len | ref  | rows | Extra           |
+----+--------------+------------+------+---------------+------+---------+------+------+-----------------+
|  1 | PRIMARY      | stu        | ALL  | NULL          | NULL | NULL    | NULL |    4 | NULL            |
|  2 | UNION        | stu2       | ALL  | NULL          | NULL | NULL    | NULL |    1 | NULL            |
| NULL | UNION RESULT | <union1,2> | ALL  | NULL          | NULL | NULL    | NULL | NULL | Using temporary |
+----+--------------+------------+------+---------------+------+---------+------+------+-----------------+
3 rows in set (0.00 sec)

```
##### 4.2.5 SUBQUERY
子查询中的第一个SELECT：

```
mysql> explain select * from book where author_id = (select author_id from author where id = 1);
+----+-------------+--------+-------+---------------+---------+---------+-------+------+-------------+
| id | select_type | table  | type  | possible_keys | key     | key_len | ref   | rows | Extra       |
+----+-------------+--------+-------+---------------+---------+---------+-------+------+-------------+
|  1 | PRIMARY     | book   | ALL   | NULL          | NULL    | NULL    | NULL  |   12 | Using where |
|  2 | SUBQUERY    | author | const | PRIMARY       | PRIMARY | 4       | const |    1 | NULL        |
+----+-------------+--------+-------+---------------+---------+---------+-------+------+-------------+
2 rows in set (0.00 sec)

```

### 4.3 table 

记录查询引用的表，有时不是真实的表名字,看到的是derivedX(X是一个数字):
```
mysql> explain select * from (select * from stu where id = 1) a;
+----+-------------+------------+--------+---------------+---------+---------+-------+------+-------+
| id | select_type | table      | type   | possible_keys | key     | key_len | ref   | rows | Extra |
+----+-------------+------------+--------+---------------+---------+---------+-------+------+-------+
|  1 | PRIMARY     | <derived2> | system | NULL          | NULL    | NULL    | NULL  |    1 | NULL  |
|  2 | DERIVED     | stu        | const  | PRIMARY       | PRIMARY | 4       | const |    1 | NULL  |
+----+-------------+------------+--------+---------------+---------+---------+-------+------+-------+
2 rows in set (0.00 sec)
```

### 4.4 type
表连接类型。以下列出了各种不同类型的表连接，依次是从最好的到最差的:
#### 4.4.1 system(待思考)
表只有一行记录（等于系统表）。这是 const表连接类型的一个特例。
```
mysql> select * from student;
+----+----------+-----+-----+-------------+-------------+
| id | stu_name | age | sex | sex_default | sex_ordinal |
+----+----------+-----+-----+-------------+-------------+
|  1 | yoona    |  24 |   1 |           1 |           1 |
+----+----------+-----+-----+-------------+-------------+
1 row in set (0.01 sec)

mysql> explain select * from student;
+----+-------------+---------+------+---------------+------+---------+------+------+-------+
| id | select_type | table   | type | possible_keys | key  | key_len | ref  | rows | Extra |
+----+-------------+---------+------+---------------+------+---------+------+------+-------+
|  1 | SIMPLE      | student | ALL  | NULL          | NULL | NULL    | NULL |    1 | NULL  |
+----+-------------+---------+------+---------------+------+---------+------+------+-------+
1 row in set (0.00 sec)

```
#### 4.4.2 const
该表最多只有一个匹配的行，在查询一开始的时候就会被读取出来。因为只有一行，所以该行中的列的值可以被其他优化器视为常量。 const表非常快，因为它们只读一次。

当将PRIMARY KEY或UNIQUE索引的所有列与常量值进行比较时，将使用到const。

下面例子中id主键，student_id为唯一索引列：
```
mysql> explain select * from Student where id = '1861';
+----+-------------+---------+-------+---------------+---------+---------+-------+------+-------+
| id | select_type | table   | type  | possible_keys | key     | key_len | ref   | rows | Extra |
+----+-------------+---------+-------+---------------+---------+---------+-------+------+-------+
|  1 | SIMPLE      | Student | const | PRIMARY       | PRIMARY | 4       | const |    1 | NULL  |
+----+-------------+---------+-------+---------------+---------+---------+-------+------+-------+
1 row in set (0.00 sec)

mysql> explain select * from Student where student_id = 'Q99878';
+----+-------------+---------+-------+-------------------+---------------+---------+-------+------+-------+
| id | select_type | table   | type  | possible_keys     | key           | key_len | ref   | rows | Extra |
+----+-------------+---------+-------+-------------------+---------------+---------+-------+------+-------+
|  1 | SIMPLE      | Student | const | unique_stu_id,idx | unique_stu_id | 26      | const |    1 | NULL  |
+----+-------------+---------+-------+-------------------+---------------+---------+-------+------+-------+
1 row in set (0.00 sec)
```


#### 4.4.3 eq_ref
从该表中会有一行记录被读取出来以和从前一个表中读取出来的记录做联合。与const类型不同的是，这是最好的连接类型。它用在索引所有部分都用于做连接并且这个索引是一个primary key 或 unique 类型。






### 4.5 possible_keys

possible_keys字段是指 mysql在搜索表记录时可能会使用到索引（可能建立多个索引）。注意，这个字段完全独立于explain 显示的表顺序（this column is totally independent of the order of the tables as displayed in the output from EXPLAIN）。这就意味着 possible_keys里面所包含的索引可能在实际的使用中没用到。

如果possible_keys为NULL（或在JSON格式的输出中未定义），则意味着没有建立相关索引。 在这种情况下，通过检查WHERE子句来判断哪些字段适合增加索引，从而提高查询的性能（examining the WHERE clause to check whether it refers to some column or columns that would be suitable for indexing）。如果是这样，请创建一个适当的索引并再次使用EXPLAIN检查查询。

### 4.6 key
key指示MySQL实际决定使用的键（索引）。 如果MySQL决定使用possible_keys索引中某一个来查找行，那么该索引将被作为key的值（实际使用到的索引）。

```
mysql> explain select * from People where last_name = 'Cuba';
+----+-------------+--------+------+--------------------------------------------+----------------+---------+-------+------+-----------------------+
| id | select_type | table  | type | possible_keys                              | key            | key_len | ref   | rows | Extra                 |
+----+-------------+--------+------+--------------------------------------------+----------------+---------+-------+------+-----------------------+
|  1 | SIMPLE      | People | ref  | idx_last_first,idx_last,idx_last_first_dob | idx_last_first | 152     | const |    1 | Using index condition |
+----+-------------+--------+------+--------------------------------------------+----------------+---------+-------+------+-----------------------+
1 row in set (0.00 sec)

```
例如上面语句表提供了三个索引，但是只使用到其中的idx_last_first索引，所以key值为idx_last_first（实际使用到的索引。

key字段可能会出现一个不存在于possible_keys值中的索引名称。如果possible_keys中没有适合的索引查找行，但是查询选择的所有列都是其他索引的列，就会发生这种情况（This can happen if none of the possible_keys indexes are suitable for looking up rows, but all the columns selected by the query are columns of some other index）。

对于InnoDB来说，即使查询中选择了主键列，辅助索引还是可能覆盖所选列，因为InnoDB会将主键值与每个辅助索引一起存储（For InnoDB, a secondary index might cover the selected columns even if the query also selects the primary key because InnoDB stores the primary key value with each secondary index）。 如果key为NULL，表明MySQL认为没有索引可以使查询执行更有效。

要强制MySQL使用或忽略在possible_keys列中的索引，可以在查询中使用FORCE INDEX，USE INDEX，IGNORE INDEX。
```
mysql> explain select * from People where last_name = 'UkTSB';
+----+-------------+--------+------+--------------------------------------------+----------+---------+-------+------+-----------------------+
| id | select_type | table  | type | possible_keys                              | key      | key_len | ref   | rows | Extra                 |
+----+-------------+--------+------+--------------------------------------------+----------+---------+-------+------+-----------------------+
|  1 | SIMPLE      | People | ref  | idx_last_first,idx_last,idx_last_first_dob | idx_last | 152     | const |    1 | Using index condition |
+----+-------------+--------+------+--------------------------------------------+----------+---------+-------+------+-----------------------+
1 row in set (0.00 sec)

mysql> explain select * from People use index (idx_last_first_dob) where last_name = 'UkTSB';
+----+-------------+--------+------+--------------------+--------------------+---------+-------+------+-----------------------+
| id | select_type | table  | type | possible_keys      | key                | key_len | ref   | rows | Extra                 |
+----+-------------+--------+------+--------------------+--------------------+---------+-------+------+-----------------------+
|  1 | SIMPLE      | People | ref  | idx_last_first_dob | idx_last_first_dob | 152     | const |    1 | Using index condition |
+----+-------------+--------+------+--------------------+--------------------+---------+-------+------+-----------------------+
1 row in set (0.00 sec)

mysql> explain select * from People ignore index (idx_last_first_dob) where last_name = 'UkTSB';
+----+-------------+--------+------+-------------------------+----------+---------+-------+------+-----------------------+
| id | select_type | table  | type | possible_keys           | key      | key_len | ref   | rows | Extra                 |
+----+-------------+--------+------+-------------------------+----------+---------+-------+------+-----------------------+
|  1 | SIMPLE      | People | ref  | idx_last_first,idx_last | idx_last | 152     | const |    1 | Using index condition |
+----+-------------+--------+------+-------------------------+----------+---------+-------+------+-----------------------+
1 row in set (0.00 sec)

```

对于MyISAM表，运行ANALYZE TABLE有助于优化器选择更好的索引。 对于MyISAM表，myisamchk --analyze 命令也可以。

### 4.7 key_len
key_len列表明MySQL实际使用索引的长度。 key_len的值可以告诉你在联合索引中mysql真正使用了哪些索引列。 如果key列显示NULL，key_len列也显示NULL。

### 4.8 ref

ref列显示将哪些列或常量与key列中的索引进行比较，以从表中选择行。


### 4.9 rows
rows列表示MySQL认为必须检查多少行以执行查询。

对于InnoDB表，此数字是一个估计值，可能不总是准确的。


### 4.10 extra

此列包含有关MySQL如何解析查询的其他信息。 有关不同值的说明，请参阅EXPLAIN Extra 信息。




