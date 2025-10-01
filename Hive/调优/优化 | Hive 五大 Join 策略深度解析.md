引言

Hive 中 Join 操作的效率直接决定了海量数据处理作业的性能，其核心挑战在于如何最小化代价高昂的 Shuffle 过程并有效应对数据倾斜。理解不同 Join 算法的原理和适用场景，是进行有效调优的关键。

本文将深入剖析 Hive 支持的几种核心 Join 策略：
- Common Join (Shuffle Join)：通用但代价最高的基础方案
- Map Join (Broadcast Join)：避免 Shuffle 的小表关联利器
- Bucket Map Join：利用分桶特性扩展 Map Join 适用范围
- Sort Merge Bucket (SMB) Join：基于分桶排序的无 Shuffle、低内存消耗关联
- Skew Join：针对性解决数据倾斜问题的优化手段

我们将探讨 Hive Join 每种算法的实现机制、触发条件、优缺点、关键配置参数及其适用场景。帮助开发者在面对不同数据规模和分布特征时，做出最优的技术选择。

## 1. Common Join (Reduce Join / Shuffle Join)

> 引入版本：Hive 最初版本 (0.x) 即支持，是最基础的 Join 实现。

![](https://mmbiz.qpic.cn/mmbiz_png/iaibeauBlUEfjgc4fDM7N82YnhvjB8XbUQFhgbHR2a5CDmbIKHJlvgy3zcDNFFoQ9L2b9Laq6TqtgWiavKUMcxoNg/640?wx_fmt=png&from=appmsg&watermark=1&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=0)

> 执行引擎：兼容 MR 和 Tez。在 Tez 上效率更高(优化 Shuffle 过程)。

### 1.1 原理

这是 Hive 最基础、最通用的 Join 实现，适用于任何大小的表。
- Map阶段：每个 Mapper 读取输入表(或分区)的数据。为每条记录打上标签(Tag) 标明来源表，并将 Join Key 作为输出 Key，将(Tag + 记录值)作为输出 Value。
- Shuffle 阶段： 框架根据Join Key对所有Mapper的输出进行排序(Sort) 和分区(Partition)，确保相同Key的所有记录(无论来自哪个表)都被发送到同一个Reducer。
- Reduce 阶段： 每个 Reducer 接收到所有表中具有相同 Join Key 的记录集合。Reducer在内存中根据Tag将记录分组到不同的“篮子”里(例如，左表篮子、右表篮子)。然后执行笛卡尔积(Cartesian Product) 或根据Join类型(INNER, LEFT, RIGHT, FULL)组装最终结果。

### 1.2 优点

通用性强，可处理任意大小的表，支持所有 Join 类型。

### 1.3 缺点

- Shuffle 开销巨大：需要通过网络传输所有参与 Join 的数据，并在 Reducer 端进行全排序，I/O和网络压力大。
- Reducer 内存压力：如果某个 Key 对应的记录非常多(数据倾斜)，会导致单个 Reducer 内存溢出(OOM)。
- 性能相对较低： 相比其他优化算法，通常是最慢的。

### 1.4 触发条件

当没有其他优化条件被满足时(例如，表太大无法 Map Join，或者没有分桶无法 SMB Join)，Hive 会自动选择 Common Join。也可通过SET `hive.auto.convert.join=false;` 强制所有 Join 使用 Common Join。

### 1.5 关键参数：

- `hive.auto.convert.join`：若设为 false，则禁用 Map Join 自动转换，强制走 Common Join。
- `hive.exec.reducers.bytes.per.reducer`：控制每个 Reducer 处理的数据量，影响并行度。
- `hive.optimize.reducededuplication`：减少重复数据 Shuffle (MR 引擎)。

数据要求：无特殊要求，通用性强。但数据倾斜时性能极差。

## 2. Map Join (Broadcast Join)

> 引入版本：Hive 0.3.0 引入基础支持，Hive 0.7.0 优化并加入自动判断。

![](https://mmbiz.qpic.cn/mmbiz_png/iaibeauBlUEfjgc4fDM7N82YnhvjB8XbUQOLVQhDLTV8Axrroq6LgLsXicSfMGSA49LEuNhcLcNloTiaGJwxNEaiaxA/640?wx_fmt=png&from=appmsg&watermark=1&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=1)

> 执行引擎：兼容 MR 和 Tez。Tez 下效率更高(小表广播优化)。LLAP 下小表可常驻内存加速。

### 2.1 原理

专门为一个大表(事实表)Join 一个足够小的小表(维度表) 的场景设计。核心思想是避免 Shuffle。
- 小表广播：先将小表广播复制到所有节点。
- 内存哈希表：将小表的数据完全加载进内存，并构建成一个哈希表(Hash Table)，Key 是Join Key。
- Map阶段：启动处理大表的 Map Task。对于大表的每条输入记录，使用其 Join Key 去内存中的哈希表查找匹配的小表记录。
- 结果生成：一旦找到匹配项，Map Task 会立即将大表记录与小表记录合并，并输出最终结果。整个过程不需要 Reduce 阶段。

### 2.2 优点

- 极高性能：完全避免 Shuffle 和 Reduce 阶段，速度非常快。
- 减少网络和磁盘I/O：只有小表数据需要广播(通常一次)，大表数据在本地处理。

### 2.3 缺点

- 小表必须能完全装入内存：这是硬性要求。如果小表过大，会导致内存溢出或频繁GC，性能反而急剧下降。
- 不支持 FULL OUTER JOIN。

### 2.4 触发条件

- 开启自动转换 `SET hive.auto.convert.join=true;` (默认通常是开启的)。
- 小表大小小于配置阈值 `hive.auto.convert.join.noconditionaltask.size`(或旧版 `hive.mapjoin.smalltable.filesize`)。
- 使用 `/*+ MAPJOIN(b) */` 提示强制指定表 b 作为小表进行 Map Join。

> 默认启用: hive.auto.convert.join=true 默认通常为 true。

### 2.5 关键参数：

- `hive.auto.convert.join`：必须为 true (默认通常开启)。
- `hive.auto.convert.join.noconditionaltask.size`：核心参数！ 指定小表总大小阈值 (默认约 25MB)小于此值的小表无条件转 Map Join。
- `hive.mapjoin.smalltable.filesize`：旧参数，功能类似，但优先级低于 `noconditionaltask.size`。
- `hive.auto.convert.join.use.nonstaged`：小表是否可直接在内存构建哈希表 (避免临时落盘)。

## 3. Bucket Map Join

> 引入版本：Hive 0.10.0 开始支持分桶表优化，Bucket Map Join 概念在后续版本明确和完善。

![](https://mmbiz.qpic.cn/mmbiz_png/iaibeauBlUEfjgc4fDM7N82YnhvjB8XbUQMt8dJKUZoMibvV1CuZEbAJeOE5iaRfXPUPSwpPErqjltSDaCTZXvJcvw/640?wx_fmt=png&from=appmsg&watermark=1&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=2)

### 3.1 原理

Bucket Map Join 是 Map Join 的一种扩展，打破了 Map Join 只适用于大表 Join 小表的限制，可用于大表 Join 大表(或者小表不够小，无法完全装入单个 Mapper 节点的内存)的场景。使用该 Join 策略要求参与 Join 的两个表均为分桶表，都根据 Join Key 进行分桶(CLUSTERED BY)，以及两表的桶数量相同或成倍数关系。
- 分桶对齐：两个表的分桶机制确保了相同 Join Key 的记录必然落在相同编号的桶中(或具有映射关系的桶中)。
- Mapper 处理对应桶：每个 Mapper 只处理两个表中相同桶编号(或具有映射关系的桶)的数据(例如，Mapper 1 只读 Table A 的 Bucket 1 和 Table B 的 Bucket 1)。
- 内存哈希表(桶级别)：Mapper 将小表对应桶的数据加载到内存中构建哈希表。无需再缓存小表的全表数据额，只需要缓存其分桶中的数据即可。
- Join 执行：使用大表(同一桶内)的记录去探测内存中的哈希表完成 Join。结果直接在 Mapper 输出。

### 3.2 优点

- 打破了 Map Join 的局限性，可处理更大的"小表"：因为每个 Mapper 只需要加载小表的一个桶(或多个有映射关系的桶)，而非整个小表。
- 避免全局 Shuffle：只需要在 Mapper 内处理对应桶的数据，无需跨节点传输。
- 高效利用分桶特性。

### 3.3 缺点

- 严格依赖分桶：两个表必须在 Join Key 上预先进行分桶，且桶数量满足条件(相同或成倍数)。
- 桶内数据仍需能装入内存：如果某个桶的数据量很大，该 Mapper 仍可能 OOM。

### 3.4 触发条件

- 开启 `SET hive.optimize.bucketmapjoin=true;`。
- 两表必须分桶 (CLUSTERED BY) Join Key。
- 桶数量：小表桶数 = 大表桶数 * 整数倍 (N)。大表每个桶会被对应的小表 N 个桶 Join。
- 小表的单个桶 (或需加载的 N 个桶) 数据量 < `hive.auto.convert.join.noconditionaltask.size` (即能装入内存)。
- Join Key = 分桶 Key。

> 不是默认启用，需显式开启 hive.optimize.bucketmapjoin。

### 3.5 关键参数

- `hive.optimize.bucketmapjoin`：必须设为 true。
- `hive.enforce.bucketmapjoin`：是否强制检查分桶条件 (有时 CBO 足够智能可省略)。
- `hive.auto.convert.join.noconditionaltask.size`：仍需满足，但评估的是小表的单个桶而非整表小。

## 4. Sort Merge Bucket (SMB) Join

> 引入版本：Hive 0.13.0 正式引入并完善。

![](https://mmbiz.qpic.cn/mmbiz_png/iaibeauBlUEfjgc4fDM7N82YnhvjB8XbUQmVdvYss8f1V4cQ28sIa34ImqfhLICLfVWfQpNDiayVeuJq02aoicvFNA/640?wx_fmt=png&from=appmsg&watermark=1&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=3)

> 执行引擎：兼容 MR 和 Tez。在 Tez 上效率更佳。向量化执行 (Hive 2.0+) 可显著加速 SMB 的归并过程。

### 4.1 原理

在 Bucket Map Join 的基础上更进一步，除了要求参与 Join 的两个表均为分桶表，都根据 Join Key 进行分桶(CLUSTERED BY)，两表的桶数量相同或成倍数关系，新增要求每个桶内的数据在 Join Key 上排序(SORTED BY)。

SMB Map Join 与 Bucket Map Join 一样，都是利用两表分桶之间的关联关系，在分桶之间进行 Join 操作，不同的是分桶之间的实现算法。Bucket Map Join 两个分桶之间的 Join 实现算法是 Hash Join 算法，而 SMB Map Join 两个分桶之间的 Join 实现算法是 Sort Merge Join 算法。
- 分桶对齐：两个表的分桶机制确保了相同 Join Key 的记录必然落在相同编号的桶中(或具有映射关系的桶中)。
- Mapper 处理对应桶：每个 Mapper 只处理两个表中相同桶编号(或具有映射关系的桶)的数据(例如，Mapper 1 只读 Table A 的 Bucket 1 和 Table B 的 Bucket 1)。
- 排序数据流：由于每个桶内数据已按 Join Key 排序，Mapper 可以像合并两个有序链表一样，使用归并排序(Merge Sort)的方式处理两个桶的数据。
- Join 执行：Mapper 使用两个游标(指针)分别指向两个桶的当前记录。根据 Join Key 比较移动游标，匹配时输出结果。整个过程不需要在内存中构建哈希表，只需要维护两个游标和少量缓冲区。

### 4.2 优点

- 解决了桶内数据装入内存可能出现的 OOM：如果某个桶的数据量很大，该 Mapper 仍可能 OOM。
- 内存消耗极低：不需要加载整个桶到内存哈希表，只需要流式读取和比较排序后的数据，适合处理桶内数据量较大的情况。
- 避免全局 Shuffle：只需要在 Mapper 内处理对应桶的数据，无需跨节点传输。
- 高效利用分桶特性。

### 4.3 缺点

- 严格依赖分桶：两个表必须在 Join Key 上预先进行分桶，且桶数量满足条件(相同或成倍数)。
- 要求最严格：两个表必须在 Join Key 上分桶且排序。
  - Join Key = 分桶 Key = 排序 Key

### 4.4 关键参数

- `hive.optimize.bucketmapjoin.sortedmerge` / `hive.auto.convert.sortmerge.join`：必须设为 true (两者功能类似，新版本推荐后者)。
- `hive.enforce.sortmergebucketmapjoin`：强制检查分桶排序条件 (旧参数，CBO 成熟后作用减弱)。
- `hive.input.format`：必须设为 `org.apache.hadoop.hive.ql.io.BucketizedHiveInputFormat` 以确保正确读取分桶数据。

## 5. Skew Join

> 引入版本：Hive 0.6.0 引入基础支持，后续版本 (如 0.10, 1.2, 3.0) 持续优化倾斜检测和处理逻辑。

![](https://mmbiz.qpic.cn/mmbiz_png/iaibeauBlUEfjgc4fDM7N82YnhvjB8XbUQ2lbhJq4ic0fkRhg0NgqQ4hfqCkyHzxZ0WtdCGgCwh51CR3uYhgib4sqw/640?wx_fmt=png&from=appmsg&watermark=1&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=4)

> 执行引擎：主要针对 MR 和 Tez 的 Common Join 优化。LLAP 也可能受益。

### 5.1 原理

专门为解决 Common Join 中数据倾斜(某些Join Key对应的记录数异常多) 问题而设计。
- 采样识别倾斜 Key：Hive(通常在编译阶段或通过配置)会识别出那些出现频率特别高的 Join Key(倾斜Key)。可以通过 `hive.skewjoin.key` 设置倾斜 Key 的阈值(默认100000)以及 `hive.skewjoin.mapjoin.map.tasks` 控制处理倾斜 Key 的 Mapper 数。
- 倾斜 Key 处理：将大表中属于倾斜 Key 的记录单独拆分出来。对于这些拆分出来的记录，使用 Map Join 的策略。即，将小表中对应这些倾斜 Key 的记录广播到所有处理这些大表倾斜记录的 Mapper 上，在 Mapper 内存中进行 Join。
- 非倾斜 Key 处理：大表中不属于倾斜 Key 的记录和小表中不属于倾斜 Key 的记录，仍然走常规的 Common Join (Shuffle-Sort-Reduce) 流程。
- 结果合并：最后将倾斜 Key 的 Join 结果和非倾斜 Key 的 Join 结果合并。

### 5.2 优点

- 有效缓解数据倾斜：防止单个 Reducer 因处理海量倾斜数据而OOM或成为瓶颈。
- 提升整体稳定性：避免作业因倾斜而失败。

### 5.3 缺点

- 增加复杂度：需要额外的采样、拆分、广播步骤。
- 需要额外资源：处理倾斜 Key 的 Map Join 可能消耗更多内存(广播小表倾斜部分数据)。
  - 小表中倾斜 Key 对应的数据子集必须能装入处理该倾斜 Key 的 Map Task 内存。
- 需要识别倾斜 Key：自动识别可能不准确，有时需要人工指定(通过hive.skewjoin.key或统计信息)。
  - 依赖于统计信息 (ANALYZE TABLE ... FOR COLUMNS) 或运行时采样识别倾斜 Key。

### 5.4 关键参数

- `hive.optimize.skewjoin`：必须设为 true。
- `hive.skewjoin.key`：核心参数！定义倾斜 Key 的阈值。Join Key 的记录数超过此值即视为倾斜 (默认 100,000)。
- `hive.skewjoin.mapjoin.map.tasks`：指定处理单个倾斜 Key 的 Map Join 任务数 (控制并行度)。
- `hive.stats.fetch.column.stats` / `hive.stats.fetch.partition.stats`：强烈建议开启 (true)，CBO 利用列/分区统计信息更准确识别倾斜。

> 默认不启用：否。需显式开启 hive.optimize.skewjoin。


## 6. 关键点总结：

- 避免 Shuffle 是王道：Map Join (及其变种 Bucket Map Join) 和 SMB Join 的核心优势在于避免或极大减少代价高昂的 Shuffle 操作。
- 内存与存储的权衡：Map Join 需要内存容纳小表，SMB Join 需要预先分桶排序的存储开销。选择哪种优化取决于资源状况和数据特性。
- 数据倾斜是顽疾：Skew Join 是应对数据分布不均导致 Common Join 性能问题的有效手段。
- CBO是大脑：Hive的基于成本的优化器 (CBO) 会综合考虑表/列的统计信息(大小、行数、NDV、直方图等)、Join类型、配置参数、是否存在分桶排序等信息，为查询自动选择最优的Join算法或组合(如Skew Join)。
- 统计信息是基础：准确、最新的统计信息是CBO做出正确Join算法选择决策的基石。务必定期运行ANALYZE TABLE。
- LLAP的作用： Hive LLAP (Live Long And Process) 守护进程可以常驻内存部分数据(如小表或热数据)，进一步加速Map Join等内存敏感操作的启动速度。
