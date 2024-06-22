### 1. 概述

Bitsets（也称为Bitmaps）通常用作快速数据结构。不幸的是，他们可能会占用太多内存。为了降低内存的使用，我们经常会使用压缩的位图。

Roaring Bitmaps 是一种压缩的位图，要优于常规的压缩位图，例如 WAH，EWAH 或者 Concise。在某些情况下，可以比它们快几百倍，并且通常提供更好的压缩。

Roaring Bitmaps 已经被很多重要系统使用：
- [Apache Lucene](http://lucene.apache.org/core/)
- [Apache Druid](http://druid.io/)
- [Apache Spark](http://spark.apache.org/)
- [Apache CarbonData](https://github.com/Netflix/atlas)
- [LinkedIn Pinot](https://github.com/linkedin/pinot/wiki)
- [Apache Kylin](http://kylin.io/)

几乎所有流行的编程语言（Java，C，C ++，Go，C＃，Rust，Python ......）都提供了 Roaring Bitmaps。

### 2. 主要思想

我们以存放 Integer 值的 Bitmap 来举例，RBM 把一个 32 位的 Integer 划分为高 16 位和低 16 位，通过高 16 位找到该数据存储在哪个桶中（高 16 位可以划分 2^16 个桶），把剩余的低 16 位放入该桶对应的 Container 中。

每个桶都有对应的 Container，不同的 Container 存储方式不同。依据不同的场景，主要有 2 种不同的 Container，分别是 Array Container 和 Bitmap Container。Array Container 存放稀疏的数据，Bitmap Container 存放稠密的数据。若一个 Container 里面的元素数量小于 4096，使用 Array Container 来存储。当 Array Container 超过最大容量 4096 时，会转换为 Bitmap Container。

### 3. Array Container

Array Container 是 Roaring Bitmap 初始化默认的 Container。Array Container 适合存放稀疏的数据，其内部数据结构是一个有序的 Short 数组。数组初始容量为 4，数组最大容量为 4096，所以 Array Container 是动态变化的，当容量不够时，需要扩容，并且当超过最大容量 4096 时，就会转换为 Bitmap Container。由于数组是有序的，存储和查询时都可以通过二分查找快速定位其在数组中的位置。

> 后面会讲解为什么超过最大容量 4096 时变更 Container 类型。

下面我们具体看一下数据如何被存储的，例如，0x00020032（十进制131122）放入一个 RBM 的过程如下图所示：

![](roaring-bitmap-introduce-1.png#pic_center)

0x00020032 的前 16 位是 0002，找到对应的桶 0x0002。在桶对应的 Container 中存储低 16 位，因为 Container 元素个数不足 4096，因此是一个 Array Container。低 16 位为 0032（十进制为50）, 在 Array Container 中二分查找找到相应的位置插入即可（如上图50的位置）。

相较于原始的 Bitmap 需要占用 16K (131122/8/1024) 内存来存储这个数，而这种存储实际只占用了4B（桶中占 2 B，Container中占 2 B，不考虑数组的初始容量）。

### 4. Bitmap Container

第二种 Container 是 Bitmap Container。它的数据结构是一个 Long 数组，数组容量恒定为 1024，和上文的 Array Container 不同，Array Container 是一个动态扩容的数组。Bitmap Container 不用像 Array Container 那样需要二分查找定位位置，而是可以直接通过下标直接寻址。

由于每个 Bitmap Container 需要处理低 16 位数据，也就是需要使用 Bitmap 来存储需要 8192 B（2^16/8）, 而一个 Long 值占 8 个 B，所以数组大小为 1024。因此一个 Bitmap Container 固定占用内存 8 KB。

下面我们具体看一下数据如何被存储的，例如，0xFFFF3ACB（十进制4294916811）放入一个 RBM 的过程如下图所示：

![](roaring-bitmap-introduce-2.png#pic_center)

0xFFFF3ACB 的前 16 位是 FFFF，找到对应的桶 0xFFFF。在桶对应的 Container 中存储低 16 位，因为 Container 中元素个数已经超过 4096，因此是一个 Bitmap Container。低 16 位为 3ACB（十进制为15051）, 因此在 Bitmap Container 中通过下标直接寻址找到相应的位置，将其置为 1 即可（如上图15051的位置）。

![](roaring-bitmap-introduce-3.png#pic_center)

可以看到元素个数达到 4096 之前，Array Container 占用的空间比 Bitmap Container 的少，当 Array Container 中元素到 4096 个时，正好等于 Bitmap Container 所占用的 8 KB。当元素个数超过了 4096 时，Array Container 所占用的空间还是继续线性增长，而 Bitmap Container 的内存空间并不会增长，始终还是占用 8 KB，与数据量无关。所以当 Array Container 超过最大容量 4096 会转换为 Bitmap Container。

## 5. 实践案例
- [货拉拉大数据对BitMap的探索与实践(上)](https://smartsi.blog.csdn.net/article/details/128891918)
- [货拉拉大数据对Bitmap的探索与实践（下）](https://smartsi.blog.csdn.net/article/details/128892077)
- [RoaringBitMap在B站大数据中的应用](https://smartsi.blog.csdn.net/article/details/127724706)
- [大数据分析常用去重算法分析之Bitmap](https://smartsi.blog.csdn.net/article/details/128882620)
- [美团 Doris Bitmap 精确去重优化实践](https://smartsi.blog.csdn.net/article/details/135893650)
- [Hologres RoaringBitmap实践：千亿级画像数据秒级分析](https://smartsi.blog.csdn.net/article/details/134223290)
- [Hive 实战：位图 Bitmap 系列-bitmap_and 函数实现解析](https://smartsi.blog.csdn.net/article/details/139549497)
- [Hive 实战：位图 Bitmap 系列-group_bitmap UDAF 实现解析](https://smartsi.blog.csdn.net/article/details/139575557)
- [Hive 实战：位图 Bitmap 系列-位图计算函数](https://smartsi.blog.csdn.net/article/details/139701146)

参考: [不深入而浅出 Roaring Bitmaps 的基本原理](https://cloud.tencent.com/developer/article/1136054)
