---
layout: post
author: smartsi
title: Flink 深入理解对齐与非对齐 Checkpoint 的 Barrier 对齐机制
date: 2026-11-13 17:05:00
tags:
  - Flink

categories: Flink
permalink: flink-aligned-unaligned-checkpoint-barrier-alignment
---

Flink 的 Exactly-Once 容错建立在 Checkpoint 之上，而 Checkpoint 能否正确、快速地完成，核心取决于一个动作：**Barrier 对齐（Barrier Alignment）**。当一个算子有多个输入通道时，各通道的 Barrier 不会同时到达，算子必须决定「以哪个时刻作为本次快照的切分点」——对齐 Checkpoint 与非对齐 Checkpoint 给出了两种截然不同的答案。

很多资料只告诉你「对齐要等待、非对齐不等待」，却很少讲清楚：**等待的到底是什么？不等待之后丢掉的语义靠什么补回来？为什么非对齐要把在途数据也写进快照？** 这篇文章就从 Barrier 的本质出发，把两种机制的 Barrier 对齐过程逐段拆透，讲清它们各自如何保证一致性、各自付出什么代价，以及工程上如何取舍；并重点澄清两个容易被误解的事实：**非对齐并没有消除对齐，而是把对齐移到了异步阶段**；**非对齐之后 Barrier 转变更快了，但 task 的 ack 时机反而发生变化，与 Barrier 转发解耦**。

## 1. 前置：Barrier 是什么，多输入算子难在哪

### 1.1 Barrier 的三个关键性质

Checkpoint Barrier 是一种随数据流一起流动的特殊控制记录，它有三个决定后续一切设计的性质：

- **位置固定**：Barrier 由 Source 在快照自身状态后注入数据流，它在流中的位置是确定的，不能超前也不能滞后于数据。它把一条流切成两段：Barrier 之前的数据属于本次 Checkpoint，Barrier 之后的数据属于下一次 Checkpoint。
- **FIFO 随流**：Barrier 不是走独立控制通道，而是和普通数据 Buffer 排在同一个队列里，按 FIFO 顺序向下游传递。这意味着**Barrier 的推进速度等于数据流的推进速度**。
- **携带编号**：每个 Barrier 带一个 Checkpoint ID，算子据此判断「这是第几次快照的切分标记」。

### 1.2 单输入算子很简单，多输入算子才是难点

对只有一个输入通道的算子，快照逻辑是平凡的：收到 ID 为 n 的 Barrier → 触发本地状态快照 → 把 Barrier 转发给下游 → 继续处理后续数据。切分点就是 Barrier 到达的那一刻。

但现实中的算子（如 keyBy 之后的聚合、join、window）往往有**多个输入通道**。由于上游各子任务处理速度不同、网络延迟不同、甚至存在数据倾斜，**同一个 Checkpoint 的 Barrier 在不同输入通道上的到达时间是错开的**。这就产生了一个根本性问题：

> 算子的本地状态是「所有输入共同作用」的结果。当第一个通道的 Barrier 到达时，其他通道还有「本该属于本次快照」的数据没到；如果此刻就快照，状态就少算了这些数据；如果等到所有数据都处理完再快照，又不知道「等到什么时候为止」。

Barrier 对齐机制，就是为了解决这个「多输入切分点对齐」的问题。对齐与非对齐，是两种不同的解法。

## 2. 对齐 Checkpoint：用「等待 + 缓存」对齐切分点

对齐 Checkpoint（Aligned Checkpoint，Flink 默认模式）的思路是：**以最后一个到达的 Barrier 为切分点，在此之前把快通道「多出来的」数据缓存起来不处理**。我们逐段拆解。

### 2.1 对齐过程逐段拆解

设算子有两个输入通道 ch1（快）和 ch2（慢），Checkpoint n 进行中。

**阶段一：首个 Barrier 到达，进入对齐状态。**
ch1 的 Barrier(n) 先到达。此刻算子不能快照（ch2 还有属于本次快照的数据未到），也不能继续处理 ch1 在 Barrier 之后的数据（那些数据属于快照 n+1，提前处理会污染快照 n 的状态）。于是算子做两件事：
- 把 ch1 标记为「已对齐（blocked）」；
- 此后 ch1 新到达的数据**只接收、不处理**，放入一个对齐缓存（alignment buffer / in-flight buffer pool）。

