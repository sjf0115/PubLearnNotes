Shell中的 test 命令用于检查某个条件是否成立，它可以进行数值、字符和文件三个方面的测试。

### 1. 数值

参数|说明
---|---
-eq	|等于则为真
-ne	|不等于则为真
-gt	|大于则为真
-ge	|大于等于则为真
-lt	|小于则为真
-le	|小于等于则为真


Example：
```
num1=100
num2=100
if test $[num1] -eq $[num2]
then
    echo '两个数相等'
else
    echo '两个数不相等'
fi
# 两个数相等
```

### 2. 字符串


参数|说明
---|---
=|等于则为真
!=	|不相等则为真
-z 字符串	|字符串的长度为零则为真
-n 字符串	|字符串的长度不为零则为真


Example：
```
str1="2016-11-21"
str2="2016-11-22"
if test ${str1} = ${str2}
then
    echo '两个日期相同'
else
    echo '两个日期不相同'
fi
# 两个日期不相同
```

==备注==

如果上面的使用方法中，字符串中有空格，则会报错：
```
str1="2016-11-22 12:34:21"
str2="2016-11-22 12:34:21"
if test ${str1} = ${str2}
then
    echo '两个日期相同'
else
    echo '两个日期不相同'
fi
```
输出：
```
两个日期不相同
/home/xiaosi/code/openDiary/BaseOperation/src/main/sh/sh_test.sh: 第 6 行: test: 参数太多
```

解决方案：
```
str1="2016-11-22 12:34:21"
str2="2016-11-22 12:34:21"
if test "${str1}" = "${str2}"
then
    echo '两个日期相同'
else
    echo '两个日期不相同'
fi
```
输出：
```
两个日期相同
```
### 3. 文件


参数	|说明
---|---
-e 文件名	|如果文件存在则为真
-r 文件名	|如果文件存在且可读则为真
-w 文件名	|如果文件存在且可写则为真
-x 文件名	|如果文件存在且可执行则为真
-s 文件名	|如果文件存在且至少有一个字符则为真
-d 文件名	|如果文件存在且为目录则为真
-f 文件名	|如果文件存在且为普通文件则为真
-c 文件名	|如果文件存在且为字符型特殊文件则为真
-b 文件名	|如果文件存在且为块特殊文件则为真


Example：
```
if test -e /home/xiaosi/error.txt
then
    echo '文件存在'
else
    echo '文件不存在'
fi
# 文件存在
if test -r /home/xiaosi/error.txt
then
    echo '文件可读'
else
    echo '文件不可读'
fi
# 文件可读
if test -s /home/xiaosi/error.txt
then
    echo '文件不为空'
else
    echo '文件为空'
fi
# 文件为空
if test -d /home/xiaosi
then
    echo '文件为目录'
else
    echo '文件不为目录'
fi
# 文件为目录
```

### 4. 逻辑操作

Shell还提供了与( -a )、或( -o )、非( ! )三个逻辑操作符用于将测试条件连接起来，其优先级为："!"最高，"-a"次之，"-o"最低。

Example：
```
str="2016-11-21"
if test "${str}" = "2016-11-21" -a -s /home/xiaosi/error.txt
then
    echo '日期正确 并且 文件不为空'
else
    echo '日期错误 或者 文件为空'
fi
# 日期错误 或者 文件为空
```
