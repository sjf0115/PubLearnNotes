### 1. 问题描述

```
127.0.0.1:6379> SET USER "yoona"
(error) MISCONF Redis is configured to save RDB snapshots,
but is currently not able to persist on disk.
Commands that may modify the data set are disabled.
Please check Redis logs for details about the error.
```
Redis被配置为保存数据库快照，但它目前不能持久化到硬盘。用来修改集合数据的命令不能用。请查看Redis日志的详细错误信息。是因为强制关闭Redis快照导致不能持久化。

### 2. 解决方案

运行如下命令来关闭配置项`stop-writes-on-bgsave-error`解决该问题：
```
127.0.0.1:6379> CONFIG SET stop-writes-on-bgsave-error no
OK
127.0.0.1:6379> SET USER "yoona"
OK
```
