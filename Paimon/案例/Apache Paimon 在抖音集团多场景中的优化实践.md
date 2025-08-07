目前抖音集团内部主要使用 Lambda 架构进行实时数仓建设，其中实时处理链路主要采用 Flink + MQ 进行实现。在 Lambda 架构体系下，主要优势是数据新鲜度高，但采用两条处理链路也带来了其它问题：
- 维护成本高：需要维护实时、离线两条不同技术栈的处理链路，开发和维护成本高；
- 计算口径难对齐：没有统一的 Table 抽象，Schema 难对齐；两条链路同时跑，计算语义难对齐；
- OLAP 查询能力差：消息队列只支持 APPEND 流，从流式数据转化为 Table 的成本开销高，需要不断处理 changelog，导致 OLAP 查询能力差；
- 问题排查困难：如果数据有问题，用户需要排查数据 Pipeline，但由于中间结果不可查，导致排查难度高；
- 数据订正困难：实时链路数据订正需要大量的人工介入，修改逻辑、双跑等，数据订正困难。

随着流式计算引擎的不断完善，以 Flink 为代表的流式计算引擎提出了新的目标：为有限数据和无限数据提供一套统一的处理 API。流批一体的计算模式进一步简化了数仓生产体系，将计算链路收敛到了相同的技术栈，降低了开发和维护成本。同时随着数据湖技术的兴起，它能够支持高效的数据流 / 批读写、数据回溯以及数据更新，进一步解决了 Lambda 架构体系下的其它问题。

Apache Paimon 是一项流式数据湖存储技术，基于 Flink Table Store 独立孵化出来的项目，主要目标是解决流式场景中的常见问题，为用户提供高吞吐、低延迟的数据摄入、流式订阅和实时查询，支持主流的计算 / OLAP 引擎，尤其对 Flink 的支持最佳。因此在经过调研后，最终决定采用 Apache Paimon 作为数据湖底座，和业务进行新一代实时数仓建设。本文将基于抖音集团两个业务的典型实时数仓场景，介绍 Apache Paimon 在抖音集团内部的生产实践。

## 1. 场景一：游戏视频指标上卷

### 1.1 业务场景

游戏-新游场景在公测宣发、测试上线首日、首发等相关节点，产品和运营需要根据游戏短视频的点赞、曝光、评论等实时指标在第一时间挖掘优质作者和发现潜力热点。游戏实时数仓团队当前通过接入短视频实时数仓团队的分钟粒度流并关联游戏相关维表，通过分钟粒度上卷到天粒度指标的方案来提供相关指标。

### 1.2 原有方案

