
## 1. 简介

ClickHouse 是一个用于联机分析(OLAP)的列式数据库管理系统(DBMS)。在处理大规模数据分析时，它提供了一个高性能的解决方案。ClickHouse 提供了一系列用于位图索引和计算的函数，这些功能特别适用于处理大量的分布式聚合。位图通常用于高效地表示一组元素的存在情况，例如，记录用户的行为或者在集合运算中快速确定唯一值等场景。

## 2. 函数

为了个更好的演示函数的用途，在这我们创建了 `tag_user` 表和 `tag_bitmap` 表。`tag_user` 表包含两个字段，`tag_id` 表示分类，`user_id` 表示用户 ID：
```sql
DROP TABLE IF EXISTS tag_user;
CREATE TABLE tag_user (
    tag_id String,
    user_id UInt32
)
ENGINE = MergeTree
ORDER BY user_id;

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
    bitmap1 AggregateFunction(groupBitmap, UInt32),
    bitmap2 AggregateFunction(groupBitmap, UInt32)
)
ENGINE = MergeTree
ORDER BY tag_id;

INSERT INTO tag_bitmap VALUES (
  'tag1',
  bitmapBuild(
    cast([1,2,3,4,5,6,7,8,9,10] as Array(UInt32))
  ),
  bitmapBuild(
    cast([2,4,6,8,10,12] as Array(UInt32))
  )
);

INSERT INTO tag_bitmap VALUES (
  'tag2',
  bitmapBuild(
    cast([6,7,8,9,10,11,12,13,14,15] as Array(UInt32))
  ),
  bitmapBuild(
    cast([2,6,10,12,13,19] as Array(UInt32))
  )
);
```

### 2.1 创建位图

位图 Bitmap 可以用两种方式生成。第一种方法是从 Array 对象生成，另一种方法是通过带 `State` 后缀的聚合函数 groupBitmap 构造。

#### 2.1.1 bitmapBuild

第一种方法是从 Array 对象生成位图，可以使用 `bitmapBuild` 方法将无符号整数数组转化为位图。语法格式如下所示：
```sql
bitmapBuild(array)
```
参数 array 表示一个无符号整数数组。如下所示将一个数组转换为位图 Bitmap：
```sql
SELECT bitmapBuild([1, 2, 3, 4, 5]) AS res, toTypeName(res) AS type
```
返回结果如下所示：
```sql
Query id: d63558e0-d3a4-40a3-83bd-e1b1e818f24d

┌─res─┬─type──────────────────────────────────┐
│     │ AggregateFunction(groupBitmap, UInt8) │
└─────┴───────────────────────────────────────┘

1 row in set. Elapsed: 0.001 sec.
```

#### 2.1.2 groupBitmapState

另一种方法是通过带 `State` 后缀的聚合函数 groupBitmap 生成，根据无符号整数列聚合计算返回一个位图 Bitmap。语法格式如下所示：
```sql
groupBitmapState(expr)
```
> 需要注意的是如果不带 `State` 后缀返回的是 UInt64 类型的位图基数。

expr 表示一个结果为 `UInt*` 类型的表达式。

如下所示将 tag_user 表中的 user_id 整数列转换为位图 Bitmap 并计算用户数：
```sql
SELECT groupBitmapState(user_id) AS bitmap, groupBitmap(user_id) AS uv, toTypeName(bitmap) AS type
FROM tag_user;
```
返回结果如下所示：
```sql
Query id: 9ec78329-a718-483d-972b-1636c798360f

┌─bitmap─┬─uv─┬─type───────────────────────────────────┐
│        │  6 │ AggregateFunction(groupBitmap, UInt32) │
└────────┴────┴────────────────────────────────────────┘

1 row in set. Elapsed: 0.011 sec.
```

### 2.2 位图运算

ClickHouse 提供了两个位图之间逻辑运算(与、或、异或等)能力。

#### 2.2.1 bitmapAnd

可以使用 `bitmapAnd` 函数计算两个 bitmap 的交集，返回新的 bitmap。语法格式如下所示：
```sql
bitmapAnd(bitmap,bitmap)
```

```sql
SELECT tag_id, bitmapToArray(bitmapAnd(bitmap1, bitmap2)) AS res
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: 0d5e844d-cb14-4593-9d04-24204e66bb34

┌─tag_id─┬─res──────────┐
│ tag2   │ [6,10,12,13] │
└────────┴──────────────┘
┌─tag_id─┬─res──────────┐
│ tag1   │ [2,4,6,8,10] │
└────────┴──────────────┘

2 rows in set. Elapsed: 0.005 sec.
```

#### 2.2.2 bitmapOr

可以使用 `bitmapOr` 函数计算两个 bitmpa 的并集，并返回新的 bitmap。语法格式如下所示：
```sql
bitmapOr(bitmap,bitmap)
```

```sql
SELECT tag_id, bitmapToArray(bitmapOr(bitmap1, bitmap2)) AS res
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: c5a30498-dc97-40ae-b5fa-d1c674d311b9

┌─tag_id─┬─res──────────────────────────────┐
│ tag2   │ [6,7,8,9,10,11,12,13,14,15,2,19] │
└────────┴──────────────────────────────────┘
┌─tag_id─┬─res───────────────────────┐
│ tag1   │ [1,2,3,4,5,6,7,8,9,10,12] │
└────────┴───────────────────────────┘

2 rows in set. Elapsed: 0.009 sec.
```
#### 2.2.3 bitmapXor

可以使用 `bitmapXor` 函数计算两个 Bitmap 的补集(不重复元素所构成的集合)，并返回新的 bitmap。语法格式如下所示：
```sql
bitmapXor(bitmap,bitmap)
```
> 逻辑上等价于 bitmapAndnot(bitmapOr(bitmap1, bitmap2), bitmapAnd(bitmap1, bitmap2))。


```sql
SELECT tag_id, bitmapToArray(bitmapXor(bitmap1, bitmap2)) AS res
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: 4f2b8842-f482-4e47-8d26-b9573b12fea6

┌─tag_id─┬─res───────────────────┐
│ tag2   │ [2,7,8,9,11,14,15,19] │
└────────┴───────────────────────┘
┌─tag_id─┬─res────────────┐
│ tag1   │ [1,3,5,7,9,12] │
└────────┴────────────────┘

2 rows in set. Elapsed: 0.012 sec.
```

#### 2.2.4 bitmapAndnot

可以使用 `bitmapAndnot` 函数计算两个 bitmap 的差集。差集是指存在于第一个集合但不存在于第二个集合的元素集合。语法格式如下所示：
```sql
SELECT tag_id, bitmapToArray(bitmapAndnot(bitmap1, bitmap2)) AS res
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: 3d57782c-afc3-4453-bea1-de9620fd1b81

┌─tag_id─┬─res──────────────┐
│ tag2   │ [7,8,9,11,14,15] │
└────────┴──────────────────┘
┌─tag_id─┬─res─────────┐
│ tag1   │ [1,3,5,7,9] │
└────────┴─────────────┘

2 rows in set. Elapsed: 0.030 sec.
```

### 2.3 位图转化

#### 2.3.1 bitmapToArray

可以使用 `bitmapToArray` 函数将 bitmap 中的所有值组合成 BIGINT 类型的数组。语法格式如下所示：
```sql
`ARRAY<BIGINT>` bitmapToArray (bitmap)
```

