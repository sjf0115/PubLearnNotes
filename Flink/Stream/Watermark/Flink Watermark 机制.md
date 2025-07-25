---
layout: post
author: sjf0115
title: Flink Watermark 机制
date: 2021-01-09 18:12:01
tags:
  - Flink

categories: Flink
permalink: flink-stream-event-time-and-watermark
---

> Flink版本：1.11.0

## 1. 为何要使用 Watermark？

在说 Watermark 之前，我们先提一下 EventTime（事件时间）和 ProcessingTime（处理时间）。事件时间是事件在现实世界中发生的时间，处理时间是 Flink 系统处理该事件的时间。如果我们比较关心事件实际发生的时间，我们就需要基于事件时间进行处理。但是基于事件时间，我们就不得不面对乱序的问题。

通常情况下，由于网络或者系统等外部因素影响，事件往往不能及时传输到 Flink 系统中，导致数据延迟到达。另一方面，流处理从事件产生，到流经 Source，再到算子，中间是有一个过程和时间的。虽然大部分情况下，流到算子的数据都是按照事件产生的时间来的，但是也可能由于网络、背压等原因，导致乱序的产生。

因此，我们需要一种机制能够控制数据处理的过程和进度，比如，基于事件时间的 Window 创建后，那如何确定属于该 Window 的数据已经全部到达。如果确定全部到达，就可以对 Window 的所有数据做窗口计算操作，如果数据没有全部到达，则继续等待该 Window 中的数据全部到达才开始处理。这种情况下就需要使用 Watermark，它能够衡量数据处理进度（表达数据到达的完整性），保证事件数据全部到达 Flink 系统，或者在乱序以及延迟到达时也能够像预期一样计算出正确并且连续的结果。Flink 会用最新的事件时间减去最大可以容忍的延迟时间最为 Watermark，也就是说理论上不会有事件超过该容忍延迟时间到达，否则被认为是迟到事件。

Watermark 的出现是为了解决一定范围内的乱序问题，一定范围内表明我们不会无限制的等待延迟的事件，我们有一定的可容忍的延迟时间。Watermark 用来表明所有比当前 Watermark 事件时间早的事件都已经（可能）到达，从而来衡量数据处理进度（表达数据到达的完整性）。

## 2. Watermark 如何产生？

### 2.1 顺序事件中的 Watermark

如果数据元素的事件时间是有序的，Watermark 时间戳会随着数据元素的事件时间按顺序生成，此时 Watermark 的变化和事件时间保持一致，这就是理想状态中的 Watermark。如下图所示， 事件按照其原本的顺序进入 Flink 系统中，Watermark 也跟随着事件时间之后生效，可以看出 Watermark 只是对数据流简单的进行周期性标记，并没有特别大的意义，也就是说在顺序事件的数据处理过程中，Watermark 并不能发挥太大的价值，反而会因为设定超期时间而导致延迟输出计算结果。

![](img-flink-stream-event-time-and-watermark-1.jpg)

### 2.2 乱序事件中的 Watermark

现实情况下数据往往并不是按照其生产顺序接入到 Flink 系统中进行处理，而是会频繁出现乱序或者迟到的情况，这种情况就需要使用 Watermark 来应对。当事件无序时，我们通常认为他们具有一定的无序性，即表明数据不可能无限期的延迟，只是在一定范围内处于一种无序状态，那么这个时候我们通过 MaxOutOfOrderness 参数设定最大乱序时间。如下图所示 MaxOutOfOrderness = 4，表明可以接受有4个时间单位的延迟，比如4秒或者4分钟等。当超过4个时间单位之后，我们认为这个数据就是一种无效数据。在4个时间单位之内接入的数据，我们认为是一种有效的乱序事件。在乱序的情况下，我们看看会产生怎样的 Watermark。在这通过 MaxOutOfOrderness 参数去计算我们的 Watermark，也就是会在我们的事件时间的基础之上减去我们的 MaxOutOfOrderness，比如事件时间为7，Watermark 就为 3（事件时间减去 MaxOutOfOrderness）：

