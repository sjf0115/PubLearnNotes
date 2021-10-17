---
layout: post
author: sjf0115
title: Hadoop Yarn上的调度器
date: 2018-05-07 20:01:01
tags:
  - Hadoop

categories: Hadoop
permalink: hadoop-scheduler-of-yarn
---

### 1. 引言

Yarn 在 Hadoop 的生态系统中担任了资源管理和任务调度的角色。在讨论其构造器之前先简单了解一下 Yarn 的架构：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hadoop/hadoop-scheduler-of-yarn-5.gif?raw=true)

上图是 Yarn 的基本架构，其中 ResourceManager 是整个架构的核心组件，负责集群上的资源管理，包括内存、CPU以及集群上的其他资； ApplicationMaster 负责在生命周期内的应用程序调度；NodeManager 负责本节点上资源的供给和隔离；Container 可以抽象的看成是运行任务的一个容器。本文讨论的调度器是在 ResourceManager 进行调度，接下来在了解一下 FIFO 调度器、Capacity 调度器、Fair 调度器三个调度器。

### 2. FIFO 调度器

![](https://github.com/sjf0115/ImageBucket/blob/main/Hadoop/hadoop-scheduler-of-yarn-1.png?raw=true)

上图显示了 FIFO 调度器的实现（执行过程示意图）。FIFO 调度器是先进先出（First In First Out）调度器。FIFO 调度器是 Hadoop 使用最早的一种调度策略，可以简单的将其理解为一个 Java 队列，这就意味着在集群中同时只能有一个作业运行。所有的应用程序按照提交顺序来执行，在上一个 Job 执行完成之后，下一个 Job 按照队列中的顺序执行。FIFO 调度器以独占集群全部资源的方式来运行作业，这样的好处是 Job 可以充分利用集群的全部资源，但是对于运行时间短，优先级高或者交互式查询类的 MR Job 需要等待它之前的 Job 完成才能被执行，这也就导致了如果前面有一个比较大的 Job 在运行，那么后面的 Job 将会被阻塞。因此，虽然 FIFO 调度器实现简单，但是并不能满足很多实际场景的要求。这也就促使 Capacity 调度器和 Fair 调度器的诞生。

> 增加作业优先级的功能后，可以通过设置 `mapred.job.priority` 属性或 JobClinet 的 `setJobPriority` 方法来设置优先级。在作业调度器选择要运行的下一个作业时，FIFO 调度器中不支持优先级抢占，所以高优先级的作业会受阻于前面已经开始，长时间运行的低优先级的作业。

### 3. Capacity调度器

![](https://github.com/sjf0115/ImageBucket/blob/main/Hadoop/hadoop-scheduler-of-yarn-2.png?raw=true)

上图显示了 Capacity 调度器的实现（执行过程示意图）。Capacity 调度器也称之为容器调度器。可以将它理解为一个资源队列。资源队列需要用户自己分配。例如，Job 需要要把整个集群分成 AB 两个队列，A 队列又可以继续分，比如将 A 队列再分为 1 和 2 两个子队列。那么队列的分配就可以参考下面的树形结构：
```
—A[60%]
  |—A.1[40%]
  |—A.2[60%]
—B[40%]
```
上述的树形结构可以理解为 A 队列占用集群全部资源的 60%，B 队列占用 40%。A 队列又分为 1，2 两个子队列，A.1 占据 40%，A.2 占据 60%，也就是说此时 A.1 和 A.2 分别占用 A 队列的 40% 和 60% 的资源。虽然此时已经对集群的资源进行了分配，但并不是说 A 提交了任务之后只能使用集群 60% 的资源，而 B 队列的 40% 的资源处于空闲。只要是其它队列中的资源处于空闲状态，那么有任务提交的队列就可以使用分配给空闲队列的那些资源，使用的多少依据具体配置。参数的配置会在后文中提到。

#### 3.1 Capacity调度器的特性

- 层次化的队列设计，这种层次化的队列设计保证了子队列可以使用父队列的全部资源。这样通过层次化的管理可以更容易分配和限制资源的使用。
- 容量，给队列设置一个容量(资源占比)，确保每个队列不会占用集群的全部资源。
- 安全，每个队列都有严格的访问控制。用户只能向自己的队列提交任务，不能修改或者访问其他队列的任务。
- 弹性分配，可以将空闲资源分配给任何队列。当多个队列出现竞争的时候，则会按照比例进行平衡。
- 多租户租用，通过队列的容量限制，多个用户可以共享同一个集群，colleagues 保证每个队列分配到自己的容量，并且提高利用率。
- 可操作性，Yarn 支持动态修改容量、权限等的分配，这些可以在运行时直接修改。还提供管理员界面，来显示当前的队列状态。管理员可以在运行时添加队列；但是不能删除队列。管理员还可以在运行时暂停某个队列，这样可以保证当前队列在执行期间不会接收其他任务。如果一个队列被设置成了 stopped，那么就不能向他或者子队列提交任务。
- 基于资源的调度，以协调不同资源需求的应用程序，比如内存、CPU、磁盘等等。

#### 3.2 Capacity调度器的参数配置

- capacity：队列的资源容量（百分比）。当系统非常繁忙时，应保证每个队列的容量得到满足，如果每个队列应用程序较少，可与其他队列共享剩余资源。注意，所有队列的容量之和应小于 100。
- maximum-capacity：队列的资源使用上限（百分比）。由于资源共享，因此一个队列使用的资源量可能超过其容量，可以通过该参数来限制最多使用资源量。（这也是前文提到的队列可以占用资源的最大百分比）
- user-limit-factor：每个用户最多可使用的资源量（百分比）。比如，如果该值为 30，那么在任何时候每个用户使用的资源量都不能超过该队列容量的 30%。
- maximum-applications：集群中或者队列中同时处于等待和运行状态的应用程序数目上限，这是一个强限制，一旦集群中应用程序数目超过该上限，后续提交的应用程序将被拒绝，默认值为 10000。所有队列的数目上限可通过参数 yarn.scheduler.capacity.maximum-applications 设置（可看做默认值），而单个队列可通过参数 `yarn.scheduler.capacity.<queue-path>.maximum-applications` 设置。
- maximum-am-resource-percent：集群中用于运行应用程序 ApplicationMaster 的最大资源比例，该参数通常用于限制处于活动状态的应用程序数目。该参数类型为浮点型，默认是0.1，表示10%。所有队列的 ApplicationMaster 资源比例上限可通过参数 `yarn.scheduler.capacity. maximum-am-resource-percent` 设置（可看做默认值），而单个队列可通过参数 `yarn.scheduler.capacity.<queue-path>.maximum-am-resource-percent` 设置。
- state：队列状态可以为 STOPPED 或者 RUNNING，如果一个队列处于 STOPPED 状态，用户不可以将应用程序提交到该队列或者它的子队列中，类似的，如果 ROOT 队列处于 STOPPED 状态，用户不可以向集群中提交应用程序，但是处于 RUNNING 状态的应用程序仍可以正常运行，以便队列可以优雅地退出。
- acl_submit_applications：指定哪些Linux用户/用户组可向队列提交应用程序。需要注意的是，该属性具有继承性，即如果一个用户可以向某个队列提交应用程序，那么它可以向它的所有子队列提交应用程序。配置该属性时，用户之间或用户组之间用 `，` 分割，用户和用户组之间用空格分割，比如 `user1,user2 group1,group2`。
- acl_administer_queue：指定队列的管理员，管理员可控制该队列的所有应用程序，例如杀死任意一个应用程序等。同样，该属性具有继承性，如果一个用户可以向某个队列提交应用程序，则它可以向它的所有子队列提交应用程序。

### 4. Fair调度器

![](https://github.com/sjf0115/ImageBucket/blob/main/Hadoop/hadoop-scheduler-of-yarn-3.png?raw=true)

上图显示了 Fair 调度器的实现（执行过程示意图）。Fair 调度器也称之为公平调度器。Fair 调度器是一种队列资源分配方式，在整个时间线上，所有的 Job 平分资源。默认情况下，Fair 调度器只是对内存资源做公平的调度和分配。当集群中只有一个任务在运行时，那么此任务会占用集群的全部资源。当有其他的任务提交后，那些释放的资源将会被分配给新的 Job，所以每个任务最终都能获取几乎一样多的资源。

![](https://github.com/sjf0115/ImageBucket/blob/main/Hadoop/hadoop-scheduler-of-yarn-4.png?raw=true)

Fair 调度器也可以在多个队列上工作，如上图所示，例如，有两个用户 A 和 B，他们分别拥有一个队列。当 A 启动一个 Job 而 B 没有提交任何任务时，A 会获得集群全部资源；当 B 启动一个 Job 后，A 的任务会继续运行，不过队列 A 会慢慢释放它的一些资源，一会儿之后两个任务会各自获得集群一半的资源。如果此时 B 再启动第二个 Job 并且其它任务也还在运行时，那么它将会和 B 队列中的的第一个 Job 共享队列 B 的资源，也就是队列 B 的两个 Job 会分别使用集群四分之一的资源，而队列 A 的 Job 仍然会使用集群一半的资源，结果就是集群的资源最终在两个用户之间平等的共享。　

#### 4.1 Fair调度器参数配置

- yarn.scheduler.fair.allocation.file： allocation 文件的位置，allocation 文件是一个用来描述队列以及它们属性的配置文件。这个文件必须为格式严格的 xml 文件。如果为相对路径，那么将会在 classpath 下查找此文件(conf目录下)。默认值为 `fair-scheduler.xml`。
- yarn.scheduler.fair.user-as-default-queue：如果没有指定队列名称时，是否将与 allocation 有关的 username 作为默认的队列名称。如果设置成　false(且没有指定队列名称) 或者没有设定，所有的 jobs 将共享 default 队列。默认值为 true。
- yarn.scheduler.fair.preemption：是否使用抢占模式(优先权，抢占)，默认为 fasle，在此版本中此功能为测试性的。
- yarn.scheduler.fair.assignmultiple：是在允许在一个心跳中发送多个容器分配信息。默认值为 false。
- yarn.scheduler.fair.max.assign：如果 yarn.scheduler.fair.assignmultiple 为true，那么在一次心跳中最多发送分配容器的个数。默认为 -1，无限制。
- yarn.scheduler.fair.locality.threshold.node：0~1之间一个 float 值，表示在等待获取满足 node-local 条件的容器时，最多放弃不满足 node-local 的容器机会次数，放弃的 nodes 个数为集群的大小的比例。默认值为 -1.0 表示不放弃任何调度的机会。
- yarn.scheduler.fair.locality.threashod.rack：同上，满足 rack-local。
- yarn.scheduler.fair.sizebaseweight：是否根据应用程序的大小(Job的个数)作为权重。默认为 false，如果为 true，那么复杂的应用程序会获取更多的资源。

### 5. 总结

如果业务逻辑比较简单或者刚接触 Hadoop 的时建议使用 FIFO 调度器；如果需要控制部分应用程序的优先级，同时又想要充分利用集群资源的情况下，建议使用 Capacity 调度器；如果想要多用户或者多队列公平的共享集群资源，那么就选用Fair调度器。希望大家能够根据业务所需选择合适的调度器。

原文：http://www.cobub.com/en/the-selection-and-use-of-hadoop-yarn-scheduler/
