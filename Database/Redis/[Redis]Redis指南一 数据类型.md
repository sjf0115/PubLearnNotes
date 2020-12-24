
### 1. 字符串

#### 1.1 SET与GET

```
SET key value
GET key
```

Redis中的字符串是一个字节序列。Redis中的字符串是二进制安全的，这意味着它们的长度不由任何特殊的终止字符决定。因此，可以在一个字符串中存储高达512兆字节的任何内容。

```
127.0.0.1:6379> SET USER "yoona"
OK
127.0.0.1:6379> GET USER
"yoona"
```

#### 1.2 INCR与INCRBY 增加指定整数

```
INCR key
INCRBY key increment
```

字符串类型可以存储任何形式的字符串，当存储的字符串是整数形式时，Redis提供了一个实用的命令`INCR`，其作用是让当前键值递增，并返回递增后的值：
```
127.0.0.1:6379> SET age 28
OK
127.0.0.1:6379> INCR age
(integer) 29
```

`INCRBY`命令与`INCR`命令基本一样，只不过前者可以通过`increment`参数指定一次增加的数值：

```
127.0.0.1:6379> INCRBY age 2
(integer) 31
127.0.0.1:6379> INCRBY age 4
(integer) 35
```

#### 1.3 DECR与DECRBY 减少指定整数

```
DECR key
DECRBY key increment
```
`DECR`命令与`INCR`命令用法相同，只不过是让键值递减：
```
127.0.0.1:6379> DECR age
(integer) 34
127.0.0.1:6379> DECR age
(integer) 33
```
`DECRBY`命令与`DECR`命令基本一样，只不过前者可以通过`increment`参数指定一次递减的数值：
```
127.0.0.1:6379> DECRBY age 1
(integer) 32
127.0.0.1:6379> DECRBY age 3
(integer) 29
```

#### 1.4 INCRBYFLOAT 增加指定浮点数

```
INCRBYFLOAT key increment
```
`INCRBYFLOAT`命令类似`INCRBY`命令，差别是前者可以递增一个双精度浮点数：
```
127.0.0.1:6379> INCRBYFLOAT price 1000
"1000"
127.0.0.1:6379> INCRBYFLOAT price 200.5
"1200.5"
```
#### 1.5 APPEND 尾部追加

```
APPEND key value
```
`APPEND`的作用是向键值的末尾追加`value`．如果键不存在则将键的值设置为`value`，即相当于`SET key value`．返回值是追加后字符串的总长度：
```
127.0.0.1:6379> APPEND favorite "football"
(integer) 8
127.0.0.1:6379> APPEND favorite "travel"
(integer) 14
127.0.0.1:6379> GET favorite
"footballtravel"
```

#### 1.6 MGET与MSET　同时获得／设置多个键值

```
MGET key [key ...]
MSET key value [key value ...]
```

`MGET/MSET` 与 `GET/SET`相似，不过前者可以同时获得/设置多个键的键值：
```
127.0.0.1:6379> MSET sex "boy" city "beijing"
OK
127.0.0.1:6379> MGET sex city
1) "boy"
2) "beijing"
```


==备注==

Redis　对于键的命名并没有强制的要求，但比较好的实践是用`对象类型:对象ID:对象属性`来命名一个键，如使用键`user:1:friends`来存储ID为1的用户的好友列表．对于单个单词则推荐使用`.`分割，键的命名一定要有意义，如`u:1:f`的可读性显然不如上面那个(虽然采用较短的名称可以节省存储空间，但由于键值的长度往往远远大于键名的长度，所以这部分的节省大部分情况下并不如可读性来的重要)．


### 2. 散列类型

散列类型的键值也是一种字典结构，其存储了字段(field)和字段值的映射，但字段值只能是字符串，不能支持其他数据类型，换句话说，散列类型不能嵌套其他的数据类型．一个散列类型键可以包含至少`2^32-1`个字段.

==备注==

除了散列类型，其他数据类型同样不支持数据类型嵌套．比如集合数据类型的每个元素都只能是字符串，不能是另一个集合或者散列表等．

==散列类型适合存储对象==：使用对象类别和ID构成键名，使用字段表示对象的属性，而字段值则存储属性值．例如存储ID为２的汽车对象，可以分别使用名为`color,name和price`的三个字段来存储该汽车的颜色，名称和价格．


