Update操作只作用于集合中存在的文档。MongoDB提供了如下方法来更新集合中的文档：

- db.collection.update()
- db.collection.updateOne() New in version 3.2
- db.collection.updateMany() New in version 3.2
- db.collection.replaceOne() New in version 3.2

你可以通过指定criteria或者filter来指定你想更新的文档：

![image](http://img.blog.csdn.net/20170613104212398?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

update函数执行数据更新操作，该函数接受3个主要参数：criteria，action，options：

- 参数criteria用于指定一个查询，查询选择将要更新的目标记录。
- 参数action用于指定更新信息，也可以使用操作符来完成。
- 参数options用于指定更新文档时的选项，可选值包括：upsert和multi。upsert可以指定如果数据存在就更新，不存在就创建数据；multi选项指定是否应该更新所有匹配的文档，或者只更新第一个文档（默认行为）。

为了更好的演示，插入数据：
```
db.users.insertMany(
   [
     {
       _id: 1,
       name: "sue",
       age: 19,
       type: 1,
       status: "P",
       favorites: { artist: "Picasso", food: "pizza" },
       finished: [ 17, 3 ],
       badges: [ "blue", "black" ],
       points: [
          { points: 85, bonus: 20 },
          { points: 85, bonus: 10 }
       ]
     },
     {
       _id: 2,
       name: "bob",
       age: 42,
       type: 1,
       status: "A",
       favorites: { artist: "Miro", food: "meringue" },
       finished: [ 11, 25 ],
       badges: [ "green" ],
       points: [
          { points: 85, bonus: 20 },
          { points: 64, bonus: 12 }
       ]
     },
     {
       _id: 3,
       name: "ahn",
       age: 22,
       type: 2,
       status: "A",
       favorites: { artist: "Cassatt", food: "cake" },
       finished: [ 6 ],
       badges: [ "blue", "Picasso" ],
       points: [
          { points: 81, bonus: 8 },
          { points: 55, bonus: 20 }
       ]
     },
     {
       _id: 4,
       name: "xi",
       age: 34,
       type: 2,
       status: "D",
       favorites: { artist: "Chagall", food: "chocolate" },
       finished: [ 5, 11 ],
       badges: [ "Picasso", "black" ],
       points: [
          { points: 53, bonus: 15 },
          { points: 51, bonus: 15 }
       ]
     },
     {
       _id: 5,
       name: "xyz",
       age: 23,
       type: 2,
       status: "D",
       favorites: { artist: "Noguchi", food: "nougat" },
       finished: [ 14, 6 ],
       badges: [ "orange" ],
       points: [
          { points: 71, bonus: 20 }
       ]
     },
     {
       _id: 6,
       name: "abc",
       age: 43,
       type: 1,
       status: "A",
       favorites: { food: "pizza", artist: "Picasso" },
       finished: [ 18, 12 ],
       badges: [ "black", "blue" ],
       points: [
          { points: 78, bonus: 8 },
          { points: 57, bonus: 7 }
       ]
     }
   ]
)
```

### 1. 字段更新操作符

#### 1.1 覆盖更新

下面的例子使用update()函数执行更新数据操作，不包含操作符：
```
> db.users.find({"name":"xyz"});
{ "_id" : 5, "name" : "xyz", "age" : 23, "type" : 2, "status" : "D", "favorites" : { "artist" : "Noguchi", "food" : "nougat" }, "finished" : [ 14, 6 ], "badges" : [ "orange" ], "points" : [ { "points" : 71, "bonus" : 20 } ] }
> 
```
修改之后：
```
> db.users.update({"name":"xyz"}, {name : "xyz", age:25, school : "xidian", type:1,  favorites: {artist : "Noguchi", food : "nougat"}, finished : [4, 5] }, {upsert:true});
WriteResult({ "nMatched" : 1, "nUpserted" : 0, "nModified" : 1 })
> 
> 
> 
> db.users.find({"name":"xyz"});
{ "_id" : 5, "name" : "xyz", "age" : 25, "school" : "xidian", "type" : 1, "favorites" : { "artist" : "Noguchi", "food" : "nougat" }, "finished" : [ 4, 5 ] }
```
该例覆写了集合中的文档，并保存更新后的值。

==备注==

任何忽略的字段都被移除（文档被覆盖）

#### 1.2 upsert

upsert可以指定如果数据存在就更新，不存在就创建数据。
```
> db.users.find({"name":"yoona"});
> 
> db.users.update({"name":"yoona"}, {name : "yoona", age:25, "school" : "xidian", type:1,  favorites: {artist : "Noguchi", food : "nougat"}, finished : [4, 5] }, {upsert:false});
WriteResult({ "nMatched" : 0, "nUpserted" : 0, "nModified" : 0 })
```
更新操作之前我们没有查询到yoona的任何信息，然后我们对其进行更新操作，并且upsert设置为false，表示如果更新的数据不存在，不走任何操作。更新之后，我们再次查询一下：
```
> db.users.find({"name":"yoona"});
> 
```
再次查询还是没有找到相应数据。我们设置upsert为true，表示如果数据存在则更新，如果不存在则创建该数据：
```
> db.users.update({"name":"yoona"}, {name : "yoona", age:25, "school" : "xidian", type:1,  favorites: {artist : "Noguchi", food : "nougat"}, finished : [4, 5] }, {upsert:true});
WriteResult({
	"nMatched" : 0,
	"nUpserted" : 1,
	"nModified" : 0,
	"_id" : ObjectId("57c3ad26d2cc0133a95bc583")
})
> 
> db.users.find({"name":"yoona"});
{ "_id" : ObjectId("57c3ad26d2cc0133a95bc583"), "name" : "yoona", "age" : 25, "school" : "xidian", "type" : 1, "favorites" : { "artist" : "Noguchi", "food" : "nougat" }, "finished" : [ 4, 5 ] }
```
#### 1.3 $inc 增加值

操作符$inc可以为指定的键执行（原子）更新操作，如果字段存在，就将该值增加给定的增量，如果该字段不存在，就创建该字段。
```
> db.users.update({"name":"yoona"}, {$inc:{age:2}});
WriteResult({ "nMatched" : 1, "nUpserted" : 0, "nModified" : 1 })
> 
> 
> db.users.find({name:"yoona"});
{ "_id" : ObjectId("57c3ad26d2cc0133a95bc583"), "name" : "yoona", "age" : 27, "school" : "xidian", "type" : 1, "favorites" : { "artist" : "Noguchi", "food" : "nougat" }, "finished" : [ 4, 5 ] }
```
上面例子中将yoona用户的年龄增加两岁。

#### 1.4 $set 设置字段值

可以使用$set操作符将某个字段设置为指定值。
```
> db.users.find({name:"yoona"});
{ "_id" : ObjectId("57c3ad26d2cc0133a95bc583"), "name" : "yoona", "age" : 27, "school" : "xidian", "type" : 1, "favorites" : { "artist" : "Noguchi", "food" : "nougat" }, "finished" : [ 4, 5 ] }
> 
> db.users.update({"name":"yoona"}, {$set:{school:"Massachusetts Institute of Technology"}});
WriteResult({ "nMatched" : 1, "nUpserted" : 0, "nModified" : 1 })
> 
> db.users.find({name:"yoona"});
{ "_id" : ObjectId("57c3ad26d2cc0133a95bc583"), "name" : "yoona", "age" : 27, "school" : "Massachusetts Institute of Technology", "type" : 1, "favorites" : { "artist" : "Noguchi", "food" : "nougat" }, "finished" : [ 4, 5 ] }
> 
```
上面例子将yoona用户的学校改为麻省理工学院。

#### 1.5 $unset删除指定字段
```
> db.users.find({name:"yoona"});
{ "_id" : ObjectId("57c3ad26d2cc0133a95bc583"), "name" : "yoona", "age" : 27, "school" : "Massachusetts Institute of Technology", "type" : 1, "favorites" : { "artist" : "Noguchi", "food" : "nougat" }, "finished" : [ 4, 5 ] }
> 
> db.users.update({"name":"yoona"}, {$unset:{school:"Massachusetts Institute of Technology"}});
WriteResult({ "nMatched" : 1, "nUpserted" : 0, "nModified" : 1 })
> 
> db.users.find({name:"yoona"});
{ "_id" : ObjectId("57c3ad26d2cc0133a95bc583"), "name" : "yoona", "age" : 27, "type" : 1, "favorites" : { "artist" : "Noguchi", "food" : "nougat" }, "finished" : [ 4, 5 ] }
```
上面例子将yoona用户的学校删除。

#### 1.6 $rename 重命名字段名称

格式：
```
{$rename: { <field1>: <newName1>, <field2>: <newName2>, ... } }
```
新字段名称必须不同与已经存在的字段名称
```
> db.users.find({name:"yoona"});
{ "_id" : ObjectId("57c3ad26d2cc0133a95bc583"), "name" : "yoona", "age" : 27, "type" : 1, "favorites" : { "artist" : "Noguchi", "food" : "nougat" }, "finished" : [ 4, 5 ] }
> 
> db.users.update({"name":"yoona"}, {$rename: {name:"userName", age:"userAge"}});
WriteResult({ "nMatched" : 1, "nUpserted" : 0, "nModified" : 1 })
> 
```
查询：
```
> db.users.find({name:"yoona"});
> db.users.find({userName:"yoona"});
{ "_id" : ObjectId("57c3ad26d2cc0133a95bc583"), "type" : 1, "favorites" : { "artist" : "Noguchi", "food" : "nougat" }, "finished" : [ 4, 5 ], "userName" : "yoona", "userAge" : 27 }
> 
```
上面例子中使用$rename将name改为userName，将age改为userAge。


#### 1.7 $min $max数值比较

如果给定值(value1)小于字段的当前值，则更新字段值为给定值。$min运算符可以可以比较不同类型的数字。

格式：
```
{ $min: { <field1>: <value1>, ... } }
```
为了演示，添加如下数据：
```
> db.score.save({_id:1, highScore:90, lowScore: 50});
WriteResult({ "nMatched" : 0, "nUpserted" : 1, "nModified" : 0, "_id" : 1 })
> 
> 
> db.score.find();
{ "_id" : 1, "highScore" : 90, "lowScore" : 50 }
```
给定值与字段当前值进行比较，给定值10小于字段的当前值50，所以更新字段当前值为给定值10：
```
> db.score.update({_id:1}, {$min : {lowScore : 10}});
WriteResult({ "nMatched" : 1, "nUpserted" : 0, "nModified" : 1 })
> 
> db.score.find();
{ "_id" : 1, "highScore" : 90, "lowScore" : 10 }
```
给定值40大于字段当前值10，不做任何变化：
```
> db.score.update({_id:1}, {$min : {lowScore : 40}});
WriteResult({ "nMatched" : 1, "nUpserted" : 0, "nModified" : 0 })
> 
> db.score.find();
{ "_id" : 1, "highScore" : 90, "lowScore" : 10 }
> 
```
#### 1.8 $setOnInsert 

如果更新操作设置upsert:true，执行insert操作时，$setOnInsert会给给定字段赋值给定值。如果更新操作不会导致插入数据，$setOnInsert不会有任何作用。

格式：
```
db.collection.update(
   <query>,
   { $setOnInsert: { <field1>: <value1>, ... } },
   { upsert: true }
)
```
举例：

假设集合products中没有任何文档，进行如下操作：
```
> db.products.find();
> 
> db.products.update({_d:1}, {$set : {item : "apple"}, $setOnInsert : {defaultQty : 100}} , {upsert : true});
WriteResult({
	"nMatched" : 0,
	"nUpserted" : 1,
	"nModified" : 0,
	"_id" : ObjectId("57c43a0ebd7a19639b912212")
})
> 
> db.products.find();
{ "_id" : ObjectId("57c43a0ebd7a19639b912212"), "_d" : 1, "item" : "apple", "defaultQty" : 100 }
```
由于集合中没有任何文档，在对其字段item进行更新时，由于item字段不存在，执行insert操作时，触发setOnInsert操作符，给defaultQty字段赋值为100。


#### 1.9 $currentDate

$curentDate设置字段值为当前日期，可以设置Date类型或者timestamp类型。

格式：
```
{ $currentDate: { <field1>: <typeSpecification1>, ... } }
```
为了演示，添加如下数据：
```
db.student.save({_id:1, name: "yoona", age: 24, college: "计算机学院"});
```
下面添加一个日期类型的"birthday"字段：
```
db.student.update({_id:1}, {$currentDate: {birthday: {$type: "date"}}});
```
最后输出结果：
```
{
    "_id" : 1.0,
    "name" : "yoona",
    "age" : 24.0,
    "college" : "计算机学院",
    "birthday" : ISODate("2016-08-30T02:29:24.425Z")
}
```
### 2. 数组操作符

#### 2.1 $push 在指定字段中添加某个值

通过$push操作符可以在指定字段中添加某个值。如果该字段是个数组，那么该值将被添加到数组中。如果该字段尚不存在，那么该字段的值将被设置为数组。如果该字段存在，但不是数组，那么将会抛出异常。如果给定的值是个数组，那么该数组被看做是一个元素，添加给定字段中（If the value is an array, $push appends the whole array as a single element）。

格式：
```
{ $push: { <field1>: <value1>, ... } }
```
举例：

添加一个分数到成绩数组中：
```
db.student.update({_id:1}, {$push : {scores: 91}});
```
输出结果：
```
{
    "_id" : 1.0,
    "name" : "yoona",
    "age" : 24.0,
    "college" : "计算机学院",
    "birthday" : ISODate("2016-08-30T02:29:24.425Z"),
    "scores" : [ 
        89.0, 
        91.0
    ]
}
```
#### 2.2 $push $each 指定数组中的多个值

格式：
```
{ $push: { <field>: { $each: [ <value1>, <value2> ... ] } } }
```
使用$push操作符可以将值添加到指定数组中，扩展指定元素中存储的数据。如果希望在给定的数组中添加多个值，可以使用可选的$each修改操作符。
```
db.student.update(
   { _id: 1 },
   { $push: { scores: { $each: [ 90, 92, 85 ] } } }
)
```
输出结果：
```
{
    "_id" : 1.0,
    "name" : "yoona",
    "age" : 24.0,
    "college" : "计算机学院",
    "birthday" : ISODate("2016-08-30T02:29:24.425Z"),
    "scores" : [ 
        89.0, 
        91.0, 
        90.0, 
        92.0, 
        85.0
    ]
}
```
在使用$each是还可以使用$slice修改操作符，通过这种方式可以限制$push操作符中数组内元素的数量。$slice可以是正数，负数或0。正数将保证数组中的前n个元素会被保留，使用负数将保证数组中的最后n个元素会被保留，而使用0则表示清空数组。注意：操作符$slice必须是$push操作中的第一个修改操作符。

使用0则表示清空数组：
```
db.student.update(
   { _id: 1 },
   { $push: { scores: { $each: [ 70, 78], $slice: 0 } } }
)
```
输出结果：
```
{
    "_id" : 1.0,
    "name" : "yoona",
    "age" : 24.0,
    "college" : "计算机学院",
    "birthday" : ISODate("2016-08-30T02:29:24.425Z"),
    "scores" : []
}
```
正数将保证数组中的前n个元素会被保留
```
db.student.update(
   { _id: 1 },
   { $push: { scores: { $each: [ 70, 78, 90], $slice: 2 } } }
)
```
输出结果：
```
{
    "_id" : 1.0,
    "name" : "yoona",
    "age" : 24.0,
    "college" : "计算机学院",
    "birthday" : ISODate("2016-08-30T02:29:24.425Z"),
    "scores" : [ 
        70.0, 
        78.0
    ]
}
```
使用负数将保证数组中的最后n个元素会被保留
```
db.student.update(
   { _id: 1 },
   { $push: { scores: { $each: [ 89, 56 ], $slice: -3 } } }
)
```
输出结果：

```
{
    "_id" : 1.0,
    "name" : "yoona",
    "age" : 24.0,
    "college" : "计算机学院",
    "birthday" : ISODate("2016-08-30T02:29:24.425Z"),
    "scores" : [ 
        78.0, 
        89.0, 
        56.0
    ]
}
```
操作符$each和$slice操作符保证不仅新值会被添加到数组中，还能保证吧数组的大小限制为指定值。

#### 2.3 $sort 排序

$sort修改操作符必须与$each修改操作符一起使用。你可以传递一个空数组给$each操作符，这样就可以只使$sort操作符起作用，达到不添加元素，只对原数组排序的目的。

在对数组元素进行排序时，1表示升序，-1表示降序。如果数组元素是文档，我们可以根据整个文档或者是文档中某个具体字段来进行排序。在以前版本中（2.6版本之前）$sort只能根据文档中的具体字段进行排序。假设数组元素是文档，如果只是根据文档中某个字段进行排序，需要使用字段和方向来进行排序，例如， { field: 1 } or { field: -1 }，不要使用{ "arrayField.field": 1 }这种方式进行排序。

格式：
```
{
  $push: {
     <field>: {
       $each: [ <value1>, <value2>, ... ],
       $sort: <sort specification>
     }
  }
}
```
举例：

（1）对数组元素是文档的数组进行排序

为了演示，插入如下数据：
```
db.students.save(
  {
  "_id": 1,
  "quizzes": [
    { "id" : 1, "score" : 6 },
    { "id" : 2, "score" : 9 }
  ]
}
)
```
下面的更新操作，将会添加文档到quizzes 数组中，并且根据数组中文档的score字段进行升序排序：
```
db.students.update(
   { _id: 1 },
   {
     $push: {
       quizzes: {
         $each: [ { id: 3, score: 8 }, { id: 4, score: 7 }, { id: 5, score: 6 } ],
         $sort: { score: 1 }
       }
     }
   }
)
```
输出结果：
```
{
    "_id" : 1.0,
    "quizzes" : [ 
        {
            "id" : 1.0,"score" : 6.0
        }, 
        {
            "id" : 5.0,"score" : 6.0
        }, 
        {
            "id" : 4.0,"score" : 7.0
        }, 
        {
            "id" : 3.0,"score" : 8.0
        }, 
        {
            "id" : 2.0,"score" : 9.0
        }
    ]
}
```
（2）对数组元素不是文档的数组进行排序

为了演示，插入如下数据：
```
db.students.save({ "_id" : 2, "scores" : [  89,  70,  89,  50 ] })
```
下面更新操作，将添加两个元素到数组中，并且对数组进行降序排序：
```
db.students.update(
   { _id: 2 },
   { $push: { scores: { $each: [ 40, 60 ], $sort: -1 } } }
)
```
输出结果：
```
{
    "_id" : 2.0,
    "scores" : [ 
        89.0, 
        89.0, 
        70.0, 
        60.0, 
        50.0, 
        40.0
    ]
}
```
（3）只对数组进行排序
```
db.students.save({ "_id" : 3, "scores" : [  89,  70,  100,  20 ] })
```
下面更新操作，只对数组进行排序，不添加元素：
```
db.students.update(
   { _id: 3 },
   { $push: { scores: { $each: [ ], $sort: 1 } } }
)
```
输出结果：
```
{
    "_id" : 3.0,
    "scores" : [ 
        20.0, 
        70.0, 
        89.0, 
        100.0
    ]
}
```
#### 2.4 $addToSet 向数组中添加数据

操作符$addToSet 是另一个可用于向数组中添加数据的命令。不过，只有数据不存在的时候，该操作符才能将数据添加到数组中（The $addToSet operator adds a value to an array unless the value is already present, in which case$addToSet does nothing to that array）。它的 工作方式与$push不同，$addToSet确保在添加元素时不会与数组中元素重复（$addToSet only ensures that there are no duplicate items added to the set and does not affect existing duplicate elements），但是$push可以添加重复元素。在使用$addToSet时，可以使用$each操作符指定的额外的参数。

如果添加的给定值是个数组，则会把整个数组看做一个元素添加到给定字段中。

格式：
```
{ $addToSet: { <field1>: <value1>, ... } }
```
举例：

（1）给定值是数组
```
{ _id: 1, letters: ["a", "b"] }
```
下面更新操作将会把数组["c", "d"]添加到letters字段中：
```
db.test.update(
   { _id: 1 },
   { $addToSet: {letters: [ "c", "d" ] } }
)
```
现在letters字段包含一个["c", "d"]数组元素：
```
{ _id: 1, letters: [ "a", "b", [ "c", "d" ] ] }
```
如果不想把数组看做一个整个元素添加到指定字段中，而是把数组中的每个元素添加到指定字段中，则需要$each修改操作符配合$addToSet使用。

（2）给定值不是数组，并且指定字段中不存在

考虑如下文档：
```
{
    "_id" : 2.0,
    "scores" : [ 
        89.0
    ]
}
```
添加元素100到成绩数组scores中，并且100在scores中不存在：
```
db.students.update({_id: 2}, { $addToSet: { scores: 100 } });
```
输出结果：
```
{
    "_id" : 2.0,
    "scores" : [ 
        89.0, 
        100.0
    ]
}
```
（3）给定值不是数组，并且指定字段中存在
```
db.students.update({_id: 3}, { $addToSet: { scores: { $each: [ 100, 20, 50 ] } } });
```
输出结果：
```
{
    "_id" : 2.0,
    "scores" : [ 
        89.0, 
        100.0, 
        20.0, 
        50.0
    ]
}
```
我们看到scores数组中只有一个100，这与$push工作方式是不同的。

#### 2.5 $pop 从数组中删除单个元素

操作符$pop可以从数组中删除单个元素。该操作符允许删除数组中的第一个元素或者最后一个元素，具体取决于传入的参数。如果传递的参数为-1表示删除数组第一个元素，1表示删除数组最后一个元素。如果删除的指定字段field不是数组，则会报错。

格式：
```
{ $pop: { <field>: <-1 | 1>, ... } }
```
举例：
```
{
    "_id" : 2.0,
    "scores" : [ 
        89.0, 
        100.0, 
        20.0, 
        50.0
    ]
}
```
删除第一个元素(89.0)：
```
db.students.update({_id:2}, {$pop: {scores: -1}});
```
输出结果：
```
{
    "_id" : 2.0,
    "scores" : [ 
        100.0, 
        20.0, 
        50.0
    ]
}
```
删除最后一个元素（50.0）：
```
db.students.update({_id:2}, {$pop: {scores: 1}});
```
输出结果：
```
{
    "_id" : 2.0,
    "scores" : [ 
        100.0, 
        20.0
    ]
}
```
#### 2.6 $pull 删除所有指定值

通过使用$pull操作符可以从数组中删除所有指定的值或者符合给定条件的值。如果数组中有多个元素的值相同，那么该操作符是非常有用的。

格式：
```
{ $pull: { <field1>: <value|condition>, <field2>: <value|condition>, ... } }
```
举例：

（1）删除与给定值相等的所有值

为了演示，添加如下数据：
```
db.stores.save(
{
   _id: 1,
   fruits: [ "apples", "pears", "oranges", "grapes", "bananas" ],
   vegetables: [ "carrots", "celery", "squash", "carrots" ]
});
db.stores.save(
{
   _id: 2,
   fruits: [ "plums", "kiwis", "oranges", "bananas", "apples" ],
   vegetables: [ "broccoli", "zucchini", "carrots", "onions" ]
});
```
下面更新操作从fruits中删除"apples" 和 "oranges"，从vegetables数组中删除"carrots"：
```
db.stores.update({}, {$pull: {fruits: {$in : ["apples", "oranges"]}, vegetables: "carrots"  }}, {multi: true});
```
输出结果：
```
/* 1 */
{
    "_id" : 1.0,
    "fruits" : [ 
        "pears", 
        "grapes", 
        "bananas"
    ],
    "vegetables" : [ 
        "celery", 
        "squash"
    ]
}
/* 2 */
{
    "_id" : 2.0,
    "fruits" : [ 
        "plums", 
        "kiwis", 
        "bananas"
    ],
    "vegetables" : [ 
        "broccoli", 
        "zucchini", 
        "onions"
    ]
}
```
（2）删除与给定条件相匹配的所有值
为了演示插入如下数据：
```
db.profiles.save({ _id: 1, votes: [ 3, 5, 6, 7, 7, 8 ] });
```
下面更新操作删除数组中大于6的元素：
```
db.profiles.update({_id:1}, {$pull: {votes: {$gte : 6}} });
```
输出结果：
```
{
    "_id" : 1.0,
    "votes" : [ 
        3.0, 
        5.0
    ]
}
```
（3）删除数组中文档类型的数组元素

为了演示，插入如下数据：
```
db.survey.save({
   _id: 1,
   results: [
      { item: "A", score: 5 },
      { item: "B", score: 8, comment: "Strongly agree" }
   ]
});
db.survey.save({
   _id: 2,
   results: [
      { item: "C", score: 8, comment: "Strongly agree" },
      { item: "B", score: 4 }
   ]
});
```
下面更新操作删除数组元素中包含值为8的score字段和值为"B"的item字段：
```
db.survey.update({ }, {$pull: {results: { score : 8, item : "B" }} }, {multi: true});
```
输出结果：
```
{
    "_id" : 1.0,
    "results" : [ 
        {
            "item" : "A",
            "score" : 5.0
        }
    ]
}
{
    "_id" : 2.0,
    "results" : [ 
        {
            "item" : "C",
            "score" : 8.0,
            "comment" : "Strongly agree"
        }, 
        {
            "item" : "B",
            "score" : 4.0
        }
    ]
}
```
（3）删除数组中嵌套文档的数组元素

为了演示，插入如下数据：
```
db.survey2.save({
   _id: 1,
   results: [
      { item: "A", score: 5, answers: [ { q: 1, a: 4 }, { q: 2, a: 6 } ] },
      { item: "B", score: 8, answers: [ { q: 1, a: 8 }, { q: 2, a: 9 } ] }
   ]
});
db.survey2.save({
   _id: 2,
   results: [
      { item: "C", score: 8, answers: [ { q: 1, a: 8 }, { q: 2, a: 7 } ] },
      { item: "B", score: 4, answers: [ { q: 1, a: 0 }, { q: 2, a: 8 } ] }
   ]
});
```
我们看到文档中嵌套文档，我们如何根据文档中嵌套的文档条件删除呢？下面更新操作删除results数组元素，其满足ansmers字段至少包含一个q值为2以及a大于等于8：
```
db.survey2.update(
  { },
  { $pull: { results: { answers: { $elemMatch: { q: 2, a: { $gte: 8 } } } } } },
  { multi: true }
)
```
输出结果：
```
{
    "_id" : 1.0,
    "results" : [ 
        {
            "item" : "A",
            "score" : 5.0,
            "answers" : [ 
                {
                    "q" : 1.0,
                    "a" : 4.0
                }, 
                {
                    "q" : 2.0,
                    "a" : 6.0
                }
            ]
        }
    ]
}
{
    "_id" : 2.0,
    "results" : [ 
        {
            "item" : "C",
            "score" : 8.0,
            "answers" : [ 
                {
                    "q" : 1.0,
                    "a" : 8.0
                }, 
                {
                    "q" : 2.0,
                    "a" : 7.0
                }
            ]
        }
    ]
}
```
#### 2.7 $pullAll删除数组中多个元素

我们还可以从数组中删除多个含有不同值的元素。该操作符将接收一个希望移除元素的数组。不同于$pull，$pull从数组中删除匹配查询条件的数组元素。

格式：
```
{ $pullAll: { <field1>: [ <value1>, <value2> ... ], ... } }
```
举例：

为了演示，插入如下数据：
```
db.scores.save({_id:1, scores:[67, 89, 90, 87, 54, 100]});
```
下面更新操作从scores数组中删除分值为"67"和"54"的成绩：
```
db.scores.update({_id:1}, {$pullAll: {scores: [67, 54]}});
```
输出结果：
```
{
    "_id" : 1.0,
    "scores" : [ 
        89.0, 
        90.0, 
        87.0, 
        100.0
    ]
}
```