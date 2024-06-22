
## 1. 简介

ClickHouse 提供了一系列用于位图索引和计算的函数，这些功能特别适用于处理大量的分布式聚合，可以高效地进行复杂的位运算。而在 Hive 中没有内置的等效函数，我们可以通过创建用户自定义函数来实现。在这我们基于 RoaringBitmap 实现了一系列的位图函数。

| 分类 | 函数名称 | 描述  |
| :------------- | :------------- | :------------- |
| 位图创建 | rbm_bitmap_from_array  | 将整数数组转化为位图 Bitmap |
| 位图创建 | rbm_group_bitmap  | 根据整数列聚合计算返回一个位图 Bitmap |
| 位图创建 | rbm_bitmap_from_str  | 将逗号分割的整数字符串转换生成一个位图 Bitmap |
| 位图创建 | rbm_bitmap_from_base64  | 将位图 Base64 字符串转换生成一个位图 Bitmap |
| 位图运算 | rbm_bitmap_and  | 计算两个位图 bitmap 的交集，返回一个新的位图 bitmap |
| 位图运算 | rbm_bitmap_or  | 计算两个位图 bitmap 的并集，并返回一个新的 bitmap |
| 位图运算 | rbm_bitmap_xor  | 两个位图 Bitmap 不重复元素所构成的集合，并返回一个新的 bitmap |
| 位图运算 | rbm_bitmap_andnot  | 计算两个位图 bitmap 的差集，并返回一个新的 bitmap |
| 位图操作 | rbm_bitmap_remove  | 删除指定的数值 |
| 位图操作 | rbm_bitmap_add  | 添加指定的数值 |
| 位图操作 | rbm_bitmap_min  | 计算位图 Bitmap 中的最小值 |
| 位图操作 | rbm_bitmap_max  | 计算位图 Bitmap 中的最大值 |
| 位图转化 | rbm_bitmap_to_array  | 将位图 bitmap 中的所有值组合成一个数组 |
| 位图转化 | rbm_bitmap_to_str  | 将位图 bitmap 中的所有值转换为一个逗号分割的字符串 |
| 位图转化 | rbm_bitmap_to_base64  | 将位图 bitmap 转换为 Base64 字符串 |
| 位图判断 | rbm_bitmap_contains  | 计算输入值是否在位图 Bitmap 中 |
| 位图判断 | rbm_bitmap_has_any  | 计算两个位图 Bitmap 是否存在相同元素 |
| 位图查询 | rbm_bitmap_subset_in_range  | 计算位图的子集，返回元素的取值需要在指定范围内，并返回一个新的位图 Bitmap |
| 位图查询 | rbm_bitmap_subset_limit  | 计算位图的子集，返回元素根据指定的起始值，从位图 Bitmap 中截取指定个数的元素，并返回一个新的位图 Bitmap |
| 位图基数 | rbm_bitmap_count  | 计算位图 bitmap 的基数，即 bitmap 中不重复值的个数 |
| 位图基数 | rbm_bitmap_and_count  | 计算两个位图 bitmap 的交集，并返回交集 bitmap 的基数 |
| 位图基数 | rbm_bitmap_or_count  | 计算两个位图 bitmap 的并集，并返回并集 bitmap 的基数 |
| 位图基数 | rbm_bitmap_xor_count  | 计算两个位图 Bitmap 的不重复元素所构成的集合，并返回新的 bitmap 的基数 |
| 位图基数 | rbm_bitmap_andnot_count  | 计算两个位图 Bitmap 的差集(存在于第一个集合但不存在于第二个集合的元素集合)，并返回新的 bitmap 的基数 |
| 位图聚合 | rbm_group_bitmap_and  | 计算位图 Bitmap 列的交集(与操作)，并返回一个新的位图 Bitmap |
| 位图聚合 | rbm_group_bitmap_or  | 计算 Bitmap 列的并集(或操作)，并返回一个新的位图 Bitmap |
| 位图聚合 | rbm_group_bitmap_xor  | 计算 Bitmap 列的不重复元素所构成的集合，并返回一个新的位图 Bitmap |

## 2. 函数介绍

为了个更好的演示函数的用途，在这我们创建了 `tag_user` 表和 `tag_bitmap` 表。`tag_user` 表包含两个字段，`tag_id` 表示分类，`user_id` 表示用户 ID：
```sql
CREATE TABLE IF NOT EXISTS tag_user (
  tag_id String COMMENT 'tag_id',
  user_id BIGINT COMMENT 'user id'
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LINES TERMINATED BY '\n';


INSERT INTO tag_user VALUES
  ('tag1', 1), ('tag1', 2), ('tag1', 1),
  ('tag1', 4),('tag1', 3), ('tag1', 3), ('tag1', 6),
  ('tag2', 1), ('tag2', 5), ('tag2', 6);
```
`tag_bitmap` 表包含三个字段，`tag_id` 表示分类，`bitmap1` 和 `bitmap2` 表示存储用户 ID 的两个位图：
```sql
DROP TABLE IF EXISTS tag_bitmap;
CREATE TABLE tag_bitmap (
    tag_id String,
    bitmap1 Binary,
    bitmap2 Binary
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LINES TERMINATED BY '\n';

INSERT INTO tag_bitmap
SELECT
    'tag1' AS tag_id,
    rbm_bitmap_from_array(
      array(1,2,3,4,5,6,7,8,9,10)
    ) AS bitmap1,
    rbm_bitmap_from_array(
      array(2,4,6,8,10,12)
    ) AS bitmap2;


INSERT INTO tag_bitmap
SELECT
  'tag2' AS tag_id,
  rbm_bitmap_from_array(
    array(6,7,8,9,10,11,12,13,14,15)
  ) AS bitmap1,
  rbm_bitmap_from_array(
    array(2,6,10,12,13,19)
  ) AS bitmap2;
```

### 2.1 创建位图

位图 Bitmap 可以用多种方式生成。下面详细介绍几种方法来生成位图。

#### 2.1.1 rbm_bitmap_from_array

可以使用 `rbm_bitmap_from_array` 方法将整数数组转化为位图 Bitmap。语法格式如下所示：
```sql
rbm_bitmap_from_array(array)
```
参数 array 表示一个整数数组。如下所示将一个数组转换为位图 Bitmap：
```sql
SELECT rbm_bitmap_from_array(array(1, 2, 3, 4, 5)) bitmap;
```

返回结果如下所示：
```sql
hive (default)> SELECT rbm_bitmap_to_str(rbm_bitmap_from_array(array(1, 2, 3, 4, 5))) bitmap;
OK
1,2,3,4,5
Time taken: 0.514 seconds, Fetched: 1 row(s)
```
> rbm_bitmap_to_str 用于将位图 Bitmap 转换为一个字符串，下面会详细介绍。

> rbm_bitmap_from_array 源码请查阅:[RbmBitmapFromArrayUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapFromArrayUDF.java)

#### 2.1.2 rbm_group_bitmap

可以通过 `rbm_group_bitmap` 聚合函数根据整数列聚合计算返回一个位图 Bitmap。语法格式如下所示：
```sql
rbm_group_bitmap(expr)
```

如下所示将 tag_user 表中的 user_id 整数列转换为位图 Bitmap 并计算用户数：
```sql
SELECT rbm_group_bitmap(user_id) AS bitmap
FROM tag_user;
```
返回结果如下所示：
```sql
hive (default)> SELECT rbm_bitmap_to_str(rbm_group_bitmap(user_id)) AS bitmap
              > FROM tag_user;
WARNING: Hive-on-MR is deprecated in Hive 2 and may not be available in the future versions. Consider using a different execution engine (i.e. spark, tez) or using Hive 1.X releases.
Query ID = wy_20240610165811_8ff82e1a-2529-4db1-93b4-0b89638167de
...
Hadoop job information for Stage-1: number of mappers: 1; number of reducers: 1
2024-06-10 16:58:20,990 Stage-1 map = 0%,  reduce = 0%
2024-06-10 16:58:26,165 Stage-1 map = 100%,  reduce = 0%
2024-06-10 16:58:32,321 Stage-1 map = 100%,  reduce = 100%
Ended Job = job_1717982783429_0008
MapReduce Jobs Launched:
Stage-Stage-1: Map: 1  Reduce: 1   HDFS Read: 8339 HDFS Write: 111 SUCCESS
Total MapReduce CPU Time Spent: 0 msec
OK
1,2,3,4,5,6
Time taken: 22.398 seconds, Fetched: 1 row(s)
```

> rbm_group_bitmap 源码请查阅:[RbmGroupBitmapUDAF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udaf/RbmGroupBitmapUDAF.java)

#### 2.1.3 rbm_bitmap_from_str

可以使用 `rbm_bitmap_from_str` 将逗号分割的整数字符串转换生成一个位图 Bitmap。语法格式如下所示：
```sql
rbm_bitmap_from_str(value)
```
参数 value 表示一个逗号分割的整数字符串。如下所示将一个逗号分割的整数字符串转换为位图 Bitmap：
```sql
SELECT rbm_bitmap_from_str('1,2,3,4,5') bitmap;
```

返回结果如下所示：
```sql
hive (default)> SELECT rbm_bitmap_to_str(rbm_bitmap_from_str('1,2,3,4,5')) bitmap;
OK
1,2,3,4,5
Time taken: 0.613 seconds, Fetched: 1 row(s)
```

> rbm_bitmap_from_str 源码请查阅:[RbmBitmapFromStringUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapFromStringUDF.java)

#### 2.1.4 rbm_bitmap_from_base64

可以使用 `rbm_bitmap_from_base64` 将位图 Base64 字符串转换生成一个位图 Bitmap。语法格式如下所示：
```sql
rbm_bitmap_from_base64(value)
```
参数 value 表示一个位图的 Base64 字符串。如下所示将一个Base64 字符串转换为位图 Bitmap：
```sql
SELECT rbm_bitmap_from_base64('AAAAAAEAAAAAOjAAAAEAAAAAAAkAEAAAAAEAAgADAAQABQAGAAcACAAJAAoA') bitmap;
```

返回结果如下所示：
```sql
hive (default)> SELECT rbm_bitmap_to_str(rbm_bitmap_from_base64('AAAAAAEAAAAAOjAAAAEAAAAAAAkAEAAAAAEAAgADAAQABQAGAAcACAAJAAoA')) bitmap;
OK
1,2,3,4,5,6,7,8,9,10
Time taken: 0.142 seconds, Fetched: 1 row(s)
```

> rbm_bitmap_from_base64 源码请查阅:[RbmBitmapFromBase64UDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapFromBase64UDF.java)

### 2.2 位图运算

位图运算函数提供了两个位图 Bitmap 之间逻辑运算(与、或、异或等)能力。

#### 2.2.1 rbm_bitmap_and

可以使用 `rbm_bitmap_and` 函数计算两个位图 bitmap 的交集，返回一个新的位图 bitmap。语法格式如下所示：
```sql
rbm_bitmap_and(bitmap,bitmap)
```

如下所示在 tag_bitmap 表中计算 bitmap1 和 bitmap2 两列对应位图 Bitmap 的交集，并返回一个新的位图 Bitmap，为了演示效果转换为一个数组展示：
```sql
SELECT tag_id, rbm_bitmap_to_array(rbm_bitmap_and(bitmap1, bitmap2)) AS res
FROM tag_bitmap;
```
返回结果如下所示：
```sql
hive (default)> SELECT tag_id, rbm_bitmap_to_array(rbm_bitmap_and(bitmap1, bitmap2)) AS res
              > FROM tag_bitmap;
OK
tag1	[2,4,6,8,10]
tag2	[6,10,12,13]
Time taken: 2.13 seconds, Fetched: 2 row(s)
```

> rbm_bitmap_and 源码请查阅:[RbmBitmapAndUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapAndUDF.java)

#### 2.2.2 rbm_bitmap_or