![](https://mmbiz.qpic.cn/mmbiz_png/jC2t9Zib67r3h3dicwkD7zia8m5YYkjSYOD0icCQgMNG4xxxFDYABcVVSXbdVC68Rry7bnULFjicuQke3xQsBycETibQ/640?wx_fmt=png&from=appmsg&randomid=ooq4mzib&tp=webp&wxfrom=5&wx_lazy=1)

### 1.3 方案痛点

1. 由于短视频 topic 流量在 100w+/s 左右，即使 Lookup Join HitRate 平均在 90% 左右，但是全链路峰值仍有60w+/s 的流量打到维表存储，给维表服务带来比较大的访问压力。

![](https://mmbiz.qpic.cn/mmbiz_png/jC2t9Zib67r3h3dicwkD7zia8m5YYkjSYODQb4GicEIfR5WJ8Bu93EWwdcvaUm8bcnhPepoE3drc7bAZlxCVj5PYicw/640?wx_fmt=png&from=appmsg&randomid=w0c5cql2&tp=webp&wxfrom=5&wx_lazy=1)

> Lookup Join HitRate

![](https://mmbiz.qpic.cn/mmbiz_png/jC2t9Zib67r3h3dicwkD7zia8m5YYkjSYOD4R4jiahDvJHtCzVvJWHTm1RUXcJxU6w1qB3Pd2ajyDTyGChDZREZ4KA/640?wx_fmt=png&from=appmsg&randomid=6a5o2117&tp=webp&wxfrom=5&wx_lazy=1)

> Lookup Join Request Per Second

2. 由于上卷任务的 source 是 append 流，分钟粒度的指标会实时的变化，所以需要消费 source 后通过 MAX / LAST_VALUE 等聚合函数去构建 retract 流、处理乱序等问题，开发效率低且增加额外的状态成本。

```sql
CREATE  VIEW view_01 AS
SELECT  
    id, f1, f2,
    MAX(f3) AS f3,
    f4, f5,
    MAX(f6) AS f6,
    MAX(f7) AS f7,
    LAST_VALUE(f8, f5) AS f8
FROM source_table
GROUP BY id, f1, f2, f4, f5;

INSERT INTO sink_table
SELECT  
    id, f1,
    SUM(f3) AS f3,
    CAST(f2 AS BIGINT) AS f2,
    MAX(f4) AS f4,
    MAX(f5) AS f5,
    MAX(f6) AS f6,
    MAX(f7) AS f7,
    LAST_VALUE(f8, f5) AS f8
FROM view_01
GROUP BY id, f1, f2;
```

### 1.4 Paimon实践

使用 Paimon 作为游戏维表，在 Flink 中 Lookup Join 将打宽结果写入 Paimon 表中，Paimon 表基于 lookup changelog producer 产生完整的 changelog，下游消费 changelog 做上卷计算。在存储层基于 Paimon 的 Sequence Field 能力处理乱序。

![](https://mmbiz.qpic.cn/mmbiz_png/jC2t9Zib67r3h3dicwkD7zia8m5YYkjSYOD1n3WprhcdpCU9hVat8zMC1qqj7AxAsfMJgpCRl7VR405ZTXV9yLbwQ/640?wx_fmt=png&from=appmsg&randomid=rwtssj5o&tp=webp&wxfrom=5&wx_lazy=1)

1. 维表打宽
```sql
--维表模型DDL
create table dim_table01 (
    `id` BIGINT,
    `f1` STRING,
    `f2` BIGINT
    PRIMART KEY (f1) NOT ENFORCED
) WITH (
    'changelog-producer'='lookup',
    'changelog-producer.row-deduplicate'='true',
    'sequence.field'='f2',
    ...
)

create table dim_table02 (
    `id` BIGINT,
    `f1` STRING,
    `f2` BIGINT
     PRIMART KEY (f1) NOT ENFORCED
) WITH(
    'changelog-producer'='lookup',
    'changelog-producer.row-deduplicate'='true',
    'sequence.field'='f2',
    ...
)

--分钟指标流关联维度
SELECT
    AA.id,
    BB.f1 as bb_f1,
    CC.f1 as cc_f1
FROM source_table AA
LEFT JOIN paimon.db_name.dim_table01 /*+ OPTIONS('lookup.async'='true', 'lookup.async-thread-number'='8') */
FOR SYSTEM_TIME AS OF proctime AS BB
ON AA.id = BB.id
LEFT JOIN paimon.db_name.dim_table02 /*+ OPTIONS('lookup.async'='true', 'lookup.async-thread-number'='8') */
FOR SYSTEM_TIME AS OF proctime AS CC
ON AA.id = CC.id;
```

2. 指标上卷
```sql
--分钟指标模型DDL
create table `db_name`.`table_name` (
    `id`      BIGINT,
    `f1`      STRING,
    `f2`      BIGINT,
    `f3`      BIGINT,
    `f4`      BIGINT,
    `f5`      STRING,
    `f6`      BIGINT,
    `f7`      STRING,
    `f8`      map<STRING, STRING>
    PRIMARY KEY (id, f1, f2, f4, f5, date, hour) NOT ENFORCED
) PARTITIONED by (
    `date` STRING comment '日期',
    `hour` STRING comment '小时'
) WITH (
    'changelog-producer'='lookup',
    'partition.expiration-time'='30 d',
    'partition.timestamp-pattern'='$date',
    'partition.expiration-check-interval'='3h',
    'sequence.field'='f8,f3',
    ...
);

--分钟指标上卷
INSERT INTO sink_table
SELECT
    id, f1,
    SUM(f3) AS f3,
    f2,
    MAX(f4) AS f4,
    MAX(f5) AS f5,
    MAX(f6) AS f6,
    MAX(f7) AS f7,
    LAST_VALUE(f8, f7) AS f8
FROM    paimon.db_name.table_name
GROUP BY id, f1, f2;
```

### 1.5 方案收益

- 流批一体模式开发：
  - 原有链路需要使用 MAX、LAST_VALUE 等函数来构造 retract 消息，以保证下游 SUM 计算结果正确，流与批的开发模式是分割的。
  - 基于 Paimon 存储数据并补齐 changelog，开发模式流与批是对齐的，获得流批一体的开发体验，提高了开发效率。
- 维表新鲜度更高：
  - 原有链路中为了减少维表服务压力，所以本地 Cache TTL设置为 50 min，数据新鲜度较低
  - 在Paimon 维表中默认每 10s 会主动检查维表数据是否有更新，并主动更新本地缓存，数据新鲜度更高。
- 数据乱序问题：
  - 原链路中需要使用 LAST_VALUE 来处理数据乱序问题，增加了额外的状态成本。
  - Paimon 合并数据时可以根据 sequence.field 来排序，从而在存储层解决数据乱序问题，不需要在 Flink 中维护状态。

![](https://mmbiz.qpic.cn/mmbiz_png/jC2t9Zib67r0IehVHQ9XrIic3jDcl5247PAfP3c0XvOu6ytxoM3Wlf9zNeJuxezSreowSDEUhwxiaHD143GPKovTg/640?wx_fmt=png&from=appmsg&randomid=x1ff7yx5&tp=webp&wxfrom=5&wx_lazy=1)

## 2. 场景二：财经多流拼接

### 2.1 业务场景

由于前端业务过程是由于多个功能模块通过接口拼接而成的，历史链路无法打通，关键节点指标缺失，DA同学需要投入大量时间找数据拼凑数据，用数成本高、数据精度低、无法实时看到增长策略表现。想要获得完整的用户交易过程的明细数据，财经侧在发起支付交易的时候创建了 trace_id，然后从支付开始透传到用户支付结束的所有流程中，利用 trace_id 构建用户交易行为宽表；

宽表打宽的过程中，会去组合前后端埋点、会员、标签、策略、交易、营销等多个主题域的数据，降低业务同学用数、找数成本。

### 2.2 原有业务方案

![](https://mmbiz.qpic.cn/mmbiz_png/jC2t9Zib67r3h3dicwkD7zia8m5YYkjSYOD0vK70SfhSWFcXH0jnbpIIJhwoHzfiaAxPhCbu45KJZiaHBwUP7HOvibBQ/640?wx_fmt=png&from=appmsg&randomid=9d593nvm&tp=webp&wxfrom=5&wx_lazy=1)

```sql
insert  into sink
select  id,
        last_value(f1) as f1,
        last_value(f2) as f2,
        last_value(f3) as f3,
        last_value(f4) as f4,
        ...
from    (
    select  id,
            f1,
            f2,
            cast(null as STRING) as f3,
            cast(null as STRING) as f4,
            ...
    from    table1
    union all
    select  id,
            cast(null as STRING) as f1,
            cast(null as STRING) as f2,
            f3,
            f4,
            ...
    from    table2
    union all
    ......
)
group by id;
```

### 1.3 方案痛点

- 资源开销和运维成本高：
  - 当前基于 MQ 和 Flink 做打宽任务的多流 Join，状态大小超过了 10TB，计算资源 1600+ CU。
  - 大状态会导致资源开销变高、任务吞吐抖动、故障恢复时间变长等问题。在当前场景下，宽表任务的异常抖动会带来下游超 10 min 的断流感知，运维成本较高，亟需优化。

![](https://mmbiz.qpic.cn/mmbiz_png/jC2t9Zib67r3h3dicwkD7zia8m5YYkjSYODHGC4pFg7T0skqrfwlGm1OVoYUp6KFQFr83BtTCZjykDeHc4KZdJUog/640?wx_fmt=png&from=appmsg&randomid=ctk227cq&tp=webp&wxfrom=5&wx_lazy=1)

- 数据乱序问题：
  - 由于打宽任务的超大状态，因此在 Flink 任务中状态的 TTL 配置相对较小（小时级）。在状态过期后，乱序数据会导致拼接结果不正确问题，产生额外的运维和排查成本。


### 1.4 Paimon实践

结合 Paimon 的 Partial Update 能力，对财经用户行为打宽任务进行了改写，数据直接写入到 Paimon 表，原链路中的聚合算子得以消除，任务状态大幅下降。同时基于 Paimon 的 Sequence Group 机制，为每个流定义了相应字段的顺序，避免因为乱序出现的数据不一致问题。

![](https://mmbiz.qpic.cn/mmbiz_png/jC2t9Zib67r3h3dicwkD7zia8m5YYkjSYODksngU0SsUXGyPmMMDQoibzwYicSoogGgNfb8bMuwhaibh1XYepsIOaCtQ/640?wx_fmt=png&from=appmsg&randomid=2x8n8r02&tp=webp&wxfrom=5&wx_lazy=1)

```sql
CREATE TABLE t (
    trace_id BIGINT,
    f1 STRING,
    f2 STRING,
    g_1 BIGINT,
    f3 STRING,
    f4 STRING,
    g_2 BIGINT,
    PRIMARY KEY (trace_id) NOT ENFORCED
) WITH (
    'merge-engine'='partial-update',
    'fields.g_1.sequence-group'='f1,f2', -- f1,f2字段根据 g_1 排序
    'fields.g_2.sequence-group'='f3,f4'  -- f3,f4字段根据 g_2 排序
);

insert  into t
select  trace_id,
        f1,
        f2,
        g_1,
        f3,
        f4,
        g_2,
        ...
from    (
    select  trace_id,
            f1,
            f2,
            g_1,
            cast(null as STRING) as f3,
            cast(null as STRING) as f4,
            cast(null as BIGINT) as g_2,
            xxx
    from    table1
    union all
    select  trace_id,
            cast(null as STRING) as f1,
            cast(null as STRING) as f2,
            cast(null as BIGINT) as g_1,
            f3,
            f4,
            g_2,
            xxx
    from    table2
    union all
    ......
)
```

### 1.5 方案收益

- 计算资源下降：计算资源优化 50%+ (1600 CU 缩减到 800 CU)，收益主要来源于状态管理成本下降；
- 状态优化：消除聚合状态后，作业状态由 10TB 缩减到小于 20GB；
- 开发和运维成本下降：中间数据可查可复用，同时指标增减可以通过 DDL 直接操作 Paimon 表；
- 数据乱序问题解决成本低：基于 Paimon 的 Sequence Group 机制可以对多流数据按序进行合并，处理更长时间范围内的乱序问题，并且不额外新增状态成本，较之于原链路方案，数据质量提升6%。

![](https://mmbiz.qpic.cn/mmbiz_png/jC2t9Zib67r0IehVHQ9XrIic3jDcl5247PuUlYw8BicJYxACvqIuBh8JTaxfZ5J0BCYiaMFRZ1EXlrfy54VFmI71IQ/640?wx_fmt=png&from=appmsg&randomid=cu2nn4p9&tp=webp&wxfrom=5&wx_lazy=1)

## 3. 未来展望

我们期望未来以 Flink 为核心，以数据湖为底座，为用户提供全链路数据生产和管理的实时数仓解决方案，进一步简化用户的开发和使用成本。我们也将继续针对实际业务场景进行 Apache Paimon 优化，包括：
- 千列大宽表合并性能优化：LSM Tree 架构使得 Apache Paimon 有很高的点查与合并性能，但在超大列数的业务场景中性能下降较多，内部将针对这一场景进行优化；
- 维表性能优化：Apache Paimon 的本地维表可以极大的减少传统外部 KV 存储的请求数量，但在大流量场景中，我们注意到本地维表刷新是同步的，同时没有按照 bucket 进行 shuffle，导致维表变化较快时，吞吐有明显尖刺，我们将结合 Flink 继续优化维表的访问性能；
- Merge Engine 扩展：部分业务场景中，业务需要自定义的 Merge Engine 来实现更加复杂的合并策略，因此我们将扩展 Merge Engine，使其支持业务进行扩展以应对更加复杂的业务场景。
