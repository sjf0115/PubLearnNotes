## 1. Bit Slice Index 核心概念

Bit Slice Index (BSI) 是一种高效的数值索引结构，它将整数值按位分解到多个位图中，从而支持快速的范围查询、聚合计算等操作。结合 RoaringBitmap 的高效压缩位图实现，BSI 能够在保持高性能的同时显著减少内存使用。在这深入解析基于 RoaringBitmap 的 Bit Slice Index 算法实现 Rbm32BitSliceIndex。

## 2. 核心数据结构设计

### 2.1 关键成员变量

```java
public class Rbm32BitSliceIndex implements BitSliceIndex<Integer, Integer> {
    private int maxValue = -1;        // 存储的最大值
    private int minValue = -1;        // 存储的最小值
    private int sliceSize = 0;        // 切片个数（二进制位数）
    private RoaringBitmap[] slices;   // 位切片数组
    private RoaringBitmap ebm;        // 存在位图（Existence Bitmap）
    private Boolean runOptimized = false; // 运行优化标志
}
```
BSI 中会存储如下信息：
- Existence bitmap（ebm）：存在位图，存储 Key 的 RoaringBitmap。
- maxValue：存储的最大值。
- minValue：存储的最小值。
- sliceSize：切片个数，最大值的二进制位数。
- slices：切片 RoaringBitmap 数组，每个切片对应一个 RoaringBitmap。

### 2.2 数据结构原理

BSI(Bit Slice Index)本质上是对 KV 键值数据的压缩，将每个整数值分解为二进制表示，每个二进制位存储在一个独立的 RoaringBitmap 位图中。对于值 value，其二进制表示的第 i 位为 1 时，在 slices[i] 位图中记录对应的 key。下面以用户(key)与用户获取的积分(value)为例为你介绍 BSI 的原理与结构。

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

表中包含用户ID user_id 列和积分 score 列。其中，score 的最大值为 96，即二进制最大位数为 7 位，因此将所有 score 的二进制值补充为 7 位。然后对二进制数据从低位向高位遍历，将第 i 位值为 1 的 user_id 存入切片 RoaringBitmap 的 slices[i] 中，形成位切片索引 BSI(Bit Slice Index)。我们以 user_id 为 1 的用户为例介绍，该用户对应的积分 48(二进制 110000)：
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
  - `Rbm32BitSliceIndex(Integer minValue, Integer maxValue)`
- 容量管理操作
  - `void resize(int newSliceSize)`
- 基础操作
  - BSI 切片个数：`int sliceSize()`
  - BSI 基数：`long getLongCardinality()`
  - BSI 是否为空：`boolean isEmpty()`
  - 克隆 BSI：`BitSliceIndex clone()`
- 插入操作
  - `void put(Integer key, Integer value)`
- 删除操作
  - 删除指定 Key：`Integer remove(Integer key)`
  - 清空所有 Key：`void clear()`
- 精确查询操作
  - 包含查询：`boolean containsKey(Integer key)`
  - 按 Key 查询：`Integer get(Integer key)`
- 范围查询操作
  - 等于：`RoaringBitmap eq(Integer value)`
  - 不等于：`RoaringBitmap neq(Integer value)`
  - 小于：`RoaringBitmap lt(Integer value)`
  - 小于等于：`RoaringBitmap le(Integer value)`
  - 大于：`RoaringBitmap gt(Integer value)`
  - 大于等于：`RoaringBitmap ge(Integer value)`
  - 范围：`RoaringBitmap between(Integer lower, Integer upper)`
- 聚合计算操作
  - 求和：`Long sum(RoaringBitmap rbm)`

### 3.1 初始化操作

