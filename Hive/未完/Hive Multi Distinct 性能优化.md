## 1. 场景1-同一去重字段

```sql
CREATE TABLE user_behavior AS
SELECT
  0 AS site_type, 800 AS cid, '15001' AS uid, '21343121232' AS content_id, '102121adaf212sfsa' AS show_id,
  10 AS show_cnt, 8 AS exp_cnt, 6 AS click_cnt, 2 AS visit_cnt, 1 AS pv, 1 AS vv,
  1 AS share_cnt, 1 AS fav_cnt, 1 AS like_cnt, 1 AS cmt_cnt;
```

### 1.1 问题

如下面所示，计算每个站点整体用户数、下发用户数、曝光用户数等指标：
```sql
EXPLAIN
SELECT
    site_type,
    COUNT(DISTINCT uid) AS uv,                                  -- 整体用户数
    COUNT(DISTINCT IF(show_cnt > 0, uid, NULL)) AS show_uv,     -- 下发用户数
    COUNT(DISTINCT IF(exp_cnt > 0, uid, NULL)) AS exp_uv,       -- 曝光用户数
    COUNT(DISTINCT IF(click_cnt > 0, uid, NULL)) AS click_uv,   -- 点击用户数
    COUNT(DISTINCT IF(visit_cnt > 0, uid, NULL)) AS visit_uv,   -- 访问用户数
    COUNT(DISTINCT IF(pv > 0, uid, NULL)) AS page_view_uv,      -- 浏览用户数
    COUNT(DISTINCT IF(vv > 0, uid, NULL)) AS play_uv,           -- 播放用户数
    COUNT(DISTINCT IF(share_cnt > 0, uid, NULL)) AS share_uv,   -- 分享用户数
    COUNT(DISTINCT IF(fav_cnt > 0, uid, NULL)) AS fav_uv,       -- 收藏用户数
    COUNT(DISTINCT IF(like_cnt > 0, uid, NULL)) AS like_uv,  -- 点赞用户数
    COUNT(DISTINCT IF(cmt_cnt > 0, uid, NULL)) AS cmt_uv        -- 评论用户数
FROM user_behavior
GROUP BY site_type;
```
通过上面代码可以看出整体用户数、下发用户数、曝光用户数等都是基于用户Id uid 去重实现，区别只是去重的条件不一样，下发用户数限定用户下发次数大于0，曝光用户数限定用户曝光次数大于0，其他用户数指标以此类推。

