## 1. 列转行

### 1.1 需求

现在我们有一张统计每日用户工作量的表 dws_cms_user_workload_1d，记录一个用户(uid)在一天内的审核次数(cnt)、审核字数(words)、审核视频数(videos)、审核音频数(audios)：

| 用户ID  | 审核次数 |  审核字数 |  审核视频数 |  审核音频数 |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| 10001  | 10 | 8000  | 3 | 4 |
| 10002  | 8  | 2000  | 6 | 0 |
| 10003  | 20 | 15000 | 8 | 7 |

现在想将上述表数据转换为如下格式进行报表展示：

| 用户ID | 操作类型 | 操作量 |
| :------------- | :------------- | :------------- |
| 10001  | 审核次数   | 10   |
| 10001  | 审核字数   | 8000 |
| 10001  | 审核视频数 | 3    |
| 10001  | 审核音频数 | 4    |
| 10002  | 审核次数  | 8 |
| 10002  | 审核字数  | 2000 |
| 10002  | 审核视频数 | 6 |
| 10002  | 审核音频数 | 0 |
| 10003  | 审核次数 | 20 |
| 10003  | 审核字数 | 15000 |
| 10003  | 审核视频数 | 8 |
| 10003  | 审核音频数 | 7 |


### 1.2 方案

#### 1.2.1 利用 UNION ALL 实现

```sql
WITH dws_cms_user_workload_1d AS (
    SELECT '10001' AS uid, 10 AS cnt, 8000 AS words, 3 AS videos, 4 AS audios
    UNION ALL
    SELECT '10002' AS uid, 8 AS cnt, 2000 AS words, 6 AS videos, 0 AS audios
    UNION ALL
    SELECT '10003' AS uid, 20 AS cnt, 15000 AS words, 8 AS videos, 7 AS audios
)
SELECT uid, '审核次数' AS op, cnt AS workload
FROM dws_cms_user_workload_1d
UNION ALL
SELECT uid, '审核字数' AS op, words AS workload
FROM dws_cms_user_workload_1d
UNION ALL
SELECT uid, '审核视频数' AS op, videos AS workload
FROM dws_cms_user_workload_1d
UNION ALL
SELECT uid, '审核音频数' AS op, audios AS workload
FROM dws_cms_user_workload_1d;
```

输出结果如下所示：

| uid | op | workload |
| :------------- | :------------- | :------------- |
| 10001    | 审核次数    | 10            |
| 10002    | 审核次数    | 8             |
| 10003    | 审核次数    | 20            |
| 10001    | 审核字数    | 8000          |
| 10002    | 审核字数    | 2000          |
| 10003    | 审核字数    | 15000         |
| 10001    | 审核视频数   | 3             |
| 10002    | 审核视频数   | 6             |
| 10003    | 审核视频数   | 8             |
| 10001    | 审核音频数   | 4             |
| 10002    | 审核音频数   | 0             |
| 10003    | 审核音频数   | 7             |


#### 1.2.2 利用 CONCAT_WS 实现

可以使用 CONCAT_WS + POSEXPLODE 方法，利用下标位置索引进行一一对应：
```sql
WITH dws_cms_user_workload_1d AS (
    SELECT '10001' AS uid, 10 AS cnt, 8000 AS words, 3 AS videos, 4 AS audios
    UNION ALL
    SELECT '10002' AS uid, 8 AS cnt, 2000 AS words, 6 AS videos, 0 AS audios
    UNION ALL
    SELECT '10003' AS uid, 20 AS cnt, 15000 AS words, 8 AS videos, 7 AS audios
)
SELECT
  uid, op, workload
FROM (
    SELECT
        uid,
        ARRAY('审核次数', '审核字数', '审核视频数', '审核音频数') AS ops,
        CONCAT_WS(',', CAST(cnt AS STRING), CAST(words AS StRING), CAST(videos AS STRING), CAST(audios AS STRING)) AS workloads
    FROM dws_cms_user_workload_1d
) AS a
LATERAL VIEW POSEXPLODE(SPLIT(workloads, ',')) workloads AS workload_pos, workload
LATERAL VIEW POSEXPLODE(ops) ops AS op_pos, op
WHERE workload_pos = op_pos;
```

输出结果如下所示：

| uid | op | workload |
| :------------- | :------------- | :------------- |
| 10001  | 审核次数   | 10        |
| 10001  | 审核字数   | 8000      |
| 10001  | 审核视频数  | 3         |
| 10001  | 审核音频数  | 4         |
| 10002  | 审核次数   | 8         |
| 10002  | 审核字数   | 2000      |
| 10002  | 审核视频数  | 6         |
| 10002  | 审核音频数  | 0         |
| 10003  | 审核次数   | 20        |
| 10003  | 审核字数   | 15000     |
| 10003  | 审核视频数  | 8         |
| 10003  | 审核音频数  | 7         |

或者只使用 CONCAT_WS 来实现：