**阶段二：慢通道继续推进。**
ch2 尚未收到 Barrier(n)，算子照常处理 ch2 的数据，这些数据属于快照 n，会被计入本次状态。与此同时 ch1 的后续数据在缓存中持续堆积。

**阶段三：最后一个 Barrier 到达，对齐完成。**
ch2 的 Barrier(n) 到达，所有通道对齐完毕。此刻算子的状态恰好等于「每个输入都处理到各自 Barrier 位置」的一致状态——这正是全局一致快照要求的切分点。算子随即：
- 触发本地状态快照（同步阶段准备 + 异步阶段上传）；
- 把 Barrier(n) 广播转发给所有下游输出通道；
- 解除 ch1 的阻塞，开始处理阶段一缓存的数据（这些数据属于快照 n+1）。

### 2.2 为什么缓存的数据不能处理，也不能入快照

这是理解对齐机制的关键，很多人卡在这里。ch1 在 Barrier 之后缓存的数据，逻辑上属于**下一次**快照（n+1）。如果在对齐等待期间处理它们，算子状态就会「超前」，把 n+1 的影响混进快照 n，破坏一致性；如果把它们写进快照 n，同样越界。所以对齐模式的正确做法是：**缓存、不处理、不入本次快照**，等对齐完成、快照 n 落定后，再作为 n+1 的输入处理。

换句话说，对齐缓存是一个「时间隔离区」：它把属于未来的数据暂时冻结，保证快照 n 只反映「所有输入都停在各自 Barrier 处」的状态。

### 2.3 对齐模式的代价

对齐机制逻辑干净、快照体积小（只含算子状态），但代价集中在「等待」上：

- **对齐延迟**：等于最慢通道 Barrier 到达时间减去最快通道到达时间。数据倾斜或某上游慢时，这个等待可以非常长，直接拉长 Checkpoint 耗时甚至超时。
- **缓存引发反压**：对齐缓存占用算子的 Input Buffer。快通道被阻塞后，其 Buffer 被缓存数据占满，根据 Credit 流控会向上游传导反压，使上游变慢、Barrier 更慢，形成「对齐等待 ↔ 反压」的恶性循环。
- **Barrier 受制于数据流**：Barrier 按 FIFO 排在积压数据后面，反压时 Barrier 传递本身就被拖慢，进一步放大对齐延迟。

一句话总结对齐模式：**用「阻塞快通道 + 缓存未来数据」换来一个干净的小快照，代价是把反压和对齐延迟引入关键路径。**

## 3. 非对齐 Checkpoint：用「插队 + 在途快照 + 异步对齐」搬走阻塞等待

非对齐 Checkpoint（Unaligned Checkpoint，Flink 1.11+ 引入）针对的正是对齐模式在反压下的痛点。它的核心改变有三条：**Barrier 不再排队而是插队；同步阶段不再等待所有 Barrier；对齐被搬到异步阶段、以关闭在途数据写入的形式存在。** 取消同步等待会破坏切分语义，必须用「在途数据快照」补回来。我们逐段拆解。

### 3.1 Barrier 插队：把 Barrier 提到所有数据之前

在对齐模式里 Barrier 按 FIFO 排在积压 Buffer 后面，反压时走不动。非对齐模式让 Barrier **overtake（越队）**：当算子决定转发 Barrier(n) 时，它把 Barrier 直接插到所有输出通道待发送 Buffer 的**最前面**，越过那些积压数据立即下发。

效果是 Barrier 的传递不再受数据积压阻塞——即使通道里堆了大量未发送数据，Barrier 也能瞬间到达下游。这从根上解决了「Barrier 被反压堵住」的问题。

### 3.2 同步阶段不等待：首个 Barrier 即快照并插队转发

对齐模式要等所有通道 Barrier 到齐才快照；非对齐模式**收到任意一个输入通道的 Barrier(n) 就立即触发本地状态快照，并立即把 Barrier(n) 插队转发给下游**，在同步阶段不做任何阻塞等待。

于是对齐模式那种「阻塞快通道、缓存未来数据」的行为消失了——快通道照常处理，Barrier 也在首个 Barrier 时刻就下发给下游，整条 Barrier 传递链不再被慢通道拖累。**被消除的，是同步阶段的阻塞式对齐等待。**

但要注意：这并不意味着非对齐不再关心其余通道的 Barrier。等待没有被消除，只是被搬走了——它藏进了异步阶段，去决定在途数据何时写完、本 task 何时能上报 ack（见 3.4 与 3.5）。

### 3.3 关键补偿：在途数据（in-flight data）必须入快照

取消等待带来一个语义缺口，这是非对齐机制最精妙也最容易被忽略的部分。

考虑 Barrier 插队并立即转发后，有一批数据处于「尴尬」位置：它们在逻辑上属于本次快照 n（位于 Barrier 之前），但因为 Barrier 插队越过它们、且算子没等慢通道，它们**既没被处理进状态、也还没真正送达下游**。这批数据就是**在途数据（in-flight data）**，具体包括两类：

- **输出侧**：各 Result Subpartition 中已由算子写出、但尚未发送到下游的 Buffer——Barrier 插队时越过了它们，下游会先收到 Barrier、后收到这些 Buffer，因此必须靠快照保存并在恢复时重发；
- **输入侧**：分两部分，一是快照时刻各 Channel 中已接收但尚未处理的 Buffer；二是更隐蔽的一类——**快照时刻之后、Barrier 尚未到达的通道（慢通道）上陆续到达、且位于其 Barrier 之前的数据**（见 3.4，这是理解异步阶段对齐的关键）。

如果快照只存算子状态而丢弃这些在途数据，那么故障恢复时：输入侧在途数据会**丢失**（它们没进状态也没被重放），输出侧在途数据会**重复或丢失**，Exactly-Once 被破坏。

因此非对齐 Checkpoint 的快照内容 = **算子状态 + 全部在途 Buffer 数据**。Flink 通过 ChannelStateWriter 把这些 in-flight Buffer 原样写入 Checkpoint 存储（称为 channel state / in-flight state）。

### 3.4 异步阶段的 Barrier 对齐：等所有 Barrier 到齐以关闭在途写入

上一节留下一个问题：快照在首个 Barrier 时刻就触发了，那么**快照时刻之后、慢通道 Barrier 到达之前**陆续到达慢通道的数据怎么办？它们逻辑上位于自己的 Barrier(n) 之前、应属于快照 n，但状态快照已经在首个 Barrier 时刻拍完、不可能包含它们；而非对齐模式又不阻塞慢通道，算子会照常处理它们。若不额外保存，恢复时这部分数据就丢了，一致性被破坏。

Flink 的答案是：**把对齐搬到异步阶段**。具体过程：

- 快照触发后，ChannelStateWriter 对各输入 Channel 开始写 input channel state；
- 对 **Barrier 尚未到达的通道（慢通道）**，从快照时刻起，其**陆续到达且尚未处理的数据会被持续写入 input channel state**——因为它们进不了状态快照，只能靠 channel state 保存、恢复时重放；
- 某个通道的 Barrier(n) 真正到达时，该通道的 input channel state 写入才**关闭（finish）**；
- 直到**最后一个输入通道的 Barrier 到达**，全部 input channel state 关闭，本次快照的 channel state 部分才算写完。

这个「等所有输入通道 Barrier 到齐」的动作，就是非对齐模式里的 Barrier 对齐操作。它与对齐模式的对齐相比，有四个根本不同：

| | 对齐模式的对齐 | 非对齐模式的对齐 |
| --- | --- | --- |
| 发生阶段 | 同步阶段（快照之前） | 异步阶段（快照之后） |
| 是否阻塞数据处理 | 阻塞：快通道数据只缓存不处理 | 不阻塞：各通道照常处理 |
| 是否阻塞 Barrier 转发 | 阻塞：对齐完成才转发 | 不阻塞：首个 Barrier 已插队转发 |
| 对齐的目的 | 决定「何时可以拍快照」 | 决定「何时可以关闭 channel state 写入」 |

所以准确的表述是：**非对齐没有消除对齐，而是把对齐从「数据处理与 Barrier 传递的关键路径」上移开，放到异步阶段后台完成。** 被消除的是阻塞式等待，而不是等待本身。

### 3.5 Checkpoint ack 时机的变化

Checkpoint 的完成靠 ack（acknowledge）确认：task 完成本地快照后向 JobManager 的 CheckpointCoordinator 上报确认消息，Coordinator 收齐所有 task 的 ack 才把该 checkpoint 标记为完成。对齐阶段的搬移，直接改写了每个 task 的 ack 时机。

**对齐模式的时间线**：所有 Barrier 到齐（同步阶段对齐，阻塞）→ 同步快照 → 转发 Barrier → 异步上传状态 → **异步完成后 ack**。对齐在快照之前，ack 依赖「阻塞对齐 + 状态上传」。

**非对齐模式的时间线**：首个 Barrier 到达 → 同步快照（极短）→ **立即插队转发 Barrier（下游从此提前推进，与本 task 的 ack 解耦）** → 异步阶段：一边上传算子状态，一边**持续把慢通道数据写入 channel state，等所有 Barrier 到齐后关闭 channel state** → 上传 channel state → **算子状态与 channel state 都上传完成后才 ack**。

由此得到三个关键变化：

- **Barrier 转发与 ack 解耦**：非对齐模式下 Barrier 转发发生在首个 Barrier 时刻、非常早；但本 task 的 ack 要等异步对齐与 channel state 上传、非常晚。下游「收到 Barrier」与本 task「上报 ack」不再像对齐模式那样时间上接近。
- **ack 的依赖项改变**：由对齐模式的「同步对齐完成 + 状态上传完成」，变为「异步对齐完成（channel state 关闭）+ 算子状态上传完成 + channel state 上传完成」。ack 的瓶颈从「同步对齐」转移到「异步对齐 + channel state 上传」。
- **观测指标的含义改变**：非对齐模式 sync duration 极短，原本同步阶段的对齐等待被搬进异步阶段——因此反压时会看到「sync 极短、async 很长」，长的 async 里既包含等慢 Barrier 到齐（异步对齐）的时间，也包含 channel state 上传时间。**Checkpoint 的端到端时长未必变短，但区别在于这段时间不再阻塞数据处理与下游 Barrier 传递。**

对 JobManager 而言，单次 checkpoint 的完成条件不变（收齐所有 task 的 ack）；变化的是每个 task 从「触发」到「ack」这段时间的内部结构。

### 3.6 恢复：状态 + 在途数据重放

非对齐 Checkpoint 的恢复也比对齐多一步：

- 恢复算子状态（与对齐相同）；
- **把快照中的在途 Buffer 重新注入回对应的 Input/Output Channel**，让这些数据像没发生故障一样继续流动、被处理或发送。

通过「状态回滚 + 在途数据重放」，非对齐模式在不等待 Barrier 的前提下，依然还原出「所有输入处理到各自 Barrier 位置」的一致状态，保证 Exactly-Once。

### 3.7 非对齐模式的代价

- **快照体积变大**：快照除了状态还要存全部在途 Buffer。反压越严重、积压 Buffer 越多，快照越大，对远程存储写入压力越大。
- **恢复更重**：恢复时要额外重放 channel state，恢复时间和复杂度高于对齐。
- **不支持 Savepoint**：Savepoint 要求可移植、跨版本兼容，始终用对齐方式生成，不受非对齐开关影响。
- **额外 IO**：写 channel state 带来额外的存储与网络开销。

一句话总结非对齐模式：**用「Barrier 插队 + 在途数据入快照 + 异步阶段对齐」把阻塞式对齐等待搬离关键路径，将时间代价换成空间（快照体积）与 ack 延迟代价。**

## 4. 两种机制的 Barrier 对齐对比

把两者放在同一张表里对照，差异一目了然：

| 维度 | 对齐 Checkpoint | 非对齐 Checkpoint |
| --- | --- | --- |
| Barrier 传递 | FIFO 排队，受积压数据阻塞 | 插队到队首，越过积压数据 |
| 同步阶段等待 | 等待所有通道 Barrier 到齐才快照 | 不等待，首个 Barrier 即快照并转发 Barrier |
| 对齐动作所在阶段 | 同步阶段（阻塞处理与转发） | 异步阶段（不阻塞，仅关闭 channel state） |
| ack 依赖 | 对齐完成 + 状态异步上传完成 | 异步对齐完成 + 状态与 channel state 上传完成 |
| 快通道 Barrier 后数据 | 缓存、不处理、不入本次快照 | 照常处理（属在途者入快照） |
| 在途数据 | 不入快照 | 输入/输出在途 Buffer 全部入快照 |
| 快照内容 | 仅算子状态 | 算子状态 + channel state |
| 快照体积 | 小 | 大（反压时显著增大） |
| 对齐延迟 | 有，取决于最慢通道 | 无 |
| 反压敏感度 | 高（缓存加剧反压、恶性循环） | 低（Barrier 不受反压阻塞） |
| 恢复方式 | 仅恢复状态 | 恢复状态 + 重放在途 Buffer |
| Savepoint | 支持 | 不支持（Savepoint 恒为对齐） |
| 适用场景 | 无反压、状态大、存储敏感 | 反压严重、对齐频繁超时 |

