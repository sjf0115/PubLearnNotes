> 当“秋天的第一杯奶茶”冲上热搜时，很多人看到的是用户的热情与订单的暴涨，而在背后，技术团队同样在全力以赴。自 4 月 30 日淘宝闪购上线以来，短短 100 天，业务团队创造了一个奇迹，技术团队则在高并发与海量数据的冲击下迎来前所未有的挑战。

> 闪购项目期间，亿级营销投入叠加多端流量，实时决策与调控对数据提出了分钟级的要求。为应对挑战，饿了么数据团队依托一年多的湖仓探索与沉淀，选择 StarRocks + Paimon 搭建实时湖仓架构，并通过物化视图优化、RoaringBitmap 去重和大查询治理，突破了传统离线架构的瓶颈，为闪购提供了坚实的数据支撑。

> 本文将根据闪购项目的实战过程，分享过程中沉淀下的经验与思考。


## 1. 背景

在即时零售业务蓬勃发展的背景下，淘宝闪购项目正式启动，标志着外卖行业迎来新一轮激烈竞争。数据驱动决策已成为商业战场的核心竞争力，而传统离线架构的时效性短板正成为业务突破的关键瓶颈。此前，饿了么数据体系以T+1离线处理为主，实时数据因高昂的开发成本和计算资源，仅覆盖了大盘核心指标。闪购项目期间多端多触点流量及亿级营销投入对实时决策和实时调控提出更高要求。海量数据需在分钟级完成采集、清洗、分析与可视化。为了应对这些挑战，饿了么数据团队基于过去一年多在湖仓领域的探索和技术沉淀，通过 StarRocks 与 Paimon 的实时湖仓架构，支撑了海量数据实时分析能力。并进一步通过以下技术手段显著提升了实时分析性能：
- 物化视图优化：StarRocks 的异步物化视图功能被用于预计算高频查询场景，通过将复杂计算结果持久化存储，将原本需要扫描千亿级数据的查询耗时从分钟级压缩至秒级；
- RoaringBitmap 去重：针对超大数据量多维度实时交叉去重指标计算场景，团队引入RoaringBitmap 技术，结合Paimon 的流读流写能力和 StarRocks 丰富的 Bitmap 函数支持，在保障查询性能的同时，业务可以查询实时数据进行任意维度的灵活分析；
- 大查询管理：利用社区提供的工具及 StarRocks 自身的组件实现集群监控报警和诊断分析的可视化管理，并使用 SQL 优化、资源隔离等方式来保障集群的持续稳定性。

该架构升级最终实现三大核心价值：存储成本大幅降低，实时分析链路端到端延迟显著下降，并支撑海量日志数据的高并发查询场景，为业务决策提供了可靠的实时数据支撑。

## 2. StarRocks&Paimon 技术原理简介

Paimon 作为流批一体的实时数据湖存储框架，支持 OSS、S3、HDFS 等多种对象存储格式，深度融入Flink、Spark生态及多款 OLAP 查询引擎，专注于解决大规模数据场景下的低延迟写入、高效更新和实时分析难题。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibpVc4lpG0ib1qMibrJyHOq2bmbLoicTDdK91YIqxxGrxkBXhJQD2b01jhvw/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=1)

StarRocks 作为一款极速统一的 MPP 数据库，利用其 Catalog 功能，可以接入多种外部数据源，如 Paimon、Hive、MaxCompute、Hudi、Iceberg 及其他可通过 JDBC 协议连接的各种数据库等。StarRocks 内部通过维护这些外部数据源的元数据信息，直接访问外表数据，我们无需在不同介质间进行数据的导入导出。此外，阿里云EMR 团队针对 Lakehouse 场景做了进一步的优化，在开启 Paimon 表的 deletion-vectors 属性后，StarRocks 查询 Paimon湖表的性能有了十倍以上的提升。因此，我们业务上可以不经过 ETL 操作，直接使用 StarRocks+Paimon 的方案迅速搭建数据看板。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibpf4icd4jPYJccbszPNMUpiav6icP8qDeQ0VbJDAzpoeSerhYSD4NjyfECg/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=2)

