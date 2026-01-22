> ClickHouse 通过将更新视作插入操作，巧妙避开了行级更新带来的性能瓶颈。在这篇系列的第一篇中，我们将介绍几个专为此场景设计的引擎，它们是如何实现高速更新的。  


## 1. 不用 UPDATE 也能实现快速更新 

列式存储天生不适合做行级更新。ClickHouse 也不例外：它从一开始就是为了 **在大规模数据场景下提供极速的写入和查询性能而设计的**，而不是为修改单行数据而优化的。但现实中的数据应用并不会遵循教科书上的“只读”模式。ClickHouse 的用户经常要处理快速变化的数据：IoT（传感器读数）、电商（订单与库存）、金融（支付状态）、游戏（玩家数据），以及 CRM/HR（用户或员工档案），这些数据需要被不断地更正、更新甚至删除。与其在一个为大规模读取设计的系统中硬塞进低效的 UPDATE 操作，我们选择了另一种方式：**将更新操作当作插入来处理**，从而绕开了性能问题。

这不是一个临时解决方案，而是 ClickHouse 有意为之的架构设计。像 ReplacingMergeTree、CoalescingMergeTree 和 CollapsingMergeTree 这样的引擎，通过写入新行代替修改旧行，实现了对更新和删除的支持。它们充分利用 ClickHouse **高并发插入能力和后台合并机制**，避开了原地更新常见的性能开销。

这些引擎在大规模数据场景中依然非常实用，尤其适合高写入、频繁变更的数据工作负载。同时，它们也为我们后来构建的新一代更新机制提供了灵感，理解它们的工作方式，有助于理解 ClickHouse 如何加速 SQL 风格的更新。

本系列将介绍以下内容：
- 第 1 部分(本篇)：介绍这些专为处理更新而设计的引擎是如何工作的，以及为何它们依旧非常高效。
- 第 2 部分：将介绍如何引入标准 SQL 风格的 UPDATE，并由一种全新的机制 —— patch parts 提供支持。
- 第 3 部：我们将对上述所有方案进行性能测试，对比它们在实际场景中的表现。

要理解 ClickHouse 是如何做到快速更新的，首先得知道为什么列式存储天生就不擅长处理更新操作。

## 2. 为什么在列式存储中执行更新很困难

在数据库系统中，更新与分析常常是性能上的对立面：一个优化了，另一个可能就会变慢。

在行式存储系统（如 PostgreSQL 或 MySQL）中：
- 每一行数据在磁盘上是连续存储的。
- 所以更新很方便，可以直接原地覆盖整行。
- 但分析性能不佳：即便你只查询两列，也必须把整行加载到内存中。

而在列式存储系统（如 ClickHouse）中：
- 每一列被存储为独立的文件。
- 因此分析非常高效，只需读取所需的列。
- 但更新变得更复杂，因为要修改某一行数据，必须同时修改多个文件，且需要重写部分数据。

这种结构性的取舍，让列式系统始终难以高效支持行级更新。ClickHouse 选择了另一种思路：用专为此场景设计的引擎，通过“避开更新”来实现更新。

## 3. 由于插入非常快，我们将更新实现为插入

