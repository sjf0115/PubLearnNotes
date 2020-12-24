### 1. 题目

给定一个可能包含重复元素的整数数组 nums，返回该数组所有可能的子集（幂集）。

说明：解集不能包含重复的子集。

示例:
```
输入: [1,2,2]
输出:
[
  [2],
  [1],
  [1,2,2],
  [2,2],
  [1,2],
  []
]
```

### 2. 实现

```java
public List<List<Integer>> subsetsWithDup(int[] nums) {
    List<List<Integer>> result = new ArrayList<>();
    Arrays.sort(nums);
    helper(result, new ArrayList<>(), nums, 0);
    return result;
}

private void helper(List<List<Integer>> result, List<Integer> tmpList, int[] nums, int index){
    result.add(new ArrayList<>(tmpList));
    for(int i = index; i < nums.length;i++){
        // 跳过重复
        if(i > index && nums[i] == nums[i-1]){
            continue;
        }
        tmpList.add(nums[i]);
        helper(result, tmpList, nums, i + 1);
        tmpList.remove(tmpList.size() - 1);
    }
}
```
