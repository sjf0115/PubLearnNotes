---
layout: post
author: sjf0115
title: Redis 如何使用 Bitmap
date: 2022-05-15 14:59:06
tags:
  - Redis

categories: Redis
permalink: how-to-use-bitmap-in-redis
---

## 1. Bitmap 是什么

Bitmap(也称为位数组或者位向量等)是一种实现对位的操作的'数据结构'，在数据结构加引号主要因为：
- Bitmap 本身不是一种数据结构，底层实际上是字符串，可以借助字符串进行位操作。
- Bitmap 单独提供了一套命令，所以与使用字符串的方法不太相同。可以把 Bitmaps 想象成一个以位为单位的数组，数组的每个单元只能存储 0 和 1，数组的下标在 Bitmap 中叫做偏移量 offset。

## 2. 占用存储空间

如上我们知道 Bitmap 本身不是一种数据结构，底层实际上使用字符串来存储。由于 Redis 中字符串的最大长度是 512 MB字节，所以 BitMap 的偏移量 offset 值也是有上限的，其最大值是：8 * 1024 * 1024 * 512 = 2^32。由于 C 语言中字符串的末尾都要存储一位分隔符，所以实际上 BitMap 的偏移量 offset 值上限是：2^32-1。Bitmap 实际占用存储空间取决于 BitMap 偏移量 offset 的最大值，占用字节数可以用 (max_offset / 8) + 1 公式来计算或者直接借助底层字符串函数 strlen 来计算：
```
127.0.0.1:6379> setbit login:20220515 0 1
(integer) 0
# (0 / 8) + 1 = 1
127.0.0.1:6379> strlen login:20220515
(integer) 1
127.0.0.1:6379> setbit login:20220515 8 1
(integer) 0
# (8 / 8) + 1 = 2
127.0.0.1:6379> strlen login:20220515
(integer) 2
```

![](https://github.com/sjf0115/ImageBucket/blob/main/Redis/how-to-use-bitmap-in-redis-1.png?raw=true)

需要注意的是，在第一次初始化 Bitmap 时，假如偏移量 offset 非常大，由于需要分配所需要的内存，整个初始化过程执行会比较慢，可能会造成 Redis 的阻塞。在 2010 款 MacBook Pro 上，设置第 2^32-1 位，由于需要分配 512MB 内存，所以大约需要 300 毫秒；设置第 2^30-1 位（128 MB）大约需要 80 毫秒；设置第 2^28 -1 位（32MB）需要约 30 毫秒；设置第 2^26 -1（8MB）需要约 8 毫秒。一旦完成第一次分配，随后对同一 key 再设置将不会产生分配开销。

## 3. 命令

> 下面示例中我们将登录 App 的用户存放在 Bitmap 中，登录的用户记做 1，没有登录的用户记做 0，用偏移量作为用户的id。

### 3.1 SETBIT

> 最早可用版本：2.2.0。时间复杂度：O(1)。

语法格式：
```
SETBIT key offset value
```

SETBIT 用来设置 key 对应第 offset 位的值（offset 从 0 开始算），可以设置为 0 或者 1。当指定的 KEY 不存在时，会自动生成一个新的字符串值。字符串会进行扩展以确保可以将 value 保存在指定的偏移量 offset 上。当字符串值进行扩展时，空白位置用 0 来填充。需要注意的是 offset 需要大于或等于 0，小于 2 的 32 次方。

假设现在有 10 个用户，用户id为 0、1、5、9 的 4 个用户在 20220514 进行了登录，那么当前 Bitmap 初始化结果如下图所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Redis/how-to-use-bitmap-in-redis-2.png?raw=true)

具体操作过程如下，login:20220514 代表 20220514 这天所有登录用户的 Bitmap：
```
127.0.0.1:6379> setbit login:20220514 0 1
(integer) 0
127.0.0.1:6379> setbit login:20220514 1 1
(integer) 0
127.0.0.1:6379> setbit login:20220514 5 1
(integer) 0
127.0.0.1:6379> setbit login:20220514 9 1
(integer) 0
```
假设用户 uid 为 15 的用户也登录了 App，那么 Bitmap 的结构变成了如下图所示，第 10 位到第 14 位都用 0 填充，第 15 位被置为 1：

