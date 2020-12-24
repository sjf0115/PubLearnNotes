### 1. 概述

所谓的CSV(逗号分隔值)格式是电子表格`spreadsheets`和数据库最常用的导入和导出格式。但是没有一种'CSV标准'，所以格式由许多读取和写入的应用程序进行操作定义。缺乏标准意味着不同应用程序生成和使用的数据通常存在微妙的差异。这些差异可能使处理来自多个源的CSV文件变得非常烦人。尽管分隔符和引用字符不同，但是整体格式类似，可以编写一个可以有效地操纵这些数据的单个模块，隐藏从程序员读取和写入数据的细节。

csv模块实现了以CSV格式读取和写入表格数据的类。 它允许程序员在不知道Excel中使用的CSV格式的精确细节的情况下说:"以Excel的格式写入数据＂或"从Excel生成的文件中读取数据"。程序员还可以描述其他应用程序理解的CSV格式，或者定义自己的专用CSV格式。

csv模块的`reader`和`writer`对象可以读写数据。程序员还可以使用`DictReader`和`DictWriter`类读取和写入数据字典。

### 2. 模块函数

csv模块定义了以下函数：

#### 2.1 reader

语法格式:
```python
csv.reader(csvfile, dialect='excel', **fmtparams)
```
该函数返回一个读取对象，该对象将在给定的`csvfile`对象上进行迭代读取。
- `csvfile`必须是支持迭代器协议(Iterator)的任何对象，并且在每次调用`next()`方法时返回一个字符串，可以是文件对象和列表对象。如果`csvfile`是一个文件对象，有所不同的是必须使用'b'标签来打开。
- `dialect`是可选参数，用于定义一组参数来指定一种特定的CSV方言(dialect)。它可能是`Dialect`类的子类的实例或者由`list_dialects()`函数返回的一个字符串。
- `fmtparams`是可选参数，用来来覆盖当前方言中的各个格式参数(override individual formatting parameters in the current dialect)。 有关方言和格式参数的完整详细信息，请参阅方言和格式参数部分。

从csv文件读取的每行都作为字符串列表返回。 不执行自动数据类型转换。

Example:
```python
import csv
with open('eggs.csv', 'rb') as csvfile:
  spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
  for row in spamreader:
    print ', '.join(row)
```

#### 2.2 writer

Example:
```python
import csv
with open('eggs.csv', 'wb') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=' ',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    spamwriter.writerow(['Spam'] * 5 + ['Baked Beans'])
    spamwriter.writerow(['Spam', 'Lovely Spam', 'Wonderful Spam'])
```
### 3. 方言与格式参数

### 4. Reader

### 5. Writer

### 6. Examples

(1) 简单读取CSV文件:
```python
import csv
with open('/home/xiaosi/data/test/sample.csv', 'rb') as f:
    reader = csv.reader(f)
    for row in reader:
        print row
```

(2) 以可选格式读取文件：
```python
import csv
with open('/home/xiaosi/data/test/sample2.csv', 'rb') as f:
    reader = csv.reader(f, delimiter=':', quoting=csv.QUOTE_NONE)
    for row in reader:
        print row
```
(3) 简单写入CSV文件:
```python
import csv
data = [
    ('Bob', 89),
    ('Kim', 78)
]
with open('/home/xiaosi/data/test/sample3.csv', 'wb') as f:
    writer = csv.writer(f)
    writer.writerows(data)

# Bob,89
# Kim,78
```
(4) 注册新方言：
```python
import csv
csv.register_dialect('unixpwd', delimiter=':', quoting=csv.QUOTE_NONE)
with open('/home/xiaosi/data/test/shadow.csv', 'rb') as f:
    reader = csv.reader(f, 'unixpwd')
    for row in reader:
        print row
```
输入:
```
xiaosi:123:16946:0:99999:7:::
```
输出:
```
['xiaosi', '123', '16946', '0', '99999', '7', '', '', '']
```
(5) reader高级特性-捕捉和报告错误：
```python
import csv, sys
filename = '/home/xiaosi/data/test/sample.csv'
with open(filename, 'rb') as f:
    reader = csv.reader(f)
    try:
        for row in reader:
            print row
    except csv.Error as e:
        sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))
```

(6) 而当模块不直接支持解析字符串时，可以很容易地完成：
```python
import csv
for row in csv.reader(['one,two,three']):
    print row
```


原文：https://docs.python.org/2/library/csv.html#module-csv
