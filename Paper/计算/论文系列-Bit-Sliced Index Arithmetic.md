位切片索引 (BSI) 最初定义于 [ONQ97]。本文核心介绍了 BSI 实现算法。对于表 T 上的任意两个 BSI X 和 Y，我们展示了如何高效地生成新的 BSI Z、V 和 W，使得 `Z = X + Y`、`V = X - Y` 以及 `W = MIN(X,Y)`；这意味着如果表 T 行 r 有一个 x 值(由 BSI X 表示)和一个 y 值(由 BSI Y 表示)，那么行 r 的 BSI Z 中的值将是 `x+y`，V 中的值将是 `x-y`，W 中的值将是 `MIN(x, y)`。由于表示一组行的位图是最简单的比特切片索引，因此 BSI 算法是通过 SQL 子句 UNION ALL（加法）、EXCEPT ALL（减法）和 INTERSECT ALL（最小值）产生的行集合的最直接方法。本文的另一个贡献是将 [ONQ97] 中的 BSI 范围查询扩展到一种新的非布尔形式：BSI 值的 Tok k，k 的范围是 1 到 T 的总行数。结合位切片加法，可以让我们能够解决文本检索的一个常见问题：给定一个对象关系表 T，其中行表示文档，集合类型列 K 表示关键词词条，我们演示了一种有效的算法来查找与某个查询列表 Q 共享最多词条的 k 个文档。在信息检索 (IR) 领域，有大量关于此类问题的已发表研究。我们引入的算法称为位切片词匹配 (BSTM)，它使用与最有效的已知 IR 算法相媲美的性能，这是对当前 DBMS 文本搜索算法的重大改进，其优势在于它仅使用我们为本机数据库操作提出的索引。

## 1. 简介

位切片索引 (BSI) 最初是在 [ONQ97] 中定义的，其中演示了如何使用表示列数量的 BSI 来计算 SQL 聚合查询（具体来说，SUM 查询），并在 SQL WHERE 子句中添加范围限制。在当前工作中，我们引入 BSI 算法：加法、减法和最小值，并展示了 BSI 运算如何提供一种自然的方式来计算 SQL 子句中 UNION ALL、EXCEPT ALL 以及 INTERSECT ALL 的结果。其中，子查询产生的行集可以组合成 MultiSets（也称为包）：即允许重复的集合。例如，下面的查询 1.1 符合 ANSI SQL-99 标准 ，并在 Microsoft SQL Server 中执行并获取 MultiSets 结果：
```sql
SELECT COUNT(*) CT,PRID
FROM (
  SELECT PRID FROM T WHERE COL_1 = const_1
  UNION ALL
  SELECT PRID FROM T WHERE COL_2 = const_2
  UNION ALL
  ...
  SELECT PRID FROM T WHERE COL_M = const_M
) AS NEW_T
GROUP BY PRID;
```
> 查询 1.1

查询 1.1 在 Select 的 FROM 子句中从相等匹配谓词的 UNION ALL 中检索具有对应主键标识符 PRID 的 `COUNT（*)` multiplicities。`GROUP BY PRID` 通常在表 T 的每一个分组中只选择一行，但在本例中，它选择由 UNION ALL 产生的适当的行数。目前还没有数据库产品使用 BSI 加法来跟踪这些 multiplicities，但是我们将证明 BSI 加法在这方面是非常有效的。

我们还可以构造这样的查询示例：使用 EXCEPT ALL 减去 multiplicities，使用 INTERSECT ALL 确定两个重复集的最小 multiplicities。注意，在 EXCEPT ALL 和 INTERSECT ALL 的情况下，结果 BSI 中的任何负数都必须用零替换，因为在 SQL 中，行不会出现负的 multiplicities。

本文还将 BSI 使用范围推广到非布尔形式：不再是寻找表 T 中 BSI 值大于某个常数 C 的所有行（无论可能有多少行），而是展示了如何高效地确定 BSI 值最高的 k 行，$$ 1 <= k <= |T|$$，其中 $$|T|$$ 是表 T 的基数。我们需要在词条匹配算法 BSTM 中使用这种能力以及 BSI 加法。


## 2. 基本概念

在介绍新材料之前，我们将在下面回顾一些以前发表的概念。

### 2.1 Bitmap 索引定义

要创建位图索引，必须为基础表 T 的所有 N 行分配序号：1，2，…，N，称为序号行位置，或简称序号位置。然后，对于 T 上索引 X 的任何索引值 $$X_i$$， T 中具有值 $$X_(i)$$ 的行列表可以用顺序位置列表表示，例如：4,7,11,15,17，…，或者等价地用逐字位图00010010001000101 .. ..表示请注意，稀疏的逐字位图（相对于0有少量的1）将被压缩，以节省磁盘和内存空间



## 3. BIT-SLICED INDEX ARITHMETIC

在本节中，我们将演示如何在位切片索引上执行算术运算，在每个位切片上使用 SIMD 操作。当然，这种技术已经在多比特计算机操作中使用了多年。



考虑图3，其中的每个位图B1、B2和B3表示三个子查询的发现集，然后在SQL查询中与UNION ALL子句组合。我们如何计算并表示结果的多行集？如果我们能以某种方式将前三行的位图相加以生成最后一行的SUM，我们就能解决这个问题。











...
