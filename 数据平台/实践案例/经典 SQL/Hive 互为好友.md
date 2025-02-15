

```sql
SELECT
  COUNT(1) AS friends_num
FROM (
  SELECT friends
  FROM (
    SELECT
      uid, friend_id,
      IF(uid > friend_id, CONCAT(uid, ':', friend_id), CONCAT(friend_id, ':', uid)) AS friends
    FROM user_table t1
    LATERAL VIEW OUTER EXPLODE(SPLIT(friends_id, ',')) friends_id AS friend_id
  ) AS a
  GROUP BY friends
  HAVING COUNT(friends) = 2
) AS b;
```