两者结合可以实现 1+1 远大于 2 的效果。淘宝闪购项目作战期间，BI 与业务运营想要查看当日流量漏斗及各渠道投放转化效率，以便及时进行分析汇报和调整运营策略。我们将实时流量数据通过 Flink 入湖，维表数据通过 Spark 入湖，StarRocks 作为计算引擎直接查询Paimon湖表，FBI接入SQL数据集搭建实时看板，快速解决了业务实时看数需求。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibpcjhUmaRvv7IzuToLNyDCeIqdGbtZFMQ3A3e0rP3RcpwaMlV2z9oMicw/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=3)

## 3. 物化视图：StarRocks 助力 Paimon 解锁查询新体验

在闪购项目初期，StarRocks 与 Paimon 的组合确实满足了基础数据服务需求，但随着业务规模的指数级增长，实时分析性能瓶颈逐渐显现。当单日流量峰值突破阈值后，复杂查询响应时间从秒级恶化至分钟级，核心业务看板的刷新延迟大幅增加，直接影响了运营决策效率。为解决这一挑战，我们基于 StarRocks 的物化视图技术构建了优化体系：

- 物化视图分层加速架构
  - 预计算层：针对高频访问的复杂查询（如多表关联、窗口聚合），通过 StarRocks 物化视图预计算结果集，查询响应时间降低 80% 以上；
  - 更新机制：我们维护了 120+ 个物化视图，平均 15min 刷新间隔，最高支撑了单分区千亿级别的数据物化加速；
  - 资源隔离策略：通过 FE 节点（25个）与 CN 节点（120个，总9280 CU）的混合部署，将物化视图刷新任务与实时查询流量隔离，支撑单日业务有效查询数量峰值为 17万/天（含1万+物化刷新任务），项目后期 CN 节点扩至 300 个，集群规模达到 20800 CU。
- 实时看板建设实践，基于优化后的架构，我们搭建了覆盖全链路的实时分析体系：
  - 流量全景看板：聚合用户行为、渠道来源、访购转化等多维度数据，支持分钟级漏斗分析与流量渠道 ROI 计算；
  - 动态资源看板：通过 StarRocks 内置的资源监控接口，实现集群负载动态可视化，物化视图刷新成功率稳定在99.9% 以上；
  - 异常诊断看板：集成 EMR Serverless StarRocks 的智能诊断平台，快速定位慢查询，问题定位效率提升 60%。

下面我们展开介绍一下在落地 StarRocks 物化视图过程中的一些实践经验。

### 3.1 StarRocks&Paimon 物化视图原理

StarRocks 的物化视图主要分为同步物化视图和异步物化视图两大类：

- 同步物化视图：只支持单表，在导入过程中同步刷新。基表只能是内表，不支持 Paimon 表。
- 异步物化视图：支持多表，同时支持异步刷新/手动刷新。基表支持 Paimon 表。
  - 非分区物化视图：执行完整查询，全量覆盖视图数据，可以用于热点数据加速
  - 分区物化视图：根据参数及基表数据变更情况，以分区粒度刷新视图，可以用于长周期存储数据。其中物化视图分区支持下面两类
    - Range 分区：通常以 date 类型作为分区字段，可使用 date_trunc 函数实现分区上卷；
    - List 分区：3.3.5 版本支持，分区字段为可枚举的 string 类型或不连续的 int 类型。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibp0Iw0wj3lnnZPFdz9jfvnibmzuBUc9BubrtjJDUvQqODibrsP4ibM6icLsg/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=4)

同步物化视图作为基表的附属结构，与基表数据实时同步，但使用场景较为局限，比较典型的场景是使用 Bitmap 或HLL 在内表中进行去重计算，我们所使用的物化视图通常为异步物化视图。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibphxBehPhKLPlibEuLOh4t7AMsDCWKRUzlagXcgNu0Ceyia4K1XDpqMOEw/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=5)

异步物化视图的调度框架主要有两个核心概念：Task 是周期运行的刷新任务，TaskRun 为每次刷新周期的运行实例。我们可以通过系统参数来设置 TaskRun 的最大 Pending 数量，Running 的并发数量及生命周期等。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibpFz5rj8vlHcpvUdtRA0R1HDuSvEgwQHDpYg33eX9BVIc0lXMIQnJsRw/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=6)

对于带分区的物化视图，主要通过与上游基表的分区依赖和数据变化来刷新对应视图分区，可以通过参数控制刷新行为，对比物化视图与基表对应分区的可见版本，来判定需要刷新的分区，以防止过多分区刷新导致的资源浪费。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibpWicJiav4eBmVmZ3aPZ7PFG1o79atPVk86Q3hb9cvdFI8NjlHF0ickzzVw/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=7)

每次刷新都是通过生成一个 insert overwrite 任务，先创建临时分区并写数据，然后将临时分区与目标分区进行原子替换。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibpv5JeSzgDbzcVSAy8yy2BQUP80eEOkNmZq02NsX5c2aJxfdlK36jWZA/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=8)

### 3.2 StarRocks&Paimon 物化视图在淘宝闪购的应用

#### 3.2.1 优化1：基础 Paimon 物化视图

随着闪购流量连续几天的飞速增长，直查湖表的实时看板性能越来越差，项目初期使用加资源的方式解决，但看板人数也在逐步增加，对集群的稳定性也造成了一定影响，因此，我们在 StarRocks 与 Paimon 之间，针对看板数据集的查询 SQL 进行了物化处理，每十分钟进行一次刷新，加速查询的同时缓解集群大查询带来的压力。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibpX6reafAO0tyiaibm4uAQwSibcfBQIb84qwjXI2tYLtQCqCbL2aptuia89A/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=9)

#### 3.2.2 优化2：针对长周期历史数据的查询优化

项目上线一段时间后，业务需要查看日环比、周同比指标，提出了长周期数据存储诉求，于是在原有方案基础上，加了一条 DataWorks 凌晨离线 insert 调度任务将前一天数据写到 StarRocks 内表，然后将当日实时数据与历史离线数据 UNION 为一个虚拟视图。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibpvpbxRgWbSo8UR4PgXhd8PtAUmP0vrDe2N6SsAvbJDRkEbfNSpVZb1Q/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=10)

#### 3.2.3 优化3：引入带分区的物化视图

在我们使用的阿里云 EMR StarRocks 3.3 版本中，支持了基于 Paimon 湖表的分区物化视图以及多基表分区对齐特性，我们将优化1 中的物化视图直接改为分区物化视图以支持历史数据存储。对比优化2，使用分区物化视图可以极大简化运维，使用分区物化时，只需要使用 PARTITION BY 指定分区字段（需要与基表分区对应）。但这里需要注意，湖表生命周期缩短时，物化视图在下次触发刷新也会删除对应分区，所以当视图需要存储的数据周期大于基表时，仍需要使用优化2中方式实现。

分区物化视图定义中不需要限制分区字段取值范围，我们在创建分区物化视图时通过设置 PROPERTIES 来控制刷新行为，存储近 30 天分区（"partition_ttl_number" = "30"），并根据事实表数据变动每次至多触发两个分区刷新（"auto_refresh_partitions_limit" = "2"），每个调度实例只刷新一个分区（"partition_refresh_number" = "1"），同时配置 excluded_trigger_tables 参数来忽略维度表变动触发的刷新行为。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibpbVttwmYEHfKWrAQBQ6x8IDgGWQBMpbswiaWFCHNGz57YucBROdv4fhA/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=11)

### 3.3 StarRocks&Paimon 物化视图实践总结

StarRocks 物化视图开发成本低，迭代方便快捷。非常适合在战时以极高的效率交付业务看数需求，并快速应对作战期间的业务调整和口径频繁变更的情况。在数据湖加速、查询改写、项目初期的数据分层建模等场景中非常适用。我们需按照不同的业务场景创建合适类型的物化视图，并通过参数控制分区刷新行为，从成本和集群稳定性角度考虑，在满足业务需求的前提下，应遵循数据刷新最少化、调度频率最低化的原则来设置物化视图刷新参数。此外，我们还需要定期对物化视图进行治理，并添加监控报警以保障集群的持续稳定性。最后，数据开发同学在使用物化视图时，需规避一些系统性风险，如：
- 当基表分区字段为字符串类型的日期时，物化视图会创建List分区，且在刷新时触发全表刷新，可以使用 str2date 函数转为日期类型，创建 Range 分区物化视图；
- 视图始终依赖于基表，物化视图刷新前会进行分区检查，基表中不存在的分区也会在物化视图中删除，即便视图属性中设置了更长时间的 partition_ttl 也无法阻止这一操作；
- 在物化视图的定义 SQL 中尽量使用 StarRocks 已支持的内置函数，一些 UDF 在物化视图刷新时可能无法兼容。


## 4. RoaringBitmap：StarRocks&Paimon 实时去重的极速神器

通过物化视图的优化实践，我们发现长远来看对于复杂的实时业务场景，物化视图更应作为 ADS 层的数据加速，而 DWD 到 ADS 层的 ETL 过程应尽可能在 Paimon 中完成。即让数据在湖里流动，StarRocks 物化视图做链路终端的查询加速。比如可以利用 Paimon 的 Partial Update 解决双流 JOIN 的场景，Aggregation 特性处理聚合场景等。

在 C 端业务中，去重指标的实时计算往往是技术痛点，于是，我们团队调研了在湖上利用 RoaringBitmap 解决大数据量级精确去重，流量域中多维数据的快速分析，基于 Bitmap 的不同人群下钻、访购率计算，流量域中长周期指标的实现等场景。通过 StarRocks 的 Bitmap 相关函数直接查询存储在 Paimon 中的 RoaringBitmap 数据，大幅提升了实时 UV、多数据域分析的数据新鲜度和查询性能。

### 4.1 RoaringBitmap 去重原理浅析

我们以6行数据在两个节点上计算来举例，在传统的 Count Distinct 去重方案中，由于数据需要进行多次 shuffle，当数据量越来越大时，所需的计算资源就会越来越多，查询也会越来越慢。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibpI7iab0dH6QEklTAIMzTusa8hBPVEHGarYygyHhKDM7uEwz1f5Liac9nw/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=12)

Bitmap 去重方案中，每个维度仅需存放一个 UID 位图即可，去重即是对多个 Bitmap 进行位运算（OR），然后直接统计位图中1的个数即为 UV 计算结果。大数据场景下，Bitmap 的存储方式相比与 UID 去重后的明细数据显然节省了大量存储空间。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibpIFn2TlJZFZH0oc0eY54Nj19q3lyzwchcnahvksoJKTXuN3QzFySC3A/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=13)

但当某个维度为稀疏分布时，此时长度为 n 的位图仅有少部分是有效位，存在大量的无效 0 占用空间，所以，需要一种更灵活的存储方式来解决这个问题。RoaringBitmap 是一种高效压缩位图结构，专为快速存储和操作大规模整数集合设计。它通过智能分桶和动态容器选择，在空间压缩和计算性能之间实现最佳平衡，在当下主流的大数据计算和存储引擎中，RoaringBitmap 也被越来越广泛的应用。以32位 RoaringBitmap 为例，内部会将高16位进行分桶，低16位根据桶内数据分布特征选择Array Container（数组容器）、Bitmap Container（位图容器）、Run Container（游程编码容器）三者中空间利用率最高的容器存储。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibp4hk6o3YJv1SByS7mnHyN46m2ejlqxUM5ZHgfIO8ud4BE8fL3yu60UQ/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=14)

如上图，十进制数 131397 转为十六进制为 0x00020145，其中 0x0002 为高位分桶，该分桶内元素小于 4096，低位 0x0145（16*16*1+16*4+5=325）采用 Array Container 存储，二分法找到对应数组位置。当元素个数达到 4096时，数组容器占用的空间为 2*4096=8192 字节，此时与位图容器所占空间一致。即当一个分桶内的元素个数超过 4096 时，会选择位图容器存储，并根据数据的连续程度来判断是否优化为行程编码以进一步压缩存储空间。