可以看到，两者本质是**时间 vs 空间**的权衡：对齐用「等待时间」换「小快照」，非对齐用「大快照」换「零等待」。

### 4.1 一个容易混淆的点：AT_LEAST_ONCE 也不对齐

需要特别澄清：Flink 在 `AT_LEAST_ONCE` 语义下同样**不做 Barrier 对齐**（Barrier 到达即快照、不等待其他通道），但它**不保存在途数据**，因此恢复时可能重复处理，只能保证 At-Least-Once。而非对齐 Checkpoint 是**在 Exactly-Once 语义下**通过「在途数据入快照」来取消对齐。两者都「不等待」，但一致性保障完全不同，切勿混淆。

## 5. 工程折中：Aligned Checkpoint Timeout

生产环境往往不想二选一：平时不反压希望对齐的小快照，反压时又需要非对齐的成功率。Flink 1.12+ 提供 **Aligned Checkpoint Timeout** 混合策略：

- 先按对齐模式开始 Barrier 对齐；
- 若在设定时间内（如 30s）仍未对齐完成（说明反压严重），**自动切换为非对齐模式**完成本次快照；
- 若对齐在超时前完成，则保持对齐，快照体积小。

实现上由一个可在对齐/非对齐之间切换的 Barrier 处理器（Alternating 处理器）承担：超时前走对齐逻辑，超时后转为非对齐逻辑（Barrier 插队 + 在途入快照）。它兼顾了快照体积与成功率，是反压偶发场景下的推荐配置。

## 6. 实现视角：Barrier 处理器与 ChannelStateWriter

从源码结构看，两种机制的差异集中在「Barrier 到达后如何处理」这一层，Flink 用一组 CheckpointBarrierHandler 抽象来承载：

- **对齐模式**：Barrier 处理器维护「已对齐通道集合」与对齐缓存。首个 Barrier 到达即阻塞该通道后续数据入缓存；集合满（所有通道到齐）才触发快照、转发 Barrier、释放缓存。
- **非对齐模式**：Barrier 处理器在同步阶段不做通道阻塞与等待。任一 Barrier 到达即触发快照并把 Barrier 插队下发；同时通过 **ChannelStateWriter** 把各 Input/Output Channel 的在途 Buffer 异步写入 Checkpoint 存储——其中 Barrier 尚未到达的输入 Channel 会**持续写入、直到其 Barrier 到达才关闭**，这正是异步阶段的对齐操作。
- **Alternating 模式**：包装上述两者，按 aligned-checkpoint-timeout 在运行时切换。
- **恢复侧**：除状态恢复外，非对齐 Checkpoint 会读取 channel state，把在途 Buffer 重建回对应 Channel，再恢复处理。
- **ack 时机**：task 只在异步阶段完成后上报 ack，即「算子状态上传完成 + channel state 关闭并上传完成」。因此非对齐模式 Barrier 转发极早、ack 并不早，二者解耦；监控中 async duration 变长往往对应异步对齐等待与 channel state 上传。

理解这层抽象有助于排查问题：对齐相关的等待与缓存行为、非对齐相关的 channel state 写入与恢复，都发生在这一层，监控中的 Alignment Duration、Checkpointed Data Size 等指标也源于此。

## 7. 踩坑复盘

按惯例把典型踩坑集中在末尾复盘。

### 坑一：非对齐开启后快照体积暴涨，存储被打爆
**现象**：为解决反压超时开启非对齐，超时缓解了，但 Checkpointed Data Size 从几百 MB 涨到数 GB。
**根因**：非对齐快照包含全部在途 Buffer，反压严重时积压多，快照自然巨大。
**解决**：配合 Buffer Debloat 把每通道在途数据控制在约 1 秒吞吐内，从源头压缩 channel state。**经验：非对齐几乎应与 Buffer Debloat 成对使用。**

