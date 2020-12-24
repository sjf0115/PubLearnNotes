MongoDB支持大量的条件操作符用于过滤结果。

所有数据：
```
> db.Book.find();
{ "_id" : ObjectId("57bbd6b2521d77442c8b9055"), "title" : "MongoDB : The Definitive Guide", "author" : "Kristina Chodorow", "year" : "2010-9-24", "price" : 39.99 }
{ "_id" : ObjectId("57bc51df521d776dc5921dfd"), "title" : "MongoDB实战", "author" : "丁雪丰", "year" : "2012-10", "price" : 59 }
{ "_id" : ObjectId("57bd315ffe1a4529639146a5"), "title" : "MongoDB实战", "author" : "丁雪丰", "year" : "2012-10", "price" : 12, "type" : "e-book" }
{ "_id" : ObjectId("57bda7e2fe1a4529639146a6"), "title" : "MongoDB实战2", "author" : "丁雪丰", "year" : "2013-10", "price" : 15, "type" : "e-book" }
```

### 1. 大于和小于比较

以下特殊参数可用于在查询中执行大于和小于比较：$gt(大于)，$lt(小于)，$gte(大于等于)，$lte(小于等于)。

$gt大于参数，该参数指定文档中的某个整数必须大于一个指定值时，才能在结果中返回，下面查找价格大于40的书籍：
```
> db.Book.find({"price":{$gt:40}});
{ "_id" : ObjectId("57bc51df521d776dc5921dfd"), "title" : "MongoDB实战", "author" : "丁雪丰", "year" : "2012-10", "price" : 59 }
```
$lt小于参数，该参数指定文档中的某个整数必须小于一个指定值时，才能在结果中返回，下面查找价格小于40的书籍：
```
> db.Book.find({"price":{$lt:40}});
{ "_id" : ObjectId("57bbd6b2521d77442c8b9055"), "title" : "MongoDB : The Definitive Guide", "author" : "Kristina Chodorow", "year" : "2010-9-24", "price" : 39.99 }
{ "_id" : ObjectId("57bd315ffe1a4529639146a5"), "title" : "MongoDB实战", "author" : "丁雪丰", "year" : "2012-10", "price" : 12, "type" : "e-book" }
{ "_id" : ObjectId("57bda7e2fe1a4529639146a6"), "title" : "MongoDB实战2", "author" : "丁雪丰", "year" : "2013-10", "price" : 15, "type" : "e-book" }
```
$gte大于等于参数，该参数指定文档中的某个整数必须大于等于一个指定值时，才能在结果中返回，下面查找价格大于等于39.99的书籍：
```
> db.Book.find({"price":{$gte:39.99}});
{ "_id" : ObjectId("57bbd6b2521d77442c8b9055"), "title" : "MongoDB : The Definitive Guide", "author" : "Kristina Chodorow", "year" : "2010-9-24", "price" : 39.99 }
{ "_id" : ObjectId("57bc51df521d776dc5921dfd"), "title" : "MongoDB实战", "author" : "丁雪丰", "year" : "2012-10", "price" : 59 }
```
我们还可以结合这些参数指定一个范围，下面查找价格大于12小于30的书籍：
```
> db.Book.find({"price":{$gt:12, $lt:30}});
{ "_id" : ObjectId("57bda7e2fe1a4529639146a6"), "title" : "MongoDB实战2", "author" : "丁雪丰", "year" : "2013-10", "price" : 15, "type" : "e-book" }
```
### 2. 获取除特定文档之外的所有文档

使用参数$ne可以回去集合中除某些符合特定条件的文档之外的所有文档。下面查找作者不是"丁雪丰"的所有图书列表：
```
> db.Book.find({"author":{$ne: "丁雪丰"}});
{ "_id" : ObjectId("57bbd6b2521d77442c8b9055"), "title" : "MongoDB : The Definitive Guide", "author" : "Kristina Chodorow", "year" : "2010-9-24", "price" : 39.99 }
```
### 3. 指定一个匹配的数组

可以使用$in操作符指定一组可能的匹配值。SQL中对应的操作符为IN。下面查找出版时间为"2010-9-24"和"2012-10"两个时间的书籍：
```
> db.Book.find({"year":{$in: ["2010-9-24", "2012-10"]}});
{ "_id" : ObjectId("57bbd6b2521d77442c8b9055"), "title" : "MongoDB : The Definitive Guide", "author" : "Kristina Chodorow", "year" : "2010-9-24", "price" : 39.99 }
{ "_id" : ObjectId("57bc51df521d776dc5921dfd"), "title" : "MongoDB实战", "author" : "丁雪丰", "year" : "2012-10", "price" : 59 }
{ "_id" : ObjectId("57bd315ffe1a4529639146a5"), "title" : "MongoDB实战", "author" : "丁雪丰", "year" : "2012-10", "price" : 12, "type" : "e-book" }
```
### 4. 查找某个不在数组中的值

