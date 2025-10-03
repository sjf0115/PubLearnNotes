在 Hive 查询优化中，MapJoin 是一项重要的优化技术，它通过将小表加载到内存中并在 Map 阶段完成 Join 操作，避免了 Reduce 阶段的 shuffle 过程。然而，确定哪个表作为"大表"（在 Reduce 端处理）是这项优化的关键决策。本文将基于 Hive 3.1.3 源码，深入分析 Hive 在自动转换 MapJoin 时判断大表候选的复杂逻辑。

## 1. 核心方法分析

让我们首先理解 `getBigTableCandidates` 方法的核心逻辑：

```java
public static Set<Integer> getBigTableCandidates(JoinCondDesc[] condns) {
    Set<Integer> bigTableCandidates = new HashSet<Integer>();
    // 是否遇到 Outer Join
    boolean seenOuterJoin = false;
    // 出现的位置
    Set<Integer> seenPostitions = new HashSet<Integer>();
    Set<Integer> leftPosListOfLastRightOuterJoin = new HashSet<Integer>();
    // 最近一个遇到的是否是 Right Outer Join
    boolean lastSeenRightOuterJoin = false;

    // 遍历所有 JOIN 条件
    for (JoinCondDesc condn : condns) {
        // 方法实现...
    }
}
```
> org.apache.hadoop.hive.ql.optimizer.getBigTableCandidates

## 2. JOIN 类型处理逻辑

### 2.1 全外连接 (FULL OUTER JOIN)

```java
if (joinType == JoinDesc.FULL_OUTER_JOIN) {
    return new HashSet<Integer>();
}
```

**处理逻辑**：一旦遇到 FULL_OUTER_JOIN，立即返回空集合，表示无法进行 MapJoin 转换。这是因为 FULL OUTER JOIN 需要保留两个表的所有记录，无法通过 MapJoin 实现。

### 2.2. 左外连接 (LEFT OUTER JOIN) 和左半连接 (LEFT SEMI JOIN)

```java
if (joinType == JoinDesc.LEFT_OUTER_JOIN || joinType == JoinDesc.LEFT_SEMI_JOIN) {
    seenOuterJoin = true;
    if(bigTableCandidates.size() == 0) {
        bigTableCandidates.add(condn.getLeft());
    }
    lastSeenRightOuterJoin = false;
}
```

**处理逻辑**：
- 标记已遇到外连接
- 如果当前大表候选集为空，将左表加入候选
- 重置最近右外连接标志为 false

**设计原理**：左连接必须保留左表的所有记录，因此左表不能作为小表被广播。

### 2.3 右外连接 (RIGHT OUTER JOIN)

```java
if (joinType == JoinDesc.RIGHT_OUTER_JOIN) {
    seenOuterJoin = true;
    lastSeenRightOuterJoin = true;
    // add all except the right side to the bad positions
    leftPosListOfLastRightOuterJoin.clear();
    leftPosListOfLastRightOuterJoin.addAll(seenPostitions);
    leftPosListOfLastRightOuterJoin.remove(condn.getRight());
    bigTableCandidates.clear();
    bigTableCandidates.add(condn.getRight());
}
```

**处理逻辑**：
- 标记已遇到外连接以及最近一个是右外连接
- 记录最近一个右外连接左侧的所有表位置（这些表不能作为大表候选）
- 清空当前候选集，只保留右表

**关键洞察**：右外连接的右表"总是胜出" - 它强制成为唯一的大表候选。

### 2.4 内连接 (INNER JOIN)

```java
if (joinType == JoinDesc.INNER_JOIN) {
    if (!seenOuterJoin || lastSeenRightOuterJoin) {
        if (!leftPosListOfLastRightOuterJoin.contains(condn.getLeft())) {
            bigTableCandidates.add(condn.getLeft());
        }
        if (!leftPosListOfLastRightOuterJoin.contains(condn.getRight())) {
            bigTableCandidates.add(condn.getRight());
        }
    }
}
```

**处理逻辑**：
- 仅在未遇到外连接 **或** 最近遇到的是右外连接时处理
- 检查左右表是否在右外连接的"禁止列表"中
- 将符合条件的表加入大表候选

## 3. 算法状态机分析

该算法本质上是一个状态机，维护以下关键状态：
- **bigTableCandidates**：当前有效的大表候选集合
- **seenOuterJoin**：是否遇到过外连接
- **lastSeenRightOuterJoin**：最近遇到的外连接是否为右外连接
- **leftPosListOfLastRightOuterJoin**：最近右外连接左侧表的"禁止列表"

## 4. 实际场景分析

### 4.1 场景1：纯内连接
```sql
A JOIN B ON ... JOIN C ON ...
```
处理过程：所有表都被加入候选集，最终选择基于表大小的最优解。

### 4.2 场景2：左外连接 + 内连接
```sql
A LEFT JOIN B ON ... JOIN C ON ...
```
处理过程：左表A首先被加入候选，后续内连接的表不会被加入，A成为唯一候选。

### 4.3 场景3：右外连接 + 内连接
```sql
A RIGHT JOIN B ON ... JOIN C ON ...
```
处理过程：右表B成为唯一候选，后续内连接中不在"禁止列表"的表也会被加入候选。

### 4.4 场景4：混合连接类型
```sql
A LEFT JOIN B ON ... RIGHT JOIN C ON ... JOIN D ON ...
```
处理过程：左外连接时A加入候选，遇到右外连接时清空候选只保留C，后续内连接中符合条件的表也会加入候选。

## 5. 设计哲学与优化考量

1. **外连接语义优先**：外连接的语义约束决定了某些表必须作为大表
2. **右外连接主导**：右外连接具有最强的约束力，会重置整个候选状态
3. **渐进式决策**：按 JOIN 顺序逐步构建候选集，反映查询的语义结构
4. **安全性保证**：通过"禁止列表"机制确保不会违反连接语义

## 6. 性能影响

这种判断机制直接影响：
- **MapJoin 适用性**：正确的大表选择是 MapJoin 的前提
- **查询性能**：合理的大表选择可以最大化 MapJoin 的效益
- **内存使用**：避免将大表错误地作为小表加载到内存

## 7. 总结

Hive 的 MapJoin 大表候选判断算法是一个基于 JOIN 语义的复杂状态机，它通过分析连接类型的序列和关系，智能地确定哪些表适合作为大表。理解这一机制对于编写高效的 Hive 查询和调优具有重要意义。

该算法的核心洞察是：**外连接的语义约束主导大表选择，其中右外连接具有最高优先级，而内连接在特定条件下可以灵活参与候选**。这种设计既保证了查询语义的正确性，又为性能优化提供了最大可能。
