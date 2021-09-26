
## 思路
理解MysSQL中索引是如何工作，最简单的方法就是去看看一本书的"索引"部分：如果现在一本书中找到我们想要看的某个特定主题，一般先会看书的"索引"，找到对应的页码。

在MysSQL中，存储引擎用类似的方法使用索引，其现在中找到对应值，然后根据匹配的索引记录找到对应的数据行。

## 样例

## 3.索引类型
索引有很多多种类型，可以为不同场景提供更好的性能。在MySQL中，索引是在存储引擎层而不是服务器层实现的。所以，不同的存储引擎的索引工作方式是不一样的，也不是所有的存储引擎都支持所有类型的索引。即使多个存储引擎支持同一种类型的索引，其底层的实现也可能不同。

### 3.1 B-Tree索引
我们一般说的索引就是B-Tree索引（如果没有特别指明类型时），它使用B-Tree数据结构来存储数据。大多数MySQL引擎都支持这种索引。不过，底层的存储引擎也可能使用不同的存储结构，例如，NDB集群存储引擎内部实际上使用了T-Tree结构存储这种索引；InnoDB则使用的是B+Tree。

存储引擎以不同的方式使用B-Tree索引，性能也各有不同，各有优劣。例如，MyISAM使用前缀压缩技术使得索引更小，但InnoDB则按照原数据格式进行存储。再如，MyISAM索引通过数据的物理位置引用被索引的行，而InnoDB则根据主键引用被索引行（思考：如果没有主键怎么办）。

B-Tree通常意味着所有的值都是按顺序存储的，并且每一个叶子页到根的距离相同。