可以使用 `rbm_bitmap_or` 函数计算两个位图 bitmap 的并集，并返回一个新的 bitmap。语法格式如下所示：
```sql
rbm_bitmap_or(bitmap,bitmap)
```

如下所示在 tag_bitmap 表中计算 bitmap1 和 bitmap2 两列对应位图 Bitmap 的并集，并返回一个新的位图 Bitmap，为了演示效果转换为一个数组展示：
```sql
SELECT tag_id, rbm_bitmap_to_array(rbm_bitmap_or(bitmap1, bitmap2)) AS res
FROM tag_bitmap;
```
返回结果如下所示：
```sql
hive (default)> SELECT tag_id, rbm_bitmap_to_array(rbm_bitmap_or(bitmap1, bitmap2)) AS res
              > FROM tag_bitmap;
OK
tag1	[1,2,3,4,5,6,7,8,9,10,12]
tag2	[2,6,7,8,9,10,11,12,13,14,15,19]
Time taken: 0.161 seconds, Fetched: 2 row(s)
```

> rbm_bitmap_or 源码请查阅:[RbmBitmapOrUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapOrUDF.java)

#### 2.2.3 rbm_bitmap_xor

可以使用 `rbm_bitmap_xor` 函数计算两个位图 Bitmap 不重复元素所构成的集合，并返回一个新的 bitmap。语法格式如下所示：
```sql
rbm_bitmap_xor(bitmap,bitmap)
```
> 逻辑上等价于 rbm_bitmap_andnot(rbm_bitmap_or(bitmap1, bitmap2), rbm_bitmap_and(bitmap1, bitmap2))。

如下所示在 tag_bitmap 表中计算 bitmap1 和 bitmap2 两列对应位图 Bitmap 的不重复元素所构成的集合，并返回一个新的位图 Bitmap，为了演示效果转换为一个数组展示：
```sql
SELECT tag_id, rbm_bitmap_to_array(rbm_bitmap_xor(bitmap1, bitmap2)) AS res
FROM tag_bitmap;
```
返回结果如下所示：
```sql
hive (default)> SELECT tag_id, rbm_bitmap_to_array(rbm_bitmap_xor(bitmap1, bitmap2)) AS res
              > FROM tag_bitmap;
OK
tag1	[1,3,5,7,9,12]
tag2	[2,7,8,9,11,14,15,19]
Time taken: 2.499 seconds, Fetched: 2 row(s)
```

> rbm_bitmap_xor 源码请查阅:[RbmBitmapXorUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapXorUDF.java)

#### 2.2.4 rbm_bitmap_andnot

可以使用 `rbm_bitmap_andnot` 函数计算两个位图 bitmap 的差集。差集是指存在于第一个集合但不存在于第二个集合的元素集合。语法格式如下所示：
```sql
rbm_bitmap_andnot(bitmap,bitmap)
```

如下所示在 tag_bitmap 表中计算 bitmap1 和 bitmap2 两列对应位图 Bitmap 的差集，即存在于 bitmap1 但不存在于 bitmap2 的元素集合，并返回一个新的位图 Bitmap，为了演示效果转换为一个数组展示：
```sql
SELECT tag_id, rbm_bitmap_to_array(rbm_bitmap_andnot(bitmap1, bitmap2)) AS res
FROM tag_bitmap;
```
返回结果如下所示：
```sql
hive (default)> SELECT tag_id, rbm_bitmap_to_array(rbm_bitmap_andnot(bitmap1, bitmap2)) AS res
              > FROM tag_bitmap;
OK
tag1	[1,3,5,7,9]
tag2	[7,8,9,11,14,15]
Time taken: 0.156 seconds, Fetched: 2 row(s)
```

> rbm_bitmap_andnot 源码请查阅:[RbmBitmapAndNotUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapAndNotUDF.java)

### 2.3 位图操作

#### 2.3.1 rbm_bitmap_remove

可以使用 `rbm_bitmap_remove` 函数删除指定的数值。语法格式如下所示：
```sql
rbm_bitmap_remove(bitmap, value)
```
bitmap 支持的数据类型为 BINARY，value 支持的数据类型为 BIGINT，返回值的数据类型为 BINARY。

如下所示在 tag_bitmap 表中分别删除 bitmap1 和 bitmap2 位图中的元素 2，为了演示效果将返回的位图转换为一个数组输出：
```sql
SELECT
  tag_id,
  rbm_bitmap_to_array(rbm_bitmap_remove(bitmap1, 2L)) AS bitmap1,
  rbm_bitmap_to_array(rbm_bitmap_remove(bitmap2, 2L)) AS bitmap2
FROM tag_bitmap;
```
返回结果如下所示：
```sql
-- tag1	[1,2,3,4,5,6,7,8,9,10]	[2,4,6,8,10,12]
-- tag2	[6,7,8,9,10,11,12,13,14,15]	[2,6,10,12,13,19]

hive (default)> SELECT
              >   tag_id,
              >   rbm_bitmap_to_array(rbm_bitmap_remove(bitmap1, 2L)) AS bitmap1,
              >   rbm_bitmap_to_array(rbm_bitmap_remove(bitmap2, 2L)) AS bitmap2
              > FROM tag_bitmap;
OK
tag1	[1,3,4,5,6,7,8,9,10]	[4,6,8,10,12]
tag2	[6,7,8,9,10,11,12,13,14,15]	[6,10,12,13,19]
Time taken: 0.18 seconds, Fetched: 2 row(s)
```

> rbm_bitmap_remove 源码请查阅:[RbmBitmapRemoveUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapRemoveUDF.java)

#### 2.3.2 rbm_bitmap_add

可以使用 `rbm_bitmap_add` 函数添加指定的数值。语法格式如下所示：
```sql
rbm_bitmap_add(bitmap, value)
```
bitmap 支持的数据类型为 BINARY，value 支持的数据类型为 BIGINT，返回值的数据类型为 BINARY。

