---
layout: post
author: sjf0115
title: ZooKeeper ACL权限控制机制
date: 2019-09-28 19:12:45
tags:
  - ZooKeeper

categories: ZooKeeper
permalink: zookeeper-acl-access-permission-control-mechanism
---

ZooKeeper 的 ACL 权限控制和 Unix/Linux 操作系统的ACL有一些区别，我们可以从三个方面来理解 ACL 机制，分别是：权限模式(Scheme)、授权对象(ID)和权限(Permission)，通常使用 `scheme:id:perm` 来标识一个有效的ACL信息。

需要注意的是，ACL仅与指定 `ZNode` 有关，不适用于子节点。例如，如果 `/app` 节点仅可由 `ip:172.16.16.1` 读取，而 `/app/status` 设置为 world 模式，那么任何人都可以读取 `/app/status`。不跟我们想象一样，ACL不是递归的。

## 1. 权限

权限(perm)就是指那些通过权限检查后可以被允许执行的操作。在 ZooKeeper 中，所有对数据的操作权限分为以下五大类：

| 权限 | ACL简写 | 描述 |
| --- | --- | --- |
| CREATE | C | 子节点的创建权限，允许授权对象在该数据节点下创建子节点。|
| DELETE | D | 子节点的删除权限，允许授权对象删除该数据节点的子节点。|
| READ | R | 数据节点的读取权限，允许授权对象访问该数据节点并读取其数据内容或子节点列表等。|
| WRITE | W | 数据节点的更新权限，允许授权对象对该数据节点进行更新操作。|
| ADMIN | A | 数据节点的管理权限，允许授权对象对该数据节点进行ACL相关的设置操作。|

## 2. 授权对象

授权对象(id)指的是权限赋予的用户或一个指定实体，例如IP地址或是机器等。在不同的权限模式下，授权对象是不同的，下表中列出了各个权限模式和授权对象之间的对应关系。

| 权限模式 | 授权对象Id |
| --- | --- |
| IP | 通常是一个IP地址或是IP段，例如 '192.168.0.110”或“192.168.0.1/24' |
| Digest | 自定义，通常是 'username:BASE64(SHA-1(username:password))'，例如 'user2:lo/iTtNMP+gEZlpUNaCqLYO3i5U=' |
| World | 只有一个ID：'anyone' |
| Auth | 该模式不关注授权对象，但必须有 |
| Super | 与Digest模式一致 |


## 3. ACL管理

权限相关命令:

| 命令 | 使用方式 | 描述 |
| --- | --- | --- |
| getAcl | getAcl <path> | 读取 ACL 权限 |
| setAcl | setAcl <path> <acl> | 设置 ACL 权限 |
| addauth | addauth <scheme> <auth> | 添加认证用户 |

### 3.1 设置ACL

通过 zkCli 脚本登录 ZooKeeper 服务器后，可以通过两种方式进行 ACL 的设置。一种是在数据节点创建的同时进行 ACL 权限的设置，命名格式如下：
```
create [-s] [-e] path data acl
```
具体使用如下所示:
```
[zk: 127.0.0.1:2181(CONNECTED) 1] create -e /test/auth-node 'auth scheme node' digest:user1:XDkd2dsEuhc9ImU3q8pa8UOdtpI=:cwrda
Created /test/auth-node
```
另一种方式则是使用 `setAcl` 命名单独对已经存在的数据节点进行 ACL 设置：
```
setAcl path acl
```
具体使用如下所示:
```
[zk: 127.0.0.1:2181(CONNECTED) 2] setAcl /test/auth-node auth:id:crdwa
cZxid = 0x202d
ctime = Sun Sep 22 20:31:31 CST 2019
mZxid = 0x202d
mtime = Sun Sep 22 20:31:31 CST 2019
pZxid = 0x202d
cversion = 0
dataVersion = 0
aclVersion = 1
ephemeralOwner = 0x100009088560218
dataLength = 16
numChildren = 0
```
### 3.2 获取ACL

适用如下方式获取ACL信息：
```
getAcl <path>
```
具体使用如下所示：
```
[zk: 127.0.0.1:2181(CONNECTED) 3] getAcl /test/auth-node
'digest,'user1:XDkd2dsEuhc9ImU3q8pa8UOdtpI=
: cdrwa
```

## 4. 权限模式

