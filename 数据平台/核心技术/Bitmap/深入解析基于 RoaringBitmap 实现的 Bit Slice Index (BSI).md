## 1. Bit Slice Index 核心概念

Bit Slice Index (BSI) 是一种高效的数值索引结构，它将整数值按位分解到多个位图中，从而支持快速的范围查询、聚合计算等操作。结合 RoaringBitmap 的高效压缩位图实现，BSI 能够在保持高性能的同时显著减少内存使用。在这深入解析基于 RoaringBitmap 的 Bit Slice Index 算法实现 Rbm32BitSliceIndex。

## 2. 2. 核心数据结构设计

### 2.1 关键成员变量

```java
public class Rbm32BitSliceIndex implements BitSliceIndex {
    private int maxValue = -1;        // 存储的最大值
    private int minValue = -1;        // 存储的最小值
    private int sliceSize = 0;        // 切片个数（二进制位数）
    private RoaringBitmap[] slices;   // 位切片数组
    private RoaringBitmap ebm;        // 存在位图（Existence Bitmap）
    private Boolean runOptimized = false; // 运行优化标志
}
```
BSI 中还会存储如下信息：
- Existence bitmap（ebm）：存在位图，存储 user_id 数组的 RoaringBitmap。
- maxValue：存储的最大值。
- minValue：存储的最小值。
- sliceSize：切片个数，最大 score 的二进制位数，本示例为 7。

### 2.2 数据结构原理

BSI(Bit Slice Index)本质上是对 KV 键值数据的压缩，将每个整数值分解为二进制表示，每个二进制位存储在一个独立的位图中。对于值 value，其二进制表示的第 i 位为 1 时，在 slices[i] 位图中记录对应的 key。下面以用户(key)与用户获取的积分(value)为例为你介绍 BSI 的原理与结构。

| user_id(用户) | score(积分十进制) | score(积分二进制) |
| :------------- | :------------- | :------------- |
| 1 | 48 | 0110000 |
| 2 | 80 | 1010000 |
| 3 | 75 | 1001011 |
| 4 | 19 | 0010011 |
| 5 | 1 | 0000001 |
| 6 | 57 | 0111001 |
| 7 | 63 | 0111111 |
| 8 | 22 | 0010110 |
| 9 | 96 | 1100000 |
| 10 | 34 | 0100010 |

表中包含用户ID user_id 列和积分 score 列。其中，score 的最大值为 96，即二进制最大位数为 7 位，因此将所有 score 的二进制值补充为 7 位。然后对二进制数据从低位向高位遍历，将位值为 1 的 user_id 存入切片 RoaringBitmap 数组的 slices 中，形成位切片索引 BSI(Bit Slice Index)。我们以用户ID为 1 的用户为例介绍，用户对应的积分 48(二进制 110000)：
- slices[0] 不添加 key=1（第0位为0）
- slices[1] 不添加 key=1（第1位为0）
- slices[2] 不添加 key=1（第2位为0）
- slices[3] 不添加 key=1（第3位为0）
- slices[4] 添加 key=1（第4位为1）
- slices[5] 添加 key=1（第5位为1）
- slices[6] 不添加 key=1（第6位为0）

上表数据最终建立了如下切片索引：

| 切片 | 用户 RoaringBitmap |
| :------------- | :------------- |
| slices[0] | {3,4,5,6,7} |
| slices[1] | {3,4,7,8,10} |
| slices[2] | {7,8} |
| slices[3] | {3,6,7} |
| slices[4] | {1,2,4,6,7,8} |
| slices[5] | {1,6,7,9,10} |
| slices[6] | {2,3,9} |

> 每个切片对应一个 RoaringBitmap，RoaringBitmap 中存储 user_id

此外，ebm 记录所有存在的用户 `{1,2,3,4,5,6,7,8,9}`，用于快速判断某个用户是否存在；maxValue 存储最大值 96，minValue 存储最小值 1。


## 3. 核心操作实现详解

- 构建 BSI
  - int sliceSize();
  - long getLongCardinality();
  - void clear();
  - boolean isEmpty();
  - void put(int key, int value);
  - void putAll(BitSliceIndex otherBsi);
- 序列化
  - void serialize(ByteBuffer buffer) throws IOException;
  - void deserialize(ByteBuffer buffer) throws IOException;
- 键操作
  - boolean containsKey(int key);
  - int remove(int key);
  - RoaringBitmap keys();
- 精确查询值
  - boolean containsValue(int value);
  - int get(int key);
- 范围查询值
  - max
  - min
  - eq
  - lt
  - le
  - gt
  - ge
  - range
- 运算
  - SUM
  - Top
  - and
  - or
  - xor
  - not

### 3.1 初始化


```java
public Rbm32BitSliceIndex(int minValue, int maxValue) {
    if (minValue < 0) {
        throw new IllegalArgumentException("Value should be non-negative");
    }
    // 索引切片个数等于最大整数二进制位数，即32减去最大整数二进制填充0个数
    sliceSize = 32 - Integer.numberOfLeadingZeros(maxValue);
    this.slices = new RoaringBitmap[sliceSize];
    for (int i = 0; i < slices.length; i++) {
        this.slices[i] = new RoaringBitmap();
    }
    this.ebm = new RoaringBitmap();
    this.minValue = minValue;
    this.maxValue = maxValue;
}
```

### 3.2 容量管理

```java
/**
 * 调整切片个数
 */
private void resize(int newSliceSize) {
    if (newSliceSize <= this.sliceSize) {
        // 小于等于之前切片个数不需要调整
        return;
    }
    RoaringBitmap[] newSlices = new RoaringBitmap[newSliceSize];
    // 复制旧切片
    if (this.sliceSize != 0) {
        System.arraycopy(this.slices, 0, newSlices, 0, this.sliceSize);
    }
    // 增加新切片
    for (int i = newSliceSize - 1; i >= this.sliceSize; i--) {
        newSlices[i] = new RoaringBitmap();
        if (this.runOptimized) {
            newSlices[i].runOptimize();
        }
    }
    this.slices = newSlices;
    this.sliceSize = newSliceSize;
}
```

### 3.3  数据插入操作

```java
public void put(int key, int value) {
    // 更新最大值和最小值
    if (this.isEmpty()) {
        this.minValue = value;
        this.maxValue = value;
    } else if (this.minValue > value) {
        this.minValue = value;
    } else if (this.maxValue < value) {
        this.maxValue = value;
    }
    // 调整切片个数
    int newSliceSize = Integer.toBinaryString(value).length();
    resize(newSliceSize);
    // 为指定 Key 关联指定 Value
    putValueInternal(key, value);
}
```

### 3.4 数据查询操作

#### 3.4.1 单键查询：

```java

```

#### 3.4.2 极值查询


### 3.5 O'Neil 范围查询算法


### 3.6 聚合计算
