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

- 初始化操作
  - Rbm32BitSliceIndex(int minValue, int maxValue)
- 容量管理操作
  - void resize(int newSliceSize)
- 基础操作
  - int sliceSize();
  - long getLongCardinality();
  - boolean isEmpty();
  - BitSliceIndex clone();
- 插入操作
  - void put(int key, int value);
  - void putAll(BitSliceIndex otherBsi);
- 删除操作
  - 删除指定 Key：`int remove(int key)`
  - 清空所有 Key：`void clear()`
- 精确查询操作
  - 包含查询：`boolean containsKey(int key)`
  - 按 Key 查询：`int get(int key)`
- 范围查询操作
  - max
  - min
  - eq
  - lt
  - le
  - gt
  - ge
  - range
- 聚合计算操作
  - SUM
- 序列化
  - void serialize(ByteBuffer buffer) throws IOException;
  - void deserialize(ByteBuffer buffer) throws IOException;


### 3.1 初始化操作

通过一个最小值和一个最大值来初始化 Bit Slice Index 的实现 Rbm32BitSliceIndex：
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
索引切片个数 sliceSize 的计算是核心，它决定了 BSI 能够表示的最大数值范围。索引切片个数等于最大整数的二进制位数，可以通过 32 减去最大整数二进制0填充个数计算得到。每个切片对应一个二进制位，从低位(0)到高位(sliceSize-1)，存储在一个独立的 RoaringBitmap 位图中。ebm 是 "Existence Bitmap" 的缩写，存储所有的 Key，用于快速判断 Key 是否存在。

### 3.2 容量管理

在上述初始化时根据设置的最大值来设置初始化容量，随着添加值的变化，可与动态调整 BSI 的容量：
```java
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
如果调整的切片个数 newSliceSize 小于等于当前切片个数 this.sliceSize，说明当前容量已经足够表示新值，直接返回，避免不必要的扩容操作。容量调整逻辑按照如下调整：
- 根据新容量分配 RoaringBitmap 数组创建新的切片数组。
- 通过 System.arraycopy 高效拷贝旧切片数据
- 为新增的高位创建空 RoaringBitmap 来初始化新切片
- 切换至新数组并更新容量记录

### 3.3 基础操作

#### 3.3.1 BSI 切片个数

```java
public int sliceSize() {
    return sliceSize;
}
```

#### 3.3.2 BSI 基数

BSI 基数即 BSI 中 Key 的个数：
```java
public long getLongCardinality() {
    return this.ebm.getLongCardinality();
}
```

#### 3.3.3 BSI 是否为空

```java
public boolean isEmpty() {
    return this.getLongCardinality() == 0;
}
```
#### 3.3.4 BSI 克隆

```java
public BitSliceIndex clone() {
    Rbm32BitSliceIndex bitSliceIndex = new Rbm32BitSliceIndex();
    // 克隆属性
    bitSliceIndex.minValue = this.minValue;
    bitSliceIndex.maxValue = this.maxValue;
    bitSliceIndex.sliceSize = this.sliceSize;
    bitSliceIndex.runOptimized = this.runOptimized;
    bitSliceIndex.ebm = this.ebm.clone();
    // 克隆切片
    RoaringBitmap[] cloneSlices = new RoaringBitmap[this.sliceSize];
    for (int i = 0; i < cloneSlices.length; i++) {
        cloneSlices[i] = this.slices[i].clone();
    }
    bitSliceIndex.slices = cloneSlices;
    return bitSliceIndex;
}
```

### 3.4  插入操作

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

private void putValueInternal(int key, int value) {
    // 为 value 的每个切片 bitmap 添加 x
    for (int i = 0; i < this.sliceSize(); i += 1) {
        if ((value & (1 << i)) > 0) {
            this.slices[i].add(key);
        } else {
            this.slices[i].remove(key);
        }
    }
    this.ebm.add(key);
}
```
> 一个 Key 只能设置一个 Value。

### 3.5 删除操作

#### 3.5.1 删除指定 Key

```java
public int remove(int key) {
    if (!this.containsKey(key)) {
        return -1;
    }
    return removeValueInternal(key);
}

private int removeValueInternal(int key) {
    int value = 0;
    for (int i = 0; i < this.sliceSize; i += 1) {
        // 切片 i 包含指定的 key 则关联的 value 第 i 位为 1
        if (this.slices[i].contains(key)) {
            value |= (1 << i);
            this.slices[i].remove(key);
        }
    }
    this.ebm.remove(key);
    return value;
}
```

#### 3.5.2 清空所有 Key

```java
public void clear() {
    this.maxValue = -1;
    this.minValue = -1;
    this.ebm = new RoaringBitmap();
    this.slices = null;
    this.sliceSize = 0;
}
```

