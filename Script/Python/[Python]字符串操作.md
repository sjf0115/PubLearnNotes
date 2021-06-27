字符串是 Python 中最常用的数据类型。我们可以使用引号('或")来创建字符串。
创建字符串很简单，只要为变量分配一个值即可。例如：
```
s = "Hello World"
print s  # Hello World
```
### 1. 大小写转换函数

大小写转换函数返回原始字符串s的一个副本：

函数|说明
---|---
lower()|将所有字符转换为小写
upper()|将所有字符转换为大写
capitalize()|将第一个字符转换为大写，同时将其他所有字符转换为小写

这些函数不会影响非字母字符。大小写转换函数是规范化的一个重要元素。

Example:
```Python
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
```

### 2. 判定函数

判断函数根据字符串s是否属于适当的类而返回True或False：

函数|说明
---|---
islower()|检查所有字母字符是否为小写
isupper()|检查所有字母字符是否为大写
isspace()|检查所有字符是否为空格
isdigit()|检查所有字符是否为范围0～9中的十进制数字
isalpha()|检查所有字符是否为a～z或A～Z范围内的字母字符

使用这些函数，你可以识别有效的单词、非负整数、标点符号等。

Example:
```Python
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
```

### 3. 解码函数

Python有时会将字符串数据表示为原始的二进制数组，而非字符串，尤其是当数据来自外部源（外部文件、数据库或Web）时。Python使用符号b来标识二进制数组。例如:
```Python
# 二进制数组
bin = b"Hello"
# 字符串  
s = "Hello"
print bin[0]
print s[0]
```
`s[0]`和`bin[0]`分别是'H'和72，其中72是字符'H'的ASCII码。

解码函数将二进制数组转换为字符串或反之：

函数|说明
---|---
decode()|将二进制数组转换为字符串
encode()|将字符串转换为二进制数组

许多Python函数都需要将二进制数据转换为字符串，然后再做处理。

### 4. 去除空白函数

字符串处理的第一步是去除不需要的空白(包括换行符和制表符)。

函数|说明
---|---
lstrip()|left strip 在字符串的开始处删除所有空格
rstrip()|right strip 在字符串的结束处删除所有空格
strip()|对整个字符串删除所有空格(不删除字符串内部空格)

经过这些删除操作后，得到的可能会是一个空字符串！

Example:
```Python
ls = " Hello world ".lstrip()
print ls + "," + str(len(ls))  # Hello world ,12

rs = " Hello World ".rstrip()
print rs + "," + str(len(rs))  #  Hello World,12

ss = " Hello World ".strip()
print ss + "," + str(len(ss))  # Hello World,1
```
### 5. 分割函数

字符串通常包含多个标记符，用空格、冒号和逗号这样的分隔符分割。函数split(delim='')使用delim作为分隔符，将字符串s分割为子字符串组成的一个列表。如果未指定分隔符，Python会使用空白字符来分割字符串，并将所有连续的空白合并：
```Python
ss = "Hello World".split()
print ss  # ['Hello', 'World']

ss = "Hello,World".split(",")
print ss  # ['Hello', 'World']
```

### 6. 连接函数

连接函数join(ls)，将字符串列表ls连接在一起，形成一个字符串，并使用特定的对象字符串作为连接符：
```Python
s = ",".join("b")
print s  # b

s = ",".join(["a", "b", "c", "d"])
print s  # a,b,c,d
```

备注:
```
join()函数仅在字符串之间插入连接符，而在第一个字符串前或最后一个字符串后都不插入连接符。
```

### 7. 查找函数

find(needle)函数返回对象字符串中子字符串needle第一次出现的索引值(下标从0开始)，当子字符串不存在时，返回-1。该函数区分大小写。
```
index = "Hello World".find("o")
print index  # 4
```



来自于<Python数据科学入门>
