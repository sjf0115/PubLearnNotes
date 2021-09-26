---
layout: post
author: sjf0115
title: MySQL 配置远程登录
date: 2017-12-29 13:29:01
tags:
  - MySQL

categories: MySQL
---

### 1. 修改配置

修改`/etc/mysql/mysql.conf.d`目录下的`mysqld.cnf`配置文件:
```
# Instead of skip-networking the default is now to listen only on
# localhost which is more compatible and is not less secure.
#bind-address           = 127.0.0.1
```
在`bind-address`前面加个`#`进行注释，允许任意IP访问。或者指定自己需要远程访问的IP地址。然后重启`mysql`:
```
ubuntu@VM-0-7-ubuntu:/etc/mysql/mysql.conf.d$ sudo /etc/init.d/mysql restart
Restarting mysql (via systemctl): mysql.service.
```
### 2. 授权用户

我们先看一下当前能登录到我们数据的用户以及允许连接的IP:
```sql
mysql> USE mysql;
Reading table information for completion of table and column names
You can turn off this feature to get a quicker startup with -A

Database changed

mysql> select User,Host from user;
+------------------+-----------+
| User             | Host      |
+------------------+-----------+
| debian-sys-maint | localhost |
| mysql.session    | localhost |
| mysql.sys        | localhost |
| root             | localhost |
+------------------+-----------+
4 rows in set (0.00 sec)
```
我们可以看到只有一个默认的`root`用户，且只允许使用`localhost`连接。下面我们另外添加一个新的`root`用户在指定IP下使用指定密码来访问数据库:
```sql
mysql> GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY 'dev' WITH GRANT OPTION;
Query OK, 0 rows affected, 1 warning (0.00 sec)
```

`*.*`中第一个`*`代表数据库名称，第二个`*`代表表名。在这里我们设置的是所有数据库里的所有表都授权给用户，如果只想授权某数据库或某些数据库下某些表，可以把`*`替换成你所需的数据库名和表明即可:
```
mysql> GRANT ALL PRIVILEGES ON test_db.user TO 'root'@'%' IDENTIFIED BY 'dev' WITH GRANT OPTION;
```
上述表示是把`test_db`数据下的`user`数据表授权给用户。

`root`表示授予`root`用户可以登录数据库。`%`表示授权的用户使用哪些IP可以登录，这里表示可以使用用户`root`在任意IP地址来访问数据库。`dev`表示分配`root`用户对应的密码。

当然我们也可以直接用`UPDATE`更新`root`用户`Host`, 但不推荐：
```
UPDATE user SET Host='%' WHERE User='root' AND Host='localhost';
```
授权用户之后，执行如下命令刷新一下权限:
```sql

mysql> flush privileges;
Query OK, 0 rows affected (0.00 sec)
```
至此我们已经完成了配置远程访问数据的所有操作，我们在看一下当前能访问我们数据库的用户:
```
mysql> select User,Host from user;
+------------------+-----------+
| User             | Host      |
+------------------+-----------+
| root             | %         |
| debian-sys-maint | localhost |
| mysql.session    | localhost |
| mysql.sys        | localhost |
| root             | localhost |
+------------------+-----------+
5 rows in set (0.00 sec)
```
