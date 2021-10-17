---
layout: post
author: smartsi
title: Hadoop Yarn 节点健康监测机制
date: 2021-10-17 16:35:01
tags:
  - Hadoop

categories: Hadoop
permalink: hadooop-yarn-nodemanager-health-checker
---

节点健康监测是 NodeManager 自带的健康状态诊断机制。通过该机制，NodeManager 可以时刻掌握自己的健康状况，并及时汇报给 ResourceManager，ResourceManager 根据节点的健康状况调整分配的任务数目。如果任何健康监测失败，NodeManager 会将该节点标记处于不健康状态，并将其传达给 ResourceManager，后者会停止将新任务分配给该节点，直到节点标记为健康状态。该机制不仅可以帮助及时发现存在问题的 NodeManager，避免不必要的任务分配，也可以用于动态升级（通过脚本指示 ResourceManager 不再分配任务，等到 NodeManager 上面的任务运行完成后，对它进行升级）。

NodeManager 上有专门一个服务判断所在节点的健康状况，该服务通过两种策略判断节点健康状况，第一种是监测磁盘损坏，第二种是通过管理员自定义的健康监测脚本。

## 1. 监测磁盘损坏

YARN 提供了一种判断 NodeManager 是否健康的机制：检测磁盘损坏数目。管理员可通过参数 yarn.nodemanager.disk-health-checker.enable 设置是否启用该功能，默认情况是启用的。该机制是由 LocalDirsHandlerService 服务实现，周期性检测 NodeManager 本地磁盘的好坏，一旦发现正常磁盘的比例低于一定的比例，则认为节点处于不健康状态，便通过心跳告诉 ResourceManager，从而不再接收到新的任务。

管理员配置 YARN 时，会设置 NodeManager 的本地可用目录列表：
- 本地目录：通常用于存储应用程序中间结果，比如 MapReduce 作业中 Map Task 的中间输出结果。由参数 yarn.nodemanager.local-dirs 指定，默认为 `${hadoop.tmp.dir}/nm-local-dir`。
- 日志目录：存放 Container 运行日志。由参数 yarn.nodemanager.log-dirs 指定，默认为 `${yarn.log.dir}/userlogs`。

> ${hadoop.tmp.dir} 通过 hadoop.tmp.dir 参数在 core-site.xml 中配置、${yarn.log.dir} 是 Java 属性，在 yarn-env.sh 中配置。

这些目录的可用性直接决定着 NodeManager 的可用性。因此，NodeManager 作为节点的代理和管理者，应该负责检测这两类目录列表的可用性，并及时将不可用目录剔除掉。NodeManager 判断一个目录所在磁盘好坏的方法是：如果一个目录具有读、写和执行权限，并且有满足要求的可用磁盘空间，则认为它是正常的，否则将被加入坏磁盘列表。LocalDirsHandlerService 服务中专门有一个定时任务周期性检测这些磁盘的好坏，一旦发现正常磁盘的比例低于阈值，该节点就被标记处于不健康状态，此后 ResourceManager 不再为它分配新任务。

具体通过如下配置参数来监测磁盘损坏情况：
- yarn.nodemanager.disk-health-checker.enable：如果为 true 表示启用磁盘健康监测，否则禁用监测。
- yarn.nodemanager.disk-health-checker.interval-ms：健康监测的时间间隔，以毫秒为单位，默认为 2 分钟，即每 2 分钟检查一次。
- yarn.nodemanager.disk-health-checker.min-healthy-disks：健康磁盘最小比例。当健康磁盘比例低于该值时，NodeManager 不会再接收和启动新的任务。默认值为 0.25。
- yarn.nodemanager.disk-health-checker.max-disk-utilization-per-disk-percentage：磁盘的最大使用率。当一块磁盘的使用率超过该值时，就会标记该磁盘处于不健康状态，不再使用该磁盘。默认为 90，即可以使用磁盘 90% 的空间。
- yarn.nodemanager.disk-health-checker.min-free-space-per-disk-mb：磁盘的最少剩余空间。当某块磁盘剩余空间低于该值时，就会标记该磁盘处于不健康状态，不再使用该磁盘。默认值为 0，即可以使用整块磁盘。

