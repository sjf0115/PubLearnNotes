

Bitmap(也称为位数组或者位向量等)是一种实现对位的操作的'数据结构'，在数据结构加引号主要因为：
- Bitmaps 本身不是一种数据结构，实际上就是字符串，但是可以对字符串进行位操作。
- Bitmaps 单独提供了一套命令，所以与使用字符串的方法不太相同。可以把 Bitmaps 想象成一个以位为单位的数组，数组的每个单元只能存储 0 和 1，数组的下标在 Bitmaps 中叫做偏移量。

Redis 是一个内存数据结构服务器，提供了对位操作的支持。然而，在 Redis 中 Bitmaps 并不是一个特殊的数据结构。相反，位操作在基本的 Redis 结构 String 上是支持的。现在，Redis 字符串的最大长度是 512 MB。因此，Redis 可以转换为 Bitmap 的最大域是 232 (512 MB = 229 bytes = 232 bits)。


## 2. 命令

本节将每个独立用户是否访问过网站存放在Bitmaps中，将访问的用户记做1，没有访问的用户记做0，用偏移量作为用户的id。

### 2.1 SETBIT

> 最早可用版本：2.2.0。时间复杂度：O(1)。

语法格式：
```
SETBIT KEY OFFSET VALUE
```

SETBIT 用来设置 KEY 对应第 OFFSET 位的值（OFFSET 从 0 开始算），可以设置为 0 或者 1。当指定的 KEY 不存在时，会自动生成一个新的字符串值。字符串会进行扩展以确保可以将 VALUE 保存在指定的偏移量 OFFSET 上。当字符串值进行扩展时，空白位置用 0 来填充。需要注意的是 OFFSET 需要大于或等于 0，小于 2 的 32 次方(即 Bitmap 上限为 512 MB，因为 Redis 字符串的最大长度是 512 MB)。

> 当设置最后一个 bit 位（偏移量等于 2^32 -1）并且存储在 key 的字符串值还没有创建，或者只保存了一个小的字符串值时，Redis 需要分配所需要的所有内存，这会阻塞服务器的一段时间。在 2010 款 MacBook Pro 上，设置第 2^32 -1 位（需要分配 512MB 内存）大约需要 300 毫秒，设置第 2^30 -1 位（128 MB）大约需要 80 毫秒，设置第 2^28 -1 位（32MB）需要约 30 毫秒，设置第 2^26 -1（8MB）需要约 8 毫秒。一旦完成第一次分配，随后对同一 KEY 的 SETBIT 调用将不会产生分配开销。

假设现在有 10 个用户，用户id为 0、1、5、9 的 4 个用户对网站进行了访问，那么当前 Bitmaps 初始化结果如下图所示：

![](1)

具体操作过程如下，uv:20220514 代表 20220514 这天的所有访问用户的 Bitmaps：
```
127.0.0.1:6379> setbit uv:20220514 0 1
(integer) 0
127.0.0.1:6379> setbit uv:20220514 1 1
(integer) 0
127.0.0.1:6379> setbit uv:20220514 5 1
(integer) 0
127.0.0.1:6379> setbit uv:20220514 9 1
(integer) 0
```
假设用户 uid 为 15 的用户访问了网站，那么 Bitmaps 的结构变成了如下图，第 10 位到第 14 位都用 0 填充，第15位被置为 1：

![](2)

> 很多应用的用户id以一个指定数字（例如 150000000000）开头，直接将用户id和 Bitmaps 的偏移量对应势必会造成一定的浪费，通常的做法是每次做 setbit 操作时将用户id减去这个指定数字。在第一次初始化 Bitmaps 时，假如偏移量非常大，那么整个初始化过程执行会比较慢，可能会造成 Redis 的阻塞。

### 2.2 GETBIT

> 最早可用版本：2.2.0。时间复杂度：O(1)。

语法格式：
```
GETBIT KEY OFFSET
```
获取 KEY 对应第 OFFSET 位的值（从 0 开始算）。当 OFFSET 超过字符串长度时，字符串假定为一个 0 位的连续空间。当指定的 KEY 不存在时，被假定为一个空字符串，OFFSET 肯定是超出字符串长度范围，因此该值也被假定为 0 位的连续空间。

下面获取用户id为 4 的用户是否在 20220514 这天访问过，返回 0 说明没有访问过：
```
127.0.0.1:6379> getbit uv:20220514 4
(integer) 0
```
下面获取用户id为 5 的用户是否在 20220514 这天访问过，返回 1 说明访问过：
```
127.0.0.1:6379> getbit uv:20220514 5
(integer) 1
```
下面获取用户id为 20 的用户是否在 20220514 这天访问过，因为 OFFSET 20 根本就不存在，所以返回结果也是 0：
```
127.0.0.1:6379> getbit uv:20220514 20
(integer) 1
```

### 2.3 BITCOUNT

> 最早可用版本：2.6.0。时间复杂度： O(N)。

语法格式：
```
BITCOUNT KEY [ start end [ BYTE | BIT]]
```
用来计算指定 KEY 对应字符串中，被设置为 1 的 bit 位的数量。一般情况下，字符串中所有 bit 位都会参与计数，我们可以通过指定额外的 start 或 end 参数，只计算指定范围内被设置为 1 的 bit 位的数量。start 和 end 参数的设置和 GETRANGE 命令类似，都可以使用负数：比如 -1 表示最后一个位，而 -2 表示倒数第二个位等。

下面计算 20220514 这天所有的访问用户数量：
```
127.0.0.1:6379> bitcount uv:20220514
(integer) 5
```
下面计算用户id在第 4 个 bit 到第 10 个 bit 之间的所有访问用户数，对应的用户id是 5、9：
```
127.0.0.1:6379> bitcount uv:20220514 4 10 bit
(integer) 2
```
> 从 Redis 7.0.0 开始支持 BYTE 或者 BIT 选项

### 2.4 Bitmaps 间的运算

> 最早可用版本：2.6.0。时间复杂度： O(N)。

语法格式：
```
BITOP operation destkey key [key ...]
```
BITOP 是一个复合操作，支持在多个 key 之间执行按位运算并将结果存储在 destkey 指定的 key 中。BITOP 命令支持四种按位运算：AND(交集)、OR(并集)、XOR(异或) 和 NOT(非)：
```
BITOP AND destkey srckey1 srckey2 srckey3 ... srckeyN
BITOP OR destkey srckey1 srckey2 srckey3 ... srckeyN
BITOP XOR destkey srckey1 srckey2 srckey3 ... srckeyN
BITOP NOT destkey srckey
```
如上所见，NOT 很特殊，因为它只需要一个输入 key，因为它执行位反转，因此它仅作为一元运算符才有意义。

假设 20220513 访问网站的用户id为 1、3、5、7，如下图所示：

![](3)

下面计算 20220513 和 20220514 两天都访问过网站的用户数量：
```
127.0.0.1:6379> bitop and uv:20220513:and:20220514 uv:20220513 uv:20220514
(integer) 2
127.0.0.1:6379> bitcount uv:20220513:and:20220514
(integer) 2
```
如果想算出 20220513 和 20220514 任意一天都访问过网站的用户数量，可以使用or求并集，具体命令如下：
```
127.0.0.1:6379> bitop or uv:20220513:and:20220514 uv:20220513 uv:20220514
(integer) 2
127.0.0.1:6379> bitcount uv:20220513:or:20220514
(integer) 2
```

https://redis.io/docs/manual/data-types/data-types-tutorial/#bitmaps
https://scalegrid.io/blog/introduction-to-redis-data-structure-bitmaps/