![](https://github.com/sjf0115/ImageBucket/blob/main/Redis/how-to-use-bitmap-in-redis-3.png?raw=true)

> 很多应用的用户id以一个指定数字（例如 150000000000）开头，直接将用户id和 Bitmap 的偏移量对应势必会造成一定的浪费，通常的做法是每次做 setbit 操作时将用户id减去这个指定数字。在第一次初始化 Bitmap 时，假如偏移量非常大，那么整个初始化过程执行会比较慢，可能会造成 Redis 的阻塞。

### 3.2 GETBIT

> 最早可用版本：2.2.0。时间复杂度：O(1)。

语法格式：
```
GETBIT key offset
```
获取 key 对应第 offset 位的值（offset 从 0 开始算）。当 offset 超过字符串长度时，字符串假定为一个 0 位的连续空间。当指定的 key 不存在时，假定为一个空字符串，offset 肯定是超出字符串长度范围，因此该值也被假定为 0 位的连续空间，都会返回 0。

下面获取用户id为 4 的用户是否在 20220514 这天登录过，返回 0 说明没有访问过：
```
127.0.0.1:6379> getbit login:20220514 4
(integer) 0
```
下面获取用户id为 5 的用户是否在 20220514 这天登录过，返回 1 说明访问过：
```
127.0.0.1:6379> getbit login:20220514 5
(integer) 1
```
下面获取用户id为 20 的用户是否在 20220514 这天登录过，因为 offset 20 根本就不存在，所以返回结果也是 0：
```
127.0.0.1:6379> getbit login:20220514 20
(integer) 1
```

### 3.3 BITCOUNT

> 最早可用版本：2.6.0。时间复杂度：O(N)。

语法格式：
```
BITCOUNT key [ start end [ BYTE | BIT]]
```
用来计算指定 key 对应字符串中，被设置为 1 的 bit 位的数量。一般情况下，字符串中所有 bit 位都会参与计数，我们可以通过 start 或 end 参数来指定一定范围内被设置为 1 的 bit 位的数量。start 和 end 参数的设置和 GETRANGE 命令类似，都可以使用负数：比如 -1 表示最后一个位，而 -2 表示倒数第二个位等。

> 从 Redis 7.0.0 开始支持 BYTE 或者 BIT 选项

下面计算 20220514 这天所有登录用户数量：
```
127.0.0.1:6379> bitcount login:20220514
(integer) 5
```

### 3.4 Bitmaps 间的运算

> 最早可用版本：2.6.0。时间复杂度： O(N)。

语法格式：
```
BITOP operation destkey key [key ...]
```
BITOP 是一个复合操作，支持在多个 key 之间执行按位运算并将结果存储在 destkey 指定的 key 中。BITOP 命令支持四种按位运算：AND(交集)、OR(并集)、XOR(异或) 和 NOT(非)：
```
BITOP AND destkey srckey1 srckey2 srckey3 ... srckeyN
BITOP OR destkey srckey1 srckey2 srckey3 ... srckeyN
BITOP XOR destkey srckey1 srckey2 srckey3 ... srckeyN
BITOP NOT destkey srckey
```
如上所见，NOT 很特殊，因为它只需要一个输入 key，因为它执行位反转，因此它仅作为一元运算符才有意义。

假设 20220513 登录 App 的用户id为 1、3、5、7，如下图所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Redis/how-to-use-bitmap-in-redis-4.png?raw=true)

如果想算出 20220513 和 20220514 两天都登录过的用户数量，如下图所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Redis/how-to-use-bitmap-in-redis-5.png?raw=true)

可以使用 AND 求交集，具体命令如下：
```
127.0.0.1:6379> bitop and login:20220513:and:20220514 login:20220513 login:20220514
(integer) 2
127.0.0.1:6379> bitcount login:20220513:and:20220514
(integer) 2
127.0.0.1:6379> getbit login:20220513:and:20220514 1
(integer) 1
127.0.0.1:6379> getbit login:20220513:and:20220514 5
(integer) 1
```
如果想算出 20220513 和 20220514 任意一天登录过 App 的用户数量：

![](https://github.com/sjf0115/ImageBucket/blob/main/Redis/how-to-use-bitmap-in-redis-6.png?raw=true)

可以使用 OR 求并集，具体命令如下：
```
127.0.0.1:6379> bitop or login:20220513:or:20220514 login:20220513 login:20220514
(integer) 2
127.0.0.1:6379> bitcount login:20220513:or:20220514
(integer) 7
127.0.0.1:6379> getbit login:20220513:or:20220514 0
(integer) 1
127.0.0.1:6379> getbit login:20220513:or:20220514 1
(integer) 1
```

### 3.5 BITPOS

> 最早可用版本：2.8.7。时间复杂度： O(N)。

语法格式：
```
BITPOS key bit [ start [ end [ BYTE | BIT]]]
```
用来计算指定 key 对应字符串中，第一位为 1 或者 0 的 offset 位置。除此之外，BITPOS 也有两个选项 start 和 end，跟 BITCOUNT 一样。

> BYTE、BIT 这两个选项从 7.0.0 版本开始才能使用。

下面计算 20220514 登录 App 的最小用户id：
```
127.0.0.1:6379> bitpos login:20220513 1
(integer) 1
```