![](https://mmbiz.qpic.cn/mmbiz_png/T17ibLEhxXySW1KYjKMFdQyr8L1FpkeLibYskXIblBUPniavpAa6wHAwhd5DvfSY8XJp6ps7vqxz9h8THbPwDJj6Q/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=15)

### 4.2 RoaringBitmap 去重适用场景

以下均针对去重指标计算场景，可直接 sum 或 count 的指标不在讨论范围内。

#### 4.2.1 多维预计算（CUBE）
在预计算场景中，每个维度的增加往往带来计算与存储资源的指数级增长，n 个维度理论上有 n 的2次方个维度组合，假设业务有七个维度，就会有上百个 grouping sets。即便中间做一层轻聚合优化，也动辄运行数小时，不仅浪费了资源，且数据产出时效差，甚至影响业务看数。

使用 RoaringBitmap，将中间层的轻度去重数据由 UID 改为聚合后的 Bitmap，原方式下，每组最细维度下有多少UID，就需要存储多少行数据，新的存储结构每组维度只需要存储一行 Bitmap 即可，极大节省了存储空间。同时下游使用位运算计算 UV 指标，计算效率也提升数倍。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibpN0Lic0qPqFh0iaicn3TgXaiaO5HcZkdtxb74UoxBm8cdrPGXXJCxXc533w/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=16)

但以上多维度预计算更适用于离线场景，实时资源的成本过于昂贵，且在大多数实时场景下，业务并不需要看全部一百多组 grouping sets 的维度数据，而更关心数据的时效性。此时我们可以仅保留需要的维度直接查询 Bitmap 数据，或将多组维度拆开，利用交、并、差集计算来满足任意维度组合的看数需求，以下介绍几种利用 RoaringBitmap 进行实时多维分析的应用场景。

#### 4.2.2 时间上卷（UNION）

位图 UNION 的本质是 OR 运算，使用 bitmap_union 和 bitmap_union_count 可以实现时间上卷或细粒度向粗粒度的聚合和去重统计，在数据湖中，可以利用 Paimon 流读流写特性和 Aggregation merge-engine 简单快速地实现bitmap 的聚合计算，当前 Paimon 的 Aggregation 已支持 rbm32 和 rbm64 函数。也可以自己开发. Flink-UDAF，在Flink-SQL 中完成聚合操作，使用 Deduplicate merge-engine 入湖。

> bitmap_or 是对两个 Bitmap 做并集，bitmap_union 是聚合函数，对同一列的多个 Bitmap 做并集计算。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibpAHU0yuH80WsOH6PmJF7HlWhxMmutukn1Igq9rNtMw4cRod8rWY6v3g/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=17)

#### 4.2.3 人群下钻（AND）

Bitmap 的交集计算适用于电商业务中常见的留存、复购、多维交叉分析等场景，即粗粒度模型存储实现更细粒度的实时分析。也可以利用交集来进行人群下钻。与其他维度不同，用户人群维度通常不是一成不变的，且开发人员无法按照既定规则去预判这种变化，业务会按需圈选各种各样的人群包。为应对不同人群的灵活下钻分析需求，在设计数据模型时我们可以把人群维度单独处理。如我们在流链路里做了一张分钟流量的 Bitmap 表，批链路加工一张人群维度的 Bitmap表，使用 bitmap_and 函数计算交集后即可得到每个人群对应的小时切片 UV。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibpVDEyjNehEaF80mxo4iaNUibuTxabLYHy9SUOia3PAQqjHNZgnT4zRWbbA/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=18)

#### 4.2.4 跳失、拉新（AND NOT）

差集计算适用于指标语义中含有“非”、“但”的逻辑，如计算前一日访问但当日未访问的用户，则可以将前一天的访客Bitmap 与当日访客 Bitmap 进行差集计算，从而找到当日跳失用户，如下：

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibpkL90LRX2Y1ib1UFxNKZD6VJArqGiajHgqSVxWJcw4JVoXTb9TNPPgmpA/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=19)

#### 4.2.5 漏斗分析（CASE WHEN）

首页-->进店-->提单-->下单是业务常用的转化率分析链路，但每个页面流量单独统计出的结果并不准确。以首页-->进店为例，部分外投渠道链接可能直接跳到店详页而不经过首页。业务想要看到精确的漏斗数据，只能使用 UID 进行串联。假设我们有一张页面维度的 Bitmap 表，则可以通过 case when+bitmap 交集计算来进行访购链路的漏斗分析。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibpAjTuB9R519foFprTfnJLu5IT6rlQticpTahCNE2dzI1uzhut86vgRyQ/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=20)

### 4.3 RoaringBitmap 在淘宝闪购的应用

