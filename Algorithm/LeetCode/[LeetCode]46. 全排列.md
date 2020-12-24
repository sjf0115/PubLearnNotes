
### 1. 题目

给定一个没有重复数字的序列，返回其所有可能的全排列。

示例:
```
输入: [1,2,3]
输出:
[
  [1,2,3],
  [1,3,2],
  [2,1,3],
  [2,3,1],
  [3,1,2],
  [3,2,1]
]
```

### 2. 实现

```java
package array;

import java.util.ArrayList;
import java.util.List;

/**
 * 46. 全排列
 * https://leetcode-cn.com/problems/permutations/description/
 * @author sjf0115
 * @Date Created in 下午1:07 18-4-3
 */
public class Permutations {

    private List<List<Integer>> result;

    /**
     * 全排列
     * @param nums
     * @return
     */
    public List<List<Integer>> permute2(int[] nums) {

        result = new ArrayList<>();
        if(nums == null || nums.length == 0){
            return result;
        }
        List<Integer> tmpList = new ArrayList<>();
        boolean[] visited = new boolean[nums.length];
        DFS(nums, visited, tmpList);
        return result;
    }

    /**
     * 深度搜索  每一轮搜索选择一个数加入列表中，同时我们还要维护一个全局的布尔数组，来标记哪些元素已经被加入列表了，这样在下一轮搜索中要跳过这些元素。
     * @param nums
     * @param visited
     * @param tmpList
     */
    private void DFS(int[] nums, boolean[] visited, List<Integer> tmpList){

        if(nums.length == tmpList.size()){
            result.add(new ArrayList<>(tmpList));
            return;
        }
        for(int i = 0;i < nums.length;i++){
            if(!visited[i]){
                visited[i] = true;
                tmpList.add(nums[i]);
                DFS(nums, visited, tmpList);
                visited[i] = false;
                tmpList.remove(tmpList.size() - 1);
            }
        }

    }

    /**
     * 优化版
     * @param nums
     * @return
     */
    public List<List<Integer>> permute(int[] nums) {
        result = new ArrayList<>();
        if(nums == null || nums.length == 0){
            return result;
        }
        List<Integer> tmpList = new ArrayList<>();
        helper(nums, tmpList);
        return result;
    }

    /**
     * 优化版
     * @param nums
     * @param tmpList
     */
    private void helper(int[] nums, List<Integer> tmpList){
        int size = nums.length;
        if(tmpList.size() == size){
            result.add(new ArrayList<>(tmpList));
            return;
        }
        for(int i = 0;i < size;i++){
            // 已使用　跳过
            if(tmpList.contains(nums[i])){
                continue;
            }
            tmpList.add(nums[i]);
            helper(nums, tmpList);
            tmpList.remove(tmpList.size() - 1);
        }
    }
}
```
