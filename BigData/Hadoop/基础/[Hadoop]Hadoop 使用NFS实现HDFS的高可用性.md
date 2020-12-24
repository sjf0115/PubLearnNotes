
### 1. 目标

这篇文章了讲述了`HDFS`高可用性`HA`功能以及如何使用`NFS`作为`NameNodes`的共享存储来配置和管理`HA` `HDFS`群集。

这篇文章假设读者对`HDFS`集群中的通用组件和节点类型有一个大体的了解。有关详细信息，请参阅[HDFS架构](http://smartying.club/2017/12/20/Hadoop/Hadoop2.x%20HDFS%E6%9E%B6%E6%9E%84/)。

### 2. 背景

在`Hadoop 2.0.0`之前，`NameNode`是`HDFS`集群中的单点故障(`SPOF`)。每个群集都只有一个`NameNode`，如果`NameNode`所在节点或所在进程不可用，那么整个集群将变的不可用，直到`NameNode`重新启动或在另一个节点上启动。

主要有两个主要方面影响了`HDFS`集群的总体可用性：

- 意外情况下(例如机器崩溃)，集群将不可用，直到操作员重新启动`NameNode`。
- 计划内的运维情况下(如`NameNode`所在节点上的软件或硬件升级)将导致集群停机一段时间。

`HDFS`高可用性功能通过提供具有热备份的`Active`/`Passive`配置，在同一个集群中运行两个冗余`NameNode`来解决上述问题。这允许在节点崩溃的情况下快速故障切换到新的`NameNode`，或为了计划内运维管理员发起的正常切换。

### 3. 架构

在典型的`HA`集群中，两台独立的机器被配置为`NameNode`。在任何时候，只有一个`NameNode`处于`Active`状态，另一个处于`Standby`状态。`Active`状态的`NameNode`负责集群中的所有客户端操作，而`Passive`状态的`NameNode`仅充当备份`NameNode`，并保存全部的状态在必要时提供快速故障转移。

为了使`Standby`节点与`Active`节点保持同步状态，目前的实现是两个节点都可以访问共享存储设备上的目录(例如，从`NAS`上挂载`NFS`)。未来版本可能会放宽这个限制。

当`Active`节点执行关于命名空间的任何修改时，它都将修改记录持久化存储到共享存储目录中的编辑日志文件中。`Standby`节点不断地监视这个目录，当看到修改时，它将它们应用到它自己的命名空间。在需要故障切换时，`Standby`状态节点在自己切换为`Active`状态之前确保从共享存储目录中已经读取所有的编辑日志。这确保了在故障切换发生之前命名空间状态已经完全同步。

为了提供快速故障切换，`Standby`节点还需要拿到有关于集群中块位置的最新信息。为了实现这一点，`DataNode`配置了两个`NameNode`的位置，并发送块位置信息和心跳给这两个。

对于`HA`集群的正确操作来说只有一个`NameNode`处于`Active`状态至关重要。否则，命名空间状态将很快在两者之间发生分歧，从而可能导致数据丢失或其他不正确的结果。为了确保此属性并防止所谓的`脑裂情形`，管理员必须至少为共享存储配置一种`fencing`方法。在故障转移期间，如果无法验证上一个`Active`节点是否离开`Active`状态，那么守护进程负责切断前一个`Active`节点对共享存储的访问。这样可以防止对命名空间进行任何的编辑，从而使新的`Active`节点安全地进行故障转移。

### 4. 硬件资源

为了部署`HA`集群，需要准备以下内容：

- `NameNode`机器 - 运行`Active`和`Standby`的`NameNode`机器应该具有相同的硬件，以及使用与在非`HA`集群中相同的硬件。
- 共享存储 - 需要有一个共享目录，这两个`NameNode`机器都有权限进行读取/写入。通常这是一个支持`NFS`的远程文件管理器，并挂载在每个`NameNode`机器上。目前只支持一个共享编辑目录(`shared edits directory`)。因此，系统的可用性受到共享编辑目录的可用性的限制，因此为了除去所有单点故障，共享编辑目录需要冗余。具体而言，多个网络路径可供存储以及存储本身(磁盘，网络和电源)中的冗余(multiple network paths to the storage, and redundancy in the storage itself)。因此，建议共享存储服务器是高可用的专用`NAS`设备，而不是简单的`Linux`服务器。

请注意，在`HA`集群中，`Standby` `NameNode`也会执行命名空间状态的检查点，因此不需要在`HA`进群中运行`Secondary NameNode`，`CheckpointNode`或`BackupNode`，事实上如果这样做将会是一个错误。这也允许正在重新配置未启用`HA`的`HDFS`群集启用`HA`时会重用之前专用于`Secondary NameNode`的硬件。

### 5. 部署

#### 5.1 配置概述

与`HDFS Federation`配置类似，`HA`配置也会向后兼容，并允许现有的单一`NameNode`配置无需更改也可工作。新配置被设计成这样使得集群中的所有节点可以具有相同的配置，而没有必要根据节点的类型为不同的机器部署不同的配置文件。

与`HDFS Federation`相似，`HA`集群重用名称服务ID(`nameservice ID`)来标识一个`HDFS`实例，实际上可能由多个`HA NameNode`组成。另外，一个名为`NameNode ID`的新抽象概念被添加到`HA`中。集群中不同的`NameNode`都用一个不同的`NameNode ID`来区分它。为了支持一个配置文件支持所有`NameNode`，相关的配置参数后缀名称带有名字服务ID以及`NameNode ID`。

#### 5.2 详细配置

要配置`HA NameNode`，必须将多个配置选项添加到`hdfs-site.xml`配置文件。

这些配置的配置顺序无关紧要，但是为`dfs.nameservices`和`dfs.ha.namenodes.[nameservice ID]`选择的值将决定后面的那些配置的`key`。因此，在设置其它配置选项之前，应该先确定这些值。

##### 5.2.1 `dfs.nameservices`

新`nameservice`的逻辑名称。为`nameservice`选择一个逻辑名称，例如`mycluster`，使用此逻辑名称作为此配置选项的值。你选择的名称可以是任意的。它将会用于配置中，也用作集群中authority组件的`HDFS`绝对路径。

注意：如果你还在使用`HDFS Federation`，那么此配置设置还应该将其他`nameservice`，`HA`或其他的，以逗号分隔的列表。

```
<property>
  <name>dfs.nameservices</name>
  <value>mycluster</value>
</property>
```

##### 5.2.2 `dfs.ha.namenodes.[nameservice ID]`

`nameservice`中每个`NameNode`的唯一标识符。使用逗号分隔的`NameNode ID`进行配置。这将由`DataNodes`来确定集群中的所有`NameNode`。例如，如果前面使用`mycluster`作为`nameservice`的标识，并且想要使用`nn1`和`nn2`作为`NameNode`的单独标识，则可以这样配置：

```
<property>
  <name>dfs.ha.namenodes.mycluster</name>
  <value>nn1,nn2</value>
</property>
```

备注:
```
目前，每个nameservice最多只能配置两个NameNode。
```

##### 5.2.3 `dfs.namenode.rpc-address.[nameservice ID].[name node ID]`

每个`NameNode`监听的全限定`RPC`地址。对于之前配置的那两个`NameNode ID`，需要设置`NameNode`进程的完整地址和IPC端口。 注意的是，这会导致需要配置两个单独的配置选项。例如：

```
<property>
  <name>dfs.namenode.rpc-address.mycluster.nn1</name>
  <value>machine1.example.com:8020</value>
</property>
<property>
  <name>dfs.namenode.rpc-address.mycluster.nn2</name>
  <value>machine2.example.com:8020</value>
</property>
```

备注:
```
上面是为namenode配置的，如果愿意，可以类似地为nameservice配置servicerpc-address。
```

##### 5.2.4 `dfs.namenode.http-address.[nameservice ID].[name node ID]`

每个`NameNode`监听的全限定的HTTP地址。与上面的`rpc-address`类似，为两个`NameNode`的HTTP服务器设置侦听地址。例如：
```
<property>
  <name>dfs.namenode.http-address.mycluster.nn1</name>
  <value>machine1.example.com:50070</value>
</property>
<property>
  <name>dfs.namenode.http-address.mycluster.nn2</name>
  <value>machine2.example.com:50070</value>
</property>
```

##### 5.2.5 `dfs.namenode.shared.edits.dir`

共享存储目录的位置。这是配置远程共享编辑目录的路径的地方，`Standby NameNode`用它来保持最新的`Active NameNode`所做的所有文件系统更改。你应该只配置一个目录(You should only configure one of these directories. )。这个目录应该挂载在两个`NameNode`机器上。这个配置的值应该是这个目录在`NameNode`机器上的绝对路径。例如：

```
<property>
  <name>dfs.namenode.shared.edits.dir</name>
  <value>file:///mnt/filer1/dfs/ha-name-dir-shared</value>
</property>
```

##### 5.2.6 `dfs.client.failover.proxy.provider.[nameservice ID]`

`HDFS`客户端用于与`Active NameNode`联系的`Java`类。配置`Java`类的名称，`HDFS`客户端用来确定哪个`NameNode`处于`Active`状态，以及哪个`NameNode`当前正在为客户端请求服务。目前`Hadoop`内置的唯一实现是`ConfiguredFailoverProxyProvider`，所以只能使用这个，除非使用自定义的。例如：

```
<property>
  <name>dfs.client.failover.proxy.provider.mycluster</name>
  <value>org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider</value>
</property>
```

##### 5.2.7 `dfs.ha.fencing.methods`

将在故障转移期间用来隔离`NameNode`的脚本或`Java`类的列表。系统的正确性是至关重要的，在任何时间只能有一个`NameNode`处于`Active`状态。因此，在故障切换期间，我们首先确保`Active NameNode`或处于`Standby`状态，或所在进程已经被终止，然后将另一个`NameNode`转换为`Active`状态。为此，你必须至少配置一种隔离方法。这些配置为一个以回车分隔的列表，将按顺序使用这个列表的每个方法直到有一个方法表示隔离成功。`Hadoop`提供了两种方式：`shell`和`sshfence`。有关自定义隔离方法的信息，请参阅`org.apache.hadoop.ha.NodeFencer`类。

###### 5.2.7.1 sshfence

使用`SSH`登录到`Active NameNode`并杀死进程。为了使此隔离方法能正常工作，必须能够在不提供密码的情况下通过`SSH`连接到目标节点。因此，还必须配置`dfs.ha.fencing.ssh.private-key-files`配置选项，该选项是以逗号分隔的`SSH`私钥文件的列表。例如：

```
<property>
  <name>dfs.ha.fencing.methods</name>
  <value>sshfence</value>
</property>

<property>
  <name>dfs.ha.fencing.ssh.private-key-files</name>
  <value>/home/exampleuser/.ssh/id_rsa</value>
</property>
```

或者，可以配置一个非标准的用户名或端口来执行SSH(one may configure a non-standard username or port to perform the SSH)。也可以为SSH配置超时时间(以毫秒为单位)，超过设定时间将认为此隔离方法失败。它可以这样配置：
```
<property>
  <name>dfs.ha.fencing.methods</name>
  <value>sshfence([[username][:port]])</value>
</property>
<property>
  <name>dfs.ha.fencing.ssh.connect-timeout</name>
  <value>30000</value>
</property>
```

###### 5.2.7.2 shell

运行一个的`shell`命令来隔离`Active NameNode`。`shell`隔离方法运行一个任意的`shell`命令。它可以这样配置：
```
<property>
  <name>dfs.ha.fencing.methods</name>
  <value>shell(/path/to/my/script.sh arg1 arg2 ...)</value>
</property>
```
`(`和`)`之间的字符串(参数变量)直接传递给`bash shell`，也可能不包括括号(may not include any closing parentheses)。

`shell`命令将运行在一个包含所有当前`Hadoop`配置变量的环境中，配置属性key中的`.`字符替换为`_`字符。例如将`dfs.namenode.rpc-address.ns1.nn1`转换为`dfs_namenode_rpc-address`。

此外，还可以使用如下变量来隔离目标节点：

变量|描述
---|---
$target_host|被隔离节点的host
$target_port|被隔离节点的IPC端口号
$target_address|上述两者的组合:host:port
$target_nameserviceid|被隔离`NameNode`的`nameservice ID`
$target_namenodeid|被隔离`NameNode``namenode ID`

这些环境变量也可以用`shell`命令的变量替代。例如：
```
<property>
  <name>dfs.ha.fencing.methods</name>
  <value>shell(/path/to/my/script.sh --nameservice=$target_nameserviceid $target_host:$target_port)</value>
</property>
```

如果`shell`命令返回退出码0，可以确定隔离成功。如果返回其他退出码，那么隔离不成功，并尝试使用列表中的下一个隔离方法。

注意：这个隔离方法没有实现超时设置。如果需要设置超时，它们应该在`shell`脚本中实现(例如通过派生一个子`shell`来在几秒内终止它的父`shell`)。

##### 5.2.8 fs.defaultFS

当没有给出`Hadoop` `FS`客户端时使用的默认路径前缀。或者，现在可以将`Hadoop`客户端的默认路径配置为使用一个新的启用`HA`的逻辑`URI`。如果之前使用`mycluster`作为`nameservice ID`，那么这将是所有`HDFS`路径中权限部分的值。在你的`core-site.xml`文件可能如下配置：
```
<property>
  <name>fs.defaultFS</name>
  <value>hdfs://mycluster</value>
</property>
```

#### 5.3 详细部署

在设置了所有必要的配置选项之后，必须首先同步两个`HA NameNode`在磁盘上的元数据:

- 如果你正在配置一个新的`HDFS`集群，那么首先在一个`NameNode`上运行`format`命令(`hdfs namenode -format`)。
- 如果已经格式化了`NameNode`，或者正准备将未启用`HA`的群集启用`HA`，那么现在你应该在未格式化的`NameNode`上运行命令`hdfs namenode - bootstrapStandby`将`NameNode`元数据目录的内容复制到另一个未格式化的`NameNode`上。运行此命令还可以确保共享编辑目录(由`dfs.namenode.shared.edits.dir`配置)中包含足够的编辑事务，以便能够启动两个`NameNode`。
- 如果要将非`HA` `NameNode`转换为`HA`，那么应该运行`hdfs -initializeSharedEdits`命令，该命令可以使用本地`NameNode`编辑目录中的编辑数据初始化共享编辑目录。

这时，你可以像启动`NameNode`一样启动两个`HA` `NameNode`。

你可以通过他们配置的`HTTP`地址来分别访问每个`NameNode`的网页。你应该注意到，配置的地址旁边将是`NameNode`的`HA`状态(`Standby`或`Active`）。每当`HA` `NameNode`启动时，它最初都处于`Standby`状态。

##### 5.3.1 管理命令

现在你的`HA NameNode`已配置并启动，你将有权访问一些其他命令来管理你的`HA HDFS`集群。具体来说，你应该熟悉`hdfs haadmin`命令的所有子命令。不带任何附加参数运行此命令显示以下用法信息：
```
Usage: DFSHAAdmin [-ns <nameserviceId>]
    [-transitionToActive <serviceId>]
    [-transitionToStandby <serviceId>]
    [-failover [--forcefence] [--forceactive] <serviceId> <serviceId>]
    [-getServiceState <serviceId>]
    [-checkHealth <serviceId>]
    [-help <command>]
```

### 6. 自动故障切换

#### 6.1 概述

上述内容介绍了如何配置手动故障转移。在上述模式下，即使主动节点失败，系统也不会自动触发从`Active`节点切到`Standby`节点的故障切换。下面介绍如何配置和部署自动故障切换。

#### 6.2 内容

自动故障切换为`HDFS`部署添加了两个新组件：`ZooKeeper quorum`和`ZKFailoverController`进程(缩写为ZKFC)。

`Apache ZooKeeper`是一种高度可用的服务，用于维护少量的协调数据，通知客户端数据的变化，并监视客户端是否失败。`HDFS`自动故障切换的实现依赖`ZooKeeper`如下操作：

(1) 失败检测 - 集群中的每个`NameNode`机器在`ZooKeeper`中维护一个持久会话。如果机器崩溃，`ZooKeeper`中的会话就会过期，通知其他`NameNode`应该触发故障切换。

(2) `Active` `NameNode`选举 - `ZooKeeper`提供了一个简单的机制来专门选举一个节点作为活跃节点。如果当前`Active` `NameNode`崩溃，那么另一个节点可能会在`ZooKeeper`中使用一个特殊的独占锁，表明它应该成为下一个活跃节点。

`ZKFailoverController`(`ZKFC`)是一个新的组件，它是`ZooKeeper`的一个客户端，监视和管理`NameNode`的状态。每个运行`NameNode`的机器也运行一个`ZKFC`，`ZKFC`负责：

(1) 健康监控 - `ZKFC`定时使用`health-check`命令对其本地的`NameNode`进行`ping`。只要`NameNode`及时响应健康状态，`ZKFC`就认为节点健康。如果节点崩溃，冻结或以其他方式进入不健康状态，那么健康监控器会将其标记为不健康。

(2) `ZooKeeper`会话管理 - 当本地`NameNode`处于健康状态时，`ZKFC`在`ZooKeeper`中保持会话打开状态。如果本地`NameNode`处于`Active`状态，那么它还包含一个特殊的`锁`znode。这个锁使用`ZooKeeper`对`短暂`节点的支持；如果会话过期，锁定节点将被自动删除。

(3) 基于`ZooKeeper`的选举 - 如果本地`NameNode`处于健康状态，并且`ZKFC`发现当前没有其他节点持有锁定`znode`，它自己尝试获取锁。如果成功，则`赢得选举`，并负责运行故障切换，使其本地`NameNode`处于`Active`状态。故障切换过程与上述手动故障切换类似：首先，如果需要，先前的`Active`节点将被隔离，然后本地`NameNode`转换为`Active`状态。

有关自动故障切换设计的更多详细信息，请参阅`Apache HDFS JIRA`上[HDFS-2185](https://issues.apache.org/jira/browse/HDFS-2185)附带的设计文档。

#### 6.3 部署ZooKeeper

在一个典型部署中，`ZooKeeper`守护进程被配置在三个或五个节点上运行。由于`ZooKeeper`本身对资源要求较低，因此可以在与`HDFS` `NameNode`和`Standby`节点相同硬件上配置`ZooKeeper`节点(it is acceptable to collocate the ZooKeeper nodes on the same hardware as the HDFS NameNode and Standby Node)。许多操作者选择在`YARN ResourceManager`同一节点上部署第三个`ZooKeeper`进程。建议配置`ZooKeeper`节点在与`HDFS`元数据不同磁盘驱动器上存储数据，以实现最佳性能和隔离。

`ZooKeeper`的配置已经超出了本文的范围。我们假设你已经建立了一个运行在三个或三个以上节点上的`ZooKeeper`集群，并通过使用`ZK CLI`连接验证了它的正确操作。

#### 6.4 配置自动故障切换

在开始配置自动故障切换之前，应该关闭集群。在集群运行时，不能从手动故障切换转换为自动故障切换。

自动故障切换配置需要在配置中添加两个新参数。在`hdfs-site.xml`配置文件中，添加：
```
<property>
   <name>dfs.ha.automatic-failover.enabled</name>
   <value>true</value>
 </property>
```
在集群中需要设置为自动故障切换。在`core-site.xml`配置文件中，添加：
```
<property>
  <name>ha.zookeeper.quorum</name>
  <value>zk1.example.com:2181,zk2.example.com:2181,zk3.example.com:2181</value>
</property>
```
上面列出了运行`ZooKeeper`服务的`host-port`对。

与前面介绍的参数一样，可以根据在每个`nameservice`的基础上给配置属性`key`添加`nameservice ID`后缀。例如，在启用了`Federation`的集群中，通过设置`dfs.ha.automatic-failover.enabled.my-nameservice-id`，可以明确地为其中一个`nameservice`启用自动故障切换。

还可以设置其他几个配置参数来控制自动故障切换；但是，对于大多数安装来说，这是不是必须的。

#### 6.5 在ZooKeeper中初始化HA状态

在添加上述配置后，下一步是在`ZooKeeper`中初始化所需的状态。你可以在其中一个`NameNode`主机上运行如下命令来完成此操作：
```
[hdfs]$ $HADOOP_PREFIX/bin/zkfc -formatZK
```
这将在`ZooKeeper`中创建一个`znode`，在`znode`上自动故障切换系统存储其数据(This will create a znode in ZooKeeper inside of which the automatic failover system stores its data.)。

#### 6.6 用start-dfs.sh启动集群

由于配置中启用了自动故障切换功能，因此`start-dfs.sh`脚本将在运行`NameNode`的任何机器上自动启动`ZKFC`守护进程。当`ZKFC`启动时，他们将自动选择一个`NameNode`来作为活跃节点。

#### 6.7 手动启动集群

如果你手动管理集群上的服务，那么需要在运行`NameNode`的每台机器上手动启动`zkfc`守护进程。你可以运行如下命令启动守护进程：
```
[hdfs]$ $HADOOP_PREFIX/sbin/hadoop-daemon.sh --script $HADOOP_PREFIX/bin/hdfs start zkfc
```

#### 6.8 安全访问ZooKeeper

如果你正在运行一个安全的集群，你可能需要确保存储在`ZooKeeper`中的信息也是安全的。这可以防止恶意客户修改`ZooKeeper`中的元数据或者可能触发错误的故障切换。

为了保护`ZooKeeper`中的信息，首先将以下内容添加到`core-site.xml`配置文件中：
```
<property>
  <name>ha.zookeeper.auth</name>
  <value>@/path/to/zk-auth.txt</value>
</property>
<property>
  <name>ha.zookeeper.acl</name>
  <value>@/path/to/zk-acl.txt</value>
</property>
```
请注意这些属性值中的`@`字符 - 这指定配置不是内联的(inline)，而是指向磁盘上的文件。

第一个配置的文件指定了与`ZK CLI`使用的相同格式的`ZooKeeper`认证列表。 例如，你可以指定如下所示的内容：
```
digest:hdfs-zkfcs:mypassword
```
...其中`hdfs-zkfcs`是`ZooKeeper`的用户名，`mypassword`是对应用户的密码。

接下来，使用类似下面的命令生成对应于此身份验证的`ZooKeeper ACL`：
```
[hdfs]$ java -cp $ZK_HOME/lib/*:$ZK_HOME/zookeeper-3.4.2.jar org.apache.zookeeper.server.auth.DigestAuthenticationProvider hdfs-zkfcs:mypassword
output: hdfs-zkfcs:mypassword->hdfs-zkfcs:P/OQvnYyU/nF/mGYvB/xurX8dYs=
```
将`->`字符串之后的部分复制并粘贴到`zk-acls.txt`文件中，并添加字符串`digest：`作为前缀。例如：
```
digest:hdfs-zkfcs:vlUvLnd8MlacsE80rDuu6ONESbM=:rwcda
```
为了使这些`ACL`生效，应该重新运行上面讲述的`zkfc -formatZK`命令。这样做后，你可以从`ZK CLI`验证`ACL`，如下所示：
```
[zk: localhost:2181(CONNECTED) 1] getAcl /hadoop-ha
'digest,'hdfs-zkfcs:vlUvLnd8MlacsE80rDuu6ONESbM=
: cdrwa
```


原文: http://hadoop.apache.org/docs/r2.7.3/hadoop-project-dist/hadoop-hdfs/HDFSHighAvailabilityWithNFS.html
