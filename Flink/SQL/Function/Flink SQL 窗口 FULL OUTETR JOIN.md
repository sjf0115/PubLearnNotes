
```sql
CREATE VIEW view_user_behavior_click AS
SELECT
  TUMBLE_START(ts, INTERVAL '1' MINUTE) AS window_start,
  TUMBLE_END(ts, INTERVAL '1' MINUTE) AS window_end,
  content_id, MAX(time) AS last_time
FROM user_behavior_click
GROUP BY TUMBLE(ts, INTERVAL '1' MINUTE), content_id;

CREATE VIEW view_user_behavior_page_view AS
SELECT
  TUMBLE_START(ts, INTERVAL '1' MINUTE) AS window_start,
  TUMBLE_END(ts, INTERVAL '1' MINUTE) AS window_end,
  content_id, MAX(time) AS last_time
FROM user_behavior_page_view
GROUP BY TUMBLE(ts, INTERVAL '1' MINUTE), content_id;

SELECT
  COALESCE(a1.window_start, a2.window_start) AS window_start,
  COALESCE(a1.window_end, a2.window_end) AS window_end,
  COALESCE(a1.content_id, a2.content_id) AS content_id,
  a1.last_time AS click_time,
  a2.last_time AS page_view_time,
FROM view_user_behavior_click AS a1
FULL OUTER JOIN view_user_behavior_page_view AS a2
ON a1.window_start = a2.window_start AND a1.window_end = a2.window_end
  AND a1.content_id = a2.content_id;
```
