https://nightlies.apache.org/flink/flink-docs-master/docs/dev/table/sql/queries/window-topn/
https://mp.weixin.qq.com/s/gd2XIlLx-LjZr0pUJnxSRQ

## 1. 简介

窗口 TopN 是一种特殊的 TopN，会为每个窗口以及分区键返回 N 个最小或者最大的值。

与常规 TopN 不同的是，窗口 TopN 不会产生中间结果（即不会产生回撤记录），只会在到达窗口末尾时产生总共 Top N 条记录。更重要的是，窗口 TopN 会清除所有不再需要的中间状态。因此，如果用户不需要每条记录的更新结果，那么窗口 TopN 查询具有更好的性能。通常，窗口 TopN 与窗口 TVF 一起直接使用。此外，窗口 TopN 还可以与基于窗口 TVF 的其他操作一起使用，例如窗口聚合、窗口 TopN 和窗口 JOIN。

窗口 TopN 可以用与常规Top-N相同的语法定义，有关更多信息，请参阅Top-N文档。此外，Window Top-N要求PARTITION BY子句包含应用窗口TVF或窗口聚合关系的window_start和window_end列。否则，优化器将无法转换查询。



Window Top-N语句的语法如下:
