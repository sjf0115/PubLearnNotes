

参数：
- hive.auto.convert.join：是否开启根据输入文件大小将 Common Join 转换成 Map Join 的优化。在 Hive 0.7.0 版本中引入该参数，默认值为 false，详见[HIVE-1642](https://issues.apache.org/jira/browse/HIVE-1642)。在 Hive 0.11.0 版本中修改默认值为 true，详见[HIVE-3297](https://issues.apache.org/jira/browse/HIVE-3297)。需要注意的是在 Hive 0.11.0 到 0.13.1，hive-default.xml.template 错误地将其默认值设置为 false。
- hive.auto.convert.join.noconditionaltask：是否开启了根据输入文件大小将 Common Join 转换成 Map Join 的优化。如果该参数开启，并且n-way join的n-1个表/分区的大小总和小于hive.auto.convert.join.noconditionaltask.size指定的大小，则直接转换join 到 mapjoin（没有条件任务）。


- hive.mapjoin.smalltable.filesize：小表输入文件大小的阈值，以字节为单位，默认值 25000000(25MB)。通过该参数来确定是否是一个小表，如果文件大小小于此阈值，会将 Common Join 转换为 Map Join。在 Hive 0.7.0 版本中引入 hive.smalltable.filesize 参数，详见[HIVE-1642](https://issues.apache.org/jira/browse/HIVE-1642)。后来在 Hive 0.8.1 版本中引入 hive.mapjoin.smalltable.filesize 参数以取代 hive.smalltable.filesize 参数。




参考：
- [Hive Configuration Properties](https://cwiki.apache.org/confluence/display/Hive/Configuration+Properties)
- HIVE-1642：https://issues.apache.org/jira/browse/HIVE-1642
- HIVE-3297：https://issues.apache.org/jira/browse/HIVE-3297