```sql
WITH dws_cms_user_workload_1d AS (
    SELECT '10001' AS uid, 10 AS cnt, 8000 AS words, 3 AS videos, 4 AS audios
    UNION ALL
    SELECT '10002' AS uid, 8 AS cnt, 2000 AS words, 6 AS videos, 0 AS audios
    UNION ALL
    SELECT '10003' AS uid, 20 AS cnt, 15000 AS words, 8 AS videos, 7 AS audios
)
SELECT
  uid, SPLIT(workload, '#')[0] AS op, SPLIT(workload, '#')[1] AS workload
FROM (
    SELECT
        uid,
        CONCAT_WS(',',
            CONCAT('审核次数#',cnt),
            CONCAT('审核字数#', words),
            CONCAT('审核视频数#', videos),
            CONCAT('审核音频数#', audios)
        ) AS workloads
    FROM dws_cms_user_workload_1d
) AS a
LATERAL VIEW EXPLODE(SPLIT(workloads, ',')) workloads AS workload;
```

| uid | op | workload |
| :------------- | :------------- | :------------- |
| 10001  | 审核次数   | 10        |
| 10001  | 审核字数   | 8000      |
| 10001  | 审核视频数  | 3         |
| 10001  | 审核音频数  | 4         |
| 10002  | 审核次数   | 8         |
| 10002  | 审核字数   | 2000      |
| 10002  | 审核视频数  | 6         |
| 10002  | 审核音频数  | 0         |
| 10003  | 审核次数   | 20        |
| 10003  | 审核字数   | 15000     |
| 10003  | 审核视频数  | 8         |
| 10003  | 审核音频数  | 7         |

## 2. 行转列

### 2.1 需求

现在我们有一张统计每日用户工作量的表 dws_cms_user_workload_1d，记录一个用户(uid)在一天内的审核次数、审核字数、审核视频数、审核音频数：

| 用户ID | 操作类型 | 操作量 |
| :------------- | :------------- | :------------- |
| 10001  | 审核次数   | 10   |
| 10001  | 审核字数   | 8000 |
| 10001  | 审核视频数 | 3    |
| 10001  | 审核音频数 | 4    |
| 10002  | 审核次数  | 8 |
| 10002  | 审核字数  | 2000 |
| 10002  | 审核视频数 | 6 |
| 10002  | 审核音频数 | 0 |
| 10003  | 审核次数 | 20 |
| 10003  | 审核字数 | 15000 |
| 10003  | 审核视频数 | 8 |
| 10003  | 审核音频数 | 7 |

现在想将上述表数据转换为如下格式进行报表展示：

| 用户ID  | 审核次数 |  审核字数 |  审核视频数 |  审核音频数 |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| 10001  | 10 | 8000  | 3 | 4 |
| 10002  | 8  | 2000  | 6 | 0 |
| 10003  | 20 | 15000 | 8 | 7 |

### 2.2 方案

使用 MAX + CASE WHEN 实现：
```sql
WITH dws_cms_user_workload_1d AS (
  SELECT '10001' AS uid, '审核次数' AS op, 10 AS workload
  UNION ALL
  SELECT '10001' AS uid, '审核字数' AS op, 8000 AS workload
  UNION ALL
  SELECT '10001' AS uid, '审核视频数' AS op, 3 AS workload
  UNION ALL
  SELECT '10001' AS uid, '审核音频数' AS op, 4 AS workload
  UNION ALL
  SELECT '10002' AS uid, '审核次数' AS op, 8 AS workload
  UNION ALL
  SELECT '10002' AS uid, '审核字数' AS op, 2000 AS workload
  UNION ALL
  SELECT '10002' AS uid, '审核视频数' AS op, 6 AS workload
  UNION ALL
  SELECT '10002' AS uid, '审核音频数' AS op, 0 AS workload
  UNION ALL
  SELECT '10003' AS uid, '审核次数' AS op, 20 AS workload
  UNION ALL
  SELECT '10003' AS uid, '审核字数' AS op, 15000 AS workload
  UNION ALL
  SELECT '10003' AS uid, '审核视频数' AS op, 8 AS workload
  UNION ALL
  SELECT '10003' AS uid, '审核音频数' AS op, 7 AS workload
)
SELECT
    uid,
    MAX((CASE op WHEN '审核次数' THEN workload ELSE 0 END)) AS cnt,
    MAX((CASE op WHEN '审核字数' THEN workload ELSE 0 END)) AS words,
    MAX((CASE op WHEN '审核视频数' THEN workload ELSE 0 END)) AS videos,
    MAX((CASE op WHEN '审核音频数' THEN workload ELSE 0 END)) AS audios
FROM dws_cms_user_workload_1d
GROUP BY uid;
```

输出结果如下所示：

| uid  | cnt |  words |  videos |  audio |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| 10001  | 10   | 8000   | 3       | 4       |
| 10002  | 8    | 2000   | 6       | 0       |
| 10003  | 20   | 15000  | 8       | 7       |