通过一个最小值和一个最大值来初始化 Bit Slice Index 的实现 Rbm32BitSliceIndex：
```java
public Rbm32BitSliceIndex(Integer minValue, Integer maxValue) {
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
索引切片个数 sliceSize 的计算是核心，它决定了 BSI 能够表示的最大数值范围。索引切片个数等于最大整数的二进制位数，可以通过 32 减去最大整数二进制0填充个数计算得到。每个切片表示一个二进制位，从低位(0)到高位(sliceSize-1)分别存储在一个独立的 RoaringBitmap 位图中。ebm 是 "Existence Bitmap" 的缩写，存储所有的 Key，用于快速判断 Key 是否存在。

### 3.2 容量管理

在上述初始化时根据设置的最大值来设置初始化容量，随着添加值的变化，可以动态调整 BSI 的容量：
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
如果调整的切片个数 newSliceSize 小于等于当前切片个数 sliceSize，说明当前容量已经足够表示新值，直接返回，避免不必要的扩容操作。如果需要扩容，容量调整逻辑按照如下调整：
- 根据新容量分配 RoaringBitmap 数组创建新的切片数组。
- 通过 System.arraycopy 高效拷贝旧切片数据
- 为新增的高位创建空 RoaringBitmap 来初始化新切片
- 切换至新数组并更新容量记录

### 3.3 基础操作

#### 3.3.1 BSI 切片个数

有专门的属性字段 sliceSize 来记录 BSI 切片个数，直接返回即可：
```java
public int sliceSize() {
    return sliceSize;
}
```
> 每个二进制位存储在一个独立的 Bitmap 中。BSI 切片个数即为 Bitmap 的个数。

#### 3.3.2 BSI 基数

BSI 基数即 BSI 中 Key 的个数，ebm 存储位图存储了所有的 Key，直接返回 ebm 位图的基数即可：
```java
public long getLongCardinality() {
    return this.ebm.getLongCardinality();
}
```

#### 3.3.3 BSI 是否为空

如果 BSI 基数为 0，表示 BSI 中没有存储 Key，是一个空 BSI：
```java
public boolean isEmpty() {
    return this.getLongCardinality() == 0;
}
```

#### 3.3.4 BSI 克隆

可以通过 `clone()` 方法克隆一个所有 KV 都一样的 BSI：
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
克隆 BSI 核心深拷贝属性字段和切片。

### 3.4  插入操作

可以通过 `put()` 方法来在 BSI 中添加一个新的 KV：
```java
public void put(Integer key, Integer value) {
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
    // 为指定的 Key 设置 Value
    putValueInternal(key, value);
}

private void putValueInternal(Integer key, Integer value) {
    // 为 value 的每个切片 bitmap 添加 key
    for (int i = 0; i < this.sliceSize(); i += 1) {
        if ((value & (1 << i)) > 0) {
            this.slices[i].add(key);
        } else {
            // 一个 Key 只能设置一个 Value，旧值会被新值覆盖。
            this.slices[i].remove(key);
        }
    }
    this.ebm.add(key);
}
```
首先根据为 key 设置的 value 来更新 BSI 的最大值和最小值。然后根据最大值的二进制位数来判断是否需要动态扩容，如果二进制位数比之前的大，则需要通过 `resize()` 方法来扩容。剩下最重要的事情就是为 BSI 添加新的 KV，核心逻辑是在 value 二进制位对应切片 RoaringBitmap 中添加 key：从低位到高位遍历切片 RoaringBitmap，如果 value 二进制位对应的 bit 为 1 则对应的切片 RoaringBitmap 添加 key。

> 一个 Key 只能设置一个 Value。

### 3.5 删除操作

#### 3.5.1 删除指定 Key

可以通过 `remove` 方法来删除指定的 Key：如果指定的 Key 存在则删除并返回对应的 Value，否则返回 -1：
```java
public Integer remove(Integer key) {
    // 不存在返回 -1
    if (!this.containsKey(key)) {
        return -1;
    }
    return removeValueInternal(key);
}

private Integer removeValueInternal(Integer key) {
    int value = 0;
    for (int i = 0; i < this.sliceSize; i += 1) {
        if (this.slices[i].contains(key)) {
            // 通过位图反向重建原始值
            value |= (1 << i);
            this.slices[i].remove(key);
        }
    }
    this.ebm.remove(key);
    return value;
}
```
首先通过 `containsKey()` 方法快速判断指定 Key 是否存在，如果不存在则返回 -1，表示 "not found" 语义。删除逻辑通过内部方法 `removeValueInternal` 实现，核心逻辑是在 value 二进制位对应切片 RoaringBitmap 中移除 key，并通过位移操作反向重建原始值。

#### 3.5.2 清空所有 KV

通过 `clear()` 方法来清空所有的 Key：
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

通过 `containsKey()` 方法判断是否存在指定的 Key：
```java
public boolean containsKey(Integer key) {
    return this.ebm.contains(key);
}
```

#### 3.6.2 按 Key 查询

可以通过 `get` 方法来查询指定的 Key 的 Value，如果指定的 Key 不存在则返回 -1：
```java
public Integer get(Integer key) {
    if (!this.containsKey(key)) {
        return -1;
    }
    return getValueInternal(key);
}

