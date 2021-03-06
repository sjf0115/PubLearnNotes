### 1. 问题描述

```
将文本文件中的多行记录转换为逗号分割的一行
```

### 2. 解决方案

#### 2.1 使用awk

先看一下原数据：
```
cat a.txt

1182
1193
1210
1272
1353
1410
1436
1450
```
转换：
```
cat a.txt | awk BEGIN{RS=EOF}'{gsub(/\n/,",");print}'

1182,1193,1210,1272,1353,1410,1436,1450 
```

说明：
```
awk记录分隔符（Record Separator即RS）默认设置为'\n'
我们更改记录分隔符为EOF（文件结束），即把整个文件视为一条记录
通过gsub函数将\n替换成逗号，最后输出
```

#### 2.2 利用sed

转换：
```
cat a.txt | sed ':a ; N;s/\n/,/ ; t a ; '

1182,1193,1210,1272,1353,1410,1436,1450
```
说明：

```
sed默认只按行处理，N可以让其读入下一行，再对\n进行替换，这样就可以将两行并做一行。
但是怎么将所有行并作一行呢？可以采用sed的跳转功能。
:a 在代码开始处设置一个标记a，在代码执行到结尾处时利用跳转命令t a重新跳转到标号a处，重新执行代码，这样就可以递归的将所有行合并成一行。
```