核心理念其实很直接：ClickHouse 对插入操作做了极致优化。由于没有像全局 B++ 索引这样的集中结构需要锁定或维护，[插入操作彼此完全隔离](https://clickhouse.com/docs/concepts/why-clickhouse-is-so-fast#storage-layer-concurrent-inserts-are-isolated-from-each-other)，可以并发执行，互不干扰，且以全速写入磁盘（某些生产环境下甚至实现了 [每秒超 10 亿行](https://clickhouse.com/blog/how-tesla-built-quadrillion-scale-observability-platform-on-clickhouse#proving-the-system-at-scale)的写入）。这也意味着表无论多大，插入性能都不会下降。此外，插入过程非常轻量：诸如记录替换之类的逻辑被拆分出去，[延迟到后台合并时再处理](https://clickhouse.com/docs/concepts/why-clickhouse-is-so-fast#storage-layer-merge-time-computation)。

> 关键在于：正因为插入足够高效，ClickHouse 可以把更新（甚至删除）当作额外的插入来处理。

在像 IoT 这样需要高吞吐的数据场景中，传统 SQL 风格的 UPDATE 操作其实并不高效：即使是在关系型数据库中，更新一条记录也往往涉及查找旧值、重写整行，甚至加锁或额外更新许多不必要的数据。

而 ClickHouse 的专用引擎如 ReplacingMergeTree、CoalescingMergeTree 和 CollapsingMergeTree，则采用了一种更高效的“只插入”模型：完全跳过了查找旧记录的过程。**更新和删除操作都被转换为快速、轻量的插入行为，实际的数据更改则交由后台合并过程异步完成**。

> 为什么这种方式如此高效：ClickHouse 本身就会在后台不断地将小的数据分片[合并](https://clickhouse.com/docs/merges)成更大的[分片](https://clickhouse.com/docs/parts)，这正是其存储引擎名称 MergeTree 的由来。合并过程中，系统会将相关数据加载到内存中、进行整理并写出一个新的分片。既然这些合并操作本来就要进行，因此顺便处理更新或删除几乎不会带来额外开销。保留某条记录的最新版本或移除已取消记录的代价非常小。

ClickHouse 能够实现这种轻量的 **插入-合并** 流程，关键就在于它的数据在磁盘上的组织方式：**数据被分割成有序、不可变的分片，并持续在后台合并**。

## 4. 理解数据分片与合并机制

想深入理解 ClickHouse 如何实现快速更新，以及更好地阅读本文（和下一篇）中的图示和机制说明，有必要先了解一切的基础 —— 分片（parts）。

### 4.1 插入会生成已排序且不可变的数据分片

每当你向 ClickHouse 表插入数据时，系统都会在磁盘上写入一个独立的、不可变的数据[分片](https://clickhouse.com/docs/parts)。每个分片包含若干行数据（按列存储），并根据其在插入和合并历史中的位置命名。例如，向一个初始为空的 orders 表插入包含 order_id、item_id、quantity、price 和 discount 列的数据后：
```sql
INSERT INTO orders VALUES
    (1001, 'kbd', 10, 45.00, 0.00),
    (1001, 'mouse', 6, 25.00, 0.00);
```
ClickHouse 会生成一个名为 `all_1_1_0` 的新分片：

![](https://mmbiz.qpic.cn/mmbiz_png/ECfQdkxm4Rb6YdBeGVvEC2JkXd3YayM4g9ZN9u4nDKw6NzkgHic1d9P4hFAv95rRuOzPsfttRJ3AJZCKw0hPGcw/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=11)

该分片中的数据在磁盘上是按照表的排序键排序的，在这个例子中是 (order_id, item_id)。这一点适用于所有 MergeTree 表的分片，是 ClickHouse 能高效合并数据、避免随机 I/O 和重新排序的关键。

### 4.2 如何解读分片的名称

每个分片的命名遵循 `partition_minBlock_maxBlock_mergeLevel` 格式：
- `partition`：all 表示[分区](https://clickhouse.com/docs/partitions) ID（此处使用默认分区）
- `minBlock`：1 表示该分片中包含的最小块号
- `maxBlock`：1 表示该分片中包含的最大块号
- `mergeLevel`：0 表示[合并层级](https://clickhouse.com/docs/merges#what-are-part-merges-in-clickhouse)，0 表示初始插入，数字越大代表合并层级越高

### 4.3 分片包含的内容

在系统底层，这个分片其实是磁盘上的一个文件夹，名为 `all_1_1_0`，其中包含表中每一列的数据文件：order_id、item_id、quantity、price 和 discount。每个文件都经过压缩，存储了该分片中对应列的所有值。

上图展示了这些列文件的结构，帮助理解分片内部的数据布局。

### 4.4 块如何组成一个分片

ClickHouse 插入数据的基本单位是数据块（block），每个块会分配一个单调递增的块号。一个分片可能包含一个或多个块，可能来源于单次插入，也可能是多个分片合并后的结果。分片名中的 minBlock 和 maxBlock 表示该分片所包含数据块号的范围。

### 4.5 合并在后台自动进行

当新的数据到来时，ClickHouse 不会修改已有的分片，而是生成新的分片写入磁盘。后台机制则会不断[合并](https://clickhouse.com/docs/merges) 这些分片，以控制数量并整理数据。

### 4.6 已排序的数据分片让合并更高效

ClickHouse 能够高效合并分片，原因在于 **所有分片都已经按照相同的列顺序排好序**。合并两个分片时，引擎只需顺序扫描二者并将数据交错写入，无需重新排序、无需随机读取，也不需要使用临时缓存。

> 这被称为单次合并扫描（single merge pass）：ClickHouse 顺序读取两个分片，实时对比每一行并写出新的合并结果。这正是其合并操作既快速又轻量的核心原因之一。

这种高效机制意味着，在合并过程中处理更新和删除操作几乎不会带来额外负担，它们也只是同一个扫描和写入流程中的一部分。

了解了底层原理后，我们接下来通过实际案例来看看它是如何运作的，首先从最简单直接的引擎开始：ReplacingMergeTree。

## 5. ReplacingMergeTree：通过插入新行替换旧行

我们用一个五金店的订单表作为示例，来演示 [ReplacingMergeTree](https://clickhouse.com/docs/engines/table-engines/mergetree-family/replacingmergetree) 的用法：
```sql
CREATE TABLE orders (
    order_id   Int32,
    item_id    String,
    quantity   UInt32,
    price      Decimal(10,2),
    discount   Decimal(5,2)
)
ENGINE = ReplacingMergeTree
ORDER BY (order_id, item_id);
```
要更新一条记录，只需要插入一条具有相同排序键 (order_id, item_id) 的新版本。在后台合并时，ClickHouse 会自动保留最新的那条记录（即最后插入的一条）。例如，假设客户 ① 一开始订购了 10 个键盘和 6 个鼠标，按原价计费：
```sql
INSERT INTO orders VALUES
    (1001, 'kbd', 10, 45.00, 0.00),
    (1001, 'mouse', 6, 25.00, 0.00);
```
后来他将鼠标的数量提高到了 60 个，享受了 20% 的批量折扣。这时候，我们不修改旧数据，而是通过 ② 插入一条包含更新后的数量和折扣的新记录：
```sql
INSERT INTO orders VALUES
    (1001, 'mouse', 60, 25.00, 0.20);
```
下图展示了最初插入（①）和更新插入（②）所创建的[数据分片](https://clickhouse.com/docs/parts)。在下一轮[后台合并](https://clickhouse.com/docs/merges)（③）中，ClickHouse 会自动丢弃旧版本，只保留最新的记录：

![](https://mmbiz.qpic.cn/mmbiz_png/ECfQdkxm4Rb6YdBeGVvEC2JkXd3YayM46nH9bz5XI373Sic2o1tHgCXLmG7FE5xaRMLUcuoRC7hatS8SwHo9niaw/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=15)

合并之后，分片 ① 和 ② 将被清除，分片 ③ 成为该表的活跃数据分片。

那么，如果你只需要更新部分字段怎么办？这就是 CoalescingMergeTree 派上用场的时候。

## 6. CoalescingMergeTree：自动合并部分更新

[CoalescingMergeTree](https://clickhouse.com/docs/engines/table-engines/mergetree-family/coalescingmergetree) 的机制与 ReplacingMergeTree 十分类似，但有一个显著不同：它支持部分更新（partial updates）。你可以只插入有变动的字段，无需整行覆盖。

我们继续使用同一个订单表：
```sql
CREATE TABLE orders (
    order_id   Int32,
    item_id    String,
    quantity   Nullable(UInt32),
    price      Nullable(Decimal(10,2)),
    discount   Nullable(Decimal(5,2))
)
ENGINE = CoalescingMergeTree
ORDER BY (order_id, item_id);
```
> 注意：非排序键的字段被设为 Nullable 类型，这样在执行部分更新时，可以省略未变更的列，未指定的字段会被自动设为 NULL。

还是同一个例子：客户 ① 一开始订购了 10 个键盘和 6 个鼠标，按原价计费：
```sql
INSERT INTO orders VALUES
    (1001, 'kbd', 10, 45.00, 0.00),
    (1001, 'mouse', 6, 25.00, 0.00);
```
② 我们插入一条仅更新数量和折扣的记录：
```sql
INSERT INTO orders VALUES
    (1001, 'mouse', 60, NULL, 0.20);
```
当后台将 ① 初始插入和 ② 更新插入进行合并时，会生成一个新的数据分片 ③，ClickHouse 会针对每一列保留最新的非空值，从而将多条部分更新记录合并为一条完整记录。合并完成后，① 和 ② 分片将被丢弃，整个流程与 ReplacingMergeTree 相同：

![](https://mmbiz.qpic.cn/mmbiz_png/ECfQdkxm4Rb6YdBeGVvEC2JkXd3YayM4ZDjUXSwMLMEF0Rnxpibj8DibrJB2QbCIHicqvGuiaY4KJgibmf7gtk44ibAA/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=19)

那如果是删除操作呢？CollapsingMergeTree 提供了一种巧妙的方式来处理。

## 7. CollapsingMergeTree：通过插入新行来删除旧行

[CollapsingMergeTree](https://clickhouse.com/docs/engines/table-engines/mergetree-family/collapsingmergetree) 允许你无需发出 DELETE 语句即可删除记录。其做法是插入一条特殊的“取消”行，用以标记原始记录无效。

我们还是用之前的订单表，不过这次我们为其添加了一个额外的 is_valid 字段，用作该引擎的 [sign 参数](https://clickhouse.com/docs/engines/table-engines/mergetree-family/collapsingmergetree#parameters)：
```sql
CREATE TABLE orders (
    order_id   Int32,
    item_id    String,
    quantity   UInt32,
    price      Decimal(10,2),
    discount   Decimal(5,2),
    is_valid   UInt8 -- only required for CollapsingMergeTree
)
ENGINE = CollapsingMergeTree(is_valid)
ORDER BY (order_id, item_id);
```
① 初始插入订单：
```sql
INSERT INTO orders VALUES
    (1001, 'kbd',  10, 45.00, 0.00, 1),
    (1001, 'mouse', 6, 25.00, 0.00, 1);
```
② 若要删除这条记录，我们插入一条相同排序键 (order_id, item_id) 的新行（其余字段可为 NULL），并将 is_valid 设为 -1：
```sql
INSERT INTO orders VALUES
    (1001, 'mouse', NULL, NULL, NULL, -1);
```
在接下来的 ③ 合并过程中，ClickHouse 会找到对应的 +1 和 -1 两条记录并将它们折叠合并，从而一并移除，连带着分片 ① 和 ② 也会被清除：

![](https://mmbiz.qpic.cn/mmbiz_png/ECfQdkxm4Rb6YdBeGVvEC2JkXd3YayM4mjILNkMiaC5jCnYc2SnJEiaoBlBthgzjKpkK0hRy6LGnWP2iawJlnVaicg/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=23)

> 这一机制同样可以用于更新操作：要更新一条记录，只需先插入一条取消记录，再插入新的值版本。在下一轮后台合并中，旧值和取消记录将被移除，只保留最新的记录。  CollapsingMergeTree 甚至支持更新排序键字段，这是 ReplacingMergeTree 和 CoalescingMergeTree 无法实现的功能。

除了支持更新和删除，这三种引擎还都具备 UPSERT 能力。

## 8. 额外特性：内置 UPSERT 行为

无论是 ReplacingMergeTree、CoalescingMergeTree，还是 CollapsingMergeTree，都支持实质上的 UPSERT（插入或更新）：当插入新行时，如果存在相同排序键的记录，引擎会自动应用对应逻辑进行合并。

这种“插入即更新”的模式非常强大，而标准的 UPDATE 语句并不具备直接支持这种用法的能力。

虽然 SQL 标准定义了 [MERGE](https://en.wikipedia.org/wiki/Merge_\(SQL\)) 命令来实现插入或更新逻辑，但它通常写法繁琐，执行效率也不高。而在 ClickHouse 中，这一切只需要一次简单、快速的插入操作即可完成。

基于插入的模型为 ClickHouse 带来了高效的更新、删除和 UPSERT 能力。但如果你希望查询结果在后台合并完成之前就反映出这些更改，该怎么处理呢？

## 9. 使用 FINAL 获取最新结果

上述三种表引擎都依赖后台合并来整合数据。这种方式让插入驱动的更新和删除变得极为高效，但也意味着这些操作是“最终一致”的：在高并发写入场景下，插入可能超过合并的处理速度，也就是存在一个数据尚未整合的窗口期。

为确保此时查询结果的准确性，ClickHouse 提供了一个机制：在查询时即时应用引擎的合并逻辑，通过 [FINAL](https://clickhouse.com/docs/sql-reference/statements/select/from#final-modifier) 修饰符实现:
```sql
SELECT * FROM orders FINAL;
```
使用 FINAL 时，并不会真正触发磁盘上的合并，而是通过内存将相关的数据分片动态整合，以查询发起时的数据状态为基础，返回已经合并后的结果。在三种引擎中，FINAL 表现一致：
- 在 ReplacingMergeTree 中，它会保留每条记录的最新版本；
- 在 CoalescingMergeTree 中，它将稀疏更新合并为完整行；
- 在 CollapsingMergeTree 中，它应用取消逻辑来处理删除与更新。

因此，在你需要数据一致性强、结果准确可控的查询场景中，FINAL 是一个强有力的工具，同时保留了基于插入操作的高吞吐性能。

> 无需惧怕 FINAL
> ClickHouse 针对 FINAL 做了大量[优化](https://clickhouse.com/blog/clickhouse-release-23-12#optimizations-for-final)：包括智能内存算法、跳过无冲突分片的选择性处理、以及向量化执行等技术，使得即使在海量数据下，FINAL 的执行依然高效。对于不涉及冲突的分片范围，ClickHouse 会直接跳过处理。每列还会 [独立并行处理](https://clickhouse.com/blog/clickhouse-release-24-01#vertical-algorithm-for-final-with-replacingmergetree)，进一步降低内存消耗，并提升宽表下的整体性能。

你可以拿到正确的结果——但这真的算是“更新”操作吗？我们稍作停顿，从更高的视角来重新理解。

## 10. 这与真正的更新有何不同？

从整体视角来看，ClickHouse 的更新模式其实与传统行式数据库非常相似：写入新版本，再读取新版本。

| 传统行式数据库 | ClickHouse |
| :------------- | :------------- |
| 原地覆盖旧数据 | 在旧数据旁追加新版本 |
| 查询立即返回新版本 | 查询同样立即返回新版本 |
| 提交写入后旧版本被删除 | 旧版本稍后由后台合并清理 |

也就是说，虽然内部机制不同，尤其是在数据清理上有所延后，但其“更新语义”却高度一致。然而，要获得这种一致性的效果，你必须采用 ClickHouse 的思维方式。这意味着理解后台合并原理、知道何时使用 FINAL，以及选择适合的表引擎。你需要将每次更新建模为一次插入，同时根据各引擎特性来设计数据模型。例如，ReplacingMergeTree 要求通过排序键来识别记录，一旦排序键发生变化，往往需要重建整张表。

这种模型并不符合传统 SQL 用户对 UPDATE 操作的直觉。

## 11. 从引擎语义到 SQL 的简洁性

虽然这些专用引擎具备极高的性能和灵活性，但也带来了学习曲线。用户需要考虑合并机制、排序键行为，以及不同引擎的具体实现方式——这就让 UPDATE 操作远不像标准 SQL 那般直观易用。

为此，ClickHouse 也在持续演进。在 [第 2 部分](https://clickhouse.com/blog/updates-in-clickhouse-2-sql-style-updates) 中，我们将介绍如何将快速、SQL 风格的 UPDATE 操作 引入 ClickHouse，同时保留其一贯的高性能特性。

我们会完整回顾这一演进路径：从早期的“重量级” mutation，到基于引擎机制的轻量即时更新，最终发展出由 patch parts 驱动的声明式更新方式。这是一种全新的可扩展机制，汲取了上一节中几种引擎的设计理念，同时实现了统一封装，并通过熟悉的 SQL 语法对外呈现。

换句话说，ClickHouse 已经提供了 UPDATE 所应具备的一切能力——只是以它特有的高性能方式实现。

> [原文](https://mp.weixin.qq.com/s/t3-YunLOCPeToogxw89pEQ)
