

我们有一份Orders数据和一份Persons数据，如下表格所示:

Persons:

Id |LastName |FirstName |Address |City
---|---|---|---|---
1 |Adams |John |Oxford Street |London
2 |Bush |George |Fifth Avenue |New York
3 |Carter |Thomas |Changan Street |Beijing
```sql
CREATE EXTERNAL TABLE IF NOT EXISTS Persons (
  id string,
  lastName string,
  firstName string,
  address string,
  city string
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LINES TERMINATED BY '\n'
LOCATION '/user/xiaosi/tmp/data_group/example/input/persons';
```
Orders:

Id|OrderNo |PersonId
---|---|---
1 |77895 |3
2 |44678 |3
3 |22456 |1
4 |24562 |1
5 |34764 |65

```sql
CREATE EXTERNAL TABLE IF NOT EXISTS Orders (
  id string,
  orderNo string,
  personId string
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LINES TERMINATED BY '\n'
LOCATION '/user/xiaosi/tmp/data_group/example/input/orders';
```

### 1. 不同的JOIN

(1) JOIN是最简单的关联操作，两边关联只取交集。

(2) OUTER JOIN 分为LEFT OUTER JOIN、RIGHT OUTER JOIN和FULL OUTER JOIN。LEFT OUTER JOIN是以左表驱动，右表不存在的key均赋值为NULL；RIGHT OUTER JOIN是以右表驱动，左表不存在的key均赋值为NULL；FULL OUTER JOIN全表关联，将两表完整的进行笛卡尔积操作，左右表均可赋值为NULL。

(3) SEMI JOIN 最主要的使用场景就是解决EXIST IN。Hive不支持where子句中的子查询，SQL常用的exist in子句在Hive中是不支持的。

### 2. JOIN

如果我们希望列出所有人的定购，可以使用下面的 SELECT 语句：　
```sql
SELECT Persons.Id, Persons.LastName, Persons.FirstName, Persons.Address, Persons.City, Orders.Id, Orders.OrderNo
FROM Persons
JOIN Orders
ON Persons.Id = Orders.PersonId;
```

输出结果:

PersonId|LastName|FirstName|Address|City|OrderId|OrderNo
---|---|---|---|---|---|---
1 |Adams |John |Oxford Street |London |3 |22456
1	|Adams |John |Oxford Street |London |4 |24562
3 |Carter |Thomas |Changan Street |Beijing |1 |77895
3 |Carter |Thomas |Changan Street |Beijing |2 |44678

### 2. LEFT OUTER JOIN

LEFT OUTER JOIN 关键字会从左边数据那里返回所有的行，即使在右边数据中没有匹配的行。右表不存在的均赋值为NULL。

现在，我们希望列出所有的人，以及他们的定购 - 如果有的话，可以使用下面的 SELECT 语句：
```sql
SELECT Persons.Id, Persons.LastName, Persons.FirstName, Persons.Address, Persons.City, Orders.Id, Orders.OrderNo
FROM Persons
LEFT OUTER JOIN Orders
ON Persons.Id = Orders.PersonId;
```

输出结果:

PersonId|LastName|FirstName|Address|City|OrderId|OrderNo
---|---|---|---|---|---|---
1 |Adams |John |Oxford Street |London |4 |24562
1 |Adams |John |Oxford Street |London |3 |22456
2 |Bush |George |Fifth Avenue |New York |	NULL|NULL
3 |Carter |Thomas |Changan Street |Beijing |1 |77895
3 |Carter |Thomas |Changan Street |Beijing |2 |44678

### 3. RIGHT OUTER JOIN

RIGHT OUTER JOIN 关键字会从右边数据那里返回所有的行，即使在左边数据中没有匹配的行。左表不存在的均赋值为NULL。

现在，我们希望列出所有的定单，以及定购它们的人 - 如果有的话，可以使用下面的 SELECT 语句：
```sql
SELECT Persons.Id, Persons.LastName, Persons.FirstName, Persons.Address, Persons.City, Orders.Id, Orders.OrderNo
FROM Persons
RIGHT OUTER JOIN Orders
ON Persons.Id = Orders.PersonId;
```
输出结果:

PersonId|LastName|FirstName|Address|City|OrderId|OrderNo
---|---|---|---|---|---|---
3	|Carter |Thomas |Changan Street |Beijing |1 |77895
3 |Carter |Thomas |Changan Street |Beijing |2 |44678
1 |Adams |John |Oxford Street |London |3 |22456
1 |Adams |John |Oxford Street |London |4 |24562
NULL|NULL|NULL|NULL|NULL|5 |34764

### 4. FULL OUTER JOIN

只要其中某份数据存在，FULL OUTER JOIN 关键字就会返回行。将两表完整的进行笛卡尔积操作，左右表中如果有不存在的均可赋值为NULL。

现在，我们希望列出所有的人，以及他们的定单，以及所有的定单，以及定购它们的人。你可以使用下面的 SELECT 语句：
```sql
SELECT Persons.Id, Persons.LastName, Persons.FirstName, Persons.Address, Persons.City, Orders.Id, Orders.OrderNo
FROM Persons
FULL OUTER JOIN Orders
ON Persons.Id = Orders.PersonId;
```
输出结果：

PersonId|LastName|FirstName|Address|City|OrderId|OrderNo
---|---|---|---|---|---|---
2 |Bush |George |Fifth Avenue |New York |	NULL|NULL
3 |Carter |Thomas |Changan Street |Beijing |1 |77895
3 |Carter |Thomas |Changan Street |Beijing |2 |44678
1 |Adams |John |Oxford Street |London |3 |22456
1 |Adams |John |Oxford Street |London |4 |24562
NULL  |NULL	|	NULL |NULL |NULL |5	|34764

### 5. LEFT SEMI JOIN

LEFT SEMI JOIN以高效的方式实现不相关的IN/EXISTS子查询语义。从Hive 0.13开始，子查询支持 IN/NOT IN/EXISTS/NOT EXISTS运算，因此大多数JOIN不再需要手动执行。使用LEFT SEMI JOIN的限制是右侧表只能在ON子句中使用，而不能在WHERE或SELECT子句中使用。

```sql
SELECT Persons.Id, Persons.LastName, Persons.FirstName, Persons.Address, Persons.City
FROM Persons
LEFT SEMI JOIN Orders
ON Persons.Id = Orders.PersonId;
```
等价于：
```sql
SELECT Id, LastName, FirstName, Address, City
FROM Persons
WHERE Id IN
(
  SELECT PersonId
  FROM Orders
);
```
PersonId|LastName|FirstName|Address|City
---|---|---|---|---|---|---
1 |Adams |John |Oxford Street |London
3 |Carter |Thomas |Changan Street |Beijing
