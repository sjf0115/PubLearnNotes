MySQL CDC Connector 允许从 MySQL 数据库读取快照数据和增量数据。本文档描述如何设置 MySQL CDC Connector 以对 MySQL 数据库运行 SQL 查询。

## 1. 依赖

为了设置 MySQL CDC Connector，下表提供了使用构建自动化工具（如Maven或SBT）和带有 SQL JAR 包的 SQL Client 的两个项目的依赖项信息。

```
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-connector-mysql-cdc</artifactId>
    <version>3.5.0</version>
</dependency>
```

## 2.

```sql
CREATE TABLE user_level (
    user_id VARCHAR(50) NOT NULL COMMENT '用户ID',
    level_id BIGINT NOT NULL COMMENT '用户等级ID',
    PRIMARY KEY (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户等级';


CREATE TABLE dim_level (
    level_id BIGINT NOT NULL COMMENT '等级ID',
    level_name VARCHAR(50) NOT NULL COMMENT '等级名称',
    PRIMARY KEY (level_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='等级映射';
```


```
CREATE TEMPORARY TABLE user_level (
  user_id BIGINT,
  level BIGINT,
  PRIMARY KEY(id) NOT ENFORCED
)WITH (...);

CREATE TEMPORARY TABLE dim_level (
  level_id BIGINT,
  level_name VARCHAR,
  PRIMARY KEY(id) NOT ENFORCED
)WITH (...);

-- sink table: t1
CREATE TEMPORARY TABLE t1 (
  id BIGINT,
  level BIGINT,
  attr VARCHAR,
  PRIMARY KEY(id) NOT ENFORCED
)WITH (...);

-- join s1 and s2 and insert the result into t1
INSERT INTO t1
SELECT s1.*, s2.attr
FROM s1
JOIN s2
ON s1.level = s2.id;
```
