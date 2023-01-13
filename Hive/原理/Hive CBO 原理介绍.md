CBO，全称是 Cost Based Optimization，即基于代价的优化器。其优化目标是：在编译阶段，根据查询语句中涉及到的表和查询条件，计算出产生中间结果少的高效 JOIN 顺序，从而减少查询时间和资源消耗。

Hive 使用开源组件 Apache Calcite 实现 CBO。首先 SQL 语句转化成 Hive 的 AST，然后转成 Calcite 可以识别的 RelNodes。Calcite 将 RelNode 中的 Join 顺序调整后，再由 Hive 将 RelNode 转成 AST，继续 Hive 的逻辑优化和物理优化过程。Hive 中实现 CBO 的总体过程如下图所示：

![](1)

Calcite 调整 Join 顺序的具体过程如下：
- 针对所有参与 Join 的表，依次选取一个表作为第一张表。
- 依据选取的第一张表，根据代价选择第二张表，第三张表。由此可以得到多个不同的执行计划。
- 计算出代价最小的一个计划，作为最终的顺序优化结果。

代价的具体计算方法：
当前版本，代价的衡量基于 Join 出来的数据条数：Join 出来的条数越少，代价越小。Join 条数的多少，取决于参与 Join 的表的选择率。表的数据条数，取自表级别的统计信息。

过滤条件过滤后的条数，由列级别的统计信息，max，min，以及NDV（Number of Distinct Values）来估算出来。例如存在一张表table_a，其统计信息如下：数据总条数1000000，NDV 50，查询条件如下：
```
Select * from table_a where colum_a='value1';
```
则估算查询的最终条数为1000000 * 1/50 = 20000条，选择率为2%。

以下以TPC-DS Q3为例来介绍CBO是如何调整Join顺序的：
```
select
    dt.d_year,
    item.i_brand_id brand_id,
    item.i_brand brand,
    sum(ss_ext_sales_price) sum_agg
from
    date_dim dt,
    store_sales,
    item
where
    dt.d_date_sk = store_sales.ss_sold_date_sk
    and store_sales.ss_item_sk = item.i_item_sk
    and item.i_manufact_id = 436
    and dt.d_moy = 12
group by dt.d_year , item.i_brand , item.i_brand_id
order by dt.d_year , sum_agg desc , brand_id
limit 10;
```




> 原文:[Hive CBO原理介绍](https://support.huaweicloud.com/productdesc-mrs/mrs_08_001102.html)