#### 4.3.1 场景1：流量域多维实时 UV
闪购项目中后期，业务提出了更多维度的实时看数需求，包含各端的闪购/非闪购及多个维度的数据。原有的物化视图直接加速湖表 DWD 的方案很难满足业务上多维灵活看数，且多个大视图抢占资源导致物化视图数据刷新的时效性越来越差。所以我们尝试使用 RoaringBitmap 和 Paimon 的流读流写特性来计算流量域数据的多维实时 UV，具体方案如下：
- 使用自增序列将 UID 实时映射为 int 类型；
- 开发 Flink-UDAF 函数，支持 bitmap_agg 和 bitmap_union 操作，并序列化为 bytes 类型返回；
- 接入 ODPS 城市/区县维表（全量缓存），Lindorm 用户分层维表（LRU 策略）；
- TT 数据入湖，Flink-SQL 流式读取 Paimon 明细层数据，并与 UID 映射表和其他维表 lookup join；
- 调用 bitmap_agg 函数将映射后的 UID 转为 Bitmap 存储，sink 到下游湖表；
- 按照业务场景，使用 StarRocks 的 bitmap_union_count 函数对所需维度实时去重统计；
- 如业务需要查看多天趋势，可以继续向下 bitmap_union 为小时或天粒度的 Bitmap。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibp6RILadJicLt0CQ5Jc2wqma1rRPns0u2Ofdj9MQWbmiaEqicvcElwTx7Ag/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=21)

此时我们可以任意组合看数的维度有：端+闪购类型+直营城代+用户L分层+用户V分层。

时间粒度：分钟切片/累计、小时切片/累计/当日累计趋势、全天数据、多天连续数据等。

#### 4.3.2 场景2：多数据域 Bitmap 应用

项目后期，在业务侧，用户L分层的口径频繁变更，业务也会圈选新的人群包进行下钻分析；技术侧看，Lindorm 在回刷数据时会产生较大波动，我决定将人群维度拆分出来单独处理。此外，我们也有了新的业务思考，如何构建流量域全维度覆盖的实时 Bitmap 数据资产，以及能否将订单域数据也加进来计算实时访购率。于是，我们在原有方案上进行了另一种数据建模方法的尝试：
- 中间做一层最细粒度的 DWS 轻度聚合层，下游再加工出常用维度+单维度的 Bitmap；
- 仅保留 UID 映射表，其余 lookup join 表全部删除，改为应用层使用时 join；
- 用户维表使用批链路处理，构造人群维度 Bitmap 湖表，计算交集进行人群下钻；
- UDAF 中添加回撤流处理，将订单域湖表数据也做成 Bitmap。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibppQypLxvmseSTFLBAwoqflG6XToKmcsOSNBXjHbHCmCJRn1RTgghrwg/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=22)

流量域 ADS 层 Bitmap 表设计：

> 端和闪购类型维度在业务上经常需要拆开看数，且这两个维度基数较少，所以每个表都保留。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibpL7bt2RIMIqtD1h4tPVQ3Z8g4muIvZkZ3ab8SmW9icIicfcUYOy007jhA/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=23)

订单域设计思路类似，当我们将各个业务域都按照各自维度存储为 Bitmap 结构后，就可以高效地计算出任意维度的实时 UV、访购率、人群下钻数据等。

### 4.4 RoaringBitmap 实践总结

借助 StarRocks 丰富的 Bitmap 函数和 Paimon 的流读流写能力，我们利用 RoaringBitmap 实现了实时场景的高效去重计算。根据其构造方式我们不难看出，只有数值类型的 UID 才能被转为 Bitmap 存储，且数据越稠密越连续性能越好，但实际业务中，我们的 UID 通常为稀疏的 bigint 或 string 类型，因此需要将 UID 重建序为 32 位的 int 类型，尽管部分引擎支持了 64 位 RoaringBitmap，但其性能显著低于 rbm32，建议仍优先使用32位。

在实时流中，需要使用支持自增序列写入和高并发点查的存储介质做维表 LOOKUP JOIN 以实现对新用户的实时映射。我们在午高峰百万级 RPS 场景下，实时点查映射表会出现反压，通过 LRU 缓存并开启 Flink-MiniBatch，并对湖表增量 Snapshot 数据预去重再关联，能够有效降低实时查询压力。同时将历史用户预映射入库，可以避免维表高频写入瓶颈。

