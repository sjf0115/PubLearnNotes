## 1. 需求

假设有一张微信好友关系表 dwd_wx_user_friend_mapping_dd，包括字段：uid（用户id），fid（好友id）；还有一张用户运动步数表 dwd_wx_user_step_di，包括字段：uid（用户id），steps（步数）。需求是计算微信运动步数在好友中的排名。

## 2. 数据准备

假设 dwd_wx_user_friend_mapping_dd 表有如下数据：

| uid| fid |
| :------------- | :------------- |
| 001 | 002 |
| 001 | 003 |
| 002 | 001 |
| 003 | 001 |

假设 dwd_wx_user_step_di 表有如下数据：

| uid| steps |
| :------------- | :------------- |
| 001 | 1500 |
| 002 | 1200 |
| 003 | 2000 |

## 3. 方案

想要求出自己的运动步数在所有好友中的排名
- 第一：需要找出自己的所有好友，可以直接根据 dwd_wx_user_friend_mapping_dd 表获取，自己和好友分为一组便于排名
- 第二：需要求出所有好友以及自己的运动步数，可以直接根据 dwd_wx_user_step_di 表获取
- 第三：在拿到所有运动步数之后，可以通过对排名函数进行开窗根据分组进行得到排名，获取自己对应的排名即可

```sql
WITH user_friend AS (
    SELECT uid, fid
    FROM dwd_wx_user_friend_mapping_dd
),
friend_group AS (
    -- 好友
    SELECT uid AS user_group, fid AS user_id
    FROM user_friend
    UNION ALL
    -- 自己
    SELECT uid AS user_group, uid AS user_id
    FROM user_friend
    GROUP BY uid
),
friend_step AS (
    SELECT a1.user_group, a1.user_id, a2.steps,
    FROM friend_group AS a1
    LEFT OUTER JOIN (
       SELECT uid, steps
       FROM dwd_wx_user_step_di
    ) AS a2
    ON a1.user_id = a2.uid
)
SELECT user_id, steps, rank
FROM (
    SELECT
        user_group, user_id, steps,
        ROW_NUMBER() OVER (PARTITION BY user_group ORDER BY steps DESC) AS rank
    FROM friend_step
) AS a1
WHERE user_group = user_id -- 自己
;
```
