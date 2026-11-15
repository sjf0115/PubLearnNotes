# Flink 反压诊断指南：如何用指标准确判断反压

> 本文以 **Flink 1.13.6 为版本基线**，聚焦一件事：**如何通过各项指标准确判断作业是否反压、反压发生在哪、方向如何传播**。指标清单来自官方博客 [《Flink Network Stack Vol. 2: Monitoring, Metrics, and that Backpressure Thing》](https://flink.apache.org/2019/07/23/flink-network-stack-vol.-2-monitoring-metrics-and-that-backpressure-thing/)（2019 年，对应 1.9 时代），**每项指标在 1.13.6 中的可用性与语义均已逐一对照源码核实**，版本差异处单独标注。

## 1. 判断反压需要两套"坐标系"

反压的物理本质一句话即可：**发送侧输出缓冲池拿不到可用 Buffer（下游收不动或网络发不出），数据"写不出去"**。成因有两类（官方博客口径）：接收方慢（自身被反压/处理不过来/GC、I/O 阻塞），或网络通道慢（带宽被同机 Checkpoint、DFS、日志、Metrics 等共享者超额订阅）。

围绕这个本质，Flink 提供了两套互补的指标坐标系：

| 坐标系 | 指标 | 回答的问题 |
|--------|------|-----------|
| **时间维度** | `busyTimeMsPerSecond` / `backPressuredTimeMsPerSecond` / `idleTimeMsPerSecond` | 任务线程这一秒在干嘛：干活？写不出去？还是没数据可干？ |
| **缓冲维度** | `outPoolUsage` / `inPoolUsage` / `floatingBuffersUsage` / `exclusiveBuffersUsage` | 缓冲池被占了多少：输出侧顶没顶满？输入侧吃不吃得下？ |

外加一组**速率/体量指标**（`numRecordsIn/OutPerSecond`、`numBytes*`、`numBuffers*`）做旁证。三组配合，才能做到"准确"二字——单看任何一个指标都可能误判。

## 2. 指标清单与 1.13.6 真实语义

### 2.1 时间三分法指标（1.13 起，Web UI/REST 反压监控的数据源）

**这是 1.13.6 判断反压的第一权威信号**，三者互斥、每秒之和恒为 1000ms：

| 指标 | 语义 | 判读 |
|------|------|------|
| `backPressuredTimeMsPerSecond` | 每秒中"有数据要发、但输出缓冲不可用"的毫秒数 | **持续 > 100ms 即存在可感知反压；接近 1000ms 为严重反压** |
| `busyTimeMsPerSecond` | 每秒中真正干活（用户代码、序列化、mailbox 处理）的毫秒数 | 接近 1000ms ⇒ 该任务是计算瓶颈的嫌疑犯 |
| `idleTimeMsPerSecond` | 每秒中"没有输入数据可处理"的毫秒数 | 高 ⇒ 在挨饿（上游慢），**与反压方向相反，切勿混淆** |

**版本差异（重要）**：

- **1.13 之前的 Web UI 反压比率来自线程栈采样**（周期性 `Thread.getStackTrace()` 统计阻塞在缓冲请求上的采样占比），旧采样代码在 1.13 中已整体删除；**1.13.6 的 Web UI/REST 比率直接等于 `backPressuredTimeMsPerSecond / 1000`**，是持续发布的 Metrics，零采样开销、可直接告警。
- 分级阈值不变：`ratio ≤ 0.10` → **OK**；`0.10 < ratio ≤ 0.5` → **LOW**；`ratio > 0.5` → **HIGH**。REST 端点仍为 `/jobs/:jobid/vertices/:vertexid/backpressure`，每个 Subtask 返回 `ratio / idleRatio / busyRatio` 三元组。
- **Vertex 级等级 = 所有 Subtask ratio 的最大值**。UI 上一个 Vertex 标红，可能只有一个 Subtask 在反压——必须下钻 Subtask 视图区分"全局瓶颈"还是"数据倾斜"。
- `busyTimeMsPerSecond` 是派生指标（1000 − idle − backPressured），受启用开关门控：1.13.6 的流式任务默认启用；若在其他场景看到 NaN，是开关未启用而非数据缺失。

### 2.2 缓冲池使用率指标（官方博客主力，1.13.6 语义如下）

| 指标 | 1.13.6 语义与判读 |
|------|------------------|
| `outPoolUsage` | 输出侧本地缓冲池使用率。**= 100% ⇒ 该 Subtask 已被反压**（官方原话：is backpressured）。注意它比时间比率"更早"：池满时任务可能还在往半满的 Buffer 里写、尚未真正阻塞，所以 `outPoolUsage=100%` 与 `backPressuredTimeMsPerSecond>0` 不要求同时出现 |
| `inPoolUsage` | 输入侧缓冲池使用率。**1.9 起 `inPoolUsage = floatingBuffersUsage + exclusiveBuffersUsage`**（1.13.6 同）。**持续 ≈100% ⇒ 输入吃满，正在（或即将）向上游施加反压**，是强信号 |
| `floatingBuffersUsage` | Gate 内共享浮动缓冲使用率。**未到 100% 基本可排除该输入在反压**；到 100% 且任一上游被反压 ⇒ 该输入正在对 Channel 施加反压 |
| `exclusiveBuffersUsage` | Channel 独占缓冲使用率。在 floating ≈100% 前提下，**它越高说明被反压的输入 Channel 越多**；接近 100% ⇒ 几乎所有 Channel 都被顶住（全局性瓶颈而非个别倾斜） |

**旧版本陷阱（1.13.6 不受影响，但混合集群/旧资料常见）**：1.8 及之前因 FLINK-11082，空的在途 Buffer 也被计入 backlog，导致 `inPoolUsage=100%` 在完全正常的场景也频繁出现；1.9 起只有"满的或已 flush 的" Buffer 才计入，`inPoolUsage` 高才真正成为反压信号。**引用任何 `inPoolUsage` 阈值经验前，先确认集群版本 ≥ 1.9。**

另有两条解读池使用率的"底噪"常识：任何使用过的输出 Channel 至少常驻占用 1 个 Buffer（1.5 起）；接收侧要等 Buffer 中最后一条记录反序列化完才释放它。低并行度小作业上池使用率天然偏高，阈值要留余量。

### 2.3 速率与体量指标（旁证，不能单独定反压）

| 指标 | 用途与注意 |
|------|-----------|
| `numRecordsInPerSecond` / `numRecordsOutPerSecond` | 上下游速率对比：上游明显高于下游 ⇒ 反压的直观表现。但**速率低 ≠ 反压**（可能只是 Source 慢），必须结合 2.1/2.2 确认 |
| `numBytesInLocal` / `numBytesInRemote` | 区分本地（同 TM）与远程流量；绝大多数场景无需分开看 |
| `numBuffersInLocal` / `numBuffersInRemote` | `numBytesInRemote / numBuffersInRemote` = 远程 Buffer 平均填充率。**填充率过低且目标是吞吐** ⇒ 增大 `taskmanager.network.memory.buffer-timeout`（默认 100ms）攒批；本地 Channel 无需分析填充率（缓冲优化只对远程通道有意义） |
| `numBuffersOut` | **有滞后**：只在 Buffer 写满或被事件（如 Checkpoint Barrier）切断时才递增（1.8/1.9 起如此，1.13.6 同），不能用它做实时反压判断 |
| `numRecordsOut` ÷ `numBytesOut` | 估算平均序列化记录大小，用于容量规划，非反压指标 |

**吞吐型异常的一个经典组合（官方博客精华）**：低吞吐 + 发送侧 `outPoolUsage` 频繁 100% + **所有**接收侧 `inPoolUsage` 低 ⇒ 不是算子慢，而是 credit 通知往返时延相对默认 exclusive 缓冲数过大、带宽吃不满（常见于跨机房/高延迟网络）。对策：增大 `taskmanager.network.memory.buffers-per-channel`（默认 2），或临时关闭 credit-based 流控做对照实验。

### 2.4 不要使用的指标

**`outputQueueLength` / `inputQueueLength`**：官方博客明确不推荐（discourage），1.13.6 中它们仍存在但同样不可用于判断：

- 绝对 Buffer 数难以解释，含义强依赖当前并行度与 exclusive/floating 配置；
- **本地 Channel 没有独立输入队列**（直接复用输出队列），其贡献恒为 0（FLINK-12576）——纯本地传输的作业 `inputQueueLength` 恒为 0，用它配告警会永远静默。

一律改用 `*PoolUsage` 系列 + 时间三分法。

### 2.5 延迟指标（辅助旁证）

`metrics.latency.interval` 开启后的 Latency 直方图可显示记录排队时间随反压上升，但注意三条边界：LatencyMarker 不进入用户代码，度量的**不是端到端延迟**；低负载 Channel 上每跳额外叠加约 `buffer_timeout / 2`；`subtask` 粒度指标量随并行度平方增长、开销大，官方建议仅调试用。判断反压请以 2.1/2.2 为准，延迟指标只做后果佐证（另需集群 NTP 时钟同步，否则数据不可信）。

## 3. 准确判定：指标组合决策法

### 3.1 官方组合判读表（in/out PoolUsage 四象限）

| | `outPoolUsage` 低 | `outPoolUsage` 高 |
|---|---|---|
| **`inPoolUsage` 低** | ✅ 健康 | 已被反压，属临时态：上游尚未（或不再）被反压 |
| **`inPoolUsage` 高（1.9+）** | 若**所有**上游 `outPoolUsage` 低：自身处理慢，即将向上游施加反压 | 被下游或网络反压，且很可能正在向上传播 |
| | 若**任一**上游 `outPoolUsage` 高：**可能正是反压源头** | 被下游反压并向上转发 |

叠加 `floating/exclusiveBuffersUsage` 进一步细分（1.9+，1.13.6 适用）：

| | `exclusiveBuffersUsage` 低 | `exclusiveBuffersUsage` 高 |
|---|---|---|
| **floating 低 + 所有上游 out 低** | ✅ 健康 | 不应出现 |
| **floating 低 + 任一上游 out 高** | ⚠️ 疑似网络瓶颈 | 不应出现 |
| **floating 高 + 所有上游 out 低** | 反压将出现在**部分**输入 Channel | 反压将出现在**大部分/全部** Channel |
| **floating 高 + 任一上游 out 高** | 反压已在部分 Channel | 反压已在大部分/全部 Channel |

**"部分 Channel" 通常指向数据倾斜，"全部 Channel" 指向全局性瓶颈**——这张表是从"是否反压"走向"什么形态的反压"的关键。

### 3.2 三分法定性：受害者、嫌疑犯、挨饿者

对任一 Subtask，看三个时间指标的占比：

- **BackPressured 高** ⇒ **受害者**：瓶颈在下游，继续往下游找；
- **Busy 高（且 BackPressured 低）** ⇒ **嫌疑犯**：自己算不过来，就是瓶颈候选；
- **Idle 高** ⇒ **挨饿者**：上游给得慢，与反压无关，直接排除。

### 3.3 沿数据流定位源头（完整判定流程）

1. **确认持续性**：反压指标看 5~10 分钟窗口。负载尖峰、Checkpoint 期间、故障恢复追数据造成的临时反压通常可忽略，不必处置。
2. **圈定嫌疑顶点**：沿 Source → Sink 方向，找**最后一个 BackPressured 高（或 `outPoolUsage` 高）的顶点**——官方博客口径：从最后一个正在经历反压的算子往后找，**它的下一个顶点就是头号嫌疑**。
3. **三分法定性嫌疑顶点**：Busy 高 ⇒ 坐实自身瓶颈（转入根因排查）；BackPressured 也高 ⇒ 瓶颈在更下游，回到第 2 步；Idle 高 ⇒ 排除，重新审视圈定。
4. **Subtask 下钻查倾斜**：同一顶点内各 Subtask 的 ratio、`busyTimeMsPerSecond`、`numRecordsInPerSecond` 悬殊 ⇒ 倾斜（记住 Vertex 级等级取的是最大值，一个红的就能把整个顶点标红）。
5. **甄别网络型反压**：发送侧 `outPoolUsage` 高、**所有**接收侧 `inPoolUsage` 低 ⇒ 瓶颈不在算子而在共享网络/同机其他进程（Checkpoint IO、DFS、日志、Metrics、其他 TM 进程）。

### 3.4 排除假信号

- **`inPoolUsage=100%` 但集群 ≤1.8**：大概率是 FLINK-11082 的正常现象，不是反压；
- **速率下降就报反压**：先看 Source 是否本来就没数据（Idle 高、各池使用率低 ⇒ 挨饿而非反压）；
- **周期性反压与 GC 重合**：开 GC 日志比对时间线，长停顿造成的"伪反压"要按 GC 问题处理；
- **反压伴随 Checkpoint 超时**（`Checkpoint expired before completing...`）：这是反压的**后果**信号（Barrier 在反压通道中传播变慢），可作旁证，但不能反推源头位置。

### 3.5 判定速查表

| 观察到的现象 | 结论 |
|--------------|------|
| `backPressuredTimeMsPerSecond` 持续 > 500 | 该 Subtask 处于严重反压（受害者），往下游找 |
| `busyTimeMsPerSecond` ≈ 1000 且 backPressured ≈ 0 | 该 Subtask 是瓶颈嫌疑犯 |
| `outPoolUsage` = 100% | 已被反压（可能尚未阻塞，比时间比率更早预警） |
| `inPoolUsage` 持续 ≈100%（≥1.9） | 正在向上游施加反压 |
| floating ≈100% + exclusive ≈100% | 全部输入 Channel 被顶住：全局瓶颈 |
| floating ≈100% + exclusive 不高 | 仅部分 Channel 反压：疑似倾斜 |
| 发送 out 高 + 所有接收 in 低 + 吞吐低 | 网络/credit 往返瓶颈，调 `buffers-per-channel` |
| `inputQueueLength` = 0 | 正常（本地 Channel 恒为 0），该指标不可用 |

## 4. 监控落地：Prometheus + 告警规则（1.13.6）

```yaml
# flink-conf.yaml
metrics.reporter.prom.factory.class: org.apache.flink.metrics.prometheus.PrometheusReporterFactory
metrics.reporter.prom.port: 9250-9260
```

```promql
# 反压告警：任一 Subtask 每秒被反压时间超过 500ms，持续 5 分钟
max by (job_name, task_name) (flink_taskmanager_job_task_backPressuredTimeMsPerSecond) > 500
  for: 5m

# 瓶颈自证：Busy 打满，持续 5 分钟
max by (job_name, task_name) (flink_taskmanager_job_task_busyTimeMsPerSecond) > 900
  for: 5m

# 缓冲顶满旁证：输出池使用率
max by (job_name, task_name) (flink_taskmanager_job_task_outPoolUsage) > 0.9
  for: 5m
```

两条纪律：

1. **一律 `max by` subtask 而非 avg**——与 REST 端点"Vertex 级取 Subtask 最大 ratio"保持同一口径，避免单个倾斜 Subtask 被平均值稀释；
2. **告警必须带持续窗口（for）**——三分法指标是瞬时秒级值，单点尖峰（Checkpoint、追数）不应触发。

Grafana 面板建议：每个核心顶点一块，画 BackPressured/Busy/Idle 堆叠面积图 + `outPoolUsage`/`inPoolUsage` 双折线，两坐标系对照着看。

## 5. 踩坑复盘：那些年误判过的反压

1. **把时间比率与池使用率当同一回事。** `ratio`（=backPressured 毫秒/1000）是"阻塞时间占比"，`outPoolUsage=100%` 是"缓冲顶满"——后者更早、前者更实。旧采样时代（≤1.12）的 ratio 语义又与两者都不同，跨版本对比历史数据前先确认测量机制。
2. **用 `inputQueueLength` 配告警，结果恒为 0。** 本地 Channel 无独立输入队列（FLINK-12576），官方明确不推荐这两个指标。
3. **在 1.8 集群把 `inPoolUsage=100%` 当反压。** FLINK-11082 修复前空 Buffer 也计 backlog，正常场景常见 100%；1.9+ 才是强信号。
4. **把 Idle 高当反压。** Idle 高是挨饿（上游慢/Source 限速），BackPressured 高才是被下游顶住，方向完全相反。
5. **把临时反压当故障。** 负载尖峰、Checkpoint 期间、恢复追数都会反压；所有结论基于持续窗口。
6. **用 avg 聚合配告警掩盖倾斜。** 单 Subtask 反压在平均值里消失；对齐 REST 口径用 max by subtask。
7. **看到 Vertex 标红就认定整个顶点是瓶颈。** 1.13.6 的 Vertex 等级取 Subtask ratio 最大值，可能只有一个倾斜 Subtask 在红。
8. **拿 `numBuffersOut` 做实时判断。** 它只在 Buffer 写满或被事件切断时递增，天然滞后。
9. **速率低就报反压。** 可能是 Source 没数据（Idle 高、池使用率低），先做 3.4 的排除。
10. **在 1.13.6 上找 Buffer Debloating 日志。** 该特性 1.14 才引入（FLIP-147），1.13.6 无此配置与日志，"1.13+ 支持 Debloating"的说法是讹传。
11. **`busyTimeMsPerSecond` 出现 NaN 就慌。** 它是派生指标且受启用开关门控，1.13.6 流式任务默认启用，NaN 只出现在未启用的任务类型上。
12. **把 Latency 直方图当端到端延迟。** LatencyMarker 不进用户代码、低负载每跳叠加约 `buffer_timeout/2`、依赖 NTP，只能做反压后果的旁证。

## 6. 总结

| 主题 | 结论（以 1.13.6 为准） |
|------|----------------------|
| 第一权威信号 | `backPressuredTimeMsPerSecond`（Web UI/REST 比率 = 它/1000；OK≤0.10<LOW≤0.5<HIGH） |
| 缓冲坐标 | `outPoolUsage=100%` ⇒ 已被反压；`inPoolUsage` 持续 100%（≥1.9）⇒ 正在向上游施压 |
| 形态细分 | floating/exclusive 组合区分"部分 Channel（倾斜）"与"全部 Channel（全局瓶颈）" |
| 定性口诀 | BackPressured 高=受害者，Busy 高=嫌疑犯，Idle 高=挨饿者 |
| 定位方向 | 沿数据流找最后一个反压顶点，其下一个顶点是头号嫌疑；发送 out 高+所有接收 in 低 ⇒ 网络型 |
| 禁用指标 | `outputQueueLength` / `inputQueueLength`（FLINK-12576）；`numBuffersOut`（滞后） |
| 告警纪律 | max by subtask + 持续窗口，口径对齐 REST 的"取最大值" |

一句话收束：**先用时间三分法定性每个 Subtask 的角色（受害者/嫌疑犯/挨饿者），再用 PoolUsage 四象限表确认反压的方向与覆盖面，沿数据流走到"最后一个受害者的下游"即源头**——两套坐标系互相印证，才能把"是否反压"判准，把"反压在哪"判对。