如下所示分别将 tag_bitmap 表中的 bitmap1 和 bitmap2 字段的 bitmap 转换为一个 BIGINT 类型的数组：
```sql
SELECT tag_id, bitmapToArray(bitmap1), bitmapToArray(bitmap2)
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: 9e2f8c3a-a5be-41a3-825a-d37a6d53f0bc

┌─tag_id─┬─bitmapToArray(bitmap1)──────┬─bitmapToArray(bitmap2)─┐
│ tag2   │ [6,7,8,9,10,11,12,13,14,15] │ [2,6,10,12,13,19]      │
└────────┴─────────────────────────────┴────────────────────────┘
┌─tag_id─┬─bitmapToArray(bitmap1)─┬─bitmapToArray(bitmap2)─┐
│ tag1   │ [1,2,3,4,5,6,7,8,9,10] │ [2,4,6,8,10,12]        │
└────────┴────────────────────────┴────────────────────────┘

2 rows in set. Elapsed: 0.009 sec.
```

### 2.4 位图基数

#### 2.4.1 bitmapCardinality

可以使用 `bitmapCardinality` 函数来计算 bitmap 的基数，即 bitmap 中不重复值的个数。语法格式如下所示：
```sql
UInt64 bitmapCardinality(bitmap)
```
如下所示分别计算 tag_bitmap 表中 bitmap1、bitmap2 字段的 bitmap 中不重复值的个数：
```sql
SELECT tag_id, bitmapCardinality(bitmap1) AS uv1, bitmapCardinality(bitmap2) AS uv2
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: 3b98408b-053c-48e6-ab9c-3f1c87b56f32

┌─tag_id─┬─uv1─┬─uv2─┐
│ tag1   │  10 │   6 │
│ tag2   │  10 │   6 │
└────────┴─────┴─────┘

2 rows in set. Elapsed: 0.005 sec.
```

#### 2.4.2 bitmapAndCardinality

可以使用 `bitmapAndCardinality` 函数来计算两个 bitmap 的交集，并返回新的 bitmap 的基数。语法格式如下所示：
```sql
UInt64 bitmapAndCardinality(bitmap,bitmap)
```
如下所示计算 tag_bitmap 表中 bitmap1 和 bitmap2 交集的基数：
```sql
SELECT tag_id, bitmapAndCardinality(bitmap1, bitmap2) AS uv, toTypeName(uv) AS type
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: 10cb1148-e858-495e-b11f-8458ae371442

┌─tag_id─┬─uv─┬─type───┐
│ tag1   │  5 │ UInt64 │
│ tag2   │  4 │ UInt64 │
└────────┴────┴────────┘

2 rows in set. Elapsed: 0.009 sec.
```

#### 2.4.3 bitmapOrCardinality

可以使用 `bitmapOrCardinality` 函数来计算两个 bitmap 的并集，并返回新的 bitmap 的基数。语法格式如下所示：
```sql
UInt64 bitmapOrCardinality(bitmap,bitmap)
```
如下所示计算 tag_bitmap 表中 bitmap1 和 bitmap2 并集的基数：
```sql
SELECT tag_id, bitmapOrCardinality(bitmap1, bitmap2) AS uv, toTypeName(uv) AS type
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: fe6405ab-f451-4395-a81f-fd2f87450123

┌─tag_id─┬─uv─┬─type───┐
│ tag1   │ 11 │ UInt64 │
│ tag2   │ 12 │ UInt64 │
└────────┴────┴────────┘

2 rows in set. Elapsed: 0.011 sec.
```

#### 2.4.4 bitmapXorCardinality

可以使用 `bitmapXorCardinality` 函数计算两个 Bitmap 的补集(不重复元素所构成的集合)，并返回新的 bitmap 的基数。语法格式如下所示：
```sql
UInt64 bitmapXorCardinality(bitmap,bitmap)
```
如下所示计算 tag_bitmap 表中 bitmap1 和 bitmap2 补集的基数：
```sql
SELECT tag_id, bitmapXorCardinality(bitmap1, bitmap2) AS uv, toTypeName(uv) AS type
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: 6c9b45a1-4b2f-487a-a07f-47c50aa9b091

┌─tag_id─┬─uv─┬─type───┐
│ tag1   │  6 │ UInt64 │
│ tag2   │  8 │ UInt64 │
└────────┴────┴────────┘

2 rows in set. Elapsed: 0.003 sec.
```