如下所示在 tag_bitmap 表中分别向 bitmap1 和 bitmap2 位图中的添加元素 11，为了演示效果将返回的位图转换为一个数组输出：
```sql
SELECT
  tag_id,
  rbm_bitmap_to_array(rbm_bitmap_add(bitmap1, 11L)) AS bitmap1,
  rbm_bitmap_to_array(rbm_bitmap_add(bitmap2, 11L)) AS bitmap2
FROM tag_bitmap;
```
返回结果如下所示：
```sql
-- tag1	[1,2,3,4,5,6,7,8,9,10]	[2,4,6,8,10,12]
-- tag2	[6,7,8,9,10,11,12,13,14,15]	[2,6,10,12,13,19]

hive (default)> SELECT
              >   tag_id,
              >   rbm_bitmap_to_array(rbm_bitmap_add(bitmap1, 11L)) AS bitmap1,
              >   rbm_bitmap_to_array(rbm_bitmap_add(bitmap2, 11L)) AS bitmap2
              > FROM tag_bitmap;
OK
tag1	[1,2,3,4,5,6,7,8,9,10,11]	[2,4,6,8,10,11,12]
tag2	[6,7,8,9,10,11,12,13,14,15]	[2,6,10,11,12,13,19]
Time taken: 2.228 seconds, Fetched: 2 row(s)
```

> rbm_bitmap_add 源码请查阅:[RbmBitmapAddUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapAddUDF.java)

#### 2.3.3 rbm_bitmap_min

可以使用 `rbm_bitmap_min` 函数计算位图 Bitmap 中的最小值，如果位图 Bitmap 为空则返回 -1。语法格式如下所示：
```sql
rbm_bitmap_min(bitmap)
```
bitmap 支持的数据类型为 BINARY，返回值的数据类型为 BIGINT。

如下所示在 tag_bitmap 表中分别查询 bitmap1 和 bitmap2 的最小值元素：
```sql
SELECT
  tag_id,
  rbm_bitmap_min(bitmap1) AS value1,
  rbm_bitmap_min(bitmap2) AS value2
FROM tag_bitmap;
```
返回结果如下所示：
```sql
-- tag1	[1,2,3,4,5,6,7,8,9,10]	[2,4,6,8,10,12]
-- tag2	[6,7,8,9,10,11,12,13,14,15]	[2,6,10,12,13,19]

hive (default)> SELECT
              >   tag_id,
              >   rbm_bitmap_min(bitmap1) AS value1,
              >   rbm_bitmap_min(bitmap2) AS value2
              > FROM tag_bitmap;
OK
tag1	1	2
tag2	6	2
Time taken: 2.392 seconds, Fetched: 2 row(s)
```

> rbm_bitmap_min 源码请查阅:[RbmBitmapMinUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapMinUDF.java)

#### 2.3.4 rbm_bitmap_max

可以使用 `rbm_bitmap_max` 函数计算位图 Bitmap 中的最大值，如果位图 Bitmap 为空则返回 0。语法格式如下所示：
```sql
rbm_bitmap_max(bitmap)
```
bitmap 支持的数据类型为 BINARY，返回值的数据类型为 BIGINT。

如下所示在 tag_bitmap 表中分别查询 bitmap1 和 bitmap2 的最大值元素：
```sql
SELECT
  tag_id,
  rbm_bitmap_max(bitmap1) AS value1,
  rbm_bitmap_max(bitmap2) AS value2
FROM tag_bitmap;
```
返回结果如下所示：
```sql
-- tag1	[1,2,3,4,5,6,7,8,9,10]	[2,4,6,8,10,12]
-- tag2	[6,7,8,9,10,11,12,13,14,15]	[2,6,10,12,13,19]

hive (default)> SELECT
              >   tag_id,
              >   rbm_bitmap_max(bitmap1) AS value1,
              >   rbm_bitmap_max(bitmap2) AS value2
              > FROM tag_bitmap;
OK
tag1	10	12
tag2	15	19
Time taken: 1.688 seconds, Fetched: 2 row(s)
```

> rbm_bitmap_max 源码请查阅:[RbmBitmapMaxUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapMaxUDF.java)

### 2.4 位图转化

#### 2.4.1 rbm_bitmap_to_array

可以使用 `rbm_bitmap_to_array` 函数将位图 bitmap 中的所有值组合成一个数组。语法格式如下所示：
```sql
rbm_bitmap_to_array (bitmap)
```
bitmap 支持的数据类型为 BINARY，返回值的数据类型为一个 BIGINT 数组。

如下所示在 tag_bitmap 表中分别将 bitmap1 和 bitmap2 列对应的位图 bitmap 转换为一个数组：
```sql
SELECT
  tag_id,
  rbm_bitmap_to_array(bitmap1),
  rbm_bitmap_to_array(bitmap2)
FROM tag_bitmap;
```
返回结果如下所示：
```sql
hive (default)> SELECT
              >   tag_id,
              >   rbm_bitmap_to_array(bitmap1),
              >   rbm_bitmap_to_array(bitmap2)
              > FROM tag_bitmap;
OK
tag1	[1,2,3,4,5,6,7,8,9,10]	[2,4,6,8,10,12]
tag2	[6,7,8,9,10,11,12,13,14,15]	[2,6,10,12,13,19]
Time taken: 0.377 seconds, Fetched: 2 row(s)
```

> rbm_bitmap_to_array 源码请查阅:[RbmBitmapToArrayUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapToArrayUDF.java)

#### 2.4.2 rbm_bitmap_to_str

可以使用 `rbm_bitmap_to_str` 函数将位图 bitmap 中的所有值转换为一个逗号分割的字符串。语法格式如下所示：
```sql
rbm_bitmap_to_str(bitmap)
```
bitmap 支持的数据类型为 BINARY，返回值的数据类型为 STRING。

如下所示在 tag_bitmap 表中分别将 bitmap1 和 bitmap2 列对应的位图 bitmap 转换为一个字符串：
```sql
SELECT
  tag_id,
  rbm_bitmap_to_str(bitmap1) AS value1,
  rbm_bitmap_to_str(bitmap2) AS value2
FROM tag_bitmap;
```
返回结果如下所示：
```sql
hive (default)> SELECT
              >   tag_id,
              >   rbm_bitmap_to_str(bitmap1) AS value1,
              >   rbm_bitmap_to_str(bitmap2) AS value2
              > FROM tag_bitmap;
OK
tag1	1,2,3,4,5,6,7,8,9,10	2,4,6,8,10,12
tag2	6,7,8,9,10,11,12,13,14,15	2,6,10,12,13,19
Time taken: 0.15 seconds, Fetched: 2 row(s)
```

