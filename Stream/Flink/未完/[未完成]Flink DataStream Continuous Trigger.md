---
layout: post
author: smartsi
title: Flink DataStream Continuous Trigger
date: 2021-08-29 17:32:17
tags:
  - Flink

categories: Flink
permalink: flink-datastream-continuous-trigger
---

短窗口的计算由于其窗口期较短，那么很快就能获取到结果，但是对于长窗口来说窗口时间比较长，如果等窗口期结束才能看到结果，那么这份数据就不具备实时性，大多数情况我们希望能够看到一个长窗口的结果不断变动的情况，对此 Flink 提供了 ContinuousEventTimeTrigger  与 ContinuousProcessingTimeTrigger 触发器，指定一个固定时间间隔周期性输出当前窗口的结果，不需要等到窗口结束才能获取最终结果。



### 1. ContinuousProcessingTimeTrigger

### 2. ContinuousEventTimeTrigger














https://www.jianshu.com/p/a2807a91dc99
https://blog.csdn.net/u013516966/article/details/103105377

原文：[]()