![](img-flink-stream-event-time-and-watermark-2.jpg)

> Watermark = 当前最大时间戳 - 最大乱序时间（MaxOutOfOrderness）

每当新来一条数据，如果高于了我们前面的最大事件时间，就会触发一个 Watermark 的更新。比如事件时间 11 高于前面的最大事件时间 7，就会触发 w(7) 的更新：

![](img-flink-stream-event-time-and-watermark-3.jpg)

对于事件时间 7 产生 Watermark 3，事件时间 11 产生 Watermark 7，但是对于 9 这样一条事件，我们发现它的事件时间没有超过我们前面的事件时间的最大值（11），那么就不会触发 Watermark 的更新。

我们发现 Watermark 的更新其实是根据我们事件时间的变动而发生变化，如果新接入的事件时间大于了前面的事件时间，这时候才会触发产生 Watermark，即每当有新的最大事件时间出现时，就可以产生新的 Watermark。

![](img-flink-stream-event-time-and-watermark-4.jpg)

| 事件时间   | 当前最大事件时间 | Watermark    | 是否触发 |
| :------------- | :------------- | :------------- | :------------- |
| 7  |  7 | w(3)  | 是 |
| 11 | 11 | w(7)  | 是 |
| 9  | 11 | w(7)  | 否 |
| 15 | 15 | w(11) | 是 |
| 12 | 15 | w(11) | 否 |
| 13 | 15 | w(11) | 否 |
| 17 | 17 | w(13) | 是 |
| 14 | 17 | w(13) | 否 |
| 21 | 21 | w(17) | 是 |
| 24 | 24 | w(20) | 是 |
| 22 | 24 | w(20) | 否 |
| 19 | 24 | w(20) | 否 |

但是对于事件时间 19 这样一条数据，我们发现它的时间戳已经小于了当前的 Watermark 的时间，这个时候系统就会将这条数据标记为迟到事件。迟到事件在窗口计算时就不会被纳入窗口的统计范围内，w(20) 之前的数据会被纳入到窗口的统计范围内。

![](img-flink-stream-event-time-and-watermark-5.jpg)

### 2.3 并行数据流中的Watermark

Watermark 一般在 Source 算子中生成，并且在每个 Source 算子的子任务中都会独立生成 Watermark。在 Source 算子的子任务中生成后就会更新该任务的 Watermark，并且会逐步更新下游算子中的 Watermark。如下图所示，Watermark w(17) 已经将 Source 算子和 Map 算子的子任务时钟全部更新值为 17。如果多个 Watermark 同时更新一个算子子任务的当前时间，Flink 会选择最小的 Watermark 来更新。

![](img-flink-stream-event-time-and-watermark-6.jpg)

## 3. Watermark与窗口的关系

Watermark 在 Flink 系统中本身没有太大的意义，只有与窗口结合才能产生其相应价值。对于窗口来讲，其实是通过 Watermark 去控制它的窗口触发时机，告诉窗口不再会有比当前 Watermark 更晚的数据到达了。只有当 Watermark 大于窗口的右边界时才会触发窗口的计算。下面我们通过具体的示例一起来看一下 Watermark 怎么应用于窗口之中。下面我们创建一个窗口大小为10分钟，滑动步长为5分钟的滑动窗口。我们的输入元素都有特定格式:<事件Id,事件时间>，我们的目标就是统计每个事件Id在窗口中出现的次数。假设我们可以接受的最大乱序时间 MaxOutOfOrderness 为10分钟，即10分钟以外的数据我们标记为延迟事件：