```
graph LR

B["car:2"]
B-->C["color"];
B-->D["name"];
B-->E["price"];
C-->F("白色");
D-->G("奥迪");
E-->H("90万");
```
如果我们在关系性数据库中存储汽车对象，存储结构如下表所示：

ID | color | name | price
---|---|---|---
1 | 黑色 | 宝马 | 100万 
2 | 白色 |奥迪 |90万
3|蓝色|宾利|600万

数据是以二维表的形式存储的，这就要求所有的记录都拥有同样的属性，无法单独为某条记录增减属性．如果想为ID为1的汽车增加生产日期属性，就需要把数据表更改为如下结构：

ID | color | name | price | date
---|---|---|---|---
1 | 黑色 | 宝马 | 100万|2017.05.27 
2 | 白色 |奥迪 |90万
3|蓝色|宾利|600万

对于ID为2或者3的两条记录而言date字段是冗余的．可想而知当不同的记录需要不同的属性时，表的字段熟两回越来越多以至于难以维护．

而Redis的散列表类型则不存在这个问题．

#### 2.1 赋值与取值

```
HSET key field value
HGET key field
HMSET key field value [field value]
HMGET key field [field]
HGETALL key
```
`HSET`命令用来给字段赋值，`HGET`命令用来获得字段的值：
```
127.0.0.1:6379> HSET car price 500
(integer) 1
127.0.0.1:6379> HSET car name BMW
(integer) 1
127.0.0.1:6379> HGET car price
"500"
127.0.0.1:6379> HGET car name
"BMW"
```
当需要同时设置多个字段的值时，可以使用`HMSET`命令，相应的，`HMGET`可以同时获得多个字段的值：
```
127.0.0.1:6379> HMSET car:2 price 1000 date 2017.05.31
OK
127.0.0.1:6379> HMGET car:2 price date
1) "1000"
2) "2017.05.31"
```
如果想获取键中所有字段和字段值使用如下命令：
```
127.0.0.1:6379> HGETALL car:2
1) "price"
2) "1000"
3) "date"
4) "2017.05.31"
```

#### 2.2 HEXISTS 判断字段是否存在

```
HEXISTS key field
```
`HEXISTS`命令用来判断一个字段是否存在.如果存在则返回1，否则返回0

```
127.0.0.1:6379> HEXISTS car:2 price
(integer) 1
127.0.0.1:6379> HEXISTS car:2 name
(integer) 0
```

#### 2.3 HINCRBY 增加数字

```
HINCRBY key field increment
```
`HINCRBY`与字符串类型命令`INCRBY`相类似，可以使字段值增加指定的整数，散列类型没有`HINCR`命令，但是可以通过`HINCRBY key field 1`实现．

```
127.0.0.1:6379> HINCRBY car:2 price 20
(integer) 1020
127.0.0.1:6379> HINCRBY car:2 price 100
(integer) 1120
```
#### 2.4 HDEL 删除字段

```
HDEL key field [field...]
```

`HDEL`命令可以删除一个或者多个字段，返回值是被删除的字段个数：
```
127.0.0.1:6379> HGETALL car:2
1) "date"
2) "2017.05.31"
127.0.0.1:6379> HDEL car:2 date
(integer) 1
```

#### 2.5 HKEYS HVALS 只获取字段名或者字段值

```
HKEYS key
HVALS key
```
有时我们仅仅需要获取键中所有字段的名字而不需要字段值或者仅仅需要获取键中所有字段值而不需要字段名：
```
127.0.0.1:6379> HKEYS car:2
1) "price"
2) "date"
127.0.0.1:6379> HVALS car:2
1) "1000"
2) "2017.05.31"
```

#### 2.6 获取字段数量

```
HLEN key
```
例如：
```
127.0.0.1:6379> HLEN car:2
(integer) 2
```

### 3. 列表类型

列表类型可以存储一个有序的字符串列表，常用的操作是向列表两端添加元素，或者获得列表的某一个片段．

列表类型内部是使用双向链表实现的，所以向列表两端添加元素的时间复杂度为O(1)，获取越接近两端的元素速度越快．这就意味着即使是一个有几千万个元素的列表，获取头部或尾部的10条记录也是挺快的（和从只有20个元素的列表中获取头部或尾部的10条记录的速度是一样的）．不过使用链表的代价是通过索引访问元素比较慢.

