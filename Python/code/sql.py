# -*- coding: UTF-8 -*-
# 数据库操作
import pymysql
import pymongo

# ----------------------------------------------------------------------------------------------------------------------
# mysql

# 连接数据库
conn = pymysql.connect(host="localhost", port=3306, user="root", passwd="root", db="test")
cur = conn.cursor()

# 查询
query = '''
    SELECT first_name, last_name
    FROM People
    ORDER BY dob
    LIMIT 3
'''
n_rows = cur.execute(query)
print n_rows  # 3

results = list(cur.fetchall())
print results  # [('gztAQV', 'aLhko'), ('ZXMtHd', 'cgwjI'), ('yHwDRF', 'NgBkY')]

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

# ----------------------------------------------------------------------------------------------------------------------
# mongodb

# 使用默认的初始化方式
client1 = pymongo.MongoClient()
# 指定主机和端口号
client2 = pymongo.MongoClient("localhost", 27017)
# 用URI方式指定主机和端口号
client3 = pymongo.MongoClient("mongodb://localhost:27017/")

# 创建并选择活动数据库test_db
db = client2["test_db"]

# 创建并选择活动集合
people = db.people

# 插入
# person1 = {"name": "John", "dob": "2017-11-24"}
# person_id1 = people.insert_one(person1).inserted_id
# print person_id1  # 5a1d4ba92317d71bb605f8ce
#
# person2 = {"_id": "XVT162", "name": "Jane", "dob": "2017-11-27"}
# person_id2 = people.insert_one(person2).inserted_id
# print person_id2  # XVT162
#
# persons = [{"name": "Lucy", "dob": "2017-11-12"}, {"name": "Tom"}]
# result = people.insert_many(persons)
# print result.inserted_ids  # [ObjectId('5a1d4c832317d71c2c4e284f'), ObjectId('5a1d4c832317d71c2c4e2850')]


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

# 聚合

count = people.count()
print count  # 5

count = people.find({"dob": "2017-11-27"}).count()
print count  # 1

people_list = list(people.find().sort("dob"))
print people_list  # [{u'_id': ObjectId('5a1d4c832317d71c2c4e2850'), u'name': u'Tom'}, {u'dob': u'2017-11-12', u'_id': ObjectId('5a1d4c832317d71c2c4e284f'), u'name': u'Lucy'}, {u'dob': u'2017-11-24', u'_id': ObjectId('5a1d4ba92317d71bb605f8ce'), u'name': u'John'}, {u'dob': u'2017-11-24', u'_id': ObjectId('5a1d4c7c2317d71c1bbeac4b'), u'name': u'John'}, {u'dob': u'2017-11-27', u'_id': u'XVT162', u'name': u'Jane'}]

# 删除
result = people.delete_many({"dob": "2017-11-27"})
print result.deleted_count  # 1


