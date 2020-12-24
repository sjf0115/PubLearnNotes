---
layout: post
author: sjf0115
title: Airflow使用指南一 安装与启动
date: 2017-12-29 12:55:01
tags:
  - Airflow

categories: Airflow
---

### 1. 安装

通过pip安装:
```
xiaosi@yoona:~$ pip install airflow
```
如果速度比较慢，可以使用下面提供的源进行安装:
```
xiaosi@yoona:~$ pip install -i https://pypi.tuna.tsinghua.edu.cn/simple airflow
```
如果出现下面提示，表示你的airflow安装成功了:
```
Successfully installed airflow alembic croniter dill flask flask-admin flask-cache flask-login flask-swagger flask-wtf funcsigs future gitpython gunicorn jinja2 lxml markdown pandas psutil pygments python-daemon python-dateutil python-nvd3 requests setproctitle sqlalchemy tabulate thrift zope.deprecation Mako python-editor click itsdangerous Werkzeug wtforms PyYAML ordereddict gitdb2 MarkupSafe pytz numpy docutils setuptools lockfile six python-slugify idna urllib3 certifi chardet smmap2 Unidecode
Cleaning up...
```
安装完成之后我的默认安装在`~/.local/bin`目录下

### 2. 配置

如果不修改路径，默认的配置为`~/airflow`

永久修改环境变量
```
echo "export AIRFLOW_HOME=/home/xiaosi/opt/airflow" >> /etc/profile
source /etc/profile
```
为了便于操作方便，进行如下配置:
```
echo "export PATH=/home/xiaosi/.local/bin:$PATH" >> /etc/profile
source /etc/profile
```

### 3. 初始化

初始化数据库:
```
xiaosi@yoona:~$ airflow initdb
[2017-08-02 16:39:22,319] {__init__.py:57} INFO - Using executor SequentialExecutor
[2017-08-02 16:39:22,432] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/Grammar.txt
[2017-08-02 16:39:22,451] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/PatternGrammar.txt
DB: sqlite:////home/xiaosi/opt/airflow/airflow.db
[2017-08-02 16:39:22,708] {db.py:287} INFO - Creating tables
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> e3a246e0dc1, current schema
INFO  [alembic.runtime.migration] Running upgrade e3a246e0dc1 -> 1507a7289a2f, create is_encrypted
/home/xiaosi/.local/lib/python2.7/site-packages/alembic/util/messaging.py:69: UserWarning: Skipping unsupported ALTER for creation of implicit constraint
  warnings.warn(msg)
INFO  [alembic.runtime.migration] Running upgrade 1507a7289a2f -> 13eb55f81627, maintain history for compatibility with earlier migrations
INFO  [alembic.runtime.migration] Running upgrade 13eb55f81627 -> 338e90f54d61, More logging into task_isntance
INFO  [alembic.runtime.migration] Running upgrade 338e90f54d61 -> 52d714495f0, job_id indices
INFO  [alembic.runtime.migration] Running upgrade 52d714495f0 -> 502898887f84, Adding extra to Log
INFO  [alembic.runtime.migration] Running upgrade 502898887f84 -> 1b38cef5b76e, add dagrun
INFO  [alembic.runtime.migration] Running upgrade 1b38cef5b76e -> 2e541a1dcfed, task_duration
INFO  [alembic.runtime.migration] Running upgrade 2e541a1dcfed -> 40e67319e3a9, dagrun_config
INFO  [alembic.runtime.migration] Running upgrade 40e67319e3a9 -> 561833c1c74b, add password column to user
INFO  [alembic.runtime.migration] Running upgrade 561833c1c74b -> 4446e08588, dagrun start end
INFO  [alembic.runtime.migration] Running upgrade 4446e08588 -> bbc73705a13e, Add notification_sent column to sla_miss
INFO  [alembic.runtime.migration] Running upgrade bbc73705a13e -> bba5a7cfc896, Add a column to track the encryption state of the 'Extra' field in connection
INFO  [alembic.runtime.migration] Running upgrade bba5a7cfc896 -> 1968acfc09e3, add is_encrypted column to variable table
INFO  [alembic.runtime.migration] Running upgrade 1968acfc09e3 -> 2e82aab8ef20, rename user table
INFO  [alembic.runtime.migration] Running upgrade 2e82aab8ef20 -> 211e584da130, add TI state index
INFO  [alembic.runtime.migration] Running upgrade 211e584da130 -> 64de9cddf6c9, add task fails journal table
INFO  [alembic.runtime.migration] Running upgrade 64de9cddf6c9 -> f2ca10b85618, add dag_stats table
INFO  [alembic.runtime.migration] Running upgrade f2ca10b85618 -> 4addfa1236f1, Add fractional seconds to mysql tables
INFO  [alembic.runtime.migration] Running upgrade 4addfa1236f1 -> 8504051e801b, xcom dag task indices
INFO  [alembic.runtime.migration] Running upgrade 8504051e801b -> 5e7d17757c7a, add pid field to TaskInstance
INFO  [alembic.runtime.migration] Running upgrade 5e7d17757c7a -> 127d2bf2dfa7, Add dag_id/state index on dag_run table
Done.
```
运行上述命令之后，会在$AIRFLOW_HOME目录下生成如下文件:
```
xiaosi@yoona:~/opt/airflow$ ll
总用量 88
drwxrwxr-x  2 xiaosi xiaosi  4096  8月  2 16:39 ./
drwxrwxr-x 26 xiaosi xiaosi  4096  7月 31 13:56 ../
-rw-rw-r--  1 xiaosi xiaosi 11424  8月  2 16:38 airflow.cfg
-rw-r--r--  1 xiaosi xiaosi 58368  8月  2 16:39 airflow.db
-rw-rw-r--  1 xiaosi xiaosi  1554  8月  2 16:38 unittests.cfg
```
### 4. 修改默认数据库

