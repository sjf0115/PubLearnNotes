## 1， 问题

登录 MySQL 时出现如下异常：
```
smartsi@192 软件 % mysql -u root -h localhost -p
zsh: command not found: mysql
```

## 2. 分析

当你在 Mac 终端尝试运行 mysql 命令时出现 `zsh: command not found: mysql` 错误，这表明：
- MySQL 客户端程序没有安装在你的系统上
- 或者 MySQL 客户端已安装但未添加到系统的 PATH 环境变量中

在这我们已经成功安装了 MySQL 客户端，那核心原因就是未添加到系统的 PATH 环境变量中。

## 3. 解决方案

如果 MySQL 已安装但命令不可用，需要将其添加到 PATH。

第一步是查找 MySQL 安装位置，通常安装在 `/usr/local/mysql/bin` 或 `/usr/local/bin` 下。可以通过使用 `which` 命令查看：
```
martsi@192 ~ % which mysql
/usr/local/mysql/bin/mysql
```

第二步修改 `/etc/profile` 文件添加如下到到 PATH：
```
# MySQL
export MYSQL_HOME=/usr/local/mysql
export PATH=$MYSQL_HOME/bin:$PATH
```

第三步执行如下命令让 PATH 立即生效：
```
smartsi@192 ~ % source /etc/profile
```

第四步登录 MySQL 进行验证：
```
smartsi@192 ~ % mysql -u root -h localhost -p
Enter password:
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 8
Server version: 8.0.43 MySQL Community Server - GPL

Copyright (c) 2000, 2025, Oracle and/or its affiliates.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql>
```