这种特性使列表类型能非常块的完成关系性数据库难以应付的场景：如社交网站的新鲜事，我们关心的只是最新的内容，使用列表类型存储，即使新鲜事的总数达到几千万个，获取其中最新的100条记录也是极快的．　列表类型也适合用来记录日志，可以保证加入新日志的速度不会受到已有日志数量的影响．

#### 3.1 向列表两端添加元素

```
LPUSH key value [value..]
RPUSH key value [value..]
```
`LPUSH`命令用来向列表左边增加元素，返回值表示增加元素后列表的长度．
```
127.0.0.1:6379> LPUSH numbers 1
(integer) 1
```
这时numbers键中的数据如下图所示：

```
graph LR
subgraph numbers
A("1")
end
```
`LPUSH`命令还支持同时添加多个元素：
```
127.0.0.1:6379> LPUSH numbers 2 3
(integer) 3
```
这时numbers键中的数据如下图所示：

```
graph LR
subgraph numbers
A("3")--- B("2")
B("2")---C("1")
end 
```
向列表右边增加元素的使用`RPUSH`命令，其用法和`LPUSH`命令一样：

```
127.0.0.1:6379> RPUSH numbers 0 -1
(integer) 5
```
这时numbers键中的数据如下图所示：

```
graph LR
subgraph numbers
A("3")--- B("2")
B("2")---C("1")
C("1")---D("0")
D("0")---E("-1")
end 
```
#### 3.2 LPOP RPOP 从两端弹出元素

```
LPOP key
RPOP key
```
`LPOP`命令可以从列表左边弹出一个元素，而`RPOP`命令可以从列表右边掏出一个元素．`LPOP`命令执行两步操作：第一步是将列表左边的元素从列表中移除，第二步是返回被移除的元素值：
```
127.0.0.1:6379> LPOP numbers
"3"
127.0.0.1:6379> RPOP numbers
"-1"
```

这时numbers键中的数据如下图所示：

```
graph LR
subgraph numbers
B("2")---C("1")
C("1")---D("0")
end 
```
#### 3.3 LRANGE 获取列表片段

```
LRANGE key start stop
```
`LRANGE`命令是列表类型最常用的命令之一，它能够获得列表中的某一片段．该命令将返回索引从start到stop之间的所有元素（包含两端的元素），列表起始索引为０：
```
127.0.0.1:6379> LRANGE numbers 1 2
1) "1"
2) "0"

```
`LRANGE`命令也支持负索引，表示从右边开始计算序数，如"-1"表示最右边第一个元素，"-2"表示最右边第二个元素，以此类推：
```
127.0.0.1:6379> LRANGE numbers -2 -1
1) "1"
2) "0"

```
#### 3.4 LREM 删除列表中指定的值

```
LREM key count value
```
`LREM`命令会删除列表中前count个值为value的元素，返回值是实际删除的元素个数．根据count值的不同，LREM命令的执行方式会略有差异：

- 当count < ０时LREM命令会从列表左边开始删除前count个值为value的元素
- 当count < ０时LREM命令会从列表右边开始删除前|count|个值为value的元素
- 当count = ０时LREM命令会删除所有值为value的元素


从右边开始删除第一个值为2的元素：
```
127.0.0.1:6379> RPUSH numbers 2
(integer) 4
127.0.0.1:6379> LRANGE numbers 0 -1
1) "2"
2) "1"
3) "0"
4) "2"
127.0.0.1:6379> LREM numbers -1 2
(integer) 1
127.0.0.1:6379> LRANGE numbers 0 -1
1) "2"
2) "1"
3) "0"
```
#### 3.5 LINDEX LSET 获得/设置指定索引的元素值

```
LINDEX key index
LSET key index value
```
如果将列表类型当做数组来用，`LINDEX`命令是必不可少的．`LINDEX`命令用来返回指定索引的元素，索引从0开始：
```
127.0.0.1:6379> LRANGE numbers 0 -1
1) "2"
2) "1"
3) "0"
127.0.0.1:6379> LINDEX numbers 1
"1"
```
`LSET`是另一个索引操作列表的命令，它将索引为index的元素赋值为value:
```
127.0.0.1:6379> LSET numbers 1 7
OK
127.0.0.1:6379> LRANGE numbers 0 -1
1) "2"
2) "7"
3) "0"

```

