---
layout: post
author: 未知
title: Hadoop MapReduce2.x下分布式缓存的一个坑
date: 2018-08-02 20:29:01
tags:
  - Hadoop
  - Hadoop TroubleShooting

categories: Hadoop
permalink: hadoop-base-trecautions-of-distributed-cache-in-mapreduce2
---


### 1. 问题

最近公司的集群从 Apache hadoop 0.20.203 升级到了 CDH 4，迈进了 Hadoop 2.0 的新时代，虽然新一代的 hadoop 努力做了架构、API 上的各种兼容， 但总有“照顾不周”的地方，下面说的这个有关分布式缓存的案例就是于此有关：一些 MR job 迁移到 Yarn 上后，发觉没数据了，而且没有报错。

查了下数据源和代码，发现是分布式缓存（DistributedCache）的用法有点小变化。以前的老代码大致如下：
```java
// 添加文件到分布式缓存中
String cacheFilePath = "/dsap/rawdata/cmc_unitparameter/20140308/part-m-00000";
DistributedCache.addCacheFile(new Path(cacheFilePath).toUri(), job.getConfiguration());

// 获取分布式缓存中的文件
Path[] paths = DistributedCache.getLocalCacheFiles(context.getConfiguration());
for (Path path : paths) {
    if (path.toString().contains("cmc_unitparameter")) {
        ...
    }
}        
```
这两段代码在 MR1 时代毫无问题，但是到了 MR2 时代 if 是永远为 false 的。特意对比了下 MR1 和 MR2 时代的 path 格式，可以看到在 MRv2 下，Path 中不包含原始路径信息了：
```
MR1 Path:   hdfs://host:fs_port/dsap/rawdata/cmc_unitparameter/20140308/part-m-00000
MR1 Path:   hdfs://host:fs_port/dsap/rawdata/cmc_unitparameter/20140308/part-m-00000

MR2 Path:   /data4/yarn/local/usercache/root/appcache/application_1394073762364_1884/container_1394073762364_1884_01_000006/part-m-00000
MR2 Path:   /data17/yarn/local/usercache/root/appcache/application_1394073762364_1884/container_1394073762364_1884_01_000002/part-m-00000
MR2 Path:   /data23/yarn/local/usercache/root/appcache/application_1394073762364_1884/container_1394073762364_1884_01_000005/part-m-00000
```
看了上面两种差异我想你能明白为啥分布式缓存在 MR2 下面“失效了”。。。

### 2. 解决方案

解决这个问题不难：其实在 MR1 时代我们上面的代码是不够规范的，每次都遍历了整个分布式缓存，我们应该用到一个小技巧：`createSymlink`。

每个缓存文件添加符号链接
```java
String cacheFilePath = "/dsap/rawdata/cmc_unitparameter/20140308/part-m-00000";
Path inPath = new Path(cacheFilePath);
// # 号之后的名称是对上面文件的链接，不同文件的链接名不能相同，虽然由你自己随便取
String inPathLink=inPath.toUri().toString()+"#"+"DIYFileName";
DistributedCache.addCacheFile(new URI(inPathLink), job.getConfiguration());
```
加了软链接后，path 信息的最后部分就是你刚才的 `DIYFileName`：
```
/data4/yarn/local/usercache/root/appcache/application_1394073762364_1966/container_1394073762364_1966_01_000005/cmcs_paracontrolvalues
/data4/yarn/local/usercache/root/appcache/application_1394073762364_1966/container_1394073762364_1966_01_000005/cmc_unitparameter
```
在需要用缓存文件的地方直接根据你刚才 # 后面自定义的文件名读取即可：
```java
BufferedReader br = null;
br = new BufferedReader(new InputStreamReader(new FileInputStream("DIYFileName")));
```

原文：[Yarn(MapReduce 2.0)下分布式缓存(DistributedCache)的注意事项](http://www.codeweblog.com/yarn-mapreduce-2-0-%E4%B8%8B%E5%88%86%E5%B8%83%E5%BC%8F%E7%BC%93%E5%AD%98-distributedcache-%E7%9A%84%E6%B3%A8%E6%84%8F%E4%BA%8B%E9%A1%B9/)