找到`$AIRFLOW_HOME/airflow.cfg`配置文件，进行如下修改:
```
sql_alchemy_conn = mysql://root:root@localhost:3306/airflow
```
**备注**

数据库用户名与密码均为`root`，airflow使用的数据库为`airflow`．使用如下命令创建对应的数据库:
```
mysql> create database airflow;
Query OK, 1 row affected (0.00 sec)
```
重新初始化服务器数据库:
```
xiaosi@yoona:~$ airflow initdb
```
出现了如下错误:
```
xiaosi@yoona:~$ airflow initdb
Traceback (most recent call last):
  File "/home/xiaosi/.local/bin/airflow", line 17, in <module>
    from airflow import configuration
  File "/home/xiaosi/.local/lib/python2.7/site-packages/airflow/__init__.py", line 30, in <module>
    from airflow import settings
  File "/home/xiaosi/.local/lib/python2.7/site-packages/airflow/settings.py", line 159, in <module>
    configure_orm()
  File "/home/xiaosi/.local/lib/python2.7/site-packages/airflow/settings.py", line 147, in configure_orm
    engine = create_engine(SQL_ALCHEMY_CONN, **engine_args)
  File "/home/xiaosi/.local/lib/python2.7/site-packages/sqlalchemy/engine/__init__.py", line 387, in create_engine
    return strategy.create(*args, **kwargs)
  File "/home/xiaosi/.local/lib/python2.7/site-packages/sqlalchemy/engine/strategies.py", line 80, in create
    dbapi = dialect_cls.dbapi(**dbapi_args)
  File "/home/xiaosi/.local/lib/python2.7/site-packages/sqlalchemy/dialects/mysql/mysqldb.py", line 110, in dbapi
    return __import__('MySQLdb')
ImportError: No module named MySQLdb
```
解决方案:

MySQL是最流行的开源数据库之一，但在Python标准库中并没有集成MySQL接口程序，MySQLdb是一个第三方包，需独立下载并安装。
```
sudo apt-get install python-mysqldb
```
再次初始化:
```
xiaosi@yoona:~$ airflow initdb
[2017-08-02 17:22:21,169] {__init__.py:57} INFO - Using executor SequentialExecutor
[2017-08-02 17:22:21,282] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/Grammar.txt
[2017-08-02 17:22:21,302] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/PatternGrammar.txt
DB: mysql://root:***@localhost:3306/airflow
[2017-08-02 17:22:21,553] {db.py:287} INFO - Creating tables
INFO  [alembic.runtime.migration] Context impl MySQLImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> e3a246e0dc1, current schema
INFO  [alembic.runtime.migration] Running upgrade e3a246e0dc1 -> 1507a7289a2f, create is_encrypted
INFO  [alembic.runtime.migration] Running upgrade 1507a7289a2f -> 13eb55f81627, maintain history for compatibility with earlier migrations
INFO  [alembic.runtime.migration] Running upgrade 13eb55f81627 -> 338e90f54d61, More logging into task_isntance
INFO  [alembic.runtime.migration] Running upgrade 338e90f54d61 -> 52d714495f0, job_id indices
INFO  [alembic.runtime.migration] Running upgrade 52d714495f0 -> 502898887f84, Adding extra to Log
INFO  [alembic.runtime.migration] Running upgrade 502898887f84 -> 1b38cef5b76e, add dagrun
INFO  [alembic.runtime.migration] Running upgrade 1b38cef5b76e -> 2e541a1dcfed, task_duration
INFO  [alembic.runtime.migration] Running upgrade 2e541a1dcfed -> 40e67319e3a9, dagrun_config
INFO  [alembic.runtime.migration] Running upgrade 40e67319e3a9 -> 561833c1c74b, add password column to user
INFO  [alembic.runtime.migration] Running upgrade 561833c1c74b -> 4446e08588, dagrun start end
INFO  [alembic.runtime.migration] Running upgrade 4446e08588 -> bbc73705a13e, Add notification_sent column to sla_miss
INFO  [alembic.runtime.migration] Running upgrade bbc73705a13e -> bba5a7cfc896, Add a column to track the encryption state of the 'Extra' field in connection
INFO  [alembic.runtime.migration] Running upgrade bba5a7cfc896 -> 1968acfc09e3, add is_encrypted column to variable table
INFO  [alembic.runtime.migration] Running upgrade 1968acfc09e3 -> 2e82aab8ef20, rename user table
INFO  [alembic.runtime.migration] Running upgrade 2e82aab8ef20 -> 211e584da130, add TI state index
INFO  [alembic.runtime.migration] Running upgrade 211e584da130 -> 64de9cddf6c9, add task fails journal table
INFO  [alembic.runtime.migration] Running upgrade 64de9cddf6c9 -> f2ca10b85618, add dag_stats table
INFO  [alembic.runtime.migration] Running upgrade f2ca10b85618 -> 4addfa1236f1, Add fractional seconds to mysql tables
INFO  [alembic.runtime.migration] Running upgrade 4addfa1236f1 -> 8504051e801b, xcom dag task indices
INFO  [alembic.runtime.migration] Running upgrade 8504051e801b -> 5e7d17757c7a, add pid field to TaskInstance
INFO  [alembic.runtime.migration] Running upgrade 5e7d17757c7a -> 127d2bf2dfa7, Add dag_id/state index on dag_run table
Done.
```
查看一下airflow数据库中做了哪些操作:
```
mysql> use airflow;
Reading table information for completion of table and column names
You can turn off this feature to get a quicker startup with -A

Database changed
mysql> show tables;
+-------------------+
| Tables_in_airflow |
+-------------------+
| alembic_version   |
| chart             |
| connection        |
| dag               |
| dag_pickle        |
| dag_run           |
| dag_stats         |
| import_error      |
| job               |
| known_event       |
| known_event_type  |
| log               |
| sla_miss          |
| slot_pool         |
| task_fail         |
| task_instance     |
| users             |
| variable          |
| xcom              |
+-------------------+
19 rows in set (0.00 sec)
```
### 5. 启动
通过如下命令就可以启动后台管理界面，默认访问localhost:8080即可:
```
xiaosi@yoona:~$ airflow webserver
[2017-08-02 17:25:31,961] {__init__.py:57} INFO - Using executor SequentialExecutor
[2017-08-02 17:25:32,075] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/Grammar.txt
[2017-08-02 17:25:32,095] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/PatternGrammar.txt
  ____________       _____________
 ____    |__( )_________  __/__  /________      __
____  /| |_  /__  ___/_  /_ __  /_  __ \_ | /| / /
___  ___ |  / _  /   _  __/ _  / / /_/ /_ |/ |/ /
 _/_/  |_/_/  /_/    /_/    /_/  \____/____/|__/

/home/xiaosi/.local/lib/python2.7/site-packages/flask/exthook.py:71: ExtDeprecationWarning: Importing flask.ext.cache is deprecated, use flask_cache instead.
  .format(x=modname), ExtDeprecationWarning
[2017-08-02 17:25:32,469] [9703] {models.py:167} INFO - Filling up the DagBag from /home/xiaosi/opt/airflow/dags
Running the Gunicorn Server with:
Workers: 4 sync
Host: 0.0.0.0:8080
Timeout: 120
Logfiles: - -
=================================================================            
[2017-08-02 17:25:33,052] {__init__.py:57} INFO - Using executor SequentialExecutor
[2017-08-02 17:25:33,156] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/Grammar.txt
[2017-08-02 17:25:33,179] {driver.py:120} INFO - Generating grammar tables from /usr/lib/python2.7/lib2to3/PatternGrammar.txt
[2017-08-02 17:25:33 +0000] [9706] [INFO] Starting gunicorn 19.3.0
[2017-08-02 17:25:33 +0000] [9706] [INFO] Listening at: http://0.0.0.0:8080 (9706)
[2017-08-02 17:25:33 +0000] [9706] [INFO] Using worker: sync
...
```

可以访问 http://localhost:8080/admin/ , 呈现出的主界面如下:
![img](http://img.blog.csdn.net/20170802173129848?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)