#### 2.4.5 bitmapAndnotCardinality

可以使用 `bitmapAndnotCardinality` 函数计算两个 Bitmap 的差集(存在于第一个集合但不存在于第二个集合的元素集合)，并返回新的 bitmap 的基数。语法格式如下所示：
```sql
UInt64 bitmapAndnotCardinality(bitmap,bitmap)
```
如下所示计算 tag_bitmap 表中 bitmap1 和 bitmap2 差集的基数：
```sql
SELECT tag_id, bitmapXorCardinality(bitmap1, bitmap2) AS uv, toTypeName(uv) AS type
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: 6c9b45a1-4b2f-487a-a07f-47c50aa9b091

┌─tag_id─┬─uv─┬─type───┐
│ tag1   │  6 │ UInt64 │
│ tag2   │  8 │ UInt64 │
└────────┴────┴────────┘

2 rows in set. Elapsed: 0.003 sec.
```

### 2.5 位图子集

#### 2.5.1 bitmapSubsetInRange

可以使用 `bitmapSubsetInRange` 函数计算位图的子集，返回元素的取值需要在指定范围内，并返回一个新的 Bitmap。语法格式如下所示：
```sql
bitmapSubsetInRange(bitmap, range_start, range_end)
```
- bitmap: 要截取的目标 bitmap。
- range_start: 用于指定范围的起始值。如果指定的起始值超过了 Bitmap 的最大长度，则返回 NULL。如果 range_start 存在于 Bitmap 中，返回值会包括 range_start。
- range_end: 用于指定范围的结束值。如果 range_end 小于或等于 range_start，返回 NULL。注意返回值不包括 range_end。

如下所示从 tag_bitmap 表取出 bitmap1 中取值在 `[1,4)` 之间的元素，并返回一个新的 Bitmap：
```sql
SELECT tag_id, bitmapToArray(bitmapSubsetInRange(bitmap1, 1, 4)) AS sub_bitmap
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: 5359fb10-dd34-4039-beae-ae603f4452c3

┌─tag_id─┬─sub_bitmap─┐
│ tag1   │ [1,2,3]    │
│ tag2   │ []         │
└────────┴────────────┘

2 rows in set. Elapsed: 0.008 sec.
```

#### 2.5.2 bitmapSubsetLimit

可以使用 `bitmapSubsetLimit` 函数计算位图的子集，返回元素根据指定的起始值，从 Bitmap 中截取指定个数的元素，并返回一个新的 Bitmap。语法格式如下所示：
```sql
bitmapSubsetLimit(bitmap, range_start, cardinality_limit)
```
- bitmap: 要截取的目标 bitmap。
- range_start: 用于指定范围的起始值，UInt32 类型。
- cardinality_limit: 从 range_start 开始，要截取的元素个数。如果符合条件的元素个数小于 cardinality_limit 取值，则返回所有满足条件的元素。

如下所示从 tag_bitmap 表取出 bitmap1 中从 9 作为起始值，截取 4 个元素，并返回一个新的 Bitmap：
```sql
SELECT tag_id, bitmapToArray(bitmapSubsetLimit(bitmap1, 9, 4)) AS sub_bitmap
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: 6978e0da-f849-47ab-8dbc-212de85e4b3d

┌─tag_id─┬─sub_bitmap───┐
│ tag1   │ [9,10]       │
│ tag2   │ [9,10,11,12] │
└────────┴──────────────┘

2 rows in set. Elapsed: 0.004 sec.
```


#### 2.5.3 subBitmap

可以使用 `subBitmap` 函数计算位图的子集，返回元素根据 offset 指定的起始位置，从 Bitmap 中截取指定个数的元素，并返回一个新的 Bitmap。语法格式如下所示：
```sql
subBitmap(bitmap, offset, cardinality_limit)
```
- bitmap: 要截取的目标 bitmap。
- offset: 用于指定起始位置，Offset 从 0 开始。
- cardinality_limit: 从 Offset 开始，要截取的元素个数。如果符合条件的元素个数小于 cardinality_limit 取值，则返回所有满足条件的元素。

