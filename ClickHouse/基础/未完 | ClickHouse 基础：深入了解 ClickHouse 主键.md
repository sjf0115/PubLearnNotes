ClickHouse 的主键设计与传统 OLTP 数据库的 B 树索引有本质区别，其核心在于通过稀疏索引和有序存储优化分析查询。本文为您介绍 ClickHouse 主键概念及最佳实践。

## 1. 主键误区

对于初次使用 ClickHouse 的用户，经常难以完全理解其独特的主键概念。通常会有以下误区。
- 误区1：主键唯一性
  - ClickHouse 主键不强制唯一，重复主键行也可共存，由 ORDER BY 子句决定数据存储顺序。
- 误区2：主键等同于索引
  - 主键仅保证数据有序，过滤非首列时可能仍需扫描多数据块，需配合跳数索引使用。

## 2. 了解主键

ClickHouse 与基于 B+ Tree 的 OLTP 数据库不同，它使用了一个稀疏索引，该索引针对每秒插入的数百万行以及 PB 级数据集进行了设计。与 OLTP 数据库相反，

在 ClickHouse 中选择一个有效的主键对查询性能和存储效率至关重要。ClickHouse 将数据组织为多个数据分片 Part，每个数据分片 Part 都包含自己的稀疏主键索引。该索引通过减少扫描的数据量显著加快查询速度。此外，由于主键决定了磁盘上数据的物理排序，它会直接影响压缩效率。数据排序越合理，压缩效果越好，从而通过减少 I/O 进一步提升性能。ClickHouse 的索引具有以下特点：
- 有序存储
  - 数据按 ORDER BY 指定的主键顺序存储在磁盘上，每个 data part 内部严格排序，以快速识别可能匹配查询的数据。
- 稀疏索引
  - ClickHouse 的索引为稀疏索引，其以固定粒度（如每8192行）记录主键值，形成轻量级索引。查询时，索引快速定位可能匹配的 data part，随后在块内顺序扫描筛选目标行。
- 设计特点
  - 针对海量数据插入（每秒百万行）和PB级分析查询优化，牺牲点查询效率，换取高吞吐范围查询和卓越压缩率。

## 3. 示例

假设我们有一张 `posts_unordered` 表，每一行对应一个 Stack Overflow 帖子：
```sql
CREATE TABLE posts_unordered (
  `Id` Int32,
  `PostTypeId` Enum('Question' = 1, 'Answer' = 2, 'Wiki' = 3, 'TagWikiExcerpt' = 4,
  'TagWiki' = 5, 'ModeratorNomination' = 6, 'WikiPlaceholder' = 7, 'PrivilegeWiki' = 8),
  `AcceptedAnswerId` UInt32,
  `CreationDate` DateTime,
  `Score` Int32,
  `ViewCount` UInt32,
  `Body` String,
  `OwnerUserId` Int32,
  `OwnerDisplayName` String,
  `LastEditorUserId` Int32,
  `LastEditorDisplayName` String,
  `LastEditDate` DateTime,
  `LastActivityDate` DateTime,
  `Title` String,
  `Tags` String,
  `AnswerCount` UInt16,
  `CommentCount` UInt8,
  `FavoriteCount` UInt8,
  `ContentLicense`LowCardinality(String),
  `ParentId` String,
  `CommunityOwnedDate` DateTime,
  `ClosedDate` DateTime
)
ENGINE = MergeTree
ORDER BY tuple()
```
现在用户希望计算在 2024 年之后提交的问题(PostTypeId='Question')数量，这是一种最常见的访问模式：
```sql
SELECT count()
FROM stackoverflow.posts_unordered
WHERE (CreationDate >= '2024-01-01') AND (PostTypeId = 'Question')

┌─count()─┐
│  192611 │
└─────────┘
1 row in set. Elapsed: 0.055 sec. Processed 59.82 million rows, 361.34 MB (1.09 billion rows/s., 6.61 GB/s.)
```
注意观察此查询读取的行数和字节数。在没有主键的情况下，查询必须扫描整个数据集。可以使用 `EXPLAIN indexes=1` 可以确认，由于缺少索引，执行的是全表扫描：
```sql
EXPLAIN indexes = 1
SELECT count()
FROM stackoverflow.posts_unordered
WHERE (CreationDate >= '2024-01-01') AND (PostTypeId = 'Question')

┌─explain───────────────────────────────────────────────────┐
│ Expression ((Project names + Projection))                 │
│   Aggregating                                             │
│     Expression (Before GROUP BY)                          │
│       Expression                                          │
│         ReadFromMergeTree (stackoverflow.posts_unordered) │
└───────────────────────────────────────────────────────────┘

5 rows in set. Elapsed: 0.003 sec.
```

