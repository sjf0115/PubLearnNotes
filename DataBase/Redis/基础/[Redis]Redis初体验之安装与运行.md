在安装Redis前需要了解Redis的版本规则以选择最合适自己的版本，Redis约定次版本（即第一个小数点后的数字）为偶数的版本是稳定版本(如 2.4版本，2.6版本)，奇数版本是非稳定版本(如2.5版本，2.7版本)，推荐使用稳定版本进行开发和在生产环境中使用．


### 1. 下载

当前最新版本为3.2.9：

官网下载：https://redis.io/

中文官网下载：http://www.redis.cn/download.html

### 2. 安装

解压缩文件到指定目录：
```
tar -zxvf redis-3.2.9.tar.gz -C opt/
```
进入解压之后的目录，进行编译
```
cd opt/redis-3.2.9/
make
```
看到如下信息，表示可以继续下一步：
```
    CC redis-check-rdb.o
    CC geo.o
    LINK redis-server
    INSTALL redis-sentinel
    CC redis-cli.o
    LINK redis-cli
    CC redis-benchmark.o
    LINK redis-benchmark
    INSTALL redis-check-rdb
    CC redis-check-aof.o
    LINK redis-check-aof

Hint: It's a good idea to run 'make test' ;)

make[1]: Leaving directory '/home/xiaosi/opt/redis-3.2.9/src'

```
二进制文件编译完成后在src目录下，进行src目录之后进行安装操作:
```
xiaosi@yoona:~/opt/redis-3.2.9/src$ sudo make install

Hint: It's a good idea to run 'make test' ;)

    INSTALL install
    INSTALL install
    INSTALL install
    INSTALL install
    INSTALL install

```
==备注==

 一般情况下，在Ubuntu系统中，都是需要使用sudo提升权限
 
 在安装成功之后，可以运行测试，确认Redis的功能是否正常：
 ```
 make test
 ```
看到如下信息，表示Redis已经安装成功： 
 ```
 
\o/ All tests passed without errors!

Cleanup: may take some time... OK

 ```
### 3. 启动

安装完Redis后的下一步就是启动它，下面将介绍在开发环境和生产环境中运行Redis的方法以及正确停止Redis的步骤．在这之前，我们先了解Redis包含的可执行文件都有哪些，如下表：


文件名你 | 说明
---|---
redis-server | Redis服务器
redis-cli | Redis命令行客户端
redis-benchmark | Redis性能测试工具
redis-check-aof | AOF文件修复工具

我们最常使用的两个程序是redis-server 和　redis-cli，其中redis-server 是 Redis的服务器，启动Redis即运行它；而redis-cli是Redis自带的Redis命令行客户端．


#### 3.1 启动Redis

启动Redis有直接启动和通过初始化脚本启动两种方式，分别适用于开发环境和生产环境．

##### 3.1.1 直接启动

直接运行redis-server即可启动Redis：
```
xiaosi@yoona:~$ redis-server
11657:C 30 May 21:52:39.810 # Warning: no config file specified, using the default config. In order to specify a config file use redis-server /path/to/redis.conf
11657:M 30 May 21:52:39.813 * Increased maximum number of open files to 10032 (it was originally set to 1024).
                _._                                                  
           _.-``__ ''-._                                             
      _.-``    `.  `_.  ''-._           Redis 3.2.9 (00000000/0) 64 bit
  .-`` .-```.  ```\/    _.,_ ''-._                                   
 (    '      ,       .-`  | `,    )     Running in standalone mode
 |`-._`-...-` __...-.``-._|'` _.-'|     Port: 6379
 |    `-._   `._    /     _.-'    |     PID: 11657
  `-._    `-._  `-./  _.-'    _.-'                                   
 |`-._`-._    `-.__.-'    _.-'_.-'|                                  
 |    `-._`-._        _.-'_.-'    |           http://redis.io        
  `-._    `-._`-.__.-'_.-'    _.-'                                   
 |`-._`-._    `-.__.-'    _.-'_.-'|                                  
 |    `-._`-._        _.-'_.-'    |                                  
  `-._    `-._`-.__.-'_.-'    _.-'                                   
      `-._    `-.__.-'    _.-'                                       
          `-._        _.-'                                           
              `-.__.-'                                               

11657:M 30 May 21:52:39.815 # WARNING: The TCP backlog setting of 511 cannot be enforced because /proc/sys/net/core/somaxconn is set to the lower value of 128.
11657:M 30 May 21:52:39.815 # Server started, Redis version 3.2.9
11657:M 30 May 21:52:39.815 # WARNING overcommit_memory is set to 0! Background save may fail under low memory condition. To fix this issue add 'vm.overcommit_memory = 1' to /etc/sysctl.conf and then reboot or run the command 'sysctl vm.overcommit_memory=1' for this to take effect.
11657:M 30 May 21:52:39.815 # WARNING you have Transparent Huge Pages (THP) support enabled in your kernel. This will create latency and memory usage issues with Redis. To fix this issue run the command 'echo never > /sys/kernel/mm/transparent_hugepage/enabled' as root, and add it to your /etc/rc.local in order to retain the setting after a reboot. Redis must be restarted after THP is disabled.
11657:M 30 May 21:52:39.815 * The server is now ready to accept connections on port 6379

```
Redis服务器默认使用`6379`端口，通过--port参数可以自定义端口号：
```
redis-server --port 6390
```
##### 3.1.2 通过初始化脚本启动Redis

