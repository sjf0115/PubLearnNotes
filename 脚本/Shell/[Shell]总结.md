
### 1. echo \t
```
echo -e "${type1}\t${type2}\t${result}" > ${user_data_path}/entrance_coincidence_result.txt
```

### 2. 数值运算

```
xiaosi@yoona:~$ adr_uv=200
xiaosi@yoona:~$ ios_uv=300
xiaosi@yoona:~$ all_uv=`expr ${adr_uv} + ${ios_uv}`
xiaosi@yoona:~$ echo ${all_uv}
500
```

### 3. 输入时间判断

```
if [ -n "$1" ]
then
    exec_date=`date +'%Y%m%d' -d "$1"`
else
    exec_date=`date +'%Y%m%d' -d "1 days ago"`
fi
format_date=`date +"%Y-%m-%d" -d "${exec_date}"`
```

### 4. 判断脚本执行结果
```
sh xxx.sh
res=$?
if [[ ${res} -ne 0 ]]
then
    echo "---------------------------------------脚本执行不成功"
    exit 1
fi
```
### 5. awk传递变量

#### 5.1 获取外部变量
```
xiaosi@yoona:~$ date=20170315
xiaosi@yoona:~$ echo | awk '{print day}' day="${date}"
20170315
```
格式：
```
awk '{action}' 变量名=变量值  
```
这样就可以在action表达式中获取变量值

注意：

变量名与值放到'{action}'后面。

或者使用-v参数：
```
xiaosi@yoona:~$ echo | awk -v day="${date}" '{print day}'
20170315
```

#### 5.2 BEGIN程序块中变量

```
xiaosi@yoona:~$ date=20170315
xiaosi@yoona:~$ echo | awk '{print day}' day="${date}"
20170315
xiaosi@yoona:~$ echo | awk 'BEGIN{print day}' day="${date}"

xiaosi@yoona:~$ echo | awk -v day="${date}" 'BEGIN{print day}'
20170315

```
如果想在BEGIN程序块中获取变量值上述方法行不通，需利用下面格式：
```
awk –v 变量名=变量值 [–v 变量2=值2 …] 'BEGIN{action}'
```

### 6. awk 分组排序

```
... | awk -F"\t" '{arrays[$3]+=1} END {for(k in arrays){print k,arrays[k]}}'    
```

### 7. 删除过期文件

```
find $location -mtime +30 -type f |xargs rm -f
```

### 8. 分组求和
```
awk '{sum += $1};END {print sum}'
```

### 9. 平均值

```
awk '{sum+=$1} END {print sum/NR}'
```
