---
layout: post
author: wy
title: 算法进阶系列1 空间搜索 GeoHash 算法
date: 2022-06-27 13:40:21
tags:
  - 算法

categories: 算法
permalink: geohash-algorithm
---

## 1. 背景

我们经常会用到 App 打车和共享单车，App 界面上会显示出自己附近一个范围内可用的出租车或者共享单车：

![](https://github.com/sjf0115/ImageBucket/blob/main/Algorithm/geohash-algorithm-1.png?raw=true)

那如何发现以自己为圆心一定范围内的车呢？最直观的想法就是在数据库里存储每一辆车的经纬度，根据自己当前位置的经纬度计算和这辆车的距离，然后筛选出距离自己小于等于指定距离的车辆返回给客户端。这种方案比较笨，一般也不会这么做。因为这种做法需要对整个表里面每一辆车都计算一次相对距离，数据量太大，查询会很慢，效率很低。

那么这些 App 是怎么做到既能精准定位，又能快速查找呢？答案就是 GeoHash。

## 2. 什么是 GeoHash

### 2.1 经纬度

了解什么是 GeoHash 原理之前，我们先来简单看一下什么是经纬度，这对于理解 GeoHash 有很大的帮助。我们将地球铺平开来，会得到下面这个平面图：

![](https://github.com/sjf0115/ImageBucket/blob/main/Algorithm/geohash-algorithm-2.png?raw=true)

以赤道和本初子午线为界来划分经度和纬度，赤道和本初子午线均在 0 度。经度是指通过某地的经线面与本初子午面所成的二面角。从本初子午线向东划分 180 度称为东经，用 'E' 表示：`(0, 180]`；向西划分 180 度称为西经，用 'W' 表示：`[-180, 0)`：

![](https://github.com/sjf0115/ImageBucket/blob/main/Algorithm/geohash-algorithm-3.png?raw=true)

纬度是指过椭球面上某点作法线，该点法线与赤道平面的线面角。以赤道向北划分 90 度称为北纬，用 'N' 表示：`(0, 90]`；向南划分 90 度称为南纬，用 'S' 表示：`[-90, 0)`：

![](https://github.com/sjf0115/ImageBucket/blob/main/Algorithm/geohash-algorithm-4.png?raw=true)

> 纬线和纬线是角度数值，并不是米。

因此我们常用十字坐标法来表示经纬度坐标图，以赤道作为经度 X 横坐标，以本初子午线作为纬度 Y 竖坐标：

![](https://github.com/sjf0115/ImageBucket/blob/main/Algorithm/geohash-algorithm-5.png?raw=true)

一个经度和一个纬度唯一确定了地球上的一个地点的精确位置。我们以北京标志性古建筑天安门为例，坐标为 (39.90733194004775, 116.39124226796913），表示的是纬度为39.90733194004775，经度为116.39124226796913：

![](https://github.com/sjf0115/ImageBucket/blob/main/Algorithm/geohash-algorithm-6.png?raw=true)

### 2.2 GeoHash

在了解什么是经纬度之后，现在我们来说一下什么是 GeoHash。GeoHash 是一种对地理坐标进行编码的方法，将二维坐标映射为一个字符串。每个字符串代表一个特定的矩形，在该矩形范围内的所有坐标都共用这个字符串。那我们如何划分矩形区间呢？如果以本初子午线、赤道为界，地球可以分成 4 个部分。在垂直方向，如果纬度在 `[-90, 0)` 区间范围内用二进制 0 代表，即用 0 来表示下面的区间，如果在 `(0, 90]` 区间内范围用二进制 1 代表，即用 1 表示上面的区间；同样在水平方向，经度在 `[-180, 0)` 区间范围内用二进制 0 代表，即用 0 来表示左边的区间，如果在 `(0, 180]` 区间范围内用二进制 1 代表，即用 1 表示右边的区间。那么地球可以分成如下 4 个部分：

![](https://github.com/sjf0115/ImageBucket/blob/main/Algorithm/geohash-algorithm-7.png?raw=true)

我们可以继续拆分，将整个地球初始分割成 4*8=32 个网格：

![](https://github.com/sjf0115/ImageBucket/blob/main/Algorithm/geohash-algorithm-8.png?raw=true)

每个网格使用一个 Base32 的字母编码表示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Algorithm/geohash-algorithm-9.png?raw=true)

当我们将各个网格区间分解成更小的子区间时，编码的顺序是自相似的（分形），每一个子区间也形成 Z 曲线，这种类型的曲线被称为 Peano 空间填充曲线。这种类型的空间填充曲线的优点是将二维空间转换成一维曲线（事实上是分形维），对大部分而言，编码相似的距离也相近，但 Peano 空间填充曲线最大的缺点就是突变性，有些编码相邻但距离却相差很远，比如 01111 与 10000，编码是相邻的，但距离相差很大。　

整个地球初始分割成 32 个网格，我们可以继续对每个网格再分成 32 个子网格。编码字符串越长精度越高，对应的网格矩形范围越小：

![](https://github.com/sjf0115/ImageBucket/blob/main/Algorithm/geohash-algorithm-10.png?raw=true)

例如，我们还是以天安门为例，整个中国大部分都落在 w 区间；继续划分 32 个子网格，北京大部分区域都落在 x 区间，就这样一直迭代划分，最终天安门的 Base32 编码为 wx4g08c。

综上可以看出，GeoHash 具有以下特点：
- GeoHash 用一个字符串表示经度和纬度两个坐标;
- GeoHash 表示的并不是一个点，而是一个区域;
- GeoHash 编码的前缀表示更大的区域;
- GeoHash 编码字符串越长精度越高，对应的区域范围就越小;

## 3. 实现原理

对一个地理坐标实现 GeoHash 编码时，需要通过如下步骤实现将一个经纬度坐标转换成一个 GeoHash 编码字符串：
- 指定一个位置的经纬度坐标值，将纬度和经度分别编码为由 0 和 1 组成的二进制数字串；
- 按照'偶数位放经度，奇数位放纬度'的原则，将得到的二进制编码穿插组合，得到一个新的二进制串；
- 合并后的二进制串，按照从前往后，每隔 5 位，换算成十进制数字，最后不足 5 位的用 0 补齐；
- 最后，根据 base32 的对照表，将十进制数字翻译成字符串，即得到地理坐标对应的目标 GeoHash 字符串

### 3.1 根据经纬度计算二进制编码

对一个地理坐标编码时，按照初始区间范围纬度 `[-90,90]` 和经度 `[-180,180]`，计算目标经度和纬度分别落在左区间还是右区间。落在左区间则取 0，右区间则取 1。然后，对上一步得到的区间继续按照此方法对半查找，得到下一位二进制编码，直到编码长度达到业务需要的精度。我们天安门坐标 '39.90733194004775, 116.39124226796913' 为例，计算其 GeoHash 字符串。首先对纬度做二进制编码：
- 将 `[-90,90]` 平分为 2 部分，纬度 '39.90733194004775' 落在右区间 `(0,90]`，则第一位取 1;
- 将 `(0,90]` 平分为 2 部分，纬度落在左区间 `(0,45]`，则第二位取 0;
- 如下图所示不断重复以上步骤，得到的目标区间会越来越小，区间的两个端点也越来越逼近 '39.90733194004775'：

![](https://github.com/sjf0115/ImageBucket/blob/main/Algorithm/geohash-algorithm-11.png?raw=true)

最终纬度二进制编码为 101110001100000111。同样也对经度做二进制编码，如下图所示不断迭代：

![](https://github.com/sjf0115/ImageBucket/blob/main/Algorithm/geohash-algorithm-12.png?raw=true)

最终经度二进制编码为 110100101100010001。

### 3.2 经纬度二进制编码奇偶组合

按照'偶数位放经度，奇数位放纬度'的规则，将经纬度的二进制编码穿插编码：

![](https://github.com/sjf0115/ImageBucket/blob/main/Algorithm/geohash-algorithm-13.png?raw=true)

最终经纬度穿插二进制编码为 11100	11101	00100	01111	00000 01000	01011 1。

### 3.3 Base32编码

Base32 编码是用 0-9、b-z（去掉a, i, l, o）这 32 个字母进行编码，如下所示是对应的对照表：

![](https://github.com/sjf0115/ImageBucket/blob/main/Algorithm/geohash-algorithm-14.png?raw=true)

具体操作是先将上一步得到的合并后二进制编码 每 5 位转换为一个十进制数字，得到 28,25,19,18,7,2。然后对照 Base32 编码表生成 Base32 编码：

![](https://github.com/sjf0115/ImageBucket/blob/main/Algorithm/geohash-algorithm-15.png?raw=true)

得到 Base32 编码为：wx4g08c。

> Base32 编码长度为 7 位，需要经度 18 位，纬度 17 位穿插编码。

## 4. 编码长度与精度

GeoHash 是将空间不断的二分，然后将二分的路径转化为 Base32 编码。从原理可以看出，Geohash 表示的是一个矩形区间，而不是一个点，GeoHash 字符串值越长，这个矩形区间就越小，标识的位置也就越精确。下图是维基百科中不同长度 GeoHash 下的经纬度误差：

![](https://github.com/sjf0115/ImageBucket/blob/main/Algorithm/geohash-algorithm-16.png?raw=true)

## 5. 注意

GeoHash 有两个需要注意的问题。第一个是边界问题，第二个是曲线突变问题。

### 5.1 边界问题

第一个需要注意的是边界问题：

![](https://github.com/sjf0115/ImageBucket/blob/main/Algorithm/geohash-algorithm-17.png?raw=true)

如上图所示，如果我们在红点位置，区域内还有一个黄点车辆，相邻区域内的也有一个绿点车辆。由于 GeoHash 表示的是一个矩形区间，我们会认为在同一个区间内的 2 个位置是最近的，黄点车辆和我们所处同一个矩形区间内，因此我们会认为黄点车辆离我们最近。但是从图中可以直观的看到绿点的车辆明显离我们更近一些，只是因为绿点车辆刚好在另一个区间内。

那么如何解决这个边界问题，给出最近最优的算法方案呢？解决方案就是把我们自己定位位置附近 8 个方向的矩形区间的 GeoHash 都算出来。最后分别计算这些区间内车辆与我们自己的距离（由于范围很小，点的数量就也很少，计算量就很少），过滤掉不满足条件的车辆就可以了。

### 5.2 曲线突变问题

第一个需要注意的是曲线突变问题。有时候可能会给人一个误解就是如果两个 GeoHash 之间二进制的差异越小，那么这两个区间距离就越近。这完全是错误的，比如上面图中的 01111 和 10000，这两个区间二进制只差 00001，但实际物理距离比较远。

参考：
- 经纬度坐标在线转 GeoHash：http://geohash.co/
- GeoHash 编码划分：https://geohash.softeng.co/
- [如何搜索附近的商家? Geohash （上）](https://www.youtube.com/watch?v=NCvYkJWenb8)
- [如何搜索附近的商家? Geohash （下）](https://www.youtube.com/watch?v=_UAkuUVzwcY)
- [一种基于快速GeoHash实现海量商品与商圈高效匹配的算法](https://mp.weixin.qq.com/s/2B-VJ2xgwxrmsSkE6zuoPA)
- [Geohash边界分形与拟合，让你的边界纵享丝滑](https://mp.weixin.qq.com/s/IN1L2-Pp9o-3LgXHAo6F7w)
- [基于Geohash算法切分OID4点码](https://mp.weixin.qq.com/s/N7wJ9uqSWwgUSj6rr_FKSQ)
- [Elasticsearch 在地理信息空间索引的探索和演进](https://mp.weixin.qq.com/s/y33FQjFN-f58h1_TIwgMAw)
- [Redis(6)——GeoHash查找附近的人](https://mp.weixin.qq.com/s/wALOAK9mewQOyajTaSqGUw)
- [Redis 到底是怎么实现“附近的人”这个功能的？](https://mp.weixin.qq.com/s/2uSr2YOjtLbUdHI01qc4rw)
- [是什么能让 APP 快速精准定位到我们的位置？](https://mp.weixin.qq.com/s/KqCxb24FoIge9AropiSzXg)
