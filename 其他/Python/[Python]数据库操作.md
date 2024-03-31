### 1. MySQL

Python使用数据库驱动模块与MySQL通信。诸如pymysql等许多数据库驱动都是免费的。这里我们将使用pymysql，它是Anaconda的一部分。驱动程序经过激活后与数据库服务器相连，然后将Python的函数调用转换为数据库查询，反过来，将数据库结果转换为Python数据结构。

`connect()`函数需要以下信息：数据库(名称)、数据库服务器的位置(主机和端口号)和数据库用户(名称和密码)。如果数据库成功连接，则返回连接标识符。接下来，创建与数据库连接相关联的数据库游标：
```Python
import pymysql

# 连接数据库
conn = pymysql.connect(host="localhost", port=3306, user="root", passwd="root", db="test")
cur = conn.cursor()
```

备注:
```
使用pymysql需要导入pymysql库：import pymysql。
```


游标的`execute()`函数向数据服务器提交要执行的查询命令，并返回受影响的行数(如果查询是非破坏性的，则返回零)。与命令行MySQL查询不同，pymysql查询语句不需要在结尾加上分号。
```Python
# 查询
query = '''
    SELECT first_name, last_name
    FROM People
    ORDER BY dob
    LIMIT 3
'''
n_rows = cur.execute(query)
print n_rows  # 3
```
如果提交非破坏性查询(比如SELECT)，需要使用游标函数`fetchall()`获取所有匹配的记录。该函数返回一个生成器，可以将其转换为列字段的元组构成的列表：
```Python
results = list(cur.fetchall())
print results  # [('gztAQV', 'aLhko'), ('ZXMtHd', 'cgwjI'), ('yHwDRF', 'NgBkY')]
```
如果查询是破坏性的(例如UPDATE、DELETE或INSERT)，则必须执行commit操作:
```Python
# 修改
update_query = '''
    UPDATE People
    SET first_name = 'yoona'
    WHERE last_name = 'aLhko'
'''
n_rows = cur.execute(update_query)
print n_rows  # 1
conn.commit()

select_query = '''
    SELECT first_name, last_name
    FROM People
    WHERE last_name = 'aLhko'
'''
cur.execute(select_query)
results = list(cur.fetchall())
print results  # [('yoona', 'aLhko')]
```

备注:
```
提供commit()函数的是连接本身(conn)，而不是游标(cur)。
```

### 2. MongoDB

在Python中，我们用`pymongo`模块中`MongoClient`类的实例来实现MongoDB客户端。首先安装`pymongo`模块(ubuntu15.10):
```
sudo pip install pymongo
```
下面就可以创建一个无参数的客户端(适用于典型的安装了本地服务器的情况)，也可以用服务器的主机名和端口号作为参数创建客户端，或使用服务器的统一资源标识符(URI)作为参数创建客户端：
```Python
# 使用默认的初始化方式
client1 = pymongo.MongoClient()
# 指定主机和端口号
client2 = pymongo.MongoClient("localhost", 27017)
# 用URI方式指定主机和端口号
client3 = pymongo.MongoClient("mongodb://localhost:27017/")
```

客户一旦端建立了与数据库服务器的连接，就可以选择当前激活的数据库，进而选择激活的集合。可以使用面向对象(".")或字典样式的符号。如果所选的数据库或集合不存在，服务器会立即创建它们：
```Python
# 创建并选择活动数据库的两种方法
db = client1.test_db
db = client1["test_db"]

# 创建并选择活动集合的两种方法
people = db.people
people = db["people"]
```

pymongo模块用字典变量来表示MongoDB文档。表示对象的每个字典必须具有_id这个键。如果该键不存在，服务器会自动生成它。

集合对象提供用于在文档集合中插入、搜索、删除、更新、替换和聚合文档以及创建索引的功能。