操作符$nin和$in类似，不过它将搜索特定字段的值不在数组列表中的文档。下面查找出版时间不为"2010-9-24"和"2012-10"两个时间的书籍：
```
> db.Book.find({"year":{$nin: ["2010-9-24", "2012-10"]}});
{ "_id" : ObjectId("57bda7e2fe1a4529639146a6"), "title" : "MongoDB实战2", "author" : "丁雪丰", "year" : "2013-10", "price" : 15, "type" : "e-book" }
> 
```
### 5. 匹配文档中的所有属性

操作符$all与$in类似，不过$all要求所有属性都匹配，$in操作符值要求文档中的一个属性匹配即可：

为了演示，插入如下数据：
```
> db.Book.insert({"title" : "MongoDB实战第三版", "author" : ["丁雪丰", "Kyle Banker"], "year" : "2015-10", "price" : 45});
WriteResult({ "nInserted" : 1 })
```
首先看$all的用法：
```
> db.Book.find({"author":{$in: ["丁雪丰", "Kyle Banker"]}});
{ "_id" : ObjectId("57bc51df521d776dc5921dfd"), "title" : "MongoDB实战", "author" : "丁雪丰", "year" : "2012-10", "price" : 59 }
{ "_id" : ObjectId("57bd315ffe1a4529639146a5"), "title" : "MongoDB实战", "author" : "丁雪丰", "year" : "2012-10", "price" : 12, "type" : "e-book" }
{ "_id" : ObjectId("57bda7e2fe1a4529639146a6"), "title" : "MongoDB实战2", "author" : "丁雪丰", "year" : "2013-10", "price" : 15, "type" : "e-book" }
{ "_id" : ObjectId("57be843dfe1a4529639146a7"), "title" : "MongoDB实战第三版", "author" : [ "丁雪丰", "Kyle Banker" ], "year" : "2015-10", "price" : 45 }
```
只要作者是"丁雪丰" 或者 "Kyle Banker"即可返回。下面看看$all的用法：
```
> db.Book.find({"author":{$all: ["丁雪丰", "Kyle Banker"]}});
{ "_id" : ObjectId("57be843dfe1a4529639146a7"), "title" : "MongoDB实战第三版", "author" : [ "丁雪丰", "Kyle Banker" ], "year" : "2015-10", "price" : 45 }
```
只有作者是"丁雪丰" 和 "Kyle Banker"两个人是才可满足。


### 6. 在文档中搜索多个表达式

在单个查询中可以使用$or操作符搜索多个表达式，它将返回满足其中任何一个条件的文档。与$in不同，$or允许同时指定键和值，而不是指定值：

```
> db.Book.find({$or: [{"price":12}, {"year":"2013-10"}]});
{ "_id" : ObjectId("57bd315ffe1a4529639146a5"), "title" : "MongoDB实战", "author" : "丁雪丰", "year" : "2012-10", "price" : 12, "type" : "e-book" }
{ "_id" : ObjectId("57bda7e2fe1a4529639146a6"), "title" : "MongoDB实战2", "author" : "丁雪丰", "year" : "2013-10", "price" : 15, "type" : "e-book" }
```
还可以将$or与另一个查询参数结合使用。这将会要求返回的文档必须先满足第一个条件，然后在满足$or操作符中的两个键值对之一：
```
> db.Book.find({"author":"丁雪丰", $or: [{"price":12}, {"year":"2010-9-24"}]});
{ "_id" : ObjectId("57bd315ffe1a4529639146a5"), "title" : "MongoDB实战", "author" : "丁雪丰", "year" : "2012-10", "price" : 12, "type" : "e-book" }
```
### 7. 使用$slice获取文档

通过$slice获取的文档将只包含数组中特定范围的值。通过该操作符还可以获取结果中每页的n项数据，该特性通常被称为分页。理论上，操作符$slice结合了limit()和skip()函数的功能；不过，limit()和skip()无法作用于数组，而$slice可以。该操作符接受两个参数：第一个参数表示将要返回数据项的总数；第二个参数是可选的，如果使用了该参数，那么第一个参数将用于定义偏移，第二个参数用于定义限制。参数limit可以使用负值。

