## 1. 背景

在 ZooKeeper 的实际使用中，我们的做法往往是搭建一个共用的 ZooKeeper 集群，统一为若干个应用提供服务。在这种情况下，不同的应用往往是不会存在共享数据的使用场景的，因此需要解决不同应用之间的权限问题。

为了避免存储在 ZooKeeper 服务器上的数据被其他进程干扰或人为操作修改，需要对 ZooKeeper 上的数据访问进行权限控制（Access Control）。ZooKeeper 提供了ACL的权限控制机制，简单的讲，就是通过设置 ZooKeeper 服务器上数据节点的ACL，来控制客户端对该数据节点的访问权限：如果一个客户端符合该ACL控制，那么就可以对其进行访问，否则将无法操作。

开发人员如果要使用 ZooKeeper 的权限控制功能，需要在完成ZooKeeper会话创建后，给该会话添加上相关的权限信息（AuthInfo）。ZooKeeper 客户端提供了相应的API接口来进行权限信息的设置:
```java
addAuthInfo(String scheme, byte[] auth)
```
API方法的参数说明如下表所示:
| 参数名	| 说明 |
| --- | --- |
| scheme | 权限控制模式，分为world、auth、digest、ip和super |
| auth | 具体的权限信息 |

该接口主要用于为当前 ZooKeeper 会话添加权限信息，之后凡是通过该会话对 ZooKeeper 服务端进行的任何操作，都会带上该权限信息。

## 2. 使用包含权限信息的ZooKeeper会话创建数据节点

下面这个示例程序就是对 ZooKeeper 会话添加权限信息的使用方式。在这个示例中，我们采用了 digest 模式，同时可以看到其包含的具体权限信息是 `user1:password1`，这非常类似于 `username:password` 的格式。完成权限信息的添加后，该示例还使用客户端会话在 ZooKeeper 上创建了 `/test/auth-node-1` 节点，这样该节点就受到了权限控制:
```java
package com.zookeeper.example;
import org.apache.zookeeper.*;
import java.io.IOException;

// ZooKeeper权限控制API
public class ZKAuth {
    // 使用包含权限信息的ZooKeeper会话创建数据节点
    public static void authCreate(String path, byte[] data) throws IOException, KeeperException, InterruptedException {
        ZooKeeper zookeeper = new ZooKeeper("localhost:2181", 50000, new Watcher() {
            public void process(WatchedEvent event) {
                Event.KeeperState state = event.getState();
                Event.EventType eventType = event.getType();
                String path = event.getPath();
                System.out.println("KeeperState: " + state.name() + ", EventType: " + eventType.name() + ", path: " + path);
            }
        });
        zookeeper.addAuthInfo("digest", "user1:password1".getBytes());
        // 所有权限
        zookeeper.create(path, data, ZooDefs.Ids.CREATOR_ALL_ACL, CreateMode.PERSISTENT);
    }

    public static void main(String[] args) throws InterruptedException, IOException, KeeperException {
        String path = "/test/auth-node-1";
        byte[] data = "zookeeper auth node 1".getBytes();
        // 权限认证创建节点
        authCreate(path, data);
    }
}
```
我们使用客户端进行验证一下:
```
[zk: 127.0.0.1:2181(CONNECTED) 3] get /test/auth-node-1
Authentication is not valid : /test/auth-node-1
[zk: 127.0.0.1:2181(CONNECTED) 4] addauth digest user1:password1
[zk: 127.0.0.1:2181(CONNECTED) 5] get /test/auth-node-1
zookeeper auth node 1
cZxid = 0x1cfc
ctime = Thu Sep 19 09:55:50 CST 2019
mZxid = 0x1cfc
mtime = Thu Sep 19 09:55:50 CST 2019
pZxid = 0x1cfc
cversion = 0
dataVersion = 0
aclVersion = 0
ephemeralOwner = 0x0
dataLength = 21
numChildren = 0
```
我们看到我们创建的节点受到了权限控制，



...
