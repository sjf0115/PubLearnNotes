
| PlayId | time  | result |
| :------------- | :------------- | :------------- |
| a | 2022-10-01 | win |
| a | 2022-10-02 | win |
| a | 2022-10-03 | lose |
| a | 2022-10-04 | win |
| a | 2022-10-05 | win |
| a | 2022-10-06 | win |
| b | 2022-10-01 | lose |
| b | 2022-10-04 | lose |
| c | 2022-10-03 | win |
| c | 2022-10-04 | lose |
| c | 2022-10-07 | win |
| c | 2022-10-08 | win |


```sql
SELECT
  play_id, MAX(win_num) AS long_win_num
FROM (
  SELECT
    play_id, flag1 - flag2 AS group_id,
    SUM(result_flag) AS win_num
  FROM (
    SELECT
      play_id, time, result,
      IF(result = 'win', 1, 0) AS result_flag,
      ROW_NUMBER OVER (PARTITION BY play_id ORDER BY time) AS flag1,
      ROW_NUMBER OVER (PARTITION BY play_id, result ORDER BY time) AS flag2
    FROM T
  ) AS a
  GROUP BY play_id, flag1 - flag2
) AS b
GROUP BY play_id;
```
