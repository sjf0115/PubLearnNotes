

男 - bitmap(user_id)

1678 - bitSlice(user_id, 1678)







Collection<Integer> values();





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




## 1. 存储结构

BSI(Bit Slice Index)本质上是对 KV 键值数据的压缩。下面以用户与用户获取的积分为例为你介绍 BSI 的原理与结构。

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

表中包含用户ID user_id 列和积分 score 列。其中，score 的最大值为 96，即二进制最大位数为 7 位，因此将所有 score 的二进制值补充为 7 位。然后对二进制数据从低位向高位遍历，将位值为 1 的 user_id 存入切片 RoaringBitmap 数组的 slices 中(`RoaringBitmap[] slices`)，形成位切片索引 BSI(Bit Slice Index)。上表数据最终建立了如下切片索引：

| 切片 | user_id |
| :------------- | :------------- |
| slices[0] | 3,4,5,6,7 |
| slices[1] | 3,4,7,8,10 |
| slices[2] | 7,8 |
| slices[3] | 3,6,7 |
| slices[4] | 1,2,4,6,7,8 |
| slices[5] | 1,6,7,9,10 |
| slices[6] | 2,3,9 |

> 每个切片对应一个 RoaringBitmap，RoaringBitmap 中存储 user_id

此外，BSI 中还会存储如下信息：
- Existence bitmap（ebm）：存储 user_id 数组的 RoaringBitmap，本示例中为 RoaringBitmap '{1,2,3,4,5,6,7,8,9,10}'。
- maxValue：score 的最大值，本示例为 96。
- minValue：score 的最小值，本示例为 1。
- sliceSize：切片个数，最大 score 的二进制位数，本示例为 7。

存储结构
```java
private int maxValue;
private int minValue;
private RoaringBitmap[] slices;
private RoaringBitmap ebm;
```






## 2. 容量空间

根据指定的最小值和最大值判断位切片索引容量空间是否需要扩容：
```java
// 容量空间
private void ensureCapacityInternal(int minValue, int maxValue) {
    if (ebm.isEmpty()) {
        // 更新最小值、最大值 - 增大容量空间
        this.minValue = minValue;
        this.maxValue = maxValue;
        grow(Integer.toBinaryString(maxValue).length());
    } else if (this.minValue > minValue) {
        // 更新最小值 - 容量空间保持不变
        this.minValue = minValue;
    } else if (this.maxValue < maxValue) {
        // 更新最大值 - 增大容量空间
        this.maxValue = maxValue;
        grow(Integer.toBinaryString(maxValue).length());
    }
}
```
如果当前位切片索引为空需要根据最大值初始化容量空间
如果位切片索引不为空，但是最大值发生了变化则需要扩大容量空间

> 最大值决定了容量空间，最小值发生变化不需要扩容

### 扩容

```java
private void grow(int newBitNum) {
    int bitNum = this.rbm.length;

    if (bitNum >= newBitNum) {
        return;
    }

    // 拷贝
    RoaringBitmap[] newRbm = new RoaringBitmap[newBitNum];
    if (bitNum != 0) {
        System.arraycopy(this.rbm, 0, newRbm, 0, bitNum);
    }

    for (int i = newBitNum - 1; i >= bitNum; i--) {
        newRbm[i] = new RoaringBitmap();
        if (this.runOptimized) {
            newRbm[i].runOptimize();
        }
    }
    this.rbm = newRbm;
}
```


## 查找

```java
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
例如 key 为 user_id = 6，则该 key 在切片 0，3，4，5 中，通过计算 value 为 57(二进制 111001)。

## 范围查询

```java
private RoaringBitmap oNeilRange(Operation operation, int value) {
    RoaringBitmap GT = new RoaringBitmap();
    RoaringBitmap LT = new RoaringBitmap();
    RoaringBitmap EQ = this.ebm;

    for (int i = this.sliceSize - 1; i >= 0; i--) {
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
## SUM

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

...
