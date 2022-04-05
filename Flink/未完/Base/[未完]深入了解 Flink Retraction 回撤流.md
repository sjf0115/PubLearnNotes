
Flink中，Kafka Source 是非回撤流，Group By 是回撤流。所谓回撤流，就是可以更新历史数据的流，更新历史数据并不是将发往下游的历史数据进行更改，要知道，已经发往下游的消息是追不回来的。更新历史数据的含义是，在得知某个Key（接在Key BY / Group By后的字段）对应数据已经存在的情况下，如果该Key对应的数据再次到来，会生成一条delete消息和一条新的insert消息发往下游。













- https://blog.csdn.net/a1240466196/article/details/109975823?spm=1001.2101.3001.6650.2&utm_medium=distribute.pc_relevant.none-task-blog-2%7Edefault%7ECTRLIST%7Edefault-2.essearch_pc_relevant&depth_1-utm_source=distribute.pc_relevant.none-task-blog-2%7Edefault%7ECTRLIST%7Edefault-2.essearch_pc_relevant
- https://blog.csdn.net/u013411339/article/details/119974387?spm=1001.2101.3001.6650.15&utm_medium=distribute.pc_relevant.none-task-blog-2%7Edefault%7ECTRLIST%7Edefault-15.highlightwordscore&depth_1-utm_source=distribute.pc_relevant.none-task-blog-2%7Edefault%7ECTRLIST%7Edefault-15.highlightwordscore
