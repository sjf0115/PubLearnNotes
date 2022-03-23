
### 1. 题目

假设按照升序排序的数组在预先未知的某个点上进行了旋转。

( 例如，数组 [0,1,2,4,5,6,7] 可能变为 [4,5,6,7,0,1,2] )。

搜索一个给定的目标值，如果数组中存在这个目标值，则返回它的索引，否则返回 -1 。

你可以假设数组中不存在重复的元素。

你的算法时间复杂度必须是 O(log n) 级别。

示例 1:
```
输入: nums = [4,5,6,7,0,1,2], target = 0
输出: 4
```
示例 2:
```
输入: nums = [4,5,6,7,0,1,2], target = 3
输出: -1
```

### 2. 实现

```java
public int search(int[] nums, int target) {
    int size = nums.length;
    int begin = 0, end = size - 1;
    while (begin <= end){
        int mid = (begin + end) / 2;
        // 找到目标
        if (nums[mid] == target){
            return mid;
        }
        // 中间元素大于等于首元素 [begin, mid] 有序 [mid, end] 无序
        if (nums[mid] >= nums[begin]){
            // 在[begin, mid-1]区间
            if (target < nums[mid] && target >= nums[begin]){
                end = mid - 1;
            }
            // 在[mid+1, end]区间
            else {
                begin = mid + 1;
            }
        }
        // 中间元素小于首元素 [begin, mid] 无序 [mid, end] 有序
        else {
            // 在[mid+1, end]区间
            if (target > nums[mid] && target <= nums[end]){
                begin = mid + 1;
            }
            // 在[begin, mid-1]区间
            else {
                end = mid - 1;
            }
        }
    }
    return -1;
}
```
















链接：https://leetcode-cn.com/problems/search-in-rotated-sorted-array/description/
