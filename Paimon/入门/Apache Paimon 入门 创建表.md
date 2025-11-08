

## 1. 管理表

创建 Paimon Catalog 后，您可以创建和删除表。在 Paimon Catalog 中创建的表就是 Paimon 的管理表，并由该 Catalog 管理，类似 Hive 的内部表。当表从 Catalog 中删除时，其表文件也将被删除。

以下SQL假设您已经注册并正在使用 Paimon Catalog。在 Catalog 的默认数据库中创建一个名为 my_table 的管理表，其中包含五个列，dt、hh 和 user_id 是主键。

```sql
CREATE TABLE my_table (
    user_id BIGINT,
    item_id BIGINT,
    behavior STRING,
    dt STRING,
    hh STRING,
    PRIMARY KEY (dt, hh, user_id) NOT ENFORCED
);
```
你可以使用如下语句创建分区表：
```sql
CREATE TABLE my_table (
    user_id BIGINT,
    item_id BIGINT,
    behavior STRING,
    dt STRING,
    hh STRING,
    PRIMARY KEY (dt, hh, user_id) NOT ENFORCED
) PARTITIONED BY (dt, hh);
```
> 如果你需要跨分区插入（主键不包含所有分区字段），请查看跨分区插入模式。通过配置 partition.expiration-time，过期的分区可以自动删除。

### 1.1 指定统计模式

Paimon 将自动收集数据文件的统计信息以加快查询过程。支持如下四种模式：
- `full`：收集完整指标，有 null_count、min、max。
- `truncate(length)`：length 可以是任何正数，默认模式是 `truncate(16)`，这意味着收集 null_count、min/max值，并截断长度为16。这主要是为了避免过大的列，这将增加 manifest 文件的大小。
- `counts`：仅收集 null 计数。
- `none`：禁用元数据统计收集。

统计收集器模式可以通过 `metadata.stats-mode` 进行配置，默认为 `truncate(16)`。您可以通过设置 `fields.{field_name}.stats-mode` 来配置字段级别。

对于 none 的统计模式，默认情况下 `metadata.stats-dense-store` 为 true，这将显著减少 manifest 的存储大小。但是，在读取引擎中，Paimon SDK 至少需要版本 0.9.1 或 1.0.0 或更高版本。


### 1.2 字段默认值

Paimon 表目前支持通过 `fields.item_id.default-value` 在表属性中为字段设置默认值，请注意分区字段和主键字段不能被指定。


## 2. Create Table As Select

表可以通过查询结果创建和填充，例如，我们有这样一个SQL语句：`CREATE TABLE table_b AS SELECT id, name FORM table_a`，生成的 `table_b` 表将等同于使用如下语句创建表并插入数据：
```sql
CREATE TABLE table_b (id INT, name STRING);
INSERT INTO table_b SELECT id, name FROM table_a;
```

在使用 CREATE TABLE AS SELECT 时，我们可以指定主键或分区，有关语法，请参考以下SQL。

```sql
/* For streaming mode, you need to enable the checkpoint. */

CREATE TABLE my_table (
    user_id BIGINT,
    item_id BIGINT
);
CREATE TABLE my_table_as AS SELECT * FROM my_table;

/* partitioned table */
CREATE TABLE my_table_partition (
     user_id BIGINT,
     item_id BIGINT,
     behavior STRING,
     dt STRING,
     hh STRING
) PARTITIONED BY (dt, hh);
CREATE TABLE my_table_partition_as WITH ('partition' = 'dt') AS SELECT * FROM my_table_partition;

/* change options */
CREATE TABLE my_table_options (
       user_id BIGINT,
       item_id BIGINT
) WITH ('file.format' = 'orc');
CREATE TABLE my_table_options_as WITH ('file.format' = 'parquet') AS SELECT * FROM my_table_options;

/* primary key */
CREATE TABLE my_table_pk (
      user_id BIGINT,
      item_id BIGINT,
      behavior STRING,
      dt STRING,
      hh STRING,
      PRIMARY KEY (dt, hh, user_id) NOT ENFORCED
);
CREATE TABLE my_table_pk_as WITH ('primary-key' = 'dt,hh') AS SELECT * FROM my_table_pk;


/* primary key + partition */
CREATE TABLE my_table_all (
      user_id BIGINT,
      item_id BIGINT,
      behavior STRING,
      dt STRING,
      hh STRING,
      PRIMARY KEY (dt, hh, user_id) NOT ENFORCED
) PARTITIONED BY (dt, hh);
CREATE TABLE my_table_all_as WITH ('primary-key' = 'dt,hh', 'partition' = 'dt') AS SELECT * FROM my_table_all;
```

## 3. Create Table Like

要创建一个与另一个表具有相同 Schema、分区和表属性的新表，可以使用 CREATE TABLE LIKE 语法：
```sql
CREATE TABLE my_table (
    user_id BIGINT,
    item_id BIGINT,
    behavior STRING,
    dt STRING,
    hh STRING,
    PRIMARY KEY (dt, hh, user_id) NOT ENFORCED
);

CREATE TABLE my_table_like LIKE my_table (EXCLUDING OPTIONS);
```

## 4. Work with Flink Temporary Tables

Flink 临时表仅被记录而不被当前 Flink SQL 会话管理。如果临时表被删除，其表数据不会被删除。当 Flink SQL 会话关闭时，临时表也会被删除。

如果你想在 Paimon Catalog 与其他表一起使用，但不想将它们存储在其他 Catalog 中，你可以创建一个临时表。以下 Flink SQL 创建了一个 Paimon Catalog 和一个临时表，并说明了如何一起使用这两个表:
```sql
CREATE CATALOG my_catalog WITH (
    'type' = 'paimon',
    'warehouse' = 'hdfs:///path/to/warehouse'
);

USE CATALOG my_catalog;

-- Assume that there is already a table named my_table in my_catalog

CREATE TEMPORARY TABLE temp_table (
    k INT,
    v STRING
) WITH (
    'connector' = 'filesystem',
    'path' = 'hdfs:///path/to/temp_table.csv',
    'format' = 'csv'
);

SELECT my_table.k, my_table.v, temp_table.v FROM my_table JOIN temp_table ON my_table.k = temp_table.k;
```
