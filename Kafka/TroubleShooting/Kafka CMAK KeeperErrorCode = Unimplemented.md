## 1. 现象

打开 CMAK Web UI，添加 Kafka 集群时报如下错误：
```
Yikes! KeeperErrorCode = Unimplemented for /kafka-manager/mutex Try again.
```

## 2. 解决方案

主要是 ZooKeeper 版本太低导致，需要升级到 3.5+ 版本。具体请参考[748](https://github.com/yahoo/CMAK/issues/748)