> rbm_bitmap_to_str 源码请查阅:[RbmBitmapToStringUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapToStringUDF.java)

#### 2.4.3 rbm_bitmap_to_base64

可以使用 `rbm_bitmap_to_base64` 函数将位图 bitmap 转换为 Base64 字符串。语法格式如下所示：
```sql
rbm_bitmap_to_base64(bitmap)
```
bitmap 支持的数据类型为 BINARY，返回值的数据类型为 STRING。

如下所示在 tag_bitmap 表中分别将 bitmap1 和 bitmap2 列对应的位图 bitmap 转换为 Base64 字符串：
```sql
SELECT
  tag_id,
  rbm_bitmap_to_base64(bitmap1) AS value1,
  rbm_bitmap_to_base64(bitmap2) AS value2
FROM tag_bitmap;
```
返回结果如下所示：
```sql
hive (default)> SELECT
              >   tag_id,
              >   rbm_bitmap_to_base64(bitmap1) AS value1,
              >   rbm_bitmap_to_base64(bitmap2) AS value2
              > FROM tag_bitmap;
OK
tag1	AAAAAAEAAAAAOjAAAAEAAAAAAAkAEAAAAAEAAgADAAQABQAGAAcACAAJAAoA	AAAAAAEAAAAAOjAAAAEAAAAAAAUAEAAAAAIABAAGAAgACgAMAA==
tag2	AAAAAAEAAAAAOjAAAAEAAAAAAAkAEAAAAAYABwAIAAkACgALAAwADQAOAA8A	AAAAAAEAAAAAOjAAAAEAAAAAAAUAEAAAAAIABgAKAAwADQATAA==
Time taken: 0.166 seconds, Fetched: 2 row(s)
```

> rbm_bitmap_to_base64 源码请查阅:[RbmBitmapToBase64UDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapToBase64UDF.java)

### 2.5 位图判断

#### 2.5.1 rbm_bitmap_contains

可以使用 `rbm_bitmap_contains` 函数计算输入值是否在位图 Bitmap 中。语法格式如下所示：
```sql
bitmapContains(bitmap, value)
```
bitmap 支持的数据类型为 BINARY，value 支持的数据类型为 BIGINT，返回值的数据类型为 BOOLEAN。

如下所示在 tag_bitmap 表中查询元素 `5` 是否在 bitmap1 位图中：
```sql
SELECT
  tag_id,
  rbm_bitmap_contains(bitmap1, 5L) AS res
FROM tag_bitmap;
```
返回结果如下所示：
```sql
-- tag1	[1,2,3,4,5,6,7,8,9,10]
-- tag2	[6,7,8,9,10,11,12,13,14,15]

hive (default)> SELECT
              >   tag_id,
              >   rbm_bitmap_contains(bitmap1, 5L) AS res
              > FROM tag_bitmap;
OK
tag1	true
tag2	false
Time taken: 0.173 seconds, Fetched: 2 row(s)
```

> rbm_bitmap_contains 源码请查阅:[RbmBitmapContainsUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapContainsUDF.java)

#### 2.5.2 rbm_bitmap_has_any

可以使用 `rbm_bitmap_has_any` 函数计算两个位图 Bitmap 是否存在相同元素。语法格式如下所示：
```sql
rbm_bitmap_has_any(bitmap1, bitmap2)
```
bitmap1、bitmap2 支持的数据类型为 BINARY，返回值的数据类型为 BOOLEAN。

> 两个 Bitmap 重叠的相同元素可以通过 rbm_bitmap_and(bitmap1, bitmap2) 函数查看。如果 bitmap2 只包含一个元素，考虑使用 rbm_bitmap_contains，因为它更有效。

如下所示在 tag_bitmap 表中查询 bitmap1 和 bitmap2 是否存在相同的元素：
```sql
SELECT
  tag_id,
  rbm_bitmap_has_any(bitmap1, bitmap2) AS res
FROM tag_bitmap;
```
返回结果如下所示：
```sql
-- tag1	[1,2,3,4,5,6,7,8,9,10]	[2,4,6,8,10,12]
-- tag2	[6,7,8,9,10,11,12,13,14,15]	[2,6,10,12,13,19]

hive (default)> SELECT
              >   tag_id,
              >   rbm_bitmap_has_any(bitmap1, bitmap2) AS res
              > FROM tag_bitmap;
OK
tag1	true
tag2	true
Time taken: 0.129 seconds, Fetched: 2 row(s)
```

> rbm_bitmap_has_any 源码请查阅:[RbmBitmapHasAnyUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapHasAnyUDF.java)

### 2.6 位图查询

#### 2.6.1 rbm_bitmap_subset_in_range

可以使用 `rbm_bitmap_subset_in_range` 函数计算位图的子集，返回元素的取值需要在指定范围内，并返回一个新的位图 Bitmap。语法格式如下所示：
```sql
rbm_bitmap_subset_in_range(bitmap, range_start, range_end)
```
bitmap 为要截取的目标 bitmap，支持的数据类型为 BINARY；range_start 用于指定范围的起始值，支持的数据类型为 BIGINT；range_end 用于指定范围的结束值，支持的数据类型为 BIGINT；返回值的数据类型为 BINARY。