private Integer getValueInternal(Integer key) {
    int value = 0;
    for (int i = 0; i < this.sliceSize; i += 1) {
        if (this.slices[i].contains(key)) {
            // 通过位图反向重建原始值
            value |= (1 << i);
        }
    }
    return value;
}
```
可以看到按 Key 查询的核心实现逻辑与 `remove()` 方法删除指定 Key 的实现逻辑几乎一致，只是在 value 二进制位对应切片 RoaringBitmap 中不再需要移除 Key。

#### 3.6.3 最小值查询

可以通过 `minValue()` 查询 BSI 中的全局最小值，通过 `minValue(RoaringBitmap rbm)` 查询 BSI 中指定 Key 集合下的最小值：
```java
public Integer minValue() {
    return minValue;
}

public Integer minValue(RoaringBitmap rbm) {
    if (this.isEmpty() || Objects.equals(rbm, null) || rbm.getLongCardinality() == 0) {
        return -1;
    }
    // 指定 Key 与 BSI 中 Key 的交集
    RoaringBitmap keys = RoaringBitmap.and(rbm, ebm);
    if (keys.getLongCardinality() == 0) {
        return -1;
    }
    // 查询最小值
    for (int i = this.sliceSize - 1; i >= 0; i -= 1) {
        RoaringBitmap tmp = RoaringBitmap.andNot(keys, slices[i]);
        if (!tmp.isEmpty()) {
            keys = tmp;
        }
    }
    // 可能存在多个 Key 拥有最小值
    return getValueInternal(keys.first());
}
```
BSI 的全局最小值可以通过 minValue 属性直接返回。而查询指定 Key 集合下的最小值则稍微麻烦一些，需要从高位到低位遍历切片 RoaringBitmap。


#### 3.6.4 最大值查询

可以通过 `maxValue()` 查询 BSI 中的全局最大值，通过 `maxValue(RoaringBitmap rbm)` 查询 BSI 中指定 Key 集合下的最大值：
```java
public Integer maxValue() {
    return maxValue;
}

