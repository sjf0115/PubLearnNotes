

> Flink 版本：1.14

本文主要描述 Flink 的 Source API 及其背后的相关概念和架构。如果您对 Flink 中的 Source 如何工作感兴趣，或者想要实现一个新的 Source，有必要阅读本文。

## 1. 概念

Source 有三个核心组件：Splits、SplitEnumerator 以及 SourceReader：
- Split：Source 消费数据的一部分，如文件或日志分区。分割是一种粒度，根据它源分发工作并并行读取数据。



SourceReader请求Split并处理它们，例如通过读取由Split表示的文件或日志分区。SourceReader在sourceoperator中的任务管理器上并行运行，并产生并行的事件/记录流。



SplitEnumerator生成拆分并将它们分配给sourcereader。它作为作业管理器上的单个实例运行，负责维护待处理拆分的积压，并以平衡的方式将它们分配给读者。



## 2. API

## 3.


- [Data Sources](https://nightlies.apache.org/flink/flink-docs-release-1.14/docs/dev/datastream/sources/)
