# -*- coding: UTF-8 -*-
# 文件操作
import json

# ----------------------------------------------------------------------------------------------------------------------
# json操作

# 将Python对象编码成JSON字符串
data = [{'apple': 23, 'bear': 11, 'banana': 54}]
s = json.dumps(data)
print type(s)  # <type 'str'>
print s  # [{"apple": 23, "bear": 11, "banana": 54}]

# 将Python对象编码成JSON字符串并格式化输出
format_str = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
print format_str
'''
[
    {
        "apple": 23,
        "banana": 54,
        "bear": 11
    }
]
'''

# 将已编码的JSON字符串解码为Python对象
data = '[{"apple": 23, "bear": 11, "banana": 54}]'
o = json.loads(data)
print type(o)  # <type 'list'>
print o[0].get('apple', 0)  # 23

# 将Python对象导出到文件中
data = [{'apple': 23, 'bear': 11, 'banana': 54}]
with open("/home/xiaosi/data.json", "w") as f_dump:
    s_dump = json.dump(data, f_dump, ensure_ascii=False)

# 将文件导出为Python对象
with open("/home/xiaosi/data.json", 'r') as f_load:
    ob = json.load(f_load)
print type(ob)  # <type 'list'>
print ob[0].get('banana')  # 54


