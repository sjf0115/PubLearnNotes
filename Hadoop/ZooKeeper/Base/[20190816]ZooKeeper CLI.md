---
layout: post
author: xpproen
title: ZooKeeper CLI
date: 2019-08-16 13:21:45
tags:
  - ZooKeeper

categories: ZooKeeper
permalink: how-to-use-cki-in-zookeeper
---

ZooKeeper 命令行界面（CLI）用于与 ZooKeeper 集合进行交互以进行开发。它有助于调试和解决不同的选项。要执行 ZooKeeper CLI 操作，首先打开 ZooKeeper 服务器（`bin/zkServer.sh start`），然后打开 ZooKeeper 客户端（`bin/zkCli.sh`）。客户端启动后，你就可以执行以下操作：
- 创建ZNode
- 获取数据
- 监视ZNode的变化
- 设置数据
- 创建ZNode的子节点
- 列出ZNode的子节点
- 检查状态
- 移除/删除ZNode

现在让我们用一个例子逐个了解上面的命令。

### 1. 创建ZNode

用给定的路径创建一个 `znode`。用 flag 参数标示创建的这个 `znode` 是临时的，持久的还是顺序的。默认情况下，所有 `znode` 都是持久的。当会话过期或客户端断开连接时，临时节点（flag：-e）会被自动删除。

顺序节点保证 `znode` 路径必须是唯一的。

ZooKeeper 集合向 `znode` 路径填充10位序列号。例如，`znode` 路径 `/myapp` 将转换为 `/myapp0000000001`，下一个序列号为 `/myapp0000000002`。如果没有指定 flag，`znode` 被认为是持久的。

#### 1.1 持久ZNode

语法：
```
create /path /data
```
示例：
```
create /first_znode "my zookeeper first znode"
```
输出：
```
[zk: 192.34.15.82:2181(CONNECTED) 1] create /first_znode "my zookeeper first znode"        
Created /first_znode
```

#### 1.2 顺序ZNode

要创建顺序节点，请添加 `flag：-s`，如下所示。

语法：
```
create -s /path /data
```
示例：
```
create -s /first_znode "my zookeeper second znode"
```
输出：
```
[zk: 192.34.15.82:2181(CONNECTED) 2] create -s /first_znode "my zookeeper second znode"
Created /first_znode0000000001
```

#### 1.3 临时ZNode

要创建临时节点，请添加 `flag：-e`，如下所示。

语法：
```
create -e /path /data
```
示例：
```
create -e /second_znode "my zookeeper tmp znode"
```
输出：
```
[zk: 192.34.15.82:2181(CONNECTED) 3] create -e /second_znode "my zookeeper tmp znode"
Created /second_znode
```

> 当客户端断开连接时，临时节点会被删除。你可以通过退出 ZooKeeper CLI，然后重新打开 CLI 来尝试。

### 2. 获取数据

返回 `znode` 的相关数据以及指定 `znode` 的元数据。你会获得一些信息，例如，上次修改数据的时间，修改位置以及数据的相关信息。CLI 还用于分配监视器以显示数据相关的通知。

语法：
```
get /path
```
示例：
```
get /first_znode
```
输出：
```
[zk: 192.34.15.82:2181(CONNECTED) 5] get /first_znode
my zookeeper first znode
cZxid = 0x100000003
ctime = Tue Aug 14 12:52:36 CST 2018
mZxid = 0x100000003
mtime = Tue Aug 14 12:52:36 CST 2018
pZxid = 0x100000003
cversion = 0
dataVersion = 0
aclVersion = 0
ephemeralOwner = 0x0
dataLength = 24
numChildren = 0
```
要访问顺序节点，必须输入 `znode` 的完整路径。

示例：
```
get /first_znode0000000001
```
输出：
```
[zk: 10.86.218.105:2181(CONNECTED) 6] get /first_znode0000000001
my zookeeper second znode
cZxid = 0x100000004
ctime = Tue Aug 14 12:56:15 CST 2018
mZxid = 0x100000004
mtime = Tue Aug 14 12:56:15 CST 2018
pZxid = 0x100000004
cversion = 0
dataVersion = 0
aclVersion = 0
ephemeralOwner = 0x0
dataLength = 25
numChildren = 0
```

### 3. Watch（监视）

当指定的 `znode` 或子 `znode` 发生变化时，监视器会显示通知。你只能在 get 命令中设置 watch。

语法：
```
get /path [watch] 1
```
示例：
```
get /first_znode 1
```
输出：
```
[zk: 10.86.218.105:2181(CONNECTED) 7] get /first_znode 1
my zookeeper first znode
cZxid = 0x100000003
ctime = Tue Aug 14 12:52:36 CST 2018
mZxid = 0x100000003
mtime = Tue Aug 14 12:52:36 CST 2018
pZxid = 0x100000003
cversion = 0
dataVersion = 0
aclVersion = 0
ephemeralOwner = 0x0
dataLength = 24
numChildren = 0
```
输出类似于普通的 get 命令，但它会在后台等待节点改变。

### 4. 设置数据

设置指定 `znode` 的数据。完成此操作后，你可以使用 get CLI 命令检查数据。

语法：
```
set /path /data
```
示例：
```
set /second_znode "update my zookeeper second znode"
```
输出：
```
[zk: 10.86.218.105:2181(CONNECTED) 10] set /second_znode "update my zookeeper second znode"
cZxid = 0x100000007
ctime = Tue Aug 14 13:05:08 CST 2018
mZxid = 0x100000008
mtime = Tue Aug 14 13:05:44 CST 2018
pZxid = 0x100000007
cversion = 0
dataVersion = 1
aclVersion = 0
ephemeralOwner = 0x0
dataLength = 32
numChildren = 0
```
如果你在 get 命令中设置了 watch 选项（如上一个命令），则输出将类似如下所示：
```
[zk: 10.86.218.105:2181(CONNECTED) 13] set /second_znode 1

WATCHER::cZxid = 0x100000007


WatchedEvent state:SyncConnected type:NodeDataChanged path:/second_znode
ctime = Tue Aug 14 13:05:08 CST 2018
mZxid = 0x100000009
mtime = Tue Aug 14 13:06:54 CST 2018
pZxid = 0x100000007
cversion = 0
dataVersion = 2
aclVersion = 0
ephemeralOwner = 0x0
dataLength = 1
numChildren = 0
```

### 5. 创建子节点

创建子节点类似于创建新的 `znode`。唯一的区别是，子 `znode` 的路径必须包含父路径。

语法：
```
create /parent/path/subnode/path /data
```
示例：
```
create /first_znode/first_child_znode first_children
```
输出：
```
[zk: 10.86.218.105:2181(CONNECTED) 14] create /first_znode/first_child_znode first_children    
Created /first_znode/first_child_znode
```

### 6. 列出子项

该命令用于列出和展示子 `znode`。

语法：
```
ls /path
```
示例：
```
ls /first_znode
```
输出：
```
[zk: 10.86.218.105:2181(CONNECTED) 15] ls /first_znode
[first_child_znode]
```

### 7. 检查状态

状态描述了指定的 `znode` 的元数据。包含了时间戳，版本号，ACL，数据长度和子 `znode` 等详细信息。

语法：
```
stat /path
```
示例：
```
stat /first_znode
```
输出：
```
[zk: 10.86.218.105:2181(CONNECTED) 16] stat /first_znode
cZxid = 0x100000003
ctime = Tue Aug 14 12:52:36 CST 2018
mZxid = 0x100000003
mtime = Tue Aug 14 12:52:36 CST 2018
pZxid = 0x10000000a
cversion = 1
dataVersion = 0
aclVersion = 0
ephemeralOwner = 0x0
dataLength = 24
numChildren = 1
```

### 8. 删除Znode

删除指定的 `znode` 以及递归删除其所有子节点。这只有在 `znode` 可用时发生。

语法：
```
rmr /path
```
示例：
```
rmr /third_znode
```
输出：
```
[zk: 10.86.218.105:2181(CONNECTED) 18] create /third_znode "my zookeeper third znode"
Created /third_znode
[zk: 10.86.218.105:2181(CONNECTED) 19] rmr /third_znode
[zk: 10.86.218.105:2181(CONNECTED) 20] get /third_znode
Node does not exist: /third_znode
```
删除(delete/path)命令类似于 remove 命令，但它只适用于没有子节点的 `znode`。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

原文：[ZooKeeper CLI](https://www.w3cschool.cn/zookeeper/zookeeper_cli.html)