```sql
STAGE DEPENDENCIES:
  Stage-1 is a root stage
  Stage-0 depends on stages: Stage-1

STAGE PLANS:
  Stage: Stage-1
    Map Reduce
      Map Operator Tree:
          TableScan
            alias: user_behavior
            Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
            Select Operator
              expressions: site_type (type: int), uid (type: string), if((show_cnt > 0), uid, null) (type: string), if((exp_cnt > 0), uid, null) (type: string), if((click_cnt > 0), uid, null) (type: string), if((visit_cnt > 0), uid, null) (type: string), if((pv > 0), uid, null) (type: string), if((vv > 0), uid, null) (type: string), if((share_cnt > 0), uid, null) (type: string), if((fav_cnt > 0), uid, null) (type: string), if((like_cnt > 0), uid, null) (type: string), if((cmt_cnt > 0), uid, null) (type: string)
              outputColumnNames: _col0, _col1, _col2, _col3, _col4, _col5, _col6, _col7, _col8, _col9, _col10, _col11
              Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
              Group By Operator
                aggregations: count(DISTINCT _col1), count(DISTINCT _col2), count(DISTINCT _col3), count(DISTINCT _col4), count(DISTINCT _col5), count(DISTINCT _col6), count(DISTINCT _col7), count(DISTINCT _col8), count(DISTINCT _col9), count(DISTINCT _col10), count(DISTINCT _col11)
                keys: _col0 (type: int), _col1 (type: string), _col2 (type: string), _col3 (type: string), _col4 (type: string), _col5 (type: string), _col6 (type: string), _col7 (type: string), _col8 (type: string), _col9 (type: string), _col10 (type: string), _col11 (type: string)
                mode: hash
                outputColumnNames: _col0, _col1, _col2, _col3, _col4, _col5, _col6, _col7, _col8, _col9, _col10, _col11, _col12, _col13, _col14, _col15, _col16, _col17, _col18, _col19, _col20, _col21, _col22
                Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
                Reduce Output Operator
                  key expressions: _col0 (type: int), _col1 (type: string), _col2 (type: string), _col3 (type: string), _col4 (type: string), _col5 (type: string), _col6 (type: string), _col7 (type: string), _col8 (type: string), _col9 (type: string), _col10 (type: string), _col11 (type: string)
                  sort order: ++++++++++++
                  Map-reduce partition columns: _col0 (type: int)
                  Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
      Reduce Operator Tree:
        Group By Operator
          aggregations: count(DISTINCT KEY._col1:0._col0), count(DISTINCT KEY._col1:1._col0), count(DISTINCT KEY._col1:2._col0), count(DISTINCT KEY._col1:3._col0), count(DISTINCT KEY._col1:4._col0), count(DISTINCT KEY._col1:5._col0), count(DISTINCT KEY._col1:6._col0), count(DISTINCT KEY._col1:7._col0), count(DISTINCT KEY._col1:8._col0), count(DISTINCT KEY._col1:9._col0), count(DISTINCT KEY._col1:10._col0)
          keys: KEY._col0 (type: int)
          mode: mergepartial
          outputColumnNames: _col0, _col1, _col2, _col3, _col4, _col5, _col6, _col7, _col8, _col9, _col10, _col11
          Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
          File Output Operator
            compressed: false
            Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
            table:
                input format: org.apache.hadoop.mapred.SequenceFileInputFormat
                output format: org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat
                serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe

  Stage: Stage-0
    Fetch Operator
      limit: -1
      Processor Tree:
        ListSink
```

### 1.2 优化

一般在做去重避免数据倾斜时，都会添加 `hive.groupby.skewindata=true` 参数，如下所示：
```sql
SET hive.groupby.skewindata=true;
SELECT
    site_type,
    COUNT(DISTINCT uid) AS uv,                                  -- 整体用户数
    COUNT(DISTINCT IF(show_cnt > 0, uid, NULL)) AS show_uv,     -- 下发用户数
    COUNT(DISTINCT IF(exp_cnt > 0, uid, NULL)) AS exp_uv,       -- 曝光用户数
    COUNT(DISTINCT IF(click_cnt > 0, uid, NULL)) AS click_uv,   -- 点击用户数
    COUNT(DISTINCT IF(visit_cnt > 0, uid, NULL)) AS visit_uv,   -- 访问用户数
    COUNT(DISTINCT IF(pv > 0, uid, NULL)) AS page_view_uv,      -- 浏览用户数
    COUNT(DISTINCT IF(vv > 0, uid, NULL)) AS play_uv,           -- 播放用户数
    COUNT(DISTINCT IF(share_cnt > 0, uid, NULL)) AS share_uv,   -- 分享用户数
    COUNT(DISTINCT IF(fav_cnt > 0, uid, NULL)) AS fav_uv,       -- 收藏用户数
    COUNT(DISTINCT IF(like_cnt > 0, uid, NULL)) AS like_uv,  -- 点赞用户数
    COUNT(DISTINCT IF(cmt_cnt > 0, uid, NULL)) AS cmt_uv        -- 评论用户数
FROM user_behavior
GROUP BY site_type;
```
但是需要注意的是 `hive.groupby.skewindata` 仅支持单字段去重，不支持类似上面的多个字段去重，否则会抛出如下异常信息：
```
FAILED: SemanticException [Error 10022]: DISTINCT on different columns not supported with skew in data
```

