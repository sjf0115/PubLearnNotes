https://cwiki.apache.org/confluence/display/Hive/LanguageManual+Transform

https://www.cnblogs.com/aquastone/p/hive-transform.html

https://www.cnblogs.com/cangos/p/6486651.html


EXPLAIN FROM adv_push_active
SELECT TRANSFORM(vid)
USING 'transform_platform.py'
AS platform
LIMIT 10;

EXPLAIN SELECT vid
FROM adv_push_active
LIMIT 10;
