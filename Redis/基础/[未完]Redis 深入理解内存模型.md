理解 Redis 内存，首先需要掌握 Redis 内存消耗在哪些方面。有些内存消耗是必不可少的，而有些可以通过参数调整和合理使用来规避内存浪费。内存消耗可以分为进程自身消耗和子进程消耗。

## 1. 内存使用统计

首先需要了解 Redis 自身使用内存的统计数据，可通过执行 info memory 命令获取内存相关指标。

![](1)

读懂每个指标有助于分析 Redis 内存使用情况：
- used_memory：由 Redis 内存分配器(例如，libc, jemalloc)分配的内存总量，是内部存储所有数据内存占有量，以字节（byte）为单位
- used_memory_human：以可读的格式返回 Redis 分配的内存总量
- used_memory_rss：从操作系统的角度展示 Redis 已分配的内存总量
- mem_fragmentation_ratio：used_memory_rss 和 used_memory 之间的比率
- mem_fragmentation_bytes：used_memory_rss 和 used_memory 之间的差值。
- used_memory_peak：Redis 内存使用峰值，即 used_memory 的峰值，以字节为单位。
- used_memory_peak_perc：Redis 内存使用量占峰值内存的百分比，即 `(used_memory / used_memory_peak) * 100%`
- used_memory_overhead：服务器为管理其内部数据结构而分配的内存大小，以字节为单位。
- used_memory_startup：Redis 在启动时消耗的初始内存大小，以字节为单位。
- used_memory_dataset：以字节为单位的数据集大小，即 `used_memory - used_memory_overhead`
- used_memory_dataset_perc：used_memory_dataset 占净内存使用量的百分比（used_memory - used_memory_startup）
- total_system_memory：Redis 主机系统内存总量
- used_memory_lua：Lua 引擎所使用的内存大小，以字节为单位
- used_memory_scripts：缓存 Lua 脚本使用的内存大小，以字节为单位
- maxmemory：maxmemory 配置参数指定的值
- maxmemory_policy： maxmemory-policy 配置参数指定的值
- mem_not_counted_for_evict:0
- mem_allocator：在编译时指定的，Redis 所使用的内存分配器。可以是 libc、jemalloc 或者 tcmalloc。

需要重点关注的指标有：used_memory_rss 和 used_memory 以及它们的比值 mem_fragmentation_ratio。
- 当 mem_fragmentation_ratio > 1 时，说明 used_memory_rss - used_memory 多出的部分内存并没有用于数据存储，而是被内存碎片所消耗，如果两者相差很大，说明碎片率严重。
- 当 mem_fragmentation_ratio < 1 时，这种情况一般出现在操作系统把 Redis 内存交换（Swap）到硬盘导致，出现这种情况时要格外关注，由于硬盘速度远远慢于内存，Redis性能会变得很差，甚至僵死。

## 2. 内存消耗划分

Redis 进程内消耗主要包括：自身内存、对象内存、缓冲内存、内存碎片，其中 Redis 空进程自身内存消耗非常少，通常 used_memory_rss 在 3MB 左右，used_memory 在 800KB 左右，一个空的 Redis 进程消耗内存可以忽略不计。下面介绍另外三种内存消耗。

### 2.1 对象内存

对象内存是 Redis 内存占用最大的一块，存储着用户所有的数据。Redis 所有的数据都采用 key-value 数据类型，每次创建键值对时，至少创建两个类型对象：key 对象和 value 对象。对象内存消耗可以简单理解为 sizeof（keys）+ sizeof（values）。键对象都是字符串，在使用 Redis 时很容易忽略键对内存消耗的影响，应当避免使用过长的键。value 对象更复杂些，主要包含 5 种基本数据类型：字符串、列表、哈希、集合、有序集合。其他数据类型都是建立在这5种数据结构之上实现的，如：Bitmaps 和 HyperLogLog 使用字符串实现，GEO 使用有序集合实现等。每种 value 对象类型根据使用规模不同，占用内存不同。在使用时一定要合理预估并监控 value 对象占用情况，避免内存溢出。

### 2.2 缓冲内存

缓冲内存主要包括：客户端缓冲、复制积压缓冲区、AOF缓冲区。

