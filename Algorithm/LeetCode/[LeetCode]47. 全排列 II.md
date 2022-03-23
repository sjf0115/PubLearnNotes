
### 1. 题目

给定一个可包含重复数字的序列，返回所有不重复的全排列。

示例:
```
输入: [1,1,2]
输出:
[
  [1,1,2],
  [1,2,1],
  [2,1,1]
]
```

### 2. 实现

```java
public List<List<Integer>> permuteUnique(int[] nums) {
    List<List<Integer>> result = new ArrayList<>();
    Arrays.sort(nums);
    helper(result, new ArrayList<>(), nums, new boolean[nums.length+1]);
    return result;
}

/**
 * 假设原数组为 1' 1 2 会出现四种情况：
 * (1) 1' 1 2 (2) 1 1 2 (3) 1' 1' 2 (4) 1 1' 2
 * @param result
 * @param tmpList
 * @param nums
 * @param used
 */
private void helper(List<List<Integer>> result, List<Integer> tmpList, int[] nums, boolean[] used){
    int size = nums.length;
    if(tmpList.size() == size){
        result.add(new ArrayList<>(tmpList));
        return;
    }
    for(int i = 0;i < size;i++){
        // 跳过重复使用的　重复元素保持原数组中的相对顺序
        if(used[i] || (i > 0 && nums[i] == nums[i-1] && !used[i-1])){
            continue;
        }
        used[i] = true;
        tmpList.add(nums[i]);
        helper(result, tmpList, nums, used);
        used[i] = false;
        tmpList.remove(tmpList.size() - 1);
    }
}
```
