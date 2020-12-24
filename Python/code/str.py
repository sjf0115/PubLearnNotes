# -*- coding: UTF-8 -*-
# 字符串操作

s = "Hello World"
print s  # Hello World

# 转为大写
us = s.upper()
print us  # HELLO WORLD

# 转为小写
ls = s.lower()
print ls  # hello world

# 首字母大写 其余小写
cs = s.capitalize()
print cs  # Hello world

# 是否为大写
ius = "HELLO".isupper()
print ius  # True

# 是否为小写
ils = "hello".islower()
print ils  # True

# 是否为空格
iss = " ".isspace()
print iss  # True

# 是否为范围0～9中的十进制数字
ids = "232".isdigit()
print ids  # True

# 是否为a～z或A～Z范围内的字母字符
ias = "a2".isalpha()
print ias  # False

# ---------------------------------------------------------------------------
# 二进制数组
b = b"Hello"
# 字符串
s = "Hello"

print b[0]
print s[0]

# ----------------------------------------------------------------------------

ls = " Hello world ".lstrip()
print ls + "," + str(len(ls))  # Hello world ,12

rs = " Hello World ".rstrip()
print rs + "," + str(len(rs))  #  Hello World,12

ss = " Hello World ".strip()
print ss + "," + str(len(ss))  # Hello World,1

# -----------------------------------------------------------------------------

ss = "Hello World".split()
print ss  # ['Hello', 'World']

ss = "Hello,World".split(",")
print ss  # ['Hello', 'World']

s = ",".join("b")
print s  # b

s = ",".join(["a", "b", "c", "d"])
print s  # a,b,c,d

index = "Hello World".find("o")
print index  # 4

seq = ["alpha", "bravo", "charlie", "delta"]
d = dict(enumerate(seq))
print d  # {0: 'alpha', 1: 'bravo', 2: 'charlie', 3: 'delta'}

kseq = ["apple", "bear", "banana"]
vseq = [12, 21, 3]
d = dict(zip(kseq, vseq))
print d  # {'apple': 12, 'bear': 21, 'banana': 3}

myList = [1, 2, 3]
list = [x**2 for x in myList]
print list

from collections import Counter

phrase = "a boy eat a banana"
cntr = Counter(phrase.split())
print cntr.most_common()  # [('a', 2), ('boy', 1), ('eat', 1), ('banana', 1)]