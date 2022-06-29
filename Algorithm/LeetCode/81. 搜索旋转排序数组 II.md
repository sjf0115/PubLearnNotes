### 1. 题目

假设按照升序排序的数组在预先未知的某个点上进行了旋转。

( 例如，数组 [0,0,1,2,2,5,6] 可能变为 [2,5,6,0,0,1,2] )。

编写一个函数来判断给定的目标值是否存在于数组中。若存在返回 true，否则返回 false。

示例 1:
```
输入: nums = [2,5,6,0,0,1,2], target = 0
输出: true
```
示例 2:
```
输入: nums = [2,5,6,0,0,1,2], target = 3
输出: false
```
进阶:
- 这是 [33. 搜索旋转排序数组](https://leetcode-cn.com/problems/search-in-rotated-sorted-array/description/) 的延伸题目，本题中的 nums  可能包含重复元素。
- 这会影响到程序的时间复杂度吗？会有怎样的影响，为什么？

### 2. 实现

```java
public boolean search(int[] nums, int target) {
    int size = nums.length;
    int begin = 0, end = size - 1;
    while (begin <= end){
        int mid = (begin + end) / 2;
        // 找到目标
        if (nums[mid] == target){
            return true;
        }
        // 中间元素等于首元素
        if(nums[mid] == nums[begin]){
            begin ++;
        }
        // 中间元素大于首元素 [begin, mid] 有序 [mid, end] 无序
        else if (nums[mid] > nums[begin]){
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
    return false;
}
```










链接：https://leetcode-cn.com/problems/search-in-rotated-sorted-array-ii/description/