> 该函数与 bitmapSubsetLimit 功能相似，不同之处在于 bitmapSubsetLimit 指定的是起始值，subBitmap 指定的是 offset。

如下所示从 tag_bitmap 表取出 bitmap1 中从偏移量 3 开始截取 4 个元素，并返回一个新的 Bitmap：
```sql
SELECT tag_id, bitmapToArray(subBitmap(bitmap1, 3, 4)) AS sub_bitmap
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: a3572df0-dee8-43bb-a8ac-3364103ae292

┌─tag_id─┬─sub_bitmap───┐
│ tag1   │ [4,5,6,7]    │
│ tag2   │ [9,10,11,12] │
└────────┴──────────────┘

2 rows in set. Elapsed: 0.003 sec.
```

### 2.6 位图聚合

#### 2.6.1 groupBitmapAndState

可以使用 `groupBitmapAndState` 函数计算 Bitmap 列的交集(与操作)，并返回一个新的 Bitmap。语法格式如下所示：
```
groupBitmapAndState(expr)
```
> 需要注意的是如果去掉 `State` 后缀返回的是一个 UInt64 类型的基数

如下所示在 tag_bitmap 表中聚合 bitmap1 列计算多行 Bitmap 的交集，并返回一个新的 Bitmap，为了演示效果转换为一个数组展示：
```sql
SELECT
  bitmapToArray(groupBitmapAndState(bitmap1)) AS res
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: c8952179-3c33-46a0-b8a8-8a514c8c4da1

┌─res──────────┐
│ [6,7,8,9,10] │
└──────────────┘

1 row in set. Elapsed: 0.003 sec.
```

#### 2.6.2 groupBitmapOrState

可以使用 `groupBitmapOrState` 函数计算 Bitmap 列的并集(或操作)，并返回一个新的 Bitmap。语法格式如下所示：
```sql
groupBitmapOrState(expr)
```
> 需要注意的是如果去掉 `State` 后缀返回的是一个 UInt64 类型的基数

如下所示在 tag_bitmap 表中聚合 bitmap1 列计算多行 Bitmap 的并集，并返回一个新的 Bitmap，为了演示效果转换为一个数组展示：
```sql
SELECT
  bitmapToArray(groupBitmapOrState(bitmap1)) AS res
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: 2ca75957-8f36-4fae-85df-3b75c2c507f1

┌─res───────────────────────────────────┐
│ [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15] │
└───────────────────────────────────────┘

1 row in set. Elapsed: 0.005 sec.
```

#### 2.6.3 groupBitmapXorState

可以使用 `groupBitmapXorState` 函数计算 Bitmap 列的补集(异或操作)，并返回一个新的 Bitmap。语法格式如下所示：
```sql
groupBitmapXorState(expr)
```
> 需要注意的是如果去掉 `State` 后缀返回的是一个 UInt64 类型的基数

如下所示在 tag_bitmap 表中聚合 bitmap1 列计算多行 Bitmap 的补集，并返回一个新的 Bitmap，为了演示效果转换为一个数组展示：
```sql
SELECT
  bitmapToArray(groupBitmapXorState(bitmap1)) AS res
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: 825e510f-022b-48ad-921a-df388d6a79b5

┌─res────────────────────────┐
│ [1,2,3,4,5,11,12,13,14,15] │
└────────────────────────────┘

1 row in set. Elapsed: 0.005 sec.
```

### 2.7 其他

#### 2.7.1 bitmapContains

可以使用 `bitmapContains` 函数计算输入值是否在 Bitmap 列中。语法格式如下所示：
```sql
bitmapContains(bitmap, needle)
```
- bitmap: 要查询的目标 bitmap。
- needle: 输入值，UInt32 类型。

