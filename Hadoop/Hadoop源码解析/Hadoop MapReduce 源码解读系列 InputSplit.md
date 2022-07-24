
## 1. 什么是 InputSplit


## 2. 如何划分 InputSplit

```
long minSize = Math.max(getFormatMinSplitSize(), getMinSplitSize(job));
long maxSize = getMaxSplitSize(job);
```

```java
protected long computeSplitSize(long blockSize, long minSize, long maxSize) {
  return Math.max(minSize, Math.min(maxSize, blockSize));
}
```
