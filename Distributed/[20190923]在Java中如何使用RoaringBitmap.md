
### 1.1 ImmutableRoaringBitmap

ImmutableRoaringBitmap 提供一种压缩的不可变（不可修改）位图。应与 MutableRoaringBitmap 一起使用，这是一个派生类，添加了修改位图的方法。因为 ImmutableRoaringBitmap 类不是最终类，并且因为存在一个派生类（MutableRoaringBitmap），所以程序员可以修改某些 ImmutableRoaringBitmap 实例，但这会涉及强制转换：如果你的代码是用 ImmutableRoaringBitmap 实例编写，那么您的对象将是真正不可变的，因此很容易推理。

ImmutableRoaringBitmap 的纯（非派生）实例的数据存储在 ByteBuffer 中。这样做的好处是可以从 ByteBuffer 构造它们（用于内存映射）。此类的对象几乎可以完全驻留在内存映射文件中。这也是它们被视为不可变的主要原因，因为使用内存映射文件时无法重新分配。

我们将MutableRoaringBitmap实例转换为ImmutableRoaringBitmap实例的设计的动机之一是，位图通常很大，或者在避免内存分配的环境中使用，因此避免了强制复制。 如果需要混合并匹配ImmutableRoaringBitmap和MutableRoaringBitmap实例，则可以预期会有副本。

### 1.2 MutableRoaringBitmap

MutableRoaringBitmap，BitSet的压缩替代形式。与 RoaringBitmap 相似，但是不同之处在于，它可以与ImmutableRoaringBitmap对象进行交互，即MutableRoaringBitmap是从MutableRoaringBitmap派生的。

MutableRoaringBitmap 是 ImmutableRoaringBitmap 的实例（在其中实现了'序列化'之类的方法）。也就是说，它们都共享相同的核心（不可变）方法，但是 MutableRoaringBitmap 添加了修改对象的方法。这种设计使我们可以在需要时将 MutableRoaringBitmap 用作 ImmutableRoaringBitmap 实例。

MutableRoaringBitmap 可以像 RoaringBitmap 实例一样使用，它们序列化为相同的输出。RoaringBitmap 实例将更快，因为它不承载 ByteBuffer 后端的开销，但是 MutableRoaringBitmap 可以用作 ImmutableRoaringBitmap 实例。因此，如果使用 ImmutableRoaringBitmap，则可能还需要使用 MutableRoaringBitmap 实例。如果您不使用 ImmutableRoaringBitmap，则可能只想使用 RoaringBitmap 实例。





https://github.com/RoaringBitmap/RoaringBitmap





。。。