```sql
EXPLAIN
SELECT
    site_type,
    COUNT(uid) AS uv,                                               -- 整体用户数
    COUNT(IF(is_show_user = 1, uid, NULL)) AS show_uv,              -- 下发用户数
    COUNT(IF(is_exp_user = 1, uid, NULL)) AS exp_uv,                -- 曝光用户数
    COUNT(IF(is_click_user = 1, uid, NULL)) AS click_uv,            -- 点击用户数
    COUNT(IF(is_visit_user = 1, uid, NULL)) AS visit_uv,            -- 访问用户数
    COUNT(IF(is_page_view_user = 1, uid, NULL)) AS page_view_uv,    -- 浏览用户数
    COUNT(IF(is_play_user = 1, uid, NULL)) AS play_uv,              -- 播放用户数
    COUNT(IF(is_share_user = 1, uid, NULL)) AS share_uv,            -- 分享用户数
    COUNT(IF(is_fav_user = 1, uid, NULL)) AS fav_uv,                -- 收藏用户数
    COUNT(IF(is_like_user = 1, uid, NULL)) AS like_uv,              -- 点赞用户数
    COUNT(IF(is_cmt_user = 1, uid, NULL)) AS cmt_uv                 -- 评论用户数
FROM (
    SELECT
        site_type, uid,
        -- 用户打标
        MAX(IF(show_cnt > 0, 1, 0)) AS is_show_user,
        MAX(IF(exp_cnt > 0, 1, 0)) AS is_exp_user,
        MAX(IF(click_cnt > 0, 1, 0)) AS is_click_user,
        MAX(IF(visit_cnt > 0, 1, 0)) AS is_visit_user,
        MAX(IF(pv > 0, 1, 0)) AS is_page_view_user,
        MAX(IF(vv > 0, 1, 0)) AS is_play_user,
        MAX(IF(share_cnt > 0, 1, 0)) AS is_share_user,
        MAX(IF(fav_cnt > 0, 1, 0)) AS is_fav_user,
        MAX(IF(like_cnt > 0, 1, 0)) AS is_like_user,
        MAX(IF(cmt_cnt > 0, 1, 0)) AS is_cmt_user
    FROM user_behavior
    GROUP BY site_type, uid
) AS a
GROUP BY site_type;
```
执行计划如下所示：
```sql
STAGE DEPENDENCIES:
  Stage-1 is a root stage
  Stage-2 depends on stages: Stage-1
  Stage-3 depends on stages: Stage-2
  Stage-4 depends on stages: Stage-3
  Stage-0 depends on stages: Stage-4

STAGE PLANS:
  Stage: Stage-1
    Map Reduce
      Map Operator Tree:
          TableScan
            alias: user_behavior
            Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
            Select Operator
              expressions: site_type (type: int), uid (type: string), if((show_cnt > 0), 1, 0) (type: int), if((exp_cnt > 0), 1, 0) (type: int), if((click_cnt > 0), 1, 0) (type: int), if((visit_cnt > 0), 1, 0) (type: int), if((pv > 0), 1, 0) (type: int), if((vv > 0), 1, 0) (type: int), if((share_cnt > 0), 1, 0) (type: int), if((fav_cnt > 0), 1, 0) (type: int), if((like_cnt > 0), 1, 0) (type: int), if((cmt_cnt > 0), 1, 0) (type: int)
              outputColumnNames: _col0, _col1, _col2, _col3, _col4, _col5, _col6, _col7, _col8, _col9, _col10, _col11
              Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
              Group By Operator
                aggregations: max(_col2), max(_col3), max(_col4), max(_col5), max(_col6), max(_col7), max(_col8), max(_col9), max(_col10), max(_col11)
                keys: _col0 (type: int), _col1 (type: string)
                mode: hash
                outputColumnNames: _col0, _col1, _col2, _col3, _col4, _col5, _col6, _col7, _col8, _col9, _col10, _col11
                Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
                Reduce Output Operator
                  key expressions: _col0 (type: int), _col1 (type: string)
                  sort order: ++
                  Map-reduce partition columns: rand() (type: double)
                  Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
                  value expressions: _col2 (type: int), _col3 (type: int), _col4 (type: int), _col5 (type: int), _col6 (type: int), _col7 (type: int), _col8 (type: int), _col9 (type: int), _col10 (type: int), _col11 (type: int)
      Reduce Operator Tree:
        Group By Operator
          aggregations: max(VALUE._col0), max(VALUE._col1), max(VALUE._col2), max(VALUE._col3), max(VALUE._col4), max(VALUE._col5), max(VALUE._col6), max(VALUE._col7), max(VALUE._col8), max(VALUE._col9)
          keys: KEY._col0 (type: int), KEY._col1 (type: string)
          mode: partials
          outputColumnNames: _col0, _col1, _col2, _col3, _col4, _col5, _col6, _col7, _col8, _col9, _col10, _col11
          Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
          File Output Operator
            compressed: false
            table:
                input format: org.apache.hadoop.mapred.SequenceFileInputFormat
                output format: org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat
                serde: org.apache.hadoop.hive.serde2.lazybinary.LazyBinarySerDe

  Stage: Stage-2
    Map Reduce
      Map Operator Tree:
          TableScan
            Reduce Output Operator
              key expressions: _col0 (type: int), _col1 (type: string)
              sort order: ++
              Map-reduce partition columns: _col0 (type: int), _col1 (type: string)
              Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
              value expressions: _col2 (type: int), _col3 (type: int), _col4 (type: int), _col5 (type: int), _col6 (type: int), _col7 (type: int), _col8 (type: int), _col9 (type: int), _col10 (type: int), _col11 (type: int)
      Reduce Operator Tree:
        Group By Operator
          aggregations: max(VALUE._col0), max(VALUE._col1), max(VALUE._col2), max(VALUE._col3), max(VALUE._col4), max(VALUE._col5), max(VALUE._col6), max(VALUE._col7), max(VALUE._col8), max(VALUE._col9)
          keys: KEY._col0 (type: int), KEY._col1 (type: string)
          mode: final
          outputColumnNames: _col0, _col1, _col2, _col3, _col4, _col5, _col6, _col7, _col8, _col9, _col10, _col11
          Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
          Select Operator
            expressions: _col0 (type: int), _col1 (type: string), if((_col2 = 1), _col1, null) (type: string), if((_col3 = 1), _col1, null) (type: string), if((_col4 = 1), _col1, null) (type: string), if((_col5 = 1), _col1, null) (type: string), if((_col6 = 1), _col1, null) (type: string), if((_col7 = 1), _col1, null) (type: string), if((_col8 = 1), _col1, null) (type: string), if((_col9 = 1), _col1, null) (type: string), if((_col10 = 1), _col1, null) (type: string), if((_col11 = 1), _col1, null) (type: string)
            outputColumnNames: _col0, _col1, _col2, _col3, _col4, _col5, _col6, _col7, _col8, _col9, _col10, _col11
            Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
            Group By Operator
              aggregations: count(_col1), count(_col2), count(_col3), count(_col4), count(_col5), count(_col6), count(_col7), count(_col8), count(_col9), count(_col10), count(_col11)
              keys: _col0 (type: int)
              mode: hash
              outputColumnNames: _col0, _col1, _col2, _col3, _col4, _col5, _col6, _col7, _col8, _col9, _col10, _col11
              Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
              File Output Operator
                compressed: false
                table:
                    input format: org.apache.hadoop.mapred.SequenceFileInputFormat
                    output format: org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat
                    serde: org.apache.hadoop.hive.serde2.lazybinary.LazyBinarySerDe

  Stage: Stage-3
    Map Reduce
      Map Operator Tree:
          TableScan
            Reduce Output Operator
              key expressions: _col0 (type: int)
              sort order: +
              Map-reduce partition columns: rand() (type: double)
              Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
              value expressions: _col1 (type: bigint), _col2 (type: bigint), _col3 (type: bigint), _col4 (type: bigint), _col5 (type: bigint), _col6 (type: bigint), _col7 (type: bigint), _col8 (type: bigint), _col9 (type: bigint), _col10 (type: bigint), _col11 (type: bigint)
      Reduce Operator Tree:
        Group By Operator
          aggregations: count(VALUE._col0), count(VALUE._col1), count(VALUE._col2), count(VALUE._col3), count(VALUE._col4), count(VALUE._col5), count(VALUE._col6), count(VALUE._col7), count(VALUE._col8), count(VALUE._col9), count(VALUE._col10)
          keys: KEY._col0 (type: int)
          mode: partials
          outputColumnNames: _col0, _col1, _col2, _col3, _col4, _col5, _col6, _col7, _col8, _col9, _col10, _col11
          Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
          File Output Operator
            compressed: false
            table:
                input format: org.apache.hadoop.mapred.SequenceFileInputFormat
                output format: org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat
                serde: org.apache.hadoop.hive.serde2.lazybinary.LazyBinarySerDe

  Stage: Stage-4
    Map Reduce
      Map Operator Tree:
          TableScan
            Reduce Output Operator
              key expressions: _col0 (type: int)
              sort order: +
              Map-reduce partition columns: _col0 (type: int)
              Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
              value expressions: _col1 (type: bigint), _col2 (type: bigint), _col3 (type: bigint), _col4 (type: bigint), _col5 (type: bigint), _col6 (type: bigint), _col7 (type: bigint), _col8 (type: bigint), _col9 (type: bigint), _col10 (type: bigint), _col11 (type: bigint)
      Reduce Operator Tree:
        Group By Operator
          aggregations: count(VALUE._col0), count(VALUE._col1), count(VALUE._col2), count(VALUE._col3), count(VALUE._col4), count(VALUE._col5), count(VALUE._col6), count(VALUE._col7), count(VALUE._col8), count(VALUE._col9), count(VALUE._col10)
          keys: KEY._col0 (type: int)
          mode: final
          outputColumnNames: _col0, _col1, _col2, _col3, _col4, _col5, _col6, _col7, _col8, _col9, _col10, _col11
          Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
          File Output Operator
            compressed: false
            Statistics: Num rows: 1 Data size: 62 Basic stats: COMPLETE Column stats: NONE
            table:
                input format: org.apache.hadoop.mapred.SequenceFileInputFormat
                output format: org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat
                serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe

  Stage: Stage-0
    Fetch Operator
      limit: -1
      Processor Tree:
        ListSink
```

