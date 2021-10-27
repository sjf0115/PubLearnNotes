---
layout: post
author: sjf0115
title: Hive 字符串相关函数
date: 2017-12-08 20:16:01
tags:
  - Hive

categories: Hive
permalink: hive-common-string-function
---

下面介绍一下常用的Hive字符串相关函数。

### 1. length 字符串长度
语法:
```
length(str | binary)
```
返回值:   
```
int
```
说明:
```
返回字符串长度或者二进制数据字节个数
```
举例：
```
select length('abc') from adv_push_promote_order_user limit 1;
3
```
### 2. reverse 反转字符串
语法:
```
reverse(str)
```
返回值:   
```
string
```
说明:
```
反转字符串
```
举例：
```
select reverse('abc') from adv_push_promote_order_user limit 1;
cba
```
### 3. concat 字符串连接
语法:
```
concat(str1, str2, ... strN)
```
返回值:   
```
string
```
说明:
```
反转字符串
```
举例：
```
select concat('hello', "-", "world") from adv_push_promote_order_user limit 1;
hello-world
```
### 4. concat_ws 使用指定分隔符连接字符串
语法:
```
concat_ws(separator, [string | array(string)]+)
```
返回值:   
```
string
```
说明:
```
使用指定分隔符连接字符串
```
举例：
```
select concat_ws('\t', "Hello", "world") from adv_push_promote_order_user limit 1;
Hello   world
```
### 5. substr substring 字符串子串
语法:
```
substr(str, pos[, len])
substring(str, pos[, len])
```
返回值:   
```
string
```
说明:
```
返回字符串A从pos位置开始的字符串，可以指定长度，如果不指定默认到字符串末尾。下标从1开始。
```
举例：
```
select substr("hello",2) from adv_push_promote_order_user limit 1;
ello
select substr("hello",2,2) from adv_push_promote_order_user limit 1;
el
```
### 6. upper ucase 字符串转大写
语法:
```
upper(str)
ucase(str)
```
返回值:   
```
string
```
说明:
```
字符串转大写
```
举例：
```
select upper("hello") from adv_push_promote_order_user limit 1;
HELLO
select ucase("hello") from adv_push_promote_order_user limit 1;
HELLO
```
### 7. lower lcase 字符串转小写
语法:
```
lower(str)
lcase(str)
```
返回值:   
```
string
```
说明:
```
字符串转小写
```
举例：
```
select lower("HELLO") from adv_push_promote_order_user limit 1;
hello
select lcase("HELLO") from adv_push_promote_order_user limit 1;
hello
```
### 8. instr
语法:
```
instr(string str, string substr)
```
返回值:
```
int
```
说明:
```
返回 substr 在 str 中第一次出现的位置。若任何参数为null返回null，若substr不在str中返回0。str中第一个字符的位置为1。
```

### 8. trim 去掉左右两边空格


### 9. split 字符串分割

语法:
```
split(string str, string pat)
```
返回值:
```
array
```
说明:
```
返回 按照pat字符串分割字符串str，返回分割后的字符串数组。
```
举例：
```

```














....
