---
layout: post
author: sjf0115
title: Linux rsync命令使用指南
date: 2018-03-20 15:17:17
tags:
  - Linux
  - Linux 命令

categories: Linux
permalink: rsync-command-usage
---

### 1. 概述

`rsync` 命令是一个远程数据同步工具，可通过 LAN/WAN 快速同步多台主机间的文件。`rsync` 使用所谓的 "rsync算法" 来使本地和远程两个主机之间的文件达到同步，这个算法只传送两个文件的不同部分，而不是每次都整份传送，因此速度相当快。`rsync` 是一个功能非常强大的工具，其命令也有很多功能特色选项。

### 2. 安装与配置

请参考：

### 3. 语法
```
rsync [OPTION...] SRC... [DEST]

rsync [OPTION...] [USER@]HOST:SRC... [DEST]

rsync [OPTION...] SRC... [USER@]HOST:DEST

rsync [OPTION...] [USER@]HOST::SRC... [DEST]
rsync [OPTION...] rsync://[USER@]HOST[:PORT]/SRC... [DEST]

rsync [OPTION...] SRC... [USER@]HOST::DEST
rsync [OPTION...] SRC... rsync://[USER@]HOST[:PORT]/DEST
```

#### 3.1 本地模式

```
rsync [OPTION...] [USER@]HOST:SRC... [DEST]
```
拷贝本地文件。当 SRC 和 DEST 路径信息都不包含有单个冒号 `:` 分隔符时就启动这种工作模式。例如：
```
xiaosi@ying:~$ rsync -a adv_push adv_push_backup/
xiaosi@ying:~$ ll adv_push_backup/
总用量 20
drwxrwxr-x  3 xiaosi xiaosi  4096  3月 20 15:29 ./
drwxr-xr-x 83 xiaosi xiaosi 12288  3月 20 15:29 ../
drwxrwxr-x  2 xiaosi xiaosi  4096  3月 20 15:28 adv_push/
```

#### 3.2 通过远程Shell访问-Pull

```
rsync [OPTION...] [USER@]HOST:SRC... [DEST]
```
使用一个远程Shell程序(如rsh、ssh)来实现将远程机器的内容拷贝到本地机器。当 SRC 地址路径包含单个冒号 `:` 分隔符时启动该模式。例如：
```
xiaosi@ying:~$ rsync -a ubuntu@xxx.xxx.xxx.xxx:test/remote_content.txt /home/xiaosi/data/share/
ubuntu@xxx.xxx.xxx.xxx's password:
```
在本地机器上查看从服务器拷贝到本地上的文件：
```
xiaosi@ying:~$ cd /home/xiaosi/data/share/
xiaosi@ying:~/data/share$ ll
总用量 12
drwxrwxr-x  2 xiaosi xiaosi 4096  3月 20 19:41 ./
drwxr-xr-x 14 xiaosi xiaosi 4096  3月 20 19:24 ../
-rw-rw-r--  1 xiaosi xiaosi   17  3月 20 15:57 remote_content.txt
```

> ubuntu@xxx.xxx.xxx.xxx 中 ubuntu 是服务器登录名  xxx.xxx.xxx.xxx 是服务器IP地址  password 是服务器登录名 ubuntu 对应的密码

> 以 Shell 方式访问，首先在服务端启动 ssh 服务： service sshd start

#### 3.3 通过远程Shell访问-Push

```
rsync [OPTION...] SRC... [USER@]HOST:DEST
```
使用一个远程shell程序(如rsh、ssh)来实现将本地机器的内容拷贝到远程机器。当 DEST 路径地址包含单个冒号 `:` 分隔符时启动该模式。例如：
```
xiaosi@ying:~$ rsync -a /home/xiaosi/data/exception.txt ubuntu@xxx.xxx.xxx.xxx:tmp
ubuntu@xxx.xxx.xxx.xxx's password:
```
在服务器上查看从本地拷贝到服务器上的文件：
```
ubuntu@VM-0-7-ubuntu:~/tmp$ ll
total 24
drwxrwxr-x  5 ubuntu ubuntu 4096 Mar 20 19:34 ./
drwxr-xr-x 11 ubuntu ubuntu 4096 Mar 20 19:32 ../
...
-rw-rw-r--  1 ubuntu ubuntu   80 Mar 20 11:03 exception.txt
...
```

> ubuntu@xxx.xxx.xxx.xxx 中 ubuntu 是服务器登录名  xxx.xxx.xxx.xxx 是服务器IP地址  password 是服务器登录名 ubuntu 对应的密码

> 以 Shell 方式访问，首先在服务端启动 ssh 服务： service sshd start

#### 3.4 通过rsync进程访问-Pull

```
rsync [OPTION...] [USER@]HOST::SRC... [DEST]
rsync [OPTION...] rsync://[USER@]HOST[:PORT]/SRC... [DEST]
```
从远程 rsync 服务器中拷贝文件到本地机。当 SRC 路径信息包含 `::` 分隔符时启动该模式。例如：
```
xiaosi@ying:~$ rsync -a test@xxx.xxx.xxx.xxx::share/remote_content.txt /home/xiaosi/data/share
```
在本地机器上查看从服务器拷贝到本地上的文件：
```
xiaosi@ying:~/data/share$ ll
总用量 12
drwxrwxr-x  2 xiaosi xiaosi 4096  3月 20 19:06 ./
drwxr-xr-x 14 xiaosi xiaosi 4096  3月 20 19:06 ../
-rw-r--r--  1 xiaosi xiaosi   17  3月 20 18:44 remote_content.txt
```

> 以后台服务方式访问 请参考：[Linux rsync配置指南](http://smartsi.club/2018/03/20/rsync-config-usage/)

> test@xxx.xxx.xxx.xxx 中 test 是以后台方式访问配置的用户

#### 3.5 通过rsync进程访问-Push

```
rsync [OPTION...] SRC... [USER@]HOST::DEST
rsync [OPTION...] SRC... rsync://[USER@]HOST[:PORT]/DEST
```
从本地机器拷贝文件到远程 rsync 服务器中。当 DEST 路径信息包含 `::` 分隔符时启动该模式。例如：
```
xiaosi@ying:~$ rsync -a  /home/xiaosi/data/sources.list.backup  test@xxx:xxx:xxx:xxx::share/config
```
在服务器上查看从本地拷贝到服务器上的文件：
```
ubuntu@VM-0-7-ubuntu:/home/share/config$ ll
total 12
drwxr-xr-x 2 root root 4096 Mar 20 19:02 ./
drwxr-xr-x 3 root root 4096 Mar 20 19:02 ../
-rw-r--r-- 1 root root 2981 Mar 20 16:30 sources.list.backup
```

> 以后台服务方式访问 请参考：[Linux rsync配置指南](http://smartsi.club/2018/03/20/rsync-config-usage/)

> test@xxx.xxx.xxx.xxx 中 test 是以后台方式访问配置的用户

#### 3.6 查阅模式

只使用一个 SRC 参数，而不使用 DEST 参数将列出源文件而不是进行复制。例如：
```
xiaosi@ying:~$ rsync -a adv_push
drwxrwxr-x          4,096 2018/03/20 15:28:15 adv_push
-rw-rw-r--            353 2018/03/14 17:02:35 adv_push/adv_push_20180307.txt
-rw-rw-r--            353 2018/03/14 17:02:33 adv_push/adv_push_20180308.txt
```

### 4. 选项

```
-v, --verbose 详细模式输出。
-q, --quiet 精简输出模式。
-c, --checksum 打开校验开关，强制对文件传输进行校验。
-a, --archive 归档模式，表示以递归方式传输文件，并保持所有文件属性，等于-rlptgoD。
-r, --recursive 对子目录以递归模式处理。
-R, --relative 使用相对路径信息。
-b, --backup 创建备份，也就是对于目的已经存在有同样的文件名时，将老的文件重新命名为~filename。可以使用--suffix选项来指定不同的备份文件前缀。
--backup-dir 将备份文件(如~filename)存放在在目录下。
-suffix=SUFFIX 定义备份文件前缀。
-u, --update 仅仅进行更新，也就是跳过所有已经存在于DST，并且文件时间晚于要备份的文件，不覆盖更新的文件。
-l, --links 保留软链结。
-L, --copy-links 想对待常规文件一样处理软链结。
--copy-unsafe-links 仅仅拷贝指向SRC路径目录树以外的链结。
--safe-links 忽略指向SRC路径目录树以外的链结。
-H, --hard-links 保留硬链结。
-p, --perms 保持文件权限。
-o, --owner 保持文件属主信息。
-g, --group 保持文件属组信息。
-D, --devices 保持设备文件信息。
-t, --times 保持文件时间信息。
-S, --sparse 对稀疏文件进行特殊处理以节省DST的空间。
-n, --dry-run现实哪些文件将被传输。
-w, --whole-file 拷贝文件，不进行增量检测。
-x, --one-file-system 不要跨越文件系统边界。
-B, --block-size=SIZE 检验算法使用的块尺寸，默认是700字节。
-e, --rsh=command 指定使用rsh、ssh方式进行数据同步。
--rsync-path=PATH 指定远程服务器上的rsync命令所在路径信息。
-C, --cvs-exclude 使用和CVS一样的方法自动忽略文件，用来排除那些不希望传输的文件。
--existing 仅仅更新那些已经存在于DST的文件，而不备份那些新创建的文件。
--delete 删除那些DST中SRC没有的文件。
--delete-excluded 同样删除接收端那些被该选项指定排除的文件。
--delete-after 传输结束以后再删除。
--ignore-errors 及时出现IO错误也进行删除。
--max-delete=NUM 最多删除NUM个文件。
--partial 保留那些因故没有完全传输的文件，以是加快随后的再次传输。
--force 强制删除目录，即使不为空。
--numeric-ids 不将数字的用户和组id匹配为用户名和组名。
--timeout=time ip超时时间，单位为秒。
-I, --ignore-times 不跳过那些有同样的时间和长度的文件。
--size-only 当决定是否要备份文件时，仅仅察看文件大小而不考虑文件时间。
--modify-window=NUM 决定文件是否时间相同时使用的时间戳窗口，默认为0。
-T --temp-dir=DIR 在DIR中创建临时文件。
--compare-dest=DIR 同样比较DIR中的文件来决定是否需要备份。
-P 等同于 --partial。
--progress 显示备份过程。
-z, --compress 对备份的文件在传输时进行压缩处理。
--exclude=PATTERN 指定排除不需要传输的文件模式。
--include=PATTERN 指定不排除而需要传输的文件模式。
--exclude-from=FILE 排除FILE中指定模式的文件。
--include-from=FILE 不排除FILE指定模式匹配的文件。
--version 打印版本信息。
--address 绑定到特定的地址。
--config=FILE 指定其他的配置文件，不使用默认的rsyncd.conf文件。
--port=PORT 指定其他的rsync服务端口。
--blocking-io 对远程shell使用阻塞IO。
-stats 给出某些文件的传输状态。
--progress 在传输时现实传输过程。
--log-format=formAT 指定日志文件格式。
--password-file=FILE 从FILE中得到密码。
--bwlimit=KBPS 限制I/O带宽，KBytes per second。
-h, --help 显示帮助信息。
```


参考: http://man.linuxde.net/rsync
