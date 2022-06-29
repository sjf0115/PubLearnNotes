---
layout: post
author: sjf0115
title: 347. 前K个高频元素
date: 2018-08-23 21:00:07
tags:
  - LeetCode

categories: LeetCode
permalink: leetcode-top-k-frequent-elements
---

### 1. 题目

给定一个非空的整数数组，返回其中出现频率前 k 高的元素。

示例 1:
```
输入: nums = [1,1,1,2,2,3], k = 2
输出: [1,2]
```
示例 2:
```
输入: nums = [1], k = 1
输出: [1]
```
说明：
- 你可以假设给定的 k 总是合理的，且 1 ≤ k ≤ 数组中不相同的元素的个数。
- 你的算法的时间复杂度必须优于 O(n log n) , n 是数组的大小。

### 2. 实现

```java
public List<Integer> topKFrequent(int[] nums, int k) {
    Queue<Map.Entry<Integer, Integer>> queue = new PriorityQueue<>(k, new Comparator<Map.Entry<Integer, Integer>>() {
        @Override
        public int compare(Map.Entry<Integer, Integer> o1, Map.Entry<Integer, Integer> o2) {
            return o1.getValue() - o2.getValue();
        }
    });
    Map<Integer, Integer> countMap = new HashMap<>();
    for(int num : nums){
        if(countMap.containsKey(num)){
            countMap.put(num, countMap.get(num) + 1);
        }
        else {
            countMap.put(num, 1);
        }
    }
    for(Map.Entry entry : countMap.entrySet()){
        System.out.println(entry.getKey());
        queue.add(entry);
        if(queue.size() > k){
            queue.poll();
        }
    }
    List<Integer> result = new ArrayList();
    for(int i = 0;i < k;i++){
        Map.Entry<Integer, Integer> element = queue.poll();
        result.add(0, element.getKey());
    }
    return result;
}
```