public Integer maxValue(RoaringBitmap rbm) {
    if (this.isEmpty() || Objects.equals(rbm, null) || rbm.getLongCardinality() == 0) {
        return -1;
    }
    // 指定 Key 与 BSI 中 Key 的交集
    RoaringBitmap keys = RoaringBitmap.and(rbm, ebm);
    if (keys.getLongCardinality() == 0) {
        return -1;
    }
    for (int i = this.sliceSize - 1; i >= 0; i -= 1) {
        RoaringBitmap tmp = RoaringBitmap.and(keys, slices[i]);
        if (!tmp.isEmpty()) {
            keys = tmp;
        }
    }
    // 可能存在多个 Key 拥有最大值
    return getValueInternal(keys.first());
}
```
BSI 的全局最大值可以通过 maxValue 属性直接返回。而查询指定 Key 集合下的最大值则稍微麻烦一些，需要从高位到低位遍历切片 RoaringBitmap。

### 3.7 范围查询操作

#### 3.7.1 O'Neil 范围查询

范围查询均是基于 O'Neil 范围查询算法实现：
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
- 第一步：初始化
  - EQ 初始化为全集 ebm 作为候选集合
  - GT 和 LT 初始化为空集合
- 第二步：从高位到低位迭代比较 EQ 候选集合中的值和查询值 Value 的 Bit 位大小
  - 比较策略：
    - 如果目标值 Bit 为 1，而 EQ 候选值 Bit 为 0，则说明该候选值小于目标值，则从 EQ 集合中转移到 LT 集合中
    - 如果目标值 Bit 为 0，而候选值 Bit 为 1，则说明该候选值大于目标值，则从 EQ 集合中转移到 GT 集合中
    - 如果目标值和候选值的 Bit 一样，则说明高位 Bit 目前还保持一致，还有相等的可能，继续留在 EQ 集合中
- 多轮迭代之后，大于查询值的 Key 存储在 GT 集合中，小于查询值的 Key 存储在 LT 集合中，等于查询值的 Key 存储在 EQ 集合中

根据查询操作选择对应的集合即可：
```java
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
```

#### 3.7.2 等于查询

等于查询使用 Operation.EQ 操作符返回 EQ 集合位图 RoaringBitmap，即返回等于指定 Value 的所有 Key：
```java
public RoaringBitmap eq(int value) {
    return oNeilRange(Operation.EQ, value);
}
```

#### 3.7.3 不等于查询

不等于查询使用 Operation.NEQ 操作符返回 ebm 和 EQ 与非操作的位图 RoaringBitmap，即返回不等于指定 Value 的所有 Key：
```java
public RoaringBitmap neq(int value) {
    return oNeilRange(Operation.NEQ, value);
}
```

#### 3.7.4 小于查询

小于查询使用 Operation.LT 操作符返回 LT 集合位图，即返回小于指定 Value 的所有 Key：
```java
public RoaringBitmap lt(int value) {
    return oNeilRange(Operation.LT, value);
}
```

#### 3.7.5 小于等于查询

小于等于查询使用 Operation.LE 操作符返回 LT 和 EQ 并集的位图，即返回小于等于指定 Value 的所有 Key：
```java
public RoaringBitmap le(int value) {
    return oNeilRange(Operation.LE, value);
}
```

#### 3.7.6 大于查询

大于查询使用 Operation.GT 操作符返回 GT 集合位图，即返回大于指定 Value 的所有 Key：
```java
public RoaringBitmap gt(int value) {
    return oNeilRange(Operation.GT, value);
}
```

#### 3.7.7 大于等于查询

大于等于查询使用 Operation.GE 操作符返回 LT 和 EQ 并集的位图，即返回大于等于指定 Value 的所有 Key：
```java
public RoaringBitmap ge(Integer value) {
    return oNeilRange(Operation.GE, value);
}
```

#### 3.7.8 区间查询

区间查询使用 Operation.GE 操作符返回大于等于 lower 的位图 lowerBitmap，使用 Operation.LE 操作符返回小于等于 upper 的位图 upperBitmap，区间查询的结果就是 lowerBitmap 和 upperBitmap 的交集：
```java
public RoaringBitmap between(Integer lower, Integer upper) {
    RoaringBitmap lowerBitmap = oNeilRange(Operation.GE, lower);
    RoaringBitmap upperBitmap = oNeilRange(Operation.LE, upper);
    RoaringBitmap resultBitmap = lowerBitmap;
    resultBitmap.and(upperBitmap);
    return resultBitmap;
}
```

### 3.8 聚合计算操作

#### 3.8.1 求和

可以通过 `SUM` 方法计算指定 Key 集合下 Value 的总和：
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
SUM 计算逻辑如下所示：
- 第一步：初始化 SUM 为 0
- 第二步：从低位到高位切片迭代累加
  - 每个切片的 SliceValue 从 1 开始，每迭代一次左移一次
  - 每轮都要计算 SliceValue 与切片上指定用户个数的乘积进行累加
- 多轮迭代之后 SUM 值就是最终我们指定用户的求和

## 4. 实战

以数据结构原理章节的用户与积分示例来实践操作如何使用 BSI。

### 4.1 构建 BSI

```java
Map<Integer, Integer> initMap = new HashMap<>();
Rbm32BitSliceIndex bsi = new Rbm32BitSliceIndex();
// 用户ID(user_id)、积分(score)
initMap.put(1, 48);
initMap.put(2, 80);
initMap.put(3, 75);
initMap.put(4, 19);
initMap.put(5, 1);
initMap.put(6, 57);
initMap.put(7, 63);
initMap.put(8, 22);
initMap.put(9, 96);
initMap.put(10, 34);
for (int key : initMap.keySet()) {
    bsi.put(key, initMap.get(key));
}
```

### 4.2 基础操作

```java
@Test
public void sliceTest() {
    int sliceSize = bsi.sliceSize();
    System.out.println("SliceSize: " + sliceSize);
    assert(sliceSize == 7);
}