在 Flink-SQL 中因原生不支持 Bitmap 操作，需通过 UDAF 函数实现 int 与 Bitmap 的互转、聚合及序列化为 BYTES 类型存储，注意准确处理回撤流的逻辑修正。面对超大规模用户基数的存储限制，采用分桶计算策略：对 UID 哈希分桶后独立聚合，确保单桶 Bitmap 长度可控，最终通过累加分桶结果实现全局统计。此外，粒度的选择尤为重要。虽然细粒度可以通过 UNION 并集计算向下游加工粗粒度数据，粗粒度数据也可以通过交集计算进行维度交叉，但仍建议结合业务查询模式进行数据模型设计，以达到灵活性与性能的黄金平衡点。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibp6qYO35RPe1kzZloCqCUXTOSHiaT90TlwweIua8NNhQxslOxLzcmRT6Q/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=24)

## 5. StarRocks on Paimon 治理最佳实践

StarRocks 作为经典的 MPP 架构，大查询易引起资源过载，所以对大查询的管理必不可少。以下是我们团队针对 StarRocks 集群运维与治理方面的一些经验，重点介绍针对大查询的诊断分析与治理。即通过监控报警感知到集群的异常波动，再使用 AuditLoader 插件采集的审计日志找出影响集群稳定性的大查询或物化视图刷新任务，然后采取下线、优化、或资源隔离的方式进行治理。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibpob5jjm1ZDg8Kq8t1VpnO8gv1HQmdXJ9BJUvC9wgfFUKpibXdcfEEwDg/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=25)

### 5.1 监控报警

我们目前使用的是阿里集团内部的 Sunfire 平台进行 StarRocks 实例的监控看板搭建和报警配置，主要针对 FE 和BE/CN 节点的 CPU、内存使用率和查询延迟等指标进行重点监控。社区的小伙伴可以使用 Grafana 实现一样的效果，StarRocks 官网文档中也提供了非常完整且详细的 Prometheus+Grafana 的可视化监控报警方案和适配于各个版本的 Dashboard 模板。并且在 3.1 以上版本，还支持了异步物化视图的专项监控指标配置，可以实时观测到当前集群刷新成功和失败的物化视图数量，刷新状态、物化视图的大小、行数、分区信息等。

### 5.2 查询分析

StarRocks 所有的 DML、DQL 等语句都会在 fe/log/fe.audit.log 中记录一条日志，包含语句内容、来源 IP、用户、所耗 CPU 及内存资源、返回时间、返回行数等。我们可以使用官方提供的免费插件 AuditLoader 将审计日志通过 Stream Load 的方式写入库表，这样我们可以通过 SQL 非常方便地查看数据库日志信息。

我们借助 AuditLoader 生成的审计表和集团的FBI平台搭建了查询日志明细报表和物化视图、SQL 指纹、用户等多个维度的资源占用看板。此外，我们还可以通过系统数据库 information_schema下的 materialized_views、tasks、task_runs 三张表来制作物化视图的专项看板，更加直观地查看各个物化视图的元数据信息及刷新任务状态。通过这些实时看板，方便我们定期清除潜在隐患，也能够在触发报警时快速定位到引起集群状态波动的大查询或写入任务。

### 5.3 资源隔离

随着物化视图的不断增多，一些较大的物化视图任务刷新时，同实例下的其他查询会受到一定影响。治理的手段往往是有滞后性的，我们尝试在运维层面降低系统性风险，通过资源隔离的方式来提升稳定性。在一个 StarRocks 实例内部，可以通过配置资源组或计算组来实现这个需求。

StarRocks 通过资源组（Resource Group）实现多租户资源隔离，允许按用户、角色或查询类型动态分配 CPU、内存及并发资源。通过设定资源配额和优先级规则，确保关键任务独享资源，避免资源竞争，保障高负载下查询性能和稳定性，支持灵活配置与实时弹性调整。StarRocks 内置了两个资源组 default_wg 和 default_mv_wg，分别对应普通查询任务和物化视图刷新任务，用户也可以根据业务场景自定义资源组配额，使用也非常简单，只需要创建资源组和分类器即可。

