
## 1. 简介

## 2. 函数

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



### 2.1 位图生成

位图可以用两种方式生成。第一种方法是从 Array 对象生成位图，另一种方法是通过带 `State` 后缀的聚合函数 groupBitmap 构造。

#### 2.1.1 bitmapBuild

第一种方法是从 Array 对象生成位图，可以使用 `bitmapBuild` 方法将无符号整数数组转化为位图。方法格式如下所示：
```sql
bitmapBuild(array)
```
参数 array 表示一个无符号整数数组。如下所示将一个数组转换为位图对象：
```sql
SELECT bitmapBuild([1, 2, 3, 4, 5]) AS res, toTypeName(res) AS type
```
返回结果如下所示：
```sql
Query id: b9229ce1-3f4b-45c2-bd0e-0f5100275dab

┌─res─┬─type──────────────────────────────────┐
│     │ AggregateFunction(groupBitmap, UInt8) │
└─────┴───────────────────────────────────────┘

1 row in set. Elapsed: 0.004 sec.
```

#### 2.1.2 groupBitmap

另一种方法是通过带 `State` 后缀的聚合函数 groupBitmap 生成，根据无符号整数列聚合计算返回位图。需要注意的是如果不带 `State` 后缀返回的是 UInt64 类型的位图基数。方法格式如下所示：
```sql
groupBitmap(expr)
```
> expr 表示一个结果为 `UInt*` 类型的表达式

如下所示将 bitmap_test_user 表中的 user_id 整数列转换为位图对象并计算用户数：
```sql
SELECT groupBitmapState(user_id) AS bitmap, groupBitmap(user_id) AS uv, toTypeName(bitmap) AS type
FROM bitmap_test_user;
```
返回结果如下所示：
```sql
Query id: bac5c14e-284e-4d39-88e6-2b91f54748af

┌─bitmap─┬─uv─┬─type───────────────────────────────────┐
│        │  6 │ AggregateFunction(groupBitmap, UInt32) │
└────────┴────┴────────────────────────────────────────┘

1 row in set. Elapsed: 0.005 sec.
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

可以使用 `bitmapAndnot` 函数计算两个 bitmap 的差集。差集是指包含所有存在于第一个集合且不存在于第二个集合的元素的集合。语法格式如下所示：
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


#### 2.4.5 bitmapAndnotCardinality





















...
