
在启动 Hadoop 服务的时候报如下问题：
```shell
wy:hadoop wy$ ./sbin/start-dfs.sh
20/08/29 23:01:54 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
Starting namenodes on [localhost]
localhost: ssh: connect to host localhost port 22: Connection refused
localhost: ssh: connect to host localhost port 22: Connection refused
Starting secondary namenodes [0.0.0.0]
0.0.0.0: ssh: connect to host 0.0.0.0 port 22: Connection refused
20/08/29 23:01:57 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
```
从上面看到 SSH 有问题，再重新验证一下：
```
wy:.ssh wy$ ssh localhost
ssh: connect to host localhost port 22: Connection refused
```
分析可能是没有打开系统偏好设置中的共享设置或者系统默认没有安装 openssh-server，我们首先需要确认一下系统偏好设置中的共享设置是否打开。如果打开了，使用如下命令来查看是否只安装了 agent，没有安装 openssh-server：
```shell
wy:.ssh wy$ ps -e | grep ssh
  529 ??         0:00.03 /usr/bin/ssh-agent -l
22005 ttys008    0:00.00 grep ssh
```
看到确实只安装了 agent。既然问题找到了，我们使用如下命令来安装 openssh-server：
```

```