客户端缓冲指的是所有接入到 Redis 服务器 TCP 连接的输入输出缓冲。输入缓冲无法控制，最大空间为 1G，如果超过将断开连接。输出缓冲通过参数 client-output-buffer-limit 控制，如下所示：
- 普通客户端：除了复制和订阅的客户端之外的所有连接，Redis的默认配置是：client-output-buffer-limit normal000，Redis并没有对普通客户端的输出缓冲区做限制，一般普通客户端的内存消耗可以忽略不计，但是当有大量慢连接客户端接入时这部分内存消耗就不能忽略了，可以设置maxclients做限制。特别是当使用大量数据输出的命令且数据无法及时推送给客户端时，如monitor命令，容易造成Redis服务器内存突然飙升。
- 从客户端：主节点会为每个从节点单独建立一条连接用于命令复制，默认配置是：client-output-buffer-limit slave256mb64mb60。当主从节点之间网络延迟较高或主节点挂载大量从节点时这部分内存消耗将占用很大一部分，建议主节点挂载的从节点不要多于2个，主从节点不要部署在较差的网络环境下，如异地跨机房环境，防止复制客户端连接缓慢造成溢出。
- 订阅客户端：当使用发布订阅功能时，连接客户端使用单独的输出缓冲区，默认配置为：client-output-buffer-limit pubsub32mb8mb60，当订阅服务的消息生产快于消费速度时，输出缓冲区会产生积压造成输出缓冲区空间溢出。

输入输出缓冲区在大流量的场景中容易失控，造成Redis内存的不稳定，需要重点监控，具体细节见4.4节中客户端管理部分。

复制积压缓冲区：Redis 在 2.8 版本之后提供了一个可重用的固定大小缓冲区用于实现部分复制功能，根据 repl-backlog-size 参数控制，默认 1MB。对于复制积压缓冲区整个主节点只有一个，所有的从节点共享此缓冲区，因此可以设置较大的缓冲区空间，如 100MB，这部分内存投入是有价值的，可以有效避免全量复制。

AOF 缓冲区：这部分空间用于在 Redis 重写期间保存最近的写入命令。AOF 缓冲区空间消耗用户无法控制，消耗的内存取决于 AOF 重写时间和写入命令量，这部分空间占用通常很小。

### 2.3 内存碎片

Redis 默认的内存分配器采用 jemalloc，可选的分配器还有：glibc、tcmalloc。内存分配器为了更好地管理和重复利用内存，分配内存策略一般采用固定范围的内存块进行分配。例如，jemalloc 在64位系统中将内存空间划分为：小、大、巨大三个范围。每个范围内又划分为多个小的内存块单位，如下所示：
- 小：[8byte]，[16byte，32byte，48byte，...，128byte]，[192byte，256byte，...，512byte]，[768byte，1024byte，...，3840byte]
- 大：[4KB，8KB，12KB，...，4072KB]
- 巨大：[4MB，8MB，12MB，...]

比如当保存 5KB 对象时 jemalloc 可能会采用 8KB 的块存储，而剩下的 3KB 空间变为了内存碎片不能再分配给其他对象存储。内存碎片问题虽然是所有内存服务的通病，但是 jemalloc 针对碎片化问题专门做了优化，一般不会存在过度碎片化的问题，正常的碎片率（mem_fragmentation_ratio）在 1.03 左右。但是当存储的数据长短差异较大时，以下场景容易出现高内存碎片问题：
- 频繁做更新操作，例如频繁对已存在的键执行append、setrange等更新操作。
- 大量过期键删除，键对象过期删除后，释放的空间无法得到充分利用，导致碎片率上升。
出现高内存碎片问题时常见的解决方式如下：
- 数据对齐：在条件允许的情况下尽量做数据对齐，比如数据尽量采用数字类型或者固定长度字符串等，但是这要视具体的业务而定，有些场景无法做到。
- 安全重启：重启节点可以做到内存碎片重新整理，因此可以利用高可用架构，如Sentinel或Cluster，将碎片率过高的主节点转换为从节点，进行安全重启。

## 3. 子进程内存消耗

