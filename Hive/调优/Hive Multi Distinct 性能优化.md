## 1. 场景1-同一去重字段

### 1.1 问题

如下面所示，计算每个站点整体用户数、下发用户数、曝光用户数等指标：
```sql
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
    COUNT(DISTINCT IF(support_cnt > 0, uid, NULL)) AS like_uv,  -- 点赞用户数
    COUNT(DISTINCT IF(cmt_cnt > 0, uid, NULL)) AS cmt_uv        -- 评论用户数
FROM behavior
WHERE dt = '20230216'
GROUP BY site_type;
```
通过上面代码可以看出整体用户数、下发用户数、曝光用户数等都是基于用户Id uid 去重实现，区别只是去重的条件不一样，下发用户数限定用户下发次数大于0，曝光用户数限定用户曝光次数大于0，其他用户数指标以此类推。

### 1.2 优化

```sql
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
        MAX(IF(support_cnt > 0, 1, 0)) AS is_like_user,
        MAX(IF(cmt_cnt > 0, 1, 0)) AS is_cmt_user
    FROM behavior
    WHERE dt = '20230216'
    GROUP BY site_type, uid
) AS a
GROUP BY site_type;
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
