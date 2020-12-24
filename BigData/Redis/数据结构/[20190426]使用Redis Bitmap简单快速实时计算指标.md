---
layout: post
author: sjf0115
title: 使用Redis Bitamp简单快速实时计算指标
date: 2019-04-27 10:21:06
tags:
  - Redis

categories: Redis
permalink: fast-easy-realtime-metrics-using-redis-bitmaps
---

传统上，度量指标一般由批处理作业执行（每小时运行，每天运行等）。Redis 中的 Bitmap 可以允许我们实时计算指标，并且非常节省空间。在1.28亿用户场景中，经典度量指标（如'日活'）在 MacBook Pro上只需不到50毫秒，而且只需要16 MB内存。

### 1. Bitmap

> 又可以称之为 Bitset。

Bitmap 或 Bitset 是一个由 0 和 1 构成的数组。在 Bitmap 中每一个 bit 被设置为 0 或 1，数组中的每个位置被称为 offset。AND，OR，XOR等操作符，以及其他位操作都是 Bitmaps 的常用操作。

### 2. 基数

Bitmap 中 1 的个数称之为基数。我们有一种有效算法来计算基数，例如，在 MacBook Pro 上，在包含10亿位填充90％的 Bitmap 上计算基数耗时 21.1 ms。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Redis/fast-easy-realtime-metrics-using-redis-bitmaps-1.png?raw=true)

### 3. Redis中的Bitmap

Redis 允许二进制键和二进制值。Bitmap 也是二进制值。将键指定 offset 设置为 0 或 1，`setbit（key，offset，value）` 操作需要用 `O(1)` 时间复杂度。

### 4. 一个简单的例子：每日活跃用户

为了统计今天登录的不同用户，我们创建了一个 Bitmap，其中每个用户都由一个 offset 标识。当用户访问页面或执行操作时，会将表示用户ID的 offset 设置为 1。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Redis/fast-easy-realtime-metrics-using-redis-bitmaps-2.png?raw=true)

在这个简单的例子中，每次用户登录时，我们都会执行：
```java
redis.setbit(daily_active_users，user_id，1)
```
这会将 daily_active_users Bitmap 键对应 offset 设置为1。这是一个 O(1) 时间复杂度操作。对此 Bitmap 进行基数统计会统计出今天一共登录了 9 个用户。键是 daily_active_users，值为 1011110100100101。

当然，由于每天活跃用户每天都会在改变，我们需要一种方法每天创建一个新的 Bitmap。我们只需在 Bitmap 键后面追加一个日期即可。例如，如果我们想要计算某天在音乐应用中播放至少1首歌曲的不同用户，我们可以将键名称设置为 `play:yyyy-mm-dd`。如果我们想要计算每小时播放至少一首歌曲的用户数量，我们可以将键名称设置为 `play:yyyy-mm-dd-hh`。为了计算每日指标，只要用户播放歌曲，我们就会在 `play：yyyy-mm-dd` 键中将用户对应的 bit 设置为1。
```java
redis.setbit(play:yyyy-mm-dd, user_id, 1)
```
今天播放歌曲的不同用户是存储以 `play:yyyy-mm-dd` 为键的值。要计算每周或每月度量指标，我们可以简单地计算一周或一个月中所有每日 Bitmap 的并集，然后计算结果 Bitmap 的总体基数。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Redis/fast-easy-realtime-metrics-using-redis-bitmaps-3.png?raw=true)

你还可以非常轻松地提取更复杂的指标。例如，11月播放歌曲的会员用户为：
```
(play:2011-11-01 ∪ play:2011-11-02 ∪...∪play:2011-11-30) ∩ premium:2011-11
```

### 5. 使用1.28亿用户进行性能比较

下表显示了针对1.28亿用户在1天，7天和30天计算的比较。通过组合每日 Bitmap 计算7日和30日指标：

| 周期 | 耗时 (MS)|
|---|---|
| 每日	| 50.2 |
| 每周 |	392.0 |
| 每月 | 1624.8 |

### 6. 优化

在上面的示例中，我们可以通过在 Redis 中缓存计算的每日，每周，每月计数来优化每周和每月计算。

这是一种非常灵活的方法。缓存的另一个好处是它允许快速群组分析，例如使用手机的每周唯一用户 - 手机用户 Bitmap 与每周活跃用户 Bitmap 的交集。或者，如果我们想要滚动计算过去n天内的唯一用户，那么缓存每日唯一用户的计数会使这变得简单 - 只需从缓存中获取前n-1天并将其与实时每日计数结合起来即可，而这只需要50ms。

### 7. 示例代码

下面的Java代码片段指定用户操作和日期来计算唯一用户：
```java
import redis.clients.jedis.Jedis;
import java.util.BitSet;
...
Jedis redis = new Jedis("localhost");
...
public int uniqueCount(String action, String date) {
  String key = action + ":" + date;
  BitSet users = BitSet.valueOf(redis.get(key.getBytes()));
  return users.cardinality();
}
```
下面的代码片段计算指定用户操作和日期列表的唯一用户：
```java
import redis.clients.jedis.Jedis;
import java.util.BitSet;
...
Jedis redis = new Jedis("localhost");
...
public int uniqueCount(String action, String... dates){
  BitSet all = new BitSet();
  for (String date : dates) {
    String key = action + ":" + date;
    BitSet users = BitSet.valueOf(redis.get(key.getBytes()));
    all.or(users);
  }
  return all.cardinality();
}
```

英译对照
- 基数: Population Count

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

原文:[REDIS BITMAPS – FAST, EASY, REALTIME METRICS](https://blog.getspool.com/2011/11/29/fast-easy-realtime-metrics-using-redis-bitmaps/)
