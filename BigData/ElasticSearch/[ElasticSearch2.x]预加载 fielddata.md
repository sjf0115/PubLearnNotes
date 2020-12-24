Elasticsearch加载fielddata到内存中默认是惰性的（延迟加载）．Elasticsearch第一次遇到需要特定字段的fielddata的查询时，会将该整个字段加载到索引中每个段的内存中(The first time Elasticsearch encounters a query that needs fielddata for a particular field, it will load that entire field into memory for each segment in the index.)。

对于小的段来说，只需要很少的时间，可以忽略。 但是如果有几个5GB的段，并且需要将10 GB的fielddata加载到内存中，则此过程可能需要几十秒。已经习惯亚秒响应的用户将会被明显无响应的的网站所打击。

有三种方法可以解决这种延迟高峰：
- 预加载 fielddata(Eagerly load fielddata)
- 预加载全局序号(Eagerly load global ordinals)
- 缓存预热(Prepopulate caches with warmers)

所有这些都是相同概念的变体：预加载fielddata，以便在用户需要执行搜索时没有延迟高峰。

### 1. Eagerly load fielddata

第一个工具被称为预加载（与默认的延迟加载相反）。 随着新段被创建（通过`refresh`，`flush`或`merge`），启用预加载的字段都在段对搜索可见之前先预加载其每个段的fielddata(fields with eager loading enabled will have their per-segment fielddata preloaded before the segment becomes visible to search)．即，在对搜索不可见时就提前加载每个段的fielddata．

这就意味着首次命中分段的查询不需要促发 `fielddata` 的加载，因为 `fielddata` 已经被加载到内存缓存中。避免了用户遇到冷缓存延迟高峰的情形(This prevents your users from experiencing the cold cache latency spike.)。

预加载是按字段启用的，所以我们可以控制具体哪个字段可以预先加载：
```
PUT /music/_mapping/_song
{
  "tags": {
    "type": "string",
    "fielddata": {
      "loading" : "eager" 
    }
  }
}
```
通过设置`fielddata.loading：eager`，我们告诉Elasticsearch将该字段的内容预加载到内存中。

可以使用 `update-mapping` API对已有字段的`fielddata`加载方式设置为`lazy`或`eager`。

==警告==

预加载只是将加载fielddata 的代价进行转移了．转移到索引刷新的时候，而不是查询时，从而大大提高了搜索体验。

大段比小段需要花费更长的刷新(refresh)时间。 通常，大段都是通过合并已经可以搜索的小段而来，因此更慢的刷新时间并不重要。

### 2. Eagerly load global ordinals

#### 2.1 全局序号

有一种可以用来降低字符串`fielddata`内存使用的技术叫做 序号(ordinals) 。

想象一下，我们有十亿个文件，每个文件都有一个状态字段。 共有三个状态：`status_pending`，`status_published`，`status_deleted`。 如果我们在内存中为每个文档保留完整字符串状态，每个文档将需要14到16个字节，或总共大约15 GB。

相反，我们可以识别三个唯一的字符串，对它们进行排序，并对它们进行编号：0,1,2。

Ordinal|Term
---|---
0 | status_deleted
1 | status_pending
2 | status_published

序号字符串在序号列表中只存储一次，每个文档只要使用数值编号的序号来替代它原始的值。

Doc | Ordinal
---|---
0 | 1  # pending
1 | 1  # pending
2 | 2  # published
3 | 0  # deleted

内存的使用从15GB降到1GB．

但是有一个问题：请记住，fielddata缓存是对每个段而言。 如果一个段只包含两个状态 - `status_deleted`和`status_published`，那么生成的序数（0和1）将不会与包含所有三个状态的段的序数(上面是0,2)相同。

如果我们尝试在状态字段上运行`terms`聚合，我们需要根据实际的字符串值聚合，这意味着我们需要识别出所有段中相同的值(不同段，同一状态，序号可能不一样)。 这样做的一个自然的方法就是在每个段上运行聚合，从每个段返回字符串值，然后将从每个段返回的结果聚合为一个最终的整体结果。 虽然这样会起作用，但CPU速度会慢一些。

取而代之的是我们使用一个称为`全局序号`的数据结构。 全局序号是构架在fielddata之上的小型内存数据结构。 唯一的值可以在所有段中标识出，并存储在如我们已经描述的序号列表中。

现在，我们的`terms`聚合只在全局序号数据结构上进行聚合，而从序号到实际字符串值的转换只在聚合结束时发生一次。这将聚合（和排序）的性能提高了三到四倍。

#### 2.2 构建全局序号

当然，生活中没有什么是免费的。 全局序号跨越索引中的所有段，因此如果添加新段或删除旧段，则需要重新构建全局序号。重建需要查阅每个分段中的所有词条(term)。 基数越高 - 存在的唯一词条(term)越多，重建过程花费时间就越长。

全局序号是建立在内存中的fielddata和doc值之上。事实上，实际上，它们正是 doc values 性能表现不错的一个主要原因。

和`fielddata`加载一样，全局序号默认也是惰性的（延迟加载）。第一个需要`fielddata`命中索引的请求会触发全局序号的构建。由于字段的基数不同，这会给用户带来显著延迟。一旦全局序号发生重建，仍会使用旧的全局序号，直到索引中的分段产生变化：在`refresh`、`flush`或`merge`之后。

#### 2.3 Eager global ordinals

单个字符串字段可以配置为预先建立全局序数：
```
PUT /music/_mapping/_song
{
  "song_title": {
    "type": "string",
    "fielddata": {
      "loading" : "eager_global_ordinals" 
    }
  }
}
```

`loading`设置`eager_global_ordinals`表示预先加载fielddata。

与`fielddata`的预加载一样，预构建全局序号也是发生在新分段在对搜索可见之前。

==注意==

`序号`只能用于字符串。 数值型数据（integer，geopoints，date等）不需要序号映射，因为这些值自己本质上就是序号映射。

因此，只能为字符串字段启用预构建全局序号。

也可以对 Doc values 进行全局序号预构建：

```
PUT /music/_mapping/_song
{
  "song_title": {
    "type":       "string",
    "doc_values": true,
    "fielddata": {
      "loading" : "eager_global_ordinals" 
    }
  }
}
```
这种情况下，fielddata 没有载入到内存中，而是 doc values 被载入到文件系统缓存中。

与 fielddata 预加载不一样，预建全局序号会对数据的 实时性 产生影响，构建一个高基数的全局序号会使一个刷新延时数秒。 选择在于是每次刷新时付出代价，还是在刷新后的第一次查询时。如果经常索引而查询较少，那么在查询时付出代价要比每次刷新时要好。如果写大于读，那么在选择在查询时重建全局序号将会是一个更好的选择。

==提示==

针对实际场景优化全局序号的重建频次。如果我们有高基数字段需要花数秒钟重建，增加 refresh_interval 的刷新的时间从而可以使我们的全局序号保留更长的有效期，这也会节省 CPU 资源，因为我们重建的频次下降了。



### 3. Prepopulate caches with warmers