如下所示在 tag_bitmap 表计算位图 bitmap1 中取值在 `[1,4)` 之间的元素，并返回一个新的位图 Bitmap，为了演示效果将返回的位图转换为一个数组输出：
```sql
SELECT
  tag_id,
  rbm_bitmap_to_array(bitmap1) AS sub_bitmap,
  rbm_bitmap_to_array(rbm_bitmap_subset_in_range(bitmap1, 1L, 4L)) AS sub_bitmap
FROM tag_bitmap;
```
返回结果如下所示：
```sql
-- tag1	[1,2,3,4,5,6,7,8,9,10]	[2,4,6,8,10,12]
-- tag2	[6,7,8,9,10,11,12,13,14,15]	[2,6,10,12,13,19]

hive (default)> SELECT
              >   tag_id,
              >   rbm_bitmap_to_array(bitmap1) AS sub_bitmap,
              >   rbm_bitmap_to_array(rbm_bitmap_subset_in_range(bitmap1, 1L, 4L)) AS sub_bitmap
              > FROM tag_bitmap;
OK
tag1	[1,2,3,4,5,6,7,8,9,10]	[1,2,3]
tag2	[6,7,8,9,10,11,12,13,14,15]	[]
```

> rbm_bitmap_subset_in_range 源码请查阅:[RbmBitmapSubsetInRangeUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapSubsetInRangeUDF.java)

#### 2.6.2 rbm_bitmap_subset_limit

可以使用 `rbm_bitmap_subset_limit` 函数计算位图的子集，返回元素根据指定的起始值，从位图 Bitmap 中截取指定个数的元素，并返回一个新的位图 Bitmap。语法格式如下所示：
```sql
rbm_bitmap_subset_limit(bitmap, range_start, cardinality_limit)
```
bitmap 为要截取的目标 bitmap，支持的数据类型为 BINARY；range_start 用于指定范围的起始值，支持的数据类型为 BIGINT；cardinality_limit 从 range_start 开始，要截取的元素个数，支持的数据类型为 BIGINT。返回值的数据类型为 BINARY。

如下所示在 tag_bitmap 表中计算位图 bitmap1 以 9 作为起始值截取 4 个元素，并返回一个新的位图 Bitmap，为了演示效果将返回的位图转换为一个数组输出：
```sql
SELECT
  tag_id,
  rbm_bitmap_to_array(bitmap1) AS bitmap,
  rbm_bitmap_to_array(rbm_bitmap_subset_limit(bitmap1, 9L, 4L)) AS sub_bitmap
FROM tag_bitmap;
```
返回结果如下所示：
```sql
-- tag1	[1,2,3,4,5,6,7,8,9,10]	[2,4,6,8,10,12]
-- tag2	[6,7,8,9,10,11,12,13,14,15]	[2,6,10,12,13,19]

hive (default)> SELECT
              >   tag_id,
              >   rbm_bitmap_to_array(bitmap1) AS bitmap,
              >   rbm_bitmap_to_array(rbm_bitmap_subset_limit(bitmap1, 9L, 4L)) AS sub_bitmap
              > FROM tag_bitmap;
OK
tag1	[1,2,3,4,5,6,7,8,9,10]	[9,10]
tag2	[6,7,8,9,10,11,12,13,14,15]	[9,10,11,12]
Time taken: 0.189 seconds, Fetched: 2 row(s)
```

> rbm_bitmap_subset_limit 源码请查阅:[RbmBitmapSubsetLimitUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapSubsetLimitUDF.java)

### 2.7 位图基数

#### 2.7.1 rbm_bitmap_count

可以使用 `rbm_bitmap_count` 函数计算位图 bitmap 的基数，即 bitmap 中不重复值的个数。语法格式如下所示：
```sql
rbm_bitmap_count(bitmap)
```
bitmap 支持的数据类型为 BINARY，返回值的数据类型为 BIGINT。

如下所示在 tag_bitmap 表中分别计算 bitmap1、bitmap2 列对应位图 bitmap 中不重复值的个数：
```sql
SELECT
  tag_id,
  rbm_bitmap_count(bitmap1) AS uv1,
  rbm_bitmap_count(bitmap2) AS uv2
FROM tag_bitmap;
```
返回结果如下所示：
```sql
-- tag1	[1,2,3,4,5,6,7,8,9,10]	[2,4,6,8,10,12]
-- tag2	[6,7,8,9,10,11,12,13,14,15]	[2,6,10,12,13,19]

hive (default)> SELECT
              >   tag_id,
              >   rbm_bitmap_count(bitmap1) AS uv1,
              >   rbm_bitmap_count(bitmap2) AS uv2
              > FROM tag_bitmap;
OK
tag1	10	6
tag2	10	6
Time taken: 0.136 seconds, Fetched: 2 row(s)
```

> rbm_bitmap_count 源码请查阅:[RbmBitmapCardinalityUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapCardinalityUDF.java)

#### 2.7.2 rbm_bitmap_and_count

可以使用 `rbm_bitmap_and_count` 函数来计算两个位图 bitmap 的交集，并返回交集 bitmap 的基数。语法格式如下所示：
```sql
rbm_bitmap_and_count(bitmap1, bitmap2)
```
bitmap1、bitmap2 支持的数据类型为 BINARY，返回值的数据类型为 BIGINT。

如下所示在 tag_bitmap 表计算 bitmap1、bitmap2 列对应位图 bitmap 交集的基数：
```sql
SELECT
  tag_id,
  rbm_bitmap_to_array(rbm_bitmap_and(bitmap1, bitmap2)) AS bitmap,
  rbm_bitmap_and_count(bitmap1, bitmap2) AS uv
FROM tag_bitmap;
```
返回结果如下所示：
```sql
-- tag1	[1,2,3,4,5,6,7,8,9,10]	[2,4,6,8,10,12]
-- tag2	[6,7,8,9,10,11,12,13,14,15]	[2,6,10,12,13,19]

hive (default)> SELECT
              >   tag_id,
              >   rbm_bitmap_to_array(rbm_bitmap_and(bitmap1, bitmap2)) AS bitmap,
              >   rbm_bitmap_and_count(bitmap1, bitmap2) AS uv
              > FROM tag_bitmap;
OK
tag1	[2,4,6,8,10]	5
tag2	[6,10,12,13]	4
Time taken: 0.163 seconds, Fetched: 2 row(s)
```

> rbm_bitmap_and_count 源码请查阅:[RbmBitmapAndCardinalityUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapAndCardinalityUDF.java)

