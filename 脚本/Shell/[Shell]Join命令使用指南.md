### 1. 用途

Linux join命令用于将两个文件中，指定栏位内容相同的行连接起来。找出两个文件中，指定栏位内容相同的行，并加以合并，再输出到标准输出设备。

### 2. 语法
```
join [OPTION]... FILE1 FILE2
```
### 3. 参数

```
      -a FILENUM
              also  print unpairable lines from file FILENUM, where FILENUM is
              1 or 2, corresponding to FILE1 or FILE2
       -e EMPTY
              replace missing input fields with EMPTY
       -i, --ignore-case
              ignore differences in case when comparing fields
       -j FIELD
              equivalent to '-1 FIELD -2 FIELD'
       -o FORMAT
              obey FORMAT while constructing output line
        -t CHAR
              use CHAR as input and output field separator
       -v FILENUM
              like -a FILENUM, but suppress joined output lines
       -1 FIELD
              join on this FIELD of file 1
       -2 FIELD
              join on this FIELD of file 2
       --check-order
              check that the input is correctly  sorted,  even  if  all  input
              lines are pairable
       --nocheck-order
              do not check that the input is correctly sorted
```
假设我们有两个文件：a.txt b.txt

a.txt
```
xiaosi@yoona:~/test$ cat a.txt
aa	1	2
cc	2	3
gg	4	6
hh	3	3
b.txt

xiaosi@yoona:~/test$ cat b.txt
aa	2	1
bb	8	2
cc	4	4
dd	5	6
ff	2	3
```
#### 3.1 -a FileNum

FileNum 指定哪个文件 （FileNum 只能取值1或者2，1表示 File1，2 表示 File2）

##### 3.1.1 -a 1
```
-a 1 等价于 左连接
```
如果左文件的某行在右文件中没有匹配行，则在结果集行中只显示左文件行中数据
```
xiaosi@yoona:~/test$ join -a 1 a.txt b.txt
aa 1 2 2 1
cc 2 3 4 4
gg 4 6
hh 3 3
```
##### 3.1.2 -a 2
```
-a 2 等价于 右连接
```
如果右文件的某行在左文件中没有匹配行，则在结果集行中只显示右文件行中数据
```
xiaosi@yoona:~/test$ join -a 2 a.txt b.txt
aa 1 2 2 1
bb 8 2
cc 2 3 4 4
dd 5 6
ff 2 3
```
##### 3.1.3 无-a 参数
```
无-a 参数 等价于 内连接
```
```
xiaosi@yoona:~/test$ join a.txt b.txt
aa 1 2 2 1
cc 2 3 4 4
```

#### 3.2 -j 指定匹配列

-j选项指定了两个文件具体按哪一列进行匹配
```
xiaosi@yoona:~/test$ join -j 1 a.txt b.txt
aa 1 2 2 1
cc 2 3 4 4
```
-j 1 指定两个文件按第一列进行匹配，等同于 join a.txt b.txt。
```
xiaosi@yoona:~/test$ join -j 2 c.txt d.txt
2 cc 3 aa 1
2 cc 3 ff 3
4 gg 6 cc 4
```
-j 2指定两个文件按第二列进行匹配。

==备注==

c.txt 为 a.txt按第二列排序后的结果
```
sort -n -k 2 a.txt > c.txt
```
d.txt 为 b.txt按第二列排序后的结果
```
sort -n -k 2 b.txt > d.txt
```
如果指定哪一列进行连接，要根据那一列进行排序，再进行连接。


#### 3.3 -v FileNum 反向匹配输出

输出指定文件不匹配的行，FileNum取值1或者2，1表示第一个文件，2表示第二个文件。
```
xiaosi@yoona:~/test$ join -v 1 a.txt b.txt 
gg 4 6
hh 3 3
```
-v 1 表示输出第一个文件中不匹配的行
```
xiaosi@yoona:~/test$ join -v 2 a.txt b.txt
bb 8 2
dd 5 6
ff 2 3
```
-v 2 表示输出第二个文件中不匹配的行


#### 3.4 -o 格式化输出

格式化输出，指定具体哪一列输出
```
xiaosi@yoona:~/test$ join -o 1.1 1.2 2.2  a.txt b.txt
aa 1 2
cc 2 4
```
上面代码中表示输出第一个文件的第一列，第二列以及第二个文件的第二列