权限模式用来确定权限验证中的校验策略。在 ZooKeeper 中，开发人员使用最多的就是以下五种权限模式。

### 4.1 World模式

World 是一种最开放的权限控制模式，从其名字中也可以看出，事实上这种权限控制方式几乎没有任何作用，数据节点的访问权限对所有用户开放，即所有用户都可以在不进行任何权限校验的情况下操作 ZooKeeper 上的数据。另外，World 模式也可以看作是一种特殊的 Digest 模式，它只有一个权限标识，即 `world:anyone`。World 模式只有一个授权对象(`anyone`)，表示世界上任意用户。

我们使用如下命令来设置任何人都可以访问的节点：
```
setAcl /<node-name> world:anyone:crdwa
```
通过正确执行上述操作，我们可以得到如下所示输出：
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ZooKeeper/zookeeper-acl-access-permission-control-mechanism-1.jpg?raw=true)

> world模式创建节点的默认模式。

### 4.2 IP模式

IP 模式表示有相同 IP 地址的任何用户，通过 IP 地址粒度来进行权限控制，例如配置了`ip:192.168.0.110`，即表示权限控制都是针对这个IP地址的。同时，IP 模式也支持按照网段的方式进行配置，例如`ip:192.168.0.1/24`表示针对`192.168.0.*`这个IP段进行权限控制。以下是使用 IP 模式的 `setAcl` 的语法：
```
setAcl /<node-name> ip:<IPv4-address>:<permission-set>
```
使用上面的语法，下面是使用 `127.0.0.1` IP地址的示例：
```
setAcl /test/ip-node ip:127.0.0.1:crdwa
```
通过正确执行上述操作，我们可以得到如下所示输出：
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ZooKeeper/zookeeper-acl-access-permission-control-mechanism-2.jpg?raw=true)

### 4.3 Digest模式

Digest 是最常用的权限控制模式，也更符合我们对于权限控制的认识，其类似于 `username:password` 形式的权限标识来进行权限配置，便于区分不同应用来进行权限控制。

当我们通过 `username:password` 形式配置了权限标识。这里的密码是密文，ZooKeeper 会对其先后进行两次编码处理，分别是SHA-1算法加密和BASE64编码，在 SHELL 中可以通过以下命令计算：
```
echo -n <user>:<password> | openssl dgst -binary -sha1 | openssl base64
```
先来算一个密文密码：
```
smartsi:SmartSi smartsi$ echo -n user-1:password-1 | openssl dgst -binary -sha1 | openssl base64
1g4T1B5w+se9ntA6Ckp90uPaJ30=
```

以下是使用 Digest 模式的 `setAcl` 的语法：
```
setAcl /<node-name> digest:<user-name>:<password>:<permission>
```
使用上面的语法，下面是使用 `user-1:password-1` 示例：
```
setAcl /test/digest-node-1 digest:user-1:1g4T1B5w+se9ntA6Ckp90uPaJ30=:crdwa
```
> `1g4T1B5w+se9ntA6Ckp90uPaJ30=` 为 `password-1` 对应的密文。

通过正确执行上述操作，我们可以得到如下所示输出：
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ZooKeeper/zookeeper-acl-access-permission-control-mechanism-4.jpg?raw=true)

注意的是虽然可以使用明文密码 `user-1:password-1` 设置 ACL(实际上 ZooKeeper 认为 `password-1` 是两次编码处理的密文)，但是获取内容时会没有权限：
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ZooKeeper/zookeeper-acl-access-permission-control-mechanism-3.jpg?raw=true)

### 4.4 Auth模式

Auth 是一种特殊模式，不会对任何授权对象ID进行授权，而是对所有已经添加认证的用户进行授权。持久化 ACL 信息时，ZooKeeper 服务器会忽略 `scheme:id:perm` 中提供的任何授权对象表达式。但是仍必须在 ACL 中提供表达式，可以是一个空串''，或者其他任意字符串，因为 ACL 必须与 `scheme:id:permission` 格式匹配:
```
[zk: 127.0.0.1:2181(CONNECTED) 9] setAcl /test/auth-node auth:crdwa
auth:crdwa does not have the form scheme:id:perm
```
如果没有添加身份认证的用户，那么使用 Auth 模式设置 ACL 会报错。如下所示在我没有提供任何认证用户的情况下：
```
[zk: 127.0.0.1:2181(CONNECTED) 3] setAcl /test/auth-node auth::crdwa
Acl is not valid : /test/auth-node
```
使用此模式的正确用法如下：
```
setAcl /<node-name> auth:<id>:<permission>
```
使用此模式我们可以给多个授权用户使用不同的用户名和密码访问 `ZNode`。假设我们有3个用户：
- user-1:password-1
- user-2:password-2
- user-3:password-3