#### 3.6 LINSERT 向列表中插入元素

```
LINSERT key BEFORE|AFTER pivot value
```

`LINSERT`命令首先会在列表中从左到右查找值为`pivot`的元素，然后根据第二个参数是`BEFORE`还是`AFTER`来决定将value插入到该元素的前面还是后面．

LINSERT命令的返回值是插入后列表的元素个数：
```
127.0.0.1:6379> LRANGE numbers 0 -1
1) "2"
2) "7"
3) "0"
127.0.0.1:6379> LINSERT numbers AFTER 7 3
(integer) 4
127.0.0.1:6379> LRANGE numbers 0 -1
1) "2"
2) "7"
3) "3"
4) "0"
127.0.0.1:6379> LINSERT NUMBERS BEFORE 2 1
(integer) 5
127.0.0.1:6379> LRANGE NUMBERS 0 -1
1) "1"
2) "2"
3) "7"
4) "3"
5) "0"
```

### 4. 集合类型

在集合中每个元素都是不同的，且没有顺序．一个集合类型键可以存储至多2^32－1个字符串. 集合类型和列表类型有相似之处，但很容易将它们区分：

＼ | 集合类型 | 列表类型
---|---|---
存储内容 |至多2^32－1个字符串|至多2^32－1个字符串
有序性 | 否 | 是
唯一性 | 是　|　否

#### 4.1 SADD SREM 增加/删除元素

```
SADD key member [member ...]
SREM key member [member ...]
```
`SADD`命令用来向集合中添加一个或者多个元素，如果键不存在则会自动创建．因为在一个集合中不能有相同的元素，所以如果要加入的元素已经存在于集合中就会胡烈这个元素．返回值是成功加入的元素数量（忽略的元素不计算在内）：
```
127.0.0.1:6379> SADD letters a
(integer) 1
127.0.0.1:6379> SADD letters a b c
(integer) 2

```

`SREM`命令用来从集合中删除一个或多个元素，并返回删除成功的个数：
```
127.0.0.1:6379> SREM letters c d
(integer) 1
```
由于元素d不在集合中，所以只删除一个元素，返回值为1．

#### 4.2 SMEMBERS 获得集合中的所有元素

```
SMEMBERS key
```
例如：
```
127.0.0.1:6379> SMEMBERS letters
1) "b"
2) "a"
```
#### 4.3 集合间运算

```
SDIFF key [key ...]
SINTER key [key...]
SUNION key [key ...]
```
`SDIFF`命令用来对多个集合执行差集运算．
```
127.0.0.1:6379> SADD seta 1 2 3
(integer) 3
127.0.0.1:6379> SADD setb 2 3 4
(integer) 3
127.0.0.1:6379> SDIFF seta setb
1) "1"
127.0.0.1:6379> SDIFF setb seta
1) "4"

```

`SINTER`命令用来对多个集合执行交集运算．
```
127.0.0.1:6379> SADD seta 1 2 3
(integer) 3
127.0.0.1:6379> SADD setb 2 3 4
(integer) 3
127.0.0.1:6379> SINTER seta setb
1) "2"
2) "3"

```
`SUNION`命令用来对多个集合执行并集运算．
```
127.0.0.1:6379> SADD seta 1 2 3
(integer) 3
127.0.0.1:6379> SADD setb 2 3 4
(integer) 3
127.0.0.1:6379> SUNION seta setb
1) "1"
2) "2"
3) "3"
4) "4"

```

### 5. 有序集合类型

在集合类型的基础上有序集合类型为集合中的每个元素都关联了一个分数，这使得我们不仅可以完成插入，删除和判断元素是否存在等集合类型支持的操作，还能够获得分数最高（最低）的前N个元素，获得指定分数范围内的元素等与分数有关的操作．虽然集合中的每个元素都是不同的，但是它们的分数却可以相同．

有序集合类型在某些方面和列表类型有些类似：
- 二者都是有序的
- 二者都可以获得某一范围的元素

但两者有着很大的区别，这使得它们的应用场景也是不同的：

