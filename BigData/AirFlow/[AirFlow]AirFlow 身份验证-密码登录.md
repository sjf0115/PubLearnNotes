---
layout: post
author: sjf0115
title: AirFlow指南二 身份验证-密码登录
date: 2018-01-03 15:24:01
tags:
  - Airflow

categories: Airflow
---

默认情况下，所有的功能都是开放的。限制访问`Web`应用程序的简单方法是在网络级别或通过使用`SSH`隧道进行。

最简单的身份验证机制之一是要求用户在登录之前指定密码。密码身份验证需要在需求文件中使用密码子包。 密码散列在存储密码之前使用bcrypt。

```
[webserver]
authenticate = True
auth_backend = airflow.contrib.auth.backends.password_auth
```

Airflow提供一个类似插件的方式让使用者可以更好地按自己的需求定制， 这里 列出了官方的一定Extra Packages.

默认安装后是，后台管理的webserver是无须登录，如果想加一个登录过程很简单：

首先安装密码验证模块：
```
sudo pip install airflow[password]
```
有可能在安装的过程中会有一些依赖包没有，只需要相应地装上就可以了。比如 libffi-dev 、 flask-bcrypt

当启用密码验证时，在用户可以登录之前需要创建初始用户凭证。在迁移到后端认证时未创建初始用户，以防止默认的`Airflow`安装受到攻击(An initial user was not created in the migrations for this authenication backend to prevent default Airflow installations from attack. )。创建一个新用户必须通过在`AirFlow`安装的同一台机器上的`Python REPL`来完成。进入你`airflow`安装目录后运行以下代码，将用户帐号密码信息写入DB：
```
import airflow
from airflow import models, settings
from airflow.contrib.auth.backends.password_auth import PasswordUser
u = PasswordUser(models.User())
u.username = 'xiaosi'
u.email = '1203745031@qq.com'
u.password = 'zxcvbnm'
session = settings.Session()
session.add(u)
session.commit()
session.close()
exit()
```
运行上述代码运行到设置密码时会报如下错误:
```
>>> u.password = 'zxcvbnm'
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/usr/local/lib/python2.7/dist-packages/sqlalchemy/ext/hybrid.py", line 873, in __set__
    raise AttributeError("can't set attribute")
AttributeError: can't set attribute
```
查阅源代码之后发现有如下代码:
```
@password.setter
def _set_password(self, plaintext):
  self._password = generate_password_hash(plaintext, 12)
  if PY3:
    self._password = str(self._password, 'utf-8')
```
所以试用一下:
```
import airflow
from airflow import models, settings
from airflow.contrib.auth.backends.password_auth import PasswordUser
u = PasswordUser(models.User())
u.username = 'xiaosi'
u.email = '1203745031@qq.com'
u._set_password = '123'
session = settings.Session()
session.add(u)
session.commit()
session.close()
exit()
```
`_set_password`主要是调用了`Flask`的密码生成函数`generate_password_hash`，对密码进行加密。查看数据库我们生成的用户:
```mysql
mysql> select * from users;
+----+----------+-------------------+--------------------------------------------------------------+
| id | username | email             | password                                                     |
+----+----------+-------------------+--------------------------------------------------------------+
|  4 | xiaosi   | 1203745031@qq.com | $2b$12$vBQU2jJIYgOiIgmuPoeFC.3gTeeQ1ljdtrFRmo0w1U3pvTAuRNMv6 |
+----+----------+-------------------+--------------------------------------------------------------+
1 row in set (0.00 sec)
```

进行上述步骤之后，重启`webserver`即可看见登录页面:




原文:http://pythonhosted.org/airflow/security.html#web-authentication