#### 2.7.3 rbm_bitmap_or_count

可以使用 `rbm_bitmap_or_count` 函数来计算两个位图 bitmap 的并集，并返回并集 bitmap 的基数。语法格式如下所示：
```sql
rbm_bitmap_or_count(bitmap1, bitmap2)
```
bitmap1、bitmap2 支持的数据类型为 BINARY，返回值的数据类型为 BIGINT。

如下所示在 tag_bitmap 表计算 bitmap1、bitmap2 列对应位图 bitmap 并集的基数：
```sql
SELECT
  tag_id,
  rbm_bitmap_to_array(rbm_bitmap_or(bitmap1, bitmap2)) AS bitmap,
  rbm_bitmap_or_count(bitmap1, bitmap2) AS uv
FROM tag_bitmap;
```
返回结果如下所示：
```sql
-- tag1	[1,2,3,4,5,6,7,8,9,10]	[2,4,6,8,10,12]
-- tag2	[6,7,8,9,10,11,12,13,14,15]	[2,6,10,12,13,19]

hive (default)> SELECT
              >   tag_id,
              >   rbm_bitmap_to_array(rbm_bitmap_or(bitmap1, bitmap2)) AS bitmap,
              >   rbm_bitmap_or_count(bitmap1, bitmap2) AS uv
              > FROM tag_bitmap;
OK
tag1	[1,2,3,4,5,6,7,8,9,10,12]	11
tag2	[2,6,7,8,9,10,11,12,13,14,15,19]	12
Time taken: 0.138 seconds, Fetched: 2 row(s)
```

> rbm_bitmap_or_count 源码请查阅:[RbmBitmapOrCardinalityUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapOrCardinalityUDF.java)

#### 2.7.4 rbm_bitmap_xor_count

可以使用 `rbm_bitmap_xor_count` 函数计算两个位图 Bitmap 的不重复元素所构成的集合，并返回新的 bitmap 的基数。语法格式如下所示：
```sql
rbm_bitmap_xor_count(bitmap1, bitmap2)
```
bitmap1、bitmap2 支持的数据类型为 BINARY，返回值的数据类型为 BIGINT。

如下所示在 tag_bitmap 表计算 bitmap1、bitmap2 列对应位图 bitmap 不重复元素所构成的集合的基数：
```sql
SELECT
  tag_id,
  rbm_bitmap_to_array(rbm_bitmap_xor(bitmap1, bitmap2)) AS bitmap,
  rbm_bitmap_xor_count(bitmap1, bitmap2) AS uv
FROM tag_bitmap;
```
返回结果如下所示：
```sql
-- tag1	[1,2,3,4,5,6,7,8,9,10]	[2,4,6,8,10,12]
-- tag2	[6,7,8,9,10,11,12,13,14,15]	[2,6,10,12,13,19]

hive (default)> SELECT
              >   tag_id,
              >   rbm_bitmap_to_array(rbm_bitmap_xor(bitmap1, bitmap2)) AS bitmap,
              >   rbm_bitmap_xor_count(bitmap1, bitmap2) AS uv
              > FROM tag_bitmap;
OK
tag1	[1,3,5,7,9,12]	6
tag2	[2,7,8,9,11,14,15,19]	8
Time taken: 0.145 seconds, Fetched: 2 row(s)
```

> rbm_bitmap_xor_count 源码请查阅:[RbmBitmapXorCardinalityUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapXorCardinalityUDF.java)

#### 2.7.5 rbm_bitmap_andnot_count

可以使用 `rbm_bitmap_andnot_count` 函数计算两个位图 Bitmap 的差集(存在于第一个集合但不存在于第二个集合的元素集合)，并返回新的 bitmap 的基数。语法格式如下所示：
```sql
rbm_bitmap_andnot_count(bitmap1, bitmap2)
```
bitmap1、bitmap2 支持的数据类型为 BINARY，返回值的数据类型为 BIGINT。

如下所示在 tag_bitmap 表中计算 bitmap1、bitmap2 列对应位图 bitmap 差集的基数：
```sql
SELECT
  tag_id,
  rbm_bitmap_to_array(rbm_bitmap_andnot(bitmap1, bitmap2)) AS bitmap,
  rbm_bitmap_andnot_count(bitmap1, bitmap2) AS uv
FROM tag_bitmap;
```
返回结果如下所示：
```sql
-- tag1	[1,2,3,4,5,6,7,8,9,10]	[2,4,6,8,10,12]
-- tag2	[6,7,8,9,10,11,12,13,14,15]	[2,6,10,12,13,19]

hive (default)>
              > SELECT
              >   tag_id,
              >   rbm_bitmap_to_array(rbm_bitmap_andnot(bitmap1, bitmap2)) AS bitmap,
              >   rbm_bitmap_andnot_count(bitmap1, bitmap2) AS uv
              > FROM tag_bitmap;
OK
tag1	[1,3,5,7,9]	5
tag2	[7,8,9,11,14,15]	6
Time taken: 0.132 seconds, Fetched: 2 row(s)
```

> rbm_bitmap_andnot_count 源码请查阅:[RbmBitmapAndNotCardinalityUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udf/RbmBitmapAndNotCardinalityUDF.java)

### 2.8 位图聚合

#### 2.8.1 rbm_group_bitmap_and

可以使用 `rbm_group_bitmap_and` 函数计算位图 Bitmap 列的交集(与操作)，并返回一个新的位图 Bitmap。语法格式如下所示：
```sql
rbm_group_bitmap_and(expr)
```