- 列表元素是通过链表实现的，获取靠近两端的数据速度极快，而当元素增多后，访问中间数据的速度会较慢，所以它更加适合实现"新鲜事"或者"日志"这样很少访问中间元素的应用．
- 有序集合类型是使用散列表和跳跃表实现的，所以即使读取位于中间部分的数据速度也很快．
- 列表中不能简单的调整某个元素的位置，但是有序集合可以（通过更改这个元素的分数）
- 有序集合要比列表类型更耗费内存

#### 5.1 ZADD 增加元素

```
ZADD key score member [score member...]
```
`ZADD`命令用来向有序集合中加入一个元素和该元素的分数，如果该元素已经存在则会用新的分数替换原有的分数．返回值是新加入到集合中的元素个数（不包括之前已经存在的元素）

```
127.0.0.1:6379> ZADD score 89 tom 67 peter 100 david
(integer) 3
```
我们发现peter的分数有误，实际是76分，可以使用该命令修改：
```
127.0.0.1:6379> ZADD score 76 peter
(integer) 0

```

#### 5.2 ZSCORE 获得元素的分数

```
ZSCORE key member
```
例如：
```
127.0.0.1:6379> ZSCORE score peter
"76"
```
#### 5.3 ZRANGE ZREVRANGE 获得排名在某个范围的元素列表

```
ZRANGE key start stop [WITHSCORES]
ZREVRANGE key start stop [WITHSCORES]
```
`ZRANGE`命令会按照元素分数从小到大的顺序返回索引从start到stop之间的所有元素（包含两端的元素）. `ZREVRANGE`是按照元素分数从大到小的顺序给出结果的．
```
127.0.0.1:6379> ZRANGE score 0 2 
1) "peter"
2) "tom"
3) "david"
127.0.0.1:6379> ZRANGE score 1 -1
1) "tom"
2) "david"
127.0.0.1:6379> ZRANGE score 0 2 WITHSCORES
1) "peter"
2) "76"
3) "tom"
4) "89"
5) "david"
6) "100"
127.0.0.1:6379> ZREVRANGE score 0 2 WITHSCORES
1) "david"
2) "100"
3) "tom"
4) "89"
5) "peter"
6) "76"

```

#### 5.4 ZRANGEBYSCORE　获得指定分数范围的元素

```
ZRANGEBYSCORE key min max [WITHSCORES] [LIMIT offset count]
```
该命令按照元素从小到大的顺序返回分数在min和max之间的元素：
```
127.0.0.1:6379> ZRANGEBYSCORE score 80 100
1) "tom"
2) "david"
127.0.0.1:6379> ZRANGEBYSCORE score 80 100 WITHSCORES
1) "tom"
2) "89"
3) "david"
4) "100"

```
MIN 和 MAX 还支持无穷大，同ZADD命令一样，　-inf和+inf分别表示负无穷和正无穷．

了解SQL语句的读者对LIMIT offset count应该很熟悉，在本命令中LIMIT offset count与SQL中的用法基本相同，即在获得的元素列表的基础上向后偏移offset个元素，并且只获得前count个元素．
```
127.0.0.1:6379> ZADD score 56 jerry 92 wendy 67 yvonne
(integer) 3
127.0.0.1:6379> ZRANGE score 0 -1 WITHSCORES
 1) "jerry"
 2) "56"
 3) "yvonne"
 4) "67"
 5) "peter"
 6) "76"
 7) "tom"
 8) "89"
 9) "wendy"
10) "92"
11) "david"
12) "100"
127.0.0.1:6379> ZRANGEBYSCORE score 60 +inf LIMIT 1 3
1) "peter"
2) "tom"
3) "wendy"
127.0.0.1:6379> ZRANGEBYSCORE score 60 +inf LIMIT 1 3 WITHSCORES
1) "peter"
2) "76"
3) "tom"
4) "89"
5) "wendy"
6) "92"

```

#### 5.5 ZINCRBY 增加某个元素的分数

```
ZINCRBY key increment member
```
ZINCRBY命令可以增加一个元素的分数，返回值是更改后的分数．例如，想给`jerry`加4分：
```
127.0.0.1:6379> ZINCRBY score 4 jerry
"60"
```

#### 5.6 ZREM 删除一个或者多个元素

```
ZREM key member [member ...]
```

ZREM命令返回值是成功删除的元素数量(不包含本来就不存在的元素)
```
127.0.0.1:6379> ZREM score wendy
(integer) 1
```

























