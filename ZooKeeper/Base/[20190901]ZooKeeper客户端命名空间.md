chroot 客户端命名空间
zk允许每个客户端为自己设置已给命名空间。如果一个zookeeper客户端设置了Chroot，那么该客户端对服务器的任何操作，都将会被限制在自己的命名空间下。

客户端可以通过在connectString中添加后缀的方式来设置Chroot，如下所示：
192.168.0.1:2181,192.168.0.2:2181,192.168.0.3:2181/apps/X
这个client的chrootPath就是/apps/X
将这样一个connectString传入客户端的ConnectStringParser后就能够解析出Chroot并保存在chrootPath属性中。
