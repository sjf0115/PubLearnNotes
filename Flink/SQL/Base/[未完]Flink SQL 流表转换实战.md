
## 1. 流转表


## 2. 表转流

与常规数据库表一样，可以通过 INSERT、UPDATE 以及 DELETE 修改动态表。动态表可以是一个只有一行且不断更新的表，也可以是一个没有 UPDATE 和 DELETE 的仅插入表，或者介于这两者之间的表。

在将动态表转换为流或将其写入外部系统时，需要对这些更改进行编码。Flink 的 Table API 和 SQL 支持三种方法来编码动态表的更改:
- Append-only stream：仅插入流
- Retract stream：回撤流
- Upsert stream：更新流

### 2.1 仅插入流

```
A dynamic table that is only modified by INSERT changes can be converted into a stream by emitting the inserted rows.
```
通过上面可以知道，如果动态表只包含 INSERT 插入变更，那么动态表就可以转化为 Append-only 流，所有数据追加到流里面。


表必须只有插入(追加)变更，如果通过更新或者删除变更对表进行了修改，那么转换将失败。


### 2.2 回撤流

回撤流包含两种类型的消息：添加消息和回撤消息。通过将 INSERT 操作编码为添加消息、将 DELETE 操作编码为回撤消息、将 UPDATE 操作编码为更新(先前)行的 retract message 和更新(新)行的 add message，将动态表转换为 retract 流。下图显示了将动态表转换为 retract 流的过程。

### 2.3 更新流



- 参考：https://www.jianshu.com/p/c352d0c4a458
https://blog.csdn.net/weixin_41197407/article/details/116996980