| 序号 | 输入 | 当前最大时间(时间戳) | 当前Watermark(时间戳) | 属于窗口 | 触发窗口 | 触发元素| 计算结果 |
| :------------- | :------------- | :------------- | :------------- | :------------- | :------------- | :------------- | :------------- |
| 1 | A,2021-01-05 12:07:01 | 2021-01-05 12:07:01 | 2021-01-05 11:57:00 | [12:00, 12:10]、[12:05, 12:15] | | | |
| 2 | B,2021-01-05 12:08:01 | 2021-01-05 12:08:01 | 2021-01-05 11:58:00 | [12:00, 12:10]、[12:05, 12:15] | | | |
| 3 | A,2021-01-05 12:14:01 | 2021-01-05 12:14:01 | 2021-01-05 12:04:00 | [12:05, 12:15]、[12:10, 12:20] | | | |
| 4 | C,2021-01-05 12:09:01 | 2021-01-05 12:14:01 | 2021-01-05 12:04:00 | [12:00, 12:10]、[12:05, 12:15] | | | |
| 5 | C,2021-01-05 12:15:01 | 2021-01-05 12:15:01 | 2021-01-05 12:05:00 | [12:10, 12:20]、[12:15, 12:25] | | | |
| 6 | A,2021-01-05 12:08:01 | 2021-01-05 12:15:01 | 2021-01-05 12:05:00 | [12:00, 12:10]、[12:05, 12:15] | | | |
| 7 | B,2021-01-05 12:13:01 | 2021-01-05 12:15:01 | 2021-01-05 12:05:00 | [12:05, 12:15]、[12:10, 12:20] | | | |
| 8 | B,2021-01-05 12:21:01 | 2021-01-05 12:21:01 | 2021-01-05 12:11:00 | [12:15, 12:25]、[12:20, 12:30] | [12:00, 12:10] | 1、2、4、6 | (A,2)、(B,1)、(C,1) |
| 9 | D,2021-01-05 12:04:01 | 2021-01-05 12:21:01 | 2021-01-05 12:11:00 | [11:55, 12:05]、[12:00, 12:10] | | | |
| 10 | B,2021-01-05 12:26:01 | 2021-01-05 12:26:01 | 2021-01-05 12:16:00 | [12:20, 12:30]、[12:25, 12:35] | [12:05, 12:15] | 1、2、3、4、6、7 | (A,3)、(C,1)、(B,2) |
| 11 | B,2021-01-05 12:17:01 | 2021-01-05 12:26:01 | 2021-01-05 12:16:00 | [12:10, 12:20]、[12:15, 12:25] | | | |
| 12 | D,2021-01-05 12:09:01 | 2021-01-05 12:26:01 | 2021-01-05 12:16:00 | [12:00, 12:10]、[12:05, 12:15] | | | |
| 13 | C,2021-01-05 12:30:01 | 2021-01-05 12:30:01 | 2021-01-05 12:20:00 | [12:25, 12:35]、[12:30, 12:40] | [12:15,12:20] | 3、5、7、11 | (B,2)、(C,1)、(A,1) |

> maxOutOfOrderness=10分钟，watermark(t)=currentMaxTimeStamp(t)-maxOutOfOrderness(t)-1

第二列是我们输入的事件，第三列是当前最大的事件时间，第四列是当前最新的 Watermark，第五列是当前事件所属于的窗口，第六列是当前 Watermark 触发了哪个窗口的计算，第七列是哪些事件在这个触发的窗口中，第八列是窗口计算的最终结果。

当第一条数据接入 Flink 系统时，会产生一个新的 Watermark，同时会产生 [12:00, 12:10]、[12:05, 12:15] 两个窗口。当第二条数据到达时，由于大于了前面的事件时间，因此会触发 Watermark 的更新，该数据属于前面一条数据创建的窗口中。前7条数据比较类似，都是创建每条数据属于的窗口以及每当有新的最大事件时间出现，都会触发 Watermark 的更新。第8条数据到来时，由于都大于前面的事件时间，因此产生新的 Watermark（2021-01-05 12:11:00）。由于当前的 Watermark 大于第一个窗口 [12:00, 12:10] 的右边界，因此第一次触发窗口的计算。同理，第13条数据到来时，触发了第二次窗口计算。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg)

参考:
- [Event Time and Watermarks](https://ci.apache.org/projects/flink/flink-docs-release-1.10/dev/event_time.html#event-time-and-watermarks)
- Flink核心技术与实战
