Timsort是一种混合稳定的排序算法，结合了合并排序（merge sort）和插入排序（insertion sort）而得出的排序算法，旨在在多种类型数据中仍然有很好的效率。Tim Peters在2002年实现了该算法并在Python语言中使用(TimSort是Python中list.sort的默认实现）。该算法找到数据中已经排好序的子序列，然后只对剩下序列进行排序。通过将识别出的子序列(称之为Run)与已经识别出的子序列进行合并，直到满足一定条件后才结束合并。Timsort自2.3版以来一直是Python的标准排序算法。现在Java SE7和Android也采用Timsort算法对数组排序。

### 1. 操作

#### 1.1 Runns

TimSort遍历数据，寻找至少有两个非降序元素(每个元素大于或等于前一个元素)或严格降序元素(每个元素小于前一个元素)的序列(称之为`Run`)。对于降序`Run`只需直接反转过来即可，所以严格的顺序保持了算法的稳定性(strict order maintains the algorithm's stability)，即相等的元素将不会反转。请注意，任何两个元素都保证是严格降序或非降序。

Where there are fewer than minrun elements in the run, it is brought up to size by sorting in, using binary insertion sort, the required number of following elements.
小于`minrun`个元素的`Run`，采用二分插入排序算法进行排序。

#### 1.2 minrun

Timsort是一种自适应排序算法，使用插入排序算法来合并比minrun小的`Run`，否则使用合并排序算法进行排序。

当`Run`的元素个数等于或略小于2的幂时，合并是最有效率的，当`Run`元素个数略大于2的幂时，效率显着降低，Timsort选择`minrun`来确保最大效率。


#### 1.2 合并



### 2. 分析

### 3. 验证