![image](http://img.blog.csdn.net/20170209130952084?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

B-Tree索引能够加快访问数据的速度，因为存储引擎不再需要进行全表扫描来获取需要的数据，取而代之的是从索引的根节点开始进行搜索。根节点的槽中存放了指向子节点的指针，存储引擎根据这些指针向下层查找。通过比较节点页的值和要查找的值可以找到合适的指针进入下层子节点，这些指针实际上定义了子节点页中值的上限和下限。最终存储引擎要么找到对应的值，要么该记录不存在。

叶子节点比较特别，它们的指针指向的是被索引的数据，而不是其他的节点页（不同存储引擎的指针类型不同）。上图中仅绘制了一个节点和其对应的叶子节点，其实在根节点和叶子节点之间可能有很多层节点页。树的深度和表的大小直接相关。


B-Tree对索引列是顺序组织存储的，所以很适合查找范围数据。

假设有下面的数据表：
```
CREATE TABLE People (
   last_name varchar(50)    not null,
   first_name varchar(50)    not null,
   dob        date           not null,
   gender     enum('m', 'f') not null,
   key(last_name, first_name, dob)
);
```
对于表中的每一行数据，索引中包含了last_name，first_name 和 dob列的值，下图显示了该索引是如何组织数据的存储的：

![image](http://img.blog.csdn.net/20170209130809660?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

索引中对多个值进行排序的依据是CREATE TABLE语句中定义索引时列的顺序。看一下最后两个条目，两个人的姓和名都一样，则根据它们的出生日期来排列顺序。


### 3.2 哈希索引
哈细索引是基于哈希表实现的，只有精确匹配索引所有列的查询才有效。对于每一行数据，存储引擎都会对所有的索引列计算一个哈希码，哈希码是一个较小的值，并且不同键值的行计算出来的哈希码也不一样的。哈细索引将哈希码存储在索引中，同时在哈希表中保存指向每个数据行的指针。

MySQL中，只有Memory存储引擎显示支持哈希索引，是Memory引擎表的默认索引类型，Memory引擎表也支持B-Tree索引。Memory存储引擎支持非唯一哈希索引，如果多个列的哈希值相同，索引会以链表的方式存放多个记录指针到同一个哈希条目中。

```
CREATE TABLE PeopleHash (
   last_name VARCHAR(50) NOT NULL,
   first_name VARCHAR(50) NOT NULL,
   KEY USING HASH(last_name)
) ENGINE=MEMORY;
```
表中包含如下数据：
```
mysql> select * from PeopleHash limit 3;
+-----------+------------+
| last_name | first_name |
+-----------+------------+
| sEBJnE    | nfaJp      |
| fXvbmn    | inrVu      |
| ErSIWY    | TKENt      |
+-----------+------------+
3 rows in set (0.00 sec)
```
假设索引使用假想的哈希函数f()，它返回下面的值：
```
f('sEBJnE') = 8784
f('fXvbmn') = 2421
f('ErSIWY') = 9143
```
则哈希索引的数据结构如下：


槽  | 值
---|---
2421 | 指向第二行的指针
8784 | 指向第一行的指针
9143 | 指向第三行的指针

现在，拉看如下查询：
```
select * from PeopleHash where last_name = 'fXvbmn'
```
MySQL先计算'fXvbmn'的哈希值，并使用该值寻找对应的。因为f('fXvbmn') = 2421，所以MySQL在索引中查找2421，可以找到指向第二行的指针，最后一步是比较第二行的值是否是'fXvbmn'，以确保就是要查找的行。



### 3.3 空间数据索引（R-Tree）
MyISAM表支持空间索引，可以用作地理数据存储。

### 3.4 全文索引
全文索引是一种特殊类型的索引，它查找的是文本中的关键词，而不是直接比较索引中的值。

在MySQL中只有Memory引擎显示支持哈细索引（默认索引类型）。

## 4. 索引策略

### 4.1 独立的列
如果查询中的列不是独立的，则MySQL不会使用索引。

*备注*

独立的列是指索引列不能是表达式的一部分，也不能是函数的参数。


例如，下面两个查询都无法使用索引


```
mysql> EXPLAIN SELECT * from actor WHERE actor_id=4;
+----+-------------+-------+-------+---------------+---------+---------+-------+------+-------+
| id | select_type | table | type  | possible_keys | key     | key_len | ref   | rows | Extra |
+----+-------------+-------+-------+---------------+---------+---------+-------+------+-------+
|  1 | SIMPLE      | actor | const | PRIMARY       | PRIMARY | 2       | const |    1 | NULL  |
+----+-------------+-------+-------+---------------+---------+---------+-------+------+-------+
1 row in set (0.00 sec)

mysql> EXPLAIN SELECT * from actor WHERE actor_id + 1 =5;
+----+-------------+-------+------+---------------+------+---------+------+------+-------------+
| id | select_type | table | type | possible_keys | key  | key_len | ref  | rows | Extra       |
+----+-------------+-------+------+---------------+------+---------+------+------+-------------+
|  1 | SIMPLE      | actor | ALL  | NULL          | NULL | NULL    | NULL |  200 | Using where |
+----+-------------+-------+------+---------------+------+---------+------+------+-------------+
1 row in set (0.00 sec)
```
凭肉眼很容易看出WHERE中的表达式其实等价于actor_id = 4，但是MySQL无法自动解析这个方程式。我们应该养成简化WHERE条件的习惯，始终将索引列单独放在比较符号的一侧。

下面的这个查询也无法使用索引，因为索引列不能是函数的参数。
```
mysql> explain SELECT * from actor where last_name = 'HOPKINS';
+----+-------------+-------+------+---------------------+---------------------+---------+-------+------+-----------------------+
| id | select_type | table | type | possible_keys       | key                 | key_len | ref   | rows | Extra                 |
+----+-------------+-------+------+---------------------+---------------------+---------+-------+------+-----------------------+
|  1 | SIMPLE      | actor | ref  | idx_actor_last_name | idx_actor_last_name | 137     | const |    3 | Using index condition |
+----+-------------+-------+------+---------------------+---------------------+---------+-------+------+-----------------------+
1 row in set (0.00 sec)

mysql> explain SELECT * from actor where CONCAT(last_name,'Q') = 'QHOPKINS';
+----+-------------+-------+------+---------------+------+---------+------+------+-------------+
| id | select_type | table | type | possible_keys | key  | key_len | ref  | rows | Extra       |
+----+-------------+-------+------+---------------+------+---------+------+------+-------------+
|  1 | SIMPLE      | actor | ALL  | NULL          | NULL | NULL    | NULL |  200 | Using where |
+----+-------------+-------+------+---------------+------+---------+------+------+-------------+
1 row in set (0.00 sec)


```

### 4.2 前缀索引和索引选择性
#### 4.2.1 需求
有时候需要索引很长的字符列，这会让索引变得大且慢。
#### 4.2.2 解决方案
一个策略是前面提到的模拟哈希索引。但是有时候这样做还不够。通常可以索引开始的部分字符，这样可以大大节约索引空间，从而提高索引效率。但这样会降低索引的选择性。索引的选择性越高则查询效率越高，因为选择性高的索引可以让MySQL在查找时过滤更多的行。唯一索引的选择性是1，这是最好的索引选择性，性能也是最好的。

**备注**

索引选择性是指，不重复的索引值（也称基数） 和 数据表的记录总数（#T）的比值。取值范围在 1/#T 到 1 之间。

一般情况下某个列前缀的选择性也是足够高的，满足查询性能。对于BLOB，Text或者很长的VARCHAR类型的列，必须使用前缀索引，因为MySQL不允许索引这些列的完成长度。

诀窍在于要选择足够长的前缀以保证较高的选择性，同时又不能太长（以便节约空间）。前缀足够长，以使的前缀索引的选择性接近于索引整个列。换句话说，前缀的“基数”接近于完整列的“基数”。

我们找到最常见的城市列表：
```
mysql> select count(*) as num , city from city_demo group by city order by num desc limit 10;
+-----+----------------+
| num | city           |
+-----+----------------+
|  53 | London         |
|  48 | Bchar          |
|  48 | Satna          |
|  47 | Cuautla        |
|  46 | Tel Aviv-Jaffa |
|  46 | Kragujevac     |
|  46 | Soshanguve     |
|  46 | Benin City     |
|  45 | Ife            |
|  45 | Patras         |
+-----+----------------+
10 rows in set (0.02 sec)

```
上面每个值都出现了45-53。


计算合适的前缀长度的一个办法就是计算完整列的选择性，并使前缀选择性接近于整列的选择性。下面显示如何计算完整列的选择性：

```
mysql> select count(DISTINCT city)/count(*) as ratio FROM city_demo;
+--------+
| ratio  |
+--------+
| 0.0312 |
+--------+
1 row in set (0.01 sec)
```
通常来说，这个例子中如果前缀的选择性能够接近于0.031，基本上就可用了。可以在一个查询中针对不同前缀长度进行计算，这对于大表非常有用。下面给出了如何在一个查询中计算不同前缀长度的选择性：
```
mysql> select count(distinct left(city,3))/count(*) as ratio3,count(distinct left(city,4))/count(*) as ratio4,count(distinct left(city,5))/count(*) as ratio5,count(distinct left(city,6))/count(*) as ratio6,count(distinct left(city,7))/count(*) as ratio7,count(distinct left(city,8))/count(*) as ratio8 from city_demo;
+--------+--------+--------+--------+--------+--------+
| ratio3 | ratio4 | ratio5 | ratio6 | ratio7 | ratio8 |
+--------+--------+--------+--------+--------+--------+
| 0.0239 | 0.0293 | 0.0305 | 0.0309 | 0.0310 | 0.0310 |
+--------+--------+--------+--------+--------+--------+
1 row in set (0.04 sec)
```
查询显示当前缀长度达到7时，在增加前缀长度，选择性提升的幅度已经很小了。

只看平均选择性是不够的，也有例外的情况，需要考虑最坏情况下的选择性。平均选择性会让你认为前缀长度为4或者5时的索引已经足够了，但如果数据分布很不均匀，可能就会有陷阱。如果观察前缀为5的最常出现城市的次数，可以看到分布明显不均匀：
```
mysql> select count(*) as num , left(city, 5) as pref from city_demo group by pref order by num desc limit 5;
+-----+-------+
| num | pref  |
+-----+-------+
| 134 | South |
|  87 | Santa |
|  74 | San F |
|  69 | Toulo |
|  67 | Valle |
+-----+-------+
5 rows in set (0.02 sec)

mysql> select count(*) as num , left(city, 7) as pref from city_demo group by pref order by num desc limit 5;
+-----+---------+
| num | pref    |
+-----+---------+
|  74 | San Fel |
|  67 | Valle d |
|  62 | Santiag |
|  53 | London  |
|  48 | Satna   |
+-----+---------+
5 rows in set (0.02 sec)

```

如果前缀为5,则最常出现的前缀的次数比最常出现的城市次数要大的多。即这些值的选择性比平均选择性要低。如果在真实的城市名上键一个长度为4的前缀索引，对于以"San"和"New"开头的城市的选择性就会非常槽糕，因为很多城市都以这两个词开头。

下面演示一下如何创建前缀索引：
```
ALTER TABLE city_demo ADD INDEX idx_city (city(7));
```
观察一下效果：
```
mysql> explain select * from city_demo where city = 'London';
+----+-------------+-----------+------+---------------+------+---------+------+-------+-------------+
| id | select_type | table     | type | possible_keys | key  | key_len | ref  | rows  | Extra       |
+----+-------------+-----------+------+---------------+------+---------+------+-------+-------------+
|  1 | SIMPLE      | city_demo | ALL  | NULL          | NULL | NULL    | NULL | 19243 | Using where |
+----+-------------+-----------+------+---------------+------+---------+------+-------+-------------+
1 row in set (0.00 sec)

mysql> alter table city_demo add key(city(7));
Query OK, 0 rows affected (0.11 sec)
Records: 0  Duplicates: 0  Warnings: 0

mysql> explain select * from city_demo where city = 'London';
+----+-------------+-----------+------+---------------+------+---------+-------+------+-------------+
| id | select_type | table     | type | possible_keys | key  | key_len | ref   | rows | Extra       |
+----+-------------+-----------+------+---------------+------+---------+-------+------+-------------+
|  1 | SIMPLE      | city_demo | ref  | city          | city | 23      | const |   53 | Using where |
+----+-------------+-----------+------+---------------+------+---------+-------+------+-------------+
1 row in set (0.00 sec)

```

前缀索引是一种能使索引，更快的有效办法，但另一方面也有其缺点：MySQL无法使用前缀索引做ORDER BY 和 GROUP BY，也无法使用

一个常见的场景是针对很长的十六进制唯一ID使用前缀索引。



### 4.3 多列索引

多列索引中一个常见的错误就是，为每个列创建独立的索引，或者按照错误的顺序创建多列索引。
这样一来最好情况下也只能是“一星”索引，其性能比真正优秀的索引可能差几个数量级。有时如果无法设计一个“三星”索引，那么不如忽略掉WHERE子句，集中精力优化索引列的顺序，或者创建一个覆盖的索引。

在多个列上建立独立的单列索引大部分情况下并不能提高MySQL的查询性能。MySQL5.0 和 更新版本引入了一种叫“索引合并”策略，一定程度上可以使用表上的多个单列索引来定位指定的行。更早版本的MySQL只能使用其中某一单列索引，然而种情况下没有哪一个独立的索引是非常有效的。


```
mysql> explain select film_id , actor_id from film_actor where actor_id = 1 or film_id = 1;
+----+-------------+------------+-------------+------------------------+------------------------+---------+------+------+--------------------------------------------------+
| id | select_type | table      | type        | possible_keys          | key                    | key_len | ref  | rows | Extra                                            |
+----+-------------+------------+-------------+------------------------+------------------------+---------+------+------+--------------------------------------------------+
|  1 | SIMPLE      | film_actor | index_merge | PRIMARY,idx_fk_film_id | PRIMARY,idx_fk_film_id | 2,2     | NULL |   29 | Using union(PRIMARY,idx_fk_film_id); Using where |
+----+-------------+------------+-------------+------------------------+------------------------+---------+------+------+--------------------------------------------------+
1 row in set (0.00 sec)

```
在老的MySQL版本中，MySQL对这个查询会使用全表扫描，但在MySQL5.0和更新版本中，查询能够同时使用这两个单列索引进行扫描，并将结果合并。这种算法有三个变种：OR条件的联合（union），AND条件的相交，组合前两种情况的联合以及相交。


### 4.4 选择合适的索引列顺序
正确的顺序依赖于使用该索引的查询，并且同时需要考虑如何更好的满足排序和分组的需求。

在一个多列B-Tree索引中，索引列的顺序意味着索引首先按照最左列进行排序，其次是第二列，等等。所以，索引可以按照升序或者降序进行扫描，以满足精确符合列顺序的ORDER BY,GROUP BY 和 DISTINCT等子句的查询需求。 

如何选择索引的列顺序的一个经验法则：将选择性最高的列放到索引最前列。这个建议在某些场景下可能有帮助，但通常不如避免随机IO和排序那么重要。当不需要考虑排序和分组时，将选择性最高的列放在前面通常是很好的。这时候索引的作用只是用于优化WHERE条件的查找。在这种情况下，这样设计的索引确实能够最快的过滤出需要的行，对于在WHERE子句中只使用了索引部分前缀列的查询来说选择性也更高。然而，性能不只是依赖于所有索引列的选择性（整体基数），也和查询条件的具体值有关，也就是和值的分布有关。可能需要根据那些运行频率最高的查询来调整索引列的顺序，让这种情况下索引的选择性最高。

以下面的查询为例：
```
select * from paryment where staff_id = 2 and customer_id = 584;
```
是应该创建一个(staff_id, customer_id)索引还是应该颠倒一下顺序？可以跑一些查询来确定哪个列的选择性更高：
```
select count(distinct staff_id)/count(*) as staff_ratio, count(distinct customer_id)/count(*) as customer_ratio from payment

staff_ratio : 0.0001
customer_ratio : 0.0373
```
根据前面的经验法则，应该将索引列customer_id放到前面，因为customer_id选择性更高。
```
alter table payment add index idx_customer_staff(customer_id, staff_id);
```
### 4.5 最左前缀原理

```
 CREATE TABLE `People` (
  `last_name` varchar(50) NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `dob` date NOT NULL,
  `gender` enum('m','f') NOT NULL,
  KEY `idx_last_first_dob` (`last_name`,`first_name`,`dob`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8
```
这里提供了一个多列索引 idx_last_first_dob(last_name, first_name, dob)

#### 4.5.1 全值匹配
全值匹配指得是和索引中的所有列进行匹配，例如上面的索引可用于查找last_name为Cuba， first_name为Allen，出生于1996-01-01的人：
```
mysql> explain select * from People where last_name = 'Cuba' and first_name = 'Allen' and dob = '1996-01-01';
+----+-------------+--------+------+--------------------+--------------------+---------+-------------------+------+-----------------------+
| id | select_type | table  | type | possible_keys      | key                | key_len | ref               | rows | Extra                 |
+----+-------------+--------+------+--------------------+--------------------+---------+-------------------+------+-----------------------+
|  1 | SIMPLE      | People | ref  | idx_last_first_dob | idx_last_first_dob | 307     | const,const,const |    1 | Using index condition |
+----+-------------+--------+------+--------------------+--------------------+---------+-------------------+------+-----------------------+
1 row in set (0.01 sec)

```
这里有一点需要注意，理论上索引对顺序是敏感的，但是由于MySQL的查询优化器会自动调整where子句的条件顺序以使用适合的索引，例如我们将where中的条件顺序颠倒：
```
mysql> explain select * from People where first_name = 'Allen' and last_name = 'Cuba' and dob = '1996-01-01';
+----+-------------+--------+------+--------------------+--------------------+---------+-------------------+------+-----------------------+
| id | select_type | table  | type | possible_keys      | key                | key_len | ref               | rows | Extra                 |
+----+-------------+--------+------+--------------------+--------------------+---------+-------------------+------+-----------------------+
|  1 | SIMPLE      | People | ref  | idx_last_first_dob | idx_last_first_dob | 307     | const,const,const |    1 | Using index condition |
+----+-------------+--------+------+--------------------+--------------------+---------+-------------------+------+-----------------------+
1 row in set (0.00 sec)

```


#### 4.5.2 匹配最左前缀
当查询条件精确匹配索引的左边连续一个或几个列时，如<last_name>或<last_name, first_name>或者<last_name, first_name, dob>，索引可以被用到，但是只能用到一部分，即条件所组成的最左前缀。
例如，上面索引可用于查找所有姓为Allen的人，即只使用了索引的第一列：
```
mysql> explain select * from People where last_name = 'Cuba';
+----+-------------+--------+------+--------------------+--------------------+---------+-------+------+-----------------------+
| id | select_type | table  | type | possible_keys      | key                | key_len | ref   | rows | Extra                 |
+----+-------------+--------+------+--------------------+--------------------+---------+-------+------+-----------------------+
|  1 | SIMPLE      | People | ref  | idx_last_first_dob | idx_last_first_dob | 152     | const |    1 | Using index condition |
+----+-------------+--------+------+--------------------+--------------------+---------+-------+------+-----------------------+
1 row in set (0.00 sec)

```

#### 4.5.3 匹配列前缀

也可以只匹配某一列的值的开头部分。例如上面索引查找所有last_name为"Cuba"，first_name以J开头的人。这里也只使用了索引的第一列与第二列：
```
mysql> explain select * from People where last_name = 'Cuba' and first_name LIKE 'J%';
+----+-------------+--------+-------+--------------------+--------------------+---------+------+------+-----------------------+
| id | select_type | table  | type  | possible_keys      | key                | key_len | ref  | rows | Extra                 |
+----+-------------+--------+-------+--------------------+--------------------+---------+------+------+-----------------------+
|  1 | SIMPLE      | People | range | idx_last_first_dob | idx_last_first_dob | 304     | NULL |    1 | Using index condition |
+----+-------------+--------+-------+--------------------+--------------------+---------+------+------+-----------------------+
1 row in set (0.00 sec)

```

#### 4.5.4 匹配范围值
范围列可以用到索引，但是范围列后面的列无法用到索引。同时，索引最多用于一个范围列，因此如果查询条件中有两个范围列则无法全用到索引。
例如上面的索引可用于查找last_name在Allen 和 Barrymore 之间的人。 这里也只使用了索引的第一列:
```
mysql> explain select * from People where last_name < 'Barrymore' and last_name > 'Allen';
+----+-------------+--------+-------+--------------------+--------------------+---------+------+-------+-----------------------+
| id | select_type | table  | type  | possible_keys      | key                | key_len | ref  | rows  | Extra                 |
+----+-------------+--------+-------+--------------------+--------------------+---------+------+-------+-----------------------+
|  1 | SIMPLE      | People | range | idx_last_first_dob | idx_last_first_dob | 152     | NULL | 21609 | Using index condition |
+----+-------------+--------+-------+--------------------+--------------------+---------+------+-------+-----------------------+
1 row in set (0.00 sec)
```

```
mysql>  explain select * from People where first_name < 'Barrymore' and first_name > 'Allen';
+----+-------------+--------+------+---------------+------+---------+------+---------+-------------+
| id | select_type | table  | type | possible_keys | key  | key_len | ref  | rows    | Extra       |
+----+-------------+--------+------+---------------+------+---------+------+---------+-------------+
|  1 | SIMPLE      | People | ALL  | NULL          | NULL | NULL    | NULL | 1000019 | Using where |
+----+-------------+--------+------+---------------+------+---------+------+---------+-------------+
1 row in set (0.00 sec)

```
范围列可以用到索引，但必须满足最左前缀原则，否则索引无法使用。




#### 4.5.5 精确匹配某一列并范围匹配另一列
例如上面的索引可以用于查询所有姓为Allen，并且名字是字母k开头的人。即第一列last_name全匹配，第二列first_name范围匹配：
```
mysql> explain select * from People where last_name = 'Allen' and first_name like 'K%';
+----+-------------+--------+-------+--------------------+--------------------+---------+------+------+-----------------------+
| id | select_type | table  | type  | possible_keys      | key                | key_len | ref  | rows | Extra                 |
+----+-------------+--------+-------+--------------------+--------------------+---------+------+------+-----------------------+
|  1 | SIMPLE      | People | range | idx_last_first_dob | idx_last_first_dob | 304     | NULL |    1 | Using index condition |
+----+-------------+--------+-------+--------------------+--------------------+---------+------+------+-----------------------+
1 row in set (0.00 sec)

```

## 5 聚簇索引
聚簇索引并不是一种单独的索引类型，而是一种数据存储方式。具体的细节依赖于其实现方式。因为是存储引擎负责实现索引，因此不是所有的存储引擎都支持聚簇索引。目前，只有solidDB和InnoDB支持。

InnoDB的聚簇索引实际上在同一个结构种保存了B-Tree索引和数据行。

当表有聚簇索引时，它的数据行实际上存放在索引的叶子页中。术语"聚簇"表示数据行和相邻的键值紧凑的存储在一起。因为无法同时把数据行存放在两个不同的地方，所以一个表只能有一个聚簇索引。


下图展示了聚簇索引中的记录是如何存放的。注意到，叶子页包含了行的全数数据，但是节点页只包含了索引列（例子中，索引列包含的是整数值）。

![image](http://img.blog.csdn.net/20170209112959386?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)


### 6. InnoDB 和 MyISAM 的数据分布对比
聚簇索引和非聚簇索引的数据分布有区别，以及对应的主键索引和二级索引的数据分布也有区别。

来看看InnoDB 和 MyISAM 是如何存储下面这个表的：
```
create table layout_test(
    col1 int not null,
    col2 int not null,
    primary key (col1),
    key(col2)
);
```
假设该表的主键取值为1-10000，按照随机顺序插入并使用OPTIMIZE TABLE命令做了优化。列col2的值是从1-100之间的随机赋值，所以有很多重复的值。

#### 6.1 MyISAM 数据分布

MyISAM按照数据插入的顺序存储在磁盘中。如下图所示：

![image](http://images.cnblogs.com/cnblogs_com/hustcat/mysql/mysql02-05.JPG)

在行的旁边显示了行号，从0开始递增。因为行是定长的，所以MyISAM 可以从表的开头跳到所需要的行（并不总是使用图中的行号，而是根据定长还是变长的行使用不同策略）。

下面显示的一系列图，隐藏了的物理细节，只显示索引的"节点"，索引中的每个叶子节点包含"行号"。

MyISAM建立的primary key的索引结构如下：

![image](http://images.cnblogs.com/cnblogs_com/hustcat/mysql/mysql02-06.JPG)

来看看col2的索引结构：

![image](http://images.cnblogs.com/cnblogs_com/hustcat/mysql/mysql02-07.JPG)

 实际上，在MyISAM中，主键索引 和 其它索引没有什么区别。主键索引仅仅只是一个叫做PRIMARY的唯一，非空的索引而已，而其他索引可以重复。


#### 6.2 InnoDB 数据分布
因为InnoDB支持聚簇索引，所以使用不同的方式存储同样的数据。下图显示了InnoDB存储数据方式：

![image](http://images.cnblogs.com/cnblogs_com/hustcat/mysql/mysql02-08.JPG)

仔细看，会注意到该图显示了整个表，而不是只有索引。因为在InnoDB中，聚簇索引"就是"表，所以不想MyISAM那样需要独立的行存储。

聚簇索引的每一个叶子节点都包含了主键值，事务ID，用于事务和MVCC的回滚指针以及所有的剩余列。如果主键是一个列前缀索引，InnoDB也会包含完整的主键列和剩下的其他列。

相对于MyISAM，InnoDB的二级索引与聚簇索引有很大的不同。InnoDB的二级索引的叶子节点中存储的不是"行指针"，而是主键值，并以此作为指向行的"指针"。这样的策略减小了当出现行移动或者数据页分裂时二级索引的维护工作。使用主键值当做指针会让二级索引占用更多的空间（主键不会重复，col2可能会重复），换来的好处是，InnoDB 在移动时无须更新二级索引中的这个"指针"。

下图显示了col2索引。每一个叶子节点都包含了索引列（col2），紧接着是主键值（col1）：

![image](http://images.cnblogs.com/cnblogs_com/hustcat/mysql/mysql02-09.JPG)

下图描述了InnoDB 和 MyISAM 如何存放表的抽象图。可以很容易看出InnoDB 和 MyISAM保存数据和索引的区别：

![image](http://images.cnblogs.com/cnblogs_com/hustcat/mysql/mysql02-10.JPG)

### 7. 在InnoDB表中按主键顺序插入行

如果正在使用InnoDB表并且没有什么数据需要聚集，那么可以定义一个代理键作为主键，这种主键的数据应该和应用无关，最简单的方法是使用AUTO_INCREMENT 自增列。这样可以保证数据行是按顺序写入，对于根据主键做关联操作的性能也会更好。

最好避免随机的（不连续且值的分布范围非常大）聚簇索引，特别是对于IO密集型的应用。例如，从性能的角度考虑，使用UUID来作为聚簇索引则会很糟糕：它使得聚簇索引的插入变得完全随机，这是最坏的情况。

为了演示这一点，做两个基准测试。第一个整数ID插入userInfo表，第二个使用UUID插入userinfo_uuid。

注意到UUID主键插入行不仅花费时间更长，而且索引占用的空间也更大。这一方面是由于主键字段更长；另一方面是由于页分裂和碎片导致的。

下图显示了插满一个页面后继续插入相邻的下一个页面的场景：

![image](http://img.blog.csdn.net/20170209132502902?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

因为主键值的是顺序的，所以InnoDB把每一条记录都存储在上一条记录的后面。当到达页的最大填充因子时（InnoDB默认的最大填充因子是页大小的15/16，留出部分空间用于以后修改），下一条记录就会写入新的页中。一旦数据按照这种顺序的方式加载，主键页就会近似于被顺序的记录的填满。

对比与第二个使用UUID聚簇索引的表插入数据，看看有什么不同，下图显示了结果：

![image](http://img.blog.csdn.net/20170209132350025?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

因为新行的主键值不一定比之前插入的大，所以InnoDB 无法简单的总是把新行插入到索引的最后，而是需要为新的行寻找合适的位置，通常是已有数据的中间位置（并且分配空间）。这回增加很多额外的工作，并导致数据分布不够优化。


缺点：

- 写入的目标页可能已经刷新到磁盘上并从缓存中移除，或者是还没有被加载到缓存中，InnoDB在插入之前不得不先找到并从磁盘读取目标页到内存中。这将导致大量的随机IO。
- 因为写入的是乱序的，InnoDB 不得不频繁的做页分裂操作，以便为新的行分配空间。页分裂会导致移动大量数据，一次插入最少需要修改三个页而不是一个页。
- 由于频繁的页分裂，页会变的稀疏并被不规则的填充，所以最终数据会有碎片。

### 数据表结构

#### actor
```
CREATE TABLE actor (
  actor_id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
  first_name VARCHAR(45) NOT NULL,
  last_name VARCHAR(45) NOT NULL,
  last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY  (actor_id),
  KEY idx_actor_last_name (last_name)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;
```


```
create table city_demo(city varchar(50) not null);

insert into city_demo(city) select city from city;


```