假设我们有一张 `posts_ordered` 的表，包含相同的数据，其定义中的 ORDER BY 为 `(PostTypeId, toDate(CreationDate))`：
```sql
CREATE TABLE posts_ordered (
  `Id` Int32,
  `PostTypeId` Enum('Question' = 1, 'Answer' = 2, 'Wiki' = 3, 'TagWikiExcerpt' = 4, 'TagWiki' = 5, 'ModeratorNomination' = 6,
  'WikiPlaceholder' = 7, 'PrivilegeWiki' = 8),
...
)
ENGINE = MergeTree
ORDER BY (PostTypeId, toDate(CreationDate))
```
> 如果我们只指定了排序键，那么主键会被隐式定义为与排序键相同。

`PostTypeId` 的基数为 8，是排序键中第一列的首选。考虑到按日期粒度进行过滤通常已经足够，因此我们使用 `toDate(CreationDate)` 作为排序键的第二列。这样还会生成更小的索引，因为日期可以用 16 位来表示，从而加快过滤速度。

如果在具有此排序键的表上重复执行相同的查询：
```sql
SELECT count()
FROM stackoverflow.posts_ordered
WHERE (CreationDate >= '2024-01-01') AND (PostTypeId = 'Question')

┌─count()─┐
│  192611 │
└─────────┘
1 row in set. Elapsed: 0.013 sec. Processed 196.53 thousand rows, 1.77 MB (14.64 million rows/s., 131.78 MB/s.)
```
此查询现在利用稀疏索引，显著减少了读取的数据量，并将执行时间提升了 4 倍，请注意读取的行数和字节数的减少。下列动画展示了如何为 Stack Overflow 的 posts_ordered 表创建一个经过优化的稀疏主索引。索引针对的是数据块，而不是单独的行：