@Test
public void getLongCardinalityTest() {
    long cardinality = bsi.getLongCardinality();
    System.out.println("Cardinality: " + cardinality);
    assert(cardinality == 10);
}

@Test
public void isEmptyTest() {
    boolean isEmpty = bsi.isEmpty();
    System.out.println("IsEmpty: " + isEmpty);
    assert(isEmpty == false);
}
```

### 4.3 精确查询操作

```java
@Test
public void containsKeyExistTest() {
    boolean isExist = bsi.containsKey(10);
    System.out.println("isExist: " + isExist);
    assert(isExist == true);
}

@Test
public void containsKeyNoExistTest() {
    boolean isExist = bsi.containsKey(11);
    System.out.println("isExist: " + isExist);
    assert(isExist == false);
}

@Test
public void getTest() {
    int value = bsi.get(10);
    System.out.println("Value: " + value);
    assert(value == 34);
}
```

### 4.4 极值查询操作

```java
@Test
public void maxValueTest() {
    int maxValue = bsi.maxValue();
    System.out.println("MaxValue: " + maxValue);
    assert(maxValue == 96);
}

@Test
public void maxValueByKeysTest() {
    RoaringBitmap rbm = new RoaringBitmap();
    rbm.add(3,4,6,7);
    int maxValue = bsi.maxValue(rbm);
    System.out.println("MaxValue: " + maxValue);
    assert(maxValue == 75);
}

@Test
public void minValueTest() {
    int minValue = bsi.minValue();
    System.out.println("MinValue: " + minValue);
    assert(minValue == 1);
}

@Test
public void minValueByKeysTest() {
    RoaringBitmap rbm = new RoaringBitmap();
    rbm.add(3,4,6,7);
    int minValue = bsi.minValue(rbm);
    System.out.println("MinValue: " + minValue);
    assert(minValue == 19);
}
```

### 4.5 范围查询操作

```java
@Test
public void eqTest() {
    RoaringBitmap eqBitmap = bsi.eq(57);
    // 6
    for (int key : eqBitmap.toArray()) {
        System.out.println("key: " + key + ", value: " + bsi.get(key));
    }
}

@Test
public void neqTest() {
    RoaringBitmap neqBitmap = bsi.neq(57);
    // 1,2,3,4,5,7,8,9,10
    for (int key : neqBitmap.toArray()) {
        System.out.println("key: " + key + ", value: " + bsi.get(key));
    }
}

@Test
public void leTest() {
    RoaringBitmap leBitmap = bsi.le(57);
    // 1,4,5,6,8,10
    for (int key : leBitmap.toArray()) {
        System.out.println("key: " + key + ", value: " + bsi.get(key));
    }
}

@Test
public void ltTest() {
    RoaringBitmap ltBitmap = bsi.lt(57);
    // 1,4,5,8,10
    for (int key : ltBitmap.toArray()) {
        System.out.println("key: " + key + ", value: " + bsi.get(key));
    }
}

@Test
public void geTest() {
    RoaringBitmap geBitmap = bsi.ge(57);
    // 2,3,6,7,9
    for (int key : geBitmap.toArray()) {
        System.out.println("key: " + key + ", value: " + bsi.get(key));
    }
}

@Test
public void gtTest() {
    RoaringBitmap gtBitmap = bsi.gt(57);
    // 2,3,7,9
    for (int key : gtBitmap.toArray()) {
        System.out.println("key: " + key + ", value: " + bsi.get(key));
    }
}

@Test
public void betweenTest() {
    RoaringBitmap betweenBitmap = bsi.between(57, 83);
    // 2,3,6,7
    for (int key : betweenBitmap.toArray()) {
        System.out.println("key: " + key + ", value: " + bsi.get(key));
    }
}
```

### 4.6 SUM

```java
@Test
public void sumTest() {
    RoaringBitmap rbm = RoaringBitmap.bitmapOf(3,6,8,9);
    long sum = bsi.sum(rbm);
    System.out.println("Sum: " + sum);
    assertEquals(250L, sum);
}
```