但需要注意的是，通过 Resource Group 实现的资源隔离通常为软隔离，即假设有三个资源组 rg1、rg2、rg3，资源配额为 1:2:3，当 BE/CN 节点满载时，集群资源会按照配额分配；当 rg1、rg2 有负载而 rg3 无负载时，rg1 和 rg2 会按照 1:2 比例分配掉全部资源。

业务实践过程中，通过资源组来实现业务间的资源隔离尤其是 CPU 资源有时并不能达到理想的效果，由于其软隔离的特性，我们始终无法在同一个实例中完全隔离出一部分 CPU 给到 P0 级业务。于是，我们继续尝试了阿里云 EMR StarRocks 存算分离版本计算组（Mutil Warehouse）隔离能力，将物化视图刷新任务与 SQL 查询任务进行隔离。即在同一个实例中共享一份数据存储，共享 FE 节点的查询规划和资源调度，将 CN 节点进行物理隔离，满足读写分离场景和不同业务负载需求，同时支持根据实际业务需求动态调整资源，确保资源高效利用并降低成本。

![](https://mmbiz.qpic.cn/mmbiz_png/Sq4ia0xXeMC766FYib43xT6WZ4eiboOLlibpNw9vXGodImDT834qgFYEEXeUGkcARfIlzMCdAMRTEibaE3zfm0hbic6w/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1#imgIndex=26)

### 5.4 SQL 及物化视图治理

当我们定位到大查询后，使用 EXPLAIN 或 EXPLAIN ANALYZE 来获取查询计划，也可以启用并查看 Query Profile 以收集更详细的执行指标，企业版用户还可以使用 StarRocks 官方提供的可视化工具进行诊断分析。常见的优化手段包括：
- 如果关联字段也是过滤条件，将过滤条件写在大表上，以便谓词正确下推至存储层；
- 大表与小表关联时，可以添加 JOIN HINT，使用 BROADCAST 方式关联减少节点间数据 shuffle；
- 聚合场景添加查询 HINT 选择合适的聚合算法，如低基数维度去重统计添加 set new_planner_agg_stage=4；
- 当多表关联时优化器未选择最优的连接顺序，可以尝试添加 JOIN HINT 或将连接条件书写完整，如 a、b、c 三表关联，ab、bc、ac 三个连接条件都写出来。

针对物化视图的治理，我们应及时将下线视图的状态改为 Inactive，降低低优业务的刷新频率，并将物化视图的刷新任务与 SQL 查询进行资源隔离。物化视图的错用滥用，以及过高的刷新频率，都会导致全部视图的 Pending 时间过长，从而影响数据产出时效，甚至会影响集群整体查询性能和稳定性。我们不仅要在事后治理，更重要的是在创建视图时规避以下错误或不恰当的用法：
- 日期写死，等于固定日期（无效视图），大于等于固定日期（高危视图）；
- 非分区物化视图未添加分区限制条件，即每次刷新全表数据；
- 分区物化视图未设置参数控制刷新行为，存在全表刷新风险，如维表数据变动；
- 多个测试版本视图未及时删除，下游无业务，空跑浪费集群资源；
- 视图定义中存在多组维度的 CUBE 且刷新频率极高。


## 6. 总结与规划

淘宝闪购自 4 月 30 号上线到 8 月 7 号的“秋天第一杯奶茶”，业务团队用 100 天创造了一个奇迹。我们技术团队也顶住了前所未有的压力，在湖仓技术的探索上不断进行突破与革新。目前 StarRocks+Paimon 的方案已经在饿了么内部全面开花，越来越多的数据开发愿意参与到我们的湖仓建设中。在未来的一段时间内:
- 我们会逐步治理物化视图中的大查询，保障 StarRocks 集群的稳定性与物化视图刷新的时效性；
- 并继续与爱橙和阿里云 EMR 团队密切合作，优化 StarRocks 查询 Paimon 性能向内表追齐；
- 我们也会尝试探索落地更多湖仓业务场景，并在数据湖上持续建设流批一体架构，彻底解决实时和离线链路重复开发和数据口径不一致的问题。

最后，项目结束不是终点，而是技术新的起点，我们的补贴仍在进行中，欢迎大家打开淘宝闪购，给我们数据团队“再上亿点压力”。e 起勇往直前，用数据驱动未来！
