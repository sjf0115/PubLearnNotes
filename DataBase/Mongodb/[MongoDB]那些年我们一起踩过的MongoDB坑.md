### 1. child process failed

#### 1.1 问题描述
```
xiaosi@yoona:~/opt/mongodb-ubuntu1404-3.2.8$ sudo ./bin/mongod --dbpath data --logpath logs/mongodb.log --logappend --fork
[sudo] xiaosi 的密码：
about to fork child process, waiting until server is ready for connections.
forked process: 6114
ERROR: child process failed, exited with error number 1
```
#### 1.2 问题解决

原因是MongoDB在非法关闭的时候，lock文件没有删除，第二次启动的时候检查到有lock文件存在，就报这个错误了。

解决方法：进入 mongod 上一次启动的时候指定的 data 目录  --dbpath=/data/mongodb

删除掉该文件:

rm /data/mongodb/mongo.lock --linux

del /data/mongodb/mongo.lock --windows