要注意的一件事是，必须先使用 `addauth` 命令，然后才能继续使用 Auth 模式设置 ACL。如果我们在执行 `addauth` 命令之前设置ACL，就会像上述所示抛出异常：
```
Acl is not valid : /test/auth-node
```
正确的方法是先执行 `addauth` 命令，然后再执行 `setAcl` 命令。以下是 `addauth` 的命令执行语法：
```
addauth digest <username>:<password>
```
通过添加认证用户并相应地设置ACL，可以确保正确设置ACL：
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ZooKeeper/zookeeper-acl-access-permission-control-mechanism-5.jpg?raw=true)

在其他窗口使用对其用户名和密码组合重复上述步骤如下所示：
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ZooKeeper/zookeeper-acl-access-permission-control-mechanism-6.jpg?raw=true)

### 5. Super模式

Super模式，顾名思义就是超级用户的意思，为管理员所使用，这也是一种特殊的 Digest 模式。在 Super 模式下，超级用户可以对任意 ZooKeeper 上的数据节点进行任何操作，不会被任何节点的 ACL 所限制。

根据ACL权限控制的原理，一旦对一个数据节点设置了 ACL 权限控制，那么其他没有被授权的 ZooKeeper 客户端将无法访问该数据节点，这的确很好的保证了 ZooKeeper 的数据安全。但同时，ACL 权限控制也给 ZooKeeper 的运维人员带来了一个困扰：如果一个持久数据节点包含了 ACL 权限控制，而其创建者客户端已经退出或已不再使用，那么这些数据节点该如何清理呢？这个时候，就需要在 ACL 的 Super 模式下，使用超级管理员权限来进行处理了。要使用超级管理员权限，首先需要在 ZooKeeper 服务器上开启 Super 模式，方法是在 ZooKeeper 服务器启动的时候，添加如下系统属性：
```
-Dzookeeper.DigestAuthenticationProvider.superDigest=super:zUZ0bpqYS7FucDXsnUgxOWTto1s=
```
其中，super 代表了一个超级管理员的用户名；`zUZ0bpqYS7FucDXsnUgxOWTto1s=` 是由 ZooKeeper 的系统管理员自主配置密码的两次编码处理后的密文，此例中使用的是 `super:root` 的编码。

打开 ZooKeeper 目录下的 `/bin/zkServer.sh` 服务器脚本，找到如下一行：
```
nohup $JAVA "-Dzookeeper.log.dir=${ZOO_LOG_DIR}" "-Dzookeeper.root.logger=${ZOO_LOG4J_PROP}"
```
默认只有以上两个配置项，我们需要把上述配置项加到服务器脚本中：
```
nohup "$JAVA" "-Dzookeeper.log.dir=${ZOO_LOG_DIR}" "-Dzookeeper.DigestAuthenticationProvider.superDigest=admin:0sxEug2Dpm/NpzMPieOlFREd9Ao=" \
    -cp "$CLASSPATH" $JVMFLAGS $ZOOMAIN "$ZOOCFG" > "$_ZOO_DAEMON_OUT" 2>&1 < /dev/null &
```

完成对 ZooKeeper 服务器的 Super 模式的开启后，重新启动服务器后就可以在应用程序中使用了，下面是一个使用超级管理员权限操作 ZooKeeper 数据节点的示例程序：
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ZooKeeper/zookeeper-acl-access-permission-control-mechanism-7.jpg?raw=true)

从上面输出结果中，我们可以看出，由于 `super:root` 是一个超级管理员，因此能够对一个受权限控制的数据节点 `/test/auth-node` 随意进行操作。但是 `user-3:password-3` 这个普通用户，就无法通过权限验证了。

参考:
- [Apache ZooKeeper – Setting ACL in ZooKeeper Client](https://ihong5.wordpress.com/2014/07/24/apache-zookeeper-setting-acl-in-zookeeper-client/)
