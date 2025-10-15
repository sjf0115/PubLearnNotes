```sql
-- 用户明细表
CREATE TABLE user_detail (
  user_id BIGINT NOT NULL PRIMARY KEY COMMENT '用户ID',
  level_id BIGINT NOT NULL COMMENT '等级ID'
);

-- 等级明细
CREATE TABLE level_detail (
  level_id BIGINT NOT NULL PRIMARY KEY COMMENT '等级ID',
  level_name VARCHAR(255) NOT NULL COMMENT '等级名称'
);

CREATE TABLE user_level_detail (
	user_id BIGINT NOT NULL PRIMARY KEY COMMENT '用户ID',
  level_id BIGINT NOT NULL COMMENT '等级ID',
  level_name VARCHAR(255) NOT NULL COMMENT '等级名称'
);
```



```sql
-- CDC source tables:  user_detail & level_detail
CREATE TEMPORARY TABLE user_detail (
  user_id BIGINT,
  level_id BIGINT,
  PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
  'connector' = 'mysql-cdc',
  'hostname' = 'localhost',
  'port' = '3306',
  'username' = 'root',
  'password' = '123456',
  'database-name' = 'flink',
  'table-name' = 'user_detail',
	'scan.startup.mode' = 'latest-offset'
);

CREATE TEMPORARY TABLE level_detail (
  level_id BIGINT,
  level_name VARCHAR,
  PRIMARY KEY (level_id) NOT ENFORCED
) WITH (
  'connector' = 'mysql-cdc',
  'hostname' = 'localhost',
  'port' = '3306',
  'username' = 'root',
  'password' = '123456',
  'database-name' = 'flink',
  'table-name' = 'level_detail',
	'scan.startup.mode' = 'initial'
);

-- sink table:
CREATE TEMPORARY TABLE user_level_detail (
	user_id BIGINT,
	level_id BIGINT,
  level_name VARCHAR,
  PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
  'connector' = 'jdbc',
  'url' = 'jdbc:mysql://localhost:3306/flink',
  'username' = 'root',
  'password' = '123456',
  'table-name' = 'user_level_detail',
	'sink.parallelism'='2'
);

-- join user_detail and level_detail and insert the result into user_level_detail
INSERT INTO user_level_detail
SELECT a1.user_id, a1.level_id, a2.level_name
FROM user_detail AS a1
JOIN level_detail AS a2
ON a1.level_id = a2.level_id;
```

```sql
-- 初始化
INSERT INTO level_detail VALUES (1,"A"), (2,"B"), (3,"C"), (4,"D");

-- 模拟数据
INSERT INTO user_detail VALUES (1001, 2);
UPDATE user_detail SET level_id = 1 WHERE user_id = 1001;
```

```
SET 'table.exec.sink.upsert-materialize'='none';
```

假设源表 user_detail 中 user_id 为 1 的记录的 Changelog 在时间 t0 插入(user_id=1001, level_id=2)，然后在时间 t1 将该行更新为(user_id=1001, level=3)。这对应三个拆分事件：

| user_detail | 事件类型|
| :------------- | :------------- |
| +I（user_id=1，level_id=2） | INSERT |
| -U（user_id=1，level_id=2） | UPDATE_BEFORE |
| +U（user_id=1，level_id=1） | UPDATE_AFTER |
