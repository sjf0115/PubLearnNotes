
```java
// 序列区间 [1, 10]
int start = 1;
int end = 10;
// 4个并发
final int stepSize = 4;
for (int taskIdx = 0;taskIdx < stepSize;taskIdx++) {
    final long congruence = start + taskIdx;
    // 数据记录总个数
    long totalNoOfElements = Math.abs(end - start + 1);
    // 每个并发分配 baseSize 或者 baseSize+1 个数据记录
    final int baseSize = (int) (totalNoOfElements / stepSize);
    // 每个并发分配的数据记录个数
    final int toCollect = (totalNoOfElements % stepSize > taskIdx) ? baseSize + 1 : baseSize;
    // 分配
    for (long collected = 0; collected < toCollect; collected++) {
        long num = collected * stepSize + congruence;
        // 核心在这
        System.out.println("TaskIdx: " + taskIdx + ", Size: " + toCollect +  ", Element: " + num);
    }
}
```
输出：
```
TaskIdx: 0, Size: 3, Element: 1
TaskIdx: 0, Size: 3, Element: 5
TaskIdx: 0, Size: 3, Element: 9
TaskIdx: 1, Size: 3, Element: 2
TaskIdx: 1, Size: 3, Element: 6
TaskIdx: 1, Size: 3, Element: 10
TaskIdx: 2, Size: 2, Element: 3
TaskIdx: 2, Size: 2, Element: 7
TaskIdx: 3, Size: 2, Element: 4
TaskIdx: 3, Size: 2, Element: 8
```
