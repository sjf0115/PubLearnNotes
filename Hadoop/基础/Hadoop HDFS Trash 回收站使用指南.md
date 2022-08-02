---
layout: post
author: sjf0115
title: Hadoop Trash 回收站使用指南
date: 2017-12-07 10:07:01
tags:
  - Hadoop
  - Hadoop 基础

categories: Hadoop
permalink: hadoop-hdfs-trash
---

我们在删除一个文件时，遇到如下问题，提示我们不能删除文件放回回收站:
```
sudo -uxiaosi hadoop fs -rm -r tmp/data_group/test/employee/employee_salary.txt
17/12/06 16:34:48 INFO fs.TrashPolicyDefault: Namenode trash configuration: Deletion interval = 72000000 minutes, Emptier interval = 0 minutes.
17/12/06 16:34:48 WARN fs.TrashPolicyDefault: Can't create trash directory: hdfs://cluster/user/xiaosi/.Trash/Current/user/xiaosi/tmp/data_group/test/employee
rm: Failed to move to trash: hdfs://cluster/user/xiaosi/tmp/data_group/test/employee/employee_salary.txt. Consider using -skipTrash option
```

去回收站对应目录下观察一下，得出的结论是：无法创建目录`employee`，因为`employee`文件已经存在，自然导致`employee_salary.txt`文件不能放回收回站:
```
-rw-r--r--   3 xiaosi xiaosi  352 2017-12-06 16:18 hdfs://cluster/user/xiaosi/.Trash/Current/user/xiaosi/tmp/data_group/test/employee
```
跟如下是同样的道理:
```
xiaosi@yoona:~$ ll employee
-rw-rw-r-- 1 xiaosi xiaosi 0 12月  6 16:56 employee
xiaosi@yoona:~$
xiaosi@yoona:~$
xiaosi@yoona:~$ mkdir employee
mkdir: 无法创建目录"employee": 文件已存在
```
借此机会，详细研究了一下`HDFS`的`Trash`回收站机制。

### 1. 配置

`HDFS`的回收站就像`Windows`操作系统中的回收站一样。它的目的是防止你无意中删除某些东西。你可以通过设置如下属性来启用此功能(默认是不开启的)：
```xml
<property>  
    <name>fs.trash.interval</name>  
    <value>1440</value>  
    <description>Number of minutes after which the checkpoint gets deleted. If zero, the trash feature is disabled.</description>  
</property>  

<property>  
    <name>fs.trash.checkpoint.interval</name>  
    <value>0</value>  
    <description>Number of minutes between trash checkpoints. Should be smaller or equal to fs.trash.interval. If zero, the value is set to the value of fs.trash.interval.</description>  
</property>
```

属性|说明
---|---
fs.trash.interval|分钟数，当超过这个分钟数后检查点会被删除。如果为零，回收站功能将被禁用。
fs.trash.checkpoint.interval|检查点创建的时间间隔(单位为分钟)。其值应该小于或等于`fs.trash.interval`。如果为零，则将该值设置为`fs.trash.interval`的值。

### 2. Trash

启用回收站功能后，使用`rm`命令从`HDFS`中删除某些内容时，文件或目录不会立即被清除，它们将被移动到回收站`Current`目录中(`/user/${username}/.Trash/current`)。如果检查点已经启用，会定期使用时间戳重命名`Current`目录。`.Trash`中的文件在用户可配置的时间延迟后被永久删除。回收站中的文件和目录可以简单地通过将它们移动到`.Trash`目录之外的位置来恢复:
```
sudo -uxiaosi hadoop fs -rm tmp/data_group/test/employee/employee_salary.txt
17/12/06 17:24:32 INFO fs.TrashPolicyDefault: Namenode trash configuration: Deletion interval = 72000000 minutes, Emptier interval = 0 minutes.
Moved: 'hdfs://cluster/user/xiaosi/tmp/data_group/test/employee/employee_salary.txt' to trash at: hdfs://cluster/user/xiaosi/.Trash/Current
```
说明:
- `Deletion interval`表示检查点删除时间间隔(单位为分钟)。这里是`fs.trash.interval`的值。`NameNode`运行一个线程来定期从文件系统中删除过期的检查点。
- `Emptier interval`表示在运行线程来管理检查点之前，`NameNode`需要等待多长时间(以分钟为单位)，即检查点创建时间间隔。`NameNode`删除超过`fs.trash.interval`的检查点，并为`/user/${username}/.Trash/Current`创建一个新的检查点。该频率由`fs.trash.checkpoint.interval`的值确定，且不得大于`Deletion interval`。这确保了在`emptier`窗口内回收站中有一个或多个检查点。

