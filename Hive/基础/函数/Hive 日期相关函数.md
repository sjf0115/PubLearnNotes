---
layout: post
author: sjf0115
title: Hive 日期相关函数
date: 2017-12-08 19:16:01
tags:
  - Hive

categories: Hive
permalink: hive-common-date-function
---

下面介绍一下常用的 Hive 日期处理相关函数。

### 1. to_date 日期时间转日期函数

语法:
```
to_date(string timestamp)
```
返回值:   
```
string
```
说明:
```
返回日期时间字段中的日期部分。
```
举例：
```
select to_date('2011-12-08 10:03:01');
2011-12-08
```

### 2. year 日期转年函数

语法:   
```
year(string date)
```
返回值:
```
int
```
说明:
```
返回日期中的年。
```
举例：
```
select year('2011-12-08 10:03:01');
2011
```

### 3. month 日期转月函数

语法:
```
month (string date)
```
返回值:
```
int
```
说明:
```
返回日期中的月份。
```
举例：
```
select month('2011-12-08 10:03:01');
12
```

### 4. day 日期转天函数

语法:
```
day (string date)
```
返回值:
```
int
```
说明:
```
返回日期中的天
```
举例：
```
select day('2011-12-08 10:03:01');
```

### 5. hour 日期转小时函数

语法:
```
hour (string date)
```
返回值:
```
int
```
说明:
```
返回日期中的小时。
```
举例：
```
select hour('2011-12-08 10:03:01');
10
```

### 6. minute 日期转分钟函数

语法:
```
minute (string date)
```
返回值:
```
int
```
说明:
```
返回日期中的分钟。
```
举例：
```
select minute('2011-12-08 10:03:01');
3
```

### 7. second 日期转秒函数

语法:
```
second (string date)
```
返回值:
```
int
```
说明:
```
返回日期中的秒。
```
举例：
```
select second('2011-12-08 10:03:01');
1
```

### 8. weekofyear 日期转周函数

语法:   
```
weekofyear (string date)
```
返回值:
```
int
```
说明:
```
返回日期在当前的周数。
```
举例：
```
select weekofyear('2011-12-08 10:03:01');
49
```

### 9. datediff 日期比较函数

语法:   
```
datediff(string enddate, string startdate)
```
返回值:
```
int
```
说明:
```
返回结束日期减去开始日期的天数。
```
举例：
```
select datediff('2012-12-08','2012-05-09');
213
select datediff("2016-10-28 07:23:45", "2016-10-20 12:23:10");
8
```

### 10. date_add 日期增加函数

语法:   
```
date_add(string startdate, int days)
```
返回值:
```
string
```
说明:
```
返回开始日期startdate增加days天后的日期。
```
举例：
```
select date_add('2012-12-08',10);
2012-12-18
```

### 11. date_sub 日期减少函数

语法:   
```
date_sub (string startdate, int days)
```
返回值:
```
string
```
说明:
```
返回开始日期startdate减少days天后的日期。
```
举例：
```
select date_sub('2012-12-08',10);
2012-11-28
```

### 12. from_unixtime 日期函数UNIX时间戳转日期函数

语法:
```
from_unixtime(bigint unixtime[, string format])
```
返回值:
```
string
```
说明:
```
转化UNIX时间戳（从1970-01-01 00:00:00 UTC到指定时间的秒数）到当前时区的时间格式
```
举例：
```
select from_unixtime(1323308943,'yyyyMMdd');
20111208
```

### 13. unix_timestamp 获取当前UNIX时间戳函数

语法:   
```
unix_timestamp()
```
返回值:   
```
bigint
```
说明:
```
获得当前时区的UNIX时间戳
```
举例：
```
select unix_timestamp();
1323309615
```

### 14. unix_timestamp 日期转UNIX时间戳函数

语法:
```
unix_timestamp(string date)
```
返回值:   
```
bigint
```
说明:
```
转换格式为“yyyy-MM-dd HH:mm:ss“的日期到UNIX时间戳。如果转化失败，则返回0。
```
举例：
```
select unix_timestamp('2011-12-07 13:01:03');
1323234063
```

### 15. unix_timestamp 指定格式日期转UNIX时间戳函数

语法:   
```
unix_timestamp(string date, string pattern)
```
返回值:   
```
bigint
```
说明:
```
转换pattern格式的日期到UNIX时间戳。如果转化失败，则返回0。
```
举例：
```
select unix_timestamp('20111207 13:01:03','yyyyMMdd HH:mm:ss');
1323234063
```

### 16. next_day 下周几的具体日期

语法：
```
next_day(string date, string week)
```
返回值：
```
string
```
说明：
```
返回大于指定日期并且与week相匹配的第一个日期。实质上是指下周几的具体日期。week可以是Mo, tue, FRIDAY等。
```
举例：
```
select next_day("2016-10-31", 'FRIDAY');
2016-11-04
```
