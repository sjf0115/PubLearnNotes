### 1. csv文件处理

记录中的字段通常由逗号分隔，但其他分隔符也是比较常见的，例如制表符（制表符分隔值，TSV）、冒号、分号和竖直条等。建议在自己创建的文件中坚持使用逗号作为分隔符，同时保证编写的处理程序能正确处理使用其他分隔符的CSV文件。

备注:
```
有时看起来像分隔符的字符并不是分隔符。通过将字段包含在双引号中，可确保字段中的分隔符只是作为变量值的一部分，不参与分割字段(如...,"Hello, world",...)。
```

Python的csv模块提供了一个CSV读取器和一个CSV写入器。两个对象的第一个参数都是已打开的文本文件句柄(在下面的示例中，使用newline=''选项打开文件，从而避免删除行的操作)。必要时可以通过可选参数delimiter和quotechar，提供默认的分隔符和引用字符。Python还提供了控制转义字符、行终止符等定界符的可选参数。
```Python
with open("somefile.csv", newline='') as infile:
  reader = csv.reader(infile, delimiter=',', quotechar='"')
```
CSV文件的第一条记录通常包含列标题，可能与文件的其余部分有所不同。这只是一个常见的做法，并非CSV格式本身的特性。

CSV读取器提供了一个可以在for循环中使用的迭代器接口。迭代器将下一条记录作为一个字符串字段列表返回。读取器不会将字段转换为任何数值数据类型，另外，除非传递可选参数`skipinitialspace=True`，否则不会删除前导的空白。

如果事先不知道CSV文件的大小，而且文件可能很大，则不宜一次性读取所有记录，而应使用增量的、迭代的、逐行的处理方式：读出一行，处理一行，再获取另一行。

CSV写入器提供`writerow()`和`writerows()`两个函数。`writerow()`将一个字符串或数字序列作为一条记录写入文件。该函数将数字转换成字符串，因此不必担心数值表示的问题。类似地，`writerows()`将字符串或数字序列的列表作为记录集写入文件。

在下面的示例中，使用csv模块从CSV文件中提取Answer.Age列。假设此列肯定存在，但列的索引未知。一旦获得数值，借助statistics模块就能得到年龄的平均值和标准偏差。

首先，打开文件并读取数据：
```Python
with open("demographics.csv", newline='') as infile:
  data = list(csv.reader(infile))
```
检查文件中的第一个记录 data[0] ，它必须包含感兴趣的列标题：
```Python
ageIndex = data[0].index("Answer.Age")
```
最后，访问剩余记录中感兴趣的字段，并计算和显示统计数据：
```Python
ages = [int(row[ageIndex]) for row in data[1:]]
print(statistics.mean(ages), statistics.stdev(ages))
```
csv和statistics模块是底层的、快速而粗糙的工具。在第6章，你将了解如何在更为复杂的项目中使用pandas的数据frame，完成那些比对几列数据进行琐碎的检索要高端得多的任务。

### 2. Json文件处理

需要注意的一点就是某些Python数据类型和结构(比如集合和复数)无法存储在JSON文件中。因此，要在导出到JSON之前，将它们转换为JSON可表示的数据类型。例如，将复数存储为两个double类型的数字组成的数组，将集合存储为一个由集合的各项所组成的数组。

将复杂数据存储到JSON文件中的操作称为JSON序列化，相应的反向操作则称为JSON反序列化。Python通过json模块中的函数，实现JSON序列化和反序列化。

函数|说明
---|---
dump()| 将Python对象导出到文件中
dumps()| 将Python对象编码成JSON字符串
load()| 将文件导出为Python对象
loads()| 将已编码的JSON字符串解码为Python对象

备注:
```
把多个对象存储在一个JSON文件中是一种错误的做法，但如果已有的文件包含多个对象，则可将其以文本的方式读入，进而将文本转换为对象数组（在文本中各个对象之间添加方括号和逗号分隔符），并使用loads()将文本反序列化为对象列表。
```

Example:

以下代码片段实现了将任意（可序列化的）对象按先序列化、后反序列化的顺序进行处理：
```Python
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
```

备注:
```
使用JSON函数需要导入json库：import json。
```
JSON 类型转换到 python 的类型对照表：

JSON|Python
---|---
object|dict
array|list
string|unicode
number (int)|int, long
number (real)|float
true|True
false|False
null|None





来自于:<Python数据科学入门>