例如，可以设置如下:
```
fs.trash.interval = 360 (deletion interval = 6 hours)
fs.trash.checkpoint.interval = 60 (emptier interval = 1 hour)
```
这导致`NameNode`为`Current`目录下的垃圾文件每小时创建一个新的检查点，并删除已经存在超过6个小时的检查点。

在回收站生命周期结束后，`NameNode`从`HDFS`命名空间中删除该文件。删除文件会导致与文件关联的块被释放。请注意，用户删除文件的时间与HDFS中相应增加可用空间的时间之间可能存在明显的时间延迟，即用户删除文件，HDFS可用空间不会立马增加，中间有一定的延迟。

### 3. 检查点

检查点仅仅是用户回收站下的一个目录，用于存储在创建检查点之前删除的所有文件或目录。如果你想查看回收站目录，可以在`/user/${username}/.Trash/{timestamp_of_checkpoint_creation}`处看到:
```
hadoop fs -ls hdfs://cluster/user/xiaosi/.Trash/
Found 3 items
drwx------   - xiaosi xiaosi          0 2017-12-05 08:00 hdfs://cluster/user/xiaosi/.Trash/171205200038
drwx------   - xiaosi xiaosi          0 2017-12-06 01:00 hdfs://cluster/user/xiaosi/.Trash/171206080038
drwx------   - xiaosi xiaosi          0 2017-12-06 08:00 hdfs://cluster/user/xiaosi/.Trash/Current
```
最近删除的文件被移动到回收站`Current`目录，并且在可配置的时间间隔内，`HDFS`会为在`Current`回收站目录下的文件创建检查点`/user/${username}/.Trash/<日期>`，并在过期时删除旧的检查点。


### 4. 清空回收站

首先想到的是只要删除整个回收站目录，将会清空回收站。诚然，这是一个选择。但是我们有更好的选择。`HDFS`提供了一个命令行工具来完成这个工作：
```
hadoop fs -expunge
```
该命令使`NameNode`永久删除回收站中比阈值更早的文件，而不是等待下一个`emptier`窗口。它立即从文件系统中删除过期的检查点。

### 5. 注意点

回收站功能默认是禁用的。对于生产环境，建议启用回收站功能以避免意外的删除操作。启用回收站提供了从用户操作删除或用户意外删除中恢复数据的机会。但是为`fs.trash.interval`和`fs.trash.checkpoint.interval`设置合适的值也是非常重要的，以使垃圾回收以你期望的方式运作。例如，如果你需要经常从`HDFS`上传和删除文件，则可能需要将`fs.trash.interval`设置为较小的值，否则检查点将占用太多空间。

当启用垃圾回收并删除一些文件时，`HDFS`容量不会增加，因为文件并未真正删除。`HDFS`不会回收空间，除非文件从回收站中删除，只有在检查点过期后才会发生。

回收站功能默认只适用于使用`Hadoop shell`删除的文件和目录。使用其他接口(例如`WebHDFS`或`Java API`)以编程的方式删除的文件或目录不会移动到回收站，即使已启用回收站，除非程序已经实现了对回收站功能的调用。

有时你可能想要在删除文件时临时禁用回收站，也就是删除的文件或目录不用放在回收站而直接删除，在这种情况下，可以使用`-skipTrash`选项运行`rm`命令。例如：
```
sudo -uxiaosi hadoop fs -rm -skipTrash tmp/data_group/test/employee/employee_salary.txt
```
这会绕过垃圾回收站并立即从文件系统中删除文件。


资料:
- https://developer.ibm.com/hadoop/2015/10/22/hdfs-trash/
- https://my.oschina.net/cloudcoder/blog/179381
- http://debugo.com/hdfs-trash/
- http://hadoop.apache.org/docs/r2.7.3/hadoop-project-dist/hadoop-hdfs/HdfsDesign.html#File_Deletes_and_Undeletes
