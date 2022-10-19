

org.apache.flink.table.runtime.operators.rank.AppendOnlyTopNFunction


Top N 根据数据源包含的数据内容（Insert、Update、Delete 消息），支持 UndefinedStrategy、AppendFastStrategy、RetractStrategy、UpdateFastStrategy 四种处理策略（源码参见： RankProcessStrategy） 对应三个处理子类： AppendOnlyTopNFunction、UpdatableTopNFunction、RetractableTopNFunction。


参考：
- [Flink SQL高效Top-N方案的实现原理](https://blog.csdn.net/u013411339/article/details/120857766)
https://www.cnblogs.com/Springmoon-venn/p/14653331.html
