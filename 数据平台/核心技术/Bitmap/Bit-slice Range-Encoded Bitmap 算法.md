

![](img-bit-slice-range-encoded-bitmap-algorithm-1.png)

- 第一步：初始化
  - EQ 初始化为全集作为候选集合
  - GT 和 LT 初始化为空集合
- 第二步：EQ 候选集合中的值和对比值的 Bit 位从高位开始迭代比较
  - 比较策略：
    - 如果目标值 Bit 为 1，而 EQ 候选值 Bit 为 0，则说明该候选值小于目标值，则从 EQ 集合中转移到 LT 集合中
    - 如果目标值 Bit 为 0，而候选值 Bit 为 1，则说明该候选值大于目标值，则从 EQ 集合中转移到 GT 集合中
    - 如果目标值和候选值的 Bit 一样，则说明高位 Bit 目前还保持一致，还有相等的可能，继续留在 EQ 集合中



给定一个值 value 计算位切片索索引切片个数：
```java
32 - Integer.numberOfLeadingZeros(value)
```
> Integer.numberOfLeadingZeros 方法用于返回一个整数的二进制表示中最高非零位之前 0 的个数。Integer 二进制 32 位减去填充 0 的个数即为整数二进制有效位数。

例如，51 的二进制为 `110011`，所以索引切片为 32 - 26 = 6 个。
