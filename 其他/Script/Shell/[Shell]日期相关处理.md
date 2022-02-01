```
xiaosi@yoona:~/company/sh$ echo `date +%Y-%m-%d`
2016-05-30
xiaosi@Qunar:~/company/sh$ echo `date +'%Y-%m-%d %H:%M:%S'`
2016-05-30 17:02:37
```

当date +%Y%m%d没有时分秒的情况下，不需要用''将格式包含起来。但是增加时分秒后，如果还这样子用 date +%Y%m%d %H:%M:%S则会报错，会将%H:%M:%S看成是额外的参数。如果日期与时间有符号连接起来，则不会报错：%Y%m%d-%H:%M:%S。出现错误的主要原因是中间出现空格，使程序误判。所以得出的经验就是：最好将格式用引号括起来。可以是单引号，也可以是双引号。根据shell变量定义的情况来。

### 1. 当前时间的前N天
```
xiaosi@yoona:~$ num=1
xiaosi@yoona:~$ before_n_date=`date +'%Y%m%d' -d "${num} days ago"`
xiaosi@yoona:~$ echo ${before_n_date}
20161221
xiaosi@yoona:~$ num=2
xiaosi@yoona:~$ before_n_date=`date +'%Y%m%d' -d "${num} days ago"`
xiaosi@yoona:~$ echo ${before_n_date}
20161220
```

### 2. 指定日期前一天
```
xiaosi@yoona:~$ exec_date=20161221
xiaosi@yoona:~$ before_date=`date -d"yesterday ${exec_date}" +%Y%m%d`
xiaosi@yoona:~$ echo ${before_date}
20161220
```

### 3. 指定日期的前N天
```
xiaosi@yoona:~$ exec_date=20161221
xiaosi@yoona:~$ num=2
xiaosi@yoona:~$ before_n_date=`date -d"${num} day ago ${exec_date}" +%Y%m%d`
xiaosi@yoona:~$ echo ${before_n_date}
20161219
xiaosi@yoona:~$ num=3
xiaosi@yoona:~$ before_n_date=`date -d"${num} day ago ${exec_date}" +%Y%m%d`
xiaosi@yoona:~$ echo ${before_n_date}
20161218
```
### 4. 格式化日期
```
xiaosi@yoona:~$ exec_date=2016-12-21
xiaosi@yoona:~$ format_date=`date +'%Y%m%d' -d "${exec_date}"`
xiaosi@yoona:~$ echo ${format_date}
20161221
xiaosi@yoona:~$ exec_date=20161221
xiaosi@yoona:~$ format_date=`date +'%Y-%m-%d' -d "${exec_date}"`
xiaosi@yoona:~$ echo ${format_date}
2016-12-21
```

### 5. 指定开始日期与结束日期
```
# 开始日期
if [ -n "$1" ]
then
    begin_date=`date +"%Y%m%d" -d "$1"`
else
    begin_date=`date +'%Y%m%d' -d "1 days ago"`
fi
# 截止日期
if [ -n "$2" ]
then
    end_date=`date +"%Y%m%d" -d "$2"`
else
    end_date=`date +'%Y%m%d' -d "1 days ago"`
fi
beg_s=`date -d "${begin_date}" +%s`在当前日期上添加10天：

date -d "10 day" +"%Y %m %d"
在当前日期上减去10天

date -d "-10 day" +"%Y %m %d"
在当前日期上添加两个月：

date -d "2 month" +"%Y %m %d"
在当前日期上减去两个月

date -d "-2 month" +"%Y %m %d"
在当前日期上加上1年：

date -d "1 year" +"%Y %m %d"
在当前日期上减去1年：

date -d "-1 year" +"%Y %m %d"
在当前日期上添加1年零一个月零一天：

date -d "1 year 1 month 1 day" +"%Y %m %d"
end_s=`date -d "${end_date}" +%s`
while [ "$beg_s" -le "$end_s" ] ;do
        format_date=`date -d "@$beg_s" +"%Y%m%d"`
        echo ${format_date}
        beg_s=$((beg_s+86400))
done
```
测试：
```
xiaosi@yoona:~$ sh date.sh 20161210 20161210
20161210
xiaosi@yoona:~$ sh date.sh 20161210 20161214
20161210
20161211
20161212
20161213
20161214
```
或者
```
if [[ "$1" != "" ]]
then
    start_date=`date +'%Y%m%d' -d "$1"`
else
    start_date=`date +'%Y%m%d' -d '1 days ago'`
fi

if [[ "$2" != "" ]]
then
    end_date=`date +'%Y%m%d' -d "$2"`
else
    end_date=`date +'%Y%m%d' -d '1 days ago'`
fi

while [[ ${start_date} -le ${end_date} ]];
do
    day=`date +'%Y%m%d' -d "${start_date}"`
    echo ${day}
    start_date=`date +'%Y%m%d' -d "${start_date} +1 days"`
done
```

### 6. 开始时间的连续N天
```
# 开始日期
if [ -n "$1" ]
then
    begin_date=`date +"%Y%m%d" -d "$1"`
else
    begin_date=`date +'%Y%m%d' -d "1 days ago"`
fi
# 天数
if [ -n "$2" ]
then
    days=$2
else
    days=0
fi
declare -i index
index=0
while [ ${index} -lt ${days}  ]
do
   date=`date -d "${begin_date} ${index} days" +"%Y%m%d"`
   echo ${date}
   index=${index}+1
done
```
测试：
```
xiaosi@yoona:~$ sh date.sh 20161210 1
20161210
xiaosi@yoona:~$ sh date.sh 20161210 2
20161210
20161211
xiaosi@yoona:~$ sh date.sh 20161210
xiaosi@yoona:~$
```

### 7. 循环输入文件

```
for day in `seq ${first_day} ${last_day}`;do
    input=${input},data_group/push/origin/${day}
done
input=${input#,}
```

### 8.

echo `date --date "1 month ago $month" +"%Y-%m-01"`
```
在当前日期上添加10天：

date -d "10 day" +"%Y %m %d"
在当前日期上减去10天

date -d "-10 day" +"%Y %m %d"
在当前日期上添加两个月：

date -d "2 month" +"%Y %m %d"
在当前日期上减去两个月

date -d "-2 month" +"%Y %m %d"
在当前日期上加上1年：

date -d "1 year" +"%Y %m %d"
在当前日期上减去1年：

date -d "-1 year" +"%Y %m %d"
在当前日期上添加1年零一个月零一天：

date -d "1 year 1 month 1 day" +"%Y %m %d"
```