如下所示在 tag_bitmap 表中查询 `5` 是否在 bitmap1 中：
```sql
SELECT tag_id, bitmapContains(bitmap1, 5) AS res
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: 8683bb93-ac02-4c76-a494-b985abe54350

┌─tag_id─┬─res─┐
│ tag1   │   1 │
│ tag2   │   0 │
└────────┴─────┘

2 rows in set. Elapsed: 0.008 sec.
```

#### 2.7.2 bitmapHasAny

可以使用 `bitmapHasAny` 函数计算两个 Bitmap 列是否存在相同元素。语法格式如下所示：
```sql
bitmapHasAny(bitmap1, bitmap2)
```
> 两个 Bitmap 重叠相同元素可以通过 bitmapAnd(bitmap1, bitmap2) 函数查看。如果 bitmap2 只包含一个元素，考虑使用 bitmapContains，因为它更有效。

如下所示在 tag_bitmap 表中查询 bitmap1 和 bitmap2 是否存在相同的元素：
```sql
SELECT tag_id, bitmapHasAny(bitmap1, bitmap2) AS res
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: 870c928b-8c47-4251-83ed-a24a33685be3

┌─tag_id─┬─res─┐
│ tag1   │   1 │
│ tag2   │   1 │
└────────┴─────┘

2 rows in set. Elapsed: 0.002 sec.
```

#### 2.7.3 bitmapHasAll

可以使用 `bitmapHasAll` 函数计算第一个 Bitmap 是否包含第二个 Bitmap。如果第一个 Bitmap 包含第二个 Bitmap 的所有元素，则返回1，否则返回 0。如果第二个 Bitmap 是空位图，则返回 1。语法格式如下所示：
```sql
bitmapHasAll(bitmap1, bitmap2)
```

如下所示在 tag_bitmap 表中查询 bitmap1 是否包含 bitmap2 中的全部元素：
```sql
SELECT tag_id, bitmapHasAll(bitmap1, bitmap2) AS res
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: ce133c78-5c67-4c21-8645-156ce93df2dc

┌─tag_id─┬─res─┐
│ tag1   │   0 │
│ tag2   │   0 │
└────────┴─────┘

2 rows in set. Elapsed: 0.004 sec.
```

#### 2.7.4 bitmapMin

可以使用 `bitmapMin` 函数计算 Bitmap 中的最小值，如果 Bitmap 为空则返回 UINT32_MAX。语法格式如下所示：
```sql
bitmapMin(bitmap)
```

如下所示在 tag_bitmap 表中查询 bitmap1 和 bitmap2 的最小值元素：
```sql
SELECT tag_id, bitmapMin(bitmap1) AS res, bitmapMin(bitmap2) AS res2
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: 72c41f56-2832-4d78-b59d-f3fbf96768f1

┌─tag_id─┬─res─┬─res2─┐
│ tag1   │   1 │    2 │
│ tag2   │   6 │    2 │
└────────┴─────┴──────┘

2 rows in set. Elapsed: 0.002 sec.
```

#### 2.7.4 bitmapMax

可以使用 `bitmapMax` 函数计算 Bitmap 中的最大值，如果 Bitmap 为空则返回 0。语法格式如下所示：
```sql
bitmapMax(bitmap)
```

如下所示在 tag_bitmap 表中查询 bitmap1 和 bitmap2 的最大值元素：
```sql
SELECT tag_id, bitmapMax(bitmap1) AS res, bitmapMax(bitmap2) AS res2
FROM tag_bitmap;
```
返回结果如下所示：
```sql
Query id: 953a4b10-061a-49e8-adcb-9ce967196322

┌─tag_id─┬─res─┬─res2─┐
│ tag1   │  10 │   12 │
│ tag2   │  15 │   19 │
└────────┴─────┴──────┘

2 rows in set. Elapsed: 0.004 sec.
```







...