![](https://clickhouse.com/docs/zh/assets/images/create_primary_key-bb475e4c7dfa59c2e5693c828e984e0f.gif)

可以通过执行 `EXPLAIN indexes=1` 来确认是否使用了该索引：
```sql
EXPLAIN indexes = 1
SELECT count()
FROM stackoverflow.posts_ordered
WHERE (CreationDate >= '2024-01-01') AND (PostTypeId = 'Question')

┌─explain─────────────────────────────────────────────────────────────────────────────────────┐
│ Expression ((Project names + Projection))                                                   │
│   Aggregating                                                                               │
│     Expression (Before GROUP BY)                                                            │
│       Expression                                                                            │
│         ReadFromMergeTree (stackoverflow.posts_ordered)                                     │
│         Indexes:                                                                            │
│           PrimaryKey                                                                        │
│             Keys:                                                                           │
│               PostTypeId                                                                    │
│               toDate(CreationDate)                                                          │
│             Condition: and((PostTypeId in [1, 1]), (toDate(CreationDate) in [19723, +Inf))) │
│             Parts: 14/14                                                                    │
│             Granules: 39/7578                                                               │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

13 rows in set. Elapsed: 0.004 sec.
```
此外，我们还通过可视化展示了稀疏索引如何裁剪掉所有不可能包含示例查询匹配结果的行块：

![](https://clickhouse.com/docs/zh/assets/images/primary_key-2ec054f1a9f4de7dcdaea8f2c584e854.gif)

## 4. 实践

### 4.1 选择与排序键不同的主键

> 在使用 `SummingMergeTree` 和 `AggregatingMergeTree` 表引擎时，这一特性非常有用

上述示例中只指定了排序键，那么主键会被隐式定义为与排序键相同。当然也可以指定一个与排序键不同的主键。在使用 `SummingMergeTree` 和 `AggregatingMergeTree` 表引擎时，这一特性非常有用。在这些引擎的常见使用场景中，表通常有两类列：维度（dimensions） 和 度量（measures）。典型查询会对度量列的值在任意 GROUP BY 条件下进行聚合，并按维度进行过滤。由于 `SummingMergeTree` 和 `AggregatingMergeTree` 会对具有相同排序键值的行进行聚合，因此将所有维度都加入排序键是很自然的做法。在这种情况下，更合理的做法是只在主键中保留少数几列，以保证高效的范围扫描，并将其余维度列加入排序键元组中。

现在用一个示例说明。假设一张 `SummingMergeTree` 数据表有 A、B、C、D、E、F 六列，如果需要按照 A、B、C、D 进行汇总，则有：
```sql
ORDER BY (A，B，C，D)
```
但是如此一来，此表的主键也被定义成了 A、B、C、D。而在业务层面，其实只需要对 A 列进行查询过滤，应该只使用 A 字段创建主键。所以，一种更加优雅的定义形式应该是：
```sql
ORDER BY (A、B、C、D)
PRIMARY KEY A
```

需要注意的是当选择与排序键不同的主键时，MergeTree 会强制要求主键列字段必须是排序键的前缀。例如下面的定义是错误的：
```sql
ORDER BY (B、C、D)
PRIMARY KEY A
```
> PRIMARY KEY 必须是 ORDER BY 的前缀。

这种强制约束保障了即便在两者定义不同的情况下，主键仍然是排序键的前缀，不会出现索引与数据顺序混乱的问题。

### 4.2 主键选择的关键原则

- 选择高频过滤列
  - 列数量限制：通常不超过三列，避免索引膨胀和排序开销。
  - 过滤频率优先：主键列应为查询中频繁用于 WHERE、GROUP BY 或 JOIN 条件的列。
- 列顺序的权衡
  - 第一列最关键：
    - 对数据裁剪影响最大，应选择高频且高筛选率的列（如时间字段）。
    - 例如，查询通常按日期过滤，将日期作为主键第一列可快速跳过无关数据块。
    - 后续列进行压缩优化：
      - 按列的基数升序排列（低基数列在前），提升压缩率。
      - 例如，主键(country, city, user_id)，country基数最低，相同值连续存储压缩效果最佳。
    - 查询性能与压缩的平衡：
      - 若高基数列需频繁查询，可将其前置，但可能牺牲压缩率。
      - 折中方案：使用跳数索引（如bloom_filter）补充高频但非主键列的查询。但跳数索引也需设计合理，具体注意事项，请参见过度使用跳数索引。


### 4.3 主键设计不合理





## 3. 示例

结合上述基础概念，通过一个示例来进一步理解 ClickHouse 的主键。如下图所示：

![](https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/7089159471/p888166.webp)

### 3.1 设计主键

T表主键设计背景：
- 列A、B、C应该按照基数升序（低基数列在前）进行排序。基数是指列中不同值的数量。
- 查询使用A、B、C列频繁过滤数据，表明这些列在查询中为使用为频繁的列。

建表T：
- 使用 DDL 语句创建表 T，其中指定了 ORDER BY (A, B, C)，列 A 被指定为稀疏主键，表 T 的数据将按照列 A、B、C 的顺序进行排序。

表 T 数据存储：
- 数据在存储中以 data part 形式存储，并且这些部分是按照指定的列（A、B、C）进行排序的。
- 每个 data part 都有一个稀疏主键，该索引基于数据的排序顺序创建。

### 3.2 分析查询T表

示例语句：
```sql
SELECT ... FROM T WHERE A = ... AND B = ... AND C BETWEEN ... AND ... GROUP BY ... ORDER BY ... LIMIT ...
```
ClickHouse 接收到上述查询语句后，其查询处理引擎会根据查询条件，使用主键快速定位相关数据，并通过流式读取有序存储的数据块，减少磁盘寻道时间，从而提高查询效率。

## 4. 不当主键影响

- 查询性能显著下降。
  - 如果主键未包含高频过滤条件列时，查询无法利用稀疏索引快速跳过无关数据块，导致扫描大量冗余数据，甚至扫描全表，进而严重影响了查询性能。
- 数据压缩率降低。
  - 主键顺序未按照基数升序排列（低基数列在前）时，相同值将分散于不同数据块中，导致压缩算法无法有效去重。
- 合并效率低下。
  - 主键设计不合理导致数据块内排序混乱，合并时需处理更多重叠或碎片化的数据块。频繁的合并操作占用I/O和CPU资源，也影响写入吞吐量。


> [](https://help.aliyun.com/zh/clickhouse/use-cases/unreasonable-primary-key-design?spm=a2c4g.11186623.help-menu-144466.d_3_5_2.4d33656e1bUdti&scm=20140722.H_2883340._.OR_help-T_cn~zh-V_1)


https://clickhouse.com/docs/zh/best-practices/choosing-a-primary-key
