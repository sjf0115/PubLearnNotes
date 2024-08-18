---
layout: post
author: sjf0115
title: Spark Streaming 2.3.1 监控应用程序
date: 2018-06-17 19:28:01
tags:
  - Spark
  - Spark Stream

categories: Spark
permalink: spark-streaming-monitoring-applications
---

除了Spark的[监控功能](http://spark.apache.org/docs/2.3.1/monitoring.html)外，Spark Streaming 还有其他的特定功能。当使用 StreamingContext 时，Spark Web UI 会额外显示一个 Streaming 选项卡，用来显示正在运行的 Receivers 的统计信息（Receivers 是否处于活跃状态，接收到的记录数量，接收器错误等）和已完成的批次（批处理时间，排队延迟等）。这可以用来监视流应用程序的进度。

Web UI中的以下两个指标尤为重要：
- Processing Time - 批处理时间。
- Scheduling Delay - 前面的批处理完成时当前批在队列中的等待时间。

如果批处理时间一直比批处理间隔长或者排队延迟持续增加，表明系统无法以批处理产生的速度处理这些数据（译者注：处理速度小于产生速度，导致数据处理不过来），整个处理过程滞后了。在这种情况下，考虑[降低批处理时间](http://spark.apache.org/docs/2.3.1/streaming-programming-guide.html#reducing-the-batch-processing-times)。

Spark Streaming 程序的进度也可以使用 [StreamingListener](http://spark.apache.org/docs/2.3.1/api/scala/index.html#org.apache.spark.streaming.scheduler.StreamingListener) 接口进行监控，该接口允许你获取 Receivers 状态和处理时间。请注意，这是一个开发者 API，将来可能会改进（报告更多信息）。

> Spark 版本 2.3.1

原文：http://spark.apache.org/docs/2.3.1/streaming-programming-guide.html#monitoring-applications
