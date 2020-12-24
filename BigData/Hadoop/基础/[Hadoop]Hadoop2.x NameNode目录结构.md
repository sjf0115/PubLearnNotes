
### 1. 目录结构

`NameNode`被格式化(`hdfs namenode -format`)之后，将会在`dfs.namenode.name.dir`配置属性所指定目录(在这里为`/tmp/hadoop-xiaosi/dfs/name`)下的`/current`目录生成如下的目录结构:

```
xiaosi@ying:/tmp/hadoop-xiaosi/dfs/name$ tree -L 2
.
└── current
    ├── fsimage_0000000000000000000
    ├── fsimage_0000000000000000000.md5
    ├── seen_txid
    └── VERSION

1 directory, 4 files
```

备注:

`dfs.namenode.name.dir`属性在`hdfs-site.xml`配置文件中配置：
```
<property>
   <name>dfs.namenode.name.dir</name>
   <value>file://${hadoop.tmp.dir}/dfs/name</value>
</property>
```
`hadoop.tmp.dir`属性在`core-site.xml`配置文件中配置:
```
<property>
   <name>hadoop.tmp.dir</name>
   <value>/tmp/hadoop-${user.name}</value>
</property>
```

### 2. 配置路径

`dfs.namenode.name.dir`属性可以指定目录(以逗号分隔的目录名称)来供`NameNode`存储永久性的文件系统的元数据(编辑日志和`fsimage`)。这些元数据会同时备份在指定的所有目录中。通常情况下，通过配置`dfs.namenode.name.dir`属性可以将`NameNode`元数据写到一两个本地磁盘和一个远程磁盘(例如，`NFS`挂载的目录)之中。这样的话，即使本地磁盘发生故障，甚至整个`NameNode`发生故障，都可以恢复元数据文件并且重构新的`NameNode`。

备注:
```
辅助NameNode只是定期保存NameNode的检查点，不维护NameNode的最新备份。
```

### 3. VERSION文件

`VERSION`文件是一个`Java`属性文件，其中包含正在运行的`HDFS`的版本信息，该文件一般包含如下内容:
```
xiaosi@ying:/tmp/hadoop-xiaosi/dfs/name/current$ cat VERSION
#Tue Dec 19 17:58:10 CST 2017
namespaceID=883735112
clusterID=CID-194479c8-4405-4d5a-9bfb-c17406f53a23
cTime=0
storageType=NAME_NODE
blockpoolID=BP-1359930363-127.0.0.1-1513677490659
layoutVersion=-63
```


(1) `namespaceID`是文件系统的唯一标识符，是在文件系统首次格式化时设置的。任何`DataNode`在注册到`NameNode`之前都不知道`namespaceID`，因此`NameNode`可以使用该属性鉴别新建的`DataNode`。

(2) `clusterID`是集群ID。当格式化一个`Namenode`时，这个`ClusterID`会自动生成或者手动提供。

(3) `cTime`是`NameNode`存储系统的创建时间。对刚格式化的存储系统，这个值为0。但在文件系统升级后该值会更新到新的时间戳。

(4) `storageType`说明这个存储目录包含的是`NameNode`的数据结构。

(5) `blockpoolID`是针对每一个`Namespace`所对应的`blockpool`的`ID`，上面的这个`BP-1359930363-127.0.0.1-1513677490659`就是存储块池的ID，这个ID包括了其对应的`NameNode`节点的IP地址。

(6) `layoutVersion`是一个负整数，描述了`HDFS`持久化数据结构的版本(也称为布局)。需要注意的是，这个版本号与`Hadoop`发布包的版本没有关系。只要布局变更，版本号就会递减(例如，版本号为-18，下一个版本号为-19)，此时`HDFS`也需要升级。否则磁盘仍然使用旧的版本的布局，新版本的`NameNode`和`DataNode`就无法正常工作了。


备注:
```
namespaceID/clusterID/blockpoolID，这三个ID在整个HDFS集群中全局唯一，作用是引导DataNode加入同一个集群。在HDFS Federation机制下，会有多个NameNode，所以不同NameNode之间namespaceID是不同的，分别管理一组blockpoolID，但是整个集群中，clusterID是唯一的，每次format namenode会生成一个新的，也可以使用-clusterid手工指定ID
```

### 4. fsimage与编辑日志

`fsimage`文件是文件系统元数据的一个快照。并非每个写操作都会更新该文件，文件客户端执行写操作时，这些操作首先被记录在编辑日志中。如果`NameNode`发生故障，可以先把`fsimage`文件载入到内存中，重构最近的元数据，再执行编辑日志中记录的各项操作。

### 5. seen_txid

存放`transactionID`，格式化文件系统后这个数字是0，代表一系列`edits_*`文件的尾数，`NameNode`重启时会循环从0001到`seen_txid`中的数字，`HDFS`重启时会比对这个数字是不是edits文件的尾数，如果不是的话可能会有元数据丢失。

参考: Hadoop  权威指南
