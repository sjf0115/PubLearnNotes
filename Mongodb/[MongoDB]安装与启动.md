### 1. 启动服务

#### 1.1 命令行方式启动

在启动MongoDB服务之前，需要为MongoDB创建一个数据目录用于存储文件。默认情况下，对于Linux系统，MongoDB将数据存储在/data/db目录中。默认端口为27017，默认HTTP端口为28017。当然你也可以修改成不同目录，只需要指定dbpath参数:
```
./bin/mongod  --dbpath=/data/db
```
一旦创建必要的目录并赋予正确的权限，就可以通过执行`mongodb`命令启动MongoDB核心数据库服务。使用如下命令启动MongoDB服务：
```
xiaosi@yoona:~/qunar/company/opt/mongodb-ubuntu1404-3.2.8$ sudo ./bin/mongod --dbpath /home/xiaosi/data/mongodb --logpath /home/xiaosi/logs/mongodb/mongodb.log --logappend --fork
about to fork child process, waiting until server is ready for connections.
forked process: 6461
child process started successfully, parent exiting
```
备注:
```
logpath为日志路径
dbpath为数据文件存放目录
```

#### 1.2 配置文件方式启动

在启动时在 mongod 后面加一长串的参数，看起来非常混乱而且不好管理和维护，那么有什么办法让这些参数有条理呢?MongoDB 也支持同 mysql 一样的读取启动配置文件的方式来启动数据库。

创建配置文件 mongodb.conf
```
# 数据存放位置
dbpath=data
# 日志
logpath=logs/mongodb.log
# 后台启动
fork=true
# 日志追加形式
logappend=true
```
启动时加上"-f"参数，并指向配置文件即可：
```
sudo ./bin/mongod -f mongodb.cnf
```
==备注==

MongoDB 提供了一种后台Daemon 方式启动的选择，只需加上一个”--fork”参数即可，这就使我们可以更方便的操作数据库的启动，但如果用到了”--fork”参数就必须也启用”--logpath”参数，这是强制的。

#### 1.3 参数说明

通过执行 mongod 即可以启动 MongoDB 数据库服务，mongod 支持很多的参数，但都有默认值，其中最重要的是需要指定数据文件路径，或者确保默认的/data/db 存在并且有访问权限，否则启动后会自动关闭服务。所以，只要确保 dbpath 就可以启动MongoDB 服务了。


(1) dbpath：数据文件存放路径，每个数据库会在其中创建一个子目录，用于防止同一个实例多次运行的 mongod.lock 也保存在此目录中。

(2) logpath：错误日志文件

(3) logappend：错误日志采用追加模式(默认是覆写模式)

(4) bind_ip：对外服务的绑定 ip，一般设置为空,及绑定在本机所有可用 ip 上,如有需要可以单独指定

(5) port：对外服务端口。Web 管理端口在这个 port 的基础上+1000

(6) fork：以后台 Daemon 形式运行服务

(7) journal：开启日志功能，通过保存操作日志来降低单机故障的恢复时间,在 1.8 版本后正式加入，取代在 1.7.5 版本中的 dur 参数。

(8) syncdelay：系统同步刷新磁盘的时间，单位为秒，默认是 60 秒。

(9) maxConns：最大连接数

(10) repairpath：执行 repair 时的临时目录。在如果没有开启 journal，异常 down 机后重启，必须执行 repair 操作


### 2. 启动数据库

使用mongo命令连接数据库
```
xiaosi@Qunar:/opt/mongodb-ubuntu1404-3.2.8$ mongo
MongoDB shell version: 3.2.8
connecting to: test
Welcome to the MongoDB shell.
For interactive help, type "help".
For more comprehensive documentation, see
	http://docs.mongodb.org/
Questions? Try the support group
	http://groups.google.com/group/mongodb-user
Server has startup warnings:
2016-08-11T21:14:02.265+0800 I CONTROL  [initandlisten] ** WARNING: You are running this process as the root user, which is not recommended.
2016-08-11T21:14:02.265+0800 I CONTROL  [initandlisten]
2016-08-11T21:14:02.265+0800 I CONTROL  [initandlisten]
2016-08-11T21:14:02.265+0800 I CONTROL  [initandlisten] ** WARNING: /sys/kernel/mm/transparent_hugepage/enabled is 'always'.
2016-08-11T21:14:02.265+0800 I CONTROL  [initandlisten] **        We suggest setting it to 'never'
2016-08-11T21:14:02.265+0800 I CONTROL  [initandlisten]
2016-08-11T21:14:02.265+0800 I CONTROL  [initandlisten] ** WARNING: /sys/kernel/mm/transparent_hugepage/defrag is 'always'.
2016-08-11T21:14:02.265+0800 I CONTROL  [initandlisten] **        We suggest setting it to 'never'
2016-08-11T21:14:02.265+0800 I CONTROL  [initandlisten]
>
```