例如，通过如下信息可以了解到磁盘的最大使用率超过了 90%，从而导致节点处于不健康状态：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hadoop/hadooop-yarn-nodemanager-health-checker-2.png?raw=true)

![](https://github.com/sjf0115/ImageBucket/blob/main/Hadoop/hadooop-yarn-nodemanager-health-checker-1.png?raw=true)

使用 df -h 查看磁盘使用情况，发现磁盘确实已经超过可 90%，可以在 yarn-site.xml 文件中配置如下参数：
```
<property>
  <name>yarn.nodemanager.disk-health-checker.max-disk-utilization-per-disk-percentage</name>
  <value>98.5</value>
</property>
```
> 如果从根据上解决问题，还是要删除磁盘上的文件，确保磁盘空间的使用率低于 90%。

## 2. 健康监测脚本

除了监测磁盘损坏情况，用户也可以通过在脚本中执行监测来判断该节点是否处于健康状态。如果脚本监测到节点不健康，可以打印一个标准的 ERROR（错误）输出。用户需要通过 yarn.nodemanager.health-checker.script.path 参数来指定健康监测脚本。NodeManager 会通过这些脚本周期性检查脚本输出，如果脚本输出以 ERROR 开头的行，该节点被标记处于不健康状态，并将节点加入到 ResourceManager 的黑名单列表中，也不会将任务分配到该节点上。然后 NodeManager 继续跑这些脚本，如果节点标记处于健康状态了，将自动从 ResourceManager 的黑名单列表中删除。除了上述所说的输出以 ERROR 开头的行之外，还有两种情况也认为节点处于不健康状态：
- 执行脚本出现超时
- 执行脚本抛出异常

但需要注意的是：
- 如果出现 0 以外的 ExitCode 不被视为失败，因为可能是由语法错误引起的。因此该节点不会被标记为不健康。
- 如果由于权限或路径错误等原因导致脚本无法执行，则视为失败，节点被标记为不健康。
- 健康监测脚本不是必须的。如果未指定脚本，那么仅通过检测磁盘损坏来确定节点的健康状况。

如下三个是全局配置参数，对所有的脚本都有效：
- yarn.nodemanager.health-checker.script：以逗号分隔的健康监测脚本的关键字，唯一对应一个脚本。默认为 'script'。
- yarn.nodemanager.health-checker.interval-ms：健康监测脚本检查的时间间隔。以毫秒为单位，默认为 10 分钟，即每 10 分钟检查一次。
- yarn.nodemanager.health-checker.timeout-ms：健康监测脚本检查的超时时间。默认为 20 分钟。

除了全局配置参数之外，还可以为每个健康监测脚本单独设置参数，如下所示：
- yarn.nodemanager.health-checker.%s.path：指定健康监测脚本的绝对路径。必需参数。
- yarn.nodemanager.health-checker.%s.opts：传递给指定健康监测脚本的参数。必需参数。
- yarn.nodemanager.health-checker.%s.interval-ms：指定健康监测脚本的检查时间间隔。以毫秒为单位。
- yarn.nodemanager.health-checker.%s.timeout-ms：指定健康监测脚本的检查超时时间。

> %s 符号替换为 yarn.nodemanager.health-checker.script 中提供的关键字。例如，默认为 'script'，上述第一个参数变为：yarn.nodemanager.health-checker.script.path

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

参考：
- Hadoop技术内幕：深入理解YARN架构设计与实现原理
- [NodeManager](https://hadoop.apache.org/docs/current/hadoop-yarn/hadoop-yarn-site/NodeManager.html#Health_Checker_Service)