如下所示在 tag_bitmap 表中分别聚合 bitmap1 列和 bitmap2 列计算多行位图 Bitmap 的交集，并返回一个新的位图 Bitmap，为了演示效果转换为一个数组展示：
```sql
SELECT
  rbm_bitmap_to_array(rbm_group_bitmap_and(bitmap1)) AS bitmap1,
  rbm_bitmap_to_array(rbm_group_bitmap_and(bitmap2)) AS bitmap2
FROM tag_bitmap;
```
返回结果如下所示：
```sql
-- tag1	[1,2,3,4,5,6,7,8,9,10]	[2,4,6,8,10,12]
-- tag2	[6,7,8,9,10,11,12,13,14,15]	[2,6,10,12,13,19]

hive (default)> SELECT
              >   rbm_bitmap_to_array(rbm_group_bitmap_and(bitmap1)) AS bitmap1,
              >   rbm_bitmap_to_array(rbm_group_bitmap_and(bitmap2)) AS bitmap2
              > FROM tag_bitmap;
Query ID = wy_20240614072629_0191f8a3-cf55-4241-a10b-f1059ea724eb
...
2024-06-14 07:26:38,465 Stage-1 map = 0%,  reduce = 0%
2024-06-14 07:26:43,615 Stage-1 map = 100%,  reduce = 0%
2024-06-14 07:26:49,780 Stage-1 map = 100%,  reduce = 100%
Ended Job = job_1718319584733_0004
MapReduce Jobs Launched:
Stage-Stage-1: Map: 1  Reduce: 1   HDFS Read: 9629 HDFS Write: 120 SUCCESS
Total MapReduce CPU Time Spent: 0 msec
OK
[6,7,8,9,10]	[2,6,10,12]
Time taken: 21.043 seconds, Fetched: 1 row(s)
```

> rbm_group_bitmap_and 源码请查阅:[RbmGroupBitmapAndUDF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udaf/RbmGroupBitmapAndUDF.java)

#### 2.8.2 rbm_group_bitmap_or

可以使用 `rbm_group_bitmap_or` 函数计算 Bitmap 列的并集(或操作)，并返回一个新的位图 Bitmap。语法格式如下所示：
```sql
rbm_group_bitmap_or(expr)
```

如下所示在 tag_bitmap 表中分别聚合 bitmap1 列和 bitmap2 列计算多行位图 Bitmap 的并集，并返回一个新的位图 Bitmap，为了演示效果转换为一个数组展示：
```sql
SELECT
  rbm_bitmap_to_array(rbm_group_bitmap_or(bitmap1)) AS bitmap1,
  rbm_bitmap_to_array(rbm_group_bitmap_or(bitmap2)) AS bitmap2
FROM tag_bitmap;
```
返回结果如下所示：
```sql
-- tag1	[1,2,3,4,5,6,7,8,9,10]	[2,4,6,8,10,12]
-- tag2	[6,7,8,9,10,11,12,13,14,15]	[2,6,10,12,13,19]

hive (default)> SELECT
              >   rbm_bitmap_to_array(rbm_group_bitmap_or(bitmap1)) AS bitmap1,
              >   rbm_bitmap_to_array(rbm_group_bitmap_or(bitmap2)) AS bitmap2
              > FROM tag_bitmap;
Query ID = wy_20240615083141_d7f91439-a1e9-44fc-8ba1-a10e21b6d30f
...
2024-06-15 08:31:50,694 Stage-1 map = 0%,  reduce = 0%
2024-06-15 08:31:55,832 Stage-1 map = 100%,  reduce = 0%
2024-06-15 08:32:02,004 Stage-1 map = 100%,  reduce = 100%
Ended Job = job_1718410798345_0002
MapReduce Jobs Launched:
Stage-Stage-1: Map: 1  Reduce: 1   HDFS Read: 9588 HDFS Write: 155 SUCCESS
Total MapReduce CPU Time Spent: 0 msec
OK
[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]	[2,4,6,8,10,12,13,19]
Time taken: 21.672 seconds, Fetched: 1 row(s)
```

> rbm_group_bitmap_or 源码请查阅:[RbmGroupBitmapOrUDAF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udaf/RbmGroupBitmapOrUDAF.java)

#### 2.8.3 rbm_group_bitmap_xor

可以使用 `rbm_group_bitmap_xor` 函数计算 Bitmap 列的不重复元素所构成的集合，并返回一个新的位图 Bitmap。语法格式如下所示：
```sql
rbm_group_bitmap_xor(expr)
```

如下所示在 tag_bitmap 表中分别聚合 bitmap1 列和 bitmap2 列计算多行位图 Bitmap 的不重复元素所构成的集合，并返回一个新的位图 Bitmap，为了演示效果转换为一个数组展示：
```sql
SELECT
  rbm_bitmap_to_array(rbm_group_bitmap_xor(bitmap1)) AS bitmap1,
  rbm_bitmap_to_array(rbm_group_bitmap_xor(bitmap2)) AS bitmap2
FROM tag_bitmap;
```
返回结果如下所示：
```sql
-- tag1	[1,2,3,4,5,6,7,8,9,10]	[2,4,6,8,10,12]
-- tag2	[6,7,8,9,10,11,12,13,14,15]	[2,6,10,12,13,19]

hive (default)> SELECT
              >   rbm_bitmap_to_array(rbm_group_bitmap_xor(bitmap1)) AS bitmap1,
              >   rbm_bitmap_to_array(rbm_group_bitmap_xor(bitmap2)) AS bitmap2
              > FROM tag_bitmap;
Query ID = wy_20240615082744_a33657d3-316f-4d96-8568-2c47b64c55fc
...
2024-06-15 08:27:57,056 Stage-1 map = 0%,  reduce = 0%
2024-06-15 08:28:02,236 Stage-1 map = 100%,  reduce = 0%
2024-06-15 08:28:09,443 Stage-1 map = 100%,  reduce = 100%
Ended Job = job_1718410798345_0001
MapReduce Jobs Launched:
Stage-Stage-1: Map: 1  Reduce: 1   HDFS Read: 9633 HDFS Write: 134 SUCCESS
Total MapReduce CPU Time Spent: 0 msec
OK
[1,2,3,4,5,11,12,13,14,15]	[4,8,13,19]
Time taken: 26.374 seconds, Fetched: 1 row(s)
```

> rbm_group_bitmap_xor 源码请查阅:[RbmGroupBitmapXorUDAF](https://github.com/sjf0115/data-market/blob/main/hive-market/src/main/java/com/data/market/udaf/RbmGroupBitmapXorUDAF.java)
