### 1. 使用count()函数返回文档的数目

函数count()将返回集合中文档数目：
```
> db.Book.count();
2
```
还可以执行额外的过滤，结合条件操作符使用count():
```
> db.Book.find({"author":"丁雪丰"});
{ "_id" : ObjectId("57bc51df521d776dc5921dfd"), "title" : "MongoDB实战", "author" : "丁雪丰", "year" : "2012-10", "price" : 59 }
> 
> 
> db.Book.find({"author":"丁雪丰"}).count();
1
```
上面例子中只返回作者为"丁雪丰"的文档数目。

==备注==

count()函数默认将忽略skip()和limit()参数。为了保证skip()和limit()参数的有效性，请使用count(true)：
```
> db.Book.find().limit(1).count();
2
> db.Book.find().limit(1).count(true);
1
```
### 2. 使用distinct()函数获取唯一值

如果集合中有很多本书（例如，实体书和电子书）含有相同标题，那么从技术上讲，其实集合中只有一本书。这时就用到distinct()函数：将返回一个唯一值。

为了演示我们在集合中添加一个电子书:
```
> db.Book.insert({"title" : "MongoDB实战", "author" : "丁雪丰", "year" : "2012-10", "price" : 12, "type": "e-book"});
WriteResult({ "nInserted" : 1 })
```
这时，集合中将含有两本相同标题的图书。在集合上使用distinct函数，结果只会显示两个唯一值：
```
> db.Book.distinct("title");
[ "MongoDB : The Definitive Guide", "MongoDB实战" ]
```

### 3. 结果分组

MongoDB的group函数类似于SQL中的GROUOP BY子句。该命令的目的是返回一个已分组元素的数组。函数group()将接收三个参数：key , initial 和 reduce。

参数key指定希望使用哪个键对结果进行分组；参数initial允许每个已分组的结果提供基数（元素开始统计的起始基数）；参数reduce接受两个参数：正在遍历的当前文档和聚集对象。

先看一下集合中的文档：

```
> db.Book.find();
{ "_id" : ObjectId("57bbd6b2521d77442c8b9055"), "title" : "MongoDB Definitive Guide", "author" : "Kristina Chodorow", "year" : "2010-9-24", "price" : 39.99 }
{ "_id" : ObjectId("57bc51df521d776dc5921dfd"), "title" : "MongoDB实战", "author" : "丁雪丰", "year" : "2012-10", "price" : 59 }
{ "_id" : ObjectId("57bd315ffe1a4529639146a5"), "title" : "MongoDB实战", "author" : "丁雪丰", "year" : "2012-10", "price" : 12, "type" : "e-book" }
{ "_id" : ObjectId("57bda7e2fe1a4529639146a6"), "title" : "MongoDB实战2", "author" : "丁雪丰", "year" : "2013-10", "price" : 15, "type" : "e-book" }
```
我们可以看到有三本书是"丁雪丰"写的，我们的目的就是以作者进行分组：
```
> db.Book.group({key:{author:true},initial:{Total:0},reduce: function(items, prev){prev.Total += 1;}})
[
	{
		"author" : "Kristina Chodorow",
		"Total" : 1
	},
	{
		"author" : "丁雪丰",
		"Total" : 3
	}
]
```
我们统计的结果是有三本书的作者是"丁雪丰"，有一本书的作者是"Kristina Chodorow"。参数initial设置了元素开始统计的起始基数Total，假设我们设置起始基数为1：
```
> db.Book.group({key:{author:true},initial:{Total:1},reduce: function(items, prev){prev.Total += 1;}})
[
	{
		"author" : "Kristina Chodorow",
		"Total" : 2
	},
	{
		"author" : "丁雪丰",
		"Total" : 4
	}
]
```
reduce参数在遇到每一个匹配项时都会进行统计，这里我们设置prev.Total += 1  即每遇到一个匹配项都会将总数加1。我们也可以设置每遇到一个匹配项加2：
```
> db.Book.group({key:{author:true},initial:{Total:0},reduce: function(items, prev){prev.Total += 2;}})
[
	{
		"author" : "Kristina Chodorow",
		"Total" : 2
	},
	{
		"author" : "丁雪丰",
		"Total" : 6
	}
]
```