子进程内存消耗主要指执行 AOF/RDB 重写时 Redis 创建的子进程内存消耗。Redis 执行 fork 操作产生的子进程内存占用量对外表现为与父进程相同，理论上需要一倍的物理内存来完成重写操作。但 Linux 具有写时复制技术（copy-on-write），父子进程会共享相同的物理内存页，当父进程处理写请求时会对需要修改的页复制出一份副本完成写操作，而子进程依然读取 fork 时整个父进程的内存快照。

Linux Kernel在2.6.38内核增加了Transparent Huge Pages（THP）机制，而有些Linux发行版即使内核达不到2.6.38也会默认加入并开启这个功能，如Redhat Enterprise Linux在6.0以上版本默认会引入THP。虽然开启THP可以降低fork子进程的速度，但之后copy-on-write期间复制内存页的单位从4KB变为2MB，如果父进程有大量写命令，会加重内存拷贝量，从而造成过度内存消耗。例如，以下两个执行AOF重写时的内存消耗日志：
// 开启THP:
C * AOF rewrite: 1039 MB of memory used by copy-on-write
// 关闭THP:
C * AOF rewrite: 9 MB of memory used by copy-on-write
这两个日志出自同一Redis进程，used_memory总量为1.5GB，子进程执行期间每秒写命令量都在200左右。当分别开启和关闭THP时，子进程内存消耗有天壤之别。如果在高并发写的场景下开启THP，子进程内存消耗可能是父进程的数倍，极易造成机器物理内存溢出，从而触发SWAP或OOM killer，更多关于THP细节见12.1节“Linux配置优化”。
子进程内存消耗总结如下：
·Redis产生的子进程并不需要消耗1倍的父进程内存，实际消耗根据期间写入命令量决定，但是依然要预留出一些内存防止溢出。
·需要设置sysctl vm.overcommit_memory=1允许内核可以分配所有的物理内存，防止Redis进程执行fork时因系统剩余内存不足而失败。
·排查当前系统是否支持并开启THP，如果开启建议关闭，防止copy-on-write期间内存过度消耗。

Redis主要通过控制内存上限和回收策略实现内存管理，本节将围绕这两个方面来介绍Redis如何管理内存。

设置内存上限
Redis使用maxmemory参数限制最大可用内存。限制内存的目的主要有：
·用于缓存场景，当超出内存上限maxmemory时使用LRU等删除策略释放空间。
·防止所用内存超过服务器物理内存。
需要注意，maxmemory限制的是Redis实际使用的内存量，也就是used_memory统计项对应的内存。由于内存碎片率的存在，实际消耗的内存可能会比maxmemory设置的更大，实际使用时要小心这部分内存溢出。通过设置内存上限可以非常方便地实现一台服务器部署多个Redis进程的内存控制。比如一台24GB内存的服务器，为系统预留4GB内存，预留4GB空闲内存给其他进程或Redis fork进程，留给Redis16GB内存，这样可以部署4个maxmemory=4GB的Redis进程。得益于Redis单线程架构和内存限制机制，即使没有采用虚拟化，不同的Redis进程之间也可以很好地实现CPU和内存的隔离性，如图8-2所示。
图8-2 服务器分配4个4GB的Redis进程


动态调整内存上限
Redis的内存上限可以通过config set maxmemory进行动态修改，即修改最大可用内存。例如之前的示例，当发现Redis-2没有做好内存预估，实际只用了不到2GB内存，而Redis-1实例需要扩容到6GB内存才够用，这时可以分别执行如下命令进行调整：
Redis-1>config set maxmemory 6GB
Redis-2>config set maxmemory 2GB
通过动态修改maxmemory，可以实现在当前服务器下动态伸缩Redis内存的目的，如图8-3所示。
图8-3 Redis实例之间调整max-memory伸缩内存
这个例子过于理想化，如果此时Redis-3和Redis-4实例也需要分别扩容到6GB，这时超出系统物理内存限制就不能简单的通过调整maxmemory来达到扩容的目的，需要采用在线迁移数据或者通过复制切换服务器来达到扩容的目的。具体细节见第9章“哨兵”和第10章“集群”部分。运维提示
Redis默认无限使用服务器内存，为防止极端情况下导致系统内存耗尽，建议所有的Redis进程都要配置maxmemory。
在保证物理内存可用的情况下，系统中所有Redis实例可以调整maxmemory参数来达到自由伸缩内存的目的。
