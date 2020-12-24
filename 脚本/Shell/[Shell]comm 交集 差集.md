### 1. 简介

comm命令可以用于两个文件之间的比较，它有一些选项可以用来调整输出，以便执行交集、求差、以及差集操作。

- 交集：打印出两个文件所共有的行。
- 求差：打印出指定文件所包含的且不相同的行。
- 差集：打印出包含在一个文件中，但不包含在其他指定文件中的行。



### 2. 语法
```
comm (选项) (参数)
```

### 3. 选项

- -1：不显示只在第一个文件出现的内容
- -2：不显示只在第二个文件中出现的内容
- -3：不显示同时在两个文件中都出现的内容


### 4. 参数

- 文件1：指定要比较的第一个有序文件
- 文件2：指定要比较的第二个有序文件



### 5. Example
原数据如下：
```
xiaosi@yoona:~/company/sh$ cat a.txt
a
b
d
e
f
g
h
l
v
xiaosi@yoona:~/company/sh$ cat b.txt
b
d
g
l
n
r
t
y
```

#### 5.1 无选项
输出的第一列只包含在a.txt中出现的行，第二列包含在b.txt中出现的行，第三列同时包含在a.txt和b.txt中的行。各列是以制表符（\t）作为定界符。
```
xiaosi@yoona:~/company/sh$ comm a.txt b.txt
a
            b
            d
e
f
		    g
h
		    l
	 n
	 r
	 t
v
	 y
```
#### 5.2 -1选项
可以理解为-1删除第一列，-2删除第二列：不显示只在第一个文件出现的内容，输出的第一列只包含在b.txt中出现的行，第二列同时包含在a.txt和b.txt中的行
```
xiaosi@Qunar:~/company/sh$ comm -1 a.txt b.txt
	            b
	            d
	            g
	            l
n
r
t
y
```

#### 5.3 交集
第三列就是交集的内容，只需删除第一列和第二列内容即可
```
xiaosi@yoona:~/company/sh$ comm -1 -2 a.txt b.txt
b
d
g
l
```
#### 5.4 求差
打印出两个文件中不相同的行，需要删除第三列，sed 's/^\t//' 是将制表符（\t）删除，以便把两列合并成一列。
```
xiaosi@yoona:~/company/sh$ comm -3 a.txt b.txt
a
e
f
h
	           n
	           r
	           t
v
	           y
xiaosi@yoona:~/company/sh$ comm -3 a.txt b.txt | sed 's/^\t//'
a
e
f
h
n
r
t
v
y
```

#### 5.5 差集

a.txt的差集
```
xiaosi@yoona:~/company/sh$ comm a.txt b.txt -2 -3
a
e
f
h
v
```
b.txt差集
```
xiaosi@yoona:~/company/sh$ comm a.txt b.txt -1 -3
n
r
t
y
```