在Linux系统中可以通过初始化脚本启动Redis，使得Redis能随系统自动运行，在生产环境中推荐使用此方法运行Redis．在Redis源代码目录的utils文件夹中有一个名为redis-init-script的初始化脚本文件，内容如下：
```
#!/bin/sh
#
# Simple Redis init.d script conceived to work on Linux systems
# as it does use of the /proc filesystem.

REDISPORT=6379
EXEC=/usr/local/bin/redis-server
CLIEXEC=/usr/local/bin/redis-cli

PIDFILE=/var/run/redis_${REDISPORT}.pid
CONF="/etc/redis/${REDISPORT}.conf"

case "$1" in
    start)
        if [ -f $PIDFILE ]
        then
                echo "$PIDFILE exists, process is already running or crashed"
        else
                echo "Starting Redis server..."
                $EXEC $CONF
        fi
        ;;
    stop)
        if [ ! -f $PIDFILE ]
        then
                echo "$PIDFILE does not exist, process is not running"
        else
                PID=$(cat $PIDFILE)
                echo "Stopping ..."
                $CLIEXEC -p $REDISPORT shutdown
                while [ -x /proc/${PID} ]
                do
                    echo "Waiting for Redis to shutdown ..."
                    sleep 1
                done
                echo "Redis stopped"
        fi
        ;;
    *)
        echo "Please use start or stop as first argument"
        ;;
esac
```
我们需要配置Redis的运行方式和持久化文件，日志文件的存储位置等，具体步骤如下：
(1) 配置初始化脚本
首先将初始化脚本复制到`/etc/init.d`目录下，文件名为`redis_端口号`，其中端口号表示要让Redis监听的端口号，客户端通过该端口连接Redis
```
xiaosi@yoona:~/opt/redis-3.2.9/utils$ sudo cp redis_init_script /etc/init.d/
xiaosi@yoona:/etc/init.d$ sudo mv redis_init_script redis_6379
```
然后修改第六行的REDISPORT变量的值为同样的端口号
```
REDISPORT=6379
```
(2) 建立需要的文件夹

建立如下表列出的目录：

目录名 | 说明
---|---
/etc/redis | 存放Redis的配置文件
/var/redis/端口号 | 存放Redis的持久化文件

```
xiaosi@yoona:~$ sudo mkdir /etc/redis
xiaosi@yoona:~$ sudo mkdir /var/redis
xiaosi@yoona:~$ sudo mkdir /var/redis/6379
```
(3) 修改配置文件

首先将配置文件模板复制到`/etc/redis`目录中，以端口号命名(例如，"6379.conf")，然后按照下标对其中的部分参数进行编辑：

```
xiaosi@yoona:~/opt/redis-3.2.9$ sudo cp redis.conf /etc/redis/
xiaosi@yoona:/etc/redis$ sudo mv redis.conf 6379.conf
```


参数 | 值 | 说明
---|---|---
daemonize | yes | 使Redis以守护进程模式运行
pidfile |/var/run/redis_端口号.pid | 设置Redis的PID文件位置
port | 端口号 | 设置Redis监听的端口号
dir | /var/redis/端口号| 设置持久化文件存放位置

现在就可以使用`/etc/init.d/redis_端口号 start` 来启动Redis，而后需要执行下面的命令使Redis随系统自动启动：
```
sudo update-rc.d redis_端口号　defaults
```

#### 3.2 客户端

可以使用内置的客户端命令redis-cli进行使用:
```
xiaosi@yoona:~$ redis-cli
127.0.0.1:6379> 
```
在上面的提示中，`127.0.0.1`是计算机的IP地址，`6379`是运行Redis服务器的端口。现在键入以下PING命令:

```
127.0.0.1:6379> ping
PONG

```
这表明Redis已成功在您的计算机上安装了。

#### 3.3 停止Redis

考虑到Redis有可能正在将内存中的数据同步到磁盘中，强行终止Redis进程可能会导致数据丢失．正确停止Redis的方式应该是向Redis发送`SHUTDOWN`命令，方法为：
```
redis-cli SHUTDOWN
```
当redis收到`SHUTDOWN`命令后，会先断开所有客户端连接，然后根据配置执行持久化，最后完成退出．




