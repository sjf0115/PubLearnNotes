## 1. 问题

在运行作业时，作业一直卡在下面语句不能运行：
```
17/01/23 21:43:21 INFO mapreduce.Job: Running job: job_1485165672363_0004
```
在访问 http://localhost:8088/cluster/ 时，发现节点为不健康节点。NodeHealthReport报告如下：
```
1/1 local-dirs are bad: /tmp/hadoop-hduser/nm-local-dir;
1/1 log-dirs are bad: /usr/local/hadoop/logs/userlogs
```
## 2. 分析

引起 local-dirs are bad 的最常见原因是由于节点上的磁盘使用率超出了**max-disk-utilization-per-disk-percentage**（默认值90.0%）。

清理不健康节点上的磁盘空间或者降低参数设置的阈值：
```xml
<property>
    <name>yarn.nodemanager.disk-health-checker.max-disk-utilization-per-disk-percentage</name>
    <value>98.5</value>
</property>
```

因为当没有磁盘空间，或因为权限问题，会导致作业失败，所以不要禁用磁盘检查。更详细的信息可以： https://hadoop.apache.org/docs/current/hadoop-yarn/hadoop-yarn-site/NodeManager.html#Disk_Checker

参考：http://stackoverflow.com/questions/29131449/hadoop-unhealthy-node-local-dirs-are-bad-tmp-hadoop-hduser-nm-local-dir