### 3.6 精确数据查询操作

#### 3.6.1 包含查询

```java
public boolean containsKey(int key) {
    return this.ebm.contains(key);
}
```

#### 3.6.2 按 Key 查询

```java
public int get(int key) {
    if (!this.containsKey(key)) {
        return -1;
    }
    return getValueInternal(key);
}

private int getValueInternal(int key) {
    int value = 0;
    for (int i = 0; i < this.sliceSize; i += 1) {
        // 切片 i 包含指定的 key 则关联的 value 第 i 位为 1
        if (this.slices[i].contains(key)) {
            value |= (1 << i);
        }
    }
    return value;
}
```

#### 3.6.3 最小值查询

```java
public int minValue() {
    if (this.isEmpty()) {
        return -1;
    }

    RoaringBitmap keys = ebm;
    for (int i = this.sliceSize - 1; i >= 0; i -= 1) {
        RoaringBitmap tmp = RoaringBitmap.andNot(keys, slices[i]);
        if (!tmp.isEmpty()) {
            keys = tmp;
        }
    }

    return getValueInternal(keys.first());
}
```
#### 3.6.4 最大值查询

```java
public int maxValue() {
    if (this.isEmpty()) {
        return -1;
    }

    RoaringBitmap keys = ebm;
    for (int i = this.sliceSize - 1; i >= 0; i -= 1) {
        RoaringBitmap tmp = RoaringBitmap.and(keys, slices[i]);
        if (!tmp.isEmpty()) {
            keys = tmp;
        }
    }

    return getValueInternal(keys.first());
}
```

### 3.7 范围查询操作

#### 3.7.1 O'Neil 范围查询

```java
private RoaringBitmap oNeilRange(Operation operation, int value) {
    RoaringBitmap GT = new RoaringBitmap();
    RoaringBitmap LT = new RoaringBitmap();
    RoaringBitmap EQ = this.ebm; // 不需要 this.ebm.clone()
    // 从高位到低位开始遍历
    for (int i = this.sliceSize - 1; i >= 0; i--) {
        // 第 i 位的值 1或者0
        int bit = (value >> i) & 1;
        if (bit == 1) {
            LT = RoaringBitmap.or(LT, RoaringBitmap.andNot(EQ, this.slices[i]));
            EQ = RoaringBitmap.and(EQ, this.slices[i]);
        } else {
            GT = RoaringBitmap.or(GT, RoaringBitmap.and(EQ, this.slices[i]));
            EQ = RoaringBitmap.andNot(EQ, this.slices[i]);
        }
    }

    switch (operation) {
        case EQ:
            return EQ;
        case NEQ:
            return RoaringBitmap.andNot(this.ebm, EQ);
        case GT:
            return GT;
        case LT:
            return LT;
        case LE:
            return RoaringBitmap.or(LT, EQ);
        case GE:
            return RoaringBitmap.or(GT, EQ);
        default:
            throw new IllegalArgumentException("");
    }
}
```

#### 3.7.2 等于查询

```java
public RoaringBitmap eq(int value) {
    return oNeilRange(Operation.EQ, value);
}
```

#### 3.7.3 不等于查询

```java
public RoaringBitmap neq(int value) {
    return oNeilRange(Operation.NEQ, value);
}
```

#### 3.7.4 小于等于查询

```java
public RoaringBitmap le(int value) {
    return oNeilRange(Operation.LE, value);
}
```

#### 3.7.5 小于查询

```java
public RoaringBitmap lt(int value) {
    return oNeilRange(Operation.LT, value);
}
```

#### 3.7.6 大于等于查询

```java
public RoaringBitmap ge(int value) {
    return oNeilRange(Operation.GE, value);
}
```

#### 3.7.7 大于查询

```java
public RoaringBitmap gt(int value) {
    return oNeilRange(Operation.GT, value);
}
```

#### 3.7.8 区间查询

```java
public RoaringBitmap between(int lower, int upper) {
    RoaringBitmap lowerBitmap = oNeilRange(Operation.GE, lower);
    RoaringBitmap upperBitmap = oNeilRange(Operation.LE, upper);
    RoaringBitmap resultBitmap = lowerBitmap;
    resultBitmap.and(upperBitmap);
    return resultBitmap;
}
```

### 3.8 聚合计算操作

#### 3.8.1 求和

```java
public Long sum(RoaringBitmap rbm) {
    if (null == rbm || rbm.isEmpty()) {
        return 0L;
    }
    long sum = 0;
    for (int i = 0; i < this.sliceSize; i ++) {
        long sliceValue = 1 << i;
        sum += sliceValue * RoaringBitmap.andCardinality(this.slices[i], rbm);
    }
    return sum;
}
```

### 3.9 序列化操作
