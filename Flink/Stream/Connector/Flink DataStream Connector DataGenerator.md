
## 1. 简介

Flink 从 1.11 开始提供了一个内置的 DataGen Connector，主要是用于生成一些随机数，用于在没有数据源的时候，进行流任务的测试以及性能测试。

## 2. DataStream

如果你使用的是 DataStream ，则可以使用 DataGeneratorSource 来实现数据生成。DataGeneratorSource 是一个抽象数据生成器的 Source。

![](1)

从上图可以知道 DataGeneratorSource 继承实现了 RichParallelSourceFunction 抽象类

以支持对外部数据源中数据的并行读取操作：

可以在数据接入的过程中获取 RuntimeContext 信息，从而实现更加复杂的操作


### 2.1 用法

### 2.2 Generator



## 3. SQL

```sql

```




参考:
