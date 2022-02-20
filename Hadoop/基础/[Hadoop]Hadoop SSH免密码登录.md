---
layout: post
author: sjf0115
title: Hadoop SSH免密码登录
date: 2016-12-29 11:13:01
tags:
  - Hadoop
  - Hadoop 基础

categories: Hadoop
permalink: hadoop-ssh-password-free-login
---

### 1. 创建ssh-key

这里我们采用rsa方式，使用如下命令：
```
xiaosi@xiaosi:~$ ssh-keygen -t rsa -f ~/.ssh/id_rsa
Generating public/private rsa key pair.
Created directory '/home/xiaosi/.ssh'.
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /home/xiaosi/.ssh/id_rsa.
Your public key has been saved in /home/xiaosi/.ssh/id_rsa.pub.
The key fingerprint is:
SHA256:n/sFaAT94A/xxxxxxxxxxxxxxxxxxxxxxx xiaosi@xiaosi
The key's randomart image is:
+---[xxxxx]----+
|        o= .. .. |
|        o.= ..  .|
|         *.* o  .|
|        +.4.=E+..|
|       .SBo=. h+ |
|        ogo..oo. |
|          or +j..|
|          ...+o=.|
|          ... o=+|
+----[xxxxx]-----+
```
备注：
```
这里会提示输入pass phrase，不需要输入任何字符，回车即可。
```

### 2. 生成authorized_keys文件
```
xiaosi@xiaosi:~$ cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
```

记得要把`authorized_keys`文件放到`.ssh`目录下，与`rsa`等文件放在一起，否则免登录失败，debug如下（ssh -vvv localhost进行调试，查找错误原因）：
```
xiaosi@xiaosi:~$ ssh -vvv localhost
OpenSSH_7.2p2 Ubuntu-4ubuntu1, OpenSSL 1.0.2g-fips  1 Mar 2016
debug1: Reading configuration data /etc/ssh/ssh_config
debug1: /etc/ssh/ssh_config line 19: Applying options for *
debug2: resolving "localhost" port 22
debug2: ssh_connect_direct: needpriv 0
debug1: Connecting to localhost [127.0.0.1] port 22.
debug1: Connection established.
debug1: identity file /home/xiaosi/.ssh/id_rsa type 1

...

debug2: we sent a publickey packet, wait for reply
debug3: receive packet: type 51
debug1: Authentications that can continue: publickey,password
debug1: Trying private key: /home/xiaosi/.ssh/id_dsa
debug3: no such identity: /home/xiaosi/.ssh/id_dsa: No such file or directory
debug1: Trying private key: /home/xiaosi/.ssh/id_ecdsa
debug3: no such identity: /home/xiaosi/.ssh/id_ecdsa: No such file or directory
debug1: Trying private key: /home/xiaosi/.ssh/id_ed25519
debug3: no such identity: /home/xiaosi/.ssh/id_ed25519: No such file or directory
debug2: we did not send a packet, disable method
debug3: authmethod_lookup password
debug3: remaining preferred: ,password
debug3: authmethod_is_enabled password
debug1: Next authentication method: password
xiaosi@localhost's password:
```

### 3. 验证
```
xiaosi@xiaosi:~$ ssh localhost
The authenticity of host 'localhost (127.0.0.1)' can't be established.
ECDSA key fingerprint is SHA256:378enl3ckhdpObP8fnsHr1EXz4d1q2Jde+jUplkub/Y.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added 'localhost' (ECDSA) to the list of known hosts.
sign_and_send_pubkey: signing failed: agent refused operation
xiaosi@localhost's password:
```

### 4. authorized_keys权限

我们可以看到还是让我输入密码，很大可能是`authorized_keys`文件权限的问题，我们给该文件赋予一定权限：
```
xiaosi@xiaosi:~$ chmod 600 ~/.ssh/authorized_keys
```
再次验证：
```
xiaosi@xiaosi:~$ ssh localhost
Welcome to Ubuntu 16.04 LTS (GNU/Linux 4.4.0-24-generic x86_64)
 * Documentation:  https://help.ubuntu.com/
0 个可升级软件包。
0 个安全更新。
Last login: Thu Jun 16 08:05:50 2016 from 127.0.0.1
```
到此表示OK了。



备注：
```
第一次需要输入密码，以后再次登陆就不需要输入密码了。
```


有更明白的小伙伴可以指导一下。。。。。。