## 2. 场景2-不同去重字段

### 2.1 问题

如下面所示，计算每个站点整体用户数、下发用户数、曝光用户数等指标：

```sql
SELECT
    site_type,
    COUNT(DISTINCT uid) AS uv,              -- 用户数
    COUNT(DISTINCT content_id) AS item_num  -- 内容量
FROM behavior
WHERE dt = '20230216'
GROUP BY site_type;
```

### 2.2 优化

```sql
WITH behavior AS (
    SELECT site_type, content_id, uid
    FROM behavior
    WHERE dt = '20230216'
    GROUP BY site_type, content_id, uid
),
user AS (
    -- 用户数
    SELECT
        site_type, COUNT(*) AS uv
    FROM (
        SELECT site_type, uid
        FROM behavior
        GROUP BY site_type, uid
    ) AS a
    GROUP BY site_type
),
item AS (
    -- 内容量
    SELECT
        site_type, COUNT(*) AS uv
    FROM (
        SELECT site_type, content_id
        FROM behavior
        GROUP BY site_type, content_id
    ) AS a
    GROUP BY site_type
)
SELECT
    site_type, SUM(uv) AS uv, SUM(item_num) AS item_num
FROM (
    -- 用户数
    SELECT site_type, uv, 0 AS item_num
    FROM user
    UNION ALL
    -- 内容量
    SELECT site_type, 0 AS uv, item_num
    FROM item
) AS a
GROUP BY site_type;
```

这种优化方案缺点也比较明显，代码看起来比较冗长与繁琐，需要每个去重字段单独去重并通过 UNION ALL 一起。如果我们有几十个去重字段，结果可想而知。

```

```



...
