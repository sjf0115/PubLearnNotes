
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
Hadoop 尝试通过 SSH 连接到 localhost(本地主机)但失败了，可能的原因包括：
- SSH 服务没有在本地运行
- 系统没有安装 SSH 服务
- SSH 配置有问题

分析可能是没有打开系统偏好设置中的共享设置或者系统默认没有安装 openssh-server，我们首先需要确认一下系统偏好设置中的共享设置是否打开。如果打开了，使用如下命令来查看是否只安装了 agent，没有安装 openssh-server：
```shell
wy:.ssh wy$ ps -e | grep ssh
  529 ??         0:00.03 /usr/bin/ssh-agent -l
22005 ttys008    0:00.00 grep ssh
```
看到确实只安装了 agent。既然问题找到了，我们使用如下命令来安装 openssh-server。但是在 macOS 上，不需要单独安装 openssh-server，因为 macOS 已经内置了 SSH 服务器功能（基于 OpenSSH）。你只需要启用它即可。通过系统设置（GUI）
- 打开 系统设置（System Settings）
- 进入 通用（General） > 共享（Sharing）
- 勾选 "远程登录（Remote Login）"

下面重新测试 SSH 连接：
```
ssh localhost
```
如果连接成功，说明 SSH 服务正常。如果提示输入密码，说明 SSH 配置正确，但需要配置[免密登录](https://smartsi.blog.csdn.net/article/details/51689041)（Hadoop 需要）。