为了更好的演示，插入如下数据：
```
> db.Book.insert({"title" : "Redis实战", "author" : ["JosiahL","Carlson", "Kyle Banker", "黄健宏"], "year" : "2015-10", "price" : 52});
WriteResult({ "nInserted" : 1 })
```
下面只返回author列表的前三项：
```
> db.Book.find({"title":"Redis实战"},{"author" : {$slice:3}});
{ "_id" : ObjectId("57beaebefe1a4529639146a8"), "title" : "Redis实战", "author" : [ "JosiahL", "Carlson", "Kyle Banker" ], "year" : "2015-10", "price" : 52 }
```
还可以使用负整数返回它的最后三项：
```
> db.Book.find({"title":"Redis实战"},{"author" : {$slice:-3}});
{ "_id" : ObjectId("57beaebefe1a4529639146a8"), "title" : "Redis实战", "author" : [ "Carlson", "Kyle Banker", "黄健宏" ], "year" : "2015-10", "price" : 52 }
```
还可以返回从某个位置开始的两项数据，下面表示从一个位置开始的2项数据（从0开始）：
```
> db.Book.find({"title":"Redis实战"},{"author" : {$slice:[1,2]}});
{ "_id" : ObjectId("57beaebefe1a4529639146a8"), "title" : "Redis实战", "author" : [ "Carlson", "Kyle Banker" ], "year" : "2015-10", "price" : 52 }
```
### 8. 搜索奇数/偶数

通过使用$mod操作符可以搜索由奇数或者偶数组成的特定数据。该操作符将把目标值除以2，并检查该运算的余数是否是0，通过这种方式只提供偶数结果。

下面我们来判断Redis实战这本书的价格是否是偶数奇数：
```
> db.Book.find({"title":"Redis实战", "price":{$mod : [2,0]}});
{ "_id" : ObjectId("57beaebefe1a4529639146a8"), "title" : "Redis实战", "author" : [ "JosiahL", "Carlson", "Kyle Banker", "黄健宏" ], "year" : "2015-10", "price" : 52 }
> 
> 
> db.Book.find({"title":"Redis实战", "price":{$mod : [2,1]}});
> 
> 
```
### 9. 使用$size过滤结果

通过操作符$size可以过滤出文档中数组大小符合条件的结果。例如，可以使用该操作符搜索只两个作者的书籍：
```
> db.Book.find({"author": {$size : 2}});
{ "_id" : ObjectId("57be843dfe1a4529639146a7"), "title" : "MongoDB实战第三版", "author" : [ "丁雪丰", "Kyle Banker" ], "year" : "2015-10", "price" : 45 }
> 
> 
> 
> db.Book.find({"author": {$size : 3}});
> db.Book.find({"author": {$size : 4}});
{ "_id" : ObjectId("57beaebefe1a4529639146a8"), "title" : "Redis实战", "author" : [ "JosiahL", "Carlson", "Kyle Banker", "黄健宏" ], "year" : "2015-10", "price" : 52 }

```
### 10. 返回含有特定字段的对象

使用$exists操作符在特定字段存在或不存在的情况下，返回该对象。下面，将返回集合中含有"type"键的所有文档：
```
> db.Book.find({"type": {$exists : true}});
{ "_id" : ObjectId("57bd315ffe1a4529639146a5"), "title" : "MongoDB实战", "author" : "丁雪丰", "year" : "2012-10", "price" : 12, "type" : "e-book" }
{ "_id" : ObjectId("57bda7e2fe1a4529639146a6"), "title" : "MongoDB实战2", "author" : "丁雪丰", "year" : "2013-10", "price" : 15, "type" : "e-book" }
```
### 11. $not

可以使用$not元操作符否定任何标准操作符执行的检查。
```
> db.Book.find({ "price" : {$not : {$gt : 30} } });
{ "_id" : ObjectId("57bd315ffe1a4529639146a5"), "title" : "MongoDB实战", "author" : "丁雪丰", "year" : "2012-10", "price" : 12, "type" : "e-book" }
{ "_id" : ObjectId("57bda7e2fe1a4529639146a6"), "title" : "MongoDB实战2", "author" : "丁雪丰", "year" : "2013-10", "price" : 15, "type" : "e-book" }
```
上面语句将会返回所有价格不大于30或者没有price字段的所有文档。

==备注==

$not操作符只能作用与于其他操作符上，不能单独在字段和文档上使用。



### 12. 使用正则表达式

允许在查询中使用正则表达式，用于在Book集合上搜索标题中包含"Refis"的所有文档：
```
> db.Book.find({ "title" : {$regex : "Redis"}});
{ "_id" : ObjectId("57beaebefe1a4529639146a8"), "title" : "Redis实战", "author" : [ "JosiahL", "Carlson", "Kyle Banker", "黄健宏" ], "year" : "2015-10", "price" : 52 }
```
