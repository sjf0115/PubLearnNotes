---
layout: post
author: sjf0115
title: 442. 数组中重复的数据
date: 2017-03-21 00:04:42
tags:
  - LeetCode

categories: LeetCode
permalink: leetcode-find-all-duplicates-in-an-array
---

### 1. 题目描述

给定一个整数数组 a，其中1 ≤ a[i] ≤ n （n为数组长度）, 其中有些元素出现两次而其他元素出现一次。

找到所有出现两次的元素。

你可以不用到任何额外空间并在O(n)时间复杂度内解决这个问题吗？

示例：

输入:
```
[4,3,2,7,8,2,3,1]
```
输出:
```
[2,3]
```

### 2. 解决方案

#### 2.1 解法I 正负号标记法

参考　LeetCode Discuss：https://discuss.leetcode.com/topic/64735/java-simple-solution

对每一个数字（取绝对值），映射到数组中某一个位置上（只有该数字能映射到该位置），用该位置上的数字的正负号来表示是否出现两次。

遍历数组，记当前数字为n（取绝对值），将数字n视为下标（因为a[i]∈[1, n]）
- 当 n 首次出现时，nums[n - 1]乘以-1
- 当 n 再次出现时，则nums[n - 1]一定＜0，将n加入结果集合中。

```java
/**
 * 正负号标记法
 * @param nums
 * @return
 */
public List<Integer> findDuplicates(int[] nums) {

    List<Integer> result = new ArrayList<>();
    if(nums == null || nums.length == 0){
        return result;
    }

    for(int i = 0;i < nums.length;i++){
        int index = Math.abs(nums[i]) - 1;
        if(nums[index] < 0){
            result.add(Math.abs(nums[i]));
        }
        nums[index] *= -1;
    }
    return result;

}
```

#### 2.2 解法II 位置交换法

遍历nums，记当前下标为i

当nums[i] > 0 并且 nums[i] != i + 1时，执行循环：

令n = nums[i]

如果n == nums[n - 1]，则将n加入答案，并将nums[i]置为0

否则，交换nums[i], nums[n - 1]

```

```


























































题目地址：https://leetcode-cn.com/problems/find-all-duplicates-in-an-array/description/