函数`insert_one(doc)`和`insert_many(docs)`将文档或文档列表插入集合。它们分别返回对象`InsertOneResult`或`InsertManyResult`，这两个对象分别提供`inserted_id`和`inserted_ids`属性。当文档没有提供明确的唯一键时，就需要使用这两个属性值作为文档的唯一键。如果指定了_id键，就是用该值作为唯一键：
```Python
# 插入
person1 = {"name": "John", "dob": "2017-11-24"}
person_id1 = people.insert_one(person1).inserted_id
print person_id1  # 5a1d4ba92317d71bb605f8ce

person2 = {"_id": "XVT162", "name": "Jane", "dob": "2017-11-27"}
person_id2 = people.insert_one(person2).inserted_id
print person_id2  # XVT162

persons = [{"name": "Lucy", "dob": "2017-11-12"}, {"name": "Tom"}]
result = people.insert_many(persons)
print result.inserted_ids  # [ObjectId('5a1d4c832317d71c2c4e284f'), ObjectId('5a1d4c832317d71c2c4e2850')]
```

函数`find_one()`和`find()`分别给出匹配可选属性的一个或多个文档，其中`find_one()`返回文档，而`find()`返回一个游标(一个生成器)，可以使用`list()`函数将该游标转换为列表，或者在for循环中将其用作迭代器。如果将字典作为参数传递给这些函数中的任意一个，函数将给出与字典的所有键值相等的文档：
```Python
# 查找

everyone = people.find()
print list(everyone)  # [{u'dob': u'2017-11-24', u'_id': ObjectId('5a1d4ba92317d71bb605f8ce'), u'name': u'John'}, {u'dob': u'2017-11-27', u'_id': u'XVT162', u'name': u'Jane'}, {u'dob': u'2017-11-24', u'_id': ObjectId('5a1d4c7c2317d71c1bbeac4b'), u'name': u'John'}, {u'dob': u'2017-11-12', u'_id': ObjectId('5a1d4c832317d71c2c4e284f'), u'name': u'Lucy'}, {u'_id': ObjectId('5a1d4c832317d71c2c4e2850'), u'name': u'Tom'}]

print list(people.find({"dob": "2017-11-27"}))  # [{u'dob': u'2017-11-27', u'_id': u'XVT162', u'name': u'Jane'}]

one_people = people.find_one()
print one_people  # {u'dob': u'2017-11-24', u'_id': ObjectId('5a1d4ba92317d71bb605f8ce'), u'name': u'John'}

one_people = people.find_one({"name": "Lucy"})
print one_people  # {u'dob': u'2017-11-12', u'_id': ObjectId('5a1d4c832317d71c2c4e284f'), u'name': u'Lucy'}

one_people = people.find_one({"_id": "XVT162"})
print one_people  # {u'dob': u'2017-11-27', u'_id': u'XVT162', u'name': u'Jane'}
```

下面介绍几个实现数据聚合和排序的分组和排序函数。函数`sort()`对查询的结果进行排序。当以无参数的方式调用它时，该函数按键_id的升序进行排序。函数`count()`返回查询结果中或整个集合中的文档数量：
```Python
# 聚合

count = people.count()
print count  # 5

count = people.find({"dob": "2017-11-27"}).count()
print count  # 1

people_list = list(people.find().sort("dob"))
print people_list  # [{u'_id': ObjectId('5a1d4c832317d71c2c4e2850'), u'name': u'Tom'}, {u'dob': u'2017-11-12', u'_id': ObjectId('5a1d4c832317d71c2c4e284f'), u'name': u'Lucy'}, {u'dob': u'2017-11-24', u'_id': ObjectId('5a1d4ba92317d71bb605f8ce'), u'name': u'John'}, {u'dob': u'2017-11-24', u'_id': ObjectId('5a1d4c7c2317d71c1bbeac4b'), u'name': u'John'}, {u'dob': u'2017-11-27', u'_id': u'XVT162', u'name': u'Jane'}]
```
函数`delete_one(doc)`和`delete_many(docs)`从集合中删除字典doc所标识的一个或多个文档。如果要在删除所有文档的同时保留集合，需使用空字典作为参数调用函数`delete_many({})`：
```Python
# 删除
result = people.delete_many({"dob": "2017-11-27"})
print result.deleted_count  # 1
```











来自于:Python数据科学入门