### 坑二：以为非对齐能加速 Savepoint，结果 Savepoint 卡死
**现象**：平时非对齐运行良好，停机做 Savepoint 却极慢/失败。
**根因**：Savepoint 恒用对齐方式生成，不受非对齐开关影响，反压下照样被拖垮。
**解决**：Savepoint 选低峰期或先消除反压。**经验：不要用 Checkpoint 成功率推断 Savepoint 成功率。**

### 坑三：把对齐缓存造成的反压误判为下游瓶颈
**现象**：监控显示某算子 HIGH 反压，但其下游 Busy 并不高，定位不到瓶颈。
**根因**：对齐模式下快通道被阻塞缓存数据，反压是「对齐等待」自身造成的，而非下游处理慢。
**解决**：结合 Alignment Duration 判断——对齐时间长说明反压源自对齐；切换非对齐或消除倾斜后反压消失。**经验：对齐模式下的反压可能是对齐机制自产的，别一味往下游找。**

### 坑四：AT_LEAST_ONCE 与非对齐混淆，误以为有 Exactly-Once
**现象**：配置了不等待 Barrier，以为开了非对齐 Exactly-Once，恢复后出现重复数据。
**根因**：语义被设为 AT_LEAST_ONCE，它不等待也不保存在途数据，只有 At-Least-Once；真正的非对齐 Exactly-Once 需 EXACTLY_ONCE + unaligned 开关。
**解决**：确认语义为 EXACTLY_ONCE 且显式开启 unaligned。**经验：「不等待」不等于「非对齐 Exactly-Once」，先看语义再看开关。**

### 坑五：恢复非对齐 Checkpoint 后短暂「卡顿」与重复感
**现象**：故障恢复后作业有一段时间吞吐偏低，且个别结果疑似重复。
**根因**：非对齐恢复需重放 channel state 的在途 Buffer，重放期间吞吐受限；在途数据重放本身是正确行为（保证不丢），下游若未幂等会看到「重放」痕迹。
**解决**：理解重放是机制的一部分；对下游做幂等或两阶段提交以吸收重放。**经验：非对齐恢复比对齐多一步在途重放，吞吐短暂下降属正常，下游需幂等兜底。**

### 坑六：见 Barrier 转快就误判 Checkpoint 一定快，或把「sync 短、async 长」误判为存储问题
**现象**：开启非对齐后下游 Barrier 确实变快，但反压时 checkpoint 端到端时长依然偏长；或监控页上 sync duration 极短、async duration 极长，被怀疑是远程存储写入慢。
**根因**：非对齐只是把对齐搬到异步阶段，并未消除——ack 必须等所有 Barrier 到齐关闭 channel state、并完成 channel state 上传。反压时慢通道 Barrier 到得慢、channel state 又大，async 自然长，与存储性能无关。
**解决**：结合 Alignment Duration（异步对齐等待）与 Checkpointed Data Size（含 channel state）判断；若 async 长源于 Barrier 慢，根因仍是反压/倾斜，应消除之；若源于 channel state 大，配合 Buffer Debloat。**经验：非对齐改变的是「等待发生的位置」，而不是「有没有等待」；Barrier 快 ≠ ack 快。**

---

## 总结

对齐与非对齐 Checkpoint 的本质，是回答同一个问题——**多输入算子如何确定全局一致的快照切分点**——的两种哲学：

- **对齐**：以最后一个 Barrier 为切分点，用「阻塞快通道 + 缓存未来数据」隔离时间，换来只含状态的小快照；代价是对齐延迟与反压恶性循环。
- **非对齐**：没有消除对齐，而是把对齐从阻塞的同步阶段搬到非阻塞的异步阶段——Barrier 插队、首个 Barrier 即快照并转发，异步阶段持续把慢通道数据写入 channel state、直到所有 Barrier 到齐才关闭，并以「在途数据入快照 + 恢复重放」补回语义；换来处理路径与 Barrier 传递不被阻塞，ack 则推迟到「异步对齐 + channel state 上传」之后；代价是快照体积与恢复复杂度。

二者是时间 vs 空间的权衡；Aligned Checkpoint Timeout 则提供了运行时自动切换的折中。记住两条判断准则：**反压严重、对齐频繁超时选非对齐（并配 Buffer Debloat）；状态巨大、存储敏感或需要 Savepoint 时优先对齐并从根上消除反压。** 监控中 Alignment Duration 与 Checkpointed Data Size 是区分两种模式健康度的最直接指标。
