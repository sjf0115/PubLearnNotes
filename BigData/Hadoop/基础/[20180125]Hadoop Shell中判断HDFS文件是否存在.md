---
author: sjf0115
title: Hadoop Shell中判断HDFS文件是否存在
date: 2018-01-25 15:49:01
tags:
  - Hadoop
  - Hadoop 基础

categories: Hadoop
permalink: hadoop-how-to-determine-the-hdfs-file-exists
---

### 1. 用法

`Hadoop`提供了`-test`命令可以验证文件目录是否存在。我们首先看一下`-test`命令的使用用法:
```
hadoop fs -help
-test -[defsz] <path>:  Answer various questions about <path>, with result via exit status.
                  -d  return 0 if <path> is a directory.
                  -e  return 0 if <path> exists.
                  -f  return 0 if <path> is a file.
                  -s  return 0 if file <path> is greater than zero bytes in size.
                  -z  return 0 if file <path> is zero bytes in size.
                else, return 1.
```

命令参数|描述
---|---
-d|如果指定路径是一个目录返回0否则返回1
-e|如果指定路径存在返回0否则返回1
-f|如果指定路径是一个文件返回0否则返回1
-s|如果指定路径文件大小大于0返回0否则返回1
-z|如果指定指定文件大小等于0返回0否则返回1


### 2. Example:

```
[xiaosi@ying:~$]$ sudo -uxiaosi hadoop fs -ls test/adv
Found 1 items
drwxr-xr-x   - xiaosi xiaosi          0 2018-01-25 15:39 test/adv/day=20180123
[xiaosi@ying:~$]$
[xiaosi@ying:~$]$ sudo -uxiaosi hadoop fs -test -e test/adv/day=20180123
[xiaosi@ying:~$]$ echo $?
0
[xiaosi@ying:~$]$ sudo -uxiaosi hadoop fs -test -e test/adv/day=20180124
[xiaosi@ying:~$]$ echo $?
1
```

### 3. Shell中判断

```
sudo -uxiaosi hadoop fs -test -e test/adv/day=20180123
if [ $? -eq 0 ] ;then
    echo '[info]目录已存在不需要创建'
else
    sudo -uxiaosi hadoop fs -mkdir -p test/adv/day=20180123
fi
```
